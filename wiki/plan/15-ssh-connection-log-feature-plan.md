---
plan_id: plan_015
related_request: "wiki/request/req-ssh-connection-log-feature.md"
status: completed
estimated_context_tokens: ~8000
context_budget_limit: ~20000
created_at: 2026-04-08 20:45:00
completed_at: 2026-04-09 10:50:00
---
# 📋 执行计划：SSH连接记录功能

## 🎯 目标与交付物
- **最终交付路径**：`server-overwatch::/monitor/ssh_recorder.py`
- **验收标准**：
  1. `/ssh <时间>` 命令可正常返回SSH连接统计
  2. 支持按用户、IP过滤
  3. 分页功能正常
  4. 90天数据自动清理
  5. 单元测试通过 ✅

## 🛠️ 任务分解与执行流

| 步骤ID | 任务描述 | 前置依赖 | 交付物/修改路径 | 需用户确认? | 状态 |
|--------|---------|---------|----------------|------------|------|
| `S1` | 创建需求文档 | 无 | `wiki/request/req-ssh-connection-log-feature.md` | ✅ 是 | ✅ 完成 |
| `S2` | 创建SSH记录器模块 `ssh_recorder.py` | S1 | `monitor/ssh_recorder.py` | ❌ 否 | ✅ 完成 |
| `S3` | 添加配置项 `ssh_monitor` | S1 | `config.yaml` | ❌ 否 | ✅ 完成 |
| `S4` | 扩展命令解析器支持 `/ssh` | S2, S3 | `bot/handler.py` | ❌ 否 | ✅ 完成 |
| `S5` | 添加格式化输出方法 | S4 | `monitor/formatter.py` | ❌ 否 | ✅ 完成 |
| `S6` | 集成到主程序定时采集 | S5 | `main.py` | ❌ 否 | ✅ 完成 |
| `S7` | 编写测试脚本并验证 | S6 | `test_ssh_recorder.py` | ✅ 是 | ✅ 完成 |

## ⚠️ 风险与约束声明
- **日志格式兼容**：✅ 已解决 - 支持传统syslog和ISO 8601两种格式
- **时区格式兼容**：✅ 已解决 - 支持 `+0800` 和 `+08:00` 两种格式
- **权限要求**：✅ 已解决 - `gpu-monitor` 已加入 `adm` 组
- **数据去重**：防止重复采集同一日志行

## 📝 执行记录（Agent Auto-Update）
- `2026-04-08 20:45`: 计划已生成，提交用户确认。
- `2026-04-08 20:45`: 用户确认规范，计划定型。
- `2026-04-08 21:00`: 权限问题讨论完成，确认使用 adm 组方案。
- `2026-04-08 21:05`: 用户确认 `gpu-monitor` 已加入 adm 组。
- `2026-04-08 21:10`: 代码实现完成（S2-S6），等待用户执行测试脚本。
- `2026-04-09 10:50`: ✅ 测试完成，计划验收通过！
  - 问题1：正则表达式无法匹配ISO 8601格式日志
  - 问题2：时区格式 `+08:00` 带冒号，原正则 `[+-]\d{4}` 不支持
  - 修复：正则改为 `[+-]\d{2}:?\d{2}` 支持两种时区格式
