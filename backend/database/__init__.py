"""
数据库模块
包含数据库连接和初始化功能
"""

from .connection import get_db, init_db

__all__ = ["get_db", "init_db"]