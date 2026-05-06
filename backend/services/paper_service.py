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

                if duplicate and library_type == 'public':
                    # 团队库已存在，为用户创建关联
                    existing_paper_id = duplicate[0]
                    cursor.execute("""
                        INSERT OR IGNORE INTO paper_user_relations
                        (paper_id, user_id, library_type, added_at)
                        VALUES (?, ?, ?, ?)
                    """, (existing_paper_id, uploader_id, library_type, datetime.now()))
                    return None, f"文献已存在于团队库: {duplicate[1]}"

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
                   sort: str = 'newest', limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取文献列表"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                # 构建查询
                query = """
                    SELECT p.*, pur.read_status, pur.is_starred, pur.library_type,
                        u.username as uploader_name
                    FROM papers p
                    JOIN paper_user_relations pur ON p.id = pur.paper_id
                    LEFT JOIN users u ON p.uploader_id = u.id
                    WHERE pur.user_id = ?
                """
                params = [user_id]

                # 添加筛选条件
                if library_type:
                    query += " AND pur.library_type = ?"
                    params.append(library_type)

                if keyword:
                    query += " AND (p.title LIKE ? OR p.authors LIKE ?)"
                    params.extend([f"%{keyword}%", f"%{keyword}%"])

                if status:
                    query += " AND pur.read_status = ?"
                    params.append(status)

                if year:
                    query += " AND p.year = ?"
                    params.append(year)

                if starred is not None:
                    query += " AND pur.is_starred = ?"
                    params.append(1 if starred else 0)

                if tag:
                    query += """
                        AND EXISTS (
                            SELECT 1 FROM paper_tags pt
                            JOIN tags t ON pt.tag_id = t.id
                            WHERE pt.paper_id = p.id AND t.name = ?
                        )
                    """
                    params.append(tag)

                # 排序
                order_by = {
                    'newest': 'p.created_at DESC',
                    'oldest': 'p.created_at ASC',
                    'title': 'p.title ASC',
                    'starred': 'pur.is_starred DESC'
                }.get(sort, 'p.created_at DESC')
                query += f" ORDER BY {order_by}"

                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                rows = cursor.execute(query, params).fetchall()
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

                return papers

        except Exception as e:
            print(f"获取文献列表失败: {str(e)}")
            return []

    @classmethod
    def get_stats(cls, user_id: int) -> Dict[str, Any]:
        """获取统计数据"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN pur.read_status = 'unread' THEN 1 END) as unread,
                        COUNT(CASE WHEN pur.is_starred = 1 THEN 1 END) as starred,
                        COUNT(CASE WHEN p.created_at > datetime('now', '-30 days') THEN 1 END) as recent
                    FROM papers p
                    JOIN paper_user_relations pur ON p.id = pur.paper_id
                    WHERE pur.user_id = ?
                """, (user_id,))
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
        """切换收藏状态"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE paper_user_relations
                    SET is_starred = NOT is_starred
                    WHERE paper_id = ? AND user_id = ?
                """, (paper_id, user_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"切换收藏失败: {str(e)}")
            return False

    @classmethod
    def update_status(cls, paper_id: int, user_id: int, status: str) -> bool:
        """更新阅读状态"""
        if status not in ['unread', 'reading', 'read']:
            return False
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE paper_user_relations
                    SET read_status = ?, last_viewed_at = ?
                    WHERE paper_id = ? AND user_id = ?
                """, (status, datetime.now(), paper_id, user_id))
                return cursor.rowcount > 0
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
        """批量收藏/取消收藏"""
        if not paper_ids:
            return 0
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                placeholders = ','.join('?' * len(paper_ids))
                cursor.execute(f"""
                    UPDATE paper_user_relations
                    SET is_starred = ?
                    WHERE paper_id IN ({placeholders}) AND user_id = ?
                """, [1 if star else 0] + paper_ids + [user_id])
                return cursor.rowcount
        except Exception as e:
            print(f"批量收藏失败: {str(e)}")
            return 0

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
                # 检查权限
                cursor.execute("""
                    SELECT p.uploader_id, p.pdf_path
                    FROM papers p
                    JOIN paper_user_relations pur ON p.id = pur.paper_id
                    WHERE p.id = ? AND pur.user_id = ?
                """, (paper_id, user_id))
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
        """获取单个文献详情"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
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
                    return None

                paper_dict = dict(row)
                # 获取标签
                cursor.execute("""
                    SELECT t.id, t.name, t.tag_type
                    FROM paper_tags pt
                    JOIN tags t ON pt.tag_id = t.id
                    WHERE pt.paper_id = ?
                """, (paper_id))
                paper_dict['tags'] = [dict(t) for t in cursor.fetchall()]
                return paper_dict
        except Exception as e:
            print(f"获取文献详情失败: {str(e)}")
            return None

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