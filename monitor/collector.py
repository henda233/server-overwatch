"""
系统资源数据采集模块
负责采集GPU、CPU、内存、显存、在线用户等数据
"""

import subprocess
import re
from typing import Dict, List


class Collector:
    """系统资源采集器
    
    通过执行系统命令采集服务器资源使用情况：
    - GPU使用率和显存 (nvidia-smi)
    - 内存使用 (free)
    - CPU使用率 (top)
    - 在线用户 (who)
    """
    
    def collect(self) -> Dict[str, Dict]:
        """采集所有在线用户的资源使用情况
        
        Returns:
            Dict[用户名, Dict[资源数据]]
            格式: {
                "user1": {
                    "gpu_percent": 80,
                    "gpu_memory_mb": 20000,
                    "gpu_memory_total_mb": 98000,
                    "cpu_percent": 40,
                    "memory_percent": 60
                },
                ...
            }
        """
        # 获取在线用户
        users = self.collect_users()
        
        # 采集系统资源
        gpu_data = self.collect_gpu()
        memory_data = self.collect_memory()
        cpu_data = self.collect_cpu()
        
        # 构建用户资源映射（简化版：所有用户共享系统资源）
        result = {}
        for user in users:
            result[user] = {
                "gpu_percent": gpu_data.get("utilization", 0),
                "gpu_memory_mb": gpu_data.get("memory_used_mb", 0),
                "gpu_memory_total_mb": gpu_data.get("memory_total_mb", 0),
                "cpu_percent": cpu_data.get("percent", 0),
                "memory_percent": memory_data.get("percent", 0)
            }
        
        # 如果没有用户，至少返回系统总体情况
        if not result:
            result["system"] = {
                "gpu_percent": gpu_data.get("utilization", 0),
                "gpu_memory_mb": gpu_data.get("memory_used_mb", 0),
                "gpu_memory_total_mb": gpu_data.get("memory_total_mb", 0),
                "cpu_percent": cpu_data.get("percent", 0),
                "memory_percent": memory_data.get("percent", 0)
            }
        
        return result
    
    def collect_gpu(self) -> Dict:
        """采集GPU信息
        
        使用 nvidia-smi 获取 GPU 使用率和显存信息。
        
        Returns:
            Dict包含:
                - utilization: GPU使用率 (0-100)
                - memory_used_mb: 已用显存 (MB)
                - memory_total_mb: 总显存 (MB)
        """
        result = {
            "utilization": 0,
            "memory_used_mb": 0,
            "memory_total_mb": 0
        }
        
        try:
            # 获取GPU使用率
            cmd_util = [
                "nvidia-smi",
                "--query-gpu=utilization.gpu",
                "--format=csv,noheader,nounits"
            ]
            output = subprocess.check_output(cmd_util, text=True, timeout=5)
            result["utilization"] = int(output.strip())
        except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
            pass
        
        try:
            # 获取显存使用情况
            cmd_mem = [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ]
            output = subprocess.check_output(cmd_mem, text=True, timeout=5)
            parts = output.strip().split(",")
            if len(parts) == 2:
                result["memory_used_mb"] = int(parts[0].strip())
                result["memory_total_mb"] = int(parts[1].strip())
        except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
            pass
        
        return result
    
    def collect_memory(self) -> Dict:
        """采集内存信息
        
        使用 free 命令获取内存使用情况。
        
        Returns:
            Dict包含:
                - percent: 内存使用百分比 (0-100)
                - used_mb: 已用内存 (MB)
                - total_mb: 总内存 (MB)
        """
        result = {
            "percent": 0,
            "used_mb": 0,
            "total_mb": 0
        }
        
        try:
            output = subprocess.check_output(
                ["free", "-m"],
                text=True,
                timeout=5
            )
            lines = output.strip().split("\n")
            for line in lines:
                if line.startswith("Mem:"):
                    parts = line.split()
                    if len(parts) >= 3:
                        total = int(parts[1])
                        used = int(parts[2])
                        result["total_mb"] = total
                        result["used_mb"] = used
                        if total > 0:
                            result["percent"] = round(used / total * 100)
                    break
        except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
            pass
        
        return result
    
    def collect_cpu(self) -> Dict:
        """采集CPU使用率
        
        使用 top 命令获取CPU使用情况。
        
        Returns:
            Dict包含:
                - percent: CPU使用百分比 (0-100)
        """
        result = {"percent": 0}
        
        try:
            output = subprocess.check_output(
                ["top", "-bn1"],
                text=True,
                timeout=5
            )
            lines = output.strip().split("\n")
            for line in lines:
                # 查找 %Cpu(s) 行
                if "%Cpu" in line or "Cpu(s)" in line:
                    # 格式: %Cpu(s):  40.0 us,  5.0 sy,  0.0 ni, 55.0 id, ...
                    match = re.search(r"(\d+\.?\d*)\s*(?:us|wa|id)", line)
                    if match:
                        # 计算使用率 = 100 - idle
                        idle_match = re.search(r"(\d+\.?\d*)\s*id", line)
                        if idle_match:
                            idle = float(idle_match.group(1))
                            result["percent"] = min(100, round(100 - idle))
                    break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        return result
    
    def collect_users(self) -> List[str]:
        """采集在线用户名列表
        
        使用 who 命令获取当前登录的用户。
        
        Returns:
            用户名列表
        """
        users = []
        
        try:
            output = subprocess.check_output(
                ["who"],
                text=True,
                timeout=5
            )
            lines = output.strip().split("\n")
            for line in lines:
                if line:
                    # 格式: user  pts/0  2026-04-07 10:00 (:0)
                    parts = line.split()
                    if parts:
                        username = parts[0]
                        if username not in users:
                            users.append(username)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        return users
