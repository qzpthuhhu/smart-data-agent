"""
UI模块
提供Web界面和日志配置
"""

from ui.logging_config import setup_logging, logger, RequestTimer, PerformanceMonitor

__all__ = ['setup_logging', 'logger', 'RequestTimer', 'PerformanceMonitor']
