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

路由配置:
    - 前缀: /api
    - 标签: 汇报材料

职责:
    - 只处理 HTTP 请求和响应
    - 不写任何业务逻辑
    - 调用 MaterialService 处理业务

依赖模块:
    - dependencies.auth        : get_current_user 认证依赖
    - services.material_service: MaterialService 业务服务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, FileResponse
from loguru import logger

from dependencies.auth import get_current_user
from services.material_service import MaterialService

router = APIRouter(prefix="/api", tags=["汇报材料"])


@router.get("/materials")
async def get_materials(request: Request):
    """获取汇报材料列表API"""
    logger.info("获取汇报材料列表")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        filters = {
            'status': request.query_params.get("status"),
            'meeting_id': request.query_params.get("meeting_id")
        }
        result = MaterialService.get_list(filters)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "data": result})

    except Exception as e:
        logger.error(f"获取汇报材料列表失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "获取汇报材料列表失败", "error": "INTERNAL_ERROR"})


@router.get("/materials/meetings")
async def get_meetings_with_materials(request: Request):
    """获取组会列表及汇报人材料状态API"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        filters = {
            'material_status': request.query_params.get("material_status"),
            'search': request.query_params.get("search", "")
        }
        result = MaterialService.get_meetings_with_materials(filters)
        return JSONResponse(content={"success": True, "data": result})

    except Exception as e:
        logger.error(f"获取组会材料列表失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "获取组会材料列表失败", "error": "INTERNAL_ERROR"})


@router.get("/materials/{presenter_id}/files")
async def get_presenter_files(presenter_id: int, request: Request):
    """获取汇报人的文件列表API"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        files = MaterialService.get_presenter_files(presenter_id)
        return JSONResponse(content={"success": True, "files": files})

    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "获取文件列表失败", "error": "INTERNAL_ERROR"})


@router.put("/materials/{presenter_id}/confirm")
async def confirm_presenter_attendance(presenter_id: int, request: Request):
    """汇报人确认参会API"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        MaterialService.confirm_attendance(presenter_id, current_user.id)
        return JSONResponse(content={"success": True, "message": "已确认参会"})

    except ValueError as e:
        if "不存在" in str(e):
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": str(e)})
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": str(e)})
    except Exception as e:
        logger.error(f"确认参会失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "服务器错误"})


@router.put("/materials/{presenter_id}/status")
async def update_material_status(presenter_id: int, request: Request):
    """更新材料审核状态API"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        data = await request.json()
        new_status = data.get("status")
        MaterialService.update_status(presenter_id, new_status, current_user.id, current_user.role)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": "材料状态更新成功"})

    except ValueError as e:
        message = str(e)
        if "不存在" in message:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": message, "error": "NOT_FOUND"})
        if "权限" in message:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": message, "error": "ACCESS_DENIED"})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": message, "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"更新材料状态失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "更新材料状态失败", "error": "INTERNAL_ERROR"})


@router.post("/materials/{presenter_id}/files")
async def upload_material_file(presenter_id: int, request: Request):
    """为汇报人上传材料文件API"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        form = await request.form()
        file = form.get("file")

        if not file:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "请选择要上传的文件", "error": "VALIDATION_ERROR"})

        result = MaterialService.upload_file(presenter_id, current_user.id, current_user.role, file)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": "材料上传成功", "data": result})

    except ValueError as e:
        message = str(e)
        if "不存在" in message:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": message, "error": "NOT_FOUND"})
        if "权限" in message:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": message, "error": "ACCESS_DENIED"})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": message, "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"上传材料失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "上传材料失败", "error": "INTERNAL_ERROR"})


@router.get("/meetings/{meeting_id}/materials")
async def get_meeting_materials(meeting_id: int, request: Request):
    """获取组会的所有汇报材料API"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        result = MaterialService.get_meeting_materials(meeting_id)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "data": result})

    except Exception as e:
        logger.error(f"获取组会材料失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "获取组会材料失败", "error": "INTERNAL_ERROR"})


@router.get("/meeting_files/{file_id}/download")
async def download_meeting_file(file_id: int, request: Request):
    """下载汇报材料文件API"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    try:
        result = MaterialService.download_file(file_id)
        return FileResponse(path=result['file_path'], filename=result['filename'], media_type="application/octet-stream")

    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": str(e), "error": "NOT_FOUND"})
    except Exception as e:
        logger.error(f"下载汇报材料失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "下载失败", "error": "INTERNAL_ERROR"})