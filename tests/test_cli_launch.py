import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.telegram_multi.cli.commands.launch import launch_instances
from src.telegram_multi.config import TelegramConfig, InstanceConfig

class TestCliLaunch:
    """Test suite for 'launch' command."""

    @pytest.mark.asyncio
    async def test_launch_single_instance(self):
        """Test launching a specific instance."""
        import asyncio

        mock_manager = MagicMock()
        mock_instance = MagicMock()
        mock_manager.get_instance.return_value = mock_instance

        # Mock instance.start() to be async
        mock_instance.start = AsyncMock()

        config = TelegramConfig(instances=[
            InstanceConfig(id="acc1", profile_path="./p1")
        ])

        # Mock asyncio.sleep to raise KeyboardInterrupt to exit keep-alive
        original_sleep = asyncio.sleep

        async def interrupt_during_sleep(seconds):
            if seconds == 1:  # Keep-alive sleep
                raise KeyboardInterrupt()
            return await original_sleep(seconds)

        with patch(
            'src.telegram_multi.instance_manager.InstanceManager.from_config',
            return_value=mock_manager,
        ):
            with patch('asyncio.sleep', side_effect=interrupt_during_sleep):
                # Should exit gracefully due to KeyboardInterrupt
                await launch_instances(config, instance_id="acc1")

        mock_manager.get_instance.assert_called_with("acc1")
        mock_instance.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_launch_all_instances(self):
        """Test launching all instances."""
        import asyncio

        mock_manager = MagicMock()
        inst1 = MagicMock()
        inst1.start = AsyncMock()
        inst2 = MagicMock()
        inst2.start = AsyncMock()

        mock_manager.instances = {"acc1": inst1, "acc2": inst2}
        mock_manager.list_instances.return_value = ["acc1", "acc2"]
        mock_manager.get_instance.side_effect = lambda k: mock_manager.instances.get(k)

        config = TelegramConfig(instances=[])

        # Mock asyncio.sleep to raise KeyboardInterrupt to exit keep-alive
        original_sleep = asyncio.sleep

        async def interrupt_during_sleep(seconds):
            if seconds == 1:  # Keep-alive sleep
                raise KeyboardInterrupt()
            return await original_sleep(seconds)

        with patch(
            'src.telegram_multi.instance_manager.InstanceManager.from_config',
            return_value=mock_manager,
        ):
            with patch('asyncio.sleep', side_effect=interrupt_during_sleep):
                # Should exit gracefully due to KeyboardInterrupt
                await launch_instances(config, launch_all=True)

        assert inst1.start.call_count == 1
        assert inst2.start.call_count == 1

    @pytest.mark.asyncio
    async def test_launch_instance_not_found(self):
        """Test error when instance not found.

        Contract: Should raise ValueError when instance not found (AC4.1).
        """
        mock_manager = MagicMock()
        mock_manager.get_instance.return_value = None

        config = TelegramConfig(instances=[])

        with patch(
            'src.telegram_multi.instance_manager.InstanceManager.from_config',
            return_value=mock_manager,
        ):
            # Should raise ValueError for missing instance
            with pytest.raises(ValueError, match="not found in config"):
                await launch_instances(config, instance_id="missing")


class TestCliLaunchKeepAlive:
    """Test suite for keep-alive lifecycle management (Phase 6.2)."""

    @pytest.mark.asyncio
    async def test_launch_keeps_running_until_keyboard_interrupt(self):
        """Contract: launch_instances keeps running after start.

        AC2.1: After launching instances, must enter infinite loop
        waiting for KeyboardInterrupt. Current implementation returns
        immediately - this test should FAIL.
        """
        import asyncio

        mock_manager = MagicMock()
        mock_instance = MagicMock()
        mock_manager.get_instance.return_value = mock_instance
        mock_instance.start = AsyncMock()

        config = TelegramConfig(
            instances=[InstanceConfig(id="test", profile_path="./p1")]
        )

        with patch(
            'src.telegram_multi.instance_manager.InstanceManager.from_config',
            return_value=mock_manager,
        ):
            # launch_instances should keep running (timeout expected)
            with pytest.raises(asyncio.TimeoutError):
                # Should timeout because keep-alive waits forever
                await asyncio.wait_for(
                    launch_instances(config, instance_id="test"), timeout=0.2
                )

        mock_instance.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_exits_gracefully(self, capsys):
        """Contract: KeyboardInterrupt exits gracefully without raising.

        AC2.2: When Ctrl+C (KeyboardInterrupt) occurs during keep-alive,
        must exit gracefully and print user-friendly message.
        """
        import asyncio

        mock_manager = MagicMock()
        mock_instance = MagicMock()
        mock_manager.get_instance.return_value = mock_instance
        mock_instance.start = AsyncMock()

        config = TelegramConfig(
            instances=[InstanceConfig(id="test", profile_path="./p1")]
        )

        # Mock asyncio.sleep to raise KeyboardInterrupt during keep-alive
        original_sleep = asyncio.sleep

        async def interrupt_during_sleep(seconds):
            if seconds == 1:  # Keep-alive sleep
                raise KeyboardInterrupt()
            return await original_sleep(seconds)

        with patch(
            'src.telegram_multi.instance_manager.InstanceManager.from_config',
            return_value=mock_manager,
        ):
            with patch('asyncio.sleep', side_effect=interrupt_during_sleep):
                # Should NOT raise - must handle KeyboardInterrupt gracefully
                await launch_instances(config, instance_id="test")

        # Check output contains graceful shutdown message
        captured = capsys.readouterr()
        output = captured.out.lower()
        assert (
            "stopped" in output or "user" in output
        ), f"Expected graceful shutdown message, got: {captured.out}"

    @pytest.mark.asyncio
    async def test_launch_propagates_non_keyboard_exceptions(self):
        """Contract: Non-KeyboardInterrupt exceptions must propagate.

        AC2.3: Other exceptions (not KeyboardInterrupt) should propagate
        to caller for proper exit code handling.
        """
        mock_manager = MagicMock()
        mock_instance = MagicMock()
        mock_manager.get_instance.return_value = mock_instance

        # Mock start() to raise a different exception
        async def raise_runtime_error():
            raise RuntimeError("Simulated launch failure")

        mock_instance.start = raise_runtime_error

        config = TelegramConfig(
            instances=[InstanceConfig(id="test", profile_path="./p1")]
        )

        with patch(
            'src.telegram_multi.instance_manager.InstanceManager.from_config',
            return_value=mock_manager,
        ):
            # Should propagate RuntimeError (not KeyboardInterrupt)
            with pytest.raises(RuntimeError, match="Simulated launch failure"):
                await launch_instances(config, instance_id="test")

    @pytest.mark.asyncio
    async def test_keep_alive_loop_runs_after_successful_start(self):
        """Contract: Keep-alive loop only runs if launch succeeds.

        AC2.1: Should enter keep-alive loop only after successful start.
        If no instances to launch, should return immediately.
        """
        config = TelegramConfig(instances=[])
        mock_manager = MagicMock()
        mock_manager.list_instances.return_value = []

        with patch(
            'src.telegram_multi.instance_manager.InstanceManager.from_config',
            return_value=mock_manager,
        ):
            # Should return immediately without entering keep-alive
            import asyncio

            try:
                await asyncio.wait_for(
                    launch_instances(config, launch_all=True), timeout=0.5
                )
            except asyncio.TimeoutError:
                pytest.fail(
                    "launch_instances should return immediately "
                    "when no instances to launch"
                )
