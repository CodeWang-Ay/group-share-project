# 文献模块 API 文档

## 模块概述

文献模块提供学术文献的上传、管理、收藏、阅读状态追踪等功能，支持团队库和个人库。

## 端点列表

| 端点 | 方法 | 功能 | 需要认证 |
|------|------|------|----------|
| `/api/paper_database/` | GET | 获取文献列表 | 是 |
| `/api/paper_database/upload` | POST | 上传文献 | 是 |
| `/api/paper_database/{id}` | GET | 获取文献详情 | 是 |
| `/api/paper_database/{id}` | PUT | 更新文献信息 | 是 |
| `/api/paper_database/{id}` | DELETE | 删除文献 | 是 |
| `/api/paper_database/{id}/star` | POST | 收藏/取消收藏 | 是 |
| `/api/paper_database/{id}/read-status` | PUT | 更新阅读状态 | 是 |
| `/api/paper_database/{id}/download` | GET | 下载文献 | 是 |
| `/api/paper_database/tags` | GET | 获取标签列表 | 是 |
| `/api/paper_database/stats` | GET | 获取统计数据 | 是 |
| `/api/paper_database/{id}/save-to-personal` | POST | 保存到个人库 | 是 |
| `/api/paper_database/{id}/share-to-team` | POST | 分享到团队库 | 是 |

---

## 1. 获取文献列表

**端点：** `GET /api/paper_database/`

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `library_type` | string | public（团队库）或 private（个人库） |
| `keyword` | string | 搜索关键词（标题模糊匹配） |
| `tag` | string | 标签筛选 |
| `year` | int | 年份筛选 |
| `sort` | string | newest（最新）或 oldest（最旧） |
| `limit` | int | 每页数量，默认 10 |
| `offset` | int | 偏移量，默认 0 |

**成功响应：**
```json
{
  "success": true,
  "data": {
    "papers": [
      {
        "id": 1,
        "title": "Attention Is All You Need",
        "authors": "Vaswani et al.",
        "year": 2017,
        "journal": "NIPS",
        "doi": null,
        "pdf_path": "/uploads/papers/xxx.pdf",
        "pdf_size": 1024000,
        "download_count": 5,
        "created_at": "2026-05-24T10:00:00",
        "is_starred": false,
        "read_status": "unread",
        "tags": ["Transformer", "NLP"]
      }
    ],
    "pagination": {
      "total": 10,
      "limit": 10,
      "offset": 0,
      "has_more": false
    }
  }
}
```

---

## 2. 上传文献

**端点：** `POST /api/paper_database/upload`

**请求体（multipart/form-data）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | file | PDF 文件 |
| `title` | string | 文献标题 |
| `authors` | string | 作者 |
| `year` | int | 发表年份 |
| `journal` | string | 期刊/会议 |
| `doi` | string | DOI |
| `abstract` | string | 摘要 |
| `library_type` | string | public 或 private |
| `tags` | string | 标签（逗号分隔） |

**成功响应：**
```json
{
  "success": true,
  "message": "文献上传成功",
  "data": {
    "id": 1,
    "title": "Attention Is All You Need",
    "library_type": "public"
  }
}
```

---

## 3. 获取文献详情

**端点：** `GET /api/paper_database/{id}`

**查询参数：**
- `library_type`: public 或 private

**成功响应：**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Attention Is All You Need",
    "authors": "Vaswani et al.",
    "year": 2017,
    "journal": "NIPS",
    "doi": null,
    "abstract": "...",
    "pdf_path": "/uploads/papers/xxx.pdf",
    "pdf_size": 1024000,
    "download_count": 5,
    "is_starred": false,
    "read_status": "unread",
    "tags": ["Transformer", "NLP"],
    "uploader_name": "admin"
  }
}
```

---

## 4. 收藏/取消收藏

**端点：** `POST /api/paper_database/{id}/star`

**查询参数：**
- `library_type`: public 或 private
- `star`: true 或 false

**成功响应：**
```json
{
  "success": true,
  "message": "已收藏"
}
```

---

## 5. 更新阅读状态

**端点：** `PUT /api/paper_database/{id}/read-status`

**查询参数：**
- `library_type`: public 或 private

**请求体：**
```json
{
  "status": "read"
}
```

**阅读状态值：**
- `unread`: 未读
- `reading`: 正在阅读
- `read`: 已读

---

## 6. 下载文献

**端点：** `GET /api/paper_database/{id}/download`

**查询参数：**
- `library_type`: public 或 private

返回 PDF 文件流。

---

## 7. 获取标签列表

**端点：** `GET /api/paper_database/tags`

**成功响应：**
```json
{
  "success": true,
  "data": [
    {"id": 1, "name": "Transformer", "tag_type": "system"},
    {"id": 2, "name": "BERT", "tag_type": "system"},
    {"id": 3, "name": "自定义标签", "tag_type": "custom"}
  ]
}
```

---

## 8. 获取统计数据

**端点：** `GET /api/paper_database/stats`

**查询参数：**
- `library_type`: public 或 private

**成功响应：**
```json
{
  "success": true,
  "data": {
    "total": 10,
    "total_size": 10240000,
    "starred_count": 3
  }
}
```

---

## 文献库类型

| 类型 | 说明 |
|------|------|
| `public` | 团队库，所有成员可见 |
| `private` | 个人库，仅自己可见 |

---

## 去重机制

上传时会自动检测重复文献：
- DOI 匹配
- 文件哈希匹配
- 标题 + 作者组合匹配