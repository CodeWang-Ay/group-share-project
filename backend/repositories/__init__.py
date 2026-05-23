"""
================================================================================
Repository 层初始化模块 (repositories/__init__.py)
================================================================================

模块名称: backend/repositories/__init__.py
功能描述: Repository 层统一导出，提供数据访问接口

导出的 Repository 类:
    - UserRepository      : 用户数据访问
    - MemberRepository    : 成员数据访问
    - MaterialRepository  : 材料数据访问
    - MessageRepository   : 消息数据访问

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑
    - 返回原始数据或基础数据结构

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from repositories.user_repository import UserRepository
from repositories.member_repository import MemberRepository
from repositories.material_repository import MaterialRepository
from repositories.message_repository import MessageRepository

__all__ = [
    'UserRepository',
    'MemberRepository',
    'MaterialRepository',
    'MessageRepository',
]