# API 合同定义

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **认证方式**: Session-based

## API 端点

### 1. 用户注册

**POST** `/api/auth/register`

#### 请求体
```json
{
  "username": "string",
  "password": "string",
  "role": "teacher|student"
}
```

#### 响应

**成功 (201)**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "user": {
      "id": 1,
      "username": "teacher_zhang",
      "role": "teacher"
    }
  }
}
```

**错误 (400)**
```json
{
  "success": false,
  "message": "用户名已存在",
  "error": "USERNAME_EXISTS"
}
```

**错误 (422)**
```json
{
  "success": false,
  "message": "数据验证失败",
  "error": "VALIDATION_ERROR",
  "details": {
    "username": ["用户名格式不正确"],
    "password": ["密码长度至少6位"]
  }
}
```

### 2. 用户登录

**POST** `/api/auth/login`

#### 请求体
```json
{
  "username": "string",
  "password": "string"
}
```

#### 响应

**成功 (200)**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "user": {
      "id": 1,
      "username": "admin",
      "role": "admin"
    },
    "redirect_url": "/"
  }
}
```

**错误 (401)**
```json
{
  "success": false,
  "message": "用户名或密码错误",
  "error": "INVALID_CREDENTIALS"
}
```

### 3. 用户登出

**POST** `/api/auth/logout`

#### 响应

**成功 (200)**
```json
{
  "success": true,
  "message": "登出成功"
}
```

### 4. 获取当前用户信息

**GET** `/api/auth/me`

#### 响应

**成功 (200)**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "admin",
      "role": "admin"
    }
  }
}
```

**错误 (401)**
```json
{
  "success": false,
  "message": "未登录",
  "error": "NOT_AUTHENTICATED"
}
```

## 数据格式规范

### 用户角色
- `admin`: 管理员
- `teacher`: 老师
- `student`: 学生

### 错误代码
- `USERNAME_EXISTS`: 用户名已存在
- `INVALID_CREDENTIALS`: 用户名或密码错误
- `VALIDATION_ERROR`: 数据验证失败
- `NOT_AUTHENTICATED`: 未登录
- `INTERNAL_ERROR`: 服务器内部错误

### 验证规则
- **username**: 3-50字符，只允许字母、数字、下划线
- **password**: 最少6字符
- **role**: 只能是 "teacher" 或 "student"（注册时）

## 会话管理

### 会话创建
登录成功时创建会话，会话有效期24小时

### 会话验证
所有需要认证的API都需要验证会话有效性

### 会话销毁
登出时立即销毁会话

## 前端集成示例

### 注册请求
```javascript
const registerData = {
  username: 'teacher_zhang',
  password: 'password123',
  role: 'teacher'
};

fetch('/api/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(registerData)
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    alert('注册成功！');
    window.location.href = '/login';
  } else {
    alert(data.message);
  }
});
```

### 登录请求
```javascript
const loginData = {
  username: 'admin',
  password: 'admin'
};

fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(loginData)
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    window.location.href = data.data.redirect_url;
  } else {
    alert(data.message);
  }
});
```