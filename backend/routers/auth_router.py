"""
================================================================================
认证路由模块 (routers/auth_router.py)
================================================================================

模块名称: backend/routers/auth_router.py
功能描述: 用户认证 API 端点

API 端点列表 (共7个):
    POST /api/auth/login          - 用户登录
    POST /api/auth/register       - 用户注册
    POST /api/auth/logout         - 用户登出
    GET  /api/auth/me             - 获取当前用户信息
    PUT  /api/auth/change-password - 修改密码
    POST /api/auth/refresh        - 刷新会话
    GET  /api/auth/session-status - 检查会话状态

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 AuthService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from dependencies.auth import get_current_user
from services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
async def login(request: Request, service: AuthService = Depends()):
    """用户登录 - 返回 JSON，前端处理重定向"""
    data = await request.json()
    result = await service.login(data)
    if result.get("success"):
        # 返回 JSON，包含 session_token，前端处理 cookie 和重定向
        response = JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "登录成功",
                "session_token": result["cookie"]["value"],
                "max_age": result["cookie"]["max_age"]
            }
        )
        # 后端也设置 cookie，作为备份
        response.set_cookie(**result["cookie"])
        return response
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/register")
async def register(request: Request, service: AuthService = Depends()):
    """用户注册"""
    data = await request.json()
    result = await service.register(data)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/logout")
async def logout(request: Request, service: AuthService = Depends()):
    """用户登出"""
    result = await service.logout(request)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/me")
async def get_current_user_info(request: Request, current_user=Depends(get_current_user), service: AuthService = Depends()):
    """获取当前用户信息"""
    result = await service.get_user_info(request, current_user)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/change-password")
async def change_password(request: Request, current_user=Depends(get_current_user), service: AuthService = Depends()):
    """修改密码"""
    data = await request.json()
    result = await service.change_password(current_user.id, data)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/refresh")
async def refresh_session(request: Request, service: AuthService = Depends()):
    """刷新会话"""
    result = await service.refresh_session(request)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/session-status")
async def check_session_status(request: Request, service: AuthService = Depends()):
    """检查会话状态"""
    result = await service.check_session_status(request)
    return JSONResponse(status_code=result["status_code"], content=result["content"])