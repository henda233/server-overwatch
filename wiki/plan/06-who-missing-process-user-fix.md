# 📋 修复计划：nvidia-smi查询字段数与代码期望不匹配

> PLAN-006 | v3.0 | 2026-04-07 | status: done ✅

## 🎯 问题描述

### 现象

当用户通过SSH启动GPU计算任务后：

- `who` 命令**正确检测到用户**
- 机器人 `/info` 显示该用户显存为 **0GB**
- 但 `nvidia-smi` 显示该用户进程实际占用了GPU显存

### 实际案例（2026-04-07 20:59）

**nvidia-smi 输出：**
```
|    0   N/A  N/A         2884752      C   python                                 7838MiB |
```

**nvidia-smi --query-compute-apps 输出：**
```
2884752, 7838
```

**机器人输出：**
```
用户名   | GPU   | 显存       | CPU   | 内存
-------------------------------------
cxy     |   0%  | 0GB/96GB   |  16%  | 0%
lgl     |   0%  | 0GB/96GB   |  16%  | 0%
```

lgl 显示显存为 **0GB**，与实际占用 **7838MiB** 不符。

### 根本原因

**代码Bug**：`collector.py` 第102-117行

`nvidia-smi --query-compute-apps` 命令只返回 **2个字段**：
```
pid, used_memory
```

但代码期望 **3个字段**：
```python
if len(parts) >= 3:  # ← 条件失败，实际只有2个字段
    result.append({
        "pid": int(parts[0]),
        "memory_mb": int(parts[1]),
        "gpu_percent": int(parts[2])  # 永远不执行
    })
```

**结果**：GPU进程数据被静默丢弃，`user_gpu` 保持为空。

### 数据流分析

| 步骤 | 代码执行 | 结果 |
|------|---------|------|
| 1 | `nvidia-smi --query-compute-apps=pid,used_memory,utilization.gpu` | ❌ 字段无效 |
| 2 | 改为 `nvidia-smi --query-compute-apps=pid,used_memory` | ✅ 成功，返回 `2884752, 7838` |
| 3 | `len(parts) >= 3` | ❌ False (只有2个元素) |
| 4 | `result.append(...)` | ❌ 跳过 |
| 5 | `processes` 列表 | ❌ 空列表 |
| 6 | `user_gpu["lgl"]` | ❌ 保持 0 |

### 验证数据链路

| 检查项 | 结果 | 说明 |
|--------|------|------|
| `who` 命令 | ✅ 正常 | lgl 在 pts/0, pts/1, pts/2 |
| `ps aux` | ✅ 正常 | PID 2884752 归属 lgl |
| `nvidia-smi --query-compute-apps` | ✅ 正常 | 返回 2个字段 |

---

## 📌 修复方案

### 核心思路

修正 `collect_process_gpu()` 方法的字段解析逻辑。

### 数据流（修复后）

```
┌─────────────────────────────────────────────┐
│  nvidia-smi --query-compute-apps=...        │
│  输出: pid, used_memory                     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  解析字段                                    │
│  if len(parts) >= 2:  ✅ 修复后             │
│      pid, memory_mb = parts                │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  GPU使用率单独获取                            │
│  nvidia-smi --query-gpu=utilization.gpu    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  正确聚合到 user_gpu["lgl"]                 │
└─────────────────────────────────────────────┘
```

---

## 🛠️ 任务分解

| 步骤ID | 任务描述 | 前置依赖 | 交付物/修改路径 | 状态 |
|--------|---------|---------|----------------|------|
| `S1` | 分析 `collect_process_gpu()` 字段解析逻辑 | 无 | 问题定位 | ✅ 已完成 |
| `S2` | 修正字段数量检查 `len >= 2` | S1 | `monitor/collector.py` | ✅ 已完成 |
| `S3` | 处理GPU使用率获取（单独查询或设为0） | S2 | `monitor/collector.py` | ✅ 已完成 |
| `S4` | 本地测试验证修复效果 | S3 | 测试输出截图 | ✅ 已完成 |
| `S5` | 部署到GPU服务器并验证 | S4 | 机器人 `/info` 实际输出 | ✅ 已完成 |

---

## 📂 修改文件清单

| 文件路径 | 修改类型 | 修改说明 |
|---------|---------|---------|
| `monitor/collector.py` | Bug修复 | 修改 `collect_process_gpu()` 字段解析逻辑 |

---

## 🔧 技术细节

### S2: 修正字段解析逻辑

**修改点**：第112行

**原代码**：
```python
if len(parts) >= 3:  # ← 问题：实际只有2个字段
    result.append({
        "pid": int(parts[0]),
        "memory_mb": int(parts[1]),
        "gpu_percent": int(parts[2])  # 永远不执行
    })
```

**新代码**：
```python
if len(parts) >= 2:  # ✅ 修复：调整为2个字段
    result.append({
        "pid": int(parts[0]),
        "memory_mb": int(parts[1]),
        "gpu_percent": 0  # 或从全局GPU使用率获取
    })
```

### S3: GPU使用率处理

`nvidia-smi --query-compute-apps` 不支持 `utilization.gpu` 字段。

**方案选择**（待定）：

| 方案 | 描述 | 优缺点 |
|------|------|--------|
| A | GPU使用率设为0 | 简单，但不准确 |
| B | 单独调用 `nvidia-smi --query-gpu=utilization.gpu` | 全局值，非进程级 |
| C | 进程级GPU使用率通过其他方式获取 | 复杂度高 |

**推荐**：方案A（设为0），待后续优化。

---

## ⚠️ 风险与约束

| 风险项 | 影响 | 缓解措施 |
|--------|------|---------|
| GPU使用率显示为0 | 影响用户体验 | 可后续优化 |
| 字段解析仍有问题 | 其他异常情况 | 添加日志记录 |
| 进程消失 | 进程结束但仍有残留 | 下次采集会自动更新 |

---

## ✅ 验收标准

1. 当用户启动GPU任务后，`/info` 显示该用户的显存占用正确
2. 机器人的 `/info` 输出与 `nvidia-smi` 显示的显存总量一致
3. 修复不影响原有功能

### 验收测试

```bash
# 场景1：验证数据一致性
nvidia-smi 显示的进程显存总和 ≈ 所有用户显存（可能有误差）

# 场景2：验证解析正确
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits
# 应在 /info 中正确显示
```

---

## 📅 预计工作量

- 代码修改：约 5 行
- 测试验证：约 10 分钟
- 部署上线：约 5 分钟

---

## 📝 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-04-07 | v2.0 | 修正根因：代码期望3字段，实际nvidia-smi返回2字段 |
| 2026-04-07 | v1.0 | 创建文档，初步分析问题根因 |

---

**关联文档**: [PLAN-005 按用户区分GPU/显存资源](./05-user-resource-fix.md) | [核心需求摘要](../abstract/requirement/core.md)
