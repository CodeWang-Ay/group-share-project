"""
组会管理路由
端点：
- GET    /api/meetings - 获取组会列表
- POST   /api/meetings - 创建组会
- GET    /api/meetings/stats - 获取组会统计
- GET    /api/meetings/{meeting_id} - 获取组会详情
- PUT    /api/meetings/{meeting_id} - 更新组会
- DELETE /api/meetings/{meeting_id} - 删除组会
- PUT    /api/meetings/{meeting_id}/status - 更新组会状态
- GET    /api/meetings/{meeting_id}/presenters - 获取汇报人列表
- POST   /api/meetings/{meeting_id}/presenters - 添加汇报人
- DELETE /api/meetings/{meeting_id}/presenters/{presenter_id} - 移除汇报人
"""
from datetime import datetime
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from utils.auth_helper import get_current_user
from services.meeting_service import MeetingService
from database.connection import get_db

router = APIRouter(prefix="/api/meetings", tags=["组会"])


@router.get("")
async def get_meetings(request: Request):
    """
    获取组会列表API
    支持分页和筛选，同时返回汇报人信息
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 先自动更新组会状态（根据日期）
        MeetingService.auto_update_meeting_statuses()

        # 获取查询参数
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        meeting_status = request.query_params.get("status")
        meeting_type = request.query_params.get("meeting_type")
        search = request.query_params.get("search", "")

        offset = (page - 1) * limit

        # 获取组会列表
        meetings = MeetingService.get_meetings(
            status=meeting_status,
            meeting_type=meeting_type,
            search=search if search else None,
            limit=limit,
            offset=offset
        )

        # 获取总数
        total = MeetingService.get_meetings_count(
            status=meeting_status,
            meeting_type=meeting_type,
            search=search if search else None
        )

        # 为每个组会获取汇报人信息
        conn = get_db()
        cursor = conn.cursor()

        meetings_with_presenters = []
        for m in meetings:
            meeting_dict = m.to_dict()

            # 获取该组会的汇报人
            cursor.execute("""
                SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes, mp.status, mp.material_status,
                       u.username, u.role
                FROM meeting_presenters mp
                LEFT JOIN users u ON mp.user_id = u.id
                WHERE mp.meeting_id = ?
                ORDER BY mp.created_at ASC
            """, (m.id,))

            presenters = []
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

                presenters.append({
                    "id": row[0],
                    "user_id": row[1],
                    "presenter_type": row[2],
                    "duration_minutes": row[3],
                    "status": row[4],
                    "material_status": row[5],
                    "username": row[6],
                    "real_name": row[6],
                    "files": files
                })

            meeting_dict["presenters"] = presenters
            meetings_with_presenters.append(meeting_dict)

        conn.close()

        # 计算分页信息
        total_pages = (total + limit - 1) // limit if total > 0 else 1

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "meetings": meetings_with_presenters,
                    "pagination": {
                        "current_page": page,
                        "per_page": limit,
                        "total": total,
                        "total_pages": total_pages,
                        "has_next": page < total_pages,
                        "has_prev": page > 1
                    }
                }
            }
        )
    except Exception as e:
        logger.error(f"获取组会列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取组会列表失败", "error": "INTERNAL_ERROR"}
        )


@router.post("")
async def create_meeting(request: Request):
    """
    创建组会API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()

        # 验证必填字段
        if not data.get("title"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "组会标题不能为空", "error": "VALIDATION_ERROR"}
            )

        if not data.get("scheduled_at"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "会议时间不能为空", "error": "VALIDATION_ERROR"}
            )

        # 解析时间
        scheduled_at = datetime.fromisoformat(data["scheduled_at"])
        material_deadline = None
        if data.get("material_deadline"):
            material_deadline = datetime.fromisoformat(data["material_deadline"])

        # 创建组会
        meeting = MeetingService.create_meeting(
            title=data["title"],
            meeting_type=data.get("meeting_type", "regular"),
            scheduled_at=scheduled_at,
            created_by=current_user.id,
            description=data.get("description"),
            location=data.get("location"),
            is_online=data.get("is_online", False),
            online_link=data.get("online_link"),
            duration_total=data.get("duration_total", 60),
            material_required=data.get("material_required", True),
            material_deadline=material_deadline,
            notes=data.get("notes"),
            minutes=data.get("minutes")
        )

        logger.info(f"创建组会成功: {meeting.title} (ID: {meeting.id})")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "组会创建成功",
                "data": meeting.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"创建组会失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "创建组会失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/stats")
