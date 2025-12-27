"""
Tests for AutoResponder (Phase 7.1.4).

Contract:
- ResponseRule supports trigger, response_template, priority, enabled
- AutoResponder matches messages against rules by priority
- Supports template variable rendering ({sender_name}, {time})
- Supports disabling individual rules
- Logs all auto-replies
"""

from src.telegram_multi.automation.auto_responder import ResponseRule, AutoResponder
from src.telegram_multi.message_interceptor import Message, MessageType


class TestResponseRule:
    """Contract tests for ResponseRule."""

    def test_response_rule_defaults(self):
        """Contract: ResponseRule has sensible defaults."""
        rule = ResponseRule(trigger="帮助", response_template="请问有什么可以帮您？")
        assert rule.trigger == "帮助"
        assert rule.response_template == "请问有什么可以帮您？"
        assert rule.priority == 0
        assert rule.enabled is True

    def test_response_rule_with_priority(self):
        """AC3.3: Support priority configuration."""
        rule = ResponseRule(trigger="VIP", response_template="VIP用户您好", priority=10)
        assert rule.priority == 10

    def test_response_rule_disabled(self):
        """AC3.4: Support disabling rules."""
        rule = ResponseRule(trigger="测试", response_template="测试回复", enabled=False)
        assert rule.enabled is False


