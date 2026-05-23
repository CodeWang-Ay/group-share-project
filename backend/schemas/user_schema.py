"""
================================================================================
用户数据验证模块 (schemas/user_schema.py)
================================================================================

模块名称: backend/schemas/user_schema.py
功能描述: 用户相关的 Pydantic 数据验证模型

Schema 类:
    - UserResponse : 用户响应数据模型
    - UserUpdate   : 用户更新数据模型

职责:
    - 定义请求/响应数据结构
    - 数据验证和序列化

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """用户响应数据模型"""
    id: int
    username: str
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None
    student_id: Optional[str] = None
    research_direction: Optional[str] = None
    status: Optional[str] = 'active'
    graduation_status: Optional[str] = None
    supervisor: Optional[str] = None
    degree_type: Optional[str] = None
    work_location: Optional[str] = None
    work_company: Optional[str] = None
    personal_bio: Optional[str] = None
    personal_homepage: Optional[str] = None
    gender: Optional[str] = None
    avatar: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """用户更新数据模型"""
    email: Optional[str] = None
    phone: Optional[str] = None
    student_id: Optional[str] = None
    research_direction: Optional[str] = None
    graduation_status: Optional[str] = None
    supervisor: Optional[str] = None
    degree_type: Optional[str] = None
    work_location: Optional[str] = None
    work_company: Optional[str] = None
    personal_bio: Optional[str] = None
    personal_homepage: Optional[str] = None
    gender: Optional[str] = None
    id_card: Optional[str] = None
    bank_card: Optional[str] = None

    class Config:
        from_attributes = True