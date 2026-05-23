"""
================================================================================
认证数据访问模块 (repositories/auth_repository.py)
================================================================================

模块名称: backend/repositories/auth_repository.py
功能描述: 认证相关数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - get_user_by_username(username)    : 根据用户名获取用户
    - get_user_by_id(user_id)           : 根据ID获取用户
    - check_username_exists(username)   : 检查用户名是否存在
    - create_user(data)                 : 创建用户
    - update_password(user_id, hash)    : 更新密码

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional, Dict, Any
from database.connection import get_db


class AuthRepository:
    """认证数据访问类"""

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash, role, email, phone, "
                "student_id, research_direction, status, avatar, created_at, updated_at "
                "FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash, role, email, phone, "
                "student_id, research_direction, status, avatar, created_at, updated_at "
                "FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def check_username_exists(username: str) -> bool:
        """检查用户名是否存在"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is not None

    @staticmethod
    def create_user(data: Dict[str, Any]) -> int:
        """创建用户，返回用户ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, email, gender, phone, degree_type, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data.get('username'),
                    data.get('password_hash'),
                    data.get('role'),
                    data.get('email'),
                    data.get('gender'),
                    data.get('phone'),
                    data.get('degree_type'),
                    data.get('created_at'),
                    data.get('updated_at')
                )
            )
            return cursor.lastrowid

    @staticmethod
    def update_password(user_id: int, password_hash: str) -> bool:
        """更新用户密码"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (password_hash, user_id)
            )
            return cursor.rowcount > 0