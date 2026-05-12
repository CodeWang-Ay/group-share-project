"""
FastAPI应用主入口
提供用户认证系统的API服务
"""
import bcrypt
from fastapi import FastAPI, Request, Depends, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pathlib import Path
import sqlite3
import os
from datetime import datetime
from typing import Optional

# 导入内部模块
from models.user import User
from models.file import File
from models.meeting import Meeting, MeetingPresenter, MeetingFile
from models.task import Task
from models.paper import Paper, Tag, PaperUserRelation
from models.research_progress import ResearchProgress, ProgressSetting
from database.connection import get_db, DATABASE_PATH
from services.auth import AuthService
from services.session import session_manager
from services.file_service import FileService
from services.meeting_service import MeetingService
from services.task_service import TaskService
from services.paper_service import PaperService
from services.research_progress_service import ResearchProgressService, ProgressSettingService
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
    allow_origins=["http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:8000", "http://127.0.0.1:8000"],
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
    logger.info(f"当前用户session_token: {session_token}")
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
                "SELECT id, username, password_hash, role, email, phone, student_id, research_direction, status, avatar, created_at, updated_at "
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
@app.get("/rm_share_file", response_class=HTMLResponse)
async def rm_share_file_page(request: Request):
    """
    共享文件页面路由
    需要用户登录才能访问
    """
    # 检查用户是否已登录
    logger.info("用户进入共享登录页面中")
    current_user = await get_current_user(request)
    if not current_user:
        # 未登录，重定向到登录页面
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # 已登录，显示共享文件页面
    return templates.TemplateResponse("rm_share_file.html", {
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
        email = data.get("email")
        gender = data.get("gender")  # 获取性别
        phone = data.get("phone")  # 获取手机号码
        degree_type = data.get("degree_type")  # 获取学位类型

        print(f"接收到注册数据: username={username}, password={'***' if password else 'None'}, role={role}, email={email}, gender={gender}, phone={phone}, degree_type={degree_type}")

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
            new_user = User.create_user(username, password, role, email)

            cursor.execute(
                "INSERT INTO users (username, password_hash, role, email, gender, phone, degree_type, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_user.username,
                    new_user.password_hash,
                    new_user.role,
                    email,
                    gender,
                    phone,
                    degree_type,
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


# API端点：修改密码
@app.put("/api/auth/change-password")
async def change_password(request: Request):
    """
    修改用户密码API端点
    """
    # 检查用户登录状态
    logger.info("修改密码页面....")
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
        # 获取请求数据
        data = await request.json()
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        # 验证输入
        if not old_password or not new_password or not confirm_password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "请填写完整的密码信息",
                    "error": "VALIDATION_ERROR"
                }
            )

        # 验证新密码长度
        if len(new_password) < 6:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "新密码长度至少为6位",
                    "error": "PASSWORD_TOO_SHORT"
                }
            )

        # 验证新密码与确认密码是否一致
        if new_password != confirm_password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "新密码与确认密码不一致",
                    "error": "PASSWORD_MISMATCH"
                }
            )

        # 验证新密码不能与旧密码相同
        if old_password == new_password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "新密码不能与当前密码相同",
                    "error": "SAME_PASSWORD"
                }
            )

        # 验证旧密码是否正确
        if not AuthService.authenticate_user(current_user.username, old_password):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "当前密码不正确",
                    "error": "INVALID_OLD_PASSWORD"
                }
            )

        # 生成新密码的哈希值
        # new_password_hash = User.hash_password(new_password)
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # 更新数据库中的密码
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (password_hash.decode('utf-8'), current_user.id)
            )

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "用户不存在",
                        "error": "USER_NOT_FOUND"
                    }
                )

        print(f"密码修改成功: user={current_user.username}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "密码修改成功，请使用新密码登录"
            }
        )

    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "修改密码过程中发生错误",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：获取用户详细个人资料
