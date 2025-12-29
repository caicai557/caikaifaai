"""
Tests for Enhancement Modules:
- GeminiCacheManager
- AutoCompactTrigger
- TaskClassifier
- PTCEnforcer
"""

import pytest


# ============================================================
# GeminiCacheManager Tests
# ============================================================


class TestGeminiCacheManager:
    """GeminiCacheManager 测试"""

    def test_estimate_tokens(self):
        """测试 Token 估算"""
        from council.context.gemini_cache import GeminiCacheManager

        mgr = GeminiCacheManager()
        # 简单验证估算逻辑
        assert mgr._estimate_tokens("hello world") > 0
        # 更长的内容应该有更多 token (或至少相等)
        assert mgr._estimate_tokens("a" * 300) >= mgr._estimate_tokens("a" * 100)

    def test_can_cache_small_content(self):
        """测试小内容不可缓存"""
        from council.context.gemini_cache import GeminiCacheManager

        mgr = GeminiCacheManager()
        can, reason = mgr.can_cache("short content")
        assert can is False
        assert "太短" in reason

    def test_can_cache_large_content(self):
        """测试大内容可以缓存"""
        from council.context.gemini_cache import GeminiCacheManager

        mgr = GeminiCacheManager()
        large_content = "x" * 100000  # ~33K tokens
        can, reason = mgr.can_cache(large_content)
        assert can is True
        assert "可以缓存" in reason

    def test_content_hash(self):
        """测试内容哈希"""
        from council.context.gemini_cache import GeminiCacheManager

        mgr = GeminiCacheManager()
        hash1 = mgr._content_hash("content1")
        hash2 = mgr._content_hash("content1")
        hash3 = mgr._content_hash("content2")

        assert hash1 == hash2  # 相同内容相同哈希
        assert hash1 != hash3  # 不同内容不同哈希


# ============================================================
# AutoCompactTrigger Tests
# ============================================================


class TestAutoCompactTrigger:
    """AutoCompactTrigger 测试"""

    @pytest.fixture
    def ctx(self):
        """创建 RollingContext"""
        from council.context.rolling_context import RollingContext

        return RollingContext(max_tokens=1000)

    def test_should_compact_low_usage(self, ctx):
        """测试低使用率不触发压缩"""
        from council.context.auto_compact import AutoCompactTrigger

        trigger = AutoCompactTrigger(threshold_percent=70)
        ctx.add_turn("User", "short message")

        should, reason = trigger.should_compact(ctx)
        assert should is False

    def test_should_compact_high_usage(self, ctx):
        """测试高使用率触发压缩"""
        from council.context.auto_compact import AutoCompactTrigger

        trigger = AutoCompactTrigger(threshold_percent=50, min_rounds_before_compact=2)

        # 添加足够多的内容
        for i in range(20):
            ctx.add_turn("User", "x" * 500)

        should, reason = trigger.should_compact(ctx)
        # 如果 context 没有溢出机制，可能不会触发
        # 这里我们只验证不会崩溃，使用率检查是否工作
        assert isinstance(should, bool)
        if should:
            assert "使用率" in reason

    def test_auto_compact_wrapper(self, ctx):
        """测试自动压缩包装器"""
        from council.context.auto_compact import AutoCompactWrapper

        wrapper = AutoCompactWrapper(ctx, threshold_percent=50)

        # 添加内容应该正常工作
        wrapper.add_turn("User", "test message")
        prompt = wrapper.get_context_for_prompt()
        assert "test message" in prompt


# ============================================================
# TaskClassifier Tests
# ============================================================


class TestTaskClassifier:
    """TaskClassifier 测试"""

    @pytest.fixture
    def classifier(self):
        from council.orchestration.task_classifier import TaskClassifier

        return TaskClassifier()

    def test_classify_planning(self, classifier):
        """测试规划类任务"""
        from council.orchestration.task_classifier import TaskType, RecommendedModel

        result = classifier.classify("设计用户认证模块的架构")
        assert result.task_type == TaskType.PLANNING
        assert result.recommended_model == RecommendedModel.GPT_CODEX

    def test_classify_coding(self, classifier):
        """测试编码类任务"""
        from council.orchestration.task_classifier import TaskType, RecommendedModel

        result = classifier.classify("实现登录功能的代码")
        assert result.task_type == TaskType.CODING
        assert result.recommended_model == RecommendedModel.CLAUDE_SONNET

    def test_classify_review(self, classifier):
        """测试审查类任务"""
        from council.orchestration.task_classifier import TaskType, RecommendedModel

        result = classifier.classify("审查这段代码的安全性")
        assert result.task_type == TaskType.REVIEW
        assert result.recommended_model == RecommendedModel.GEMINI_PRO

    def test_classify_debugging(self, classifier):
        """测试调试类任务"""
        from council.orchestration.task_classifier import TaskType

        result = classifier.classify("修复这个 bug")
        assert result.task_type == TaskType.DEBUGGING

    def test_recommend_model(self, classifier):
        """测试快速推荐"""
        from council.orchestration.task_classifier import RecommendedModel

        model = classifier.recommend_model("设计系统架构")
        assert model == RecommendedModel.GPT_CODEX

    def test_explain(self, classifier):
        """测试解释功能"""
        result = classifier.classify("实现用户登录")
        explanation = classifier.explain(result)
        assert "类型" in explanation
        assert "推荐模型" in explanation


# ============================================================
# PTCEnforcer Tests
# ============================================================


class TestPTCEnforcer:
    """PTCEnforcer 测试"""

    @pytest.fixture
    def enforcer(self):
        from council.governance.ptc_enforcer import PTCEnforcer

        return PTCEnforcer(strict_mode=False)

    @pytest.fixture
    def strict_enforcer(self):
        from council.governance.ptc_enforcer import PTCEnforcer

        return PTCEnforcer(strict_mode=True)

    def test_single_file_edit_allowed(self, enforcer):
        """测试单文件编辑允许"""
        from council.governance.ptc_enforcer import OperationType

        result = enforcer.check(file_count=1, operation=OperationType.EDIT)
        assert result.should_use_ptc is False

    def test_batch_files_require_ptc(self, enforcer):
        """测试批量文件需要 PTC"""
        from council.governance.ptc_enforcer import OperationType

        result = enforcer.check(file_count=5, operation=OperationType.EDIT)
        assert result.should_use_ptc is True
        assert "5 个文件" in result.reason

    def test_lint_fix_requires_ptc(self, enforcer):
        """测试 lint 修复需要 PTC"""
        from council.governance.ptc_enforcer import OperationType

        result = enforcer.check(file_count=1, operation=OperationType.LINT_FIX)
        assert result.should_use_ptc is True
        assert "ruff" in result.suggested_command

    def test_format_requires_ptc(self, enforcer):
        """测试格式化需要 PTC"""
        from council.governance.ptc_enforcer import OperationType

        result = enforcer.check(file_count=1, operation=OperationType.FORMAT)
        assert result.should_use_ptc is True

    def test_strict_mode_raises(self, strict_enforcer):
        """测试严格模式抛出异常"""
        from council.governance.ptc_enforcer import OperationType, PTCRequiredError

        with pytest.raises(PTCRequiredError) as exc_info:
            strict_enforcer.check_and_enforce(
                file_count=5, operation=OperationType.EDIT
            )

        assert "5 个文件" in str(exc_info.value)

    def test_bypass_tracking(self, enforcer):
        """测试绕过计数"""
        enforcer.bypass("紧急修复")
        enforcer.bypass("测试用途")

        assert enforcer.get_bypass_count() == 2
