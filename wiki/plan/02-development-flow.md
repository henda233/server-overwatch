# 🚀 开发流程

> 文档编号: PLAN-002 | 版本: v2.0 | 创建时间: 2026-04-07 | 更新: 2026-04-07

## 1. 开发环境

| 项目 | 说明 |
|------|------|
| 本地系统 | Arch Linux |
| 部署系统 | GPU服务器 (Ubuntu 24.04) |
| 代码同步 | Git |
| 包管理 | uv |

## 2. 开发流程

```
┌──────────────┐    git commit    ┌──────────────┐
│  本地开发     │ ──────────────→ │  服务器部署   │
│  Arch Linux  │                  │  GPU服务器   │
└──────────────┘                  └──────────────┘
       ↑                                  │
       └────────────── git pull ──────────┘
```

**步骤**:
1. 本地开发、测试
2. `git commit` 提交
3. 服务器 `git pull` 拉取
4. 重启 systemd 服务

## 3. 开发阶段

```
阶段1: 基础框架          阶段2: 核心功能          阶段3: 历史功能          阶段4: 部署
───────────────          ───────────────          ───────────────          ─────────────
• 项目结构               • QQ机器人连接            • SQLite存储             • systemd配置
• 配置管理               • 实时数据采集            • 30天自动清理           • 启动测试
• 日志系统               • 命令解析                • 历史查询
```

### 阶段 1: 基础框架

- [ ] 创建项目目录结构
- [ ] 配置管理 (`utils/config.py`)
- [ ] `config.yaml` 配置文件

### 阶段 2: 核心功能

- [ ] QQ机器人连接 (`bot/handler.py`)
- [ ] 数据采集 (`monitor/collector.py`)
- [ ] 命令解析 (`/info`, `/help`)
- [ ] 结果格式化 (`monitor/formatter.py`)

### 阶段 3: 历史功能

- [ ] SQLite数据库 (`monitor/recorder.py`)
- [ ] 定时采集任务 (每10分钟)
- [ ] 30天自动清理
- [ ] 历史查询 (`/info 1d/1w/1m`)

### 阶段 4: 部署

- [ ] systemd 服务配置
- [ ] 服务器测试
- [ ] 文档完善

## 4. 本地开发指南

### 4.1 环境准备

```bash
# 本地安装依赖
uv sync

# 配置文件
cp config.yaml.example config.yaml
# 编辑 config.yaml 填入机器人凭证
```

### 4.2 运行测试

```bash
# 启动机器人
uv run python main.py
```

### 4.3 部署到服务器

```bash
# 服务器上
cd /path/to/server-overwatch
git pull
uv sync
sudo systemctl restart server-overwatch
```

## 5. 开发优先级

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | QQ机器人连接 | 核心功能 |
| P0 | 实时数据采集 | GPU/CPU/内存/用户 |
| P0 | 命令解析 | `/info`, `/help` |
| P1 | 结果格式化 | 表格输出 |
| P1 | SQLite存储 | 历史记录 |
| P1 | 定时任务 | 每10分钟采集 |
| P2 | 自动清理 | 30天过期数据 |
| P2 | systemd配置 | 服务管理 |

---

**关联文档**: [系统架构](./01-architecture.md) | [模块详细设计](./03-module-design.md) | [命令设计](./04-command-design.md)
