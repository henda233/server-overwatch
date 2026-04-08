"""
结果格式化模块
负责将采集和查询的数据格式化为友好的文本输出
"""

from typing import Dict, List, Optional


class Formatter:
    """结果格式化器
    
    将数据格式化为适合QQ消息的文本格式。
    使用Unicode方框字符绘制表格。
    """
    
    def format_realtime(self, data: Dict[str, Dict]) -> str:
        """格式化实时数据（统一单行文字格式）
        
        Args:
            data: Dict[用户名, Dict[资源数据]]
            
        Returns:
            格式化的文本
        """
        if not data:
            return "📭 当前没有在线用户"
        
        lines = []
        lines.append(f"当前服务器资源使用情况（在线{len(data)}人）")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        
        for username, stats in data.items():
            gpu = stats.get("gpu_percent", 0)
            gpu_mem = stats.get("gpu_memory_mb", 0)
            gpu_mem_total = stats.get("gpu_memory_total_mb", 0)
            cpu = stats.get("cpu_percent", 0)
            mem = stats.get("memory_percent", 0)
            
            # 显存格式化
            gpu_mem_gb = gpu_mem / 1024 if gpu_mem else 0
            total_gb = gpu_mem_total / 1024 if gpu_mem_total else 0
            if total_gb > 0:
                mem_str = f"{gpu_mem_gb:.1f}GB/{total_gb:.0f}GB"
            else:
                mem_str = f"{gpu_mem:.0f}MB"
            
            # 单行格式（不依赖等宽字体）
            line = f"{username[:6]:<6}  GPU: {gpu:>5.1f}%  显存: {mem_str:<12}  CPU: {cpu:>5.1f}%  内存: {mem:>5.1f}%"
            lines.append(line)
        
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("提示: /info <用户> 查看指定用户详情")
        
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
    
    def format_history_compact(self, records: List[Dict], stats: Dict, 
                               time_range: str, username: Optional[str] = None,
                               page: int = 1, page_size: int = 10) -> str:
        """格式化精简版历史数据（支持分页导航）
        
        Args:
            records: 过滤后的记录列表
            stats: 统计信息（total, valid, filtered, cpu_peak, mem_peak, gpu_peak, total_pages, current_page）
            time_range: 查询的时间范围
            username: 指定用户时显示用户名前缀，None时显示多用户模式
            page: 当前页码
            page_size: 每页条数
        """
        if not records:
            return f"📭 暂无 {time_range} 的历史记录"
        
        lines = []
        
        # 获取分页信息
        total_pages = stats.get('total_pages', 1)
        current_page = stats.get('current_page', page)
        
        # 页码导航头
        if total_pages > 1:
            lines.append(f"📄 第{current_page}页/共{total_pages}页")
            if current_page < total_pages:
                # 构建下一页命令提示
                if username:
                    cmd_hint = f"/info {username} {time_range} {current_page + 1}"
                else:
                    cmd_hint = f"/info {time_range} {current_page + 1}"
                lines.append(f"还有{total_pages - current_page}页数据，输入 {cmd_hint} 查看下一页")
            else:
                lines.append("（最后一页）")
            lines.append("")
        
        # 标题行
        if username:
            lines.append(f"{username} 过去 {time_range} 的历史记录（精简版）")
        else:
            lines.append(f"过去 {time_range} 的历史记录（精简版）")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 统计行
        lines.append(f"统计: {stats['valid']}条 / {stats['total']}条总（已过滤{stats['filtered']}条空闲）")
        lines.append(f"GPU峰值: {stats.get('gpu_peak', 0):.1f}%  |  CPU峰值: {stats['cpu_peak']:.1f}%  |  内存峰值: {stats['mem_peak']:.1f}%")
        lines.append("")
        
        # 数据行（使用 page_size 限制）
        for record in records[:page_size]:
            timestamp = record.get("timestamp", "")[5:16]  # MM-DD HH:MM
            gpu = record.get("gpu_percent", 0)
            gpu_mem_gb = record.get("gpu_memory_mb", 0) / 1024 if record.get("gpu_memory_mb") else 0
            
            if username:
                # 单用户模式：无需显示用户名
                line = f"{timestamp}  GPU: {gpu:>5.1f}%  显存: {gpu_mem_gb:.1f}GB  CPU: {record.get('cpu_percent', 0):>5.1f}%  内存: {record.get('memory_percent', 0):>5.1f}%"
            else:
                # 多用户模式：显示用户名
                user = record.get("username", "")[:6]
                line = f"{timestamp}  {user:<6}  GPU: {gpu:>5.1f}%  显存: {gpu_mem_gb:.1f}GB"
            
            lines.append(line)
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 操作提示
        if username:
            lines.append(f"提示: /info {username} 查看该用户当前状态")
        else:
            lines.append("提示: /info <用户> <时间> 查看指定用户的详细记录")
        
        return "\n".join(lines)
    
    def format_user_detail(self, username: str, data: Dict) -> str:
        """格式化指定用户的详细信息（统一单行文字格式）
        
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
        
        # 显存格式化
        gpu_mem_gb = gpu_mem_mb / 1024 if gpu_mem_mb else 0
        total_gb = gpu_mem_total / 1024 if gpu_mem_total else 0
        if total_gb > 0:
            mem_str = f"{gpu_mem_gb:.1f}GB/{total_gb:.0f}GB"
        else:
            mem_str = f"{gpu_mem_mb:.0f}MB"
        
        lines = []
        lines.append(f"👤 {username} 当前状态")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append(f"GPU: {gpu:>5.1f}%  显存: {mem_str:<12}  CPU: {cpu:>5.1f}%  内存: {mem:>5.1f}%")
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"提示: /info {username} 3d 查看该用户历史记录")
        
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
        lines.append("📌 实时查询:")
        lines.append("  /info              - 查看所有在线用户资源")
        lines.append("  /info <用户>       - 查看指定用户资源详情")
        lines.append("")
        lines.append("📌 历史查询（精简模式）:")
        lines.append("  /info <number>d    - 查看最近N天历史 (如: /info 7d)")
        lines.append("  /info <number>w    - 查看最近N周历史 (如: /info 2w)")
        lines.append("  /info <number>m    - 查看最近N月历史 (如: /info 3m)")
        lines.append("  /info <用户> <时间> - 查看指定用户的历史 (如: /info cxy 7d)")
        lines.append("  /info <时间> <页码> - 历史查询翻页 (如: /info 7d 2)")
        lines.append("")
        lines.append("📌 统计查询:")
        lines.append("  /stats <时间>      - 查看资源使用统计 (如: /stats 3d)")
        lines.append("  /top               - 查看资源使用排行")
        lines.append("  /top gpu/mem/cpu  - 按GPU/显存/CPU排序")
        lines.append("  /users [天数]      - 查看服务器用户列表")
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
    
    def format_stats(self, stats: Dict[str, Dict], time_range: str) -> str:
        """格式化统计摘要
        
        Args:
            stats: Dict[用户名, 统计信息]
            time_range: 查询的时间范围
            
        Returns:
            格式化的统计文本
        """
        if not stats:
            return f"📭 暂无 {time_range} 的统计数据"
        
        lines = []
        lines.append(f"📊 过去 {time_range} 的资源使用统计")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        
        # 按GPU峰值排序
        sorted_users = sorted(stats.items(), key=lambda x: x[1]["gpu_peak"], reverse=True)
        
        for username, user_stats in sorted_users:
            gpu_peak = user_stats.get("gpu_peak", 0)
            gpu_avg = user_stats.get("gpu_avg", 0)
            mem_peak = user_stats.get("mem_peak_gb", 0)
            mem_avg = user_stats.get("mem_avg_gb", 0)
            hours = user_stats.get("active_hours", 0)
            
            lines.append(f"👤 {username}")
            lines.append(f"   GPU峰值: {gpu_peak:.1f}% | 平均: {gpu_avg:.1f}%")
            lines.append(f"   显存峰值: {mem_peak:.1f}GB | 平均: {mem_avg:.1f}GB")
            lines.append(f"   活跃时段: 累计{hours}小时")
            lines.append("")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
    
    def format_top(self, data: Dict[str, Dict], sort_by: str = "gpu") -> str:
        """格式化排行榜
        
        Args:
            data: Dict[用户名, 资源数据]
            sort_by: 排序字段 "gpu", "mem", "cpu"
            
        Returns:
            格式化的排行榜文本
        """
        if not data:
            return "📭 当前没有在线用户"
        
        # 排序名称映射
        sort_names = {"gpu": "GPU 使用率", "mem": "显存使用量", "cpu": "CPU 使用率"}
        sort_name = sort_names.get(sort_by, "GPU 使用率")
        
        lines = []
        lines.append(f"🏆 当前资源使用排行榜")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"按 {sort_name} 排序:")
        lines.append("")
        
        # 奖牌emoji
        medals = ["🥇", "🥈", "🥉"]
        
        # 获取排序键
        if sort_by == "mem":
            sort_key = lambda x: x[1].get("gpu_memory_mb", 0)
        else:
            sort_key = lambda x: x[1].get(f"{sort_by}_percent", 0)
        
        sorted_users = sorted(data.items(), key=sort_key, reverse=True)
        
        for i, (username, stats) in enumerate(sorted_users[:10]):
            medal = medals[i] if i < 3 else f"{i+1}."
            gpu = stats.get("gpu_percent", 0)
            gpu_mem = stats.get("gpu_memory_mb", 0)
            gpu_mem_gb = gpu_mem / 1024 if gpu_mem else 0
            cpu = stats.get("cpu_percent", 0)
            
            # 根据排序字段调整显示
            if sort_by == "gpu":
                line = f"{medal} {username:<8} GPU: {gpu:>5.1f}%  显存: {gpu_mem_gb:>5.1f}GB  CPU: {cpu:>5.1f}%"
            elif sort_by == "mem":
                line = f"{medal} {username:<8} 显存: {gpu_mem_gb:>5.1f}GB  GPU: {gpu:>5.1f}%  CPU: {cpu:>5.1f}%"
            else:
                line = f"{medal} {username:<8} CPU: {cpu:>5.1f}%  GPU: {gpu:>5.1f}%  显存: {gpu_mem_gb:>5.1f}GB"
            
            lines.append(line)
        
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"在线用户: {len(data)}人")
        
        return "\n".join(lines)
    
    def format_users(self, users: List[Dict], time_range: str = "30") -> str:
        """格式化用户列表
        
        Args:
            users: 用户列表
            time_range: 查询的时间范围字符串
            
        Returns:
            格式化的用户列表文本
        """
        if not users:
            return f"📭 近 {time_range} 天内暂无用户记录"
        
        lines = []
        lines.append("👥 服务器用户统计")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"📌 共 {len(users)} 个用户（近{time_range}天）")
        lines.append("")
        
        # 表头
        lines.append("用户名      | 最后活跃      | 总记录数  | 峰值GPU")
        lines.append("-" * 45)
        
        # 数据行（限制20个用户）
        for user in users[:20]:
            username = user.get("username", "")[:8]
            last_active = user.get("last_active", "无")[:12]
            total = user.get("total_records", 0)
            gpu_peak = user.get("gpu_peak", 0)
            
            line = f"{username:<10}| {last_active:<14}| {total:>6}    | {gpu_peak:>5.1f}%"
            lines.append(line)
        
        # 截断提示
        if len(users) > 20:
            lines.append(f"... 还有 {len(users) - 20} 个用户")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
