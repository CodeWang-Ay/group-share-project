# 研究任务管理功能设计规格

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现研究任务管理功能，支持个人任务和导师分配任务两种类型

**Architecture:** FastAPI后端 + SQLite数据库 + Jinja2前端模板，复用现有认证和用户系统

**Tech Stack:** FastAPI, SQLite, Jinja2, Tailwind CSS, JavaScript

---

## 1. 功能概述

研究任务管理功能支持两种任务来源：
1. **个人任务** - 学生自己创建和管理的Todo清单
2. **导师任务** - 导师分配给学生的研究任务

核心功能：任务CRUD、状态管理、进度跟踪、筛选排序

---

## 2. 数据模型

### Task 表结构

```sql
CREATE TABLE IF NOT EXISTS research_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'middle',  -- high, middle, low
    status VARCHAR(20) DEFAULT 'pending',   -- pending, ongoing, completed
    progress INTEGER DEFAULT 0,             -- 0-100
    assignee_id INTEGER NOT NULL,           -- 负责人ID
    creator_id INTEGER NOT NULL,            -- 创建者ID
    task_type VARCHAR(20) DEFAULT 'personal', -- personal, assigned
    deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 索引

```sql
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON research_tasks(assignee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_creator ON research_tasks(creator_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON research_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON research_tasks(deadline);
```

### Task 模型类 (Python)

```python
@dataclass
class Task:
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    priority: str = "middle"  # high, middle, low
    status: str = "pending"   # pending, ongoing, completed
    progress: int = 0         # 0-100
    assignee_id: int = 0
    creator_id: int = 0
    task_type: str = "personal"  # personal, assigned
    deadline: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

---

## 3. API端点设计

所有端点路径前缀：`/api/research_tasks`

### 3.1 获取任务列表
```
GET /api/research_tasks
```
**查询参数：**
- `status`: 状态筛选 (pending/ongoing/completed/overdue)
- `priority`: 优先级筛选 (high/middle/low)
- `assignee_id`: 负责人筛选
- `task_type`: 任务类型筛选 (personal/assigned)
- `sort_by`: 排序字段 (deadline/created_at/priority)
- `sort_order`: 排序方向 (asc/desc)
- `page`: 页码
- `limit`: 每页数量

**返回：**
```json
{
    "success": true,
    "data": {
        "tasks": [...],
        "pagination": {
            "current_page": 1,
            "per_page": 10,
            "total": 50,
            "total_pages": 5
        }
    }
}
```

### 3.2 获取统计信息
```
GET /api/research_tasks/stats
```
**返回：**
```json
{
    "success": true,
    "data": {
        "total": 50,
        "pending_count": 10,
        "ongoing_count": 20,
        "completed_count": 15,
        "overdue_count": 5
    }
}
```

### 3.3 创建任务
```
POST /api/research_tasks
```
**请求体：**
```json
{
    "title": "任务标题",
    "description": "任务描述",
    "priority": "high",
    "deadline": "2026-05-20T10:00:00",
    "assignee_id": 2
}
```

### 3.4 获取任务详情
```
GET /api/research_tasks/{id}
```

### 3.5 更新任务
```
PUT /api/research_tasks/{id}
```
**请求体：** 同创建任务，所有字段可选

### 3.6 更新进度（学生权限）
```
PUT /api/research_tasks/{id}/progress
```
**请求体：**
```json
{
    "progress": 50,
    "status": "ongoing"
}
```

### 3.7 删除任务
```
DELETE /api/research_tasks/{id}
```

---

## 4. 权限控制逻辑

### 4.1 创建任务权限

| 用户角色 | 可创建类型 | assignee限制 |
|---------|-----------|--------------|
| 学生 | personal | 必须是自己 |
| 导师 | assigned | 任意学生 |
| 管理员 | assigned | 任意学生 |

### 4.2 编辑任务权限

| 任务类型 | 导师 | 学生(创建者) | 学生(非创建者) |
|---------|------|-------------|---------------|
| assigned | 可编辑全部字段 | 仅可更新进度 | 仅可更新进度(如为assignee) |
| personal | 可编辑(如为创建者) | 可编辑全部字段 | 无权限 |

### 4.3 删除任务权限

| 任务类型 | 导师 | 学生(创建者) | 学生(assignee) |
|---------|------|-------------|---------------|
| assigned | 可删除 | 无权限 | 无权限 |
| personal | 可删除(如为创建者) | 可删除 | 无权限 |

---

## 5. 前端页面功能

### 5.1 统计卡片
- 总任务数
- 待开始数量
- 进行中数量
- 已完成数量
- 已逾期数量

### 5.2 筛选功能
- 状态筛选：全部/待开始/进行中/已完成/已逾期
- 优先级筛选：全部/高/中/低
- 负责人筛选（导师可见）：全部/选择学生
- 排序：截止日期/创建时间/优先级

### 5.3 任务卡片显示
- 任务标题
- 任务描述（截断显示）
- 优先级标签（高/中/低，颜色区分）
- 状态标签（待开始/进行中/已完成/已逾期）
- 进度条
- 负责人头像和姓名
- 截止日期
- 操作按钮：查看详情、编辑、删除

### 5.4 任务操作
- 新建任务：弹出模态框填写信息
- 查看详情：显示完整任务信息
- 编辑任务：模态框编辑（根据权限控制可编辑字段）
- 更新进度：进度条拖动或输入百分比
- 删除任务：确认后删除

---

## 6. 文件结构

```
backend/
├── models/
│   └── task.py              # Task数据模型
├── services/
│   └── task_service.py      # 任务业务逻辑服务
├── database/
│   └── connection.py        # 添加research_tasks表初始化
├── main.py                  # 添加任务API端点

templates/
└── rm_research_tasks.html   # 前端页面（已有模板，需改造）
```

---

## 7. 状态说明

| 状态值 | 显示文本 | 颜色 |
|-------|---------|------|
| pending | 待开始 | 蓝色 |
| ongoing | 进行中 | 绿色 |
| completed | 已完成 | 灰色 |
| overdue | 已逾期 | 红色（系统根据deadline计算）|

**注意：** overdue不是数据库存储的状态，而是根据deadline和当前状态动态计算的显示状态。

---

## 8. 优先级说明

| 优先级值 | 显示文本 | 颜色 |
|---------|---------|------|
| high | 高优先级 | 红色 |
| middle | 中优先级 | 黄色 |
| low | 低优先级 | 绿色 |

---

## 9. 实现任务清单

- [ ] 创建 Task 模型类 (backend/models/task.py)
- [ ] 添加 research_tasks 表初始化 (backend/database/connection.py)
- [ ] 创建 TaskService 服务类 (backend/services/task_service.py)
- [ ] 添加任务API端点 (backend/main.py)
- [ ] 改造前端页面模板 (templates/rm_research_tasks.html)
- [ ] 实现筛选和排序功能
- [ ] 实现权限控制逻辑
- [ ] 测试验证