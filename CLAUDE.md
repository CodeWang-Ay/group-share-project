# 项目架构规范

## 技术栈
- Python 3.11 + FastAPI + SQLite

## 分层规范
- routers/      只处理 HTTP 请求和响应，不写任何业务逻辑
- services/     所有业务逻辑写在这里
- repositories/ 只做数据库 CRUD，不写业务判断

## 命名规范
- 文件名：snake_case + 层级后缀，如 user_service.py
- 类名：PascalCase + 层级后缀，如 UserService
- 函数名：snake_case，如 get_user_by_id

## 开发规则
- 禁止在 router 层直接操作数据库
- 禁止在 repository 层写业务判断逻辑
- 新增模块必须同时创建三层文件

# 例如
app/
├── routers/
│   ├── __init__.py
│   ├── user_router.py
│   └── order_router.py
│
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   └── order_service.py
│
├── repositories/
│   ├── __init__.py
│   ├── user_repository.py
│   └── order_repository.py
│
├── schemas/
│   ├── __init__.py
│   ├── user_schema.py        # UserCreate, UserUpdate, UserResponse
│   └── order_schema.py       # OrderCreate, OrderUpdate, OrderResponse
│
├── models/
│   ├── __init__.py
│   ├── user_model.py         # User (ORM 表映射)
│   └── order_model.py        # Order (ORM 表映射)
│
└── dependencies/
    ├── __init__.py
    ├── auth.py               # 鉴权依赖（功能命名，不加层级后缀）
    └── pagination.py         # 分页依赖