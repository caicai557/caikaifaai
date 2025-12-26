"""
Tests for telegram_multi configuration system (Phase 1).

Contract:
- InstanceConfig supports instance_id, profile_path, translation settings
- TranslationConfig validates language pairs and providers (google, deepl, local)
- TelegramConfig manages multiple instances and browser settings
- Config loads from YAML files
"""

import pytest
from src.telegram_multi.config import (
    InstanceConfig,
    TranslationConfig,
    BrowserConfig,
    TelegramConfig,
)


class TestInstanceConfig:
    """Contract tests for InstanceConfig."""

    def test_create_instance_config_minimal(self):
        """Contract: Can create InstanceConfig with instance_id and profile_path."""
        config = InstanceConfig(id="test-instance", profile_path="/tmp/profiles/test")
        assert config.id == "test-instance"
        assert config.profile_path == "/tmp/profiles/test"

    def test_create_instance_config_with_translation(self):
        """Contract: InstanceConfig supports translation configuration."""
        translation = TranslationConfig(
            enabled=True, source_lang="en", target_lang="zh-CN", provider="google"
        )
        config = InstanceConfig(
            id="work", profile_path="/tmp/profiles/work", translation=translation
        )
        assert config.id == "work"
        assert config.translation.enabled is True
        assert config.translation.source_lang == "en"
        assert config.translation.target_lang == "zh-CN"
        assert config.translation.provider == "google"

    def test_instance_config_translation_disabled_by_default(self):
        """Contract: Translation is disabled by default."""
        config = InstanceConfig(id="test", profile_path="/tmp/profiles/test")
        assert config.translation.enabled is False

    def test_instance_config_requires_id(self):
        """Contract: InstanceConfig requires instance_id."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            InstanceConfig(profile_path="/tmp/profiles/test")

    def test_instance_config_requires_profile_path(self):
        """Contract: InstanceConfig requires profile_path."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            InstanceConfig(id="test")


class TestTranslationConfig:
    """Contract tests for TranslationConfig."""

    def test_translation_config_defaults(self):
        """Contract: TranslationConfig has sensible defaults."""
        config = TranslationConfig()
        assert config.enabled is False
        assert config.provider == "google"
        assert config.source_lang == "auto"
        assert config.target_lang == "en"

    def test_translation_config_google_provider(self):
        """Contract: Google Translate provider is supported."""
        config = TranslationConfig(provider="google")
        assert config.provider == "google"

    def test_translation_config_deepl_provider(self):
        """Contract: DeepL provider is supported."""
        config = TranslationConfig(provider="deepl")
        assert config.provider == "deepl"

    def test_translation_config_local_provider(self):
        """Contract: Local offline provider is supported."""
        config = TranslationConfig(provider="local")
        assert config.provider == "local"

    def test_translation_config_invalid_provider(self):
        """Contract: Invalid providers are rejected."""
        with pytest.raises(ValueError):
            TranslationConfig(provider="invalid_provider")

    def test_translation_config_with_source_and_target(self):
        """Contract: Can set source and target languages."""
        config = TranslationConfig(source_lang="en", target_lang="zh-CN")
        assert config.source_lang == "en"
        assert config.target_lang == "zh-CN"

    # === Phase 4.1: display_mode 和 show_header 测试 ===

    def test_translation_config_display_mode_default(self):
        """Contract: display_mode defaults to 'bilingual'."""
        config = TranslationConfig()
        assert config.display_mode == "bilingual"

    def test_translation_config_display_mode_bilingual(self):
        """Contract: display_mode accepts 'bilingual'."""
        config = TranslationConfig(display_mode="bilingual")
        assert config.display_mode == "bilingual"

    def test_translation_config_display_mode_replace(self):
        """Contract: display_mode accepts 'replace'."""
        config = TranslationConfig(display_mode="replace")
        assert config.display_mode == "replace"

    def test_translation_config_display_mode_original(self):
        """Contract: display_mode accepts 'original'."""
        config = TranslationConfig(display_mode="original")
        assert config.display_mode == "original"

    def test_translation_config_display_mode_invalid(self):
        """Contract: display_mode rejects invalid values."""
        with pytest.raises(ValueError):
            TranslationConfig(display_mode="invalid_mode")

    def test_translation_config_show_header_default(self):
        """Contract: show_header defaults to True."""
        config = TranslationConfig()
        assert config.show_header is True

    def test_translation_config_show_header_false(self):
        """Contract: show_header can be set to False."""
        config = TranslationConfig(show_header=False)
        assert config.show_header is False

    def test_translation_config_full_bilingual_setup(self):
        """Contract: Full bilingual configuration works."""
        config = TranslationConfig(
            enabled=True,
            provider="google",
            source_lang="zh",
            target_lang="en",
            display_mode="bilingual",
            show_header=True,
        )
        assert config.enabled is True
        assert config.display_mode == "bilingual"
        assert config.show_header is True


