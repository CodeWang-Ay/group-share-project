"""
================================================================================
研究任务路由模块 (routers/task_router.py)
================================================================================

模块名称: backend/routers/task_router.py
功能描述: 研究任务管理 API 端点

API 端点列表 (共7个):
    GET    /api/research_tasks              - 获取任务列表
    GET    /api/research_tasks/stats        - 获取任务统计
    POST   /api/research_tasks              - 创建研究任务
    GET    /api/research_tasks/{task_id}    - 获取任务详情
    PUT    /api/research_tasks/{task_id}    - 更新任务信息
    PUT    /api/research_tasks/{task_id}/progress - 更新任务进度
    DELETE /api/research_tasks/{task_id}    - 删除任务

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 TaskService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from dependencies.auth import get_current_user
from services.task_service import TaskService

router = APIRouter(prefix="/api/research_tasks", tags=["研究任务"])


@router.get("")
async def get_research_tasks(request: Request, current_user=Depends(get_current_user),
                              service: TaskService = Depends()):
    """获取研究任务列表"""
    filters = dict(request.query_params)
    filters['page'] = int(filters.get('page', 1))
    filters['limit'] = int(filters.get('limit', 10))
    result = await service.api_get_list(filters, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/stats")
async def get_research_task_stats(request: Request, current_user=Depends(get_current_user),
                                   service: TaskService = Depends()):
    """获取研究任务统计"""
    result = await service.api_get_stats(current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("")
async def create_research_task(request: Request, current_user=Depends(get_current_user),
                                service: TaskService = Depends()):
    """创建研究任务"""
    data = await request.json()
    result = await service.api_create(data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{task_id}")
async def get_research_task_detail(task_id: int, request: Request, current_user=Depends(get_current_user),
                                    service: TaskService = Depends()):
    """获取任务详情"""
    result = await service.api_get_detail(task_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{task_id}")
async def update_research_task(task_id: int, request: Request, current_user=Depends(get_current_user),
                                service: TaskService = Depends()):
    """更新任务"""
    data = await request.json()
    result = await service.api_update(task_id, data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{task_id}/progress")
async def update_research_task_progress(task_id: int, request: Request, current_user=Depends(get_current_user),
                                         service: TaskService = Depends()):
    """更新任务进度"""
    data = await request.json()
    result = await service.api_update_progress(task_id, data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.delete("/{task_id}")
async def delete_research_task(task_id: int, request: Request, current_user=Depends(get_current_user),
                                service: TaskService = Depends()):
    """删除任务"""
    result = await service.api_delete(task_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])