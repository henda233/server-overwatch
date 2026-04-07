# 🗂️ WIKI Index（全局摘要索引）

> 🔄 最后同步：2026-04-07 20:36 | 🤖 维护Agent：v2.3 | 📦 总摘要数：7 + 计划文档8份 + 部署文档1份

## 📊 模块总览

| 摘要ID | 所属模块/类别 | 核心摘要链接 | 关键状态/结论 | 最后更新 |
|--------|--------------|-------------|--------------|---------|
| `abs_001` | `project/overview` | [🔗](./abstract/project/overview.md) | ✅ Server Only架构 | 04-07 |
| `abs_002` | `tech/botpy` | [🔗](./abstract/tech/botpy.md) | SDK已集成 | 04-07 |
| `abs_003` | `config/qq_bot` | [🔗](./abstract/config/qq_bot.md) | 配置模板已就绪 | 04-07 |
| `abs_004` | `server/gpu_info` | [🔗](./abstract/server/gpu_info.md) | 服务器环境信息 | 04-07 |
| `abs_005` | `requirement/core` | [🔗](./abstract/requirement/core.md) | ✅ Server Only架构 | 04-07 |
| `abs_phase1` | `dev_progress/phase1` | [🔗](./abstract/dev_progress/phase1-complete.md) | ✅ 阶段1完成 | 04-07 |
| `abs_phase2` | `dev_progress/botpy-intents` | [🔗](./abstract/dev_progress/botpy-intents-fix.md) | ✅ intents配置修复 + 私聊支持 | 04-07 |

## 📐 开发计划文档

| 文档编号 | 文档名称 | 版本 | 状态 | 链接 |
|----------|---------|------|------|------|
| PLAN-001 | 系统架构设计 | v2.0 | ✅ 完成 | [🔗](./plan/01-architecture.md) |
| PLAN-002 | 开发流程 | v2.0 | ✅ 完成 | [🔗](./plan/02-development-flow.md) |
| PLAN-003 | 模块详细设计 | v2.0 | ✅ 完成 | [🔗](./plan/03-module-design.md) |
| PLAN-004 | QQ机器人命令设计 | v2.0 | ✅ 完成 | [🔗](./plan/04-command-design.md) |
| PLAN-005 | 用户资源区分修复 | v1.0 | ✅ 完成 | [🔗](./plan/05-user-resource-fix.md) |
| PLAN-006 | nvidia-smi字段解析Bug修复 | v2.0 | ✅ 完成 | [🔗](./plan/06-who-missing-process-user-fix.md) |
| PLAN-007 | 按用户区分CPU/内存/GPU使用率 | v1.0 | ✅ 已完成 | [🔗](./plan/07-user-cpu-memory-gpu-percent-fix.md) |
| PLAN-008 | GPU使用率和显存显示小数 | v1.0 | 📋 待执行 | [🔗](./plan/08-gpu-memory-decimal-fix.md) |

## 🚨 开发待办

### 阶段1: 基础框架
- [x] 项目结构搭建
- [x] 配置管理 (`utils/config.py`)
- [x] `config.yaml` 配置文件
- [x] `main.py` 程序入口
- [x] `requirements.txt` 依赖文件

### 阶段2: 核心功能
- [x] QQ机器人连接 (`bot/handler.py`, `main.py`) ✅ 已实现
- [x] 数据采集 (`monitor/collector.py`) ✅ 已实现
- [x] 命令解析 (`/info`, `/help`) ✅ 已实现
- [x] 结果格式化 (`monitor/formatter.py`) ✅ 已实现

### 阶段3: 历史功能
- [x] SQLite数据库 (`monitor/recorder.py`) ✅ 已实现
- [x] 定时采集任务 (每10分钟) ✅ 已在 PeriodicCollector 实现
- [x] 30天自动清理 ✅ 已在 PeriodicCollector 集成
- [x] 历史查询 (`/info 1d/1w/1m`) ✅ 已在 handler.py 实现

### 阶段4: 部署
- [x] systemd 服务配置 ✅ 已完成
- [ ] 服务器测试

### 阶段5: 用户资源区分修复
- [x] 修改 collector.py，按用户聚合GPU数据
- [x] 本地测试验证
- [ ] 部署到GPU服务器

### 阶段6: nvidia-smi字段解析Bug修复
- [x] 修正 collector.py 字段检查 `len >= 2`
- [x] 处理GPU使用率获取（设为0）
- [x] 部署到GPU服务器

