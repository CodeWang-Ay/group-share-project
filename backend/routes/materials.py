"""
汇报材料路由
端点：
- GET  /api/materials - 获取汇报材料列表
- GET  /api/materials/meetings - 获取组会及材料状态
- GET  /api/materials/{presenter_id}/files - 获取汇报人文件
- PUT  /api/materials/{presenter_id}/confirm - 确认参会
- PUT  /api/materials/{presenter_id}/status - 更新材料审核状态
- POST /api/materials/{presenter_id}/files - 上传材料文件
- GET  /api/meetings/{meeting_id}/materials - 获取组会所有材料
- GET  /api/meeting_files/{file_id}/download - 下载汇报材料
"""
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, FileResponse
from loguru import logger

from database.connection import get_db
from utils.auth_helper import get_current_user

router = APIRouter(prefix="/api", tags=["汇报材料"])


@router.get("/materials")
async def get_materials(request: Request):
    """
    获取汇报材料列表API
    显示所有组会的汇报人材料状态
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取查询参数
        status_filter = request.query_params.get("status")  # pending, submitted, approved, rejected
        meeting_id_filter = request.query_params.get("meeting_id")

        conn = get_db()
        cursor = conn.cursor()

        # 构建查询条件
        where_conditions = ["mp.material_required = 1"]
        params = []

        if status_filter:
            where_conditions.append("mp.material_status = ?")
            params.append(status_filter)

        if meeting_id_filter:
            where_conditions.append("mp.meeting_id = ?")
            params.append(int(meeting_id_filter))

        where_clause = "WHERE " + " AND ".join(where_conditions)

        # 查询汇报材料列表
        query = f"""
            SELECT mp.id, mp.meeting_id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                   mp.material_status, mp.created_at, mp.updated_at,
                   m.title, m.scheduled_at, m.meeting_type, m.status as meeting_status,
                   u.username, u.role as user_role
            FROM meeting_presenters mp
            LEFT JOIN meetings m ON mp.meeting_id = m.id
            LEFT JOIN users u ON mp.user_id = u.id
            {where_clause}
            ORDER BY m.scheduled_at DESC, mp.created_at ASC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        materials = []
        for row in rows:
            # 获取关联的文件（从 meeting_files 表直接获取，不依赖 files 表）
            cursor.execute("""
                SELECT mf.id, mf.filename, mf.file_type, mf.file_size, mf.uploaded_at
                FROM meeting_files mf
                WHERE mf.presenter_id = ? AND mf.filename IS NOT NULL
            """, (row[0],))

            files = []
            for file_row in cursor.fetchall():
                files.append({
                    "id": file_row[0],
                    "filename": file_row[1],
                    "file_type": file_row[2],
                    "file_size": file_row[3],
                    "uploaded_at": file_row[4]
                })

            # 状态文本映射
            status_text_map = {
                'pending': '待提交',
                'submitted': '待审核',
                'approved': '已通过',
                'rejected': '已驳回'
            }

            materials.append({
                "id": row[0],
                "meeting_id": row[1],
                "user_id": row[2],
                "presenter_type": row[3],
                "duration_minutes": row[4],
                "status": row[5],
                "status_text": status_text_map.get(row[5], '待提交'),
                "created_at": row[6],
                "updated_at": row[7],
                "meeting_title": row[8],
                "meeting_scheduled_at": row[9],
                "meeting_type": row[10],
                "meeting_status": row[11],
                "username": row[12],
                "user_role": row[13],
                "files": files
            })

        conn.close()

        # 统计数据
        stats = {
            "total": len(materials),
            "pending": len([m for m in materials if m['status'] == 'pending']),
            "submitted": len([m for m in materials if m['status'] == 'submitted']),
            "approved": len([m for m in materials if m['status'] == 'approved']),
            "rejected": len([m for m in materials if m['status'] == 'rejected'])
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "materials": materials,
                    "stats": stats
                }
            }
        )
    except Exception as e:
        logger.error(f"获取汇报材料列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取汇报材料列表失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/materials/meetings")
