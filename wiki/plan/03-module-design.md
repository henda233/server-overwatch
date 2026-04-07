# 📋 模块详细设计

> 文档编号: PLAN-003 | 版本: v2.0 | 创建时间: 2026-04-07 | 更新: 2026-04-07

## 1. 配置文件 (config.yaml)

```yaml
# QQ机器人配置
qq_bot:
  appid: "1903767942"
  secret: "your-secret-here"

# 监控配置
monitor:
  interval: 600          # 采集间隔(秒)，10分钟
  retention_days: 30     # 数据保留天数

# 日志配置
logging:
  level: "INFO"
  file: "logs/bot.log"
```

## 2. 配置加载 (utils/config.py)

```python
class Config:
    """配置管理器"""
    
    def load(self, path: str = "config.yaml") -> None:
        """加载配置文件"""
        ...
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项，支持点号分隔路径"""
        ...
```

## 3. 数据采集 (monitor/collector.py)

### 3.1 采集项

| 采集目标 | 命令 | 说明 |
|----------|------|------|
| GPU使用率 | `nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits` | 0-100 |
| 显存使用 | `nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits` | MB |
| 内存使用 | `free -b` | 字节 |
| CPU使用率 | `top -bn1` | 解析第一行 |
| 在线用户 | `who` | 当前登录用户 |

### 3.2 接口定义

```python
class Collector:
    """系统资源采集器"""
    
    def collect(self) -> dict:
        """采集所有资源，返回dict"""
        ...
    
    def collect_gpu(self) -> dict:
        """采集GPU信息"""
        ...
    
    def collect_memory(self) -> dict:
        """采集内存信息"""
        ...
    
    def collect_cpu(self) -> dict:
        """采集CPU信息"""
        ...
    
    def collect_users(self) -> List[str]:
        """采集在线用户名列表"""
        ...
```

## 4. 历史存储 (monitor/recorder.py)

### 4.1 数据库结构

```sql
CREATE TABLE resource_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    username TEXT NOT NULL,
    gpu_percent INTEGER,
    gpu_memory_mb INTEGER,
    cpu_percent INTEGER,
    memory_percent INTEGER
);

CREATE INDEX idx_timestamp ON resource_history(timestamp);
CREATE INDEX idx_username ON resource_history(username);
```

### 4.2 接口定义

```python
class Recorder:
    """历史记录管理器"""
    
    def __init__(self, db_path: str = "history.db"):
        ...
    
    def save(self, timestamp: datetime, username: str, data: dict) -> None:
        """保存单条记录"""
        ...
    
    def query(self, time_range: str) -> List[dict]:
        """查询历史数据
        Args:
            time_range: "1d", "1w", "1m"
        Returns:
            记录列表
        """
        ...
    
    def cleanup(self, retention_days: int = 30) -> int:
        """清理过期数据，返回删除条数"""
        ...
```

## 5. 结果格式化 (monitor/formatter.py)

### 5.1 输出格式

```
用户名 | GPU | 显存 | CPU | 内存
user1  | 80% | 20GB | 40% | 60%
user2  | 30% | 8GB  | 15% | 40%
```

### 5.2 接口定义

```python
class Formatter:
    """结果格式化器"""
    
    def format_realtime(self, data: dict) -> str:
        """格式化实时数据"""
        ...
    
    def format_history(self, records: List[dict], time_range: str) -> str:
        """格式化历史数据"""
        ...
    
    def format_help(self) -> str:
        """格式化帮助信息"""
        ...
```

## 6. 命令处理 (bot/handler.py)

### 6.1 命令格式

| 命令 | 功能 |
|------|------|
| `/info` | 查询当前所有在线用户资源使用 |
| `/info <用户名>` | 查询指定用户当前资源使用 |
| `/info 1d` | 查询过去1天的历史记录 |
| `/info 1w` | 查询过去1周的历史记录 |
| `/info 1m` | 查询过去1月的历史记录 |
| `/help` | 显示帮助信息 |

### 6.2 接口定义

```python
class CommandHandler:
    """命令处理器"""
    
    def __init__(self, collector: Collector, recorder: Recorder, formatter: Formatter):
        ...
    
    def parse(self, text: str) -> Command:
        """解析命令"""
        ...
    
    async def handle(self, message: Message) -> str:
        """处理消息，返回回复内容"""
        ...
```

### 6.3 命令解析逻辑

```python
class Command(NamedTuple):
    action: str      # "info", "help"
    target: str      # 用户名 或 None
    time_range: str  # "1d", "1w", "1m", None

def parse(text: str) -> Command:
    """解析命令文本"""
    text = text.strip()
    
    if text == "/help" or text == "help":
        return Command(action="help", target=None, time_range=None)
    
    if text.startswith("/info"):
        rest = text[5:].strip()
        # 解析剩余参数
        ...
```

## 7. 主入口 (main.py)

```python
import asyncio
from botpy import Client
from bot.handler import CommandHandler
from monitor.collector import Collector
from monitor.recorder import Recorder
from monitor.formatter import Formatter
from utils.config import Config
import threading

class BotClient(Client):
    def __init__(self, config: dict):
        self.handler = CommandHandler(...)
        super().__init__()
    
    async def on_at_message_create(self, message: Message):
        reply = await self.handler.handle(message)
        await message.reply(content=reply)

def start_periodic_collector(recorder: Recorder, interval: int):
    """启动定时采集任务"""
    def run():
        while True:
            collector = Collector()
            data = collector.collect()
            for username, user_data in data.items():
                recorder.save(datetime.now(), username, user_data)
            time.sleep(interval)
    threading.Thread(target=run, daemon=True).start()

def main():
    config = Config()
    config.load()
    
    recorder = Recorder()
    start_periodic_collector(recorder, config.get("monitor.interval", 600))
    
    client = BotClient(config)
    client.run(appid=config.get("qq_bot.appid"),
               secret=config.get("qq_bot.secret"))

if __name__ == "__main__":
    main()
```

## 8. 目录结构最终版

```
server-overwatch/
├── config.yaml              # 配置文件
├── main.py                  # 程序入口
├── bot/                     # QQ机器人模块
│   └── handler.py           # 命令处理
├── monitor/                 # 系统监控模块
│   ├── collector.py         # 实时数据采集
│   ├── recorder.py          # 历史记录存储
│   └── formatter.py          # 格式化输出
├── utils/                   # 工具模块
│   └── config.py            # 配置加载
└── requirements.txt         # 依赖
```

---

**关联文档**: [系统架构](./01-architecture.md) | [开发流程](./02-development-flow.md) | [命令设计](./04-command-design.md)