### 阶段7: 按用户区分CPU/内存/GPU使用率
- [x] 重构 `get_pid_username_map()` 为 `get_process_info()`
- [x] 实现按用户聚合 CPU/内存
- [x] 实现按显存比例分配 GPU 使用率
- [x] 部署到GPU服务器 ✅ 验证通过

## 📝 全局更新日志（近10条）

- `04-07 20:36`: 📋 **PLAN-008 创建：GPU使用率和显存显示小数**
  - 问题：GPU使用率和显存显示为整数，不够精确
  - 方案：`collector.py` 使用 `round()` 保留2位小数，`formatter.py` 调整显示格式
  - 创建 `wiki/plan/08-gpu-memory-decimal-fix.md`
- `04-07 20:36`: ✅ **问题分析：GPU使用率为0**
  - 根因：全局GPU使用率接近0，按显存比例分配后仍为0
  - 方案：调整为小数显示，让用户看到精确值
- `04-07 20:36`: ✅ **PLAN-007 修复完成**
  - 重构 `get_pid_username_map()` → `get_process_info()`
  - 按进程聚合 CPU/内存（累计值，可超过100%）
  - 按显存比例分配 GPU 使用率
  - GPU服务器验证：cxy(CPU 11.3%, MEM 4.6%), lgl(CPU 891%, MEM 1.5%, GPU 37%)
- `04-07 20:45`: 📋 **PLAN-007 创建：按用户区分CPU/内存/GPU使用率**
  - 问题：GPU使用率显示0，CPU/内存所有用户相同
  - 根因：`nvidia-smi --query-compute-apps`不支持GPU使用率，CPU/内存为系统级数据
  - 方案：按显存比例分配GPU使用率 + 按进程聚合CPU/内存
  - 创建 `wiki/plan/07-user-cpu-memory-gpu-percent-fix.md`
- `04-07 21:30`: ✅ **PLAN-006 修复完成**
  - 修改 `monitor/collector.py` 第102-120行
  - 查询字段改为 `pid,used_memory`
  - 字段检查改为 `len >= 2`
  - GPU使用率暂设为0
  - 用户在GPU服务器验证：显存显示正确
- `04-07 21:25`: 🐛 **PLAN-006 根因修正**
  - 问题：lgl登录正常，`who`检测正常，但显存仍显示0GB
  - **实际根因**：`nvidia-smi --query-compute-apps`返回2字段，代码期望3字段
  - 更新 `wiki/plan/06-who-missing-process-user-fix.md` v2.0
  - 修复方案：修正字段数量检查 `len >= 2`
- `04-07 18:10`: 📋 **修复计划已制定**
  - 创建 `wiki/plan/05-user-resource-fix.md`
  - 方案：进程级GPU采集 + PID用户名映射
  - 6个任务步骤，待用户确认后执行
- `04-07 17:50`: ✅ **部署文档完成**
  - 创建 `docs/部署指南.md`
  - systemd 服务配置方案
  - 包含完整部署步骤、管理命令、故障排查
- `04-07 17:45`: ✅ **botpy intents配置修复 + 私聊支持**
  - 修复 `BotClient.__init__()` 缺少 intents 参数问题
  - 添加频道@消息、C2C私聊、DMS私信支持
  - 修复 `on_ready()` 方法签名错误
- `04-07 17:35`: ✅ **阶段2+阶段3 核心功能全部完成**
  - 集成30天自动清理到 PeriodicCollector
  - 添加 cleanup_interval 每日清理机制
  - 更新 config.yaml 添加 monitor 配置
  - 所有模块验证通过
- `04-07 17:15`: ✅ **阶段1基础框架开发完成**
  - 创建项目目录结构 (bot/, monitor/, utils/)
  - 完成 utils/config.py 配置加载模块
  - 完成 monitor/collector.py 数据采集模块
  - 完成 monitor/recorder.py 历史记录存储模块
  - 完成 monitor/formatter.py 格式化输出模块
  - 完成 bot/handler.py 命令处理模块
  - 完成 main.py 程序入口
  - 添加 requirements.txt 依赖文件
  - 验证代码可导入性和核心功能
- `04-07`: ✅ 架构更新为 Server Only v2.0
  - 移除SSH模块
  - 简化目录结构
  - 新增SQLite历史存储
  - 定时采集任务设计
- `04-07 16:30`: ✅ 开发环境配置完成
- `04-07 16:10`: ✅ 开发计划文档完成（架构+流程+模块+命令设计）
- `04-07 16:07`: Agent 完成项目WIKI记忆库初始化
- `04-07 15:43`: 项目创建，导入botpy submodule
