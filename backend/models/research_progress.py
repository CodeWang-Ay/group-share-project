"""
研究进展数据模型
定义 ResearchProgress 和 ProgressSetting 类及相关数据库操作
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


@dataclass
class ResearchProgress:
    """
    研究进展数据模型

    属性:
        id: 进展ID（数据库自增）
        user_id: 提交者ID（学生）
        research_direction: 研究方向
        weekly_progress: 本周进展内容
        next_goal: 下周目标
        difficulties: 遇到的问题/困难
        completion_rate: 完成度百分比 (0-100)
        attachments: 附件文件路径（JSON格式）
        submission_period: 提交周期类型
        submission_date: 本次提交日期
        period_start: 本周期起始日期
        period_end: 本周期截止日期
        status: 状态
        supervisor_feedback: 导师反馈内容
        feedback_by: 反馈导师ID
        feedback_by_name: 反馈导师名字（查询时关联）
        feedback_at: 导师反馈时间
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: Optional[int] = None
    user_id: int = 0
    research_direction: str = ""
    weekly_progress: str = ""
    next_goal: str = ""
    difficulties: Optional[str] = None
    completion_rate: int = 0
    attachments: Optional[str] = None
    submission_period: str = "weekly"
    submission_date: Optional[datetime] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    status: str = "normal"
    supervisor_feedback: Optional[str] = None
    feedback_by: Optional[int] = None
    feedback_by_name: Optional[str] = None
    feedback_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 状态常量
    STATUS_NORMAL = 'normal'
    STATUS_DELAYED = 'delayed'
    STATUS_WARNING = 'warning'

    # 提交周期常量
    PERIOD_WEEKLY = 'weekly'
    PERIOD_BIWEEKLY = 'biweekly'
    PERIOD_MONTHLY = 'monthly'

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式，用于API响应

        Returns:
            Dict[str, Any]: 进展信息字典
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "research_direction": self.research_direction,
            "weekly_progress": self.weekly_progress,
            "next_goal": self.next_goal,
            "difficulties": self.difficulties,
            "completion_rate": self.completion_rate,
            "attachments": self.get_attachments_list(),
            "submission_period": self.submission_period,
            "submission_date": self.submission_date.isoformat() if self.submission_date else None,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "status": self.status,
            "supervisor_feedback": self.supervisor_feedback,
            "feedback_by": self.feedback_by,
            "feedback_by_name": self.feedback_by_name,
            "feedback_at": self.feedback_at.isoformat() if self.feedback_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchProgress":
        """
        从字典创建进展实例

        Args:
            data: 包含进展信息的字典

        Returns:
            ResearchProgress: 进展实例
        """
        # 处理日期字段
        submission_date = None
        if data.get("submission_date"):
            if isinstance(data["submission_date"], str):
                submission_date = datetime.fromisoformat(data["submission_date"])
            else:
                submission_date = data["submission_date"]

        period_start = None
        if data.get("period_start"):
            if isinstance(data["period_start"], str):
                period_start = datetime.fromisoformat(data["period_start"])
            else:
                period_start = data["period_start"]

        period_end = None
        if data.get("period_end"):
            if isinstance(data["period_end"], str):
                period_end = datetime.fromisoformat(data["period_end"])
            else:
                period_end = data["period_end"]

        feedback_at = None
        if data.get("feedback_at"):
            if isinstance(data["feedback_at"], str):
                feedback_at = datetime.fromisoformat(data["feedback_at"])
            else:
                feedback_at = data["feedback_at"]

        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"])
            else:
                created_at = data["created_at"]

        updated_at = None
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(data["updated_at"])
            else:
                updated_at = data["updated_at"]

        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", 0),
            research_direction=data.get("research_direction", ""),
            weekly_progress=data.get("weekly_progress", ""),
            next_goal=data.get("next_goal", ""),
            difficulties=data.get("difficulties"),
            completion_rate=data.get("completion_rate", 0),
            attachments=data.get("attachments"),
            submission_period=data.get("submission_period", "weekly"),
            submission_date=submission_date,
            period_start=period_start,
            period_end=period_end,
            status=data.get("status", "normal"),
            supervisor_feedback=data.get("supervisor_feedback"),
            feedback_by=data.get("feedback_by"),
            feedback_by_name=data.get("feedback_by_name"),
            feedback_at=feedback_at,
            created_at=created_at,
            updated_at=updated_at
        )

    def get_attachments_list(self) -> List[str]:
        """
        获取附件列表

        Returns:
            List[str]: 附件文件名列表
        """
        if not self.attachments:
            return []
        try:
            return json.loads(self.attachments)
        except json.JSONDecodeError:
            return []

    def set_attachments_list(self, attachments: List[str]) -> None:
        """
        设置附件列表

        Args:
            attachments: 附件文件名列表
        """
        self.attachments = json.dumps(attachments) if attachments else None

    def get_status_text(self) -> str:
        """
        获取状态显示文本

        Returns:
            str: 状态文本
        """
        status_map = {
            'normal': '进度正常',
            'delayed': '进度滞后',
            'warning': '进度预警'
        }
        return status_map.get(self.status, '进度正常')

    def get_period_text(self) -> str:
        """
        获取提交周期显示文本

        Returns:
            str: 周期文本
        """
        period_map = {
            'weekly': '每周',
            'biweekly': '每两周',
            'monthly': '每月'
        }
        return period_map.get(self.submission_period, '每周')


