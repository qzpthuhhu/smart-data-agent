"""
日志系统模块
提供统一的日志配置和管理功能
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional


class LoggerManager:
    """日志管理器"""
    
    _loggers = {}
    _log_dir = "logs"
    
    @classmethod
    def setup(cls, log_dir: str = "logs", log_level: str = "INFO"):
        """设置日志目录和级别"""
        cls._log_dir = log_dir
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # 设置根日志级别
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    @classmethod
    def get_logger(cls, name: str, log_file: Optional[str] = None) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件名
            
        Returns:
            日志记录器实例
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file is None:
            log_file = f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_path = Path(cls._log_dir) / log_file
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 错误日志单独记录
        error_file_path = Path(cls._log_dir) / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = RotatingFileHandler(
            error_file_path,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def close_all(cls):
        """关闭所有日志处理器"""
        for logger in cls._loggers.values():
            for handler in logger.handlers:
                handler.close()
                logger.removeHandler(handler)
        cls._loggers.clear()


def setup_logging(
    name: str = "smart_data_agent",
    log_dir: str = "logs",
    log_level: str = "INFO"
) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        name: 日志记录器名称
        log_dir: 日志目录
        log_level: 日志级别
        
    Returns:
        日志记录器
    """
    LoggerManager.setup(log_dir, log_level)
    return LoggerManager.get_logger(name)


# 全局日志实例
logger = setup_logging()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, name: str = "performance"):
        self.name = name
        self.logger = LoggerManager.get_logger(f"{name}_monitor")
        self.metrics = {}
    
    def record(self, metric_name: str, value: float, tags: dict = None):
        """记录指标"""
        timestamp = datetime.now().isoformat()
        key = f"{metric_name}_{int(time.time() * 1000)}"
        
        self.metrics[key] = {
            "name": metric_name,
            "value": value,
            "timestamp": timestamp,
            "tags": tags or {}
        }
        
        self.logger.debug(f"[METRIC] {metric_name}={value} {tags}")
    
    def get_metrics(self, metric_name: str = None) -> list:
        """获取指标"""
        if metric_name:
            return [m for m in self.metrics.values() if m["name"] == metric_name]
        return list(self.metrics.values())


import time


class RequestTimer:
    """请求计时器"""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.logger = LoggerManager.get_logger("request_timer")
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"[START] {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        if exc_type is None:
            self.logger.info(f"[END] {self.operation} - 耗时: {elapsed:.3f}秒")
        else:
            self.logger.error(f"[ERROR] {self.operation} - 耗时: {elapsed:.3f}秒 - 错误: {exc_val}")
        return False
