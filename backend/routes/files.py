"""
文件路由
端点：
- POST /api/files/upload - 上传文件
- GET  /api/files/download/{filename} - 按文件名下载
- GET  /api/files - 获取文件列表（分页）
- GET  /api/files/stats - 获取文件统计
- GET  /api/files/{file_id} - 获取文件详情
- PUT  /api/files/{file_id} - 更新文件信息
- DELETE /api/files/{file_id} - 删除文件
- GET  /api/files/{file_id}/download - 文件下载
- GET  /api/files/{file_id}/view - 文件预览
"""
import os
import urllib.parse
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, FileResponse
from loguru import logger

from utils.auth_helper import get_current_user
from services.file_service import FileService
from database.connection import get_db

router = APIRouter(prefix="/api/files", tags=["文件"])


@router.post("/upload")
async def upload_file(request: Request):
    """文件上传API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        form = await request.form()
        file = form.get("file")
        description = form.get("description", "")
        tags = form.get("tags", "")
        is_public = form.get("is_public", "false").lower() == "true"

        if not file:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "请选择要上传的文件", "error": "NO_FILE"}
            )

        # 检查文件大小
        file_data = await file.read()
        if len(file_data) > FileService.MAX_FILE_SIZE:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"文件大小超过限制（最大 {FileService.MAX_FILE_SIZE // (1024*1024)} MB）",
                    "error": "FILE_TOO_LARGE"
                }
            )

        # 检查文件类型
        if not FileService.is_allowed_file(file.filename):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "不支持的文件类型", "error": "UNSUPPORTED_FILE_TYPE"}
            )

        # 上传文件
        uploaded_file, error_message = FileService.upload_file(
            file_data=file_data,
            original_filename=file.filename,
            uploader_id=current_user.id,
            description=description if description else None,
            tags=tags if tags else None,
            is_public=is_public
        )

        if uploaded_file:
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={"success": True, "message": "文件上传成功", "data": uploaded_file.to_dict()}
            )
        else:
            # 根据错误类型返回不同的状态码
            if "已存在" in error_message:
                status_code = status.HTTP_409_CONFLICT
            elif "超过限制" in error_message:
                status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            elif "不支持" in error_message:
                status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            return JSONResponse(
                status_code=status_code,
                content={"success": False, "message": error_message or "文件上传失败", "error": "UPLOAD_FAILED"}
            )

    except Exception as e:
        logger.error(f"文件上传错误: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"文件上传过程中发生错误: {str(e)}", "error": "INTERNAL_ERROR"}
        )


@router.get("/download/{filename}")
async def download_file_by_name(filename: str, request: Request):
    """根据文件名下载文件API端点，用于研究进展附件下载"""
    decoded_filename = urllib.parse.unquote(filename)
    logger.info(f"下载文件请求: {decoded_filename}")

    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_path, file_type, uploader_id
                FROM files
                WHERE filename = ? AND status = 'active'
            """, (decoded_filename,))
            file_row = cursor.fetchone()

            if not file_row:
                logger.error(f"文件不存在: {decoded_filename}")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}
                )

            file_id, stored_filename, file_path, file_type, uploader_id = file_row

        if not os.path.exists(file_path):
            logger.error(f"物理文件不存在: {file_path}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}
            )

        return FileResponse(
            path=file_path,
            filename=stored_filename,
            media_type=file_type or 'application/octet-stream'
        )

    except Exception as e:
        logger.error(f"文件下载错误: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"文件下载失败: {str(e)}", "error": "INTERNAL_ERROR"}
        )


