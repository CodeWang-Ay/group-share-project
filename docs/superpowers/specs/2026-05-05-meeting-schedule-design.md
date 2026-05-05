# 组会安排功能设计文档

> 创建日期：2026-05-05
> 状态：待审核

---

## 一、功能概述

组会安排是研究生组会文件共享系统的核心功能模块，用于管理实验室每周组会的创建、分配、材料提交和状态跟踪。

### 核心特性

- **混合分配模式**：导师可指定汇报人，学生也可主动报名
- **完整信息管理**：时间、地点、主题、汇报人、时长、材料要求、线上/线下选项
- **双向材料关联**：汇报人上传材料 + 导师指定材料
- **全员参与**：导师/管理员管理组会，学生可报名汇报

---

## 二、数据库设计

### 2.1 meetings 表（组会主表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| title | VARCHAR(200) | 组会标题 |
| meeting_type | VARCHAR(50) | 组会类型：regular/paper_reading/topic_discussion |
| description | TEXT | 组会描述/主题说明 |
| location | VARCHAR(100) | 会议地点 |
| is_online | BOOLEAN | 是否线上会议 |
| online_link | VARCHAR(500) | 线上会议链接 |
| scheduled_at | TIMESTAMP | 会议时间 |
| duration_total | INTEGER | 总时长（分钟） |
| material_required | BOOLEAN | 是否需要提交材料 |
| material_deadline | TIMESTAMP | 材料提交截止时间 |
| notes | TEXT | 备注/材料要求说明 |
| status | VARCHAR(20) | 状态：scheduled/ongoing/completed |
| created_by | INTEGER | 创建人ID |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 2.2 meeting_presenters 表（汇报人关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| meeting_id | INTEGER | 组会ID |
| user_id | INTEGER | 汇报人ID（关联users表） |
| presenter_type | VARCHAR(20) | 分配类型：assigned/volunteered/pending |
| duration_minutes | INTEGER | 汇报时长（分钟） |
| material_required | BOOLEAN | 是否需要提交材料 |
| status | VARCHAR(20) | 汇报人状态：pending/confirmed/completed |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**presenter_type 说明**：
- `assigned`：导师直接指定
- `volunteered`：学生主动报名
- `pending`：待分配名额（导师创建后等待报名）

### 2.3 meeting_files 表（材料关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| meeting_id | INTEGER | 组会ID |
| file_id | INTEGER | 文件ID（关联files表） |
| presenter_id | INTEGER | 汇报人ID（关联meeting_presenters表） |
| created_at | TIMESTAMP | 创建时间 |

---

## 三、状态流转

### 3.1 组会状态

```
scheduled（待召开） -> ongoing（进行中） -> completed（已完成）
```

- 创建组会后默认为 `scheduled`
- 导师/管理员可手动标记为 `ongoing`（组会开始时）
- 组会结束后标记为 `completed`

### 3.2 汇报人状态

```
pending（待确认） -> confirmed（已确认） -> completed（已完成）
```

- 被分配或报名后默认为 `pending`
- 汇报人确认后变为 `confirmed`
- 组会完成后变为 `completed`

---

## 四、权限控制

| 操作 | 管理员 | 导师 | 学生 |
|------|--------|------|------|
| 创建组会 | ✓ | ✓ | ✓* |
| 编辑组会 | ✓ | ✓ | ✗ |
| 删除组会 | ✓ | ✓ | ✗ |
| 分配汇报人 | ✓ | ✓ | ✗ |
| 报名汇报 | ✓ | ✓ | ✓ |
| 上传材料 | ✓ | ✓ | ✓** |
| 更新组会状态 | ✓ | ✓ | ✗ |

*学生创建的组会需要导师/管理员审核（当前版本暂不实现审核流程，学生创建直接生效）
**仅能上传自己作为汇报人的材料

---

## 五、API接口设计

### 5.1 组会管理接口

