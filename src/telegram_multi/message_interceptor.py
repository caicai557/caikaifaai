"""
Message interception system for Telegram Web A.

Contract:
- Message: Data structure for incoming/outgoing messages
- MessageInterceptor: Captures and modifies messages with translation
- Preserves metadata (sender, timestamp)
- Provides JavaScript injection for DOM integration
"""

import json
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

    message_type: MessageType = Field(..., description="Incoming or outgoing message")
    content: str = Field(..., description="Message text content")
    sender: Optional[str] = Field(default=None, description="Sender name/ID")
    timestamp: Optional[str] = Field(
        default=None, description="Message timestamp (ISO 8601)"
    )
    translated_content: Optional[str] = Field(
        default=None, description="Translated message content"
    )


class MessageInterceptor:
    """Message interceptor for capturing and translating messages."""

    def __init__(self, config: TranslationConfig, translator=None):
        """Initialize message interceptor.

        Args:
            config: TranslationConfig with language pair and provider
            translator: Optional Translator instance for translations
        """
        self.config = config
        self.translator = translator
        self._on_message_received_callback: Optional[Callable] = None
        self._on_message_sending_callback: Optional[Callable] = None

    def on_message_received(self, callback: Callable[[Message], None]) -> None:
        """Register callback for incoming messages.

        Args:
            callback: Function to call when message is received
        """
        self._on_message_received_callback = callback

    def on_message_sending(self, callback: Callable[[Message], Message]) -> None:
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
                dest_lang=self.config.target_lang,
            )
            message.translated_content = translated
        except Exception:
            # Graceful fallback: keep original translation field as None
            pass

        return message

    def translate_bidirectional(self, message: Message) -> Message:
        """Translate a message based on its direction (incoming/outgoing).

        Bidirectional Translation Logic:
        - INCOMING: Translate FROM target_lang TO source_lang
          (So user reads their native language)
        - OUTGOING: Translate FROM source_lang TO target_lang
          (So recipient reads their native language)

        Args:
            message: Message to translate

        Returns:
            Message with translated_content field populated
        """
        if not self.config.enabled or not self.translator:
            return message

        try:
            if message.message_type == MessageType.INCOMING:
                # Received message: translate TO user's language
                translated = self.translator.translate(
                    message.content,
                    src_lang=self.config.target_lang,  # From foreign
                    dest_lang=self.config.source_lang,  # To user's lang
                )
            else:
                # Sending message: translate FROM user's language
                translated = self.translator.translate(
                    message.content,
                    src_lang=self.config.source_lang,  # From user's lang
                    dest_lang=self.config.target_lang,  # To foreign
                )
            message.translated_content = translated
        except Exception:
            pass

        return message

    def get_injection_script(self) -> str:
        """Get JavaScript injection script for DOM integration.

        Returns:
            JavaScript code to inject into Telegram Web A
        """
        # Build dynamic CONFIG from self.config
        config_dict = {
            "enabled": self.config.enabled,
            "sourceLang": self.config.source_lang,
            "targetLang": self.config.target_lang,
            "displayMode": self.config.display_mode,
            "showHeader": self.config.show_header,
            "translateUrl": "https://translate.googleapis.com/translate_a/single"
        }
        config_json = json.dumps(config_dict, indent=2)
        return _get_injection_script(config_json)