@router.get("")
async def get_files(request: Request):
    """获取文件列表API端点"""
    logger.info("加载用户文件列表")
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        # 获取查询参数
        user_id = request.query_params.get("user_id")
        scope = request.query_params.get("scope", "my")
        limit = int(request.query_params.get("limit", 5))
        offset = int(request.query_params.get("offset", 0))
        page = int(request.query_params.get("page", 1))
        keyword = request.query_params.get("keyword", "")

        # 验证参数
        if limit not in [5, 10, 20, 100]:
            limit = 5

        # 计算偏移量
        offset = (page - 1) * limit if page > 1 else 0

        files = []
        total = 0

        if scope == "my":
            files = FileService.get_files_by_user(current_user.id, limit, offset)
            total = FileService.get_files_count_by_user(current_user.id)
        elif scope == "public":
            files = FileService.get_public_files(limit, offset)
            my_files = FileService.get_files_by_user(current_user.id, limit, offset)
            existing_ids = set(f.id for f in files)
            for f in my_files:
                if f.id not in existing_ids:
                    files.append(f)
            total = FileService.get_public_files_count() + FileService.get_files_count_by_user(current_user.id)
        elif scope == "all" and current_user.role == "admin":
            if user_id:
                files = FileService.get_files_by_user(int(user_id), limit, offset)
                total = FileService.get_files_count_by_user(int(user_id))
            else:
                files = FileService.get_files_by_user(current_user.id, limit, offset)
                files.extend(FileService.get_public_files(limit, offset))
                total = FileService.get_files_count_by_user(current_user.id) + FileService.get_public_files_count()

        # 搜索关键词
        if keyword:
            if scope == "my":
                files = FileService.search_files(keyword, current_user.id, limit, offset)
                total = FileService.get_search_files_count(keyword, current_user.id)
            elif scope == "public":
                files = FileService.search_files(keyword, None, limit, offset)
                total = FileService.get_search_files_count(keyword, None)
            elif scope == "all" and current_user.role == "admin":
                files = FileService.search_files(keyword, int(user_id) if user_id else None, limit, offset)
                total = FileService.get_search_files_count(keyword, int(user_id) if user_id else None)

        # 计算分页信息
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1

        # 获取上传者名字
        files_data = []
        with get_db() as conn:
            cursor = conn.cursor()
            for file in files:
                file_dict = file.to_dict()
                cursor.execute("SELECT username FROM users WHERE id = ?", (file.uploader_id,))
                uploader_row = cursor.fetchone()
                file_dict['uploader_name'] = uploader_row[0] if uploader_row else '未知用户'
                files_data.append(file_dict)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "files": files_data,
                    "total_files_count": total,
                    "pagination": {
                        "current_page": page,
                        "per_page": limit,
                        "total": total,
                        "total_pages": total_pages,
                        "has_next": has_next,
                        "has_prev": has_prev,
                        "next_page": page + 1 if has_next else None,
                        "prev_page": page - 1 if has_prev else None
                    }
                }
            }
        )

    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": "参数错误", "error": "INVALID_PARAMETERS"}
        )
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取文件列表失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/stats")
async def get_file_stats(request: Request):
    """获取文件统计信息API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        user_id = request.query_params.get("user_id")
        scope = request.query_params.get("scope", "my")

        # 确定统计范围
        target_user_id = None
        if scope == "my":
            target_user_id = current_user.id
        elif scope == "all" and current_user.role == "admin":
            target_user_id = int(user_id) if user_id else None

        stats = FileService.get_file_stats(target_user_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": stats}
        )

    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": "参数错误", "error": "INVALID_PARAMETERS"}
        )
    except Exception as e:
        logger.error(f"获取文件统计信息失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取文件统计信息失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/{file_id}")
async def get_file_details(file_id: int, request: Request):
    """获取文件详情API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        file_obj = FileService.get_file_by_id(file_id)
        if not file_obj:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}
            )

        # 检查访问权限
        if not file_obj.is_accessible_by_user(current_user.id, current_user.role):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "没有权限访问此文件", "error": "ACCESS_DENIED"}
            )

        # 更新访问时间
        FileService.increment_download_count(file_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": file_obj.to_dict()}
        )

    except Exception as e:
        logger.error(f"获取文件详情失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "获取文件详情失败", "error": "INTERNAL_ERROR"}
        )


@router.put("/{file_id}")
async def update_file_info(file_id: int, request: Request):
    """更新文件信息API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        data = await request.json()
        description = data.get("description")
        tags = data.get("tags")
        is_public = data.get("is_public")

        success = FileService.update_file_info(
            file_id, current_user.id, current_user.role,
            description, tags, is_public
        )

        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"success": True, "message": "文件信息更新成功"}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "文件信息更新失败，可能没有权限或文件不存在", "error": "UPDATE_FAILED"}
            )

    except Exception as e:
        logger.error(f"更新文件信息失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "更新文件信息失败", "error": "INTERNAL_ERROR"}
        )


@router.delete("/{file_id}")
async def delete_file(file_id: int, request: Request):
    """删除文件API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        success = FileService.delete_file(file_id, current_user.id, current_user.role)
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"success": True, "message": "文件删除成功"}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "文件删除失败，可能没有权限或文件不存在", "error": "DELETE_FAILED"}
            )

    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "删除文件失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/{file_id}/download")
async def download_file(file_id: int, request: Request):
    """文件下载API端点"""
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        file_obj = FileService.get_file_by_id(file_id)
        if not file_obj:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}
            )

        # 检查访问权限
        if not file_obj.is_accessible_by_user(current_user.id, current_user.role):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "没有权限访问此文件", "error": "ACCESS_DENIED"}
            )

        # 检查文件是否存在
        if not os.path.exists(file_obj.file_path):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件已丢失", "error": "FILE_LOST"}
            )

        # 增加下载次数
        FileService.increment_download_count(file_id)

        return FileResponse(
            path=file_obj.file_path,
            filename=file_obj.filename,
            media_type=file_obj.file_type
        )

    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "文件下载失败", "error": "INTERNAL_ERROR"}
        )


@router.get("/{file_id}/view")
async def view_file(file_id: int, request: Request):
    """
    直接文件预览API端点
    类似于Flask的send_file功能，直接返回文件内容供浏览器预览
    特别适用于PDF文件的浏览器内预览
    """
    current_user = await get_current_user(request)
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "请先登录", "error": "NOT_AUTHENTICATED"}
        )

    try:
        file_obj = FileService.get_file_by_id(file_id)
        if not file_obj:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件不存在", "error": "FILE_NOT_FOUND"}
            )

        # 检查访问权限
        if not file_obj.is_accessible_by_user(current_user.id, current_user.role):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "没有权限访问此文件", "error": "ACCESS_DENIED"}
            )

        # 检查文件是否存在
        if not os.path.exists(file_obj.file_path):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "文件已丢失", "error": "FILE_LOST"}
            )

        # 增加访问次数
        FileService.increment_download_count(file_id)

        # 根据文件类型设置合适的MIME类型
        media_type = file_obj.file_type
        if file_obj.file_type == 'application/pdf':
            media_type = 'application/pdf'
        elif not file_obj.file_type.startswith(('image/', 'text/', 'video/', 'audio/')):
            media_type = 'application/octet-stream'

        return FileResponse(
            path=file_obj.file_path,
            filename=file_obj.filename,
            media_type=media_type,
            headers={"Content-Disposition": f"inline; filename=\"{file_obj.filename}\""}
        )

    except Exception as e:
        logger.error(f"文件预览失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "文件预览失败", "error": "INTERNAL_ERROR"}
        )