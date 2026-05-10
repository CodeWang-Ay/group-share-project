"""
研究进展业务逻辑服务
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import calendar

from database.connection import get_db
from models.research_progress import ResearchProgress, ProgressSetting
from loguru import logger


class ResearchProgressService:
    """研究进展服务类"""

    # 状态常量
    STATUS_NORMAL = 'normal'
    STATUS_DELAYED = 'delayed'
    STATUS_WARNING = 'warning'

    # 周期常量
    PERIOD_WEEKLY = 'weekly'
    PERIOD_BIWEEKLY = 'biweekly'
    PERIOD_MONTHLY = 'monthly'

    @staticmethod
    def create_progress(
        user_id: int,
        research_direction: str,
        weekly_progress: str,
        next_goal: str,
        difficulties: Optional[str] = None,
        completion_rate: int = 0,
        attachments: Optional[List[str]] = None,
        submission_period: str = 'weekly'
    ) -> ResearchProgress:
        """
        创建进展提交

        Args:
            user_id: 用户ID
            research_direction: 研究方向
            weekly_progress: 本周进展内容
            next_goal: 下周目标
            difficulties: 遇到的问题
            completion_rate: 完成度
            attachments: 附件列表
            submission_period: 提交周期类型

        Returns:
            ResearchProgress: 创建的进展对象
        """
        with get_db() as conn:
            cursor = conn.cursor()

            # 计算周期时间范围
            now = datetime.now()
            period_start, period_end = ResearchProgressService._calculate_period_range(
                submission_period, now
            )

            # 根据完成度判断状态
            status = ResearchProgressService._determine_status(completion_rate)

            # 处理附件
            attachments_json = json.dumps(attachments) if attachments else None

            cursor.execute("""
                INSERT INTO research_progress (
                    user_id, research_direction, weekly_progress, next_goal,
                    difficulties, completion_rate, attachments, submission_period,
                    submission_date, period_start, period_end, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                user_id, research_direction, weekly_progress, next_goal,
                difficulties, completion_rate, attachments_json, submission_period,
                now, period_start, period_end, status
            ))

            progress_id = cursor.lastrowid

            return ResearchProgress(
                id=progress_id,
                user_id=user_id,
                research_direction=research_direction,
                weekly_progress=weekly_progress,
                next_goal=next_goal,
                difficulties=difficulties,
                completion_rate=completion_rate,
                attachments=attachments_json,
                submission_period=submission_period,
                submission_date=now,
                period_start=period_start,
                period_end=period_end,
                status=status,
                created_at=now,
                updated_at=now
            )

    @staticmethod
    def get_progress_by_id(progress_id: int) -> Optional[ResearchProgress]:
        """
        根据ID获取进展

        Args:
            progress_id: 进展ID

        Returns:
            Optional[ResearchProgress]: 进展对象或None
        """
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
            if row:
                return ResearchProgress.from_dict(dict(row))
            return None

    @staticmethod
    def get_user_progress_list(
        user_id: int,
        page: int = 1,
        limit: int = 10,
        order: str = 'desc'
    ) -> List[ResearchProgress]:
        """
        获取用户的进展历史列表

        Args:
            user_id: 用户ID
            page: 页码
            limit: 每页数量
            order: 排序方向

        Returns:
            List[ResearchProgress]: 进展列表
        """
        with get_db() as conn:
            cursor = conn.cursor()

            offset = (page - 1) * limit
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

            rows = cursor.fetchall()
            return [ResearchProgress.from_dict(dict(row)) for row in rows]

    @staticmethod
    def get_team_progress_list(
        user_role: str,
        student_type: Optional[str] = None,
        grade: Optional[int] = None,
        research_direction: Optional[str] = None,
        status: Optional[str] = None,
        updated_within: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取团队进展列表（导师/管理员）

        Args:
            user_role: 当前用户角色
            student_type: 学生类型筛选
            grade: 年级筛选
            research_direction: 研究方向筛选
            status: 进度状态筛选
            updated_within: 最近更新时间范围
            page: 页码
            limit: 每页数量

        Returns:
            List[Dict]: 包含用户信息和最新进展的列表
        """
        with get_db() as conn:
            cursor = conn.cursor()

            # 构建查询 - 获取每个学生的最新进展
            query = """
                SELECT
                    u.id as user_id,
                    u.username,
                    u.research_direction as user_research_direction,
                    u.degree_type,
                    u.student_id,
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

            # 添加筛选条件
            if student_type:
                if student_type == 'doctoral':
                    query += " AND u.degree_type LIKE '%博士%'"
                elif student_type == 'master':
                    query += " AND u.degree_type LIKE '%硕士%'"
                elif student_type == 'undergraduate':
                    query += " AND u.degree_type LIKE '%本科%'"

            if research_direction:
                query += " AND (u.research_direction LIKE ? OR rp.research_direction LIKE ?)"
                params.extend([f"%{research_direction}%", f"%{research_direction}%"])

            # 处理状态筛选
            if status:
                if status == 'not_updated':
                    # 未更新：超过一周没有提交进展
                    query += " AND (rp.submission_date IS NULL OR rp.submission_date < DATE('now', '-7 days'))"
                elif status == 'delayed':
                    query += " AND rp.status = 'delayed'"
                elif status == 'warning':
                    query += " AND rp.status = 'warning'"
                elif status == 'normal':
                    query += " AND rp.status = 'normal'"

            # 处理时间范围筛选
            if updated_within:
                if updated_within == '7days':
                    query += " AND rp.submission_date >= DATE('now', '-7 days')"
                elif updated_within == '14days':
                    query += " AND rp.submission_date >= DATE('now', '-14 days')"
                elif updated_within == '30days':
                    query += " AND rp.submission_date >= DATE('now', '-30 days')"

            # 排序和分页
            query += " ORDER BY rp.submission_date DESC NULLS LAST LIMIT ? OFFSET ?"
            offset = (page - 1) * limit
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                data = dict(row)
                # 计算状态（如果数据库中没有）
                if data.get('status') is None:
                    if data.get('submission_date') is None:
                        data['computed_status'] = 'not_updated'
                    else:
                        submission_date = datetime.fromisoformat(data['submission_date'])
                        if submission_date < datetime.now() - timedelta(days=7):
                            data['computed_status'] = 'delayed'
                        else:
                            data['computed_status'] = 'normal'
                else:
                    data['computed_status'] = data['status']
                result.append(data)

            return result

    @staticmethod
    def get_progress_stats() -> Dict[str, int]:
        """
        获取进展统计数据

        Returns:
            Dict[str, int]: 统计数据
        """
        with get_db() as conn:
            cursor = conn.cursor()

            # 总学生数
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student' AND status = 'active'")
            total_students = cursor.fetchone()[0]

            # 进度正常人数（最近有提交且状态正常）
            cursor.execute("""
                SELECT COUNT(DISTINCT u.id)
                FROM users u
                JOIN research_progress rp ON u.id = rp.user_id
                WHERE u.role = 'student' AND u.status = 'active'
                AND rp.status = 'normal'
                AND rp.submission_date >= DATE('now', '-7 days')
            """)
            normal_count = cursor.fetchone()[0]

            # 进度滞后人数
            cursor.execute("""
                SELECT COUNT(DISTINCT u.id)
                FROM users u
                JOIN research_progress rp ON u.id = rp.user_id
                WHERE u.role = 'student' AND u.status = 'active'
                AND rp.status = 'delayed'
            """)
            delayed_count = cursor.fetchone()[0]

            # 未更新本周人数
            cursor.execute("""
                SELECT COUNT(*)
                FROM users u
                LEFT JOIN (
                    SELECT user_id, MAX(submission_date) as max_date
                    FROM research_progress
                    GROUP BY user_id
                ) latest ON u.id = latest.user_id
                WHERE u.role = 'student' AND u.status = 'active'
                AND (latest.max_date IS NULL OR latest.max_date < DATE('now', '-7 days'))
            """)
            not_updated_count = cursor.fetchone()[0]

            return {
                'total': total_students,
                'normal': normal_count,
                'delayed': delayed_count,
                'not_updated': not_updated_count,
                'warning': 0  # 暂时设为0，后续可添加导师标记功能
            }

    @staticmethod
    def update_progress(
        progress_id: int,
        user_id: int,
        research_direction: Optional[str] = None,
        weekly_progress: Optional[str] = None,
        next_goal: Optional[str] = None,
        difficulties: Optional[str] = None,
        completion_rate: Optional[int] = None,
        attachments: Optional[List[str]] = None
    ) -> Optional[ResearchProgress]:
        """
        更新进展（仅限本周提交）

        Args:
            progress_id: 进展ID
            user_id: 用户ID（用于权限校验）
            其他参数为要更新的字段

        Returns:
            Optional[ResearchProgress]: 更新后的进展对象
        """
        # 获取现有进展
        progress = ResearchProgressService.get_progress_by_id(progress_id)
        if not progress:
            return None

        # 校验权限：必须是自己的进展
        if progress.user_id != user_id:
            return None

        # 校验时间：必须是本周提交的才能编辑
        if progress.submission_date:
            days_since_submission = (datetime.now() - progress.submission_date).days
            if days_since_submission > 7:
                return None

        with get_db() as conn:
            cursor = conn.cursor()

            # 构建更新字段
            update_fields = []
            params = []

            if research_direction:
                update_fields.append("research_direction = ?")
                params.append(research_direction)

            if weekly_progress:
                update_fields.append("weekly_progress = ?")
                params.append(weekly_progress)

            if next_goal:
                update_fields.append("next_goal = ?")
                params.append(next_goal)

            if difficulties is not None:
                update_fields.append("difficulties = ?")
                params.append(difficulties)

            if completion_rate is not None:
                update_fields.append("completion_rate = ?")
                params.append(completion_rate)
                # 同时更新状态
                status = ResearchProgressService._determine_status(completion_rate)
                update_fields.append("status = ?")
                params.append(status)

            if attachments is not None:
                update_fields.append("attachments = ?")
                params.append(json.dumps(attachments))

            if not update_fields:
                return progress

            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(progress_id)

            query = f"UPDATE research_progress SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)

            return ResearchProgressService.get_progress_by_id(progress_id)

    @staticmethod
    def add_supervisor_feedback(
        progress_id: int,
        feedback: str,
        supervisor_id: int
    ) -> Optional[ResearchProgress]:
        """
        添加导师反馈

        Args:
            progress_id: 进展ID
            feedback: 反馈内容
            supervisor_id: 导师ID

        Returns:
            Optional[ResearchProgress]: 更新后的进展对象
        """
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE research_progress
                SET supervisor_feedback = ?, feedback_at = CURRENT_TIMESTAMP, feedback_by = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (feedback, supervisor_id, progress_id))

            if cursor.rowcount == 0:
                return None

            return ResearchProgressService.get_progress_by_id(progress_id)

    @staticmethod
    def _calculate_period_range(period_type: str, reference_date: datetime) -> tuple:
        """
        计算周期时间范围

        Args:
            period_type: 周期类型
            reference_date: 参考日期

        Returns:
            tuple: (period_start, period_end)
        """
        if period_type == 'weekly':
            # 本周：周一到周日
            days_since_monday = reference_date.weekday()
            period_start = reference_date - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(days=6)

        elif period_type == 'biweekly':
            # 两周周期
            days_since_monday = reference_date.weekday()
            week_number = reference_date.isocalendar()[1]
            if week_number % 2 == 0:
                period_start = reference_date - timedelta(days=days_since_monday + 7)
            else:
                period_start = reference_date - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(days=13)

        elif period_type == 'monthly':
            # 本月：1日到月末
            period_start = reference_date.replace(day=1)
            last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
            period_end = reference_date.replace(day=last_day)

        else:
            # 默认一周
            days_since_monday = reference_date.weekday()
            period_start = reference_date - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(days=6)

        return period_start, period_end

    @staticmethod
    def _determine_status(completion_rate: int) -> str:
        """
        根据完成度判断状态

        Args:
            completion_rate: 完成度百分比

        Returns:
            str: 状态
        """
        if completion_rate < 30:
            return ResearchProgressService.STATUS_DELAYED
        elif completion_rate < 50:
            return ResearchProgressService.STATUS_WARNING
        else:
            return ResearchProgressService.STATUS_NORMAL


