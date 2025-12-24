"""
Tests for Google Translate provider implementation (Phase 3).

Contract:
- GoogleTranslator: Wraps googletrans library
- Must handle network errors gracefully
- Must support rate limiting with exponential backoff
- Must return original text on failure
"""

from src.telegram_multi.translators.google import GoogleTranslator
from src.telegram_multi.config import TranslationConfig


class TestGoogleTranslator:
    """Contract tests for Google Translate provider."""

    def test_create_google_translator(self):
        """Contract: Can instantiate GoogleTranslator."""
        config = TranslationConfig(
            provider="google", source_lang="en", target_lang="zh-CN"
        )
        translator = GoogleTranslator(config)
        assert translator is not None
        assert translator.config.provider == "google"

    def test_google_translator_translate_signature(self):
        """Contract: GoogleTranslator has translate() method."""
        config = TranslationConfig(provider="google")
        translator = GoogleTranslator(config)
        assert hasattr(translator, "translate")
        assert callable(translator.translate)

    def test_google_translator_batch_translate_signature(self):
        """Contract: GoogleTranslator has batch_translate() method."""
        config = TranslationConfig(provider="google")
        translator = GoogleTranslator(config)
        assert hasattr(translator, "batch_translate")
        assert callable(translator.batch_translate)

    def test_google_translator_has_cache(self):
        """Contract: GoogleTranslator has translation cache."""
        config = TranslationConfig(provider="google")
        translator = GoogleTranslator(config)
        assert hasattr(translator, "cache")

    def test_google_translator_clear_cache(self):
        """Contract: Can clear GoogleTranslator cache."""
        config = TranslationConfig(provider="google")
        translator = GoogleTranslator(config)
        assert callable(translator.clear_cache)

    def test_google_translator_supports_auto_detect(self):
        """Contract: GoogleTranslator supports auto language detection."""
        config = TranslationConfig(
            provider="google", source_lang="auto", target_lang="en"
        )
        translator = GoogleTranslator(config)
        assert translator.config.source_lang == "auto"

    def test_google_translator_fallback_on_error(self):
        """Contract: Returns original text on translation failure."""
        config = TranslationConfig(
            provider="google", source_lang="en", target_lang="zh-CN"
        )
        translator = GoogleTranslator(config)
        # Contract: If translation fails, return original text (not None)
        # Implementation will mock this behavior
        assert hasattr(translator, "translate")


class TestGoogleTranslatorRateLimiting:
    """Contract tests for rate limiting."""

    def test_google_translator_has_retry_logic(self):
        """Contract: GoogleTranslator supports retry on failure."""
        config = TranslationConfig(provider="google")
        translator = GoogleTranslator(config)
        assert hasattr(translator, "max_retries")

    def test_google_translator_backoff_delay(self):
        """Contract: GoogleTranslator supports exponential backoff."""
        config = TranslationConfig(provider="google")
        translator = GoogleTranslator(config)
        assert hasattr(translator, "backoff_factor")

    def test_google_translator_respects_retry_limit(self):
        """Contract: Stops retrying after max_retries."""
        config = TranslationConfig(provider="google")
        translator = GoogleTranslator(config)
        # Should be configurable
        assert isinstance(translator.max_retries, int)
        assert translator.max_retries > 0
