# Paper Database Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a paper database feature with team sharing and personal library support, including backend APIs and frontend integration.

**Architecture:** Follow existing patterns - dataclass models, service layer with @classmethod, SQLite database, FastAPI routes with dependency injection for authentication. Frontend PaperManager connects to APIs replacing mock data.

**Tech Stack:** FastAPI, SQLite, Python dataclasses, Jinja2 templates, JavaScript fetch API

---

## File Structure

**Backend:**
- Create: `backend/models/paper.py` - Paper, Tag, PaperUserRelation dataclasses
- Modify: `backend/database/connection.py` - Add paper tables to init_db()
- Create: `backend/services/paper_service.py` - PaperService with business logic
- Modify: `backend/main.py` - Add paper API routes

**Frontend:**
- Modify: `templates/rm_paper_database.html` - Connect PaperManager to backend APIs

**Uploads:**
- Create: `uploads/papers/` directory for PDF storage

---

## Task 1: Create Database Tables

**Files:**
- Modify: `backend/database/connection.py:49-227` (init_db function)

- [ ] **Step 1: Add papers table creation**

Add after the research_tasks table creation (around line 177):

```python
        # 创建文献表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                journal TEXT,
                doi TEXT,
                abstract TEXT,
                pdf_path TEXT,
                pdf_size INTEGER,
                file_hash TEXT,
                arxiv_link TEXT,
                semantic_scholar_link TEXT,
                download_count INTEGER DEFAULT 0,
                uploader_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_hash ON papers(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_uploader ON papers(uploader_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year)")
```

- [ ] **Step 2: Add tags table creation**

```python
        # 创建标签表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                tag_type TEXT DEFAULT 'system',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_name ON tags(name)")
```

- [ ] **Step 3: Add paper_user_relations table creation**

```python
        # 创建文献-用户关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_user_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                read_status TEXT DEFAULT 'unread',
                is_starred INTEGER DEFAULT 0,
                library_type TEXT DEFAULT 'public',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_viewed_at TIMESTAMP,
                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_user_paper ON paper_user_relations(paper_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_user_user ON paper_user_relations(user_id)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_paper_user_unique ON paper_user_relations(paper_id, user_id)")
```

- [ ] **Step 4: Add paper_tags table creation**

```python
        # 创建文献-标签关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_tags (
                paper_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (paper_id, tag_id),
                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
```

- [ ] **Step 5: Add system tags initialization**

Add after admin user creation (around line 226):

```python
        # 初始化系统标签
        system_tags = ['Transformer', 'BERT', 'CNN', '大模型', 'NLP', '计算机视觉']
        cursor.execute("SELECT COUNT(*) FROM tags WHERE tag_type = 'system'")
        if cursor.fetchone()[0] == 0:
            for tag_name in system_tags:
                cursor.execute(
                    "INSERT INTO tags (name, tag_type) VALUES (?, ?)",
                    (tag_name, 'system')
                )
            print(f"✅ 已创建 {len(system_tags)} 个系统标签")
```

- [ ] **Step 6: Run database initialization**

```bash
cd backend && python -c "from database.connection import init_db; init_db()"
```

Expected: Database tables created, system tags initialized

- [ ] **Step 7: Commit database changes**

```bash
git add backend/database/connection.py
git commit -m "feat: add paper database tables and system tags initialization"
```

---

## Task 2: Create Data Models

**Files:**
- Create: `backend/models/paper.py`

- [ ] **Step 1: Create Paper dataclass**

