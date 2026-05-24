"""
================================================================================
研究任务业务逻辑模块 (services/task_service.py)
================================================================================

模块名称: backend/services/task_service.py
功能描述: 研究任务业务逻辑，返回 {status_code, content} 格式

Service 类方法:
    TaskService:
        - create_task(...)                       : 创建任务
        - get_task_by_id(task_id)                : 获取任务详情
        - get_tasks(...)                         : 获取任务列表
        - get_tasks_count(...)                   : 获取任务总数
        - update_task(...)                       : 更新任务
        - update_progress(...)                   : 更新任务进度
        - delete_task(task_id)                   : 删除任务
        - get_task_stats(...)                    : 获取统计信息
        - check_permission(...)                  : 检查权限

        - api_get_list(...)                      : API - 获取任务列表
        - api_get_stats(...)                     : API - 获取统计
        - api_create(...)                        : API - 创建任务
        - api_get_detail(...)                    : API - 获取详情
        - api_update(...)                        : API - 更新任务
        - api_update_progress(...)               : API - 更新进度
        - api_delete(...)                        : API - 删除任务

职责:
    - 所有业务逻辑写在这里
    - 调用 TaskRepository 进行数据操作
    - 返回 {status_code: int, content: dict} 格式

作者: wjg
创建日期: 2026-05-24
================================================================================
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from models.task import Task


class TaskService:
    """研究任务服务类"""

    # 优先级常量
    PRIORITY_HIGH = 'high'
    PRIORITY_MIDDLE = 'middle'
    PRIORITY_LOW = 'low'

    # 状态常量
    STATUS_PENDING = 'pending'
    STATUS_ONGOING = 'ongoing'
    STATUS_COMPLETED = 'completed'

    # 任务类型常量
    TYPE_PERSONAL = 'personal'
    TYPE_ASSIGNED = 'assigned'

    @staticmethod
    def create_task(
        title: str,
        creator_id: int,
        assignee_id: int,
        task_type: str = 'personal',
        description: Optional[str] = None,
        priority: str = 'middle',
        deadline: Optional[datetime] = None
    ) -> Task:
        """创建任务"""
        data = {
            'title': title,
            'description': description,
            'priority': priority,
            'status': 'pending',
            'progress': 0,
            'assignee_id': assignee_id,
            'creator_id': creator_id,
            'task_type': task_type,
            'deadline': deadline.isoformat() if deadline else None
        }

        task_id = TaskRepository.create_task(data)
        now = datetime.now()

        return Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            status='pending',
            progress=0,
            assignee_id=assignee_id,
            creator_id=creator_id,
            task_type=task_type,
            deadline=deadline,
            created_at=now,
            updated_at=now
        )

    @staticmethod
    def get_task_by_id(task_id: int) -> Optional[Task]:
        """根据ID获取任务"""
        row = TaskRepository.get_by_id(task_id)
        if row:
            return Task.from_dict(row)
        return None

    @staticmethod
    def get_tasks(
        user_id: int,
        user_role: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        task_type: Optional[str] = None,
        keyword: Optional[str] = None,
        sort_by: str = 'deadline',
        sort_order: str = 'asc',
        limit: int = 10,
        offset: int = 0
    ) -> List[Task]:
        """获取任务列表"""
        filters = {
            'user_id': user_id,
            'user_role': user_role,
            'status': status,
            'priority': priority,
            'assignee_id': assignee_id,
            'task_type': task_type,
            'keyword': keyword,
            'sort_by': sort_by,
            'sort_order': sort_order
        }

        rows = TaskRepository.get_list(filters, limit, offset)
        return [Task.from_dict(row) for row in rows]

    @staticmethod
    def get_tasks_count(
        user_id: int,
        user_role: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        task_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> int:
        """获取任务总数"""
        filters = {
            'user_id': user_id,
            'user_role': user_role,
            'status': status,
            'priority': priority,
            'assignee_id': assignee_id,
            'task_type': task_type,
            'keyword': keyword
        }
        return TaskRepository.get_count(filters)

    @staticmethod
    def update_task(task_id: int, **kwargs) -> Optional[Task]:
        """更新任务信息"""
        update_data = {}
        allowed_fields = ['title', 'description', 'priority', 'status', 'progress', 'assignee_id', 'deadline']

        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                if field == 'deadline' and isinstance(kwargs[field], datetime):
                    update_data[field] = kwargs[field].isoformat()
                else:
                    update_data[field] = kwargs[field]

        if not update_data:
            return None

        success = TaskRepository.update_task(task_id, update_data)
        if not success:
            return None

        return TaskService.get_task_by_id(task_id)

    @staticmethod
    def update_progress(task_id: int, progress: int, status: Optional[str] = None) -> Optional[Task]:
        """更新任务进度"""
        progress = max(0, min(100, progress))

        update_data = {'progress': progress}

        if progress == 100:
            update_data['status'] = 'completed'
        elif progress > 0 and status != 'completed':
            update_data['status'] = 'ongoing'
        elif status:
            update_data['status'] = status

        return TaskService.update_task(task_id, **update_data)

    @staticmethod
    def delete_task(task_id: int) -> bool:
        """删除任务"""
        return TaskRepository.delete_task(task_id)

    @staticmethod
    def get_task_stats(user_id: int, user_role: str) -> Dict[str, int]:
        """获取任务统计信息"""
        return TaskRepository.get_stats(user_id, user_role)

    @staticmethod
    def check_permission(
        task: Task,
        user_id: int,
        user_role: str,
        action: str
    ) -> bool:
        """检查用户对任务的操作权限"""
        if action == 'create':
            if user_role == 'admin':
                return True
            elif user_role == 'teacher':
                return True
            else:
                return True

        elif action == 'edit':
            if user_role == 'admin':
                return True
            elif user_role == 'teacher':
                if task.task_type == 'assigned':
                    return True
                else:
                    return task.creator_id == user_id
            else:
                if task.task_type == 'assigned':
                    return False
                else:
                    return task.creator_id == user_id

        elif action == 'update_progress':
            if user_role == 'admin':
                return True
            elif user_role == 'teacher':
                return True
            else:
                return task.assignee_id == user_id

        elif action == 'delete':
            if user_role == 'admin':
                return True
            elif user_role == 'teacher':
                if task.task_type == 'assigned':
                    return True
                else:
                    return task.creator_id == user_id
            else:
                return task.task_type == 'personal' and task.creator_id == user_id

        return False

    # ==================== API 异步方法（返回 {status_code, content}） ====================

    async def api_get_list(self, filters: Dict[str, Any], user_id: int, user_role: str) -> Dict[str, Any]:
        """获取任务列表 API"""
        page = filters.get('page', 1)
        limit = filters.get('limit', 10)
        offset = (page - 1) * limit

        tasks = TaskService.get_tasks(
            user_id=user_id, user_role=user_role,
            status=filters.get('status'), priority=filters.get('priority'),
            assignee_id=int(filters.get('assignee_id')) if filters.get('assignee_id') else None,
            task_type=filters.get('task_type'), keyword=filters.get('keyword'),
            sort_by=filters.get('sort_by', 'deadline'), sort_order=filters.get('sort_order', 'asc'),
            limit=limit, offset=offset
        )

        total = TaskService.get_tasks_count(
            user_id=user_id, user_role=user_role,
            status=filters.get('status'), priority=filters.get('priority'),
            assignee_id=int(filters.get('assignee_id')) if filters.get('assignee_id') else None,
            task_type=filters.get('task_type'), keyword=filters.get('keyword')
        )

        total_pages = (total + limit - 1) // limit if total > 0 else 1

        tasks_with_assignee = []
        for task in tasks:
            task_dict = task.to_dict()
            task_dict['display_status'] = task.get_display_status()
            task_dict['status_text'] = task.get_status_text()
            task_dict['priority_text'] = task.get_priority_text()

            assignee_data = UserRepository.get_by_id(task.assignee_id)
            if assignee_data:
                task_dict['assignee'] = {'id': assignee_data['id'], 'username': assignee_data['username']}

            creator_data = UserRepository.get_by_id(task.creator_id)
            if creator_data:
                task_dict['creator'] = {'id': creator_data['id'], 'username': creator_data['username']}

            tasks_with_assignee.append(task_dict)

        return {"status_code": 200, "content": {
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
        }}

    async def api_get_stats(self, user_id: int, user_role: str) -> Dict[str, Any]:
        """获取任务统计 API"""
        stats = TaskService.get_task_stats(user_id, user_role)
        return {"status_code": 200, "content": {"success": True, "data": stats}}

    async def api_create(self, data: Dict[str, Any], user_id: int, user_role: str) -> Dict[str, Any]:
        """创建任务 API"""
        title = data.get("title")
        if not title:
            return {"status_code": 400, "content": {"success": False, "message": "任务标题不能为空", "error": "VALIDATION_ERROR"}}

        deadline_str = data.get("deadline")
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
            except:
                pass

        if user_role in ['admin', 'teacher']:
            task_type = data.get("task_type", "assigned")
            assignee_id = data.get("assignee_id") or user_id
        else:
            task_type = "personal"
            assignee_id = user_id

        task = TaskService.create_task(
            title=title, creator_id=user_id, assignee_id=assignee_id,
            task_type=task_type, description=data.get("description"),
            priority=data.get("priority", "middle"), deadline=deadline
        )

        return {"status_code": 201, "content": {"success": True, "message": "任务创建成功", "data": task.to_dict()}}

    async def api_get_detail(self, task_id: int, user_id: int, user_role: str) -> Dict[str, Any]:
        """获取任务详情 API"""
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return {"status_code": 404, "content": {"success": False, "message": "任务不存在", "error": "NOT_FOUND"}}

        if user_role not in ['admin', 'teacher']:
            if task.assignee_id != user_id and task.creator_id != user_id:
                return {"status_code": 403, "content": {"success": False, "message": "无权限查看此任务", "error": "ACCESS_DENIED"}}

        task_dict = task.to_dict()
        task_dict['display_status'] = task.get_display_status()
        task_dict['status_text'] = task.get_status_text()
        task_dict['priority_text'] = task.get_priority_text()

        assignee_data = UserRepository.get_by_id(task.assignee_id)
        if assignee_data:
            task_dict['assignee'] = {'id': assignee_data['id'], 'username': assignee_data['username']}

        creator_data = UserRepository.get_by_id(task.creator_id)
        if creator_data:
            task_dict['creator'] = {'id': creator_data['id'], 'username': creator_data['username']}

        return {"status_code": 200, "content": {"success": True, "data": task_dict}}

    async def api_update(self, task_id: int, data: Dict[str, Any], user_id: int, user_role: str) -> Dict[str, Any]:
        """更新任务 API"""
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return {"status_code": 404, "content": {"success": False, "message": "任务不存在", "error": "NOT_FOUND"}}

        if not TaskService.check_permission(task, user_id, user_role, 'edit'):
            return {"status_code": 403, "content": {"success": False, "message": "无权限编辑此任务", "error": "ACCESS_DENIED"}}

        deadline_str = data.get("deadline")
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
            except:
                pass

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
            return {"status_code": 500, "content": {"success": False, "message": "更新失败", "error": "UPDATE_FAILED"}}

        return {"status_code": 200, "content": {"success": True, "message": "任务更新成功", "data": updated_task.to_dict()}}

    async def api_update_progress(self, task_id: int, data: Dict[str, Any], user_id: int, user_role: str) -> Dict[str, Any]:
        """更新任务进度 API"""
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return {"status_code": 404, "content": {"success": False, "message": "任务不存在", "error": "NOT_FOUND"}}

        if not TaskService.check_permission(task, user_id, user_role, 'update_progress'):
            return {"status_code": 403, "content": {"success": False, "message": "无权限更新此任务进度", "error": "ACCESS_DENIED"}}

        updated_task = TaskService.update_progress(task_id, data.get("progress", 0), data.get("status"))

        if not updated_task:
            return {"status_code": 500, "content": {"success": False, "message": "更新进度失败", "error": "UPDATE_FAILED"}}

        return {"status_code": 200, "content": {"success": True, "message": "进度更新成功", "data": updated_task.to_dict()}}

    async def api_delete(self, task_id: int, user_id: int, user_role: str) -> Dict[str, Any]:
        """删除任务 API"""
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return {"status_code": 404, "content": {"success": False, "message": "任务不存在", "error": "NOT_FOUND"}}

        if not TaskService.check_permission(task, user_id, user_role, 'delete'):
            return {"status_code": 403, "content": {"success": False, "message": "无权限删除此任务", "error": "ACCESS_DENIED"}}

        success = TaskService.delete_task(task_id)
        if not success:
            return {"status_code": 500, "content": {"success": False, "message": "删除失败", "error": "DELETE_FAILED"}}

        return {"status_code": 200, "content": {"success": True, "message": "任务删除成功"}}