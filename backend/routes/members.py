"""
================================================================================
成员管理路由模块 (routes/members.py)
================================================================================

模块名称: backend/routes/members.py
功能描述: 团队成员管理 API 端点，包括成员增删改查、批量操作等

API 端点列表 (共10个):
    GET    /api/members                    - 获取成员列表（分页筛选）
        参数: role, status, degree, search, page, per_page
        返回: 成员列表 + 分页信息

    GET    /api/members/stats              - 获取成员统计
        返回: 总人数、角色分布、活跃/非活跃数量

    PUT    /api/members/{member_id}/status - 更新成员状态
        接收: status (active/inactive)
        需要管理员权限

    PUT    /api/members/{member_id}        - 更新成员信息
        接收: username, email, phone, role, degree_type 等
        需要管理员权限

    POST   /api/members                    - 添加新成员
        接收: 完整成员信息
        需要管理员权限

    DELETE /api/members/{member_id}        - 删除成员
        需要管理员权限

    PUT    /api/members/{member_id}/reset-password - 重置密码
        接收: new_password
        需要管理员权限

    POST   /api/users/batch-update-role    - 批量修改角色
        接收: user_ids[], role
        需要管理员权限

    POST   /api/users/batch-update-status  - 批量修改状态
        接收: user_ids[], status
        需要管理员权限

    POST   /api/users/batch-delete         - 批量删除成员
        接收: user_ids[]
        需要管理员权限

路由配置:
    - 前缀: /api
    - 标签: 成员管理

权限要求:
    大部分端点需要管理员 (admin) 权限

依赖模块:
    - utils.auth_helper       : get_current_user, get_admin_user
    - utils.helpers           : getFieldLabel 字段标签映射
    - database.connection     : 数据库连接
    - models.user.User        : 用户模型

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
import re
from datetime import datetime

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
import bcrypt
from loguru import logger

from models.user import User
from database.connection import get_db
from utils.auth_helper import get_current_user
from utils.helpers import getFieldLabel

router = APIRouter(prefix="/api", tags=["成员管理"])


@router.get("/members")
async def get_members(request: Request):
    """获取成员列表API端点"""
    logger.info("获取成员列表")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取查询参数
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 10))
        role_filter = request.query_params.get("role", "")
        status_filter = request.query_params.get("status", "")
        degree_filter = request.query_params.get("degree", "")
        search = request.query_params.get("search", "")

        # 验证参数
        if per_page not in [5, 10, 20, 50, 100]:
            per_page = 10
        if page < 1:
            page = 1

        offset = (page - 1) * per_page

        with get_db() as conn:
            cursor = conn.cursor()

            # 构建查询条件
            where_conditions = []
            params = []

            if role_filter:
                where_conditions.append("role = ?")
                params.append(role_filter)
            if status_filter:
                where_conditions.append("status = ?")
                params.append(status_filter)
            if degree_filter:
                where_conditions.append("degree_type = ?")
                params.append(degree_filter)
            if search:
                where_conditions.append("(username LIKE ? OR id LIKE ? OR student_id LIKE ? OR real_name LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # 获取总记录数
            cursor.execute(f"SELECT COUNT(*) FROM users {where_clause}", params)
            total = cursor.fetchone()[0]

            # 获取成员信息列表
            query = f"""
                SELECT id, username, role, created_at, updated_at, email, phone,
                       student_id, research_direction, status, graduation_status,
                       supervisor, degree_type, work_location, work_company,
                       personal_bio, personal_homepage, gender, id_card, bank_card, avatar
                FROM users
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [per_page, offset])
            rows = cursor.fetchall()

            # 转换为字典格式
            members = []
            for row in rows:
                member = dict(row)
                member['student_id'] = member.get('student_id') or None
                member['email'] = member.get('email') or None
                member['phone'] = member.get('phone') or None
                member['status'] = member.get('status') or 'active'
                member['research_direction'] = member.get('research_direction') or None
                member['degree_type'] = member.get('degree_type') or None
                member['gender'] = member.get('gender') or None
                # 使用真实头像，如果没有则生成默认头像
                if member.get('avatar'):
                    member['avatar'] = member['avatar']
                else:
                    member['avatar'] = f"https://picsum.photos/seed/{member['username']}/100/100.jpg"
                member['created_at'] = member['created_at'].split(' ')[0] if member['created_at'] else None
                members.append(member)

            # 计算分页信息
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1
            has_next = page < total_pages
            has_prev = page > 1

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "data": {
                        "members": members,
                        "pagination": {
                            "current_page": page,
                            "per_page": per_page,
                            "total": total,
                            "total_pages": total_pages,
                            "has_next": has_next,
                            "has_prev": has_prev,
                            "next_page": page + 1 if has_next else None,
                            "prev_page": page - 1 if has_prev else None
                        }
                    }
                }
            )

    except Exception as e:
        logger.error(f"获取成员列表失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取成员列表失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/members/stats")
