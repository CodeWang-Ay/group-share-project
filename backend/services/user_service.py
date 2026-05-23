"""
================================================================================
用户业务服务模块 (services/user_service.py)
================================================================================

模块名称: backend/services/user_service.py
功能描述: 用户业务逻辑处理，返回完整响应数据

Service 类方法:
    - get_profile(user_id)         : 获取用户资料（返回响应数据）
    - update_profile(user_id, data): 更新用户资料（返回响应数据）
    - upload_avatar(user_id, form) : 上传头像（返回响应数据）

职责:
    - 所有业务逻辑写在这里
    - 返回完整响应数据（status_code, content）
    - 调用 Repository 进行数据操作

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Dict, Any
from pathlib import Path
import time
from loguru import logger

from repositories.user_repository import UserRepository
from config import Config


class UserService:
    """用户业务服务类"""

    async def get_profile(self, user_id: int) -> Dict[str, Any]:
        """获取用户资料"""
        profile = UserRepository.get_profile(user_id)
        if not profile:
            return {"status_code": 404, "content": {"success": False, "message": "用户不存在", "error": "USER_NOT_FOUND"}}
        return {"status_code": 200, "content": {"success": True, "data": profile}}

    async def update_profile(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户资料"""
        allowed_fields = ['email', 'phone', 'student_id', 'research_direction', 'graduation_status', 'supervisor',
                          'degree_type', 'work_location', 'work_company', 'personal_bio', 'personal_homepage',
                          'gender', 'id_card', 'bank_card']

        update_data = {field: data[field] for field in allowed_fields if field in data}

        if not update_data:
            return {"status_code": 400, "content": {"success": False, "message": "没有提供要更新的数据", "error": "NO_DATA"}}

        success = UserRepository.update_profile(user_id, update_data)
        if not success:
            return {"status_code": 404, "content": {"success": False, "message": "用户不存在", "error": "USER_NOT_FOUND"}}

        logger.info(f"用户资料更新成功: user_id={user_id}")
        return {"status_code": 200, "content": {"success": True, "message": "个人资料更新成功", "data": update_data}}

    async def upload_avatar(self, user_id: int, form: Dict[str, Any]) -> Dict[str, Any]:
        """上传用户头像"""
        file = form.get("avatar")
        if not file:
            return {"status_code": 400, "content": {"success": False, "message": "请选择要上传的头像图片", "error": "NO_FILE"}}

        # 1. 文件类型验证
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            return {"status_code": 400, "content": {"success": False, "message": "只支持 JPG、PNG、GIF、WEBP 格式", "error": "INVALID_TYPE"}}

        # 2. 文件大小验证
        file_data = file.file.read()
        if len(file_data) > 5 * 1024 * 1024:
            return {"status_code": 400, "content": {"success": False, "message": "头像图片大小不能超过5MB", "error": "FILE_TOO_LARGE"}}

        # 3. 保存文件
        timestamp = int(time.time())
        file_ext = Path(file.filename).suffix.lower() or '.jpg'
        avatar_filename = f"avatar_{user_id}_{timestamp}{file_ext}"

        avatars_dir = Config.UPLOAD_DIR / "avatars"
        avatars_dir.mkdir(parents=True, exist_ok=True)

        with open(avatars_dir / avatar_filename, 'wb') as f:
            f.write(file_data)

        # 4. 更新数据库
        avatar_url = f"/uploads/avatars/{avatar_filename}"
        UserRepository.update_avatar(user_id, avatar_url)

        logger.info(f"头像上传成功: {avatar_url}")
        return {"status_code": 200, "content": {"success": True, "message": "头像上传成功", "data": {"avatar_url": avatar_url}}}