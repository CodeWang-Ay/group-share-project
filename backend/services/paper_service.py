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

    # 最大文件大小 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    @classmethod
    def init_upload_directory(cls) -> None:
        """初始化PDF上传目录"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
                    tags: Optional[List[str]] = None, library_type: str = 'public') -> Tuple[Optional[Paper], Optional[str]]:
        """上传新文献"""
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

            # 检查团队库是否已存在相同文件
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title FROM papers
                    WHERE file_hash = ? AND EXISTS (
                        SELECT 1 FROM paper_user_relations
                        WHERE paper_id = papers.id AND library_type = 'public'
                    )
                """, (sha256_hash,))
                duplicate = cursor.fetchone()

                if duplicate:
                    # 文献内容已存在于系统中
                    existing_paper_id = duplicate[0]
                    existing_title = duplicate[1]

                    # 检查用户是否已关联该文献
                    cursor.execute("""
                        SELECT id FROM paper_user_relations
                        WHERE paper_id = ? AND user_id = ?
                    """, (existing_paper_id, uploader_id))
                    user_rel = cursor.fetchone()

                    if user_rel:
                        return None, f"您的文献库中已有相同内容的文献：{existing_title}"

                    # 为用户创建关联
                    cursor.execute("""
                        INSERT INTO paper_user_relations
                        (paper_id, user_id, library_type, read_status, is_starred, added_at)
                        VALUES (?, ?, ?, 'unread', 0, ?)
                    """, (existing_paper_id, uploader_id, library_type, datetime.now()))

                    # 获取现有文献并返回成功（非错误）
                    cursor.execute("""
                        SELECT * FROM papers WHERE id = ?
                    """, (existing_paper_id,))
                    existing_row = cursor.fetchone()
                    existing_paper = Paper.from_dict(dict(existing_row))
                    # 使用特殊的返回方式：(Paper对象, 关联成功消息)
                    return existing_paper, f"文献已存在于系统，已为您关联：{existing_title}"

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
                        uploader_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, authors, year, journal, doi, abstract,
                    str(file_path), len(pdf_data), sha256_hash,
                    arxiv_link, semantic_scholar_link, uploader_id,
                    datetime.now(), datetime.now()))

                cursor.execute("SELECT last_insert_rowid()")
                paper_id = cursor.fetchone()[0]

                # 创建用户关联
                cursor.execute("""
                    INSERT INTO paper_user_relations
                    (paper_id, user_id, library_type, added_at)
                    VALUES (?, ?, ?, ?)
                """, (paper_id, uploader_id, library_type, datetime.now()))

                # 处理标签
                if tags:
                    for tag_name in tags:
                        tag_name = tag_name.strip()
                        if not tag_name:
                            continue
                        # 查找或创建标签
                        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                        tag_row = cursor.fetchone()
                        if tag_row:
                            tag_id = tag_row[0]
                        else:
                            cursor.execute("""
                                INSERT INTO tags (name, tag_type, created_by, created_at)
                                VALUES (?, 'custom', ?, ?)
                            """, (tag_name, uploader_id, datetime.now()))
                            cursor.execute("SELECT last_insert_rowid()")
                            tag_id = cursor.fetchone()[0]

                        # 创建标签关联
                        cursor.execute("""
                            INSERT OR IGNORE INTO paper_tags (paper_id, tag_id)
                            VALUES (?, ?)
                        """, (paper_id, tag_id))

            return Paper(
                id=paper_id, title=title, authors=authors, year=year,
                journal=journal, doi=doi, abstract=abstract,
                pdf_path=str(file_path), pdf_size=len(pdf_data),
                file_hash=sha256_hash, arxiv_link=arxiv_link,
                semantic_scholar_link=semantic_scholar_link,
                download_count=0, uploader_id=uploader_id,
                created_at=datetime.now(), updated_at=datetime.now()
            ), None

        except Exception as e:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            return None, f"上传失败: {str(e)}"

    @classmethod
    def get_papers(cls, user_id: int, keyword: Optional[str] = None,
                   tag: Optional[str] = None, status: Optional[str] = None,
                   year: Optional[int] = None, starred: Optional[bool] = None,
                   library_type: Optional[str] = None,
                   sort: str = 'newest', limit: int = 20, offset: int = 0):
        """获取文献列表，返回 (papers, total) 元组"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                # 团队文献库(public)：所有 public 文献，LEFT JOIN 获取当前用户状态
                # 个人文献库(private)：用户所有关联的文献（包括收藏的团队文献）
                if library_type == 'public':
                    # 使用子查询获取一个 public 关联作为 owner，避免因多用户关联导致重复
                    base_query = """
                        FROM papers p
                        JOIN (
                            SELECT DISTINCT paper_id FROM paper_user_relations
                            WHERE library_type = 'public'
                        ) public_papers ON p.id = public_papers.paper_id
                        LEFT JOIN paper_user_relations pur_user ON p.id = pur_user.paper_id
                            AND pur_user.user_id = ?
                        LEFT JOIN users u ON p.uploader_id = u.id
                        WHERE 1=1
                    """
                    base_params = [user_id]
                    select_status = "COALESCE(pur_user.read_status, 'unread') as read_status, COALESCE(pur_user.is_starred, 0) as is_starred, 'public' as library_type"
                else:
                    # 个人库：查询用户所有关联的文献（public + private 都显示）
                    base_query = """
                        FROM papers p
                        JOIN paper_user_relations pur ON p.id = pur.paper_id
                        LEFT JOIN users u ON p.uploader_id = u.id
                        WHERE pur.user_id = ?
                    """
                    base_params = [user_id]
                    select_status = "pur.read_status, pur.is_starred, pur.library_type"
                    # 个人库不额外筛选 library_type，显示所有

                if keyword:
                    base_query += " AND (p.title LIKE ? OR p.authors LIKE ? OR p.abstract LIKE ? OR p.journal LIKE ?)"
                    base_params.extend([f"%{keyword}%"] * 4)

                if status and library_type == 'public':
                    base_query += " AND COALESCE(pur_user.read_status, 'unread') = ?"
                    base_params.append(status)
                elif status:
                    base_query += " AND pur.read_status = ?"
                    base_params.append(status)

                if year:
                    base_query += " AND p.year = ?"
                    base_params.append(year)

                if starred is not None and library_type == 'public':
                    base_query += " AND COALESCE(pur_user.is_starred, 0) = ?"
                    base_params.append(1 if starred else 0)
                elif starred is not None:
                    base_query += " AND pur.is_starred = ?"
                    base_params.append(1 if starred else 0)

                if tag:
                    base_query += """
                        AND EXISTS (
                            SELECT 1 FROM paper_tags pt
                            JOIN tags t ON pt.tag_id = t.id
                            WHERE pt.paper_id = p.id AND t.name = ?
                        )
                    """
                    base_params.append(tag)

                # 查询总数
                count_query = "SELECT COUNT(*) " + base_query
                cursor.execute(count_query, base_params)
                total = cursor.fetchone()[0]

                # 查询列表
                order_by = {
                    'newest': 'p.created_at DESC',
                    'oldest': 'p.created_at ASC',
                    'title': 'p.title ASC',
                    'starred': 'COALESCE(pur_user.is_starred, 0) DESC' if library_type == 'public' else 'pur.is_starred DESC'
                }.get(sort, 'p.created_at DESC')

                list_query = ("SELECT p.*, " + select_status + ", "
                              "u.username as uploader_name " + base_query
                              + f" ORDER BY {order_by} LIMIT ? OFFSET ?")
                list_params = base_params + [limit, offset]

                rows = cursor.execute(list_query, list_params).fetchall()
                papers = []
                for row in rows:
                    paper_dict = dict(row)
                    cursor.execute("""
                        SELECT t.id, t.name, t.tag_type
                        FROM paper_tags pt
                        JOIN tags t ON pt.tag_id = t.id
                        WHERE pt.paper_id = ?
                    """, (paper_dict['id'],))
                    paper_dict['tags'] = [dict(t) for t in cursor.fetchall()]
                    papers.append(paper_dict)

                return papers, total

        except Exception as e:
            print(f"获取文献列表失败: {str(e)}")
            return [], 0

    @classmethod
    def get_stats(cls, user_id: int, library_type: Optional[str] = None) -> Dict[str, Any]:
        """获取统计数据"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                if library_type == 'public':
                    # 团队库：统计所有 public 文献
                    query = """
                        SELECT
                            COUNT(*) as total,
                            COUNT(CASE WHEN COALESCE(pur_user.read_status, 'unread') = 'unread' THEN 1 END) as unread,
                            COUNT(CASE WHEN COALESCE(pur_user.is_starred, 0) = 1 THEN 1 END) as starred,
                            COUNT(CASE WHEN p.created_at > datetime('now', '-30 days') THEN 1 END) as recent
                        FROM papers p
                        JOIN paper_user_relations pur_owner ON p.id = pur_owner.paper_id
                            AND pur_owner.library_type = 'public'
                        LEFT JOIN paper_user_relations pur_user ON p.id = pur_user.paper_id
                            AND pur_user.user_id = ?
                    """
                    params = [user_id]
                else:
                    query = """
                        SELECT
                            COUNT(*) as total,
                            COUNT(CASE WHEN pur.read_status = 'unread' THEN 1 END) as unread,
                            COUNT(CASE WHEN pur.is_starred = 1 THEN 1 END) as starred,
                            COUNT(CASE WHEN p.created_at > datetime('now', '-30 days') THEN 1 END) as recent
                        FROM papers p
                        JOIN paper_user_relations pur ON p.id = pur.paper_id
                        WHERE pur.user_id = ?
                    """
                    params = [user_id]
                    if library_type:
                        query += " AND pur.library_type = ?"
                        params.append(library_type)

                cursor.execute(query, params)
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
    def toggle_star(cls, paper_id: int, user_id: int) -> bool:
        """切换收藏状态（团队文献自动创建用户关联）"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                # 检查用户是否已有关联记录
                cursor.execute("""
                    SELECT id FROM paper_user_relations
                    WHERE paper_id = ? AND user_id = ?
                """, (paper_id, user_id))
                relation = cursor.fetchone()

                if relation:
                    # 已有记录，直接更新
                    cursor.execute("""
                        UPDATE paper_user_relations
                        SET is_starred = NOT is_starred
                        WHERE paper_id = ? AND user_id = ?
                    """, (paper_id, user_id))
                else:
                    # 无记录，检查是否为团队文献
                    cursor.execute("""
                        SELECT library_type FROM paper_user_relations
                        WHERE paper_id = ? AND library_type = 'public'
                        LIMIT 1
                    """, (paper_id,))
                    public_rel = cursor.fetchone()
                    if public_rel:
                        # 团队文献，为用户创建关联记录
                        cursor.execute("""
                            INSERT INTO paper_user_relations
                            (paper_id, user_id, library_type, read_status, is_starred, added_at)
                            VALUES (?, ?, 'public', 'unread', 1, ?)
                        """, (paper_id, user_id, datetime.now()))
                    else:
                        return False  # 非团队文献且无关联，无法操作
                return True
        except Exception as e:
            print(f"切换收藏失败: {str(e)}")
            return False

    @classmethod
    def update_status(cls, paper_id: int, user_id: int, status: str) -> bool:
        """更新阅读状态（团队文献自动创建用户关联）"""
        if status not in ['unread', 'reading', 'read']:
            return False
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                # 检查用户是否已有关联记录
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
                    # 无记录，检查是否为团队文献
                    cursor.execute("""
                        SELECT library_type FROM paper_user_relations
                        WHERE paper_id = ? AND library_type = 'public'
                        LIMIT 1
                    """, (paper_id,))
                    public_rel = cursor.fetchone()
                    if public_rel:
                        cursor.execute("""
                            INSERT INTO paper_user_relations
                            (paper_id, user_id, library_type, read_status, is_starred, added_at, last_viewed_at)
                            VALUES (?, ?, 'public', ?, 0, ?, ?)
                        """, (paper_id, user_id, status, datetime.now(), datetime.now()))
                    else:
                        return False
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
    def batch_star(cls, paper_ids: List[int], user_id: int, star: bool) -> int:
        """批量收藏/取消收藏（支持团队文献）"""
        if not paper_ids:
            return 0
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                count = 0
                for paper_id in paper_ids:
                    # 检查用户是否已有关联
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
                        # 检查是否为团队文献
                        cursor.execute("""
                            SELECT library_type FROM paper_user_relations
                            WHERE paper_id = ? AND library_type = 'public'
                            LIMIT 1
                        """, (paper_id,))
                        public_rel = cursor.fetchone()
                        if public_rel:
                            cursor.execute("""
                                INSERT INTO paper_user_relations
                                (paper_id, user_id, library_type, read_status, is_starred, added_at)
                                VALUES (?, ?, 'public', 'unread', ?, ?)
                            """, (paper_id, user_id, 1 if star else 0, datetime.now()))
                            count += 1
                return count
        except Exception as e:
            print(f"批量收藏失败: {str(e)}")
            return 0

    @classmethod
    def add_to_personal_library(cls, paper_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """将团队文献添加到个人文献库（含去重检查）"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                # 检查用户是否已直接关联该文献
                cursor.execute("""
                    SELECT id, library_type FROM paper_user_relations
                    WHERE paper_id = ? AND user_id = ?
                """, (paper_id, user_id))
                existing = cursor.fetchone()

                if existing:
                    return False, "该文献已在您的文献库中"

                # 获取团队文献的 file_hash 和 title
                cursor.execute("""
                    SELECT file_hash, title FROM papers WHERE id = ?
                """, (paper_id,))
                paper_info = cursor.fetchone()
                if not paper_info:
                    return False, "文献不存在"

                file_hash, title = paper_info

                # 基于 file_hash 去重检查：用户是否已有相同内容的文献
                if file_hash:
                    cursor.execute("""
                        SELECT p.id, p.title FROM papers p
                        JOIN paper_user_relations pur ON p.id = pur.paper_id
                        WHERE pur.user_id = ? AND p.file_hash = ? AND p.id != ?
                        LIMIT 1
                    """, (user_id, file_hash, paper_id))
                    duplicate = cursor.fetchone()
                    if duplicate:
                        return False, f"您的文献库中已有相同内容的文献：{duplicate[1]}"

                # 检查是否为团队文献（有 public 关联）
                cursor.execute("""
                    SELECT id FROM paper_user_relations
                    WHERE paper_id = ? AND library_type = 'public'
                    LIMIT 1
                """, (paper_id,))
                public_rel = cursor.fetchone()

                if public_rel:
                    # 团队文献：为用户创建关联
                    cursor.execute("""
                        INSERT INTO paper_user_relations
                        (paper_id, user_id, library_type, read_status, is_starred, added_at)
                        VALUES (?, ?, 'public', 'unread', 0, ?)
                    """, (paper_id, user_id, datetime.now()))
                    return True, None
                else:
                    return False, "文献不存在"
        except Exception as e:
            return False, f"添加失败: {str(e)}"

    @classmethod
    def share_to_team(cls, paper_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """将个人文献分享到团队文献库（含去重检查）"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                # 检查用户是否拥有该文献关联
                cursor.execute("""
                    SELECT library_type FROM paper_user_relations
                    WHERE paper_id = ? AND user_id = ?
                """, (paper_id, user_id))
                relation = cursor.fetchone()
                if not relation:
                    return False, "文献不存在或无权限"

                # 获取文献的 file_hash 用于去重检查
                cursor.execute("""
                    SELECT file_hash, title FROM papers WHERE id = ?
                """, (paper_id,))
                paper_info = cursor.fetchone()
                if not paper_info:
                    return False, "文献不存在"

                file_hash, title = paper_info

                # 先检查团队库是否已有相同内容的文献（基于 file_hash）
                if file_hash:
                    cursor.execute("""
                        SELECT p.id, p.title FROM papers p
                        JOIN paper_user_relations pur ON p.id = pur.paper_id
                        WHERE pur.library_type = 'public' AND p.file_hash = ? AND p.id != ?
                        LIMIT 1
                    """, (file_hash, paper_id))
                    duplicate = cursor.fetchone()
                    if duplicate:
                        return False, f"团队文献库中已存在相同内容的文献：{duplicate[1]}"

                # 如果该文献已是团队文献（用户的关联已经是 public）
                if relation[0] == 'public':
                    return True, "该文献已在团队文献库中"

                # 将用户的关联改为 public
                cursor.execute("""
                    UPDATE paper_user_relations
                    SET library_type = 'public'
                    WHERE paper_id = ? AND user_id = ?
                """, (paper_id, user_id))
                return True, "已成功分享到团队文献库"
        except Exception as e:
            return False, f"分享失败: {str(e)}"

    @classmethod
    def batch_delete(cls, paper_ids: List[int], user_id: int, user_role: str) -> int:
        """批量删除"""
        count = 0
        for paper_id in paper_ids:
            if cls.delete_paper(paper_id, user_id, user_role):
                count += 1
        return count

    @classmethod
    def delete_paper(cls, paper_id: int, user_id: int, user_role: str) -> bool:
        """删除文献"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                # 直接查询文献信息（不依赖用户关联）
                cursor.execute("""
                    SELECT p.uploader_id, p.pdf_path
                    FROM papers p
                    WHERE p.id = ?
                """, (paper_id,))
                row = cursor.fetchone()
                if not row:
                    return False

                uploader_id, pdf_path = row
                # 只有上传者和管理员可以删除
                if uploader_id != user_id and user_role != 'admin':
                    return False

                # 删除物理文件
                if pdf_path and os.path.exists(pdf_path):
                    os.remove(pdf_path)

                # 删除数据库记录
                cursor.execute("DELETE FROM paper_tags WHERE paper_id = ?", (paper_id,))
                cursor.execute("DELETE FROM paper_user_relations WHERE paper_id = ?", (paper_id,))
                cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
                return True
        except Exception as e:
            print(f"删除失败: {str(e)}")
            return False

    @classmethod
    def get_paper_by_id(cls, paper_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """获取单个文献详情（支持团队文献）"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                # 先尝试获取用户自己的关联记录
                cursor.execute("""
                    SELECT p.*, pur.read_status, pur.is_starred, pur.library_type,
                        u.username as uploader_name
                    FROM papers p
                    JOIN paper_user_relations pur ON p.id = pur.paper_id
                    LEFT JOIN users u ON p.uploader_id = u.id
                    WHERE p.id = ? AND pur.user_id = ?
                """, (paper_id, user_id))
                row = cursor.fetchone()

                if not row:
                    # 检查是否为团队文献
                    cursor.execute("""
                        SELECT p.*, 'unread' as read_status, 0 as is_starred, 'public' as library_type,
                            u.username as uploader_name
                        FROM papers p
                        JOIN paper_user_relations pur ON p.id = pur.paper_id AND pur.library_type = 'public'
                        LEFT JOIN users u ON p.uploader_id = u.id
                        WHERE p.id = ?
                        LIMIT 1
                    """, (paper_id,))
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
                     tags: Optional[List[str]] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """更新文献元数据（不含PDF）"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                # 检查权限：只有上传者可以编辑
                cursor.execute("""
                    SELECT p.uploader_id FROM papers p
                    WHERE p.id = ?
                """, (paper_id,))
                row = cursor.fetchone()
                if not row:
                    return None, "文献不存在"
                uploader_id = row[0]
                if uploader_id != user_id:
                    return None, "只有上传者可以编辑文献"

                # 更新文献信息
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
                    # 清除旧标签
                    cursor.execute("DELETE FROM paper_tags WHERE paper_id = ?", (paper_id,))
                    # 添加新标签
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

                # 返回更新后的文献信息
                return cls.get_paper_by_id(paper_id, user_id), None
        except Exception as e:
            return None, f"更新失败: {str(e)}"

    @classmethod
    def increment_download_count(cls, paper_id: int) -> bool:
        """增加下载次数"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE papers
                    SET download_count = download_count + 1, updated_at = ?
                    WHERE id = ?
                """, (datetime.now(), paper_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新下载次数失败: {str(e)}")
            return False