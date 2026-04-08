# 📦 历史记录精简模式 & 统一 UI 优化

> PLAN-009 | v1.1 | 2026-04-08 | status: completed

## 1. 背景问题

### 1.1 问题描述

**问题A：历史查询冗余数据**
当前 `/info <number>d/w/m` 命令返回所有原始记录（包括600s间隔采集的空闲数据）。

**问题B：ASCII表格对齐问题**
当前使用 `|` 分隔符的表格在手机端QQ显示时，因非等宽字体导致对齐错位。

### 1.2 数据量估算

| 时间范围 | 采集点数/用户 | 说明 |
|----------|--------------|------|
| 1天 | 144条 | 每10分钟采集 |
| 3天 | 432条 | - |
| 1周 | 1008条 | - |
| 1月 | 4320条 | - |

**有效率假设**：
- 活跃用户：~30% 有GPU任务
- 空闲用户：0% 有GPU任务
- 结果：大量0值记录

### 1.3 根因分析

```
采集器按固定间隔采集数据 → 用户可能空闲 → 数据全为0 → 历史记录包含大量无效数据
```

```
ASCII表格依赖等宽字体 → 手机QQ使用非等宽字体 → 列对齐错位
```

---

## 2. 解决方案

### 2.1 统一单行文字格式（推荐）

**设计原则**：
- 使用纯文字标签 + 空格分隔，不依赖等宽字体
- 每行数据独立完整，不依赖对齐
- 信息分层：统计摘要 → 数据行 → 操作提示
- 实时查询与历史查询风格统一

### 2.2 过滤规则

```
记录有效条件：
  gpu_memory_mb > 0  （有显存占用）
```

> **说明**：CPU/内存可能因系统后台进程非0，所以仅用显存作为主要判断依据。

---

## 3. 输出示例

### 3.1 实时查询 `/info`

```
当前服务器资源使用情况（在线2人）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cxy    GPU: 92.0%  显存: 45.2GB/98GB  CPU: 85.2%  内存: 72.1%
lgl    GPU: 45.0%  显存: 12.3GB/98GB  CPU: 52.1%  内存: 65.3%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
提示: /info cxy 查看指定用户详情
```

### 3.2 历史查询 `/info 3d`

```
过去 3天 的历史记录（精简版）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
统计: 152条有效 / 1296条总（已过滤1144条空闲）
CPU峰值: 85.2%  |  内存峰值: 72.1%

04-07 15:50  cxy     GPU: 92.0%  显存: 45.2GB
04-07 15:40  cxy     GPU: 88.0%  显存: 44.8GB
04-07 15:30  cxy     GPU: 85.0%  显存: 44.5GB
04-06 14:20  lgl     GPU: 45.0%  显存: 12.3GB
... 还有 148 条记录
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
提示: /info cxy 3d 查看指定用户的详细记录
```

### 3.3 指定用户历史 `/info cxy 3d`

```
cxy 过去 3天 的历史记录（精简版）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
统计: 145条有效 / 432条总（已过滤287条空闲）
CPU峰值: 85.2%  |  内存峰值: 72.1%

04-07 15:50  GPU: 92.0%  显存: 45.2GB  CPU: 85.2%  内存: 72.1%
04-07 15:40  GPU: 88.0%  显存: 44.8GB  CPU: 82.1%  内存: 71.8%
04-07 15:30  GPU: 85.0%  显存: 44.5GB  CPU: 78.5%  内存: 70.2%
04-07 15:20  GPU: 80.0%  显存: 43.0GB  CPU: 75.0%  内存: 68.5%
... 还有 141 条记录
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
提示: /info cxy 查看该用户当前状态
```

---

## 4. 实现设计

### 4.1 格式化模板

