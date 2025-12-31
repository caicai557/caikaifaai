"""
Council Structured Logger - 结构化日志记录器

2025 Best Practice:
- JSON logs for machine consumption (Splunk, Datadog)
- Rich console logs for human consumption
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from rich.console import Console
    from rich.logging import RichHandler
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class JsonFormatter(logging.Formatter):
    """JSON 格式化器"""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)

def get_logger(name: str = "council", json_output: bool = False) -> logging.Logger:
    """
    获取配置好的 Logger
    
    Args:
        name: Logger 名称
        json_output: 是否强制 JSON 输出 (用于生产环境)
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 防止重复添加 Handler
    if logger.handlers:
        return logger
        
    if json_output:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    elif HAS_RICH:
        # 使用 Rich 进行漂亮的控制台输出
        handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_path=False
        )
        logger.addHandler(handler)
    else:
        # 标准输出
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# 全局 Logger 实例
logger = get_logger()
