"""
Configuration management for telegram-multi instances.

Contract:
- InstanceConfig: instance_id, profile_path, translation settings
- TranslationConfig: language pairs, providers (google, deepl, local)
- BrowserConfig: headless, executable_path
- TelegramConfig: multiple instances, browser settings, YAML loading
"""

from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class TranslationConfig(BaseModel):
    """Translation configuration for a Telegram instance."""

    enabled: bool = False
    provider: str = "google"
    source_lang: str = "auto"
    target_lang: str = "en"

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that provider is one of supported types."""
        valid_providers = {"google", "deepl", "local"}
        if v not in valid_providers:
            raise ValueError(
                f"provider must be one of {valid_providers}, got {v}"
            )
        return v


class BrowserConfig(BaseModel):
    """Browser configuration settings."""

    headless: bool = False
    executable_path: Optional[str] = None


class InstanceConfig(BaseModel):
    """Configuration for a single Telegram instance."""

    id: str
    profile_path: str
    translation: TranslationConfig = Field(default_factory=TranslationConfig)


class TelegramConfig(BaseModel):
    """Root configuration for telegram-multi application."""

    instances: List[InstanceConfig] = Field(default_factory=list)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)

    @classmethod
    def from_yaml(cls, file_path: str) -> "TelegramConfig":
        """Load configuration from a YAML file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            TelegramConfig instance

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If YAML is invalid
        """
        import yaml

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")

        if data is None:
            data = {}

        return cls(**data)
