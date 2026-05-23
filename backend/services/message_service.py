"""
================================================================================
消息业务服务模块 (services/message_service.py)
================================================================================

模块名称: backend/services/message_service.py
功能描述: 消息系统业务逻辑处理，返回完整响应数据

Service 类方法:
    - send(sender_id, receiver_id, title, content): 发送消息
    - get_received(user_id)                       : 获取收到的消息
    - mark_read(message_id, user_id)              : 标记已读

职责:
    - 所有业务逻辑写在这里
    - 返回完整响应数据（status_code, content）
    - 调用 Repository 进行数据操作

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from datetime import datetime
from loguru import logger

from repositories.message_repository import MessageRepository


class MessageService:
    """消息业务服务类"""

    async def send(self, sender_id: int, receiver_id: int, title: str, content: str) -> dict:
        """发送消息"""
        # 1. 参数验证
        if not receiver_id or not title or not content:
            return {"status_code": 400, "content": {"success": False, "message": "缺少必要参数", "error": "MISSING_PARAMS"}}

        # 2. 不能给自己留言
        if receiver_id == sender_id:
            return {"status_code": 400, "content": {"success": False, "message": "不能给自己留言", "error": "SELF_MESSAGE_NOT_ALLOWED"}}

        # 3. 检查接收者是否存在
        if not MessageRepository.check_user_active(receiver_id):
            return {"status_code": 404, "content": {"success": False, "message": "接收者不存在或已被禁用", "error": "RECEIVER_NOT_FOUND"}}

        # 4. 创建消息
        message_id = MessageRepository.create(sender_id, receiver_id, title, content)
        logger.info(f"留言发送成功: {sender_id} -> {receiver_id}")
        return {"status_code": 200, "content": {"success": True, "message": "留言成功", "data": {"message_id": message_id}}}

    async def get_received(self, user_id: int) -> dict:
        """获取用户收到的消息列表"""
        messages = MessageRepository.get_by_receiver(user_id)
        return {"status_code": 200, "content": {"success": True, "messages": messages}}

    async def mark_read(self, message_id: int, user_id: int) -> dict:
        """标记消息已读"""
        # 1. 获取消息
        message = MessageRepository.get_by_id(message_id)
        if not message:
            return {"status_code": 404, "content": {"success": False, "message": "留言不存在", "error": "MESSAGE_NOT_FOUND"}}

        # 2. 权限验证
        if message['receiver_id'] != user_id:
            return {"status_code": 404, "content": {"success": False, "message": "留言不存在", "error": "MESSAGE_NOT_FOUND"}}

        # 3. 标记已读
        MessageRepository.mark_read(message_id, datetime.now().isoformat())
        logger.info(f"留言已标记已读: message_id={message_id}")
        return {"status_code": 200, "content": {"success": True, "message": "已标记为已读"}}