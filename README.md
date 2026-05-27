# 研究生组会管理系统

一个基于 Web 的研究生组会管理与文件共享平台，专为研究实验室设计，用于协调组会、共享研究材料和跟踪学生进度。

## 功能模块

### 用户认证
- 用户注册与登录（支持管理员/导师/学生三级角色）
- 会话管理与自动续期
- 密码修改与账户安全

### 组会管理 (gm_)
- **组会安排** - 创建组会、添加汇报人、设置时间地点
- **汇报材料** - 材料上传、审核、参会确认
- **组会记录** - 会议纪要、讨论记录

### 资源管理 (rm_)
- **学术文献** - 团队文献库、个人文献库、收藏、阅读状态、标签分类
- **共享资料** - 文件上传、下载、预览、权限管理
- **研究任务** - 任务分配、进度跟踪、逾期提醒

### 团队管理 (tm_)
- **成员管理** - 成员列表、角色管理、批量操作
- **研究进展** - 周期性进展提交、导师反馈、进度预警
- **学术工具** - 学术网站链接汇总

### 工作台
- 数据统计概览
- 即将到来的组会
- 最近提交的材料和文献

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 | SQLite |
| 模板引擎 | Jinja2 |
| 前端样式 | Tailwind CSS |
| 图标库 | Font Awesome 4.7 |

## 项目架构

遵循分层架构设计：

```
backend/
├── routers/        # HTTP 请求处理
├── services/       # 业务逻辑层
├── repositories/   # 数据库 CRUD
├── models/         # 数据模型
├── schemas/        # Pydantic 数据验证
├── dependencies/   # 依赖注入（认证、分页）
└── database/       # 数据库连接与初始化
templates/          # HTML 模板
uploads/            # 上传文件存储
```

## 快速启动

### 方式一：本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
cd backend
python app.py
```

访问 http://localhost:8081 即可使用系统。

默认管理员账号：`admin` / `admin`

### 方式二：Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8081/docs
- ReDoc: http://localhost:8081/redoc

## 环境要求

- Python 3.11+
- SQLite 3
- Docker (可选，用于容器化部署)

## 主要依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| fastapi | 0.104.1 | Web 框架 |
| uvicorn | 0.24.0 | ASGI 服务器 |
| jinja2 | 3.1.2 | 模板引擎 |
| bcrypt | 4.1.2 | 密码哈希 |
| loguru | 0.7.2 | 日志管理 |
| aiofiles | 23.2.1 | 异步文件操作 |

## 数据库表结构

系统包含 14 张数据表：

| 表名 | 功能 |
|------|------|
| users | 用户信息 |
| meetings | 组会信息 |
| meeting_presenters | 汇报人关联 |
| meeting_files | 组会材料 |
| research_tasks | 研究任务 |
| papers | 团队文献 |
| personal_papers | 个人文献 |
| tags | 标签 |
| paper_user_relations | 文献-用户关系 |
| paper_tags | 文献-标签关联 |
| files | 共享文件 |
| research_progress | 研究进展 |
| progress_settings | 提交周期设置 |
| messages | 消息留言 |

## 开发规范

详见 [CLAUDE.md](./CLAUDE.md)

- 文件名：snake_case + 层级后缀
- 类名：PascalCase + 层级后缀
- 函数名：snake_case
- 三层分离：Router → Service → Repository

## License

MIT License