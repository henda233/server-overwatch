---
abstract_id: abs_plan09
source_contents:
  - "server-overwatch::/wiki/plan/09-history-compact-mode.md"
  - "server-overwatch::/monitor/recorder.py"
  - "server-overwatch::/monitor/formatter.py"
  - "server-overwatch::/bot/handler.py"
dependencies:
  - "abs_005"
  - "server-overwatch::/wiki/plan/10-command-extension.md"
created_at: 2026-04-08 11:55:00
updated_at: 2026-04-08 12:00:00
audit_status: approved
---
# 📖 摘要：PLAN-009 历史记录精简模式

## 🎯 核心结论与关键信息
- **命令扩展**：新增 `/info <用户> <时间>` 组合命令支持
- **数据过滤**：历史查询自动过滤0值记录（显存=0），只显示有GPU任务的用户
- **统一UI**：实时与历史查询使用相同的单行文字格式，不依赖等宽字体
- **统计摘要**：显示有效记录数/总记录数、已过滤数、GPU/CPU/内存峰值

## 📋 内容概述
实现了历史记录的精简模式，解决了两个核心问题：
1. 历史查询返回大量0值空闲数据淹没有效信息
2. ASCII表格在手机QQ非等宽字体下对齐错位

### 新增/修改的代码
| 文件 | 修改内容 |
|------|----------|
| `bot/handler.py` | 支持 `/info <user> <time>` 组合命令解析 |
| `monitor/recorder.py` | 新增 `query_filtered()` 方法（过滤0值+统计） |
| `monitor/formatter.py` | `format_realtime()` 改为单行格式 |
| `monitor/formatter.py` | 新增 `format_history_compact()` 精简模式 |
| `monitor/formatter.py` | `format_user_detail()` 风格统一 |

### 过滤规则
```
记录有效条件：gpu_memory_mb > 0（有显存占用）
原因：CPU/内存可能因系统后台进程非0，仅用显存作为主要判断依据
```

### Bug修复
- 修正 `query_filtered()` SQL查询：`GROUP BY` 与 `MAX()` 不能在同一查询中使用峰值计算，需分两步查询

## 🔗 依赖与影响链
- **上游依赖**：`abs_005`（命令设计基础）
- **下游被依赖**：`PLAN-010`（命令扩展依赖本计划）
- **变更扩散评估**：中（涉及命令解析、数据查询、格式化多个模块）

## 📝 验证结果
- ✅ 命令解析测试通过
- ✅ 实时数据格式化测试通过
- ✅ 精简历史格式化测试通过
- ✅ `query_filtered()` 方法测试通过
- ✅ Handler 集成测试通过