@app.get("/api/user/profile")
async def get_user_profile(request: Request):
    """
    获取用户详细个人资料信息
    包含用户表中的所有字段
    """
    # 检查用户登录状态
    logger.info("用户详细个人资料页面")
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
        with get_db() as conn:
            cursor = conn.cursor()

            # 查询用户的所有字段信息
            cursor.execute("""
                SELECT id, username, role, created_at, updated_at, email, phone,
                       student_id, research_direction, status, graduation_status,
                       supervisor, degree_type, work_location, work_company,
                       personal_bio, personal_homepage, gender, id_card, bank_card, avatar
                FROM users
                WHERE id = ?
            """, (current_user.id,))

            user_data = cursor.fetchone()

            if not user_data:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "用户信息不存在",
                        "error": "USER_NOT_FOUND"
                    }
                )

            # 将查询结果转换为字典
            columns = [description[0] for description in cursor.description]
            user_profile = dict(zip(columns, user_data))

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "data": user_profile
                }
            )

    except Exception as e:
        logger.error(f"获取用户个人资料失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取用户个人资料失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：更新用户个人资料
@app.put("/api/user/profile")
async def update_user_profile(request: Request):
    """
    更新用户个人资料信息
    """
    # 检查用户登录状态
    logger.info("更新用户个人资料")
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
        # 获取更新数据
        data = await request.json()

        # 允许更新的字段
        allowed_fields = [
            'email', 'phone', 'student_id', 'research_direction',
            'graduation_status', 'supervisor', 'degree_type',
            'work_location', 'work_company', 'personal_bio',
            'personal_homepage', 'gender', 'id_card', 'bank_card'
        ]

        # 过滤出允许更新的字段
        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

        if not update_data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "没有提供要更新的数据",
                    "error": "NO_DATA"
                }
            )

        with get_db() as conn:
            cursor = conn.cursor()

            # 构建更新语句
            set_clause = ", ".join([f"{field} = ?" for field in update_data.keys()])
            values = list(update_data.values()) + [current_user.id]

            # 更新数据
            cursor.execute(f"""
                UPDATE users
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "用户不存在",
                        "error": "USER_NOT_FOUND"
                    }
                )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "个人资料更新成功",
                    "data": update_data
                }
            )

    except Exception as e:
        logger.error(f"更新用户个人资料失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "更新个人资料失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：上传头像
@app.post("/api/user/avatar")
async def upload_avatar(request: Request):
    """
    上传用户头像
    """
    logger.info("上传用户头像")
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
        file = form.get("avatar")

        if not file:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "请选择要上传的头像图片",
                    "error": "NO_FILE"
                }
            )

        # 检查文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "只支持 JPG、PNG、GIF、WEBP 格式的图片",
                    "error": "UNSUPPORTED_FILE_TYPE"
                }
            )

        # 读取文件数据
        file_data = await file.read()

        # 检查文件大小（最大5MB）
        if len(file_data) > 5 * 1024 * 1024:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "头像图片大小不能超过5MB",
                    "error": "FILE_TOO_LARGE"
                }
            )

        # 生成文件名
        from pathlib import Path
        import time
        timestamp = int(time.time())
        file_ext = Path(file.filename).suffix.lower() or '.jpg'
        avatar_filename = f"avatar_{current_user.id}_{timestamp}{file_ext}"

        # 创建头像存储目录
        avatars_dir = Path(__file__).parent.parent / "uploads" / "avatars"
        avatars_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        avatar_path = avatars_dir / avatar_filename
        with open(avatar_path, 'wb') as f:
            f.write(file_data)

        # 生成头像URL
        avatar_url = f"/uploads/avatars/{avatar_filename}"

        # 更新数据库
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET avatar = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (avatar_url, current_user.id))

        logger.info(f"用户 {current_user.username} 上传头像成功: {avatar_url}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "头像上传成功",
                "data": {
                    "avatar_url": avatar_url
                }
            }
        )

    except Exception as e:
        logger.error(f"上传头像失败: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"上传头像失败: {str(e)}",
                "error": "INTERNAL_ERROR"
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
    logger.info(f"上传文件 {request}")
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
        logger.error(f"文件上传错误: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"文件上传过程中发生错误: {str(e)}",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：下载文件（根据文件名）
@app.get("/api/files/download/{filename}")
async def download_file_by_name(filename: str, request: Request):
    """
    根据文件名下载文件API端点
    用于研究进展附件下载
    """
    import urllib.parse
    # URL解码文件名
    decoded_filename = urllib.parse.unquote(filename)

    logger.info(f"下载文件请求: {decoded_filename}")

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
        # 在数据库中查找文件
        from database.connection import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_path, file_type, uploader_id
                FROM files
                WHERE filename = ? AND status = 'active'
            """, (decoded_filename,))
            file_row = cursor.fetchone()

            if not file_row:
                logger.error(f"文件不存在: {decoded_filename}")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "文件不存在",
                        "error": "FILE_NOT_FOUND"
                    }
                )

            file_id, stored_filename, file_path, file_type, uploader_id = file_row

        # 检查文件是否存在
        import os
        from pathlib import Path
        if not os.path.exists(file_path):
            logger.error(f"物理文件不存在: {file_path}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "文件不存在",
                    "error": "FILE_NOT_FOUND"
                }
            )

        # 返回文件
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=stored_filename,
            media_type=file_type or 'application/octet-stream'
        )

    except Exception as e:
        logger.error(f"文件下载错误: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"文件下载失败: {str(e)}",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：获取文件列表
@app.get("/api/files")
async def get_files(request: Request):
    """
    获取文件列表API端点
    """

    logger.info("加载用户文件列表")
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

# 成员管理页面路由
@app.get("/tm_user_management", response_class=HTMLResponse)
async def member_management_page(request: Request):
    """
    成员管理页面路由
    需要用户登录才能访问
    """
    logger.info("成员管理页面路由")
    # 检查用户是否已登录
    current_user = await get_current_user(request)
    if not current_user:
        # 未登录，重定向到登录页面
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # 已登录，显示成员管理页面
    return templates.TemplateResponse("tm_user_management.html", {
        "request": request,
        "user": current_user
    })


# API端点：获取成员列表
@app.get("/api/members")
async def get_members(request: Request):
    """
    获取成员列表API端点
    """
    logger.info("获取成员列表")
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
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 10))
        role_filter = request.query_params.get("role", "")
        status_filter = request.query_params.get("status", "")
        search = request.query_params.get("search", "")

        # 验证参数
        if per_page not in [5, 10, 20, 50]:
            per_page = 10

        if page < 1:
            page = 1

        # 计算偏移量
        offset = (page - 1) * per_page

        # 查询成员数据
        with get_db() as conn:
            cursor = conn.cursor()

            # 构建查询条件
            where_conditions = []
            params = []

            if role_filter:
                where_conditions.append("role = ?")
                params.append(role_filter)

            if status_filter:
                where_conditions.append("status = ?")
                params.append(status_filter)

            if search:
                where_conditions.append("(username LIKE ? OR id LIKE ? OR student_id LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # 获取总记录数
            count_query = f"SELECT COUNT(*) FROM users {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # 获取成员信息列表
            query = f"""
                SELECT id, username, role, created_at, updated_at, email, phone,
                       student_id, research_direction, status, graduation_status,
                       supervisor, degree_type, work_location, work_company,
                       personal_bio, personal_homepage, gender, id_card, bank_card, avatar
                FROM users
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [per_page, offset])
            rows = cursor.fetchall()

            # 转换为字典格式
            members = []
            for row in rows:
                member = dict(row)
                # 为前端添加必要的字段
                member['student_id'] = member.get('student_id', str(member['id']))  # 使用student_id或id作为学号
                member['username'] = member['username']  # 使用username作为姓名
                member['email'] = member.get('email', f"{member['username']}@example.com")  # 使用真实邮箱或生成示例邮箱
                member['phone'] = member.get('phone', '13800138000')  # 使用真实手机号或示例手机号
                member['status'] = member.get('status', 'active')  # 使用真实状态
                member['research_direction'] = member.get('research_direction', '未设置研究方向')  # 使用真实研究方向
                # 使用真实头像，如果没有则生成默认头像
                if member.get('avatar'):
                    member['avatar'] = member['avatar']
                else:
                    member['avatar'] = f"https://picsum.photos/seed/{member['username']}/100/100.jpg"
                member['created_at'] = member['created_at'].split(' ')[0]  # 只取日期部分
                members.append(member)

            # 计算分页信息
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1
            has_next = page < total_pages
            has_prev = page > 1

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "data": {
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
                }
            )

    except Exception as e:
        logger.error(f"获取成员列表失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取成员列表失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：获取成员统计信息
@app.get("/api/members/stats")
async def get_members_stats(request: Request):
    """
    获取成员统计信息API端点
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
        with get_db() as conn:
            cursor = conn.cursor()

            # 获取总成员数
            cursor.execute("SELECT COUNT(*) FROM users")
            total_members = cursor.fetchone()[0]

            # 获取激活成员数
            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
            active_members = cursor.fetchone()[0]

            # 获取学生数量
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
            student_count = cursor.fetchone()[0]

            # 获取导师数量
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
            teacher_count = cursor.fetchone()[0]

            # 获取管理员数量
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]

            stats = {
                "total_members": total_members,
                "active_members": active_members,
                "student_count": student_count,
                "teacher_count": teacher_count,
                "admin_count": admin_count,
                "inactive_members": total_members - active_members
            }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": stats
            }
        )

    except Exception as e:
        logger.error(f"获取成员统计失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取成员统计失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：更新成员状态
@app.put("/api/members/{member_id}/status")
async def update_member_status(member_id: int, request: Request):
    """
    更新成员状态API端点
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

    # 只有管理员可以更新成员状态
    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "没有权限修改成员状态",
                "error": "ACCESS_DENIED"
            }
        )

    try:
        data = await request.json()
        new_status = data.get("status")

        if new_status not in ["active", "inactive"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "状态值无效",
                    "error": "INVALID_STATUS"
                }
            )

        with get_db() as conn:
            cursor = conn.cursor()

            # 更新成员状态
            cursor.execute(
                "UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_status, member_id)
            )

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "成员不存在",
                        "error": "MEMBER_NOT_FOUND"
                    }
                )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "成员状态更新成功"
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "更新成员状态失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：更新成员信息
@app.put("/api/members/{member_id}")
async def update_member_info(member_id: int, request: Request):
    """
    更新成员信息API端点
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
    # 只有管理员可以添加成员
    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "没有权限更新成员信息",
                "error": "ACCESS_DENIED"
            }
        )
    try:
        # 获取更新数据
        data = await request.json()

        # 允许更新的字段
        allowed_fields = [
            'username', 'email', 'phone', 'student_id', 'role',
            'research_direction', 'personal_bio', 'gender',
            'id_card', 'bank_card', 'status', 'degree_type'
        ]

        # 过滤出允许更新的字段
        update_data = {}
        for field in allowed_fields:
            if field in data and data[field] is not None:
                update_data[field] = data[field]

        if not update_data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "没有提供要更新的数据",
                    "error": "NO_DATA"
                }
            )

        # 验证角色
        if 'role' in update_data and update_data['role'] not in ['admin', 'teacher', 'student']:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "角色值无效",
                    "error": "INVALID_ROLE"
                }
            )

        # 验证状态
        if 'status' in update_data and update_data['status'] not in ['active', 'inactive']:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "状态值无效",
                    "error": "INVALID_STATUS"
                }
            )

        # 验证身份证号格式
        if 'id_card' in update_data and update_data['id_card']:
            id_card = update_data['id_card']
            if len(id_card) != 18:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": "身份证号必须为18位",
                        "error": "INVALID_ID_CARD"
                    }
                )

        with get_db() as conn:
            cursor = conn.cursor()

            # 检查成员是否存在
            cursor.execute("SELECT id FROM users WHERE id = ?", (member_id,))
            if not cursor.fetchone():
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "成员不存在",
                        "error": "MEMBER_NOT_FOUND"
                    }
                )

            # 如果更新用户名，检查是否重复
            if 'username' in update_data:
                cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?",
                              (update_data['username'], member_id))
                if cursor.fetchone():
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "success": False,
                            "message": "用户名已存在",
                            "error": "USERNAME_EXISTS"
                        }
                    )

            # 构建更新语句
            set_clause = ", ".join([f"{field} = ?" for field in update_data.keys()])
            values = list(update_data.values()) + [member_id]

            # 更新数据
            cursor.execute(f"""
                UPDATE users
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "成员不存在或更新失败",
                        "error": "UPDATE_FAILED"
                    }
                )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "成员信息更新成功",
                    "data": update_data
                }
            )

    except Exception as e:
        logger.error(f"更新成员信息失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "更新成员信息失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：添加成员
@app.post("/api/members")
async def create_member(request: Request):
    """
    添加成员API端点（管理员专用）
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

    # 只有管理员可以添加成员
    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "没有权限添加成员",
                "error": "ACCESS_DENIED"
            }
        )

    try:
        # 获取请求数据
        data = await request.json()

        # 必填字段验证
        required_fields = ['username', 'password', 'email', 'role']
        for field in required_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": f"请填写{getFieldLabel(field)}",
                        "error": "MISSING_FIELD"
                    }
                )

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        student_id = data.get('student_id', '').strip()
        role = data.get('role', '').strip()

        # 验证角色
        if role not in ['admin', 'teacher', 'student']:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "角色值无效",
                    "error": "INVALID_ROLE"
                }
            )

        # 验证用户名格式
        if not User.is_valid_username(username):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "用户名格式不正确：3-50个字符，只允许字母、数字、下划线",
                    "error": "INVALID_USERNAME"
                }
            )

        # 验证密码长度
        if len(password) < 6:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "密码长度至少为6位",
                    "error": "PASSWORD_TOO_SHORT"
                }
            )

        # 验证邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "邮箱格式不正确",
                    "error": "INVALID_EMAIL"
                }
            )

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

            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": "邮箱已存在",
                        "error": "EMAIL_EXISTS"
                    }
                )

            # 检查学号是否已存在（如果提供了学号）
            if student_id:
                cursor.execute("SELECT id FROM users WHERE student_id = ?", (student_id,))
                if cursor.fetchone():
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "success": False,
                            "message": "学号/工号已存在",
                            "error": "STUDENT_ID_EXISTS"
                        }
                    )

            # 创建新用户
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # 插入新用户数据
            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, email, phone, student_id, role,
                    research_direction, personal_bio, gender, id_card, bank_card,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                username,
                password_hash.decode('utf-8'),
                email,
                phone if phone else None,
                student_id if student_id else None,
                role,
                data.get('research_direction'),
                data.get('personal_bio'),
                data.get('gender'),
                data.get('id_card'),
                data.get('bank_card')
            ))

            # 获取新创建的用户ID
            cursor.execute("SELECT last_insert_rowid()")
            new_user_id = cursor.fetchone()[0]

            logger.info(f"管理员 {current_user.username} 创建了新用户: {username} (ID: {new_user_id})")

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "success": True,
                    "message": "成员添加成功",
                    "data": {
                        "id": new_user_id,
                        "username": username,
                        "email": email,
                        "role": role,
                        "student_id": student_id
                    }
                }
            )

    except Exception as e:
        logger.error(f"添加成员失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "添加成员失败",
                "error": "INTERNAL_ERROR"
            }
        )

# 辅助函数：获取字段标签
def getFieldLabel(field):
    labels = {
        'username': '用户名',
        'password': '密码',
        'email': '邮箱',
        'phone': '手机号',
        'student_id': '学号/工号',
        'role': '角色'
    }
    return labels.get(field, field)


