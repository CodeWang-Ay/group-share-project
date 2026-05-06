# 文献库功能设计文档

日期：2026-05-06

## 概述

研究生组会文件共享系统的文献库功能，支持团队成员共享文献资源，同时允许每个成员管理私人文献空间。

## 核心需求

1. **双库模式**：团队共享库 + 个人私人库
2. **PDF上传**：用户上传PDF文件，手动填写文献信息
3. **阅读状态**：未读/在读/已读 + 收藏标记
4. **标签系统**：系统预设标签 + 用户自定义标签，颜色区分
5. **重复检测**：通过文件hash值检测，团队共享库不允许重复文献
6. **批量操作**：批量收藏、设置标签、删除

## 数据库设计

### papers 表（文献元数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 主键 |
| title | TEXT NOT NULL | 标题 |
| authors | TEXT | 作者 |
| year | INTEGER | 发表年份 |
| journal | TEXT | 期刊/会议 |
| doi | TEXT | DOI |
| abstract | TEXT | 摘要 |
| pdf_path | TEXT | PDF文件路径 |
| pdf_size | INTEGER | 文件大小（字节） |
| file_hash | TEXT | 文件SHA256哈希（用于重复检测） |
| arxiv_link | TEXT | arXiv链接 |
| semantic_scholar_link | TEXT | Semantic Scholar链接 |
| download_count | INTEGER DEFAULT 0 | 下载次数 |
| created_at | DATETIME | 创建时间 |
| uploader_id | INTEGER | 上传者用户ID |

### tags 表（标签库）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 主键 |
| name | TEXT NOT NULL UNIQUE | 标签名称 |
| tag_type | TEXT DEFAULT 'system' | 类型：system/custom |
| created_by | INTEGER | 创建者ID（custom标签） |
| created_at | DATETIME | 创建时间 |

预设系统标签：Transformer, BERT, CNN, 大模型, NLP, 计算机视觉

### paper_user_relations 表（用户与文献关系）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 主键 |
| paper_id | INTEGER NOT NULL | 文献ID |
| user_id | INTEGER NOT NULL | 用户ID |
| read_status | TEXT DEFAULT 'unread' | 阅读状态：unread/reading/read |
| is_starred | INTEGER DEFAULT 0 | 是否收藏：0/1 |
| library_type | TEXT DEFAULT 'public' | 库类型：public/private |
| added_at | DATETIME | 加入时间 |
| last_viewed_at | DATETIME | 最后查看时间 |

### paper_tags 表（文献-标签关联）

| 字段 | 类型 | 说明 |
|------|------|------|
| paper_id | INTEGER NOT NULL | 文献ID |
| tag_id | INTEGER NOT NULL | 标签ID |

注：paper_id + tag_id 为联合主键

## API 设计

所有API路径前缀：`/api/paper_database/`

### 基础操作

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/paper_database/ | 获取文献列表（支持筛选参数） |
| GET | /api/paper_database/{id} | 获取文献详情 |
| POST | /api/paper_database/ | 上传新文献（含重复检测） |
| PUT | /api/paper_database/{id} | 编辑文献元数据 |
| DELETE | /api/paper_database/{id} | 删除文献 |

### 状态与收藏

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/paper_database/{id}/star | 收藏/取消收藏 |
| PUT | /api/paper_database/{id}/status | 更新阅读状态 |

### 标签管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/paper_database/tags | 获取标签列表 |
| POST | /api/paper_database/tags | 添加新标签（用户自定义） |
| POST | /api/paper_database/{id}/tags | 为文献设置标签 |
| DELETE | /api/paper_database/{id}/tags/{tag_id} | 移除文献标签 |

### 统计与批量操作

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/paper_database/stats | 获取统计数据 |
| POST | /api/paper_database/batch/star | 批量收藏/取消收藏 |
| POST | /api/paper_database/batch/tags | 批量设置标签 |
| DELETE | /api/paper_database/batch | 批量删除 |

### 查询参数

GET /api/paper_database/ 支持以下筛选参数：
- `keyword`: 搜索关键词（标题/作者）
- `tag`: 标签ID
- `status`: 阅读状态
- `year`: 发表年份
- `starred`: 是否收藏
- `library_type`: 库类型
- `sort`: 排序方式

