"""
Translation abstraction layer and factory.

Contract:
- Translator: Abstract interface for translation services
- TranslatorFactory: Factory for creating translator instances
- Supports multiple providers (google, deepl, local)
- Graceful error handling (return original text on failure)
"""

from typing import Dict, List
from abc import ABC, abstractmethod
from src.telegram_multi.config import TranslationConfig


class Translator(ABC):
    """Abstract base class for translation providers."""

    def __init__(self, config: TranslationConfig):
        """Initialize translator with configuration.

        Args:
            config: TranslationConfig with provider, languages, etc.
        """
        self.config = config
        self.cache: Dict[str, str] = {}

    @abstractmethod
    def translate(
        self,
        text: str,
        src_lang: str,
        dest_lang: str
    ) -> str:
        """Translate text from source to destination language.

        Args:
            text: Text to translate
            src_lang: Source language code
            dest_lang: Destination language code

        Returns:
            Translated text, or original text on failure
        """
        pass

    @abstractmethod
    def batch_translate(
        self,
        texts: List[str],
        src_lang: str,
        dest_lang: str
    ) -> List[str]:
        """Translate multiple texts at once.

        Args:
            texts: List of texts to translate
            src_lang: Source language code
            dest_lang: Destination language code

        Returns:
            List of translated texts
        """
        pass

    def clear_cache(self) -> None:
        """Clear the translation cache."""
        self.cache.clear()


class TranslatorFactory:
    """Factory for creating translator instances."""

    _providers = {}

    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: type
    ) -> None:
        """Register a translator provider.

        Args:
            name: Provider name (google, deepl, local)
            provider_class: Translator subclass
        """
        cls._providers[name] = provider_class

    @classmethod
    def create(cls, config: TranslationConfig) -> Translator:
        """Create a translator instance based on config.

        Args:
            config: TranslationConfig with provider specification

        Returns:
            Translator instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_name = config.provider

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown translator provider: {provider_name}. "
                f"Available: {list(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_name]
        return provider_class(config)


# Register built-in providers
def _register_builtin_providers():
    """Register built-in translation providers."""
    from src.telegram_multi.translators.google import GoogleTranslator

    TranslatorFactory.register_provider("google", GoogleTranslator)

    # Placeholder for future providers
    # from src.telegram_multi.translators.deepl import DeepLTranslator
    # TranslatorFactory.register_provider("deepl", DeepLTranslator)
    #
    # from src.telegram_multi.translators.local import LocalTranslator
    # TranslatorFactory.register_provider("local", LocalTranslator)


_register_builtin_providers()
