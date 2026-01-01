"""
Unit tests for Council Hooks mechanism

Tests cover:
- HookManager registration and triggering
- SessionStartHook initialization
- PreToolUseHook security blocking
- PostToolUseHook quality gates
"""

import pytest

from council.hooks.base import (
    HookType,
    HookAction,
    HookContext,
)
from council.hooks.manager import HookManager
from council.hooks.session_start import SessionStartHook
from council.hooks.pre_tool_use import PreToolUseHook
from council.hooks.post_tool_use import PostToolUseHook


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def hook_context():
    """Create a basic hook context"""
    return HookContext(
        hook_type=HookType.PRE_TOOL_USE,
        session_id="test-session-001",
        agent_name="test_agent",
        working_dir=".",
    )


@pytest.fixture
def hook_manager():
    """Create a fresh hook manager"""
    return HookManager()


# ============================================================================
# HookManager Tests
# ============================================================================


class TestHookManager:
    """Tests for HookManager"""

    def test_register_hook(self, hook_manager):
        """Should register hooks correctly"""
        hook = PreToolUseHook()
        hook_manager.register(hook)

        hooks = hook_manager.get_hooks(HookType.PRE_TOOL_USE)
        assert len(hooks) == 1
        assert hooks[0].name == "pre_tool_use"

    def test_unregister_hook(self, hook_manager):
        """Should unregister hooks correctly"""
        hook = PreToolUseHook()
        hook_manager.register(hook)

        result = hook_manager.unregister("pre_tool_use")
        assert result is True
        assert len(hook_manager.get_hooks(HookType.PRE_TOOL_USE)) == 0

    def test_priority_ordering(self, hook_manager):
        """Hooks should be ordered by priority"""
        hook1 = PreToolUseHook(priority=100)
        hook1.name = "hook1"
        hook2 = PreToolUseHook(priority=50)
        hook2.name = "hook2"
        hook3 = PreToolUseHook(priority=75)
        hook3.name = "hook3"

        hook_manager.register(hook1)
        hook_manager.register(hook2)
        hook_manager.register(hook3)

        hooks = hook_manager.get_hooks(HookType.PRE_TOOL_USE)
        assert hooks[0].name == "hook2"  # priority 50
        assert hooks[1].name == "hook3"  # priority 75
        assert hooks[2].name == "hook1"  # priority 100

    @pytest.mark.asyncio
    async def test_trigger_returns_allow_when_empty(self, hook_manager, hook_context):
        """Should return ALLOW when no hooks registered"""
        result = await hook_manager.trigger(HookType.PRE_TOOL_USE, hook_context)
        assert result.action == HookAction.ALLOW

    @pytest.mark.asyncio
    async def test_trigger_stops_on_block(self, hook_manager, hook_context):
        """Should stop chain when hook returns BLOCK"""
        hook = PreToolUseHook()
        hook_manager.register(hook)

        # Set up a dangerous command
        hook_context.tool_name = "bash"
        hook_context.tool_args = {"command": "rm -rf /"}

        result = await hook_manager.trigger(HookType.PRE_TOOL_USE, hook_context)
        assert result.action == HookAction.BLOCK


# ============================================================================
# PreToolUseHook Tests
# ============================================================================


class TestPreToolUseHook:
    """Tests for PreToolUseHook security checks"""

    @pytest.mark.asyncio
    async def test_block_rm_rf(self, hook_context):
        """Should block rm -rf command"""
        hook = PreToolUseHook()
        hook_context.tool_name = "bash"
        hook_context.tool_args = {"command": "rm -rf /"}

        result = await hook.execute(hook_context)
        assert result.action == HookAction.BLOCK
        assert (
            "dangerous" in result.message.lower() or "blocked" in result.message.lower()
        )

    @pytest.mark.asyncio
    async def test_block_ssh_path(self, hook_context):
        """Should block access to .ssh directory"""
        hook = PreToolUseHook()
        hook_context.tool_name = "read_file"
        hook_context.tool_args = {"path": "/home/user/.ssh/id_rsa"}

        result = await hook.execute(hook_context)
        assert result.action == HookAction.BLOCK
        assert (
            "sensitive" in result.message.lower() or "blocked" in result.message.lower()
        )

    @pytest.mark.asyncio
    async def test_allow_normal_command(self, hook_context):
        """Should allow normal commands"""
        hook = PreToolUseHook()
        hook_context.tool_name = "bash"
        hook_context.tool_args = {"command": "ls -la"}

        result = await hook.execute(hook_context)
        assert result.action == HookAction.ALLOW

    @pytest.mark.asyncio
    async def test_allow_with_sudo_token(self, hook_context):
        """Should allow dangerous commands with sudo token"""
        hook = PreToolUseHook(sudo_token="authorized")
        hook_context.tool_name = "bash"
        hook_context.tool_args = {"command": "rm -rf /tmp/test"}

        result = await hook.execute(hook_context)
        assert result.action == HookAction.ALLOW

    @pytest.mark.asyncio
    async def test_block_eval(self, hook_context):
        """Should block eval() in code"""
        hook = PreToolUseHook()
        hook_context.tool_name = "execute"
        hook_context.tool_args = {"code": 'eval(\'__import__("os").system("ls")\'))'}

        result = await hook.execute(hook_context)
        assert result.action == HookAction.BLOCK

    @pytest.mark.asyncio
    async def test_block_sql_injection(self, hook_context):
        """Should block DROP TABLE commands"""
        hook = PreToolUseHook()
        hook_context.tool_name = "database"
        hook_context.tool_args = {"query": "DROP TABLE users"}

        result = await hook.execute(hook_context)
        assert result.action == HookAction.BLOCK


