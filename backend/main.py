"""
FastAPI应用主入口
提供用户认证系统的API服务
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import sqlite3
import os
from datetime import datetime
from typing import Optional

# 导入内部模块
from models.user import User
from models.file import File
from database.connection import get_db, DATABASE_PATH
from services.auth import AuthService
from services.session import session_manager
from services.file_service import FileService
from loguru import logger

# 创建FastAPI应用实例
app = FastAPI(
    title="基础用户认证系统",
    description="研究生组会文件共享系统 - 用户认证API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置模板引擎
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# 设置模板环境变量
templates.env.globals['app_name'] = "研究生组会文件共享系统"
templates.env.globals['current_year'] = datetime.now().year

# 配置CORS中间件 - 支持前后端通信
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 挂载静态文件目录 - 用于文件预览
uploads_dir = Path(__file__).parent.parent / "uploads"
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
else:
    # 如果uploads目录不存在，创建它
    uploads_dir.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


# 错误处理中间件
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    添加安全头信息的中间件
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    记录请求日志的中间件
    """
    start_time = datetime.now()

    # 记录请求开始
    print(f"[{start_time.isoformat()}] {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # 记录请求完成
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"[{end_time.isoformat()}] {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")

        return response
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] {request.method} {request.url.path} - ERROR: {str(e)}")
        raise


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error": "INTERNAL_ERROR"
        }
    )


# 依赖函数：获取当前用户
async def get_current_user(request: Request) -> Optional[User]:
    """
    获取当前登录用户
    从请求头、cookie或URL参数中获取会话令牌并验证
    """
    # 从请求头中获取会话令牌
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]  # 移除 "Bearer " 前缀

    # 如果请求头中没有，尝试从cookie中获取
    if not session_token:
        session_token = request.cookies.get("session_token")

    # 如果cookie中也没有，尝试从URL参数中获取（仅用于跨域场景，一次性使用）
    if not session_token:
        session_token = request.query_params.get("session_token")
        # 如果是从URL参数获取的token，验证后需要重定向到干净的URL
        url_token_used = bool(session_token)

    if not session_token:
        return None

    # 验证会话令牌
    session = session_manager.validate_session(session_token)
    if not session:
        return None

    # 从数据库获取用户信息
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash, role, created_at, updated_at "
                "FROM users WHERE id = ?",
                (session["user_id"],)
            )
            user_row = cursor.fetchone()
            if user_row:
                return User.from_dict(dict(user_row))
    except Exception:
        pass

    return None


# 健康检查端点
@app.get("/health")
async def health_check():
    """
    应用健康检查端点
    检查数据库连接、会话管理器状态等关键组件
    """
    health_status = {
        "success": True,
        "message": "应用运行正常",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "status": "healthy",
        "checks": {}
    }

    try:
        # 检查数据库连接
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                health_status["checks"]["database"] = {
                    "status": "healthy",
                    "message": "数据库连接正常"
                }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "message": f"数据库连接失败: {str(e)}"
            }
            health_status["status"] = "unhealthy"
            health_status["success"] = False
            health_status["message"] = "部分服务异常"

        # 检查会话管理器
        try:
            session_count = len(session_manager.sessions)
            health_status["checks"]["session_manager"] = {
                "status": "healthy",
                "message": f"会话管理器正常，当前活跃会话: {session_count}"
            }
        except Exception as e:
            health_status["checks"]["session_manager"] = {
                "status": "unhealthy",
                "message": f"会话管理器异常: {str(e)}"
            }
            health_status["status"] = "unhealthy"
            health_status["success"] = False
            health_status["message"] = "部分服务异常"

        # 检查模板引擎
        try:
            # 尝试获取模板目录信息
            templates_info = {
                "directory": str(templates_dir),
                "exists": templates_dir.exists()
            }
            health_status["checks"]["templates"] = {
                "status": "healthy" if templates_dir.exists() else "warning",
                "message": f"模板目录{'' if templates_dir.exists() else '不存在'}",
                "info": templates_info
            }
        except Exception as e:
            health_status["checks"]["templates"] = {
                "status": "unhealthy",
                "message": f"模板引擎异常: {str(e)}"
            }

        # 检查数据库文件状态
        try:
            db_path = Path(DATABASE_PATH)
            if db_path.exists():
                db_size = db_path.stat().st_size
                health_status["checks"]["database_file"] = {
                    "status": "healthy",
                    "message": f"数据库文件正常，大小: {db_size} bytes",
                    "path": str(db_path),
                    "size": db_size
                }
            else:
                health_status["checks"]["database_file"] = {
                    "status": "warning",
                    "message": "数据库文件不存在，将在首次使用时创建",
                    "path": str(db_path)
                }
        except Exception as e:
            health_status["checks"]["database_file"] = {
                "status": "unhealthy",
                "message": f"数据库文件检查失败: {str(e)}"
            }

        # 系统信息
        import sys
        import platform
        health_status["system"] = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "memory_usage": "N/A"  # 可以添加内存监控
        }

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["success"] = False
        health_status["message"] = f"健康检查失败: {str(e)}"
        health_status["error"] = str(e)

    # 确定HTTP状态码
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


