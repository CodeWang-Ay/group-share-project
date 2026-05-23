"""
研究任务业务逻辑服务
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from database.connection import get_db
from models.task import Task
from loguru import logger


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
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO research_tasks (
                    title, description, priority, status, progress,
                    assignee_id, creator_id, task_type, deadline,
                    created_at, updated_at
                ) VALUES (?, ?, ?, 'pending', 0, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                title, description, priority, assignee_id, creator_id, task_type,
                deadline.isoformat() if deadline else None
            ))

            task_id = cursor.lastrowid

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
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

    @staticmethod
    def get_task_by_id(task_id: int) -> Optional[Task]:
        """根据ID获取任务"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, priority, status, progress,
                       assignee_id, creator_id, task_type, deadline,
                       created_at, updated_at
                FROM research_tasks WHERE id = ?
            """, (task_id,))

            row = cursor.fetchone()
            if row:
                return Task.from_dict(dict(row))
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
        """
        获取任务列表

        Args:
            user_id: 当前用户ID
            user_role: 当前用户角色
            status: 状态筛选
            priority: 优先级筛选
            assignee_id: 负责人筛选
            task_type: 任务类型筛选
            keyword: 搜索关键词（标题模糊匹配）
            sort_by: 排序字段
            sort_order: 排序方向
            limit: 返回数量
            offset: 偏移量
        """
        with get_db() as conn:
            cursor = conn.cursor()

            # 构建查询条件
            where_conditions = []
            params = []

            # 权限筛选：学生只能看到自己相关的任务，导师可以看到所有任务
            if user_role not in ['admin', 'teacher']:
                # 学生：只能看到自己是负责人或创建者的任务
                where_conditions.append("(assignee_id = ? OR creator_id = ?)")
                params.extend([user_id, user_id])

            # 状态筛选：特殊处理 overdue（逾期）
            if status:
                if status == 'overdue':
                    # 逾期状态：未完成 + 截止日期已过期
                    where_conditions.append("status != 'completed' AND deadline IS NOT NULL AND deadline < CURRENT_TIMESTAMP")
                else:
                    where_conditions.append("status = ?")
                    params.append(status)

            if priority:
                where_conditions.append("priority = ?")
                params.append(priority)

            if assignee_id:
                where_conditions.append("assignee_id = ?")
                params.append(assignee_id)

            if task_type:
                where_conditions.append("task_type = ?")
                params.append(task_type)

            if keyword:
                where_conditions.append("title LIKE ?")
                params.append(f"%{keyword}%")

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # 排序处理
            valid_sort_fields = ['deadline', 'created_at', 'priority', 'updated_at']
            sort_by = sort_by if sort_by in valid_sort_fields else 'deadline'
            sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'

            # 优先级排序需要特殊处理
            if sort_by == 'priority':
                priority_order = """
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'middle' THEN 2
                        WHEN 'low' THEN 3
                    END
                """
                order_clause = f"ORDER BY {priority_order} {sort_order}"
            else:
                order_clause = f"ORDER BY {sort_by} {sort_order}"

            query = f"""
                SELECT id, title, description, priority, status, progress,
                       assignee_id, creator_id, task_type, deadline,
                       created_at, updated_at
                FROM research_tasks
                {where_clause}
                {order_clause}
                LIMIT ? OFFSET ?
            """

            cursor.execute(query, params + [limit, offset])
            rows = cursor.fetchall()

            return [Task.from_dict(dict(row)) for row in rows]

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
        with get_db() as conn:
            cursor = conn.cursor()

            where_conditions = []
            params = []

            # 权限筛选
            if user_role not in ['admin', 'teacher']:
                where_conditions.append("(assignee_id = ? OR creator_id = ?)")
                params.extend([user_id, user_id])

            # 状态筛选：特殊处理 overdue（逾期）
            if status:
                if status == 'overdue':
                    # 逾期状态：未完成 + 截止日期已过期
                    where_conditions.append("status != 'completed' AND deadline IS NOT NULL AND deadline < CURRENT_TIMESTAMP")
                else:
                    where_conditions.append("status = ?")
                    params.append(status)

            if priority:
                where_conditions.append("priority = ?")
                params.append(priority)

            if assignee_id:
                where_conditions.append("assignee_id = ?")
                params.append(assignee_id)

            if task_type:
                where_conditions.append("task_type = ?")
                params.append(task_type)

            if keyword:
                where_conditions.append("title LIKE ?")
                params.append(f"%{keyword}%")

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"SELECT COUNT(*) FROM research_tasks {where_clause}"
            cursor.execute(query, params)

            return cursor.fetchone()[0]

    @staticmethod
    def update_task(task_id: int, **kwargs) -> Optional[Task]:
        """
        更新任务信息

        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
        """
        allowed_fields = [
            'title', 'description', 'priority', 'status', 'progress',
            'assignee_id', 'deadline'
        ]

        update_data = {}
        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                if field == 'deadline' and isinstance(kwargs[field], datetime):
                    update_data[field] = kwargs[field].isoformat()
                else:
                    update_data[field] = kwargs[field]

        if not update_data:
            return None

        with get_db() as conn:
            cursor = conn.cursor()

            set_clause = ", ".join([f"{field} = ?" for field in update_data.keys()])
            values = list(update_data.values()) + [task_id]

            cursor.execute(f"""
                UPDATE research_tasks
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)

            if cursor.rowcount == 0:
                return None

            return TaskService.get_task_by_id(task_id)

    @staticmethod
    def update_progress(task_id: int, progress: int, status: Optional[str] = None) -> Optional[Task]:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度值 (0-100)
            status: 可选的状态更新
        """
        # 确保进度在有效范围内
        progress = max(0, min(100, progress))

        update_data = {'progress': progress}

        # 自动更新状态
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
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM research_tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_task_stats(user_id: int, user_role: str) -> Dict[str, int]:
        """
        获取任务统计信息

        Args:
            user_id: 当前用户ID
            user_role: 当前用户角色
        """
        with get_db() as conn:
            cursor = conn.cursor()

            # 权限筛选
            if user_role in ['admin', 'teacher']:
                where_clause = ""
                params = []
            else:
                where_clause = "WHERE (assignee_id = ? OR creator_id = ?)"
                params = [user_id, user_id]

            # 获取各状态统计
            query = f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                    COUNT(CASE WHEN status = 'ongoing' THEN 1 END) as ongoing_count,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count
                FROM research_tasks
                {where_clause}
            """
            cursor.execute(query, params)
            row = cursor.fetchone()

            # 计算逾期数量
            overdue_query = f"""
                SELECT COUNT(*) FROM research_tasks
                {where_clause}
                {' AND ' if where_clause else 'WHERE '} status != 'completed' AND deadline < CURRENT_TIMESTAMP
            """
            cursor.execute(overdue_query, params)
            overdue_count = cursor.fetchone()[0]

            return {
                'total': row[0] or 0,
                'pending_count': row[1] or 0,
                'ongoing_count': row[2] or 0,
                'completed_count': row[3] or 0,
                'overdue_count': overdue_count
            }

    @staticmethod
    def check_permission(
        task: Task,
        user_id: int,
        user_role: str,
        action: str
    ) -> bool:
        """
        检查用户对任务的操作权限

        Args:
            task: 任务对象
            user_id: 用户ID
            user_role: 用户角色
            action: 操作类型 ('create', 'edit', 'delete', 'update_progress')

        Returns:
            bool: 是否有权限
        """
        if action == 'create':
            # 创建权限：学生只能创建个人任务，导师可以创建导师任务
            if user_role == 'admin':
                return True
            elif user_role == 'teacher':
                return True  # 导师可以创建任意类型任务
            else:
                return True  # 学生可以创建个人任务（assignee限制在API层处理）

        elif action == 'edit':
            # 编辑权限
            if user_role == 'admin':
                return True
            elif user_role == 'teacher':
                # 导师可以编辑导师任务，以及自己创建的个人任务
                if task.task_type == 'assigned':
                    return True
                else:
                    return task.creator_id == user_id
            else:
                # 学生：导师任务只能更新进度，个人任务可以全部编辑
                if task.task_type == 'assigned':
                    return False  # 学生不能编辑导师任务（只能更新进度）
                else:
                    return task.creator_id == user_id

        elif action == 'update_progress':
            # 更新进度权限
            if user_role == 'admin':
                return True
            elif user_role == 'teacher':
                return True
            else:
                # 学生：如果是任务的负责人，可以更新进度
                return task.assignee_id == user_id

        elif action == 'delete':
            # 删除权限
            if user_role == 'admin':
                return True
            elif user_role == 'teacher':
                # 导师可以删除导师任务，以及自己创建的个人任务
                if task.task_type == 'assigned':
                    return True
                else:
                    return task.creator_id == user_id
            else:
                # 学生只能删除自己创建的个人任务
                return task.task_type == 'personal' and task.creator_id == user_id

        return False

    # ==================== API 异步方法（返回 {status_code, content}） ====================

    async def api_get_list(self, filters: Dict[str, Any], user_id: int, user_role: str) -> Dict[str, Any]:
        """获取任务列表 API"""
        from repositories.user_repository import UserRepository

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
        from datetime import datetime

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

        # 确定任务类型和负责人
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
        from repositories.user_repository import UserRepository

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
        from datetime import datetime

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