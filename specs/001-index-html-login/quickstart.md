# 快速开始指南

## 系统要求

- Python 3.11+
- 现代Web浏览器（Chrome、Firefox、Safari、Edge）

## 安装步骤

### 1. 环境准备

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt
```

### 2. 数据库初始化

```bash
# 进入backend目录
cd backend

# 运行数据库初始化脚本
python -c "from database.connection import init_db; init_db()"
```

### 3. 启动服务

```bash
# 启动后端服务
python main.py

# 服务将在 http://localhost:8000 启动
# API文档可在 http://localhost:8000/docs 查看
```

### 4. 访问前端

```bash
# 在浏览器中打开
# 登录页面: http://localhost:8000/login
# 注册页面: http://localhost:8000/register
# 主页面:   http://localhost:8000/
# 注意：页面通过FastAPI的模板系统提供服务，无需.html后缀
```

## 默认账号

系统预设管理员账号：
- 用户名：`admin`
- 密码：`admin`
- 角色：管理员

## 基本操作

### 管理员登录

1. 访问 `http://localhost:8000/login`
2. 输入用户名：`admin`
3. 输入密码：`admin`
4. 点击登录按钮
5. 成功后跳转到主页面

### 老师注册

1. 访问 `http://localhost:8000/register`
2. 填写用户名（如：`teacher_zhang`）
3. 填写密码（至少6位）
4. 选择角色：`老师`
5. 点击注册按钮
6. 成功后跳转到登录页面

### 学生注册

1. 访问 `http://localhost:8000/register`
2. 填写用户名（如：`student_wang`）
3. 填写密码（至少6位）
4. 选择角色：`学生`
5. 点击注册按钮
6. 成功后跳转到登录页面

## 开发调试

### 查看API文档

启动服务后，访问 `http://localhost:8000/docs` 查看自动生成的API文档。

### 查看数据库

```bash
# 使用sqlite命令查看数据库
sqlite backend/database/users.db

# 查看用户表
SELECT * FROM users;
```

### 日志查看

后端服务运行时会在控制台显示日志信息，包括：
- 请求日志
- 错误信息
- 数据库操作

## 常见问题

### Q: 忘记管理员密码怎么办？
A: 目前不支持密码重置，需要重新初始化数据库。

### Q: 如何修改端口？
A: 修改 `backend/main.py` 中的 `uvicorn.run` 参数。

### Q: 如何添加新用户？
A: 通过注册页面添加老师和学生账号，管理员账号需要在数据库中手动创建。

## 下一步

1. 根据需要修改前端页面样式
2. 添加更多用户管理功能
3. 实现密码重置功能
4. 添加用户权限管理

## 技术支持

如遇到问题，请检查：
1. Python版本是否符合要求
2. 依赖是否正确安装
3. 端口是否被占用
4. 浏览器控制台是否有错误信息