# 详细健康检查端点（包含更多信息）
@app.get("/health/detailed")
async def detailed_health_check():
    """
    详细健康检查端点
    提供更详细的系统信息和性能指标
    """
    detailed_status = await health_check()

    try:
        # 添加更多详细信息

        # 清理过期会话并统计
        expired_count = session_manager.cleanup_expired_sessions()
        detailed_status["data"]["cleanup_info"] = {
            "expired_sessions_cleaned": expired_count,
            "active_sessions": len(session_manager.sessions)
        }

        # 数据库统计信息
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                # 用户统计
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]

                cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
                users_by_role = dict(cursor.fetchall())

                detailed_status["data"]["database_stats"] = {
                    "total_users": total_users,
                    "users_by_role": users_by_role
                }
        except Exception as e:
            detailed_status["data"]["database_stats"] = {
                "error": f"获取数据库统计失败: {str(e)}"
            }

        # 添加环境变量信息（隐藏敏感信息）
        import os
        detailed_status["data"]["environment"] = {
            "cwd": os.getcwd(),
            "debug": os.getenv("DEBUG", "false").lower() == "true"
        }

    except Exception as e:
        detailed_status["data"]["detailed_check_error"] = str(e)

    return JSONResponse(content=detailed_status)


# 就绪检查端点（用于Kubernetes等容器编排）
@app.get("/ready")
async def readiness_check():
    """
    就绪检查端点
    检查应用是否准备好接收请求
    """
    try:
        # 检查数据库连接
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")

        # 检查关键目录
        required_dirs = [templates_dir]
        for dir_path in required_dirs:
            if not dir_path.exists():
                return JSONResponse(
                    status_code=503,
                    content={
                        "ready": False,
                        "message": f"必需目录不存在: {dir_path}"
                    }
                )

        return JSONResponse(
            status_code=200,
            content={
                "ready": True,
                "message": "应用已就绪"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "message": f"应用未就绪: {str(e)}"
            }
        )


# 存活检查端点（最简单的检查）
@app.get("/alive")
async def liveness_check():
    """
    存活检查端点
    最简单的检查，确认应用进程正在运行
    """
    return JSONResponse(
        status_code=200,
        content={
            "alive": True,
            "timestamp": datetime.now().isoformat()
        }
    )


