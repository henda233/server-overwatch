---
abstract_id: abs_plan12
source_contents:
  - "server-overwatch::/wiki/plan/12-history-filter-fix.md"
dependencies:
  - "abs_005"
  - "abs_plan09"
created_at: 2026-04-08 11:32:00
updated_at: 2026-04-08 11:32:00
audit_status: pending
---

# 📖 摘要：PLAN-012 历史查询过滤条件修复

## 🎯 核心结论与关键信息

- **问题**：`/info 1d` 查询返回"暂无历史记录"，但数据库有11条记录
- **根因**：过滤条件 `gpu_memory_mb > 0` 过于严格，用户无GPU训练时记录被全部过滤
- **修复**：改为 `NOT (gpu_memory_mb = 0 AND cpu_percent = 0 AND memory_percent = 0)`
- **影响范围**：仅 `recorder.py` 的 `query_filtered()` 方法（2处SQL）

## 📋 内容概述

PLAN-012 修复历史查询过滤条件过严的问题，将"只保留显存>0"改为"保留任何资源>0的记录"，确保有CPU/内存使用但无GPU训练的记录不被误过滤。

## 🔗 依赖与影响链

- **上游依赖**：
  - `abs_005`（核心需求）
  - `abs_plan09`（历史记录精简模式）
- **下游被依赖**：无
- **变更扩散评估**：低（仅修改数据过滤逻辑，不影响业务层）

## 🛡️ 审计记录

- [ ] 2026-04-08：计划已创建，待执行
