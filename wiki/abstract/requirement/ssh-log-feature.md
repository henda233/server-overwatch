---
abstract_id: abs_015
source_contents:
  - "server-overwatch::/wiki/request/req-ssh-connection-log-feature.md"
  - "server-overwatch::/monitor/ssh_recorder.py"
dependencies:
  - "abs_005" (requirement/core.md)
created_at: 2026-04-08 20:45:00
updated_at: 2026-04-09 10:50:00
audit_status: pending
---
# 📖 摘要：SSH连接记录功能需求

## 🎯 核心结论与关键信息

### 功能目标
- 记录SSH连接信息（用户、IP、成功/失败次数）
- 通过QQ机器人 `/ssh` 命令查询

### 技术要点
| 项目 | 详情 |
|------|------|
| 日志来源 | `/var/log/auth.log` |
| 数据库 | `ssh_history.db` |
| 保留周期 | 90天 |
| 采集方式 | 定时采集（每分钟） |

### ✅ 已解决的技术问题
- **日志格式兼容**：支持两种auth.log格式
  - 传统syslog：`Apr  8 20:30:00 hostname sshd[...]`
  - ISO 8601：`2026-04-09T10:59:28.898309+08:00 hostname sshd[...]`
- **时区格式兼容**：支持 `+0800` 和 `+08:00` 两种时区格式
- **权限问题**：用户需加入 `adm` 组读取auth.log

### 命令格式
| 命令 | 说明 |
|------|------|
| `/ssh 1d` | 最近1天全部记录，按次数降序 |
| `/ssh 1d lgl` | 按用户过滤 |
| `/ssh 1d 172.19.106.183` | 按IP过滤 |
| `/ssh 1d lgl@172.19.106.183` | 用户+IP过滤（且关系） |
| `/ssh 1d 2` | 分页显示 |

### 日志解析规则
- 成功登录：`Accepted password for <user> from <ip>`
- 失败登录：`Failed password for <user> from <ip>`

## 📋 内容概述
新增SSH连接记录功能，包括数据采集、存储、查询和展示。需要新建 `ssh_recorder.py` 模块，复用现有架构。

## 🔗 依赖与影响链
- **上游依赖**: 
  - `abs_005` (核心功能需求+命令设计)
  - `abs_014` (分页功能)
- **下游被依赖**: 
  - `/ssh` 命令解析
  - SSH历史数据库
- **变更扩散评估**: 中（新增独立模块）
