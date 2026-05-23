"""
================================================================================
Schema 层初始化模块 (schemas/__init__.py)
================================================================================

模块名称: backend/schemas/__init__.py
功能描述: Schema 层统一导出，Pydantic 数据验证模型

导出的 Schema 类:
    - UserResponse, UserUpdate       : 用户数据模型
    - MemberCreate, MemberUpdate     : 成员数据模型
    - MaterialResponse               : 材料数据模型
    - MessageCreate, MessageResponse : 消息数据模型

职责:
    - 定义请求/响应数据结构
    - 数据验证和序列化

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from schemas.user_schema import UserResponse, UserUpdate
from schemas.member_schema import MemberCreate, MemberUpdate, MemberResponse
from schemas.material_schema import MaterialResponse, PresenterInfo, FileInfo
from schemas.message_schema import MessageCreate, MessageResponse

__all__ = [
    'UserResponse',
    'UserUpdate',
    'MemberCreate',
    'MemberUpdate',
    'MemberResponse',
    'MaterialResponse',
    'PresenterInfo',
    'FileInfo',
    'MessageCreate',
    'MessageResponse',
]