"""
================================================================================
文献路由模块 (routers/paper_router.py)
================================================================================

模块名称: backend/routers/paper_router.py
功能描述: 文献论文管理 API 端点

API 端点列表 (共15个):
    GET    /api/paper_database/             - 获取文献列表
    GET    /api/paper_database/stats        - 获取文献统计
    GET    /api/paper_database/tags         - 获取标签列表
    POST   /api/paper_database/batch/star   - 批量收藏
    POST   /api/paper_database/{paper_id}/add-to-personal - 添加到个人库
    POST   /api/paper_database/{paper_id}/share-to-team   - 分享到团队库
    POST   /api/paper_database/batch/tags   - 批量设置标签
    DELETE /api/paper_database/batch        - 批量删除
    GET    /api/paper_database/{paper_id}   - 获取文献详情
    POST   /api/paper_database/             - 上传文献
    PUT    /api/paper_database/{paper_id}   - 更新文献信息
    POST   /api/paper_database/{paper_id}/star - 收藏/取消收藏
    PUT    /api/paper_database/{paper_id}/status - 更新阅读状态
    DELETE /api/paper_database/{paper_id}   - 删除文献
    GET    /api/paper_database/{paper_id}/download - 下载文献

职责:
    - 只处理 HTTP 请求和响应（一行代码）
    - 不写任何业务逻辑
    - 调用 PaperService 处理业务

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
import json
from loguru import logger
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional

from dependencies.auth import get_current_user
from services.paper_service import PaperService

router = APIRouter(prefix="/api/paper_database", tags=["学术文献"])


@router.get("/")
async def get_papers(request: Request, current_user=Depends(get_current_user),
                     keyword: Optional[str] = None, tag: Optional[str] = None,
                     status: Optional[str] = Query(None, alias="status"),
                     year: Optional[int] = None, starred: Optional[bool] = None,
                     library_type: Optional[str] = None, sort: str = 'newest',
                     limit: int = 20, offset: int = 0,
                     service: PaperService = Depends()):
    """获取文献列表"""
    filters = {"keyword": keyword, "tag": tag, "status": status, "year": year,
               "starred": starred, "library_type": library_type, "sort": sort,
               "limit": limit, "offset": offset}
    logger.info(json.dumps(filters, ensure_ascii=False))
    result = await service.api_get_list(filters, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/stats")
async def get_paper_stats(request: Request, current_user=Depends(get_current_user),
                          library_type: Optional[str] = None,
                          service: PaperService = Depends()):
    """获取文献统计"""
    result = await service.api_get_stats(current_user.id, library_type)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/tags")
async def get_paper_tags(request: Request, current_user=Depends(get_current_user),
                         service: PaperService = Depends()):
    """获取标签列表"""
    result = await service.api_get_tags()
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/batch/star")
async def batch_star_papers(request: Request, current_user=Depends(get_current_user),
                            service: PaperService = Depends()):
    """批量收藏"""
    data = await request.json()
    result = await service.api_batch_star(data, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/{paper_id}/add-to-personal")
async def add_paper_to_personal(paper_id: int, request: Request,
                                current_user=Depends(get_current_user),
                                service: PaperService = Depends()):
    """添加到个人文献库"""
    result = await service.api_add_to_personal(paper_id, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/{paper_id}/share-to-team")
async def share_paper_to_team(paper_id: int, request: Request,
                              current_user=Depends(get_current_user),
                              service: PaperService = Depends()):
    """分享到团队文献库"""
    result = await service.api_share_to_team(paper_id, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/batch/tags")
async def batch_set_paper_tags(request: Request, current_user=Depends(get_current_user),
                               service: PaperService = Depends()):
    """批量设置标签"""
    data = await request.json()
    result = await service.api_batch_set_tags(data, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.delete("/batch")
async def batch_delete_papers(request: Request, current_user=Depends(get_current_user),
                              service: PaperService = Depends()):
    """批量删除"""
    data = await request.json()
    result = await service.api_batch_delete(data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{paper_id}")
async def get_paper_detail(paper_id: int, request: Request,
                           current_user=Depends(get_current_user),
                           library_type: str = 'public',
                           service: PaperService = Depends()):
    """获取文献详情"""
    result = await service.api_get_detail(paper_id, current_user.id, library_type)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/")
async def upload_paper(request: Request, current_user=Depends(get_current_user),
                       service: PaperService = Depends()):
    """上传新文献"""
    form = await request.form()
    result = await service.api_upload(form, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{paper_id}")
async def update_paper_info(paper_id: int, request: Request,
                            current_user=Depends(get_current_user),
                            service: PaperService = Depends()):
    """更新文献元数据"""
    data = await request.json()
    result = await service.api_update(paper_id, data, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.post("/{paper_id}/star")
async def toggle_paper_star(paper_id: int, request: Request,
                            current_user=Depends(get_current_user),
                            service: PaperService = Depends()):
    """收藏/取消收藏"""
    try:
        data = await request.json()
    except:
        data = {}
    result = await service.api_toggle_star(paper_id, data, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.put("/{paper_id}/status")
async def update_paper_status(paper_id: int, request: Request,
                              current_user=Depends(get_current_user),
                              service: PaperService = Depends()):
    """更新阅读状态"""
    data = await request.json()
    result = await service.api_update_status(paper_id, data, current_user.id)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.delete("/{paper_id}")
async def delete_paper(paper_id: int, request: Request,
                       current_user=Depends(get_current_user),
                       service: PaperService = Depends()):
    """删除文献"""
    try:
        data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    except:
        data = {}
    result = await service.api_delete(paper_id, data, current_user.id, current_user.role)
    return JSONResponse(status_code=result["status_code"], content=result["content"])


@router.get("/{paper_id}/download")
async def download_paper(paper_id: int, request: Request,
                         current_user=Depends(get_current_user),
                         library_type: str = 'public',
                         service: PaperService = Depends()):
    """下载文献PDF"""
    result = await service.api_download(paper_id, current_user.id, library_type)
    if result.get("error"):
        return JSONResponse(status_code=result["status_code"], content=result["content"])
    return FileResponse(path=result["file_path"], filename=result["filename"], media_type=result["media_type"])