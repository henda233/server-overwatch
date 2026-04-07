---
abstract_id: abs_002
source_contents:
  - "server-overwatch::/botpy/README.md"
  - "server-overwatch::/botpy/docs/事件监听.md"
  - "server-overwatch::/botpy/examples/demo_at_reply.py"
dependencies:
  - "abs_003"
created_at: 2026-04-07 16:07:00
updated_at: 2026-04-07 16:07:00
audit_status: approved
---

# 📖 摘要：botpy技术栈

## 🎯 核心结论与关键信息

- **安装方式**: `pip install qq-botpy`
- **Python版本**: 3.8+
- **核心类**: 继承 `botpy.Client` 实现机器人逻辑
- **事件监听**: 通过覆写 `on_*` 方法处理各类事件

### 核心代码结构

```python
import botpy
from botpy.message import Message

class MyClient(botpy.Client):
    async def on_at_message_create(self, message: Message):
        await message.reply(content="回复内容")

# 启动机器人
intents = botpy.Intents(public_guild_messages=True)
client = MyClient(intents=intents)
client.run(appid="appid", secret="secret")
```

### 常用事件监听

| 事件方法 | 说明 | 需要开启的Intents |
|---------|------|------------------|
| `on_at_message_create` | 收到@机器人消息 | `public_guild_messages` |
| `on_direct_message_create` | 收到私信 | `direct_message` |
| `on_message_create` | 频道消息（私域） | `guild_messages` |

## 📋 内容概述

botpy是腾讯官方的QQ机器人Python SDK，提供基于websocket的事件监听机制。机器人通过继承Client类并覆写事件处理方法来实现功能响应。配置通过YAML文件存储appid和secret。

## 🔗 依赖与影响链

- **上游依赖**: 
  - `abs_003`（QQ机器人配置）
- **下游被依赖**: 
  - `abs_005`（核心需求 - 命令处理模块）
- **变更扩散评估**: 中（技术选型已确定）

## 🛡️ 审计记录（User Only）

- [ ] 用户已核对关键信息
- 📝 修改意见/确认标记：`<首次创建，暂无>`
