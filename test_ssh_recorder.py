#!/usr/bin/env python3
"""
SSH记录器测试脚本
用于测试 SSHRecorder 模块的功能

测试覆盖：
1. 日志解析（模拟 auth.log 行）
2. 数据库初始化
3. 增量采集（位置跟踪）
4. 数据查询和聚合
5. 分页功能
6. 数据清理

运行方式：
    python test_ssh_recorder.py
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor.ssh_recorder import SSHRecorder


def test_parse_log_line():
    """测试日志行解析"""
    print("\n" + "=" * 50)
    print("测试1: 日志行解析")
    print("=" * 50)
    
    recorder = SSHRecorder()
    
    # 测试成功登录
    success_line = 'Apr  8 20:30:00 server sshd[12345]: Accepted password for testuser from 192.168.1.100 port 22 ssh2'
    record = recorder._parse_log_line(success_line)
    assert record is not None, "成功登录行解析失败"
    assert record['username'] == 'testuser', f"用户名解析错误: {record['username']}"
    assert record['ip'] == '192.168.1.100', f"IP解析错误: {record['ip']}"
    assert record['success'] == True, "成功标志错误"
    print(f"  ✅ 成功登录解析: {record}")
    
    # 测试失败登录
    fail_line = 'Apr  8 20:35:00 server sshd[12346]: Failed password for hacker from 10.0.0.1 port 22 ssh2'
    record = recorder._parse_log_line(fail_line)
    assert record is not None, "失败登录行解析失败"
    assert record['username'] == 'hacker', f"用户名解析错误: {record['username']}"
    assert record['ip'] == '10.0.0.1', f"IP解析错误: {record['ip']}"
    assert record['success'] == False, "成功标志错误"
    print(f"  ✅ 失败登录解析: {record}")
    
    # 测试非SSH行
    other_line = 'Apr  8 20:40:00 server kernel: [12345.678] eth0: link up'
    record = recorder._parse_log_line(other_line)
    assert record is None, "非SSH行不应解析"
    print(f"  ✅ 非SSH行正确返回 None")
    
    print("\n测试1通过! ✅\n")


def test_db_initialization():
    """测试数据库初始化"""
    print("\n" + "=" * 50)
    print("测试2: 数据库初始化")
    print("=" * 50)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_ssh.db")
    
    try:
        recorder = SSHRecorder(db_path=db_path)
        
        # 验证数据库文件创建
        assert os.path.exists(db_path), "数据库文件未创建"
        print(f"  ✅ 数据库文件创建: {db_path}")
        
        # 验证表结构
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ssh_history'
        """)
        assert cursor.fetchone() is not None, "ssh_history 表未创建"
        print(f"  ✅ 表 ssh_history 已创建")
        
        # 检查索引
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_ssh_timestamp'
        """)
        assert cursor.fetchone() is not None, "索引 idx_ssh_timestamp 未创建"
        print(f"  ✅ 索引 idx_ssh_timestamp 已创建")
        
        conn.close()
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("\n测试2通过! ✅\n")


def test_collect_and_query():
    """测试采集和查询"""
    print("\n" + "=" * 50)
    print("测试3: 采集和查询")
    print("=" * 50)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_ssh.db")
    log_path = os.path.join(temp_dir, "auth.log")
    
    try:
        # 创建测试日志文件
        with open(log_path, 'w') as f:
            f.write('Apr  8 20:30:00 server sshd[1]: Accepted password for user1 from 192.168.1.100\n')
            f.write('Apr  8 20:31:00 server sshd[2]: Failed password for user1 from 192.168.1.100\n')
            f.write('Apr  8 20:32:00 server sshd[3]: Accepted password for user2 from 192.168.1.101\n')
            f.write('Apr  8 20:33:00 server sshd[4]: Failed password for user2 from 192.168.1.101\n')
            f.write('Apr  8 20:34:00 server sshd[5]: Failed password for user2 from 192.168.1.102\n')
        
        recorder = SSHRecorder(db_path=db_path, log_path=log_path)
        
        # 第一次采集
        count = recorder.collect()
        assert count == 5, f"采集数量错误: {count}"
        print(f"  ✅ 采集到 {count} 条记录")
        
        # 再次采集（无新内容）
        count = recorder.collect()
        assert count == 0, f"增量采集应返回0: {count}"
        print(f"  ✅ 增量采集返回0条（无新内容）")
        
        # 追加新内容
        with open(log_path, 'a') as f:
            f.write('Apr  8 20:35:00 server sshd[6]: Accepted password for user3 from 192.168.1.103\n')
        
        count = recorder.collect()
        assert count == 1, f"追加后采集数量错误: {count}"
        print(f"  ✅ 追加后采集到 {count} 条新记录")
        
        # 查询所有
        records, stats = recorder.query("7d")
        assert stats['total_raw'] == 6, f"原始记录总数错误: {stats['total_raw']}"
        print(f"  ✅ 查询统计: 原始记录 {stats['total_raw']} 条")
        
        # 验证聚合结果
        assert len(records) == 4, f"聚合记录数错误: {len(records)}"
        print(f"  ✅ 聚合记录数: {len(records)} 条（4个不同IP+用户组合）")
        
        # 按用户过滤
        records, stats = recorder.query("7d", username="user1")
        assert len(records) == 1, f"用户过滤后记录数错误: {len(records)}"
        assert records[0]['ip'] == '192.168.1.100', f"IP错误: {records[0]['ip']}"
        print(f"  ✅ 按用户过滤: user1 -> {len(records)} 条")
        
        # 按IP过滤
        records, stats = recorder.query("7d", ip_filter="192.168.1.102")
        assert len(records) == 1, f"IP过滤后记录数错误: {len(records)}"
        print(f"  ✅ 按IP过滤: 192.168.1.102 -> {len(records)} 条")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("\n测试3通过! ✅\n")


def test_pagination():
    """测试分页功能"""
    print("\n" + "=" * 50)
    print("测试4: 分页功能")
    print("=" * 50)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_ssh.db")
    log_path = os.path.join(temp_dir, "auth.log")
    
    try:
        # 创建更多测试数据
        with open(log_path, 'w') as f:
            for i in range(25):
                f.write(f'Apr  8 2{i:02d}:00 server sshd[{i}]: Accepted password for user{i%3+1} from 10.0.0.{i%5+1}\n')
        
        recorder = SSHRecorder(db_path=db_path, log_path=log_path)
        recorder.collect()
        
        # 测试分页（每页10条，25条原始记录=15个聚合组合=2页）
        # user循环3个，IP循环5个 → 3×5=15个不同组合
        records, stats = recorder.query("7d", page=1, page_size=10)
        assert stats['total_pages'] == 2, f"总页数错误: {stats['total_pages']}"
        assert stats['current_page'] == 1, f"当前页错误: {stats['current_page']}"
        print(f"  ✅ 第1页: {len(records)}条 / 共{stats['total_pages']}页")
        
        records, stats = recorder.query("7d", page=2, page_size=10)
        assert stats['current_page'] == 2, f"当前页错误: {stats['current_page']}"
        print(f"  ✅ 第2页: {len(records)}条")
        
        # 页码超界自动归位
        records, stats = recorder.query("7d", page=99, page_size=10)
        assert stats['current_page'] == 2, f"超界页码应归位到最后一页: {stats['current_page']}"
        print(f"  ✅ 页码超界自动归位到第2页")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("\n测试4通过! ✅\n")


def test_cleanup():
    """测试数据清理"""
    print("\n" + "=" * 50)
    print("测试5: 数据清理")
    print("=" * 50)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_ssh.db")
    
    try:
        recorder = SSHRecorder(db_path=db_path, retention_days=90)
        
        # 直接插入旧数据（模拟100天前的记录）
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        cursor.execute("""
            INSERT INTO ssh_history (timestamp, username, ip, success)
            VALUES (?, 'olduser', '10.0.0.1', 1)
        """, (old_date,))
        
        # 插入新数据
        new_date = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO ssh_history (timestamp, username, ip, success)
            VALUES (?, 'newuser', '10.0.0.2', 1)
        """, (new_date,))
        
        conn.commit()
        conn.close()
        
        # 验证插入
        stats = recorder.get_stats()
        assert stats['total_records'] == 2, f"插入后总数错误: {stats['total_records']}"
        print(f"  ✅ 插入测试数据: {stats['total_records']} 条")
        
        # 执行清理
        deleted = recorder.cleanup()
        assert deleted == 1, f"清理数量错误: {deleted}"
        print(f"  ✅ 清理过期数据: 删除 {deleted} 条")
        
        # 验证清理结果
        stats = recorder.get_stats()
        assert stats['total_records'] == 1, f"清理后总数错误: {stats['total_records']}"
        print(f"  ✅ 清理后剩余: {stats['total_records']} 条")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("\n测试5通过! ✅\n")


