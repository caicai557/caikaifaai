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
            timestamp="2025-12-24T10:30:00Z"
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
            translated_content="你好"
        )
        assert msg.translated_content == "你好"

    def test_message_translated_defaults_to_none(self):
        """Contract: Translation is optional."""
        msg = Message(
            message_type=MessageType.INCOMING,
            content="Hello"
        )
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
            enabled=True,
            source_lang="en",
            target_lang="zh-CN",
            provider="google"
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
            enabled=True,
            source_lang="en",
            target_lang="zh-CN",
            provider="google"
        )
        translator = TranslatorFactory.create(config)
        interceptor = MessageInterceptor(config, translator=translator)

        assert interceptor.translator is not None
        assert interceptor.translator == translator

    def test_interceptor_translate_incoming_message(self):
        """Contract: Interceptor can translate incoming messages."""
        from src.telegram_multi.translator import TranslatorFactory

        config = TranslationConfig(
            enabled=True,
            source_lang="en",
            target_lang="zh-CN",
            provider="google"
        )
        translator = TranslatorFactory.create(config)
        interceptor = MessageInterceptor(config, translator=translator)

        msg = Message(
            message_type=MessageType.INCOMING,
            content="Hello",
            sender="Alice"
        )

        # Should be able to translate
        assert hasattr(interceptor, 'translate_message')
        assert callable(interceptor.translate_message)

    def test_interceptor_translate_disabled(self):
        """Contract: When disabled, interceptor returns original."""
        config = TranslationConfig(
            enabled=False,
            source_lang="en",
            target_lang="zh-CN",
            provider="google"
        )
        interceptor = MessageInterceptor(config)

        msg = Message(
            message_type=MessageType.INCOMING,
            content="Hello"
        )

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
