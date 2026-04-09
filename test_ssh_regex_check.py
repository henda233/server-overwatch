#!/usr/bin/env python3
"""
SSH日志正则表达式测试脚本
用于测试 ssh_recorder.py 中的正则表达式是否能正确匹配 auth.log 中的SSH记录
"""

import re

# 测试日志样本（来自服务器 auth.log）
TEST_LOGS = [
    # ISO 8601 格式（带毫秒）
    "2026-04-09T10:59:28.898309+08:00 hi sshd[5867]: Accepted password for lgl from 172.19.106.183 port 53056 ssh2",
    # ISO 8601 格式（不带毫秒）
    "2026-04-09T10:59:28+08:00 hi sshd[5867]: Accepted password for lgl from 172.19.106.183 port 53056 ssh2",
    # 传统 syslog 格式
    "Apr  9 10:30:00 hi sshd[12345]: Accepted password for user from 192.168.1.1",
    # 失败登录 ISO 格式
    "2026-04-09T10:59:28.898309+08:00 hi sshd[5867]: Failed password for root from 172.19.106.183 port 53056 ssh2",
    # 失败登录 传统格式
    "Apr  9 10:30:00 hi sshd[12345]: Failed password for root from 192.168.1.1",
]

# ssh_recorder.py 中的正则表达式
PATTERN_ACCEPTED = re.compile(
    r'(?:'
    # 格式1: 传统syslog
    r'(?P<month1>\w+)\s+(?P<day1>\d+)\s+(?P<time1>\d+:\d+:\d+)\s+\S+\s+sshd\[\d+\]:\s+'
    # 格式2: ISO 8601
    r'|'
    r'\d{4}-\d{2}-\d{2}T(?P<time2>\d+:\d+:\d+)[.\d]*[+-]\d{2}:?\d{2}\s+\S+\s+sshd\[\d+\]:\s+'
    r')'
    r'Accepted password for (?P<user>\S+) from (?P<ip>\S+)'
)

PATTERN_FAILED = re.compile(
    r'(?:'
    # 格式1: 传统syslog
    r'(?P<month1>\w+)\s+(?P<day1>\d+)\s+(?P<time1>\d+:\d+:\d+)\s+\S+\s+sshd\[\d+\]:\s+'
    # 格式2: ISO 8601
    r'|'
    r'\d{4}-\d{2}-\d{2}T(?P<time2>\d+:\d+:\d+)[.\d]*[+-]\d{2}:?\d{2}\s+\S+\s+sshd\[\d+\]:\s+'
    r')'
    r'Failed password for (?P<user>\S+) from (?P<ip>\S+)'
)


def test_regex():
    """测试正则表达式"""
    print("=" * 60)
    print("SSH日志正则表达式测试")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, log in enumerate(TEST_LOGS, 1):
        print(f"\n--- 测试 {i} ---")
        print(f"日志: {log[:80]}...")
        
        matched = False
        # 尝试匹配成功登录
        match = PATTERN_ACCEPTED.search(log)
        if match:
            print(f"✅ 匹配成功登录: user={match.group('user')}, ip={match.group('ip')}")
            matched = True
            passed += 1
        else:
            # 尝试匹配失败登录
            match = PATTERN_FAILED.search(log)
            if match:
                print(f"✅ 匹配失败登录: user={match.group('user')}, ip={match.group('ip')}")
                matched = True
                passed += 1
        
        if not matched:
            print(f"❌ 匹配失败!")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = test_regex()
    exit(0 if success else 1)
