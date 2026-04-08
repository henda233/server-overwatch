---
abstract_id: abs_014
source_contents:
  - "server-overwatch::/wiki/request/req-pagination-feature.md"
  - "server-overwatch::/wiki/plan/14-pagination-feature-plan.md"
dependencies:
  - "abs_005"
created_at: 2026-04-08 20:40:00
updated_at: 2026-04-08 20:40:05
audit_status: approved
---

# 📖 摘要：历史查询翻页功能

## 🎯 核心结论与关键信息

### 功能需求（R14）

| 需求ID | 功能描述 | 状态 |
|--------|---------|------|
| R14 | 历史查询命令翻页功能 | ✅ 已完成 |

### 翻页语法

| 命令 | 翻页后格式 |
|------|-----------|
| `/info <时间>` | `/info 5d [页码]` |
| `/info <用户> <时间>` | `/info 张三 5d [页码]` |
| `/stats <时间>` | `/stats 1w [页码]` |
| `/top [类型]` | `/top gpu [页码]` |
| `/users [天数]` | `/users 7d [页码]` |

### 配置项

```yaml
pagination:
  page_size: 10  # 每页默认条数，config.yaml可调整
```

### 边界处理规则

- 页码超出范围 → 静默返回最后一页
- 非数字页码 → 静默忽略，返回第1页

## 📋 内容概述

为历史查询命令增加翻页功能，解决数据过多被截断的问题。用户可通过 `/命令 参数 页码` 查看指定页内容。

## 🔗 依赖与影响链

- **上游依赖**: `abs_005`（核心需求摘要）
- **下游被依赖**: 无
- **变更扩散评估**: 中（涉及所有历史查询命令的解析和格式化逻辑）
