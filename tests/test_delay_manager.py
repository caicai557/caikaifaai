"""
Tests for DelayManager (Phase 7.1.3).

Contract:
- DelayConfig supports min_delay, max_delay, enabled, show_typing
- DelayManager executes random delays within configured range
- DelayManager respects enabled flag (no delay when disabled)
- Async execution does not block event loop
"""

import asyncio
import time
import pytest
from pydantic import ValidationError
from src.telegram_multi.automation.delay_manager import DelayConfig, DelayManager


class TestDelayConfig:
    """Contract tests for DelayConfig."""

    def test_delay_config_defaults(self):
        """Contract: DelayConfig has sensible defaults."""
        config = DelayConfig()
        assert config.enabled is True
        assert config.min_delay == 2.0
        assert config.max_delay == 5.0
        assert config.show_typing is False

    def test_delay_config_custom_range(self):
        """AC2.1: Support custom delay range."""
        config = DelayConfig(min_delay=1.0, max_delay=3.0)
        assert config.min_delay == 1.0
        assert config.max_delay == 3.0

    def test_delay_config_zero_delay(self):
        """AC2.3: Support zero delay (disabled)."""
        config = DelayConfig(min_delay=0.0, max_delay=0.0)
        assert config.min_delay == 0.0
        assert config.max_delay == 0.0

    def test_delay_config_disabled(self):
        """AC2.3: Support disabling delay via enabled flag."""
        config = DelayConfig(enabled=False)
        assert config.enabled is False

    def test_delay_config_show_typing_enabled(self):
        """AC2.4: Support show_typing configuration."""
        config = DelayConfig(show_typing=True)
        assert config.show_typing is True

    def test_delay_config_min_equals_max(self):
        """Contract: Allow min_delay == max_delay (fixed delay)."""
        config = DelayConfig(min_delay=3.0, max_delay=3.0)
        assert config.min_delay == 3.0
        assert config.max_delay == 3.0

    def test_delay_config_negative_delay_rejected(self):
        """Contract: Reject negative delays."""
        with pytest.raises(ValidationError):
            DelayConfig(min_delay=-1.0, max_delay=5.0)

    def test_delay_config_min_greater_than_max_rejected(self):
        """Contract: Reject min_delay > max_delay."""
        with pytest.raises(ValidationError):
            DelayConfig(min_delay=5.0, max_delay=2.0)


class TestDelayManager:
    """Contract tests for DelayManager."""

    @pytest.mark.asyncio
    async def test_delay_manager_initialization(self):
        """Contract: DelayManager accepts DelayConfig."""
        config = DelayConfig(min_delay=1.0, max_delay=2.0)
        manager = DelayManager(config)
        assert manager.config == config

    @pytest.mark.asyncio
    async def test_delay_executes_within_range(self):
        """AC2.2: Delay time is within configured range."""
        config = DelayConfig(min_delay=0.1, max_delay=0.3)
        manager = DelayManager(config)

        start = time.time()
        await manager.delay()
        elapsed = time.time() - start

        assert config.min_delay <= elapsed <= config.max_delay + 0.05  # 50ms tolerance

    @pytest.mark.asyncio
    async def test_delay_is_random(self):
        """AC2.2: Multiple delays produce different wait times."""
        config = DelayConfig(min_delay=0.1, max_delay=0.5)
        manager = DelayManager(config)

        delays = []
        for _ in range(5):
            start = time.time()
            await manager.delay()
            delays.append(time.time() - start)

        # At least 2 different delay values (with 100ms precision)
        unique_delays = len(set(round(d, 1) for d in delays))
        assert unique_delays >= 2, "Delays should vary (randomness check)"

    @pytest.mark.asyncio
    async def test_delay_disabled_returns_immediately(self):
        """AC2.3: No delay when enabled=False."""
        config = DelayConfig(enabled=False, min_delay=1.0, max_delay=2.0)
        manager = DelayManager(config)

        start = time.time()
        await manager.delay()
        elapsed = time.time() - start

        assert elapsed < 0.1, "Should return immediately when disabled"

    @pytest.mark.asyncio
    async def test_delay_zero_range_returns_immediately(self):
        """AC2.3: No delay when min=max=0."""
        config = DelayConfig(min_delay=0.0, max_delay=0.0)
        manager = DelayManager(config)

        start = time.time()
        await manager.delay()
        elapsed = time.time() - start

        assert elapsed < 0.1, "Should return immediately with zero delay"

    @pytest.mark.asyncio
    async def test_delay_fixed_time_when_min_equals_max(self):
        """Contract: Fixed delay when min_delay == max_delay."""
        config = DelayConfig(min_delay=0.2, max_delay=0.2)
        manager = DelayManager(config)

        start = time.time()
        await manager.delay()
        elapsed = time.time() - start

        assert 0.15 <= elapsed <= 0.25, "Should execute fixed delay"

    @pytest.mark.asyncio
    async def test_delay_does_not_block_event_loop(self):
        """Contract: Async execution allows concurrent operations."""
        config = DelayConfig(min_delay=0.2, max_delay=0.3)
        manager = DelayManager(config)

        # Start two delays concurrently
        start = time.time()
        await asyncio.gather(manager.delay(), manager.delay())
        elapsed = time.time() - start

        # Both should run in parallel, not sequential
        # If sequential: ~0.4-0.6s, if parallel: ~0.2-0.3s
        assert elapsed < 0.4, "Should execute delays concurrently"

    @pytest.mark.asyncio
    async def test_multiple_delay_calls_independent(self):
        """Contract: Multiple DelayManager instances work independently."""
        config1 = DelayConfig(min_delay=0.1, max_delay=0.2)
        config2 = DelayConfig(min_delay=0.3, max_delay=0.4)

        manager1 = DelayManager(config1)
        manager2 = DelayManager(config2)

        start1 = time.time()
        await manager1.delay()
        elapsed1 = time.time() - start1

        start2 = time.time()
        await manager2.delay()
        elapsed2 = time.time() - start2

        assert 0.05 <= elapsed1 <= 0.25
        assert 0.25 <= elapsed2 <= 0.45
