"""
系统资源数据采集模块
负责采集GPU、CPU、内存、显存、在线用户等数据
"""

import subprocess
import re
from typing import Dict, List, Tuple
from collections import defaultdict


class Collector:
    """系统资源采集器
    
    通过执行系统命令采集服务器资源使用情况：
    - GPU使用率和显存 (nvidia-smi)
    - 内存使用 (free)
    - CPU使用率 (top)
    - 在线用户 (who)
    """
    
    def collect(self) -> Dict[str, Dict]:
        """采集所有在线用户的资源使用情况（按用户区分CPU/内存/GPU数据）
        
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
        
        # 获取进程信息（包含PID→用户名、CPU%、MEM%）
        pid_to_user, pid_info = self.get_process_info()
        
        # 获取每个计算进程的GPU使用情况
        processes = self.collect_process_gpu()
        
        # 按用户聚合GPU显存
        user_gpu = defaultdict(lambda: {"gpu_memory_mb": 0})
        
        for proc in processes:
            username = pid_to_user.get(proc["pid"])
            if username and username in users:
                user_gpu[username]["gpu_memory_mb"] += proc["memory_mb"]
        
        # 获取全局GPU数据（使用率和显存总量）
        global_gpu = self.collect_gpu()
        global_gpu_usage = global_gpu.get("utilization", 0)
        global_mem_used = global_gpu.get("memory_used_mb", 0)
        gpu_total_memory = global_gpu.get("memory_total_mb", 0)
        
        # 按用户聚合CPU/内存
        user_resources = defaultdict(lambda: {"cpu_percent": 0.0, "memory_percent": 0.0})
        
        for pid, username in pid_to_user.items():
            if username in users:
                info = pid_info.get(pid, {})
                user_resources[username]["cpu_percent"] += info.get("cpu_percent", 0)
                user_resources[username]["memory_percent"] += info.get("mem_percent", 0)
        
        # 构建用户资源映射
        result = {}
        for user in users:
            gpu_data = user_gpu.get(user, {"gpu_memory_mb": 0})
            resources = user_resources.get(user, {"cpu_percent": 0, "memory_percent": 0})
            user_mem = gpu_data["gpu_memory_mb"]
            
            # 按显存比例分配GPU使用率
            if global_mem_used > 0:
                gpu_percent = round(global_gpu_usage * user_mem / global_mem_used, 2)
            else:
                gpu_percent = 0
            
            result[user] = {
                "gpu_percent": min(gpu_percent, 100),  # 防止超过100%
                "gpu_memory_mb": user_mem,
                "gpu_memory_total_mb": gpu_total_memory,
                "cpu_percent": round(resources["cpu_percent"], 1),
                "memory_percent": round(resources["memory_percent"], 1)
            }
        
        # 如果没有用户，至少返回系统总体情况
        if not result:
            result["system"] = {
                "gpu_percent": global_gpu_usage,
                "gpu_memory_mb": global_mem_used,
                "gpu_memory_total_mb": gpu_total_memory,
                "cpu_percent": 0,
                "memory_percent": 0
            }
        
        return result
    
    def collect_process_gpu(self) -> List[Dict]:
        """采集每个计算进程的GPU使用情况
        
        通过 nvidia-smi --query-compute-apps 获取正在使用GPU的进程信息。
        
        Returns:
            List[Dict], 每个进程包含:
                - pid: int, 进程ID
                - memory_mb: int, 使用的显存 (MB)
                - gpu_percent: int, GPU使用率
        """
        result = []
        
        try:
            # 注意：--query-compute-apps 只支持 pid,used_memory 两个字段
            # utilization.gpu 字段对计算进程无效，会导致解析失败
            cmd = [
                "nvidia-smi",
                "--query-compute-apps=pid,used_memory",
                "--format=csv,noheader,nounits"
            ]
            output = subprocess.check_output(cmd, text=True, timeout=5)
            
            for line in output.strip().split("\n"):
                if line:
                    parts = [p.strip() for p in line.split(",")]
                    # 修复：nvidia-smi --query-compute-apps 只返回 2 个字段 (pid, used_memory)
                    if len(parts) >= 2:
                        result.append({
                            "pid": int(parts[0]),
                            "memory_mb": int(parts[1]),
                            "gpu_percent": 0  # 进程级GPU使用率暂不支持，设为0
                        })
        except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
            pass
        
        return result
    
    def get_process_info(self) -> Tuple[Dict[int, str], Dict[int, Dict]]:
        """获取进程详细信息
        
        通过 ps aux 获取所有进程的PID、用户名、CPU使用率和内存使用率。
        
        Returns:
            Tuple:
                - pid_to_user: Dict[pid, username]
                - pid_info: Dict[pid, {"cpu_percent": float, "mem_percent": float}]
        """
        pid_to_user = {}
        pid_info = {}
        
        try:
            output = subprocess.check_output(
                ["ps", "aux"],
                text=True,
                timeout=5
            )
            
            for line in output.strip().split("\n"):
                # 跳过表头行（第一行是 USER PID %CPU %MEM ...）
                if line.startswith("USER") or not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 11:  # ps aux 格式: USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND
                    username = parts[0]
                    pid = int(parts[1])
                    cpu_percent = float(parts[2])
                    mem_percent = float(parts[3])
                    
                    pid_to_user[pid] = username
                    pid_info[pid] = {"cpu_percent": cpu_percent, "mem_percent": mem_percent}
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        return pid_to_user, pid_info
    
    def _get_gpu_total_memory(self) -> int:
        """获取GPU总显存
        
        Returns:
            总显存 (MB)，获取失败返回 0
        """
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits"
            ]
            output = subprocess.check_output(cmd, text=True, timeout=5)
            return int(output.strip())
        except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
            return 0
    
    def collect_gpu(self) -> Dict:
        """采集GPU信息（系统级，作为备用）
        
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