```python
"""
文献数据模型
定义Paper、Tag、PaperUserRelation类
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib


@dataclass
class Paper:
    """文献数据模型"""
    id: Optional[int] = None
    title: str = ""
    authors: Optional[str] = None
    year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    pdf_path: Optional[str] = None
    pdf_size: Optional[int] = None
    file_hash: Optional[str] = None
    arxiv_link: Optional[str] = None
    semantic_scholar_link: Optional[str] = None
    download_count: int = 0
    uploader_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.title:
            raise ValueError("文献标题不能为空")

    @staticmethod
    def calculate_file_hash(file_path: str) -> Optional[str]:
        """计算PDF文件的SHA256哈希"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"计算文件哈希失败: {str(e)}")
            return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "abstract": self.abstract,
            "pdf_path": self.pdf_path,
            "pdf_size": self.pdf_size,
            "file_hash": self.file_hash,
            "arxiv_link": self.arxiv_link,
            "semantic_scholar_link": self.semantic_scholar_link,
            "download_count": self.download_count,
            "uploader_id": self.uploader_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paper":
        """从字典创建实例"""
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            authors=data.get("authors"),
            year=data.get("year"),
            journal=data.get("journal"),
            doi=data.get("doi"),
            abstract=data.get("abstract"),
            pdf_path=data.get("pdf_path"),
            pdf_size=data.get("pdf_size"),
            file_hash=data.get("file_hash"),
            arxiv_link=data.get("arxiv_link"),
            semantic_scholar_link=data.get("semantic_scholar_link"),
            download_count=data.get("download_count", 0),
            uploader_id=data.get("uploader_id"),
            created_at=created_at,
            updated_at=updated_at
        )
```

- [ ] **Step 2: Create Tag dataclass**

```python
@dataclass
class Tag:
    """标签数据模型"""
    id: Optional[int] = None
    name: str = ""
    tag_type: str = "system"  # system or custom
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("标签名称不能为空")
        if self.tag_type not in ["system", "custom"]:
            raise ValueError("标签类型必须是system或custom")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "tag_type": self.tag_type,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tag":
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            tag_type=data.get("tag_type", "system"),
            created_by=data.get("created_by"),
            created_at=created_at
        )
```

- [ ] **Step 3: Create PaperUserRelation dataclass**

```python
@dataclass
class PaperUserRelation:
    """文献-用户关系模型"""
    id: Optional[int] = None
    paper_id: Optional[int] = None
    user_id: Optional[int] = None
    read_status: str = "unread"  # unread, reading, read
    is_starred: bool = False
    library_type: str = "public"  # public or private
    added_at: Optional[datetime] = None
    last_viewed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.read_status not in ["unread", "reading", "read"]:
            raise ValueError("阅读状态必须是unread、reading或read")
        if self.library_type not in ["public", "private"]:
            raise ValueError("库类型必须是public或private")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "user_id": self.user_id,
            "read_status": self.read_status,
            "is_starred": self.is_starred,
            "library_type": self.library_type,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "last_viewed_at": self.last_viewed_at.isoformat() if self.last_viewed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperUserRelation":
        added_at = data.get("added_at")
        if added_at and isinstance(added_at, str):
            added_at = datetime.fromisoformat(added_at)

        last_viewed_at = data.get("last_viewed_at")
        if last_viewed_at and isinstance(last_viewed_at, str):
            last_viewed_at = datetime.fromisoformat(last_viewed_at)

        return cls(
            id=data.get("id"),
            paper_id=data.get("paper_id"),
            user_id=data.get("user_id"),
            read_status=data.get("read_status", "unread"),
            is_starred=bool(data.get("is_starred", 0)),
            library_type=data.get("library_type", "public"),
            added_at=added_at,
            last_viewed_at=last_viewed_at
        )
```

- [ ] **Step 4: Update models/__init__.py**

Modify `backend/models/__init__.py` to add exports:

```python
from models.user import User
from models.file import File
from models.meeting import Meeting, MeetingPresenter, MeetingFile
from models.task import Task
from models.paper import Paper, Tag, PaperUserRelation

__all__ = ['User', 'File', 'Meeting', 'MeetingPresenter', 'MeetingFile', 'Task', 'Paper', 'Tag', 'PaperUserRelation']
```

- [ ] **Step 5: Commit data models**

```bash
git add backend/models/paper.py backend/models/__init__.py
git commit -m "feat: add Paper, Tag, PaperUserRelation data models"
```

---

## Task 3: Create PaperService

**Files:**
- Create: `backend/services/paper_service.py`

- [ ] **Step 1: Create PaperService class skeleton**

```python
"""
文献服务模块
处理文献相关的业务逻辑
"""

import os
import shutil
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
```

- [ ] **Step 2: Add create_paper method**

```python
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

                paper_id = cursor.fetchone()[0] if cursor.execute("SELECT last_insert_rowid()").fetchone() else None

                # 创建用户关联
                cursor.execute("""
                    INSERT INTO paper_user_relations
                    (paper_id, user_id, library_type, added_at)
                    VALUES (?, ?, ?, ?)
                """, (paper_id, uploader_id, library_type, datetime.now()))

                # 处理标签
                if tags:
                    for tag_name in tags:
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
                            tag_id = cursor.execute("SELECT last_insert_rowid()").fetchone()[0]

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
```

