"""
================================================================================
Repository 层初始化模块 (repositories/__init__.py)
================================================================================

模块名称: backend/repositories/__init__.py
功能描述: Repository 层统一导出，提供数据访问接口

导出的 Repository 类:
    - AuthRepository           : 认证数据访问
    - UserProfileRepository           : 用户数据访问
    - MemberManagementRepository         : 成员数据访问
    - MeetingMaterialRepository       : 材料数据访问
    - MessageSystemRepository        : 消息数据访问
    - SharedResourcesRepository: 共享资料数据访问
    - MeetingScheduleRepository        : 组会数据访问
    - PaperRepository          : 文献数据访问
    - ResearchProgressRepository       : 研究进展数据访问
    - ResearchTasksRepository           : 研究任务数据访问

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑
    - 返回原始数据或基础数据结构

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from repositories.auth_repository import AuthRepository
from repositories.user_profile_repository import UserProfileRepository
from repositories.member_management_repository import MemberManagementRepository
from repositories.meeting_material_repository import MeetingMaterialRepository
from repositories.message_system_repository import MessageSystemRepository
from repositories.shared_resources_repository import SharedResourcesRepository
from repositories.meeting_schedule_repository import MeetingScheduleRepository
from repositories.paper_repository import PaperRepository
from repositories.research_progress_repository import ResearchProgressRepository
from repositories.research_tasks_repository import ResearchTasksRepository

__all__ = [
    'AuthRepository',
    'UserProfileRepository',
    'MemberManagementRepository',
    'MeetingMaterialRepository',
    'MessageSystemRepository',
    'SharedResourcesRepository',
    'MeetingScheduleRepository',
    'PaperRepository',
    'ResearchProgressRepository',
    'ResearchTasksRepository',
]