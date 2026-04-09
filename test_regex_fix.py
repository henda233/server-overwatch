#!/usr/bin/env python3
"""
正则表达式修复验证脚本
用于测试ISO 8601格式auth.log的解析是否正常
"""

import re
import sys

# 你的auth.log实际格式
line = '2026-04-09T10:59:28.898309+08:00 hi sshd[5867]: Accepted password for lgl from 172.19.106.183 port 53056 ssh2'

# 修复后的正则表达式
PATTERN_ACCEPTED = re.compile(
    r'(?:'
    r'(?P<month1>\w+)\s+(?P<day1>\d+)\s+(?P<time1>\d+:\d+:\d+)\s+\S+\s+sshd\[\d+\]:\s+'
    r'|'
    r'\d{4}-\d{2}-\d{2}T(?P<time2>\d+:\d+:\d+)[.\d]*[+-]\d{2}:?\d{2}\s+\S+\s+sshd\[\d+\]:\s+'
    r')'
    r'Accepted password for (?P<user>\S+) from (?P<ip>\S+)'
)

print("=" * 60)
print("正则表达式修复验证")
print("=" * 60)
print()
print(f"测试日志行:")
print(f"  {line}")
print()

match = PATTERN_ACCEPTED.search(line)
if match:
    print("✅ 正则表达式匹配成功!")
    print(f"  用户(user): {match.group('user')}")
    print(f"  IP(ip):     {match.group('ip')}")
    print(f"  时间(time2): {match.group('time2')}")
else:
    print("❌ 正则表达式匹配失败!")
    print()
    print("正在尝试诊断问题...")
    print()

    # 诊断：检查各部分是否能匹配
    iso_prefix = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*[+-]\d{2}:?\d{2}'
    sshd_part = r'\s+\S+\s+sshd\[\d+\]:\s+'
    user_ip_part = r'Accepted password for \S+ from \S+'

    print(f"检查ISO时间前缀: {'✅ 匹配' if re.search(iso_prefix, line) else '❌ 不匹配'}")
    print(f"检查sshd部分: {'✅ 匹配' if re.search(sshd_part, line) else '❌ 不匹配'}")
    print(f"检查用户IP部分: {'✅ 匹配' if re.search(user_ip_part, line) else '❌ 不匹配'}")

    sys.exit(1)

print()
print("=" * 60)
print("现在测试采集功能...")
print("=" * 60)
print()

# 测试完整采集流程
sys.path.insert(0, '/opt/server-overwatch')  # 项目路径
from monitor.ssh_recorder import SSHRecorder
import tempfile
import os

temp_dir = tempfile.mkdtemp()
db_path = os.path.join(temp_dir, "test_regex.db")
log_path = "/var/log/auth.log"

try:
    recorder = SSHRecorder(db_path=db_path, log_path=log_path)

    print(f"日志文件: {log_path}")
    print(f"文件大小: {os.path.getsize(log_path)} bytes")
    print()

    count = recorder.collect()
    print(f"采集结果: {count} 条记录")

    if count > 0:
        print()
        records, stats = recorder.query("7d")
        print(f"过去7天统计:")
        print(f"  原始记录: {stats['total_raw']} 条")
        print(f"  聚合记录: {stats['total_agg']} 条")
        print(f"  成功登录: {stats['success_total']} 次")
        print(f"  失败登录: {stats['fail_total']} 次")

        if records:
            print()
            print("前5条聚合记录:")
            for i, r in enumerate(records[:5], 1):
                print(f"  {i}. {r['username']}@{r['ip']} - 成功:{r['success_count']} 失败:{r['fail_count']}")
    else:
        print()
        print("⚠️  没有采集到记录，可能是:")
        print("  1. auth.log已被完全读取过（增量采集跳过）")
        print("  2. 日志中没有新的SSH登录记录")
        print("  3. 试试删除位置文件后重新测试:")
        print(f"     rm -f {db_path}.pos")

        # 诊断：读取文件前10行尝试解析
        print()
        print("诊断: 尝试解析auth.log前10行...")
        with open(log_path, 'r', errors='ignore') as f:
            for i, line in enumerate(f.readlines()[:10], 1):
                match = PATTERN_ACCEPTED.search(line)
                status = "✅" if match else "  "
                print(f"  {status} 行{i}: {line[:80].strip()}...")

finally:
    import shutil
    shutil.rmtree(temp_dir)

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
