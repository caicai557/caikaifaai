"""
Tests for src/config.py feature flags and configuration.
"""

from src.config import Config


class TestConfig:
    """Test suite for Config class."""

    def test_default_feature_flags(self):
        """Test default feature flag values."""
        assert Config.FEATURE_DARK_MODE is False
        assert Config.FEATURE_BETA_FEATURES is False

    def test_default_app_settings(self):
        """Test default application settings."""
        assert Config.APP_NAME == "CESI Demo"
        assert Config.VERSION == "0.1.0"
        assert Config.DEBUG is False

    def test_is_feature_enabled_existing_feature(self):
        """Test checking if an existing feature is enabled."""
        # Initially disabled
        assert Config.is_feature_enabled("dark_mode") is False

        # Enable and check
        Config.FEATURE_DARK_MODE = True
        assert Config.is_feature_enabled("dark_mode") is True

        # Cleanup
        Config.FEATURE_DARK_MODE = False

    def test_is_feature_enabled_non_existent_feature(self):
        """Test checking a non-existent feature returns False."""
        assert Config.is_feature_enabled("non_existent") is False

    def test_enable_feature_existing(self):
        """Test enabling an existing feature flag."""
        # Start with disabled
        Config.FEATURE_DARK_MODE = False

        # Enable
        Config.enable_feature("dark_mode")
        assert Config.FEATURE_DARK_MODE is True

        # Cleanup
        Config.FEATURE_DARK_MODE = False

    def test_enable_feature_non_existent(self):
        """Test enabling a non-existent feature does nothing."""
        # Should not raise error, just silently skip
        Config.enable_feature("non_existent_feature")

        # Verify no attribute was created
        assert not hasattr(Config, "FEATURE_NON_EXISTENT_FEATURE")

    def test_disable_feature_existing(self):
        """Test disabling an existing feature flag."""
        # Start with enabled
        Config.FEATURE_BETA_FEATURES = True

        # Disable
        Config.disable_feature("beta_features")
        assert Config.FEATURE_BETA_FEATURES is False

    def test_disable_feature_non_existent(self):
        """Test disabling a non-existent feature does nothing."""
        # Should not raise error, just silently skip
        Config.disable_feature("non_existent_feature")

        # Verify no attribute was created
        assert not hasattr(Config, "FEATURE_NON_EXISTENT_FEATURE")

    def test_enable_disable_cycle(self):
        """Test enable/disable cycle maintains correct state."""
        feature = "dark_mode"

        # Start disabled
        Config.FEATURE_DARK_MODE = False
        assert Config.is_feature_enabled(feature) is False

        # Enable
        Config.enable_feature(feature)
        assert Config.is_feature_enabled(feature) is True

        # Disable
        Config.disable_feature(feature)
        assert Config.is_feature_enabled(feature) is False

    def test_case_insensitive_feature_names(self):
        """Test that feature names are case-insensitive."""
        Config.FEATURE_DARK_MODE = False

        # Test various case combinations
        Config.enable_feature("DARK_MODE")
        assert Config.FEATURE_DARK_MODE is True

        Config.disable_feature("dark_mode")
        assert Config.FEATURE_DARK_MODE is False

        Config.enable_feature("Dark_Mode")
        assert Config.FEATURE_DARK_MODE is True

        # Cleanup
        Config.FEATURE_DARK_MODE = False
