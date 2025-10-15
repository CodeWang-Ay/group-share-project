# 研究生组会文件共享系统 - 快速开始指南

## 系统要求

- **Python 3.11+**
- **现代Web浏览器**（Chrome、Firefox、Safari、Edge）
- **至少 100MB 可用磁盘空间**

## 快速安装

### 方法一：一键安装脚本（推荐）

```bash
# 克隆或下载项目
git clone <repository-url>
cd group-share-project

# 运行安装脚本
./install.sh
```

### 方法二：手动安装

#### 1. 环境准备

```bash
# 创建项目目录
mkdir group-share-project
cd group-share-project

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

#### 2. 安装依赖

```bash
# 安装生产依赖
pip install -r requirements.txt

# 或者安装开发依赖（包含测试工具）
pip install -r requirements-dev.txt
```

#### 3. 数据库初始化

```bash
# 进入后端目录
cd backend

# 运行数据库初始化脚本
python -c "from database.connection import init_db; init_db()"

# 或者使用初始化脚本
python database/init_db.py
```

#### 4. 启动服务

```bash
# 启动开发服务器
cd backend
python main.py

# 服务将在 http://localhost:8082 启动
# API文档可在 http://localhost:8082/docs 查看
```

## 访问应用

### Web界面访问

- **登录页面**: http://localhost:8082/login
- **注册页面**: http://localhost:8082/register
- **主页面**: http://localhost:8082/
- **API文档**: http://localhost:8082/docs

### 预设账号

系统预设管理员账号：
- **用户名**: `admin`
- **密码**: `admin`
- **角色**: 管理员

## 用户操作指南

### 管理员登录

1. 访问 `http://localhost:8082/login`
2. 输入用户名：`admin`
3. 输入密码：`admin`
4. 点击登录按钮
5. 成功后跳转到管理员工作台

### 老师注册

1. 访问 `http://localhost:8082/register`
2. 填写用户名（建议格式：`teacher_姓名`）
3. 填写密码（至少6位字符）
4. 选择角色：`老师`
5. 点击注册按钮
6. 成功后跳转到登录页面

### 学生注册

1. 访问 `http://localhost:8082/register`
2. 填写用户名（建议格式：`student_姓名`）
3. 填写密码（至少6位字符）
4. 选择角色：`学生`
5. 点击注册按钮
6. 成功后跳转到登录页面

## 开发环境配置

### 启动开发模式

```bash
# 启动热重载开发服务器
cd backend
uvicorn main:app --host 0.0.0.0 --port 8082 --reload
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=backend tests/

# 运行特定测试文件
pytest tests/test_auth.py
```

### 代码格式化

```bash
# 格式化代码
black backend/

# 排序导入
isort backend/

# 代码检查
flake8 backend/
```

## 系统功能

### 用户管理
- ✅ 用户注册（老师/学生）
- ✅ 用户登录/登出
- ✅ 会话管理（支持记住我）
- ✅ 密码安全存储

### 前端界面
- ✅ 响应式设计（支持移动端）
- ✅ 加载状态指示
- ✅ 会话超时警告
- ✅ 用户友好的错误提示

### 安全特性
- ✅ 密码哈希存储
- ✅ 会话令牌管理
- ✅ 自动会话过期
- ✅ XSS防护头部

### 管理功能
- ✅ 健康检查端点
- ✅ API文档自动生成
- ✅ 请求日志记录
- ✅ 错误处理

## 配置选项

### 环境变量

```bash
# 设置端口（默认8082）
export PORT=8082

# 设置日志级别
export LOG_LEVEL=info

# 设置数据库路径（可选）
export DATABASE_PATH=./database/users.db
```

### 服务端口配置

修改 `backend/main.py` 中的端口号：

```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8082,  # 修改此处的端口号
    reload=True,
    log_level="info"
)
```

## 故障排除

### 常见问题

**Q: 端口被占用怎么办？**
```bash
# 查看端口占用
lsof -i :8082

# 或者修改端口
export PORT=8083
python main.py
```

**Q: 忘记管理员密码？**
```bash
# 重新初始化数据库（会清空所有数据）
cd backend
python -c "from database.connection import init_db; init_db()"
```

**Q: 依赖安装失败？**
```bash
# 升级pip并重试
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

**Q: 数据库权限问题？**
```bash
# 确保目录有写权限
chmod -R 755 backend/database/
```

### 日志查看

应用运行时会显示详细的日志信息：

```bash
# 查看实时日志
python main.py

# 日志级别包括：
# - INFO: 正常操作信息
# - WARNING: 警告信息
# - ERROR: 错误信息
# - DEBUG: 调试信息（需要设置LOG_LEVEL=debug）
```

### 数据库管理

```bash
# 进入SQLite数据库
sqlite backend/database/users.db

# 查看所有用户
SELECT * FROM users;

# 查看会话信息
SELECT * FROM sessions;

# 清理过期会话
DELETE FROM sessions WHERE expires_at < datetime('now');
```

## 生产部署

### 使用Gunicorn部署

```bash
# 安装Gunicorn
pip install gunicorn

# 启动生产服务器
cd backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8082
```

### Docker部署（可选）

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ ./backend/
EXPOSE 8082

CMD ["python", "backend/main.py"]
```

### Nginx反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 下一步开发计划

- [ ] 文件上传功能
- [ ] 组会日程管理
- [ ] 文献库系统
- [ ] 实时通知功能
- [ ] 权限细化管理
- [ ] 数据备份功能

## 技术支持

如遇到问题，请检查：

1. **环境检查**：Python版本、依赖安装
2. **网络检查**：端口占用、防火墙设置
3. **权限检查**：文件读写权限
4. **日志检查**：控制台错误信息
5. **浏览器检查**：开发者工具错误信息

更多技术问题请查看项目文档或提交Issue。