class TestAutoResponder:
    """Contract tests for AutoResponder."""

    def test_auto_responder_initialization(self):
        """Contract: AutoResponder accepts list of ResponseRule."""
        rules = [ResponseRule(trigger="hi", response_template="Hello")]
        responder = AutoResponder(rules=rules)
        assert responder.rules == rules

    def test_match_single_rule(self):
        """AC3.1: Match single rule."""
        rules = [ResponseRule(trigger="价格", response_template="请联系客服")]
        responder = AutoResponder(rules=rules)

        msg = Message(message_type=MessageType.INCOMING, content="请问价格是多少？")

        matched = responder.match(msg)
        assert matched is not None
        assert matched.trigger == "价格"

    def test_match_no_rule(self):
        """Contract: Return None when no rule matches."""
        rules = [ResponseRule(trigger="价格", response_template="请联系客服")]
        responder = AutoResponder(rules=rules)

        msg = Message(message_type=MessageType.INCOMING, content="你好")

        matched = responder.match(msg)
        assert matched is None

    def test_match_multiple_rules_by_priority(self):
        """AC3.3: Match highest priority rule when multiple match."""
        rules = [
            ResponseRule(trigger="VIP", response_template="VIP客户", priority=10),
            ResponseRule(trigger="价格", response_template="普通价格", priority=5),
            ResponseRule(trigger="VIP", response_template="VIP优先", priority=20),
        ]
        responder = AutoResponder(rules=rules)

        msg = Message(message_type=MessageType.INCOMING, content="VIP价格")

        matched = responder.match(msg)
        assert matched is not None
        assert matched.priority == 20
        assert matched.response_template == "VIP优先"

    def test_match_ignores_disabled_rules(self):
        """AC3.4: Ignore disabled rules."""
        rules = [
            ResponseRule(trigger="测试", response_template="测试回复", enabled=False),
            ResponseRule(trigger="测试", response_template="启用回复", enabled=True),
        ]
        responder = AutoResponder(rules=rules)

        msg = Message(message_type=MessageType.INCOMING, content="这是测试消息")

        matched = responder.match(msg)
        assert matched is not None
        assert matched.response_template == "启用回复"

    def test_render_response_simple(self):
        """AC3.2: Render simple template without variables."""
        rule = ResponseRule(trigger="hi", response_template="Hello, welcome!")
        responder = AutoResponder(rules=[rule])

        msg = Message(message_type=MessageType.INCOMING, content="hi", sender="Alice")

        response = responder.render_response(rule, msg)
        assert response == "Hello, welcome!"

    def test_render_response_with_sender_name(self):
        """AC3.2: Render template with {sender_name} variable."""
        rule = ResponseRule(
            trigger="hi", response_template="Hello {sender_name}, welcome!"
        )
        responder = AutoResponder(rules=[rule])

        msg = Message(message_type=MessageType.INCOMING, content="hi", sender="Alice")

        response = responder.render_response(rule, msg)
        assert response == "Hello Alice, welcome!"

    def test_render_response_with_time(self):
        """AC3.2: Render template with {time} variable."""
        rule = ResponseRule(trigger="时间", response_template="当前时间: {time}")
        responder = AutoResponder(rules=[rule])

        msg = Message(
            message_type=MessageType.INCOMING,
            content="现在几点",
            timestamp="2025-12-27T10:30:00",
        )

        response = responder.render_response(rule, msg)
        assert "2025-12-27T10:30:00" in response

    def test_render_response_with_content(self):
        """AC3.2: Render template with {content} variable."""
        rule = ResponseRule(trigger="复读", response_template="你说: {content}")
        responder = AutoResponder(rules=[rule])

        msg = Message(message_type=MessageType.INCOMING, content="复读 Hello World")

        response = responder.render_response(rule, msg)
        assert "Hello World" in response

    def test_render_response_missing_variable(self):
        """Contract: Gracefully handle missing variables."""
        rule = ResponseRule(trigger="hi", response_template="Hello {sender_name}")
        responder = AutoResponder(rules=[rule])

        msg = Message(
            message_type=MessageType.INCOMING,
            content="hi",
            sender=None,  # Missing sender
        )

        response = responder.render_response(rule, msg)
        # Should not crash, replace with empty or "Unknown"
        assert "Hello" in response

    def test_auto_reply_returns_rendered_response(self):
        """Contract: auto_reply returns rendered response when rule matches."""
        rules = [
            ResponseRule(
                trigger="帮助",
                response_template="您好 {sender_name}，请问有什么可以帮您？",
            )
        ]
        responder = AutoResponder(rules=rules)

        msg = Message(
            message_type=MessageType.INCOMING, content="我需要帮助", sender="Bob"
        )

        response = responder.auto_reply(msg)
        assert response is not None
        assert "Bob" in response
        assert "请问有什么可以帮您" in response

    def test_auto_reply_returns_none_when_no_match(self):
        """Contract: auto_reply returns None when no rule matches."""
        rules = [ResponseRule(trigger="帮助", response_template="请问有什么可以帮您？")]
        responder = AutoResponder(rules=rules)

        msg = Message(message_type=MessageType.INCOMING, content="你好")

        response = responder.auto_reply(msg)
        assert response is None

    def test_auto_reply_empty_rules(self):
        """Contract: Empty rules list returns None."""
        responder = AutoResponder(rules=[])

        msg = Message(message_type=MessageType.INCOMING, content="任意内容")

        response = responder.auto_reply(msg)
        assert response is None

    def test_responder_logs_auto_replies(self):
        """AC3.5: Log all auto-replies."""
        rules = [ResponseRule(trigger="测试", response_template="测试回复")]
        responder = AutoResponder(rules=rules)

        msg = Message(message_type=MessageType.INCOMING, content="这是测试")

        responder.auto_reply(msg)

        # Should have reply_log attribute
        assert hasattr(responder, "reply_log")
        assert len(responder.reply_log) == 1
        assert responder.reply_log[0]["trigger"] == "测试"

    def test_responder_priority_sorting(self):
        """Contract: Rules are sorted by priority in descending order."""
        rules = [
            ResponseRule(trigger="A", response_template="A", priority=5),
            ResponseRule(trigger="B", response_template="B", priority=20),
            ResponseRule(trigger="C", response_template="C", priority=10),
        ]
        responder = AutoResponder(rules=rules)

        # Rules should be sorted: B(20), C(10), A(5)
        assert responder.rules[0].priority == 20
        assert responder.rules[1].priority == 10
        assert responder.rules[2].priority == 5
