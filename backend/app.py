"""
================================================================================
应用入口模块 (app.py)
================================================================================

模块名称: backend/app.py
功能描述: FastAPI 应用主入口，负责创建和配置整个应用程序

主要内容:
    1. FastAPI 应用实例创建
    2. 中间件配置 (CORS、安全头、请求日志)
    3. 全局异常处理
    4. 静态文件挂载
    5. 路由模块注册

注册的路由模块 (共12个):
    - health_router     : 健康检查端点
    - pages_router      : HTML 页面路由
    - auth_router       : 用户认证 (登录、注册、登出)
    - users_router      : 用户信息管理
    - files_router      : 文件上传下载管理
    - members_router    : 团队成员管理
    - messages_router   : 消息系统
    - meetings_router   : 组会管理
    - materials_router  : 汇报材料管理
    - tasks_router      : 研究任务管理
    - papers_router     : 文献库管理
    - progress_router   : 研究进展管理

依赖模块:
    - config            : 应用配置
    - extensions        : 扩展初始化
    - routes/*          : 各路由模块

运行方式:
    python app.py

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from loguru import logger

from config import Config

# 导入所有路由模块
from routes import (
    auth_router,
    users_router,
    files_router,
    health_router,
    pages_router,
    meetings_router,
    messages_router,
    tasks_router,
    members_router,
)
from routes.papers import router as papers_router
from routes.materials import router as materials_router
from routes.progress import router as progress_router

# 创建 FastAPI 应用
app = FastAPI(
    title=Config.APP_NAME,
    description=Config.APP_DESCRIPTION,
    version=Config.APP_VERSION,
    docs_url=Config.DOCS_URL,
    redoc_url=Config.REDOC_URL
)


# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=Config.CORS_ALLOW_CREDENTIALS,
    allow_methods=Config.CORS_ALLOW_METHODS,
    allow_headers=Config.CORS_ALLOW_HEADERS,
)


# 安全头中间件
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info(f"[{start_time.isoformat()}] {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"[{end_time.isoformat()}] {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
        return response
    except Exception as e:
        logger.error(f"请求错误: {e}")
        raise


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "服务器内部错误", "error": "INTERNAL_ERROR"}
    )


# 挂载静态文件
Config.UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(Config.UPLOAD_DIR)), name="uploads")


# 注册所有路由
app.include_router(health_router)
app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(files_router)
app.include_router(members_router)
app.include_router(messages_router)
app.include_router(meetings_router)
app.include_router(materials_router)
app.include_router(tasks_router)
app.include_router(papers_router)
app.include_router(progress_router)


# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("应用启动...")
    logger.info("已注册 12 个路由模块")
    logger.info("应用启动完成")


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("应用关闭")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8081)