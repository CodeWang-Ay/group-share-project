"""
================================================================================
消息路由模块 (routers/message_router.py)
================================================================================

模块名称: backend/routers/message_router.py
功能描述: 消息系统 API 端点

API 端点列表 (共3个):
    POST /api/messages/send          - 发送留言
    GET  /api/messages               - 获取消息列表
    PUT  /api/messages/{message_id}/read - 标记已读

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 MessageService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from dependencies.auth import get_current_user
from services.message_service import MessageService

router = APIRouter(prefix="/api/messages", tags=["消息"])


@router.post("/send")
async def send_message(request: Request, current_user=Depends(get_current_user), service: MessageService = Depends()):
    """发送留言"""
    data = await request.json()
    result = await service.send(current_user.id, data.get("receiver_id"), data.get("title"), data.get("content"))
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("")
async def get_messages(request: Request, current_user=Depends(get_current_user), service: MessageService = Depends()):
    """获取用户消息列表"""
    result = await service.get_received(current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{message_id}/read")
async def mark_message_read(message_id: int, request: Request, current_user=Depends(get_current_user), service: MessageService = Depends()):
    """标记留言已读"""
    result = await service.mark_read(message_id, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])