"""
================================================================================
研究任务路由模块 (routes/tasks.py)
================================================================================

模块名称: backend/routes/tasks.py
功能描述: 研究任务管理 API 端点，包括任务创建、进度跟踪等

API 端点列表 (共7个):
    GET    /api/research_tasks              - 获取任务列表（分页筛选）
        参数: status, assignee_id, creator_id, keyword, page, limit
        返回: 任务列表 + 分页信息

    GET    /api/research_tasks/stats        - 获取任务统计
        返回: 任务总数、状态分布、完成率等

    POST   /api/research_tasks              - 创建研究任务
        接收: title, description, assignee_id, deadline, priority
        需要导师/管理员权限

    GET    /api/research_tasks/{task_id}    - 获取任务详情
        返回: 任务完整信息 + 进度记录

    PUT    /api/research_tasks/{task_id}    - 更新任务信息
        接收: title, description, deadline, priority
        需要创建者/导师/管理员权限

    PUT    /api/research_tasks/{task_id}/progress - 更新任务进度
        接收: progress_value, note
        学生可更新自己被分配的任务进度

    DELETE /api/research_tasks/{task_id}    - 删除任务
        需要创建者/导师/管理员权限

路由配置:
    - 前缀: /api/research_tasks
    - 标签: 研究任务

权限要求:
    创建/删除: 导师 (teacher) 或管理员 (admin)
    更新进度: 被分配的学生 或 导师/管理员
    查看: 所有已登录用户

依赖模块:
    - services.task_service.TaskService: 任务服务
    - utils.auth_helper                : 认证依赖
    - database.connection              : 数据库连接

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from datetime import datetime
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from utils.auth_helper import get_current_user
from services.task_service import TaskService
from database.connection import get_db

router = APIRouter(prefix="/api/research_tasks", tags=["研究任务"])


@router.get("")
async def get_research_tasks(request: Request):
    """
    获取研究任务列表API
    支持分页、筛选和排序
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取查询参数
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        status_filter = request.query_params.get("status")
        priority_filter = request.query_params.get("priority")
        assignee_filter = request.query_params.get("assignee_id")
        type_filter = request.query_params.get("task_type")
        keyword_filter = request.query_params.get("keyword")
        sort_by = request.query_params.get("sort_by", "deadline")
        sort_order = request.query_params.get("sort_order", "asc")

        offset = (page - 1) * limit

        # 获取任务列表
        tasks = TaskService.get_tasks(
            user_id=current_user.id,
            user_role=current_user.role,
            status=status_filter,
            priority=priority_filter,
            assignee_id=int(assignee_filter) if assignee_filter else None,
            task_type=type_filter,
            keyword=keyword_filter,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

        # 获取总数
        total = TaskService.get_tasks_count(
            user_id=current_user.id,
            user_role=current_user.role,
            status=status_filter,
            priority=priority_filter,
            assignee_id=int(assignee_filter) if assignee_filter else None,
            task_type=type_filter,
            keyword=keyword_filter
        )

        # 计算分页信息
        total_pages = (total + limit - 1) // limit if total > 0 else 1

        # 获取负责人信息
        with get_db() as conn:
            cursor = conn.cursor()
            tasks_with_assignee = []
            for task in tasks:
                task_dict = task.to_dict()
                task_dict['display_status'] = task.get_display_status()
                task_dict['status_text'] = task.get_status_text()
                task_dict['priority_text'] = task.get_priority_text()

                # 获取负责人信息
                cursor.execute("SELECT id, username FROM users WHERE id = ?", (task.assignee_id,))
                assignee_row = cursor.fetchone()
                if assignee_row:
                    task_dict['assignee'] = {
                        'id': assignee_row[0],
                        'username': assignee_row[1]
                    }

                # 获取创建者信息
                cursor.execute("SELECT id, username FROM users WHERE id = ?", (task.creator_id,))
                creator_row = cursor.fetchone()
                if creator_row:
                    task_dict['creator'] = {
                        'id': creator_row[0],
                        'username': creator_row[1]
                    }

                tasks_with_assignee.append(task_dict)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "tasks": tasks_with_assignee,
                    "pagination": {
                        "current_page": page,
                        "per_page": limit,
                        "total": total,
                        "total_pages": total_pages,
                        "has_next": page < total_pages,
                        "has_prev": page > 1
                    }
                }
            }
        )
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取任务列表失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/stats")
async def get_research_task_stats(request: Request):
    """
    获取研究任务统计API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        stats = TaskService.get_task_stats(current_user.id, current_user.role)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": stats}
        )
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取任务统计失败", "error": "INTERNAL_ERROR"}
        )


@router.post("")
async def create_research_task(request: Request):
    """
    创建研究任务API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        title = data.get("title")
        description = data.get("description")
        priority = data.get("priority", "middle")
        deadline_str = data.get("deadline")
        assignee_id = data.get("assignee_id")

        if not title:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "任务标题不能为空", "error": "VALIDATION_ERROR"}
            )

        # 处理截止日期
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
            except:
                pass

        # 确定任务类型和负责人
        if current_user.role in ['admin', 'teacher']:
            # 导师可以创建导师任务
            task_type = data.get("task_type", "assigned")
            if not assignee_id:
                assignee_id = current_user.id  # 默认分配给自己
        else:
            # 学生只能创建个人任务
            task_type = "personal"
            assignee_id = current_user.id  # 学生创建的任务负责人必须是自己

        # 创建任务
        task = TaskService.create_task(
            title=title,
            creator_id=current_user.id,
            assignee_id=assignee_id,
            task_type=task_type,
            description=description,
            priority=priority,
            deadline=deadline
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "任务创建成功",
                "data": task.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "创建任务失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/{task_id}")
