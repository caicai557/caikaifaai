"""
Tests for CLI main entry point (Phase 6.3).

Contract:
- cli_main must return non-zero exit code on failures
- Exceptions from launch_instances must propagate to exit handler
- Configuration errors must exit with code 1
"""

import pytest
from unittest.mock import patch
from src.telegram_multi.cli.cli_main import main
from src.telegram_multi.config import TelegramConfig, InstanceConfig


class TestCliMainExitCodes:
    """Contract tests for CLI exit code semantics (Phase 6.3)."""

    @pytest.mark.asyncio
    async def test_launch_exception_propagates_to_cli_main(self):
        """Contract: Exceptions from launch_instances must be caught by cli_main.

        AC4.3: When launch_instances raises an exception (not KeyboardInterrupt),
        cli_main must catch it and call sys.exit(1).
        """
        mock_config = TelegramConfig(
            instances=[InstanceConfig(id="test", profile_path="./p1")]
        )

        # Mock launch_instances to raise an exception
        async def raise_runtime_error(*args, **kwargs):
            raise RuntimeError("Launch failed")

        with patch(
            "src.telegram_multi.cli.cli_main.TelegramConfig.from_yaml",
            return_value=mock_config,
        ):
            with patch(
                "src.telegram_multi.cli.cli_main.launch_instances",
                side_effect=raise_runtime_error,
            ):
                with patch("sys.exit") as mock_exit:
                    # sys.exit raises SystemExit
                    mock_exit.side_effect = SystemExit

                    # Should catch exception and call sys.exit(1)
                    with pytest.raises(SystemExit):
                        await main(["launch", "--instance", "test"])

                    mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_launch_exception_causes_exit_code_1(self):
        """Contract: Launch exceptions must cause exit code 1.

        AC4.3: When launch_instances raises an exception, cli_main should
        catch it and call sys.exit(1).
        """
        mock_config = TelegramConfig(
            instances=[InstanceConfig(id="test", profile_path="./p1")]
        )

        async def raise_runtime_error(*args, **kwargs):
            raise RuntimeError("Launch failed")

        with patch(
            "src.telegram_multi.cli.cli_main.TelegramConfig.from_yaml",
            return_value=mock_config,
        ):
            with patch(
                "src.telegram_multi.cli.cli_main.launch_instances",
                side_effect=raise_runtime_error,
            ):
                with patch("sys.exit") as mock_exit:
                    # sys.exit raises SystemExit
                    mock_exit.side_effect = SystemExit

                    # Should catch exception and call sys.exit(1)
                    with pytest.raises(SystemExit):
                        await main(["launch", "--instance", "test"])

                    # Verify exit code is 1
                    mock_exit.assert_called_with(1)

    @pytest.mark.asyncio
    async def test_config_load_failure_exits_with_code_1(self):
        """Contract: Configuration load errors must exit with code 1.

        AC4.2: When TelegramConfig.from_yaml raises an exception,
        cli_main must catch it and call sys.exit(1).
        """
        with patch(
            "src.telegram_multi.cli.cli_main.TelegramConfig.from_yaml",
            side_effect=Exception("Invalid YAML"),
        ):
            with patch("sys.exit") as mock_exit:
                # sys.exit raises SystemExit, so we need to catch it
                mock_exit.side_effect = SystemExit

                with pytest.raises(SystemExit):
                    await main(["launch", "--all"])

                # Should have called sys.exit(1)
                mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_check_command_failure_exits_with_code_1(self):
        """Contract: Check command failures must exit with code 1.

        Verify that when check_config returns False, cli_main calls sys.exit(1).
        """
        with patch(
            "src.telegram_multi.cli.cli_main.check_config", return_value=False
        ):
            with patch("sys.exit") as mock_exit:
                # sys.exit raises SystemExit
                mock_exit.side_effect = SystemExit

                with pytest.raises(SystemExit):
                    await main(["--config", "test.yaml", "check"])

                # Should have called sys.exit(1)
                mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_check_command_success_exits_with_code_0(self):
        """Contract: Check command success must exit with code 0.

        Verify that when check_config returns True, cli_main calls sys.exit(0).
        """
        with patch(
            "src.telegram_multi.cli.cli_main.check_config", return_value=True
        ):
            with patch("sys.exit") as mock_exit:
                # sys.exit raises SystemExit
                mock_exit.side_effect = SystemExit

                with pytest.raises(SystemExit):
                    await main(["--config", "test.yaml", "check"])

                # Should have called sys.exit(0)
                mock_exit.assert_called_once_with(0)


class TestCliMainInstanceNotFound:
    """Contract tests for instance not found error handling (AC4.1)."""

    @pytest.mark.asyncio
    async def test_launch_nonexistent_instance_exits_with_code_1(self):
        """Contract: Launching non-existent instance must exit with code 1.

        AC4.1: When user requests an instance that doesn't exist,
        cli_main must exit with code 1 (not just print error and return).
        """
        mock_config = TelegramConfig(instances=[])  # Empty instances

        with patch(
            "src.telegram_multi.cli.cli_main.TelegramConfig.from_yaml",
            return_value=mock_config,
        ):
            with patch("sys.exit") as mock_exit:
                await main(["launch", "--instance", "nonexistent"])

                # Currently launch_instances just prints error and returns
                # After fix, should call sys.exit(1)
                # This test should FAIL initially
                mock_exit.assert_called_with(1)


class TestCliMainCommandDispatch:
    """Contract tests for command dispatching logic."""

    @pytest.mark.asyncio
    async def test_list_command_prints_instances(self, capsys):
        """Contract: List command should print all instances."""
        mock_config = TelegramConfig(
            instances=[
                InstanceConfig(id="acc1", profile_path="./p1"),
                InstanceConfig(id="acc2", profile_path="./p2"),
            ]
        )

        with patch(
            "src.telegram_multi.cli.cli_main.TelegramConfig.from_yaml",
            return_value=mock_config,
        ):
            await main(["list"])

            captured = capsys.readouterr()
            assert "Loaded 2 instances" in captured.out
            assert "[acc1]" in captured.out
            assert "[acc2]" in captured.out

    @pytest.mark.asyncio
    async def test_stop_command_placeholder(self, capsys):
        """Contract: Stop command should show placeholder message."""
        mock_config = TelegramConfig(instances=[])

        with patch(
            "src.telegram_multi.cli.cli_main.TelegramConfig.from_yaml",
            return_value=mock_config,
        ):
            await main(["stop", "test_instance"])

            captured = capsys.readouterr()
            assert "Not implemented yet" in captured.out
