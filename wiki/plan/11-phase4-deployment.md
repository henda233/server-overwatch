---
plan_id: plan_phase4_20260408
related_request: "阶段4部署"
status: completed
created_at: 2026-04-08 11:35:00
---
# 📋 执行计划：阶段4 - 部署

## 🎯 目标与交付物

- **最终交付**：GPU服务器上运行 server-overwatch systemd服务
- **验收标准**：
  1. `sudo systemctl status server-overwatch` 显示 `active (running)`
  2. QQ机器人成功接收/发送消息
  3. `/users` 等命令返回正常数据

## 🛠️ 任务分解与执行流

| 步骤ID | 任务描述 | 前置依赖 | 交付物/修改路径 | 需用户确认? | 状态 |
|--------|----------|----------|-----------------|-------------|------|
| `S1` | 服务器环境检查 | 无 | 确认SSH连接、Python版本、系统命令 | ✅ 是 | ⏳ |
| `S2` | 创建gpu-monitor用户 | S1 | 服务器用户创建 | ✅ 是 | ⏳ |
| `S3` | 上传程序文件 | S2 | `/opt/server-overwatch/` | ✅ 是 | ⏳ |
| `S4` | 安装依赖 | S3 | `.venv` + `uv sync` | ✅ 是 | ⏳ |
| `S5` | 配置config.yaml | S4 | 填写appid/secret | ✅ 是 | ⏳ |
| `S6` | 创建systemd服务 | S5 | `/etc/systemd/system/server-overwatch.service` | ✅ 是 | ⏳ |
| `S7` | 启动服务并验证 | S6 | 服务运行 + 机器人响应 | ✅ 是 | ⏳ |

## 📝 详细执行步骤

### S1: 服务器环境检查

```bash
# SSH连接到服务器后执行
python3 --version          # 需 >= 3.8
which nvidia-smi            # 需存在
which uv || pip3 install uv  # 安装uv
```

### S2: 创建运行用户

```bash
sudo useradd -r -s /bin/bash -m -d /home/gpu-monitor gpu-monitor
```

### S3: 上传程序

```bash
# 本地执行打包
cd /home/yuanlin/桌面/GPU\ server/服务器用户监控项目/server-overwatch
tar --exclude='.venv' --exclude='__pycache__' --exclude='.git' -czvf overwatch.tar.gz .

# 上传到服务器（用户需执行）
scp overwatch.tar.gz 服务器用户@服务器IP:/tmp/
ssh 服务器用户@服务器IP "sudo mkdir -p /opt/server-overwatch && sudo tar -xzvf /tmp/overwatch.tar.gz -C /opt/server-overwatch && sudo chown -R gpu-monitor:gpu-monitor /opt/server-overwatch"
```

### S4: 安装依赖

```bash
sudo -u gpu-monitor bash -c "cd /opt/server-overwatch && uv venv .venv"
sudo -u gpu-monitor bash -c "cd /opt/server-overwatch && uv sync"
```

### S5: 配置程序

```bash
# 编辑配置文件（用户提供真实appid/secret）
sudo -u gpu-monitor nano /opt/server-overwatch/config.yaml
```

### S6: 创建systemd服务

```bash
# 创建service文件
sudo nano /etc/systemd/system/server-overwatch.service
# 粘贴部署指南中的service内容

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable server-overwatch
```

### S7: 启动并验证

```bash
# 启动服务
sudo systemctl start server-overwatch

# 检查状态
sudo systemctl status server-overwatch

# 查看日志
sudo journalctl -u server-overwatch -f

# 测试机器人（QQ发送 /users 命令）
```

## ⚠️ 风险与约束声明

- **用户需提供**：服务器SSH访问信息（IP/用户名/密码或密钥）
- **用户需提供**：QQ机器人 appid 和 secret
- **回滚锚点**：服务配置前记录当前状态
