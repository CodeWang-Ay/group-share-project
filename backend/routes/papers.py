"""
================================================================================
文献库路由模块 (routes/papers.py)
================================================================================

模块名称: backend/routes/papers.py
功能描述: 文献论文管理 API 端点，包括文献上传、收藏、标签管理等

API 端点列表 (共15个):
    GET    /api/paper_database/             - 获取文献列表
        参数: scope(personal/team/public), keyword, tag, status, page, limit
        返回: 文献列表 + 分页信息

    GET    /api/paper_database/stats        - 获取文献统计
        返回: 文献总数、状态分布、标签分布等

    GET    /api/paper_database/tags         - 获取标签列表
        返回: 所有可用标签及其使用次数

    POST   /api/paper_database/batch/star   - 批量收藏
        接收: paper_ids[]
        批量添加到个人收藏

    POST   /api/paper_database/{paper_id}/add-to-personal - 添加到个人库
        将团队/公开文献添加到个人库

    POST   /api/paper_database/{paper_id}/share-to-team    - 分享到团队库
        将个人文献分享给团队

    POST   /api/paper_database/batch/tags   - 批量设置标签
        接收: paper_ids[], tags[]
        为多篇文献统一设置标签

    DELETE /api/paper_database/batch        - 批量删除文献
        接收: paper_ids[]

    GET    /api/paper_database/{paper_id}   - 获取文献详情
        返回: 文献完整信息 + 标签列表

    POST   /api/paper_database/             - 上传文献
        接收: multipart/form-data (file + metadata)
        支持: PDF 格式

    PUT    /api/paper_database/{paper_id}   - 更新文献信息
        接收: title, authors, journal, year, abstract 等

    POST   /api/paper_database/{paper_id}/star - 收藏/取消收藏
        切换收藏状态

    PUT    /api/paper_database/{paper_id}/status - 更新阅读状态
        接收: status (unread/reading/read)

    DELETE /api/paper_database/{paper_id}   - 删除文献
        删除文献记录及 PDF 文件

    GET    /api/paper_database/{paper_id}/download - 下载文献 PDF
        返回 PDF 文件流

路由配置:
    - 前缀: /api/paper_database
    - 标签: 文献库

文献状态:
    - unread   : 未读
    - reading  : 正在读
    - read     : 已读完
    - starred  : 已收藏

依赖模块:
    - services.paper_service.PaperService: 文献服务
    - utils.auth_helper                   : 认证依赖
    - database.connection                 : 数据库连接

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
import os
from datetime import datetime
from fastapi import APIRouter, Request, status, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
from loguru import logger

from utils.auth_helper import get_current_user
from services.paper_service import PaperService
from database.connection import get_db

router = APIRouter(prefix="/api/paper_database", tags=["文献库"])


@router.get("/")
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


@router.get("/stats")
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


@router.get("/tags")
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


@router.post("/batch/star")
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


@router.post("/{paper_id}/add-to-personal")
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


@router.post("/{paper_id}/share-to-team")
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


@router.post("/batch/tags")
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


@router.delete("/batch")
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


@router.get("/{paper_id}")
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


@router.post("/")
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


@router.put("/{paper_id}")
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


@router.post("/{paper_id}/star")
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


@router.put("/{paper_id}/status")
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


@router.delete("/{paper_id}")
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


@router.get("/{paper_id}/download")
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