class ProgressSettingService:
    """提交周期设置服务类"""

    @staticmethod
    def get_setting_by_user(user_id: int) -> Optional[ProgressSetting]:
        """
        获取用户的周期设置

        Args:
            user_id: 用户ID

        Returns:
            Optional[ProgressSetting]: 设置对象或None
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, period_type, reminder_enabled, reminder_days,
                       next_deadline, created_by, created_at, updated_at
                FROM progress_settings WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if row:
                return ProgressSetting.from_dict(dict(row))
            return None

    @staticmethod
    def create_or_update_setting(
        user_id: int,
        period_type: str,
        reminder_enabled: bool,
        reminder_days: int,
        created_by: int
    ) -> ProgressSetting:
        """
        创建或更新周期设置

        Args:
            user_id: 学生ID
            period_type: 周期类型
            reminder_enabled: 是否启用提醒
            reminder_days: 提前提醒天数
            created_by: 配置创建者ID

        Returns:
            ProgressSetting: 设置对象
        """
        with get_db() as conn:
            cursor = conn.cursor()

            # 计算下次截止时间
            setting = ProgressSetting(
                user_id=user_id,
                period_type=period_type,
                reminder_enabled=reminder_enabled,
                reminder_days=reminder_days,
                created_by=created_by
            )
            next_deadline = setting.calculate_next_deadline()

            # 检查是否已存在
            cursor.execute("SELECT id FROM progress_settings WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()

            if existing:
                # 更新
                cursor.execute("""
                    UPDATE progress_settings
                    SET period_type = ?, reminder_enabled = ?, reminder_days = ?,
                        next_deadline = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (period_type, int(reminder_enabled), reminder_days, next_deadline, user_id))
                setting_id = existing[0]
            else:
                # 创建
                cursor.execute("""
                    INSERT INTO progress_settings (
                        user_id, period_type, reminder_enabled, reminder_days,
                        next_deadline, created_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (user_id, period_type, int(reminder_enabled), reminder_days, next_deadline, created_by))
                setting_id = cursor.lastrowid

            # 从同一连接查询，确保能看到刚插入的数据
            cursor.execute("""
                SELECT id, user_id, period_type, reminder_enabled, reminder_days,
                       next_deadline, created_by, created_at, updated_at
                FROM progress_settings WHERE id = ?
            """, (setting_id,))
            row = cursor.fetchone()

            if row:
                return ProgressSetting.from_dict(dict(row))
            return setting  # 返回原始对象作为备用

    @staticmethod
    def batch_create_settings(
        user_ids: List[int],
        period_type: str,
        reminder_days: int,
        created_by: int
    ) -> List[ProgressSetting]:
        """
        批量创建周期设置

        Args:
            user_ids: 学生ID列表
            period_type: 周期类型
            reminder_days: 提前提醒天数
            created_by: 配置创建者ID

        Returns:
            List[ProgressSetting]: 设置对象列表
        """
        results = []
        for user_id in user_ids:
            setting = ProgressSettingService.create_or_update_setting(
                user_id, period_type, True, reminder_days, created_by
            )
            results.append(setting)
        return results

    @staticmethod
    def get_all_settings() -> List[ProgressSetting]:
        """
        获取所有学生的周期设置

        Returns:
            List[ProgressSetting]: 设置列表
        """
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

            rows = cursor.fetchall()
            return [ProgressSetting.from_dict(dict(row)) for row in rows]