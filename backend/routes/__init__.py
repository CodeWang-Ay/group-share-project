"""
================================================================================
路由包初始化模块 (routes/__init__.py)
================================================================================

模块名称: backend/routes/__init__.py
功能描述: 路由模块统一导入和导出，便于 app.py 统一注册

导出的路由模块 (共10个):
    - auth_router      : 认证路由 (登录、注册、登出等)
    - users_router     : 用户路由 (个人资料、头像等)
    - files_router     : 文件路由 (上传、下载、管理)
    - health_router    : 健康检查路由 (health、ready、alive等)
    - pages_router     : 页面路由 (HTML页面渲染)
    - meetings_router  : 组会路由 (组会管理、汇报人)
    - messages_router  : 消息路由 (留言系统)
    - tasks_router     : 任务路由 (研究任务管理)
    - members_router   : 成员路由 (团队成员管理)
    - progress_router  : 进展路由 (研究进展提交)

额外路由 (在 app.py 中单独导入):
    - papers_router    : 文献路由 (文献库管理)
    - materials_router : 材料路由 (汇报材料)

使用方式:
    from routes import (
        auth_router,
        users_router,
        files_router,
        health_router,
        pages_router,
        meetings_router,
        messages_router,
        tasks_router,
        members_router,
    )

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .files import router as files_router
from .health import router as health_router
from .pages import router as pages_router
from .meetings import router as meetings_router
from .messages import router as messages_router
from .tasks import router as tasks_router
from .members import router as members_router
from .progress import router as progress_router

# 待拆分的路由模块
# from .materials import router as materials_router
# from .papers import router as papers_router

__all__ = ['auth_router', 'users_router', 'files_router', 'health_router', 'pages_router', 'meetings_router', 'messages_router', 'tasks_router', 'members_router', 'progress_router']