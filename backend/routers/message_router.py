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

路由配置:
    - 前缀: /api/messages
    - 标签: 消息

职责:
    - 只处理 HTTP 请求和响应
    - 不写任何业务逻辑
    - 调用 MessageService 处理业务

依赖模块:
    - dependencies.auth        : get_current_user 认证依赖
    - services.message_service: MessageService 业务服务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from dependencies.auth import get_current_user
from services.message_service import MessageService

router = APIRouter(prefix="/api/messages", tags=["消息"])


@router.post("/send")
async def send_message(request: Request):
    """发送留言"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        data = await request.json()
        receiver_id = data.get("receiver_id")
        title = data.get("title")
        content = data.get("content")

        result = MessageService.send(current_user.id, receiver_id, title, content)
        logger.info(f"留言发送成功: {current_user.id} -> {receiver_id}")
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": "留言成功", "data": result})

    except ValueError as e:
        message = str(e)
        if "不存在" in message:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": message, "error": "RECEIVER_NOT_FOUND"})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": message, "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "发送消息失败", "error": "INTERNAL_ERROR"})


@router.get("")
async def get_messages(request: Request):
    """获取用户消息列表"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        messages = MessageService.get_received(current_user.id)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "messages": messages})

    except Exception as e:
        logger.error(f"获取留言失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "获取留言失败", "error": "INTERNAL_ERROR"})


@router.put("/{message_id}/read")
async def mark_message_read(message_id: int, request: Request):
    """标记留言已读"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        MessageService.mark_read(message_id, current_user.id)
        logger.info(f"留言已标记已读: message_id={message_id}")
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": "已标记为已读"})

    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": str(e), "error": "MESSAGE_NOT_FOUND"})
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "操作失败", "error": "INTERNAL_ERROR"})