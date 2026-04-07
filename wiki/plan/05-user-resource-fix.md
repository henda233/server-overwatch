# 📋 修复计划：按用户区分GPU/显存资源

> PLAN-005 | v1.0 | 2026-04-07 | status: draft

## 🎯 问题描述

当前 `/info` 命令输出的所有在线用户的 GPU、显存、CPU、内存数据完全相同，这是因为：

1. `collect_gpu()` 只获取整个GPU的总使用率和总显存
2. `collect_cpu()` / `collect_memory()` 只获取整个系统的CPU/内存使用率
3. 所有用户被分配了完全相同的系统级数据

### 当前输出（问题）
```
用户名   | GPU   | 显存       | CPU   | 内存
-----------------------------------------------
cxy     |  20%  | 8GB/96GB   |  17%  | 0%
zsc     |  20%  | 8GB/96GB   |  17%  | 0%
lgl     |  20%  | 8GB/96GB   |  17%  | 0%
```

### 期望输出（修复后）
```
用户名   | GPU   | 显存       | CPU   | 内存
-----------------------------------------------
cxy     |  30%  | 12GB/96GB  |  25%  | 15%
zsc     |  10%  | 4GB/96GB   |   8%  |  5%
lgl     |  20%  | 8GB/96GB   |  10%  |  8%
```

---

## 📌 修复方案

### 技术方案：进程级GPU采集 + PID用户名映射

通过 `nvidia-smi` 查询每个计算进程的GPU使用情况，再将进程映射到用户。

### 数据流

```
nvidia-smi --query-compute-apps=pid,used_memory,utilization.gpu
        │
        ▼
┌───────────────────────┐
│  获取进程列表          │
│  PID | Memory | GPU%  │
└───────────────────────┘
        │
        ▼
ps aux --获取 PID → Username 映射
        │
        ▼
┌───────────────────────┐
│  按用户聚合            │
│  User1: GPU%求和      │
│  User1: Memory求和    │
└───────────────────────┘
```

---

## 🛠️ 任务分解

| 步骤ID | 任务描述 | 前置依赖 | 交付物/修改路径 | 状态 |
|--------|---------|---------|----------------|------|
| `S1` | 添加 `collect_process_gpu()` 方法，获取每个进程的GPU使用情况 | 无 | `monitor/collector.py` | ⏳ 待执行 |
| `S2` | 添加 `get_pid_username_map()` 方法，通过 `ps aux` 获取 PID→用户名映射 | S1 | `monitor/collector.py` | ⏳ 待执行 |
| `S3` | 重构 `collect()` 方法，按用户聚合GPU数据 | S2 | `monitor/collector.py` | ⏳ 待执行 |
| `S4` | 保留 `collect_cpu()` / `collect_memory()` 作为系统级数据（可选：也按用户区分） | S3 | `monitor/collector.py` | ⏳ 待执行 |
| `S5` | 本地测试验证修复效果 | S4 | 测试输出截图 | ⏳ 待执行 |
| `S6` | 部署到GPU服务器并验证 | S5 | 机器人 `/info` 实际输出 | ⏳ 待执行 |

---

## 📂 修改文件清单

| 文件路径 | 修改类型 | 修改说明 |
|---------|---------|---------|
| `monitor/collector.py` | 重构 | 新增方法、重写 `collect()` 逻辑 |

---

## 🔧 技术细节

### S1: 新增 `collect_process_gpu()` 方法

```python
def collect_process_gpu(self) -> List[Dict]:
    """采集每个计算进程的GPU使用情况
    
    Returns:
        List[Dict], 每个进程包含:
            - pid: int
            - memory_mb: int
            - gpu_percent: int
    """
    result = []
    
    try:
        # 方法A: 使用 --query-compute-apps
        cmd = [
            "nvidia-smi",
            "--query-compute-apps=pid,used_memory,utilization.gpu",
            "--format=csv,noheader,nounits"
        ]
        output = subprocess.check_output(cmd, text=True, timeout=5)
        
        for line in output.strip().split("\n"):
            if line:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    result.append({
                        "pid": int(parts[0]),
                        "memory_mb": int(parts[1]),
                        "gpu_percent": int(parts[2])
                    })
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
        pass
    
    return result
```

### S2: 新增 `get_pid_username_map()` 方法

```python
def get_pid_username_map(self) -> Dict[int, str]:
    """获取 PID → 用户名 的映射
    
    Returns:
        Dict[pid, username]
    """
    pid_to_user = {}
    
    try:
        # ps aux 获取所有进程，第三个字段是用户名，第二个是PID
        output = subprocess.check_output(
            ["ps", "aux"],
            text=True,
            timeout=5
        )
        
        for line in output.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 11:  # ps aux 格式: USER PID %CPU %MEM ...
                username = parts[0]
                pid = int(parts[1])
                pid_to_user[pid] = username
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    
    return pid_to_user
```

### S3: 重构 `collect()` 方法

```python
def collect(self) -> Dict[str, Dict]:
    """采集所有在线用户的资源使用情况（按用户区分）"""
    
    users = self.collect_users()
    pid_to_user = self.get_pid_username_map()
    processes = self.collect_process_gpu()
    
    # 按用户聚合GPU数据
    user_gpu = defaultdict(lambda: {"gpu_percent": 0, "gpu_memory_mb": 0})
    
    for proc in processes:
        username = pid_to_user.get(proc["pid"])
        if username and username in users:
            user_gpu[username]["gpu_percent"] += proc["gpu_percent"]
            user_gpu[username]["gpu_memory_mb"] += proc["memory_mb"]
    
    # 构建结果（未使用GPU的用户也需要显示）
    result = {}
    for user in users:
        gpu_data = user_gpu.get(user, {"gpu_percent": 0, "gpu_memory_mb": 0})
        
        # CPU/内存暂时仍为系统级（可选优化）
        result[user] = {
            "gpu_percent": min(gpu_data["gpu_percent"], 100),  # 防止超过100%
            "gpu_memory_mb": gpu_data["gpu_memory_mb"],
            "gpu_memory_total_mb": self._get_gpu_total_memory(),  # 需要新增方法
            "cpu_percent": 0,  # TODO: 可按用户区分
            "memory_percent": 0  # TODO: 可按用户区分
        }
    
    return result
```

---

## ⚠️ 风险与约束

| 风险项 | 影响 | 缓解措施 |
|--------|------|---------|
| 用户进程未使用GPU | 显示0%但实际在线 | 正常情况，保持显示 |
| GPU使用率超过100% | 多进程同时使用同一GPU | 取 min(value, 100) |
| 多GPU服务器 | 需分别查询每块GPU | 当前方案只获取总GPU（按需求简化） |
| ps aux 执行慢 | 影响响应速度 | 设置5秒超时 |

---

## ✅ 验收标准

1. `/info` 输出中，每个在线用户的 GPU% 和 显存 使用量不同
2. 同一用户在多次查询间，数据可能变化（反映实时状态）
3. 未使用GPU的用户显示 0% GPU 和 0MB 显存
4. 系统整体GPU使用率 ≈ 各用户GPU%之和（允许误差<5%）

---

## 📅 预计工作量

- 代码修改：约 100 行
- 测试验证：约 30 分钟
- 部署上线：约 10 分钟

---

**关联文档**: [模块详细设计](./03-module-design.md) | [核心需求摘要](../abstract/requirement/core.md)
