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
    ) -> Dict[str, Any]:
        """
        获取用户的进展历史列表

        Args:
            user_id: 用户ID
            page: 页码
            limit: 每页数量
            order: 排序方向

        Returns:
            Dict: 包含 items, total, page, limit, total_pages
        """
        with get_db() as conn:
            cursor = conn.cursor()

            # 获取总数
            cursor.execute("""
                SELECT COUNT(*) FROM research_progress WHERE user_id = ?
            """, (user_id,))
            total = cursor.fetchone()[0]

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
            items = [ResearchProgress.from_dict(dict(row)) for row in rows]

            total_pages = (total + limit - 1) // limit if total > 0 else 1

            return {
                'items': items,
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': total_pages
            }

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
                    # 进度预警：包括warning状态和未更新
                    query += " AND (rp.status = 'warning' OR rp.submission_date IS NULL OR rp.submission_date < DATE('now', '-7 days'))"
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
            # 先获取总数
            count_query = query.replace("SELECT\n                    u.id as user_id,\n                    u.username,\n                    u.research_direction as user_research_direction,\n                    u.degree_type,\n                    u.student_id,\n                    u.avatar,\n                    rp.id as progress_id,\n                    rp.research_direction,\n                    rp.weekly_progress,\n                    rp.next_goal,\n                    rp.completion_rate,\n                    rp.status,\n                    rp.submission_date,\n                    rp.supervisor_feedback,\n                    rp.feedback_by,\n                    supervisor.username as feedback_by_name,\n                    ps.period_type,\n                    ps.next_deadline", "SELECT COUNT(*)")
            cursor.execute(count_query, params.copy())
            total = cursor.fetchone()[0]

            # 再获取分页数据
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

            return {
                'items': result,
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': (total + limit - 1) // limit if total > 0 else 1
            }

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

            # 进度预警人数（状态为warning）
            cursor.execute("""
                SELECT COUNT(DISTINCT u.id)
                FROM users u
                JOIN research_progress rp ON u.id = rp.user_id
                WHERE u.role = 'student' AND u.status = 'active'
                AND rp.status = 'warning'
            """)
            warning_status_count = cursor.fetchone()[0]

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

            # 进度预警人数（状态warning + 未更新）
            warning_count = warning_status_count + not_updated_count

            return {
                'total': total_students,
                'normal': normal_count,
                'warning': warning_count,
                'not_updated': not_updated_count
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

    # ==================== API 异步方法（返回 {status_code, content}） ====================

    async def api_get_my_progress(self, user_id: int, page: int, limit: int, order: str) -> Dict[str, Any]:
        """获取自己进展历史 API"""
        result = ResearchProgressService.get_user_progress_list(user_id, page, limit, order)
        return {"status_code": 200, "content": {
            "success": True,
            "data": [p.to_dict() for p in result['items']],
            "pagination": {
                "total": result['total'],
                "page": result['page'],
                "limit": result['limit'],
                "total_pages": result['total_pages']
            }
        }}

    async def api_submit_progress(self, data: Dict[str, Any], user_id: int, user_role: str, research_direction: str) -> Dict[str, Any]:
        """提交进展 API"""
        if user_role != 'student':
            return {"status_code": 403, "content": {"success": False, "message": "只有学生可以提交进展", "error": "FORBIDDEN"}}

        weekly_progress = data.get("weekly_progress")
        next_goal = data.get("next_goal")

        if not weekly_progress or not next_goal:
            return {"status_code": 400, "content": {"success": False, "message": "本周进展和下周目标为必填项", "error": "VALIDATION_ERROR"}}

        progress = ResearchProgressService.create_progress(
            user_id=user_id,
            research_direction=data.get("research_direction", research_direction or ""),
            weekly_progress=weekly_progress,
            next_goal=next_goal,
            difficulties=data.get("difficulties"),
            completion_rate=data.get("completion_rate", 0),
            attachments=data.get("attachments"),
            submission_period=data.get("submission_period", "weekly")
        )

        return {"status_code": 200, "content": {"success": True, "message": "进展提交成功", "data": progress.to_dict()}}

    async def api_get_settings(self, user_id: int) -> Dict[str, Any]:
        """获取提交周期设置 API"""
        setting = ProgressSettingService.get_setting_by_user(user_id)

        if not setting:
            return {"status_code": 200, "content": {
                "success": True,
                "data": {
                    "period_type": "weekly",
                    "reminder_enabled": True,
                    "reminder_days": 1,
                    "next_deadline": None,
                    "period_text": "每周提交"
                }
            }}

        result = setting.to_dict()
        result["period_text"] = setting.get_period_text()
        return {"status_code": 200, "content": {"success": True, "data": result}}

    async def api_get_team_progress(self, filters: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """获取团队进展 API"""
        progress_list = ResearchProgressService.get_team_progress_list(
            user_role=user_role,
            student_type=filters.get('student_type'),
            grade=filters.get('grade'),
            research_direction=filters.get('research_direction'),
            status=filters.get('status'),
            updated_within=filters.get('updated_within'),
            page=filters.get('page', 1),
            limit=filters.get('limit', 20)
        )
        return {"status_code": 200, "content": {
            "success": True,
            "data": progress_list['items'],
            "pagination": {
                "total": progress_list['total'],
                "page": progress_list['page'],
                "limit": progress_list['limit'],
                "total_pages": progress_list['total_pages']
            }
        }}

    async def api_get_stats(self) -> Dict[str, Any]:
        """获取统计数据 API"""
        stats = ResearchProgressService.get_progress_stats()
        return {"status_code": 200, "content": {"success": True, "data": stats}}

    async def api_set_user_settings(self, user_id: int, data: Dict[str, Any], current_user_id: int, current_role: str) -> Dict[str, Any]:
        """设置学生提交周期 API"""
        if current_role not in ['teacher', 'admin']:
            return {"status_code": 403, "content": {"success": False, "message": "只有导师和管理员可以设置提交周期", "error": "FORBIDDEN"}}

        period_type = data.get("period_type", "weekly")
        if period_type not in ['weekly', 'biweekly', 'monthly']:
            return {"status_code": 400, "content": {"success": False, "message": "无效的周期类型", "error": "VALIDATION_ERROR"}}

        setting = ProgressSettingService.create_or_update_setting(
            user_id=user_id,
            period_type=period_type,
            reminder_enabled=data.get("reminder_enabled", True),
            reminder_days=data.get("reminder_days", 1),
            created_by=current_user_id
        )

        return {"status_code": 200, "content": {"success": True, "message": "周期设置成功", "data": setting.to_dict()}}

    async def api_batch_set_settings(self, data: Dict[str, Any], current_user_id: int, current_role: str) -> Dict[str, Any]:
        """批量设置提交周期 API"""
        if current_role not in ['admin', 'teacher']:
            return {"status_code": 403, "content": {"success": False, "message": "只有管理员或导师可以批量设置提交周期", "error": "FORBIDDEN"}}

        user_ids = data.get("user_ids", [])
        if not user_ids:
            return {"status_code": 400, "content": {"success": False, "message": "请选择要设置的学生", "error": "VALIDATION_ERROR"}}

        settings = ProgressSettingService.batch_create_settings(
            user_ids=user_ids,
            period_type=data.get("period_type", "weekly"),
            reminder_days=data.get("reminder_days", 1),
            created_by=current_user_id
        )

        return {"status_code": 200, "content": {
            "success": True,
            "message": f"成功设置 {len(settings)} 个学生的提交周期",
            "data": [s.to_dict() for s in settings]
        }}

    async def api_get_detail(self, progress_id: int, user_id: int, user_role: str) -> Dict[str, Any]:
        """获取进展详情 API"""
        from repositories.user_repository import UserRepository

        progress = ResearchProgressService.get_progress_by_id(progress_id)
        if not progress:
            return {"status_code": 404, "content": {"success": False, "message": "进展不存在", "error": "NOT_FOUND"}}

        if user_role == 'student' and progress.user_id != user_id:
            return {"status_code": 403, "content": {"success": False, "message": "无权查看此进展", "error": "FORBIDDEN"}}

        user_data = UserRepository.get_by_id(progress.user_id)
        result = progress.to_dict()
        if user_data:
            result["user_info"] = {
                "id": user_data['id'],
                "username": user_data['username'],
                "research_direction": user_data.get('research_direction', '')
            }

        return {"status_code": 200, "content": {"success": True, "data": result}}

    async def api_update_progress(self, progress_id: int, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """更新进展 API"""
        progress = ResearchProgressService.update_progress(
            progress_id=progress_id,
            user_id=user_id,
            research_direction=data.get("research_direction"),
            weekly_progress=data.get("weekly_progress"),
            next_goal=data.get("next_goal"),
            difficulties=data.get("difficulties"),
            completion_rate=data.get("completion_rate"),
            attachments=data.get("attachments")
        )

        if not progress:
            return {"status_code": 403, "content": {"success": False, "message": "无权编辑此进展或已超过编辑时限", "error": "FORBIDDEN"}}

        return {"status_code": 200, "content": {"success": True, "message": "进展更新成功", "data": progress.to_dict()}}

    async def api_add_feedback(self, progress_id: int, data: Dict[str, Any], supervisor_id: int, supervisor_role: str) -> Dict[str, Any]:
        """发送导师反馈 API"""
        if supervisor_role not in ['teacher', 'admin']:
            return {"status_code": 403, "content": {"success": False, "message": "只有导师和管理员可以发送反馈", "error": "FORBIDDEN"}}

        feedback = data.get("feedback")
        if not feedback:
            return {"status_code": 400, "content": {"success": False, "message": "反馈内容不能为空", "error": "VALIDATION_ERROR"}}

        progress = ResearchProgressService.add_supervisor_feedback(
            progress_id=progress_id,
            feedback=feedback,
            supervisor_id=supervisor_id
        )

        if not progress:
            return {"status_code": 404, "content": {"success": False, "message": "进展不存在", "error": "NOT_FOUND"}}

        return {"status_code": 200, "content": {"success": True, "message": "反馈发送成功", "data": progress.to_dict()}}