```python
# 实时查询模板
"{username:<6}  GPU: {gpu:>5.1f}%  显存: {mem_str:<12}  CPU: {cpu:>5.1f}%  内存: {mem:>5.1f}%"

# 历史查询模板（多用户）
"{timestamp}  {username:<6}  GPU: {gpu:>5.1f}%  显存: {gpu_mem_gb:.1f}GB"

# 历史查询模板（单用户）
"{timestamp}  GPU: {gpu:>5.1f}%  显存: {gpu_mem_gb:.1f}GB  CPU: {cpu:>5.1f}%  内存: {mem:>5.1f}%"
```

### 4.2 数据层修改 (`recorder.py`)

新增方法 `query_filtered()`：

```python
def query_filtered(self, time_range: str, username: Optional[str] = None) -> Tuple[List[Dict], Dict]:
    """
    查询历史数据（过滤0值）
    
    Returns:
        (过滤后的记录列表, 统计信息Dict)
        统计信息: {
            "total": int,      # 总记录数
            "valid": int,      # 有效记录数
            "filtered": int,   # 被过滤的0值记录数
            "cpu_peak": float, # CPU峰值
            "mem_peak": float  # 内存峰值
        }
    """
```

### 4.3 格式化层修改 (`formatter.py`)

#### 4.3.1 修改 `format_realtime()` 方法

```python
def format_realtime(self, data: Dict[str, Dict]) -> str:
    """格式化实时数据（统一单行文字格式）"""
    if not data:
        return "📭 当前没有在线用户"
    
    lines = []
    lines.append(f"当前服务器资源使用情况（在线{len(data)}人）")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    
    for username, stats in data.items():
        gpu = stats.get("gpu_percent", 0)
        gpu_mem = stats.get("gpu_memory_mb", 0)
        gpu_mem_total = stats.get("gpu_memory_total_mb", 0)
        cpu = stats.get("cpu_percent", 0)
        mem = stats.get("memory_percent", 0)
        
        # 显存格式化
        gpu_mem_gb = gpu_mem / 1024 if gpu_mem else 0
        total_gb = gpu_mem_total / 1024 if gpu_mem_total else 0
        if total_gb > 0:
            mem_str = f"{gpu_mem_gb:.1f}GB/{total_gb:.0f}GB"
        else:
            mem_str = f"{gpu_mem:.0f}MB"
        
        # 单行格式
        line = f"{username[:6]:<6}  GPU: {gpu:>5.1f}%  显存: {mem_str:<12}  CPU: {cpu:>5.1f}%  内存: {mem:>5.1f}%"
        lines.append(line)
    
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("提示: /info <用户> 查看指定用户详情")
    
    return "\n".join(lines)
```

#### 4.3.2 新增 `format_history_compact()` 方法

```python
def format_history_compact(self, records: List[Dict], stats: Dict, 
                           time_range: str, username: Optional[str] = None) -> str:
    """格式化精简版历史数据（统一单行文字格式）
    
    Args:
        records: 过滤后的记录列表
        stats: 统计信息（total, valid, filtered, cpu_peak, mem_peak）
        time_range: 查询的时间范围
        username: 指定用户时显示用户名前缀，None时显示多用户模式
    """
    if not records:
        return f"📭 暂无 {time_range} 的历史记录"
    
    lines = []
    
    # 标题行
    if username:
        lines.append(f"{username} 过去 {time_range} 的历史记录（精简版）")
    else:
        lines.append(f"过去 {time_range} 的历史记录（精简版）")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # 统计行
    lines.append(f"统计: {stats['valid']}条有效 / {stats['total']}条总（已过滤{stats['filtered']}条空闲）")
    lines.append(f"CPU峰值: {stats['cpu_peak']:.1f}%  |  内存峰值: {stats['mem_peak']:.1f}%")
    lines.append("")
    
    # 数据行（限制15条）
    max_rows = 15
    for record in records[:max_rows]:
        timestamp = record.get("timestamp", "")[5:16]  # MM-DD HH:MM
        gpu = record.get("gpu_percent", 0)
        gpu_mem_gb = record.get("gpu_memory_mb", 0) / 1024
        
        if username:
            # 单用户模式：无需显示用户名
            line = f"{timestamp}  GPU: {gpu:>5.1f}%  显存: {gpu_mem_gb:.1f}GB  CPU: {record.get('cpu_percent', 0):>5.1f}%  内存: {record.get('memory_percent', 0):>5.1f}%"
        else:
            # 多用户模式：显示用户名
            user = record.get("username", "")[:6]
            line = f"{timestamp}  {user:<6}  GPU: {gpu:>5.1f}%  显存: {gpu_mem_gb:.1f}GB"
        
        lines.append(line)
    
    # 截断提示
    if len(records) > max_rows:
        lines.append(f"... 还有 {len(records) - max_rows} 条记录")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # 操作提示
    if username:
        lines.append(f"提示: /info {username} 查看该用户当前状态")
    else:
        lines.append("提示: /info <用户> <时间> 查看指定用户的详细记录")
    
    return "\n".join(lines)
```

