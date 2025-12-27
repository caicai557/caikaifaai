"""
Tests for KeywordMonitor (Phase 7.1.2).

Contract:
- KeywordRule supports pattern, is_regex, ignore_case, callback
- KeywordMonitor checks text against multiple keyword rules
- Supports exact match and regex match
- Triggers callbacks when keywords are detected
- Case-insensitive matching and emoji handling
"""

from src.telegram_multi.automation.keyword_monitor import KeywordRule, KeywordMonitor
from src.telegram_multi.message_interceptor import Message, MessageType


class TestKeywordRule:
    """Contract tests for KeywordRule."""

    def test_keyword_rule_defaults(self):
        """Contract: KeywordRule has sensible defaults."""
        rule = KeywordRule(pattern="价格")
        assert rule.pattern == "价格"
        assert rule.is_regex is False
        assert rule.ignore_case is True
        assert rule.callback is None

    def test_keyword_rule_exact_match_config(self):
        """AC1.1: Configure exact match rule."""
        rule = KeywordRule(pattern="合作", is_regex=False)
        assert rule.pattern == "合作"
        assert rule.is_regex is False

    def test_keyword_rule_regex_config(self):
        """AC1.1: Configure regex match rule."""
        rule = KeywordRule(pattern=r"\d+元", is_regex=True)
        assert rule.pattern == r"\d+元"
        assert rule.is_regex is True

    def test_keyword_rule_with_callback(self):
        """AC1.2: KeywordRule supports callback configuration."""

        def mock_callback(msg):
            pass

        rule = KeywordRule(pattern="test", callback=mock_callback)
        assert rule.callback == mock_callback

    def test_keyword_rule_case_sensitive_config(self):
        """AC1.4: Support case sensitivity configuration."""
        rule_insensitive = KeywordRule(pattern="VIP", ignore_case=True)
        assert rule_insensitive.ignore_case is True

        rule_sensitive = KeywordRule(pattern="VIP", ignore_case=False)
        assert rule_sensitive.ignore_case is False


