# 数据模型设计

## 实体关系图

```
用户 (User)
├── id (主键)
├── username (用户名，唯一)
├── password (密码，存储哈希值)
├── role (角色：admin/teacher/student)
├── created_at (创建时间)
└── updated_at (更新时间)
```

## 数据表设计

### users 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 用户唯一标识 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名，系统内唯一 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希值，不存储明文密码 |
| role | VARCHAR(20) | NOT NULL | 用户角色：admin/teacher/student |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 最后更新时间 |

### 角色定义

| 角色值 | 中文名称 | 权限说明 |
|--------|----------|----------|
| admin | 管理员 | 系统管理权限，可以管理所有用户 |
| teacher | 老师 | 可以上传文件、管理学生、参与组会 |
| student | 学生 | 可以下载文件、参与组会、上传汇报材料 |

## 数据验证规则

### 用户名验证
- 长度：3-50个字符
- 格式：只允许字母、数字、下划线
- 唯一性：系统内不能重复
- 示例：admin, teacher_zhang, student_01

### 密码验证
- 长度：最少6个字符
- 复杂度：无特殊要求（第一阶段）
- 存储：使用bcrypt进行哈希处理

### 角色验证
- 注册时只能选择：teacher, student
- admin角色为预设，不允许注册
- 角色值必须为预定义的三种之一

## 初始数据

### 预设管理员账号
```sql
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$2b$12$...', 'admin');
```

- 用户名：admin
- 密码：admin
- 角色：admin
- 说明：系统初始化时自动创建

## 状态转换

### 用户注册流程
```
[用户填写表单] → [数据验证] → [用户名重复检查] → [密码哈希] → [保存到数据库] → [注册成功]
```

### 用户登录流程
```
[用户输入凭证] → [数据验证] → [查询用户] → [密码验证] → [创建会话] → [登录成功]
```

## 错误处理

### 注册错误类型
- 用户名已存在
- 用户名格式不正确
- 密码长度不足
- 角色选择无效

### 登录错误类型
- 用户名不存在
- 密码错误
- 账号被禁用（扩展功能）

## 安全考虑

### 密码安全
- 使用bcrypt进行密码哈希
- 不在日志中记录密码
- 密码传输使用HTTPS（生产环境）

### 会话安全
- 会话ID随机生成
- 会话有过期时间
- 登出时清除会话

## 扩展性考虑

### 预留字段
- email：邮箱地址（后续功能）
- status：账号状态（启用/禁用）
- last_login：最后登录时间

### 索引设计
- username字段建立唯一索引
- created_at字段建立普通索引（用于统计）