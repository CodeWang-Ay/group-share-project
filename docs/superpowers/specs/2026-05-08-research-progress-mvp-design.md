# 研究进展模块 MVP 设计规范

**版本号：V0.0.1**
**编写日期：2026-05-08**
**适用范围：智能计算实验室 - 研究进展模块 MVP 开发**

---

## 一、项目概述

### 1.1 目标

为研究生组会文件共享系统实现「研究进展」模块的核心功能，让学生能够定期提交研究进展，导师能够查看和管理团队进展。

### 1.2 MVP 范围

本次开发聚焦以下核心功能：

- **学生端**：提交进展、查看自己的进展历史、获取提交周期设置
- **导师端**：查看团队所有成员进展、多维度筛选、统计数据、发送反馈/沟通
- **管理员端**：设置学生提交周期、批量配置、手动触发提醒

后续迭代将添加：趋势分析、甘特图、批量提醒、模板复用等高级功能。

---

## 二、数据模型设计

### 2.1 ResearchProgress 模型

**职责：** 存储每次进展提交记录

**字段设计：**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | int | 否 | 主键，自增 |
| user_id | int | 是 | 提交者（学生），关联 users 表 |
| research_direction | str | 是 | 研究方向 |
| weekly_progress | str | 是 | 本周进展内容 |
| next_goal | str | 是 | 下周目标 |
| difficulties | str | 否 | 遇到的问题/困难 |
| completion_rate | int | 否 | 完成度百分比 (0-100)，默认 0 |
| attachments | str | 否 | 附件文件路径（JSON格式存储多个文件） |
| submission_period | str | 否 | 提交周期类型：weekly/biweekly/monthly，默认 weekly |
| submission_date | datetime | 否 | 本次提交日期 |
| period_start | datetime | 否 | 本周期起始日期 |
| period_end | datetime | 否 | 本周期截止日期 |
| status | str | 否 | 状态：normal/delayed/warning，默认 normal |
| supervisor_feedback | str | 否 | 导师反馈内容 |
| feedback_at | datetime | 否 | 导师反馈时间 |
| created_at | datetime | 否 | 创建时间 |
| updated_at | datetime | 否 | 更新时间 |

**状态说明：**
- `normal`: 进度正常
- `delayed`: 进度滞后（超过提交周期未更新）
- `warning`: 进度预警（导师标记）

### 2.2 ProgressSetting 模型

**职责：** 管理学生的提交周期配置

**字段设计：**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | int | 否 | 主键，自增 |
| user_id | int | 是 | 学生ID，关联 users 表，唯一约束 |
| period_type | str | 是 | 周期类型：weekly/biweekly/monthly，默认 weekly |
| reminder_enabled | bool | 否 | 是否启用提醒，默认 True |
| reminder_days | int | 否 | 提前多少天提醒，默认 1 |
| next_deadline | datetime | 否 | 下次提交截止时间 |
| created_by | int | 是 | 配置创建者（导师/管理员），关联 users 表 |
| created_at | datetime | 否 | 创建时间 |
| updated_at | datetime | 否 | 更新时间 |

---

## 三、API 接口设计

### 3.1 学生端 API

| API | 方法 | 功能 | 请求参数 |
|-----|------|------|----------|
| `/api/research_progress/my` | GET | 获取自己的进展历史列表 | `page`, `limit`, `order` |
| `/api/research_progress/submit` | POST | 提交新的进展 | 见 3.4 提交参数 |
| `/api/research_progress/{id}` | PUT | 编辑已提交的进展 | 见 3.4 提交参数（仅限本周） |
| `/api/research_progress/{id}` | GET | 查看进展详情 | 无 |
| `/api/research_progress/settings` | GET | 获取自己的提交周期设置 | 无 |

### 3.2 导师端 API

| API | 方法 | 功能 | 请求参数 |
|-----|------|------|----------|
| `/api/research_progress/team` | GET | 获取团队所有成员进展 | 见 3.5 篮选参数 |
| `/api/research_progress/stats` | GET | 获取统计数据 | 无 |
| `/api/research_progress/{id}` | GET | 查看某个学生的进展详情 | 无 |
| `/api/research_progress/{id}/feedback` | POST | 发送导师反馈/沟通 | `feedback` |
| `/api/research_progress/settings/{user_id}` | PUT | 设置某个学生的提交周期 | 见 3.6 周期设置参数 |

### 3.3 管理员 API

| API | 方法 | 功能 | 请求参数 |
|-----|------|------|----------|
| `/api/research_progress/settings/batch` | POST | 批量设置学生提交周期 | `user_ids`, `period_type`, `reminder_days` |
| `/api/research_progress/reminders` | POST | 手动触发提醒 | `user_ids` 或 `all` |

### 3.4 提交进展参数