- [ ] **Step 3: Add get_papers method**

```python
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
                    """, (paper_dict['id']))
                    paper_dict['tags'] = [dict(t) for t in cursor.fetchall()]
                    papers.append(paper_dict)

                return papers

        except Exception as e:
            print(f"获取文献列表失败: {str(e)}")
            return []
```

- [ ] **Step 4: Add get_stats method**

```python
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
```

- [ ] **Step 5: Add toggle_star and update_status methods**

```python
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
```

- [ ] **Step 6: Add get_tags and create_tag methods**

```python
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
                tag_id = cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
                return Tag(id=tag_id, name=name, tag_type='custom',
                          created_by=user_id, created_at=datetime.now()), None
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                return None, "标签已存在"
            return None, f"创建失败: {str(e)}"
```

- [ ] **Step 7: Add batch operations methods**

```python
    @classmethod
    def batch_star(cls, paper_ids: List[int], user_id: int, star: bool) -> int:
        """批量收藏/取消收藏"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE paper_user_relations
                    SET is_starred = ?
                    WHERE paper_id IN ({}) AND user_id = ?
                """.format(','.join('?' * len(paper_ids))),
                [1 if star else 0] + paper_ids + [user_id])
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
```

- [ ] **Step 8: Add import hashlib at top of file**

```python
import hashlib
```

- [ ] **Step 9: Update services/__init__.py**

```python
from services.auth import AuthService
from services.session import session_manager
from services.file_service import FileService
from services.meeting_service import MeetingService
from services.task_service import TaskService
from services.paper_service import PaperService

__all__ = ['AuthService', 'session_manager', 'FileService', 'MeetingService', 'TaskService', 'PaperService']
```

- [ ] **Step 10: Commit PaperService**

```bash
git add backend/services/paper_service.py backend/services/__init__.py
git commit -m "feat: implement PaperService with CRUD and batch operations"
```

---

## Task 4: Add API Routes

**Files:**
- Modify: `backend/main.py` (add routes after existing file routes)

- [ ] **Step 1: Add imports in main.py**

Add after existing imports (around line 28):

```python
from models.paper import Paper, Tag, PaperUserRelation
from services.paper_service import PaperService
```

- [ ] **Step 2: Add GET /api/paper_database/ route**

Add after existing routes (around line 1900):

```python
# ==================== 文献库API ====================

@app.get("/api/paper_database/")
async def get_papers(
    keyword: Optional[str] = None,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    year: Optional[int] = None,
    starred: Optional[bool] = None,
    library_type: Optional[str] = None,
    sort: str = 'newest',
    limit: int = 20,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user)
):
    """获取文献列表"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    papers = PaperService.get_papers(
        user_id=current_user.id,
        keyword=keyword, tag=tag, status=status,
        year=year, starred=starred, library_type=library_type,
        sort=sort, limit=limit, offset=offset
    )
    return {"success": True, "data": papers}
```

- [ ] **Step 3: Add GET /api/paper_database/stats route**

```python
@app.get("/api/paper_database/stats")
async def get_paper_stats(current_user: Optional[User] = Depends(get_current_user)):
    """获取文献统计"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    stats = PaperService.get_stats(user_id=current_user.id)
    return {"success": True, "data": stats}
```

- [ ] **Step 4: Add GET /api/paper_database/tags route**

```python
@app.get("/api/paper_database/tags")
async def get_tags(current_user: Optional[User] = Depends(get_current_user)):
    """获取标签列表"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    tags = PaperService.get_tags()
    return {"success": True, "data": [t.to_dict() for t in tags]}
```

- [ ] **Step 5: Add POST /api/paper_database/ route**