# API端点：删除成员
@app.delete("/api/members/{member_id}")
async def delete_member(member_id: int, request: Request):
    """
    删除成员API端点
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
        # 只有管理员可以删除成员
        if current_user.role != "admin":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "message": "没有权限删除成员",
                    "error": "ACCESS_DENIED"
                }
            )

        with get_db() as conn:
            cursor = conn.cursor()

            # 删除成员
            cursor.execute("DELETE FROM users WHERE id = ?", (member_id,))

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "成员不存在",
                        "error": "MEMBER_NOT_FOUND"
                    }
                )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "成员删除成功"
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "删除成员失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：批量修改成员角色
@app.post("/api/users/batch-update-role")
async def batch_update_user_role(request: Request):
    """
    批量修改成员角色API端点
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

    # 只有管理员可以批量修改角色
    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "没有权限批量修改成员角色",
                "error": "ACCESS_DENIED"
            }
        )

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])
        role = data.get("role")

        if not user_ids or not role:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "缺少必要参数",
                    "error": "MISSING_PARAMS"
                }
            )

        if role not in ["admin", "teacher", "student"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "角色必须是admin、teacher或student",
                    "error": "INVALID_ROLE"
                }
            )

        with get_db() as conn:
            cursor = conn.cursor()
            updated_count = 0
            for user_id in user_ids:
                cursor.execute(
                    "UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
                    (role, datetime.now().isoformat(), user_id)
                )
                if cursor.rowcount > 0:
                    updated_count += 1

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"成功更新 {updated_count} 个成员的角色",
                "updated_count": updated_count
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "批量修改角色失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：批量修改成员状态
@app.post("/api/users/batch-update-status")
async def batch_update_user_status(request: Request):
    """
    批量修改成员状态API端点
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

    # 只有管理员可以批量修改状态
    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "没有权限批量修改成员状态",
                "error": "ACCESS_DENIED"
            }
        )

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])
        status_value = data.get("status")

        if not user_ids or not status_value:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "缺少必要参数",
                    "error": "MISSING_PARAMS"
                }
            )

        if status_value not in ["active", "inactive"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "状态必须是active或inactive",
                    "error": "INVALID_STATUS"
                }
            )

        with get_db() as conn:
            cursor = conn.cursor()
            updated_count = 0
            for user_id in user_ids:
                cursor.execute(
                    "UPDATE users SET status = ?, updated_at = ? WHERE id = ?",
                    (status_value, datetime.now().isoformat(), user_id)
                )
                if cursor.rowcount > 0:
                    updated_count += 1

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"成功更新 {updated_count} 个成员的状态",
                "updated_count": updated_count
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "批量修改状态失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：批量删除成员
@app.post("/api/users/batch-delete")
async def batch_delete_users(request: Request):
    """
    批量删除成员API端点
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

    # 只有管理员可以批量删除成员
    if current_user.role != "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "没有权限批量删除成员",
                "error": "ACCESS_DENIED"
            }
        )

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])

        if not user_ids:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "缺少要删除的成员ID",
                    "error": "MISSING_USER_IDS"
                }
            )

        with get_db() as conn:
            cursor = conn.cursor()
            deleted_count = 0
            for user_id in user_ids:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                if cursor.rowcount > 0:
                    deleted_count += 1

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"成功删除 {deleted_count} 个成员",
                "deleted_count": deleted_count
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "批量删除失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：留言
@app.post("/api/messages/send")
async def send_message(request: Request):
    """
    留言API端点
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
        receiver_id = data.get("receiver_id")
        title = data.get("title")
        content = data.get("content")

        if not receiver_id or not title or not content:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "缺少必要参数",
                    "error": "MISSING_PARAMS"
                }
            )

        # 检查接收者是否存在
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users WHERE id = ? AND status = 'active'", (receiver_id,))
            receiver = cursor.fetchone()

            if not receiver:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "接收者不存在或已被禁用",
                        "error": "RECEIVER_NOT_FOUND"
                    }
                )

            # 不能给自己留言
            if receiver_id == current_user.id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": "不能给自己留言",
                        "error": "SELF_MESSAGE_NOT_ALLOWED"
                    }
                )

            # 插入留言
            cursor.execute(
                "INSERT INTO messages (sender_id, receiver_id, title, content) VALUES (?, ?, ?, ?)",
                (current_user.id, receiver_id, title, content)
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "留言成功"
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "发送消息失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：获取消息列表
@app.get("/api/messages")
async def get_messages(request: Request):
    """
    获取用户消息列表API端点
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
        with get_db() as conn:
            cursor = conn.cursor()

            # 获取用户收到的消息
            cursor.execute("""
                SELECT m.id, m.title, m.content, m.is_read, m.created_at,
                       u.id as sender_id, u.username as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.receiver_id = ?
                ORDER BY m.created_at DESC
            """, (current_user.id,))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "is_read": row["is_read"],
                    "created_at": row["created_at"],
                    "sender": {
                        "id": row["sender_id"],
                        "username": row["sender_name"]
                    }
                })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "messages": messages
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取留言失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：标记留言已读
@app.put("/api/messages/{message_id}/read")
async def mark_message_read(message_id: int, request: Request):
    """
    标记留言已读API端点
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
        with get_db() as conn:
            cursor = conn.cursor()

            # 检查留言是否存在且属于当前用户
            cursor.execute(
                "SELECT id FROM messages WHERE id = ? AND receiver_id = ?",
                (message_id, current_user.id)
            )
            message = cursor.fetchone()

            if not message:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "留言不存在",
                        "error": "MESSAGE_NOT_FOUND"
                    }
                )

            # 标记为已读
            cursor.execute(
                "UPDATE messages SET is_read = 1, read_at = ? WHERE id = ?",
                (datetime.now().isoformat(), message_id)
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "已标记为已读"
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "操作失败",
                "error": "INTERNAL_ERROR"
            }
        )


# API端点：重置成员密码
@app.put("/api/members/{member_id}/reset-password")
async def reset_member_password(member_id: int, request: Request):
    """
    重置成员密码API端点（管理员专用）
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
        # 只有管理员可以重置密码
        if current_user.role != "admin":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "message": "没有权限重置密码",
                    "error": "ACCESS_DENIED"
                }
            )

        # 获取请求数据
        data = await request.json()
        new_password = data.get("password", "123456")  # 默认密码为123456

        # 验证密码长度
        if len(new_password) < 6:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "密码长度至少为6位",
                    "error": "PASSWORD_TOO_SHORT"
                }
            )

        with get_db() as conn:
            cursor = conn.cursor()

            # 检查成员是否存在
            cursor.execute("SELECT username FROM users WHERE id = ?", (member_id,))
            member_data = cursor.fetchone()
            if not member_data:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "success": False,
                        "message": "成员不存在",
                        "error": "MEMBER_NOT_FOUND"
                    }
                )

            member_username = member_data[0]

            # 生成新密码的哈希值
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            # 更新密码
            cursor.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (password_hash.decode('utf-8'), member_id)
            )

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "message": "密码重置失败",
                        "error": "UPDATE_FAILED"
                    }
                )

            # 记录操作日志
            logger.info(f"管理员 {current_user.username} 重置了用户 {member_username} (ID: {member_id}) 的密码")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "密码重置成功",
                    "data": {
                        "new_password": new_password,
                        "member_id": member_id,
                        "member_username": member_username
                    }
                }
            )

    except Exception as e:
        logger.error(f"重置密码失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "重置密码失败",
                "error": "INTERNAL_ERROR"
            }
        )


# 共享文件页面路由
@app.get("/tm_academic_website", response_class=HTMLResponse)
async def rm_share_file_page(request: Request):
    """
    共享文件页面路由
    需要用户登录才能访问
    """
    # 检查用户是否已登录
    logger.info("用户学术工具页面中")
    current_user = await get_current_user(request)
    if not current_user:
        # 未登录，重定向到登录页面
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # 已登录，显示共享文件页面
    return templates.TemplateResponse("tm_academic_website.html", {
        "request": request,
        "user": current_user
    })

# 研究进展页面
@app.get("/tm_research_progress", response_class=HTMLResponse)
async def tm_research_progress_page(request: Request):
    """
    研究进展页面路由
    需要用户登录才能访问
    """
    logger.info("用户研究进展页面")
    current_user = await get_current_user(request)
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("tm_research_progress.html", {
        "request": request,
        "user": current_user
    })

# 文献库页面
@app.get("/rm_paper_database", response_class=HTMLResponse)
async def rm_paper_database_page(request: Request):
    """
    文献库页面路由
    需要用户登录才能访问
    """
    logger.info("用户文献库页面")
    current_user = await get_current_user(request)
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("rm_paper_database.html", {
        "request": request,
        "user": current_user
    })

# 组会安排页面
@app.get("/gm_meeting_schedule", response_class=HTMLResponse)
async def gm_meeting_schedule_page(request: Request):
    """
    组会安排页面路由
    需要用户登录才能访问
    """
    logger.info("用户组会安排页面")
    current_user = await get_current_user(request)
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("gm_meeting_schedule.html", {
        "request": request,
        "user": current_user
    })

# 汇报材料页面
@app.get("/gm_report_materials", response_class=HTMLResponse)
async def gm_report_materials_page(request: Request):
    """
    汇报材料页面路由
    需要用户登录才能访问
    """
    logger.info("用户汇报材料页面")
    current_user = await get_current_user(request)
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("gm_report_materials.html", {
        "request": request,
        "user": current_user
    })

# 组会记录页面
@app.get("/gm_meeting_record", response_class=HTMLResponse)
async def gm_meeting_record_page(request: Request):
    """
    组会记录页面路由
    需要用户登录才能访问
    """
    logger.info("用户组会记录页面")
    current_user = await get_current_user(request)
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("gm_meeting_record.html", {
        "request": request,
        "user": current_user
    })

# 研究任务页面
@app.get("/rm_research_tasks", response_class=HTMLResponse)
async def rm_research_tasks_page(request: Request):
    """
    研究任务页面路由
    需要用户登录才能访问
    """
    logger.info("用户研究任务页面")
    current_user = await get_current_user(request)
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("rm_research_tasks.html", {
        "request": request,
        "user": current_user
    })

@app.get("/user_profile", response_class=HTMLResponse)
async def user_profile_page(request: Request):
    """
    个人资料页面路由
    需要用户登录才能访问
    """
    # 检查用户是否已登录
    logger.info("用户访问个人资料页面")
    current_user = await get_current_user(request)
    if not current_user:
        # 未登录，重定向到登录页面
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # 已登录，显示个人资料页面
    return templates.TemplateResponse("user_profile.html", {
        "request": request,
        "user": current_user
    })