## 服务层设计

### PaperService 类

负责处理文献相关的业务逻辑：

1. **create_paper**: 上传文献
   - 计算PDF文件hash
   - 检查团队共享库是否已存在相同hash的文献
   - 如果重复：返回已存在文献ID，创建用户关联关系
   - 如果不重复：创建新文献记录 + 用户关联关系

2. **get_papers**: 获取文献列表
   - 根据用户ID和library_type查询
   - 关联标签、阅读状态、收藏信息
   - 支持筛选和排序

3. **update_status**: 更新阅读状态
   - 更新paper_user_relations表的read_status字段

4. **toggle_star**: 收藏/取消收藏
   - 更新paper_user_relations表的is_starred字段

5. **batch_operations**: 批量操作
   - 批量更新多个文献的状态或标签

### 重复检测逻辑

```
上传团队共享文献流程：
1. 计算PDF文件的SHA256 hash值
2. 查询 papers 表的 file_hash 字段
3. 如果hash匹配：
   - 返回提示"文献已存在于团队库"
   - 为当前用户创建与已有文献的关联关系（paper_user_relations）
   - 不创建新的papers记录
4. 如果不匹配：
   - 创建新的papers记录
   - 为用户创建关联关系
```

## 前端改造设计

现有前端 `PaperManager` 对象改造：

### 初始化

```javascript
// 原代码：使用假数据数组
papers: [...假数据...]

// 新代码：从API加载
async init() {
    await this.loadPapers();
    await this.loadTags();
    this.updateStats();
}
```

### 数据加载方法改造

| 方法 | 改造内容 |
|------|---------|
| loadPapers() | GET /api/paper_database/ |
| searchPapers(keyword) | GET /api/paper_database/?keyword=xxx |
| filterByTag(tag) | GET /api/paper_database/?tag=xxx |
| filterByStatus(status) | GET /api/paper_database/?status=xxx |
| filterByYear(year) | GET /api/paper_database/?year=xxx |
| updateStats() | GET /api/paper_database/stats |

### 操作方法改造

| 方法 | 改造内容 |
|------|---------|
| toggleStar(id) | POST /api/paper_database/{id}/star |
| updateReadStatus() | PUT /api/paper_database/{id}/status |
| deletePaper(id) | DELETE /api/paper_database/{id} |
| savePaper() | POST /api/paper_database/（含FormData上传） |
| downloadPaper(id) | 直接打开pdf_path链接 |

### 批量操作改造

| 方法 | 改造内容 |
|------|---------|
| batchStar(star) | POST /api/paper_database/batch/star |
| applyBatchTag() | POST /api/paper_database/batch/tags |
| batchDelete() | DELETE /api/paper_database/batch |

### 标签颜色区分

系统标签：蓝色系背景
自定义标签：灰色系背景

前端渲染时根据tag_type字段应用不同CSS类：
```html
<span class="tag-badge bg-blue-100 text-blue-700">{{ tag.name }}</span>  <!-- system -->
<span class="tag-badge bg-gray-100 text-gray-600">{{ tag.name }}</span>  <!-- custom -->
```

## 文件存储

PDF文件存储于项目 `uploads/papers/` 目录：
- 文件命名：`{paper_id}_{timestamp}.pdf`
- 路径示例：`uploads/papers/1_20260506123045.pdf`
- 通过静态文件服务访问：`/uploads/papers/xxx.pdf`

## 权限设计

- 团队共享库文献：所有团队成员可查看
- 个人私人库文献：仅创建者可查看
- 上传文献的用户可编辑文献元数据
- 管理员可删除任意文献

## 开发计划

### 阶段一：后端数据层
1. 创建Paper、Tag、PaperUserRelation数据模型
2. 创建数据库表结构
3. 初始化系统标签数据

### 阶段二：后端服务层
1. 实现PaperService类
2. 实现所有API接口
3. 实现重复检测逻辑

### 阶段三：前端改造
1. 改造PaperManager初始化方法
2. 改造数据加载方法
3. 改造操作方法对接API
4. 实现标签颜色区分显示

### 阶段四：测试与优化
1. 功能测试
2. 重复检测测试
3. 批量操作测试
4. UI体验优化