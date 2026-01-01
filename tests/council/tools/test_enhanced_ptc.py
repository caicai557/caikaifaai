import pytest
from unittest.mock import MagicMock, patch
from council.tools.enhanced_ptc import EnhancedPTCExecutor, PTCResult


@pytest.fixture
def executor():
    # Use local runner for testing to avoid docker requirement
    return EnhancedPTCExecutor(force_docker=False, force_single_inference=True)


@pytest.mark.asyncio
async def test_orchestrate_flow(executor):
    task = "Analyze logs"

    # Mock orchestrator behavior since actual execution requires valid python code
    # and we want to test the flow, not the engine's code generation capability here
    args = MagicMock()
    args.summary = "Summary result"
    args.success = True
    args.token_saved = 0.95
    args.execution_time = 1.0
    args.anomalies = ["Error found"]

    with patch.object(executor._orchestrator, "orchestrate", return_value=args):
        result = await executor.orchestrate(task)

        assert isinstance(result, PTCResult)
        assert result.success is True
        assert result.summary == "Summary result"
        assert result.token_saved == 0.95
        assert result.anomalies == ["Error found"]
        assert result.token_stats["saved_rate"] == 0.95


def test_execute_local(executor):
    # Test actual local execution of a safe script
    # Use long enough output to ensure positive token savings (> 2000 chars)
    script = """
print('Hello ' * 500)
print('ERROR: Simulation')
"""
    result = executor.execute(script)

    assert result.success is True
    assert "Hello" in result.summary
    assert result.token_saved > 0  # Should be positive now due to truncation
    assert any("ERROR" in a for a in result.anomalies)


def test_security_validation(executor):
    script = "import os; os.system('rm -rf /')"
    # CodeValidator should catch this
    result = executor.execute(script)

    assert result.success is False
    assert "安全违规" in result.summary or "Security" in result.summary


def test_token_stats_accumulation(executor):
    executor.reset_token_stats()

    script = "print('A' * 3000)"
    executor.execute(script)

    stats = executor.get_token_stats()
    assert stats["input_tokens"] > 0
    assert stats["saved_tokens"] > 0
