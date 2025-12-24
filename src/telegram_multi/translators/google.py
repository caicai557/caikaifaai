"""
Google Translate provider implementation.

Contract:
- Wraps googletrans library
- Supports automatic language detection (source_lang='auto')
- Caches translations to reduce API calls
- Gracefully handles failures (returns original text)
- Implements exponential backoff for rate limiting
"""

import hashlib
import time
from typing import List
from src.telegram_multi.translator import Translator
from src.telegram_multi.config import TranslationConfig


class GoogleTranslator(Translator):
    """Google Translate provider using googletrans library."""

    def __init__(self, config: TranslationConfig):
        """Initialize Google Translator.

        Args:
            config: TranslationConfig with source/target languages
        """
        super().__init__(config)
        self.max_retries = 3
        self.backoff_factor = 0.5  # Exponential backoff multiplier

    def translate(self, text: str, src_lang: str = None, dest_lang: str = None) -> str:
        """Translate text using Google Translate.

        Args:
            text: Text to translate
            src_lang: Source language (uses config.source_lang if None)
            dest_lang: Destination language (uses config.target_lang if None)

        Returns:
            Translated text, or original text on failure
        """
        if not self.config.enabled:
            return text

        src_lang = src_lang or self.config.source_lang
        dest_lang = dest_lang or self.config.target_lang

        # Create cache key using MD5 hash of full text to avoid collisions
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        cache_key = f"{src_lang}:{dest_lang}:{text_hash}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Try translation with retries
        for attempt in range(self.max_retries):
            try:
                from googletrans import Translator as GoogleTransLib

                translator = GoogleTransLib()
                result = translator.translate(
                    text, src_language=src_lang, dest_language=dest_lang
                )
                trans_text = (
                    result.get("text", text)
                    if isinstance(result, dict)
                    else result.text
                )

                # Cache the result
                self.cache[cache_key] = trans_text
                return trans_text

            except Exception:
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = self.backoff_factor * (2**attempt)
                    time.sleep(wait_time)
                else:
                    # Final attempt failed, return original text
                    return text

        return text

    def batch_translate(
        self, texts: List[str], src_lang: str = None, dest_lang: str = None
    ) -> List[str]:
        """Translate multiple texts.

        Args:
            texts: List of texts to translate
            src_lang: Source language (uses config.source_lang if None)
            dest_lang: Destination language (uses config.target_lang if None)

        Returns:
            List of translated texts
        """
        if not self.config.enabled:
            return texts

        results = []
        for text in texts:
            translated = self.translate(text, src_lang, dest_lang)
            results.append(translated)

        return results