```json
{
  "research_direction": "多模态学习与生成模型",
  "weekly_progress": "完成了跨模态注意力机制设计...",
  "next_goal": "准备数据集扩展和 ablation study",
  "difficulties": "数据集标注质量不佳",
  "completion_rate": 75,
  "attachments": ["paper_draft_v2.pdf", "experiment_data.xlsx"]
}
```

### 3.5 篮选参数

```
GET /api/research_progress/team?student_type=doctoral&grade=2&research_direction=AI&status=delayed&updated_within=7days&page=1&limit=20
```

| 参数 | 说明 | 可选值 |
|------|------|--------|
| student_type | 学生类型 | doctoral, master, undergraduate |
| grade | 年级 | 1-6 |
| research_direction | 研究方向关键词 | 任意字符串 |
| status | 进度状态 | normal, delayed, warning, not_updated |
| updated_within | 最近更新时间范围 | 7days, 14days, 30days |
| page | 分页页码 | 数字 |
| limit | 每页数量 | 数字 |

### 3.6 周期设置参数

```json
{
  "period_type": "weekly",
  "reminder_enabled": true,
  "reminder_days": 1,
  "next_deadline": "2026-05-15T18:00:00"
}
```

---

## 四、前端页面设计

### 4.1 页面结构

**页面：** `tm_research_progress.html`

**角色适配：**
- 学生角色：显示「提交进展」按钮 + 自己的进展历史列表
- 导师/管理员角色：显示统计卡片 + 团队进展表格 + 篮选工具栏

### 4.2 导师端界面布局

```
┌─────────────────────────────────────────────────────────┐
│  研究进展 - 跟踪和管理团队成员的研究进展                    │
├─────────────────────────────────────────────────────────┤
│  篮选工具栏                                              │
│  [全部成员] [博士生] [硕士生] [本科] [进度预警]  [批量设置周期]│
├─────────────────────────────────────────────────────────┤
│  统计卡片                                                │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                    │
│  │总人数│ │进度  │ │进度  │ │未更新│                     │
│  │  18  │ │正常12│ │滞后 4│ │本周 2│                     │
│  └──────┘ └──────┘ └──────┘ └──────┘                    │
├─────────────────────────────────────────────────────────┤
│  学生研究进展表格                                         │
│  学生 | 研究方向 | 最近进展 | 下周目标 | 完成度 | 更新时间 | 操作│
│  张明 | 多模态.. | 完成了.. | 准备..   |  75%  | 2023-.. | 详情 沟通│
│  李华 | 低资源.. | 完成了.. | 撰写..   |  90%  | 2023-.. | 详情 沟通│
│  ...                                                     │
├─────────────────────────────────────────────────────────┤
│  [查看所有学生进展]                                       │
└─────────────────────────────────────────────────────────┘
```

### 4.3 学生端界面布局

```
┌─────────────────────────────────────────────────────────┐
│  研究进展 - 我的研究进展                                   │
├─────────────────────────────────────────────────────────┤
│  提交周期信息                                             │
│  当前周期：每周提交 | 下次截止时间：2023-11-19              │
│  [提交本周进展]                                           │
├─────────────────────────────────────────────────────────┤
│  我的进展历史                                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 2023-11-12 第12周                                  │   │
│  │ 研究方向：多模态学习                                │   │
│  │ 本周进展：完成了跨模态注意力机制设计...              │   │
│  │ 下周目标：准备数据集扩展和 ablation study           │   │
│  │ 完成度：75%  [编辑] [查看详情]                      │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 2023-11-05 第11周                                  │   │
│  │ ...                                                 │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 4.4 提交进展弹窗

点击「提交本周进展」后显示表单：

| 字段 | 输入类型 | 说明 |
|------|----------|------|
| 研究方向 | 下拉选择 | 从用户资料中获取，或手动输入 |
| 本周进展内容 | 多行文本 | 必填 |
| 下周目标 | 多行文本 | 必填 |
| 遇到的问题/困难 | 多行文本 | 可选 |
| 完成度 | 数字滑块/输入 | 0-100 |
| 附件上传 | 文件选择 | 可选，支持多文件 |

### 4.5 详情弹窗

点击「详情」后显示完整进展内容，导师可在此添加反馈：

```
┌─────────────────────────────────────────────────────────┐
│  进展详情 - 张明 (2023-11-12)                         [X] │
├─────────────────────────────────────────────────────────┤
│  研究方向：多模态学习与生成模型                           │
│  本周进展：完成了跨模态注意力机制设计，初步实验结果显示... │
│  下周目标：准备数据集扩展和 ablation study               │
│  问题困难：无                                            │
│  完成度：75%                                             │
│  附件：paper_draft_v2.pdf                                │
├─────────────────────────────────────────────────────────┤
│  导师反馈（可选）：                                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 建议优先完成数据集准备工作，下周组会汇报进展...    │    │
│  └─────────────────────────────────────────────────┘    │
│                    [取消]  [发送反馈]                    │
└─────────────────────────────────────────────────────────┘
```

---

## 五、权限设计

### 5.1 角色权限矩阵

| 功能 | 学生 | 导师 | 管理员 |
|------|------|------|--------|
| 提交自己的进展 | ✓ | - | - |
| 编辑自己的进展（本周） | ✓ | - | - |
| 查看自己的进展历史 | ✓ | - | - |
| 查看团队公开进度看板 | ✓ | ✓ | ✓ |
| 查看所有成员进展详情 | - | ✓ | ✓ |
| 发送反馈/沟通 | - | ✓ | ✓ |
| 设置学生提交周期 | - | ✓ | ✓ |
| 批量配置周期 | - | - | ✓ |
| 手动触发提醒 | - | - | ✓ |
| 配置系统设置 | - | - | ✓ |

### 5.2 权限校验逻辑

- 学生只能操作 `user_id == current_user.id` 的进展
- 导师可以查看所有学生进展，但只能修改反馈内容
- 管理员拥有全部权限

---

## 六、文件结构

### 6.1 新增文件

```
backend/
├── models/
│   └── research_progress.py      # ResearchProgress + ProgressSetting 模型
│
├── services/
│   └── research_progress_service.py  # 进展相关的业务逻辑
│
├── database/
│   └── connection.py (更新)      # 添加进展表初始化
│
└── main.py (更新)                # 添加进展相关 API 路由

