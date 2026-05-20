# 研究生组会文件共享系统

一个基于 Web 的研究生组会管理与文件共享平台，专为研究实验室设计，用于协调组会、共享研究材料和跟踪学生进度。

## 功能模块

### 用户管理
- 用户注册与登录（支持老师/学生角色）
- 个人资料管理与头像上传
- 密码修改与账户设置
- 成员管理（管理员权限）

### 组会管理 (gm_)
- **组会安排** - 创建和管理组会日程
- **组会记录** - 记录组会内容与讨论
- **汇报材料** - 上传和管理汇报演示文稿

### 资源管理 (rm_)
- **共享文件** - 文件上传、下载、分享
- **文献库** - 论文文献管理与分类
- **研究任务** - 研究任务分配与跟踪

### 团队管理 (tm_)
- **研究进展** - 学生汇报研究进度
- **成员管理** - 团队成员信息维护
- **学术网站** - 学术主页管理

## 技术栈

- **后端**: FastAPI + Python
- **前端**: HTML5 + Tailwind CSS + JavaScript
- **数据库**: SQLite
- **模板引擎**: Jinja2

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
cd backend
python main.py
```

访问 http://localhost:8000 即可使用系统。

## 目录结构

```
├── backend/           # FastAPI 后端服务
│   ├── main.py        # 应用入口
│   ├── models/        # 数据模型
│   ├── services/      # 业务服务
│   └── database/      # 数据库连接
├── templates/         # HTML 模板文件
├── uploads/           # 上传文件存储
└── docs/              # 文档目录
```

## API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc