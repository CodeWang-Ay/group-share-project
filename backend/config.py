"""
================================================================================
应用配置模块 (config.py)
================================================================================

模块名称: backend/config.py
功能描述: 应用配置类，管理不同环境的配置参数
使用方式:
    from config import Config, get_config
    config = get_config("development")

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from pathlib import Path

class Config:
    """应用配置"""

    # 应用信息
    APP_NAME = "研究生组会文件共享系统"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "研究生组会文件共享系统 - 用户认证API"

    # API 文档
    DOCS_URL = "/docs"
    REDOC_URL = "/redoc"

    # CORS 配置
    CORS_ORIGINS = [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["*"]

    # 目录配置
    BASE_DIR = Path(__file__).parent
    UPLOAD_DIR = BASE_DIR.parent / "uploads"
    TEMPLATES_DIR = BASE_DIR.parent / "templates"

    # 会话配置
    SESSION_EXPIRE_HOURS = 24  # 普通登录
    SESSION_EXPIRE_DAYS = 7    # 记住登录

    # 文件上传配置
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    # 开发环境配置
    DEBUG = False

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    CORS_ORIGINS = []  # 生产环境需配置具体域名

# 配置映射
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": Config
}

def get_config(env: str = "default") -> Config:
    """获取配置实例"""
    return config_map.get(env, Config)