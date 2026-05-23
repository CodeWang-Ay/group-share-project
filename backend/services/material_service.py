"""
================================================================================
材料业务服务模块 (services/material_service.py)
================================================================================

模块名称: backend/services/material_service.py
功能描述: 汇报材料业务逻辑处理

Service 类方法:
    - get_list(filters)                      : 获取材料列表
    - get_meetings_with_materials(filters)   : 获取组会材料
    - get_presenter_files(presenter_id)      : 获取汇报人文件
    - confirm_attendance(presenter_id, ...)  : 确认参会
    - update_status(presenter_id, ...)       : 更新材料状态
    - upload_file(presenter_id, ...)         : 上传材料
    - download_file(file_id)                 : 下载材料

职责:
    - 处理业务逻辑
    - 权限验证
    - 文件处理
    - 调用 Repository 进行数据操作

依赖:
    - repositories.material_repository: 数据访问层
    - config.Config.UPLOAD_DIR       : 上传目录

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger

from repositories.material_repository import MaterialRepository
from config import Config


class MaterialService:
    """材料业务服务类"""

    # 状态文本映射
    STATUS_TEXT_MAP = {
        'pending': '待提交',
        'submitted': '待审核',
        'approved': '已通过',
        'rejected': '已驳回'
    }

    # 允许的文件类型
    ALLOWED_FILE_TYPES = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md', 'zip', 'rar']

    @staticmethod
    def get_list(filters: Dict[str, Any]) -> Dict[str, Any]:
        """获取汇报材料列表"""
        materials = MaterialRepository.get_presenters_list(filters)

        # 处理数据
        for material in materials:
            material['status_text'] = MaterialService.STATUS_TEXT_MAP.get(material['status'], '待提交')

        # 统计数据
        stats = {
            "total": len(materials),
            "pending": len([m for m in materials if m['status'] == 'pending']),
            "submitted": len([m for m in materials if m['status'] == 'submitted']),
            "approved": len([m for m in materials if m['status'] == 'approved']),
            "rejected": len([m for m in materials if m['status'] == 'rejected'])
        }

        return {
            "materials": materials,
            "stats": stats
        }

    @staticmethod
    def get_meetings_with_materials(filters: Dict[str, Any]) -> Dict[str, Any]:
        """获取组会列表及汇报人材料状态"""
        meetings = MaterialRepository.get_meetings_with_presenters(filters)

        # 处理汇报人数据
        total_pending = 0
        total_submitted = 0
        total_approved = 0

        for meeting in meetings:
            presenters = meeting.get('presenters', [])
            for presenter in presenters:
                presenter['user'] = {
                    'username': presenter.get('username', ''),
                    'real_name': presenter.get('username', '')
                }
                presenter['name'] = presenter.get('username', '未知')

                presenter_status = presenter.get('material_status', 'pending')
                if presenter_status == 'pending':
                    total_pending += 1
                elif presenter_status == 'submitted':
                    total_submitted += 1
                elif presenter_status == 'approved':
                    total_approved += 1

        # 按材料状态筛选（业务逻辑层处理）
        material_status_filter = filters.get('material_status')
        if material_status_filter:
            filtered_meetings = []
            for meeting in meetings:
                presenters = meeting.get('presenters', [])
                if material_status_filter == 'pending':
                    if any(p.get('material_status') == 'pending' for p in presenters):
                        filtered_meetings.append(meeting)
                elif material_status_filter == 'submitted':
                    if any(p.get('material_status') == 'submitted' for p in presenters):
                        filtered_meetings.append(meeting)
                elif material_status_filter == 'approved':
                    if all(p.get('material_status') == 'approved' for p in presenters if p.get('material_required')):
                        filtered_meetings.append(meeting)
            meetings = filtered_meetings

        stats = {
            'total_meetings': len(meetings),
            'pending': total_pending,
            'submitted': total_submitted,
            'approved': total_approved
        }

        return {
            "meetings": meetings,
            "stats": stats
        }

    @staticmethod
    def get_presenter_files(presenter_id: int) -> list:
        """获取汇报人的文件列表"""
        return MaterialRepository.get_presenter_files(presenter_id)

    @staticmethod
    def confirm_attendance(presenter_id: int, user_id: int) -> bool:
        """汇报人确认参会"""
        presenter = MaterialRepository.get_presenter_by_id(presenter_id)
        if not presenter:
            raise ValueError("汇报人记录不存在")

        # 权限验证：只有汇报人自己可以确认
        if presenter['user_id'] != user_id:
            raise ValueError("只有汇报人本人可以确认参会")

        success = MaterialRepository.update_presenter_status(presenter_id, 'confirmed')
        if not success:
            raise ValueError("确认失败")

        logger.info(f"汇报人确认参会: presenter_id={presenter_id}")
        return True

    @staticmethod
    def update_status(presenter_id: int, status: str, user_id: int, user_role: str) -> bool:
        """更新材料审核状态"""
        if status not in ['pending', 'submitted', 'approved', 'rejected']:
            raise ValueError("无效的状态值")

        presenter = MaterialRepository.get_presenter_by_id(presenter_id)
        if not presenter:
            raise ValueError("汇报人不存在")

        # 权限验证：汇报人本人、导师、管理员可以审核
        if user_id != presenter['user_id'] and user_role not in ['admin', 'teacher']:
            raise ValueError("只有汇报人本人、导师或管理员可以审核材料")

        success = MaterialRepository.update_material_status(presenter_id, status)
        if not success:
            raise ValueError("更新失败")

        logger.info(f"材料状态更新: presenter_id={presenter_id}, status={status}")
        return True

    @staticmethod
    def upload_file(presenter_id: int, user_id: int, user_role: str, file) -> Dict[str, Any]:
        """上传材料文件"""
        presenter = MaterialRepository.get_presenter_by_id(presenter_id)
        if not presenter:
            raise ValueError("汇报人不存在")

        # 权限验证
        if user_id != presenter['user_id'] and user_role not in ['admin', 'teacher']:
            raise ValueError("只有汇报人本人或导师可以上传材料")

        # 文件验证
        if not file:
            raise ValueError("请选择要上传的文件")

        file_content = file.file.read()
        file_size = len(file_content)
        if file_size > 50 * 1024 * 1024:
            raise ValueError("文件大小超过限制（最大50MB）")

        original_filename = file.filename
        file_type = original_filename.split('.')[-1].lower() if '.' in original_filename else 'unknown'
        if file_type not in MaterialService.ALLOWED_FILE_TYPES:
            raise ValueError(f"不支持的文件类型: {file_type}")

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{original_filename}"

        # 创建存储目录
        materials_dir = Config.UPLOAD_DIR / "materials"
        materials_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_path = materials_dir / unique_filename
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # 创建文件记录
        file_data = {
            'meeting_id': presenter['meeting_id'],
            'presenter_id': presenter_id,
            'filename': unique_filename,
            'file_path': str(file_path),
            'file_size': file_size,
            'file_type': file_type,
            'uploaded_by': user_id
        }
        file_id = MaterialRepository.create_file(file_data)

        # 更新材料状态为已通过
        MaterialRepository.update_material_status(presenter_id, 'approved')

        logger.info(f"材料上传成功: file_id={file_id}, filename={unique_filename}")

        return {
            "file_id": file_id,
            "filename": unique_filename,
            "file_type": file_type,
            "file_size": file_size
        }

    @staticmethod
    def download_file(file_id: int) -> Dict[str, Any]:
        """下载材料文件"""
        file_info = MaterialRepository.get_file_by_id(file_id)
        if not file_info:
            raise ValueError("文件不存在")

        file_path = Path(file_info['file_path'])
        if not file_path.exists():
            raise ValueError("文件已被删除")

        return {
            "file_path": str(file_path),
            "filename": file_info['filename'],
            "file_type": file_info['file_type']
        }

    @staticmethod
    def get_meeting_materials(meeting_id: int) -> Dict[str, Any]:
        """获取组会的所有汇报材料"""
        materials = MaterialRepository.get_meeting_materials(meeting_id)
        return {"materials": materials}