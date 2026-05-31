# 研究生组会管理系统

一个面向实验室研究团队的组会管理平台，支持组会安排、材料提交、文献管理、研究进展跟踪等功能。

## 功能模块

### 用户认证
- 用户注册与登录（支持管理员/导师/学生三级角色）
- 会话管理与自动续期
- 密码修改与账户安全

### 组会管理
| 模块 | 功能 |
|------|------|
| **工作台** | 数据概览、即将到来的组会、最近材料、文献库、研究进展 |
| **组会安排** | 日历/列表/卡片视图、创建/编辑/删除组会、分配汇报人、材料状态跟踪 |
| **汇报材料** | 上传/管理汇报材料、材料状态跟踪、权限控制 |
| **组会记录** | 历史组会纪要、Markdown 编辑、材料查看、汇报人分组显示 |

### 资源管理
| 模块 | 功能 |
|------|------|
| **学术文献** | 团队文献库、个人文献库、文献分享、标签管理、阅读状态 |
| **共享资料** | 文件上传/下载、权限控制、文件预览、按汇报人分组显示材料 |
| **研究任务** | 任务创建/分配、进度跟踪、状态管理 |

### 团队管理
| 模块 | 功能 |
|------|------|
| **成员管理** | 用户列表、角色分配、成员信息管理 |
| **学术工具** | 学术资源链接、工具推荐 |
| **研究进展** | 进展提交、导师反馈、进度统计、附件上传/删除 |

### 个人中心
| 模块 | 功能 |
|------|------|
| **个人资料** | 用户信息编辑、头像设置 |
| **修改密码** | 安全密码修改 |
| **设置** | 个人偏好设置 |

## 技术栈

### 前端
| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.4 | 渐进式 JavaScript 框架 |
| Vue Router | 4.6 | 官方路由管理器 |
| Pinia | 2.1 | 状态管理库 |
| Tailwind CSS | 3.4 | 实用优先的 CSS 框架 |
| Vite | 5.0 | 下一代前端构建工具 |
| Axios | 1.6 | HTTP 请求库 |
| Marked | 18.0 | Markdown 解析库 |

### 后端
| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.11 | 编程语言 |
| FastAPI | 0.136 | 现代高性能 Web 框架 |
| SQLite | 3 | 轻量级数据库 |
| Uvicorn | 0.48 | ASGI 服务器 |
| Loguru | 0.7 | 日志管理 |
| bcrypt | 5.0 | 密码加密 |
| Pydantic | 2.13 | 数据验证 |

## 项目结构

