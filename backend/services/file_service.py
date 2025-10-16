"""
文件服务模块
处理文件相关的业务逻辑
"""

import os
import shutil
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from models.file import File
from database.connection import get_db


class FileService:
    """文件服务类"""

    # 文件上传目录
    UPLOAD_DIR = Path(__file__).parent.parent / "uploads"

    # 允许的文件类型
    ALLOWED_EXTENSIONS = {
        # 文档
        '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx',
        # 图片
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
        # 视频
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv',
        # 音频
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma',
        # 压缩文件
        '.zip', '.rar', '.7z', '.tar', '.gz',
        # 代码文件
        '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go',
        # 其他
        '.md', '.json', '.xml', '.csv'
    }

    # 最大文件大小（50MB）
    MAX_FILE_SIZE = 50 * 1024 * 1024

    @classmethod
    def init_upload_directory(cls) -> None:
        """初始化文件上传目录"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_allowed_file(cls, filename: str) -> bool:
        """
        检查文件类型是否允许上传

        Args:
            filename: 文件名

        Returns:
            bool: 是否允许上传
        """
        file_extension = Path(filename).suffix.lower()
        return file_extension in cls.ALLOWED_EXTENSIONS

    @classmethod
    def generate_unique_filename(cls, original_filename: str) -> str:
        """
        生成唯一的文件名，避免文件名冲突

        Args:
            original_filename: 原始文件名

        Returns:
            str: 唯一的文件名
        """
        file_path = Path(original_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 生成新文件名：时间戳_原始文件名
        new_filename = f"{timestamp}_{file_path.name}"

        # 如果文件名过长，截断处理
        if len(new_filename) > 255:
            name_without_ext = file_path.stem[:200]  # 保留最多200个字符
            extension = file_path.suffix
            new_filename = f"{timestamp}_{name_without_ext}{extension}"

        return new_filename

    @classmethod
    def upload_file(cls, file_data: bytes, original_filename: str,
                   uploader_id: int, description: Optional[str] = None,
                   tags: Optional[str] = None, is_public: bool = False) -> tuple[Optional[File], Optional[str]]:
        """
        上传文件

        Args:
            file_data: 文件二进制数据
            original_filename: 原始文件名
            uploader_id: 上传者ID
            description: 文件描述
            tags: 标签
            is_public: 是否公开

        Returns:
            tuple: (文件对象, 错误信息)，成功时错误信息为None
        """
        try:
            # 检查文件大小
            if len(file_data) > cls.MAX_FILE_SIZE:
                return None, f"文件大小超过限制（最大 {cls.MAX_FILE_SIZE // (1024*1024)} MB）"

            # 检查文件类型
            if not cls.is_allowed_file(original_filename):
                return None, "不支持的文件类型"

            # 检查是否已存在相同文件名的文件（同一用户下）
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, filename FROM files
                    WHERE filename = ? AND uploader_id = ? AND status = 'active'
                """, (original_filename, uploader_id))

                existing_file = cursor.fetchone()
                if existing_file:
                    return None, f"文件名 '{original_filename}' 已存在，请重命名后再次上传"

            # 初始化上传目录
            cls.init_upload_directory()

            # 生成唯一文件名
            unique_filename = cls.generate_unique_filename(original_filename)
            file_path = cls.UPLOAD_DIR / unique_filename

            # 保存文件到磁盘
            with open(file_path, 'wb') as f:
                f.write(file_data)

            # 计算文件信息
            file_size = len(file_data)
            file_hash = File.calculate_file_hash(str(file_path))
            file_type = File.get_mime_type(original_filename)

            # 检查是否已存在相同文件内容的文件（通过哈希值）
            if file_hash:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, filename FROM files
                        WHERE file_hash = ? AND uploader_id = ? AND status = 'active'
                    """, (file_hash, uploader_id))

                    duplicate_content = cursor.fetchone()
                    if duplicate_content:
                        # 删除刚创建的文件，因为内容重复
                        os.remove(file_path)
                        return None, f"文件内容与已存在的文件 '{duplicate_content[1]}' 重复"

            # 创建文件对象
            file_obj = File(
                filename=original_filename,
                file_path=str(file_path),
                file_size=file_size,
                file_type=file_type,
                uploader_id=uploader_id,
                file_hash=file_hash,
                description=description,
                tags=tags,
                is_public=is_public
            )

            # 保存到数据库 - 使用新的数据库连接
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO files (
                        filename, file_path, file_size, file_type, file_hash,
                        uploader_id, description, tags, is_public
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_obj.filename,
                    file_obj.file_path,
                    file_obj.file_size,
                    file_obj.file_type,
                    file_obj.file_hash,
                    file_obj.uploader_id,
                    file_obj.description,
                    file_obj.tags,
                    file_obj.is_public
                ))

                # 获取新插入的文件ID
                cursor.execute("SELECT last_insert_rowid()")
                file_obj.id = cursor.fetchone()[0]

            return file_obj, None

        except Exception as e:
            # 如果上传失败，删除已创建的文件
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            print(f"文件上传失败: {str(e)}")
            return None, f"文件上传失败: {str(e)}"

    @classmethod
    def get_file_by_id(cls, file_id: int) -> Optional[File]:
        """
        根据ID获取文件

        Args:
            file_id: 文件ID

        Returns:
            File: 文件对象，不存在时返回None
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM files WHERE id = ? AND status = 'active'
                """, (file_id,))

                row = cursor.fetchone()
                if row:
                    return File.from_dict(dict(row))
                return None
        except Exception as e:
            print(f"获取文件失败: {str(e)}")
            return None

    @classmethod
    def get_files_by_user(cls, user_id: int, limit: int = 50, offset: int = 0) -> List[File]:
        """
        获取用户上传的文件列表

        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[File]: 文件列表
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                files_list = cursor.execute("""
                    SELECT * FROM files
                    WHERE uploader_id = ? AND status = 'active'
                    ORDER BY upload_time DESC
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset)).fetchall()

                return [File.from_dict(dict(row)) for row in files_list]
        except Exception as e:
            print(f"获取用户文件列表失败: {str(e)}")
            return []

    @classmethod
    def get_public_files(cls, limit: int = 50, offset: int = 0) -> List[File]:
        """
        获取公开文件列表

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[File]: 文件列表
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM files
                    WHERE is_public = 1 AND status = 'active'
                    ORDER BY upload_time DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

                return [File.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取公开文件列表失败: {str(e)}")
            return []

    @classmethod
    def search_files(cls, keyword: str, user_id: Optional[int] = None,
                    limit: int = 50, offset: int = 0) -> List[File]:
        """
        搜索文件

        Args:
            keyword: 搜索关键词
            user_id: 用户ID（可选，用于限制搜索范围）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[File]: 文件列表
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                if user_id:
                    # 搜索用户的文件和公开文件
                    cursor.execute("""
                        SELECT * FROM files
                        WHERE status = 'active'
                        AND (uploader_id = ? OR is_public = 1)
                        AND (filename LIKE ? OR description LIKE ? OR tags LIKE ?)
                        ORDER BY upload_time DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit, offset))
                else:
                    # 只搜索公开文件
                    cursor.execute("""
                        SELECT * FROM files
                        WHERE status = 'active' AND is_public = 1
                        AND (filename LIKE ? OR description LIKE ? OR tags LIKE ?)
                        ORDER BY upload_time DESC
                        LIMIT ? OFFSET ?
                    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit, offset))

                return [File.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"搜索文件失败: {str(e)}")
            return []

    @classmethod
    def delete_file(cls, file_id: int, user_id: int, user_role: str) -> bool:
        """
        删除文件（软删除）

        Args:
            file_id: 文件ID
            user_id: 操作用户ID
            user_role: 操作用户角色

        Returns:
            bool: 是否删除成功
        """
        try:
            file_obj = cls.get_file_by_id(file_id)
            if not file_obj:
                return False

            # 检查权限
            if not file_obj.is_accessible_by_user(user_id, user_role):
                return False

            # 只有文件上传者和管理员可以删除文件
            if file_obj.uploader_id != user_id and user_role != "admin":
                return False

            # 软删除
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE files
                    SET status = 'deleted', updated_at = ?
                    WHERE id = ?
                """, (datetime.now(), file_id))

                return cursor.rowcount > 0

        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return False

    @classmethod
    def update_file_info(cls, file_id: int, user_id: int, user_role: str,
                        description: Optional[str] = None, tags: Optional[str] = None,
                        is_public: Optional[bool] = None) -> bool:
        """
        更新文件信息

        Args:
            file_id: 文件ID
            user_id: 操作用户ID
            user_role: 操作用户角色
            description: 新的描述
            tags: 新的标签
            is_public: 是否公开

        Returns:
            bool: 是否更新成功
        """
        try:
            file_obj = cls.get_file_by_id(file_id)
            if not file_obj:
                return False

            # 检查权限
            if not file_obj.is_accessible_by_user(user_id, user_role):
                return False

            # 只有文件上传者和管理员可以修改文件信息
            if file_obj.uploader_id != user_id and user_role != "admin":
                return False

            # 更新数据库
            with get_db() as conn:
                cursor = conn.cursor()

                # 构建更新语句
                updates = []
                params = []

                if description is not None:
                    updates.append("description = ?")
                    params.append(description)

                if tags is not None:
                    updates.append("tags = ?")
                    params.append(tags)

                if is_public is not None:
                    updates.append("is_public = ?")
                    params.append(is_public)

                if updates:
                    updates.append("updated_at = ?")
                    params.append(datetime.now())
                    params.append(file_id)

                    cursor.execute(f"""
                        UPDATE files
                        SET {', '.join(updates)}
                        WHERE id = ?
                    """, params)

                    return cursor.rowcount > 0

                return True

        except Exception as e:
            print(f"更新文件信息失败: {str(e)}")
            return False

    @classmethod
    def increment_download_count(cls, file_id: int) -> bool:
        """
        增加文件下载次数

        Args:
            file_id: 文件ID

        Returns:
            bool: 是否更新成功
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE files
                    SET download_count = download_count + 1,
                        last_accessed = ?,
                        updated_at = ?
                    WHERE id = ? AND status = 'active'
                """, (datetime.now(), datetime.now(), file_id))

                return cursor.rowcount > 0

        except Exception as e:
            print(f"更新下载次数失败: {str(e)}")
            return False

    @classmethod
    def get_file_stats(cls, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取文件统计信息

        Args:
            user_id: 用户ID（可选，用于获取特定用户的统计）

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                if user_id:
                    # 获取特定用户的统计
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total_files,
                            SUM(file_size) as total_size,
                            COUNT(CASE WHEN is_public = 1 THEN 1 END) as public_files,
                            SUM(download_count) as total_downloads
                        FROM files
                        WHERE uploader_id = ? AND status = 'active'
                    """, (user_id,))
                else:
                    # 获取全局统计
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total_files,
                            SUM(file_size) as total_size,
                            COUNT(CASE WHEN is_public = 1 THEN 1 END) as public_files,
                            SUM(download_count) as total_downloads
                        FROM files
                        WHERE status = 'active'
                    """)

                result = cursor.fetchone()

                return {
                    'total_files': result[0] or 0,
                    'total_size': result[1] or 0,
                    'public_files': result[2] or 0,
                    'total_downloads': result[3] or 0
                }

        except Exception as e:
            print(f"获取文件统计失败: {str(e)}")
            return {
                'total_files': 0,
                'total_size': 0,
                'public_files': 0,
                'total_downloads': 0
            }