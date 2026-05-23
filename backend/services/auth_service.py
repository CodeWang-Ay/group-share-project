"""
认证服务模块
提供密码哈希、用户验证等认证相关功能
"""

import bcrypt
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import secrets
from models.user import User
from database.connection import get_db

# 配置日志记录器
logger = logging.getLogger(__name__)


class AuthService:
    """
    认证服务类
    提供用户认证相关的核心功能
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        对密码进行哈希处理

        Args:
            password: 明文密码

        Returns:
            str: 密码哈希值
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        验证密码是否正确

        Args:
            password: 明文密码
            hashed: 密码哈希值

        Returns:
            bool: 密码是否正确
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """
        验证用户凭据

        Args:
            username: 用户名
            password: 明文密码

        Returns:
            Optional[User]: 验证成功返回用户对象，失败返回None
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, password_hash, role, created_at, updated_at "
                    "FROM users WHERE username = ?",
                    (username,)
                )
                user_row = cursor.fetchone()

                if not user_row:
                    logger.warning(f"用户认证失败: 用户名不存在 - {username}")
                    return None

                user = User.from_dict(dict(user_row))

                if AuthService.verify_password(password, user.password_hash):
                    logger.info(f"用户认证成功: {username} ({user.role})")
                    return user
                else:
                    logger.warning(f"用户认证失败: 密码错误 - {username}")
                    return None
        except Exception as e:
            logger.error(f"用户认证过程中发生错误: 用户名={username}, 错误={str(e)}")
            return None

    @staticmethod
    def create_session_token() -> str:
        """
        创建会话令牌

        Returns:
            str: 随机会话令牌
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_username(username: str) -> bool:
        """
        验证用户名格式

        Args:
            username: 用户名

        Returns:
            bool: 用户名是否有效
        """
        return User.is_valid_username(username)

    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """
        验证密码强度

        Args:
            password: 密码

        Returns:
            Dict[str, Any]: 验证结果
        """
        result = {
            "valid": True,
            "errors": []
        }

        if len(password) < 6:
            result["valid"] = False
            result["errors"].append("密码长度至少为6位")

        if len(password) > 100:
            result["valid"] = False
            result["errors"].append("密码长度不能超过100位")

        return result

    @staticmethod
    def check_username_exists(username: str) -> bool:
        """
        检查用户名是否已存在

        Args:
            username: 用户名

        Returns:
            bool: 用户名是否已存在
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                exists = cursor.fetchone() is not None
                logger.debug(f"检查用户名是否存在: {username} -> {exists}")
                return exists
        except Exception as e:
            logger.error(f"检查用户名是否存在时发生错误: 用户名={username}, 错误={str(e)}")
            return False