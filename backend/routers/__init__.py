"""
================================================================================
路由包初始化模块 (routers/__init__.py)
================================================================================

模块名称: backend/routers/__init__.py
功能描述: 路由模块统一导入和导出，便于 app.py 统一注册

导出的路由模块 (共12个):
    - auth_router       : 认证路由 (登录、注册、登出)
    - user_router       : 用户路由 (个人资料、头像)
    - file_router       : 文件路由 (上传、下载、管理)
    - health_router     : 健康检查路由 (health、ready、alive)
    - page_router       : 页面路由 (HTML页面渲染)
    - meeting_router    : 组会路由 (组会管理、汇报人)
    - message_router    : 消息路由 (留言系统)
    - task_router       : 任务路由 (研究任务管理)
    - member_router     : 成员路由 (团队成员管理)
    - material_router   : 材料路由 (汇报材料管理)
    - paper_router      : 文献路由 (文献库管理)
    - progress_router   : 进展路由 (研究进展提交)

命名规范: snake_case + 层级后缀 (遵循 CLAUDE.md)
    - 文件名: xxx_router.py
    - 变量名: xxx_router

使用方式:
    from routers import (
        auth_router,
        user_router,
        file_router,
        ...
    )

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter

# 导入所有路由模块 (遵循 CLAUDE.md 命名规范: xxx_router.py)
from .auth_router import router as auth_router
from .user_router import router as user_router
from .file_router import router as file_router
from .health_router import router as health_router
from .page_router import router as page_router
from .meeting_router import router as meeting_router
from .message_router import router as message_router
from .task_router import router as task_router
from .member_router import router as member_router
from .material_router import router as material_router
from .paper_router import router as paper_router
from .progress_router import router as progress_router

__all__ = [
    'auth_router',
    'user_router',
    'file_router',
    'health_router',
    'page_router',
    'meeting_router',
    'message_router',
    'task_router',
    'member_router',
    'material_router',
    'paper_router',
    'progress_router'
]