@app.get("/user_profile", response_class=HTMLResponse)
async def user_profile_page(request: Request):
    """
    个人资料页面路由（别名）
    需要用户登录才能访问
    """
    # 检查用户是否已登录
    logger.info("用户访问个人资料页面（别名路由）")
    current_user = await get_current_user(request)
    if not current_user:
        # 未登录，重定向到登录页面
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # 已登录，显示个人资料页面
    return templates.TemplateResponse("user_profile.html", {
        "request": request,
        "user": current_user
    })

@app.get("/edit_password", response_class=HTMLResponse)
async def rm_share_file_page(request: Request):
    """
    共享文件页面路由
    需要用户登录才能访问
    """
    # 检查用户是否已登录
    logger.info("用户学术工具页面中")
    current_user = await get_current_user(request)
    if not current_user:
        # 未登录，重定向到登录页面
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # 已登录，显示共享文件页面
    return templates.TemplateResponse("edit_password.html", {
        "request": request,
        "user": current_user
    })

@app.get("/settings", response_class=HTMLResponse)
async def rm_share_file_page(request: Request):
    """
    共享文件页面路由
    需要用户登录才能访问
    """
    # 检查用户是否已登录
    logger.info("用户学术工具页面中")
    current_user = await get_current_user(request)
    if not current_user:
        # 未登录，重定向到登录页面
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # 已登录，显示共享文件页面
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": current_user
    })

# ==================== 组会管理API ====================

@app.get("/api/meetings")
async def get_meetings(request: Request):
    """
    获取组会列表API
    支持分页和筛选，同时返回汇报人信息
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取查询参数
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        meeting_status = request.query_params.get("status")
        meeting_type = request.query_params.get("meeting_type")

        offset = (page - 1) * limit

        # 获取组会列表
        meetings = MeetingService.get_meetings(
            status=meeting_status,
            meeting_type=meeting_type,
            limit=limit,
            offset=offset
        )

        # 获取总数
        total = MeetingService.get_meetings_count(
            status=meeting_status,
            meeting_type=meeting_type
        )

        # 为每个组会获取汇报人信息
        conn = get_db()
        cursor = conn.cursor()

        meetings_with_presenters = []
        for m in meetings:
            meeting_dict = m.to_dict()

            # 获取该组会的汇报人
            cursor.execute("""
                SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes, mp.status, mp.material_status,
                       u.username, u.role
                FROM meeting_presenters mp
                LEFT JOIN users u ON mp.user_id = u.id
                WHERE mp.meeting_id = ?
                ORDER BY mp.created_at ASC
            """, (m.id,))

            presenters = []
            for row in cursor.fetchall():
                presenter_id = row[0]

                # 获取该汇报人的文件（从 meeting_files 表直接获取）
                cursor.execute("""
                    SELECT mf.id, mf.filename, mf.file_type, mf.file_size, mf.uploaded_at
                    FROM meeting_files mf
                    WHERE mf.presenter_id = ? AND mf.filename IS NOT NULL
                """, (presenter_id,))

                files = []
                for file_row in cursor.fetchall():
                    files.append({
                        "id": file_row[0],
                        "filename": file_row[1],
                        "file_type": file_row[2],
                        "file_size": file_row[3],
                        "uploaded_at": file_row[4]
                    })

                presenters.append({
                    "id": row[0],
                    "user_id": row[1],
                    "presenter_type": row[2],
                    "duration_minutes": row[3],
                    "status": row[4],
                    "material_status": row[5],
                    "username": row[6],
                    "real_name": row[6],
                    "files": files
                })

            meeting_dict["presenters"] = presenters
            meetings_with_presenters.append(meeting_dict)

        conn.close()

        # 计算分页信息
        total_pages = (total + limit - 1) // limit if total > 0 else 1

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "meetings": meetings_with_presenters,
                    "pagination": {
                        "current_page": page,
                        "per_page": limit,
                        "total": total,
                        "total_pages": total_pages,
                        "has_next": page < total_pages,
                        "has_prev": page > 1
                    }
                }
            }
        )
    except Exception as e:
        logger.error(f"获取组会列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取组会列表失败", "error": "INTERNAL_ERROR"}
        )


@app.post("/api/meetings")
async def create_meeting(request: Request):
    """
    创建组会API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()

        # 验证必填字段
        if not data.get("title"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "组会标题不能为空", "error": "VALIDATION_ERROR"}
            )

        if not data.get("scheduled_at"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "会议时间不能为空", "error": "VALIDATION_ERROR"}
            )

        # 解析时间
        scheduled_at = datetime.fromisoformat(data["scheduled_at"])
        material_deadline = None
        if data.get("material_deadline"):
            material_deadline = datetime.fromisoformat(data["material_deadline"])

        # 创建组会
        meeting = MeetingService.create_meeting(
            title=data["title"],
            meeting_type=data.get("meeting_type", "regular"),
            scheduled_at=scheduled_at,
            created_by=current_user.id,
            description=data.get("description"),
            location=data.get("location"),
            is_online=data.get("is_online", False),
            online_link=data.get("online_link"),
            duration_total=data.get("duration_total", 60),
            material_required=data.get("material_required", True),
            material_deadline=material_deadline,
            notes=data.get("notes"),
            minutes=data.get("minutes")
        )

        logger.info(f"创建组会成功: {meeting.title} (ID: {meeting.id})")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "组会创建成功",
                "data": meeting.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"创建组会失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "创建组会失败", "error": "INTERNAL_ERROR"}
        )


@app.get("/api/meetings/stats")
async def get_meeting_stats(request: Request):
    """
    获取组会统计信息API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        stats = MeetingService.get_meeting_stats()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": stats
            }
        )
    except Exception as e:
        logger.error(f"获取组会统计失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取组会统计失败", "error": "INTERNAL_ERROR"}
        )


@app.get("/api/meetings/{meeting_id}")
async def get_meeting_detail(meeting_id: int, request: Request):
    """
    获取组会详情API，包含汇报人信息
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        meeting = MeetingService.get_meeting_by_id(meeting_id)
        if not meeting:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}
            )

        # 获取汇报人信息
        meeting_dict = meeting.to_dict()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes, mp.status,
                   u.username, u.role
            FROM meeting_presenters mp
            LEFT JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = ?
            ORDER BY mp.created_at ASC
        """, (meeting_id,))

        presenters = []
        for row in cursor.fetchall():
            presenters.append({
                "id": row[0],
                "user_id": row[1],
                "presenter_type": row[2],
                "duration_minutes": row[3],
                "status": row[4],
                "username": row[5],
                "real_name": row[5],
                "user_role": row[6]
            })

        meeting_dict["presenters"] = presenters
        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": meeting_dict
            }
        )
    except Exception as e:
        logger.error(f"获取组会详情失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取组会详情失败", "error": "INTERNAL_ERROR"}
        )


@app.put("/api/meetings/{meeting_id}")
async def update_meeting(meeting_id: int, request: Request):
    """
    更新组会API
    只有导师、管理员或创建者可以更新
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取组会
        meeting = MeetingService.get_meeting_by_id(meeting_id)
        if not meeting:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}
            )

        # 权限检查：只有导师、管理员或创建者可以更新
        if current_user.role not in ['admin', 'teacher'] and meeting.created_by != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "没有权限修改此组会", "error": "ACCESS_DENIED"}
            )

        data = await request.json()

        # 解析时间字段
        update_data = {}
        if data.get("scheduled_at"):
            update_data["scheduled_at"] = datetime.fromisoformat(data["scheduled_at"])
        if data.get("material_deadline"):
            update_data["material_deadline"] = datetime.fromisoformat(data["material_deadline"])

        # 其他字段
        for field in ['title', 'meeting_type', 'description', 'location', 'is_online',
                       'online_link', 'duration_total', 'material_required', 'notes', 'minutes', 'status']:
            if field in data:
                update_data[field] = data[field]

        updated_meeting = MeetingService.update_meeting(meeting_id, **update_data)

        if not updated_meeting:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "更新组会失败", "error": "UPDATE_FAILED"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "组会更新成功",
                "data": updated_meeting.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"更新组会失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新组会失败", "error": "INTERNAL_ERROR"}
        )


@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: int, request: Request):
    """
    删除组会API
    只有导师和管理员可以删除
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限检查
    if current_user.role not in ['admin', 'teacher']:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限删除组会", "error": "ACCESS_DENIED"}
        )

    try:
        success = MeetingService.delete_meeting(meeting_id)

        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "组会删除成功"}
        )
    except Exception as e:
        logger.error(f"删除组会失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "删除组会失败", "error": "INTERNAL_ERROR"}
        )


@app.put("/api/meetings/{meeting_id}/status")
async def update_meeting_status(meeting_id: int, request: Request):
    """
    更新组会状态API
    只有导师和管理员可以更新状态
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限检查
    if current_user.role not in ['admin', 'teacher']:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "没有权限更新组会状态", "error": "ACCESS_DENIED"}
        )

    try:
        data = await request.json()
        status_value = data.get("status")

        # 支持的状态：scheduled(待召开)、ongoing(进行中)、completed(已召开)、cancelled(废弃)、postponed(推迟)
        valid_statuses = ['scheduled', 'ongoing', 'completed', 'cancelled', 'postponed']
        if status_value not in valid_statuses:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": f"状态值无效，有效状态：{', '.join(valid_statuses)}", "error": "INVALID_STATUS"}
            )

        updated_meeting = MeetingService.update_meeting_status(meeting_id, status_value)

        if not updated_meeting:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "组会不存在", "error": "MEETING_NOT_FOUND"}
            )

        # 组会状态联动更新汇报人状态
        conn = get_db()
        cursor = conn.cursor()

        if status_value == 'completed':
            # 组会召开完成，自动更新汇报人状态为 completed
            cursor.execute("""
                UPDATE meeting_presenters
                SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ? AND status = 'confirmed'
            """, (meeting_id,))

            # 自动通过已提交的材料
            cursor.execute("""
                UPDATE meeting_presenters
                SET material_status = 'approved', updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ? AND material_status = 'submitted'
            """, (meeting_id,))

        elif status_value == 'cancelled':
            # 组会废弃，重置材料状态
            cursor.execute("""
                UPDATE meeting_presenters
                SET material_status = 'pending', updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ?
            """, (meeting_id,))

        conn.commit()
        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "组会状态更新成功",
                "data": updated_meeting.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"更新组会状态失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新组会状态失败", "error": "INTERNAL_ERROR"}
        )


