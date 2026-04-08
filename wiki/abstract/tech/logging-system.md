---
abstract_id: abs_013
source_contents:
  - "server-overwatch::/utils/logger.py"
  - "server-overwatch::/main.py"
  - "server-overwatch::/bot/handler.py"
dependencies:
  - "abs_001"
  - "abs_002"
created_at: 2026-04-08 11:45:00
updated_at: 2026-04-08 11:45:00
audit_status: pending
---
# 📖 摘要：日志系统

## 🎯 核心结论与关键信息
- **日志系统**：使用 `utils/logger.py` 提供统一的日志记录器
- **日志格式**：`%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`
- **双输出**：控制台 + 文件（按日期分割，存放在 `logs/` 目录）
- **命令日志**：记录每次命令调用（用户ID、命令内容、耗时）
- **异常日志**：记录错误堆栈信息（`exc_info=True`）

## 📋 内容概述
> 升级日志系统：控制台+文件双输出、命令调用记录、异常堆栈记录。

## 🔗 依赖与影响链
- **上游依赖**：`abs_001`（项目概述）、`abs_002`（botpy SDK）
- **下游被依赖**：`main.py`、`bot/handler.py`
- **变更扩散评估**：高（影响所有模块的日志输出）

## 🛠️ 实现细节

### utils/logger.py
```python
def setup_logger(name: str, log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger
```
- `TimedRotatingFileHandler`：每天午夜自动分割日志
- 避免重复添加 handler（检查 `logger.handlers`）

### bot/handler.py
- `handle()` 方法签名：`async def handle(self, message_text: str, user_id: str = "unknown") -> str`
- finally 块记录命令调用日志
- except 块记录错误堆栈

### main.py
- 替换 `logging.basicConfig` 为 `setup_logger()`
- 三个消息回调均传递 `user_id` 参数
