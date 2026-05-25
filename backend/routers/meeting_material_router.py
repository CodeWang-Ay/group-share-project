"""
================================================================================
汇报材料路由模块 (routers/material_router.py)
================================================================================

模块名称: backend/routers/material_router.py
功能描述: 组会汇报材料管理 API 端点

API 端点列表 (共8个):
    GET  /api/materials                     - 获取汇报材料列表
    GET  /api/materials/meetings            - 获取组会及材料状态
    GET  /api/materials/{presenter_id}/files - 获取汇报人文件
    PUT  /api/materials/{presenter_id}/confirm - 确认参会
    PUT  /api/materials/{presenter_id}/status - 更新材料审核状态
    POST /api/materials/{presenter_id}/files - 上传材料文件
    GET  /api/meetings/{meeting_id}/materials - 获取组会所有材料
    GET  /api/meeting_files/{file_id}/download - 下载汇报材料

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 MeetingMaterialService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from dependencies.auth import get_current_user
from services.meeting_material_service import MeetingMaterialService

router = APIRouter(prefix="/api", tags=["汇报材料"])


@router.get("/materials")
async def get_materials(request: Request, current_user=Depends(get_current_user), service: MeetingMaterialService = Depends()):
    """获取汇报材料列表"""
    filters = dict(request.query_params)
    result = await service.get_list(filters)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/materials/meetings")
async def get_meetings_with_materials(request: Request, current_user=Depends(get_current_user), service: MeetingMaterialService = Depends()):
    """获取组会列表及汇报人材料状态"""
    filters = dict(request.query_params)
    result = await service.get_meetings_with_materials(filters)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/materials/{presenter_id}/files")
async def get_presenter_files(presenter_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingMaterialService = Depends()):
    """获取汇报人的文件列表"""
    result = await service.get_presenter_files(presenter_id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/materials/{presenter_id}/confirm")
async def confirm_presenter_attendance(presenter_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingMaterialService = Depends()):
    """汇报人确认参会"""
    result = await service.confirm_attendance(presenter_id, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/materials/{presenter_id}/status")
async def update_material_status(presenter_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingMaterialService = Depends()):
    """更新材料审核状态"""
    data = await request.json()
    result = await service.update_status(presenter_id, data.get("status"), current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/materials/{presenter_id}/files")
async def upload_material_file(presenter_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingMaterialService = Depends()):
    """为汇报人上传材料文件"""
    form = await request.form()
    result = await service.upload_file(presenter_id, current_user.id, current_user.role, form)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/meetings/{meeting_id}/materials")
async def get_meeting_materials(meeting_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingMaterialService = Depends()):
    """获取组会的所有汇报材料"""
    result = await service.get_meeting_materials(meeting_id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/meeting_files/{file_id}/download")
async def download_meeting_file(file_id: int, request: Request, current_user=Depends(get_current_user), service: MeetingMaterialService = Depends()):
    """下载汇报材料文件"""
    result = await service.download_file(file_id)
    if result.get("error"):
        return JSONResponse(status_code=result["status_code"], content=result["content"])
    return FileResponse(path=result["file_path"], filename=result["filename"], media_type="application/octet-stream")