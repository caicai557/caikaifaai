"""
Browser context wrapper for Telegram instances.

Contract:
- BrowserContext: Independent user_data_dir per instance
- Wraps Playwright browser context configuration
- Stores instance metadata (id, profile, URL, port)
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from src.telegram_multi.config import BrowserConfig


class BrowserContext(BaseModel):
    """Configuration and metadata for a single Telegram browser instance."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    instance_id: str = Field(..., description="Unique instance identifier")
    profile_path: str = Field(..., description="Browser profile directory path")
    browser_config: BrowserConfig = Field(
        default_factory=BrowserConfig,
        description="Browser settings (headless, executable_path)",
    )
    target_url: str = Field(
        default="https://web.telegram.org/a/", description="Target URL to navigate to"
    )
    port: Optional[int] = Field(
        default=None, description="Debugging port for browser instance (optional)"
    )
