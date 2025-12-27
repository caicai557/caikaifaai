"""
Delay manager for Telegram automation.

Contract:
- DelayConfig validates delay range (rejects negative, min > max)
- DelayManager executes random delays within configured range
- Supports disabling delays via enabled flag
- Async execution does not block event loop
"""

import asyncio
import random
from pydantic import BaseModel, field_validator


class DelayConfig(BaseModel):
    """Configuration for delay behavior."""

    enabled: bool = True
    min_delay: float = 2.0
    max_delay: float = 5.0
    show_typing: bool = False

    @field_validator("min_delay", "max_delay")
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        """Validate that delays are non-negative."""
        if v < 0:
            raise ValueError("Delay must be non-negative")
        return v

    @field_validator("max_delay")
    @classmethod
    def validate_max_greater_than_min(cls, v: float, info) -> float:
        """Validate that max_delay >= min_delay."""
        if "min_delay" in info.data and v < info.data["min_delay"]:
            raise ValueError("max_delay must be >= min_delay")
        return v


class DelayManager:
    """Manages random delays for automation tasks."""

    def __init__(self, config: DelayConfig):
        """Initialize delay manager with configuration.

        Args:
            config: DelayConfig instance with delay settings
        """
        self.config = config

    async def delay(self) -> None:
        """Execute a random delay within configured range.

        Returns immediately if:
        - enabled=False
        - min_delay=max_delay=0

        Otherwise, sleeps for random duration in [min_delay, max_delay].
        """
        if not self.config.enabled:
            return

        if self.config.min_delay == 0 and self.config.max_delay == 0:
            return

        wait_time = random.uniform(self.config.min_delay, self.config.max_delay)
        await asyncio.sleep(wait_time)
