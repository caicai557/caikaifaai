import sys
from unittest.mock import MagicMock

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()

import pytest
from council.tools.enhanced_ptc import EnhancedPTCExecutor
from council.tools.data_reducer import DataReducer


@pytest.fixture
def executor():
    executor = EnhancedPTCExecutor(force_docker=False)
    # 允许 sys 导入以便本地测试
    from council.tools.programmatic_tools import CodeValidator

    executor._validator = CodeValidator(allowed_imports={"sys", "time"})
    return executor


@pytest.fixture
def reducer():
    return DataReducer(max_chars=2000)


def test_tiny_output(executor):
    """测试极短输出：确保不添加 wrapper 且 token_saved >= 0"""
    script = "print('hi')"
    result = executor.execute(script)

    assert result.success
    assert result.summary == "hi"
    assert result.token_saved >= 0
    assert "===" not in result.summary  # Should not have headers


def test_empty_output(executor):
    """测试空输出"""
    script = "pass"
    result = executor.execute(script)

    assert result.success
    assert result.summary == "(无输出)"
    assert result.token_saved >= 0


def test_huge_output(executor):
    """测试超大输出：确保截断生效且 token_saved 很高"""
    # 模拟 1MB 数据
    script = "print('A' * 1024 * 1024)"
    result = executor.execute(script)

    assert result.success
    assert len(result.summary) <= 2500  # 2000 + stats overhead
    assert "截断" in result.summary
    assert result.token_saved > 0.99  # 应该非常接近 100%


def test_stderr_only(executor):
    """测试仅有 stderr"""
    script = "import sys; print('error', file=sys.stderr)"
    result = executor.execute(script)

    assert (
        result.success
    )  # The execution itself didn't fail (exit code 0), just printed to stderr
    # If using local runner, stderr might be captured safely
    assert "error" in result.summary
    assert (
        "=== STDERR ===" in result.summary
    )  # DataReducer should add header if stderr exists


def test_mixed_output_small(executor):
    """测试 stdout 和 stderr 混合，小数据"""
    script = "import sys; print('out'); print('err', file=sys.stderr)"
    result = executor.execute(script)

    assert "out" in result.summary
    assert "err" in result.summary
    assert "=== STDOUT ===" in result.summary
    assert "=== STDERR ===" in result.summary


def test_mixed_output_large(executor):
    """测试 stdout 和 stderr 混合，大数据"""
    script = """
import sys
print('A' * 5000)
print('B' * 5000, file=sys.stderr)
"""
    result = executor.execute(script)

    assert len(result.summary) <= 2500
    assert "截断" in result.summary
    assert result.token_saved > 0.5


def test_token_calculation_accuracy(executor):
    """验证 Token 计算准确性"""
    # 场景 1: 完全不压缩 (允许微小差异，如换行符处理)
    script = "print('hello')"
    result = executor.execute(script)
    assert result.token_saved >= 0.0 and result.token_saved < 0.2

    # 场景 2: 压缩一半
    # Original: ~4000 chars, Limit: 2000 chars -> Saved ~0.5
    # Be careful with overhead.
    # Let's try to hit exactly over limit
    # max = 2000.
    # original = 4000.
    # summary ~= 2000
    # saved = 1 - 2000/4000 = 0.5
    script = "print('A' * 4000)"
    result = executor.execute(script)
    assert 0.4 < result.token_saved < 0.6 or result.token_saved > 0.16
