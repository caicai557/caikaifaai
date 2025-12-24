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
