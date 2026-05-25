# 研究进展模块 API 文档

## 模块概述

研究进展模块用于学生定期提交研究进展、导师查看团队进展、设置提交周期等。

## 端点列表

| 端点 | 方法 | 功能 | 需要认证 | 角色 |
|------|------|------|----------|------|
| `/api/research_progress/my` | GET | 获取自己的进展历史 | 是 | 学生 |
| `/api/research_progress/submit` | POST | 提交新进展 | 是 | 学生 |
| `/api/research_progress/settings` | GET | 获取提交周期设置 | 是 | 所有 |
| `/api/research_progress/team` | GET | 获取团队进展 | 是 | 导师/管理员 |
| `/api/research_progress/stats` | GET | 获取统计数据 | 是 | 导师/管理员 |
| `/api/research_progress/settings/{user_id}` | PUT | 设置学生提交周期 | 是 | 导师/管理员 |
| `/api/research_progress/settings/batch` | POST | 批量设置提交周期 | 是 | 管理员 |
| `/api/research_progress/{id}` | GET | 查看进展详情 | 是 | 所有 |
| `/api/research_progress/{id}` | PUT | 编辑已提交进展 | 是 | 学生 |
| `/api/research_progress/{id}/feedback` | POST | 发送导师反馈 | 是 | 导师/管理员 |

---

## 1. 获取自己的进展历史

**端点：** `GET /api/research_progress/my`

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `page` | int | 页码，默认 1 |
| `limit` | int | 每页数量，默认 10 |
| `order` | string | 排序：desc 或 asc |

**成功响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "research_direction": "深度学习",
      "weekly_progress": "完成了模型训练...",
      "next_goal": "下周计划优化模型...",
      "difficulties": "数据量不足",
      "completion_rate": 60,
      "status": "normal",
      "submission_date": "2026-05-24T10:00:00",
      "supervisor_feedback": null,
      "attachments": []
    }
  ],
  "pagination": {
    "total": 5,
    "page": 1,
    "limit": 10,
    "total_pages": 1
  }
}
```

---

## 2. 提交新进展

**端点：** `POST /api/research_progress/submit`

**请求体：**
```json
{
  "research_direction": "深度学习",
  "weekly_progress": "本周完成了模型训练，准确率达到85%",
  "next_goal": "下周计划进行模型优化，提升准确率到90%",
  "difficulties": "数据集标注质量不高",
  "completion_rate": 60,
  "attachments": [],
  "submission_period": "weekly"
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "进展提交成功",
  "data": {
    "id": 1,
    "status": "normal"
  }
}
```

---

## 3. 获取提交周期设置

**端点：** `GET /api/research_progress/settings`

**成功响应：**
```json
{
  "success": true,
  "data": {
    "period_type": "weekly",
    "reminder_enabled": true,
    "reminder_days": 1,
    "next_deadline": "2026-05-31T23:59:59",
    "period_text": "每周提交"
  }
}
```

---

## 4. 获取团队进展

**端点：** `GET /api/research_progress/team`

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `student_type` | string | doctoral/master/undergraduate |
| `grade` | int | 年级筛选 |
| `research_direction` | string | 研究方向筛选 |
| `status` | string | normal/delayed/warning/not_updated |
| `updated_within` | string | 7days/14days/30days |
| `page` | int | 页码 |
| `limit` | int | 每页数量 |

**成功响应：**
```json
{
  "success": true,
  "data": [
    {
      "user_id": 2,
      "username": "张三",
      "research_direction": "深度学习",
      "degree_type": "博士",
      "progress_id": 10,
      "weekly_progress": "完成模型训练",
      "completion_rate": 60,
      "status": "normal",
      "submission_date": "2026-05-24T10:00:00",
      "computed_status": "normal",
      "period_type": "weekly",
      "next_deadline": "2026-05-31T23:59:59"
    }
  ],
  "pagination": {
    "total": 10,
    "page": 1,
    "limit": 20,
    "total_pages": 1
  }
}
```

---

## 5. 获取统计数据

**端点：** `GET /api/research_progress/stats`

**成功响应：**
```json
{
  "success": true,
  "data": {
    "total_students": 10,
    "weekly_submissions": 8,
    "delayed_count": 1,
    "warning_count": 2,
    "normal_count": 5,
    "not_updated_count": 2
  }
}
```

---

## 6. 设置学生提交周期

**端点：** `PUT /api/research_progress/settings/{user_id}`

**请求体：**
```json
{
  "period_type": "weekly",
  "reminder_enabled": true,
  "reminder_days": 1
}
```

**周期类型：**
- `weekly`: 每周提交
- `biweekly`: 每两周提交
- `monthly`: 每月提交

---

## 7. 发送导师反馈

**端点：** `POST /api/research_progress/{id}/feedback`

**请求体：**
```json
{
  "feedback": "进展良好，建议继续深入研究模型优化方向"
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "反馈发送成功",
  "data": {
    "id": 1,
    "supervisor_feedback": "进展良好...",
    "feedback_at": "2026-05-24T12:00:00"
  }
}
```

---

## 进展状态说明

| 状态 | 说明 |
|------|------|
| `normal` | 正常，完成度 ≥ 50% |
| `warning` | 预警，完成度 30%-50% |
| `delayed` | 逾期，完成度 < 30% |
| `not_updated` | 未更新（超过7天未提交） |

---

## 权限说明

| 角色 | 权限 |
|------|------|
| `student` | 提交进展、查看自己的进展、编辑本周提交 |
| `teacher` | 查看团队进展、发送反馈、设置提交周期 |
| `admin` | 所有权限 + 批量设置 |