# ==================== 汇报人管理API ====================

@app.get("/api/meetings/{meeting_id}/presenters")
async def get_meeting_presenters(meeting_id: int, request: Request):
    """
    获取组会汇报人列表API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        conn = get_db()
        cursor = conn.cursor()

        # 获取汇报人列表，包含用户信息和材料状态
        cursor.execute("""
            SELECT mp.id, mp.meeting_id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                   mp.material_required, mp.status, mp.material_status, mp.created_at, mp.updated_at,
                   u.username, u.role, u.research_direction
            FROM meeting_presenters mp
            LEFT JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = ?
            ORDER BY mp.created_at ASC
        """, (meeting_id,))

        presenters = []
        for row in cursor.fetchall():
            presenter_id = row[0]

            # 获取该汇报人的文件（从 meeting_files 表直接获取）
            cursor.execute("""
                SELECT mf.id, mf.filename, mf.file_type, mf.file_size, mf.uploaded_at
                FROM meeting_files mf
                WHERE mf.presenter_id = ? AND mf.filename IS NOT NULL
            """, (presenter_id,))

            files = []
            for file_row in cursor.fetchall():
                files.append({
                    "id": file_row[0],
                    "filename": file_row[1],
                    "file_type": file_row[2],
                    "file_size": file_row[3],
                    "uploaded_at": file_row[4]
                })

            presenters.append({
                "id": row[0],
                "meeting_id": row[1],
                "user_id": row[2],
                "presenter_type": row[3],
                "duration_minutes": row[4],
                "material_required": row[5],
                "status": row[6],
                "material_status": row[7],
                "created_at": row[8],
                "updated_at": row[9],
                "user": {
                    "id": row[2],
                    "username": row[10],
                    "real_name": row[10],
                    "role": row[11],
                    "research_direction": row[12]
                },
                "files": files
            })

        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": {"presenters": presenters}}
        )
    except Exception as e:
        logger.error(f"获取汇报人列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取汇报人列表失败", "error": "INTERNAL_ERROR"}
        )


@app.post("/api/meetings/{meeting_id}/presenters")
async def add_meeting_presenter(meeting_id: int, request: Request):
    """
    添加汇报人API
    导师、管理员或组会创建者可以添加
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限检查：导师和管理员直接允许
    if current_user.role not in ['admin', 'teacher']:
        # 检查是否是组会创建者
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT created_by FROM meetings WHERE id = ?", (meeting_id,))
            meeting_row = cursor.fetchone()

        if not meeting_row or meeting_row[0] != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "只有导师、管理员或组会创建者可以分配汇报人", "error": "ACCESS_DENIED"}
            )

    try:
        data = await request.json()
        user_id = data.get("user_id")
        presenter_type = data.get("presenter_type", "assigned")
        duration_minutes = data.get("duration_minutes", 20)

        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请选择汇报人", "error": "VALIDATION_ERROR"}
            )

        with get_db() as conn:
            cursor = conn.cursor()

            # 检查是否已存在
            cursor.execute("SELECT id FROM meeting_presenters WHERE meeting_id = ? AND user_id = ?", (meeting_id, user_id))
            if cursor.fetchone():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "message": "该成员已是汇报人", "error": "ALREADY_EXISTS"}
                )

            # 添加汇报人
            cursor.execute("""
                INSERT INTO meeting_presenters (meeting_id, user_id, presenter_type, duration_minutes, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (meeting_id, user_id, presenter_type, duration_minutes))
            presenter_id = cursor.lastrowid

            # 获取添加的汇报人信息
            cursor.execute("""
                SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes, mp.status,
                       u.username, u.research_direction
                FROM meeting_presenters mp
                LEFT JOIN users u ON mp.user_id = u.id
                WHERE mp.id = ?
            """, (presenter_id,))
            row = cursor.fetchone()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "添加汇报人成功",
                "data": {
                    "id": row[0],
                    "meeting_id": meeting_id,
                    "user_id": row[1],
                    "presenter_type": row[2],
                    "duration_minutes": row[3],
                    "status": row[4],
                    "user": {
                        "id": row[1],
                        "username": row[5],
                        "real_name": row[5],
                        "research_direction": row[6]
                    }
                }
            }
        )
    except Exception as e:
        logger.error(f"添加汇报人失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "添加汇报人失败", "error": "INTERNAL_ERROR"}
        )


@app.delete("/api/meetings/{meeting_id}/presenters/{presenter_id}")
async def remove_meeting_presenter(meeting_id: int, presenter_id: int, request: Request):
    """
    移除汇报人API
    导师、管理员或组会创建者可以移除
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限检查：导师和管理员直接允许
    if current_user.role not in ['admin', 'teacher']:
        # 检查是否是组会创建者
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT created_by FROM meetings WHERE id = ?", (meeting_id,))
            meeting_row = cursor.fetchone()

        if not meeting_row or meeting_row[0] != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "只有导师、管理员或组会创建者可以移除汇报人", "error": "ACCESS_DENIED"}
            )

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meeting_presenters WHERE id = ? AND meeting_id = ?", (presenter_id, meeting_id))
            deleted = cursor.rowcount > 0

        if not deleted:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "汇报人不存在", "error": "NOT_FOUND"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "移除汇报人成功"}
        )
    except Exception as e:
        logger.error(f"移除汇报人失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "移除汇报人失败", "error": "INTERNAL_ERROR"}
        )


# ====================== 汇报材料 API ======================

@app.get("/api/materials")
async def get_materials(request: Request):
    """
    获取汇报材料列表API
    显示所有组会的汇报人材料状态
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取查询参数
        status_filter = request.query_params.get("status")  # pending, submitted, approved, rejected
        meeting_id_filter = request.query_params.get("meeting_id")

        conn = get_db()
        cursor = conn.cursor()

        # 构建查询条件
        where_conditions = ["mp.material_required = 1"]
        params = []

        if status_filter:
            where_conditions.append("mp.material_status = ?")
            params.append(status_filter)

        if meeting_id_filter:
            where_conditions.append("mp.meeting_id = ?")
            params.append(int(meeting_id_filter))

        where_clause = "WHERE " + " AND ".join(where_conditions)

        # 查询汇报材料列表
        query = f"""
            SELECT mp.id, mp.meeting_id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                   mp.material_status, mp.created_at, mp.updated_at,
                   m.title, m.scheduled_at, m.meeting_type, m.status as meeting_status,
                   u.username, u.role as user_role
            FROM meeting_presenters mp
            LEFT JOIN meetings m ON mp.meeting_id = m.id
            LEFT JOIN users u ON mp.user_id = u.id
            {where_clause}
            ORDER BY m.scheduled_at DESC, mp.created_at ASC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        materials = []
        for row in rows:
            # 获取关联的文件（从 meeting_files 表直接获取，不依赖 files 表）
            cursor.execute("""
                SELECT mf.id, mf.filename, mf.file_type, mf.file_size, mf.uploaded_at
                FROM meeting_files mf
                WHERE mf.presenter_id = ? AND mf.filename IS NOT NULL
            """, (row[0],))

            files = []
            for file_row in cursor.fetchall():
                files.append({
                    "id": file_row[0],
                    "filename": file_row[1],
                    "file_type": file_row[2],
                    "file_size": file_row[3],
                    "uploaded_at": file_row[4]
                })

            # 状态文本映射
            status_text_map = {
                'pending': '待提交',
                'submitted': '待审核',
                'approved': '已通过',
                'rejected': '已驳回'
            }

            materials.append({
                "id": row[0],
                "meeting_id": row[1],
                "user_id": row[2],
                "presenter_type": row[3],
                "duration_minutes": row[4],
                "status": row[5],
                "status_text": status_text_map.get(row[5], '待提交'),
                "created_at": row[6],
                "updated_at": row[7],
                "meeting_title": row[8],
                "meeting_scheduled_at": row[9],
                "meeting_type": row[10],
                "meeting_status": row[11],
                "username": row[12],
                "user_role": row[13],
                "files": files
            })

        conn.close()

        # 统计数据
        stats = {
            "total": len(materials),
            "pending": len([m for m in materials if m['status'] == 'pending']),
            "submitted": len([m for m in materials if m['status'] == 'submitted']),
            "approved": len([m for m in materials if m['status'] == 'approved']),
            "rejected": len([m for m in materials if m['status'] == 'rejected'])
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "materials": materials,
                    "stats": stats
                }
            }
        )
    except Exception as e:
        logger.error(f"获取汇报材料列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取汇报材料列表失败", "error": "INTERNAL_ERROR"}
        )


