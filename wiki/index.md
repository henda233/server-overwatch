# 🗂️ WIKI Index（全局摘要索引）

> 🔄 最后同步：2026-04-07 | 🤖 维护Agent：v2.0 | 📦 总摘要数：5 + 计划文档4份

## 📊 模块总览

| 摘要ID | 所属模块/类别 | 核心摘要链接 | 关键状态/结论 | 最后更新 |
|--------|--------------|-------------|--------------|---------|
| `abs_001` | `project/overview` | [🔗](./abstract/project/overview.md) | ✅ Server Only架构 | 04-07 |
| `abs_002` | `tech/botpy` | [🔗](./abstract/tech/botpy.md) | SDK已集成 | 04-07 |
| `abs_003` | `config/qq_bot` | [🔗](./abstract/config/qq_bot.md) | 配置模板已就绪 | 04-07 |
| `abs_004` | `server/gpu_info` | [🔗](./abstract/server/gpu_info.md) | 服务器环境信息 | 04-07 |
| `abs_005` | `requirement/core` | [🔗](./abstract/requirement/core.md) | ✅ Server Only架构 | 04-07 |

## 📐 开发计划文档

| 文档编号 | 文档名称 | 版本 | 状态 | 链接 |
|----------|---------|------|------|------|
| PLAN-001 | 系统架构设计 | v2.0 | ✅ 完成 | [🔗](./plan/01-architecture.md) |
| PLAN-002 | 开发流程 | v2.0 | ✅ 完成 | [🔗](./plan/02-development-flow.md) |
| PLAN-003 | 模块详细设计 | v2.0 | ✅ 完成 | [🔗](./plan/03-module-design.md) |
| PLAN-004 | QQ机器人命令设计 | v2.0 | ✅ 完成 | [🔗](./plan/04-command-design.md) |

## 🚨 开发待办

### 阶段1: 基础框架
- [ ] 项目结构搭建
- [ ] 配置管理 (`utils/config.py`)
- [ ] `config.yaml` 配置文件

### 阶段2: 核心功能
- [ ] QQ机器人连接 (`bot/handler.py`)
- [ ] 数据采集 (`monitor/collector.py`)
- [ ] 命令解析 (`/info`, `/help`)
- [ ] 结果格式化 (`monitor/formatter.py`)

### 阶段3: 历史功能
- [ ] SQLite数据库 (`monitor/recorder.py`)
- [ ] 定时采集任务 (每10分钟)
- [ ] 30天自动清理
- [ ] 历史查询 (`/info 1d/1w/1m`)

### 阶段4: 部署
- [ ] systemd 服务配置
- [ ] 服务器测试

## 📝 全局更新日志（近10条）

- `04-07`: ✅ 架构更新为 Server Only v2.0
  - 移除SSH模块
  - 简化目录结构
  - 新增SQLite历史存储
  - 定时采集任务设计
- `04-07 16:10`: ✅ 开发计划文档完成（架构+流程+模块+命令设计）
- `04-07 16:30`: ✅ 开发环境配置完成
- `04-07 16:07`: Agent 完成项目WIKI记忆库初始化
- `04-07 15:43`: 项目创建，导入botpy submodule
