import tempfile
import os
from unittest.mock import patch
from src.telegram_multi.cli.commands.check import check_config

class TestCliCheck:
    """Test suite for 'check' command."""

    def test_check_valid_config(self):
        """Test validation of a valid configuration file."""
        valid_yaml = """
        instances:
          - id: test1
            profile_path: ./p1
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(valid_yaml)
            config_path = f.name

        try:
            # Should not raise exception
            assert check_config(config_path) is True
        finally:
            os.remove(config_path)

    def test_check_invalid_yaml(self):
        """Test validation fails with invalid YAML."""
        invalid_yaml = "instances: [ unclosed_list"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            config_path = f.name

        try:
            assert check_config(config_path) is False
        finally:
            os.remove(config_path)

    def test_check_file_not_found(self):
        """Test validation fails when file missing."""
        assert check_config("non_existent_file.yaml") is False

    @patch('src.telegram_multi.config.TelegramConfig.from_yaml')
    def test_check_validation_error(self, mock_from_yaml):
        """Test Pydantic validation error handling."""
        mock_from_yaml.side_effect = ValueError("Invalid field")
        assert check_config("dummy.yaml") is False


class TestCliCheckEdgeCases:
    """Edge case tests for check.py exception handling (Task 7.2)."""

    @patch('src.telegram_multi.config.TelegramConfig.from_yaml')
    def test_check_handles_runtime_error(self, mock_from_yaml, capsys):
        """Test generic exception handling (line 24-26).

        Contract AC2.1, AC2.2: Verify catch-all exception branch.
        This tests that non-FileNotFoundError/ValueError exceptions
        are properly caught and return False.
        """
        # Mock a RuntimeError to trigger generic Exception handler
        mock_from_yaml.side_effect = RuntimeError("Simulated I/O error")

        result = check_config("dummy.yaml")

        # AC2.2: Should return False
        assert result is False

        # AC2.2: Should print error message
        captured = capsys.readouterr()
        assert "Unexpected error" in captured.out
        assert "Simulated I/O error" in captured.out

    @patch('src.telegram_multi.config.TelegramConfig.from_yaml')
    def test_check_handles_permission_error(self, mock_from_yaml, capsys):
        """Test permission error handling.

        Contract AC2.3: Example scenario - PermissionError triggers
        the generic Exception handler (not FileNotFoundError/ValueError).
        """
        # Mock a PermissionError
        mock_from_yaml.side_effect = PermissionError("No read permission")

        result = check_config("restricted.yaml")

        # Should return False
        assert result is False

        # Should print error message
        captured = capsys.readouterr()
        assert "Unexpected error" in captured.out
        assert "No read permission" in captured.out