@app.put("/api/materials/{presenter_id}/status")
async def update_material_status(presenter_id: int, request: Request):
    """
    更新材料审核状态API
    只有导师和管理员可以审核
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取汇报人信息，检查权限
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mp.id, mp.user_id, mp.meeting_id
            FROM meeting_presenters mp
            WHERE mp.id = ?
        """, (presenter_id,))

        presenter_row = cursor.fetchone()
        if not presenter_row:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "汇报人不存在", "error": "NOT_FOUND"}
            )

        presenter_user_id = presenter_row[1]

        # 权限检查：汇报人本人、导师、管理员都可以审核
        if current_user.id != presenter_user_id and current_user.role not in ['admin', 'teacher']:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "只有汇报人本人、导师或管理员可以审核材料", "error": "ACCESS_DENIED"}
            )

        data = await request.json()
        new_status = data.get("status")

        if new_status not in ['pending', 'submitted', 'approved', 'rejected']:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "无效的状态值", "error": "VALIDATION_ERROR"}
            )

        cursor.execute("""
            UPDATE meeting_presenters
            SET material_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, presenter_id))

        conn.commit()
        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "材料状态更新成功"}
        )
    except Exception as e:
        logger.error(f"更新材料状态失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新材料状态失败", "error": "INTERNAL_ERROR"}
        )


@app.post("/api/materials/{presenter_id}/files")
async def upload_material_file(presenter_id: int, request: Request):
    """
    为汇报人上传材料文件API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取汇报人信息
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mp.id, mp.meeting_id, mp.user_id, mp.status
            FROM meeting_presenters mp
            WHERE mp.id = ?
        """, (presenter_id,))

        presenter_row = cursor.fetchone()
        if not presenter_row:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "汇报人不存在", "error": "NOT_FOUND"}
            )

        # 权限检查：只有汇报人本人、导师、管理员可以上传
        presenter_user_id = presenter_row[2]
        if current_user.id != presenter_user_id and current_user.role not in ['admin', 'teacher']:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "只有汇报人本人或导师可以上传材料", "error": "ACCESS_DENIED"}
            )

        # 解析请求体
        form = await request.form()
        file = form.get("file")

        if not file:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请选择要上传的文件", "error": "VALIDATION_ERROR"}
            )

        # 检查文件大小
        file_content = await file.read()
        file_size = len(file_content)
        if file_size > 50 * 1024 * 1024:  # 50MB
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "文件大小超过限制（最大50MB）", "error": "FILE_TOO_LARGE"}
            )

        # 检查文件类型
        original_filename = file.filename
        file_type = original_filename.split('.')[-1].lower() if '.' in original_filename else 'unknown'
        allowed_types = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md', 'zip', 'rar']
        if file_type not in allowed_types:
            conn.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": f"不支持的文件类型: {file_type}", "error": "UNSUPPORTED_TYPE"}
            )

        # 生成唯一文件名（时间戳前缀）
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{original_filename}"

        # 创建材料存储目录
        materials_dir = Path(__file__).parent.parent / "uploads" / "materials"
        materials_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件到磁盘
        file_path = materials_dir / unique_filename
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # 直接插入到 meeting_files 表（独立存储，不依赖 files 表）
        meeting_id = presenter_row[1]
        cursor.execute("""
            INSERT INTO meeting_files (meeting_id, presenter_id, filename, file_path, file_size, file_type, uploaded_by, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (meeting_id, presenter_id, unique_filename, str(file_path), file_size, file_type, current_user.id))

        meeting_file_id = cursor.lastrowid

        # 更新汇报人材料状态为已提交
        cursor.execute("""
            UPDATE meeting_presenters
            SET material_status = 'submitted', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (presenter_id,))

        conn.commit()
        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "材料上传成功",
                "data": {
                    "file_id": meeting_file_id,
                    "filename": unique_filename,
                    "file_type": file_type,
                    "file_size": file_size
                }
            }
        )
    except Exception as e:
        logger.error(f"上传材料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "上传材料失败", "error": "INTERNAL_ERROR"}
        )


@app.get("/api/meetings/{meeting_id}/materials")
async def get_meeting_materials(meeting_id: int, request: Request):
    """
    获取组会的所有汇报材料API（供组会记录页面使用）
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        conn = get_db()
        cursor = conn.cursor()

        # 获取组会所有汇报人的材料
        cursor.execute("""
            SELECT mp.id, mp.user_id, mp.presenter_type, mp.duration_minutes,
                   mp.material_status, u.username
            FROM meeting_presenters mp
            LEFT JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = ?
            ORDER BY mp.created_at ASC
        """, (meeting_id,))

        materials = []
        for row in cursor.fetchall():
            presenter_id = row[0]

            # 获取该汇报人的文件（从 meeting_files 表直接获取）
            cursor.execute("""
                SELECT mf.id, mf.filename, mf.file_type, mf.file_size, mf.uploaded_at
                FROM meeting_files mf
                WHERE mf.presenter_id = ? AND mf.filename IS NOT NULL
            """, (presenter_id,))

            files = []
            for file_row in cursor.fetchall():
                files.append({
                    "id": file_row[0],
                    "filename": file_row[1],
                    "file_type": file_row[2],
                    "file_size": file_row[3],
                    "uploaded_at": file_row[4]
                })

            materials.append({
                "presenter_id": presenter_id,
                "user_id": row[1],
                "username": row[5],
                "real_name": row[5],
                "presenter_type": row[2],
                "duration_minutes": row[3],
                "material_status": row[4],
                "files": files
            })

        conn.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": {"materials": materials}}
        )
    except Exception as e:
        logger.error(f"获取组会材料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取组会材料失败", "error": "INTERNAL_ERROR"}
        )


@app.get("/api/meeting_files/{file_id}/download")
async def download_meeting_file(file_id: int, request: Request):
    """
    下载汇报材料文件API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mf.id, mf.filename, mf.file_path, mf.file_type
            FROM meeting_files mf
            WHERE mf.id = ? AND mf.filename IS NOT NULL
        """, (file_id,))

        file_row = cursor.fetchone()
        conn.close()

        if not file_row:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件不存在", "error": "NOT_FOUND"}
            )

        file_path = Path(file_row[2])
        if not file_path.exists():
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件已被删除", "error": "FILE_NOT_FOUND"}
            )

        return FileResponse(
            path=str(file_path),
            filename=file_row[1],
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"下载汇报材料失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "下载失败", "error": "INTERNAL_ERROR"}
        )


# ====================== 研究任务 API ======================

@app.get("/api/research_tasks")
async def get_research_tasks(request: Request):
    """
    获取研究任务列表API
    支持分页、筛选和排序
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取查询参数
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        status_filter = request.query_params.get("status")
        priority_filter = request.query_params.get("priority")
        assignee_filter = request.query_params.get("assignee_id")
        type_filter = request.query_params.get("task_type")
        keyword_filter = request.query_params.get("keyword")
        sort_by = request.query_params.get("sort_by", "deadline")
        sort_order = request.query_params.get("sort_order", "asc")

        offset = (page - 1) * limit

        # 获取任务列表
        tasks = TaskService.get_tasks(
            user_id=current_user.id,
            user_role=current_user.role,
            status=status_filter,
            priority=priority_filter,
            assignee_id=int(assignee_filter) if assignee_filter else None,
            task_type=type_filter,
            keyword=keyword_filter,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

        # 获取总数
        total = TaskService.get_tasks_count(
            user_id=current_user.id,
            user_role=current_user.role,
            status=status_filter,
            priority=priority_filter,
            assignee_id=int(assignee_filter) if assignee_filter else None,
            task_type=type_filter,
            keyword=keyword_filter
        )

        # 计算分页信息
        total_pages = (total + limit - 1) // limit if total > 0 else 1

        # 获取负责人信息
        with get_db() as conn:
            cursor = conn.cursor()
            tasks_with_assignee = []
            for task in tasks:
                task_dict = task.to_dict()
                task_dict['display_status'] = task.get_display_status()
                task_dict['status_text'] = task.get_status_text()
                task_dict['priority_text'] = task.get_priority_text()

                # 获取负责人信息
                cursor.execute("SELECT id, username FROM users WHERE id = ?", (task.assignee_id,))
                assignee_row = cursor.fetchone()
                if assignee_row:
                    task_dict['assignee'] = {
                        'id': assignee_row[0],
                        'username': assignee_row[1]
                    }

                # 获取创建者信息
                cursor.execute("SELECT id, username FROM users WHERE id = ?", (task.creator_id,))
                creator_row = cursor.fetchone()
                if creator_row:
                    task_dict['creator'] = {
                        'id': creator_row[0],
                        'username': creator_row[1]
                    }

                tasks_with_assignee.append(task_dict)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "tasks": tasks_with_assignee,
                    "pagination": {
                        "current_page": page,
                        "per_page": limit,
                        "total": total,
                        "total_pages": total_pages,
                        "has_next": page < total_pages,
                        "has_prev": page > 1
                    }
                }
            }
        )
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取任务列表失败", "error": "INTERNAL_ERROR"}
        )


@app.get("/api/research_tasks/stats")
async def get_research_task_stats(request: Request):
    """
    获取研究任务统计API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        stats = TaskService.get_task_stats(current_user.id, current_user.role)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": stats}
        )
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取任务统计失败", "error": "INTERNAL_ERROR"}
        )


@app.post("/api/research_tasks")
async def create_research_task(request: Request):
    """
    创建研究任务API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        title = data.get("title")
        description = data.get("description")
        priority = data.get("priority", "middle")
        deadline_str = data.get("deadline")
        assignee_id = data.get("assignee_id")

        if not title:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "任务标题不能为空", "error": "VALIDATION_ERROR"}
            )

        # 处理截止日期
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
            except:
                pass

        # 确定任务类型和负责人
        if current_user.role in ['admin', 'teacher']:
            # 导师可以创建导师任务
            task_type = data.get("task_type", "assigned")
            if not assignee_id:
                assignee_id = current_user.id  # 默认分配给自己
        else:
            # 学生只能创建个人任务
            task_type = "personal"
            assignee_id = current_user.id  # 学生创建的任务负责人必须是自己

        # 创建任务
        task = TaskService.create_task(
            title=title,
            creator_id=current_user.id,
            assignee_id=assignee_id,
            task_type=task_type,
            description=description,
            priority=priority,
            deadline=deadline
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "任务创建成功",
                "data": task.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "创建任务失败", "error": "INTERNAL_ERROR"}
        )


@app.get("/api/research_tasks/{task_id}")
async def get_research_task_detail(task_id: int, request: Request):
    """
    获取任务详情API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "任务不存在", "error": "NOT_FOUND"}
            )

        # 权限检查
        if current_user.role not in ['admin', 'teacher']:
            if task.assignee_id != current_user.id and task.creator_id != current_user.id:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"success": False, "message": "无权限查看此任务", "error": "ACCESS_DENIED"}
                )

        task_dict = task.to_dict()
        task_dict['display_status'] = task.get_display_status()
        task_dict['status_text'] = task.get_status_text()
        task_dict['priority_text'] = task.get_priority_text()

        # 获取负责人和创建者信息
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users WHERE id = ?", (task.assignee_id,))
            assignee_row = cursor.fetchone()
            if assignee_row:
                task_dict['assignee'] = {'id': assignee_row[0], 'username': assignee_row[1]}

            cursor.execute("SELECT id, username FROM users WHERE id = ?", (task.creator_id,))
            creator_row = cursor.fetchone()
            if creator_row:
                task_dict['creator'] = {'id': creator_row[0], 'username': creator_row[1]}

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": task_dict}
        )
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取任务详情失败", "error": "INTERNAL_ERROR"}
        )