# 应用指标端点
@app.get("/metrics")
async def metrics():
    """
    应用指标端点
    提供基本的性能和使用统计信息
    """
    try:
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "uptime": "N/A",  # 可以添加启动时间跟踪
            "sessions": {
                "active": len(session_manager.sessions),
                "expired_last_cleanup": session_manager.cleanup_expired_sessions()
            }
        }

        # 数据库统计
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                # 用户统计
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]

                cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
                users_by_role = dict(cursor.fetchall())

                # 按创建日期统计最近注册用户
                cursor.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM users
                    WHERE created_at >= date('now', '-7 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                recent_registrations = dict(cursor.fetchall())

                metrics_data["users"] = {
                    "total": total_users,
                    "by_role": users_by_role,
                    "recent_registrations_7_days": recent_registrations
                }
        except Exception as e:
            metrics_data["users"] = {"error": str(e)}

        # 系统资源信息
        import psutil
        if psutil:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            metrics_data["system"] = {
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "cpu_percent": psutil.cpu_percent(interval=1)
            }

        return JSONResponse(content=metrics_data)

    except ImportError:
        # psutil不可用时的简化版本
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "message": "基础指标（需要psutil库获取系统指标）",
            "sessions": {
                "active": len(session_manager.sessions)
            }
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"获取指标失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )


# 主页面路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    主页面路由 - 根据登录状态显示不同页面
    """
    # 检查是否通过URL参数传递了token
    url_token = request.query_params.get("session_token")

    # 检查用户是否已登录
    print(f"检查用户登录状态...")
    print(f"   - Cookie session_token: {request.cookies.get('session_token')}")
    print(f"   - Authorization header: {request.headers.get('Authorization')}")
    print(f"   - URL token: {url_token}")

    current_user = await get_current_user(request)
    print(f"   - Current user: {current_user}")

    if not current_user:
        # 未登录，直接显示登录页面
        print("用户未登录，显示登录页面")
        return templates.TemplateResponse("login.html", {"request": request})

    # 如果是通过URL参数认证成功，设置cookie并重定向到干净的URL
    if url_token:
        from fastapi.responses import RedirectResponse
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_token",
            value=url_token,
            max_age=86400,  # 24小时
            httponly=True,
            samesite="lax"
        )
        return response

    # 已登录，提供主页面模板，并传递用户信息
    print(f"用户已登录: {current_user.username}，显示主页面")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user
    })


# 登录页面路由
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    登录页面路由
    """
    print(request)
    return templates.TemplateResponse("login.html", {"request": request})


# 注册页面路由
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    注册页面路由
    """
    return templates.TemplateResponse("register.html", {"request": request})


# 共享文件页面路由
@app.get("/share-file", response_class=HTMLResponse)
async def share_file_page(request: Request):
    """
    共享文件页面路由
    需要用户登录才能访问
    """
    # 检查用户是否已登录
    current_user = await get_current_user(request)
    if not current_user:
        # 未登录，重定向到登录页面
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # 已登录，显示共享文件页面
    return templates.TemplateResponse("share-file.html", {
        "request": request,
        "user": current_user
    })


# API端点：用户登录
@app.post("/api/auth/login")
async def login(request: Request):
    """
    用户登录API端点

    接收JSON格式的登录数据并验证用户凭据
    登录成功后直接重定向到主页
    """
    print("登录API被调用")

    try:
        # 获取请求体数据
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        captcha = data.get("captcha", "")
        remember_me = data.get("remember_me", False)

        print(f"接收到登录数据: username={username}, password={'***' if password else 'None'}, captcha={captcha}, remember_me={remember_me}")

        # 验证输入
        if not username or not password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "请输入用户名和密码",
                    "error": "VALIDATION_ERROR"
                }
            )

        # 使用认证服务验证用户
        user = AuthService.authenticate_user(username, password)

        if not user:
            print(f"登录失败: 用户名或密码错误 (username={username})")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "message": "用户名或密码错误",
                    "error": "INVALID_CREDENTIALS"
                }
            )

        # 登录成功，创建会话
        session_token = session_manager.create_session(
            user_id=user.id,
            username=user.username,
            role=user.role,
            remember_me=remember_me
        )

        print(f"登录成功: user={user.username}, role={user.role}, session_token={session_token[:20]}...")

        # 登录成功，直接重定向到主页，在URL中传递session_token
        from fastapi.responses import RedirectResponse
        response = RedirectResponse(url=f"/?session_token={session_token}", status_code=302)

        # 同时设置cookie，以便后续请求使用
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=86400 if not remember_me else 604800,  # 24小时或7天
            httponly=True,
            samesite="lax"
        )

        return response

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "登录过程中发生错误",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：用户注册
@app.post("/api/auth/register")
async def register(request: Request):
    """
    用户注册API端点

    接收JSON格式的注册数据并创建新用户
    """
    print("注册API被调用")

    try:
        # 获取请求体数据
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")

        print(f"接收到注册数据: username={username}, password={'***' if password else 'None'}, role={role}")

        # 验证输入
        if not username or not password or not role:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "请填写完整的注册信息",
                    "error": "VALIDATION_ERROR"
                }
            )

        if role not in ["teacher", "student"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "注册角色无效",
                    "error": "VALIDATION_ERROR"
                }
            )

        # 验证用户名格式
        if not User.is_valid_username(username):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "用户名格式不正确：3-50个字符，只允许字母、数字、下划线",
                    "error": "VALIDATION_ERROR"
                }
            )

        # 验证密码长度
        if len(password) < 6:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "密码长度至少为6位",
                    "error": "VALIDATION_ERROR"
                }
            )

        # 连接数据库并检查用户名是否已存在
        with get_db() as conn:
            cursor = conn.cursor()

            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": "用户名已存在",
                        "error": "USERNAME_EXISTS"
                    }
                )

            # 创建新用户
            new_user = User.create_user(username, password, role)

            cursor.execute(
                "INSERT INTO users (username, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (
                    new_user.username,
                    new_user.password_hash,
                    new_user.role,
                    new_user.created_at,
                    new_user.updated_at
                )
            )

            # 获取新创建的用户ID
            cursor.execute("SELECT last_insert_rowid()")
            new_user.id = cursor.fetchone()[0]

        print(f"注册成功: user={new_user.username}, role={new_user.role}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "注册成功",
                "data": {
                    "user": new_user.to_dict()
                }
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "注册过程中发生错误",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：用户登出
@app.post("/api/auth/logout")
async def logout(request: Request):
    """
    用户登出API端点

    清除用户会话信息
    """
    # 获取会话令牌
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]  # 移除 "Bearer " 前缀

    if not session_token:
        session_token = request.cookies.get("session_token")

    # 销毁会话
    if session_token:
        session_manager.destroy_session(session_token)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "登出成功"
        }
    )


# API端点：获取当前用户信息
@app.get("/api/auth/me")
async def get_current_user_info(request: Request):
    """
    获取当前登录用户信息
    """
    # 获取会话令牌
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]

    if not session_token:
        session_token = request.cookies.get("session_token")

    # 验证会话并获取详细信息
    session = session_manager.validate_session(session_token) if session_token else None
    if not session:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "未登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    # 从数据库获取用户信息
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "用户不存在",
                "error": "USER_NOT_FOUND"
            }
        )

    # 检查会话超时警告
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

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": response_data
        }
    )


# API端点：刷新会话
@app.post("/api/auth/refresh")
async def refresh_session(request: Request):
    """
    刷新会话过期时间
    """
    # 获取会话令牌
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]

    if not session_token:
        session_token = request.cookies.get("session_token")

    if not session_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "未登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    # 刷新会话
    success = session_manager.refresh_session(session_token)
    if not success:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "会话无效",
                "error": "INVALID_SESSION"
            }
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "会话已刷新"
        }
    )


# API端点：检查会话状态
@app.get("/api/auth/session-status")
async def check_session_status(request: Request):
    """
    检查当前会话状态
    """
    # 获取会话令牌
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]

    if not session_token:
        session_token = request.cookies.get("session_token")

    if not session_token:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "authenticated": False,
                    "message": "未登录"
                }
            }
        )

    # 验证会话
    session = session_manager.validate_session(session_token)
    if not session:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "authenticated": False,
                    "message": "会话已过期"
                }
            }
        )

    # 检查超时警告
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

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": response_data
        }
    )


# 文件相关API端点

# API端点：上传文件
@app.post("/api/files/upload")
async def upload_file(request: Request):
    """
    文件上传API端点
    """
    # 检查用户登录状态
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        # 获取表单数据
        form = await request.form()
        file = form.get("file")
        description = form.get("description", "")
        tags = form.get("tags", "")
        is_public = form.get("is_public", "false").lower() == "true"

        if not file:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "请选择要上传的文件",
                    "error": "NO_FILE"
                }
            )

        # 检查文件大小
        file_data = await file.read()
        if len(file_data) > FileService.MAX_FILE_SIZE:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"文件大小超过限制（最大 {FileService.MAX_FILE_SIZE // (1024*1024)} MB）",
                    "error": "FILE_TOO_LARGE"
                }
            )

        # 检查文件类型
        if not FileService.is_allowed_file(file.filename):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "不支持的文件类型",
                    "error": "UNSUPPORTED_FILE_TYPE"
                }
            )

        # 上传文件
        uploaded_file, error_message = FileService.upload_file(
            file_data=file_data,
            original_filename=file.filename,
            uploader_id=current_user.id,
            description=description if description else None,
            tags=tags if tags else None,
            is_public=is_public
        )

        if uploaded_file:
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "success": True,
                    "message": "文件上传成功",
                    "data": uploaded_file.to_dict()
                }
            )
        else:
            # 根据错误类型返回不同的状态码和消息
            if "已存在" in error_message:
                status_code = status.HTTP_409_CONFLICT  # Conflict
            elif "超过限制" in error_message:
                status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            elif "不支持" in error_message:
                status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "message": error_message or "文件上传失败",
                    "error": "UPLOAD_FAILED"
                }
            )

    except Exception as e:
        logger.error(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "文件上传过程中发生错误",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：获取文件列表
@app.get("/api/files")
async def get_files(request: Request):
    """
    获取文件列表API端点
    """
    # 检查用户登录状态
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        # 获取查询参数
        user_id = request.query_params.get("user_id")
        scope = request.query_params.get("scope", "my")  # my, public, all
        limit = int(request.query_params.get("limit", 5))  # 默认每页5条
        offset = int(request.query_params.get("offset", 0))
        page = int(request.query_params.get("page", 1))  # 页码，从1开始
        keyword = request.query_params.get("keyword", "")

        # 验证参数
        if limit not in [5, 10, 20, 100]:
            limit = 5  # 默认每页5条

        # 计算偏移量
        if page > 1:
            offset = (page - 1) * limit
        else:
            offset = 0

        files = []
        total = 0  # 总记录数

        if scope == "my":
            # 获取用户的文件
            files = FileService.get_files_by_user(current_user.id, limit, offset)
            total = FileService.get_files_count_by_user(current_user.id)
        elif scope == "public":
            # 获取公开文件
            files = FileService.get_public_files(limit, offset)
            total = FileService.get_public_files_count()
        elif scope == "all" and current_user.role == "admin":
            # 管理员获取所有文件
            if user_id:
                files = FileService.get_files_by_user(int(user_id), limit, offset)
                total = FileService.get_files_count_by_user(int(user_id))
            else:
                files = FileService.get_files_by_user(current_user.id, limit, offset)
                files.extend(FileService.get_public_files(limit, offset))
                total = FileService.get_files_count_by_user(current_user.id) + FileService.get_public_files_count()

        # 如果有搜索关键词，进行搜索
        if keyword:
            if scope == "my":
                files = FileService.search_files(keyword, current_user.id, limit, offset)
                total = FileService.get_search_files_count(keyword, current_user.id)
            elif scope == "public":
                files = FileService.search_files(keyword, None, limit, offset)
                total = FileService.get_search_files_count(keyword, None)
            elif scope == "all" and current_user.role == "admin":
                files = FileService.search_files(keyword, int(user_id) if user_id else None, limit, offset)
                total = FileService.get_search_files_count(keyword, int(user_id) if user_id else None)
        try:
            # 计算分页信息
            total_pages = (total + limit - 1) // limit if total > 0 else 1
            has_next = page < total_pages
            has_prev = page > 1

            reponse_content = {
                "success": True,
                "data": {
                    "files": [file.to_dict() for file in files],
                    "total_files_count": total,
                    "pagination": {
                        "current_page": page,
                        "per_page": limit,
                        "total": total,
                        "total_pages": total_pages,
                        "has_next": has_next,
                        "has_prev": has_prev,
                        "next_page": page + 1 if has_next else None,
                        "prev_page": page - 1 if has_prev else None
                    }
                }
            }
            for file in files:
                logger.info(file.filename)
        except Exception as e:
            logger.error(e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "message": "获取文件列表失败",
                    "error": "INTERNAL_ERROR"
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=reponse_content
        )

    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "参数错误",
                "error": "INVALID_PARAMETERS"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取文件列表失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：获取文件详情
@app.get("/api/files/{file_id}")
async def get_file_details(file_id: int, request: Request):
    """
    获取文件详情API端点
    """
    # 检查用户登录状态
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        file_obj = FileService.get_file_by_id(file_id)
        if not file_obj:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "文件不存在",
                    "error": "FILE_NOT_FOUND"
                }
            )

        # 检查访问权限
        if not file_obj.is_accessible_by_user(current_user.id, current_user.role):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "message": "没有权限访问此文件",
                    "error": "ACCESS_DENIED"
                }
            )

        # 更新访问时间
        FileService.increment_download_count(file_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": file_obj.to_dict()
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取文件详情失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：删除文件
@app.delete("/api/files/{file_id}")
async def delete_file(file_id: int, request: Request):
    """
    删除文件API端点
    """
    # 检查用户登录状态
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        success = FileService.delete_file(file_id, current_user.id, current_user.role)
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "文件删除成功"
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "文件删除失败，可能没有权限或文件不存在",
                    "error": "DELETE_FAILED"
                }
            )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "删除文件失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：更新文件信息
@app.put("/api/files/{file_id}")
async def update_file_info(file_id: int, request: Request):
    """
    更新文件信息API端点
    """
    # 检查用户登录状态
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        data = await request.json()
        description = data.get("description")
        tags = data.get("tags")
        is_public = data.get("is_public")

        success = FileService.update_file_info(
            file_id, current_user.id, current_user.role,
            description, tags, is_public
        )

        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "文件信息更新成功"
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "文件信息更新失败，可能没有权限或文件不存在",
                    "error": "UPDATE_FAILED"
                }
            )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "更新文件信息失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：获取文件统计信息
@app.get("/api/files/stats")
async def get_file_stats(request: Request):
    """
    获取文件统计信息API端点
    """
    # 检查用户登录状态
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        # 获取查询参数
        user_id = request.query_params.get("user_id")
        scope = request.query_params.get("scope", "my")  # my, all

        # 确定统计范围
        target_user_id = None
        if scope == "my":
            target_user_id = current_user.id
        elif scope == "all" and current_user.role == "admin":
            target_user_id = int(user_id) if user_id else None

        stats = FileService.get_file_stats(target_user_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": stats
            }
        )

    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "参数错误",
                "error": "INVALID_PARAMETERS"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取文件统计信息失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：下载文件
@app.get("/api/files/{file_id}/download")
async def download_file(file_id: int, request: Request):
    """
    文件下载API端点
    """
    # 检查用户登录状态
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        file_obj = FileService.get_file_by_id(file_id)
        if not file_obj:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "文件不存在",
                    "error": "FILE_NOT_FOUND"
                }
            )

        # 检查访问权限
        if not file_obj.is_accessible_by_user(current_user.id, current_user.role):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "message": "没有权限访问此文件",
                    "error": "ACCESS_DENIED"
                }
            )

        # 检查文件是否存在
        import os
        if not os.path.exists(file_obj.file_path):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "文件已丢失",
                    "error": "FILE_LOST"
                }
            )

        # 增加下载次数
        FileService.increment_download_count(file_id)

        # 返回文件
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_obj.file_path,
            filename=file_obj.filename,
            media_type=file_obj.file_type
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "文件下载失败",
                "error": "INTERNAL_ERROR"
            }
        )



# API端点：直接文件预览 - 用于PDF等文件的浏览器内预览
@app.get("/api/files/{file_id}/view")
async def view_file(file_id: int, request: Request):
    """
    直接文件预览API端点
    类似于Flask的send_file功能，直接返回文件内容供浏览器预览
    特别适用于PDF文件的浏览器内预览
    """
    # 检查用户登录状态
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "请先登录",
                "error": "NOT_AUTHENTICATED"
            }
        )

    try:
        file_obj = FileService.get_file_by_id(file_id)
        if not file_obj:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "文件不存在",
                    "error": "FILE_NOT_FOUND"
                }
            )

        # 检查访问权限
        if not file_obj.is_accessible_by_user(current_user.id, current_user.role):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "message": "没有权限访问此文件",
                    "error": "ACCESS_DENIED"
                }
            )

        # 检查文件是否存在
        import os
        if not os.path.exists(file_obj.file_path):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "文件已丢失",
                    "error": "FILE_LOST"
                }
            )

        # 增加访问次数
        FileService.increment_download_count(file_id)

        # 使用FastAPI的FileResponse返回文件
        # 类似于Flask的send_file(as_attachment=False)
        from fastapi.responses import FileResponse

        # 根据文件类型设置合适的MIME类型
        media_type = file_obj.file_type
        if file_obj.file_type == 'application/pdf':
            media_type = 'application/pdf'  # 确保PDF使用正确的MIME类型
        elif file_obj.file_type.startswith('image/'):
            media_type = file_obj.file_type
        elif file_obj.file_type.startswith('text/'):
            media_type = 'text/plain'
        elif file_obj.file_type.startswith('video/'):
            media_type = file_obj.file_type
        elif file_obj.file_type.startswith('audio/'):
            media_type = file_obj.file_type

        return FileResponse(
            path=file_obj.file_path,
            filename=file_obj.filename,
            media_type=media_type,
            # 不设置as_attachment=True，这样浏览器会尝试直接显示而不是下载
            headers={
                "Content-Disposition": f"inline; filename=\"{file_obj.filename}\""
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "文件预览失败",
                "error": "INTERNAL_ERROR"
            }
        )


# 启动时清理过期会话
@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行的任务
    """
    print("执行启动任务...")

    # 清理过期会话
    cleaned_count = session_manager.cleanup_expired_sessions()
    if cleaned_count > 0:
        print(f"启动时清理了 {cleaned_count} 个过期会话")

    print("启动任务完成")


# API端点：清空所有会话（开发调试用）
@app.delete("/api/admin/clear-sessions")
async def clear_all_sessions():
    """
    清空所有会话（仅用于开发调试）
    """
    # 检查是否为开发环境
    if os.getenv("DEBUG", "false").lower() == "true":
        cleared_count = session_manager.clear_all_sessions()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"已清空所有会话",
                "cleared_count": cleared_count
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "此功能仅在开发环境可用",
                "error": "FORBIDDEN"
            }
        )


# 启动命令
if __name__ == "__main__":
    import uvicorn

    print("启动基础用户认证系统...")
    print(f"服务信息:")
    print(f"   - 服务地址: http://localhost:8081")
    print(f"   - API文档: http://localhost:8081/docs")
    print(f"   - 数据库: {DATABASE_PATH}")
    print(f"   - Session存储: {'文件持久化' if session_manager.use_file_storage else '内存（重启清空）'}")
    print()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )