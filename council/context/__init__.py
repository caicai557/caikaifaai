"""
Council Context Module

Token-efficient context management for Multi-Agent Systems.
"""

from council.context.rolling_context import RollingContext, RoundEntry
from council.context.context_manager import ContextManager, ContextLayer, ContextEntry

__all__ = [
    # Rolling Context
    "RollingContext",
    "RoundEntry",
    # Context Manager (2025 Best Practice)
    "ContextManager",
    "ContextLayer",
    "ContextEntry",
]
