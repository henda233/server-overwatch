#!/usr/bin/env python3
"""
Plan-09 功能验证测试脚本
执行方式: python test_plan09.py
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor.recorder import Recorder
from monitor.formatter import Formatter
from bot.handler import CommandHandler, Command


def test_command_parse():
    """测试命令解析"""
    print("=" * 60)
    print("测试1: 命令解析 (Command.parse)")
    print("=" * 60)
    
    handler = CommandHandler(None, None, None)
    test_cases = [
        ("/info", "无参数-实时"),
        ("/info cxy", "仅用户名-实时"),
        ("/info 3d", "仅时间范围-历史"),
        ("/info cxy 3d", "组合命令-用户+时间"),
        ("/info testuser 7d", "组合命令-长用户名"),
        ("/info 2w", "周时间范围"),
        ("/info 1m", "月时间范围"),
    ]
    
    for cmd_text, desc in test_cases:
        cmd = handler.parse(cmd_text)
        print(f"\n输入: {cmd_text}")
        print(f"  描述: {desc}")
        print(f"  结果: action={cmd.action}, target={cmd.target}, time_range={cmd.time_range}")


def test_formatter_realtime():
    """测试实时数据格式化"""
    print("\n" + "=" * 60)
    print("测试2: 实时数据格式化 (format_realtime)")
    print("=" * 60)
    
    formatter = Formatter()
    
    # 测试数据
    test_data = {
        "cxy": {
            "gpu_percent": 92.0,
            "gpu_memory_mb": 46387,  # ~45.2GB
            "gpu_memory_total_mb": 100352,  # ~98GB
            "cpu_percent": 85.2,
            "memory_percent": 72.1
        },
        "lgl": {
            "gpu_percent": 45.0,
            "gpu_memory_mb": 12582,  # ~12.3GB
            "gpu_memory_total_mb": 100352,
            "cpu_percent": 52.1,
            "memory_percent": 65.3
        }
    }
    
    result = formatter.format_realtime(test_data)
    print("\n格式化结果:")
    print(result)


def test_formatter_history_compact():
    """测试精简历史数据格式化"""
    print("\n" + "=" * 60)
    print("测试3: 精简历史数据格式化 (format_history_compact)")
    print("=" * 60)
    
    formatter = Formatter()
    
    # 测试数据
    test_records = [
        {"timestamp": "2026-04-07T15:50:00", "username": "cxy", "gpu_percent": 92.0, "gpu_memory_mb": 46387, "cpu_percent": 85.2, "memory_percent": 72.1},
        {"timestamp": "2026-04-07T15:40:00", "username": "cxy", "gpu_percent": 88.0, "gpu_memory_mb": 45875, "cpu_percent": 82.1, "memory_percent": 71.8},
        {"timestamp": "2026-04-06T14:20:00", "username": "lgl", "gpu_percent": 45.0, "gpu_memory_mb": 12582, "cpu_percent": 52.1, "memory_percent": 65.3},
    ]
    test_stats = {
        "total": 100,
        "valid": 3,
        "filtered": 97,
        "cpu_peak": 85.2,
        "mem_peak": 72.1,
        "gpu_peak": 92.0
    }
    
    # 多用户模式
    print("\n[多用户模式] /info 3d")
    result = formatter.format_history_compact(test_records, test_stats, "3天")
    print(result)
    
    # 单用户模式
    print("\n[单用户模式] /info cxy 3d")
    user_records = [r for r in test_records if r["username"] == "cxy"]
    result = formatter.format_history_compact(user_records, test_stats, "3天", "cxy")
    print(result)


def test_formatter_user_detail():
    """测试用户详情格式化"""
    print("\n" + "=" * 60)
    print("测试4: 用户详情格式化 (format_user_detail)")
    print("=" * 60)
    
    formatter = Formatter()
    
    user_data = {
        "gpu_percent": 92.0,
        "gpu_memory_mb": 46387,
        "gpu_memory_total_mb": 100352,
        "cpu_percent": 85.2,
        "memory_percent": 72.1
    }
    
    result = formatter.format_user_detail("cxy", user_data)
    print(result)


def test_recorder_query_filtered():
    """测试精简历史查询"""
    print("\n" + "=" * 60)
    print("测试5: 精简历史查询 (recorder.query_filtered)")
    print("=" * 60)
    
    recorder = Recorder("history.db")
    
    # 检查方法是否存在
    if not hasattr(recorder, 'query_filtered'):
        print("❌ query_filtered 方法不存在!")
        return
    
    print("✅ query_filtered 方法存在")
    
    # 测试查询
    print("\n查询最近3天的数据...")
    records, stats = recorder.query_filtered("3d")
    print(f"总记录数: {stats['total']}")
    print(f"有效记录数: {stats['valid']}")
    print(f"过滤记录数: {stats['filtered']}")
    print(f"GPU峰值: {stats['gpu_peak']}%")
    print(f"CPU峰值: {stats['cpu_peak']}%")
    print(f"内存峰值: {stats['mem_peak']}%")
    
    if records:
        print(f"\n前3条有效记录:")
        for r in records[:3]:
            print(f"  {r['timestamp']} | {r['username']} | GPU:{r['gpu_percent']}% | 显存:{r['gpu_memory_mb']}MB")
    
    # 测试指定用户查询
    print("\n查询cxy用户的数据...")
    records, stats = recorder.query_filtered("3d", "cxy")
    print(f"总记录数: {stats['total']}")
    print(f"有效记录数: {stats['valid']}")
    print(f"过滤记录数: {stats['filtered']}")


def test_handler_integration():
    """测试 Handler 集成"""
    print("\n" + "=" * 60)
    print("测试6: Handler 集成测试")
    print("=" * 60)
    
    from monitor.collector import Collector
    
    collector = Collector()
    recorder = Recorder("history.db")
    formatter = Formatter()
    
    handler = CommandHandler(collector, recorder, formatter)
    
    # 测试各种命令解析
    test_cases = [
        "/info",
        "/info cxy",
        "/info 3d",
        "/info cxy 3d",
        "/help",
    ]
    
    for cmd_text in test_cases:
        cmd = handler.parse(cmd_text)
        print(f"\n命令: {cmd_text}")
        print(f"  -> action={cmd.action}, target={cmd.target}, time_range={cmd.time_range}")
        
        # 检查组合命令是否正确解析
        if cmd_text == "/info cxy 3d":
            if cmd.target == "cxy" and cmd.time_range == "3d":
                print("  ✅ 组合命令解析正确!")
            else:
                print("  ❌ 组合命令解析错误!")


def main():
    print("Plan-09 历史记录精简模式 & 统一 UI 优化 - 功能验证")
    print("=" * 60)
    
    test_command_parse()
    test_formatter_realtime()
    test_formatter_history_compact()
    test_formatter_user_detail()
    test_recorder_query_filtered()
    test_handler_integration()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
