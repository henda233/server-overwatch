"""
QQ机器人命令处理模块
负责接收消息、解析命令、返回结果
"""

from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass
import re
import time

from utils.logger import setup_logger

if TYPE_CHECKING:
    from monitor.collector import Collector
    from monitor.recorder import Recorder
    from monitor.formatter import Formatter


@dataclass
class Command:
    """命令数据结构（扩展版）"""
    action: str           # "info", "help", "stats", "top", "users"
    target: Optional[str] = None  # 用户名 或 None
    time_range: Optional[str] = None  # "1d", "1w", "1m", None
    sort_by: Optional[str] = None  # "gpu", "mem", "cpu", None (用于top命令)


class CommandHandler:
    """命令处理器
    
    负责解析用户命令并返回相应的结果。
    支持的命令：
        /info - 查询所有在线用户资源
        /info <用户名> - 查询指定用户资源
        /info <数字>d/w/m - 查询历史记录
        /help - 显示帮助信息
    """
    
    def __init__(
        self,
        collector: "Collector",
        recorder: "Recorder",
        formatter: "Formatter"
    ):
        """初始化命令处理器
        
        Args:
            collector: 数据采集器
            recorder: 历史记录管理器
            formatter: 格式化器
        """
        self.collector = collector
        self.recorder = recorder
        self.formatter = formatter
        # 命令日志记录器
        self.command_logger = setup_logger("command", log_dir="logs")
    
    def parse(self, text: str) -> Command:
        """解析命令文本
        
        Args:
            text: 命令文本，如 "/info user1 3d" 或 "/info 7d"
            
        Returns:
            Command对象
        """
        text = text.strip()
        
        # 解析 /help 命令
        if text == "/help" or text == "help":
            return Command(action="help")
        
        # 解析 /info 命令
        if text.startswith("/info"):
            rest = text[5:].strip()
            
            if not rest:
                # /info - 查询所有用户（实时）
                return Command(action="info")
            
            # 时间范围模式 (数字 + d/w/m)
            time_pattern = r"^(\d+)([dDwWmM])$"
            time_match = re.match(time_pattern, rest)
            if time_match:
                num, unit = time_match.groups()
                return Command(action="info", time_range=f"{num}{unit.lower()}")
            
            # 组合命令模式: /info <用户名> <时间范围>
            # 匹配 "用户名 + 空格 + 时间" 的格式
            combo_pattern = r"^(\S+)\s+(\d+)([dDwWmM])$"
            combo_match = re.match(combo_pattern, rest)
            if combo_match:
                username, num, unit = combo_match.groups()
                return Command(action="info", target=username, time_range=f"{num}{unit.lower()}")
            
            # 否则当作用户名（实时查询）
            return Command(action="info", target=rest)
        
        # 解析 /stats 命令
        if text.startswith("/stats"):
            rest = text[6:].strip()
            if not rest:
                # /stats 默认7天
                return Command(action="stats", time_range="7d")
            # 匹配时间范围
            time_pattern = r"^(\d+)([dDwWmM])$"
            time_match = re.match(time_pattern, rest)
            if time_match:
                num, unit = time_match.groups()
                return Command(action="stats", time_range=f"{num}{unit.lower()}")
            return Command(action="help")
        
        # 解析 /top 命令
        if text.startswith("/top"):
            rest = text[4:].strip()
            if not rest:
                # /top 默认按GPU排序
                return Command(action="top", sort_by="gpu")
            # 匹配排序参数
            sort_options = ["gpu", "mem", "cpu"]
            if rest.lower() in sort_options:
                return Command(action="top", sort_by=rest.lower())
            return Command(action="help")
        
        # 解析 /users 命令
        if text.startswith("/users"):
            rest = text[6:].strip()
            if not rest:
                # /users 默认30天
                return Command(action="users", time_range="30")
            # 匹配时间范围（只匹配数字，自动按天计算）
            time_pattern = r"^(\d+)([dDwWmM])?$"
            time_match = re.match(time_pattern, rest)
            if time_match:
                num = time_match.group(1)
                unit = time_match.group(2)
                if unit and unit.lower() in ['w', 'm']:
                    # 周/月按天计算
                    if unit.lower() == 'w':
                        days = int(num) * 7
                    else:
                        days = int(num) * 30
                else:
                    days = int(num)
                return Command(action="users", time_range=str(days))
            return Command(action="help")
        
        # 默认返回帮助
        return Command(action="help")
    
    async def handle(self, message_text: str, user_id: str = "unknown") -> str:
        """处理消息
        
        Args:
            message_text: 消息文本
            user_id: 用户标识（用于日志记录）
            
        Returns:
            回复内容
        """
        start_time = time.time()
        command = self.parse(message_text)
        
        try:
            if command.action == "help":
                return self.formatter.format_help()
            
            if command.action == "info":
                # 组合命令: /info <用户名> <时间范围>
                if command.target and command.time_range:
                    # 检查 recorder 是否有 query_filtered 方法
                    if hasattr(self.recorder, 'query_filtered'):
                        records, stats = self.recorder.query_filtered(
                            command.time_range, command.target
                        )
                        return self.formatter.format_history_compact(
                            records, stats, command.time_range, command.target
                        )
                    else:
                        return "❌ 服务器暂不支持历史查询"
                
                # 仅时间范围: /info 3d
                if command.time_range:
                    if hasattr(self.recorder, 'query_filtered'):
                        records, stats = self.recorder.query_filtered(command.time_range)
                        return self.formatter.format_history_compact(
                            records, stats, command.time_range
                        )
                    else:
                        records = self.recorder.query(command.time_range)
                        return self.formatter.format_history(records, command.time_range)
                
                # 实时查询: /info 或 /info <用户名>
                if command.target:
                    data = self.collector.collect()
                    user_data = data.get(command.target)
                    if user_data is None:
                        return "❌ 用户不存在或未在线"
                    return self.formatter.format_realtime({command.target: user_data})
                else:
                    data = self.collector.collect()
                    return self.formatter.format_realtime(data)
            
            # /stats 命令 - 统计摘要
            if command.action == "stats":
                if hasattr(self.recorder, 'get_all_users_stats'):
                    stats = self.recorder.get_all_users_stats(command.time_range)
                    return self.formatter.format_stats(stats, command.time_range)
                else:
                    return "❌ 服务器暂不支持统计查询"
            
            # /top 命令 - 排行榜
            if command.action == "top":
                # 先获取实时数据排序
                data = self.collector.collect()
                if not data:
                    return "📭 当前没有在线用户"
                # 按指定字段排序
                sorted_users = sorted(
                    data.items(),
                    key=lambda x: x[1].get(f"{command.sort_by}_percent" if command.sort_by != 'mem' else 'gpu_memory_mb', 0),
                    reverse=True
                )
                sorted_data = {k: v for k, v in sorted_users}
                return self.formatter.format_top(sorted_data, command.sort_by)
            
            # /users 命令 - 用户列表
            if command.action == "users":
                if hasattr(self.recorder, 'get_all_users'):
                    users = self.recorder.get_all_users(int(command.time_range))
                    return self.formatter.format_users(users, command.time_range)
                else:
                    return "❌ 服务器暂不支持用户查询"
            
            return "❌ 未知命令，请使用 /help 查看帮助"
            
        except Exception as e:
            # 错误时记录异常堆栈
            self.command_logger.error(
                f"命令失败 | 用户: {user_id} | 命令: {message_text} | 错误: {e}",
                exc_info=True
            )
            raise
        finally:
            # 记录命令执行日志
            elapsed = (time.time() - start_time) * 1000
            self.command_logger.info(
                f"命令调用 | 用户: {user_id} | 命令: {message_text} | 耗时: {elapsed:.0f}ms"
            )
