"""
================================================================================
成员路由模块 (routers/member_router.py)
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

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 MemberManagementService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from dependencies.auth import get_current_user
from services.member_management_service import MemberManagementService

router = APIRouter(prefix="/api", tags=["成员管理"])


@router.get("/members")
async def get_members(request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """获取成员列表"""
    filters = dict(request.query_params)
    page = int(filters.get("page", 1))
    per_page = int(filters.get("per_page", 10))
    result = await service.get_list(filters, {"page": page, "per_page": per_page})
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/members/stats")
async def get_members_stats(request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """获取成员统计"""
    result = await service.get_stats()
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/members/{member_id}/status")
async def update_member_status(member_id: int, request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """更新成员状态"""
    data = await request.json()
    result = await service.update_status(member_id, data.get("status"), current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/members/{member_id}")
async def update_member_info(member_id: int, request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """更新成员信息"""
    data = await request.json()
    result = await service.update(member_id, data, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/members")
async def create_member(request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """添加成员"""
    data = await request.json()
    result = await service.create(data, current_user.role, current_user.username)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.delete("/members/{member_id}")
async def delete_member(member_id: int, request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """删除成员"""
    result = await service.delete(member_id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/members/{member_id}/reset-password")
async def reset_member_password(member_id: int, request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """重置密码"""
    data = await request.json()
    result = await service.reset_password(member_id, data.get("password", "123456"), current_user.role, current_user.username)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/users/batch-update-role")
async def batch_update_user_role(request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """批量修改角色"""
    data = await request.json()
    result = await service.batch_update_role(data.get("user_ids", []), data.get("role"), current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/users/batch-update-status")
async def batch_update_user_status(request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """批量修改状态"""
    data = await request.json()
    result = await service.batch_update_status(data.get("user_ids", []), data.get("status"), current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/users/batch-delete")
async def batch_delete_users(request: Request, current_user=Depends(get_current_user), service: MemberManagementService = Depends()):
    """批量删除成员"""
    data = await request.json()
    result = await service.batch_delete(data.get("user_ids", []), current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])