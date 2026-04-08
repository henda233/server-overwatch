# 📋 PLAN-012：历史查询过滤条件修复

> v1.0 | 2026-04-08 | status: completed

## 1. 背景问题

**问题描述**：`/info 1d` 查询返回"暂无历史记录"，但数据库中确实有11条记录。

**根因分析**：
- 数据库中 `gpu_memory_mb` 字段值全为0（用户当时未使用GPU训练）
- 当前过滤条件 `gpu_memory_mb > 0` 过于严格，将所有记录过滤掉
- 实际上用户有CPU和内存使用（cpu_percent=8.7%, memory_percent=1.7%），这些记录是有价值的

## 2. 解决方案

**过滤原则**：只过滤所有资源列都为0的记录，保留有任何资源使用的记录。

**修改前**：
```sql
WHERE timestamp >= ? AND gpu_memory_mb > 0
```

**修改后**：
```sql
WHERE timestamp >= ? 
  AND NOT (gpu_memory_mb = 0 AND cpu_percent = 0 AND memory_percent = 0)
```

## 3. 修改范围

| 文件 | 修改内容 | 优先级 |
|------|---------|--------|
| `monitor/recorder.py` | `query_filtered()` 方法过滤条件修改（2处） | P0 |

**不受影响**：
- 峰值统计查询保持不变（从全量数据计算）
- `formatter.py` 无需修改
- `handler.py` 无需修改

## 4. 任务清单

| 序号 | 任务 | 状态 | 备注 |
|------|------|------|------|
| 1 | 修改 `query_filtered()` 用户名过滤条件 | ✅ 已完成 | 4处SQL |
| 2 | 更新 WIKI 摘要 | ✅ 已完成 | abs_005 |
| 3 | 更新 WIKI index | ✅ 已完成 | index.md |

## 5. 验收标准

- [ ] `/info 1d` 能返回有效记录（不再显示"暂无历史记录"）
- [ ] 统计信息（峰值）保持正确
- [ ] 历史悠久的全零记录仍被正确过滤

---

**依赖**: PLAN-009（历史记录精简模式）
**阻塞**: 无
