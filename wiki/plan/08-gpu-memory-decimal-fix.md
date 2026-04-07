# 📋 修复计划：GPU使用率和显存显示小数

> PLAN-008 | v1.0 | 2026-04-07 | status: pending

## 🎯 问题描述

### 现象

- GPU使用率显示为整数（如 `0%`），用户无法看到精确值
- 显存显示为整数（如 `8GB`），不够精确

### 根本原因

1. `collector.py` 第79行使用 `int()` 截断小数
2. `formatter.py` 使用 `:.0f` 格式，不保留小数

---

## 📌 修改方案

### 涉及文件

| 文件路径 | 修改类型 | 修改说明 |
|---------|---------|---------|
| `monitor/collector.py` | 功能修改 | GPU使用率保留2位小数 |
| `monitor/formatter.py` | 功能修改 | GPU、显存、CPU、内存显示小数 |

---

### 详细修改

#### 1. `monitor/collector.py` 第79行

**修改前**：
```python
gpu_percent = int(global_gpu_usage * user_mem / global_mem_used)
```

**修改后**：
```python
gpu_percent = round(global_gpu_usage * user_mem / global_mem_used, 2)
```

---

#### 2. `monitor/formatter.py` 第33行（表头）

**修改前**：
```python
header = "用户名   | GPU   | 显存       | CPU   | 内存"
```

**修改后**：
```python
header = "用户名   | GPU      | 显存           | CPU    | 内存"
```

---

#### 3. `monitor/formatter.py` 第51行（实时数据行）

**修改前**：
```python
line = f"{username[:7]:<7} | {gpu:>3}%  | {mem_str:<10} | {cpu:>3}%  | {mem}%"
```

**修改后**：
```python
line = f"{username[:7]:<7} | {gpu:>6.2f}% | {mem_str:<13} | {cpu:>6.1f}%  | {mem:>5.1f}%"
```

---

#### 4. `monitor/formatter.py` 第179行（_format_memory方法）

**修改前**：
```python
return f"{used_gb:.0f}GB/{total_gb:.0f}GB"
```

**修改后**：
```python
return f"{used_gb:.2f}GB/{total_gb:.2f}GB"
```

---

#### 5. `monitor/formatter.py` 第89行（历史记录）

**修改前**：
```python
line = f"{username:<7} | {timestamp:<18} | {gpu:>3}%  | {gpu_mem_gb:.1f}GB"
```

**修改后**：
```python
line = f"{username:<7} | {timestamp:<18} | {gpu:>6.2f}% | {gpu_mem_gb:.2f}GB"
```

---

#### 6. `monitor/formatter.py` 第116行、121行、125-126行（用户详情）

**修改前**：
```python
lines.append(f"GPU使用率: {gpu}%")
lines.append(f"显存使用: {gpu_mem_gb:.1f}GB / {total_gb:.1f}GB")
lines.append(f"CPU使用率: {cpu}%")
lines.append(f"内存使用: {mem}%")
```

**修改后**：
```python
lines.append(f"GPU使用率: {gpu:.2f}%")
lines.append(f"显存使用: {gpu_mem_gb:.2f}GB / {total_gb:.2f}GB")
lines.append(f"CPU使用率: {cpu:.1f}%")
lines.append(f"内存使用: {mem:.1f}%")
```

---

## 📝 预期效果

### 修改前
```
用户名   | GPU   | 显存       | CPU   | 内存
-------------------------------------
cxy     |   0%  | 0GB/96GB   | 11.3%  | 4.5%
lgl     |   0%  | 8GB/96GB   | 926.0%  | 1.5%
```

### 修改后
```
用户名   | GPU      | 显存              | CPU    | 内存
--------------------------------------------------------------
cxy     |   0.00% |  0.00GB/96.00GB   |  11.3%  |  4.5%
lgl     |   0.00% |  8.00GB/96.00GB   | 926.0%  |  1.5%
```

---

## 🛠️ 任务分解

| 步骤ID | 任务描述 | 前置依赖 | 交付物/修改路径 | 状态 |
|--------|---------|---------|----------------|------|
| `S1` | 修改 `collector.py` GPU使用率计算 | 无 | `monitor/collector.py` | pending |
| `S2` | 修改 `formatter.py` 表头宽度 | S1 | `monitor/formatter.py` | pending |
| `S3` | 修改 `formatter.py` 实时数据行格式 | S2 | `monitor/formatter.py` | pending |
| `S4` | 修改 `formatter.py` _format_memory方法 | S3 | `monitor/formatter.py` | pending |
| `S5` | 修改 `formatter.py` 历史记录格式 | S4 | `monitor/formatter.py` | pending |
| `S6` | 修改 `formatter.py` 用户详情格式 | S5 | `monitor/formatter.py` | pending |
| `S7` | GPU服务器测试验证 | S6 | 测试输出 | pending |

---

## ⚠️ 风险与约束

| 风险项 | 影响 | 缓解措施 |
|--------|------|---------|
| 表格宽度增加 | 显示可能换行 | 调整列宽适配 |
| 兼容性测试 | `sum()` 对浮点数求和 | Python原生支持，无问题 |

---

## ✅ 验收标准

1. GPU使用率显示2位小数（如 `37.50%`）
2. 显存显示2位小数（如 `8.00GB/96.00GB`）
3. CPU/内存显示1位小数（如 `926.0%`）
4. 表格对齐正常，不换行
5. 测试代码 `test_collector.py` 运行正常

---

**关联文档**: [PLAN-007 按用户区分CPU/内存/GPU使用率](./07-user-cpu-memory-gpu-percent-fix.md)
