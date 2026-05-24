"""
================================================================================
文献业务服务模块 (services/paper_service.py)
================================================================================

模块名称: backend/services/paper_service.py
功能描述: 文献业务逻辑处理

职责:
    - 所有业务逻辑写在这里
    - 调用 PaperRepository 进行数据操作
    - 不直接操作数据库

作者: wjg
创建日期: 2026-05-24
================================================================================
"""
import os
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

from repositories.paper_repository import PaperRepository


class PaperService:
    """文献业务服务类"""

    # PDF上传目录
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "papers"
    PERSONAL_UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "personal_papers"

    # 最大文件大小 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    @classmethod
    def init_upload_directory(cls) -> None:
        """初始化PDF上传目录"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.PERSONAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def init_personal_directory(cls, user_id: int) -> Path:
        """初始化用户个人文献目录"""
        user_dir = cls.PERSONAL_UPLOAD_DIR / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    @classmethod
    def get_papers(cls, user_id: int, keyword: Optional[str] = None, tag: Optional[str] = None,
                   status: Optional[str] = None, year: Optional[int] = None,
                   starred: Optional[bool] = None, library_type: Optional[str] = None,
                   sort: str = 'newest', limit: int = 20, offset: int = 0) -> Tuple[List[Dict], int]:
        """获取文献列表"""
        filters = {'keyword': keyword, 'tag': tag, 'status': status, 'year': year, 'sort': sort}

        if library_type == 'private' or library_type == 'personal':
            papers = PaperRepository.get_personal_paper_list(user_id, filters, limit, offset)
            total = PaperRepository.get_personal_paper_count(user_id, filters)
            # 添加标签信息
            for p in papers:
                p['tags'] = PaperRepository.get_personal_paper_tags(p['id'])
                p['uploader_name'] = PaperRepository.get_user_name(p['owner_user_id'])
                p['library_type'] = 'private'
        else:
            papers = PaperRepository.get_paper_list(filters, limit, offset)
            total = PaperRepository.get_paper_count(filters)
            # 添加标签和关系信息
            for p in papers:
                p['tags'] = PaperRepository.get_paper_tags(p['id'])
                p['uploader_name'] = PaperRepository.get_user_name(p['uploader_id'])
                p['library_type'] = 'public'
                relation = PaperRepository.get_paper_user_relation(p['id'], user_id, 'public')
                p['is_starred'] = relation.get('is_starred', 0) if relation else 0
                p['read_status'] = relation.get('read_status', 'unread') if relation else 'unread'

        return papers, total

    @classmethod
    def get_stats(cls, user_id: int, library_type: Optional[str] = None) -> Dict[str, Any]:
        """获取文献统计"""
        return PaperRepository.get_paper_stats(user_id, library_type)

    @classmethod
    def get_tags(cls) -> List[Any]:
        """获取标签列表"""
        from models.paper import Tag
        tags_data = PaperRepository.get_tags()
        return [Tag.from_dict(t) for t in tags_data]

    @classmethod
    def create_paper(cls, title: str, pdf_data: bytes, original_filename: str,
                    uploader_id: int, authors: Optional[str] = None, year: Optional[int] = None,
                    journal: Optional[str] = None, doi: Optional[str] = None, abstract: Optional[str] = None,
                    arxiv_link: Optional[str] = None, semantic_scholar_link: Optional[str] = None,
                    tags: Optional[List[str]] = None, library_type: str = 'public') -> Tuple[Optional[Dict], Optional[str]]:
        """上传新文献"""
        cls.init_upload_directory()

        if len(pdf_data) > cls.MAX_FILE_SIZE:
            return None, f"文件大小超过限制（最大 {cls.MAX_FILE_SIZE // (1024*1024)} MB）"
        if not original_filename.lower().endswith('.pdf'):
            return None, "只支持PDF文件"

        sha256_hash = hashlib.sha256(pdf_data).hexdigest()

        # 去重校验
        dup_library = 'team' if library_type == 'public' else 'personal'
        duplicate = PaperRepository.check_duplicate(dup_library, uploader_id, sha256_hash, doi, title, authors)
        if duplicate:
            return None, f"文献已存在：{duplicate['title']}"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if library_type == 'public':
            filename = f"{timestamp}_{original_filename}"
            file_path = cls.UPLOAD_DIR / filename
            with open(file_path, 'wb') as f:
                f.write(pdf_data)

            paper_data = {
                'title': title, 'authors': authors, 'year': year, 'journal': journal,
                'doi': doi, 'abstract': abstract, 'arxiv_link': arxiv_link,
                'semantic_scholar_link': semantic_scholar_link,
                'pdf_path': str(file_path),
                'file_hash': sha256_hash, 'pdf_size': len(pdf_data), 'uploader_id': uploader_id
            }
            paper_id = PaperRepository.create_paper(paper_data)

            PaperRepository.create_paper_user_relation({
                'paper_id': paper_id, 'user_id': uploader_id,
                'library_type': 'public', 'relation_type': 'team_view'
            })

            if tags:
                cls._process_tags(paper_id, tags, uploader_id, 'public')

            return {'id': paper_id, 'title': title, 'pdf_path': str(file_path),
                    'pdf_size': len(pdf_data), 'library_type': 'public'}, None
        else:
            user_dir = cls.init_personal_directory(uploader_id)
            filename = f"{timestamp}_{original_filename}"
            file_path = user_dir / filename
            with open(file_path, 'wb') as f:
                f.write(pdf_data)

            paper_data = {
                'title': title, 'authors': authors, 'year': year, 'journal': journal,
                'doi': doi, 'abstract': abstract, 'arxiv_link': arxiv_link,
                'semantic_scholar_link': semantic_scholar_link,
                'pdf_path': str(file_path),
                'file_hash': sha256_hash, 'pdf_size': len(pdf_data),
                'owner_user_id': uploader_id, 'source_paper_id': None
            }
            paper_id = PaperRepository.create_personal_paper(paper_data)

            if tags:
                cls._process_tags(paper_id, tags, uploader_id, 'private')

            return {'id': paper_id, 'title': title, 'pdf_path': str(file_path),
                    'pdf_size': len(pdf_data), 'library_type': 'private'}, None

    @classmethod
    def _process_tags(cls, paper_id: int, tags: Optional[List[str]], user_id: int, library_type: str) -> None:
        """处理标签"""
        if not tags:
            return
        for tag_name in tags:
            tag_id = PaperRepository.get_or_create_tag(tag_name, user_id)
            if library_type == 'public':
                PaperRepository.add_paper_tag(paper_id, tag_id)
            else:
                PaperRepository.add_personal_paper_tag(paper_id, tag_id)

    @classmethod
    def get_paper_by_id(cls, paper_id: int, user_id: int, library_type: str) -> Optional[Dict]:
        """获取文献详情"""
        if library_type == 'public':
            paper = PaperRepository.get_paper_by_id(paper_id)
            if paper:
                paper['tags'] = PaperRepository.get_paper_tags(paper_id)
                paper['uploader_name'] = PaperRepository.get_user_name(paper['uploader_id'])
                relation = PaperRepository.get_paper_user_relation(paper_id, user_id, 'public')
                paper['is_starred'] = relation.get('is_starred', 0) if relation else 0
                paper['read_status'] = relation.get('read_status', 'unread') if relation else 'unread'
                paper['library_type'] = 'public'
        else:
            paper = PaperRepository.get_personal_paper_by_id(paper_id)
            if paper:
                paper['tags'] = PaperRepository.get_personal_paper_tags(paper_id)
                paper['uploader_name'] = PaperRepository.get_user_name(paper['owner_user_id'])
                paper['library_type'] = 'private'
        return paper

    @classmethod
    def toggle_star(cls, paper_id: int, user_id: int, library_type: str) -> bool:
        """收藏/取消收藏"""
        relation = PaperRepository.get_paper_user_relation(paper_id, user_id, library_type)
        current_star = relation.get('is_starred', 0) if relation else 0
        new_star = 1 if current_star == 0 else 0
        return PaperRepository.toggle_star(paper_id, user_id, library_type, new_star)

    @classmethod
    def update_status(cls, paper_id: int, user_id: int, status: str, library_type: str) -> bool:
        """更新阅读状态"""
        return PaperRepository.update_read_status(paper_id, user_id, status, library_type)

    @classmethod
    def update_paper(cls, paper_id: int, user_id: int, title: Optional[str] = None,
                     authors: Optional[str] = None, year: Optional[int] = None,
                     journal: Optional[str] = None, doi: Optional[str] = None,
                     abstract: Optional[str] = None, arxiv_link: Optional[str] = None,
                     semantic_scholar_link: Optional[str] = None, tags: Optional[List[str]] = None,
                     read_status: Optional[str] = None, library_type: str = 'public') -> Tuple[Optional[Dict], Optional[str]]:
        """更新文献"""
        update_data = {}
        for field in ['title', 'authors', 'year', 'journal', 'doi', 'abstract', 'arxiv_link', 'semantic_scholar_link', 'read_status']:
            if locals().get(field) is not None:
                update_data[field] = locals().get(field)

        if library_type == 'public':
            # 权限检查：团队文献需要是上传者或管理员
            paper = PaperRepository.get_paper_by_id(paper_id)
            if not paper:
                return None, "文献不存在"
            if paper['uploader_id'] != user_id:
                return None, "只有上传者可以修改团队文献"
            PaperRepository.update_paper(paper_id, update_data)
        else:
            paper = PaperRepository.get_personal_paper_by_id(paper_id)
            if not paper:
                return None, "文献不存在"
            if paper['owner_user_id'] != user_id:
                return None, "只有本人可以修改个人文献"
            PaperRepository.update_personal_paper(paper_id, update_data)

        if tags:
            cls._process_tags(paper_id, tags, user_id, library_type)

        return cls.get_paper_by_id(paper_id, user_id, library_type), None

    @classmethod
    def batch_star(cls, paper_ids: List[int], user_id: int, star: bool, library_type: str) -> int:
        """批量收藏"""
        count = 0
        for paper_id in paper_ids:
            if PaperRepository.toggle_star(paper_id, user_id, library_type, star):
                count += 1
        return count

    @classmethod
    def batch_delete(cls, paper_ids: List[int], user_id: int, user_role: str, library_type: str) -> Dict:
        """批量删除"""
        deleted = 0
        failed = 0
        for paper_id in paper_ids:
            if cls.delete_paper(paper_id, user_id, user_role, library_type).get('success'):
                deleted += 1
            else:
                failed += 1
        return {'success': True, 'deleted': deleted, 'failed': failed}

    @classmethod
    def delete_paper(cls, paper_id: int, user_id: int, user_role: str, library_type: str) -> Dict:
        """删除文献"""
        if library_type == 'public':
            paper = PaperRepository.get_paper_by_id(paper_id)
            if not paper:
                return {'success': False, 'message': '文献不存在'}
            if user_role != 'admin' and paper['uploader_id'] != user_id:
                return {'success': False, 'message': '无权限删除'}
            # 删除物理文件
            if os.path.exists(paper['pdf_path']):
                os.remove(paper['pdf_path'])
            PaperRepository.delete_paper(paper_id)
        else:
            paper = PaperRepository.get_personal_paper_by_id(paper_id)
            if not paper:
                return {'success': False, 'message': '文献不存在'}
            if paper['owner_user_id'] != user_id:
                return {'success': False, 'message': '无权限删除'}
            if os.path.exists(paper['pdf_path']):
                os.remove(paper['pdf_path'])
            PaperRepository.delete_personal_paper(paper_id)

        return {'success': True, 'message': '删除成功'}

    @classmethod
    def add_to_personal_library(cls, paper_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """将团队文献添加到个人库"""
        paper = PaperRepository.get_paper_by_id(paper_id)
        if not paper:
            return False, "文献不存在"

        # 检查是否已存在
        duplicate = PaperRepository.check_duplicate('personal', user_id, paper.get('file_hash'),
                                                     paper.get('doi'), paper.get('title'), paper.get('authors'))
        if duplicate:
            return False, "该文献已在个人库中"

        # 复制文件到个人目录
        user_dir = cls.init_personal_directory(user_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 从 pdf_path 提取文件名
        original_filename = os.path.basename(paper['pdf_path'])
        new_filename = f"{timestamp}_{original_filename}"
        new_path = user_dir / new_filename

        if os.path.exists(paper['pdf_path']):
            import shutil
            shutil.copy2(paper['pdf_path'], new_path)
        else:
            return False, "源文件不存在"

        # 创建个人文献记录
        personal_data = {
            'title': paper['title'], 'authors': paper['authors'], 'year': paper['year'],
            'journal': paper['journal'], 'doi': paper['doi'], 'abstract': paper['abstract'],
            'arxiv_link': paper['arxiv_link'], 'semantic_scholar_link': paper['semantic_scholar_link'],
            'pdf_path': str(new_path),
            'file_hash': paper['file_hash'], 'pdf_size': paper['pdf_size'],
            'owner_user_id': user_id, 'source_paper_id': paper_id
        }
        PaperRepository.create_personal_paper(personal_data)

        return True, None

    @classmethod
    def share_to_team(cls, paper_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """将个人文献分享到团队库"""
        paper = PaperRepository.get_personal_paper_by_id(paper_id)
        if not paper:
            return False, "文献不存在"
        if paper['owner_user_id'] != user_id:
            return False, "无权限分享"

        # 检查团队库是否已存在
        duplicate = PaperRepository.check_duplicate('team', user_id, paper.get('file_hash'),
                                                     paper.get('doi'), paper.get('title'), paper.get('authors'))
        if duplicate:
            return False, "该文献已在团队库中"

        # 复制文件到团队目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = os.path.basename(paper['pdf_path'])
        new_filename = f"{timestamp}_{original_filename}"
        new_path = cls.UPLOAD_DIR / new_filename

        if os.path.exists(paper['pdf_path']):
            import shutil
            shutil.copy2(paper['pdf_path'], new_path)
        else:
            return False, "源文件不存在"

        # 创建团队文献记录
        team_data = {
            'title': paper['title'], 'authors': paper['authors'], 'year': paper['year'],
            'journal': paper['journal'], 'doi': paper['doi'], 'abstract': paper['abstract'],
            'arxiv_link': paper['arxiv_link'], 'semantic_scholar_link': paper['semantic_scholar_link'],
            'pdf_path': str(new_path),
            'file_hash': paper['file_hash'], 'pdf_size': paper['pdf_size'],
            'uploader_id': user_id
        }
        PaperRepository.create_paper(team_data)

        return True, "已分享到团队库"

    @classmethod
    def increment_download_count(cls, paper_id: int, library_type: str = 'public') -> bool:
        """增加下载次数"""
        return PaperRepository.increment_download_count(paper_id, library_type)

    @classmethod
    def batch_set_tags(cls, paper_ids: List[int], tag: str, user_id: int, library_type: str) -> Tuple[int, Optional[str]]:
        """批量设置标签"""
        if not tag:
            return 0, "标签不能为空"
        if not paper_ids:
            return 0, "文献ID不能为空"

        count = 0
        tag_id = PaperRepository.get_or_create_tag(tag, user_id)
        for paper_id in paper_ids:
            if library_type == 'public':
                PaperRepository.add_paper_tag(paper_id, tag_id)
            else:
                PaperRepository.add_personal_paper_tag(paper_id, tag_id)
            count += 1
        return count, None

    # ==================== API 异步方法（返回 {status_code, content}） ====================

    async def api_get_list(self, filters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """获取文献列表 API"""
        papers, total = self.get_papers(
            user_id=user_id, keyword=filters.get('keyword'), tag=filters.get('tag'),
            status=filters.get('status'), year=filters.get('year'), starred=filters.get('starred'),
            library_type=filters.get('library_type'), sort=filters.get('sort', 'newest'),
            limit=filters.get('limit', 20), offset=filters.get('offset', 0)
        )
        return {"status_code": 200, "content": {"success": True, "data": papers, "total": total}}

    async def api_get_stats(self, user_id: int, library_type: Optional[str] = None) -> Dict[str, Any]:
        """获取文献统计 API"""
        stats = self.get_stats(user_id=user_id, library_type=library_type)
        return {"status_code": 200, "content": {"success": True, "data": stats}}

    async def api_get_tags(self) -> Dict[str, Any]:
        """获取标签列表 API"""
        tags = self.get_tags()
        return {"status_code": 200, "content": {"success": True, "data": [t.to_dict() for t in tags]}}

    async def api_batch_star(self, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """批量收藏 API"""
        paper_ids = data.get("paper_ids", [])
        star = data.get("star", True)
        library_type = data.get("library_type", "public")
        count = self.batch_star(paper_ids, user_id, star, library_type)
        return {"status_code": 200, "content": {"success": True, "count": count}}

    async def api_add_to_personal(self, paper_id: int, user_id: int) -> Dict[str, Any]:
        """添加到个人库 API"""
        success, error = self.add_to_personal_library(paper_id, user_id)
        if success:
            return {"status_code": 200, "content": {"success": True, "message": "已添加到个人文献库"}}
        return {"status_code": 400, "content": {"success": False, "message": error}}

    async def api_share_to_team(self, paper_id: int, user_id: int) -> Dict[str, Any]:
        """分享到团队库 API"""
        success, message = self.share_to_team(paper_id, user_id)
        if success:
            return {"status_code": 200, "content": {"success": True, "message": message or "已分享到团队文献库"}}
        return {"status_code": 400, "content": {"success": False, "message": message}}

    async def api_batch_set_tags(self, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """批量设置标签 API"""
        paper_ids = data.get("paper_ids", [])
        tag = data.get("tag")
        library_type = data.get("library_type", "public")
        count, error = self.batch_set_tags(paper_ids, tag, user_id, library_type)
        if error:
            return {"status_code": 400, "content": {"success": False, "message": error}}
        return {"status_code": 200, "content": {"success": True, "count": count}}

    async def api_batch_delete(self, data: Dict[str, Any], user_id: int, user_role: str) -> Dict[str, Any]:
        """批量删除 API"""
        paper_ids = data.get("paper_ids", [])
        library_type = data.get("library_type", "public")
        result = self.batch_delete(paper_ids, user_id, user_role, library_type)
        return {"status_code": 200, "content": result}

    async def api_get_detail(self, paper_id: int, user_id: int, library_type: str) -> Dict[str, Any]:
        """获取文献详情 API"""
        paper = self.get_paper_by_id(paper_id, user_id, library_type)
        if not paper:
            return {"status_code": 404, "content": {"success": False, "message": "文献不存在", "error": "NOT_FOUND"}}
        return {"status_code": 200, "content": {"success": True, "data": paper}}

    async def api_upload(self, form: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """上传文献 API"""
        title = form.get("title")
        pdf_file = form.get("pdf")

        if not title:
            return {"status_code": 400, "content": {"success": False, "message": "标题不能为空"}}
        if not pdf_file:
            return {"status_code": 400, "content": {"success": False, "message": "请上传PDF文件"}}

        pdf_data = await pdf_file.read()
        library_type = form.get("library_type", "public")
        year_val = int(form.get("year")) if form.get("year") else None
        tags_str = form.get("tags", "")
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

        paper, error = self.create_paper(
            title=title, pdf_data=pdf_data, original_filename=pdf_file.filename,
            uploader_id=user_id, authors=form.get("authors"), year=year_val,
            journal=form.get("journal"), doi=form.get("doi"), abstract=form.get("abstract"),
            arxiv_link=form.get("arxiv_link"), semantic_scholar_link=form.get("semantic_scholar_link"),
            tags=tags_list, library_type=library_type
        )

        if paper is None and error:
            return {"status_code": 400, "content": {"success": False, "message": error}}
        return {"status_code": 201, "content": {"success": True, "data": paper, "message": error if error else "文献上传成功"}}

    async def api_update(self, paper_id: int, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """更新文献 API"""
        library_type = data.get("library_type", "public")
        year_val = int(data.get("year")) if data.get("year") else None
        tags_str = data.get("tags", "")
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

        paper, error = self.update_paper(
            paper_id=paper_id, user_id=user_id, title=data.get("title"),
            authors=data.get("authors"), year=year_val, journal=data.get("journal"),
            doi=data.get("doi"), abstract=data.get("abstract"), arxiv_link=data.get("arxiv_link"),
            semantic_scholar_link=data.get("semantic_scholar_link"), tags=tags_list,
            read_status=data.get("read_status"), library_type=library_type
        )

        if error:
            return {"status_code": 400, "content": {"success": False, "message": error}}
        return {"status_code": 200, "content": {"success": True, "data": paper, "message": "文献更新成功"}}

    async def api_toggle_star(self, paper_id: int, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """收藏/取消收藏 API"""
        library_type = data.get("library_type", "public") if data else "public"
        success = self.toggle_star(paper_id, user_id, library_type)
        return {"status_code": 200, "content": {"success": success}}

    async def api_update_status(self, paper_id: int, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """更新阅读状态 API"""
        status_val = data.get("status")
        library_type = data.get("library_type", "public")
        if not status_val:
            return {"status_code": 400, "content": {"success": False, "message": "状态不能为空"}}
        success = self.update_status(paper_id, user_id, status_val, library_type)
        return {"status_code": 200, "content": {"success": success}}

    async def api_delete(self, paper_id: int, data: Dict[str, Any], user_id: int, user_role: str) -> Dict[str, Any]:
        """删除文献 API"""
        library_type = data.get("library_type", "public") if data else "public"
        result = self.delete_paper(paper_id, user_id, user_role, library_type)
        return {"status_code": 200, "content": result}

    async def api_download(self, paper_id: int, user_id: int, library_type: str) -> Dict[str, Any]:
        """下载文献 API"""
        paper = self.get_paper_by_id(paper_id, user_id, library_type)
        if not paper:
            return {"status_code": 404, "content": {"success": False, "message": "文献不存在", "error": "NOT_FOUND"}, "error": True}

        pdf_path = paper.get('pdf_path')
        if not pdf_path or not os.path.exists(pdf_path):
            return {"status_code": 404, "content": {"success": False, "message": "PDF文件不存在"}, "error": True}

        self.increment_download_count(paper_id, library_type)
        return {"status_code": 200, "file_path": pdf_path, "filename": os.path.basename(pdf_path), "media_type": "application/pdf"}