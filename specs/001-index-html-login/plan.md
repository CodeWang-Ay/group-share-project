# Implementation Plan: 基础用户认证系统

**Branch**: `001-index-html-login` | **Date**: 2025-10-15 | **Spec**: [基础用户认证系统](spec.md)
**Input**: Feature specification from `/specs/001-index-html-login/spec.md`
**Technical Stack**: 前端采用原生 HTML、JavaScript 与 CSS 开发，后端使用 Python FastAPI 框架，数据库选用 SQLite，不使用数据加密

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

本功能需要实现基础的用户认证系统，包括管理员登录、老师和学生的用户注册以及登录验证功能。主要需求包括三个用户角色（管理员、老师、学生）、预设管理员账号（admin/admin）、注册功能限制（老师和学生角色）、登录成功后跳转到index.html页面。

**✅ 技术栈完全符合章程要求**：Python FastAPI + SQLite架构已获得章程支持。

## Technical Context

**Language/Version**: Python 3.11+ ✅ [章程允许]
**Primary Dependencies**: FastAPI, SQLite, Uvicorn ✅ [符合章程要求]
**Storage**: SQLite数据库 ✅ [章程明确指定]
**Testing**: pytest ✅ [基础测试即可，符合实用测试覆盖原则]
**Target Platform**: Web浏览器 + 本地Python服务器 ✅ [符合架构要求]
**Project Type**: Web应用（前端+后端）✅ [符合章程技术栈]
**Performance Goals**: <2秒响应时间，支持10-50用户并发 ✅ [符合成功标准]
**Constraints**: 不使用数据加密 ✅ [符合用户要求]
**Scale/Scope**: 小型实验室使用，3种用户角色 ✅ [符合需求规模]

**技术合规性**：
- 用户选择：Python FastAPI + SQLite（后端架构）
- 章程要求：Python后端 + SQLite数据库
- 合规状态：完全符合章程要求 ✅

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 简单性优先检查
- [x] 能否在单个HTML文件中实现？ [前端部分保持单文件，后端仅添加必要的API服务]
- [x] 是否避免了不必要的模块拆分？ [FastAPI应用结构简单，仅3个核心模块]
- [x] 是否使用了Python后端（章程允许）
- [x] 是否使用了SQLite数据库（章程明确指定）

### YAGNI原则检查
- [x] 所有功能是否都有第二周内的明确需求？ [管理员登录、用户注册、登录验证]
- [x] 是否避免了过度抽象和扩展点？ [基础功能，无额外抽象层]

### 先跑通再优化检查
- [x] 是否避免了缓存、并发、微服务等复杂优化？ [SQLite简单存储，无复杂优化]
- [x] 优先保证功能正确性而非性能？ [基础认证功能优先]

### 可读性优先检查
- [x] 变量和函数命名是否清晰完整？ [设计文档已定义清晰的命名规范]
- [x] 是否提供了足够的中文行内注释？ [设计文档要求中文注释]

### 实用测试覆盖检查
- [x] 是否覆盖了主要用户路径？ [登录、注册、验证流程]
- [x] 是否避免了过度工程化的测试？ [基础功能测试即可]

### 技术选择审慎检查
- [x] 每个技术选择是否都有明确的业务驱动力？ [研究文档已分析SQLite vs localStorage的必要性]
- [x] 是否回答了"不用就解决不了"的问题？ [研究文档已说明为什么不能用纯前端方案]

### 中文文档优先检查
- [x] 所有文档是否使用中文编写？ [规范、计划、研究、数据模型文档都使用中文]
- [x] 代码注释是否使用中文？ [设计文档已要求中文注释]

## ✅ Phase 1 重新评估结果

**章程检查状态**: 全部通过 ✅

**通过理由**:
1. **简单性**: 前端保持单文件，后端结构简洁，仅实现必要功能
2. **YAGNI**: 只实现注册、登录、验证三个核心功能
3. **功能优先**: 无缓存、并发等复杂优化，专注基础功能
4. **可读性**: 清晰的命名规范和中文注释要求
5. **测试覆盖**: 覆盖主要用户路径，避免过度测试
6. **技术审慎**: 研究文档充分论证了技术选择的必要性
7. **中文文档**: 所有设计文档都使用中文编写

**复杂性解决方案**:
通过Phase 0研究，明确了技术选择的合理性，解决了章程合规性问题。

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
# 后端服务（Python FastAPI）
backend/
├── main.py                    # FastAPI应用入口
├── models/
│   ├── __init__.py
│   └── user.py               # 用户数据模型
├── services/
│   ├── __init__.py
│   └── auth.py               # 认证服务逻辑
├── database/
│   ├── __init__.py
│   └── connection.py         # SQLite数据库连接
└── requirements.txt          # Python依赖包

# 前端模板文件
templates/
├── index.html                # 主页面（登录后跳转）
├── login.html                # 登录页面
└── register.html             # 注册页面
```

**Structure Decision**:
根据用户需求和更新后的章程，选择前后端分离架构：
- 后端：Python FastAPI + SQLite，提供用户认证API
- 前端：模板文件存放在templates文件夹，通过FastAPI的模板系统提供服务
- 符合章程允许的Python后端要求，同时保持简单的文件组织结构

## Complexity Tracking

✅ **无章程冲突**：所有技术选择都符合章程要求，无需特殊论证。
