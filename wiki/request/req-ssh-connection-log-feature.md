# 📝 需求文档：SSH连接记录功能

> 提交时间：2026-04-08 20:45:00
> 需求ID：req-ssh-connection-log-feature
> 状态：待开发

## 需求概述

增加新功能：记录SSH连接信息到SQLite数据库，并通过QQ机器人查询。

## 详细需求

### 1. 数据来源
- **日志文件**：`/var/log/auth.log`
- **日志格式**：
  - 成功登录：`Accepted password for <user> from <ip>`
  - 失败登录：`Failed password for <user> from <ip>`

### 2. 数据存储
- **数据库**：新建 `ssh_history.db`
- **表结构**：
  ```sql
  CREATE TABLE ssh_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    username TEXT NOT NULL,
    ip TEXT NOT NULL,
    success BOOLEAN NOT NULL
  );
  CREATE INDEX idx_timestamp ON ssh_history(timestamp);
  CREATE INDEX idx_username ON ssh_history(username);
  CREATE INDEX idx_ip ON ssh_history(ip);
  ```
- **数据保留**：90天自动清理

### 3. 命令设计
| 命令 | 说明 |
|------|------|
| `/ssh 1d` | 显示最近1天全部记录，按总次数降序 |
| `/ssh 1d lgl` | 按用户 "lgl" 过滤 |
| `/ssh 1d 172.19.106.183` | 按IP过滤（自动识别IP格式） |
| `/ssh 1d lgl@172.19.106.183` | 同时按用户+IP过滤（且关系） |
| `/ssh 1d 2` | 显示第2页（默认每页10条） |
| `/ssh 1d lgl 2` | 按用户过滤+第2页 |

### 4. 输出格式
```
📊 过去 1d 的SSH连接记录
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 第2页/共5页
还有3页数据，输入 /ssh 1d 3 查看下一页

统计: 20条 / 50条总
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

172.19.106.183  root   成功:  3次  失败: 12次
172.19.106.184  lgl    成功:  8次  失败:  2次
...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
提示: /ssh 1d root 查看指定用户的详细记录
```

### 5. 配置项（config.yaml）
```yaml
ssh_monitor:
  log_path: "/var/log/auth.log"
  retention_days: 90
  page_size: 10
```

### 6. 采集机制
- **定时采集**：复用现有定时任务（每分钟）
- **采集逻辑**：读取新增日志行，解析后写入数据库

## 验收标准
1. `/ssh <时间>` 命令可正常返回SSH连接统计
2. 支持按用户、IP过滤
3. 分页功能正常
4. 90天数据自动清理
5. 单元测试通过
