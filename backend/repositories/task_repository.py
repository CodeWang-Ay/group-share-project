"""
================================================================================
研究任务数据访问模块 (repositories/task_repository.py)
================================================================================

模块名称: backend/repositories/task_repository.py
功能描述: 研究任务数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - create_task(data)                    : 创建任务
    - get_by_id(task_id)                   : 获取任务详情
    - get_list(filters, limit, offset)     : 获取任务列表
    - get_count(filters)                   : 获取任务总数
    - update_task(task_id, data)           : 更新任务
    - delete_task(task_id)                 : 删除任务
    - get_stats(user_id, user_role)        : 获取统计信息

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-24
================================================================================
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from database.connection import get_db


class TaskRepository:
    """研究任务数据访问类"""

    @staticmethod
    def create_task(data: Dict[str, Any]) -> int:
        """创建任务，返回任务ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO research_tasks (
                    title, description, priority, status, progress,
                    assignee_id, creator_id, task_type, deadline,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                data.get('title'), data.get('description'), data.get('priority', 'middle'),
                data.get('status', 'pending'), data.get('progress', 0),
                data.get('assignee_id'), data.get('creator_id'), data.get('task_type', 'personal'),
                data.get('deadline')
            ))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, priority, status, progress,
                       assignee_id, creator_id, task_type, deadline,
                       created_at, updated_at
                FROM research_tasks WHERE id = ?
            """, (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_list(filters: Dict[str, Any], limit: int, offset: int) -> List[Dict[str, Any]]:
        """获取任务列表"""
        with get_db() as conn:
            cursor = conn.cursor()

            where_conditions = []
            params = []

            user_id = filters.get('user_id')
            user_role = filters.get('user_role')

            # 权限筛选
            if user_role not in ['admin', 'teacher']:
                where_conditions.append("(assignee_id = ? OR creator_id = ?)")
                params.extend([user_id, user_id])

            # 状态筛选
            status = filters.get('status')
            if status:
                if status == 'overdue':
                    where_conditions.append("status != 'completed' AND deadline IS NOT NULL AND deadline < CURRENT_TIMESTAMP")
                else:
                    where_conditions.append("status = ?")
                    params.append(status)

            if filters.get('priority'):
                where_conditions.append("priority = ?")
                params.append(filters.get('priority'))

            if filters.get('assignee_id'):
                where_conditions.append("assignee_id = ?")
                params.append(filters.get('assignee_id'))

            if filters.get('task_type'):
                where_conditions.append("task_type = ?")
                params.append(filters.get('task_type'))

            if filters.get('keyword'):
                where_conditions.append("title LIKE ?")
                params.append(f"%{filters.get('keyword')}%")

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # 排序处理
            sort_by = filters.get('sort_by', 'deadline')
            sort_order = 'DESC' if filters.get('sort_order', 'asc').lower() == 'desc' else 'ASC'

            valid_sort_fields = ['deadline', 'created_at', 'priority', 'updated_at']
            sort_by = sort_by if sort_by in valid_sort_fields else 'deadline'

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
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_count(filters: Dict[str, Any]) -> int:
        """获取任务总数"""
        with get_db() as conn:
            cursor = conn.cursor()

            where_conditions = []
            params = []

            user_id = filters.get('user_id')
            user_role = filters.get('user_role')

            if user_role not in ['admin', 'teacher']:
                where_conditions.append("(assignee_id = ? OR creator_id = ?)")
                params.extend([user_id, user_id])

            status = filters.get('status')
            if status:
                if status == 'overdue':
                    where_conditions.append("status != 'completed' AND deadline IS NOT NULL AND deadline < CURRENT_TIMESTAMP")
                else:
                    where_conditions.append("status = ?")
                    params.append(status)

            if filters.get('priority'):
                where_conditions.append("priority = ?")
                params.append(filters.get('priority'))

            if filters.get('assignee_id'):
                where_conditions.append("assignee_id = ?")
                params.append(filters.get('assignee_id'))

            if filters.get('task_type'):
                where_conditions.append("task_type = ?")
                params.append(filters.get('task_type'))

            if filters.get('keyword'):
                where_conditions.append("title LIKE ?")
                params.append(f"%{filters.get('keyword')}%")

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"SELECT COUNT(*) FROM research_tasks {where_clause}"
            cursor.execute(query, params)
            return cursor.fetchone()[0] or 0

    @staticmethod
    def update_task(task_id: int, data: Dict[str, Any]) -> bool:
        """更新任务"""
        allowed_fields = ['title', 'description', 'priority', 'status', 'progress', 'assignee_id', 'deadline']
        update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}

        if not update_data:
            return False

        with get_db() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            params = list(update_data.values()) + [task_id]
            cursor.execute(f"""
                UPDATE research_tasks
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, params)
            return cursor.rowcount > 0

    @staticmethod
    def delete_task(task_id: int) -> bool:
        """删除任务"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM research_tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_stats(user_id: int, user_role: str) -> Dict[str, int]:
        """获取统计信息"""
        with get_db() as conn:
            cursor = conn.cursor()

            if user_role in ['admin', 'teacher']:
                where_clause = ""
                params = []
            else:
                where_clause = "WHERE (assignee_id = ? OR creator_id = ?)"
                params = [user_id, user_id]

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