"""
日志管理器 - 基于 Python logging 模块
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict


class Logger:
    """日志管理器 - 单例模式"""
    
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def get_logger(cls, name: str, log_dir: str = 'logs', 
                   level: str = 'INFO', max_bytes: int = 10 * 1024 * 1024,
                   backup_count: int = 5) -> logging.Logger:
        """
        获取日志器（单例）
        
        Args:
            name: 日志器名称
            log_dir: 日志目录
            level: 日志级别
            max_bytes: 单个日志文件最大大小
            backup_count: 保留的备份文件数量
        
        Returns:
            logging.Logger 实例
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # 避免重复添加 handler
        if logger.handlers:
            return logger
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 日志文件名
        log_file = os.path.join(log_dir, f'EasyApp_{datetime.now().strftime("%Y%m%d")}.log')
        
        # 文件 Handler - 按大小滚动
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        
        # 控制台 Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # 统一格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # 缓存日志器
        cls._loggers[name] = logger
        
        return logger
