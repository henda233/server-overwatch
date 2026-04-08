# 🎮 QQ机器人命令扩展

> PLAN-010 | v1.0 | 2026-04-07 | status: pending

## 1. 扩展目标

在现有命令基础上，新增4个命令：
1. `/info <用户> <时间>` - 指定用户的历史记录
2. `/stats <时间>` - 统计摘要
3. `/top` - 按资源排序的用户列表
4. `/users` - 历史用户列表

---

## 2. 新增命令详情

### 2.1 `/info <用户> <时间>`

**功能**：查询指定用户的历史记录

**示例**：
```
输入: /info cxy 3d
输入: /info lgl 1w
输入: /info admin 1m
```

**输出**：
```
📅 cxy 过去 3天 的历史记录
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 统计: 145条有效记录 / 432条总记录（287条为空闲数据已过滤）

用户名   | 时间                | GPU   | 显存
cxy      | 04-07 15:50         | 92%   | 45.20GB
cxy      | 04-07 15:40         | 88%   | 44.80GB
cxy      | 04-07 15:30         | 85%   | 44.50GB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**解析规则**：
```
输入: "/info cxy 3d"
  → action: "info", target: "cxy", time_range: "3d"
```

---

### 2.2 `/stats <时间>`

**功能**：显示统计摘要（峰值/平均/使用时长）

**示例**：
```
输入: /stats 3d
输入: /stats 1w
输入: /stats 1m
```

**输出**：
```
📊 过去 3天 的资源使用统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 cxy
   GPU峰值: 92% | 平均: 65%
   显存峰值: 45.20GB | 平均: 32.50GB
   活跃时段: 累计72小时
   
👤 lgl
   GPU峰值: 45% | 平均: 30%
   显存峰值: 12.30GB | 平均: 8.20GB
   活跃时段: 累计24小时
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**统计指标**：
| 指标 | 说明 |
|------|------|
| GPU峰值 | 3天内GPU使用率最大值 |
| GPU平均 | 3天内GPU使用率平均值 |
| 显存峰值 | 3天内显存使用最大值 |
| 显存平均 | 3天内显存使用平均值 |
| 活跃时长 | 3天内有GPU任务的总小时数 |

---

### 2.3 `/top`

**功能**：按资源使用排序的用户列表（当前在线用户）

**示例**：
```
输入: /top
输入: /top gpu
输入: /top mem
```

**输出**：
```
🏆 当前资源使用排行榜
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
按 GPU 使用率排序:

🥇 cxy      | GPU: 92%  | 显存: 45.20GB | CPU: 80%
🥈 lgl      | GPU: 45%  | 显存: 12.30GB | CPU: 15%
🥉 user3    | GPU: 10%  | 显存: 2.50GB  | CPU: 5%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
在线用户: 3人
```

**排序选项**：
| 参数 | 排序依据 |
|------|----------|
| `/top` | 默认GPU使用率 |
| `/top gpu` | GPU使用率 |
| `/top mem` | 显存使用量 |
| `/top cpu` | CPU使用率 |

---

### 2.4 `/users`

**功能**：显示所有历史用户列表及简要统计

**示例**：
```
输入: /users
输入: /users 30d
```

**输出**：
```
👥 服务器用户统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 共 5 个用户（近30天）

用户名      | 最后活跃   | 总记录数 | 峰值GPU
cxy         | 04-07 15:50 |  1,234   | 92%
lgl         | 04-06 14:20 |    456   | 78%
test_user   | 04-05 10:00 |     89   | 15%
admin       | 04-01 09:00 |     12   | 5%
guest       | 03-28 18:00 |      5   | 0%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 3. 命令解析扩展

### 3.1 扩展 Command 数据类

```python
@dataclass
class Command:
    """命令数据结构（扩展版）"""
    action: str                        # "info", "help", "stats", "top", "users"
    target: Optional[str] = None       # 用户名 或 None
    time_range: Optional[str] = None   # "1d", "1w", "1m", None
    sort_by: Optional[str] = None      # "gpu", "mem", "cpu", None (用于top命令)
```

### 3.2 解析规则扩展

```
# 新增规则
输入: "/info cxy 3d"
  → action: "info", target: "cxy", time_range: "3d"

输入: "/stats 3d"
  → action: "stats", time_range: "3d"

输入: "/top"
  → action: "top", sort_by: None (默认gpu)