async def get_members_stats(request: Request):
    """获取成员统计信息API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM users")
            total_members = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
            active_members = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
            student_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
            teacher_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]

            stats = {
                "total_members": total_members,
                "active_members": active_members,
                "student_count": student_count,
                "teacher_count": teacher_count,
                "admin_count": admin_count,
                "inactive_members": total_members - active_members
            }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": stats}
        )

    except Exception as e:
        logger.error(f"获取成员统计失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取成员统计失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/members/{member_id}/status")
async def update_member_status(member_id: int, request: Request):
    """更新成员状态API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限修改成员状态", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()
        new_status = data.get("status")

        if new_status not in ["active", "inactive"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "状态值无效", "error": "INVALID_STATUS"}
            )

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_status, member_id)
            )

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "成员不存在", "error": "MEMBER_NOT_FOUND"}
                )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "成员状态更新成功"}
        )

    except Exception as e:
        logger.error(f"更新成员状态失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新成员状态失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/members/{member_id}")
async def update_member_info(member_id: int, request: Request):
    """更新成员信息API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限更新成员信息", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()

        # 允许更新的字段
        allowed_fields = [
            'username', 'email', 'phone', 'student_id', 'role',
            'research_direction', 'personal_bio', 'gender',
            'id_card', 'bank_card', 'status', 'degree_type'
        ]

        # 过滤出允许更新的字段
        update_data = {}
        for field in allowed_fields:
            if field in data and data[field] is not None:
                update_data[field] = data[field]

        if not update_data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "没有提供要更新的数据", "error": "NO_DATA"}
            )

        # 验证角色
        if 'role' in update_data and update_data['role'] not in ['admin', 'teacher', 'student']:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "角色值无效", "error": "INVALID_ROLE"}
            )

        # 验证状态
        if 'status' in update_data and update_data['status'] not in ['active', 'inactive']:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "状态值无效", "error": "INVALID_STATUS"}
            )

        # 验证身份证号格式
        if 'id_card' in update_data and update_data['id_card']:
            if len(update_data['id_card']) != 18:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "message": "身份证号必须为18位", "error": "INVALID_ID_CARD"}
                )

        with get_db() as conn:
            cursor = conn.cursor()

            # 检查成员是否存在
            cursor.execute("SELECT id FROM users WHERE id = ?", (member_id,))
            if not cursor.fetchone():
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "成员不存在", "error": "MEMBER_NOT_FOUND"}
                )

            # 如果更新用户名，检查是否重复
            if 'username' in update_data:
                cursor.execute(
                    "SELECT id FROM users WHERE username = ? AND id != ?",
                    (update_data['username'], member_id)
                )
                if cursor.fetchone():
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"success": False, "message": "用户名已存在", "error": "USERNAME_EXISTS"}
                    )

            # 构建更新语句
            set_clause = ", ".join([f"{field} = ?" for field in update_data.keys()])
            values = list(update_data.values()) + [member_id]

            cursor.execute(
                f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "成员不存在或更新失败", "error": "UPDATE_FAILED"}
                )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"success": True, "message": "成员信息更新成功", "data": update_data}
            )

    except Exception as e:
        logger.error(f"更新成员信息失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新成员信息失败", "error": "INTERNAL_ERROR"}
        )


@router.post("/members")
async def create_member(request: Request):
    """添加成员API端点（管理员专用）"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限添加成员", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()

        # 必填字段验证
        required_fields = ['username', 'password', 'email', 'role']
        for field in required_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "message": f"请填写{getFieldLabel(field)}", "error": "MISSING_FIELD"}
                )

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        student_id = data.get('student_id', '').strip()
        role = data.get('role', '').strip()

        # 验证角色
        if role not in ['admin', 'teacher', 'student']:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "角色值无效", "error": "INVALID_ROLE"}
            )

        # 验证用户名格式
        if not User.is_valid_username(username):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "用户名格式不正确：3-50个字符，只允许字母、数字、下划线", "error": "INVALID_USERNAME"}
            )

        # 验证密码长度
        if len(password) < 6:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "密码长度至少为6位", "error": "PASSWORD_TOO_SHORT"}
            )

        # 验证邮箱格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "邮箱格式不正确", "error": "INVALID_EMAIL"}
            )

        with get_db() as conn:
            cursor = conn.cursor()

            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "message": "用户名已存在", "error": "USERNAME_EXISTS"}
                )

            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "message": "邮箱已存在", "error": "EMAIL_EXISTS"}
                )

            # 检查学号是否已存在
            if student_id:
                cursor.execute("SELECT id FROM users WHERE student_id = ?", (student_id,))
                if cursor.fetchone():
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"success": False, "message": "学号/工号已存在", "error": "STUDENT_ID_EXISTS"}
                    )

            # 创建新用户
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, email, phone, student_id, role,
                    research_direction, personal_bio, gender, id_card, bank_card,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                username,
                password_hash.decode('utf-8'),
                email,
                phone if phone else None,
                student_id if student_id else None,
                role,
                data.get('research_direction'),
                data.get('personal_bio'),
                data.get('gender'),
                data.get('id_card'),
                data.get('bank_card')
            ))

            cursor.execute("SELECT last_insert_rowid()")
            new_user_id = cursor.fetchone()[0]

            logger.info(f"管理员 {current_user.username} 创建了新用户: {username} (ID: {new_user_id})")

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "success": True,
                    "message": "成员添加成功",
                    "data": {
                        "id": new_user_id,
                        "username": username,
                        "email": email,
                        "role": role,
                        "student_id": student_id
                    }
                }
            )

    except Exception as e:
        logger.error(f"添加成员失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "添加成员失败", "error": "INTERNAL_ERROR"}
        )


