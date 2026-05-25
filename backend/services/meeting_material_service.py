"""
================================================================================
材料业务服务模块 (services/material_service.py)
================================================================================

模块名称: backend/services/material_service.py
功能描述: 汇报材料业务逻辑处理，返回完整响应数据

Service 类方法:
    - get_list(filters)                      : 获取材料列表
    - get_meetings_with_materials(filters)   : 获取组会材料
    - get_presenter_files(presenter_id)      : 获取汇报人文件
    - confirm_attendance(presenter_id, ...)  : 确认参会
    - update_status(presenter_id, ...)       : 更新材料状态
    - upload_file(presenter_id, ...)         : 上传材料
    - download_file(file_id)                 : 下载材料
    - get_meeting_materials(meeting_id)      : 获取组会材料

职责:
    - 所有业务逻辑写在这里
    - 返回完整响应数据（status_code, content）
    - 调用 Repository 进行数据操作

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from loguru import logger

from repositories.meeting_material_repository import MeetingMaterialRepository
from config import Config


class MeetingMaterialService:
    """材料业务服务类"""

    STATUS_TEXT = {'pending': '待提交', 'submitted': '待审核', 'approved': '已通过', 'rejected': '已驳回'}
    ALLOWED_TYPES = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md', 'zip', 'rar']

    async def get_list(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """获取汇报材料列表"""
        materials = MeetingMaterialRepository.get_presenters_list(filters)
        for m in materials:
            m['status_text'] = self.STATUS_TEXT.get(m['status'], '待提交')
        stats = {"total": len(materials), "pending": sum(1 for m in materials if m['status'] == 'pending'),
                 "submitted": sum(1 for m in materials if m['status'] == 'submitted'),
                 "approved": sum(1 for m in materials if m['status'] == 'approved'),
                 "rejected": sum(1 for m in materials if m['status'] == 'rejected')}
        return {"status_code": 200, "content": {"success": True, "data": {"materials": materials, "stats": stats}}}

    async def get_meetings_with_materials(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """获取组会列表及汇报人材料状态"""
        meetings = MeetingMaterialRepository.get_meetings_with_presenters(filters)
        total_pending = total_submitted = total_approved = 0
        for m in meetings:
            for p in m.get('presenters', []):
                p['user'] = {'username': p.get('username', ''), 'real_name': p.get('username', '')}
                p['name'] = p.get('username', '未知')
                status = p.get('material_status', 'pending')
                if status == 'pending': total_pending += 1
                elif status == 'submitted': total_submitted += 1
                elif status == 'approved': total_approved += 1
        return {"status_code": 200, "content": {"success": True, "data": {
            "meetings": meetings, "stats": {"total_meetings": len(meetings), "pending": total_pending,
                                            "submitted": total_submitted, "approved": total_approved}}}}

    async def get_presenter_files(self, presenter_id: int) -> Dict[str, Any]:
        """获取汇报人的文件列表"""
        files = MeetingMaterialRepository.get_presenter_files(presenter_id)
        return {"status_code": 200, "content": {"success": True, "files": files}}

    async def confirm_attendance(self, presenter_id: int, user_id: int) -> Dict[str, Any]:
        """汇报人确认参会"""
        presenter = MeetingMaterialRepository.get_presenter_by_id(presenter_id)
        if not presenter:
            return {"status_code": 404, "content": {"success": False, "message": "汇报人记录不存在"}}
        if presenter['user_id'] != user_id:
            return {"status_code": 403, "content": {"success": False, "message": "只有汇报人本人可以确认参会"}}
        MeetingMaterialRepository.update_presenter_status(presenter_id, 'confirmed')
        logger.info(f"汇报人确认参会: presenter_id={presenter_id}")
        return {"status_code": 200, "content": {"success": True, "message": "已确认参会"}}

    async def update_status(self, presenter_id: int, status: str, user_id: int, user_role: str) -> Dict[str, Any]:
        """更新材料审核状态"""
        if status not in ['pending', 'submitted', 'approved', 'rejected']:
            return {"status_code": 400, "content": {"success": False, "message": "无效的状态值", "error": "VALIDATION_ERROR"}}
        presenter = MeetingMaterialRepository.get_presenter_by_id(presenter_id)
        if not presenter:
            return {"status_code": 404, "content": {"success": False, "message": "汇报人不存在", "error": "NOT_FOUND"}}
        if user_id != presenter['user_id'] and user_role not in ['admin', 'teacher']:
            return {"status_code": 403, "content": {"success": False, "message": "只有汇报人本人、导师或管理员可以审核材料", "error": "ACCESS_DENIED"}}
        MeetingMaterialRepository.update_material_status(presenter_id, status)
        logger.info(f"材料状态更新: presenter_id={presenter_id}, status={status}")
        return {"status_code": 200, "content": {"success": True, "message": "材料状态更新成功"}}

    async def upload_file(self, presenter_id: int, user_id: int, user_role: str, form: Dict[str, Any]) -> Dict[str, Any]:
        """上传材料文件"""
        presenter = MeetingMaterialRepository.get_presenter_by_id(presenter_id)
        if not presenter:
            return {"status_code": 404, "content": {"success": False, "message": "汇报人不存在", "error": "NOT_FOUND"}}
        if user_id != presenter['user_id'] and user_role not in ['admin', 'teacher']:
            return {"status_code": 403, "content": {"success": False, "message": "只有汇报人本人或导师可以上传材料", "error": "ACCESS_DENIED"}}
        file = form.get("file")
        if not file:
            return {"status_code": 400, "content": {"success": False, "message": "请选择要上传的文件", "error": "NO_FILE"}}
        content = file.file.read()
        if len(content) > 50 * 1024 * 1024:
            return {"status_code": 400, "content": {"success": False, "message": "文件大小超过限制（最大50MB）", "error": "FILE_TOO_LARGE"}}
        file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
        if file_type not in self.ALLOWED_TYPES:
            return {"status_code": 400, "content": {"success": False, "message": f"不支持的文件类型: {file_type}", "error": "INVALID_TYPE"}}
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        materials_dir = Config.UPLOAD_DIR / "materials"
        materials_dir.mkdir(parents=True, exist_ok=True)
        with open(materials_dir / filename, 'wb') as f:
            f.write(content)
        file_id = MeetingMaterialRepository.create_file({"meeting_id": presenter['meeting_id'], "presenter_id": presenter_id,
                                                   "filename": filename, "file_path": str(materials_dir / filename),
                                                   "file_size": len(content), "file_type": file_type, "uploaded_by": user_id})
        MeetingMaterialRepository.update_material_status(presenter_id, 'approved')
        logger.info(f"材料上传成功: file_id={file_id}")
        return {"status_code": 200, "content": {"success": True, "message": "材料上传成功",
                                                 "data": {"file_id": file_id, "filename": filename, "file_type": file_type, "file_size": len(content)}}}

    async def download_file(self, file_id: int) -> Dict[str, Any]:
        """下载材料文件"""
        file_info = MeetingMaterialRepository.get_file_by_id(file_id)
        if not file_info:
            return {"status_code": 404, "error": True, "content": {"success": False, "message": "文件不存在", "error": "NOT_FOUND"}}
        file_path = Path(file_info['file_path'])
        if not file_path.exists():
            return {"status_code": 404, "error": True, "content": {"success": False, "message": "文件已被删除", "error": "FILE_NOT_FOUND"}}
        return {"file_path": str(file_path), "filename": file_info['filename'], "file_type": file_info['file_type']}

    async def get_meeting_materials(self, meeting_id: int) -> Dict[str, Any]:
        """获取组会的所有汇报材料"""
        materials = MeetingMaterialRepository.get_meeting_materials(meeting_id)
        return {"status_code": 200, "content": {"success": True, "data": {"materials": materials}}}