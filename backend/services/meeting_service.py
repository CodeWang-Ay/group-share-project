"""
组会业务逻辑服务
"""
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

from database.connection import get_db
from models.meeting import Meeting, MeetingPresenter, MeetingFile
from loguru import logger


class MeetingService:
    """组会服务类"""

    # 组会类型常量
    MEETING_TYPES = ['regular', 'paper_reading', 'topic_discussion']

    # 组会状态常量
    STATUS_SCHEDULED = 'scheduled'
    STATUS_ONGOING = 'ongoing'
    STATUS_COMPLETED = 'completed'

    # 汇报人类型常量
    PRESENTER_ASSIGNED = 'assigned'
    PRESENTER_VOLUNTEERED = 'volunteered'
    PRESENTER_PENDING = 'pending'

    # 汇报人状态常量
    PRESENTER_STATUS_PENDING = 'pending'
    PRESENTER_STATUS_CONFIRMED = 'confirmed'
    PRESENTER_STATUS_COMPLETED = 'completed'

    @staticmethod
    def create_meeting(
        title: str,
        meeting_type: str,
        scheduled_at: datetime,
        created_by: int,
        description: Optional[str] = None,
        location: Optional[str] = None,
        is_online: bool = False,
        online_link: Optional[str] = None,
        duration_total: int = 60,
        material_required: bool = True,
        material_deadline: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Meeting:
        """创建组会"""
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO meetings (
                    title, meeting_type, description, location, is_online, online_link,
                    scheduled_at, duration_total, material_required, material_deadline,
                    notes, status, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                title, meeting_type, description, location, is_online, online_link,
                scheduled_at.isoformat(), duration_total, material_required,
                material_deadline.isoformat() if material_deadline else None,
                notes, created_by
            ))

            meeting_id = cursor.lastrowid

            return Meeting(
                id=meeting_id,
                title=title,
                meeting_type=meeting_type,
                description=description,
                location=location,
                is_online=is_online,
                online_link=online_link,
                scheduled_at=scheduled_at,
                duration_total=duration_total,
                material_required=material_required,
                material_deadline=material_deadline,
                notes=notes,
                status='scheduled',
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

    @staticmethod
    def get_meeting_by_id(meeting_id: int) -> Optional[Meeting]:
        """根据ID获取组会"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, meeting_type, description, location, is_online, online_link,
                       scheduled_at, duration_total, material_required, material_deadline,
                       notes, status, created_by, created_at, updated_at
                FROM meetings WHERE id = ?
            """, (meeting_id,))

            row = cursor.fetchone()
            if row:
                return Meeting.from_dict(dict(row))
            return None

    @staticmethod
    def get_meetings(
        status: Optional[str] = None,
        meeting_type: Optional[str] = None,
        created_by: Optional[int] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Meeting]:
        """获取组会列表"""
        with get_db() as conn:
            cursor = conn.cursor()

            where_conditions = []
            params = []

            if status:
                where_conditions.append("status = ?")
                params.append(status)

            if meeting_type:
                where_conditions.append("meeting_type = ?")
                params.append(meeting_type)

            if created_by:
                where_conditions.append("created_by = ?")
                params.append(created_by)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"""
                SELECT id, title, meeting_type, description, location, is_online, online_link,
                       scheduled_at, duration_total, material_required, material_deadline,
                       notes, status, created_by, created_at, updated_at
                FROM meetings
                {where_clause}
                ORDER BY scheduled_at DESC
                LIMIT ? OFFSET ?
            """

            cursor.execute(query, params + [limit, offset])
            rows = cursor.fetchall()

            return [Meeting.from_dict(dict(row)) for row in rows]

    @staticmethod
    def get_meetings_count(
        status: Optional[str] = None,
        meeting_type: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> int:
        """获取组会总数"""
        with get_db() as conn:
            cursor = conn.cursor()

            where_conditions = []
            params = []

            if status:
                where_conditions.append("status = ?")
                params.append(status)

            if meeting_type:
                where_conditions.append("meeting_type = ?")
                params.append(meeting_type)

            if created_by:
                where_conditions.append("created_by = ?")
                params.append(created_by)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"SELECT COUNT(*) FROM meetings {where_clause}"
            cursor.execute(query, params)

            return cursor.fetchone()[0]

    @staticmethod
    def update_meeting(meeting_id: int, **kwargs) -> Optional[Meeting]:
        """更新组会信息"""
        allowed_fields = [
            'title', 'meeting_type', 'description', 'location', 'is_online',
            'online_link', 'scheduled_at', 'duration_total', 'material_required',
            'material_deadline', 'notes', 'status'
        ]

        update_data = {}
        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                if field in ['scheduled_at', 'material_deadline'] and isinstance(kwargs[field], datetime):
                    update_data[field] = kwargs[field].isoformat()
                else:
                    update_data[field] = kwargs[field]

        if not update_data:
            return None

        with get_db() as conn:
            cursor = conn.cursor()

            set_clause = ", ".join([f"{field} = ?" for field in update_data.keys()])
            values = list(update_data.values()) + [meeting_id]

            cursor.execute(f"""
                UPDATE meetings SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, values)

            if cursor.rowcount == 0:
                return None

            return MeetingService.get_meeting_by_id(meeting_id)

    @staticmethod
    def delete_meeting(meeting_id: int) -> bool:
        """删除组会"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            return cursor.rowcount > 0

    @staticmethod
    def update_meeting_status(meeting_id: int, status: str) -> Optional[Meeting]:
        """更新组会状态"""
        valid_statuses = ['scheduled', 'ongoing', 'completed']
        if status not in valid_statuses:
            return None

        return MeetingService.update_meeting(meeting_id, status=status)

    @staticmethod
    def get_meeting_stats(created_by: Optional[int] = None) -> dict:
        """获取组会统计信息"""
        with get_db() as conn:
            cursor = conn.cursor()

            where_clause = "WHERE created_by = ?" if created_by else ""
            params = [created_by] if created_by else []

            # 总组会数
            cursor.execute(f"SELECT COUNT(*) FROM meetings {where_clause}", params)
            total_meetings = cursor.fetchone()[0]

            # 各状态组会数
            cursor.execute(f"""
                SELECT status, COUNT(*) FROM meetings {where_clause} GROUP BY status
            """, params)
            status_counts = dict(cursor.fetchall())

            # 本月组会数
            cursor.execute(f"""
                SELECT COUNT(*) FROM meetings
                {where_clause.replace('WHERE', 'WHERE') if where_clause else 'WHERE'}
                scheduled_at >= date('now', 'start of month')
            """, params if where_clause else [])
            this_month_meetings = cursor.fetchone()[0]

            return {
                'total_meetings': total_meetings,
                'scheduled_count': status_counts.get('scheduled', 0),
                'ongoing_count': status_counts.get('ongoing', 0),
                'completed_count': status_counts.get('completed', 0),
                'this_month_meetings': this_month_meetings
            }