# ============================================================================
# SessionStartHook Tests
# ============================================================================


class TestSessionStartHook:
    """Tests for SessionStartHook"""

    @pytest.mark.asyncio
    async def test_execute_returns_allow(self, hook_context, tmp_path):
        """Should return ALLOW on successful initialization"""
        hook = SessionStartHook(working_dir=str(tmp_path))
        hook_context.hook_type = HookType.SESSION_START

        result = await hook.execute(hook_context)
        assert result.action == HookAction.ALLOW
        assert "initialized" in result.message.lower()

    @pytest.mark.asyncio
    async def test_state_persistence(self, hook_context, tmp_path):
        """Should save and restore state"""
        hook = SessionStartHook(working_dir=str(tmp_path))

        # Set and save state
        hook.set_state("test_key", "test_value")
        await hook.save_state()

        # Create new hook and restore
        hook2 = SessionStartHook(working_dir=str(tmp_path))
        await hook2._restore_state()

        assert hook2.get_state("test_key") == "test_value"

    @pytest.mark.asyncio
    async def test_env_loading(self, hook_context, tmp_path):
        """Should load environment variables from .env"""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\nANOTHER=123")

        hook = SessionStartHook(working_dir=str(tmp_path))
        count = await hook._load_env_vars()

        assert count == 2
        import os

        assert os.environ.get("TEST_VAR") == "test_value"


# ============================================================================
# PostToolUseHook Tests
# ============================================================================


class TestPostToolUseHook:
    """Tests for PostToolUseHook quality gates"""

    @pytest.mark.asyncio
    async def test_skip_non_file_tools(self, hook_context, tmp_path):
        """Should skip quality gates for non-file tools"""
        hook = PostToolUseHook(working_dir=str(tmp_path))
        hook_context.tool_name = "search"
        hook_context.tool_args = {}

        result = await hook.execute(hook_context)
        assert result.action == HookAction.ALLOW
        assert result.metadata.get("skipped") is True

    @pytest.mark.asyncio
    async def test_run_for_file_tools(self, hook_context, tmp_path):
        """Should run quality gates for file modification tools"""
        hook = PostToolUseHook(
            working_dir=str(tmp_path),
            enable_format=False,  # Disable to avoid actual command execution
            enable_lint=False,
            enable_test=False,
        )
        hook_context.tool_name = "write_file"
        hook_context.tool_args = {"path": "test.py"}

        result = await hook.execute(hook_context)
        assert result.action == HookAction.ALLOW

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, hook_context, tmp_path):
        """Should return RETRY when quality gates fail"""
        hook = PostToolUseHook(
            working_dir=str(tmp_path),
            enable_format=True,
            enable_lint=False,
            enable_test=False,
        )

        # Mock the format command to fail
        async def mock_run_command(cmd, timeout=120):
            return {"returncode": 1, "stdout": "", "stderr": "Format error"}

        hook._run_command = mock_run_command
        hook_context.tool_name = "write_file"
        hook_context.tool_args = {"path": "test.py"}

        result = await hook.execute(hook_context)
        assert result.action == HookAction.RETRY
        assert result.metadata.get("self_healing") is True


# ============================================================================
# Integration Tests
# ============================================================================


class TestHooksIntegration:
    """Integration tests for the hooks system"""

    @pytest.mark.asyncio
    async def test_full_hook_chain(self, tmp_path):
        """Test complete hook chain execution"""
        manager = HookManager()

        # Register all hooks
        manager.register(SessionStartHook(working_dir=str(tmp_path)))
        manager.register(PreToolUseHook())
        manager.register(
            PostToolUseHook(
                working_dir=str(tmp_path),
                enable_format=False,
                enable_lint=False,
                enable_test=False,
            )
        )

        context = HookContext(
            hook_type=HookType.SESSION_START,
            session_id="integration-test",
            agent_name="test_agent",
            working_dir=str(tmp_path),
        )

        # Test session start
        result = await manager.trigger_session_start(context)
        assert result.action == HookAction.ALLOW

        # Test pre-tool (safe command)
        context.tool_name = "bash"
        context.tool_args = {"command": "echo hello"}
        result = await manager.trigger_pre_tool(context)
        assert result.action == HookAction.ALLOW

        # Test pre-tool (dangerous command)
        context.tool_args = {"command": "rm -rf /"}
        result = await manager.trigger_pre_tool(context)
        assert result.action == HookAction.BLOCK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
