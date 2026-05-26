"""
================================================================================
仪表盘业务服务模块 (services/dashboard_service.py)
================================================================================

模块名称: backend/services/dashboard_service.py
功能描述: 仪表盘业务逻辑处理，返回完整响应数据

Service 类方法:
    - get_stats(user_id, role)              : 获取统计数据
    - get_upcoming_meetings(user_id, role)  : 获取即将到来的组会
    - get_recent_files(user_id, role)       : 获取最近提交的材料
    - get_recent_papers(user_id, role)      : 获取最近的文献

作者: wjg
创建日期: 2026-05-26
================================================================================
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from repositories.meeting_schedule_repository import MeetingScheduleRepository
from repositories.paper_repository import PaperRepository
from repositories.member_management_repository import MemberManagementRepository
from repositories.meeting_material_repository import MeetingMaterialRepository
from repositories.research_progress_repository import ResearchProgressRepository


class DashboardService:
    """仪表盘业务服务类"""

    async def get_stats(self, user_id: int, role: str) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        # 获取本月组会次数
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        month_meetings = MeetingScheduleRepository.get_count_by_date_range(month_start, now)

        # 获取上月组会次数（用于比较）
        last_month_end = month_start - timedelta(days=1)
        last_month_start = datetime(last_month_end.year, last_month_end.month, 1)
        last_month_meetings = MeetingScheduleRepository.get_count_by_date_range(last_month_start, last_month_end)

        # 获取待审阅材料数量
        pending_materials = MeetingMaterialRepository.get_pending_count(user_id, role)

        # 获取团队成员数量
        member_stats = MemberManagementRepository.get_stats()
        team_members = member_stats.get('total', 0)
        phd_count = member_stats.get('phd_count', 0)
        master_count = member_stats.get('master_count', 0)

        # 获取共享文献数量
        paper_stats = PaperRepository.get_paper_stats(user_id if role != 'admin' else None)
        total_papers = paper_stats.get('total_files', 0)

        # 获取本月新增文献
        month_new_papers = PaperRepository.get_count_by_date_range(month_start, now)

        return {
            "status_code": 200,
            "content": {
                "success": True,
                "data": {
                    "month_meetings": month_meetings,
                    "last_month_meetings": last_month_meetings,
                    "pending_materials": pending_materials,
                    "team_members": team_members,
                    "phd_count": phd_count,
                    "master_count": master_count,
                    "total_papers": total_papers,
                    "month_new_papers": month_new_papers
                }
            }
        }

    async def get_upcoming_meetings(self, user_id: int, role: str) -> Dict[str, Any]:
        """获取即将到来的组会（未来7天内）"""
        now = datetime.now()
        end_date = now + timedelta(days=7)

        meetings = MeetingScheduleRepository.get_upcoming_meetings(now, end_date, user_id, role)

        # 为每个组会添加汇报人信息和材料状态
        for meeting in meetings:
            presenters = MeetingScheduleRepository.get_meeting_presenters(meeting['id'])
            meeting['presenters'] = presenters
            # 计算材料提交状态
            submitted_count = 0
            for p in presenters:
                files = MeetingMaterialRepository.get_presenter_files(p['id'])
                if files:
                    submitted_count += 1
            meeting['materials_status'] = {
                'submitted': submitted_count,
                'total': len(presenters)
            }

        return {
            "status_code": 200,
            "content": {
                "success": True,
                "data": {
                    "meetings": meetings,
                    "total": len(meetings)
                }
            }
        }

    async def get_recent_files(self, user_id: int, role: str, limit: int = 3) -> Dict[str, Any]:
        """获取最近提交的材料"""
        files = MeetingMaterialRepository.get_recent_files(user_id, role, limit)

        # 为每个文件添加上传者信息
        for f in files:
            uploader = MemberManagementRepository.get_user_by_id(f['uploader_id'])
            f['uploader_name'] = uploader.get('username', '未知') if uploader else '未知'
            # 获取关联的组会信息
            meeting = MeetingScheduleRepository.get_by_id(f['meeting_id']) if f.get('meeting_id') else None
            f['meeting_title'] = meeting.get('title', '') if meeting else ''

        return {
            "status_code": 200,
            "content": {
                "success": True,
                "data": {
                    "files": files,
                    "total": len(files)
                }
            }
        }

    async def get_recent_papers(self, user_id: int, role: str, limit: int = 3) -> Dict[str, Any]:
        """获取最近的文献"""
        papers = PaperRepository.get_recent_papers(user_id, role, limit)

        # 为每个文献添加上传者信息
        for p in papers:
            uploader = MemberManagementRepository.get_user_by_id(p['uploader_id'])
            p['uploader_name'] = uploader.get('username', '未知') if uploader else '未知'

        return {
            "status_code": 200,
            "content": {
                "success": True,
                "data": {
                    "papers": papers,
                    "total": len(papers)
                }
            }
        }

    async def get_recent_progress(self, user_id: int, role: str, limit: int = 5) -> Dict[str, Any]:
        """获取学生研究进展"""
        # 获取团队进展列表
        progress_list = ResearchProgressRepository.get_team_list({}, limit, 0)

        # 为每个学生添加学位类型文字
        for p in progress_list:
            degree_type = p.get('degree_type', '')
            if '博士' in degree_type or degree_type == 'phd':
                p['degree_text'] = '博士'
            elif '硕士' in degree_type or degree_type == 'master':
                p['degree_text'] = '硕士'
            else:
                p['degree_text'] = '本科'

        return {
            "status_code": 200,
            "content": {
                "success": True,
                "data": {
                    "progress": progress_list,
                    "total": len(progress_list)
                }
            }
        }