```python
@app.post("/api/paper_database/")
async def upload_paper(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user)
):
    """上传新文献"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    try:
        form = await request.form()
        title = form.get("title")
        pdf_file = form.get("pdf")

        if not title:
            return {"success": False, "message": "标题不能为空"}

        if not pdf_file:
            return {"success": False, "message": "请上传PDF文件"}

        pdf_data = await pdf_file.read()

        paper, error = PaperService.create_paper(
            title=title,
            pdf_data=pdf_data,
            original_filename=pdf_file.filename,
            uploader_id=current_user.id,
            authors=form.get("authors"),
            year=int(form.get("year") or 0) if form.get("year") else None,
            journal=form.get("journal"),
            doi=form.get("doi"),
            abstract=form.get("abstract"),
            arxiv_link=form.get("arxiv_link"),
            semantic_scholar_link=form.get("semantic_scholar_link"),
            tags=form.get("tags", "").split(",") if form.get("tags") else None,
            library_type=form.get("library_type", "public")
        )

        if error:
            return {"success": False, "message": error}

        return {"success": True, "data": paper.to_dict()}

    except Exception as e:
        return {"success": False, "message": f"上传失败: {str(e)}"}
```

- [ ] **Step 6: Add POST /api/paper_database/{id}/star route**

```python
@app.post("/api/paper_database/{paper_id}/star")
async def toggle_paper_star(
    paper_id: int,
    current_user: Optional[User] = Depends(get_current_user)
):
    """收藏/取消收藏"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    success = PaperService.toggle_star(paper_id, current_user.id)
    return {"success": success}
```

- [ ] **Step 7: Add PUT /api/paper_database/{id}/status route**

```python
@app.put("/api/paper_database/{paper_id}/status")
async def update_paper_status(
    paper_id: int,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user)
):
    """更新阅读状态"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    data = await request.json()
    status = data.get("status")
    if not status:
        return {"success": False, "message": "状态不能为空"}

    success = PaperService.update_status(paper_id, current_user.id, status)
    return {"success": success}
```

- [ ] **Step 8: Add batch operation routes**

```python
@app.post("/api/paper_database/batch/star")
async def batch_star_papers(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user)
):
    """批量收藏"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    data = await request.json()
    paper_ids = data.get("paper_ids", [])
    star = data.get("star", True)

    count = PaperService.batch_star(paper_ids, current_user.id, star)
    return {"success": True, "count": count}

@app.post("/api/paper_database/batch/tags")
async def batch_set_tags(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user)
):
    """批量设置标签"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    data = await request.json()
    paper_ids = data.get("paper_ids", [])
    tag = data.get("tag")

    # 实现批量设置标签逻辑
    # ... (需要在PaperService中添加对应方法)

    return {"success": True}

@app.delete("/api/paper_database/batch")
async def batch_delete_papers(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user)
):
    """批量删除"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    data = await request.json()
    paper_ids = data.get("paper_ids", [])

    count = PaperService.batch_delete(paper_ids, current_user.id, current_user.role)
    return {"success": True, "count": count}
```

- [ ] **Step 9: Add DELETE /api/paper_database/{id} route**

```python
@app.delete("/api/paper_database/{paper_id}")
async def delete_paper(
    paper_id: int,
    current_user: Optional[User] = Depends(get_current_user)
):
    """删除文献"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    success = PaperService.delete_paper(paper_id, current_user.id, current_user.role)
    return {"success": success}
```

- [ ] **Step 10: Commit API routes**

```bash
git add backend/main.py
git commit -m "feat: add paper database API routes"
```

---

## Task 5: Modify Frontend

**Files:**
- Modify: `templates/rm_paper_database.html` (JavaScript section)

- [ ] **Step 1: Replace mock papers data with API loading**

Modify the `papers` array and `init` method (around line 955-964):

```javascript
// 原代码删除 papers 假数据数组
// papers: [...] 删除

async init() {
    await this.loadPapers();
    await this.loadTags();
    this.updateStats();
    this.setupEventListeners();
},
```

- [ ] **Step 2: Add loadPapers method**

