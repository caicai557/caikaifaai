"""
Tests for browser context management (Phase 2).

Contract:
- BrowserContext wraps Playwright with independent user_data_dir
- Must support headless and headed modes
- Must support custom executable paths
- Must handle Telegram Web A URL navigation
"""

import pytest
from src.telegram_multi.browser_context import BrowserContext
from src.telegram_multi.config import BrowserConfig


class TestBrowserContext:
    """Contract tests for BrowserContext."""

    def test_create_browser_context_with_profile_path(self, tmp_path):
        """Contract: Can create BrowserContext with profile path."""
        profile_path = tmp_path / "profile"
        context = BrowserContext(
            instance_id="test",
            profile_path=str(profile_path),
            browser_config=BrowserConfig(),
        )
        assert context.instance_id == "test"
        assert context.profile_path == str(profile_path)

    def test_browser_context_requires_instance_id(self, tmp_path):
        """Contract: BrowserContext requires instance_id."""
        from pydantic import ValidationError

        profile_path = tmp_path / "profile"
        with pytest.raises(ValidationError):
            BrowserContext(
                profile_path=str(profile_path), browser_config=BrowserConfig()
            )

    def test_browser_context_requires_profile_path(self):
        """Contract: BrowserContext requires profile_path."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BrowserContext(instance_id="test", browser_config=BrowserConfig())

    def test_browser_context_with_headless_mode(self, tmp_path):
        """Contract: BrowserContext respects headless setting."""
        profile_path = tmp_path / "profile"
        config = BrowserConfig(headless=True)
        context = BrowserContext(
            instance_id="test", profile_path=str(profile_path), browser_config=config
        )
        assert context.browser_config.headless is True

    def test_browser_context_with_custom_executable(self, tmp_path):
        """Contract: BrowserContext respects custom executable path."""
        profile_path = tmp_path / "profile"
        config = BrowserConfig(executable_path="/usr/bin/google-chrome")
        context = BrowserContext(
            instance_id="test", profile_path=str(profile_path), browser_config=config
        )
        assert context.browser_config.executable_path == "/usr/bin/google-chrome"

    def test_browser_context_stores_url(self, tmp_path):
        """Contract: BrowserContext can store target URL."""
        profile_path = tmp_path / "profile"
        context = BrowserContext(
            instance_id="test",
            profile_path=str(profile_path),
            browser_config=BrowserConfig(),
            target_url="https://web.telegram.org/a/",
        )
        assert context.target_url == "https://web.telegram.org/a/"

    def test_browser_context_default_url(self, tmp_path):
        """Contract: BrowserContext defaults to Telegram Web A URL."""
        profile_path = tmp_path / "profile"
        context = BrowserContext(
            instance_id="test",
            profile_path=str(profile_path),
            browser_config=BrowserConfig(),
        )
        assert context.target_url == "https://web.telegram.org/a/"


class TestBrowserContextPortManagement:
    """Contract tests for port/resource management."""

    def test_browser_context_can_get_port(self, tmp_path):
        """Contract: Can assign/get a port for instance."""
        profile_path = tmp_path / "profile"
        context = BrowserContext(
            instance_id="test",
            profile_path=str(profile_path),
            browser_config=BrowserConfig(),
            port=9222,
        )
        assert context.port == 9222

    def test_browser_context_port_optional(self, tmp_path):
        """Contract: Port is optional."""
        profile_path = tmp_path / "profile"
        context = BrowserContext(
            instance_id="test",
            profile_path=str(profile_path),
            browser_config=BrowserConfig(),
        )
        assert context.port is None


class TestBrowserContextStart:
    """Contract tests for BrowserContext.start() method (Phase 6.1)."""

    @pytest.mark.asyncio
    async def test_start_raises_not_implemented_error(self, tmp_path):
        """Contract: BrowserContext.start() raises NotImplementedError.

        AC1.1: start() must throw NotImplementedError to indicate stub status.
        """
        profile_path = tmp_path / "profile"
        context = BrowserContext(
            instance_id="test_instance",
            profile_path=str(profile_path),
            browser_config=BrowserConfig(),
        )

        with pytest.raises(NotImplementedError) as exc_info:
            await context.start()

        # Verify exception message contains key information
        error_message = str(exc_info.value)
        assert "not implemented" in error_message.lower()

    @pytest.mark.asyncio
    async def test_start_error_message_contains_instance_id(self, tmp_path):
        """Contract: NotImplementedError message includes instance_id for debugging.

        AC1.2: Error message must contain instance_id to help identify which
        instance failed.
        """
        profile_path = tmp_path / "profile"
        context = BrowserContext(
            instance_id="my_test_account",
            profile_path=str(profile_path),
            browser_config=BrowserConfig(),
        )

        with pytest.raises(NotImplementedError) as exc_info:
            await context.start()

        error_message = str(exc_info.value)
        assert "my_test_account" in error_message

    @pytest.mark.asyncio
    async def test_start_error_message_mentions_phase_5(self, tmp_path):
        """Contract: Error message guides developer to Phase 5 implementation.

        AC1.2: Error message should mention that implementation is pending
        in Phase 5.
        """
        profile_path = tmp_path / "profile"
        context = BrowserContext(
            instance_id="test",
            profile_path=str(profile_path),
            browser_config=BrowserConfig(),
        )

        with pytest.raises(NotImplementedError) as exc_info:
            await context.start()

        error_message = str(exc_info.value).lower()
        # Message should guide to Phase 5 or indicate stub status
        assert "phase 5" in error_message or "stub" in error_message
