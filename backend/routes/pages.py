"""
================================================================================
页面路由模块 (routes/pages.py)
================================================================================

模块名称: backend/routes/pages.py
功能描述: 所有 HTML 页面的路由端点，用于前端页面渲染

页面路由列表 (共15个):
    GET /                    - 主页面（根据登录状态显示）
        未登录: 显示登录页面
        已登录: 显示仪表板首页

    GET /login               - 登录页面
        渲染: login.html

    GET /register            - 注册页面
        渲染: register.html

    GET /rm_share_file       - 共享文件页面 (资源管理)
        渲染: rm_share_file.html
        需要登录

    GET /tm_user_management  - 成员管理页面 (团队管理)
        渲染: tm_user_management.html
        需要登录

    GET /tm_academic_website - 学术网站页面 (团队管理)
        渲染: tm_academic_website.html
        需要登录

    GET /tm_research_progress - 研究进展页面 (团队管理)
        渲染: tm_research_progress.html
        需要登录

    GET /rm_paper_database   - 文献库页面 (资源管理)
        渲染: rm_paper_database.html
        需要登录

    GET /gm_meeting_schedule - 组会安排页面 (组会管理)
        渲染: gm_meeting_schedule.html
        需要登录

    GET /gm_report_materials - 汇报材料页面 (组会管理)
        渲染: gm_report_materials.html
        需要登录

    GET /gm_meeting_record   - 组会记录页面 (组会管理)
        渲染: gm_meeting_record.html
        需要登录

    GET /rm_research_tasks   - 研究任务页面 (资源管理)
        渲染: rm_research_tasks.html
        需要登录

    GET /user_profile        - 个人资料页面
        渲染: user_profile.html
        需要登录

    GET /edit_password       - 修改密码页面
        渲染: edit_password.html
        需要登录

    GET /settings            - 设置页面
        渲染: settings.html
        需要登录

路由配置:
    - 前缀: 无 (根路径和各页面路径)
    - 标签: 页面

页面模块分类:
    - gm_ (组会管理)  : 组会安排、汇报材料、组会记录
    - rm_ (资源管理)  : 共享文件、文献库、研究任务
    - tm_ (团队管理)  : 成员管理、学术网站、研究进展

登录检查:
    大部分页面需要登录，未登录时自动重定向到 /login

依赖模块:
    - extensions.templates    : Jinja2 模板引擎
    - utils.auth_helper       : get_current_user 登录检查

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from loguru import logger

from extensions import templates
from utils.auth_helper import get_current_user

router = APIRouter(tags=["页面"])


def _check_login(request: Request):
    """检查登录状态，返回用户或 None"""
    return get_current_user(request)


def _redirect_to_login():
    """返回登录页面重定向"""
    return RedirectResponse(url="/login", status_code=302)


def _render_page(template_name: str, request: Request, user):
    """渲染页面模板"""
    return templates.TemplateResponse(template_name, {
        "request": request,
        "user": user
    })


# 主页面
@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页面 - 根据登录状态显示不同页面"""
    url_token = request.query_params.get("session_token")
    logger.info("检查用户登录状态...")

    current_user = await get_current_user(request)
    logger.info(f"Current user: {current_user}")

    if not current_user:
        logger.info("用户未登录，显示登录页面")
        return templates.TemplateResponse("login.html", {"request": request})

    if url_token:
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_token",
            value=url_token,
            max_age=86400,
            httponly=True,
            samesite="lax"
        )
        return response

    logger.info(f"用户已登录: {current_user.username}")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user
    })


# 登录页面
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})


# 注册页面
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """注册页面"""
    return templates.TemplateResponse("register.html", {"request": request})


# 共享文件页面
@router.get("/rm_share_file", response_class=HTMLResponse)
async def rm_share_file_page(request: Request):
    """共享文件页面"""
    logger.info("共享文件页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("rm_share_file.html", request, current_user)


# 成员管理页面
@router.get("/tm_user_management", response_class=HTMLResponse)
async def tm_user_management_page(request: Request):
    """成员管理页面"""
    logger.info("成员管理页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("tm_user_management.html", request, current_user)


# 学术网站页面
@router.get("/tm_academic_website", response_class=HTMLResponse)
async def tm_academic_website_page(request: Request):
    """学术工具页面"""
    logger.info("学术工具页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("tm_academic_website.html", request, current_user)


# 研究进展页面
@router.get("/tm_research_progress", response_class=HTMLResponse)
async def tm_research_progress_page(request: Request):
    """研究进展页面"""
    logger.info("研究进展页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("tm_research_progress.html", request, current_user)


# 文献库页面
@router.get("/rm_paper_database", response_class=HTMLResponse)
async def rm_paper_database_page(request: Request):
    """文献库页面"""
    logger.info("文献库页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("rm_paper_database.html", request, current_user)


# 组会安排页面
@router.get("/gm_meeting_schedule", response_class=HTMLResponse)
async def gm_meeting_schedule_page(request: Request):
    """组会安排页面"""
    logger.info("组会安排页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("gm_meeting_schedule.html", request, current_user)


# 汇报材料页面
@router.get("/gm_report_materials", response_class=HTMLResponse)
async def gm_report_materials_page(request: Request):
    """汇报材料页面"""
    logger.info("汇报材料页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("gm_report_materials.html", request, current_user)


# 组会记录页面
@router.get("/gm_meeting_record", response_class=HTMLResponse)
async def gm_meeting_record_page(request: Request):
    """组会记录页面"""
    logger.info("组会记录页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("gm_meeting_record.html", request, current_user)


# 研究任务页面
@router.get("/rm_research_tasks", response_class=HTMLResponse)
async def rm_research_tasks_page(request: Request):
    """研究任务页面"""
    logger.info("研究任务页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("rm_research_tasks.html", request, current_user)


# 个人资料页面
@router.get("/user_profile", response_class=HTMLResponse)
async def user_profile_page(request: Request):
    """个人资料页面"""
    logger.info("个人资料页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("user_profile.html", request, current_user)


# 修改密码页面
@router.get("/edit_password", response_class=HTMLResponse)
async def edit_password_page(request: Request):
    """修改密码页面"""
    logger.info("修改密码页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("edit_password.html", request, current_user)


# 设置页面
@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """设置页面"""
    logger.info("设置页面")
    current_user = await get_current_user(request)
    if not current_user:
        return _redirect_to_login()
    return _render_page("settings.html", request, current_user)