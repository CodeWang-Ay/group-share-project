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

            if status:
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
        task_type: Optional[str] = None
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

            if status:
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