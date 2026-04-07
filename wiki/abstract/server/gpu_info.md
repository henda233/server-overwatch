---
abstract_id: abs_004
source_contents:
  - "server-overwatch::/docs/远程GPU服务器信息.md"
dependencies: []
created_at: 2026-04-07 16:07:00
updated_at: 2026-04-07 16:07:00
audit_status: approved
---

# 📖 摘要：远程GPU服务器信息

## 🎯 核心结论与关键信息

### 硬件配置

| 项目 | 规格 |
|------|------|
| 系统 | Ubuntu 24.04.4 LTS |
| GPU | NVIDIA RTX PRO 6000 Black |
| 显存 | 98,787 MiB（约96GB） |
| CUDA版本 | 13.0 |
| 驱动版本 | 580.126.09 |
| 电源功率 | 600W |

### 环境特点

- ✅ 普通用户可执行docker命令
- ⚠️ 服务器没有外网IP
- ⚠️ 需要内网或VPN连接

### 监控命令参考

```bash
# 查看GPU状态
nvidia-smi

# 查看用户登录情况
who
last
w

# 查看系统资源
top
htop
free -h
```

## 📋 内容概述

目标GPU服务器运行Ubuntu系统，配备单块RTX PRO 6000 Black显卡。由于无外网IP，监控程序需要通过内网或跳板机连接。普通用户权限足够执行docker和基础监控命令。

## 🔗 依赖与影响链

- **上游依赖**: 无
- **下游被依赖**: 
  - `abs_005`（核心需求 - 监控命令设计）
- **变更扩散评估**: 中（服务器配置变更需同步更新）

## 🛡️ 审计记录（User Only）

- [ ] 用户已核对关键信息
- 📝 修改意见/确认标记：`<首次创建，暂无>`
