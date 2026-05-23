"""
================================================================================
组会数据访问模块 (repositories/meeting_repository.py)
================================================================================

模块名称: backend/repositories/meeting_repository.py
功能描述: 组会数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - create(data)                          : 创建组会
    - get_by_id(meeting_id)                 : 根据ID获取组会
    - get_list(filters, limit, offset)      : 获取组会列表
    - get_count(filters)                    : 获取组会总数
    - update(meeting_id, data)              : 更新组会信息
    - delete(meeting_id)                    : 删除组会
    - get_stats(created_by)                 : 获取统计信息
    - auto_update_status()                  : 自动更新状态

汇报人相关:
    - get_presenters(meeting_id)            : 获取汇报人列表
    - get_presenter_by_id(presenter_id)     : 获取汇报人详情
    - add_presenter(meeting_id, user_id, presenter_type, duration_minutes): 添加汇报人
    - remove_presenter(presenter_id)        : 移除汇报人
    - update_presenter_status(meeting_id, status): 更新汇报人状态
    - check_presenter_exists(meeting_id, user_id): 检查汇报人是否存在
    - get_presenter_files(presenter_id)     : 获取汇报人文件

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from database.connection import get_db


class MeetingRepository:
    """组会数据访问类"""

    @staticmethod
    def create(data: Dict[str, Any]) -> int:
        """创建组会，返回组会ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meetings (
                    title, meeting_type, description, location, is_online, online_link,
                    scheduled_at, duration_total, material_required, material_deadline,
                    notes, minutes, status, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?)
            """, (
                data.get('title'), data.get('meeting_type'), data.get('description'),
                data.get('location'), data.get('is_online', False), data.get('online_link'),
                data.get('scheduled_at'), data.get('duration_total', 60),
                data.get('material_required', True), data.get('material_deadline'),
                data.get('notes'), data.get('minutes'), data.get('created_by')
            ))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(meeting_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取组会"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, meeting_type, description, location, is_online, online_link,
                       scheduled_at, duration_total, material_required, material_deadline,
                       notes, minutes, status, created_by, created_at, updated_at
                FROM meetings WHERE id = ?
            """, (meeting_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_list(filters: Dict[str, Any], limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """获取组会列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            where_conditions = []
            params = []

            if filters.get('status'):
                where_conditions.append("status = ?")
                params.append(filters.get('status'))

            if filters.get('meeting_type'):
                where_conditions.append("meeting_type = ?")
                params.append(filters.get('meeting_type'))

            if filters.get('created_by'):
                where_conditions.append("created_by = ?")
                params.append(filters.get('created_by'))

            if filters.get('search'):
                where_conditions.append("title LIKE ?")
                params.append(f"%{filters.get('search')}%")

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"""
                SELECT id, title, meeting_type, description, location, is_online, online_link,
                       scheduled_at, duration_total, material_required, material_deadline,
                       notes, minutes, status, created_by, created_at, updated_at
                FROM meetings {where_clause}
                ORDER BY scheduled_at DESC LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [limit, offset])
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_count(filters: Dict[str, Any]) -> int:
        """获取组会总数"""
        with get_db() as conn:
            cursor = conn.cursor()
            where_conditions = []
            params = []

            if filters.get('status'):
                where_conditions.append("status = ?")
                params.append(filters.get('status'))

            if filters.get('meeting_type'):
                where_conditions.append("meeting_type = ?")
                params.append(filters.get('meeting_type'))

            if filters.get('created_by'):
                where_conditions.append("created_by = ?")
                params.append(filters.get('created_by'))

            if filters.get('search'):
                where_conditions.append("title LIKE ?")
                params.append(f"%{filters.get('search')}%")

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            query = f"SELECT COUNT(*) FROM meetings {where_clause}"
            cursor.execute(query, params)
            return cursor.fetchone()[0] or 0

    @staticmethod
    def update(meeting_id: int, data: Dict[str, Any]) -> bool:
        """更新组会信息"""
        allowed_fields = [
            'title', 'meeting_type', 'description', 'location', 'is_online',
            'online_link', 'scheduled_at', 'duration_total', 'material_required',
            'material_deadline', 'notes', 'minutes', 'status'
        ]

        update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}
        if not update_data:
            return False

        with get_db() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{field} = ?" for field in update_data.keys()])
            values = list(update_data.values()) + [datetime.now().isoformat(), meeting_id]
            cursor.execute(f"""
                UPDATE meetings SET {set_clause}, updated_at = ? WHERE id = ?
            """, values)
            return cursor.rowcount > 0

    @staticmethod
    def delete(meeting_id: int) -> bool:
        """删除组会（级联删除关联数据）"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meeting_files WHERE meeting_id = ?", (meeting_id,))
            cursor.execute("DELETE FROM meeting_presenters WHERE meeting_id = ?", (meeting_id,))
            cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_stats(created_by: Optional[int] = None) -> Dict[str, Any]:
        """获取组会统计信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            where_clause = "WHERE created_by = ?" if created_by else ""
            params = [created_by] if created_by else []

            cursor.execute(f"SELECT COUNT(*) FROM meetings {where_clause}", params)
            total_meetings = cursor.fetchone()[0] or 0

            cursor.execute(f"""
                SELECT status, COUNT(*) FROM meetings {where_clause} GROUP BY status
            """, params)
            status_counts = dict(cursor.fetchall())

            if where_clause:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM meetings
                    {where_clause} AND scheduled_at >= date('now', 'start of month')
                """, params)
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM meetings
                    WHERE scheduled_at >= date('now', 'start of month')
                """)
            this_month_meetings = cursor.fetchone()[0] or 0

            return {
                'total_meetings': total_meetings,
                'scheduled_count': status_counts.get('scheduled', 0),
                'ongoing_count': status_counts.get('ongoing', 0),
                'completed_count': status_counts.get('completed', 0),
                'this_month_meetings': this_month_meetings
            }

    @staticmethod
    def auto_update_status() -> int:
        """根据日期自动更新组会状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            today = date.today().isoformat()
            now = datetime.now().isoformat()

            cursor.execute("""
                UPDATE meetings SET status = 'completed', updated_at = ?
                WHERE status IN ('scheduled', 'ongoing') AND DATE(scheduled_at) < ?
            """, (now, today))
            past_updated = cursor.rowcount

            cursor.execute("""
                UPDATE meetings SET status = 'ongoing', updated_at = ?
                WHERE status = 'scheduled' AND DATE(scheduled_at) = ?
            """, (now, today))
            today_updated = cursor.rowcount

            return past_updated + today_updated

    @staticmethod
    def get_presenters(meeting_id: int) -> List[Dict[str, Any]]:
        """获取汇报人列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mp.id, mp.meeting_id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                       mp.material_required, mp.status, mp.material_status, mp.created_at, mp.updated_at,
                       u.username, u.role, u.research_direction
                FROM meeting_presenters mp
                LEFT JOIN users u ON mp.user_id = u.id
                WHERE mp.meeting_id = ? ORDER BY mp.created_at ASC
            """, (meeting_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_presenter_by_id(presenter_id: int) -> Optional[Dict[str, Any]]:
        """获取汇报人详情"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mp.id, mp.meeting_id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                       mp.material_required, mp.status, mp.material_status, mp.created_at, mp.updated_at,
                       u.username, u.role, u.research_direction
                FROM meeting_presenters mp
                LEFT JOIN users u ON mp.user_id = u.id
                WHERE mp.id = ?
            """, (presenter_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_presenter_files(presenter_id: int) -> List[Dict[str, Any]]:
        """获取汇报人文件列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_type, file_size, uploaded_at
                FROM meeting_files WHERE presenter_id = ? AND filename IS NOT NULL
            """, (presenter_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def add_presenter(meeting_id: int, user_id: int, presenter_type: str, duration_minutes: int) -> int:
        """添加汇报人，返回汇报人ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meeting_presenters (meeting_id, user_id, presenter_type, duration_minutes, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (meeting_id, user_id, presenter_type, duration_minutes))
            return cursor.lastrowid

    @staticmethod
    def remove_presenter(presenter_id: int, meeting_id: int) -> bool:
        """移除汇报人"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meeting_presenters WHERE id = ? AND meeting_id = ?", (presenter_id, meeting_id))
            return cursor.rowcount > 0

    @staticmethod
    def check_presenter_exists(meeting_id: int, user_id: int) -> bool:
        """检查汇报人是否已存在"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM meeting_presenters WHERE meeting_id = ? AND user_id = ?", (meeting_id, user_id))
            return cursor.fetchone() is not None

    @staticmethod
    def update_presenter_status(meeting_id: int, status: str) -> int:
        """批量更新汇报人状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE meeting_presenters SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ? AND status = 'confirmed'
            """, (status, meeting_id))
            return cursor.rowcount

    @staticmethod
    def update_presenter_material_status(meeting_id: int, status: str) -> int:
        """批量更新汇报人材料状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE meeting_presenters SET material_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ? AND material_status = 'submitted'
            """, (status, meeting_id))
            return cursor.rowcount

    @staticmethod
    def reset_presenter_material_status(meeting_id: int) -> int:
        """重置汇报人材料状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE meeting_presenters SET material_status = 'pending', updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ?
            """, (meeting_id,))
            return cursor.rowcount

    @staticmethod
    def get_meeting_creator(meeting_id: int) -> Optional[int]:
        """获取组会创建者ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT created_by FROM meetings WHERE id = ?", (meeting_id,))
            row = cursor.fetchone()
            return row[0] if row else None