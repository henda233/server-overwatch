---
abstract_id: abs_plan10
source_contents:
  - "server-overwatch::/wiki/plan/10-command-extension.md"
  - "server-overwatch::/bot/handler.py"
  - "server-overwatch::/monitor/recorder.py"
  - "server-overwatch::/monitor/formatter.py"
dependencies:
  - "abs_plan09"
created_at: 2026-04-08 11:50:00
updated_at: 2026-04-08 11:55:00
audit_status: approved
---
# 📖 摘要：PLAN-010 命令扩展

## 🎯 核心结论与关键信息
- **新增3个命令**：`/stats`, `/top`, `/users`
- **命令解析**：扩展 `Command` 数据类，新增 `sort_by` 字段
- **数据层**：新增 `get_all_users_stats()`, `get_all_users()` 方法
- **格式化层**：新增 `format_stats()`, `format_top()`, `format_users()` 方法

## 📋 内容概述
实现了3个新的查询命令，丰富了机器人的统计和排行功能：

### 新增命令
| 命令 | 功能 | 示例 |
|------|------|------|
| `/stats <时间>` | 显示统计摘要（峰值/平均/活跃时长） | `/stats 3d` |
| `/top [gpu/mem/cpu]` | 按资源排序的用户排行榜 | `/top`, `/top mem` |
| `/users [天数]` | 历史用户列表及简要统计 | `/users`, `/users 30d` |

### 新增/修改的代码
| 文件 | 修改内容 |
|------|----------|
| `bot/handler.py` | 扩展 `Command` 数据类 + `parse()` + `handle()` |
| `monitor/recorder.py` | 新增 `get_all_users_stats()`, `get_all_users()` |
| `monitor/formatter.py` | 新增 `format_stats()`, `format_top()`, `format_users()` + 更新帮助信息 |

## 🔗 依赖与影响链
- **上游依赖**：`abs_plan09`（命令解析基础）
- **下游被依赖**：无
- **变更扩散评估**：低（仅新增命令，不影响现有功能）

## 📝 验证结果
- ✅ 命令解析测试通过（10个测试用例）
- ✅ `get_all_users_stats()` 测试通过
- ✅ `get_all_users()` 测试通过
- ✅ `format_stats()` 输出正确
- ✅ Handler 集成测试通过（7个命令）
- ✅ GPU服务器测试通过