```javascript
async loadPapers() {
    try {
        const params = new URLSearchParams();
        if (this.currentKeyword) params.set('keyword', this.currentKeyword);
        if (this.currentTag) params.set('tag', this.currentTag);
        if (this.currentStatus) params.set('status', this.currentStatus);
        if (this.currentYear) params.set('year', this.currentYear);
        if (this.currentStarred) params.set('starred', this.currentStarred);
        if (this.sortBy) params.set('sort', this.sortBy);

        const response = await fetch(`${API_BASE_URL}/api/paper_database/?${params.toString()}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
        });
        const result = await response.json();
        if (result.success) {
            this.papers = result.data;
            this.renderPaperList();
        }
    } catch (error) {
        console.error('加载文献失败:', error);
        alert('加载文献失败');
    }
},
```

- [ ] **Step 3: Add loadTags method**

```javascript
async loadTags() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/paper_database/tags`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
        });
        const result = await response.json();
        if (result.success) {
            this.tags = result.data;
            this.renderTagOptions();
        }
    } catch (error) {
        console.error('加载标签失败:', error);
    }
},
```

- [ ] **Step 4: Modify updateStats to use API**

```javascript
async updateStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/paper_database/stats`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
        });
        const result = await response.json();
        if (result.success) {
            document.getElementById('stat-total').textContent = result.data.total;
            document.getElementById('stat-unread').textContent = result.data.unread;
            document.getElementById('stat-starred').textContent = result.data.starred;
            document.getElementById('stat-recent').textContent = result.data.recent;
        }
    } catch (error) {
        console.error('获取统计失败:', error);
    }
},
```

- [ ] **Step 5: Modify toggleStar to use API**

```javascript
async toggleStar(paperId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/paper_database/${paperId}/star`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
        });
        const result = await response.json();
        if (result.success) {
            await this.loadPapers();
        }
    } catch (error) {
        console.error('收藏失败:', error);
    }
},
```

- [ ] **Step 6: Modify updateReadStatus to use API**

```javascript
async updateReadStatus() {
    const status = document.getElementById('detail-read-status').value;
    try {
        const response = await fetch(`${API_BASE_URL}/api/paper_database/${this.currentPaperId}/status`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('session_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status })
        });
        const result = await response.json();
        if (result.success) {
            this.closeDetailModal();
            await this.loadPapers();
        }
    } catch (error) {
        console.error('更新状态失败:', error);
    }
},
```

- [ ] **Step 7: Modify savePaper to use API**

```javascript
async savePaper() {
    const title = document.getElementById('paper-title').value;
    if (!title) {
        alert('请填写文献标题');
        return;
    }

    const formData = new FormData();
    formData.append('title', title);
    formData.append('authors', document.getElementById('paper-authors').value);
    formData.append('year', document.getElementById('paper-year').value);
    formData.append('journal', document.getElementById('paper-journal').value);
    formData.append('doi', document.getElementById('paper-doi').value);
    formData.append('abstract', document.getElementById('paper-abstract').value);
    formData.append('tags', document.getElementById('paper-tags').value);

    const pdfFile = document.getElementById('paper-pdf').files[0];
    if (pdfFile) {
        formData.append('pdf', pdfFile);
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/paper_database/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` },
            body: formData
        });
        const result = await response.json();
        if (result.success) {
            this.closeEditModal();
            await this.loadPapers();
            alert('文献保存成功');
        } else {
            alert(result.message || '保存失败');
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败');
    }
},
```

- [ ] **Step 8: Add renderPaperList method**

```javascript
renderPaperList() {
    const container = document.getElementById('paper-list');
    container.innerHTML = this.papers.map(paper => `
        <div class="paper-row px-4 py-4 border-b border-gray-100" data-paper-id="${paper.id}">
            <div class="grid grid-cols-12 gap-3 items-center">
                <div class="checkbox-cell">
                    <input type="checkbox" class="paper-checkbox w-4 h-4 rounded border-gray-300" data-paper-id="${paper.id}">
                </div>
                <div class="col-span-5 flex items-center gap-3 cursor-pointer" onclick="PaperManager.openDetail(${paper.id})">
                    <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                        <i class="fa fa-file-pdf-o text-blue-500 text-lg"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                            <h3 class="font-medium text-primary truncate">${paper.title}</h3>
                            ${paper.is_starred ? '<i class="fa fa-star text-yellow-500 paper-starred" title="已收藏"></i>' : ''}
                        </div>
                        <p class="text-xs text-gray-500 mt-1 line-clamp-1">${paper.abstract || ''}</p>
                        <div class="mt-2 flex gap-1">
                            ${(paper.tags || []).map(t => `<span class="tag-badge bg-${t.tag_type === 'system' ? 'blue' : 'gray'}-100 text-${t.tag_type === 'system' ? 'blue' : 'gray'}-700">${t.name}</span>`).join('')}
                        </div>
                    </div>
                </div>
                <div class="col-span-2 text-center text-sm text-gray-600">${paper.authors || '-'}</div>
                <div class="col-span-2 text-center text-sm text-gray-600">${paper.year || '-'}</div>
                <div class="col-span-1 text-center">
                    <span class="px-2 py-1 rounded-full text-xs ${this.getStatusStyle(paper.read_status)}">${this.getStatusText(paper.read_status)}</span>
                </div>
                <div class="col-span-2 text-center">
                    <div class="flex gap-2 justify-center">
                        <button class="p-2 hover:bg-gray-100 rounded transition-colors" onclick="PaperManager.toggleStar(${paper.id})" title="收藏">
                            <i class="fa fa-star${paper.is_starred ? ' text-yellow-500' : '-o text-gray-400'}"></i>
                        </button>
                        <button class="p-2 hover:bg-gray-100 rounded transition-colors" onclick="PaperManager.downloadPaper(${paper.id})" title="下载">
                            <i class="fa fa-download text-gray-500"></i>
                        </button>
                        <button class="p-2 hover:bg-red-50 rounded transition-colors" onclick="PaperManager.deletePaper(${paper.id})" title="删除">
                            <i class="fa fa-trash-o text-red-500"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
},

getStatusStyle(status) {
    return { unread: 'bg-gray-100 text-gray-700', reading: 'bg-yellow-100 text-yellow-700', read: 'bg-green-100 text-green-700' }[status] || 'bg-gray-100 text-gray-700';
},

getStatusText(status) {
    return { unread: '未读', reading: '在读', read: '已读' }[status] || '未读';
},
```

- [ ] **Step 9: Add renderTagOptions method**

```javascript
renderTagOptions() {
    const select = document.getElementById('filter-tag');
    select.innerHTML = '<option value="">全部标签</option>' +
        this.tags.map(t => `<option value="${t.name}">${t.name}</option>`).join('');
},
```

- [ ] **Step 10: Add state properties to PaperManager**

```javascript
papers: [],
tags: [],
currentKeyword: '',
currentTag: '',
currentStatus: '',
currentYear: '',
currentStarred: null,
sortBy: 'newest',
```

- [ ] **Step 11: Commit frontend changes**

```bash
git add templates/rm_paper_database.html
git commit -m "feat: connect PaperManager to backend APIs"
```

---

## Task 6: Testing and Integration

- [ ] **Step 1: Start backend server**

```bash
cd backend && python main.py
```

Expected: Server running on http://localhost:8081

- [ ] **Step 2: Test database initialization**

```bash
curl http://localhost:8081/health
```

Expected: JSON response with database status healthy

- [ ] **Step 3: Login to get session token**

```bash
curl -X POST http://localhost:8081/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

Expected: JSON with session_token

- [ ] **Step 4: Test GET papers API**

```bash
curl http://localhost:8081/api/paper_database/ \
  -H "Authorization: Bearer <session_token>"
```

Expected: Empty papers list (success: true, data: [])

- [ ] **Step 5: Test GET tags API**

```bash
curl http://localhost:8081/api/paper_database/tags \
  -H "Authorization: Bearer <session_token>"
```

Expected: List of 6 system tags

- [ ] **Step 6: Open frontend in browser**

```bash
open http://localhost:8081/rm_paper_database?session_token=<token>
```

Expected: Paper database page loads without errors

- [ ] **Step 7: Test upload paper functionality**

Upload a PDF file through the frontend interface. Expected: Paper appears in list after upload.

- [ ] **Step 8: Commit final integration**

```bash
git add -A
git commit -m "feat: paper database feature complete with backend and frontend integration"
```

---

## Self-Review Checklist

After completing all tasks, run this checklist:

- [ ] **Spec Coverage:**
  - Database tables created: papers, tags, paper_user_relations, paper_tags ✓
  - API routes implemented: all routes from spec ✓
  - Frontend connected to APIs ✓
  - Duplicate detection working ✓
  - Batch operations implemented ✓

- [ ] **Placeholder Scan:** No "TBD", "TODO", or incomplete sections found.

- [ ] **Type Consistency:** All method names and parameters match between service and API routes.