@app.put("/api/research_tasks/{task_id}")
async def update_research_task(task_id: int, request: Request):
    """
    更新任务API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "任务不存在", "error": "NOT_FOUND"}
            )

        # 权限检查
        if not TaskService.check_permission(task, current_user.id, current_user.role, 'edit'):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "无权限编辑此任务", "error": "ACCESS_DENIED"}
            )

        data = await request.json()

        # 处理截止日期
        deadline_str = data.get("deadline")
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
            except:
                pass

        # 更新任务
        updated_task = TaskService.update_task(
            task_id,
            title=data.get("title"),
            description=data.get("description"),
            priority=data.get("priority"),
            status=data.get("status"),
            progress=data.get("progress"),
            assignee_id=data.get("assignee_id"),
            deadline=deadline
        )

        if not updated_task:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "更新失败", "error": "UPDATE_FAILED"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "任务更新成功",
                "data": updated_task.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新任务失败", "error": "INTERNAL_ERROR"}
        )


@app.put("/api/research_tasks/{task_id}/progress")
async def update_research_task_progress(task_id: int, request: Request):
    """
    更新任务进度API（学生权限）
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "任务不存在", "error": "NOT_FOUND"}
            )

        # 权限检查：负责人可以更新进度
        if not TaskService.check_permission(task, current_user.id, current_user.role, 'update_progress'):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "无权限更新此任务进度", "error": "ACCESS_DENIED"}
            )

        data = await request.json()
        progress = data.get("progress", 0)
        status = data.get("status")

        # 更新进度
        updated_task = TaskService.update_progress(task_id, progress, status)

        if not updated_task:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "更新进度失败", "error": "UPDATE_FAILED"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "进度更新成功",
                "data": updated_task.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"更新进度失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新进度失败", "error": "INTERNAL_ERROR"}
        )


@app.delete("/api/research_tasks/{task_id}")
async def delete_research_task(task_id: int, request: Request):
    """
    删除任务API
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "任务不存在", "error": "NOT_FOUND"}
            )

        # 权限检查
        if not TaskService.check_permission(task, current_user.id, current_user.role, 'delete'):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "无权限删除此任务", "error": "ACCESS_DENIED"}
            )

        # 删除任务
        success = TaskService.delete_task(task_id)

        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"success": True, "message": "任务删除成功"}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "删除失败", "error": "DELETE_FAILED"}
            )
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "删除任务失败", "error": "INTERNAL_ERROR"}
        )


# ==================== 文献库API ====================

@app.get("/api/paper_database/")
async def get_papers(
    request: Request,
    keyword: Optional[str] = None,
    tag: Optional[str] = None,
    read_status: Optional[str] = Query(None, alias="status"),
    year: Optional[int] = None,
    starred: Optional[bool] = None,
    library_type: Optional[str] = None,
    sort: str = 'newest',
    limit: int = 20,
    offset: int = 0
):
    """获取文献列表"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    papers, total = PaperService.get_papers(
        user_id=current_user.id,
        keyword=keyword, tag=tag, status=read_status,
        year=year, starred=starred, library_type=library_type,
        sort=sort, limit=limit, offset=offset
    )
    return JSONResponse(content={"success": True, "data": papers, "total": total})


@app.get("/api/paper_database/stats")
async def get_paper_stats(request: Request, library_type: Optional[str] = None):
    """获取文献统计"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    stats = PaperService.get_stats(user_id=current_user.id, library_type=library_type)
    return JSONResponse(content={"success": True, "data": stats})


@app.get("/api/paper_database/tags")
async def get_paper_tags(request: Request):
    """获取标签列表"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    tags = PaperService.get_tags()
    return JSONResponse(content={"success": True, "data": [t.to_dict() for t in tags]})


@app.post("/api/paper_database/batch/star")
async def batch_star_papers(request: Request):
    """批量收藏"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        paper_ids = data.get("paper_ids", [])
        star = data.get("star", True)
        library_type = data.get("library_type", "public")

        count = PaperService.batch_star(paper_ids, current_user.id, star, library_type)
        return JSONResponse(content={"success": True, "count": count})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


@app.post("/api/paper_database/{paper_id}/add-to-personal")
async def add_paper_to_personal(paper_id: int, request: Request):
    """将团队文献添加到个人文献库"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    success, error = PaperService.add_to_personal_library(paper_id, current_user.id)
    if success:
        return JSONResponse(content={"success": True, "message": "已添加到个人文献库"})
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": error}
        )


@app.post("/api/paper_database/{paper_id}/share-to-team")
async def share_paper_to_team(paper_id: int, request: Request):
    """将个人文献分享到团队文献库"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    success, message = PaperService.share_to_team(paper_id, current_user.id)
    if success:
        return JSONResponse(content={"success": True, "message": message or "已分享到团队文献库"})
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": message}
        )


@app.post("/api/paper_database/batch/tags")
async def batch_set_paper_tags(request: Request):
    """批量设置标签"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        paper_ids = data.get("paper_ids", [])
        tag = data.get("tag")
        library_type = data.get("library_type", "public")

        if not tag:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "标签不能为空"}
            )

        # 为每个文献添加标签
        count = 0
        with get_db() as conn:
            cursor = conn.cursor()

            # 确保个人文献标签表存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_paper_tags (
                    personal_paper_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (personal_paper_id, tag_id)
                )
            """)

            # 获取或创建标签
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
            tag_row = cursor.fetchone()
            if tag_row:
                tag_id = tag_row[0]
            else:
                cursor.execute("""
                    INSERT INTO tags (name, tag_type, created_by, created_at)
                    VALUES (?, 'custom', ?, ?)
                """, (tag, current_user.id, datetime.now()))
                cursor.execute("SELECT last_insert_rowid()")
                tag_id = cursor.fetchone()[0]

            for paper_id in paper_ids:
                if library_type == 'public':
                    cursor.execute("""
                        INSERT OR IGNORE INTO paper_tags (paper_id, tag_id)
                        VALUES (?, ?)
                    """, (paper_id, tag_id))
                else:
                    cursor.execute("""
                        INSERT OR IGNORE INTO personal_paper_tags (personal_paper_id, tag_id)
                        VALUES (?, ?)
                    """, (paper_id, tag_id))
                count += 1

        return JSONResponse(content={"success": True, "count": count})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


@app.delete("/api/paper_database/batch")
async def batch_delete_papers(request: Request):
    """批量删除"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        paper_ids = data.get("paper_ids", [])
        library_type = data.get("library_type", "public")

        result = PaperService.batch_delete(paper_ids, current_user.id, current_user.role, library_type)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


@app.get("/api/paper_database/{paper_id}")
async def get_paper_detail(paper_id: int, request: Request, library_type: str = 'public'):
    """获取文献详情"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    paper = PaperService.get_paper_by_id(paper_id, current_user.id, library_type)
    if not paper:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "message": "文献不存在", "error": "NOT_FOUND"}
        )

    return JSONResponse(content={"success": True, "data": paper})


@app.post("/api/paper_database/")
async def upload_paper(request: Request):
    """上传新文献"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        form = await request.form()
        title = form.get("title")
        pdf_file = form.get("pdf")
        library_type = form.get("library_type", "public")

        if not title:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "标题不能为空"}
            )

        if not pdf_file:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请上传PDF文件"}
            )

        pdf_data = await pdf_file.read()

        year_val = None
        if form.get("year"):
            try:
                year_val = int(form.get("year"))
            except:
                pass

        tags_str = form.get("tags", "")
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

        paper, error = PaperService.create_paper(
            title=title,
            pdf_data=pdf_data,
            original_filename=pdf_file.filename,
            uploader_id=current_user.id,
            authors=form.get("authors"),
            year=year_val,
            journal=form.get("journal"),
            doi=form.get("doi"),
            abstract=form.get("abstract"),
            arxiv_link=form.get("arxiv_link"),
            semantic_scholar_link=form.get("semantic_scholar_link"),
            tags=tags_list,
            library_type=library_type
        )

        if paper is None and error:
            # 实际错误（如文件大小超限、用户已有相同文献等）
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": error}
            )

        # 成功：返回 paper dict
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"success": True, "data": paper, "message": error if error else "文献上传成功"}
        )

    except Exception as e:
        logger.error(f"上传文献失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"上传失败: {str(e)}"}
        )


@app.put("/api/paper_database/{paper_id}")
async def update_paper_info(paper_id: int, request: Request):
    """更新文献元数据"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        library_type = data.get("library_type", "public")

        year_val = None
        if data.get("year"):
            try:
                year_val = int(data.get("year"))
            except:
                pass

        tags_str = data.get("tags", "")
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

        paper, error = PaperService.update_paper(
            paper_id=paper_id,
            user_id=current_user.id,
            title=data.get("title"),
            authors=data.get("authors"),
            year=year_val,
            journal=data.get("journal"),
            doi=data.get("doi"),
            abstract=data.get("abstract"),
            arxiv_link=data.get("arxiv_link"),
            semantic_scholar_link=data.get("semantic_scholar_link"),
            tags=tags_list,
            read_status=data.get("read_status"),
            library_type=library_type
        )

        if error:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": error}
            )

        return JSONResponse(content={"success": True, "data": paper, "message": "文献更新成功"})
    except Exception as e:
        logger.error(f"更新文献失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"更新失败: {str(e)}"}
        )


@app.post("/api/paper_database/{paper_id}/star")
async def toggle_paper_star(paper_id: int, request: Request):
    """收藏/取消收藏"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json() if request.method == "POST" else {}
        library_type = data.get("library_type", "public") if data else "public"
    except:
        library_type = "public"

    success = PaperService.toggle_star(paper_id, current_user.id, library_type)
    return JSONResponse(content={"success": success})


