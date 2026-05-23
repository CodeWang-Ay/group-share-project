"""
================================================================================
文件路由模块 (routers/file_router.py)
================================================================================

模块名称: backend/routers/file_router.py
功能描述: 文件上传、下载、管理 API 端点（共享资料模块）

API 端点列表 (共9个):
    POST /api/files/upload              - 上传文件
    GET  /api/files/download/{filename} - 按文件名下载
    GET  /api/files                     - 获取文件列表
    GET  /api/files/stats               - 获取文件统计
    GET  /api/files/{file_id}           - 获取文件详情
    PUT  /api/files/{file_id}           - 更新文件信息
    DELETE /api/files/{file_id}         - 删除文件
    GET  /api/files/{file_id}/download  - 按 ID 下载文件
    GET  /api/files/{file_id}/view      - 文件预览

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 FileService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from dependencies.auth import get_current_user
from services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["文件"])


@router.post("/upload")
async def upload_file(request: Request, current_user=Depends(get_current_user), service: FileService = Depends()):
    """上传文件"""
    form = await request.form()
    result = await service.upload(form, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/download/{filename}")
async def download_file_by_name(filename: str, request: Request, current_user=Depends(get_current_user), service: FileService = Depends()):
    """按文件名下载"""
    result = await service.download_by_name(filename, current_user.id)
    if result.get("error"):
        return JSONResponse(status_code=result["status_code"], content=result["content"])
    return FileResponse(path=result["file_path"], filename=result["filename"], media_type=result["file_type"])


@router.get("")
async def get_files(request: Request, current_user=Depends(get_current_user), service: FileService = Depends()):
    """获取文件列表"""
    filters = dict(request.query_params)
    result = await service.get_list(filters, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/stats")
async def get_file_stats(request: Request, current_user=Depends(get_current_user), service: FileService = Depends()):
    """获取文件统计"""
    filters = dict(request.query_params)
    result = await service.get_stats(filters, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{file_id}")
async def get_file_details(file_id: int, request: Request, current_user=Depends(get_current_user), service: FileService = Depends()):
    """获取文件详情"""
    result = await service.get_detail(file_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{file_id}")
async def update_file_info(file_id: int, request: Request, current_user=Depends(get_current_user), service: FileService = Depends()):
    """更新文件信息"""
    data = await request.json()
    result = await service.update(file_id, data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.delete("/{file_id}")
async def delete_file(file_id: int, request: Request, current_user=Depends(get_current_user), service: FileService = Depends()):
    """删除文件"""
    result = await service.delete(file_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{file_id}/download")
async def download_file(file_id: int, request: Request, current_user=Depends(get_current_user), service: FileService = Depends()):
    """按 ID 下载文件"""
    result = await service.download(file_id, current_user.id, current_user.role)
    if result.get("error"):
        return JSONResponse(status_code=result["status_code"], content=result["content"])
    return FileResponse(path=result["file_path"], filename=result["filename"], media_type=result["file_type"])


@router.get("/{file_id}/view")
async def view_file(file_id: int, request: Request, current_user=Depends(get_current_user), service: FileService = Depends()):
    """文件预览"""
    result = await service.view(file_id, current_user.id, current_user.role)
    if result.get("error"):
        return JSONResponse(status_code=result["status_code"], content=result["content"])
    return FileResponse(path=result["file_path"], filename=result["filename"], media_type=result["media_type"], headers=result["headers"])