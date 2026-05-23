"""
================================================================================
依赖注入初始化模块 (dependencies/__init__.py)
================================================================================

模块名称: backend/dependencies/__init__.py
功能描述: 依赖注入统一导出，提供 FastAPI 依赖函数

导出的依赖函数:
    - get_current_user       : 获取当前登录用户（可选）
    - get_current_user_required: 获取当前用户（必须登录）
    - get_admin_user         : 获取管理员用户
    - PaginationParams       : 分页参数

职责:
    - 认证依赖
    - 分页依赖
    - 其他公共依赖

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from dependencies.auth import get_current_user, get_current_user_required, get_admin_user
from dependencies.pagination import PaginationParams

__all__ = [
    'get_current_user',
    'get_current_user_required',
    'get_admin_user',
    'PaginationParams',
]