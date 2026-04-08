"""
历史查询翻页功能测试脚本
测试命令解析、分页查询、格式化输出
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bot.handler import CommandHandler
from monitor.collector import Collector
from monitor.recorder import Recorder
from monitor.formatter import Formatter


def test_command_parsing():
    """测试命令解析功能"""
    print("=" * 60)
    print("测试1: 命令解析 - 页码提取")
    print("=" * 60)
    
    recorder = Recorder()
    formatter = Formatter()
    collector = Collector()
    handler = CommandHandler(collector, recorder, formatter, page_size=10)
    
    test_cases = [
        # (输入命令, 期望action, 期望page)
        ("/info", "info", 1),
        ("/info 7d", "info", 1),
        ("/info 7d 1", "info", 1),
        ("/info 7d 2", "info", 2),
        ("/info 7d 10", "info", 10),
        ("/info cxy 7d", "info", 1),
        ("/info cxy 7d 1", "info", 1),
        ("/info cxy 7d 2", "info", 2),
        ("/stats 3d", "stats", 1),
        ("/stats 3d 2", "stats", 2),
        ("/top gpu", "top", 1),
        ("/top gpu 2", "top", 2),
        ("/users 7d", "users", 1),
        ("/users 7d 3", "users", 3),
        ("/help", "help", 1),
        ("/help 5", "help", 5),  # help命令也会解析页码
    ]
    
    all_passed = True
    for cmd_text, expected_action, expected_page in test_cases:
        cmd = handler.parse(cmd_text)
        action_ok = cmd.action == expected_action
        page_ok = cmd.page == expected_page
        
        if action_ok and page_ok:
            print(f"✅ PASS: '{cmd_text}' -> action={cmd.action}, page={cmd.page}")
        else:
            print(f"❌ FAIL: '{cmd_text}'")
            print(f"   期望: action={expected_action}, page={expected_page}")
            print(f"   实际: action={cmd.action}, page={cmd.page}")
            all_passed = False
    
    print()
    return all_passed


def test_pagination_query():
    """测试分页查询功能"""
    print("=" * 60)
    print("测试2: 分页查询 - query_filtered")
    print("=" * 60)
    
    recorder = Recorder()
    page_size = 10
    
    # 查询7天的数据
    time_range = "7d"
    
    # 获取总记录数（第一页）
    records_p1, stats_p1 = recorder.query_filtered(time_range, page=1, page_size=page_size)
    
    print(f"总记录数: {stats_p1['total']}")
    print(f"过滤后: {stats_p1['valid']}")
    print(f"总页数: {stats_p1['total_pages']}")
    print(f"第1页记录数: {len(records_p1)}")
    print()
    
    # 检查分页是否正确
    all_passed = True
    
    # 第1页记录数应该 <= page_size
    if len(records_p1) <= page_size:
        print(f"✅ 第1页记录数正确: {len(records_p1)} <= {page_size}")
    else:
        print(f"❌ 第1页记录数错误: {len(records_p1)} > {page_size}")
        all_passed = False
    
    # 如果有多页，测试第2页
    if stats_p1['total_pages'] >= 2:
        records_p2, stats_p2 = recorder.query_filtered(time_range, page=2, page_size=page_size)
        print(f"第2页记录数: {len(records_p2)}")
        
        # 第2页记录数应该 <= page_size
        if len(records_p2) <= page_size:
            print(f"✅ 第2页记录数正确: {len(records_p2)} <= {page_size}")
        else:
            print(f"❌ 第2页记录数错误: {len(records_p2)} > {page_size}")
            all_passed = False
        
        # 检查第1页和第2页数据不重复
        if records_p1 and records_p2:
            p1_timestamps = {r['timestamp'] for r in records_p1}
            p2_timestamps = {r['timestamp'] for r in records_p2}
            if p1_timestamps.isdisjoint(p2_timestamps):
                print(f"✅ 第1页和第2页数据不重复")
            else:
                print(f"❌ 第1页和第2页数据有重复!")
                all_passed = False
    else:
        print("（数据不足1页，跳过第2页测试）")
    
    # 测试页码边界
    if stats_p1['total_pages'] >= 1:
        # 请求超过最大页数
        last_page = stats_p1['total_pages']
        records_last, stats_last = recorder.query_filtered(time_range, page=last_page + 10, page_size=page_size)
        
        if stats_last['current_page'] == last_page:
            print(f"✅ 页码超界自动归位到最后一页: {last_page + 10} -> {stats_last['current_page']}")
        else:
            print(f"❌ 页码超界未正确处理: 期望{last_page}, 实际{stats_last['current_page']}")
            all_passed = False
        
        # 请求第0页或负数
        records_zero, stats_zero = recorder.query_filtered(time_range, page=0, page_size=page_size)
        if stats_zero['current_page'] == 1:
            print(f"✅ 页码0自动归位到第1页: 0 -> {stats_zero['current_page']}")
        else:
            print(f"❌ 页码0未正确处理: 期望1, 实际{stats_zero['current_page']}")
            all_passed = False
    
    print()
    return all_passed


def test_pagination_format():
    """测试分页格式化输出"""
    print("=" * 60)
    print("测试3: 分页格式化 - format_history_compact")
    print("=" * 60)
    
    recorder = Recorder()
    formatter = Formatter()
    page_size = 10
    
    # 查询数据
    time_range = "7d"
    records, stats = recorder.query_filtered(time_range, page=1, page_size=page_size)
    
    if not records:
        print("⚠️ 暂无历史记录，跳过格式化测试")
        print()
        return True
    
    print(f"格式化第1页（总{stats['total_pages']}页）:")
    print("-" * 40)
    
    output = formatter.format_history_compact(
        records, stats, time_range, username=None,
        page=stats['current_page'], page_size=page_size
    )
    print(output)
    print()
    
    # 测试指定用户
    # 获取第一个用户的记录
    first_user = records[0].get('username') if records else None
    if first_user:
        print(f"格式化指定用户 '{first_user}' 第1页:")
        print("-" * 40)
        
        records_user, stats_user = recorder.query_filtered(
            time_range, username=first_user, page=1, page_size=page_size
        )
        
        if records_user:
            output_user = formatter.format_history_compact(
                records_user, stats_user, time_range, username=first_user,
                page=stats_user['current_page'], page_size=page_size
            )
            print(output_user)
            print()
    
    print("✅ 格式化输出测试完成")
    print()
    return True


def test_full_pagination_flow():
    """测试完整分页流程"""
    print("=" * 60)
    print("测试4: 完整分页流程 - 多页数据遍历")
    print("=" * 60)
    
    recorder = Recorder()
    page_size = 10
    time_range = "7d"
    
    # 获取总页数
    _, stats = recorder.query_filtered(time_range, page=1, page_size=page_size)
    total_pages = stats['total_pages']
    
    print(f"总页数: {total_pages}")
    
    if total_pages <= 1:
        print("⚠️ 数据不足1页，跳过多页测试")
        print()
        return True
    
    all_timestamps = set()
    all_passed = True
    
    # 遍历每一页
    for page in range(1, min(total_pages + 1, 6)):  # 最多测试前5页
        records, page_stats = recorder.query_filtered(
            time_range, page=page, page_size=page_size
        )
        
        if not records:
            print(f"第{page}页: 无数据")
            continue
        
        # 检查时间戳不重复
        page_timestamps = {r['timestamp'] for r in records}
        
        if page_timestamps.isdisjoint(all_timestamps):
            print(f"第{page}页: ✅ {len(records)}条记录，时间戳无重复")
            all_timestamps.update(page_timestamps)
        else:
            overlap = page_timestamps.intersection(all_timestamps)
            print(f"第{page}页: ❌ 发现重复时间戳 {len(overlap)} 个")
            all_passed = False
    
    if total_pages > 5:
        print(f"... 还有 {total_pages - 5} 页未测试")
    
    print()
    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 历史查询翻页功能测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行所有测试
    results.append(("命令解析", test_command_parsing()))
    results.append(("分页查询", test_pagination_query()))
    results.append(("分页格式化", test_pagination_format()))
    results.append(("完整分页流程", test_full_pagination_flow()))
    
    # 输出总结
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 所有测试通过!")
    else:
        print("⚠️ 部分测试失败，请检查!")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
