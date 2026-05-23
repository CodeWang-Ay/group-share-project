"""
会话管理模块
提供用户会话的创建、验证和管理功能
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import secrets
import json
import logging
from pathlib import Path

# 配置日志记录器
logger = logging.getLogger(__name__)


class SessionManager:
    """
    会话管理器
    负责用户会话的创建、存储、验证和销毁
    """

    def __init__(self, use_file_storage=False):
        """
        初始化会话管理器

        Args:
            use_file_storage: 是否使用文件存储（生产环境为True，开发环境为False）
        """
        self.use_file_storage = use_file_storage
        self.session_file = Path(__file__).parent.parent / "data" / "sessions.json"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        if self.use_file_storage:
            self.sessions = self._load_sessions()
        else:
            # 开发环境使用内存存储，服务重启后清空session
            self.sessions = {}
            print("开发模式：Session使用内存存储，服务重启后将清空所有会话")

    def _load_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        从文件加载会话数据

        Returns:
            Dict[str, Dict[str, Any]]: 会话数据字典
        """
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    sessions = json.load(f)
                    logger.info(f"成功加载会话数据: {len(sessions)} 个活跃会话")
                    return sessions
            else:
                logger.info("会话文件不存在，创建空会话字典")
        except Exception as e:
            logger.error(f"加载会话数据时发生错误: {str(e)}")
        return {}

    def _save_sessions(self) -> None:
        """保存会话数据到文件"""
        if not self.use_file_storage:
            # 内存模式不需要保存到文件
            return

        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
                logger.debug(f"成功保存会话数据: {len(self.sessions)} 个活跃会话")
        except Exception as e:
            logger.error(f"保存会话数据时发生错误: {str(e)}")

    def create_session(self, user_id: int, username: str, role: str, remember_me: bool = False) -> str:
        """
        创建新会话

        Args:
            user_id: 用户ID
            username: 用户名
            role: 用户角色
            remember_me: 是否记住登录状态

        Returns:
            str: 会话令牌
        """
        session_token = secrets.token_urlsafe(32)
        now = datetime.now()

        # 根据记住我选项设置不同的过期时间
        if remember_me:
            expires_at = now + timedelta(days=30)  # 记住我：30天过期
            timeout_hours = 720
        else:
            expires_at = now + timedelta(hours=24)  # 默认：24小时过期
            timeout_hours = 24

        self.sessions[session_token] = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_accessed": now.isoformat(),
            "remember_me": remember_me,
            "timeout_hours": timeout_hours
        }

        self._save_sessions()
        logger.info(f"创建新会话: 用户={username}({role}), 记住我={remember_me}, 令牌={session_token[:20]}..., 过期时间={expires_at}")
        return session_token

    def validate_session(self, session_token: str, auto_refresh: bool = True) -> Optional[Dict[str, Any]]:
        """
        验证会话令牌

        Args:
            session_token: 会话令牌
            auto_refresh: 是否自动刷新会话过期时间

        Returns:
            Optional[Dict[str, Any]]: 验证成功返回会话信息，失败返回None
        """
        if not session_token or session_token not in self.sessions:
            return None

        session = self.sessions[session_token]
        now = datetime.now()
        expires_at = datetime.fromisoformat(session["expires_at"])

        # 检查会话是否过期
        if now > expires_at:
            logger.info(f"会话已过期: 令牌={session_token[:20]}..., 用户={session.get('username', 'unknown')}")
            self.destroy_session(session_token)
            return None

        # 检查是否即将过期（剩余时间不足1小时）
        time_remaining = expires_at - now
        is_near_expiry = time_remaining.total_seconds() < 3600  # 1小时

        # 自动刷新会话过期时间（如果启用且不是记住我会话）
        if auto_refresh and not session.get("remember_me", False) and is_near_expiry:
            new_expires_at = now + timedelta(hours=session.get("timeout_hours", 24))
            session["expires_at"] = new_expires_at.isoformat()
            logger.info(f"会话已自动刷新: 令牌={session_token[:20]}..., 新过期时间={new_expires_at}")

        # 更新最后访问时间
        session["last_accessed"] = now.isoformat()
        self._save_sessions()

        # 添加会话状态信息
        session["is_near_expiry"] = is_near_expiry
        session["time_remaining_seconds"] = int(time_remaining.total_seconds())

        return session

    def destroy_session(self, session_token: str) -> bool:
        """
        销毁会话

        Args:
            session_token: 会话令牌

        Returns:
            bool: 是否成功销毁
        """
        if session_token in self.sessions:
            del self.sessions[session_token]
            self._save_sessions()
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """
        清理过期的会话

        Returns:
            int: 清理的会话数量
        """
        now = datetime.now()
        expired_tokens = []

        for token, session in self.sessions.items():
            expires_at = datetime.fromisoformat(session["expires_at"])
            if now > expires_at:
                expired_tokens.append(token)
                logger.debug(f"清理过期会话: 令牌={token[:20]}..., 用户={session.get('username', 'unknown')}")

        for token in expired_tokens:
            del self.sessions[token]

        if expired_tokens:
            self._save_sessions()
            logger.info(f"已清理 {len(expired_tokens)} 个过期会话")

        return len(expired_tokens)

    def get_session_timeout_warning(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        获取会话超时警告信息

        Args:
            session_token: 会话令牌

        Returns:
            Optional[Dict[str, Any]]: 警告信息，无警告返回None
        """
        if not session_token or session_token not in self.sessions:
            return None

        session = self.sessions[session_token]
        now = datetime.now()
        expires_at = datetime.fromisoformat(session["expires_at"])
        time_remaining = expires_at - now
        remaining_seconds = int(time_remaining.total_seconds())

        # 会话已过期
        if remaining_seconds <= 0:
            return {
                "warning_type": "expired",
                "message": "会话已过期，请重新登录",
                "remaining_seconds": 0
            }

        # 即将过期（剩余时间不足15分钟）
        if remaining_seconds < 900:  # 15分钟
            return {
                "warning_type": "near_expiry",
                "message": f"会话将在 {remaining_seconds // 60} 分钟后过期",
                "remaining_seconds": remaining_seconds,
                "minutes_remaining": remaining_seconds // 60
            }

        # 无警告
        return None

    def refresh_session(self, session_token: str) -> bool:
        """
        手动刷新会话过期时间

        Args:
            session_token: 会话令牌

        Returns:
            bool: 是否成功刷新
        """
        if not session_token or session_token not in self.sessions:
            return False

        session = self.sessions[session_token]
        now = datetime.now()

        # 计算新的过期时间
        timeout_hours = session.get("timeout_hours", 24)
        new_expires_at = now + timedelta(hours=timeout_hours)

        session["expires_at"] = new_expires_at.isoformat()
        session["last_accessed"] = now.isoformat()

        self._save_sessions()
        logger.info(f"会话已手动刷新: 令牌={session_token[:20]}..., 用户={session.get('username', 'unknown')}, 新过期时间={new_expires_at}")

        return True

    def get_user_sessions(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """
        获取用户的所有会话

        Args:
            user_id: 用户ID

        Returns:
            Dict[str, Dict[str, Any]]: 用户的会话字典
        """
        user_sessions = {}
        for token, session in self.sessions.items():
            if session["user_id"] == user_id:
                user_sessions[token] = session
        return user_sessions

    def destroy_user_sessions(self, user_id: int) -> int:
        """
        销毁用户的所有会话

        Args:
            user_id: 用户ID

        Returns:
            int: 销毁的会话数量
        """
        tokens_to_remove = []
        for token, session in self.sessions.items():
            if session["user_id"] == user_id:
                tokens_to_remove.append(token)

        for token in tokens_to_remove:
            del self.sessions[token]

        if tokens_to_remove:
            self._save_sessions()

        return len(tokens_to_remove)

    def clear_all_sessions(self) -> int:
        """
        清空所有会话（开发环境调试用）

        Returns:
            int: 清理的会话数量
        """
        count = len(self.sessions)
        self.sessions = {}
        if self.use_file_storage:
            self._save_sessions()
        logger.info(f"已清空所有会话: {count} 个会话被清除")
        return count


# 全局会话管理器实例
# 开发环境使用内存存储（服务重启后清空session）
# 生产环境可以通过环境变量SESSION_USE_FILE_STORAGE=true启用文件存储
import os
USE_FILE_STORAGE = os.getenv("SESSION_USE_FILE_STORAGE", "false").lower() == "true"
session_manager = SessionManager(use_file_storage=USE_FILE_STORAGE)