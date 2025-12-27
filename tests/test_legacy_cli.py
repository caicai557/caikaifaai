"""
Tests for legacy CLI parameter compatibility (Phase 6.4).

Contract:
- Legacy parameters (--instances, -n, --source, -s) should be detected
- Migration message should be shown with examples
- Should exit with code 1 to indicate error
"""

from unittest.mock import patch


class TestLegacyParameterDetection:
    """Contract tests for legacy parameter detection (Phase 6.4)."""

    def test_legacy_instances_param_shows_migration_message(self, capsys):
        """Contract: Detect --instances parameter and show migration message.

        AC3.1: When --instances is used, show migration guide.
        """
        # Mock sys.argv to simulate legacy parameter
        test_argv = ["run_telegram.py", "--instances", "acc1,acc2"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit") as mock_exit:
                # Import run_telegram module (will execute detection logic)
                # We need to test the detection function directly
                from tests.helpers import detect_legacy_params

                detect_legacy_params()

                # Should have called sys.exit(1)
                mock_exit.assert_called_once_with(1)

        # Check that migration message was printed
        captured = capsys.readouterr()
        assert "旧 CLI 参数" in captured.out or "deprecated" in captured.out.lower()

    def test_legacy_n_flag_shows_migration_message(self, capsys):
        """Contract: Detect -n flag and show migration message.

        AC3.1: When -n is used, show migration guide.
        """
        test_argv = ["run_telegram.py", "-n", "2"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit") as mock_exit:
                from tests.helpers import detect_legacy_params

                detect_legacy_params()
                mock_exit.assert_called_once_with(1)

        captured = capsys.readouterr()
        assert "旧" in captured.out or "deprecated" in captured.out.lower()

    def test_legacy_source_param_shows_migration_message(self, capsys):
        """Contract: Detect --source parameter and show migration message.

        AC3.1: When --source is used, show migration guide.
        """
        test_argv = ["run_telegram.py", "--source", "zh-CN"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit") as mock_exit:
                from tests.helpers import detect_legacy_params

                detect_legacy_params()
                mock_exit.assert_called_once_with(1)

        captured = capsys.readouterr()
        assert "旧" in captured.out or "deprecated" in captured.out.lower()

    def test_legacy_s_flag_shows_migration_message(self, capsys):
        """Contract: Detect -s flag and show migration message.

        AC3.1: When -s is used, show migration guide.
        """
        test_argv = ["run_telegram.py", "-s", "en"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit") as mock_exit:
                from tests.helpers import detect_legacy_params

                detect_legacy_params()
                mock_exit.assert_called_once_with(1)

        captured = capsys.readouterr()
        assert "旧" in captured.out or "deprecated" in captured.out.lower()


class TestMigrationMessageContent:
    """Contract tests for migration message content (AC3.2, AC3.3)."""

    def test_migration_message_contains_example_command(self, capsys):
        """Contract: Migration message includes example commands.

        AC3.2, AC3.3: Message must contain quick start command examples.
        """
        test_argv = ["run_telegram.py", "--instances", "acc1"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit"):
                from tests.helpers import detect_legacy_params

                detect_legacy_params()

        captured = capsys.readouterr()
        output = captured.out

        # Should contain launch command example
        assert "launch" in output.lower()
        assert "--all" in output or "launch --all" in output

    def test_migration_message_contains_config_template(self, capsys):
        """Contract: Migration message includes config file template.

        AC3.2: Message must show configuration file structure.
        """
        test_argv = ["run_telegram.py", "--instances", "acc1"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit"):
                from tests.helpers import detect_legacy_params

                detect_legacy_params()

        captured = capsys.readouterr()
        output = captured.out

        # Should contain config template keywords
        assert "instances:" in output or "配置" in output
        assert "id:" in output or "profile_path:" in output

    def test_migration_message_contains_quick_start_command(self, capsys):
        """Contract: Migration message contains quick start command.

        AC3.3: Message must provide ready-to-use command.
        """
        test_argv = ["run_telegram.py", "--instances", "acc1"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit"):
                from tests.helpers import detect_legacy_params

                detect_legacy_params()

        captured = capsys.readouterr()
        output = captured.out

        # Should contain executable command
        assert "run_telegram.py" in output or "python" in output
        assert "launch" in output

    def test_new_cli_params_are_not_detected_as_legacy(self, capsys):
        """Contract: New CLI parameters should not trigger legacy detection.

        Ensure that valid new CLI usage doesn't show migration message.
        """
        test_argv = ["run_telegram.py", "launch", "--all"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit") as mock_exit:
                from tests.helpers import detect_legacy_params

                detect_legacy_params()

                # Should NOT call sys.exit for new CLI
                mock_exit.assert_not_called()

        captured = capsys.readouterr()
        # Should not print migration message
        assert "旧" not in captured.out
        assert "deprecated" not in captured.out.lower()

    def test_config_flag_is_not_legacy(self, capsys):
        """Contract: --config flag should not be treated as legacy.

        The --config flag is part of the new CLI.
        """
        test_argv = ["run_telegram.py", "--config", "telegram.yaml", "launch", "--all"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit") as mock_exit:
                from tests.helpers import detect_legacy_params

                detect_legacy_params()
                mock_exit.assert_not_called()

        captured = capsys.readouterr()
        assert "旧" not in captured.out
        assert "deprecated" not in captured.out.lower()


class TestLegacyDetectionExitCode:
    """Contract tests for exit code when legacy params detected."""

    def test_legacy_param_exits_with_code_1(self):
        """Contract: Legacy parameters should cause exit code 1.

        AC3.1: Should exit with error code, not success.
        """
        test_argv = ["run_telegram.py", "--instances", "acc1"]

        with patch("sys.argv", test_argv):
            with patch("sys.exit") as mock_exit:
                from tests.helpers import detect_legacy_params

                detect_legacy_params()

                # Verify exit code is 1, not 0
                mock_exit.assert_called_once_with(1)
