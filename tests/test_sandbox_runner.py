"""
Tests for sandbox runners.
"""

import os


def test_local_sandbox_runner_executes_code(tmp_path):
    from council.sandbox import LocalSandboxRunner

    runner = LocalSandboxRunner(working_dir=str(tmp_path), env=os.environ.copy())
    result = runner.run('print("hello sandbox")', timeout=5)

    assert result.status == "success"
    assert "hello sandbox" in result.stdout


def test_get_sandbox_runner_local(tmp_path):
    from council.sandbox import get_sandbox_runner, LocalSandboxRunner

    runner = get_sandbox_runner(
        "local",
        env=os.environ.copy(),
        working_dir=str(tmp_path),
    )
    assert isinstance(runner, LocalSandboxRunner)