class TestKeywordMonitor:
    """Contract tests for KeywordMonitor."""

    def test_monitor_initialization(self):
        """Contract: KeywordMonitor accepts list of KeywordRule."""
        rules = [KeywordRule(pattern="test")]
        monitor = KeywordMonitor(rules=rules)
        assert monitor.rules == rules

    def test_monitor_exact_match_single_keyword(self):
        """AC1.1: Detect single exact match keyword."""
        rules = [KeywordRule(pattern="价格", is_regex=False)]
        monitor = KeywordMonitor(rules=rules)

        matches = monitor.check("请问一下价格是多少？")
        assert len(matches) == 1
        assert matches[0].pattern == "价格"

    def test_monitor_exact_match_no_match(self):
        """Contract: Return empty list when no match."""
        rules = [KeywordRule(pattern="价格")]
        monitor = KeywordMonitor(rules=rules)

        matches = monitor.check("你好，请问在吗？")
        assert len(matches) == 0

    def test_monitor_multiple_keywords(self):
        """AC1.1: Support multiple keywords."""
        rules = [KeywordRule(pattern="价格"), KeywordRule(pattern="合作")]
        monitor = KeywordMonitor(rules=rules)

        # Match first keyword
        matches1 = monitor.check("这个价格不错")
        assert len(matches1) == 1
        assert matches1[0].pattern == "价格"

        # Match second keyword
        matches2 = monitor.check("期待合作")
        assert len(matches2) == 1
        assert matches2[0].pattern == "合作"

        # Match both keywords
        matches3 = monitor.check("价格合适就合作")
        assert len(matches3) == 2

    def test_monitor_regex_match(self):
        """AC1.1: Support regex pattern matching."""
        rules = [
            KeywordRule(pattern=r"1[3-9]\d{9}", is_regex=True)  # Chinese phone number
        ]
        monitor = KeywordMonitor(rules=rules)

        matches = monitor.check("联系我：13812345678")
        assert len(matches) == 1

        no_matches = monitor.check("联系我：12345678")
        assert len(no_matches) == 0

    def test_monitor_ignore_case(self):
        """AC1.4: Support case-insensitive matching."""
        rules = [KeywordRule(pattern="VIP", ignore_case=True)]
        monitor = KeywordMonitor(rules=rules)

        assert len(monitor.check("vip用户")) == 1
        assert len(monitor.check("Vip用户")) == 1
        assert len(monitor.check("VIP用户")) == 1

    def test_monitor_case_sensitive(self):
        """AC1.4: Support case-sensitive matching when configured."""
        rules = [KeywordRule(pattern="VIP", ignore_case=False)]
        monitor = KeywordMonitor(rules=rules)

        assert len(monitor.check("VIP用户")) == 1
        assert len(monitor.check("vip用户")) == 0

    def test_monitor_emoji_handling(self):
        """AC1.4: Handle emoji interference."""
        rules = [KeywordRule(pattern="价格")]
        monitor = KeywordMonitor(rules=rules)

        # Emoji between characters should still match
        matches = monitor.check("价💰格是多少")
        assert len(matches) == 1

    def test_monitor_callback_trigger(self):
        """AC1.2, AC1.3: Trigger callback with correct message data."""
        callback_called = False
        captured_msg = None

        def on_keyword_found(msg: Message):
            nonlocal callback_called, captured_msg
            callback_called = True
            captured_msg = msg

        rules = [KeywordRule(pattern="紧急", callback=on_keyword_found)]
        monitor = KeywordMonitor(rules=rules)

        test_message = Message(
            message_type=MessageType.INCOMING,
            content="发现紧急情况",
            sender="UserA",
            timestamp="2025-12-27T10:00:00",
        )

        monitor.on_match(test_message)

        assert callback_called is True
        assert captured_msg is not None
        assert captured_msg.content == "发现紧急情况"
        assert captured_msg.sender == "UserA"
        assert captured_msg.timestamp == "2025-12-27T10:00:00"

    def test_monitor_multiple_callbacks(self):
        """AC1.2: Support multiple rules with different callbacks."""
        callback1_called = False
        callback2_called = False

        def callback1(msg):
            nonlocal callback1_called
            callback1_called = True

        def callback2(msg):
            nonlocal callback2_called
            callback2_called = True

        rules = [
            KeywordRule(pattern="关键词1", callback=callback1),
            KeywordRule(pattern="关键词2", callback=callback2),
        ]
        monitor = KeywordMonitor(rules=rules)

        msg1 = Message(message_type=MessageType.INCOMING, content="包含关键词1的消息")
        monitor.on_match(msg1)
        assert callback1_called is True
        assert callback2_called is False

    def test_monitor_empty_rules(self):
        """Contract: Empty rules list returns no matches."""
        monitor = KeywordMonitor(rules=[])
        assert len(monitor.check("任意内容")) == 0

    def test_monitor_empty_text(self):
        """Contract: Empty text returns no matches."""
        rules = [KeywordRule(pattern="test")]
        monitor = KeywordMonitor(rules=rules)
        assert len(monitor.check("")) == 0

    def test_monitor_special_regex_chars_as_literal(self):
        """Contract: Special regex chars treated as literal when is_regex=False."""
        rules = [KeywordRule(pattern=".*", is_regex=False)]
        monitor = KeywordMonitor(rules=rules)

        # Should match literal ".*"
        assert len(monitor.check(".*")) == 1
        # Should NOT match anything (not regex)
        assert len(monitor.check("anything")) == 0

    def test_monitor_precompile_patterns(self):
        """Contract: Patterns are pre-compiled for efficiency."""
        rules = [
            KeywordRule(pattern="test1"),
            KeywordRule(pattern=r"\d+", is_regex=True),
        ]
        monitor = KeywordMonitor(rules=rules)

        # Should have compiled patterns
        assert hasattr(monitor, "_compiled_patterns")
        assert monitor._compiled_patterns is not None
