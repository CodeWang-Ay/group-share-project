"""
================================================================================
分页依赖模块 (dependencies/pagination.py)
================================================================================

模块名称: backend/dependencies/pagination.py
功能描述: 提供 FastAPI 分页参数依赖注入

主要类:
    - PaginationParams : 分页参数模型

属性:
    - page     : 当前页码（默认 1）
    - per_page : 每页数量（默认 10，可选 5/10/20/50/100）

使用方式:
    from dependencies.pagination import PaginationParams

    @router.get("/list")
    async def get_list(pagination: PaginationParams = Depends()):
        offset = pagination.offset
        limit = pagination.per_page

作者: wjg
创建日期: 2026-05-23
================================================================================
"""
from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    """分页参数模型"""
    page: int = Query(default=1, ge=1, description="当前页码")
    per_page: int = Query(default=10, ge=1, le=100, description="每页数量")

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.per_page

    def validate_per_page(self) -> int:
        """验证每页数量是否在允许范围内"""
        allowed = [5, 10, 20, 50, 100]
        if self.per_page not in allowed:
            return 10
        return self.per_page