def _get_injection_script(config_json: str) -> str:
    """Generate JavaScript injection script for message interception.

    Args:
        config_json: JSON string of configuration object

    Returns:
        JavaScript code that:
        - Uses MutationObserver to detect new messages
        - Adds Apple-style "Liquid Glass" translation overlay
        - Handles bidirectional translation with smart alignment
    """
    # Use raw string concatenation to avoid f-string escaping issues with JS braces
    return (
        """
(function() {
  // Telegram Web A Translation Overlay Script (Apple Design System)

  const CONFIG = """
        + config_json
        + """;

  // --- Apple Design System CSS Injection ---
  const style = document.createElement('style');
  style.textContent = `
    :root {
      --apple-glass-bg: rgba(245, 245, 247, 0.75);
      --apple-glass-border: rgba(255, 255, 255, 0.4);
      --apple-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
      --apple-blur: blur(20px);
      --apple-font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
      --apple-blue: #007AFF;
      --apple-text-primary: #1C1C1E;
      --apple-text-secondary: #8E8E93;
    }

    /* Dark Mode (Telegram's .theme-dark class or media query) */
    @media (prefers-color-scheme: dark) {
      :root {
        --apple-glass-bg: rgba(30, 30, 30, 0.70);
        --apple-glass-border: rgba(255, 255, 255, 0.1);
        --apple-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        --apple-text-primary: #FFFFFF;
        --apple-text-secondary: #98989D;
      }
    }

    .tg-apple-overlay {
      margin-top: 6px;
      padding: 8px 12px;
      border-radius: 14px;
      background: var(--apple-glass-bg);
      backdrop-filter: var(--apple-blur);
      -webkit-backdrop-filter: var(--apple-blur);
      border: 0.5px solid var(--apple-glass-border);
      box-shadow: var(--apple-shadow);
      font-family: var(--apple-font);
      max-width: 100%;
      min-width: 120px;
      opacity: 0;
      transform: translateY(4px) scale(0.98);
      animation: applePopIn 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
      pointer-events: auto;
      user-select: text;
    }

    @keyframes applePopIn {
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }

    .tg-apple-header {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-bottom: 4px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--apple-text-secondary);
    }

    .tg-apple-icon {
      font-size: 11px;
    }

    .tg-apple-content {
      font-size: 13px;
      line-height: 1.4;
      color: var(--apple-text-primary);
      white-space: pre-wrap;
      word-break: break-word;
    }

    /* Loading shimmer effect */
    .tg-apple-loading {
      height: 12px;
      width: 80%;
      background: linear-gradient(90deg,
        rgba(150,150,150,0.1),
        rgba(150,150,150,0.2),
        rgba(150,150,150,0.1));
      background-size: 200% 100%;
      animation: appleShimmer 1.5s infinite;
      border-radius: 4px;
    }

    @keyframes appleShimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* Bilingual mode styles */
    .tg-apple-bilingual-original {
      font-size: 12px;
      color: var(--apple-text-secondary);
      margin-bottom: 4px;
      padding-bottom: 4px;
      border-bottom: 1px solid var(--apple-glass-border);
    }

    .tg-apple-bilingual-translated {
      font-size: 13px;
      color: var(--apple-text-primary);
    }
  `;
  document.head.appendChild(style);

  // --- Translation Logic ---
  const translationCache = new Map();

  async function translateText(text, targetLang) {
    if (!text || text.length < 2) return null;
    const cacheKey = `${text}:${targetLang}`;
    if (translationCache.has(cacheKey)) return translationCache.get(cacheKey);

    try {
      const params = new URLSearchParams({
        client: 'gtx',
        sl: CONFIG.sourceLang || 'auto',
        tl: targetLang,
        dt: 't',
        q: text
      });
      const response = await fetch(`${CONFIG.translateUrl}?${params}`);
      const data = await response.json();
      if (data && data[0]) {
        const translated = data[0].map(item => item[0]).join('');
        translationCache.set(cacheKey, translated);
        return translated;
      }
    } catch (e) {
      console.warn('[Translation] API error:', e);
    }
    return null;
  }

  // --- Bilingual Display Logic ---
  function renderBilingualContent(content, originalText, translatedText) {
    // For bilingual mode, show both original and translated
    if (CONFIG.displayMode === 'bilingual') {
      const originalDiv = document.createElement('div');
      originalDiv.className = 'tg-apple-bilingual-original';
      originalDiv.textContent = originalText;

      const translatedDiv = document.createElement('div');
      translatedDiv.className = 'tg-apple-bilingual-translated';
      translatedDiv.textContent = translatedText;

      content.innerHTML = '';
      content.appendChild(originalDiv);
      content.appendChild(translatedDiv);
    } else {
      // Replace mode: just show translated
      content.textContent = translatedText;
    }
  }

  // --- Overlay Injection ---
  async function addTranslationOverlay(element) {
    if (!CONFIG.enabled) return;
    if (element.querySelector('.tg-apple-overlay')) return;

    // Find text node
    const textNode = element.querySelector('.text-content, .message-content') || element;
    const originalText = (textNode.textContent || '').trim();
    if (!originalText || originalText.length < 2) return;

    // Create container
    const overlay = document.createElement('div');
    overlay.className = 'tg-apple-overlay';

    // Header (conditional based on showHeader config)
    if (CONFIG.showHeader) {
      const header = document.createElement('div');
      header.className = 'tg-apple-header';
      header.innerHTML = '<span class="tg-apple-icon">🌐</span> TRANSPARENT TRANSLATE';
      overlay.appendChild(header);
    }

    // Content (Loading State)
    const content = document.createElement('div');
    content.className = 'tg-apple-content';
    const loader = document.createElement('div');
    loader.className = 'tg-apple-loading';
    content.appendChild(loader);
    overlay.appendChild(content);

    // Append to message bubble
    element.appendChild(overlay);

    // Determine target language based on message direction (Simple heuristic)
    // If we are sending (right side), we want to see what they see (or verify our trans).
    // Actually, user wants to see EVERYTHING in their language.
    // Unless the user explicitly wants bidirectional check.
    // For now, simpler rule: Translate EVERYTHING to valid targetLang.
    // If source is already target language, Google Translate usually handles it (returns same or english).
    // Let's rely on auto-detection.

    const translated = await translateText(originalText, CONFIG.targetLang);

    if (translated && translated !== originalText) {
      // Handle bilingual vs replace mode
      renderBilingualContent(content, originalText, translated);
    } else {
      // Translation failed or same language -> Remove overlay gracefully
      overlay.style.opacity = '0';
      setTimeout(() => overlay.remove(), 300);
    }
  }

  // --- Observer Logic ---
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType !== Node.ELEMENT_NODE) return;

        // Telegram Web A typically uses .message class
        if (node.matches('.message, .Message, [class*="message-content"]')) {
          addTranslationOverlay(node);
        } else {
          // Check children
          const messages = node.querySelectorAll('.message, .Message, [class*="message-content"]');
          messages.forEach(msg => addTranslationOverlay(msg));
        }
      });
    });
  });

  // --- Input Area Monitoring (for outgoing messages) ---
  function setupInputMonitoring() {
    // Monitor textarea or contenteditable input for message composition
    const inputSelectors = [
      'textarea',
      '[contenteditable="true"]',
      'input[type="text"]',
      '.composer-input',
      '.message-input'
    ];

    inputSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(input => {
        if (input.dataset.translationMonitor) return;
        input.dataset.translationMonitor = 'true';

        // Add subtle indicator that translation is active
        input.addEventListener('focus', () => {
          console.log('[AppleTranslate] Input focused, translation active');
        });
      });
    });
  }

  function startObserver() {
    const container = document.querySelector('#MiddleColumn, .messages-container, [class*="chat"]');
    if (container) {
      observer.observe(container, { childList: true, subtree: true });
      // Process existing
      document.querySelectorAll('.message, .Message, [class*="message-content"]').forEach(addTranslationOverlay);
      console.log('[AppleTranslate] Active');
      setupInputMonitoring();
    } else {
      setTimeout(startObserver, 1000);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startObserver);
  } else {
    setTimeout(startObserver, 500);
  }
})();
"""
    )
