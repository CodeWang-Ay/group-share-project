"""
用户路由
端点：
- GET  /api/user/profile
- PUT  /api/user/profile
- POST /api/user/avatar
"""
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pathlib import Path
import time
from loguru import logger

from utils.auth_helper import get_current_user
from database.connection import get_db

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.get("/profile")
async def get_user_profile(request: Request):
    """获取用户个人资料"""
    logger.info("获取用户个人资料")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, role, created_at, updated_at, email, phone,
                       student_id, research_direction, status, graduation_status,
                       supervisor, degree_type, work_location, work_company,
                       personal_bio, personal_homepage, gender, id_card, bank_card, avatar
                FROM users WHERE id = ?
            """, (current_user.id,))
            user_data = cursor.fetchone()

            if not user_data:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "用户信息不存在", "error": "USER_NOT_FOUND"}
                )

            columns = [desc[0] for desc in cursor.description]
            user_profile = dict(zip(columns, user_data))

        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "data": user_profile})

    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取用户资料失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/profile")
async def update_user_profile(request: Request):
    """更新用户个人资料"""
    logger.info("更新用户个人资料")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        allowed_fields = [
            'email', 'phone', 'student_id', 'research_direction',
            'graduation_status', 'supervisor', 'degree_type',
            'work_location', 'work_company', 'personal_bio',
            'personal_homepage', 'gender', 'id_card', 'bank_card'
        ]

        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

        if not update_data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "没有提供要更新的数据", "error": "NO_DATA"}
            )

        with get_db() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{field} = ?" for field in update_data.keys()])
            values = list(update_data.values()) + [current_user.id]
            cursor.execute(f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "用户不存在", "error": "USER_NOT_FOUND"}
                )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "个人资料更新成功", "data": update_data}
        )

    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新个人资料失败", "error": "INTERNAL_ERROR"}
        )


@router.post("/avatar")
async def upload_avatar(request: Request):
    """上传用户头像"""
    logger.info("上传用户头像")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        form = await request.form()
        file = form.get("avatar")

        if not file:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请选择要上传的头像图片", "error": "NO_FILE"}
            )

        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "只支持 JPG、PNG、GIF、WEBP 格式", "error": "UNSUPPORTED_FILE_TYPE"}
            )

        file_data = await file.read()
        if len(file_data) > 5 * 1024 * 1024:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "头像图片大小不能超过5MB", "error": "FILE_TOO_LARGE"}
            )

        timestamp = int(time.time())
        file_ext = Path(file.filename).suffix.lower() or '.jpg'
        avatar_filename = f"avatar_{current_user.id}_{timestamp}{file_ext}"

        avatars_dir = Path(__file__).parent.parent.parent / "uploads" / "avatars"
        avatars_dir.mkdir(parents=True, exist_ok=True)

        avatar_path = avatars_dir / avatar_filename
        with open(avatar_path, 'wb') as f:
            f.write(file_data)

        avatar_url = f"/uploads/avatars/{avatar_filename}"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET avatar = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (avatar_url, current_user.id))

        logger.info(f"头像上传成功: {avatar_url}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "头像上传成功", "data": {"avatar_url": avatar_url}}
        )

    except Exception as e:
        logger.error(f"上传头像失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"上传头像失败: {str(e)}", "error": "INTERNAL_ERROR"}
        )