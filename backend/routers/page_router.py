"""
================================================================================
页面路由模块 (routers/page_router.py)
================================================================================

模块名称: backend/routers/page_router.py
功能描述: 页面路由重定向到 Vue 前端

所有页面路由都重定向到 Vue 前端应用，不再使用 Jinja2 模板。

页面路由列表 (共15个):
    GET /                    - 主页面 → Vue 工作台
    GET /login               - 登录页面 → Vue 登录
    GET /register            - 注册页面 → Vue 注册
    GET /rm_share_file       - 共享文件 → Vue 共享资料
    GET /tm_user_management  - 成员管理 → Vue 成员管理
    GET /tm_academic_website - 学术工具 → Vue 学术工具
    GET /tm_research_progress - 研究进展 → Vue 研究进展
    GET /rm_paper_database   - 文献库 → Vue 学术文献
    GET /gm_meeting_schedule - 组会安排 → Vue 组会安排
    GET /gm_report_materials - 汇报材料 → Vue 汇报材料
    GET /gm_meeting_record   - 组会记录 → Vue 组会记录
    GET /rm_research_tasks   - 研究任务 → Vue 研究任务
    GET /user_profile        - 个人资料 → Vue 个人资料
    GET /edit_password       - 修改密码 → Vue 修改密码
    GET /settings            - 设置 → Vue 设置

作者: wjg
创建日期: 2026-05-21
更新日期: 2026-05-31 (改为 Vue 前端重定向)
================================================================================
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from dependencies.auth import get_current_user

router = APIRouter(tags=["页面"])

# Vue 前端地址
VUE_FRONTEND_URL = "http://localhost:3001"


def _get_session_token(request: Request) -> str:
    """从请求中获取 session_token"""
    # URL 参数
    session_token = request.query_params.get("session_token")
    if session_token:
        return session_token

    # Authorization 头
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]

    # Cookie
    session_token = request.cookies.get("session_token")
    if session_token:
        return session_token

    return None


async def _redirect_to_vue(path: str, request: Request, require_login: bool = True) -> RedirectResponse:
    """重定向到 Vue 前端"""
    if require_login:
        current_user = await get_current_user(request)
        if not current_user:
            # 未登录，重定向到 Vue 登录页面
            return RedirectResponse(url=f"{VUE_FRONTEND_URL}/login", status_code=302)

    # 获取 session_token 并传递给 Vue
    session_token = _get_session_token(request)
    if session_token:
        return RedirectResponse(url=f"{VUE_FRONTEND_URL}{path}?session_token={session_token}", status_code=302)
    else:
        return RedirectResponse(url=f"{VUE_FRONTEND_URL}{path}", status_code=302)


# 主页面 - 重定向到 Vue 工作台
@router.get("/")
async def index(request: Request):
    """主页面 → Vue 工作台"""
    return await _redirect_to_vue("/", request)


# 登录页面 - 重定向到 Vue 登录
@router.get("/login")
async def login_page(request: Request):
    """登录页面 → Vue 登录"""
    return RedirectResponse(url=f"{VUE_FRONTEND_URL}/login", status_code=302)


# 注册页面 - 重定向到 Vue 注册
@router.get("/register")
async def register_page(request: Request):
    """注册页面 → Vue 注册"""
    return RedirectResponse(url=f"{VUE_FRONTEND_URL}/register", status_code=302)


# 共享文件页面 - 重定向到 Vue 共享资料
@router.get("/rm_share_file")
async def rm_share_file_page(request: Request):
    """共享文件页面 → Vue 共享资料"""
    return await _redirect_to_vue("/share-file", request)


# 成员管理页面 - 重定向到 Vue 成员管理
@router.get("/tm_user_management")
async def tm_user_management_page(request: Request):
    """成员管理页面 → Vue 成员管理"""
    return await _redirect_to_vue("/user-management", request)


# 学术工具页面 - 重定向到 Vue 学术工具
@router.get("/tm_academic_website")
async def tm_academic_website_page(request: Request):
    """学术工具页面 → Vue 学术工具"""
    return await _redirect_to_vue("/academic-tools", request)


# 研究进展页面 - 重定向到 Vue 研究进展
@router.get("/tm_research_progress")
async def tm_research_progress_page(request: Request):
    """研究进展页面 → Vue 研究进展"""
    return await _redirect_to_vue("/research-progress", request)


# 文献库页面 - 重定向到 Vue 学术文献
@router.get("/rm_paper_database")
async def rm_paper_database_page(request: Request):
    """文献库页面 → Vue 学术文献"""
    return await _redirect_to_vue("/paper-database", request)


# 组会安排页面 - 重定向到 Vue 组会安排
@router.get("/gm_meeting_schedule")
async def gm_meeting_schedule_page(request: Request):
    """组会安排页面 → Vue 组会安排"""
    return await _redirect_to_vue("/meeting-schedule", request)


# 汇报材料页面 - 重定向到 Vue 汇报材料
@router.get("/gm_report_materials")
async def gm_report_materials_page(request: Request):
    """汇报材料页面 → Vue 汇报材料"""
    return await _redirect_to_vue("/report-materials", request)


# 组会记录页面 - 重定向到 Vue 组会记录
@router.get("/gm_meeting_record")
async def gm_meeting_record_page(request: Request):
    """组会记录页面 → Vue 组会记录"""
    return await _redirect_to_vue("/meeting-record", request)


# 研究任务页面 - 重定向到 Vue 研究任务
@router.get("/rm_research_tasks")
async def rm_research_tasks_page(request: Request):
    """研究任务页面 → Vue 研究任务"""
    return await _redirect_to_vue("/research-tasks", request)


# 个人资料页面 - 重定向到 Vue 个人资料
@router.get("/user_profile")
async def user_profile_page(request: Request):
    """个人资料页面 → Vue 个人资料"""
    return await _redirect_to_vue("/user-profile", request)


# 修改密码页面 - 重定向到 Vue 修改密码
@router.get("/edit_password")
async def edit_password_page(request: Request):
    """修改密码页面 → Vue 修改密码"""
    return await _redirect_to_vue("/edit-password", request)


# 设置页面 - 重定向到 Vue 设置
@router.get("/settings")
async def settings_page(request: Request):
    """设置页面 → Vue 设置"""
    return await _redirect_to_vue("/settings", request)