---
abstract_id: abs_001
source_contents:
  - "server-overwatch::/README.md"
  - "server-overwatch::/wiki/plan/01-architecture.md"
dependencies: []
created_at: 2026-04-07 16:07:00
updated_at: 2026-04-07 16:07:00
audit_status: approved
---

# 📖 摘要：项目概述

## 🎯 核心结论与关键信息

- **项目名称**: GPU服务器用户监控程序（server-overwatch）
- **架构模式**: Server Only（机器人直接运行在GPU服务器上）
- **核心功能**: 通过QQ机器人接收用户命令，查询本地GPU服务器的用户登录情况和资源使用情况
- **监控范围**: GPU使用率、显存、CPU使用率、内存使用率
- **时间维度**: 实时查询 + 历史查询（1天/1周/1月）

## 📋 内容概述

本项目旨在为GPU服务器用户提供一个基于QQ机器人的监控工具。

- **开发环境**: Arch Linux 本地开发 → Git同步 → 服务器部署
- **部署方式**: systemd 服务
- **数据存储**: SQLite本地数据库（30天保留）
- **采集间隔**: 每10分钟

### 目录结构

```
server-overwatch/
├── config.yaml          # 配置文件
├── main.py              # 程序入口
├── bot/handler.py       # QQ命令处理
├── monitor/             # 监控模块
│   ├── collector.py    # 数据采集
│   ├── recorder.py      # 历史存储
│   └── formatter.py     # 格式化输出
├── utils/config.py      # 配置加载
└── requirements.txt     # 依赖
```

## 🔗 依赖与影响链

- **上游依赖**: 无
- **下游被依赖**: 
  - `abs_002`（botpy技术栈）
  - `abs_004`（GPU服务器信息）
  - `abs_005`（核心需求）

## 🛡️ 审计记录（User Only）

- [x] 2026-04-07: 项目概述已更新为 Server Only 架构
