"""
================================================================================
健康检查路由模块 (routes/health.py)
================================================================================

模块名称: backend/routes/health.py
功能描述: 应用健康状态检查 API 端点，用于运维监控和负载均衡
API 端点列表 (共6个):
    GET /health                      - 基础健康检查
    GET /health/detailed             - 详细健康检查
    GET /ready                       - 就绪检查 (Readiness)
    GET /alive                       - 存活检查 (Liveness)
    GET /metrics                     - 应用指标统计
    DELETE /api/admin/clear-sessions - 清空所有会话
依赖模块:
    - config.Config             : 配置信息
    - database.connection       : 数据库连接检查
    - services.session          : 会话管理器检查

作者: wjg
创建日期: 2026-05-21
================================================================================
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path
import sys
import platform
import os
from loguru import logger

from config import Config
from database.connection import get_db, DATABASE_PATH
from services.session import session_manager

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check():
    """应用健康检查端点"""
    health_status = {
        "success": True,
        "message": "应用运行正常",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "status": "healthy",
        "checks": {}
    }

    try:
        # 检查数据库连接
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                health_status["checks"]["database"] = {
                    "status": "healthy",
                    "message": "数据库连接正常"
                }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "message": f"数据库连接失败: {str(e)}"
            }
            health_status["status"] = "unhealthy"
            health_status["success"] = False

        # 检查会话管理器
        try:
            session_count = len(session_manager.sessions)
            health_status["checks"]["session_manager"] = {
                "status": "healthy",
                "message": f"会话管理器正常，当前活跃会话: {session_count}"
            }
        except Exception as e:
            health_status["checks"]["session_manager"] = {
                "status": "unhealthy",
                "message": f"会话管理器异常: {str(e)}"
            }

        # 检查模板目录
        try:
            templates_info = {
                "directory": str(Config.TEMPLATES_DIR),
                "exists": Config.TEMPLATES_DIR.exists()
            }
            health_status["checks"]["templates"] = {
                "status": "healthy" if Config.TEMPLATES_DIR.exists() else "warning",
                "info": templates_info
            }
        except Exception as e:
            health_status["checks"]["templates"] = {
                "status": "unhealthy",
                "message": f"模板目录检查失败: {str(e)}"
            }

        # 检查数据库文件
        try:
            db_path = Path(DATABASE_PATH)
            if db_path.exists():
                db_size = db_path.stat().st_size
                health_status["checks"]["database_file"] = {
                    "status": "healthy",
                    "size": db_size
                }
            else:
                health_status["checks"]["database_file"] = {
                    "status": "warning",
                    "message": "数据库文件不存在"
                }
        except Exception as e:
            health_status["checks"]["database_file"] = {
                "status": "unhealthy",
                "message": str(e)
            }

        # 系统信息
        health_status["system"] = {
            "python_version": sys.version,
            "platform": platform.platform()
        }

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["success"] = False
        health_status["error"] = str(e)

    return JSONResponse(
        status_code=200 if health_status["status"] == "healthy" else 503,
        content=health_status
    )


@router.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    base_status = await health_check()
    detailed_status = {"data": base_status.body}

    try:
        expired_count = session_manager.cleanup_expired_sessions()
        detailed_status["data"]["cleanup_info"] = {
            "expired_sessions_cleaned": expired_count,
            "active_sessions": len(session_manager.sessions)
        }

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
            users_by_role = dict(cursor.fetchall())
            detailed_status["data"]["database_stats"] = {
                "total_users": total_users,
                "users_by_role": users_by_role
            }

        detailed_status["data"]["environment"] = {
            "cwd": os.getcwd(),
            "debug": os.getenv("DEBUG", "false").lower() == "true"
        }
    except Exception as e:
        detailed_status["data"]["detailed_check_error"] = str(e)

    return JSONResponse(content=detailed_status)


@router.get("/ready")
async def readiness_check():
    """就绪检查"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")

        if not Config.TEMPLATES_DIR.exists():
            return JSONResponse(
                status_code=503,
                content={"ready": False, "message": f"模板目录不存在"}
            )

        return JSONResponse(
            status_code=200,
            content={"ready": True, "message": "应用已就绪"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "message": str(e)}
        )


@router.get("/alive")
async def liveness_check():
    """存活检查"""
    return JSONResponse(
        status_code=200,
        content={"alive": True, "timestamp": datetime.now().isoformat()}
    )


@router.get("/metrics")
async def metrics():
    """应用指标"""
    try:
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "sessions": {
                "active": len(session_manager.sessions),
                "expired_last_cleanup": session_manager.cleanup_expired_sessions()
            }
        }

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            metrics_data["users"] = {"total": cursor.fetchone()[0]}

        return JSONResponse(content=metrics_data)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.delete("/api/admin/clear-sessions")
async def clear_all_sessions():
    """清空所有会话（仅开发环境）"""
    if os.getenv("DEBUG", "false").lower() == "true":
        cleared_count = session_manager.clear_all_sessions()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "cleared_count": cleared_count}
        )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"success": False, "message": "仅开发环境可用"}
    )