"""
Feature flags and configuration management.
"""

class Config:
    """Application configuration with feature flags."""
    
    # Feature flags - 功能开关
    FEATURE_DARK_MODE = False
    FEATURE_BETA_FEATURES = False
    
    # App settings
    APP_NAME = "CESI Demo"
    VERSION = "0.1.0"
    DEBUG = False
    
    @classmethod
    def is_feature_enabled(cls, feature_name: str) -> bool:
        """Check if a feature flag is enabled."""
        flag_name = f"FEATURE_{feature_name.upper()}"
        return getattr(cls, flag_name, False)
    
    @classmethod
    def enable_feature(cls, feature_name: str) -> None:
        """Enable a feature flag."""
        flag_name = f"FEATURE_{feature_name.upper()}"
        if hasattr(cls, flag_name):
            setattr(cls, flag_name, True)
    
    @classmethod
    def disable_feature(cls, feature_name: str) -> None:
        """Disable a feature flag."""
        flag_name = f"FEATURE_{feature_name.upper()}"
        if hasattr(cls, flag_name):
            setattr(cls, flag_name, False)
