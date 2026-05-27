"""
================================================================================
认证依赖模块 (dependencies/auth.py)
================================================================================

模块名称: backend/dependencies/auth.py
功能描述: 提供 FastAPI 依赖注入所需的用户认证相关函数

主要函数:
    - get_current_user(request) -> Optional[User]
        获取当前登录用户（可选）
        从请求头、cookie 或 URL 参数中获取 session_token 并验证

    - get_current_user_required(request) -> User
        获取当前用户（必须登录）
        未登录时抛出 401 异常

    - get_admin_user(request) -> User
        获取管理员用户
        验证用户角色为 admin，否则抛出 403 异常

会话令牌获取顺序:
    1. Authorization 请求头 (Bearer token)
    2. Cookie 中的 session_token
    3. URL 参数 session_token

依赖模块:
    - models.user.User      : 用户模型
    - services.session      : 会话管理服务
    - database.connection   : 数据库连接

使用方式:
    from dependencies.auth import get_current_user
    current_user = await get_current_user(request)

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import Request, HTTPException, status
from typing import Optional
from loguru import logger

from models.user import User
from services.session_service import session_manager
from database.connection import get_db


async def get_current_user(request: Request) -> Optional[User]:
    """
    获取当前登录用户
    尝试所有可能的 token 来源，使用有效的那个
    """
    # 收集所有可能的 token 来源
    tokens_to_try = []

    # URL 参数（最新登录传递的）
    url_token = request.query_params.get("session_token")
    if url_token:
        tokens_to_try.append(url_token)

    # Authorization 请求头
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        header_token = auth_header[7:]
        if header_token not in tokens_to_try:
            tokens_to_try.append(header_token)

    # Cookie
    cookie_token = request.cookies.get("session_token")
    if cookie_token and cookie_token not in tokens_to_try:
        tokens_to_try.append(cookie_token)

    # 尝试所有 token，找到有效的
    for session_token in tokens_to_try:
        session = session_manager.validate_session(session_token)
        if session:
            # 找到有效 session，获取用户
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, username, password_hash, role, email, phone, "
                        "student_id, research_direction, status, avatar, created_at, updated_at "
                        "FROM users WHERE id = ?",
                        (session["user_id"],)
                    )
                    user_row = cursor.fetchone()
                    if user_row:
                        return User.from_dict(dict(user_row))
            except Exception:
                pass

    return None

    # 从数据库获取用户信息
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash, role, email, phone, "
                "student_id, research_direction, status, avatar, created_at, updated_at "
                "FROM users WHERE id = ?",
                (session["user_id"],)
            )
            user_row = cursor.fetchone()
            if user_row:
                return User.from_dict(dict(user_row))
    except Exception:
        pass

    return None


async def get_current_user_required(request: Request) -> User:
    """
    获取当前用户（必须登录）
    如果用户未登录，抛出 401 异常

    Args:
        request: FastAPI 请求对象

    Returns:
        User 对象

    Raises:
        HTTPException: 401 未授权
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录"
        )
    return user


async def get_admin_user(request: Request) -> User:
    """
    获取管理员用户
    如果用户未登录或不是管理员，抛出异常

    Args:
        request: FastAPI 请求对象

    Returns:
        User 对象（管理员）

    Raises:
        HTTPException: 401 未授权 或 403 无权限
    """
    user = await get_current_user_required(request)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user