async def get_meetings_with_materials(request: Request):
    """
    获取组会列表及汇报人材料状态API
    用于汇报材料页面，按组会展示汇报人材料情况
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        conn = get_db()
        cursor = conn.cursor()

        # 获取查询参数
        material_status_filter = request.query_params.get("material_status")  # pending, submitted, approved
        search_keyword = request.query_params.get("search", "")

        # 获取所有组会（排除已废弃的）
        cursor.execute("""
            SELECT m.id, m.title, m.scheduled_at, m.meeting_type, m.status, m.location,
                   m.duration_total, m.description
            FROM meetings m
            WHERE m.status != 'cancelled'
            ORDER BY m.scheduled_at DESC
        """)
        meetings_rows = cursor.fetchall()

        meetings = []
        total_pending = 0
        total_submitted = 0
        total_approved = 0

        for row in meetings_rows:
            meeting = dict(row)

            # 搜索过滤
            if search_keyword and search_keyword.lower() not in (meeting.get('title', '') or '').lower():
                continue

            # 获取该组会的汇报人
            cursor.execute("""
                SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                       mp.material_status, mp.status, u.username
                FROM meeting_presenters mp
                LEFT JOIN users u ON mp.user_id = u.id
                WHERE mp.meeting_id = ?
                ORDER BY mp.created_at ASC
            """, (meeting['id'],))
            presenters_rows = cursor.fetchall()

            presenters = []
            meeting_has_pending = False
            meeting_has_submitted = False
            meeting_all_approved = True

            for p_row in presenters_rows:
                presenter = dict(p_row)
                presenter['user'] = {
                    'username': presenter.get('username', ''),
                    'real_name': presenter.get('username', '')  # 使用 username 作为显示名
                }
                presenter['name'] = presenter.get('username', '未知')

                # 获取该汇报人的文件
                cursor.execute("""
                    SELECT id, filename, file_path, file_size, file_type, uploaded_at
                    FROM meeting_files
                    WHERE presenter_id = ? AND filename IS NOT NULL
                """, (presenter['id'],))
                files_rows = cursor.fetchall()
                presenter['files'] = [dict(f) for f in files_rows]

                presenters.append(presenter)

                # 统计材料状态
                presenter_status = presenter.get('material_status', 'pending')
                if presenter_status == 'pending':
                    total_pending += 1
                    meeting_has_pending = True
                    meeting_all_approved = False
                elif presenter_status == 'submitted':
                    total_submitted += 1
                    meeting_has_submitted = True
                    meeting_all_approved = False
                elif presenter_status == 'approved':
                    total_approved += 1

            meeting['presenters'] = presenters

            # 按材料状态筛选组会
            if material_status_filter == 'pending' and not meeting_has_pending:
                continue
            elif material_status_filter == 'submitted' and not meeting_has_submitted:
                continue
            elif material_status_filter == 'approved' and not meeting_all_approved:
                continue

            meetings.append(meeting)

        stats = {
            'total_meetings': len(meetings),
            'pending': total_pending,
            'submitted': total_submitted,
            'approved': total_approved
        }

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "meetings": meetings,
                    "stats": stats
                }
            }
        )
    except Exception as e:
        logger.error(f"获取组会材料列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取组会材料列表失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/materials/{presenter_id}/files")
async def get_presenter_files(presenter_id: int, request: Request):
    """
    获取汇报人的文件列表API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, filename, file_path, file_size, file_type, uploaded_at
            FROM meeting_files
            WHERE presenter_id = ? AND filename IS NOT NULL
            ORDER BY uploaded_at DESC
        """, (presenter_id,))

        files = []
        for row in cursor.fetchall():
            files.append({
                "id": row[0],
                "filename": row[1],
                "file_path": row[2],
                "file_size": row[3],
                "file_type": row[4],
                "uploaded_at": row[5]
            })

        conn.close()

        return JSONResponse(
            content={"success": True, "files": files}
        )
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取文件列表失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/materials/{presenter_id}/confirm")
async def confirm_presenter_attendance(presenter_id: int, request: Request):
    """
    汇报人确认参会API
    只有被指定的汇报人自己可以确认
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        conn = get_db()
        cursor = conn.cursor()

        # 获取汇报人信息
        cursor.execute("""
            SELECT mp.id, mp.user_id, mp.meeting_id, mp.status, mp.presenter_type
            FROM meeting_presenters mp
            WHERE mp.id = ?
        """, (presenter_id,))

        presenter_row = cursor.fetchone()
        if not presenter_row:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "汇报人记录不存在"}
            )

        presenter = dict(presenter_row)

        # 只有汇报人自己可以确认参会
        if presenter['user_id'] != current_user.id:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "只有汇报人本人可以确认参会"}
            )

        # 更新状态为已确认
        cursor.execute("""
            UPDATE meeting_presenters
            SET status = 'confirmed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (presenter_id,))

        conn.commit()
        conn.close()

        return {"success": True, "message": "已确认参会"}

    except Exception as e:
        logger.error(f"确认参会失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "服务器错误"}
        )


@router.put("/materials/{presenter_id}/status")
async def update_material_status(presenter_id: int, request: Request):
    """
    更新材料审核状态API
    只有导师和管理员可以审核
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取汇报人信息，检查权限
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mp.id, mp.user_id, mp.meeting_id
            FROM meeting_presenters mp
            WHERE mp.id = ?
        """, (presenter_id,))

        presenter_row = cursor.fetchone()
        if not presenter_row:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "汇报人不存在", "error": "NOT_FOUND"}
            )

        presenter_user_id = presenter_row[1]

        # 权限检查：汇报人本人、导师、管理员都可以审核
        if current_user.id != presenter_user_id and current_user.role not in ['admin', 'teacher']:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "只有汇报人本人、导师或管理员可以审核材料", "error": "ACCESS_DENIED"}
            )

        data = await request.json()
        new_status = data.get("status")

        if new_status not in ['pending', 'submitted', 'approved', 'rejected']:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "无效的状态值", "error": "VALIDATION_ERROR"}
            )

        cursor.execute("""
            UPDATE meeting_presenters
            SET material_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, presenter_id))

        conn.commit()
        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "材料状态更新成功"}
        )
    except Exception as e:
        logger.error(f"更新材料状态失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新材料状态失败", "error": "INTERNAL_ERROR"}
        )


