"""
================================================================================
通用辅助函数模块 (utils/helpers.py)
================================================================================

模块名称: backend/utils/helpers.py
功能描述: 提供通用的辅助函数和常量定义

主要内容:
    - FIELD_LABELS (dict): 字段中英文标签映射表
        映射数据库字段名到中文显示名称

    - getFieldLabel(field) -> str
        获取字段的中文名称标签
        参数: field - 英文字段名
        返回: 中文标签名，无映射时返回原字段名

字段映射示例:
    username      -> 用户名
    email         -> 邮箱
    phone         -> 手机号
    student_id    -> 学号/工号
    degree_type   -> 学位类型
    ...

使用方式:
    from utils.helpers import getFieldLabel, FIELD_LABELS
    label = getFieldLabel("username")  # 返回 "用户名"

作者: wjg
创建日期: 2026-05-21
================================================================================
"""

# 字段标签映射
FIELD_LABELS = {
    'username': '用户名',
    'password': '密码',
    'email': '邮箱',
    'phone': '手机号',
    'student_id': '学号/工号',
    'role': '角色',
    'gender': '性别',
    'degree_type': '学位类型',
    'research_direction': '研究方向',
    'status': '状态',
    'graduation_status': '毕业状态',
    'supervisor': '导师',
    'work_location': '工作地点',
    'work_company': '工作单位',
    'personal_bio': '个人简介',
    'personal_homepage': '个人主页',
    'id_card': '身份证号',
    'bank_card': '银行卡号',
}


def getFieldLabel(field: str) -> str:
    """
    获取字段的中文名称标签

    Args:
        field: 字段名称（英文）

    Returns:
        字段的中文名称，如果没有对应标签则返回原字段名
    """
    return FIELD_LABELS.get(field, field)