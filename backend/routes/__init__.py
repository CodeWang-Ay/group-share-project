"""
routes 包初始化
路由模块注册
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