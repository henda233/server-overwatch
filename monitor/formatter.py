"""
结果格式化模块
负责将采集和查询的数据格式化为友好的文本输出
"""

from typing import Dict, List


class Formatter:
    """结果格式化器
    
    将数据格式化为适合QQ消息的文本格式。
    使用Unicode方框字符绘制表格。
    """
    
    def format_realtime(self, data: Dict[str, Dict]) -> str:
        """格式化实时数据
        
        Args:
            data: Dict[用户名, Dict[资源数据]]
            
        Returns:
            格式化的文本
        """
        if not data:
            return "📭 当前没有在线用户"
        
        lines = []
        lines.append("📊 当前服务器资源使用情况")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 表头
        header = "用户名   | GPU      | 显存              | CPU    | 内存"
        lines.append(header)
        lines.append("-" * len(header))
        
        # 数据行
        for username, stats in data.items():
            gpu = stats.get("gpu_percent", 0)
            gpu_mem = stats.get("gpu_memory_mb", 0)
            gpu_mem_total = stats.get("gpu_memory_total_mb", 0)
            cpu = stats.get("cpu_percent", 0)
            mem = stats.get("memory_percent", 0)
            
            # 格式化显存显示
            if gpu_mem_total > 0:
                mem_str = self._format_memory(gpu_mem, gpu_mem_total)
            else:
                mem_str = f"{gpu_mem}MB"
            
            line = f"{username[:7]:<7} | {gpu:>6.2f}% | {mem_str:<17} | {cpu:>6.1f}%  | {mem:>5.1f}%"
            lines.append(line)
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"在线用户: {len(data)}人")
        
        return "\n".join(lines)
    
    def format_history(self, records: List[Dict], time_range: str) -> str:
        """格式化历史数据
        
        Args:
            records: 记录列表
            time_range: 查询的时间范围
            
        Returns:
            格式化的文本
        """
        if not records:
            return f"📭 暂无 {time_range} 的历史记录"
        
        lines = []
        lines.append(f"📅 过去 {time_range} 的历史记录")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 表头
        header = "用户名   | 时间                | GPU   | 显存"
        lines.append(header)
        lines.append("-" * len(header))
        
        # 数据行（最多显示20条）
        for record in records[:20]:
            username = record.get("username", "unknown")[:7]
            timestamp = record.get("timestamp", "")[:16]  # 截取日期和时间
            gpu = record.get("gpu_percent", 0)
            gpu_mem_mb = record.get("gpu_memory_mb", 0)
            gpu_mem_gb = gpu_mem_mb / 1024 if gpu_mem_mb else 0
            
            line = f"{username:<7} | {timestamp:<18} | {gpu:>6.2f}% | {gpu_mem_gb:.2f}GB"
            lines.append(line)
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"共 {len(records)} 条记录")
        
        return "\n".join(lines)
    
    def format_user_detail(self, username: str, data: Dict) -> str:
        """格式化指定用户的详细信息
        
        Args:
            username: 用户名
            data: 用户资源数据
            
        Returns:
            格式化的文本
        """
        gpu = data.get("gpu_percent", 0)
        gpu_mem_mb = data.get("gpu_memory_mb", 0)
        gpu_mem_total = data.get("gpu_memory_total_mb", 0)
        cpu = data.get("cpu_percent", 0)
        mem = data.get("memory_percent", 0)
        
        lines = []
        lines.append(f"👤 {username} 当前状态")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"GPU使用率: {gpu:.2f}%")
        
        if gpu_mem_total > 0:
            gpu_mem_gb = gpu_mem_mb / 1024
            total_gb = gpu_mem_total / 1024
            lines.append(f"显存使用: {gpu_mem_gb:.2f}GB / {total_gb:.2f}GB")
        else:
            lines.append(f"显存使用: {gpu_mem_mb}MB")
        
        lines.append(f"CPU使用率: {cpu:.1f}%")
        lines.append(f"内存使用: {mem:.1f}%")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
    
    def format_help(self) -> str:
        """格式化帮助信息
        
        Returns:
            帮助文本
        """
        lines = []
        lines.append("🤖 Server Overwatch 使用指南")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append("📌 查询命令:")
        lines.append("  /info              - 查看所有在线用户资源")
        lines.append("  /info <用户>       - 查看指定用户资源")
        lines.append("  /info <number>d    - 查看最近N天历史 (如: /info 7d)")
        lines.append("  /info <number>w    - 查看最近N周历史 (如: /info 2w)")
        lines.append("  /info <number>m    - 查看最近N月历史 (如: /info 3m)")
        lines.append("  /help              - 显示本帮助")
        lines.append("")
        lines.append("💡 提示: 输入 @机器人 + 命令")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
    
    def format_error(self, message: str) -> str:
        """格式化错误信息
        
        Args:
            message: 错误消息
            
        Returns:
            格式化的错误文本
        """
        return f"❌ {message}"
    
    def _format_memory(self, used_mb: int, total_mb: int) -> str:
        """格式化显存显示
        
        Args:
            used_mb: 已用显存(MB)
            total_mb: 总显存(MB)
            
        Returns:
            格式化字符串，如 "20GB/98GB"
        """
        used_gb = used_mb / 1024 if used_mb else 0
        total_gb = total_mb / 1024 if total_mb else 0
        
        if total_gb > 0:
            return f"{used_gb:.2f}GB/{total_gb:.2f}GB"
        else:
            return f"{used_mb}MB"
