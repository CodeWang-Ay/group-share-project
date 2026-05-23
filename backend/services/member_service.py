"""
================================================================================
成员业务服务模块 (services/member_service.py)
================================================================================

模块名称: backend/services/member_service.py
功能描述: 成员管理业务逻辑处理，返回完整响应数据

Service 类方法:
    - get_list(filters, pagination)   : 获取成员列表
    - get_stats()                      : 获取统计数据
    - create(data, role, username)     : 创建成员
    - update(member_id, data, role)    : 更新成员
    - delete(member_id, role)          : 删除成员
    - update_status(member_id, status, role): 更新状态
    - reset_password(member_id, pwd, role, username): 重置密码
    - batch_update_role(ids, role, user_role): 批量更新角色
    - batch_update_status(ids, status, user_role): 批量更新状态
    - batch_delete(ids, user_role)     : 批量删除

职责:
    - 所有业务逻辑写在这里
    - 返回完整响应数据（status_code, content）
    - 调用 Repository 进行数据操作

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
import re
import bcrypt
from typing import Dict, Any, List
from loguru import logger

from repositories.member_repository import MemberRepository
from models.user import User


class MemberService:
    """成员管理业务服务类"""

    async def get_list(self, filters: Dict[str, Any], pagination: Dict[str, int]) -> Dict[str, Any]:
        """获取成员列表"""
        page = pagination.get('page', 1)
        per_page = pagination.get('per_page', 10)
        if per_page not in [5, 10, 20, 50, 100]:
            per_page = 10

        offset = (page - 1) * per_page
        members = MemberRepository.get_list(filters, offset, per_page)
        total = MemberRepository.get_count(filters)

        # 数据处理
        for member in members:
            member['avatar'] = member.get('avatar') or f"https://picsum.photos/seed/{member['username']}/100/100.jpg"
            if member.get('created_at'):
                member['created_at'] = member['created_at'].split(' ')[0]

        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        return {"status_code": 200, "content": {"success": True, "data": {
            "members": members,
            "pagination": {"current_page": page, "per_page": per_page, "total": total, "total_pages": total_pages,
                           "has_next": page < total_pages, "has_prev": page > 1}
        }}}

    async def get_stats(self) -> Dict[str, Any]:
        """获取成员统计"""
        stats = MemberRepository.get_stats()
        return {"status_code": 200, "content": {"success": True, "data": stats}}

    async def create(self, data: Dict[str, Any], user_role: str, username: str) -> Dict[str, Any]:
        """创建成员"""
        # 1. 权限验证
        if user_role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "没有权限添加成员", "error": "ACCESS_DENIED"}}

        # 2. 必填字段验证
        required = ['username', 'password', 'email', 'role']
        for field in required:
            if not data.get(field):
                return {"status_code": 400, "content": {"success": False, "message": f"缺少必填字段: {field}", "error": "MISSING_FIELD"}}

        # 3. 业务验证
        username = data['username'].strip()
        password = data['password'].strip()
        email = data['email'].strip()
        role = data['role'].strip()

        if role not in ['admin', 'teacher', 'student']:
            return {"status_code": 400, "content": {"success": False, "message": "角色值无效", "error": "INVALID_ROLE"}}

        if not User.is_valid_username(username):
            return {"status_code": 400, "content": {"success": False, "message": "用户名格式不正确", "error": "INVALID_USERNAME"}}

        if len(password) < 6:
            return {"status_code": 400, "content": {"success": False, "message": "密码长度至少为6位", "error": "PASSWORD_TOO_SHORT"}}

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {"status_code": 400, "content": {"success": False, "message": "邮箱格式不正确", "error": "INVALID_EMAIL"}}

        # 4. 唯一性验证
        if MemberRepository.check_username_exists(username):
            return {"status_code": 400, "content": {"success": False, "message": "用户名已存在", "error": "USERNAME_EXISTS"}}

        if MemberRepository.check_email_exists(email):
            return {"status_code": 400, "content": {"success": False, "message": "邮箱已存在", "error": "EMAIL_EXISTS"}}

        # 5. 创建用户
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        create_data = {
            'username': username, 'password_hash': password_hash, 'email': email, 'role': role,
            'phone': data.get('phone'), 'student_id': data.get('student_id'),
            'research_direction': data.get('research_direction'), 'personal_bio': data.get('personal_bio'),
            'gender': data.get('gender'), 'id_card': data.get('id_card'), 'bank_card': data.get('bank_card')
        }
        user_id = MemberRepository.create(create_data)

        logger.info(f"管理员 {username} 创建了新用户: {username} (ID: {user_id})")
        return {"status_code": 201, "content": {"success": True, "message": "成员添加成功",
                                                 "data": {"id": user_id, "username": username, "email": email, "role": role}}}

    async def update(self, member_id: int, data: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """更新成员信息"""
        if user_role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "没有权限更新成员信息", "error": "ACCESS_DENIED"}}

        allowed_fields = ['username', 'email', 'phone', 'student_id', 'role', 'research_direction',
                          'personal_bio', 'gender', 'id_card', 'bank_card', 'status', 'degree_type']
        update_data = {f: data[f] for f in allowed_fields if f in data}

        if not update_data:
            return {"status_code": 400, "content": {"success": False, "message": "没有提供要更新的数据", "error": "NO_DATA"}}

        if 'role' in update_data and update_data['role'] not in ['admin', 'teacher', 'student']:
            return {"status_code": 400, "content": {"success": False, "message": "角色值无效", "error": "INVALID_ROLE"}}

        if 'status' in update_data and update_data['status'] not in ['active', 'inactive']:
            return {"status_code": 400, "content": {"success": False, "message": "状态值无效", "error": "INVALID_STATUS"}}

        member = MemberRepository.get_by_id(member_id)
        if not member:
            return {"status_code": 404, "content": {"success": False, "message": "成员不存在", "error": "MEMBER_NOT_FOUND"}}

        if 'username' in update_data and MemberRepository.check_username_exists(update_data['username'], member_id):
            return {"status_code": 400, "content": {"success": False, "message": "用户名已存在", "error": "USERNAME_EXISTS"}}

        success = MemberRepository.update(member_id, update_data)
        if not success:
            return {"status_code": 500, "content": {"success": False, "message": "更新失败", "error": "UPDATE_FAILED"}}

        logger.info(f"成员信息更新成功: member_id={member_id}")
        return {"status_code": 200, "content": {"success": True, "message": "成员信息更新成功", "data": update_data}}

    async def delete(self, member_id: int, user_role: str) -> Dict[str, Any]:
        """删除成员"""
        if user_role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "没有权限删除成员", "error": "ACCESS_DENIED"}}

        member = MemberRepository.get_by_id(member_id)
        if not member:
            return {"status_code": 404, "content": {"success": False, "message": "成员不存在", "error": "MEMBER_NOT_FOUND"}}

        MemberRepository.delete(member_id)
        logger.info(f"成员删除成功: member_id={member_id}")
        return {"status_code": 200, "content": {"success": True, "message": "成员删除成功"}}

    async def update_status(self, member_id: int, new_status: str, user_role: str) -> Dict[str, Any]:
        """更新成员状态"""
        if user_role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "没有权限修改成员状态", "error": "ACCESS_DENIED"}}

        if new_status not in ['active', 'inactive']:
            return {"status_code": 400, "content": {"success": False, "message": "状态值无效", "error": "INVALID_STATUS"}}

        member = MemberRepository.get_by_id(member_id)
        if not member:
            return {"status_code": 404, "content": {"success": False, "message": "成员不存在", "error": "MEMBER_NOT_FOUND"}}

        MemberRepository.update_status(member_id, new_status)
        logger.info(f"成员状态更新成功: member_id={member_id}, status={new_status}")
        return {"status_code": 200, "content": {"success": True, "message": "成员状态更新成功"}}

    async def reset_password(self, member_id: int, password: str, user_role: str, username: str) -> Dict[str, Any]:
        """重置密码"""
        if user_role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "没有权限重置密码", "error": "ACCESS_DENIED"}}

        if len(password) < 6:
            return {"status_code": 400, "content": {"success": False, "message": "密码长度至少为6位", "error": "PASSWORD_TOO_SHORT"}}

        member = MemberRepository.get_by_id(member_id)
        if not member:
            return {"status_code": 404, "content": {"success": False, "message": "成员不存在", "error": "MEMBER_NOT_FOUND"}}

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        MemberRepository.update_password(member_id, password_hash)

        logger.info(f"管理员 {username} 重置了用户 {member.get('username')} 的密码")
        return {"status_code": 200, "content": {"success": True, "message": "密码重置成功",
                                                 "data": {"new_password": password, "member_id": member_id, "member_username": member.get('username')}}}

    async def batch_update_role(self, user_ids: List[int], role: str, user_role: str) -> Dict[str, Any]:
        """批量更新角色"""
        if user_role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "没有权限批量修改成员角色", "error": "ACCESS_DENIED"}}

        if not user_ids:
            return {"status_code": 400, "content": {"success": False, "message": "缺少用户ID列表", "error": "MISSING_USER_IDS"}}

        if role not in ['admin', 'teacher', 'student']:
            return {"status_code": 400, "content": {"success": False, "message": "角色必须是admin、teacher或student", "error": "INVALID_ROLE"}}

        updated_count = MemberRepository.batch_update_role(user_ids, role)
        logger.info(f"批量更新角色成功: {updated_count} 个成员")
        return {"status_code": 200, "content": {"success": True, "message": f"成功更新 {updated_count} 个成员的角色", "updated_count": updated_count}}

    async def batch_update_status(self, user_ids: List[int], status: str, user_role: str) -> Dict[str, Any]:
        """批量更新状态"""
        if user_role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "没有权限批量修改成员状态", "error": "ACCESS_DENIED"}}

        if not user_ids:
            return {"status_code": 400, "content": {"success": False, "message": "缺少用户ID列表", "error": "MISSING_USER_IDS"}}

        if status not in ['active', 'inactive']:
            return {"status_code": 400, "content": {"success": False, "message": "状态必须是active或inactive", "error": "INVALID_STATUS"}}

        updated_count = MemberRepository.batch_update_status(user_ids, status)
        logger.info(f"批量更新状态成功: {updated_count} 个成员")
        return {"status_code": 200, "content": {"success": True, "message": f"成功更新 {updated_count} 个成员的状态", "updated_count": updated_count}}

    async def batch_delete(self, user_ids: List[int], user_role: str) -> Dict[str, Any]:
        """批量删除"""
        if user_role != "admin":
            return {"status_code": 403, "content": {"success": False, "message": "没有权限批量删除成员", "error": "ACCESS_DENIED"}}

        if not user_ids:
            return {"status_code": 400, "content": {"success": False, "message": "缺少要删除的成员ID", "error": "MISSING_USER_IDS"}}

        deleted_count = MemberRepository.batch_delete(user_ids)
        logger.info(f"批量删除成功: {deleted_count} 个成员")
        return {"status_code": 200, "content": {"success": True, "message": f"成功删除 {deleted_count} 个成员", "deleted_count": deleted_count}}