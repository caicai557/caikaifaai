"""
Keyword monitor for Telegram automation.

Contract:
- KeywordRule validates pattern, supports regex/exact match
- KeywordMonitor checks text against multiple rules
- Supports case-insensitive matching and callbacks
- Pre-compiles patterns for efficiency
"""

import re
from typing import Callable, List, Optional
from pydantic import BaseModel, ConfigDict
from ..message_interceptor import Message


class KeywordRule(BaseModel):
    """Configuration for a single keyword rule."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    pattern: str
    is_regex: bool = False
    ignore_case: bool = True
    callback: Optional[Callable[[Message], None]] = None


class KeywordMonitor:
    """Monitors text for keywords and triggers callbacks."""

    # Emoji removal pattern (common emoji ranges only)
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map
        "\U0001f1e0-\U0001f1ff"  # flags
        "\U00002600-\U000027bf"  # misc symbols
        "]+",
        flags=re.UNICODE,
    )

    def __init__(self, rules: List[KeywordRule]):
        """Initialize keyword monitor with rules.

        Args:
            rules: List of KeywordRule instances
        """
        self.rules = rules
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> List[re.Pattern]:
        """Pre-compile regex patterns for efficiency.

        Returns:
            List of compiled regex Pattern objects
        """
        compiled = []
        for rule in self.rules:
            if rule.is_regex:
                # Already regex, compile directly
                flags = re.IGNORECASE if rule.ignore_case else 0
                compiled.append(re.compile(rule.pattern, flags))
            else:
                # Escape special regex chars for literal match
                escaped = re.escape(rule.pattern)
                flags = re.IGNORECASE if rule.ignore_case else 0
                compiled.append(re.compile(escaped, flags))
        return compiled

    def check(self, text: str) -> List[KeywordRule]:
        """Check text against all keyword rules.

        Args:
            text: Text to check

        Returns:
            List of KeywordRule objects that matched
        """
        if not text:
            return []

        # Remove emoji interference (allows "价💰格" to match "价格")
        text_normalized = self.EMOJI_PATTERN.sub("", text)

        matches = []
        for rule, pattern in zip(self.rules, self._compiled_patterns):
            if pattern.search(text_normalized):
                matches.append(rule)
        return matches

    def on_match(self, message: Message) -> None:
        """Check message content and trigger callbacks for matches.

        Args:
            message: Message instance to check
        """
        matched_rules = self.check(message.content)
        for rule in matched_rules:
            if rule.callback:
                rule.callback(message)
