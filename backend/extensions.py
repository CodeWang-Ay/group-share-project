"""
扩展初始化
FastAPI 扩展和工具的初始化配置
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