"""
================================================================================
用户数据访问模块 (repositories/user_repository.py)
================================================================================

模块名称: backend/repositories/user_repository.py
功能描述: 用户数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - get_by_id(user_id)           : 根据ID获取用户
    - get_profile(user_id)         : 获取用户详细资料
    - update_profile(user_id, data): 更新用户资料
    - update_avatar(user_id, url)  : 更新用户头像

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional, Dict, Any
from database.connection import get_db


class UserProfileRepository:
    """用户数据访问类"""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户基础信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, role, created_at, updated_at FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_profile(user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户详细资料"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, role, created_at, updated_at, email, phone,
                       student_id, research_direction, status, graduation_status,
                       supervisor, degree_type, work_location, work_company,
                       personal_bio, personal_homepage, gender, id_card, bank_card, avatar
                FROM users WHERE id = ?
            """, (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

    @staticmethod
    def update_profile(user_id: int, data: Dict[str, Any]) -> bool:
        """更新用户资料"""
        with get_db() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{field} = ?" for field in data.keys()])
            values = list(data.values()) + [user_id]
            cursor.execute(
                f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_avatar(user_id: int, avatar_url: str) -> bool:
        """更新用户头像"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET avatar = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (avatar_url, user_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def check_username_exists(username: str, exclude_id: Optional[int] = None) -> bool:
        """检查用户名是否存在"""
        with get_db() as conn:
            cursor = conn.cursor()
            if exclude_id:
                cursor.execute(
                    "SELECT id FROM users WHERE username = ? AND id != ?",
                    (username, exclude_id)
                )
            else:
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is not None

    @staticmethod
    def check_email_exists(email: str) -> bool:
        """检查邮箱是否存在"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            return cursor.fetchone() is not None