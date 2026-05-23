"""
================================================================================
组会路由模块 (routers/meeting_router.py)
================================================================================

模块名称: backend/routers/meeting_router.py
功能描述: 组会管理 API 端点

API 端点列表 (共10个):
    GET    /api/meetings                  - 获取组会列表
    POST   /api/meetings                  - 创建组会
    GET    /api/meetings/stats            - 获取组会统计
    GET    /api/meetings/{meeting_id}     - 获取组会详情
    PUT    /api/meetings/{meeting_id}     - 更新组会信息
    DELETE /api/meetings/{meeting_id}     - 删除组会
    PUT    /api/meetings/{meeting_id}/status - 更新组会状态
    GET    /api/meetings/{meeting_id}/presenters - 获取汇报人列表
    POST   /api/meetings/{meeting_id}/presenters - 添加汇报人
    DELETE /api/meetings/{meeting_id}/presenters/{presenter_id} - 移除汇报人

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 MeetingService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from dependencies.auth import get_current_user
from services.meeting_service import MeetingService

router = APIRouter(prefix="/api/meetings", tags=["组会"])


@router.get("")
async def get_meetings(request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """获取组会列表"""
    filters = dict(request.query_params)
    result = await service.get_list(filters, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("")
async def create_meeting(request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """创建组会"""
    data = await request.json()
    result = await service.create(data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/stats")
async def get_meeting_stats(request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """获取组会统计"""
    result = await service.get_stats()
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{meeting_id}")
async def get_meeting_detail(meeting_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """获取组会详情"""
    result = await service.get_detail(meeting_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{meeting_id}")
async def update_meeting(meeting_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """更新组会信息"""
    data = await request.json()
    result = await service.update(meeting_id, data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """删除组会"""
    result = await service.delete(meeting_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{meeting_id}/status")
async def update_meeting_status(meeting_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """更新组会状态"""
    data = await request.json()
    result = await service.update_status(meeting_id, data.get("status"), current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{meeting_id}/presenters")
async def get_meeting_presenters(meeting_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """获取汇报人列表"""
    result = await service.get_presenters(meeting_id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/{meeting_id}/presenters")
async def add_meeting_presenter(meeting_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """添加汇报人"""
    data = await request.json()
    result = await service.add_presenter(meeting_id, data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.delete("/{meeting_id}/presenters/{presenter_id}")
async def remove_meeting_presenter(meeting_id: int, presenter_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingService = Depends()):
    """移除汇报人"""
    result = await service.remove_presenter(meeting_id, presenter_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])