| 接口 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/api/meetings` | GET | 全员 | 获取组会列表（支持分页、筛选） |
| `/api/meetings` | POST | 全员 | 创建组会 |
| `/api/meetings/{id}` | GET | 全员 | 获取组会详情 |
| `/api/meetings/{id}` | PUT | 导师/管理员/创建者 | 更新组会信息 |
| `/api/meetings/{id}` | DELETE | 导师/管理员 | 删除组会 |
| `/api/meetings/{id}/status` | PUT | 导师/管理员 | 更新组会状态 |

### 5.2 汇报人接口

| 接口 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/api/meetings/{id}/presenters` | GET | 全员 | 获取汇报人列表 |
| `/api/meetings/{id}/presenters` | POST | 导师/管理员 | 分配汇报人 |
| `/api/meetings/{id}/presenters/{pid}` | PUT | 该汇报人 | 汇报人确认/取消 |
| `/api/meetings/{id}/presenters/{pid}` | DELETE | 导师/管理员 | 移除汇报人 |
| `/api/meetings/{id}/volunteer` | POST | 学生 | 学生报名汇报 |

### 5.3 材料接口

| 接口 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/api/meetings/{id}/materials` | GET | 全员 | 获取组会材料列表 |
| `/api/meetings/{id}/materials` | POST | 汇报人 | 上传材料并关联 |
| `/api/meetings/{id}/materials/{fid}` | DELETE | 汇报人/导师 | 移除材料关联 |

### 5.4 统计接口

| 接口 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/api/meetings/stats` | GET | 全员 | 获取组会统计信息 |

---

## 六、前端页面设计

### 6.1 组会列表页

- 展示组会卡片列表，支持按状态、类型、时间筛选
- 顶部统计卡片：本月组会次数、待审阅材料、团队成员、共享文献
- 每个组会卡片显示：标题、时间、地点、汇报人、状态
- 操作按钮：查看详情、编辑（有权限）、报名汇报（学生）

### 6.2 组会详情页

- 完整组会信息展示
- 汇报人列表及材料状态
- 材料上传/查看区域
- 操作按钮：编辑、更新状态、分配汇报人

### 6.3 创建/编辑组会表单

- 基本信息：标题、类型、描述
- 时间地点：时间、时长、地点、线上/线下、链接
- 汇报人设置：汇报人数上限、每人时长、材料要求、截止时间
- 备注：材料要求说明

---

## 七、组会类型

预设三种类型：

| 类型 | 标识 | 说明 |
|------|------|------|
| 常规组会 | regular | 每周例行组会，进展汇报 |
| 论文研读 | paper_reading | 针对特定论文的研读讨论 |
| 专题讨论 | topic_discussion | 针对特定研究主题的讨论 |

---

## 八、与现有模块的关系

### 8.1 与汇报材料模块的关系

- 组会创建后，汇报人可在汇报材料页面提交材料并关联到组会
- 组会详情页展示关联的汇报材料
- 材料状态（已提交/未提交）在组会页面可见

### 8.2 与组会记录模块的关系

- 组会完成后，可基于组会安排生成组会记录
- 组会记录继承组会的基本信息（时间、地点、汇报人）
- 记录内容另行编辑（讨论内容、决议等）

### 8.3 与文件系统的关系

- 汇报材料复用现有 `files` 表
- `meeting_files` 表建立组会与材料的关联
- 材料文件存储路径与现有共享文件一致

---

## 九、实现优先级

### 第一阶段（本次实现）

1. 数据库表创建
2. 组会 CRUD API
3. 组会列表页面（替换现有假数据）
4. 组会详情页面
5. 创建/编辑组会表单

### 第二阶段（后续迭代）

1. 汇报人分配与报名功能
2. 材料关联功能
3. 组会状态流转
4. 统计数据展示

---

## 十、技术实现要点

### 10.1 数据库迁移

- 在 `backend/database/connection.py` 的 `init_db()` 中添加表创建语句
- 现有数据库通过 ALTER TABLE 方式添加新表（不影响现有数据）

### 10.2 API 实现

- 在 `backend/main.py` 中添加组会相关路由
- 复用现有的认证中间件 `get_current_user()`
- 权限校验在路由函数中实现

### 10.3 前端实现

- 修改现有 `gm_meeting_schedule.html` 模板
- 添加 JavaScript 代码调用 API
- 复用现有侧边栏、导航栏组件

---

## 十一、待确认事项

- 无

---

## 十二、后续扩展考虑

- 组会提醒通知（邮件/站内通知）
- 组会日历视图
- 组会模板（快速创建相似组会）
- 学生创建组会的审核机制
- 组会签到功能