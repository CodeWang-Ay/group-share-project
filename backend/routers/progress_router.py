"""
================================================================================
研究进展路由模块 (routers/progress_router.py)
================================================================================

模块名称: backend/routers/progress_router.py
功能描述: 研究进展管理 API 端点

API 端点列表 (共10个):
    GET  /api/research_progress/my        - 获取自己进展历史
    POST /api/research_progress/submit    - 提交新进展
    GET  /api/research_progress/settings  - 获取提交周期设置
    GET  /api/research_progress/team      - 获取团队进展
    GET  /api/research_progress/stats     - 获取统计数据
    PUT  /api/research_progress/settings/{user_id} - 设置学生提交周期
    POST /api/research_progress/settings/batch - 批量设置提交周期
    GET  /api/research_progress/{progress_id} - 查看进展详情
    PUT  /api/research_progress/{progress_id} - 编辑已提交进展
    POST /api/research_progress/{progress_id}/feedback - 发送导师反馈

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 ResearchProgressService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import JSONResponse

from dependencies.auth import get_current_user
from services.research_progress_service import ResearchProgressService, ProgressSettingService

router = APIRouter(prefix="/api/research_progress", tags=["研究进展"])


@router.get("/my")
async def get_my_progress(request: Request, current_user=Depends(get_current_user),
                          page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100),
                          order: str = Query("desc"), service: ResearchProgressService = Depends()):
    """获取自己的进展历史列表"""
    result = await service.api_get_my_progress(current_user.id, page, limit, order)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/submit")
async def submit_progress(request: Request, current_user=Depends(get_current_user),
                          service: ResearchProgressService = Depends()):
    """提交新的进展"""
    data = await request.json()
    result = await service.api_submit_progress(data, current_user.id, current_user.role, current_user.research_direction)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/settings")
async def get_my_settings(request: Request, current_user=Depends(get_current_user),
                          service: ResearchProgressService = Depends()):
    """获取自己的提交周期设置"""
    result = await service.api_get_settings(current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/team")
async def get_team_progress(request: Request, current_user=Depends(get_current_user),
                             student_type: Optional[str] = Query(None),
                             grade: Optional[int] = Query(None),
                             research_direction: Optional[str] = Query(None),
                             status: Optional[str] = Query(None),
                             updated_within: Optional[str] = Query(None),
                             page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                             service: ResearchProgressService = Depends()):
    """获取团队所有成员进展"""
    filters = {"student_type": student_type, "grade": grade, "research_direction": research_direction,
               "status": status, "updated_within": updated_within, "page": page, "limit": limit}
    result = await service.api_get_team_progress(filters, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/stats")
async def get_progress_stats(request: Request, current_user=Depends(get_current_user),
                             service: ResearchProgressService = Depends()):
    """获取统计数据"""
    result = await service.api_get_stats()
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/settings/{user_id}")
async def set_user_settings(user_id: int, request: Request, current_user=Depends(get_current_user),
                             service: ResearchProgressService = Depends()):
    """设置某个学生的提交周期"""
    data = await request.json()
    result = await service.api_set_user_settings(user_id, data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/settings/batch")
async def batch_set_settings(request: Request, current_user=Depends(get_current_user),
                             service: ResearchProgressService = Depends()):
    """批量设置学生提交周期"""
    data = await request.json()
    result = await service.api_batch_set_settings(data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{progress_id}")
async def get_progress_detail(progress_id: int, request: Request, current_user=Depends(get_current_user),
                              service: ResearchProgressService = Depends()):
    """查看进展详情"""
    result = await service.api_get_detail(progress_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{progress_id}")
async def update_progress(progress_id: int, request: Request, current_user=Depends(get_current_user),
                          service: ResearchProgressService = Depends()):
    """编辑已提交的进展"""
    data = await request.json()
    result = await service.api_update_progress(progress_id, data, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/{progress_id}/feedback")
async def add_feedback(progress_id: int, request: Request, current_user=Depends(get_current_user),
                       service: ResearchProgressService = Depends()):
    """发送导师反馈"""
    data = await request.json()
    result = await service.api_add_feedback(progress_id, data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])