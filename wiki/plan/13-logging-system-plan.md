---
plan_id: plan_13
related_request: 日志系统添加
status: completed
created_at: 2026-04-08 11:35:00
---
# 📋 执行计划：日志系统添加

## 🎯 目标与交付物

- **目标**：将简陋的日志系统升级为完善的日志系统
  - 记录命令调用情况（谁、什么时候、调用了什么命令、耗时）
  - 记录程序运行中的错误和异常（带堆栈信息）
  - 日志输出到文件（按日期分割）和控制台
- **验收标准**：
  - 日志文件存在于 `logs/` 目录
  - 命令调用后能在日志中查看到调用记录
  - 程序报错后能在日志中查看到错误堆栈

## 📋 现状分析

### 当前日志系统
```
# main.py 第30-34行
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```
- 仅配置了控制台输出，无文件日志
- 仅记录：启动/连接/错误（main.py）
- **缺失**：命令调用记录、错误堆栈、日志文件

### 当前命令处理（bot/handler.py）
- `parse()`: 解析命令
- `handle()`: 执行命令，无日志记录

## 🛠️ 任务分解

| 步骤ID | 任务描述 | 前置依赖 | 交付物 | 状态 |
|--------|----------|----------|--------|------|
| S1 | 创建 `utils/logger.py` 日志模块 | 无 | `utils/logger.py` | ⏳ 待执行 |
| S2 | 修改 `main.py` 集成新日志系统 | S1 | `main.py` | ⏳ 待执行 |
| S3 | 修改 `bot/handler.py` 添加命令日志 | S1 | `bot/handler.py` | ⏳ 待执行 |
| S4 | 添加异常处理装饰器/上下文 | S3 | `bot/handler.py` | ⏳ 待执行 |
| S5 | 测试日志输出 | S2+S3+S4 | 日志文件验证 | ⏳ 待执行 |

## 📝 详细方案

### S1: 创建 `utils/logger.py`

```python
"""
日志工具模块
支持：控制台输出 + 文件输出（按日期分割）
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logger(
    name: str,
    log_dir: str = "logs",
    level: int = logging.INFO
) -> logging.Logger:
    """
    创建日志记录器
    
    Args:
        name: 日志记录器名称
        log_dir: 日志目录
        level: 日志级别
    
    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 控制台 handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # 文件 handler（按天分割）
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now():%Y-%m-%d}.log")
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",      # 每天午夜分割
        interval=1,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
```

### S2: 修改 `main.py`

```python
# 修改第29-34行
from utils.logger import setup_logger

# 替换 basicConfig
logger = setup_logger("server_overwatch", log_dir="logs")
# 删除 basicConfig 相关代码

# 其他位置保持 logger 调用不变
```

### S3: 修改 `bot/handler.py`

```python
# 在 handle() 方法中添加命令日志
import time
from utils.logger import setup_logger

# 添加类属性
command_logger = setup_logger("command", log_dir="logs")

async def handle(self, message_text: str, user_id: str = "unknown") -> str:
    start_time = time.time()
    command = self.parse(message_text)
    
    try:
        # ... 原有命令处理逻辑 ...
        
        # 命令执行成功后记录
        elapsed = (time.time() - start_time) * 1000
        command_logger.info(
            f"命令调用 | 用户: {user_id} | 命令: {message_text} | 耗时: {elapsed:.0f}ms"
        )
    except Exception as e:
        # 错误时记录异常
        command_logger.error(
            f"命令失败 | 用户: {user_id} | 命令: {message_text} | 错误: {e}",
            exc_info=True  # 包含堆栈信息
        )
        raise
```

### S4: 修改 `main.py` 中的消息回调传递 user_id

```python
# 在 on_c2c_message_create, on_direct_message_create, on_at_message_create 中
# 将 user_id 传递给 handler.handle()

reply = await self.handler.handle(message.content, user_id=message.author.user_openid)
```

### S5: 日志验证

```bash
# 运行程序后检查
tail -f logs/$(date +%Y-%m-%d).log

# 预期输出示例：
# 2026-04-08 11:30:00 | INFO     | server_overwatch | 机器人已就绪: YuanFox
# 2026-04-08 11:30:05 | INFO     | command | 命令调用 | 用户: U123456 | 命令: /info | 耗时: 150ms
# 2026-04-08 11:30:10 | ERROR    | command | 命令失败 | 用户: U789 | 命令: /stats 1d | 错误: xxx
#   Traceback (most recent call last):
#     File "xxx", line 100, in handle
#     ...
```

## ⚠️ 注意事项

1. **用户ID获取**：botpy 消息对象中 `message.author.user_openid` 可能为空，需确认
2. **日志轮转**：`TimedRotatingFileHandler` 默认保留 7 天，可配置 `backupCount`
3. **敏感信息**：可选择是否在日志中记录 user_id

## 📊 预估工作量

- 代码修改：~50 行
- 测试验证：~10 分钟
- 总预计时间：~30 分钟
