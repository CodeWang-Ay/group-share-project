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
from database.connection import get_db, DATABASE_PATH
from services.auth import AuthService
from services.session import session_manager

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
    从请求头中获取会话令牌并验证
    """
    # 从请求头或cookie中获取会话令牌
    session_token = request.headers.get("Authorization")
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token[7:]  # 移除 "Bearer " 前缀

    # 如果请求头中没有，尝试从cookie中获取
    if not session_token:
        session_token = request.cookies.get("session_token")

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
    主页面路由 - 需要登录才能访问
    """
    # 检查用户是否已登录
    current_user = await get_current_user(request)
    if not current_user:
        # 未登录，重定向到登录页面
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # 已登录，提供主页面模板，并传递用户信息
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
    return templates.TemplateResponse("login.html", {"request": request})


# 注册页面路由
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    注册页面路由
    """
    return templates.TemplateResponse("register.html", {"request": request})


# API端点：用户登录
@app.post("/api/auth/login")
async def login(request: Request):
    """
    用户登录API端点

    接收JSON格式的登录数据并验证用户凭据
    """
    print("🔥 登录API被调用")

    try:
        # 获取请求体数据
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        captcha = data.get("captcha", "")
        remember_me = data.get("remember_me", False)

        print(f"📝 接收到登录数据: username={username}, password={'***' if password else 'None'}, captcha={captcha}, remember_me={remember_me}")

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
            print(f"❌ 登录失败: 用户名或密码错误 (username={username})")
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

        print(f"✅ 登录成功: user={user.username}, role={user.role}, session_token={session_token[:20]}...")

        # 登录成功，返回用户信息、会话令牌和跳转URL
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "登录成功",
                "data": {
                    "user": user.to_dict(),
                    "session_token": session_token,
                    "redirect_url": "/"
                }
            }
        )

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
    print("🔥 注册API被调用")

    try:
        # 获取请求体数据
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")

        print(f"📝 接收到注册数据: username={username}, password={'***' if password else 'None'}, role={role}")

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

        print(f"✅ 注册成功: user={new_user.username}, role={new_user.role}")

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


# 启动时清理过期会话
@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行的任务
    """
    print("🔧 执行启动任务...")

    # 清理过期会话
    cleaned_count = session_manager.cleanup_expired_sessions()
    if cleaned_count > 0:
        print(f"🧹 启动时清理了 {cleaned_count} 个过期会话")

    print("✅ 启动任务完成")


# 启动命令
if __name__ == "__main__":
    import uvicorn

    print("🚀 启动基础用户认证系统...")
    print(f"📋 服务信息:")
    print(f"   - 服务地址: http://localhost:8081")
    print(f"   - API文档: http://localhost:8081/docs")
    print(f"   - 数据库: {DATABASE_PATH}")
    print()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )