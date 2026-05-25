"""
================================================================================
服务层初始化模块 (services/__init__.py)
================================================================================

模块名称: backend/services/__init__.py
功能描述: Service 层统一导出，提供业务逻辑服务

导出的 Service 类 (遵循 CLAUDE.md 命名规范: XxxService):
    - AuthService              : 认证服务
    - SessionManager           : 会话管理
    - SharedResourcesService   : 共享资料服务
    - UserProfileService              : 用户服务
    - MemberManagementService            : 成员服务
    - MeetingMaterialService          : 材料服务
    - MessageSystemService           : 消息服务
    - MeetingScheduleService           : 组会服务
    - ResearchTasksService              : 任务服务
    - PaperService             : 文献服务
    - ResearchProgressService  : 研究进展服务

命名规范: snake_case + 层级后缀 (遵循 CLAUDE.md)
    - 文件名: xxx_service.py
    - 类名: XxxService

职责:
    - 所有业务逻辑写在这里
    - 调用 Repository 进行数据操作

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from .auth_service import AuthService
from .session_service import SessionManager, session_manager
from .shared_resources_service import SharedResourcesService
from .user_profile_service import UserProfileService
from .member_management_service import MemberManagementService
from .meeting_material_service import MeetingMaterialService
from .message_system_service import MessageSystemService
from .meeting_schedule_service import MeetingScheduleService
from .research_tasks_service import ResearchTasksService
from .paper_service import PaperService
from .research_progress_service import ResearchProgressService

__all__ = [
    "AuthService",
    "SessionManager",
    "session_manager",
    "SharedResourcesService",
    "UserProfileService",
    "MemberManagementService",
    "MeetingMaterialService",
    "MessageSystemService",
    "MeetingScheduleService",
    "ResearchTasksService",
    "PaperService",
    "ResearchProgressService"
]