@router.post("/materials/{presenter_id}/files")
async def upload_material_file(presenter_id: int, request: Request):
    """
    为汇报人上传材料文件API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取汇报人信息
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mp.id, mp.meeting_id, mp.user_id, mp.status
            FROM meeting_presenters mp
            WHERE mp.id = ?
        """, (presenter_id,))

        presenter_row = cursor.fetchone()
        if not presenter_row:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "汇报人不存在", "error": "NOT_FOUND"}
            )

        # 权限检查：只有汇报人本人、导师、管理员可以上传
        presenter_user_id = presenter_row[2]
        if current_user.id != presenter_user_id and current_user.role not in ['admin', 'teacher']:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "只有汇报人本人或导师可以上传材料", "error": "ACCESS_DENIED"}
            )

        # 解析请求体
        form = await request.form()
        file = form.get("file")

        if not file:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请选择要上传的文件", "error": "VALIDATION_ERROR"}
            )

        # 检查文件大小
        file_content = await file.read()
        file_size = len(file_content)
        if file_size > 50 * 1024 * 1024:  # 50MB
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "文件大小超过限制（最大50MB）", "error": "FILE_TOO_LARGE"}
            )

        # 检查文件类型
        original_filename = file.filename
        file_type = original_filename.split('.')[-1].lower() if '.' in original_filename else 'unknown'
        allowed_types = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md', 'zip', 'rar']
        if file_type not in allowed_types:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": f"不支持的文件类型: {file_type}", "error": "UNSUPPORTED_TYPE"}
            )

        # 生成唯一文件名（时间戳前缀）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{original_filename}"

        # 创建材料存储目录
        materials_dir = Path(__file__).parent.parent / "uploads" / "materials"
        materials_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件到磁盘
        file_path = materials_dir / unique_filename
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # 直接插入到 meeting_files 表（独立存储，不依赖 files 表）
        meeting_id = presenter_row[1]
        cursor.execute("""
            INSERT INTO meeting_files (meeting_id, presenter_id, filename, file_path, file_size, file_type, uploaded_by, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (meeting_id, presenter_id, unique_filename, str(file_path), file_size, file_type, current_user.id))

        meeting_file_id = cursor.lastrowid

        # 更新汇报人材料状态为已通过（无需审核）
        cursor.execute("""
            UPDATE meeting_presenters
            SET material_status = 'approved', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (presenter_id,))

        conn.commit()
        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "材料上传成功",
                "data": {
                    "file_id": meeting_file_id,
                    "filename": unique_filename,
                    "file_type": file_type,
                    "file_size": file_size
                }
            }
        )
    except Exception as e:
        logger.error(f"上传材料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "上传材料失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/meetings/{meeting_id}/materials")
async def get_meeting_materials(meeting_id: int, request: Request):
    """
    获取组会的所有汇报材料API（供组会记录页面使用）
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        conn = get_db()
        cursor = conn.cursor()

        # 获取组会所有汇报人的材料
        cursor.execute("""
            SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                   mp.material_status, u.username
            FROM meeting_presenters mp
            LEFT JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = ?
            ORDER BY mp.created_at ASC
        """, (meeting_id,))

        materials = []
        for row in cursor.fetchall():
            presenter_id = row[0]

            # 获取该汇报人的文件（从 meeting_files 表直接获取）
            cursor.execute("""
                SELECT mf.id, mf.filename, mf.file_type, mf.file_size, mf.uploaded_at
                FROM meeting_files mf
                WHERE mf.presenter_id = ? AND mf.filename IS NOT NULL
            """, (presenter_id,))

            files = []
            for file_row in cursor.fetchall():
                files.append({
                    "id": file_row[0],
                    "filename": file_row[1],
                    "file_type": file_row[2],
                    "file_size": file_row[3],
                    "uploaded_at": file_row[4]
                })

            materials.append({
                "presenter_id": presenter_id,
                "user_id": row[1],
                "username": row[5],
                "real_name": row[5],
                "presenter_type": row[2],
                "duration_minutes": row[3],
                "material_status": row[4],
                "files": files
            })

        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": {"materials": materials}}
        )
    except Exception as e:
        logger.error(f"获取组会材料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取组会材料失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/meeting_files/{file_id}/download")
async def download_meeting_file(file_id: int, request: Request):
    """
    下载汇报材料文件API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mf.id, mf.filename, mf.file_path, mf.file_type
            FROM meeting_files mf
            WHERE mf.id = ? AND mf.filename IS NOT NULL
        """, (file_id,))

        file_row = cursor.fetchone()
        conn.close()

        if not file_row:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件不存在", "error": "NOT_FOUND"}
            )

        file_path = Path(file_row[2])
        if not file_path.exists():
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件已被删除", "error": "FILE_NOT_FOUND"}
            )

        return FileResponse(
            path=str(file_path),
            filename=file_row[1],
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"下载汇报材料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "下载失败", "error": "INTERNAL_ERROR"}
        )