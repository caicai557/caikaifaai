"""
Health Check Module for Council Framework (2026)

Provides:
- Periodic model API availability checks
- Automatic degradation marking
- Recovery detection
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status of a model or service."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    target: str
    status: HealthStatus
    latency_ms: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelHealth:
    """Health state for a model."""

    model_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    avg_latency_ms: float = 0.0
    check_count: int = 0

    def update(self, success: bool, latency_ms: float) -> None:
        """Update health state based on check result."""
        self.last_check = datetime.now()
        self.check_count += 1

        # Update rolling average latency
        if self.check_count == 1:
            self.avg_latency_ms = latency_ms
        else:
            self.avg_latency_ms = (self.avg_latency_ms * 0.9) + (latency_ms * 0.1)

        if success:
            self.consecutive_failures = 0
            self.consecutive_successes += 1
            self.last_success = datetime.now()

            # Recover from degraded/unhealthy
            if self.consecutive_successes >= 3:
                self.status = HealthStatus.HEALTHY
            elif self.status == HealthStatus.UNHEALTHY:
                self.status = HealthStatus.DEGRADED
        else:
            self.consecutive_successes = 0
            self.consecutive_failures += 1
            self.last_failure = datetime.now()

            # Degrade on failures
            if self.consecutive_failures >= 3:
                self.status = HealthStatus.UNHEALTHY
            elif self.consecutive_failures >= 1:
                self.status = HealthStatus.DEGRADED


class HealthChecker:
    """
    Health checker for models and services.

    Provides:
    - Periodic health checks
    - Status tracking and history
    - Automatic degradation and recovery

    Example:
        checker = HealthChecker()

        # Register a model check
        async def check_claude():
            response = await call_claude("ping")
            return len(response) > 0

        checker.register("claude-sonnet", check_claude)

        # Start background checks
        await checker.start(interval=60)

        # Check status
        if checker.is_healthy("claude-sonnet"):
            ...
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_threshold: int = 3,
        latency_threshold_ms: float = 5000,
    ):
        """
        Initialize health checker.

        Args:
            failure_threshold: Consecutive failures before unhealthy
            recovery_threshold: Consecutive successes before healthy
            latency_threshold_ms: Latency threshold for degradation
        """
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.latency_threshold_ms = latency_threshold_ms

        self._health_states: Dict[str, ModelHealth] = {}
        self._check_functions: Dict[str, Callable] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._history: List[HealthCheckResult] = []
        self._max_history = 100

    def register(
        self,
        name: str,
        check_func: Callable[[], bool] | Callable[[], Any],
        initial_status: HealthStatus = HealthStatus.UNKNOWN,
    ) -> None:
        """
        Register a health check.

        Args:
            name: Name of the target (e.g., model name)
            check_func: Function that returns True if healthy
            initial_status: Initial health status
        """
        self._check_functions[name] = check_func
        self._health_states[name] = ModelHealth(
            model_name=name, status=initial_status
        )
        logger.info(f"Registered health check for: {name}")

    def unregister(self, name: str) -> None:
        """Remove a health check."""
        self._check_functions.pop(name, None)
        self._health_states.pop(name, None)

    async def check(self, name: str) -> HealthCheckResult:
        """
        Run a single health check.

        Args:
            name: Target name

        Returns:
            HealthCheckResult
        """
        if name not in self._check_functions:
            return HealthCheckResult(
                target=name,
                status=HealthStatus.UNKNOWN,
                latency_ms=0,
                message=f"No check registered for {name}",
            )

        check_func = self._check_functions[name]
        health = self._health_states[name]

        start_time = time.perf_counter()
        try:
            # Run the check
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()

            latency_ms = (time.perf_counter() - start_time) * 1000
            success = bool(result)

            # Check latency threshold
            if success and latency_ms > self.latency_threshold_ms:
                success = False  # Treat high latency as failure
                message = f"High latency: {latency_ms:.0f}ms"
            else:
                message = "OK" if success else "Check returned false"

            health.update(success, latency_ms)

            check_result = HealthCheckResult(
                target=name,
                status=health.status,
                latency_ms=latency_ms,
                message=message,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            health.update(False, latency_ms)

            check_result = HealthCheckResult(
                target=name,
                status=health.status,
                latency_ms=latency_ms,
                message=f"Error: {str(e)}",
            )
            logger.warning(f"Health check failed for {name}: {e}")

        # Store in history
        self._history.append(check_result)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        return check_result

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        for name in self._check_functions:
            results[name] = await self.check(name)
        return results

    async def start(self, interval: float = 60.0) -> None:
        """
        Start background health checks.

        Args:
            interval: Check interval in seconds
        """
        if self._running:
            logger.warning("Health checker already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop(interval))
        logger.info(f"Health checker started (interval={interval}s)")

    async def stop(self) -> None:
        """Stop background health checks."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health checker stopped")

    async def _run_loop(self, interval: float) -> None:
        """Background check loop."""
        while self._running:
            try:
                await self.check_all()
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

            await asyncio.sleep(interval)

    def get_status(self, name: str) -> HealthStatus:
        """Get current health status."""
        health = self._health_states.get(name)
        return health.status if health else HealthStatus.UNKNOWN

    def get_health(self, name: str) -> Optional[ModelHealth]:
        """Get full health state."""
        return self._health_states.get(name)

    def get_all_health(self) -> Dict[str, ModelHealth]:
        """Get all health states."""
        return self._health_states.copy()

    def is_healthy(self, name: str) -> bool:
        """Check if target is healthy."""
        return self.get_status(name) == HealthStatus.HEALTHY

    def is_available(self, name: str) -> bool:
        """Check if target is available (healthy or degraded)."""
        status = self.get_status(name)
        return status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNKNOWN)

    def get_healthy_models(self) -> List[str]:
        """Get list of healthy models."""
        return [
            name
            for name, health in self._health_states.items()
            if health.status == HealthStatus.HEALTHY
        ]

    def get_available_models(self) -> List[str]:
        """Get list of available models (healthy or degraded)."""
        return [
            name
            for name, health in self._health_states.items()
            if health.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        ]

    def get_history(self, name: Optional[str] = None, limit: int = 10) -> List[HealthCheckResult]:
        """
        Get health check history.

        Args:
            name: Filter by target name
            limit: Maximum results

        Returns:
            List of HealthCheckResult
        """
        results = self._history
        if name:
            results = [r for r in results if r.target == name]
        return results[-limit:]

    def mark_unhealthy(self, name: str, reason: str = "Manual") -> None:
        """Manually mark a target as unhealthy."""
        if name in self._health_states:
            self._health_states[name].status = HealthStatus.UNHEALTHY
            self._health_states[name].consecutive_failures = self.failure_threshold
            logger.warning(f"Manually marked {name} as unhealthy: {reason}")

    def mark_healthy(self, name: str, reason: str = "Manual") -> None:
        """Manually mark a target as healthy."""
        if name in self._health_states:
            self._health_states[name].status = HealthStatus.HEALTHY
            self._health_states[name].consecutive_successes = self.recovery_threshold
            self._health_states[name].consecutive_failures = 0
            logger.info(f"Manually marked {name} as healthy: {reason}")


# Default health checker instance
default_checker = HealthChecker()


__all__ = [
    "HealthStatus",
    "HealthCheckResult",
    "ModelHealth",
    "HealthChecker",
    "default_checker",
]
