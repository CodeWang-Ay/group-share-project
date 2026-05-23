"""
================================================================================
材料数据验证模块 (schemas/material_schema.py)
================================================================================

模块名称: backend/schemas/material_schema.py
功能描述: 汇报材料相关的 Pydantic 数据验证模型

Schema 类:
    - MaterialResponse : 材料响应数据模型
    - PresenterInfo    : 汇报人信息模型
    - FileInfo         : 文件信息模型

职责:
    - 定义请求/响应数据结构
    - 数据验证和序列化

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """文件信息数据模型"""
    id: int
    filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    uploaded_at: Optional[str] = None

    class Config:
        from_attributes = True


class PresenterInfo(BaseModel):
    """汇报人信息数据模型"""
    id: int
    user_id: Optional[int] = None
    presenter_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    material_status: Optional[str] = None
    status: Optional[str] = None
    username: Optional[str] = None
    files: List[FileInfo] = []

    class Config:
        from_attributes = True


class MaterialResponse(BaseModel):
    """材料响应数据模型"""
    id: int
    meeting_id: int
    user_id: Optional[int] = None
    presenter_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None
    status_text: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    meeting_title: Optional[str] = None
    meeting_scheduled_at: Optional[str] = None
    meeting_type: Optional[str] = None
    meeting_status: Optional[str] = None
    username: Optional[str] = None
    user_role: Optional[str] = None
    files: List[FileInfo] = []

    class Config:
        from_attributes = True


class MaterialStats(BaseModel):
    """材料统计数据模型"""
    total: int
    pending: int
    submitted: int
    approved: int
    rejected: int


class MaterialListResponse(BaseModel):
    """材料列表响应数据模型"""
    materials: List[MaterialResponse]
    stats: MaterialStats