"""
================================================================================
成员数据验证模块 (schemas/member_schema.py)
================================================================================

模块名称: backend/schemas/member_schema.py
功能描述: 成员管理相关的 Pydantic 数据验证模型

Schema 类:
    - MemberCreate  : 成员创建数据模型
    - MemberUpdate  : 成员更新数据模型
    - MemberResponse: 成员响应数据模型

职责:
    - 定义请求/响应数据结构
    - 数据验证和序列化

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class MemberCreate(BaseModel):
    """成员创建数据模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    email: str = Field(..., description="邮箱")
    role: str = Field(..., description="角色: admin/teacher/student")
    phone: Optional[str] = None
    student_id: Optional[str] = None
    research_direction: Optional[str] = None
    personal_bio: Optional[str] = None
    gender: Optional[str] = None
    id_card: Optional[str] = None
    bank_card: Optional[str] = None

    class Config:
        from_attributes = True


class MemberUpdate(BaseModel):
    """成员更新数据模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = None
    student_id: Optional[str] = None
    role: Optional[str] = None
    research_direction: Optional[str] = None
    personal_bio: Optional[str] = None
    gender: Optional[str] = None
    id_card: Optional[str] = None
    bank_card: Optional[str] = None
    status: Optional[str] = None
    degree_type: Optional[str] = None

    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    """成员响应数据模型"""
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


class MemberListResponse(BaseModel):
    """成员列表响应数据模型"""
    members: List[MemberResponse]
    pagination: dict


class MemberStatsResponse(BaseModel):
    """成员统计响应数据模型"""
    total_members: int
    active_members: int
    student_count: int
    teacher_count: int
    admin_count: int
    inactive_members: int