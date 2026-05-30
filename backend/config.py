"""
================================================================================
应用配置模块 (config.py)
================================================================================

模块名称: backend/config.py
功能描述: 应用配置类，管理不同环境的配置参数
使用方式:
    from config import Config
    config = Config

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
import os
from pathlib import Path

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 如果没有安装 python-dotenv，使用默认值

class Config:
    """应用配置"""

    # 应用信息
    APP_NAME = "研究生组会文件共享系统"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "研究生组会文件共享系统 - 用户认证API"

    # API 文档
    DOCS_URL = "/docs"
    REDOC_URL = "/redoc"

    # 服务配置（从环境变量读取）
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8088"))

    # 前端地址（从环境变量读取）
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")

    # CORS 配置（动态生成）
    CORS_ORIGINS = [
        FRONTEND_URL,
        f"http://localhost:{PORT}",
        f"http://127.0.0.1:{PORT}",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",  # Vite 默认端口
    ]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["*"]

    # 目录配置
    BASE_DIR = Path(__file__).parent
    UPLOAD_DIR = BASE_DIR.parent / "uploads"
    TEMPLATES_DIR = BASE_DIR.parent / "templates-html"

    # 会话配置
    SESSION_EXPIRE_HOURS = 24  # 普通登录
    SESSION_EXPIRE_DAYS = 7    # 记住登录

    # 文件上传配置
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    # 开发环境配置
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境需配置具体域名
    CORS_ORIGINS = [os.getenv("FRONTEND_URL", "")] if os.getenv("FRONTEND_URL") else []


# 配置映射
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": Config
}


def get_config(env: str = "default") -> Config:
    """获取配置实例"""
    return config_map.get(env, Config)