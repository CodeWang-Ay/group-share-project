"""
================================================================================
文件业务服务模块 (services/file_service.py)
================================================================================

模块名称: backend/services/file_service.py
功能描述: 文件业务逻辑处理，返回完整响应数据

Service 类方法:
    - upload(form, user_id)                : 上传文件
    - get_list(filters, user_id, role)     : 获取文件列表
    - get_stats(filters, user_id, role)    : 获取统计信息
    - get_detail(file_id, user_id, role)   : 获取文件详情
    - update(file_id, data, user_id, role) : 更新文件信息
    - delete(file_id, user_id, role)       : 删除文件
    - download(file_id, user_id, role)     : 下载文件
    - download_by_name(filename, user_id)  : 按文件名下载
    - view(file_id, user_id, role)         : 预览文件

职责:
    - 所有业务逻辑写在这里
    - 返回完整响应数据（status_code, content）
    - 调用 Repository 进行数据操作

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger

from repositories.file_repository import FileRepository
from models.file import File
from config import Config


class FileService:
    """文件业务服务类"""

    UPLOAD_DIR = Config.UPLOAD_DIR / "share_files"
    ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx',
                          '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.mp4', '.avi', '.mov',
                          '.wmv', '.flv', '.webm', '.mkv', '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma',
                          '.zip', '.rar', '.7z', '.tar', '.gz', '.py', '.js', '.html', '.css', '.java',
                          '.cpp', '.c', '.php', '.rb', '.go', '.md', '.json', '.xml', '.csv'}
    MAX_FILE_SIZE = 50 * 1024 * 1024

    async def upload(self, form: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """上传文件"""
        file = form.get("file")
        if not file:
            return {"status_code": 400, "content": {"success": False, "message": "请选择要上传的文件", "error": "NO_FILE"}}

        file_data = file.file.read()
        if len(file_data) > self.MAX_FILE_SIZE:
            return {"status_code": 400, "content": {"success": False, "message": f"文件大小超过限制（最大 {self.MAX_FILE_SIZE // (1024*1024)} MB）", "error": "FILE_TOO_LARGE"}}

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return {"status_code": 400, "content": {"success": False, "message": "不支持的文件类型", "error": "UNSUPPORTED_TYPE"}}

        # 检查文件名是否存在
        if FileRepository.check_filename_exists(file.filename, user_id):
            return {"status_code": 409, "content": {"success": False, "message": f"文件名 '{file.filename}' 已存在", "error": "FILENAME_EXISTS"}}

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_path = self.UPLOAD_DIR / unique_filename
        with open(file_path, 'wb') as f:
            f.write(file_data)

        # 创建记录
        file_hash = File.calculate_file_hash(str(file_path))
        create_data = {
            'filename': unique_filename, 'file_path': str(file_path), 'file_size': len(file_data),
            'file_type': File.get_mime_type(file.filename), 'file_hash': file_hash, 'uploader_id': user_id,
            'description': form.get("description"), 'tags': form.get("tags"), 'is_public': form.get("is_public", "false").lower() == "true"
        }
        file_id = FileRepository.create(create_data)

        logger.info(f"文件上传成功: {unique_filename} (ID: {file_id})")
        return {"status_code": 201, "content": {"success": True, "message": "文件上传成功",
                                                 "data": {"id": file_id, "filename": unique_filename, "file_size": len(file_data)}}}

    async def get_list(self, filters: Dict[str, Any], user_id: int, role: str) -> Dict[str, Any]:
        """获取文件列表"""
        scope = filters.get("scope", "my")
        keyword = filters.get("keyword", "")
        page = int(filters.get("page", 1))
        limit = int(filters.get("limit", 5))
        if limit not in [5, 10, 20, 100]:
            limit = 5
        offset = (page - 1) * limit

        files, total = [], 0
        if scope == "my":
            files = FileRepository.get_by_user(user_id, limit, offset)
            total = FileRepository.get_count_by_user(user_id)
        elif scope == "public":
            files = FileRepository.get_public(limit, offset)
            user_files = FileRepository.get_by_user(user_id, limit, offset)
            existing_ids = set(f['id'] for f in files)
            for f in user_files:
                if f['id'] not in existing_ids:
                    files.append(f)
            total = FileRepository.get_public_count() + FileRepository.get_count_by_user(user_id)
        elif scope == "all" and role == "admin":
            target_id = filters.get("user_id")
            if target_id:
                files = FileRepository.get_by_user(int(target_id), limit, offset)
                total = FileRepository.get_count_by_user(int(target_id))
            else:
                files = FileRepository.get_by_user(user_id, limit, offset) + FileRepository.get_public(limit, offset)
                total = FileRepository.get_count_by_user(user_id) + FileRepository.get_public_count()

        if keyword:
            files = FileRepository.search(keyword, user_id if scope == "my" else None, limit, offset)
            total = FileRepository.get_search_count(keyword, user_id if scope == "my" else None)

        # 添加上传者名字
        for f in files:
            f['uploader_name'] = FileRepository.get_uploader_name(f['uploader_id']) or '未知用户'

        total_pages = (total + limit - 1) // limit if total > 0 else 1
        return {"status_code": 200, "content": {"success": True, "data": {
            "files": files, "total_files_count": total, "pagination": {
                "current_page": page, "per_page": limit, "total": total, "total_pages": total_pages,
                "has_next": page < total_pages, "has_prev": page > 1}}}}

    async def get_stats(self, filters: Dict[str, Any], user_id: int, role: str) -> Dict[str, Any]:
        """获取文件统计"""
        scope = filters.get("scope", "my")
        target_id = None
        if scope == "my":
            target_id = user_id
        elif scope == "all" and role == "admin":
            target_id = int(filters.get("user_id", 0)) if filters.get("user_id") else None
        stats = FileRepository.get_stats(target_id)
        return {"status_code": 200, "content": {"success": True, "data": stats}}

    async def get_detail(self, file_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """获取文件详情"""
        file_data = FileRepository.get_by_id(file_id)
        if not file_data:
            return {"status_code": 404, "content": {"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}}
        file_obj = File.from_dict(file_data)
        if not file_obj.is_accessible_by_user(user_id, role):
            return {"status_code": 403, "content": {"success": False, "message": "没有权限访问此文件", "error": "ACCESS_DENIED"}}
        FileRepository.increment_download(file_id)
        return {"status_code": 200, "content": {"success": True, "data": file_obj.to_dict()}}

    async def update(self, file_id: int, data: Dict[str, Any], user_id: int, role: str) -> Dict[str, Any]:
        """更新文件信息"""
        file_data = FileRepository.get_by_id(file_id)
        if not file_data:
            return {"status_code": 404, "content": {"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}}
        file_obj = File.from_dict(file_data)
        if not file_obj.is_accessible_by_user(user_id, role):
            return {"status_code": 403, "content": {"success": False, "message": "没有权限修改此文件", "error": "ACCESS_DENIED"}}
        if file_obj.uploader_id != user_id and role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "只有上传者和管理员可以修改", "error": "ACCESS_DENIED"}}
        update_data = {}
        if data.get("description"):
            update_data['description'] = data.get("description")
        if data.get("tags"):
            update_data['tags'] = data.get("tags")
        if data.get("is_public") is not None:
            update_data['is_public'] = data.get("is_public")
        FileRepository.update(file_id, update_data)
        logger.info(f"文件信息更新成功: file_id={file_id}")
        return {"status_code": 200, "content": {"success": True, "message": "文件信息更新成功"}}

    async def delete(self, file_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """删除文件"""
        file_data = FileRepository.get_by_id(file_id)
        if not file_data:
            return {"status_code": 404, "content": {"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}}
        file_obj = File.from_dict(file_data)
        if not file_obj.is_accessible_by_user(user_id, role):
            return {"status_code": 403, "content": {"success": False, "message": "没有权限删除此文件", "error": "ACCESS_DENIED"}}
        if file_obj.uploader_id != user_id and role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "只有上传者和管理员可以删除", "error": "ACCESS_DENIED"}}
        # 删除物理文件
        if os.path.exists(file_obj.file_path):
            os.remove(file_obj.file_path)
        FileRepository.delete(file_id)
        logger.info(f"文件删除成功: file_id={file_id}")
        return {"status_code": 200, "content": {"success": True, "message": "文件删除成功"}}

    async def download(self, file_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """下载文件"""
        file_data = FileRepository.get_by_id(file_id)
        if not file_data:
            return {"status_code": 404, "error": True, "content": {"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}}
        file_obj = File.from_dict(file_data)
        if not file_obj.is_accessible_by_user(user_id, role):
            return {"status_code": 403, "error": True, "content": {"success": False, "message": "没有权限访问此文件", "error": "ACCESS_DENIED"}}
        if not os.path.exists(file_obj.file_path):
            return {"status_code": 404, "error": True, "content": {"success": False, "message": "文件已丢失", "error": "FILE_LOST"}}
        FileRepository.increment_download(file_id)
        return {"file_path": file_obj.file_path, "filename": file_obj.filename, "file_type": file_obj.file_type}

    async def download_by_name(self, filename: str, user_id: int) -> Dict[str, Any]:
        """按文件名下载"""
        import urllib.parse
        decoded = urllib.parse.unquote(filename)
        file_data = FileRepository.get_by_filename(decoded)
        if not file_data:
            return {"status_code": 404, "error": True, "content": {"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}}
        if not os.path.exists(file_data['file_path']):
            return {"status_code": 404, "error": True, "content": {"success": False, "message": "文件已丢失", "error": "FILE_LOST"}}
        return {"file_path": file_data['file_path'], "filename": file_data['filename'], "file_type": file_data['file_type']}

    async def view(self, file_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """预览文件"""
        result = await self.download(file_id, user_id, role)
        if result.get("error"):
            return result
        # 设置预览 MIME 类型
        media_type = result['file_type']
        if result['file_type'] == 'application/pdf':
            media_type = 'application/pdf'
        elif not result['file_type'].startswith(('image/', 'text/', 'video/', 'audio/')):
            media_type = 'application/octet-stream'
        result['media_type'] = media_type
        result['headers'] = {"Content-Disposition": f"inline; filename=\"{result['filename']}\""}
        return result