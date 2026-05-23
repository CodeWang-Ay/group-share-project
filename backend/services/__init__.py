"""
================================================================================
服务层初始化模块 (services/__init__.py)
================================================================================

模块名称: backend/services/__init__.py
功能描述: Service 层统一导出，提供业务逻辑服务

导出的 Service 类 (遵循 CLAUDE.md 命名规范: XxxService):
    - AuthService           : 认证服务
    - SessionManager        : 会话管理
    - FileService           : 文件服务
    - UserService           : 用户服务
    - MemberService         : 成员服务
    - MaterialService       : 材料服务
    - MessageService        : 消息服务
    - MeetingService        : 组会服务
    - TaskService           : 任务服务
    - PaperService          : 文献服务
    - ResearchProgressService: 研究进展服务

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
from .file_service import FileService
from .user_service import UserService
from .member_service import MemberService
from .material_service import MaterialService
from .message_service import MessageService
from .meeting_service import MeetingService
from .task_service import TaskService
from .paper_service import PaperService
from .research_progress_service import ResearchProgressService

__all__ = [
    "AuthService",
    "SessionManager",
    "session_manager",
    "FileService",
    "UserService",
    "MemberService",
    "MaterialService",
    "MessageService",
    "MeetingService",
    "TaskService",
    "PaperService",
    "ResearchProgressService"
]