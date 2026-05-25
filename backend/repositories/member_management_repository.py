"""
================================================================================
成员数据访问模块 (repositories/member_repository.py)
================================================================================

模块名称: backend/repositories/member_repository.py
功能描述: 成员管理数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - get_list(filters, offset, limit)    : 获取成员列表
    - get_count(filters)                  : 获取成员总数
    - get_stats()                         : 获取统计数据
    - get_by_id(member_id)                : 根据ID获取成员
    - create(data)                        : 创建成员
    - update(member_id, data)             : 更新成员
    - delete(member_id)                   : 删除成员
    - update_status(member_id, status)    : 更新状态
    - update_password(member_id, hash)    : 更新密码
    - batch_update_role(ids, role)        : 批量更新角色
    - batch_update_status(ids, status)    : 批量更新状态
    - batch_delete(ids)                   : 批量删除

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from database.connection import get_db


class MemberManagementRepository:
    """成员数据访问类"""

    @staticmethod
    def get_list(filters: Dict[str, Any], offset: int, limit: int) -> List[Dict[str, Any]]:
        """获取成员列表"""
        with get_db() as conn:
            cursor = conn.cursor()

            where_conditions = []
            params = []

            if filters.get('role'):
                where_conditions.append("role = ?")
                params.append(filters['role'])
            if filters.get('status'):
                where_conditions.append("status = ?")
                params.append(filters['status'])
            if filters.get('degree'):
                where_conditions.append("degree_type = ?")
                params.append(filters['degree'])
            if filters.get('search'):
                where_conditions.append("(username LIKE ? OR id LIKE ? OR student_id LIKE ? OR real_name LIKE ?)")
                search = filters['search']
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

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
            cursor.execute(query, params + [limit, offset])
            rows = cursor.fetchall()

            members = []
            for row in rows:
                member = dict(row)
                members.append(member)
            return members

    @staticmethod
    def get_count(filters: Dict[str, Any]) -> int:
        """获取成员总数"""
        with get_db() as conn:
            cursor = conn.cursor()

            where_conditions = []
            params = []

            if filters.get('role'):
                where_conditions.append("role = ?")
                params.append(filters['role'])
            if filters.get('status'):
                where_conditions.append("status = ?")
                params.append(filters['status'])
            if filters.get('degree'):
                where_conditions.append("degree_type = ?")
                params.append(filters['degree'])
            if filters.get('search'):
                where_conditions.append("(username LIKE ? OR id LIKE ? OR student_id LIKE ? OR real_name LIKE ?)")
                search = filters['search']
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            cursor.execute(f"SELECT COUNT(*) FROM users {where_clause}", params)
            return cursor.fetchone()[0]

    @staticmethod
    def get_stats() -> Dict[str, int]:
        """获取成员统计数据"""
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

            return {
                "total_members": total_members,
                "active_members": active_members,
                "student_count": student_count,
                "teacher_count": teacher_count,
                "admin_count": admin_count,
                "inactive_members": total_members - active_members
            }

    @staticmethod
    def get_by_id(member_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取成员"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users WHERE id = ?", (member_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(data: Dict[str, Any]) -> int:
        """创建成员，返回新成员ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, email, phone, student_id, role,
                    research_direction, personal_bio, gender, id_card, bank_card,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                data.get('username'),
                data.get('password_hash'),
                data.get('email'),
                data.get('phone'),
                data.get('student_id'),
                data.get('role'),
                data.get('research_direction'),
                data.get('personal_bio'),
                data.get('gender'),
                data.get('id_card'),
                data.get('bank_card')
            ))
            return cursor.lastrowid

    @staticmethod
    def update(member_id: int, data: Dict[str, Any]) -> bool:
        """更新成员信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{field} = ?" for field in data.keys()])
            values = list(data.values()) + [member_id]
            cursor.execute(
                f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete(member_id: int) -> bool:
        """删除成员"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (member_id,))
            return cursor.rowcount > 0

    @staticmethod
    def update_status(member_id: int, status: str) -> bool:
        """更新成员状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, member_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_password(member_id: int, password_hash: str) -> bool:
        """更新成员密码"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (password_hash, member_id)
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

    @staticmethod
    def check_student_id_exists(student_id: str) -> bool:
        """检查学号是否存在"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE student_id = ?", (student_id,))
            return cursor.fetchone() is not None

    @staticmethod
    def batch_update_role(user_ids: List[int], role: str) -> int:
        """批量更新角色，返回更新数量"""
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
            return updated_count

    @staticmethod
    def batch_update_status(user_ids: List[int], status: str) -> int:
        """批量更新状态，返回更新数量"""
        with get_db() as conn:
            cursor = conn.cursor()
            updated_count = 0
            for user_id in user_ids:
                cursor.execute(
                    "UPDATE users SET status = ?, updated_at = ? WHERE id = ?",
                    (status, datetime.now().isoformat(), user_id)
                )
                if cursor.rowcount > 0:
                    updated_count += 1
            return updated_count

    @staticmethod
    def batch_delete(user_ids: List[int]) -> int:
        """批量删除，返回删除数量"""
        with get_db() as conn:
            cursor = conn.cursor()
            deleted_count = 0
            for user_id in user_ids:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                if cursor.rowcount > 0:
                    deleted_count += 1
            return deleted_count