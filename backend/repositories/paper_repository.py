"""
================================================================================
文献数据访问模块 (repositories/paper_repository.py)
================================================================================

模块名称: backend/repositories/paper_repository.py
功能描述: 文献数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - check_duplicate(...)                 : 去重校验
    - get_user_name(user_id)               : 获取用户名
    - create_paper(data)                   : 创建文献
    - create_personal_paper(data)          : 创建个人文献
    - get_paper_by_id(paper_id)            : 获取文献
    - get_personal_paper_by_id(paper_id)   : 获取个人文献
    - get_paper_list(filters, ...)         : 获取文献列表
    - get_paper_count(filters)             : 获取文献总数
    - get_personal_paper_list(...)         : 获取个人文献列表
    - get_personal_paper_count(...)        : 获取个人文献总数
    - update_paper(paper_id, data)         : 更新文献
    - update_personal_paper(paper_id, data): 更新个人文献
    - delete_paper(paper_id)               : 删除文献
    - delete_personal_paper(paper_id)      : 删除个人文献
    - get_tags()                           : 获取标签列表
    - get_or_create_tag(name, user_id)     : 获取或创建标签
    - add_paper_tag(paper_id, tag_id)      : 添加文献标签
    - add_personal_paper_tag(paper_id, tag_id): 添加个人文献标签
    - get_paper_stats(user_id, library_type): 获取统计信息
    - toggle_star(paper_id, user_id, ...)  : 收藏/取消收藏
    - update_read_status(paper_id, ...)    : 更新阅读状态
    - increment_download_count(paper_id)   : 增加下载次数
    - get_paper_user_relation(...)         : 获取文献用户关系
    - create_paper_user_relation(...)      : 创建文献用户关系
    - update_paper_user_relation(...)      : 更新文献用户关系

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-24
================================================================================
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from database.connection import get_db


class PaperRepository:
    """文献数据访问类"""

    @staticmethod
    def check_duplicate(library_type: str, user_id: Optional[int] = None,
                        file_hash: Optional[str] = None, doi: Optional[str] = None,
                        title: Optional[str] = None, authors: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """去重校验：DOI、file_hash、标题+作者组合"""
        with get_db() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if file_hash:
                conditions.append("file_hash = ?")
                params.append(file_hash)
            if doi:
                conditions.append("doi = ?")
                params.append(doi)
            if title and authors:
                conditions.append("title = ? AND authors = ?")
                params.extend([title, authors])

            if not conditions:
                return None

            if library_type == 'team':
                query = f"""
                    SELECT id, title FROM papers
                    WHERE team_library = 1 AND is_deleted = 0
                    AND ({' OR '.join(conditions)})
                    LIMIT 1
                """
            else:
                query = f"""
                    SELECT id, title FROM personal_papers
                    WHERE owner_user_id = ?
                    AND ({' OR '.join(conditions)})
                    LIMIT 1
                """
                params.insert(0, user_id)

            cursor.execute(query, params)
            result = cursor.fetchone()
            return {'id': result[0], 'title': result[1]} if result else None

    @staticmethod
    def get_user_name(user_id: int) -> Optional[str]:
        """获取用户名"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    @staticmethod
    def create_paper(data: Dict[str, Any]) -> int:
        """创建文献，返回文献ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO papers (
                    title, authors, year, journal, doi, abstract,
                    arxiv_link, semantic_scholar_link, pdf_path,
                    file_hash, pdf_size, team_library, uploader_id,
                    created_at, is_deleted, download_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP, 0, 0)
            """, (
                data.get('title'), data.get('authors'), data.get('year'),
                data.get('journal'), data.get('doi'), data.get('abstract'),
                data.get('arxiv_link'), data.get('semantic_scholar_link'),
                data.get('pdf_path'),
                data.get('file_hash'), data.get('pdf_size'),
                data.get('uploader_id')
            ))
            return cursor.lastrowid

    @staticmethod
    def create_personal_paper(data: Dict[str, Any]) -> int:
        """创建个人文献，返回文献ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO personal_papers (
                    title, authors, year, journal, doi, abstract,
                    arxiv_link, semantic_scholar_link, pdf_path,
                    file_hash, pdf_size, owner_user_id, source_paper_id,
                    created_at, download_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
            """, (
                data.get('title'), data.get('authors'), data.get('year'),
                data.get('journal'), data.get('doi'), data.get('abstract'),
                data.get('arxiv_link'), data.get('semantic_scholar_link'),
                data.get('pdf_path'),
                data.get('file_hash'), data.get('pdf_size'),
                data.get('owner_user_id'), data.get('source_paper_id')
            ))
            return cursor.lastrowid

    @staticmethod
    def get_paper_by_id(paper_id: int) -> Optional[Dict[str, Any]]:
        """获取文献"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, authors, year, journal, doi, abstract,
                       arxiv_link, semantic_scholar_link, pdf_path,
                       file_hash, pdf_size, team_library, uploader_id,
                       created_at, is_deleted, download_count
                FROM papers WHERE id = ? AND is_deleted = 0
            """, (paper_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_personal_paper_by_id(paper_id: int) -> Optional[Dict[str, Any]]:
        """获取个人文献"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, authors, year, journal, doi, abstract,
                       arxiv_link, semantic_scholar_link, pdf_path,
                       file_hash, pdf_size, owner_user_id, source_paper_id,
                       created_at, download_count
                FROM personal_papers WHERE id = ?
            """, (paper_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_paper_list(filters: Dict[str, Any], limit: int, offset: int, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取团队文献列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            where_conditions = ["p.team_library = 1", "p.is_deleted = 0"]
            params = []

            if filters.get('keyword'):
                where_conditions.append("p.title LIKE ?")
                params.append(f"%{filters['keyword']}%")
            if filters.get('tag'):
                where_conditions.append("EXISTS (SELECT 1 FROM paper_tags pt JOIN tags t ON pt.tag_id = t.id WHERE pt.paper_id = p.id AND t.name = ?)")
                params.append(filters['tag'])
            if filters.get('year'):
                where_conditions.append("p.year = ?")
                params.append(filters['year'])

            # 阅读状态筛选（需要关联 paper_user_relations 表）
            if filters.get('status') and user_id:
                status = filters.get('status')
                if status == 'unread':
                    # 未读：没有关联记录 或 关联记录的 read_status = 'unread'
                    where_conditions.append("(pur.read_status = 'unread' OR pur.id IS NULL)")
                elif status == 'reading':
                    where_conditions.append("pur.read_status = 'reading'")
                elif status == 'read':
                    where_conditions.append("pur.read_status = 'read'")

            # 收藏筛选
            if filters.get('starred') is not None and user_id:
                starred = filters.get('starred')
                if starred:
                    where_conditions.append("pur.is_starred = 1")
                else:
                    where_conditions.append("(pur.is_starred = 0 OR pur.id IS NULL)")

            where_clause = "WHERE " + " AND ".join(where_conditions)
            order_by = "p.created_at DESC" if filters.get('sort') == 'newest' else "p.created_at ASC"

            # 如果有状态或收藏筛选，需要 LEFT JOIN paper_user_relations
            need_join = (filters.get('status') and user_id) or (filters.get('starred') is not None and user_id)
            if need_join:
                query = f"""
                    SELECT p.id, p.title, p.authors, p.year, p.journal, p.doi, p.abstract,
                           p.pdf_path, p.pdf_size, p.uploader_id,
                           p.created_at, p.download_count, pur.read_status, pur.is_starred
                    FROM papers p
                    LEFT JOIN paper_user_relations pur ON p.id = pur.paper_id AND pur.user_id = ?
                    {where_clause}
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                """
                params = [user_id] + params + [limit, offset]
            else:
                query = f"""
                    SELECT p.id, p.title, p.authors, p.year, p.journal, p.doi, p.abstract,
                           p.pdf_path, p.pdf_size, p.uploader_id,
                           p.created_at, p.download_count
                    FROM papers p
                    {where_clause}
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                """
                params = params + [limit, offset]

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_paper_count(filters: Dict[str, Any], user_id: Optional[int] = None) -> int:
        """获取团队文献总数"""
        with get_db() as conn:
            cursor = conn.cursor()
            where_conditions = ["p.team_library = 1", "p.is_deleted = 0"]
            params = []

            if filters.get('keyword'):
                where_conditions.append("p.title LIKE ?")
                params.append(f"%{filters['keyword']}%")
            if filters.get('tag'):
                where_conditions.append("EXISTS (SELECT 1 FROM paper_tags pt JOIN tags t ON pt.tag_id = t.id WHERE pt.paper_id = p.id AND t.name = ?)")
                params.append(filters['tag'])
            if filters.get('year'):
                where_conditions.append("p.year = ?")
                params.append(filters['year'])

            # 阅读状态筛选
            if filters.get('status') and user_id:
                status = filters.get('status')
                if status == 'unread':
                    where_conditions.append("(pur.read_status = 'unread' OR pur.id IS NULL)")
                elif status == 'reading':
                    where_conditions.append("pur.read_status = 'reading'")
                elif status == 'read':
                    where_conditions.append("pur.read_status = 'read'")

            # 收藏筛选
            if filters.get('starred') is not None and user_id:
                starred = filters.get('starred')
                if starred:
                    where_conditions.append("pur.is_starred = 1")
                else:
                    where_conditions.append("(pur.is_starred = 0 OR pur.id IS NULL)")

            where_clause = "WHERE " + " AND ".join(where_conditions)

            need_join = (filters.get('status') and user_id) or (filters.get('starred') is not None and user_id)
            if need_join:
                query = f"SELECT COUNT(*) FROM papers p LEFT JOIN paper_user_relations pur ON p.id = pur.paper_id AND pur.user_id = ? {where_clause}"
                params = [user_id] + params
            else:
                query = f"SELECT COUNT(*) FROM papers p {where_clause}"

            cursor.execute(query, params)
            return cursor.fetchone()[0] or 0

    @staticmethod
    def get_personal_paper_list(user_id: int, filters: Dict[str, Any], limit: int, offset: int) -> List[Dict[str, Any]]:
        """获取个人文献列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            where_conditions = ["pp.owner_user_id = ?"]
            params = [user_id]

            if filters.get('keyword'):
                where_conditions.append("pp.title LIKE ?")
                params.append(f"%{filters['keyword']}%")

            # 阅读状态筛选（需要关联 paper_user_relations 表）
            if filters.get('status'):
                status = filters.get('status')
                if status == 'unread':
                    where_conditions.append("(pur.read_status = 'unread' OR pur.id IS NULL)")
                elif status == 'reading':
                    where_conditions.append("pur.read_status = 'reading'")
                elif status == 'read':
                    where_conditions.append("pur.read_status = 'read'")

            # 收藏筛选
            if filters.get('starred') is not None:
                starred = filters.get('starred')
                if starred:
                    where_conditions.append("pur.is_starred = 1")
                else:
                    where_conditions.append("(pur.is_starred = 0 OR pur.id IS NULL)")

            where_clause = "WHERE " + " AND ".join(where_conditions)
            order_by = "pp.created_at DESC" if filters.get('sort') == 'newest' else "pp.created_at ASC"

            # 如果有状态或收藏筛选，需要 LEFT JOIN paper_user_relations
            need_join = filters.get('status') or (filters.get('starred') is not None)
            if need_join:
                query = f"""
                    SELECT pp.id, pp.title, pp.authors, pp.year, pp.journal, pp.doi, pp.abstract,
                           pp.pdf_path, pp.pdf_size, pp.owner_user_id, pp.source_paper_id,
                           pp.created_at, pp.download_count, pur.read_status, pur.is_starred
                    FROM personal_papers pp
                    LEFT JOIN paper_user_relations pur ON pp.id = pur.personal_paper_id AND pur.user_id = ?
                    {where_clause}
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                """
                params = [user_id] + params + [limit, offset]
            else:
                query = f"""
                    SELECT pp.id, pp.title, pp.authors, pp.year, pp.journal, pp.doi, pp.abstract,
                           pp.pdf_path, pp.pdf_size, pp.owner_user_id, pp.source_paper_id,
                           pp.created_at, pp.download_count
                    FROM personal_papers pp
                    {where_clause}
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                """
                params = params + [limit, offset]

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_personal_paper_count(user_id: int, filters: Dict[str, Any]) -> int:
        """获取个人文献总数"""
        with get_db() as conn:
            cursor = conn.cursor()
            where_conditions = ["pp.owner_user_id = ?"]
            params = [user_id]

            if filters.get('keyword'):
                where_conditions.append("pp.title LIKE ?")
                params.append(f"%{filters['keyword']}%")

            # 阅读状态筛选
            if filters.get('status'):
                status = filters.get('status')
                if status == 'unread':
                    where_conditions.append("(pur.read_status = 'unread' OR pur.id IS NULL)")
                elif status == 'reading':
                    where_conditions.append("pur.read_status = 'reading'")
                elif status == 'read':
                    where_conditions.append("pur.read_status = 'read'")

            # 收藏筛选
            if filters.get('starred') is not None:
                starred = filters.get('starred')
                if starred:
                    where_conditions.append("pur.is_starred = 1")
                else:
                    where_conditions.append("(pur.is_starred = 0 OR pur.id IS NULL)")

            where_clause = "WHERE " + " AND ".join(where_conditions)

            need_join = filters.get('status') or (filters.get('starred') is not None)
            if need_join:
                query = f"SELECT COUNT(*) FROM personal_papers pp LEFT JOIN paper_user_relations pur ON pp.id = pur.personal_paper_id AND pur.user_id = ? {where_clause}"
                params = [user_id] + params
            else:
                query = f"SELECT COUNT(*) FROM personal_papers pp {where_clause}"

            cursor.execute(query, params)
            return cursor.fetchone()[0] or 0

    @staticmethod
    def update_paper(paper_id: int, data: Dict[str, Any]) -> bool:
        """更新文献"""
        allowed_fields = ['title', 'authors', 'year', 'journal', 'doi', 'abstract',
                          'arxiv_link', 'semantic_scholar_link']
        update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}

        if not update_data:
            return False

        with get_db() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            params = list(update_data.values()) + [datetime.now().isoformat(), paper_id]
            cursor.execute(f"UPDATE papers SET {set_clause}, updated_at = ? WHERE id = ?", params)
            return cursor.rowcount > 0

    @staticmethod
    def update_personal_paper(paper_id: int, data: Dict[str, Any]) -> bool:
        """更新个人文献"""
        allowed_fields = ['title', 'authors', 'year', 'journal', 'doi', 'abstract',
                          'arxiv_link', 'semantic_scholar_link']
        update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}

        if not update_data:
            return False

        with get_db() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            params = list(update_data.values()) + [datetime.now().isoformat(), paper_id]
            cursor.execute(f"UPDATE personal_papers SET {set_clause}, updated_at = ? WHERE id = ?", params)
            return cursor.rowcount > 0

    @staticmethod
    def delete_paper(paper_id: int) -> bool:
        """删除文献（软删除）"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE papers SET is_deleted = 1, updated_at = ? WHERE id = ?", (datetime.now().isoformat(), paper_id))
            return cursor.rowcount > 0

    @staticmethod
    def delete_personal_paper(paper_id: int) -> bool:
        """删除个人文献"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM personal_papers WHERE id = ?", (paper_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_tags() -> List[Dict[str, Any]]:
        """获取标签列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, tag_type, created_by, created_at FROM tags ORDER BY tag_type, name")
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_or_create_tag(name: str, user_id: int) -> int:
        """获取或创建标签，返回标签ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            cursor.execute("""
                INSERT INTO tags (name, tag_type, created_by, created_at)
                VALUES (?, 'custom', ?, ?)
            """, (name, user_id, datetime.now().isoformat()))
            return cursor.lastrowid

    @staticmethod
    def add_paper_tag(paper_id: int, tag_id: int) -> bool:
        """添加文献标签"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)", (paper_id, tag_id))
            return cursor.rowcount > 0

    @staticmethod
    def add_personal_paper_tag(paper_id: int, tag_id: int) -> bool:
        """添加个人文献标签"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_paper_tags (
                    personal_paper_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (personal_paper_id, tag_id)
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO personal_paper_tags (personal_paper_id, tag_id) VALUES (?, ?)", (paper_id, tag_id))
            return cursor.rowcount > 0

    @staticmethod
    def get_paper_stats(user_id: Optional[int] = None, library_type: Optional[str] = None) -> Dict[str, Any]:
        """获取文献统计"""
        with get_db() as conn:
            cursor = conn.cursor()
            if library_type == 'private' or library_type == 'personal':
                # 个人文献库总数
                cursor.execute("""
                    SELECT COUNT(*) as total, SUM(pdf_size) as total_size
                    FROM personal_papers WHERE owner_user_id = ?
                """, (user_id,))
                row = cursor.fetchone()
                total = row[0] or 0

                # 未读数量：没有关联记录或 read_status='unread'
                cursor.execute("""
                    SELECT COUNT(*) FROM personal_papers pp
                    LEFT JOIN paper_user_relations pur ON pp.id = pur.personal_paper_id AND pur.user_id = ?
                    WHERE pp.owner_user_id = ? AND (pur.read_status = 'unread' OR pur.id IS NULL)
                """, (user_id, user_id))
                unread = cursor.fetchone()[0] or 0

                # 收藏数
                cursor.execute("""
                    SELECT COUNT(*) FROM paper_user_relations
                    WHERE user_id = ? AND personal_paper_id IS NOT NULL AND is_starred = 1
                """, (user_id,))
                starred = cursor.fetchone()[0] or 0

                # 近30天新增
                cursor.execute("""
                    SELECT COUNT(*) FROM personal_papers
                    WHERE owner_user_id = ? AND created_at >= date('now', '-30 days')
                """, (user_id,))
                recent = cursor.fetchone()[0] or 0

                return {'total': total, 'total_size': row[1] or 0, 'unread': unread, 'starred': starred, 'recent': recent}
            else:
                # 团队文献库总数
                cursor.execute("""
                    SELECT COUNT(*) as total, SUM(pdf_size) as total_size
                    FROM papers WHERE team_library = 1 AND is_deleted = 0
                """)
                row = cursor.fetchone()
                total = row[0] or 0

                # 未读数量：没有关联记录或 read_status='unread'
                cursor.execute("""
                    SELECT COUNT(*) FROM papers p
                    LEFT JOIN paper_user_relations pur ON p.id = pur.paper_id AND pur.user_id = ?
                    WHERE p.team_library = 1 AND p.is_deleted = 0 AND (pur.read_status = 'unread' OR pur.id IS NULL)
                """, (user_id,))
                unread = cursor.fetchone()[0] or 0

                # 收藏数
                cursor.execute("""
                    SELECT COUNT(*) FROM paper_user_relations
                    WHERE user_id = ? AND paper_id IS NOT NULL AND is_starred = 1
                """, (user_id,))
                starred = cursor.fetchone()[0] or 0

                # 近30天新增
                cursor.execute("""
                    SELECT COUNT(*) FROM papers
                    WHERE team_library = 1 AND is_deleted = 0 AND created_at >= date('now', '-30 days')
                """)
                recent = cursor.fetchone()[0] or 0

                return {'total': total, 'total_size': row[1] or 0, 'unread': unread, 'starred': starred, 'recent': recent}

    @staticmethod
    def get_paper_user_relation(paper_id: int, user_id: int, library_type: str) -> Optional[Dict[str, Any]]:
        """获取文献用户关系"""
        with get_db() as conn:
            cursor = conn.cursor()
            if library_type == 'public':
                cursor.execute("""
                    SELECT id, paper_id, user_id, read_status, is_starred, added_at
                    FROM paper_user_relations WHERE paper_id = ? AND user_id = ?
                """, (paper_id, user_id))
            else:
                cursor.execute("""
                    SELECT id, personal_paper_id, user_id, read_status, is_starred, added_at
                    FROM paper_user_relations WHERE personal_paper_id = ? AND user_id = ?
                """, (paper_id, user_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def create_paper_user_relation(data: Dict[str, Any]) -> int:
        """创建文献用户关系"""
        with get_db() as conn:
            cursor = conn.cursor()
            if data.get('paper_id'):
                cursor.execute("""
                    INSERT INTO paper_user_relations
                    (paper_id, user_id, library_type, relation_type, read_status, is_starred, added_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data.get('paper_id'), data.get('user_id'), data.get('library_type', 'public'),
                      data.get('relation_type', 'team_view'), data.get('read_status', 'unread'),
                      data.get('is_starred', 0), datetime.now().isoformat()))
            else:
                cursor.execute("""
                    INSERT INTO paper_user_relations
                    (user_id, personal_paper_id, library_type, relation_type, read_status, is_starred, added_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data.get('user_id'), data.get('personal_paper_id'), data.get('library_type', 'private'),
                      data.get('relation_type', 'personal_owner'), data.get('read_status', 'unread'),
                      data.get('is_starred', 0), datetime.now().isoformat()))
            return cursor.lastrowid

    @staticmethod
    def update_paper_user_relation(relation_id: int, data: Dict[str, Any]) -> bool:
        """更新文献用户关系"""
        with get_db() as conn:
            cursor = conn.cursor()
            allowed_fields = ['read_status', 'is_starred']
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            if not update_data:
                return False
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            params = list(update_data.values()) + [relation_id]
            cursor.execute(f"UPDATE paper_user_relations SET {set_clause} WHERE id = ?", params)
            return cursor.rowcount > 0

    @staticmethod
    def toggle_star(paper_id: int, user_id: int, library_type: str, star: bool) -> bool:
        """收藏/取消收藏"""
        with get_db() as conn:
            cursor = conn.cursor()
            relation = PaperRepository.get_paper_user_relation(paper_id, user_id, library_type)

            if relation:
                cursor.execute("""
                    UPDATE paper_user_relations SET is_starred = ?
                    WHERE id = ?
                """, (1 if star else 0, relation['id']))
            else:
                if library_type == 'public':
                    cursor.execute("""
                        INSERT INTO paper_user_relations
                        (paper_id, user_id, library_type, relation_type, read_status, is_starred, added_at)
                        VALUES (?, ?, 'public', 'team_view', 'unread', ?, ?)
                    """, (paper_id, user_id, 1 if star else 0, datetime.now().isoformat()))
                else:
                    cursor.execute("""
                        INSERT INTO paper_user_relations
                        (user_id, personal_paper_id, library_type, relation_type, read_status, is_starred, added_at)
                        VALUES (?, ?, 'private', 'personal_owner', 'unread', ?, ?)
                    """, (user_id, paper_id, 1 if star else 0, datetime.now().isoformat()))
            return True

    @staticmethod
    def update_read_status(paper_id: int, user_id: int, status: str, library_type: str) -> bool:
        """更新阅读状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            if library_type == 'public':
                relation = PaperRepository.get_paper_user_relation(paper_id, user_id, library_type)
                if relation:
                    cursor.execute("UPDATE paper_user_relations SET read_status = ? WHERE id = ?", (status, relation['id']))
                else:
                    cursor.execute("""
                        INSERT INTO paper_user_relations
                        (paper_id, user_id, library_type, relation_type, read_status, is_starred, added_at)
                        VALUES (?, ?, 'public', 'team_view', ?, 0, ?)
                    """, (paper_id, user_id, status, datetime.now().isoformat()))
            else:
                relation = PaperRepository.get_paper_user_relation(paper_id, user_id, library_type)
                if relation:
                    cursor.execute("UPDATE paper_user_relations SET read_status = ? WHERE id = ?", (status, relation['id']))
                else:
                    cursor.execute("""
                        INSERT INTO paper_user_relations
                        (user_id, personal_paper_id, library_type, relation_type, read_status, is_starred, added_at)
                        VALUES (?, ?, 'private', 'personal_owner', ?, 0, ?)
                    """, (user_id, paper_id, status, datetime.now().isoformat()))
            return True

    @staticmethod
    def increment_download_count(paper_id: int, library_type: str) -> bool:
        """增加下载次数"""
        with get_db() as conn:
            cursor = conn.cursor()
            if library_type == 'public':
                cursor.execute("UPDATE papers SET download_count = download_count + 1, updated_at = ? WHERE id = ?", (datetime.now().isoformat(), paper_id))
            else:
                cursor.execute("UPDATE personal_papers SET download_count = download_count + 1, updated_at = ? WHERE id = ?", (datetime.now().isoformat(), paper_id))
            return cursor.rowcount > 0

    @staticmethod
    def get_paper_tags(paper_id: int) -> List[Dict[str, Any]]:
        """获取文献标签列表（返回带name和tag_type的对象）"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.name, t.tag_type FROM tags t
                JOIN paper_tags pt ON t.id = pt.tag_id
                WHERE pt.paper_id = ?
            """, (paper_id,))
            return [{'id': row[0], 'name': row[1], 'tag_type': row[2]} for row in cursor.fetchall()]

    @staticmethod
    def get_personal_paper_tags(paper_id: int) -> List[Dict[str, Any]]:
        """获取个人文献标签列表（返回带name和tag_type的对象）"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.name, t.tag_type FROM tags t
                JOIN personal_paper_tags pt ON t.id = pt.tag_id
                WHERE pt.personal_paper_id = ?
            """, (paper_id,))
            return [{'id': row[0], 'name': row[1], 'tag_type': row[2]} for row in cursor.fetchall()]

    @staticmethod
    def check_user_exists(user_id: int) -> bool:
        """检查用户是否存在"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = ? AND status = 'active'", (user_id,))
            return cursor.fetchone() is not None