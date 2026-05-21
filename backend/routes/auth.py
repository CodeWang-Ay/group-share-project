"""
================================================================================
认证路由模块 (routes/auth.py)
================================================================================

模块名称: backend/routes/auth.py
功能描述: 用户认证相关 API 端点，包括登录、注册、会话管理等
路由配置:
    - 前缀: /api/auth
    - 标签: 认证

依赖模块:
    - models.user.User           : 用户模型
    - services.auth.AuthService  : 认证服务
    - services.session           : 会话管理
    - database.connection        : 数据库连接
    - utils.auth_helper          : 认证辅助函数

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
import bcrypt
from loguru import logger

from models.user import User
from services.auth import AuthService
from services.session import session_manager
from database.connection import get_db
from utils.auth_helper import get_current_user

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
async def login(request: Request):
    """用户登录"""
    logger.info("登录API被调用")

    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        captcha = data.get("captcha", "")
        remember_me = data.get("remember_me", False)

        logger.info(f"登录数据: username={username}")

        if not username or not password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请输入用户名和密码", "error": "VALIDATION_ERROR"}
            )

        user = AuthService.authenticate_user(username, password)

        if not user:
            logger.warning(f"登录失败: {username}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"success": False, "message": "用户名或密码错误", "error": "INVALID_CREDENTIALS"}
            )

        session_token = session_manager.create_session(
            user_id=user.id,
            username=user.username,
            role=user.role,
            remember_me=remember_me
        )

        logger.info(f"登录成功: {user.username}")

        response = RedirectResponse(url=f"/?session_token={session_token}", status_code=302)
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=86400 if not remember_me else 604800,
            httponly=True,
            samesite="lax"
        )
        return response

    except Exception as e:
        logger.error(f"登录错误: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "登录过程中发生错误", "error": "INTERNAL_ERROR"}
        )


@router.post("/register")
async def register(request: Request):
    """用户注册"""
    logger.info("注册API被调用")

    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")
        email = data.get("email")
        gender = data.get("gender")
        phone = data.get("phone")
        degree_type = data.get("degree_type")

        logger.info(f"注册数据: username={username}, role={role}")

        if not username or not password or not role:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请填写完整的注册信息", "error": "VALIDATION_ERROR"}
            )

        if role not in ["teacher", "student"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "注册角色无效", "error": "VALIDATION_ERROR"}
            )

        if not User.is_valid_username(username):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "用户名格式不正确", "error": "VALIDATION_ERROR"}
            )

        if len(password) < 6:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "密码长度至少为6位", "error": "VALIDATION_ERROR"}
            )

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "message": "用户名已存在", "error": "USERNAME_EXISTS"}
                )

            new_user = User.create_user(username, password, role, email)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, email, gender, phone, degree_type, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_user.username, new_user.password_hash, new_user.role, email, gender, phone, degree_type, new_user.created_at, new_user.updated_at)
            )
            cursor.execute("SELECT last_insert_rowid()")
            new_user.id = cursor.fetchone()[0]

        logger.info(f"注册成功: {new_user.username}")
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"success": True, "message": "注册成功", "data": {"user": new_user.to_dict()}}
        )

    except Exception as e:
        logger.error(f"注册错误: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "注册过程中发生错误", "error": "INTERNAL_ERROR"}
        )


@router.post("/logout")
async def logout(request: Request):
    """用户登出"""
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]

    if not session_token:
        session_token = request.cookies.get("session_token")

    if session_token:
        session_manager.destroy_session(session_token)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "message": "登出成功"}
    )


@router.get("/me")
async def get_current_user_info(request: Request):
    """获取当前用户信息"""
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]

    if not session_token:
        session_token = request.cookies.get("session_token")

    session = session_manager.validate_session(session_token) if session_token else None
    if not session:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "未登录", "error": "NOT_AUTHENTICATED"}
        )

    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "用户不存在", "error": "USER_NOT_FOUND"}
        )

    timeout_warning = session_manager.get_session_timeout_warning(session_token)
    response_data = {
        "user": current_user.to_dict(),
        "session": {
            "is_near_expiry": session.get("is_near_expiry", False),
            "time_remaining_seconds": session.get("time_remaining_seconds", 0)
        }
    }
    if timeout_warning:
        response_data["timeout_warning"] = timeout_warning

    return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "data": response_data})


@router.put("/change-password")
async def change_password(request: Request):
    """修改密码"""
    logger.info("修改密码")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not old_password or not new_password or not confirm_password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请填写完整的密码信息", "error": "VALIDATION_ERROR"}
            )

        if len(new_password) < 6:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "新密码长度至少为6位", "error": "PASSWORD_TOO_SHORT"}
            )

        if new_password != confirm_password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "新密码与确认密码不一致", "error": "PASSWORD_MISMATCH"}
            )

        if old_password == new_password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "新密码不能与当前密码相同", "error": "SAME_PASSWORD"}
            )

        if not AuthService.authenticate_user(current_user.username, old_password):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "当前密码不正确", "error": "INVALID_OLD_PASSWORD"}
            )

        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (password_hash.decode('utf-8'), current_user.id)
            )

        logger.info(f"密码修改成功: {current_user.username}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "密码修改成功，请使用新密码登录"}
        )

    except Exception as e:
        logger.error(f"修改密码错误: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "修改密码过程中发生错误", "error": "INTERNAL_ERROR"}
        )


@router.post("/refresh")
async def refresh_session(request: Request):
    """刷新会话"""
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]

    if not session_token:
        session_token = request.cookies.get("session_token")

    if not session_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "未登录", "error": "NOT_AUTHENTICATED"}
        )

    success = session_manager.refresh_session(session_token)
    if not success:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "会话无效", "error": "INVALID_SESSION"}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "message": "会话已刷新"}
    )


@router.get("/session-status")
async def check_session_status(request: Request):
    """检查会话状态"""
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]

    if not session_token:
        session_token = request.cookies.get("session_token")

    if not session_token:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": {"authenticated": False, "message": "未登录"}}
        )

    session = session_manager.validate_session(session_token)
    if not session:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": {"authenticated": False, "message": "会话已过期"}}
        )

    timeout_warning = session_manager.get_session_timeout_warning(session_token)
    response_data = {
        "authenticated": True,
        "session": {
            "username": session.get("username"),
            "role": session.get("role"),
            "is_near_expiry": session.get("is_near_expiry", False),
            "time_remaining_seconds": session.get("time_remaining_seconds", 0),
            "remember_me": session.get("remember_me", False)
        }
    }
    if timeout_warning:
        response_data["timeout_warning"] = timeout_warning

    return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "data": response_data})