"""
================================================================================
材料数据访问模块 (repositories/material_repository.py)
================================================================================

模块名称: backend/repositories/material_repository.py
功能描述: 汇报材料数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - get_presenters_list(filters)       : 获取汇报人列表
    - get_meetings_with_presenters(...)   : 获取组会及汇报人
    - get_presenter_files(presenter_id)   : 获取汇报人文件
    - get_presenter_by_id(presenter_id)   : 获取汇报人信息
    - update_presenter_status(...)        : 更新汇报人状态
    - update_material_status(...)         : 更新材料状态
    - create_file(data)                   : 创建文件记录
    - get_file_by_id(file_id)             : 获取文件
    - get_meeting_materials(meeting_id)   : 获取组会材料

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Optional, Dict, Any, List
from database.connection import get_db


class MeetingMaterialRepository:
    """材料数据访问类"""

    @staticmethod
    def get_presenters_list(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取汇报人材料列表"""
        with get_db() as conn:
            cursor = conn.cursor()

            where_conditions = ["mp.material_required = 1"]
            params = []

            if filters.get('status'):
                where_conditions.append("mp.material_status = ?")
                params.append(filters['status'])

            if filters.get('meeting_id'):
                where_conditions.append("mp.meeting_id = ?")
                params.append(int(filters['meeting_id']))

            where_clause = "WHERE " + " AND ".join(where_conditions)

            query = f"""
                SELECT mp.id, mp.meeting_id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                       mp.material_status, mp.created_at, mp.updated_at,
                       m.title, m.scheduled_at, m.meeting_type, m.status as meeting_status,
                       u.username, u.role as user_role
                FROM meeting_presenters mp
                LEFT JOIN meetings m ON mp.meeting_id = m.id
                LEFT JOIN users u ON mp.user_id = u.id
                {where_clause}
                ORDER BY m.scheduled_at DESC, mp.created_at ASC
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()

            materials = []
            for row in rows:
                presenter_id = row[0]
                # 获取关联的文件
                cursor.execute("""
                    SELECT mf.id, mf.filename, mf.file_type, mf.file_size, mf.uploaded_at
                    FROM meeting_files mf
                    WHERE mf.presenter_id = ? AND mf.filename IS NOT NULL
                """, (presenter_id,))
                files = [dict(f) for f in cursor.fetchall()]

                materials.append({
                    "id": row[0],
                    "meeting_id": row[1],
                    "user_id": row[2],
                    "presenter_type": row[3],
                    "duration_minutes": row[4],
                    "status": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                    "meeting_title": row[8],
                    "meeting_scheduled_at": row[9],
                    "meeting_type": row[10],
                    "meeting_status": row[11],
                    "username": row[12],
                    "user_role": row[13],
                    "files": files
                })
            return materials

    @staticmethod
    def get_meetings_with_presenters(filters: Dict[str, Any], limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取组会列表及汇报人"""
        with get_db() as conn:
            cursor = conn.cursor()

            # 构建组会筛选条件
            where_conditions = ["m.status != 'cancelled'"]
            params = []

            # 组会状态筛选
            if filters.get('status'):
                where_conditions.append("m.status = ?")
                params.append(filters['status'])

            # 组会类型筛选
            if filters.get('meeting_type'):
                where_conditions.append("m.meeting_type = ?")
                params.append(filters['meeting_type'])

            where_clause = "WHERE " + " AND ".join(where_conditions)

            # 材料状态筛选参数
            material_status_filter = filters.get('material_status')

            # 如果有材料状态筛选，使用子查询只获取有匹配汇报人的组会
            if material_status_filter:
                cursor.execute(f"""
                    SELECT DISTINCT m.id, m.title, m.scheduled_at, m.meeting_type, m.status, m.location,
                           m.duration_total, m.description
                    FROM meetings m
                    INNER JOIN meeting_presenters mp ON m.id = mp.meeting_id
                    {where_clause} AND mp.material_status = ?
                    ORDER BY m.scheduled_at DESC
                    LIMIT ? OFFSET ?
                """, params + [material_status_filter, limit, offset])
            else:
                cursor.execute(f"""
                    SELECT m.id, m.title, m.scheduled_at, m.meeting_type, m.status, m.location,
                           m.duration_total, m.description
                    FROM meetings m
                    {where_clause}
                    ORDER BY m.scheduled_at DESC
                    LIMIT ? OFFSET ?
                """, params + [limit, offset])

            meetings_rows = cursor.fetchall()

            meetings = []
            for row in meetings_rows:
                meeting = dict(row)

                # 搜索过滤
                search_keyword = filters.get('search', '')
                if search_keyword and search_keyword.lower() not in (meeting.get('title', '') or '').lower():
                    continue

                # 获取该组会的汇报人（根据材料状态筛选）
                presenter_where = "mp.meeting_id = ?"
                presenter_params = [meeting['id']]

                if material_status_filter:
                    presenter_where += " AND mp.material_status = ?"
                    presenter_params.append(material_status_filter)

                cursor.execute(f"""
                    SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                           mp.material_status, mp.status, u.username
                    FROM meeting_presenters mp
                    LEFT JOIN users u ON mp.user_id = u.id
                    WHERE {presenter_where}
                    ORDER BY mp.created_at ASC
                """, presenter_params)
                presenters_rows = cursor.fetchall()

                # 如果筛选了材料状态但没有汇报人，跳过该组会
                if material_status_filter and len(presenters_rows) == 0:
                    continue

                presenters = []
                for p_row in presenters_rows:
                    presenter = dict(p_row)
                    presenter_id = presenter['id']

                    # 获取该汇报人的文件
                    cursor.execute("""
                        SELECT id, filename, file_path, file_size, file_type, uploaded_at
                        FROM meeting_files
                        WHERE presenter_id = ? AND filename IS NOT NULL
                    """, (presenter_id,))
                    presenter['files'] = [dict(f) for f in cursor.fetchall()]
                    presenters.append(presenter)

                meeting['presenters'] = presenters
                meetings.append(meeting)
            return meetings

    @staticmethod
    def get_meetings_count(filters: Dict[str, Any]) -> int:
        """获取符合条件的组会总数"""
        with get_db() as conn:
            cursor = conn.cursor()

            where_conditions = ["m.status != 'cancelled'"]
            params = []

            if filters.get('status'):
                where_conditions.append("m.status = ?")
                params.append(filters['status'])

            if filters.get('meeting_type'):
                where_conditions.append("m.meeting_type = ?")
                params.append(filters['meeting_type'])

            material_status_filter = filters.get('material_status')

            where_clause = "WHERE " + " AND ".join(where_conditions)

            # 搜索关键词筛选（需要在SQL层面处理才能正确计数）
            search_keyword = filters.get('search', '')
            if search_keyword:
                where_conditions.append("m.title LIKE ?")
                params.append(f"%{search_keyword}%")

            if material_status_filter:
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT m.id)
                    FROM meetings m
                    INNER JOIN meeting_presenters mp ON m.id = mp.meeting_id
                    {where_clause} AND mp.material_status = ?
                """, params + [material_status_filter])
            else:
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM meetings m
                    {where_clause}
                """, params)

            return cursor.fetchone()[0] or 0

    @staticmethod
    def get_presenter_files(presenter_id: int) -> List[Dict[str, Any]]:
        """获取汇报人的文件列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_path, file_size, file_type, uploaded_at
                FROM meeting_files
                WHERE presenter_id = ? AND filename IS NOT NULL
                ORDER BY uploaded_at DESC
            """, (presenter_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_presenter_by_id(presenter_id: int) -> Optional[Dict[str, Any]]:
        """获取汇报人信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mp.id, mp.user_id, mp.meeting_id, mp.status, mp.presenter_type, mp.material_status
                FROM meeting_presenters mp
                WHERE mp.id = ?
            """, (presenter_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_presenter_status(presenter_id: int, status: str) -> bool:
        """更新汇报人状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE meeting_presenters
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, presenter_id))
            return cursor.rowcount > 0

    @staticmethod
    def update_material_status(presenter_id: int, material_status: str) -> bool:
        """更新材料状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE meeting_presenters
                SET material_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (material_status, presenter_id))
            return cursor.rowcount > 0

    @staticmethod
    def create_file(data: Dict[str, Any]) -> int:
        """创建文件记录，返回文件ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meeting_files (meeting_id, presenter_id, filename, file_path, file_size, file_type, uploaded_by, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                data.get('meeting_id'),
                data.get('presenter_id'),
                data.get('filename'),
                data.get('file_path'),
                data.get('file_size'),
                data.get('file_type'),
                data.get('uploaded_by')
            ))
            return cursor.lastrowid

    @staticmethod
    def get_file_by_id(file_id: int) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mf.id, mf.filename, mf.file_path, mf.file_type
                FROM meeting_files mf
                WHERE mf.id = ? AND mf.filename IS NOT NULL
            """, (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_meeting_materials(meeting_id: int) -> List[Dict[str, Any]]:
        """获取组会的所有汇报材料"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                       mp.material_status, u.username
                FROM meeting_presenters mp
                LEFT JOIN users u ON mp.user_id = u.id
                WHERE mp.meeting_id = ?
                ORDER BY mp.created_at ASC
            """, (meeting_id,))
            rows = cursor.fetchall()

            materials = []
            for row in rows:
                presenter_id = row[0]
                cursor.execute("""
                    SELECT mf.id, mf.filename, mf.file_type, mf.file_size, mf.uploaded_at
                    FROM meeting_files mf
                    WHERE mf.presenter_id = ? AND mf.filename IS NOT NULL
                """, (presenter_id,))
                files = [dict(f) for f in cursor.fetchall()]

                materials.append({
                    "presenter_id": presenter_id,
                    "user_id": row[1],
                    "username": row[5],
                    "real_name": row[5],
                    "presenter_type": row[2],
                    "duration_minutes": row[3],
                    "material_status": row[4],
                    "files": files
                })
            return materials