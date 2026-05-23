"""
================================================================================
用户业务服务模块 (services/user_service.py)
================================================================================

模块名称: backend/services/user_service.py
功能描述: 用户业务逻辑处理

Service 类方法:
    - get_profile(user_id)       : 获取用户资料
    - update_profile(user_id, data): 更新用户资料
    - upload_avatar(user_id, file): 上传头像

职责:
    - 处理业务逻辑
    - 调用 Repository 进行数据操作
    - 数据转换和验证

依赖:
    - repositories.user_repository: 数据访问层
    - config.Config.UPLOAD_DIR    : 上传目录

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Dict, Any, Optional
from pathlib import Path
import time
from loguru import logger

from repositories.user_repository import UserRepository
from config import Config


class UserService:
    """用户业务服务类"""

    @staticmethod
    def get_profile(user_id: int) -> Dict[str, Any]:
        """获取用户资料"""
        profile = UserRepository.get_profile(user_id)
        if not profile:
            raise ValueError("用户不存在")
        return profile

    @staticmethod
    def update_profile(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户资料"""
        # 允许更新的字段
        allowed_fields = [
            'email', 'phone', 'student_id', 'research_direction',
            'graduation_status', 'supervisor', 'degree_type',
            'work_location', 'work_company', 'personal_bio',
            'personal_homepage', 'gender', 'id_card', 'bank_card'
        ]

        # 过滤允许更新的字段
        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

        if not update_data:
            raise ValueError("没有提供要更新的数据")

        success = UserRepository.update_profile(user_id, update_data)
        if not success:
            raise ValueError("用户不存在")

        logger.info(f"用户资料更新成功: user_id={user_id}")
        return update_data

    @staticmethod
    def upload_avatar(user_id: int, file) -> Dict[str, Any]:
        """上传用户头像"""
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            raise ValueError("只支持 JPG、PNG、GIF、WEBP 格式")

        # 验证文件大小
        file_data = file.file.read()
        if len(file_data) > 5 * 1024 * 1024:
            raise ValueError("头像图片大小不能超过5MB")

        # 生成文件名
        timestamp = int(time.time())
        file_ext = Path(file.filename).suffix.lower() or '.jpg'
        avatar_filename = f"avatar_{user_id}_{timestamp}{file_ext}"

        # 创建存储目录
        avatars_dir = Config.UPLOAD_DIR / "avatars"
        avatars_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        avatar_path = avatars_dir / avatar_filename
        with open(avatar_path, 'wb') as f:
            f.write(file_data)

        # 更新数据库
        avatar_url = f"/uploads/avatars/{avatar_filename}"
        UserRepository.update_avatar(user_id, avatar_url)

        logger.info(f"头像上传成功: {avatar_url}")
        return {"avatar_url": avatar_url}