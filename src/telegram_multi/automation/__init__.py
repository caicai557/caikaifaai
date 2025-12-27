"""Telegram automation module."""

from .delay_manager import DelayConfig, DelayManager

# TODO: Import keyword_monitor when implemented
# from .keyword_monitor import KeywordRule, KeywordMonitor

__all__ = ["DelayConfig", "DelayManager"]
