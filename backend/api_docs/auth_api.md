# 认证模块 API 文档

## 模块概述

认证模块提供用户登录、注册、会话管理等功能。

## 端点列表

| 端点 | 方法 | 功能 | 需要认证 |
|------|------|------|----------|
| `/api/auth/login` | POST | 用户登录 | 否 |
| `/api/auth/register` | POST | 用户注册 | 否 |
| `/api/auth/logout` | POST | 用户登出 | 否 |
| `/api/auth/me` | GET | 获取当前用户信息 | 是 |
| `/api/auth/change-password` | PUT | 修改密码 | 是 |
| `/api/auth/refresh` | POST | 刷新会话 | 否 |
| `/api/auth/session-status` | GET | 检查会话状态 | 否 |

---

## 1. 用户登录

**端点：** `POST /api/auth/login`

**请求体：**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "email": null,
    "research_direction": null
  }
}
```

**失败响应：**
```json
{
  "success": false,
  "message": "用户名或密码错误",
  "error": "INVALID_CREDENTIALS"
}
```

---

## 2. 用户注册

**端点：** `POST /api/auth/register`

**请求体：**
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "role": "student"
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": 2,
    "username": "newuser",
    "role": "student"
  }
}
```

---

## 3. 用户登出

**端点：** `POST /api/auth/logout`

**成功响应：**
```json
{
  "success": true,
  "message": "登出成功"
}
```

---

## 4. 获取当前用户信息

**端点：** `GET /api/auth/me`

需要携带有效的 session cookie。

**成功响应：**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "email": "admin@example.com",
    "research_direction": "人工智能",
    "student_id": null,
    "degree_type": null,
    "avatar": null
  }
}
```

---

## 5. 修改密码

**端点：** `PUT /api/auth/change-password`

**请求体：**
```json
{
  "old_password": "oldpassword",
  "new_password": "newpassword"
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "密码修改成功"
}
```

**失败响应：**
```json
{
  "success": false,
  "message": "原密码错误",
  "error": "INVALID_PASSWORD"
}
```

---

## 6. 刷新会话

**端点：** `POST /api/auth/refresh`

延长会话有效期。

**成功响应：**
```json
{
  "success": true,
  "message": "会话已刷新"
}
```

---

## 7. 检查会话状态

**端点：** `GET /api/auth/session-status`

**成功响应：**
```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "user_id": 1,
    "username": "admin"
  }
}
```

**未登录响应：**
```json
{
  "success": true,
  "data": {
    "authenticated": false
  }
}
```

---

## 认证机制

本项目使用 **Session Cookie** 进行认证：

1. 登录成功后，服务器创建 session 并设置 cookie
2. Cookie 名称：`session_id`
3. 后续请求需携带 cookie 进行身份验证
4. Session 默认有效期：24 小时

## 用户角色

| 角色 | 说明 |
|------|------|
| `admin` | 管理员，拥有所有权限 |
| `teacher` | 导师，可管理学生、查看团队进展 |
| `student` | 学生，可提交进展、管理个人任务 |