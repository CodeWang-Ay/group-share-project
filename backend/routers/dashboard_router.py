"""
================================================================================
仪表盘路由模块 (routers/dashboard_router.py)
================================================================================

模块名称: backend/routers/dashboard_router.py
功能描述: 仪表盘数据接口，返回工作台所需的各种统计数据

API 接口:
    GET /api/dashboard/stats          - 获取仪表盘统计数据
    GET /api/dashboard/upcoming       - 获取即将到来的组会
    GET /api/dashboard/recent_files   - 获取最近提交的材料
    GET /api/dashboard/recent_papers  - 获取最近的文献

作者: wjg
创建日期: 2026-05-26
================================================================================
"""
import json
from loguru import logger
from fastapi import APIRouter, Request, Depends
from services.dashboard_service import DashboardService
from dependencies.auth import get_current_user_required

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(request: Request, current_user=Depends(get_current_user_required), service: DashboardService = Depends()):
    """获取仪表盘统计数据"""
    result = await service.get_stats(current_user.id, current_user.role)
    return result


@router.get("/upcoming")
async def get_upcoming_meetings(request: Request, current_user=Depends(get_current_user_required), service: DashboardService = Depends()):
    """获取即将到来的组会"""
    result = await service.get_upcoming_meetings(current_user.id, current_user.role)
    meeting_list = result["content"]["data"]["meetings"]
    logger.info(f"最新会议个数 {len(meeting_list)}")
    return result


@router.get("/recent_files")
async def get_recent_files(request: Request, current_user=Depends(get_current_user_required), service: DashboardService = Depends()):
    """获取最近提交的材料"""
    result = await service.get_recent_files(current_user.id, current_user.role)
    material_list = result["content"]["data"]
    logger.info(f"最新材料个数 {len(material_list)}")
    return result


@router.get("/recent_papers")
async def get_recent_papers(request: Request, current_user=Depends(get_current_user_required), service: DashboardService = Depends()):
    """获取最近的文献"""
    logger.info(f"{current_user.id}, current_user.role")
    result = await service.get_recent_papers(current_user.id, current_user.role)
    paper_list = result["content"]["data"]
    logger.info(f"最新文献个数 {len(paper_list)}")
    return result


@router.get("/recent_progress")
async def get_recent_progress(request: Request, current_user=Depends(get_current_user_required), service: DashboardService = Depends()):
    """获取学生研究进展"""
    result = await service.get_recent_progress(current_user.id, current_user.role)
    return result