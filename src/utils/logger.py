"""
日志工具模块

提供统一的日志配置，支持：
- 控制台输出（彩色）
- 文件输出
- 日志级别配置
- 格式自定义

使用方法：
    from src.utils.logger import setup_logger
    setup_logger("INFO")
    logger = logging.getLogger(__name__)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(level: str = "INFO", log_file: str = None) -> None:
    """
    配置全局日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选，默认不写文件）
    """
    # 日志级别映射
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = level_map.get(level.upper(), logging.INFO)

    # 创建根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除已有的处理器（避免重复）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 日志格式
    # 格式说明：
    # %(asctime)s - 时间
    # %(name)s - logger名称
    # %(levelname)s - 日志级别
    # %(message)s - 日志内容
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台处理器（彩色输出）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（可选）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 设置第三方库的日志级别，减少噪音
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的logger

    Args:
        name: logger名称，通常使用 __name__

    Returns:
        配置好的logger实例
    """
    return logging.getLogger(name)
