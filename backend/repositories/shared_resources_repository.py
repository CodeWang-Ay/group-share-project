"""
================================================================================
共享资料数据访问模块 (repositories/shared_resources_repository.py)
================================================================================

模块名称: backend/repositories/shared_resources_repository.py
功能描述: 共享资料数据 CRUD 操作，不包含业务逻辑

Repository 类方法:
    - get_by_id(file_id)                    : 根据ID获取资料
    - get_by_filename(filename)             : 根据文件名获取资料
    - get_by_user(user_id, limit, offset)   : 获取用户资料列表
    - get_public(limit, offset)             : 获取公开资料列表
    - create(data)                          : 创建资料记录
    - update(file_id, data)                 : 更新资料信息
    - delete(file_id)                       : 删除资料
    - search(keyword, user_id, limit, offset): 搜索资料
    - get_stats(user_id)                    : 获取统计信息
    - increment_download(file_id)           : 增加下载次数

职责:
    - 只做数据库 CRUD 操作
    - 不写业务判断逻辑

作者: wjg
创建日期: 2026-05-25
================================================================================
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from database.connection import get_db


class SharedResourcesRepository:
    """共享资料数据访问类"""

    @staticmethod
    def get_by_id(file_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取资料"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE id = ? AND status = 'active'", (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_filename(filename: str) -> Optional[Dict[str, Any]]:
        """根据文件名获取资料"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, filename, file_path, file_type, uploader_id FROM files WHERE filename = ? AND status = 'active'", (filename,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_user(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取用户资料列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE uploader_id = ? AND status = 'active' ORDER BY upload_time DESC LIMIT ? OFFSET ?", (user_id, limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_public(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取公开资料列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE is_public = 1 AND status = 'active' ORDER BY upload_time DESC LIMIT ? OFFSET ?", (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_public_and_user(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取公开资料和用户资料列表（合并查询，正确分页）"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM files
                WHERE (is_public = 1 OR uploader_id = ?) AND status = 'active'
                ORDER BY upload_time DESC LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_public_and_user_count(user_id: int) -> int:
        """获取公开资料和用户资料总数"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM files WHERE (is_public = 1 OR uploader_id = ?) AND status = 'active'", (user_id,))
            return cursor.fetchone()[0] or 0

    @staticmethod
    def get_count_by_user(user_id: int) -> int:
        """获取用户资料总数"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM files WHERE uploader_id = ? AND status = 'active'", (user_id,))
            return cursor.fetchone()[0] or 0

    @staticmethod
    def get_public_count() -> int:
        """获取公开资料总数"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM files WHERE is_public = 1 AND status = 'active'")
            return cursor.fetchone()[0] or 0

    @staticmethod
    def create(data: Dict[str, Any]) -> int:
        """创建资料记录，返回资料ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO files (filename, file_path, file_size, file_type, file_hash, uploader_id, description, tags, is_public)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data.get('filename'), data.get('file_path'), data.get('file_size'), data.get('file_type'),
                  data.get('file_hash'), data.get('uploader_id'), data.get('description'), data.get('tags'), data.get('is_public', False)))
            return cursor.lastrowid

    @staticmethod
    def update(file_id: int, data: Dict[str, Any]) -> bool:
        """更新资料信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            updates = [f"{k} = ?" for k in data.keys()]
            updates.append("updated_at = ?")
            params = list(data.values()) + [datetime.now(), file_id]
            cursor.execute(f"UPDATE files SET {', '.join(updates)} WHERE id = ?", params)
            return cursor.rowcount > 0

    @staticmethod
    def delete(file_id: int) -> bool:
        """删除资料记录"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
            return cursor.rowcount > 0

    @staticmethod
    def search(keyword: str, user_id: Optional[int], limit: int, offset: int) -> List[Dict[str, Any]]:
        """搜索资料"""
        with get_db() as conn:
            cursor = conn.cursor()
            pattern = f"%{keyword}%"
            if user_id:
                cursor.execute("""
                    SELECT * FROM files WHERE status = 'active' AND (uploader_id = ? OR is_public = 1)
                    AND (filename LIKE ? OR description LIKE ? OR tags LIKE ?) ORDER BY upload_time DESC LIMIT ? OFFSET ?
                """, (user_id, pattern, pattern, pattern, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM files WHERE status = 'active' AND is_public = 1
                    AND (filename LIKE ? OR description LIKE ? OR tags LIKE ?) ORDER BY upload_time DESC LIMIT ? OFFSET ?
                """, (pattern, pattern, pattern, limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_search_count(keyword: str, user_id: Optional[int]) -> int:
        """获取搜索结果总数"""
        with get_db() as conn:
            cursor = conn.cursor()
            pattern = f"%{keyword}%"
            if user_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM files WHERE status = 'active' AND (uploader_id = ? OR is_public = 1)
                    AND (filename LIKE ? OR description LIKE ? OR tags LIKE ?)
                """, (user_id, pattern, pattern, pattern))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM files WHERE status = 'active' AND is_public = 1
                    AND (filename LIKE ? OR description LIKE ? OR tags LIKE ?)
                """, (pattern, pattern, pattern))
            return cursor.fetchone()[0] or 0

    @staticmethod
    def get_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
        """获取资料统计"""
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                    SELECT COUNT(*) as total_files, SUM(file_size) as total_size,
                    COUNT(CASE WHEN is_public = 1 THEN 1 END) as public_files, SUM(download_count) as total_downloads
                    FROM files WHERE uploader_id = ? AND status = 'active'
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT COUNT(*) as total_files, SUM(file_size) as total_size,
                    COUNT(CASE WHEN is_public = 1 THEN 1 END) as public_files, SUM(download_count) as total_downloads
                    FROM files WHERE status = 'active'
                """)
            row = cursor.fetchone()
            return {'total_files': row[0] or 0, 'total_size': row[1] or 0, 'public_files': row[2] or 0, 'total_downloads': row[3] or 0}

    @staticmethod
    def increment_download(file_id: int) -> bool:
        """增加下载次数"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE files SET download_count = download_count + 1, last_accessed = ?, updated_at = ? WHERE id = ? AND status = 'active'",
                          (datetime.now(), datetime.now(), file_id))
            return cursor.rowcount > 0

    @staticmethod
    def check_filename_exists(filename: str, uploader_id: int) -> bool:
        """检查文件名是否已存在"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM files WHERE filename = ? AND uploader_id = ? AND status = 'active'", (filename, uploader_id))
            return cursor.fetchone() is not None

    @staticmethod
    def check_file_hash_exists(file_hash: str, uploader_id: int) -> Optional[Dict[str, Any]]:
        """检查文件哈希是否已存在"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, filename FROM files WHERE file_hash = ? AND uploader_id = ? AND status = 'active'", (file_hash, uploader_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_uploader_name(user_id: int) -> Optional[str]:
        """获取上传者用户名"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None