@dataclass
class ProgressSetting:
    """
    提交周期设置数据模型

    属性:
        id: 设置ID（数据库自增）
        user_id: 学生ID（唯一）
        period_type: 周期类型
        reminder_enabled: 是否启用提醒
        reminder_days: 提前多少天提醒
        next_deadline: 下次提交截止时间
        created_by: 配置创建者ID
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: Optional[int] = None
    user_id: int = 0
    period_type: str = "weekly"
    reminder_enabled: bool = True
    reminder_days: int = 1
    next_deadline: Optional[datetime] = None
    created_by: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 周期常量
    PERIOD_WEEKLY = 'weekly'
    PERIOD_BIWEEKLY = 'biweekly'
    PERIOD_MONTHLY = 'monthly'

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式，用于API响应

        Returns:
            Dict[str, Any]: 设置信息字典
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "period_type": self.period_type,
            "reminder_enabled": self.reminder_enabled,
            "reminder_days": self.reminder_days,
            "next_deadline": self.next_deadline.isoformat() if self.next_deadline else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressSetting":
        """
        从字典创建设置实例

        Args:
            data: 包含设置信息的字典

        Returns:
            ProgressSetting: 设置实例
        """
        # 处理日期字段
        next_deadline = None
        if data.get("next_deadline"):
            if isinstance(data["next_deadline"], str):
                next_deadline = datetime.fromisoformat(data["next_deadline"])
            else:
                next_deadline = data["next_deadline"]

        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"])
            else:
                created_at = data["created_at"]

        updated_at = None
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(data["updated_at"])
            else:
                updated_at = data["updated_at"]

        # 处理布尔值
        reminder_enabled = data.get("reminder_enabled", True)
        if isinstance(reminder_enabled, int):
            reminder_enabled = bool(reminder_enabled)

        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", 0),
            period_type=data.get("period_type", "weekly"),
            reminder_enabled=reminder_enabled,
            reminder_days=data.get("reminder_days", 1),
            next_deadline=next_deadline,
            created_by=data.get("created_by", 0),
            created_at=created_at,
            updated_at=updated_at
        )

    def get_period_text(self) -> str:
        """
        获取周期类型显示文本

        Returns:
            str: 周期文本
        """
        period_map = {
            'weekly': '每周提交',
            'biweekly': '每两周提交',
            'monthly': '每月提交'
        }
        return period_map.get(self.period_type, '每周提交')

    def calculate_next_deadline(self) -> datetime:
        """
        计算下次提交截止时间

        Returns:
            datetime: 下次截止时间
        """
        from datetime import timedelta

        now = datetime.now()

        if self.period_type == 'weekly':
            # 每周截止时间：周日 18:00
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0 and now.hour >= 18:
                days_until_sunday = 7
            next_deadline = now + timedelta(days=days_until_sunday)
            return next_deadline.replace(hour=18, minute=0, second=0, microsecond=0)

        elif self.period_type == 'biweekly':
            # 每两周截止时间：两周后的周日 18:00
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0 and now.hour >= 18:
                days_until_sunday = 14
            else:
                days_until_sunday += 7
            next_deadline = now + timedelta(days=days_until_sunday)
            return next_deadline.replace(hour=18, minute=0, second=0, microsecond=0)

        elif self.period_type == 'monthly':
            # 每月截止时间：月末最后一天 18:00
            if now.month == 12:
                next_month = 1
                next_year = now.year + 1
            else:
                next_month = now.month + 1
                next_year = now.year

            # 获取本月最后一天
            import calendar
            last_day = calendar.monthrange(now.year, now.month)[1]
            next_deadline = datetime(now.year, now.month, last_day, 18, 0, 0)

            # 如果已经过了本月截止时间，计算下月
            if now > next_deadline:
                last_day = calendar.monthrange(next_year, next_month)[1]
                next_deadline = datetime(next_year, next_month, last_day, 18, 0, 0)

            return next_deadline

        # 默认返回一周后
        return now + timedelta(days=7)