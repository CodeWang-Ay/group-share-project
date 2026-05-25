"""
================================================================================
消息数据访问模块 (repositories/message_repository.py)
================================================================================

模块名称: backend/repositories/message_repository.py
功能描述: 消息系统数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - create(sender_id, receiver_id, title, content): 创建消息
    - get_by_receiver(receiver_id)                   : 获取用户收到的消息
    - get_by_id(message_id)                          : 获取消息详情
    - mark_read(message_id, read_at)                 : 标记已读
    - check_user_active(user_id)                     : 检查用户是否活跃

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from database.connection import get_db


class MessageSystemRepository:
    """消息数据访问类"""

    @staticmethod
    def create(sender_id: int, receiver_id: int, title: str, content: str) -> int:
        """创建消息，返回消息ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (sender_id, receiver_id, title, content) VALUES (?, ?, ?, ?)",
                (sender_id, receiver_id, title, content)
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_receiver(receiver_id: int) -> List[Dict[str, Any]]:
        """获取用户收到的消息列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.title, m.content, m.is_read, m.created_at,
                       u.id as sender_id, u.username as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.receiver_id = ?
                ORDER BY m.created_at DESC
            """, (receiver_id,))
            rows = cursor.fetchall()

            messages = []
            for row in rows:
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
            return messages

    @staticmethod
    def get_by_id(message_id: int) -> Optional[Dict[str, Any]]:
        """获取消息详情"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, receiver_id, sender_id, title, content, is_read FROM messages WHERE id = ?",
                (message_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def mark_read(message_id: int, read_at: str) -> bool:
        """标记消息已读"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE messages SET is_read = 1, read_at = ? WHERE id = ?",
                (read_at, message_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def check_user_active(user_id: int) -> bool:
        """检查用户是否活跃"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username FROM users WHERE id = ? AND status = 'active'",
                (user_id,)
            )
            return cursor.fetchone() is not None

    @staticmethod
    def get_user_username(user_id: int) -> Optional[str]:
        """获取用户名"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None