async def get_research_task_detail(task_id: int, request: Request):
    """
    获取任务详情API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "任务不存在", "error": "NOT_FOUND"}
            )

        # 权限检查
        if current_user.role not in ['admin', 'teacher']:
            if task.assignee_id != current_user.id and task.creator_id != current_user.id:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"success": False, "message": "无权限查看此任务", "error": "ACCESS_DENIED"}
                )

        task_dict = task.to_dict()
        task_dict['display_status'] = task.get_display_status()
        task_dict['status_text'] = task.get_status_text()
        task_dict['priority_text'] = task.get_priority_text()

        # 获取负责人和创建者信息
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users WHERE id = ?", (task.assignee_id,))
            assignee_row = cursor.fetchone()
            if assignee_row:
                task_dict['assignee'] = {'id': assignee_row[0], 'username': assignee_row[1]}

            cursor.execute("SELECT id, username FROM users WHERE id = ?", (task.creator_id,))
            creator_row = cursor.fetchone()
            if creator_row:
                task_dict['creator'] = {'id': creator_row[0], 'username': creator_row[1]}

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": task_dict}
        )
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取任务详情失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/{task_id}")
async def update_research_task(task_id: int, request: Request):
    """
    更新任务API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "任务不存在", "error": "NOT_FOUND"}
            )

        # 权限检查
        if not TaskService.check_permission(task, current_user.id, current_user.role, 'edit'):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "无权限编辑此任务", "error": "ACCESS_DENIED"}
            )

        data = await request.json()

        # 处理截止日期
        deadline_str = data.get("deadline")
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
            except:
                pass

        # 更新任务
        updated_task = TaskService.update_task(
            task_id,
            title=data.get("title"),
            description=data.get("description"),
            priority=data.get("priority"),
            status=data.get("status"),
            progress=data.get("progress"),
            assignee_id=data.get("assignee_id"),
            deadline=deadline
        )

        if not updated_task:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "更新失败", "error": "UPDATE_FAILED"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "任务更新成功",
                "data": updated_task.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新任务失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/{task_id}/progress")
async def update_research_task_progress(task_id: int, request: Request):
    """
    更新任务进度API（学生权限）
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "任务不存在", "error": "NOT_FOUND"}
            )

        # 权限检查：负责人可以更新进度
        if not TaskService.check_permission(task, current_user.id, current_user.role, 'update_progress'):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "无权限更新此任务进度", "error": "ACCESS_DENIED"}
            )

        data = await request.json()
        progress = data.get("progress", 0)
        task_status = data.get("status")

        # 更新进度
        updated_task = TaskService.update_progress(task_id, progress, task_status)

        if not updated_task:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "更新进度失败", "error": "UPDATE_FAILED"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "进度更新成功",
                "data": updated_task.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"更新进度失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新进度失败", "error": "INTERNAL_ERROR"}
        )


@router.delete("/{task_id}")
async def delete_research_task(task_id: int, request: Request):
    """
    删除任务API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "任务不存在", "error": "NOT_FOUND"}
            )

        # 权限检查
        if not TaskService.check_permission(task, current_user.id, current_user.role, 'delete'):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "无权限删除此任务", "error": "ACCESS_DENIED"}
            )

        # 删除任务
        success = TaskService.delete_task(task_id)

        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"success": True, "message": "任务删除成功"}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "删除失败", "error": "DELETE_FAILED"}
            )
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "删除任务失败", "error": "INTERNAL_ERROR"}
        )