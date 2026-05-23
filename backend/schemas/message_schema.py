"""
================================================================================
消息数据验证模块 (schemas/message_schema.py)
================================================================================

模块名称: backend/schemas/message_schema.py
功能描述: 消息系统相关的 Pydantic 数据验证模型

Schema 类:
    - MessageCreate  : 消息创建数据模型
    - MessageResponse: 消息响应数据模型

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


class SenderInfo(BaseModel):
    """发送者信息数据模型"""
    id: int
    username: str

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """消息创建数据模型"""
    receiver_id: int = Field(..., description="接收者ID")
    title: str = Field(..., min_length=1, max_length=100, description="消息标题")
    content: str = Field(..., min_length=1, description="消息内容")

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """消息响应数据模型"""
    id: int
    title: str
    content: str
    is_read: Optional[int] = 0
    created_at: Optional[str] = None
    sender: Optional[SenderInfo] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """消息列表响应数据模型"""
    messages: List[MessageResponse]