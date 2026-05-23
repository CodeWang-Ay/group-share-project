"""
================================================================================
成员管理路由模块 (routers/member_router.py)
================================================================================

模块名称: backend/routers/member_router.py
功能描述: 团队成员管理 API 端点

API 端点列表 (共10个):
    GET    /api/members                    - 获取成员列表
    GET    /api/members/stats              - 获取成员统计
    PUT    /api/members/{member_id}/status - 更新成员状态
    PUT    /api/members/{member_id}        - 更新成员信息
    POST   /api/members                    - 添加新成员
    DELETE /api/members/{member_id}        - 删除成员
    PUT    /api/members/{member_id}/reset-password - 重置密码
    POST   /api/users/batch-update-role    - 批量修改角色
    POST   /api/users/batch-update-status  - 批量修改状态
    POST   /api/users/batch-delete         - 批量删除成员

路由配置:
    - 前缀: /api
    - 标签: 成员管理

职责:
    - 只处理 HTTP 请求和响应
    - 不写任何业务逻辑
    - 调用 MemberService 处理业务

依赖模块:
    - dependencies.auth       : get_current_user 认证依赖
    - services.member_service : MemberService 业务服务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from dependencies.auth import get_current_user
from services.member_service import MemberService

router = APIRouter(prefix="/api", tags=["成员管理"])


@router.get("/members")
async def get_members(request: Request):
    """获取成员列表API端点"""
    logger.info("获取成员列表")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        filters = {
            'role': request.query_params.get("role", ""),
            'status': request.query_params.get("status", ""),
            'degree': request.query_params.get("degree", ""),
            'search': request.query_params.get("search", "")
        }
        pagination = {
            'page': int(request.query_params.get("page", 1)),
            'per_page': int(request.query_params.get("per_page", 10))
        }

        result = MemberService.get_list(filters, pagination)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "data": result})

    except Exception as e:
        logger.error(f"获取成员列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取成员列表失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/members/stats")
async def get_members_stats(request: Request):
    """获取成员统计信息API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        stats = MemberService.get_stats()
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "data": stats})

    except Exception as e:
        logger.error(f"获取成员统计失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取成员统计失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/members/{member_id}/status")
async def update_member_status(member_id: int, request: Request):
    """更新成员状态API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限修改成员状态", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()
        new_status = data.get("status")
        MemberService.update_status(member_id, new_status)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": "成员状态更新成功"})

    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": str(e), "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"更新成员状态失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "更新成员状态失败", "error": "INTERNAL_ERROR"})


@router.put("/members/{member_id}")
async def update_member_info(member_id: int, request: Request):
    """更新成员信息API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    if current_user.role != "admin":
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": "没有权限更新成员信息", "error": "ACCESS_DENIED"})

    try:
        data = await request.json()
        update_data = MemberService.update(member_id, data)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": "成员信息更新成功", "data": update_data})

    except ValueError as e:
        message = str(e)
        if "不存在" in message:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": message, "error": "MEMBER_NOT_FOUND"})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": message, "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"更新成员信息失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "更新成员信息失败", "error": "INTERNAL_ERROR"})


@router.post("/members")
async def create_member(request: Request):
    """添加成员API端点（管理员专用）"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    if current_user.role != "admin":
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": "没有权限添加成员", "error": "ACCESS_DENIED"})

    try:
        data = await request.json()
        result = MemberService.create(data)
        logger.info(f"管理员 {current_user.username} 创建了新用户: {result['username']} (ID: {result['id']})")
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"success": True, "message": "成员添加成功", "data": result})

    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": str(e), "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"添加成员失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "添加成员失败", "error": "INTERNAL_ERROR"})


@router.delete("/members/{member_id}")
async def delete_member(member_id: int, request: Request):
    """删除成员API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    if current_user.role != "admin":
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": "没有权限删除成员", "error": "ACCESS_DENIED"})

    try:
        MemberService.delete(member_id)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": "成员删除成功"})

    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": str(e), "error": "MEMBER_NOT_FOUND"})
    except Exception as e:
        logger.error(f"删除成员失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "删除成员失败", "error": "INTERNAL_ERROR"})


@router.put("/members/{member_id}/reset-password")
async def reset_member_password(member_id: int, request: Request):
    """重置成员密码API端点（管理员专用）"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    if current_user.role != "admin":
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": "没有权限重置密码", "error": "ACCESS_DENIED"})

    try:
        data = await request.json()
        password = data.get("password", "123456")
        result = MemberService.reset_password(member_id, password)
        logger.info(f"管理员 {current_user.username} 重置了用户 {result['member_username']} 的密码")
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": "密码重置成功", "data": result})

    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": str(e), "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"重置密码失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "重置密码失败", "error": "INTERNAL_ERROR"})


@router.post("/users/batch-update-role")
async def batch_update_user_role(request: Request):
    """批量修改成员角色API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    if current_user.role != "admin":
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": "没有权限批量修改成员角色", "error": "ACCESS_DENIED"})

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])
        role = data.get("role")
        updated_count = MemberService.batch_update_role(user_ids, role)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": f"成功更新 {updated_count} 个成员的角色", "updated_count": updated_count})

    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": str(e), "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"批量修改角色失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "批量修改角色失败", "error": "INTERNAL_ERROR"})


@router.post("/users/batch-update-status")
async def batch_update_user_status(request: Request):
    """批量修改成员状态API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    if current_user.role != "admin":
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": "没有权限批量修改成员状态", "error": "ACCESS_DENIED"})

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])
        status_value = data.get("status")
        updated_count = MemberService.batch_update_status(user_ids, status_value)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": f"成功更新 {updated_count} 个成员的状态", "updated_count": updated_count})

    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": str(e), "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"批量修改状态失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "批量修改状态失败", "error": "INTERNAL_ERROR"})


@router.post("/users/batch-delete")
async def batch_delete_users(request: Request):
    """批量删除成员API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"})

    if current_user.role != "admin":
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"success": False, "message": "没有权限批量删除成员", "error": "ACCESS_DENIED"})

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])
        deleted_count = MemberService.batch_delete(user_ids)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": f"成功删除 {deleted_count} 个成员", "deleted_count": deleted_count})

    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": str(e), "error": "VALIDATION_ERROR"})
    except Exception as e:
        logger.error(f"批量删除失败: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "批量删除失败", "error": "INTERNAL_ERROR"})