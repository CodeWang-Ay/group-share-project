"""
================================================================================
扩展初始化模块 (extensions.py)
================================================================================

模块名称: backend/extensions.py
功能描述: FastAPI 扩展和工具的初始化配置

使用方式:
    from extensions import templates
    return templates.TemplateResponse("index.html", {"request": request})

依赖模块:
    - config.Config: 获取模板目录配置

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from fastapi.templating import Jinja2Templates
from datetime import datetime
from pathlib import Path

from config import Config

# 模板引擎初始化
templates = Jinja2Templates(directory=str(Config.TEMPLATES_DIR))

# 设置模板全局变量
templates.env.globals['app_name'] = Config.APP_NAME
templates.env.globals['current_year'] = datetime.now().year