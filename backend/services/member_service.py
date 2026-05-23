"""
================================================================================
成员业务服务模块 (services/member_service.py)
================================================================================

模块名称: backend/services/member_service.py
功能描述: 成员管理业务逻辑处理

Service 类方法:
    - get_list(filters, pagination)   : 获取成员列表
    - get_stats()                      : 获取统计数据
    - create(data)                     : 创建成员
    - update(member_id, data)          : 更新成员
    - delete(member_id)                : 删除成员
    - update_status(member_id, status) : 更新状态
    - reset_password(member_id, pwd)   : 重置密码
    - batch_update_role(ids, role)     : 批量更新角色
    - batch_update_status(ids, status) : 批量更新状态
    - batch_delete(ids)                : 批量删除

职责:
    - 处理业务逻辑
    - 数据验证和转换
    - 调用 Repository 进行数据操作

依赖:
    - repositories.member_repository: 数据访问层
    - models.user.User              : 用户模型

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

    @staticmethod
    def get_list(filters: Dict[str, Any], pagination: Dict[str, int]) -> Dict[str, Any]:
        """获取成员列表"""
        page = pagination.get('page', 1)
        per_page = pagination.get('per_page', 10)

        # 验证分页参数
        if per_page not in [5, 10, 20, 50, 100]:
            per_page = 10
        if page < 1:
            page = 1

        offset = (page - 1) * per_page

        # 获取数据
        members = MemberRepository.get_list(filters, offset, per_page)
        total = MemberRepository.get_count(filters)

        # 处理数据
        for member in members:
            member['student_id'] = member.get('student_id') or None
            member['email'] = member.get('email') or None
            member['phone'] = member.get('phone') or None
            member['status'] = member.get('status') or 'active'
            member['research_direction'] = member.get('research_direction') or None
            member['degree_type'] = member.get('degree_type') or None
            member['gender'] = member.get('gender') or None

            # 头像处理
            if member.get('avatar'):
                member['avatar'] = member['avatar']
            else:
                member['avatar'] = f"https://picsum.photos/seed/{member['username']}/100/100.jpg"

            # 日期格式化
            if member.get('created_at'):
                member['created_at'] = member['created_at'].split(' ')[0]

        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "members": members,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": page + 1 if has_next else None,
                "prev_page": page - 1 if has_prev else None
            }
        }

    @staticmethod
    def get_stats() -> Dict[str, int]:
        """获取成员统计"""
        return MemberRepository.get_stats()

    @staticmethod
    def create(data: Dict[str, Any]) -> Dict[str, Any]:
        """创建成员"""
        # 必填字段验证
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', '').strip()

        if not username or not password or not email or not role:
            raise ValueError("请填写完整的注册信息")

        # 角色验证
        if role not in ['admin', 'teacher', 'student']:
            raise ValueError("角色值无效")

        # 用户名格式验证
        if not User.is_valid_username(username):
            raise ValueError("用户名格式不正确：3-50个字符，只允许字母、数字、下划线")

        # 密码长度验证
        if len(password) < 6:
            raise ValueError("密码长度至少为6位")

        # 箱格式验证
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("邮箱格式不正确")

        # 检查用户名是否存在
        if MemberRepository.check_username_exists(username):
            raise ValueError("用户名已存在")

        # 检查邮箱是否存在
        if MemberRepository.check_email_exists(email):
            raise ValueError("邮箱已存在")

        # 检查学号是否存在
        student_id = data.get('student_id', '').strip()
        if student_id and MemberRepository.check_student_id_exists(student_id):
            raise ValueError("学号/工号已存在")

        # 生成密码哈希
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # 准备创建数据
        create_data = {
            'username': username,
            'password_hash': password_hash,
            'email': email,
            'phone': data.get('phone', '').strip() or None,
            'student_id': student_id or None,
            'role': role,
            'research_direction': data.get('research_direction'),
            'personal_bio': data.get('personal_bio'),
            'gender': data.get('gender'),
            'id_card': data.get('id_card'),
            'bank_card': data.get('bank_card')
        }

        # 创建成员
        new_user_id = MemberRepository.create(create_data)

        logger.info(f"创建新用户: {username} (ID: {new_user_id})")

        return {
            "id": new_user_id,
            "username": username,
            "email": email,
            "role": role,
            "student_id": student_id
        }

    @staticmethod
    def update(member_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新成员信息"""
        # 允许更新的字段
        allowed_fields = [
            'username', 'email', 'phone', 'student_id', 'role',
            'research_direction', 'personal_bio', 'gender',
            'id_card', 'bank_card', 'status', 'degree_type'
        ]

        update_data = {}
        for field in allowed_fields:
            if field in data and data[field] is not None:
                update_data[field] = data[field]

        if not update_data:
            raise ValueError("没有提供要更新的数据")

        # 角色验证
        if 'role' in update_data and update_data['role'] not in ['admin', 'teacher', 'student']:
            raise ValueError("角色值无效")

        # 状态验证
        if 'status' in update_data and update_data['status'] not in ['active', 'inactive']:
            raise ValueError("状态值无效")

        # 身份证验证
        if 'id_card' in update_data and update_data['id_card']:
            if len(update_data['id_card']) != 18:
                raise ValueError("身份证号必须为18位")

        # 检查成员是否存在
        member = MemberRepository.get_by_id(member_id)
        if not member:
            raise ValueError("成员不存在")

        # 检查用户名是否重复
        if 'username' in update_data:
            if MemberRepository.check_username_exists(update_data['username'], exclude_id=member_id):
                raise ValueError("用户名已存在")

        # 更新成员
        success = MemberRepository.update(member_id, update_data)
        if not success:
            raise ValueError("更新失败")

        logger.info(f"成员信息更新成功: member_id={member_id}")
        return update_data

    @staticmethod
    def delete(member_id: int) -> bool:
        """删除成员"""
        member = MemberRepository.get_by_id(member_id)
        if not member:
            raise ValueError("成员不存在")

        success = MemberRepository.delete(member_id)
        if not success:
            raise ValueError("删除失败")

        logger.info(f"成员删除成功: member_id={member_id}")
        return True

    @staticmethod
    def update_status(member_id: int, status: str) -> bool:
        """更新成员状态"""
        if status not in ['active', 'inactive']:
            raise ValueError("状态值无效")

        member = MemberRepository.get_by_id(member_id)
        if not member:
            raise ValueError("成员不存在")

        success = MemberRepository.update_status(member_id, status)
        if not success:
            raise ValueError("更新失败")

        logger.info(f"成员状态更新成功: member_id={member_id}, status={status}")
        return True

    @staticmethod
    def reset_password(member_id: int, password: str = "123456") -> Dict[str, Any]:
        """重置成员密码"""
        if len(password) < 6:
            raise ValueError("密码长度至少为6位")

        member = MemberRepository.get_by_id(member_id)
        if not member:
            raise ValueError("成员不存在")

        # 生成密码哈希
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        success = MemberRepository.update_password(member_id, password_hash)
        if not success:
            raise ValueError("密码重置失败")

        logger.info(f"密码重置成功: member_id={member_id}")
        return {
            "new_password": password,
            "member_id": member_id,
            "member_username": member.get('username')
        }

    @staticmethod
    def batch_update_role(user_ids: List[int], role: str) -> int:
        """批量更新角色"""
        if not user_ids:
            raise ValueError("缺少用户ID列表")

        if role not in ['admin', 'teacher', 'student']:
            raise ValueError("角色必须是admin、teacher或student")

        updated_count = MemberRepository.batch_update_role(user_ids, role)
        logger.info(f"批量更新角色成功: {updated_count} 个成员")
        return updated_count

    @staticmethod
    def batch_update_status(user_ids: List[int], status: str) -> int:
        """批量更新状态"""
        if not user_ids:
            raise ValueError("缺少用户ID列表")

        if status not in ['active', 'inactive']:
            raise ValueError("状态必须是active或inactive")

        updated_count = MemberRepository.batch_update_status(user_ids, status)
        logger.info(f"批量更新状态成功: {updated_count} 个成员")
        return updated_count

    @staticmethod
    def batch_delete(user_ids: List[int]) -> int:
        """批量删除"""
        if not user_ids:
            raise ValueError("缺少要删除的成员ID")

        deleted_count = MemberRepository.batch_delete(user_ids)
        logger.info(f"批量删除成功: {deleted_count} 个成员")
        return deleted_count