async def get_meeting_stats(request: Request):
    """
    获取组会统计信息API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 先自动更新组会状态
        MeetingService.auto_update_meeting_statuses()

        stats = MeetingService.get_meeting_stats()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": stats
            }
        )
    except Exception as e:
        logger.error(f"获取组会统计失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取组会统计失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/{meeting_id}")
async def get_meeting_detail(meeting_id: int, request: Request):
    """
    获取组会详情API，包含汇报人信息
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        meeting = MeetingService.get_meeting_by_id(meeting_id)
        if not meeting:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}
            )

        # 获取汇报人信息
        meeting_dict = meeting.to_dict()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes, mp.status,
                   u.username, u.role
            FROM meeting_presenters mp
            LEFT JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = ?
            ORDER BY mp.created_at ASC
        """, (meeting_id,))

        presenters = []
        for row in cursor.fetchall():
            presenters.append({
                "id": row[0],
                "user_id": row[1],
                "presenter_type": row[2],
                "duration_minutes": row[3],
                "status": row[4],
                "username": row[5],
                "real_name": row[5],
                "user_role": row[6]
            })

        meeting_dict["presenters"] = presenters
        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": meeting_dict
            }
        )
    except Exception as e:
        logger.error(f"获取组会详情失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取组会详情失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/{meeting_id}")
async def update_meeting(meeting_id: int, request: Request):
    """
    更新组会API
    只有导师、管理员或创建者可以更新
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取组会
        meeting = MeetingService.get_meeting_by_id(meeting_id)
        if not meeting:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}
            )

        # 权限检查：只有导师、管理员或创建者可以更新
        if current_user.role not in ['admin', 'teacher'] and meeting.created_by != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "没有权限修改此组会", "error": "ACCESS_DENIED"}
            )

        data = await request.json()

        # 解析时间字段
        update_data = {}
        if data.get("scheduled_at"):
            update_data["scheduled_at"] = datetime.fromisoformat(data["scheduled_at"])
        if data.get("material_deadline"):
            update_data["material_deadline"] = datetime.fromisoformat(data["material_deadline"])

        # 其他字段
        for field in ['title', 'meeting_type', 'description', 'location', 'is_online',
                       'online_link', 'duration_total', 'material_required', 'notes', 'minutes', 'status']:
            if field in data:
                update_data[field] = data[field]

        updated_meeting = MeetingService.update_meeting(meeting_id, **update_data)

        if not updated_meeting:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "更新组会失败", "error": "UPDATE_FAILED"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "组会更新成功",
                "data": updated_meeting.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"更新组会失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新组会失败", "error": "INTERNAL_ERROR"}
        )


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: int, request: Request):
    """
    删除组会API
    只有导师和管理员可以删除
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限检查
    if current_user.role not in ['admin', 'teacher']:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限删除组会", "error": "ACCESS_DENIED"}
        )

    try:
        success = MeetingService.delete_meeting(meeting_id)

        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "组会删除成功"}
        )
    except Exception as e:
        logger.error(f"删除组会失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "删除组会失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/{meeting_id}/status")
async def update_meeting_status(meeting_id: int, request: Request):
    """
    更新组会状态API
    只有导师和管理员可以更新状态
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限检查
    if current_user.role not in ['admin', 'teacher']:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限更新组会状态", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()
        status_value = data.get("status")

        # 支持的状态：scheduled(待召开)、ongoing(进行中)、completed(已召开)、cancelled(废弃)、postponed(推迟)
        valid_statuses = ['scheduled', 'ongoing', 'completed', 'cancelled', 'postponed']
        if status_value not in valid_statuses:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": f"状态值无效，有效状态：{', '.join(valid_statuses)}", "error": "INVALID_STATUS"}
            )

        updated_meeting = MeetingService.update_meeting_status(meeting_id, status_value)

        if not updated_meeting:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}
            )

        # 组会状态联动更新汇报人状态
        conn = get_db()
        cursor = conn.cursor()

        if status_value == 'completed':
            # 组会召开完成，自动更新汇报人状态为 completed
            cursor.execute("""
                UPDATE meeting_presenters
                SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ? AND status = 'confirmed'
            """, (meeting_id,))

            # 自动通过已提交的材料
            cursor.execute("""
                UPDATE meeting_presenters
                SET material_status = 'approved', updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ? AND material_status = 'submitted'
            """, (meeting_id,))

        elif status_value == 'cancelled':
            # 组会废弃，重置材料状态
            cursor.execute("""
                UPDATE meeting_presenters
                SET material_status = 'pending', updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ?
            """, (meeting_id,))

        conn.commit()
        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "组会状态更新成功",
                "data": updated_meeting.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"更新组会状态失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新组会状态失败", "error": "INTERNAL_ERROR"}
        )


# ==================== 汇报人管理API ====================

