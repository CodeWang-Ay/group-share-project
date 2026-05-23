"""
================================================================================
组会业务服务模块 (services/meeting_service.py)
================================================================================

模块名称: backend/services/meeting_service.py
功能描述: 组会业务逻辑处理，返回完整响应数据

Service 类方法:
    - get_list(filters, user_id, role)       : 获取组会列表
    - create(data, user_id, role)            : 创建组会
    - get_stats()                            : 获取统计信息
    - get_detail(meeting_id, user_id, role)  : 获取组会详情
    - update(meeting_id, data, user_id, role): 更新组会
    - delete(meeting_id, user_id, role)      : 删除组会
    - update_status(meeting_id, status, user_id, role): 更新状态
    - get_presenters(meeting_id)             : 获取汇报人列表
    - add_presenter(meeting_id, data, user_id, role): 添加汇报人
    - remove_presenter(meeting_id, presenter_id, user_id, role): 移除汇报人

职责:
    - 所有业务逻辑写在这里
    - 返回完整响应数据（status_code, content）
    - 调用 Repository 进行数据操作

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from loguru import logger

from repositories.meeting_repository import MeetingRepository


class MeetingService:
    """组会业务服务类"""

    async def get_list(self, filters: Dict[str, Any], user_id: int, role: str) -> Dict[str, Any]:
        """获取组会列表"""
        page = int(filters.get("page", 1))
        limit = int(filters.get("limit", 10))
        offset = (page - 1) * limit

        MeetingRepository.auto_update_status()

        meetings = MeetingRepository.get_list(filters, limit, offset)
        total = MeetingRepository.get_count(filters)

        meetings_with_presenters = []
        for m in meetings:
            presenters = MeetingRepository.get_presenters(m['id'])
            presenter_list = []
            for p in presenters:
                files = MeetingRepository.get_presenter_files(p['id'])
                presenter_list.append({
                    "id": p['id'],
                    "user_id": p['user_id'],
                    "presenter_type": p['presenter_type'],
                    "duration_minutes": p['duration_minutes'],
                    "status": p['status'],
                    "material_status": p['material_status'],
                    "username": p['username'],
                    "real_name": p['username'],
                    "files": files
                })
            m['presenters'] = presenter_list
            meetings_with_presenters.append(m)

        total_pages = (total + limit - 1) // limit if total > 0 else 1
        return {"status_code": 200, "content": {"success": True, "data": {
            "meetings": meetings_with_presenters,
            "pagination": {
                "current_page": page, "per_page": limit, "total": total,
                "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1
            }
        }}}

    async def create(self, data: Dict[str, Any], user_id: int, role: str) -> Dict[str, Any]:
        """创建组会"""
        if role not in ['admin', 'teacher']:
            return {"status_code": 403, "content": {"success": False, "message": "只有导师和管理员可以创建组会", "error": "ACCESS_DENIED"}}

        if not data.get("title"):
            return {"status_code": 400, "content": {"success": False, "message": "组会标题不能为空", "error": "VALIDATION_ERROR"}}
        if not data.get("scheduled_at"):
            return {"status_code": 400, "content": {"success": False, "message": "会议时间不能为空", "error": "VALIDATION_ERROR"}}

        scheduled_at = datetime.fromisoformat(data["scheduled_at"])
        material_deadline = datetime.fromisoformat(data.get("material_deadline")) if data.get("material_deadline") else None

        create_data = {
            'title': data["title"],
            'meeting_type': data.get("meeting_type", "regular"),
            'scheduled_at': scheduled_at.isoformat(),
            'created_by': user_id,
            'description': data.get("description"),
            'location': data.get("location"),
            'is_online': data.get("is_online", False),
            'online_link': data.get("online_link"),
            'duration_total': data.get("duration_total", 60),
            'material_required': data.get("material_required", True),
            'material_deadline': material_deadline.isoformat() if material_deadline else None,
            'notes': data.get("notes"),
            'minutes': data.get("minutes")
        }
        meeting_id = MeetingRepository.create(create_data)

        logger.info(f"创建组会成功: {data['title']} (ID: {meeting_id})")
        return {"status_code": 201, "content": {"success": True, "message": "组会创建成功", "data": {"id": meeting_id, "title": data["title"]}}}

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        MeetingRepository.auto_update_status()
        stats = MeetingRepository.get_stats()
        return {"status_code": 200, "content": {"success": True, "data": stats}}

    async def get_detail(self, meeting_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """获取组会详情"""
        meeting = MeetingRepository.get_by_id(meeting_id)
        if not meeting:
            return {"status_code": 404, "content": {"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}}

        presenters = MeetingRepository.get_presenters(meeting_id)
        presenter_list = []
        for p in presenters:
            presenter_list.append({
                "id": p['id'],
                "user_id": p['user_id'],
                "presenter_type": p['presenter_type'],
                "duration_minutes": p['duration_minutes'],
                "status": p['status'],
                "username": p['username'],
                "real_name": p['username'],
                "user_role": p['role']
            })
        meeting['presenters'] = presenter_list

        return {"status_code": 200, "content": {"success": True, "data": meeting}}

    async def update(self, meeting_id: int, data: Dict[str, Any], user_id: int, role: str) -> Dict[str, Any]:
        """更新组会"""
        meeting = MeetingRepository.get_by_id(meeting_id)
        if not meeting:
            return {"status_code": 404, "content": {"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}}

        if role not in ['admin', 'teacher'] and meeting['created_by'] != user_id:
            return {"status_code": 403, "content": {"success": False, "message": "没有权限修改此组会", "error": "ACCESS_DENIED"}}

        update_data = {}
        if data.get("scheduled_at"):
            update_data["scheduled_at"] = datetime.fromisoformat(data["scheduled_at"]).isoformat()
        if data.get("material_deadline"):
            update_data["material_deadline"] = datetime.fromisoformat(data["material_deadline"]).isoformat()

        for field in ['title', 'meeting_type', 'description', 'location', 'is_online',
                       'online_link', 'duration_total', 'material_required', 'notes', 'minutes', 'status']:
            if field in data:
                update_data[field] = data[field]

        MeetingRepository.update(meeting_id, update_data)

        logger.info(f"组会更新成功: meeting_id={meeting_id}")
        return {"status_code": 200, "content": {"success": True, "message": "组会更新成功"}}

    async def delete(self, meeting_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """删除组会"""
        if role not in ['admin', 'teacher']:
            return {"status_code": 403, "content": {"success": False, "message": "没有权限删除组会", "error": "ACCESS_DENIED"}}

        meeting = MeetingRepository.get_by_id(meeting_id)
        if not meeting:
            return {"status_code": 404, "content": {"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}}

        MeetingRepository.delete(meeting_id)
        logger.info(f"组会删除成功: meeting_id={meeting_id}")
        return {"status_code": 200, "content": {"success": True, "message": "组会删除成功"}}

    async def update_status(self, meeting_id: int, status: str, user_id: int, role: str) -> Dict[str, Any]:
        """更新组会状态"""
        if role not in ['admin', 'teacher']:
            return {"status_code": 403, "content": {"success": False, "message": "没有权限更新组会状态", "error": "ACCESS_DENIED"}}

        valid_statuses = ['scheduled', 'ongoing', 'completed', 'cancelled', 'postponed']
        if status not in valid_statuses:
            return {"status_code": 400, "content": {"success": False, "message": f"状态值无效，有效状态：{', '.join(valid_statuses)}", "error": "INVALID_STATUS"}}

        meeting = MeetingRepository.get_by_id(meeting_id)
        if not meeting:
            return {"status_code": 404, "content": {"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}}

        MeetingRepository.update(meeting_id, {'status': status})

        if status == 'completed':
            MeetingRepository.update_presenter_status(meeting_id, 'completed')
            MeetingRepository.update_presenter_material_status(meeting_id, 'approved')
        elif status == 'cancelled':
            MeetingRepository.reset_presenter_material_status(meeting_id)

        logger.info(f"组会状态更新成功: meeting_id={meeting_id}, status={status}")
        return {"status_code": 200, "content": {"success": True, "message": "组会状态更新成功"}}

    async def get_presenters(self, meeting_id: int) -> Dict[str, Any]:
        """获取汇报人列表"""
        presenters = MeetingRepository.get_presenters(meeting_id)
        presenter_list = []
        for p in presenters:
            files = MeetingRepository.get_presenter_files(p['id'])
            presenter_list.append({
                "id": p['id'],
                "meeting_id": p['meeting_id'],
                "user_id": p['user_id'],
                "presenter_type": p['presenter_type'],
                "duration_minutes": p['duration_minutes'],
                "material_required": p['material_required'],
                "status": p['status'],
                "material_status": p['material_status'],
                "created_at": p['created_at'],
                "updated_at": p['updated_at'],
                "user": {
                    "id": p['user_id'],
                    "username": p['username'],
                    "real_name": p['username'],
                    "role": p['role'],
                    "research_direction": p['research_direction']
                },
                "files": files
            })
        return {"status_code": 200, "content": {"success": True, "data": {"presenters": presenter_list}}}

    async def add_presenter(self, meeting_id: int, data: Dict[str, Any], user_id: int, role: str) -> Dict[str, Any]:
        """添加汇报人"""
        if role not in ['admin', 'teacher']:
            creator_id = MeetingRepository.get_meeting_creator(meeting_id)
            if creator_id != user_id:
                return {"status_code": 403, "content": {"success": False, "message": "只有导师、管理员或组会创建者可以分配汇报人", "error": "ACCESS_DENIED"}}

        user_id_to_add = data.get("user_id")
        if not user_id_to_add:
            return {"status_code": 400, "content": {"success": False, "message": "请选择汇报人", "error": "VALIDATION_ERROR"}}

        if MeetingRepository.check_presenter_exists(meeting_id, user_id_to_add):
            return {"status_code": 400, "content": {"success": False, "message": "该成员已是汇报人", "error": "ALREADY_EXISTS"}}

        presenter_type = data.get("presenter_type", "assigned")
        duration_minutes = data.get("duration_minutes", 20)
        presenter_id = MeetingRepository.add_presenter(meeting_id, user_id_to_add, presenter_type, duration_minutes)

        presenter = MeetingRepository.get_presenter_by_id(presenter_id)
        logger.info(f"添加汇报人成功: meeting_id={meeting_id}, presenter_id={presenter_id}")
        return {"status_code": 200, "content": {"success": True, "message": "添加汇报人成功",
                                                 "data": {"id": presenter_id, "meeting_id": meeting_id,
                                                          "user_id": user_id_to_add, "presenter_type": presenter_type,
                                                          "duration_minutes": duration_minutes, "status": "pending",
                                                          "user": {"id": user_id_to_add, "username": presenter['username'],
                                                                   "real_name": presenter['username'],
                                                                   "research_direction": presenter['research_direction']}}}}

    async def remove_presenter(self, meeting_id: int, presenter_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """移除汇报人"""
        if role not in ['admin', 'teacher']:
            creator_id = MeetingRepository.get_meeting_creator(meeting_id)
            if creator_id != user_id:
                return {"status_code": 403, "content": {"success": False, "message": "只有导师、管理员或组会创建者可以移除汇报人", "error": "ACCESS_DENIED"}}

        if not MeetingRepository.remove_presenter(presenter_id, meeting_id):
            return {"status_code": 404, "content": {"success": False, "message": "汇报人不存在", "error": "NOT_FOUND"}}

        logger.info(f"移除汇报人成功: presenter_id={presenter_id}")
        return {"status_code": 200, "content": {"success": True, "message": "移除汇报人成功"}}