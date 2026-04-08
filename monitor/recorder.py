"""
历史记录存储模块
负责将采集的数据存入SQLite数据库，并支持查询和清理
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os


class Recorder:
    """历史记录管理器
    
    使用SQLite存储资源使用历史记录：
    - 自动创建数据库和表
    - 支持按时间范围查询
    - 支持自动清理过期数据
    """
    
    def __init__(self, db_path: str = "history.db"):
        """初始化记录器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库，创建表和索引"""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建资源历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                username TEXT NOT NULL,
                gpu_percent INTEGER,
                gpu_memory_mb INTEGER,
                cpu_percent INTEGER,
                memory_percent INTEGER
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON resource_history(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_username 
            ON resource_history(username)
        """)
        
        conn.commit()
        conn.close()
    
    def save(self, timestamp: datetime, username: str, data: Dict) -> None:
        """保存单条记录
        
        Args:
            timestamp: 记录时间
            username: 用户名
            data: 资源数据，包含 gpu_percent, gpu_memory_mb, cpu_percent, memory_percent
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO resource_history 
            (timestamp, username, gpu_percent, gpu_memory_mb, cpu_percent, memory_percent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp.isoformat(),
            username,
            data.get("gpu_percent"),
            data.get("gpu_memory_mb"),
            data.get("cpu_percent"),
            data.get("memory_percent")
        ))
        
        conn.commit()
        conn.close()
    
    def query(self, time_range: str) -> List[Dict]:
        """查询历史数据
        
        Args:
            time_range: 时间范围，如 "1d", "7d", "2w", "1m"
            
        Returns:
            记录列表，每条记录是一个Dict
        """
        # 解析时间范围
        delta = self._parse_time_range(time_range)
        if delta is None:
            return []
        
        start_time = datetime.now() - delta
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, username, gpu_percent, gpu_memory_mb, 
                   cpu_percent, memory_percent
            FROM resource_history
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (start_time.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            records.append({
                "timestamp": row[0],
                "username": row[1],
                "gpu_percent": row[2],
                "gpu_memory_mb": row[3],
                "cpu_percent": row[4],
                "memory_percent": row[5]
            })
        
        return records
    
    def query_filtered(self, time_range: str, username: Optional[str] = None,
                   page: int = 1, page_size: int = 10) -> Tuple[List[Dict], Dict]:
        """查询历史数据（过滤0值，支持分页）
        
        Args:
            time_range: 时间范围，如 "1d", "7d", "2w", "1m"
            username: 可选，指定用户名
            page: 页码，默认第1页
            page_size: 每页条数，默认10条
            
        Returns:
            (过滤后的记录列表, 统计信息Dict)
            统计信息: {
                "total": int,      # 总记录数
                "valid": int,      # 有效记录数（受分页影响）
                "filtered": int,   # 被过滤的0值记录数
                "cpu_peak": float, # CPU峰值
                "mem_peak": float, # 内存峰值
                "gpu_peak": float, # GPU峰值
                "total_pages": int # 总页数
            }
        """
        delta = self._parse_time_range(time_range)
        if delta is None:
            return [], {"total": 0, "valid": 0, "filtered": 0, "cpu_peak": 0, "mem_peak": 0, "gpu_peak": 0, "total_pages": 0}
        
        start_time = datetime.now() - delta
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 过滤条件：只过滤所有资源都为0的记录
        filter_condition = "NOT (gpu_memory_mb = 0 AND cpu_percent = 0 AND memory_percent = 0)"
        
        # 查询总记录数（过滤后）
        if username:
            cursor.execute(f"""
                SELECT COUNT(*) FROM resource_history
                WHERE timestamp >= ? AND username = ? AND {filter_condition}
            """, (start_time.isoformat(), username))
        else:
            cursor.execute(f"""
                SELECT COUNT(*) FROM resource_history
                WHERE timestamp >= ? AND {filter_condition}
            """, (start_time.isoformat(),))
        filtered_total = cursor.fetchone()[0] or 0
        
        # 查询原始总记录数（未过滤）
        if username:
            cursor.execute("""
                SELECT COUNT(*) FROM resource_history
                WHERE timestamp >= ? AND username = ?
            """, (start_time.isoformat(), username))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM resource_history
                WHERE timestamp >= ?
            """, (start_time.isoformat(),))
        total = cursor.fetchone()[0] or 0
        
        # 计算总页数
        total_pages = max(1, (filtered_total + page_size - 1) // page_size)
        # 确保页码在有效范围内
        page = min(max(1, page), total_pages)
        # 计算 OFFSET
        offset = (page - 1) * page_size
        
        # 查询1: 获取峰值（全局聚合，与过滤记录分开）
        if username:
            cursor.execute(f"""
                SELECT MAX(cpu_percent), MAX(memory_percent), MAX(gpu_percent)
                FROM resource_history
                WHERE timestamp >= ? AND username = ? AND {filter_condition}
            """, (start_time.isoformat(), username))
        else:
            cursor.execute(f"""
                SELECT MAX(cpu_percent), MAX(memory_percent), MAX(gpu_percent)
                FROM resource_history
                WHERE timestamp >= ? AND {filter_condition}
            """, (start_time.isoformat(),))
        
        peak_row = cursor.fetchone()
        cpu_peak = peak_row[0] or 0 if peak_row else 0
        mem_peak = peak_row[1] or 0 if peak_row else 0
        gpu_peak = peak_row[2] or 0 if peak_row else 0
        
        # 查询2: 获取分页后的记录列表（按时间倒序）
        if username:
            cursor.execute(f"""
                SELECT timestamp, username, gpu_percent, gpu_memory_mb, 
                       cpu_percent, memory_percent
                FROM resource_history
                WHERE timestamp >= ? AND username = ? AND {filter_condition}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (start_time.isoformat(), username, page_size, offset))
        else:
            cursor.execute(f"""
                SELECT timestamp, username, gpu_percent, gpu_memory_mb, 
                       cpu_percent, memory_percent
                FROM resource_history
                WHERE timestamp >= ? AND {filter_condition}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (start_time.isoformat(), page_size, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            records.append({
                "timestamp": row[0],
                "username": row[1],
                "gpu_percent": row[2],
                "gpu_memory_mb": row[3],
                "cpu_percent": row[4],
                "memory_percent": row[5]
            })
        
        stats = {
            "total": total,
            "valid": len(records),
            "filtered": total - filtered_total,
            "cpu_peak": cpu_peak,
            "mem_peak": mem_peak,
            "gpu_peak": gpu_peak,
            "total_pages": total_pages,
            "current_page": page
        }
        
        return records, stats
    
    def _parse_time_range(self, time_range: str) -> Optional[timedelta]:
        """解析时间范围字符串
        
        Args:
            time_range: 如 "1d", "7d", "2w", "1m"
            
        Returns:
            timedelta对象，或None如果解析失败
        """
        time_range = time_range.lower().strip()
        
        if not time_range:
            return None
        
        if time_range.endswith("d"):
            # 天
            try:
                days = int(time_range[:-1])
                return timedelta(days=days)
            except ValueError:
                return None
        
        elif time_range.endswith("w"):
            # 周
            try:
                weeks = int(time_range[:-1])
                return timedelta(weeks=weeks)
            except ValueError:
                return None
        
        elif time_range.endswith("m"):
            # 月（按30天计算）
            try:
                months = int(time_range[:-1])
                return timedelta(days=months * 30)
            except ValueError:
                return None
        
        return None
    
    def cleanup(self, retention_days: int = 30) -> int:
        """清理过期数据
        
        Args:
            retention_days: 保留天数
            
        Returns:
            删除的记录条数
        """
        cutoff = datetime.now() - timedelta(days=retention_days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM resource_history
            WHERE timestamp < ?
        """, (cutoff.isoformat(),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_stats(self) -> Dict:
        """获取数据库统计信息
        
        Returns:
            Dict包含记录总数、最早记录时间、最新记录时间
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM resource_history
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total_records": row[0] or 0,
            "earliest": row[1],
            "latest": row[2]
        }
    
    def get_all_users_stats(self, time_range: str) -> Dict[str, Dict]:
        """获取所有用户的历史统计信息
        
        Args:
            time_range: 时间范围，如 "1d", "7d", "2w", "1m"
            
        Returns:
            Dict[用户名, Dict[统计信息]]
            统计信息: {
                "gpu_peak": float,      # GPU使用率峰值
                "gpu_avg": float,       # GPU使用率平均值
                "mem_peak_gb": float,   # 显存峰值(GB)
                "mem_avg_gb": float,    # 显存平均值(GB)
                "active_hours": int     # 活跃小时数（有记录的小时数）
            }
        """
        delta = self._parse_time_range(time_range)
        if delta is None:
            return {}
        
        start_time = datetime.now() - delta
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 按用户聚合统计
        cursor.execute("""
            SELECT 
                username,
                MAX(gpu_percent) as gpu_peak,
                AVG(gpu_percent) as gpu_avg,
                MAX(gpu_memory_mb) / 1024.0 as mem_peak_gb,
                AVG(gpu_memory_mb) / 1024.0 as mem_avg_gb
            FROM resource_history
            WHERE timestamp >= ? AND gpu_memory_mb > 0
            GROUP BY username
        """, (start_time.isoformat(),))
        
        rows = cursor.fetchall()
        
        # 计算活跃小时数（独立小时数）
        cursor.execute("""
            SELECT username, COUNT(DISTINCT strftime('%Y-%m-%d %H', timestamp)) as active_hours
            FROM resource_history
            WHERE timestamp >= ? AND gpu_memory_mb > 0
            GROUP BY username
        """, (start_time.isoformat(),))
        
        hours_rows = cursor.fetchall()
        hours_map = {row[0]: row[1] for row in hours_rows}
        
        conn.close()
        
        result = {}
        for row in rows:
            username = row[0]
            result[username] = {
                "gpu_peak": round(row[1] or 0, 1),
                "gpu_avg": round(row[2] or 0, 1),
                "mem_peak_gb": round(row[3] or 0, 1),
                "mem_avg_gb": round(row[4] or 0, 1),
                "active_hours": hours_map.get(username, 0)
            }
        
        return result
    
    def get_all_users(self, days: int = 30) -> List[Dict]:
        """获取所有历史用户及其简要统计
        
        Args:
            days: 统计天数（默认30天）
            
        Returns:
            用户列表，每条记录包含: username, last_active, total_records, gpu_peak
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                username,
                MAX(timestamp) as last_active,
                COUNT(*) as total_records,
                MAX(gpu_percent) as gpu_peak
            FROM resource_history
            WHERE timestamp >= ?
            GROUP BY username
            ORDER BY last_active DESC
        """, (cutoff.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "username": row[0],
                "last_active": row[1][:16] if row[1] else "无",
                "total_records": row[2],
                "gpu_peak": row[3] or 0
            })
        
        return result
