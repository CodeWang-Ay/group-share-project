"""
================================================================================
用户路由模块 (routers/user_router.py)
================================================================================

模块名称: backend/routers/user_router.py
功能描述: 用户个人信息管理 API 端点

API 端点列表 (共3个):
    GET  /api/user/profile - 获取当前用户详细资料
    PUT  /api/user/profile - 更新用户个人资料
    POST /api/user/avatar  - 上传用户头像

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 UserService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from dependencies.auth import get_current_user
from services.user_service import UserService

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.get("/profile")
async def get_user_profile(request: Request, current_user=Depends(get_current_user), service: UserService = Depends()):
    """获取用户个人资料"""
    result = await service.get_profile(current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/profile")
async def update_user_profile(request: Request, current_user=Depends(get_current_user), service: UserService = Depends()):
    """更新用户个人资料"""
    data = await request.json()
    result = await service.update_profile(current_user.id, data)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/avatar")
async def upload_avatar(request: Request, current_user=Depends(get_current_user), service: UserService = Depends()):
    """上传用户头像"""
    form = await request.form()
    result = await service.upload_avatar(current_user.id, form)
    return JSONResponse(status_code=result["status_code"], content=result["content"])