"""
Server Overwatch - GPU服务器用户监控程序

通过QQ机器人接收用户命令，查询远程GPU服务器上的用户登录情况
和资源使用情况（CPU、GPU、内存、显存）。

程序运行在GPU服务器上（Server Only架构），无需SSH功能。
"""

import asyncio
import logging
import os
import threading
import time
from datetime import datetime

import botpy
from botpy import Client
from botpy.message import C2CMessage, DirectMessage, Message
from botpy.ext.cog_yaml import read

from bot.handler import CommandHandler
from monitor.collector import Collector
from monitor.recorder import Recorder
from monitor.formatter import Formatter
from utils.config import Config


# 全局日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BotClient(Client):
    """QQ机器人客户端"""
    
    def __init__(self, config: Config, handler: CommandHandler):
        """初始化机器人客户端
        
        Args:
            config: 配置管理器
            handler: 命令处理器
        """
        self.config = config
        self.handler = handler
        
        # 创建 intents 对象：支持频道@消息 + 私聊
        intents = botpy.Intents(
            public_guild_messages=True,  # 频道@消息
            public_messages=True,         # C2C 私聊
            direct_message=True           # DMS 私信
        )
        
        super().__init__(intents=intents)
    
    async def on_c2c_message_create(self, message: C2CMessage):
        """处理C2C私聊消息"""
        try:
            logger.info(f"收到C2C私聊: {message.content}")
            reply = await self.handler.handle(message.content)
            await message._api.post_c2c_message(
                openid=message.author.user_openid,
                msg_type=0,
                msg_id=message.id,
                content=reply
            )
            logger.info(f"发送C2C回复: {reply[:100]}...")
        except Exception as e:
            logger.error(f"处理C2C消息失败: {e}")
    
    async def on_direct_message_create(self, message: DirectMessage):
        """处理DMS私信"""
        try:
            logger.info(f"收到DMS私信: {message.content}")
            reply = await self.handler.handle(message.content)
            await self.api.post_dms(
                guild_id=message.guild_id,
                content=reply,
                msg_id=message.id
            )
            logger.info(f"发送DMS回复: {reply[:100]}...")
        except Exception as e:
            logger.error(f"处理DMS消息失败: {e}")
    
    async def on_at_message_create(self, message):
        """处理@消息
        
        Args:
            message: 接收到的消息对象
        """
        try:
            logger.info(f"收到消息: {message.content}")
            
            # 处理命令
            reply = await self.handler.handle(message.content)
            
            # 回复消息
            await message.reply(content=reply)
            logger.info(f"发送回复: {reply[:100]}...")
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            await message.reply(content=f"❌ 处理失败: {str(e)}")
    
    async def on_ready(self):
        """机器人就绪回调"""
        logger.info(f"机器人已就绪: {self.robot.name}")


class PeriodicCollector:
    """定时数据采集器"""
    
    def __init__(
        self,
        recorder: Recorder,
        collector: Collector,
        interval: int,
        retention_days: int = 30,
        cleanup_interval: int = 86400  # 默认每天清理一次
    ):
        """初始化定时采集器
        
        Args:
            recorder: 历史记录管理器
            collector: 数据采集器
            interval: 采集间隔（秒）
            retention_days: 数据保留天数，默认30天
            cleanup_interval: 清理间隔（秒），默认86400秒（1天）
        """
        self.recorder = recorder
        self.collector = collector
        self.interval = interval
        self.retention_days = retention_days
        self.cleanup_interval = cleanup_interval
        self._running = False
        self._thread = None
        self._last_cleanup = 0
    
    def start(self):
        """启动定时采集"""
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"定时采集已启动，间隔: {self.interval}秒")
        logger.info(f"数据保留期限: {self.retention_days}天")
    
    def stop(self):
        """停止定时采集"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("定时采集已停止")
    
    def _cleanup_old_records(self):
        """清理过期数据"""
        try:
            deleted = self.recorder.cleanup(self.retention_days)
            if deleted > 0:
                logger.info(f"清理过期记录: {deleted} 条")
            stats = self.recorder.get_stats()
            logger.info(f"当前数据库记录数: {stats['total_records']}")
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
    
    def _run(self):
        """采集循环"""
        elapsed = 0
        while self._running:
            try:
                # 采集当前数据
                data = self.collector.collect()
                
                # 保存到数据库
                timestamp = datetime.now()
                for username, user_data in data.items():
                    self.recorder.save(timestamp, username, user_data)
                
                logger.info(f"采集完成: {len(data)} 个用户/系统记录")
                
                # 检查是否需要清理
                elapsed += self.interval
                if elapsed >= self.cleanup_interval:
                    self._cleanup_old_records()
                    elapsed = 0
                
            except Exception as e:
                logger.error(f"采集失败: {e}")
            
            # 等待下次采集
            time.sleep(self.interval)


def main():
    """主入口函数"""
    logger.info("=" * 50)
    logger.info("Server Overwatch 启动中...")
    logger.info("=" * 50)
    
    # 加载配置
    config = Config()
    try:
        config.load("config.yaml")
        logger.info("配置文件加载成功")
    except FileNotFoundError as e:
        logger.error(f"配置文件未找到: {e}")
        return
    
    # 确保日志目录存在
    log_dir = os.path.dirname(config.log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # 初始化模块
    collector = Collector()
    recorder = Recorder()
    formatter = Formatter()
    handler = CommandHandler(collector, recorder, formatter)
    
    # 启动定时采集
    periodic = PeriodicCollector(
        recorder,
        collector,
        config.interval,
        retention_days=config.retention_days
    )
    periodic.start()
    
    # 启动机器人
    client = BotClient(config, handler)
    
    try:
        logger.info(f"机器人连接中...")
        client.run(
            appid=config.appid,
            secret=config.secret
        )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    finally:
        periodic.stop()
        logger.info("程序已退出")


if __name__ == "__main__":
    main()
