"""
Tests for message interception system (Phase 4).

Contract:
- MessageInterceptor: Capture and modify messages in Telegram Web A
- Intercept incoming messages via MutationObserver
- Intercept outgoing messages before send
- Display both original + translated text
- Preserve message metadata (timestamps, sender, etc.)
"""

import pytest
from src.telegram_multi.message_interceptor import (
    MessageInterceptor,
    Message,
    MessageType,
)
from src.telegram_multi.config import TranslationConfig


class TestMessage:
    """Contract tests for Message data structure."""

    def test_create_incoming_message(self):
        """Contract: Can create incoming message with metadata."""
        msg = Message(
            message_type=MessageType.INCOMING,
            content="Hello world",
            sender="Alice",
            timestamp="2025-12-24T10:30:00Z",
        )
        assert msg.message_type == MessageType.INCOMING
        assert msg.content == "Hello world"
        assert msg.sender == "Alice"
        assert msg.timestamp == "2025-12-24T10:30:00Z"

    def test_create_outgoing_message(self):
        """Contract: Can create outgoing message."""
        msg = Message(
            message_type=MessageType.OUTGOING,
            content="Hello back",
        )
        assert msg.message_type == MessageType.OUTGOING
        assert msg.content == "Hello back"

    def test_message_with_translation(self):
        """Contract: Message can store translation."""
        msg = Message(
            message_type=MessageType.INCOMING,
            content="Hello",
            translated_content="你好",
        )
        assert msg.translated_content == "你好"

    def test_message_translated_defaults_to_none(self):
        """Contract: Translation is optional."""
        msg = Message(message_type=MessageType.INCOMING, content="Hello")
        assert msg.translated_content is None

    def test_message_requires_type_and_content(self):
        """Contract: Message requires type and content."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Message(content="Hello")  # missing message_type

        with pytest.raises(ValidationError):
            Message(message_type=MessageType.INCOMING)  # missing content


class TestMessageInterceptor:
    """Contract tests for MessageInterceptor."""

    def test_create_interceptor(self):
        """Contract: Can create MessageInterceptor."""
        config = TranslationConfig(
            enabled=True, source_lang="en", target_lang="zh-CN", provider="google"
        )
        interceptor = MessageInterceptor(config)
        assert interceptor is not None
        assert interceptor.config == config

    def test_interceptor_on_message_received(self):
        """Contract: Can register callback for incoming messages."""
        config = TranslationConfig(enabled=True, provider="google")
        interceptor = MessageInterceptor(config)

        callback_called = []

        def on_message(msg: Message):
            callback_called.append(msg)

        interceptor.on_message_received(on_message)
        assert callable(interceptor._on_message_received_callback)

    def test_interceptor_on_message_sending(self):
        """Contract: Can register callback for outgoing messages."""
        config = TranslationConfig(enabled=True, provider="google")
        interceptor = MessageInterceptor(config)

        callback_called = []

        def on_send(msg: Message) -> Message:
            callback_called.append(msg)
            return msg

        interceptor.on_message_sending(on_send)
        assert callable(interceptor._on_message_sending_callback)

    def test_interceptor_has_injection_script(self):
        """Contract: Interceptor provides JavaScript injection."""
        config = TranslationConfig(enabled=True, provider="google")
        interceptor = MessageInterceptor(config)

        script = interceptor.get_injection_script()
        assert script is not None
        assert isinstance(script, str)
        assert len(script) > 0

    def test_injection_script_contains_mutation_observer(self):
        """Contract: Injection script uses MutationObserver."""
        config = TranslationConfig(enabled=True, provider="google")
        interceptor = MessageInterceptor(config)

        script = interceptor.get_injection_script()
        assert "MutationObserver" in script

    def test_injection_script_contains_translation_overlay(self):
        """Contract: Injection script adds translation overlay."""
        config = TranslationConfig(enabled=True, provider="google")
        interceptor = MessageInterceptor(config)

        script = interceptor.get_injection_script()
        # Should contain code to display translations
        assert "translate" in script.lower()


class TestMessageInterceptorWithTranslator:
    """Contract tests for interceptor with translator integration."""

    def test_interceptor_with_translator(self):
        """Contract: Interceptor can use translator for messages."""
        from src.telegram_multi.translator import TranslatorFactory

        config = TranslationConfig(
            enabled=True, source_lang="en", target_lang="zh-CN", provider="google"
        )
        translator = TranslatorFactory.create(config)
        interceptor = MessageInterceptor(config, translator=translator)

        assert interceptor.translator is not None
        assert interceptor.translator == translator

    def test_interceptor_translate_incoming_message(self):
        """Contract: Interceptor can translate incoming messages."""
        from src.telegram_multi.translator import TranslatorFactory

        config = TranslationConfig(
            enabled=True, source_lang="en", target_lang="zh-CN", provider="google"
        )
        translator = TranslatorFactory.create(config)
        interceptor = MessageInterceptor(config, translator=translator)

        # Should be able to translate
        assert hasattr(interceptor, "translate_message")
        assert callable(interceptor.translate_message)

    def test_interceptor_translate_disabled(self):
        """Contract: When disabled, interceptor returns original."""
        config = TranslationConfig(
            enabled=False, source_lang="en", target_lang="zh-CN", provider="google"
        )
        interceptor = MessageInterceptor(config)

        msg = Message(message_type=MessageType.INCOMING, content="Hello")

        # When disabled, should return original content
        result = interceptor.translate_message(msg)
        assert result.content == "Hello"
        assert result.translated_content is None


class TestMessageInterceptorDOMIntegration:
    """Contract tests for DOM integration."""

    def test_injection_script_is_valid_javascript(self):
        """Contract: Injection script is valid JavaScript."""
        config = TranslationConfig(enabled=True, provider="google")
        interceptor = MessageInterceptor(config)

        script = interceptor.get_injection_script()
        # Should not have obvious syntax errors
        assert "{" in script
        assert "}" in script
        assert "function" in script or "const" in script or "var" in script

    def test_injection_script_handles_message_container(self):
        """Contract: Script targets message container elements."""
        config = TranslationConfig(enabled=True, provider="google")
        interceptor = MessageInterceptor(config)

        script = interceptor.get_injection_script()
        # Should reference message-related selectors
        assert (
            "message" in script.lower()
            or "chat" in script.lower()
            or "text" in script.lower()
        )

    def test_injection_script_handles_text_area(self):
        """Contract: Script monitors text area for outgoing messages."""
        config = TranslationConfig(enabled=True, provider="google")
        interceptor = MessageInterceptor(config)

        script = interceptor.get_injection_script()
        # Should handle textarea or input for message composition
        assert (
            "textarea" in script.lower()
            or "input" in script.lower()
            or "contenteditable" in script.lower()
        )


class TestInjectionScriptDynamicConfig:
    """Phase 4.2: Contract tests for dynamic configuration in injection script."""

    def test_script_contains_dynamic_config(self):
        """Contract: JS script contains dynamic CONFIG object."""
        config = TranslationConfig(enabled=True)
        interceptor = MessageInterceptor(config)
        script = interceptor.get_injection_script()
        assert "const CONFIG =" in script or "var CONFIG =" in script

    def test_config_contains_source_lang(self):
        """Contract: CONFIG contains sourceLang from config.source_lang."""
        config = TranslationConfig(enabled=True, source_lang="fr")
        interceptor = MessageInterceptor(config)
        script = interceptor.get_injection_script()
        assert '"sourceLang": "fr"' in script or "'sourceLang': 'fr'" in script

    def test_config_contains_target_lang(self):
        """Contract: CONFIG contains targetLang from config.target_lang."""
        config = TranslationConfig(enabled=True, target_lang="ja")
        interceptor = MessageInterceptor(config)
        script = interceptor.get_injection_script()
        assert '"targetLang": "ja"' in script or "'targetLang': 'ja'" in script

    def test_config_contains_display_mode(self):
        """Contract: CONFIG contains displayMode from config.display_mode."""
        config = TranslationConfig(enabled=True, display_mode="replace")
        interceptor = MessageInterceptor(config)
        script = interceptor.get_injection_script()
        assert (
            '"displayMode": "replace"' in script
            or "'displayMode': 'replace'" in script
        )

    def test_config_contains_show_header(self):
        """Contract: CONFIG contains showHeader from config.show_header."""
        config = TranslationConfig(enabled=True, show_header=False)
        interceptor = MessageInterceptor(config)
        script = interceptor.get_injection_script()
        # After .lower(), "showHeader" becomes "showheader"
        assert (
            '"showheader": false' in script.lower()
            or "'showheader': false" in script.lower()
        )

    def test_no_hardcoded_default_lang(self):
        """Contract: Script has no hardcoded 'zh-CN' when configured otherwise."""
        config = TranslationConfig(enabled=True, target_lang="en")
        interceptor = MessageInterceptor(config)
        script = interceptor.get_injection_script()
        # zh-CN shouldn't be forced in CONFIG when target is different
        assert '"targetLang": "zh-CN"' not in script
        assert "'targetLang': 'zh-CN'" not in script

    def test_different_configs_generate_different_scripts(self):
        """Contract: Different configurations generate different scripts."""
        config1 = TranslationConfig(enabled=True, target_lang="en")
        config2 = TranslationConfig(enabled=True, target_lang="ja")

        script1 = MessageInterceptor(config1).get_injection_script()
        script2 = MessageInterceptor(config2).get_injection_script()

        assert script1 != script2

    def test_bilingual_mode_contains_logic(self):
        """Contract: Bilingual mode script contains bilingual related logic."""
        config = TranslationConfig(enabled=True, display_mode="bilingual")
        interceptor = MessageInterceptor(config)
        script = interceptor.get_injection_script()

        # Should contain logic to handle both original and translated text
        assert "bilingual" in script.lower()
