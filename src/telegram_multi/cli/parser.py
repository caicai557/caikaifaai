import argparse
from typing import Optional, List

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for SeaBox CLI.

    Returns:
        Argparse parser object configured with commands and arguments.
    """
    parser = argparse.ArgumentParser(
        description="Telegram Multi-Instance CLI (cesi-telegram-multi)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Global arguments
    parser.add_argument(
        "--config",
        "-c",
        default="telegram.yaml",
        help="Path to configuration file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True

    # Command: launch
    launch_parser = subparsers.add_parser(
        "launch",
        help="Launch Telegram instances",
    )
    launch_group = launch_parser.add_mutually_exclusive_group(required=True)
    launch_group.add_argument(
        "--instance",
        "-i",
        help="Launch a specific instance by ID",
    )
    launch_group.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Launch all configured instances",
    )

    # Command: list
    subparsers.add_parser(
        "list",
        help="List configured instances",
    )

    # Command: check
    subparsers.add_parser(
        "check",
        help="Validate configuration file",
    )

    # Command: stop
    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop a running instance",
    )
    stop_parser.add_argument(
        "instance_id",
        help="ID of the instance to stop",
    )

    # Command: council
    subparsers.add_parser(
        "council",
        help="Start the Agent Council Orchestrator",
    )

    return parser


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Optional list of arguments. If None, uses sys.argv[1:].

    Returns:
        Parsed arguments namespace.
    """
    parser = create_parser()
    return parser.parse_args(args)
