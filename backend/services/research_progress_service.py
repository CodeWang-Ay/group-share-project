"""
================================================================================
研究进展业务逻辑模块 (services/research_progress_service.py)
================================================================================

模块名称: backend/services/research_progress_service.py
功能描述: 研究进展业务逻辑，返回 {status_code, content} 格式

Service 类方法:
    ResearchProgressService:
        - create_progress(...)                    : 创建进展
        - get_progress_by_id(progress_id)         : 获取进展详情
        - get_user_progress_list(...)             : 获取用户进展列表
        - get_team_progress_list(...)             : 获取团队进展列表
        - get_progress_stats()                    : 获取统计信息
        - update_progress(...)                    : 更新进展
        - add_supervisor_feedback(...)            : 添加导师反馈
        - _calculate_period_range(...)            : 计算周期时间范围
        - _determine_status(completion_rate)      : 根据完成度判断状态

    ProgressSettingService:
        - get_setting_by_user(user_id)            : 获取用户周期设置
        - create_or_update_setting(...)           : 创建或更新设置
        - batch_create_settings(...)              : 批量创建设置
        - get_all_settings()                      : 获取所有设置

        - api_get_my_progress(...)                : API - 获取自己进展
        - api_submit_progress(...)                : API - 提交进展
        - api_get_settings(...)                   : API - 获取设置
        - api_get_team_progress(...)              : API - 获取团队进展
        - api_get_stats()                         : API - 获取统计
        - api_set_user_settings(...)              : API - 设置周期
        - api_batch_set_settings(...)             : API - 批量设置周期
        - api_get_detail(...)                     : API - 获取详情
        - api_update_progress(...)                : API - 更新进展
        - api_add_feedback(...)                   : API - 添加反馈

职责:
    - 所有业务逻辑写在这里
    - 调用 ProgressRepository 进行数据操作
    - 返回 {status_code: int, content: dict} 格式

作者: wjg
创建日期: 2026-05-24
================================================================================
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import calendar

from repositories.progress_repository import ProgressRepository
from repositories.user_repository import UserRepository
from models.research_progress import ResearchProgress, ProgressSetting


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
        """创建进展提交"""
        now = datetime.now()
        period_start, period_end = ResearchProgressService._calculate_period_range(submission_period, now)
        status = ResearchProgressService._determine_status(completion_rate)

        data = {
            'user_id': user_id,
            'research_direction': research_direction,
            'weekly_progress': weekly_progress,
            'next_goal': next_goal,
            'difficulties': difficulties,
            'completion_rate': completion_rate,
            'attachments': attachments,
            'submission_period': submission_period,
            'submission_date': now,
            'period_start': period_start,
            'period_end': period_end,
            'status': status
        }

        progress_id = ProgressRepository.create_progress(data)

        return ResearchProgress(
            id=progress_id,
            user_id=user_id,
            research_direction=research_direction,
            weekly_progress=weekly_progress,
            next_goal=next_goal,
            difficulties=difficulties,
            completion_rate=completion_rate,
            attachments=attachments,
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
        """根据ID获取进展"""
        row = ProgressRepository.get_by_id(progress_id)
        if row:
            return ResearchProgress.from_dict(row)
        return None

    @staticmethod
    def get_user_progress_list(
        user_id: int,
        page: int = 1,
        limit: int = 10,
        order: str = 'desc'
    ) -> Dict[str, Any]:
        """获取用户的进展历史列表"""
        total = ProgressRepository.get_user_count(user_id)
        offset = (page - 1) * limit

        rows = ProgressRepository.get_user_list(user_id, limit, offset, order)
        items = [ResearchProgress.from_dict(row) for row in rows]

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
    ) -> Dict[str, Any]:
        """获取团队进展列表（导师/管理员）"""
        filters = {
            'student_type': student_type,
            'grade': grade,
            'research_direction': research_direction,
            'status': status,
            'updated_within': updated_within
        }

        total = ProgressRepository.get_team_count(filters)
        offset = (page - 1) * limit

        rows = ProgressRepository.get_team_list(filters, limit, offset)

        result = []
        for row in rows:
            data = row
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
        """获取进展统计数据"""
        return ProgressRepository.get_stats()

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
        """更新进展（仅限本周提交）"""
        progress = ResearchProgressService.get_progress_by_id(progress_id)
        if not progress:
            return None

        if progress.user_id != user_id:
            return None

        if progress.submission_date:
            days_since_submission = (datetime.now() - progress.submission_date).days
            if days_since_submission > 7:
                return None

        update_data = {}
        if research_direction:
            update_data['research_direction'] = research_direction
        if weekly_progress:
            update_data['weekly_progress'] = weekly_progress
        if next_goal:
            update_data['next_goal'] = next_goal
        if difficulties is not None:
            update_data['difficulties'] = difficulties
        if completion_rate is not None:
            update_data['completion_rate'] = completion_rate
            update_data['status'] = ResearchProgressService._determine_status(completion_rate)
        if attachments is not None:
            update_data['attachments'] = attachments

        if not update_data:
            return progress

        ProgressRepository.update_progress(progress_id, update_data)

        return ResearchProgressService.get_progress_by_id(progress_id)

    @staticmethod
    def add_supervisor_feedback(
        progress_id: int,
        feedback: str,
        supervisor_id: int
    ) -> Optional[ResearchProgress]:
        """添加导师反馈"""
        success = ProgressRepository.add_feedback(progress_id, feedback, supervisor_id)
        if not success:
            return None
        return ResearchProgressService.get_progress_by_id(progress_id)

    @staticmethod
    def _calculate_period_range(period_type: str, reference_date: datetime) -> tuple:
        """计算周期时间范围"""
        if period_type == 'weekly':
            days_since_monday = reference_date.weekday()
            period_start = reference_date - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(days=6)

        elif period_type == 'biweekly':
            days_since_monday = reference_date.weekday()
            week_number = reference_date.isocalendar()[1]
            if week_number % 2 == 0:
                period_start = reference_date - timedelta(days=days_since_monday + 7)
            else:
                period_start = reference_date - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(days=13)

        elif period_type == 'monthly':
            period_start = reference_date.replace(day=1)
            last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
            period_end = reference_date.replace(day=last_day)

        else:
            days_since_monday = reference_date.weekday()
            period_start = reference_date - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(days=6)

        return period_start, period_end

    @staticmethod
    def _determine_status(completion_rate: int) -> str:
        """根据完成度判断状态"""
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
        """获取用户的周期设置"""
        row = ProgressRepository.get_setting_by_user(user_id)
        if row:
            return ProgressSetting.from_dict(row)
        return None

    @staticmethod
    def create_or_update_setting(
        user_id: int,
        period_type: str,
        reminder_enabled: bool,
        reminder_days: int,
        created_by: int
    ) -> ProgressSetting:
        """创建或更新周期设置"""
        setting = ProgressSetting(
            user_id=user_id,
            period_type=period_type,
            reminder_enabled=reminder_enabled,
            reminder_days=reminder_days,
            created_by=created_by
        )
        next_deadline = setting.calculate_next_deadline()

        data = {
            'user_id': user_id,
            'period_type': period_type,
            'reminder_enabled': reminder_enabled,
            'reminder_days': reminder_days,
            'next_deadline': next_deadline,
            'created_by': created_by
        }

        setting_id = ProgressRepository.create_or_update_setting(data)

        row = ProgressRepository.get_setting_by_user(user_id)
        if row:
            return ProgressSetting.from_dict(row)
        return setting

    @staticmethod
    def batch_create_settings(
        user_ids: List[int],
        period_type: str,
        reminder_days: int,
        created_by: int
    ) -> List[ProgressSetting]:
        """批量创建周期设置"""
        ProgressRepository.batch_create_settings(user_ids, period_type, reminder_days, created_by)

        results = []
        for user_id in user_ids:
            row = ProgressRepository.get_setting_by_user(user_id)
            if row:
                results.append(ProgressSetting.from_dict(row))
        return results

    @staticmethod
    def get_all_settings() -> List[ProgressSetting]:
        """获取所有学生的周期设置"""
        rows = ProgressRepository.get_all_settings()
        return [ProgressSetting.from_dict(row) for row in rows]

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