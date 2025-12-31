"""
Council Protocol Module

Structured schemas for token-efficient agent communication.
Implements 2025 Best Practice: Protocol-First Communication.
"""

from council.protocol.schema import (
    VoteEnum,
    RiskCategory,
    MinimalVote,
    MinimalThinkResult,
)

__all__ = [
    "VoteEnum",
    "RiskCategory",
    "MinimalVote",
    "MinimalThinkResult",
]
