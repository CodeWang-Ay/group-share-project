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