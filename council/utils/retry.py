"""
Retry Utilities for Council Framework (2026)

Provides decorators and utilities for automatic retry with:
- Exponential backoff
- Fallback model switching
- Detailed logging
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """
    Retry configuration.

    Attributes:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Exponential backoff base
        jitter: Add random jitter to delay
        retry_on: Exception types to retry on
        fallback_value: Value to return if all retries fail
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on: tuple = (Exception,)
    fallback_value: Any = None


@dataclass
class RetryStats:
    """Statistics for retry operations."""

    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_delay_seconds: float = 0.0
    last_error: Optional[str] = None
    fallback_used: bool = False


def calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool,
) -> float:
    """
    Calculate delay with exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Exponential backoff base
        jitter: Add random jitter

    Returns:
        float: Delay in seconds
    """
    import random

    delay = min(base_delay * (exponential_base**attempt), max_delay)
    if jitter:
        delay = delay * (0.5 + random.random())
    return delay


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """
    Decorator for synchronous functions with retry logic.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        exponential_base: Exponential backoff base
        jitter: Add random jitter to delay
        retry_on: Exception types to retry on
        on_retry: Callback on each retry (exception, attempt)

    Returns:
        Decorated function

    Example:
        @retry(max_attempts=3, base_delay=1.0)
        def fetch_data():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = calculate_delay(
                            attempt, base_delay, max_delay, exponential_base, jitter
                        )
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}. "
                            f"Waiting {delay:.2f}s"
                        )
                        if on_retry:
                            on_retry(e, attempt)
                        time.sleep(delay)

            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """
    Decorator for async functions with retry logic.

    Same parameters as `retry` but for async functions.

    Example:
        @async_retry(max_attempts=3, base_delay=1.0)
        async def fetch_data():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = calculate_delay(
                            attempt, base_delay, max_delay, exponential_base, jitter
                        )
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}. "
                            f"Waiting {delay:.2f}s"
                        )
                        if on_retry:
                            on_retry(e, attempt)
                        await asyncio.sleep(delay)

            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def with_fallback(
    fallback_func: Optional[Callable[..., T]] = None,
    fallback_value: Optional[T] = None,
    max_attempts: int = 2,
    base_delay: float = 0.5,
    retry_on: tuple = (Exception,),
) -> Callable:
    """
    Decorator that tries main function, then falls back on failure.

    Args:
        fallback_func: Fallback function to call on failure
        fallback_value: Static value to return on failure (if no fallback_func)
        max_attempts: Attempts before falling back
        base_delay: Delay between retries
        retry_on: Exception types to handle

    Returns:
        Decorated function

    Example:
        def backup_api():
            return call_backup()

        @with_fallback(fallback_func=backup_api)
        def primary_api():
            return call_primary()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Try main function with retries
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    if attempt < max_attempts - 1:
                        delay = calculate_delay(attempt, base_delay, 10.0, 2.0, True)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s"
                        )
                        time.sleep(delay)

            # Main function failed, try fallback
            logger.warning(f"{func.__name__} failed after {max_attempts} attempts, using fallback")

            if fallback_func:
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Fallback also failed: {e}")
                    if fallback_value is not None:
                        return fallback_value
                    raise

            if fallback_value is not None:
                return fallback_value

            raise RuntimeError(f"No fallback available for {func.__name__}")

        return wrapper

    return decorator


def async_with_fallback(
    fallback_func: Optional[Callable[..., T]] = None,
    fallback_value: Optional[T] = None,
    max_attempts: int = 2,
    base_delay: float = 0.5,
    retry_on: tuple = (Exception,),
) -> Callable:
    """
    Async version of with_fallback decorator.

    Example:
        async def backup_api():
            return await call_backup()

        @async_with_fallback(fallback_func=backup_api)
        async def primary_api():
            return await call_primary()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Try main function with retries
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    if attempt < max_attempts - 1:
                        delay = calculate_delay(attempt, base_delay, 10.0, 2.0, True)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s"
                        )
                        await asyncio.sleep(delay)

            # Main function failed, try fallback
            logger.warning(f"{func.__name__} failed after {max_attempts} attempts, using fallback")

            if fallback_func:
                try:
                    if asyncio.iscoroutinefunction(fallback_func):
                        return await fallback_func(*args, **kwargs)
                    else:
                        return fallback_func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Fallback also failed: {e}")
                    if fallback_value is not None:
                        return fallback_value
                    raise

            if fallback_value is not None:
                return fallback_value

            raise RuntimeError(f"No fallback available for {func.__name__}")

        return wrapper

    return decorator


class RetryManager:
    """
    Centralized retry management with statistics.

    Example:
        manager = RetryManager(config=RetryConfig(max_attempts=3))

        @manager.wrap
        def my_function():
            ...

        # Check stats
        print(manager.stats)
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.stats = RetryStats()

    def wrap(self, func: Callable[..., T]) -> Callable[..., T]:
        """Wrap a function with retry logic and statistics tracking."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            start_time = time.time()

            for attempt in range(self.config.max_attempts):
                self.stats.total_attempts += 1
                try:
                    result = func(*args, **kwargs)
                    self.stats.successful_attempts += 1
                    return result
                except self.config.retry_on as e:
                    last_exception = e
                    self.stats.failed_attempts += 1
                    self.stats.last_error = str(e)

                    if attempt < self.config.max_attempts - 1:
                        delay = calculate_delay(
                            attempt,
                            self.config.base_delay,
                            self.config.max_delay,
                            self.config.exponential_base,
                            self.config.jitter,
                        )
                        self.stats.total_delay_seconds += delay
                        logger.warning(
                            f"Retry {attempt + 1}/{self.config.max_attempts}: {e}"
                        )
                        time.sleep(delay)

            # All retries failed
            if self.config.fallback_value is not None:
                self.stats.fallback_used = True
                logger.warning(f"Using fallback value for {func.__name__}")
                return self.config.fallback_value

            raise last_exception  # type: ignore

        return wrapper

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = RetryStats()


__all__ = [
    "RetryConfig",
    "RetryStats",
    "RetryManager",
    "retry",
    "async_retry",
    "with_fallback",
    "async_with_fallback",
    "calculate_delay",
]
