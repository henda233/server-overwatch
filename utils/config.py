"""
配置管理模块
提供YAML配置文件加载功能
"""

import os
from typing import Any, Optional

import yaml


class Config:
    """配置管理器
    
    负责加载和访问config.yaml中的配置项。
    支持点号分隔的路径访问，如 "qq_bot.appid"
    """
    
    def __init__(self):
        self._config: dict = {}
    
    def load(self, path: str = "config.yaml") -> None:
        """加载配置文件
        
        Args:
            path: 配置文件路径，默认为 "config.yaml"
        """
        config_path = os.path.join(os.path.dirname(__file__), "..", path)
        config_path = os.path.abspath(config_path)
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键，支持点号分隔路径，如 "qq_bot.appid"
            default: 默认值，当键不存在时返回
            
        Returns:
            配置值或默认值
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    @property
    def appid(self) -> str:
        """获取机器人AppID"""
        return self.get("qq_bot.appid", "")
    
    @property
    def secret(self) -> str:
        """获取机器人密钥"""
        return self.get("qq_bot.secret", "")
    
    @property
    def interval(self) -> int:
        """获取采集间隔（秒）"""
        return self.get("monitor.interval", 600)
    
    @property
    def retention_days(self) -> int:
        """获取数据保留天数"""
        return self.get("monitor.retention_days", 30)
    
    @property
    def log_level(self) -> str:
        """获取日志级别"""
        return self.get("logging.level", "INFO")
    
    @property
    def log_file(self) -> str:
        """获取日志文件路径"""
        return self.get("logging.file", "logs/bot.log")
    
    @property
    def page_size(self) -> int:
        """获取每页默认条数"""
        return self.get("pagination.page_size", 10)
