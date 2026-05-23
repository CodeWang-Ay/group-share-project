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

路由配置:
    - 前缀: /api/user
    - 标签: 用户

职责:
    - 只处理 HTTP 请求和响应
    - 不写任何业务逻辑
    - 调用 UserService 处理业务

依赖模块:
    - dependencies.auth       : get_current_user 认证依赖
    - services.user_service   : UserService 业务服务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from dependencies.auth import get_current_user
from services.user_service import UserService

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.get("/profile")
async def get_user_profile(request: Request):
    """获取用户个人资料"""
    logger.info("获取用户个人资料")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        profile = UserService.get_profile(current_user.id)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "data": profile})

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "message": str(e), "error": "USER_NOT_FOUND"}
        )
    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取用户资料失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/profile")
async def update_user_profile(request: Request):
    """更新用户个人资料"""
    logger.info("更新用户个人资料")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        update_data = UserService.update_profile(current_user.id, data)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "个人资料更新成功", "data": update_data}
        )

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": str(e), "error": "VALIDATION_ERROR"}
        )
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新个人资料失败", "error": "INTERNAL_ERROR"}
        )


@router.post("/avatar")
async def upload_avatar(request: Request):
    """上传用户头像"""
    logger.info("上传用户头像")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        form = await request.form()
        file = form.get("avatar")

        if not file:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请选择要上传的头像图片", "error": "NO_FILE"}
            )

        result = UserService.upload_avatar(current_user.id, file)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "头像上传成功", "data": result}
        )

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": str(e), "error": "VALIDATION_ERROR"}
        )
    except Exception as e:
        logger.error(f"上传头像失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"上传头像失败: {str(e)}", "error": "INTERNAL_ERROR"}
        )