@app.put("/api/paper_database/{paper_id}/status")
async def update_paper_status(paper_id: int, request: Request):
    """更新阅读状态"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        status_val = data.get("status")
        library_type = data.get("library_type", "public")

        if not status_val:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "状态不能为空"}
            )

        success = PaperService.update_status(paper_id, current_user.id, status_val, library_type)
        return JSONResponse(content={"success": success})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


@app.delete("/api/paper_database/{paper_id}")
async def delete_paper(paper_id: int, request: Request):
    """删除文献"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json() if request.headers.get("content-type") == "application/json" else {}
        library_type = data.get("library_type", "public") if data else "public"
    except:
        library_type = "public"

    result = PaperService.delete_paper(paper_id, current_user.id, current_user.role, library_type)
    return JSONResponse(content=result)


@app.get("/api/paper_database/{paper_id}/download")
async def download_paper(paper_id: int, request: Request, library_type: str = 'public'):
    """下载文献PDF"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    paper = PaperService.get_paper_by_id(paper_id, current_user.id, library_type)
    if not paper:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "message": "文献不存在", "error": "NOT_FOUND"}
        )

    pdf_path = paper.get('pdf_path')
    if not pdf_path or not os.path.exists(pdf_path):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "message": "PDF文件不存在"}
        )

    # 增加下载次数
    PaperService.increment_download_count(paper_id)

    return FileResponse(
        path=pdf_path,
        filename=os.path.basename(pdf_path),
        media_type='application/pdf'
    )


# ====================== 研究进展 API ======================

@app.get("/api/research_progress/my")
async def get_my_progress(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    order: str = Query("desc")
):
    """获取自己的进展历史列表"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    progress_list = ResearchProgressService.get_user_progress_list(
        current_user.id, page, limit, order
    )

    return JSONResponse(content={
        "success": True,
        "data": [p.to_dict() for p in progress_list],
        "page": page,
        "limit": limit
    })


@app.post("/api/research_progress/submit")
async def submit_progress(request: Request):
    """提交新的进展"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 学生角色才能提交进展
    if current_user.role != 'student':
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "只有学生可以提交进展", "error": "FORBIDDEN"}
        )

    try:
        data = await request.json()
        research_direction = data.get("research_direction", current_user.research_direction or "")
        weekly_progress = data.get("weekly_progress")
        next_goal = data.get("next_goal")
        difficulties = data.get("difficulties")
        completion_rate = data.get("completion_rate", 0)
        attachments = data.get("attachments")
        submission_period = data.get("submission_period", "weekly")

        # 验证必填字段
        if not weekly_progress or not next_goal:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "本周进展和下周目标为必填项", "error": "VALIDATION_ERROR"}
            )

        # 创建进展
        progress = ResearchProgressService.create_progress(
            user_id=current_user.id,
            research_direction=research_direction,
            weekly_progress=weekly_progress,
            next_goal=next_goal,
            difficulties=difficulties,
            completion_rate=completion_rate,
            attachments=attachments,
            submission_period=submission_period
        )

        logger.info(f"用户 {current_user.username} 提交了研究进展")

        return JSONResponse(content={
            "success": True,
            "message": "进展提交成功",
            "data": progress.to_dict()
        })

    except Exception as e:
        logger.error(f"提交进展失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"提交失败: {str(e)}", "error": "SERVER_ERROR"}
        )


@app.get("/api/research_progress/settings")
async def get_my_settings(request: Request):
    """获取自己的提交周期设置"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    setting = ProgressSettingService.get_setting_by_user(current_user.id)

    if not setting:
        # 返回默认设置
        return JSONResponse(content={
            "success": True,
            "data": {
                "period_type": "weekly",
                "reminder_enabled": True,
                "reminder_days": 1,
                "next_deadline": None,
                "period_text": "每周提交"
            }
        })

    result = setting.to_dict()
    result["period_text"] = setting.get_period_text()

    return JSONResponse(content={
        "success": True,
        "data": result
    })


@app.get("/api/research_progress/team")
async def get_team_progress(
    request: Request,
    student_type: Optional[str] = Query(None),
    grade: Optional[int] = Query(None),
    research_direction: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    updated_within: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """获取团队所有成员进展（导师/管理员）"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 所有用户都可以查看团队进展（学生只能查看，导师/管理员可以操作）
    progress_list = ResearchProgressService.get_team_progress_list(
        user_role=current_user.role,
        student_type=student_type,
        grade=grade,
        research_direction=research_direction,
        status=status,
        updated_within=updated_within,
        page=page,
        limit=limit
    )

    return JSONResponse(content={
        "success": True,
        "data": progress_list,
        "page": page,
        "limit": limit
    })


@app.get("/api/research_progress/stats")
async def get_progress_stats(request: Request):
    """获取统计数据"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 所有用户都可以查看统计数据
    stats = ResearchProgressService.get_progress_stats()

    return JSONResponse(content={
        "success": True,
        "data": stats
    })


@app.put("/api/research_progress/settings/{user_id}")
async def set_user_settings(user_id: int, request: Request):
    """设置某个学生的提交周期"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限校验：只有导师和管理员可以设置周期
    if current_user.role not in ['teacher', 'admin']:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "只有导师和管理员可以设置提交周期", "error": "FORBIDDEN"}
        )

    try:
        data = await request.json()
        period_type = data.get("period_type", "weekly")
        reminder_enabled = data.get("reminder_enabled", True)
        reminder_days = data.get("reminder_days", 1)

        # 验证周期类型
        if period_type not in ['weekly', 'biweekly', 'monthly']:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "无效的周期类型", "error": "VALIDATION_ERROR"}
            )

        setting = ProgressSettingService.create_or_update_setting(
            user_id=user_id,
            period_type=period_type,
            reminder_enabled=reminder_enabled,
            reminder_days=reminder_days,
            created_by=current_user.id
        )

        logger.info(f"导师 {current_user.username} 为学生 {user_id} 设置了提交周期")

        return JSONResponse(content={
            "success": True,
            "message": "周期设置成功",
            "data": setting.to_dict()
        })

    except Exception as e:
        logger.error(f"设置周期失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"设置失败: {str(e)}", "error": "SERVER_ERROR"}
        )


@app.post("/api/research_progress/settings/batch")
async def batch_set_settings(request: Request):
    """批量设置学生提交周期（管理员/导师）"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限校验：管理员和导师可以批量设置
    if current_user.role not in ['admin', 'teacher']:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "只有管理员或导师可以批量设置提交周期", "error": "FORBIDDEN"}
        )

    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])
        period_type = data.get("period_type", "weekly")
        reminder_days = data.get("reminder_days", 1)

        if not user_ids:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请选择要设置的学生", "error": "VALIDATION_ERROR"}
            )

        settings = ProgressSettingService.batch_create_settings(
            user_ids=user_ids,
            period_type=period_type,
            reminder_days=reminder_days,
            created_by=current_user.id
        )

        logger.info(f"{current_user.role} {current_user.username} 批量设置了 {len(settings)} 个学生的提交周期")

        return JSONResponse(content={
            "success": True,
            "message": f"成功设置 {len(settings)} 个学生的提交周期",
            "data": [s.to_dict() for s in settings]
        })

    except Exception as e:
        logger.error(f"批量设置失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"设置失败: {str(e)}", "error": "SERVER_ERROR"}
        )


@app.get("/api/research_progress/{progress_id}")
async def get_progress_detail(progress_id: int, request: Request):
    """查看进展详情"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    progress = ResearchProgressService.get_progress_by_id(progress_id)
    if not progress:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "message": "进展不存在", "error": "NOT_FOUND"}
        )

    # 权限校验：学生只能看自己的，导师和管理员可以看所有
    if current_user.role == 'student' and progress.user_id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "无权查看此进展", "error": "FORBIDDEN"}
        )

    # 获取提交者信息
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, research_direction FROM users WHERE id = ?", (progress.user_id,))
        user_row = cursor.fetchone()

    result = progress.to_dict()
    if user_row:
        result["user_info"] = {
            "id": user_row[0],
            "username": user_row[1],
            "research_direction": user_row[2]
        }

    return JSONResponse(content={
        "success": True,
        "data": result
    })


@app.put("/api/research_progress/{progress_id}")
async def update_progress(progress_id: int, request: Request):
    """编辑已提交的进展（仅限本周）"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()

        progress = ResearchProgressService.update_progress(
            progress_id=progress_id,
            user_id=current_user.id,
            research_direction=data.get("research_direction"),
            weekly_progress=data.get("weekly_progress"),
            next_goal=data.get("next_goal"),
            difficulties=data.get("difficulties"),
            completion_rate=data.get("completion_rate"),
            attachments=data.get("attachments")
        )

        if not progress:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "无权编辑此进展或已超过编辑时限", "error": "FORBIDDEN"}
            )

        logger.info(f"用户 {current_user.username} 更新了研究进展 {progress_id}")

        return JSONResponse(content={
            "success": True,
            "message": "进展更新成功",
            "data": progress.to_dict()
        })

    except Exception as e:
        logger.error(f"更新进展失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"更新失败: {str(e)}", "error": "SERVER_ERROR"}
        )


@app.post("/api/research_progress/{progress_id}/feedback")
async def add_feedback(progress_id: int, request: Request):
    """发送导师反馈/沟通"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    # 权限校验：只有导师和管理员可以发送反馈
    if current_user.role not in ['teacher', 'admin']:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "message": "只有导师和管理员可以发送反馈", "error": "FORBIDDEN"}
        )

    try:
        data = await request.json()
        feedback = data.get("feedback")

        if not feedback:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "反馈内容不能为空", "error": "VALIDATION_ERROR"}
            )

        progress = ResearchProgressService.add_supervisor_feedback(
            progress_id=progress_id,
            feedback=feedback,
            supervisor_id=current_user.id
        )

        if not progress:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "进展不存在", "error": "NOT_FOUND"}
            )

        logger.info(f"导师 {current_user.username} 对进展 {progress_id} 发送了反馈")

        return JSONResponse(content={
            "success": True,
            "message": "反馈发送成功",
            "data": progress.to_dict()
        })

    except Exception as e:
        logger.error(f"发送反馈失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"发送失败: {str(e)}", "error": "SERVER_ERROR"}
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