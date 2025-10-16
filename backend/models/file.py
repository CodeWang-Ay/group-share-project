"""
文件数据模型
定义文件相关的数据结构和操作
"""

import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class File:
    """文件模型类"""

    def __init__(self,
                 filename: str,
                 file_path: str,
                 file_size: int,
                 file_type: str,
                 uploader_id: int,
                 file_hash: Optional[str] = None,
                 upload_time: Optional[datetime] = None,
                 description: Optional[str] = None,
                 tags: Optional[str] = None,
                 is_public: bool = False,
                 download_count: int = 0,
                 last_accessed: Optional[datetime] = None,
                 status: str = "active",
                 id: Optional[int] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """
        初始化文件对象

        Args:
            filename: 原始文件名
            file_path: 服务器存储路径
            file_size: 文件大小（字节）
            file_type: 文件MIME类型
            uploader_id: 上传者ID
            file_hash: 文件SHA256哈希值
            upload_time: 上传时间
            description: 文件描述
            tags: 标签（JSON格式）
            is_public: 是否公开
            download_count: 下载次数
            last_accessed: 最后访问时间
            status: 文件状态
            id: 文件ID
            created_at: 创建时间
            updated_at: 更新时间
        """
        self.id = id
        self.filename = filename
        self.file_path = file_path
        self.file_size = file_size
        self.file_type = file_type
        self.file_hash = file_hash
        self.uploader_id = uploader_id
        self.upload_time = upload_time or datetime.now()
        self.description = description
        self.tags = tags
        self.is_public = is_public
        self.download_count = download_count
        self.last_accessed = last_accessed
        self.status = status
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'File':
        """从字典创建文件对象"""
        return cls(
            id=data.get('id'),
            filename=data.get('filename'),
            file_path=data.get('file_path'),
            file_size=data.get('file_size'),
            file_type=data.get('file_type'),
            file_hash=data.get('file_hash'),
            uploader_id=data.get('uploader_id'),
            upload_time=data.get('upload_time'),
            description=data.get('description'),
            tags=data.get('tags'),
            is_public=bool(data.get('is_public', 0)),
            download_count=data.get('download_count', 0),
            last_accessed=data.get('last_accessed'),
            status=data.get('status', 'active'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'file_hash': self.file_hash,
            'uploader_id': self.uploader_id,
            'upload_time': self.upload_time if self.upload_time else None,
            'description': self.description,
            'tags': self.tags,
            'is_public': self.is_public,
            'download_count': self.download_count,
            'last_accessed': self.last_accessed if self.last_accessed else None,
            'status': self.status,
            'created_at': self.created_at if self.created_at else None,
            'updated_at': self.updated_at if self.updated_at else None
        }

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """
        计算文件的SHA256哈希值

        Args:
            file_path: 文件路径

        Returns:
            str: 文件的SHA256哈希值
        """
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        获取文件大小

        Args:
            file_path: 文件路径

        Returns:
            int: 文件大小（字节）
        """
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0

    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """
        获取文件MIME类型

        Args:
            file_path: 文件路径

        Returns:
            str: 文件MIME类型
        """
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    def increment_download_count(self) -> None:
        """增加下载次数"""
        self.download_count += 1
        self.last_accessed = datetime.now()
        self.updated_at = datetime.now()

    def soft_delete(self) -> None:
        """软删除文件（标记为已删除）"""
        self.status = "deleted"
        self.updated_at = datetime.now()

    def restore(self) -> None:
        """恢复已删除的文件"""
        self.status = "active"
        self.updated_at = datetime.now()

    def is_accessible_by_user(self, user_id: int, user_role: str) -> bool:
        """
        检查用户是否有权限访问文件

        Args:
            user_id: 用户ID
            user_role: 用户角色

        Returns:
            bool: 是否有权限访问
        """
        # 管理员可以访问所有文件
        if user_role == "admin":
            return True

        # 文件上传者可以访问自己的文件
        if self.uploader_id == user_id:
            return True

        # 公开文件所有人都可以访问
        if self.is_public:
            return True

        # 其他情况无权限访问
        return False

    def update_access_time(self) -> None:
        """更新最后访问时间"""
        self.last_accessed = datetime.now()

    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return Path(self.filename).suffix.lower()

    def is_image_file(self) -> bool:
        """判断是否为图片文件"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        return self.get_file_extension() in image_extensions

    def is_document_file(self) -> bool:
        """判断是否为文档文件"""
        doc_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
        return self.get_file_extension() in doc_extensions

    def is_video_file(self) -> bool:
        """判断是否为视频文件"""
        video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
        return self.get_file_extension() in video_extensions

    def is_audio_file(self) -> bool:
        """判断是否为音频文件"""
        audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'}
        return self.get_file_extension() in audio_extensions

    def get_formatted_file_size(self) -> str:
        """
        获取格式化的文件大小

        Returns:
            str: 格式化的文件大小（如：1.5 MB）
        """
        if self.file_size == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(self.file_size)

        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.1f} {size_names[i]}"