```
group-share-project/
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── views/              # 页面组件 (15个)
│   │   │   ├── Dashboard.vue   # 工作台
│   │   │   ├── MeetingSchedule.vue  # 组会安排
│   │   │   ├── ReportMaterials.vue  # 汇报材料
│   │   │   ├── MeetingRecord.vue    # 组会记录
│   │   │   ├── PaperDatabase.vue    # 学术文献
│   │   │   ├── ShareFile.vue        # 共享资料
│   │   │   ├── ResearchTasks.vue    # 研究任务
│   │   │   ├── UserManagement.vue   # 成员管理
│   │   │   ├── AcademicTools.vue    # 学术工具
│   │   │   ├── ResearchProgress.vue # 研究进展
│   │   │   ├── UserProfile.vue      # 个人资料
│   │   │   ├── EditPassword.vue     # 修改密码
│   │   │   ├── Settings.vue         # 设置
│   │   │   ├── Login.vue            # 登录
│   │   │   └── Register.vue         # 注册
│   │   ├── components/          # 公共组件
│   │   │   ├── Header.vue       # 顶部导航栏
│   │   │   ├── Sidebar.vue      # 侧边栏菜单
│   │   │   ├── MenuItem.vue     # 菜单项
│   │   │   ├── Toast.vue        # 消息提示
│   │   │   ├── MeetingCard.vue  # 组会卡片
│   │   │   ├── MeetingCalendar.vue # 日历视图
│   │   │   ├── MeetingGrid.vue  # 卡片视图
│   │   │   ├── MeetingList.vue  # 列表视图
│   │   │   ├── MeetingModal.vue # 创建/编辑弹窗
│   │   │   ├── MeetingDetail.vue # 详情弹窗
│   │   │   ├── StatCard.vue     # 统计卡片
│   │   │   ├── FileList.vue     # 文件列表
│   │   │   ├── PaperList.vue    # 文献列表
│   │   │   └── ProgressTable.vue # 进展表格
│   │   ├── api/                 # API 接口
│   │   │   ├── dashboard.js     # 工作台 API
│   │   │   ├── meeting.js       # 组会 API
│   │   │   ├── paper.js         # 文献 API
│   │   │   ├── research_progress.js # 进展 API
│   │   │   └── record.js        # 记录 API
│   │   ├── stores/              # Pinia 状态
│   │   │   └── user.js          # 用户状态
│   │   ├── router/              # 路由配置
│   │   │   └── index.js         # 路由定义
│   │   ├── config/              # 配置文件
│   │   ├── App.vue              # 应用入口
│   │   └── main.js              # 启动文件
│   ├── public/                  # 静态资源
│   ├── index.html               # HTML 入口
│   ├── package.json             # NPM 配置
│   ├── vite.config.js           # Vite 配置
│   ├── tailwind.config.js       # Tailwind 配置
│   └── postcss.config.js        # PostCSS 配置
│
├── backend/                     # FastAPI 后端
│   ├── app.py                   # 应用入口
│   ├── config.py                # 配置文件
│   ├── routers/                 # API 路由 (13个)
│   │   ├── auth_router.py       # 认证路由
│   │   ├── dashboard_router.py  # 工作台路由
│   │   ├── health_router.py     # 健康检查
│   │   ├── meeting_material_router.py  # 组会材料
│   │   ├── meeting_schedule_router.py  # 组会安排
│   │   ├── member_management_router.py # 成员管理
│   │   ├── message_system_router.py    # 消息系统
│   │   ├── page_router.py       # 页面路由
│   │   ├── paper_router.py      # 学术文献
│   │   ├── research_progress_router.py # 研究进展
│   │   ├── research_tasks_router.py    # 研究任务
│   │   ├── shared_resources_router.py  # 共享资源
│   │   └── user_profile_router.py      # 用户资料
│   ├── services/                # 业务逻辑层
│   │   ├── auth_service.py      # 认证服务
│   │   ├── meeting_service.py   # 组会服务
│   │   ├── paper_service.py     # 文献服务
│   │   ├── shared_resources_service.py # 共享资源服务
│   │   ├── research_progress_service.py # 研究进展服务
│   │   └── user_service.py      # 用户服务
│   ├── repositories/            # 数据访问层
│   │   ├── meeting_repository.py # 组会数据
│   │   ├── paper_repository.py  # 文献数据
│   │   ├── shared_resources_repository.py # 共享资源数据
│   │   └── user_repository.py   # 用户数据
│   ├── models/                  # 数据模型
│   │   ├── user.py              # 用户模型
│   │   ├── file.py              # 文件模型
│   │   └── paper.py             # 文献模型
│   ├── dependencies/            # 依赖注入
│   │   └── auth.py              # 认证依赖
│   └── database/                # 数据库配置
│       ├── connection.py        # 数据库连接
│       └── app.db               # SQLite 数据库
│
├── uploads/                     # 上传文件目录
│   ├── share_files/            # 共享资料
│   ├── papers/                  # 学术文献
│   ├── meeting_files/          # 组会材料
│   ├── progress_files/         # 研究进展附件
│   └── avatars/                 # 用户头像
│
├── docs/                        # 文档目录
├── requirements.txt             # Python 依赖
├── CLAUDE.md                    # 开发规范
├── Dockerfile                   # Docker 镜像
├── docker-compose.yml           # Docker 编排
└── README.md                    # 项目说明
```

## 快速启动

### 环境要求
- Python 3.11+
- Node.js 18+
- SQLite 3

### 后端启动

```bash
# 方式一：使用 uv (推荐)
pip install uv
uv sync

# 方式二：传统 pip
pip install -r requirements.txt

# 启动服务
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8088
```

后端服务将在 `http://localhost:8088` 运行。

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式启动
npm run dev

# 生产构建
npm run build

# 预览生产版本
npm run preview
```

前端开发服务将在 `http://localhost:3001` 运行。

### Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

访问 `http://localhost:8088` 即可使用系统。

**默认管理员账号：** `admin` / `admin`

## 用户角色权限

