# 📋 修复计划：按用户区分CPU/内存/GPU使用率

> PLAN-007 | v1.0 | 2026-04-07 | status: draft

## 🎯 问题描述

### 现象

1. **GPU使用率**：所有用户显示 0%（当前已能正确获取显存）
2. **CPU/内存**：所有在线用户显示相同的系统级数据

### 根本原因

| 问题 | 根因 | 当前数据源 |
|------|------|-----------|
| GPU使用率 | `nvidia-smi --query-compute-apps` 不支持 `utilization.gpu` 字段 | 无 |
| CPU/内存 | `collect()` 直接使用系统级 `collect_cpu()` 和 `collect_memory()` 结果 | 所有用户相同 |

### 技术验证

```bash
# nvidia-smi --query-compute-apps 支持的字段（不含GPU使用率）
timestamp, gpu_name, gpu_bus_id, gpu_serial, gpu_uuid, pid, process_name, used_gpu_memory

# 测试结果
nvidia-smi --query-compute-apps=pid,used_memory,utilization.gpu --format=csv,noheader,nounits
# ERROR: Field "utilization.gpu" is not a valid field to query.
```

---

## 📌 修复方案

### 方案：按显存比例分配 GPU 使用率

**思路**：
1. 获取全局 GPU 使用率 (`nvidia-smi --query-gpu=utilization.gpu`)
2. 获取每个用户的显存使用量（已有）
3. 按显存比例分配 GPU 使用率

**公式**：
```
用户GPU使用率 = 全局GPU使用率 × (用户显存使用量 / 全局显存使用量)
```

**示例**：
| 指标 | 全局 | 用户A | 用户B |
|------|------|-------|-------|
| GPU使用率 | 80% | 60% | 20% |
| 显存使用 | 60000MB | 45000MB | 15000MB |
| 占比 | 100% | 75% | 25% |

**计算**：
- 用户A: `80% × 45000/60000 = 60%` ✅
- 用户B: `80% × 15000/60000 = 20%` ✅

### CPU/内存：按进程聚合

**思路**：复用 `ps aux` 数据（已有 PID→用户 映射）

`ps aux` 输出格式：
```
USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND
```

**修改 `get_pid_username_map()`**：
- 同时提取 `%CPU` 和 `%MEM`
- 按用户聚合

---

## 🛠️ 任务分解

| 步骤ID | 任务描述 | 前置依赖 | 交付物/修改路径 | 状态 |
|--------|---------|---------|----------------|------|
| `S1` | 分析 ps aux 数据结构 | 无 | 字段解析 | ✅ 已完成 |
| `S2` | 修改 `get_pid_username_map()` 为 `get_process_info()` | S1 | `monitor/collector.py` | ⏳ 待执行 |
| `S3` | 实现按用户聚合 CPU/内存 | S2 | `monitor/collector.py` | ⏳ 待执行 |
| `S4` | 实现按显存比例分配 GPU 使用率 | S2 | `monitor/collector.py` | ⏳ 待执行 |
| `S5` | 本地测试验证 | S3+S4 | 测试输出 | ⏳ 待执行 |

---

## 📂 修改文件清单

| 文件路径 | 修改类型 | 修改说明 |
|---------|---------|---------|
| `monitor/collector.py` | Bug修复 | 重构数据采集逻辑 |

---

## 🔧 技术细节

### S2: 重构 `get_pid_username_map()` → `get_process_info()`

**修改前**：
```python
def get_pid_username_map(self) -> Dict[int, str]:
    """获取 PID → 用户名 的映射"""
    pid_to_user = {}
    # ... 只提取 USER, PID
```

**修改后**：
```python
def get_process_info(self) -> Tuple[Dict[int, str], Dict[int, Dict]]:
    """获取进程详细信息
    
    Returns:
        - pid_to_user: Dict[pid, username]
        - pid_info: Dict[pid, {"cpu_percent": float, "mem_percent": float}]
    """
    pid_to_user = {}
    pid_info = {}
    
    # ps aux 格式: USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND
    for line in output.strip().split("\n"):
        if line.startswith("USER") or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 11:
            username = parts[0]
            pid = int(parts[1])
            cpu_percent = float(parts[2])
            mem_percent = float(parts[3])
            
            pid_to_user[pid] = username
            pid_info[pid] = {"cpu_percent": cpu_percent, "mem_percent": mem_percent}
```

### S3: 按用户聚合 CPU/内存

**修改 `collect()` 方法**：
```python
# 获取进程信息（包含CPU/内存）
pid_to_user, pid_info = self.get_process_info()

# 按用户聚合
user_resources = defaultdict(lambda: {"cpu_percent": 0.0, "memory_percent": 0.0})

for pid, username in pid_to_user.items():
    if username in users:
        info = pid_info.get(pid, {})
        user_resources[username]["cpu_percent"] += info.get("cpu_percent", 0)
        user_resources[username]["memory_percent"] += info.get("mem_percent", 0)
```

### S4: 按显存比例分配 GPU 使用率

**修改 `collect()` 方法**：
```python
# 获取全局GPU使用率和显存使用
global_gpu = self.collect_gpu()
global_gpu_usage = global_gpu.get("utilization", 0)
global_mem_used = global_gpu.get("memory_used_mb", 0)

# 按显存比例计算用户GPU使用率
for user in users:
    user_mem = result[user]["gpu_memory_mb"]
    if global_mem_used > 0:
        result[user]["gpu_percent"] = int(
            global_gpu_usage * user_mem / global_mem_used
        )
    else:
        result[user]["gpu_percent"] = 0
```

---

## ⚠️ 风险与约束

| 风险项 | 影响 | 缓解措施 |
|--------|------|---------|
| GPU使用率为估算值 | 非精确进程级数据 | 文档说明 |
| 多进程CPU累加可能超过100% | 显示异常 | 可设上限或显示原始值 |
| ps aux %MEM 是进程占比 | 用户内存总和可能超过100% | 这是预期行为 |

---

## ✅ 验收标准

1. 每个在线用户的 GPU 使用率显示不同值（按显存比例分配）
2. 每个在线用户的 CPU/内存显示不同值（按进程聚合）
3. 总显存 = 各用户显存之和
4. 修复不影响原有功能

---

## 📅 预计工作量

- 代码修改：约 50 行
- 测试验证：约 10 分钟

---

**关联文档**: [PLAN-006 GPU显存字段解析修复](./06-who-missing-process-user-fix.md) | [核心需求摘要](../abstract/requirement/core.md)
