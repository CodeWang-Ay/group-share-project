"""
================================================================================
消息路由模块 (routes/messages.py)
================================================================================

模块名称: backend/routes/messages.py
功能描述: 消息系统 API 端点，用于导师与学生之间的留言通知

API 端点列表 (共3个):
    POST /api/messages/send          - 发送留言
        接收: receiver_id, title, content
        发送私信给指定用户
        返回: 消息 ID 和发送时间

    GET  /api/messages               - 获取消息列表
        参数: is_read (true/false/all)
        返回: 收到的消息列表，按时间倒序排列

    PUT  /api/messages/{message_id}/read - 标记已读
        将指定消息标记为已读状态
        返回: 更新后的消息状态

路由配置:
    - 前缀: /api/messages
    - 标签: 消息

消息状态:
    - unread : 未读（新消息）
    - read   : 已读

消息流程:
    1. 导师发送留言给学生
    2. 学生收到消息通知
    3. 学生阅读后标记已读

依赖模块:
    - utils.auth_helper       : get_current_user 认证依赖
    - database.connection     : 数据库连接
    - datetime                : 时间处理

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from datetime import datetime

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from database.connection import get_db
from utils.auth_helper import get_current_user

router = APIRouter(prefix="/api/messages", tags=["消息"])


@router.post("/send")
async def send_message(request: Request):
    """发送留言"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        data = await request.json()
        receiver_id = data.get("receiver_id")
        title = data.get("title")
        content = data.get("content")

        if not receiver_id or not title or not content:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "缺少必要参数",
                    "error": "MISSING_PARAMS"
                }
            )

        # 检查接收者是否存在
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users WHERE id = ? AND status = 'active'", (receiver_id,))
            receiver = cursor.fetchone()

            if not receiver:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "接收者不存在或已被禁用",
                        "error": "RECEIVER_NOT_FOUND"
                    }
                )

            # 不能给自己留言
            if receiver_id == current_user.id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": "不能给自己留言",
                        "error": "SELF_MESSAGE_NOT_ALLOWED"
                    }
                )

            # 插入留言
            cursor.execute(
                "INSERT INTO messages (sender_id, receiver_id, title, content) VALUES (?, ?, ?, ?)",
                (current_user.id, receiver_id, title, content)
            )

        logger.info(f"留言发送成功: {current_user.id} -> {receiver_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "留言成功"
            }
        )

    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "发送消息失败",
                "error": "INTERNAL_ERROR"
            }
        )


@router.get("")
async def get_messages(request: Request):
    """获取用户消息列表"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 获取用户收到的消息
            cursor.execute("""
                SELECT m.id, m.title, m.content, m.is_read, m.created_at,
                       u.id as sender_id, u.username as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.receiver_id = ?
                ORDER BY m.created_at DESC
            """, (current_user.id,))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "is_read": row["is_read"],
                    "created_at": row["created_at"],
                    "sender": {
                        "id": row["sender_id"],
                        "username": row["sender_name"]
                    }
                })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "messages": messages
            }
        )

    except Exception as e:
        logger.error(f"获取留言失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取留言失败",
                "error": "INTERNAL_ERROR"
            }
        )


@router.put("/{message_id}/read")
async def mark_message_read(message_id: int, request: Request):
    """标记留言已读"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 检查留言是否存在且属于当前用户
            cursor.execute(
                "SELECT id FROM messages WHERE id = ? AND receiver_id = ?",
                (message_id, current_user.id)
            )
            message = cursor.fetchone()

            if not message:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "留言不存在",
                        "error": "MESSAGE_NOT_FOUND"
                    }
                )

            # 标记为已读
            cursor.execute(
                "UPDATE messages SET is_read = 1, read_at = ? WHERE id = ?",
                (datetime.now().isoformat(), message_id)
            )

        logger.info(f"留言已标记已读: message_id={message_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "已标记为已读"
            }
        )

    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "操作失败",
                "error": "INTERNAL_ERROR"
            }
        )