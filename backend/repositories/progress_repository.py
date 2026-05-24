"""
================================================================================
研究进展数据访问模块 (repositories/progress_repository.py)
================================================================================

模块名称: backend/repositories/progress_repository.py
功能描述: 研究进展数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - create_progress(data)                 : 创建进展
    - get_by_id(progress_id)                : 获取进展详情
    - get_user_list(user_id, limit, offset, order): 获取用户进展列表
    - get_user_count(user_id)               : 获取用户进展总数
    - get_team_list(filters, limit, offset) : 获取团队进展列表
    - get_team_count(filters)               : 获取团队进展总数
    - get_stats()                           : 获取统计信息
    - update_progress(progress_id, data)    : 更新进展
    - add_feedback(progress_id, feedback, supervisor_id): 添加导师反馈
    - get_setting_by_user(user_id)          : 获取用户周期设置
    - create_or_update_setting(data)        : 创建或更新设置
    - batch_create_settings(user_ids, period_type, reminder_days, created_by): 批量创建设置
    - get_all_settings()                    : 获取所有设置

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-24
================================================================================
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from database.connection import get_db


class ProgressRepository:
    """研究进展数据访问类"""

    @staticmethod
    def create_progress(data: Dict[str, Any]) -> int:
        """创建进展，返回进展ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            attachments_json = json.dumps(data.get('attachments')) if data.get('attachments') else None
            cursor.execute("""
                INSERT INTO research_progress (
                    user_id, research_direction, weekly_progress, next_goal,
                    difficulties, completion_rate, attachments, submission_period,
                    submission_date, period_start, period_end, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                data.get('user_id'), data.get('research_direction'), data.get('weekly_progress'),
                data.get('next_goal'), data.get('difficulties'), data.get('completion_rate', 0),
                attachments_json, data.get('submission_period', 'weekly'),
                data.get('submission_date'), data.get('period_start'), data.get('period_end'),
                data.get('status', 'normal')
            ))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(progress_id: int) -> Optional[Dict[str, Any]]:
        """获取进展详情"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rp.id, rp.user_id, rp.research_direction, rp.weekly_progress, rp.next_goal,
                       rp.difficulties, rp.completion_rate, rp.attachments, rp.submission_period,
                       rp.submission_date, rp.period_start, rp.period_end, rp.status,
                       rp.supervisor_feedback, rp.feedback_at, rp.feedback_by,
                       supervisor.username as feedback_by_name,
                       rp.created_at, rp.updated_at
                FROM research_progress rp
                LEFT JOIN users supervisor ON rp.feedback_by = supervisor.id
                WHERE rp.id = ?
            """, (progress_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_user_list(user_id: int, limit: int, offset: int, order: str = 'DESC') -> List[Dict[str, Any]]:
        """获取用户进展列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            order_clause = 'DESC' if order.lower() == 'desc' else 'ASC'
            cursor.execute(f"""
                SELECT rp.id, rp.user_id, rp.research_direction, rp.weekly_progress, rp.next_goal,
                       rp.difficulties, rp.completion_rate, rp.attachments, rp.submission_period,
                       rp.submission_date, rp.period_start, rp.period_end, rp.status,
                       rp.supervisor_feedback, rp.feedback_at, rp.feedback_by,
                       supervisor.username as feedback_by_name,
                       rp.created_at, rp.updated_at
                FROM research_progress rp
                LEFT JOIN users supervisor ON rp.feedback_by = supervisor.id
                WHERE rp.user_id = ?
                ORDER BY rp.submission_date {order_clause}
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_user_count(user_id: int) -> int:
        """获取用户进展总数"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM research_progress WHERE user_id = ?", (user_id,))
            return cursor.fetchone()[0] or 0

    @staticmethod
    def get_team_list(filters: Dict[str, Any], limit: int, offset: int) -> List[Dict[str, Any]]:
        """获取团队进展列表"""
        with get_db() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    u.id as user_id,
                    u.username,
                    u.research_direction as user_research_direction,
                    u.degree_type,
                    u.student_id,
                    u.avatar,
                    rp.id as progress_id,
                    rp.research_direction,
                    rp.weekly_progress,
                    rp.next_goal,
                    rp.completion_rate,
                    rp.status,
                    rp.submission_date,
                    rp.supervisor_feedback,
                    rp.feedback_by,
                    supervisor.username as feedback_by_name,
                    ps.period_type,
                    ps.next_deadline
                FROM users u
                LEFT JOIN (
                    SELECT user_id, MAX(submission_date) as max_date
                    FROM research_progress
                    GROUP BY user_id
                ) latest ON u.id = latest.user_id
                LEFT JOIN research_progress rp ON latest.user_id = rp.user_id AND latest.max_date = rp.submission_date
                LEFT JOIN users supervisor ON rp.feedback_by = supervisor.id
                LEFT JOIN progress_settings ps ON u.id = ps.user_id
                WHERE u.role = 'student' AND u.status = 'active'
            """
            params = []

            student_type = filters.get('student_type')
            if student_type == 'doctoral':
                query += " AND u.degree_type LIKE '%博士%'"
            elif student_type == 'master':
                query += " AND u.degree_type LIKE '%硕士%'"
            elif student_type == 'undergraduate':
                query += " AND u.degree_type LIKE '%本科%'"

            research_direction = filters.get('research_direction')
            if research_direction:
                query += " AND (u.research_direction LIKE ? OR rp.research_direction LIKE ?)"
                params.extend([f"%{research_direction}%", f"%{research_direction}%"])

            status = filters.get('status')
            if status == 'not_updated':
                query += " AND (rp.submission_date IS NULL OR rp.submission_date < DATE('now', '-7 days'))"
            elif status == 'delayed':
                query += " AND rp.status = 'delayed'"
            elif status == 'warning':
                query += " AND (rp.status = 'warning' OR rp.submission_date IS NULL OR rp.submission_date < DATE('now', '-7 days'))"
            elif status == 'normal':
                query += " AND rp.status = 'normal'"

            updated_within = filters.get('updated_within')
            if updated_within == '7days':
                query += " AND rp.submission_date >= DATE('now', '-7 days')"
            elif updated_within == '14days':
                query += " AND rp.submission_date >= DATE('now', '-14 days')"
            elif updated_within == '30days':
                query += " AND rp.submission_date >= DATE('now', '-30 days')"

            query += " ORDER BY rp.submission_date DESC NULLS LAST LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_team_count(filters: Dict[str, Any]) -> int:
        """获取团队进展总数"""
        with get_db() as conn:
            cursor = conn.cursor()

            query = """
                SELECT COUNT(*) FROM users u
                LEFT JOIN (
                    SELECT user_id, MAX(submission_date) as max_date
                    FROM research_progress
                    GROUP BY user_id
                ) latest ON u.id = latest.user_id
                LEFT JOIN research_progress rp ON latest.user_id = rp.user_id AND latest.max_date = rp.submission_date
                WHERE u.role = 'student' AND u.status = 'active'
            """
            params = []

            student_type = filters.get('student_type')
            if student_type == 'doctoral':
                query += " AND u.degree_type LIKE '%博士%'"
            elif student_type == 'master':
                query += " AND u.degree_type LIKE '%硕士%'"
            elif student_type == 'undergraduate':
                query += " AND u.degree_type LIKE '%本科%'"

            research_direction = filters.get('research_direction')
            if research_direction:
                query += " AND (u.research_direction LIKE ? OR rp.research_direction LIKE ?)"
                params.extend([f"%{research_direction}%", f"%{research_direction}%"])

            status = filters.get('status')
            if status == 'not_updated':
                query += " AND (rp.submission_date IS NULL OR rp.submission_date < DATE('now', '-7 days'))"
            elif status == 'delayed':
                query += " AND rp.status = 'delayed'"
            elif status == 'warning':
                query += " AND (rp.status = 'warning' OR rp.submission_date IS NULL OR rp.submission_date < DATE('now', '-7 days'))"
            elif status == 'normal':
                query += " AND rp.status = 'normal'"

            cursor.execute(query, params)
            return cursor.fetchone()[0] or 0

    @staticmethod
    def get_stats() -> Dict[str, int]:
        """获取统计信息"""
        with get_db() as conn:
            cursor = conn.cursor()

            # 总学生数
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student' AND status = 'active'")
            total_students = cursor.fetchone()[0] or 0

            # 本周提交数
            cursor.execute("""
                SELECT COUNT(*) FROM research_progress
                WHERE submission_date >= DATE('now', '-7 days')
            """)
            weekly_submissions = cursor.fetchone()[0] or 0

            # 状态统计
            cursor.execute("""
                SELECT status, COUNT(*) FROM research_progress
                WHERE submission_date >= DATE('now', '-30 days')
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())

            # 未更新学生数
            cursor.execute("""
                SELECT COUNT(*) FROM users u
                WHERE u.role = 'student' AND u.status = 'active'
                AND NOT EXISTS (
                    SELECT 1 FROM research_progress rp
                    WHERE rp.user_id = u.id AND rp.submission_date >= DATE('now', '-7 days')
                )
            """)
            not_updated = cursor.fetchone()[0] or 0

            return {
                'total_students': total_students,
                'weekly_submissions': weekly_submissions,
                'delayed_count': status_counts.get('delayed', 0),
                'warning_count': status_counts.get('warning', 0),
                'normal_count': status_counts.get('normal', 0),
                'not_updated_count': not_updated
            }

    @staticmethod
    def update_progress(progress_id: int, data: Dict[str, Any]) -> bool:
        """更新进展"""
        allowed_fields = ['research_direction', 'weekly_progress', 'next_goal', 'difficulties',
                          'completion_rate', 'attachments', 'status']
        update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}

        if 'attachments' in update_data and isinstance(update_data['attachments'], list):
            update_data['attachments'] = json.dumps(update_data['attachments'])

        if not update_data:
            return False

        with get_db() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            params = list(update_data.values()) + [datetime.now().isoformat(), progress_id]
            cursor.execute(f"UPDATE research_progress SET {set_clause}, updated_at = ? WHERE id = ?", params)
            return cursor.rowcount > 0

    @staticmethod
    def add_feedback(progress_id: int, feedback: str, supervisor_id: int) -> bool:
        """添加导师反馈"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE research_progress
                SET supervisor_feedback = ?, feedback_at = CURRENT_TIMESTAMP, feedback_by = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (feedback, supervisor_id, progress_id))
            return cursor.rowcount > 0

    @staticmethod
    def get_setting_by_user(user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户周期设置"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ps.id, ps.user_id, ps.period_type, ps.reminder_enabled, ps.reminder_days,
                       ps.next_deadline, ps.created_by, ps.created_at, ps.updated_at,
                       u.username, u.research_direction
                FROM progress_settings ps
                JOIN users u ON ps.user_id = u.id
                WHERE ps.user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def create_or_update_setting(data: Dict[str, Any]) -> int:
        """创建或更新设置，返回设置ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            user_id = data.get('user_id')

            # 检查是否存在
            cursor.execute("SELECT id FROM progress_settings WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE progress_settings
                    SET period_type = ?, reminder_enabled = ?, reminder_days = ?, next_deadline = ?,
                        created_by = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (
                    data.get('period_type', 'weekly'), data.get('reminder_enabled', True),
                    data.get('reminder_days', 1), data.get('next_deadline'),
                    data.get('created_by'), user_id
                ))
                return existing[0]
            else:
                cursor.execute("""
                    INSERT INTO progress_settings (
                        user_id, period_type, reminder_enabled, reminder_days, next_deadline, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id, data.get('period_type', 'weekly'), data.get('reminder_enabled', True),
                    data.get('reminder_days', 1), data.get('next_deadline'), data.get('created_by')
                ))
                return cursor.lastrowid

    @staticmethod
    def batch_create_settings(user_ids: List[int], period_type: str, reminder_days: int, created_by: int) -> List[int]:
        """批量创建设置"""
        setting_ids = []
        with get_db() as conn:
            cursor = conn.cursor()
            for user_id in user_ids:
                cursor.execute("""
                    INSERT OR REPLACE INTO progress_settings (
                        user_id, period_type, reminder_enabled, reminder_days, created_by
                    ) VALUES (?, ?, 1, ?, ?)
                """, (user_id, period_type, reminder_days, created_by))
                setting_ids.append(cursor.lastrowid)
        return setting_ids

    @staticmethod
    def get_all_settings() -> List[Dict[str, Any]]:
        """获取所有设置"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ps.id, ps.user_id, ps.period_type, ps.reminder_enabled, ps.reminder_days,
                       ps.next_deadline, ps.created_by, ps.created_at, ps.updated_at,
                       u.username, u.research_direction
                FROM progress_settings ps
                JOIN users u ON ps.user_id = u.id
                WHERE u.role = 'student' AND u.status = 'active'
            """)
            return [dict(row) for row in cursor.fetchall()]