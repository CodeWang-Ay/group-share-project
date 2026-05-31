"""
================================================================================
共享资料路由模块 (routers/shared_resources_router.py)
================================================================================

模块名称: backend/routers/shared_resources_router.py
功能描述: 共享资料上传、下载、管理 API 端点

API 端点列表 (共9个):
    POST /api/shared-resources/upload              - 上传资料
    GET  /api/shared-resources/download/{filename} - 按文件名下载
    GET  /api/shared-resources                     - 获取资料列表
    GET  /api/shared-resources/stats               - 获取资料统计
    GET  /api/shared-resources/{file_id}           - 获取资料详情
    PUT  /api/shared-resources/{file_id}           - 更新资料信息
    DELETE /api/shared-resources/{file_id}         - 删除资料
    GET  /api/shared-resources/{file_id}/download  - 按 ID 下载资料
    GET  /api/shared-resources/{file_id}/view      - 资料预览

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 SharedResourcesService 处理业务

作者: wjg
创建日期: 2026-05-25
================================================================================
"""
import json
from loguru     import logger 
from fastapi    import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from dependencies.auth import get_current_user
from services.shared_resources_service import SharedResourcesService

router = APIRouter(prefix="/api/files", tags=["共享资料"])


@router.post("/upload")
async def upload_file(request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """上传资料"""
    form = await request.form()
    result = await service.upload(form, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/download/{filename}")
async def download_file_by_name(filename: str, request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """按文件名下载"""
    result = await service.download_by_name(filename, current_user.id)
    if result.get("error"):
        return JSONResponse(status_code=result["status_code"], content=result["content"])
    return FileResponse(path=result["file_path"], filename=result["filename"], media_type=result["file_type"])


@router.get("")
async def get_files(request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """获取资料列表"""
    filters = dict(request.query_params)
    logger.info(json.dumps(filters, ensure_ascii=False))
    result = await service.get_list(filters, current_user.id, current_user.role)
    result_list = result["content"]["data"]["files"]
    logger.info(len(result_list))
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/stats")
async def get_file_stats(request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """获取资料统计"""
    filters = dict(request.query_params)
    result = await service.get_stats(filters, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{file_id}")
async def get_file_details(file_id: int, request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """获取资料详情"""
    result = await service.get_detail(file_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{file_id}")
async def update_file_info(file_id: int, request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """更新资料信息"""
    data = await request.json()
    result = await service.update(file_id, data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.delete("/{file_id}")
async def delete_file(file_id: int, request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """删除资料"""
    result = await service.delete(file_id, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.delete("/by_filename/{filename}")
async def delete_file_by_filename(filename: str, request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """按文件名删除资料（用于研究进展附件删除）"""
    result = await service.delete_by_filename(filename, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{file_id}/download")
async def download_file(file_id: int, request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """按 ID 下载资料"""
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    result = await service.download(file_id, current_user.id, current_user.role)
    if result.get("error"):
        return JSONResponse(status_code=result["status_code"], content=result["content"])
    return FileResponse(path=result["file_path"], filename=result["filename"], media_type=result["file_type"])


@router.get("/{file_id}/view")
async def view_file(file_id: int, request: Request, current_user=Depends(get_current_user), service: SharedResourcesService = Depends()):
    """资料预览"""
    if not current_user:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    result = await service.view(file_id, current_user.id, current_user.role)
    if result.get("error"):
        return JSONResponse(status_code=result["status_code"], content=result["content"])
    return FileResponse(path=result["file_path"], filename=result["filename"], media_type=result["media_type"], headers=result["headers"])