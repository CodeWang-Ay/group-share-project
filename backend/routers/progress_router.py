"""
================================================================================
研究进展路由模块 (routes/progress.py)
================================================================================

模块名称: backend/routes/progress.py
功能描述: 研究进展管理 API 端点，包括进度提交、周期设置、导师反馈等

API 端点列表 (共10个):
    GET  /api/research_progress/my        - 获取自己进展历史
        返回: 用户提交的所有研究进展记录

    POST /api/research_progress/submit    - 提交新进展
        接收: title, content, attachments[], progress_date
        学生提交周/月度进展报告

    GET  /api/research_progress/settings  - 获取提交周期设置
        返回: 各学生的提交周期配置

    GET  /api/research_progress/team      - 获取团队进展
        返回: 所有学生的最新进展汇总
        需要导师/管理员权限

    GET  /api/research_progress/stats     - 获取统计数据
        返回: 提交率、活跃度、逾期统计等

    PUT  /api/research_progress/settings/{user_id} - 设置学生提交周期
        接收: cycle_type(weekly/monthly), cycle_day
        需要导师/管理员权限

    POST /api/research_progress/settings/batch - 批量设置提交周期
        接收: user_ids[], cycle_type, cycle_day
        为多名学生统一设置提交周期

    GET  /api/research_progress/{progress_id} - 查看进展详情
        返回: 进展完整内容 + 附件

    PUT  /api/research_progress/{progress_id} - 编辑已提交进展
        接收: title, content, attachments[]
        仅限提交者本人或导师/管理员

    POST /api/research_progress/{progress_id}/feedback - 发送导师反馈
        接收: content
        导师对进展进行评价指导

路由配置:
    - 前缀: /api/research_progress
    - 标签: 研究进展

提交周期类型:
    - weekly  : 每周提交 (如每周一)
    - monthly : 每月提交 (如每月15日)

权限要求:
    提交进展: 学生本人
    设置周期: 导师/管理员
    查看团队: 导师/管理员
    发送反馈: 导师/管理员

依赖模块:
    - services.research_progress_service: 研究进展服务
    - utils.auth_helper                 : 认证依赖
    - database.connection               : 数据库连接

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from typing import Optional

from fastapi import APIRouter, Request, Query, status
from fastapi.responses import JSONResponse
from loguru import logger

from utils.auth_helper import get_current_user
from services.research_progress_service import ResearchProgressService, ProgressSettingService
from database.connection import get_db

router = APIRouter(prefix="/api/research_progress", tags=["研究进展"])


@router.get("/my")
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

    result = ResearchProgressService.get_user_progress_list(
        current_user.id, page, limit, order
    )

    return JSONResponse(content={
        "success": True,
        "data": [p.to_dict() for p in result['items']],
        "pagination": {
            "total": result['total'],
            "page": result['page'],
            "limit": result['limit'],
            "total_pages": result['total_pages']
        }
    })


@router.post("/submit")
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


@router.get("/settings")
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


@router.get("/team")
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
        "data": progress_list['items'],
        "pagination": {
            "total": progress_list['total'],
            "page": progress_list['page'],
            "limit": progress_list['limit'],
            "total_pages": progress_list['total_pages']
        }
    })


@router.get("/stats")
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


@router.put("/settings/{user_id}")
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


@router.post("/settings/batch")
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


@router.get("/{progress_id}")
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


@router.put("/{progress_id}")
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


@router.post("/{progress_id}/feedback")
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