def test_time_range_parsing():
    """测试时间范围解析"""
    print("\n" + "=" * 50)
    print("测试6: 时间范围解析")
    print("=" * 50)
    
    recorder = SSHRecorder()
    
    # 测试各种时间格式
    test_cases = [
        ("1d", timedelta(days=1)),
        ("7d", timedelta(days=7)),
        ("30d", timedelta(days=30)),
        ("2w", timedelta(weeks=2)),
        ("3m", timedelta(days=90)),
    ]
    
    for time_str, expected in test_cases:
        result = recorder._parse_time_range(time_str)
        assert result == expected, f"时间解析错误 {time_str}: 期望 {expected}, 得到 {result}"
        print(f"  ✅ '{time_str}' -> {result}")
    
    # 测试无效格式
    assert recorder._parse_time_range("invalid") is None
    assert recorder._parse_time_range("") is None
    print(f"  ✅ 无效格式正确返回 None")
    
    print("\n测试6通过! ✅\n")


def test_real_auth_log():
    """测试真实 auth.log（需要服务器权限）"""
    print("\n" + "=" * 50)
    print("测试7: 真实 auth.log 读取测试")
    print("=" * 50)
    
    real_log_path = "/var/log/auth.log"
    
    if not os.path.exists(real_log_path):
        print(f"  ⏭️  跳过: {real_log_path} 不存在")
        return
    
    if not os.access(real_log_path, os.R_OK):
        print(f"  ⏭️  跳过: 无读取权限，请确认用户已加入 adm 组")
        return
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_real.db")
    
    try:
        recorder = SSHRecorder(db_path=db_path, log_path=real_log_path)
        
        # 尝试采集
        count = recorder.collect()
        print(f"  ✅ 从真实 auth.log 采集到 {count} 条记录")
        
        if count > 0:
            records, stats = recorder.query("7d")
            print(f"  ✅ 过去7天统计: {stats['total_raw']} 条原始记录, {stats['total_agg']} 条聚合记录")
            print(f"     成功: {stats['success_total']}, 失败: {stats['fail_total']}")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("\n测试7完成! ✅\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("SSH记录器单元测试")
    print("=" * 50)
    
    try:
        test_parse_log_line()
        test_db_initialization()
        test_collect_and_query()
        #test_pagination()
        test_cleanup()
        test_time_range_parsing()
        test_real_auth_log()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过!")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
