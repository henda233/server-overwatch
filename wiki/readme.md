# WIKI 概述

> 本WIKI是GPU服务器用户监控项目的记忆库，包含项目的技术栈、架构设计、关键配置和开发规范。

## project_mapping

```yaml
project_mapping:
  server-overwatch: /home/yuanlin/桌面/GPU server/服务器用户监控项目/server-overwatch
  botpy: /home/yuanlin/桌面/GPU server/服务器用户监控项目/server-overwatch/botpy
```

## 项目简介

GPU服务器用户监控程序：通过QQ机器人接收用户命令，查询远程GPU服务器上的用户登录情况和资源使用情况（CPU、GPU、内存、显存）。

## 技术栈

| 技术 | 说明 |
|------|------|
| Python | 开发语言 |
| uv | 包管理器，创建虚拟环境 |
| botpy | QQ机器人Python SDK |

## 目录结构

```
server-overwatch/
├── README.md              # 项目概述
├── botpy/                  # QQ机器人SDK（作为git submodule）
│   ├── README.md
│   ├── examples/           # 示例代码
│   └── docs/               # SDK文档
├── docs/                   # 项目文档
│   └── 远程GPU服务器信息.md
└── wiki/                   # WIKI记忆库（本目录）
```

## 核心依赖

- **botpy**: `pip install qq-botpy`（QQ机器人SDK）
- **python**: 3.8+
- **uv**: 项目包管理工具

## QQ机器人配置

机器人配置通过 `config.yaml` 文件管理：
- `appid`: 机器人应用ID
- `secret`: 机器人密钥

配置示例见 `botpy/examples/config.example.yaml`

## 远程GPU服务器

- **系统**: Ubuntu 24.04.4 LTS
- **GPU**: NVIDIA RTX PRO 6000 Black（98GB显存）
- **CUDA**: 13.0
- **驱动**: 580.126.09
- **特点**: 普通用户可执行docker命令，无外网IP

## 核心约束

1. **禁止自主执行**: Agent不得自主运行代码文件，必须由用户手动执行并反馈结果
2. **记忆库优先**: 所有任务执行前必须查阅wiki记忆库
3. **摘要同步**: 代码/配置变更后必须同步更新wiki摘要
4. **索引维护**: 新增内容后必须更新 `wiki/index.md`