@router.get("/{meeting_id}/presenters")
async def get_meeting_presenters(meeting_id: int, request: Request):
    """
    获取组会汇报人列表API
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

        # 获取汇报人列表，包含用户信息和材料状态
        cursor.execute("""
            SELECT mp.id, mp.meeting_id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                   mp.material_required, mp.status, mp.material_status, mp.created_at, mp.updated_at,
                   u.username, u.role, u.research_direction
            FROM meeting_presenters mp
            LEFT JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = ?
            ORDER BY mp.created_at ASC
        """, (meeting_id,))

        presenters = []
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

            presenters.append({
                "id": row[0],
                "meeting_id": row[1],
                "user_id": row[2],
                "presenter_type": row[3],
                "duration_minutes": row[4],
                "material_required": row[5],
                "status": row[6],
                "material_status": row[7],
                "created_at": row[8],
                "updated_at": row[9],
                "user": {
                    "id": row[2],
                    "username": row[10],
                    "real_name": row[10],  # 使用 username 作为显示名
                    "role": row[11],
                    "research_direction": row[12]
                },
                "files": files
            })

        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": {"presenters": presenters}}
        )
    except Exception as e:
        logger.error(f"获取汇报人列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取汇报人列表失败", "error": "INTERNAL_ERROR"}
        )


@router.post("/{meeting_id}/presenters")
async def add_meeting_presenter(meeting_id: int, request: Request):
    """
    添加汇报人API
    导师、管理员或组会创建者可以添加
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限检查：导师和管理员直接允许
    if current_user.role not in ['admin', 'teacher']:
        # 检查是否是组会创建者
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT created_by FROM meetings WHERE id = ?", (meeting_id,))
            meeting_row = cursor.fetchone()

        if not meeting_row or meeting_row[0] != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "只有导师、管理员或组会创建者可以分配汇报人", "error": "ACCESS_DENIED"}
            )

    try:
        data = await request.json()
        user_id = data.get("user_id")
        presenter_type = data.get("presenter_type", "assigned")
        duration_minutes = data.get("duration_minutes", 20)

        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请选择汇报人", "error": "VALIDATION_ERROR"}
            )

        with get_db() as conn:
            cursor = conn.cursor()

            # 检查是否已存在
            cursor.execute("SELECT id FROM meeting_presenters WHERE meeting_id = ? AND user_id = ?", (meeting_id, user_id))
            if cursor.fetchone():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "message": "该成员已是汇报人", "error": "ALREADY_EXISTS"}
                )

            # 添加汇报人
            cursor.execute("""
                INSERT INTO meeting_presenters (meeting_id, user_id, presenter_type, duration_minutes, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (meeting_id, user_id, presenter_type, duration_minutes))
            presenter_id = cursor.lastrowid

            # 获取添加的汇报人信息
            cursor.execute("""
                SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes, mp.status,
                       u.username, u.research_direction
                FROM meeting_presenters mp
                LEFT JOIN users u ON mp.user_id = u.id
                WHERE mp.id = ?
            """, (presenter_id,))
            row = cursor.fetchone()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "添加汇报人成功",
                "data": {
                    "id": row[0],
                    "meeting_id": meeting_id,
                    "user_id": row[1],
                    "presenter_type": row[2],
                    "duration_minutes": row[3],
                    "status": row[4],
                    "user": {
                        "id": row[1],
                        "username": row[5],
                        "real_name": row[5],
                        "research_direction": row[6]
                    }
                }
            }
        )
    except Exception as e:
        logger.error(f"添加汇报人失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "添加汇报人失败", "error": "INTERNAL_ERROR"}
        )


@router.delete("/{meeting_id}/presenters/{presenter_id}")
async def remove_meeting_presenter(meeting_id: int, presenter_id: int, request: Request):
    """
    移除汇报人API
    导师、管理员或组会创建者可以移除
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限检查：导师和管理员直接允许
    if current_user.role not in ['admin', 'teacher']:
        # 检查是否是组会创建者
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT created_by FROM meetings WHERE id = ?", (meeting_id,))
            meeting_row = cursor.fetchone()

        if not meeting_row or meeting_row[0] != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "只有导师、管理员或组会创建者可以移除汇报人", "error": "ACCESS_DENIED"}
            )

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meeting_presenters WHERE id = ? AND meeting_id = ?", (presenter_id, meeting_id))
            deleted = cursor.rowcount > 0

        if not deleted:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "汇报人不存在", "error": "NOT_FOUND"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "移除汇报人成功"}
        )
    except Exception as e:
        logger.error(f"移除汇报人失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "移除汇报人失败", "error": "INTERNAL_ERROR"}
        )