### 4.4 业务层修改 (`handler.py`)

```python
# 历史查询逻辑修改
async def handle_info(self, command):
    if command.is_realtime:
        # 实时查询
        data = self.collector.get_current_data()
        return self.formatter.format_realtime(data)
    elif command.target and command.time_range:
        # 指定用户 + 时间范围: /info cxy 3d
        records, stats = self.recorder.query_filtered(command.time_range, command.target)
        return self.formatter.format_history_compact(records, stats, command.time_range, command.target)
    elif command.time_range:
        # 仅时间范围: /info 3d
        records, stats = self.recorder.query_filtered(command.time_range)
        return self.formatter.format_history_compact(records, stats, command.time_range)
    elif command.target:
        # 仅用户: /info cxy
        data = self.collector.get_user_data(command.target)
        return self.formatter.format_user_detail(command.target, data)
    else:
        # 无参数: /info
        data = self.collector.get_current_data()
        return self.formatter.format_realtime(data)
```

---

## 5. 设计要点总结

| 要点 | 说明 |
|------|------|
| **分隔符** | 空格分隔，不依赖等宽字体 |
| **标签固定** | `GPU:` `显存:` `CPU:` `内存:` 等标签固定位置 |
| **对齐方式** | 数字右对齐，文字左对齐 |
| **信息分层** | 统计行 → 数据行 → 提示行 |
| **截断处理** | 超过15行显示 `... 还有 N 条记录` |
| **风格统一** | 实时查询与历史查询使用相同的设计语言 |

---

## 6. 任务清单

| 序号 | 任务 | 文件 | 优先级 |
|------|------|------|--------|
| 1 | 修改 `format_realtime()` 为单行文字格式 | `formatter.py` | P0 |
| 2 | 新增 `format_history_compact()` 方法 | `formatter.py` | P0 |
| 3 | 修改 `format_user_detail()` 保持风格一致 | `formatter.py` | P0 |
| 4 | 新增 `query_filtered()` 方法 | `recorder.py` | P0 |
| 5 | 修改 `handler.py` 历史查询逻辑 | `handler.py` | P0 |
| 6 | 更新帮助信息 | `formatter.py` | P1 |
| 7 | 本地测试验证 | - | P0 |
| 8 | 部署到GPU服务器验证 | - | P1 |

---

## 7. 验收标准

- [ ] `/info` 实时查询使用统一单行文字格式
- [ ] `/info 3d` 自动过滤0值记录并使用新格式
- [ ] `/info cxy 3d` 单用户模式显示完整CPU/内存信息
- [ ] 显示统计摘要（有效/总/过滤数 + CPU/内存峰值）
- [ ] 手机端QQ显示正常，无对齐错位
- [ ] PC端QQ显示正常
- [ ] 数据库查询性能无明显下降

---

## 8. 关联文档

- [04-command-design.md](./04-command-design.md) - 命令设计
- [03-module-design.md](./03-module-design.md) - 模块设计
- [10-command-extension.md](./10-command-extension.md) - 命令扩展（依赖）

---

**依赖**: PLAN-010（命令扩展）