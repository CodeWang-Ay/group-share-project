"""
================================================================================
消息业务服务模块 (services/message_service.py)
================================================================================

模块名称: backend/services/message_service.py
功能描述: 消息系统业务逻辑处理

Service 类方法:
    - send(sender_id, receiver_id, title, content): 发送消息
    - get_received(user_id)                       : 获取收到的消息
    - mark_read(message_id, user_id)              : 标记已读

职责:
    - 处理业务逻辑
    - 权限验证
    - 调用 Repository 进行数据操作

依赖:
    - repositories.message_repository: 数据访问层

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from repositories.message_repository import MessageRepository


class MessageService:
    """消息业务服务类"""

    @staticmethod
    def send(sender_id: int, receiver_id: int, title: str, content: str) -> Dict[str, Any]:
        """发送消息"""
        # 参数验证
        if not receiver_id or not title or not content:
            raise ValueError("缺少必要参数")

        # 不能给自己留言
        if receiver_id == sender_id:
            raise ValueError("不能给自己留言")

        # 检查接收者是否存在且活跃
        if not MessageRepository.check_user_active(receiver_id):
            raise ValueError("接收者不存在或已被禁用")

        # 创建消息
        message_id = MessageRepository.create(sender_id, receiver_id, title, content)

        logger.info(f"留言发送成功: {sender_id} -> {receiver_id}")
        return {
            "message_id": message_id,
            "success": True
        }

    @staticmethod
    def get_received(user_id: int) -> List[Dict[str, Any]]:
        """获取用户收到的消息列表"""
        messages = MessageRepository.get_by_receiver(user_id)
        return messages

    @staticmethod
    def mark_read(message_id: int, user_id: int) -> bool:
        """标记消息已读"""
        # 获取消息
        message = MessageRepository.get_by_id(message_id)
        if not message:
            raise ValueError("留言不存在")

        # 权限验证：只有接收者可以标记已读
        if message['receiver_id'] != user_id:
            raise ValueError("留言不存在")

        # 标记已读
        read_at = datetime.now().isoformat()
        success = MessageRepository.mark_read(message_id, read_at)

        if not success:
            raise ValueError("操作失败")

        logger.info(f"留言已标记已读: message_id={message_id}")
        return True