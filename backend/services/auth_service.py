"""
================================================================================
认证业务服务模块 (services/auth_service.py)
================================================================================

模块名称: backend/services/auth_service.py
功能描述: 认证业务逻辑处理，返回完整响应数据

Service 类方法:
    - login(data)                        : 用户登录（返回响应数据）
    - register(data)                     : 用户注册（返回响应数据）
    - logout(request)                    : 用户登出（返回响应数据）
    - get_user_info(request, user)       : 获取用户信息（返回响应数据）
    - change_password(user_id, data)     : 修改密码（返回响应数据）
    - refresh_session(request)           : 刷新会话（返回响应数据）
    - check_session_status(request)      : 检查会话状态（返回响应数据）

职责:
    - 所有业务逻辑写在这里
    - 返回完整响应数据（status_code, content）
    - 调用 Repository 进行数据操作

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
import bcrypt
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request
from loguru import logger

from repositories.auth_repository import AuthRepository
from models.user import User
from services.session_service import session_manager


class AuthService:
    """认证业务服务类"""

    # ==================== Repository 层调用 ====================

    @staticmethod
    def _hash_password(password: str) -> str:
        """密码哈希"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        """密码验证"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def _get_session_token(request: Request) -> str:
        """获取会话令牌"""
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token[7:]
        return token or request.cookies.get("session_token") or ""

    # ==================== 业务逻辑 ====================

    async def login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        用户登录
        返回: {"status_code": int, "content": dict, "redirect": str, "cookie": dict}
        """
        username = data.get("username")
        password = data.get("password")
        remember_me = data.get("remember_me", False)

        # 1. 参数验证
        if not username or not password:
            return {"status_code": 400, "content": {"success": False, "message": "请输入用户名和密码", "error": "VALIDATION_ERROR"}}

        # 2. 用户认证
        user_data = AuthRepository.get_user_by_username(username)
        if not user_data or not self._verify_password(password, user_data['password_hash']):
            logger.warning(f"登录失败: {username}")
            return {"status_code": 401, "content": {"success": False, "message": "用户名或密码错误", "error": "INVALID_CREDENTIALS"}}

        user = User.from_dict(user_data)

        # 3. 创建会话
        session_token = session_manager.create_session(user.id, user.username, user.role, remember_me)
        logger.info(f"登录成功: {user.username}")

        # 4. 返回登录成功响应（不再重定向，由前端处理）
        return {
            "success": True,
            "status_code": 200,
            "redirect": f"/?session_token={session_token}",
            "cookie": {
                "key": "session_token",
                "value": session_token,
                "max_age": 86400 if not remember_me else 604800,
                "httponly": True,
                "samesite": "lax"
            },
            "content": {"success": True, "message": "登录成功", "session_token": session_token}
        }

    async def register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        用户注册
        返回: {"status_code": int, "content": dict}
        """
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        role = data.get("role", "").strip()

        # 1. 必填验证
        if not username or not password or not role:
            return {"status_code": 400, "content": {"success": False, "message": "请填写完整的注册信息", "error": "VALIDATION_ERROR"}}

        # 2. 角色验证
        if role not in ["teacher", "student"]:
            return {"status_code": 400, "content": {"success": False, "message": "注册角色无效", "error": "VALIDATION_ERROR"}}

        # 3. 用户名格式验证
        if not User.is_valid_username(username):
            return {"status_code": 400, "content": {"success": False, "message": "用户名格式不正确", "error": "VALIDATION_ERROR"}}

        # 4. 密码长度验证
        if len(password) < 6:
            return {"status_code": 400, "content": {"success": False, "message": "密码长度至少为6位", "error": "VALIDATION_ERROR"}}

        # 5. 用户名唯一性验证
        if AuthRepository.check_username_exists(username):
            return {"status_code": 400, "content": {"success": False, "message": "用户名已存在", "error": "USERNAME_EXISTS"}}

        # 6. 创建用户
        password_hash = self._hash_password(password)
        now = datetime.now().isoformat()
        create_data = {
            'username': username,
            'password_hash': password_hash,
            'role': role,
            'email': data.get('email'),
            'gender': data.get('gender'),
            'phone': data.get('phone'),
            'degree_type': data.get('degree_type'),
            'created_at': now,
            'updated_at': now
        }
        user_id = AuthRepository.create_user(create_data)

        # 7. 构建用户对象
        user = User(id=user_id, username=username, role=role, email=data.get('email'), created_at=datetime.now(), updated_at=datetime.now())
        logger.info(f"注册成功: {username}")

        return {"status_code": 201, "content": {"success": True, "message": "注册成功", "data": {"user": user.to_dict()}}}

    async def logout(self, request: Request) -> Dict[str, Any]:
        """
        用户登出
        返回: {"status_code": int, "content": dict}
        """
        session_token = self._get_session_token(request)
        if session_token:
            session_manager.destroy_session(session_token)
        return {"status_code": 200, "content": {"success": True, "message": "登出成功"}}

    async def get_user_info(self, request: Request, current_user: Optional[User]) -> Dict[str, Any]:
        """
        获取当前用户信息
        返回: {"status_code": int, "content": dict}
        """
        if not current_user:
            return {"status_code": 401, "content": {"success": False, "message": "未登录", "error": "NOT_AUTHENTICATED"}}

        session_token = self._get_session_token(request)
        session = session_manager.validate_session(session_token) if session_token else None

        if not session:
            return {"status_code": 401, "content": {"success": False, "message": "会话已过期", "error": "SESSION_EXPIRED"}}

        timeout_warning = session_manager.get_session_timeout_warning(session_token)
        response_data = {
            "user": current_user.to_dict(),
            "session": {"is_near_expiry": session.get("is_near_expiry", False), "time_remaining_seconds": session.get("time_remaining_seconds", 0)}
        }
        if timeout_warning:
            response_data["timeout_warning"] = timeout_warning

        return {"status_code": 200, "content": {"success": True, "data": response_data}}

    async def change_password(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        修改密码
        返回: {"status_code": int, "content": dict}
        """
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        # 1. 必填验证
        if not old_password or not new_password or not confirm_password:
            return {"status_code": 400, "content": {"success": False, "message": "请填写完整的密码信息", "error": "VALIDATION_ERROR"}}

        # 2. 密码长度验证
        if len(new_password) < 6:
            return {"status_code": 400, "content": {"success": False, "message": "新密码长度至少为6位", "error": "PASSWORD_TOO_SHORT"}}

        # 3. 密码一致性验证
        if new_password != confirm_password:
            return {"status_code": 400, "content": {"success": False, "message": "新密码与确认密码不一致", "error": "PASSWORD_MISMATCH"}}

        # 4. 新旧密码验证
        if old_password == new_password:
            return {"status_code": 400, "content": {"success": False, "message": "新密码不能与当前密码相同", "error": "SAME_PASSWORD"}}

        # 5. 验证旧密码
        user_data = AuthRepository.get_user_by_id(user_id)
        if not user_data or not self._verify_password(old_password, user_data['password_hash']):
            return {"status_code": 400, "content": {"success": False, "message": "当前密码不正确", "error": "INVALID_OLD_PASSWORD"}}

        # 6. 更新密码
        password_hash = self._hash_password(new_password)
        AuthRepository.update_password(user_id, password_hash)

        logger.info(f"密码修改成功: user_id={user_id}")
        return {"status_code": 200, "content": {"success": True, "message": "密码修改成功，请使用新密码登录"}}

    async def refresh_session(self, request: Request) -> Dict[str, Any]:
        """
        刷新会话
        返回: {"status_code": int, "content": dict}
        """
        session_token = self._get_session_token(request)
        if not session_token:
            return {"status_code": 401, "content": {"success": False, "message": "未登录", "error": "NOT_AUTHENTICATED"}}

        success = session_manager.refresh_session(session_token)
        if not success:
            return {"status_code": 401, "content": {"success": False, "message": "会话无效", "error": "INVALID_SESSION"}}

        return {"status_code": 200, "content": {"success": True, "message": "会话已刷新"}}

    async def check_session_status(self, request: Request) -> Dict[str, Any]:
        """
        检查会话状态
        返回: {"status_code": int, "content": dict}
        """
        session_token = self._get_session_token(request)
        if not session_token:
            return {"status_code": 200, "content": {"success": True, "data": {"authenticated": False, "message": "未登录"}}}

        session = session_manager.validate_session(session_token)
        if not session:
            return {"status_code": 200, "content": {"success": True, "data": {"authenticated": False, "message": "会话已过期"}}}

        timeout_warning = session_manager.get_session_timeout_warning(session_token)
        response_data = {
            "authenticated": True,
            "session": {
                "username": session.get("username"),
                "role": session.get("role"),
                "is_near_expiry": session.get("is_near_expiry", False),
                "time_remaining_seconds": session.get("time_remaining_seconds", 0),
                "remember_me": session.get("remember_me", False)
            }
        }
        if timeout_warning:
            response_data["timeout_warning"] = timeout_warning

        return {"status_code": 200, "content": {"success": True, "data": response_data}}