输入: "/top gpu"
  → action: "top", sort_by: "gpu"

输入: "/users"
  → action: "users", time_range: None (默认30天)

输入: "/users 30d"
  → action: "users", time_range: "30d"
```

### 3.3 歧义处理

**问题**：`cxy` 是用户名还是时间？

**解决方案**：按正则匹配优先级判断
1. 先匹配 `\d+[dDwWmM]` → 时间范围
2. 剩余部分 → 用户名

```
"/info cxy"     → 用户名 (无时间)
"/info 3d"      → 时间范围 (无用户)
/info cxy 3d"  → 用户名 + 时间范围
```

---

## 4. 实现设计

### 4.1 数据层 (`recorder.py`)

**新增方法**：

```python
def query_by_user(self, username: str, time_range: str) -> List[Dict]:
    """按用户名查询历史记录（过滤0值）"""
    
def get_user_stats(self, username: str, time_range: str) -> Dict:
    """获取用户统计信息"""
    
def get_all_users(self, days: int = 30) -> List[Dict]:
    """获取所有历史用户及其统计"""
```

### 4.2 格式化层 (`formatter.py`)

**新增方法**：

```python
def format_user_history(self, records: List[Dict], stats: Dict, 
                         username: str, time_range: str) -> str:
    """格式化指定用户的历史记录"""

def format_stats(self, stats: Dict, time_range: str) -> str:
    """格式化统计摘要"""

def format_top(self, data: List[Dict], sort_by: str) -> str:
    """格式化排行榜"""

def format_users(self, users: List[Dict], time_range: str) -> str:
    """格式化用户列表"""
```

### 4.3 业务层 (`handler.py`)

**修改方法**：

```python
def parse(self, text: str) -> Command:
    """扩展解析逻辑支持新命令"""

async def handle(self, message_text: str) -> str:
    """扩展处理逻辑"""
    # 新增分支
    if command.action == "stats":
        ...
    elif command.action == "top":
        ...
    elif command.action == "users":
        ...
```

---

## 5. 任务清单

| 序号 | 任务 | 文件 | 优先级 |
|------|------|------|--------|
| 1 | 扩展 Command 数据类 | `handler.py` | P0 |
| 2 | 扩展 parse() 解析逻辑 | `handler.py` | P0 |
| 3 | 扩展 handle() 处理逻辑 | `handler.py` | P0 |
| 4 | 实现 `query_by_user()` | `recorder.py` | P0 |
| 5 | 实现 `get_user_stats()` | `recorder.py` | P1 |
| 6 | 实现 `get_all_users()` | `recorder.py` | P1 |
| 7 | 实现 `format_user_history()` | `formatter.py` | P0 |
| 8 | 实现 `format_stats()` | `formatter.py` | P1 |
| 9 | 实现 `format_top()` | `formatter.py` | P1 |
| 10 | 实现 `format_users()` | `formatter.py` | P1 |
| 11 | 更新帮助信息 | `formatter.py` | P1 |
| 12 | 本地测试验证 | - | P0 |
| 13 | 部署到GPU服务器验证 | - | P1 |

---

## 6. 验收标准

- [ ] `/info cxy 3d` 正确返回指定用户的历史记录
- [ ] `/stats 3d` 显示正确的统计摘要
- [ ] `/top` 按GPU使用率正确排序
- [ ] `/top mem` 按显存正确排序
- [ ] `/users` 显示所有历史用户
- [ ] 帮助信息包含新命令说明
- [ ] 命令解析无歧义

---

## 7. 输出格式汇总

| 命令 | 输出内容 | 示例场景 |
|------|---------|----------|
| `/info` | 当前所有用户资源 | 查看谁在线 |
| `/info <用户>` | 指定用户当前资源 | 查看某人当前状态 |
| `/info <时间>` | 所有用户历史记录（精简） | 查看某时段概况 |
| `/info <用户> <时间>` | 指定用户历史记录（精简） | 查看某人某时段详情 |
| `/stats <时间>` | 统计摘要 | 快速了解峰值/平均 |
| `/top` | 排行榜 | 查看谁用最多 |
| `/users` | 用户列表 | 查看服务器有哪些用户 |

---

## 8. 关联文档

- [04-command-design.md](./04-command-design.md) - 命令设计（需更新）
- [09-history-compact-mode.md](./09-history-compact-mode.md) - 历史精简模式

---

**依赖**: 无
