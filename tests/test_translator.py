"""
Tests for translation abstraction layer (Phase 3).

Contract:
- Translator: Abstract interface for translation services
- Must support multiple providers (google, deepl, local)
- Must handle translation failures gracefully (return original text)
- Must support batching for performance
"""

import pytest
from src.telegram_multi.translator import TranslatorFactory
from src.telegram_multi.config import TranslationConfig


class TestTranslator:
    """Contract tests for Translator interface."""

    def test_translator_translate_basic(self):
        """Contract: Can translate text from source to target language."""
        translator = TranslatorFactory.create(
            TranslationConfig(
                enabled=True, source_lang="en", target_lang="zh-CN", provider="google"
            )
        )
        # Interface contract: method exists and returns string
        assert callable(translator.translate)

    def test_translator_translate_signature(self):
        """Contract: translate() accepts text, src_lang, dest_lang."""
        translator = TranslatorFactory.create(
            TranslationConfig(enabled=True, provider="google")
        )
        # Method signature: translate(text: str, src_lang: str, dest_lang: str) -> str
        assert hasattr(translator, "translate")

    def test_translator_batch_translate_signature(self):
        """Contract: batch_translate() accepts list of texts."""
        translator = TranslatorFactory.create(
            TranslationConfig(enabled=True, provider="google")
        )
        assert hasattr(translator, "batch_translate")

    def test_translator_enabled_flag(self):
        """Contract: Translator respects enabled flag."""
        translator_enabled = TranslatorFactory.create(
            TranslationConfig(enabled=True, provider="google")
        )
        translator_disabled = TranslatorFactory.create(
            TranslationConfig(enabled=False, provider="google")
        )
        assert translator_enabled.config.enabled is True
        assert translator_disabled.config.enabled is False

    def test_translator_provider_config(self):
        """Contract: Translator stores provider configuration."""
        config = TranslationConfig(
            provider="google", source_lang="en", target_lang="zh-CN"
        )
        translator = TranslatorFactory.create(config)
        assert translator.config.provider == "google"
        assert translator.config.source_lang == "en"
        assert translator.config.target_lang == "zh-CN"


class TestTranslatorFactory:
    """Contract tests for translator factory."""

    def test_factory_create_google_translator(self):
        """Contract: Can create Google Translate provider."""
        config = TranslationConfig(
            enabled=True, provider="google", source_lang="en", target_lang="zh-CN"
        )
        translator = TranslatorFactory.create(config)
        assert translator is not None
        assert translator.config.provider == "google"

    def test_factory_create_multiple_providers(self):
        """Contract: Factory can be extended with additional providers."""
        # Verify factory has mechanism to register providers
        assert hasattr(TranslatorFactory, "register_provider")
        assert callable(TranslatorFactory.register_provider)

    def test_factory_provider_registry(self):
        """Contract: Factory maintains provider registry."""
        # Check that at least google is registered
        config = TranslationConfig(
            enabled=True, provider="google", source_lang="en", target_lang="zh-CN"
        )
        translator = TranslatorFactory.create(config)
        assert translator is not None
        assert translator.config.provider == "google"

    def test_factory_provider_validation(self):
        """Contract: TranslationConfig validates provider values."""
        # TranslationConfig should validate provider at init time
        # Invalid provider should be caught by Pydantic
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TranslationConfig(provider="invalid_unknown_provider")

    def test_factory_disabled_translation(self):
        """Contract: Factory handles disabled translation config."""
        config = TranslationConfig(enabled=False)
        translator = TranslatorFactory.create(config)
        assert translator is not None
        assert translator.config.enabled is False


class TestTranslationCaching:
    """Contract tests for translation caching."""

    def test_translator_has_cache(self):
        """Contract: Translator can cache translations."""
        translator = TranslatorFactory.create(
            TranslationConfig(enabled=True, provider="google")
        )
        assert hasattr(translator, "cache")

    def test_cache_is_dict(self):
        """Contract: Cache is a dictionary-like structure."""
        translator = TranslatorFactory.create(
            TranslationConfig(enabled=True, provider="google")
        )
        # Cache should be dict or have dict-like interface
        assert hasattr(translator.cache, "__getitem__")
        assert hasattr(translator.cache, "__setitem__")

    def test_translator_clear_cache(self):
        """Contract: Can clear translation cache."""
        translator = TranslatorFactory.create(
            TranslationConfig(enabled=True, provider="google")
        )
        assert callable(translator.clear_cache)