templates/
└── tm_research_progress.html (改造)  # 动态渲染真实数据，弹窗内嵌
```

### 6.2 数据库表 SQL

**research_progress 表：**

```sql
CREATE TABLE research_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    research_direction TEXT NOT NULL,
    weekly_progress TEXT NOT NULL,
    next_goal TEXT NOT NULL,
    difficulties TEXT,
    completion_rate INTEGER DEFAULT 0,
    attachments TEXT,
    submission_period TEXT DEFAULT 'weekly',
    submission_date DATETIME,
    period_start DATETIME,
    period_end DATETIME,
    status TEXT DEFAULT 'normal',
    supervisor_feedback TEXT,
    feedback_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**progress_settings 表：**

```sql
CREATE TABLE progress_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    period_type TEXT DEFAULT 'weekly',
    reminder_enabled INTEGER DEFAULT 1,
    reminder_days INTEGER DEFAULT 1,
    next_deadline DATETIME,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

---

## 七、实现要点

### 7.1 提交周期计算

- `weekly`: 每周一为周期起始，周日为截止
- `biweekly`: 每两周一个周期
- `monthly`: 每月 1 日为周期起始，月末为截止

系统根据 `progress_settings` 表中的配置自动计算 `next_deadline`。

### 7.2 状态自动判断

- `not_updated`: 超过截止时间未提交新进展
- `delayed`: 提交了进展但 `completion_rate` < 50% 或导师标记
- `normal`: 正常提交且进度良好

### 7.3 前端交互

- 使用 JavaScript Fetch API 与后端通信
- 弹窗使用模态框实现（内嵌在页面中）
- 表单验证在提交前检查必填字段
- 附件上传复用现有文件上传逻辑

### 7.4 兼容性

- 保持现有 `tm_research_progress.html` 页面路由不变
- 保持现有导航栏和侧边栏结构不变
- 新增 API 不影响现有其他模块

---

## 八、后续迭代计划

本次 MVP 不包含以下功能，留待后续迭代：

1. **趋势分析**: 个人进度趋势图、团队进度对比
2. **甘特图**: 目标时间线可视化
3. **批量提醒**: 自动发送提醒邮件/消息
4. **模板复用**: 学生保存常用进展模板
5. **智能填充**: 根据历史记录推荐撰写要点
6. **版本对比**: 对比不同阶段进展变化
7. **逾期申请**: 学生提交延期申请，导师审批

---

## 九、验收标准

### 9.1 功能验收

- [ ] 学生能成功提交进展，数据正确保存到数据库
- [ ] 学生能查看自己的进展历史列表
- [ ] 导师能查看团队所有成员进展列表
- [ ] 导师能使用筛选功能（学生类型、年级、研究方向、状态）
- [ ] 导师能看到正确的统计数据（总人数/正常/滞后/未更新）
- [ ] 导师能发送反馈，学生能看到反馈内容
- [ ] 管理员能设置单个学生的提交周期
- [ ] 管理员能批量设置学生提交周期

### 9.2 权限验收

- [ ] 学生无法查看其他学生的进展详情
- [ ] 学生无法修改其他学生的进展
- [ ] 导师无法修改进展内容，只能添加反馈
- [ ] 未登录用户无法访问页面和 API

### 9.3 UI 验收

- [ ] 页面布局正确显示（导师端和学生端）
- [ ] 弹窗正常打开和关闭
- [ ] 表单验证提示清晰
- [ ] 响应式设计在移动端正常显示