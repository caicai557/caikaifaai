"""
Message interception system for Telegram Web A.

Contract:
- Message: Data structure for incoming/outgoing messages
- MessageInterceptor: Captures and modifies messages with translation
- Preserves metadata (sender, timestamp)
- Provides JavaScript injection for DOM integration
"""

from enum import Enum
from typing import Optional, Callable
from pydantic import BaseModel, Field, ConfigDict
from src.telegram_multi.config import TranslationConfig


class MessageType(str, Enum):
    """Message type enumeration."""

    INCOMING = "incoming"
    OUTGOING = "outgoing"


class Message(BaseModel):
    """Data structure for a single message."""

    model_config = ConfigDict(use_enum_values=False)

    message_type: MessageType = Field(
        ..., description="Incoming or outgoing message"
    )
    content: str = Field(..., description="Message text content")
    sender: Optional[str] = Field(
        default=None, description="Sender name/ID"
    )
    timestamp: Optional[str] = Field(
        default=None, description="Message timestamp (ISO 8601)"
    )
    translated_content: Optional[str] = Field(
        default=None, description="Translated message content"
    )


class MessageInterceptor:
    """Message interceptor for capturing and translating messages."""

    def __init__(
        self,
        config: TranslationConfig,
        translator=None
    ):
        """Initialize message interceptor.

        Args:
            config: TranslationConfig with language pair and provider
            translator: Optional Translator instance for translations
        """
        self.config = config
        self.translator = translator
        self._on_message_received_callback: Optional[Callable] = None
        self._on_message_sending_callback: Optional[Callable] = None

    def on_message_received(
        self,
        callback: Callable[[Message], None]
    ) -> None:
        """Register callback for incoming messages.

        Args:
            callback: Function to call when message is received
        """
        self._on_message_received_callback = callback

    def on_message_sending(
        self,
        callback: Callable[[Message], Message]
    ) -> None:
        """Register callback for outgoing messages.

        Args:
            callback: Function to call when message is about to send.
                     Can modify message and return it.
        """
        self._on_message_sending_callback = callback

    def translate_message(self, message: Message) -> Message:
        """Translate a message content.

        Args:
            message: Message to translate

        Returns:
            Message with translated_content field populated

        If translation is disabled, returns message unchanged.
        """
        if not self.config.enabled or not self.translator:
            return message

        try:
            translated = self.translator.translate(
                message.content,
                src_lang=self.config.source_lang,
                dest_lang=self.config.target_lang
            )
            message.translated_content = translated
        except Exception:
            # Graceful fallback: keep original translation field as None
            pass

        return message

    def get_injection_script(self) -> str:
        """Get JavaScript injection script for DOM integration.

        Returns:
            JavaScript code to inject into Telegram Web A
        """
        return _get_injection_script()


def _get_injection_script() -> str:
    """Generate JavaScript injection script for message interception.

    Returns:
        JavaScript code that:
        - Uses MutationObserver to detect new messages
        - Adds translation overlay to messages
        - Monitors textarea for outgoing messages
    """
    return '''
(function() {
  // Message interception script for Telegram Web A

  const messageConfig = {
    enabled: true,
    sourceLanguage: 'auto',
    targetLanguage: 'zh-CN'
  };

  // Function to add translation overlay to message element
  function addTranslationOverlay(element, originalText) {
    if (!messageConfig.enabled || !originalText) return;

    try {
      const translationDiv = document.createElement('div');
      translationDiv.className = 'telegram-translation-overlay';
      translationDiv.style.cssText = `
        background-color: #f0f0f0;
        border-top: 1px solid #ccc;
        padding: 4px 8px;
        margin-top: 4px;
        font-size: 0.9em;
        color: #666;
      `;
      translationDiv.textContent = '[Translation: ]';

      element.appendChild(translationDiv);
    } catch (e) {
      console.warn('Failed to add translation overlay:', e);
    }
  }

  // MutationObserver to detect new messages
  const messageObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(function(node) {
          // Look for message containers
          if (node.nodeType === Node.ELEMENT_NODE) {
            const messageElements = node.querySelectorAll(
              '[class*="message"], [class*="chat"], [class*="text"]'
            );
            messageElements.forEach(function(element) {
              const textContent = element.textContent || element.innerText;
              if (textContent && !element.querySelector('.telegram-translation-overlay')) {
                addTranslationOverlay(element, textContent);
              }
            });
          }
        });
      }
    });
  });

  // Start observing message container
  const chatContainer = document.querySelector(
    '[class*="messages"], [class*="chat-container"], [role="log"]'
  );

  if (chatContainer) {
    messageObserver.observe(chatContainer, {
      childList: true,
      subtree: true,
      characterData: false
    });
  }

  // Monitor textarea/input for outgoing messages
  const textareaObserver = new MutationObserver(function(mutations) {
    const textarea = document.querySelector(
      'textarea[class*="input"], input[class*="message"], [contenteditable="true"]'
    );
    if (textarea) {
      // Message being composed - could add translation here
    }
  });

  // Observe document for changes
  textareaObserver.observe(document.body, {
    subtree: true,
    childList: true
  });

  console.log('Telegram message interception script loaded');
})();
'''
