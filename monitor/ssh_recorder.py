"""
SSH连接记录模块
负责从 /var/log/auth.log 采集SSH连接信息，存入SQLite数据库
"""

import sqlite3
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SSHRecorder:
    """SSH连接记录管理器
    
    从 auth.log 采集SSH连接记录：
    - 自动创建数据库和表
    - 支持增量采集（基于文件位置）
    - 支持按用户、IP过滤查询
    - 支持分页和统计聚合
    - 支持90天数据自动清理
    """
    
    # SSH日志正则表达式（支持两种格式）
    # 格式1（传统syslog）: Apr  8 20:30:00 hostname sshd[12345]: Accepted password for user from ip
    # 格式2（ISO 8601）: 2026-04-09T10:59:28.898309+08:00 hostname sshd[5867]: Accepted password for user from ip
    
    # 成功登录
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
    # 失败登录
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
    
    def __init__(self, db_path: str = "ssh_history.db", log_path: str = "/var/log/auth.log", 
                 retention_days: int = 90):
        """初始化SSH记录器
        
        Args:
            db_path: 数据库文件路径
            log_path: SSH日志文件路径
            retention_days: 数据保留天数
        """
        self.db_path = db_path
        self.log_path = log_path
        self.retention_days = retention_days
        self._position_file = db_path + ".pos"  # 记录上次读取位置
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库，创建表和索引"""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建SSH历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ssh_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                username TEXT NOT NULL,
                ip TEXT NOT NULL,
                success BOOLEAN NOT NULL
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ssh_timestamp 
            ON ssh_history(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ssh_username 
            ON ssh_history(username)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ssh_ip 
            ON ssh_history(ip)
        """)
        
        conn.commit()
        conn.close()
    
    def _get_position(self) -> int:
        """获取上次读取位置"""
        try:
            if os.path.exists(self._position_file):
                with open(self._position_file, 'r') as f:
                    return int(f.read().strip())
        except Exception:
            pass
        return 0
    
    def _set_position(self, pos: int) -> None:
        """设置当前读取位置"""
        try:
            with open(self._position_file, 'w') as f:
                f.write(str(pos))
        except Exception as e:
            logger.warning(f"无法保存读取位置: {e}")
    
    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """解析单行日志
        
        Args:
            line: 日志行
            
        Returns:
            Dict包含 timestamp, username, ip, success，或None
        """
        # 尝试匹配成功登录
        match = self.PATTERN_ACCEPTED.search(line)
        if match:
            return self._build_record(match, success=True)
        
        # 尝试匹配失败登录
        match = self.PATTERN_FAILED.search(line)
        if match:
            return self._build_record(match, success=False)
        
        return None
    
    def _build_record(self, match: re.Match, success: bool) -> Dict:
        """构建记录Dict
        
        支持两种auth.log时间格式：
        1. 传统syslog: Apr  8 20:30:00
        2. ISO 8601: 2026-04-09T10:59:28（通过捕获的time2获取时间部分）
        """
        year = datetime.now().year
        
        # 尝试从传统syslog格式获取时间 (group 'month', 'day', 'time')
        month = match.group('month1')
        day = match.group('day1')
        time_str = match.group('time1')
        
        if month is None:
            # ISO 8601格式，只有时间部分被捕获
            time_str = match.group('time2')
            # 使用当前日期（ISO格式不包含日期，需要从文件或其他方式获取）
            # 这里使用datetime.now()的日期部分
            now = datetime.now()
            timestamp = now.replace(
                hour=int(time_str.split(':')[0]),
                minute=int(time_str.split(':')[1]),
                second=int(time_str.split(':')[2]),
                microsecond=0
            )
        else:
            # 解析传统syslog格式时间
            try:
                timestamp = datetime.strptime(f"{year} {month} {day} {time_str}", "%Y %b %d %H:%M:%S")
            except ValueError:
                timestamp = datetime.now()
        
        return {
            "timestamp": timestamp,
            "username": match.group('user'),
            "ip": match.group('ip'),
            "success": success
        }
    
    def collect(self) -> int:
        """采集新增的SSH日志
        
        Returns:
            新增记录数
        """
        if not os.path.exists(self.log_path):
            logger.warning(f"SSH日志文件不存在: {self.log_path}")
            return 0
        
        # 获取当前文件大小
        current_size = os.path.getsize(self.log_path)
        last_pos = self._get_position()
        
        # 如果文件被轮转（变小），从头开始读
        if current_size < last_pos:
            last_pos = 0
        
        # 打开文件读取新增内容
        try:
            with open(self.log_path, 'r', errors='ignore') as f:
                f.seek(last_pos)
                new_lines = f.readlines()
                new_pos = f.tell()
        except PermissionError:
            logger.error(f"权限不足，无法读取 {self.log_path}，请确保用户已加入 adm 组")
            return 0
        except Exception as e:
            logger.error(f"读取日志文件失败: {e}")
            return 0
        
        if not new_lines:
            return 0
        
        # 解析并保存记录
        new_records = []
        for line in new_lines:
            record = self._parse_log_line(line)
            if record:
                new_records.append(record)
        
        if new_records:
            self._save_records(new_records)
        
        # 保存读取位置
        self._set_position(new_pos)
        
        logger.info(f"采集到 {len(new_records)} 条SSH记录")
        return len(new_records)
    
    def _save_records(self, records: List[Dict]) -> None:
        """批量保存记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for record in records:
            cursor.execute("""
                INSERT INTO ssh_history (timestamp, username, ip, success)
                VALUES (?, ?, ?, ?)
            """, (
                record["timestamp"].isoformat(),
                record["username"],
                record["ip"],
                record["success"]
            ))
        
        conn.commit()
        conn.close()
    
    def query(self, time_range: str, username: Optional[str] = None, 
              ip_filter: Optional[str] = None, page: int = 1, 
              page_size: int = 10) -> Tuple[List[Dict], Dict]:
        """查询SSH记录（带聚合统计）
        
        Args:
            time_range: 时间范围，如 "1d", "7d", "2w", "1m"
            username: 可选，按用户名过滤
            ip_filter: 可选，按IP过滤
            page: 页码，默认第1页
            page_size: 每页条数，默认10条
            
        Returns:
            (聚合后的记录列表, 统计信息Dict)
            记录: 按 (ip, username) 分组，统计成功/失败次数
            统计: {
                "total_agg": int,      # 聚合后的记录数
                "total_raw": int,      # 原始记录总数
                "success_total": int, # 成功总数
                "fail_total": int,     # 失败总数
                "total_pages": int,   # 总页数
                "current_page": int    # 当前页
            }
        """
        delta = self._parse_time_range(time_range)
        if delta is None:
            return [], {"total_agg": 0, "total_raw": 0, "success_total": 0, 
                       "fail_total": 0, "total_pages": 0, "current_page": 1}
        
        start_time = datetime.now() - delta
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 构建WHERE条件
        conditions = ["timestamp >= ?"]
        params = [start_time.isoformat()]
        
        if username:
            conditions.append("username = ?")
            params.append(username)
        
        if ip_filter:
            conditions.append("ip = ?")
            params.append(ip_filter)
        
        where_clause = " AND ".join(conditions)
        
        # 查询原始总数和成功/失败数
        cursor.execute(f"""
            SELECT COUNT(*), SUM(CASE WHEN success THEN 1 ELSE 0 END), 
                   SUM(CASE WHEN success THEN 0 ELSE 1 END)
            FROM ssh_history
            WHERE {where_clause}
        """, params)
        
        row = cursor.fetchone()
        total_raw = row[0] or 0
        success_total = row[1] or 0
        fail_total = row[2] or 0
        
        # 查询聚合后的记录数（按 IP+用户名 分组）
        cursor.execute(f"""
            SELECT COUNT(DISTINCT ip || username)
            FROM ssh_history
            WHERE {where_clause}
        """, params)
        
        total_agg = cursor.fetchone()[0] or 0
        
        # 计算总页数
        total_pages = max(1, (total_agg + page_size - 1) // page_size)
        # 确保页码在有效范围内
        page = min(max(1, page), total_pages)
        offset = (page - 1) * page_size
        
        # 查询聚合记录（按次数降序）
        cursor.execute(f"""
            SELECT ip, username, 
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                   SUM(CASE WHEN success THEN 0 ELSE 1 END) as fail_count
            FROM ssh_history
            WHERE {where_clause}
            GROUP BY ip, username
            ORDER BY (success_count + fail_count) DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            records.append({
                "ip": row[0],
                "username": row[1],
                "success_count": row[2],
                "fail_count": row[3]
            })
        
        stats = {
            "total_agg": total_agg,
            "total_raw": total_raw,
            "success_total": success_total,
            "fail_total": fail_total,
            "total_pages": total_pages,
            "current_page": page
        }
        
        return records, stats
    
    def query_detailed(self, time_range: str, ip: str, username: str,
                       page: int = 1, page_size: int = 10) -> Tuple[List[Dict], Dict]:
        """查询指定IP和用户的详细记录
        
        Args:
            time_range: 时间范围
            ip: IP地址
            username: 用户名
            page: 页码
            page_size: 每页条数
            
        Returns:
            (详细记录列表, 统计信息)
        """
        delta = self._parse_time_range(time_range)
        if delta is None:
            return [], {"total": 0, "total_pages": 0, "current_page": 1}
        
        start_time = datetime.now() - delta
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查询总数
        cursor.execute("""
            SELECT COUNT(*)
            FROM ssh_history
            WHERE timestamp >= ? AND ip = ? AND username = ?
        """, (start_time.isoformat(), ip, username))
        
        total = cursor.fetchone()[0] or 0
        
        # 计算总页数
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(max(1, page), total_pages)
        offset = (page - 1) * page_size
        
        # 查询详细记录
        cursor.execute("""
            SELECT timestamp, ip, username, success
            FROM ssh_history
            WHERE timestamp >= ? AND ip = ? AND username = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (start_time.isoformat(), ip, username, page_size, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            records.append({
                "timestamp": row[0],
                "ip": row[1],
                "username": row[2],
                "success": row[3]
            })
        
        stats = {
            "total": total,
            "total_pages": total_pages,
            "current_page": page
        }
        
        return records, stats
    
    def cleanup(self) -> int:
        """清理过期数据
        
        Returns:
            删除的记录数
        """
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM ssh_history
            WHERE timestamp < ?
        """, (cutoff.isoformat(),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            logger.info(f"清理了 {deleted} 条过期SSH记录")
        
        return deleted
    
    def _parse_time_range(self, time_range: str) -> Optional[timedelta]:
        """解析时间范围字符串"""
        time_range = time_range.lower().strip()
        
        if not time_range:
            return None
        
        if time_range.endswith("d"):
            try:
                days = int(time_range[:-1])
                return timedelta(days=days)
            except ValueError:
                return None
        elif time_range.endswith("w"):
            try:
                weeks = int(time_range[:-1])
                return timedelta(weeks=weeks)
            except ValueError:
                return None
        elif time_range.endswith("m"):
            try:
                months = int(time_range[:-1])
                return timedelta(days=months * 30)
            except ValueError:
                return None
        
        return None
    
    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*), MIN(timestamp), MAX(timestamp),
                   SUM(CASE WHEN success THEN 1 ELSE 0 END),
                   SUM(CASE WHEN success THEN 0 ELSE 1 END)
            FROM ssh_history
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total_records": row[0] or 0,
            "earliest": row[1],
            "latest": row[2],
            "success_count": row[3] or 0,
            "fail_count": row[4] or 0
        }
