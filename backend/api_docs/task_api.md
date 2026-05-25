# 研究任务模块 API 文档

## 模块概述

研究任务模块用于创建和管理研究任务，支持个人任务和导师分配任务。

## 端点列表

| 端点 | 方法 | 功能 | 需要认证 |
|------|------|------|----------|
| `/api/research_tasks` | GET | 获取任务列表 | 是 |
| `/api/research_tasks/stats` | GET | 获取任务统计 | 是 |
| `/api/research_tasks` | POST | 创建研究任务 | 是 |
| `/api/research_tasks/{id}` | GET | 获取任务详情 | 是 |
| `/api/research_tasks/{id}` | PUT | 更新任务信息 | 是 |
| `/api/research_tasks/{id}/progress` | PUT | 更新任务进度 | 是 |
| `/api/research_tasks/{id}` | DELETE | 删除任务 | 是 |

---

## 1. 获取任务列表

**端点：** `GET /api/research_tasks`

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | pending/ongoing/completed/overdue |
| `priority` | string | high/middle/low |
| `assignee_id` | int | 负责人ID |
| `task_type` | string | personal/assigned |
| `keyword` | string | 搜索关键词 |
| `sort_by` | string | deadline/created_at/priority/updated_at |
| `sort_order` | string | asc/desc |
| `page` | int | 页码 |
| `limit` | int | 每页数量 |

**成功响应：**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": 1,
        "title": "完成论文初稿",
        "description": "完成论文第一章的撰写",
        "priority": "high",
        "status": "ongoing",
        "progress": 30,
        "assignee_id": 2,
        "assignee": {"id": 2, "username": "张三"},
        "creator_id": 1,
        "creator": {"id": 1, "username": "导师"},
        "task_type": "assigned",
        "deadline": "2026-06-30T23:59:59",
        "display_status": "进行中",
        "status_text": "进行中",
        "priority_text": "高优先级",
        "created_at": "2026-05-24T10:00:00"
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 10,
      "total": 5,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

## 2. 获取任务统计

**端点：** `GET /api/research_tasks/stats`

**成功响应：**
```json
{
  "success": true,
  "data": {
    "total": 10,
    "pending_count": 2,
    "ongoing_count": 5,
    "completed_count": 3,
    "overdue_count": 1
  }
}
```

---

## 3. 创建研究任务

**端点：** `POST /api/research_tasks`

**请求体：**
```json
{
  "title": "完成论文初稿",
  "description": "完成论文第一章的撰写",
  "priority": "high",
  "assignee_id": 2,
  "task_type": "assigned",
  "deadline": "2026-06-30T23:59:59"
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "任务创建成功",
  "data": {
    "id": 1,
    "title": "完成论文初稿",
    "status": "pending",
    "progress": 0
  }
}
```

---

## 4. 更新任务信息

**端点：** `PUT /api/research_tasks/{id}`

**请求体：**
```json
{
  "title": "修改后的标题",
  "description": "修改后的描述",
  "priority": "middle",
  "deadline": "2026-07-15T23:59:59"
}
```

---

## 5. 更新任务进度

**端点：** `PUT /api/research_tasks/{id}/progress`

**请求体：**
```json
{
  "progress": 50,
  "status": "ongoing"
}
```

**自动状态更新规则：**
- 进度 = 100% → 自动标记为 `completed`
- 进度 > 0% → 自动标记为 `ongoing`

**成功响应：**
```json
{
  "success": true,
  "message": "进度更新成功",
  "data": {
    "id": 1,
    "progress": 50,
    "status": "ongoing"
  }
}
```

---

## 6. 删除任务

**端点：** `DELETE /api/research_tasks/{id}`

**成功响应：**
```json
{
  "success": true,
  "message": "任务删除成功"
}
```

---

## 任务类型

| 类型 | 说明 | 创建权限 |
|------|------|----------|
| `personal` | 个人任务 | 学生、导师、管理员 |
| `assigned` | 导师分配任务 | 导师、管理员 |

---

## 任务状态

| 状态 | 说明 |
|------|------|
| `pending` | 待开始 |
| `ongoing` | 进行中 |
| `completed` | 已完成 |
| `overdue` | 已逾期 |

---

## 优先级

| 优先级 | 说明 |
|------|------|
| `high` | 高优先级 |
| `middle` | 中优先级 |
| `low` | 低优先级 |

---

## 权限规则

| 角色 | 创建 | 编辑 | 更新进度 | 删除 |
|------|------|------|----------|------|
| `admin` | 所有任务 | 所有任务 | 所有任务 | 所有任务 |
| `teacher` | assigned + personal | assigned + 自己的personal | 所有 | assigned + 自己的personal |
| `student` | 仅 personal | 仅自己的personal | 自己负责的任务 | 仅自己的personal |