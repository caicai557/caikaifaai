"""
Council Configuration
Centralized configuration management using Pydantic.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class CouncilConfig(BaseSettings):
    """
    Global configuration for the Council Agent.
    Loads from environment variables and .env file.
    """

    # --- API Keys ---
    GEMINI_API_KEY: Optional[str] = Field(None, description="Google Gemini API Key")
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API Key")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, description="Anthropic API Key")

    # --- Model Selection ---
    DEFAULT_MODEL: str = Field("gemini-2.0-flash-exp", description="Default model for general tasks")
    PLANNER_MODEL: str = Field("gemini-2.0-flash-thinking-exp-1219", description="Model for planning and architecture")
    CODER_MODEL: str = Field("gemini-2.0-flash-exp", description="Model for code generation")
    REVIEWER_MODEL: str = Field("gemini-2.0-flash-exp", description="Model for code review")

    # --- Wald Consensus Settings ---
    WALD_UPPER_LIMIT: float = Field(0.95, description="Upper threshold for auto-approval")
    WALD_LOWER_LIMIT: float = Field(0.30, description="Lower threshold for rejection")
    WALD_PRIOR: float = Field(0.70, description="Prior probability of approval")

    # --- Self-Healing Settings ---
    MAX_HEALING_ITERATIONS: int = Field(5, description="Maximum self-healing attempts")
    TEST_COMMAND: str = Field("python -m pytest", description="Default test command")

    # --- System Settings ---
    VERBOSE: bool = Field(True, description="Enable verbose logging")
    WORKING_DIR: str = Field(".", description="Default working directory")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global config instance
config = CouncilConfig()