@router.delete("/members/{member_id}")
async def delete_member(member_id: int, request: Request):
    """删除成员API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限删除成员", "error": "ACCESS_DENIED"}
        )

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (member_id,))

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "成员不存在", "error": "MEMBER_NOT_FOUND"}
                )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "成员删除成功"}
        )

    except Exception as e:
        logger.error(f"删除成员失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "删除成员失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/members/{member_id}/reset-password")
async def reset_member_password(member_id: int, request: Request):
    """重置成员密码API端点（管理员专用）"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限重置密码", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()
        new_password = data.get("password", "123456")  # 默认密码为123456

        # 验证密码长度
        if len(new_password) < 6:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "密码长度至少为6位", "error": "PASSWORD_TOO_SHORT"}
            )

        with get_db() as conn:
            cursor = conn.cursor()

            # 检查成员是否存在
            cursor.execute("SELECT username FROM users WHERE id = ?", (member_id,))
            member_data = cursor.fetchone()
            if not member_data:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "成员不存在", "error": "MEMBER_NOT_FOUND"}
                )

            member_username = member_data[0]

            # 生成新密码的哈希值
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            # 更新密码
            cursor.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (password_hash.decode('utf-8'), member_id)
            )

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"success": False, "message": "密码重置失败", "error": "UPDATE_FAILED"}
                )

            logger.info(f"管理员 {current_user.username} 重置了用户 {member_username} (ID: {member_id}) 的密码")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "密码重置成功",
                    "data": {
                        "new_password": new_password,
                        "member_id": member_id,
                        "member_username": member_username
                    }
                }
            )

    except Exception as e:
        logger.error(f"重置密码失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "重置密码失败", "error": "INTERNAL_ERROR"}
        )


@router.post("/users/batch-update-role")
async def batch_update_user_role(request: Request):
    """批量修改成员角色API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限批量修改成员角色", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])
        role = data.get("role")

        if not user_ids or not role:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "缺少必要参数", "error": "MISSING_PARAMS"}
            )

        if role not in ["admin", "teacher", "student"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "角色必须是admin、teacher或student", "error": "INVALID_ROLE"}
            )

        with get_db() as conn:
            cursor = conn.cursor()
            updated_count = 0
            for user_id in user_ids:
                cursor.execute(
                    "UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
                    (role, datetime.now().isoformat(), user_id)
                )
                if cursor.rowcount > 0:
                    updated_count += 1

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"成功更新 {updated_count} 个成员的角色",
                "updated_count": updated_count
            }
        )

    except Exception as e:
        logger.error(f"批量修改角色失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "批量修改角色失败", "error": "INTERNAL_ERROR"}
        )


@router.post("/users/batch-update-status")
async def batch_update_user_status(request: Request):
    """批量修改成员状态API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限批量修改成员状态", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])
        status_value = data.get("status")

        if not user_ids or not status_value:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "缺少必要参数", "error": "MISSING_PARAMS"}
            )

        if status_value not in ["active", "inactive"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "状态必须是active或inactive", "error": "INVALID_STATUS"}
            )

        with get_db() as conn:
            cursor = conn.cursor()
            updated_count = 0
            for user_id in user_ids:
                cursor.execute(
                    "UPDATE users SET status = ?, updated_at = ? WHERE id = ?",
                    (status_value, datetime.now().isoformat(), user_id)
                )
                if cursor.rowcount > 0:
                    updated_count += 1

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"成功更新 {updated_count} 个成员的状态",
                "updated_count": updated_count
            }
        )

    except Exception as e:
        logger.error(f"批量修改状态失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "批量修改状态失败", "error": "INTERNAL_ERROR"}
        )


@router.post("/users/batch-delete")
async def batch_delete_users(request: Request):
    """批量删除成员API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限批量删除成员", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])

        if not user_ids:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "缺少要删除的成员ID", "error": "MISSING_USER_IDS"}
            )

        with get_db() as conn:
            cursor = conn.cursor()
            deleted_count = 0
            for user_id in user_ids:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                if cursor.rowcount > 0:
                    deleted_count += 1

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"成功删除 {deleted_count} 个成员",
                "deleted_count": deleted_count
            }
        )

    except Exception as e:
        logger.error(f"批量删除失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "批量删除失败", "error": "INTERNAL_ERROR"}
        )