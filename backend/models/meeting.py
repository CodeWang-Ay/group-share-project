"""
组会数据模型
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def _parse_datetime(value) -> Optional[datetime]:
    """安全解析 datetime，格式错误返回 None"""
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


@dataclass
class Meeting:
    """组会模型"""
    id: Optional[int]
    title: str
    meeting_type: str  # regular, paper_reading, topic_discussion
    description: Optional[str]
    location: Optional[str]
    is_online: bool
    online_link: Optional[str]
    scheduled_at: Optional[datetime]
    duration_total: int  # 总时长（分钟）
    material_required: bool
    material_deadline: Optional[datetime]
    notes: Optional[str]
    status: str  # scheduled, ongoing, completed
    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_dict(cls, data: dict) -> 'Meeting':
        """从字典创建Meeting对象"""
        return cls(
            id=data.get('id'),
            title=data['title'],
            meeting_type=data.get('meeting_type', 'regular'),
            description=data.get('description'),
            location=data.get('location'),
            is_online=data.get('is_online', False),
            online_link=data.get('online_link'),
            scheduled_at=_parse_datetime(data.get('scheduled_at')),
            duration_total=data.get('duration_total', 60),
            material_required=data.get('material_required', True),
            material_deadline=_parse_datetime(data.get('material_deadline')),
            notes=data.get('notes'),
            status=data.get('status', 'scheduled'),
            created_by=data.get('created_by'),
            created_at=_parse_datetime(data.get('created_at')) or datetime.now(),
            updated_at=_parse_datetime(data.get('updated_at')) or datetime.now()
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'meeting_type': self.meeting_type,
            'description': self.description,
            'location': self.location,
            'is_online': self.is_online,
            'online_link': self.online_link,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'duration_total': self.duration_total,
            'material_required': self.material_required,
            'material_deadline': self.material_deadline.isoformat() if self.material_deadline else None,
            'notes': self.notes,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class MeetingPresenter:
    """汇报人模型"""
    id: Optional[int]
    meeting_id: Optional[int]
    user_id: Optional[int]
    presenter_type: str  # assigned, volunteered, pending
    duration_minutes: int
    material_required: bool
    status: str  # pending, confirmed, completed
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_dict(cls, data: dict) -> 'MeetingPresenter':
        """从字典创建MeetingPresenter对象"""
        return cls(
            id=data.get('id'),
            meeting_id=data.get('meeting_id'),
            user_id=data.get('user_id'),
            presenter_type=data.get('presenter_type', 'pending'),
            duration_minutes=data.get('duration_minutes', 20),
            material_required=data.get('material_required', True),
            status=data.get('status', 'pending'),
            created_at=_parse_datetime(data.get('created_at')) or datetime.now(),
            updated_at=_parse_datetime(data.get('updated_at')) or datetime.now()
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'user_id': self.user_id,
            'presenter_type': self.presenter_type,
            'duration_minutes': self.duration_minutes,
            'material_required': self.material_required,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class MeetingFile:
    """组会材料关联模型"""
    id: Optional[int]
    meeting_id: Optional[int]
    file_id: Optional[int]
    presenter_id: Optional[int]
    created_at: Optional[datetime]

    @classmethod
    def from_dict(cls, data: dict) -> 'MeetingFile':
        """从字典创建MeetingFile对象"""
        return cls(
            id=data.get('id'),
            meeting_id=data.get('meeting_id'),
            file_id=data.get('file_id'),
            presenter_id=data.get('presenter_id'),
            created_at=_parse_datetime(data.get('created_at')) or datetime.now()
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'file_id': self.file_id,
            'presenter_id': self.presenter_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }