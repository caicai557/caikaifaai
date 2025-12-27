import argparse
from unittest.mock import patch
from src.telegram_multi.cli.parser import create_parser, parse_args

class TestCliParser:
    """Test suite for CLI argument parsing logic."""

    def test_parser_creation(self):
        """Test that parser is created with correct description."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert "Telegram Multi-Instance CLI" in parser.description

    def test_command_launch_args(self):
        """Test 'launch' command arguments."""
        parser = create_parser()

        # Test specific instance (global args before subcommand)
        args = parser.parse_args(
            ["--config", "cfg.yaml", "launch", "--instance", "acc1"]
        )
        assert args.command == "launch"
        assert args.instance == "acc1"
        assert args.config == "cfg.yaml"
        assert args.all is False

        # Test --all flag
        args = parser.parse_args(["--config", "cfg.yaml", "launch", "--all"])
        assert args.command == "launch"
        assert args.all is True
        assert args.instance is None

    def test_command_check_args(self):
        """Test 'check' command arguments."""
        parser = create_parser()
        args = parser.parse_args(["--config", "my_config.yaml", "check"])
        assert args.command == "check"
        assert args.config == "my_config.yaml"

    def test_command_list_args(self):
        """Test 'list' command arguments."""
        parser = create_parser()
        args = parser.parse_args(["--config", "cfg.yaml", "list"])
        assert args.command == "list"
        # Config is global argument, so it should be present
        assert args.config == "cfg.yaml"

    def test_default_config_path(self):
        """Test default configuration path."""
        parser = create_parser()
        args = parser.parse_args(["list"])
        assert args.config == "telegram.yaml"

    def test_parse_args_wrapper(self):
        """Test the high-level parse_args wrapper."""
        with patch("sys.argv", ["prog", "launch", "--all"]):
            args = parse_args()
            assert args.command == "launch"
            assert args.all is True
