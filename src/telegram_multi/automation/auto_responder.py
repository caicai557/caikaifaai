"""
Auto-responder engine for Telegram automation.

Contract:
- ResponseRule validates trigger, response_template, priority, enabled
- AutoResponder matches messages by priority
- Supports template variable rendering
- Logs all auto-replies
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from ..message_interceptor import Message
from .keyword_monitor import KeywordMonitor, KeywordRule


class ResponseRule(BaseModel):
    """Configuration for an auto-response rule."""

    trigger: str
    response_template: str
    priority: int = 0
    enabled: bool = True


class AutoResponder:
    """Auto-response engine with rule matching and template rendering."""

    def __init__(self, rules: List[ResponseRule]):
        """Initialize auto-responder with rules.

        Args:
            rules: List of ResponseRule instances
        """
        # Sort rules by priority (highest first)
        self.rules = sorted(rules, key=lambda x: x.priority, reverse=True)
        self.reply_log: List[Dict] = []

        # Build keyword monitor for matching
        keyword_rules = [
            KeywordRule(pattern=rule.trigger, is_regex=False)
            for rule in self.rules
            if rule.enabled
        ]
        self._monitor = KeywordMonitor(rules=keyword_rules)

    def match(self, message: Message) -> Optional[ResponseRule]:
        """Match message against rules by priority.

        Args:
            message: Message instance to check

        Returns:
            Highest priority matching ResponseRule or None
        """
        # Check matches using keyword monitor
        matched_keyword_rules = self._monitor.check(message.content)

        if not matched_keyword_rules:
            return None

        # Find highest priority enabled ResponseRule
        for rule in self.rules:
            if not rule.enabled:
                continue
            # Check if this rule's trigger matches
            for kw_rule in matched_keyword_rules:
                if kw_rule.pattern == rule.trigger:
                    return rule

        return None

    def render_response(self, rule: ResponseRule, message: Message) -> str:
        """Render response template with variables.

        Args:
            rule: ResponseRule with template
            message: Message providing context

        Returns:
            Rendered response string

        Supported variables:
            {sender_name}: Message sender name
            {time}: Message timestamp
            {content}: Message content
        """
        template = rule.response_template

        # Replace template variables
        variables = {
            "sender_name": message.sender or "Unknown",
            "time": message.timestamp or datetime.now().isoformat(),
            "content": message.content,
        }

        try:
            return template.format(**variables)
        except KeyError:
            # Gracefully handle missing variables
            return template

    def auto_reply(self, message: Message) -> Optional[str]:
        """Generate auto-reply for message.

        Args:
            message: Incoming message

        Returns:
            Rendered response string or None if no match

        Side effects:
            Logs reply to self.reply_log
        """
        matched_rule = self.match(message)

        if matched_rule is None:
            return None

        response = self.render_response(matched_rule, message)

        # Log the reply
        self.reply_log.append(
            {
                "trigger": matched_rule.trigger,
                "message_content": message.content,
                "response": response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return response
