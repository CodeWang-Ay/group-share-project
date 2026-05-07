"""
文献服务模块
处理文献相关的业务逻辑
"""

import os
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

from models.paper import Paper, Tag, PaperUserRelation
from database.connection import get_db


class PaperService:
    """文献服务类"""

    # PDF上传目录
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "papers"
    PERSONAL_UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "personal_papers"

    # 最大文件大小 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    @classmethod
    def init_upload_directory(cls) -> None:
        """初始化PDF上传目录"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.PERSONAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def init_personal_directory(cls, user_id: int) -> Path:
        """初始化用户个人文献目录"""
        user_dir = cls.PERSONAL_UPLOAD_DIR / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    @classmethod
    def check_duplicate(cls, library_type: str, user_id: Optional[int] = None,
                        file_hash: Optional[str] = None, doi: Optional[str] = None,
                        title: Optional[str] = None, authors: Optional[str] = None) -> Optional[Dict]:
        """三维度去重校验：DOI、file_hash、标题+作者组合"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                conditions = []
                params = []

                # 1. file_hash（最高优先级）
                if file_hash:
                    conditions.append("file_hash = ?")
                    params.append(file_hash)

                # 2. DOI
                if doi:
                    conditions.append("doi = ?")
                    params.append(doi)

                # 3. 标题+作者组合（精确匹配）
                if title and authors:
                    conditions.append("title = ? AND authors = ?")
                    params.extend([title, authors])

                if not conditions:
                    return None

                if library_type == 'team':
                    # 团队库：查询 papers 表，排除已删除
                    query = f"""
                        SELECT id, title FROM papers
                        WHERE team_library = 1 AND is_deleted = 0
                        AND ({' OR '.join(conditions)})
                        LIMIT 1
                    """
                else:
                    # 个人库：查询 personal_papers 表，限定用户
                    query = f"""
                        SELECT id, title FROM personal_papers
                        WHERE owner_user_id = ?
                        AND ({' OR '.join(conditions)})
                        LIMIT 1
                    """
                    params.insert(0, user_id)

                cursor.execute(query, params)
                result = cursor.fetchone()
                if result:
                    return {'id': result[0], 'title': result[1]}
                return None
        except Exception as e:
            print(f"去重校验失败: {str(e)}")
            return None

    @classmethod
    def get_user_by_id(cls, user_id: int) -> Optional[str]:
        """根据用户ID获取用户名"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"获取用户名失败: {str(e)}")
            return None

    @classmethod
    def create_paper(cls, title: str, pdf_data: bytes, original_filename: str,
                    uploader_id: int, authors: Optional[str] = None,
                    year: Optional[int] = None, journal: Optional[str] = None,
                    doi: Optional[str] = None, abstract: Optional[str] = None,
                    arxiv_link: Optional[str] = None, semantic_scholar_link: Optional[str] = None,
                    tags: Optional[List[str]] = None, library_type: str = 'public') -> Tuple[Optional[Dict], Optional[str]]:
        """
        上传新文献到指定库

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)

        Returns:
            (paper_dict, error_message)
        """
        try:
            cls.init_upload_directory()

            # 检查文件大小
            if len(pdf_data) > cls.MAX_FILE_SIZE:
                return None, f"文件大小超过限制（最大 {cls.MAX_FILE_SIZE // (1024*1024)} MB）"

            # 检查文件类型
            if not original_filename.lower().endswith('.pdf'):
                return None, "只支持PDF文件"

            # 计算文件哈希
            sha256_hash = hashlib.sha256(pdf_data).hexdigest()

            # 去重校验（分库校验）
            dup_library = 'team' if library_type == 'public' else 'personal'
            duplicate = cls.check_duplicate(
                dup_library, uploader_id, sha256_hash, doi, title, authors
            )

            if duplicate:
                if library_type == 'public':
                    # 团队库强制去重
                    return None, f"该文献已存在于团队文献库，禁止重复新增：{duplicate['title']}"
                else:
                    # 个人库仅提示
                    return None, f"该文献已存在于您的个人文献库：{duplicate['title']}"

            # 生成文件名和时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if library_type == 'public':
                # 团队库：使用原有目录和 papers 表
                filename = f"{timestamp}_{original_filename}"
                file_path = cls.UPLOAD_DIR / filename

                # 保存文件
                with open(file_path, 'wb') as f:
                    f.write(pdf_data)

                # 创建文献记录
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO papers (title, authors, year, journal, doi, abstract,
                            pdf_path, pdf_size, file_hash, arxiv_link, semantic_scholar_link,
                            uploader_id, team_library, is_deleted, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?)
                    """, (title, authors, year, journal, doi, abstract,
                        str(file_path), len(pdf_data), sha256_hash,
                        arxiv_link, semantic_scholar_link, uploader_id,
                        datetime.now(), datetime.now()))

                    cursor.execute("SELECT last_insert_rowid()")
                    paper_id = cursor.fetchone()[0]

                    # 创建用户关联
                    cursor.execute("""
                        INSERT INTO paper_user_relations
                        (paper_id, user_id, library_type, relation_type, added_at)
                        VALUES (?, ?, 'public', 'team_view', ?)
                    """, (paper_id, uploader_id, datetime.now()))

                    # 处理标签
                    cls._process_tags(cursor, paper_id, tags, uploader_id)

                return {
                    'id': paper_id, 'title': title, 'authors': authors, 'year': year,
                    'journal': journal, 'doi': doi, 'abstract': abstract,
                    'pdf_path': str(file_path), 'pdf_size': len(pdf_data),
                    'file_hash': sha256_hash, 'library_type': 'public'
                }, None

            else:
                # 个人库：使用个人目录和 personal_papers 表
                user_dir = cls.init_personal_directory(uploader_id)
                filename = f"{timestamp}_{original_filename}"
                file_path = user_dir / filename

                # 保存文件
                with open(file_path, 'wb') as f:
                    f.write(pdf_data)

                # 创建个人文献记录
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO personal_papers (title, authors, year, journal, doi, abstract,
                            pdf_path, pdf_size, file_hash, arxiv_link, semantic_scholar_link,
                            owner_user_id, source_type, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'uploaded', ?, ?)
                    """, (title, authors, year, journal, doi, abstract,
                        str(file_path), len(pdf_data), sha256_hash,
                        arxiv_link, semantic_scholar_link, uploader_id,
                        datetime.now(), datetime.now()))

                    cursor.execute("SELECT last_insert_rowid()")
                    personal_paper_id = cursor.fetchone()[0]

                    # 创建用户状态关联
                    cursor.execute("""
                        INSERT INTO paper_user_relations
                        (user_id, personal_paper_id, library_type, relation_type, added_at)
                        VALUES (?, ?, 'private', 'personal_owner', ?)
                    """, (uploader_id, personal_paper_id, datetime.now()))

                    # 处理标签
                    cls._process_personal_tags(cursor, personal_paper_id, tags, uploader_id)

                return {
                    'id': personal_paper_id, 'title': title, 'authors': authors, 'year': year,
                    'journal': journal, 'doi': doi, 'abstract': abstract,
                    'pdf_path': str(file_path), 'pdf_size': len(pdf_data),
                    'file_hash': sha256_hash, 'library_type': 'private'
                }, None

        except Exception as e:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            return None, f"上传失败: {str(e)}"

    @classmethod
    def _process_tags(cls, cursor, paper_id: int, tags: Optional[List[str]], user_id: int) -> None:
        """处理团队文献标签"""
        if not tags:
            return
        for tag_name in tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_row = cursor.fetchone()
            if tag_row:
                tag_id = tag_row[0]
            else:
                cursor.execute("""
                    INSERT INTO tags (name, tag_type, created_by, created_at)
                    VALUES (?, 'custom', ?, ?)
                """, (tag_name, user_id, datetime.now()))
                cursor.execute("SELECT last_insert_rowid()")
                tag_id = cursor.fetchone()[0]
            cursor.execute("INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)", (paper_id, tag_id))

    @classmethod
    def _process_personal_tags(cls, cursor, personal_paper_id: int, tags: Optional[List[str]], user_id: int) -> None:
        """处理个人文献标签（创建 personal_paper_tags 表如果不存在）"""
        # 确保个人文献标签关联表存在
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personal_paper_tags (
                personal_paper_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (personal_paper_id, tag_id),
                FOREIGN KEY (personal_paper_id) REFERENCES personal_papers(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        if not tags:
            return
        for tag_name in tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_row = cursor.fetchone()
            if tag_row:
                tag_id = tag_row[0]
            else:
                cursor.execute("""
                    INSERT INTO tags (name, tag_type, created_by, created_at)
                    VALUES (?, 'custom', ?, ?)
                """, (tag_name, user_id, datetime.now()))
                cursor.execute("SELECT last_insert_rowid()")
                tag_id = cursor.fetchone()[0]
            cursor.execute("INSERT OR IGNORE INTO personal_paper_tags (personal_paper_id, tag_id) VALUES (?, ?)", (personal_paper_id, tag_id))

    @classmethod
    def get_papers(cls, user_id: int, keyword: Optional[str] = None,
                   tag: Optional[str] = None, status: Optional[str] = None,
                   year: Optional[int] = None, starred: Optional[bool] = None,
                   library_type: Optional[str] = None,
                   sort: str = 'newest', limit: int = 20, offset: int = 0):
        """
        获取文献列表（分表查询）

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)

        Returns:
            (papers_list, total_count)
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                if library_type == 'public':
                    # 团队文献库：查询 papers 表
                    return cls._get_team_papers(cursor, user_id, keyword, tag, status, year, starred, sort, limit, offset)
                else:
                    # 个人文献库：查询 personal_papers 表
                    return cls._get_personal_papers(cursor, user_id, keyword, tag, status, year, starred, sort, limit, offset)

        except Exception as e:
            print(f"获取文献列表失败: {str(e)}")
            return [], 0

    @classmethod
    def _get_team_papers(cls, cursor, user_id: int, keyword: Optional[str] = None,
                         tag: Optional[str] = None, status: Optional[str] = None,
                         year: Optional[int] = None, starred: Optional[bool] = None,
                         sort: str = 'newest', limit: int = 20, offset: int = 0):
        """获取团队文献列表"""
        # 用户状态关联（JOIN 放在 FROM 后面）
        base_from = """
            FROM papers p
            LEFT JOIN paper_user_relations pur ON p.id = pur.paper_id AND pur.user_id = ?
            LEFT JOIN users u ON p.uploader_id = u.id
        """
        base_params = [user_id]

        base_where = "WHERE p.team_library = 1 AND p.is_deleted = 0"

        # 搜索关键词
        if keyword:
            base_where += " AND (p.title LIKE ? OR p.authors LIKE ? OR p.abstract LIKE ? OR p.journal LIKE ?)"
            base_params.extend([f"%{keyword}%"] * 4)

        # 年份筛选
        if year:
            base_where += " AND p.year = ?"
            base_params.append(year)

        # 标签筛选
        if tag:
            base_where += """
                AND EXISTS (
                    SELECT 1 FROM paper_tags pt
                    JOIN tags t ON pt.tag_id = t.id
                    WHERE pt.paper_id = p.id AND t.name = ?
                )
            """
            base_params.append(tag)

        # 状态筛选
        if status:
            base_where += " AND COALESCE(pur.read_status, 'unread') = ?"
            base_params.append(status)

        # 收藏筛选
        if starred is not None:
            base_where += " AND COALESCE(pur.is_starred, 0) = ?"
            base_params.append(1 if starred else 0)

        # 查询总数
        count_query = "SELECT COUNT(*) " + base_from + " " + base_where
        cursor.execute(count_query, base_params)
        total = cursor.fetchone()[0]

        # 查询列表
        order_by = {
            'newest': 'p.created_at DESC',
            'oldest': 'p.created_at ASC',
            'title': 'p.title ASC',
            'starred': 'COALESCE(pur.is_starred, 0) DESC'
        }.get(sort, 'p.created_at DESC')

        select_fields = """
            p.id, p.title, p.authors, p.year, p.journal, p.doi, p.abstract,
            p.pdf_path, p.pdf_size, p.file_hash, p.arxiv_link, p.semantic_scholar_link,
            p.download_count, p.uploader_id, p.created_at, p.updated_at,
            COALESCE(pur.read_status, 'unread') as read_status,
            COALESCE(pur.is_starred, 0) as is_starred,
            'public' as library_type,
            u.username as uploader_name
        """

        list_query = "SELECT " + select_fields + " " + base_from + " " + base_where + f" ORDER BY {order_by} LIMIT ? OFFSET ?"
        list_params = base_params + [limit, offset]

        rows = cursor.execute(list_query, list_params).fetchall()
        papers = []
        for row in rows:
            paper_dict = dict(row)
            # 获取标签
            cursor.execute("""
                SELECT t.id, t.name, t.tag_type
                FROM paper_tags pt
                JOIN tags t ON pt.tag_id = t.id
                WHERE pt.paper_id = ?
            """, (paper_dict['id'],))
            paper_dict['tags'] = [dict(t) for t in cursor.fetchall()]
            papers.append(paper_dict)

        return papers, total

    @classmethod
    def _get_personal_papers(cls, cursor, user_id: int, keyword: Optional[str] = None,
                             tag: Optional[str] = None, status: Optional[str] = None,
                             year: Optional[int] = None, starred: Optional[bool] = None,
                             sort: str = 'newest', limit: int = 20, offset: int = 0):
        """获取个人文献列表"""
        base_query = """
            FROM personal_papers pp
            LEFT JOIN paper_user_relations pur ON pp.id = pur.personal_paper_id AND pur.user_id = ?
            WHERE pp.owner_user_id = ?
        """
        base_params = [user_id, user_id]

        # 搜索关键词
        if keyword:
            base_query += " AND (pp.title LIKE ? OR pp.authors LIKE ? OR pp.abstract LIKE ? OR pp.journal LIKE ?)"
            base_params.extend([f"%{keyword}%"] * 4)

        # 年份筛选
        if year:
            base_query += " AND pp.year = ?"
            base_params.append(year)

        # 标签筛选
        if tag:
            base_query += """
                AND EXISTS (
                    SELECT 1 FROM personal_paper_tags ppt
                    JOIN tags t ON ppt.tag_id = t.id
                    WHERE ppt.personal_paper_id = pp.id AND t.name = ?
                )
            """
            base_params.append(tag)

        # 状态筛选
        if status:
            base_query += " AND COALESCE(pur.read_status, 'unread') = ?"
            base_params.append(status)

        # 收藏筛选
        if starred is not None:
            base_query += " AND COALESCE(pur.is_starred, 0) = ?"
            base_params.append(1 if starred else 0)

        # 查询总数
        count_query = "SELECT COUNT(*) " + base_query
        cursor.execute(count_query, base_params)
        total = cursor.fetchone()[0]

        # 查询列表
        order_by = {
            'newest': 'pp.created_at DESC',
            'oldest': 'pp.created_at ASC',
            'title': 'pp.title ASC',
            'starred': 'COALESCE(pur.is_starred, 0) DESC'
        }.get(sort, 'pp.created_at DESC')

        select_fields = """
            pp.id, pp.title, pp.authors, pp.year, pp.journal, pp.doi, pp.abstract,
            pp.pdf_path, pp.pdf_size, pp.file_hash, pp.arxiv_link, pp.semantic_scholar_link,
            pp.download_count, pp.owner_user_id, pp.source_type, pp.source_paper_id,
            pp.created_at, pp.updated_at,
            COALESCE(pur.read_status, 'unread') as read_status,
            COALESCE(pur.is_starred, 0) as is_starred,
            'private' as library_type
        """

        list_query = "SELECT " + select_fields + " " + base_query + f" ORDER BY {order_by} LIMIT ? OFFSET ?"
        list_params = base_params + [limit, offset]

        rows = cursor.execute(list_query, list_params).fetchall()
        papers = []
        for row in rows:
            paper_dict = dict(row)
            # 重命名字段以保持与团队文献一致
            paper_dict['uploader_id'] = paper_dict.get('owner_user_id')
            paper_dict['uploader_name'] = None  # 个人文献不显示上传者

            # 获取标签
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_paper_tags (
                    personal_paper_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (personal_paper_id, tag_id)
                )
            """)
            cursor.execute("""
                SELECT t.id, t.name, t.tag_type
                FROM personal_paper_tags ppt
                JOIN tags t ON ppt.tag_id = t.id
                WHERE ppt.personal_paper_id = ?
            """, (paper_dict['id'],))
            paper_dict['tags'] = [dict(t) for t in cursor.fetchall()]
            papers.append(paper_dict)

        return papers, total

    @classmethod
    def get_stats(cls, user_id: int, library_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计数据（分表统计）

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)

        Returns:
            {'total', 'unread', 'starred', 'recent'}
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                if library_type == 'public':
                    # 团队库统计
                    query = """
                        SELECT
                            COUNT(*) as total,
                            COUNT(CASE WHEN COALESCE(pur.read_status, 'unread') = 'unread' THEN 1 END) as unread,
                            COUNT(CASE WHEN COALESCE(pur.is_starred, 0) = 1 THEN 1 END) as starred,
                            COUNT(CASE WHEN p.created_at > datetime('now', '-30 days') THEN 1 END) as recent
                        FROM papers p
                        LEFT JOIN paper_user_relations pur ON p.id = pur.paper_id AND pur.user_id = ?
                        WHERE p.team_library = 1 AND p.is_deleted = 0
                    """
                    cursor.execute(query, (user_id,))
                else:
                    # 个人库统计
                    query = """
                        SELECT
                            COUNT(*) as total,
                            COUNT(CASE WHEN COALESCE(pur.read_status, 'unread') = 'unread' THEN 1 END) as unread,
                            COUNT(CASE WHEN COALESCE(pur.is_starred, 0) = 1 THEN 1 END) as starred,
                            COUNT(CASE WHEN pp.created_at > datetime('now', '-30 days') THEN 1 END) as recent
                        FROM personal_papers pp
                        LEFT JOIN paper_user_relations pur ON pp.id = pur.personal_paper_id AND pur.user_id = ?
                        WHERE pp.owner_user_id = ?
                    """
                    cursor.execute(query, (user_id, user_id))

                result = cursor.fetchone()
                return {
                    'total': result[0] or 0,
                    'unread': result[1] or 0,
                    'starred': result[2] or 0,
                    'recent': result[3] or 0
                }
        except Exception as e:
            print(f"获取统计失败: {str(e)}")
            return {'total': 0, 'unread': 0, 'starred': 0, 'recent': 0}

    @classmethod
    def toggle_star(cls, paper_id: int, user_id: int, library_type: str = 'public') -> bool:
        """
        切换收藏状态

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                if library_type == 'public':
                    # 团队文献：检查/创建用户关联
                    cursor.execute("""
                        SELECT id, is_starred FROM paper_user_relations
                        WHERE paper_id = ? AND user_id = ?
                    """, (paper_id, user_id))
                    relation = cursor.fetchone()

                    if relation:
                        cursor.execute("""
                            UPDATE paper_user_relations
                            SET is_starred = NOT is_starred
                            WHERE paper_id = ? AND user_id = ?
                        """, (paper_id, user_id))
                    else:
                        # 为用户创建关联记录
                        cursor.execute("""
                            INSERT INTO paper_user_relations
                            (paper_id, user_id, library_type, relation_type, read_status, is_starred, added_at)
                            VALUES (?, ?, 'public', 'team_view', 'unread', 1, ?)
                        """, (paper_id, user_id, datetime.now()))
                else:
                    # 个人文献：直接更新关联
                    cursor.execute("""
                        SELECT id, is_starred FROM paper_user_relations
                        WHERE personal_paper_id = ? AND user_id = ?
                    """, (paper_id, user_id))
                    relation = cursor.fetchone()

                    if relation:
                        cursor.execute("""
                            UPDATE paper_user_relations
                            SET is_starred = NOT is_starred
                            WHERE personal_paper_id = ? AND user_id = ?
                        """, (paper_id, user_id))
                    else:
                        # 创建关联记录
                        cursor.execute("""
                            INSERT INTO paper_user_relations
                            (user_id, personal_paper_id, library_type, relation_type, read_status, is_starred, added_at)
                            VALUES (?, ?, 'private', 'personal_owner', 'unread', 1, ?)
                        """, (user_id, paper_id, datetime.now()))

                return True

        except Exception as e:
            print(f"切换收藏失败: {str(e)}")
            return False

    @classmethod
    def update_status(cls, paper_id: int, user_id: int, status: str,
                      library_type: str = 'public') -> bool:
        """
        更新阅读状态

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)
        """
        if status not in ['unread', 'reading', 'read']:
            return False

        try:
            with get_db() as conn:
                cursor = conn.cursor()

                if library_type == 'public':
                    # 团队文献
                    cursor.execute("""
                        SELECT id FROM paper_user_relations
                        WHERE paper_id = ? AND user_id = ?
                    """, (paper_id, user_id))
                    relation = cursor.fetchone()

                    if relation:
                        cursor.execute("""
                            UPDATE paper_user_relations
                            SET read_status = ?, last_viewed_at = ?
                            WHERE paper_id = ? AND user_id = ?
                        """, (status, datetime.now(), paper_id, user_id))
                    else:
                        # 为用户创建关联记录
                        cursor.execute("""
                            INSERT INTO paper_user_relations
                            (paper_id, user_id, library_type, relation_type, read_status, is_starred, added_at, last_viewed_at)
                            VALUES (?, ?, 'public', 'team_view', ?, 0, ?, ?)
                        """, (paper_id, user_id, status, datetime.now(), datetime.now()))
                else:
                    # 个人文献
                    cursor.execute("""
                        SELECT id FROM paper_user_relations
                        WHERE personal_paper_id = ? AND user_id = ?
                    """, (paper_id, user_id))
                    relation = cursor.fetchone()

                    if relation:
                        cursor.execute("""
                            UPDATE paper_user_relations
                            SET read_status = ?, last_viewed_at = ?
                            WHERE personal_paper_id = ? AND user_id = ?
                        """, (status, datetime.now(), paper_id, user_id))
                    else:
                        cursor.execute("""
                            INSERT INTO paper_user_relations
                            (user_id, personal_paper_id, library_type, relation_type, read_status, is_starred, added_at, last_viewed_at)
                            VALUES (?, ?, 'private', 'personal_owner', ?, 0, ?, ?)
                        """, (user_id, paper_id, status, datetime.now(), datetime.now()))

                return True

        except Exception as e:
            print(f"更新状态失败: {str(e)}")
            return False

    @classmethod
    def get_tags(cls) -> List[Tag]:
        """获取所有标签"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, tag_type, created_by, created_at
                    FROM tags ORDER BY tag_type, name
                """)
                return [Tag.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取标签失败: {str(e)}")
            return []

    @classmethod
    def create_tag(cls, name: str, user_id: int) -> Tuple[Optional[Tag], Optional[str]]:
        """创建自定义标签"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tags (name, tag_type, created_by, created_at)
                    VALUES (?, 'custom', ?, ?)
                """, (name, user_id, datetime.now()))
                cursor.execute("SELECT last_insert_rowid()")
                tag_id = cursor.fetchone()[0]
                return Tag(id=tag_id, name=name, tag_type='custom',
                          created_by=user_id, created_at=datetime.now()), None
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                return None, "标签已存在"
            return None, f"创建失败: {str(e)}"

    @classmethod
    def batch_star(cls, paper_ids: List[int], user_id: int, star: bool,
                   library_type: str = 'public') -> int:
        """
        批量收藏/取消收藏

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)
        """
        if not paper_ids:
            return 0
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                count = 0
                for paper_id in paper_ids:
                    # 查找或创建关联记录
                    if library_type == 'public':
                        cursor.execute("""
                            SELECT id FROM paper_user_relations
                            WHERE paper_id = ? AND user_id = ?
                        """, (paper_id, user_id))
                        relation = cursor.fetchone()

                        if relation:
                            cursor.execute("""
                                UPDATE paper_user_relations
                                SET is_starred = ?
                                WHERE paper_id = ? AND user_id = ?
                            """, (1 if star else 0, paper_id, user_id))
                            count += 1
                        else:
                            # 为团队文献创建关联
                            cursor.execute("""
                                INSERT INTO paper_user_relations
                                (paper_id, user_id, library_type, relation_type, read_status, is_starred, added_at)
                                VALUES (?, ?, 'public', 'team_view', 'unread', ?, ?)
                            """, (paper_id, user_id, 1 if star else 0, datetime.now()))
                            count += 1
                    else:
                        cursor.execute("""
                            SELECT id FROM paper_user_relations
                            WHERE personal_paper_id = ? AND user_id = ?
                        """, (paper_id, user_id))
                        relation = cursor.fetchone()

                        if relation:
                            cursor.execute("""
                                UPDATE paper_user_relations
                                SET is_starred = ?
                                WHERE personal_paper_id = ? AND user_id = ?
                            """, (1 if star else 0, paper_id, user_id))
                            count += 1
                        else:
                            cursor.execute("""
                                INSERT INTO paper_user_relations
                                (user_id, personal_paper_id, library_type, relation_type, read_status, is_starred, added_at)
                                VALUES (?, ?, 'private', 'personal_owner', 'unread', ?, ?)
                            """, (user_id, paper_id, 1 if star else 0, datetime.now()))
                            count += 1

                return count
        except Exception as e:
            print(f"批量收藏失败: {str(e)}")
            return 0

    @classmethod
    def add_to_personal_library(cls, paper_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        将团队文献拷贝副本到个人库（物理拷贝，源文献不变）

        Args:
            paper_id: 团队文献ID（papers表）
            user_id: 目标用户ID

        Returns:
            (success, error_message)
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                # 1. 获取团队文献详情
                cursor.execute("""
                    SELECT id, title, authors, year, journal, doi, abstract,
                           pdf_path, pdf_size, file_hash, arxiv_link, semantic_scholar_link
                    FROM papers
                    WHERE id = ? AND team_library = 1 AND is_deleted = 0
                """, (paper_id,))
                team_paper = cursor.fetchone()
                if not team_paper:
                    return False, "团队文献不存在"

                team_paper_dict = dict(team_paper)

                # 2. 去重校验（个人库）
                duplicate = cls.check_duplicate(
                    'personal', user_id,
                    team_paper_dict.get('file_hash'),
                    team_paper_dict.get('doi'),
                    team_paper_dict.get('title'),
                    team_paper_dict.get('authors')
                )
                if duplicate:
                    return False, f"该文献已存在于您的个人文献库，无需重复分享：{duplicate['title']}"

                # 3. 复制 PDF 文件到个人目录
                team_pdf_path = team_paper_dict.get('pdf_path')
                if not team_pdf_path or not os.path.exists(team_pdf_path):
                    return False, "团队文献PDF文件不存在"

                user_dir = cls.init_personal_directory(user_id)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_filename = os.path.basename(team_pdf_path)
                # 去除原有时间戳前缀
                if '_' in original_filename:
                    original_filename = original_filename.split('_', 2)[-1]
                personal_pdf_path = user_dir / f"{timestamp}_{original_filename}"

                # 物理拷贝文件
                import shutil
                shutil.copy2(team_pdf_path, personal_pdf_path)

                # 4. 创建 personal_papers 记录
                cursor.execute("""
                    INSERT INTO personal_papers (title, authors, year, journal, doi, abstract,
                        pdf_path, pdf_size, file_hash, arxiv_link, semantic_scholar_link,
                        owner_user_id, source_type, source_paper_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'shared_from_team', ?, ?, ?)
                """, (team_paper_dict.get('title'), team_paper_dict.get('authors'),
                    team_paper_dict.get('year'), team_paper_dict.get('journal'),
                    team_paper_dict.get('doi'), team_paper_dict.get('abstract'),
                    str(personal_pdf_path), team_paper_dict.get('pdf_size'),
                    team_paper_dict.get('file_hash'), team_paper_dict.get('arxiv_link'),
                    team_paper_dict.get('semantic_scholar_link'), user_id,
                    paper_id, datetime.now(), datetime.now()))

                cursor.execute("SELECT last_insert_rowid()")
                personal_paper_id = cursor.fetchone()[0]

                # 5. 创建用户状态关联
                cursor.execute("""
                    INSERT INTO paper_user_relations
                    (user_id, personal_paper_id, library_type, relation_type, added_at)
                    VALUES (?, ?, 'private', 'personal_owner', ?)
                """, (user_id, personal_paper_id, datetime.now()))

                # 6. 拷贝标签
                cursor.execute("""
                    SELECT tag_id FROM paper_tags WHERE paper_id = ?
                """, (paper_id,))
                tag_ids = [row[0] for row in cursor.fetchall()]
                if tag_ids:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS personal_paper_tags (
                            personal_paper_id INTEGER NOT NULL,
                            tag_id INTEGER NOT NULL,
                            PRIMARY KEY (personal_paper_id, tag_id)
                        )
                    """)
                    for tag_id in tag_ids:
                        cursor.execute("""
                            INSERT OR IGNORE INTO personal_paper_tags
                            (personal_paper_id, tag_id) VALUES (?, ?)
                        """, (personal_paper_id, tag_id))

                return True, None

        except Exception as e:
            # 清理可能已复制的文件
            if 'personal_pdf_path' in locals() and os.path.exists(personal_pdf_path):
                os.remove(personal_pdf_path)
            return False, f"添加失败: {str(e)}"

    @classmethod
    def share_to_team(cls, paper_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        将个人文献拷贝副本到团队库（物理拷贝，源文献不变）

        Args:
            paper_id: 个人文献ID（personal_papers表）
            user_id: 拥有者用户ID

        Returns:
            (success, error_message)
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                # 1. 验证用户是个人文献的拥有者
                cursor.execute("""
                    SELECT id, title, authors, year, journal, doi, abstract,
                           pdf_path, pdf_size, file_hash, arxiv_link, semantic_scholar_link
                    FROM personal_papers
                    WHERE id = ? AND owner_user_id = ?
                """, (paper_id, user_id))
                personal_paper = cursor.fetchone()
                if not personal_paper:
                    return False, "文献不存在或无权限"

                personal_paper_dict = dict(personal_paper)

                # 2. 团队库去重校验（强制）
                duplicate = cls.check_duplicate(
                    'team', None,
                    personal_paper_dict.get('file_hash'),
                    personal_paper_dict.get('doi'),
                    personal_paper_dict.get('title'),
                    personal_paper_dict.get('authors')
                )
                if duplicate:
                    return False, f"该文献已存在于团队文献库，禁止分享：{duplicate['title']}"

                # 3. 复制 PDF 文件到团队目录
                personal_pdf_path = personal_paper_dict.get('pdf_path')
                if not personal_pdf_path or not os.path.exists(personal_pdf_path):
                    return False, "个人文献PDF文件不存在"

                cls.init_upload_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_filename = os.path.basename(personal_pdf_path)
                # 去除用户目录前缀和时间戳
                if '_' in original_filename:
                    parts = original_filename.split('_')
                    if len(parts) >= 3:
                        original_filename = parts[-1]
                team_pdf_path = cls.UPLOAD_DIR / f"{timestamp}_{original_filename}"

                # 物理拷贝文件
                import shutil
                shutil.copy2(personal_pdf_path, team_pdf_path)

                # 4. 创建团队文献记录（papers表）
                # 分享人成为创建责任人（uploader_id）
                cursor.execute("""
                    INSERT INTO papers (title, authors, year, journal, doi, abstract,
                        pdf_path, pdf_size, file_hash, arxiv_link, semantic_scholar_link,
                        uploader_id, team_library, is_deleted, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?)
                """, (personal_paper_dict.get('title'), personal_paper_dict.get('authors'),
                    personal_paper_dict.get('year'), personal_paper_dict.get('journal'),
                    personal_paper_dict.get('doi'), personal_paper_dict.get('abstract'),
                    str(team_pdf_path), personal_paper_dict.get('pdf_size'),
                    personal_paper_dict.get('file_hash'), personal_paper_dict.get('arxiv_link'),
                    personal_paper_dict.get('semantic_scholar_link'), user_id,
                    datetime.now(), datetime.now()))

                cursor.execute("SELECT last_insert_rowid()")
                team_paper_id = cursor.fetchone()[0]

                # 5. 创建团队文献关联
                cursor.execute("""
                    INSERT INTO paper_user_relations
                    (paper_id, user_id, library_type, relation_type, added_at)
                    VALUES (?, ?, 'public', 'team_view', ?)
                """, (team_paper_id, user_id, datetime.now()))

                # 6. 拷贝标签
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS personal_paper_tags (
                        personal_paper_id INTEGER NOT NULL,
                        tag_id INTEGER NOT NULL,
                        PRIMARY KEY (personal_paper_id, tag_id)
                    )
                """)
                cursor.execute("""
                    SELECT tag_id FROM personal_paper_tags WHERE personal_paper_id = ?
                """, (paper_id,))
                tag_ids = [row[0] for row in cursor.fetchall()]
                if tag_ids:
                    for tag_id in tag_ids:
                        cursor.execute("""
                            INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)
                        """, (team_paper_id, tag_id))

                # 7. 不修改原个人文献（副本独立）

                return True, "已成功分享到团队文献库"

        except Exception as e:
            # 清理可能已复制的文件
            if 'team_pdf_path' in locals() and os.path.exists(team_pdf_path):
                os.remove(team_pdf_path)
            return False, f"分享失败: {str(e)}"

    @classmethod
    def batch_delete(cls, paper_ids: List[int], user_id: int, user_role: str,
                     library_type: str = 'public') -> dict:
        """
        批量删除文献

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)

        Returns:
            dict: {'success': bool, 'deleted_count': int, 'failed_messages': list}
        """
        deleted_count = 0
        failed_messages = []
        for paper_id in paper_ids:
            result = cls.delete_paper(paper_id, user_id, user_role, library_type)
            if result['success']:
                deleted_count += 1
            else:
                failed_messages.append(f"文献ID {paper_id}: {result['message']}")

        if deleted_count == len(paper_ids):
            return {'success': True, 'deleted_count': deleted_count, 'message': f'成功删除 {deleted_count} 篇文献'}
        elif deleted_count == 0:
            return {'success': False, 'deleted_count': 0, 'message': '删除失败', 'failed_messages': failed_messages}
        else:
            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f'成功删除 {deleted_count} 篇，失败 {len(paper_ids) - deleted_count} 篇',
                'failed_messages': failed_messages
            }

    @classmethod
    def delete_paper(cls, paper_id: int, user_id: int, user_role: str,
                     library_type: str = 'public') -> dict:
        """
        删除文献（根据库类型调用不同删除逻辑）

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)

        Returns:
            dict: {'success': bool, 'message': str}
        """
        if library_type == 'public':
            return cls.delete_team_paper(paper_id, user_id, user_role)
        else:
            return cls.delete_personal_paper(paper_id, user_id)

    @classmethod
    def delete_team_paper(cls, paper_id: int, user_id: int, user_role: str) -> dict:
        """
        删除团队文献（不影响个人库副本）

        权限：上传者或管理员

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                # 1. 获取文献信息
                cursor.execute("""
                    SELECT uploader_id, pdf_path, title
                    FROM papers
                    WHERE id = ? AND team_library = 1 AND is_deleted = 0
                """, (paper_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '删除失败：文献不存在'}

                uploader_id, pdf_path, title = row

                # 2. 权限校验：只有上传者和管理员可以删除
                if uploader_id != user_id and user_role != 'admin':
                    return {'success': False, 'message': '删除失败：您暂无该操作权限，仅能删除自己创建的文献'}

                # 3. 检查个人库副本数量（可选提示）
                cursor.execute("""
                    SELECT COUNT(*) FROM personal_papers
                    WHERE source_paper_id = ?
                """, (paper_id,))
                personal_copies = cursor.fetchone()[0]
                if personal_copies > 0:
                    print(f"团队文献删除，{personal_copies} 个个人副本保留")

                # 4. 删除物理文件
                if pdf_path and os.path.exists(pdf_path):
                    os.remove(pdf_path)

                # 5. 删除数据库记录（软删除或硬删除）
                # 使用硬删除以清理关联数据
                cursor.execute("DELETE FROM paper_tags WHERE paper_id = ?", (paper_id,))
                cursor.execute("DELETE FROM paper_user_relations WHERE paper_id = ?", (paper_id,))
                cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))

                return {'success': True, 'message': '删除成功'}

        except Exception as e:
            print(f"删除团队文献失败: {str(e)}")
            return {'success': False, 'message': f'删除失败：{str(e)}'}

    @classmethod
    def delete_personal_paper(cls, personal_paper_id: int, user_id: int) -> dict:
        """
        删除个人文献（不影响团队库源文献）

        权限：仅拥有者

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                # 1. 验证用户是拥有者
                cursor.execute("""
                    SELECT pdf_path, source_paper_id
                    FROM personal_papers
                    WHERE id = ? AND owner_user_id = ?
                """, (personal_paper_id, user_id))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '删除失败：文献不存在或无权限'}

                pdf_path, source_paper_id = row

                # 2. 删除个人文献物理文件
                if pdf_path and os.path.exists(pdf_path):
                    os.remove(pdf_path)

                # 3. 删除数据库记录
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS personal_paper_tags (
                        personal_paper_id INTEGER NOT NULL,
                        tag_id INTEGER NOT NULL,
                        PRIMARY KEY (personal_paper_id, tag_id)
                    )
                """)
                cursor.execute("DELETE FROM personal_paper_tags WHERE personal_paper_id = ?", (personal_paper_id,))
                cursor.execute("DELETE FROM paper_user_relations WHERE personal_paper_id = ?", (personal_paper_id,))
                cursor.execute("DELETE FROM personal_papers WHERE id = ?", (personal_paper_id,))

                # 4. 不影响源团队文献（如果有 source_paper_id）

                return {'success': True, 'message': '删除成功'}

        except Exception as e:
            print(f"删除个人文献失败: {str(e)}")
            return {'success': False, 'message': f'删除失败：{str(e)}'}

    @classmethod
    def get_paper_by_id(cls, paper_id: int, user_id: int,
                        library_type: str = 'public') -> Optional[Dict[str, Any]]:
        """
        获取单个文献详情（支持团队和个人文献）

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                if library_type == 'public':
                    # 团队文献
                    cursor.execute("""
                        SELECT p.*, COALESCE(pur.read_status, 'unread') as read_status,
                            COALESCE(pur.is_starred, 0) as is_starred, 'public' as library_type,
                            u.username as uploader_name
                        FROM papers p
                        LEFT JOIN paper_user_relations pur ON p.id = pur.paper_id AND pur.user_id = ?
                        LEFT JOIN users u ON p.uploader_id = u.id
                        WHERE p.id = ? AND p.team_library = 1 AND p.is_deleted = 0
                    """, (user_id, paper_id))
                    row = cursor.fetchone()

                    if not row:
                        return None

                    paper_dict = dict(row)
                    cursor.execute("""
                        SELECT t.id, t.name, t.tag_type
                        FROM paper_tags pt
                        JOIN tags t ON pt.tag_id = t.id
                        WHERE pt.paper_id = ?
                    """, (paper_id,))
                    paper_dict['tags'] = [dict(t) for t in cursor.fetchall()]

                else:
                    # 个人文献
                    cursor.execute("""
                        SELECT pp.*, COALESCE(pur.read_status, 'unread') as read_status,
                            COALESCE(pur.is_starred, 0) as is_starred, 'private' as library_type
                        FROM personal_papers pp
                        LEFT JOIN paper_user_relations pur ON pp.id = pur.personal_paper_id AND pur.user_id = ?
                        WHERE pp.id = ? AND pp.owner_user_id = ?
                    """, (user_id, paper_id, user_id))
                    row = cursor.fetchone()

                    if not row:
                        return None

                    paper_dict = dict(row)
                    paper_dict['uploader_id'] = paper_dict.get('owner_user_id')
                    paper_dict['uploader_name'] = None

                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS personal_paper_tags (
                            personal_paper_id INTEGER NOT NULL,
                            tag_id INTEGER NOT NULL,
                            PRIMARY KEY (personal_paper_id, tag_id)
                        )
                    """)
                    cursor.execute("""
                        SELECT t.id, t.name, t.tag_type
                        FROM personal_paper_tags ppt
                        JOIN tags t ON ppt.tag_id = t.id
                        WHERE ppt.personal_paper_id = ?
                    """, (paper_id,))
                    paper_dict['tags'] = [dict(t) for t in cursor.fetchall()]

                return paper_dict

        except Exception as e:
            print(f"获取文献详情失败: {str(e)}")
            return None

    @classmethod
    def update_paper(cls, paper_id: int, user_id: int, title: Optional[str] = None,
                     authors: Optional[str] = None, year: Optional[int] = None,
                     journal: Optional[str] = None, doi: Optional[str] = None,
                     abstract: Optional[str] = None, arxiv_link: Optional[str] = None,
                     semantic_scholar_link: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     read_status: Optional[str] = None,
                     library_type: str = 'public') -> Tuple[Optional[Dict], Optional[str]]:
        """
        更新文献元数据（不含PDF）

        Args:
            library_type: 'public' (团队库) 或 'private' (个人库)
            read_status: 阅读状态 'unread' / 'reading' / 'read'
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                if library_type == 'public':
                    # 团队文献：只有上传者可以编辑
                    cursor.execute("""
                        SELECT uploader_id FROM papers
                        WHERE id = ? AND team_library = 1 AND is_deleted = 0
                    """, (paper_id,))
                    row = cursor.fetchone()
                    if not row:
                        return None, "文献不存在"
                    uploader_id = row[0]
                    if uploader_id != user_id:
                        return None, "只有上传者可以编辑文献"

                    # 更新字段
                    update_fields = []
                    update_params = []
                    if title is not None:
                        update_fields.append("title = ?")
                        update_params.append(title)
                    if authors is not None:
                        update_fields.append("authors = ?")
                        update_params.append(authors)
                    if year is not None:
                        update_fields.append("year = ?")
                        update_params.append(year)
                    if journal is not None:
                        update_fields.append("journal = ?")
                        update_params.append(journal)
                    if doi is not None:
                        update_fields.append("doi = ?")
                        update_params.append(doi)
                    if abstract is not None:
                        update_fields.append("abstract = ?")
                        update_params.append(abstract)
                    if arxiv_link is not None:
                        update_fields.append("arxiv_link = ?")
                        update_params.append(arxiv_link)
                    if semantic_scholar_link is not None:
                        update_fields.append("semantic_scholar_link = ?")
                        update_params.append(semantic_scholar_link)

                    if update_fields:
                        update_fields.append("updated_at = ?")
                        update_params.append(datetime.now())
                        update_params.append(paper_id)
                        cursor.execute(f"UPDATE papers SET {', '.join(update_fields)} WHERE id = ?", update_params)

                    # 更新标签
                    if tags is not None:
                        cursor.execute("DELETE FROM paper_tags WHERE paper_id = ?", (paper_id,))
                        for tag_name in tags:
                            tag_name = tag_name.strip()
                            if not tag_name:
                                continue
                            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                            tag_row = cursor.fetchone()
                            if tag_row:
                                tag_id = tag_row[0]
                            else:
                                cursor.execute("""
                                    INSERT INTO tags (name, tag_type, created_by, created_at)
                                    VALUES (?, 'custom', ?, ?)
                                """, (tag_name, user_id, datetime.now()))
                                cursor.execute("SELECT last_insert_rowid()")
                                tag_id = cursor.fetchone()[0]
                            cursor.execute("INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)", (paper_id, tag_id))

                else:
                    # 个人文献：只有拥有者可以编辑
                    cursor.execute("""
                        SELECT owner_user_id FROM personal_papers
                        WHERE id = ?
                    """, (paper_id,))
                    row = cursor.fetchone()
                    if not row or row[0] != user_id:
                        return None, "文献不存在或无权限"

                    # 更新字段
                    update_fields = []
                    update_params = []
                    if title is not None:
                        update_fields.append("title = ?")
                        update_params.append(title)
                    if authors is not None:
                        update_fields.append("authors = ?")
                        update_params.append(authors)
                    if year is not None:
                        update_fields.append("year = ?")
                        update_params.append(year)
                    if journal is not None:
                        update_fields.append("journal = ?")
                        update_params.append(journal)
                    if doi is not None:
                        update_fields.append("doi = ?")
                        update_params.append(doi)
                    if abstract is not None:
                        update_fields.append("abstract = ?")
                        update_params.append(abstract)
                    if arxiv_link is not None:
                        update_fields.append("arxiv_link = ?")
                        update_params.append(arxiv_link)
                    if semantic_scholar_link is not None:
                        update_fields.append("semantic_scholar_link = ?")
                        update_params.append(semantic_scholar_link)

                    if update_fields:
                        update_fields.append("updated_at = ?")
                        update_params.append(datetime.now())
                        update_params.append(paper_id)
                        cursor.execute(f"UPDATE personal_papers SET {', '.join(update_fields)} WHERE id = ?", update_params)

                    # 更新标签
                    if tags is not None:
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS personal_paper_tags (
                                personal_paper_id INTEGER NOT NULL,
                                tag_id INTEGER NOT NULL,
                                PRIMARY KEY (personal_paper_id, tag_id)
                            )
                        """)
                        cursor.execute("DELETE FROM personal_paper_tags WHERE personal_paper_id = ?", (paper_id,))
                        for tag_name in tags:
                            tag_name = tag_name.strip()
                            if not tag_name:
                                continue
                            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                            tag_row = cursor.fetchone()
                            if tag_row:
                                tag_id = tag_row[0]
                            else:
                                cursor.execute("""
                                    INSERT INTO tags (name, tag_type, created_by, created_at)
                                    VALUES (?, 'custom', ?, ?)
                                """, (tag_name, user_id, datetime.now()))
                                cursor.execute("SELECT last_insert_rowid()")
                                tag_id = cursor.fetchone()[0]
                            cursor.execute("INSERT OR IGNORE INTO personal_paper_tags (personal_paper_id, tag_id) VALUES (?, ?)", (paper_id, tag_id))

                # 更新阅读状态
                if read_status is not None:
                    if library_type == 'public':
                        # 团队文献：更新 paper_user_relations
                        cursor.execute("""
                            SELECT id FROM paper_user_relations
                            WHERE paper_id = ? AND user_id = ?
                        """, (paper_id, user_id))
                        relation = cursor.fetchone()
                        if relation:
                            cursor.execute("""
                                UPDATE paper_user_relations SET read_status = ?
                                WHERE paper_id = ? AND user_id = ?
                            """, (read_status, paper_id, user_id))
                        else:
                            cursor.execute("""
                                INSERT INTO paper_user_relations
                                (paper_id, user_id, library_type, relation_type, read_status, added_at)
                                VALUES (?, ?, 'public', 'team_view', ?, ?)
                            """, (paper_id, user_id, read_status, datetime.now()))
                    else:
                        # 个人文献：更新 paper_user_relations
                        cursor.execute("""
                            SELECT id FROM paper_user_relations
                            WHERE personal_paper_id = ? AND user_id = ?
                        """, (paper_id, user_id))
                        relation = cursor.fetchone()
                        if relation:
                            cursor.execute("""
                                UPDATE paper_user_relations SET read_status = ?
                                WHERE personal_paper_id = ? AND user_id = ?
                            """, (read_status, paper_id, user_id))
                        else:
                            cursor.execute("""
                                INSERT INTO paper_user_relations
                                (user_id, personal_paper_id, library_type, relation_type, read_status, added_at)
                                VALUES (?, ?, 'private', 'personal_owner', ?, ?)
                            """, (user_id, paper_id, read_status, datetime.now()))

                # 返回更新后的文献信息
                return cls.get_paper_by_id(paper_id, user_id, library_type), None

        except Exception as e:
            return None, f"更新失败: {str(e)}"

    @classmethod
    def increment_download_count(cls, paper_id: int, library_type: str = 'public') -> bool:
        """增加下载次数"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                if library_type == 'public':
                    cursor.execute("""
                        UPDATE papers
                        SET download_count = download_count + 1, updated_at = ?
                        WHERE id = ?
                    """, (datetime.now(), paper_id))
                else:
                    cursor.execute("""
                        UPDATE personal_papers
                        SET download_count = download_count + 1, updated_at = ?
                        WHERE id = ?
                    """, (datetime.now(), paper_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新下载次数失败: {str(e)}")
            return False