class TestBrowserConfig:
    """Contract tests for BrowserConfig."""

    def test_browser_config_defaults(self):
        """Contract: BrowserConfig has defaults."""
        config = BrowserConfig()
        assert config.headless is False
        assert config.executable_path is None

    def test_browser_config_headless(self):
        """Contract: Can set headless mode."""
        config = BrowserConfig(headless=True)
        assert config.headless is True

    def test_browser_config_executable_path(self):
        """Contract: Can set custom executable path."""
        config = BrowserConfig(executable_path="/usr/bin/google-chrome")
        assert config.executable_path == "/usr/bin/google-chrome"


class TestTelegramConfig:
    """Contract tests for TelegramConfig."""

    def test_telegram_config_creation(self):
        """Contract: Can create TelegramConfig with instances."""
        config = TelegramConfig(
            instances=[
                {
                    "id": "work",
                    "profile_path": "profiles/work",
                    "translation": {
                        "enabled": True,
                        "source_lang": "en",
                        "target_lang": "zh-CN",
                    },
                }
            ]
        )
        assert len(config.instances) == 1
        assert config.instances[0].id == "work"
        assert config.instances[0].translation.enabled is True

    def test_telegram_config_multiple_instances(self):
        """Contract: Can define multiple instances."""
        config = TelegramConfig(
            instances=[
                {"id": "work", "profile_path": "profiles/work"},
                {"id": "personal", "profile_path": "profiles/personal"},
                {"id": "business", "profile_path": "profiles/business"},
            ]
        )
        assert len(config.instances) == 3
        ids = [inst.id for inst in config.instances]
        assert ids == ["work", "personal", "business"]

    def test_telegram_config_empty_instances_list(self):
        """Contract: Can create config with empty instances list."""
        config = TelegramConfig(instances=[])
        assert len(config.instances) == 0

    def test_telegram_config_default_browser_settings(self):
        """Contract: TelegramConfig has default browser settings."""
        config = TelegramConfig()
        assert config.browser.headless is False
        assert config.browser.executable_path is None

    def test_telegram_config_browser_override(self):
        """Contract: Can override browser settings."""
        config = TelegramConfig(
            browser={"headless": True, "executable_path": "/usr/bin/chrome"}
        )
        assert config.browser.headless is True
        assert config.browser.executable_path == "/usr/bin/chrome"

    def test_telegram_config_from_yaml(self, tmp_path):
        """Contract: Can load config from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
instances:
  - id: test
    profile_path: profiles/test
    translation:
      enabled: true
      source_lang: en
      target_lang: zh-CN

browser:
  headless: false
  executable_path: null
""")
        config = TelegramConfig.from_yaml(str(config_file))
        assert len(config.instances) == 1
        assert config.instances[0].id == "test"
        assert config.instances[0].translation.enabled is True

    def test_telegram_config_from_yaml_file_not_found(self):
        """Contract: Raises error if YAML file not found."""
        with pytest.raises(FileNotFoundError):
            TelegramConfig.from_yaml("/nonexistent/config.yaml")

    def test_telegram_config_from_yaml_invalid_format(self, tmp_path):
        """Contract: Raises error if YAML is malformed."""
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("invalid: yaml: content: [")
        with pytest.raises(Exception):  # YAML parse error
            TelegramConfig.from_yaml(str(config_file))

    def test_telegram_config_instance_ids_unique(self):
        """Contract: Instance IDs uniqueness (not enforced at config level)."""
        # Data quality check - system should work with duplicates
        # but it's not recommended. We test that it allows duplicates.
        config = TelegramConfig(
            instances=[
                {"id": "work", "profile_path": "profiles/work1"},
                {"id": "work", "profile_path": "profiles/work2"},
            ]
        )
        assert len(config.instances) == 2

    # === Phase 4.1: YAML 加载支持新字段 ===

    def test_telegram_config_yaml_with_display_mode(self, tmp_path):
        """Contract: YAML loading supports display_mode field."""
        config_file = tmp_path / "bilingual.yaml"
        config_file.write_text("""
instances:
  - id: test
    profile_path: profiles/test
    translation:
      enabled: true
      source_lang: en
      target_lang: zh-CN
      display_mode: bilingual
      show_header: true
""")
        config = TelegramConfig.from_yaml(str(config_file))
        assert config.instances[0].translation.display_mode == "bilingual"
        assert config.instances[0].translation.show_header is True

    def test_telegram_config_yaml_backward_compatible(self, tmp_path):
        """Contract: Old YAML configs without new fields still load."""
        config_file = tmp_path / "old_config.yaml"
        config_file.write_text("""
instances:
  - id: legacy
    profile_path: profiles/legacy
    translation:
      enabled: true
      provider: google
      source_lang: auto
      target_lang: en
""")
        config = TelegramConfig.from_yaml(str(config_file))
        # Should use defaults for missing fields
        assert config.instances[0].translation.display_mode == "bilingual"
        assert config.instances[0].translation.show_header is True