| 角色 | 权限说明 |
|------|----------|
| **管理员 (admin)** | 全部功能、成员管理、系统设置、所有数据操作 |
| **导师 (teacher)** | 组会管理、材料审阅、进展反馈、查看所有学生数据 |
| **学生 (student)** | 材料提交、进展提交、个人文献管理、查看团队文献 |

## API 文档

启动后端服务后访问：
- **Swagger UI:** http://localhost:8088/docs
- **ReDoc:** http://localhost:8088/redoc

### 主要 API 端点

#### 认证 `/api/auth`
- `POST /login` - 登录
- `POST /register` - 注册
- `POST /logout` - 退出登录
- `GET /me` - 获取当前用户信息

#### 组会管理 `/api/meetings`
- `GET /` - 组会列表（支持分页、筛选）
- `POST /` - 创建组会
- `GET /{id}` - 组会详情
- `PUT /{id}` - 更新组会
- `DELETE /{id}` - 删除组会
- `GET /stats` - 统计数据
- `GET /{id}/presenters` - 汇报人列表
- `POST /{id}/presenters` - 添加汇报人

#### 汇报材料 `/api/materials`
- `GET /{presenter_id}/files` - 获取汇报人材料
- `POST /{presenter_id}/files` - 上传材料
- `GET /meeting_files/{file_id}/download` - 下载材料

#### 学术文献 `/api/paper_database`
- `GET /` - 文献列表
- `POST /` - 上传文献
- `GET /{id}` - 文献详情
- `POST /{id}/add-to-personal` - 添加到个人库
- `POST /{id}/share-to-team` - 分享到团队
- `PUT /{id}/tags` - 设置标签

#### 共享资料 `/api/files`
- `POST /upload` - 上传文件
- `GET /` - 文件列表
- `GET /{file_id}` - 文件详情
- `DELETE /{file_id}` - 删除文件
- `DELETE /by_filename/{filename}` - 按文件名删除
- `GET /{file_id}/download` - 下载文件

#### 研究进展 `/api/research_progress`
- `GET /my` - 我的进展列表
- `POST /submit` - 提交进展
- `GET /{id}` - 进展详情
- `PUT /{id}` - 更新进展
- `GET /team` - 团队进展
- `GET /stats` - 进展统计
- `POST /{id}/feedback` - 导师反馈

## 数据库表结构

| 表名 | 功能 |
|------|------|
| users | 用户信息（角色、头像、研究方向） |
| meetings | 组会信息（标题、时间、地点、状态） |
| meeting_presenters | 汇报人关联（用户、时长、材料状态） |
| meeting_files | 组会材料（文件路径、类型、大小） |
| research_tasks | 研究任务（任务名、负责人、进度） |
| papers | 团队文献（标题、作者、DOI、PDF） |
| personal_papers | 个人文献（关联团队文献） |
| tags | 标签（文献分类） |
| paper_user_relations | 文献-用户关系（收藏、阅读状态） |
| files | 共享文件（上传者、权限、哈希） |
| research_progress | 研究进展（周报、附件、反馈） |
| progress_settings | 提交周期设置（提醒天数） |
| messages | 消息留言（类型、内容） |

## 开发规范

详见 [CLAUDE.md](./CLAUDE.md)

### 后端分层架构
- **routers/** - 只处理 HTTP 请求和响应，不写任何业务逻辑
- **services/** - 所有业务逻辑写在这里
- **repositories/** - 只做数据库 CRUD，不写业务判断

### 前端分层架构
- **views/** - 页面组件，处理页面逻辑
- **components/** - 可复用 UI 组件
- **api/** - API 请求封装
- **stores/** - 全局状态管理

### 命名规范
- 文件名：`snake_case + 层级后缀`，如 `meeting_service.py`
- 类名：`PascalCase + 层级后缀`，如 `MeetingService`
- 函数名：`snake_case`，如 `get_meeting_by_id`

### 开发规则
- 禁止在 router 层直接操作数据库
- 禁止在 repository 层写业务判断逻辑
- 新增模块必须同时创建三层文件

## 版本历史

| 版本 | 功能更新 |
|------|----------|
| v0.0.1 | 基础架构搭建、用户认证 |
| v0.0.2 | 组会管理、汇报材料 |
| v0.0.3 | 学术文献、共享资料、研究任务 |
| v0.0.4 | 研究进展、分页优化、Vue 前端重构 |

## 作者

wjg

## License

MIT License