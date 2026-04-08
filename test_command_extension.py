#!/usr/bin/env python3
"""
PLAN-010 命令扩展测试脚本
测试新增的3个命令: /stats, /top, /users

使用方法:
1. 将此脚本复制到GPU服务器的项目目录
2. 运行: python test_command_extension.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor.recorder import Recorder
from monitor.formatter import Formatter
from bot.handler import CommandHandler
from monitor.collector import Collector


def test_parser():
    """测试命令解析"""
    print("=" * 60)
    print("测试1: 命令解析 (parse)")
    print("=" * 60)
    
    recorder = Recorder("history.db")
    formatter = Formatter()
    collector = Collector()
    handler = CommandHandler(collector, recorder, formatter)
    
    test_cases = [
        ("/stats 3d", "统计查询-3天"),
        ("/stats 1w", "统计查询-1周"),
        ("/stats 1m", "统计查询-1月"),
        ("/top", "排行榜-默认GPU"),
        ("/top gpu", "排行榜-GPU排序"),
        ("/top mem", "排行榜-显存排序"),
        ("/top cpu", "排行榜-CPU排序"),
        ("/users", "用户列表-默认"),
        ("/users 7d", "用户列表-7天"),
        ("/users 30d", "用户列表-30天"),
    ]
    
    all_passed = True
    for cmd, desc in test_cases:
        try:
            result = handler.parse(cmd)
            print(f"✅ {cmd:20} -> action={result.action}, target={result.target}, time_range={result.time_range}, sort_by={result.sort_by}")
        except Exception as e:
            print(f"❌ {cmd:20} -> 错误: {e}")
            all_passed = False
    
    return all_passed


def test_recorder_methods():
    """测试 recorder 新方法"""
    print("\n" + "=" * 60)
    print("测试2: Recorder 数据层方法")
    print("=" * 60)
    
    recorder = Recorder("history.db")
    
    # 测试 get_all_users_stats
    print("\n[测试 get_all_users_stats(3d)]")
    try:
        stats = recorder.get_all_users_stats("3d")
        print(f"✅ 方法存在，返回类型: {type(stats)}")
        print(f"   数据样例: {list(stats.items())[:2] if stats else '空'}")
    except AttributeError:
        print("❌ get_all_users_stats 方法不存在")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    # 测试 get_top_users
    print("\n[测试 get_top_users(3d, gpu)]")
    try:
        top = recorder.get_top_users("3d", "gpu")
        print(f"✅ 方法存在，返回类型: {type(top)}")
        print(f"   数据样例: {top[:2] if top else '空'}")
    except AttributeError:
        print("❌ get_top_users 方法不存在")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    # 测试 get_all_users
    print("\n[测试 get_all_users(30)]")
    try:
        users = recorder.get_all_users(30)
        print(f"✅ 方法存在，返回类型: {type(users)}")
        print(f"   数据样例: {users[:2] if users else '空'}")
    except AttributeError:
        print("❌ get_all_users 方法不存在")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    return True


def test_formatter_methods():
    """测试 formatter 新方法"""
    print("\n" + "=" * 60)
    print("测试3: Formatter 格式化方法")
    print("=" * 60)
    
    formatter = Formatter()
    
    # 模拟数据
    mock_stats = {
        "cxy": {"gpu_peak": 92.5, "gpu_avg": 65.3, "mem_peak_gb": 45.2, "mem_avg_gb": 32.5, "active_hours": 72},
        "lgl": {"gpu_peak": 45.0, "gpu_avg": 30.2, "mem_peak_gb": 12.3, "mem_avg_gb": 8.2, "active_hours": 24},
    }
    
    mock_top = [
        {"username": "cxy", "gpu_percent": 92.5, "gpu_memory_mb": 46325, "cpu_percent": 80.0},
        {"username": "lgl", "gpu_percent": 45.0, "gpu_memory_mb": 12595, "cpu_percent": 15.0},
    ]
    
    mock_users = [
        {"username": "cxy", "last_active": "2026-04-08 10:00", "total_records": 1234, "gpu_peak": 92.5},
        {"username": "lgl", "last_active": "2026-04-07 14:20", "total_records": 456, "gpu_peak": 78.0},
    ]
    
    # 测试 format_stats
    print("\n[测试 format_stats]")
    try:
        result = formatter.format_stats(mock_stats, "3d")
        print(f"✅ format_stats 方法存在")
        print(f"   输出预览:\n{result[:200]}...")
    except AttributeError:
        print("❌ format_stats 方法不存在")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    # 测试 format_top
    print("\n[测试 format_top]")
    try:
        result = formatter.format_top(mock_top, "gpu")
        print(f"✅ format_top 方法存在")
        print(f"   输出预览:\n{result[:200]}...")
    except AttributeError:
        print("❌ format_top 方法不存在")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    # 测试 format_users
    print("\n[测试 format_users]")
    try:
        result = formatter.format_users(mock_users, "30d")
        print(f"✅ format_users 方法存在")
        print(f"   输出预览:\n{result[:200]}...")
    except AttributeError:
        print("❌ format_users 方法不存在")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    return True


def test_handler_integration():
    """测试 handler 集成"""
    print("\n" + "=" * 60)
    print("测试4: Handler 集成测试")
    print("=" * 60)
    
    recorder = Recorder("history.db")
    formatter = Formatter()
    collector = Collector()
    handler = CommandHandler(collector, recorder, formatter)
    
    test_cases = [
        "/stats 3d",
        "/top",
        "/top gpu",
        "/top mem",
        "/top cpu",
        "/users",
        "/users 30d",
    ]
    
    all_passed = True
    for cmd in test_cases:
        try:
            result = handler.parse(cmd)
            if result.action in ["stats", "top", "users"]:
                print(f"✅ {cmd:20} -> action={result.action} ✓")
            else:
                print(f"❌ {cmd:20} -> action={result.action} ✗ (期望: stats/top/users)")
                all_passed = False
        except Exception as e:
            print(f"❌ {cmd:20} -> 错误: {e}")
            all_passed = False
    
    return all_passed


def main():
    print("🎮 PLAN-010 命令扩展测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 命令解析
    results.append(("命令解析", test_parser()))
    
    # 测试2: Recorder 方法
    results.append(("Recorder方法", test_recorder_methods()))
    
    # 测试3: Formatter 方法
    results.append(("Formatter方法", test_formatter_methods()))
    
    # 测试4: Handler 集成
    results.append(("Handler集成", test_handler_integration()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name:20}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试失败，请检查实现")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
