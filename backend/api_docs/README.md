# API 文档索引

本目录包含各模块的 API 接口文档。

## 文档列表

| 文件 | 模块 | 端点数量 |
|------|------|----------|
| [auth_api.md](auth_api.md) | 认证模块 | 7 |
| [paper_api.md](paper_api.md) | 文献模块 | 12 |
| [progress_api.md](progress_api.md) | 研究进展模块 | 10 |
| [task_api.md](task_api.md) | 研究任务模块 | 7 |

---

## API 基础信息

- **Base URL:** `http://localhost:8081/api`
- **认证方式:** Session Cookie
- **响应格式:** JSON

---

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

### 失败响应
```json
{
  "success": false,
  "message": "错误信息",
  "error": "ERROR_CODE"
}
```

### 错误代码

| 错误代码 | 说明 | HTTP 状态码 |
|----------|------|-------------|
| `INVALID_CREDENTIALS` | 用户名或密码错误 | 401 |
| `FORBIDDEN` | 无权限访问 | 403 |
| `NOT_FOUND` | 资源不存在 | 404 |
| `VALIDATION_ERROR` | 参数验证失败 | 400 |
| `DUPLICATE_ENTRY` | 数据重复 | 409 |
| `INTERNAL_ERROR` | 服务器内部错误 | 500 |

---

## 用户角色

| 角色 | 说明 | 典型权限 |
|------|------|----------|
| `admin` | 管理员 | 所有模块完全权限 |
| `teacher` | 导师 | 管理学生、查看团队进展、分配任务 |
| `student` | 学生 | 提交进展、管理个人任务、上传文献 |

---

## 项目架构

```
backend/
├── routers/           # API 端点（仅处理请求响应）
│   ├── auth_router.py
│   ├── paper_router.py
│   ├── progress_router.py
│   ├── task_router.py
│   ├── meeting_router.py
│   ├── member_router.py
│   ├── user_router.py
│   ├── file_router.py
│   └── message_router.py
│
├── services/          # 业务逻辑层
│   ├── auth_service.py
│   ├── paper_service.py
│   ├── research_progress_service.py
│   ├── task_service.py
│   └── ...
│
├── repositories/      # 数据访问层
│   ├── auth_repository.py
│   ├── paper_repository.py
│   ├── progress_repository.py
│   ├── task_repository.py
│   └── ...
│
├── dependencies/      # 依赖注入
│   └── auth.py        # get_current_user 认证依赖
│
├── models/            # 数据模型
│   ├── user.py
│   ├── paper.py
│   ├── research_progress.py
│   └── ...
│
├── database/          # 数据库连接
│   └── connection.py  # get_db(), init_db()
│
├── api_docs/          # API 文档目录
│   └── ...
│
└── app.py             # 应用入口
```

---

## 分层职责

| 层 | 职责 | 代码量 |
|----|------|--------|
| Router | 只处理 HTTP 请求和响应，一行代码调用 Service | 最少 |
| Service | 所有业务逻辑、权限校验、数据组装 | 中等 |
| Repository | 只做数据库 CRUD，不写业务判断 | 较多 SQL |

---

## 开发规范

### 命名规范
- 文件名：`snake_case + _router/_service/_repository`
- 类名：`PascalCase + Router/Service/Repository`
- 函数名：`snake_case`

### 返回格式
- Service 层统一返回 `{status_code: int, content: dict}`
- Router 层使用 `JSONResponse` 返回

### 新增模块
1. 创建 Repository 文件（CRUD）
2. 创建 Service 文件（业务逻辑 + API 方法）
3. 创建 Router 文件（端点）
4. 在 `repositories/__init__.py` 导出
5. 在 `app.py` 注册路由