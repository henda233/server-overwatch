# 🗂️ WIKI Index（全局摘要索引）

> 🔄 最后同步：2026-04-08 12:00 | 🤖 维护Agent：v2.8 | 📦 总摘要数：10 + 计划文档10份 + 部署文档1份

## 📊 模块总览

| 摘要ID | 类别 | 链接 | 内容 | 更新 |
|--------|------|------|------|------|
| `abs_001` | project/overview | [🔗](./abstract/project/overview.md) | 项目概述+目录结构 | 04-07 |
| `abs_002` | tech/botpy | [🔗](./abstract/tech/botpy.md) | QQ机器人SDK，事件监听 | 04-07 |
| `abs_003` | config/qq_bot | [🔗](./abstract/config/qq_bot.md) | 配置模板 | 04-07 |
| `abs_004` | server/gpu_info | [🔗](./abstract/server/gpu_info.md) | 服务器环境信息 | 04-07 |
| `abs_005` | requirement/core | [🔗](./abstract/requirement/core.md) | 功能需求+命令设计 | 04-07 |
| `abs_phase1`~`abs_phase2` | dev_progress | [🔗](./abstract/dev_progress/) | ✅ 阶段1-2完成 | 04-07 |
| `abs_006` | config/env | [🔗](./abstract/config/env.md) | 开发环境配置 | 04-07 |
| `abs_plan09`~`abs_plan10` | dev_progress | [🔗](./abstract/dev_progress/) | ✅ PLAN-09~10完成 | 04-08 |

## 📐 开发计划文档

| 编号 | 名称 | 状态 | 链接 |
|------|------|------|------|
| PLAN-001~004 | 架构/流程/模块/命令设计 | ✅ | [🔗](./plan/) |
| PLAN-005 | 用户资源区分修复 | ✅ | [🔗](./plan/05-user-resource-fix.md) |
| PLAN-006 | nvidia-smi字段解析Bug | ✅ | [🔗](./plan/06-who-missing-process-user-fix.md) |
| PLAN-007 | 按用户区分CPU/内存/GPU | ✅ | [🔗](./plan/07-user-cpu-memory-gpu-percent-fix.md) |
| PLAN-008 | GPU使用率和显存显示小数 | ✅ | [🔗](./plan/08-gpu-memory-decimal-fix.md) |
| PLAN-009 | 历史记录精简模式 | ✅ | [🔗](./plan/09-history-compact-mode.md) |
| PLAN-010 | QQ机器人命令扩展 | ✅ | [🔗](./plan/10-command-extension.md) |

## ✅ 开发待办（状态汇总）

| 阶段 | 任务 | 状态 |
|------|------|------|
| 1 | 基础框架搭建 | ✅ |
| 2 | 核心功能（机器人/采集/命令/格式化） | ✅ |
| 3 | 历史功能（SQLite/定时采集/30天清理/历史查询） | ✅ |
| 4 | 部署（systemd服务配置/服务器测试） | 🔲 待办 |
| 5-8 | 用户资源区分/Bug修复/命令扩展 | ✅ |

## 📝 全局更新日志（近10条）

- `04-08 12:00`: ✅ **PLAN-009完成：历史记录精简模式**
  - `/info <用户> <时间>` 组合命令、历史自动过滤0值、统一单行格式、统计摘要
- `04-08 11:55`: ✅ **PLAN-010完成：命令扩展**
  - 新增 `/stats <时间>`、`/top [gpu/mem/cpu]`、`/users [天数]`
- `04-07 20:36`: ✅ **PLAN-008完成：GPU/显存小数显示**
  - `round(..., 2)` 保留2位小数，GPU 51.85%，显存 7.65GB/95.59GB
- `04-07 20:45`: ✅ **PLAN-007完成：按用户区分CPU/内存/GPU**
  - `get_process_info()` 按进程聚合、按显存比例分配GPU使用率
- `04-07 21:30`: ✅ **PLAN-006完成：nvidia-smi字段解析修复**
  - 字段检查改为 `len >= 2`
- `04-07 20:40`: ✅ **WIKI一致性修复 + PLAN-005完成**
- `04-07 17:50`: ✅ **部署文档完成** - `docs/部署指南.md`
- `04-07 17:45`: ✅ **botpy intents修复 + 私聊支持**
- `04-07 17:35`: ✅ **阶段2+3全部完成** - 30天清理/历史查询
- `04-07 17:15`: ✅ **阶段1基础框架完成**
