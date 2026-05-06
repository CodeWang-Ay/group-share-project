"""
研究任务数据模型
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Task:
    """研究任务数据类"""
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    priority: str = "middle"  # high, middle, low
    status: str = "pending"   # pending, ongoing, completed
    progress: int = 0         # 0-100
    assignee_id: int = 0
    creator_id: int = 0
    task_type: str = "personal"  # personal, assigned
    deadline: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 优先级常量
    PRIORITY_HIGH = 'high'
    PRIORITY_MIDDLE = 'middle'
    PRIORITY_LOW = 'low'

    # 状态常量
    STATUS_PENDING = 'pending'
    STATUS_ONGOING = 'ongoing'
    STATUS_COMPLETED = 'completed'

    # 任务类型常量
    TYPE_PERSONAL = 'personal'
    TYPE_ASSIGNED = 'assigned'

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'progress': self.progress,
            'assignee_id': self.assignee_id,
            'creator_id': self.creator_id,
            'task_type': self.task_type,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """从字典创建Task对象"""
        deadline = data.get('deadline')
        if deadline and isinstance(deadline, str):
            deadline = datetime.fromisoformat(deadline)

        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description'),
            priority=data.get('priority', 'middle'),
            status=data.get('status', 'pending'),
            progress=data.get('progress', 0),
            assignee_id=data.get('assignee_id', 0),
            creator_id=data.get('creator_id', 0),
            task_type=data.get('task_type', 'personal'),
            deadline=deadline,
            created_at=created_at,
            updated_at=updated_at
        )

    def is_overdue(self) -> bool:
        """检查任务是否逾期"""
        if self.deadline and self.status != self.STATUS_COMPLETED:
            return datetime.now() > self.deadline
        return False

    def get_priority_text(self) -> str:
        """获取优先级显示文本"""
        priority_map = {
            'high': '高优先级',
            'middle': '中优先级',
            'low': '低优先级'
        }
        return priority_map.get(self.priority, '中优先级')

    def get_status_text(self) -> str:
        """获取状态显示文本"""
        if self.is_overdue():
            return '已逾期'
        status_map = {
            'pending': '待开始',
            'ongoing': '进行中',
            'completed': '已完成'
        }
        return status_map.get(self.status, '待开始')

    def get_display_status(self) -> str:
        """获取显示状态（包含逾期状态）"""
        if self.is_overdue():
            return 'overdue'
        return self.status