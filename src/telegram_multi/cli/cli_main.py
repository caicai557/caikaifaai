import sys
import asyncio
from src.telegram_multi.cli.parser import parse_args
from src.telegram_multi.cli.commands.check import check_config
from src.telegram_multi.cli.commands.launch import launch_instances
from src.telegram_multi.config import TelegramConfig

async def main(args=None):
    """Main CLI entry point."""
    if args is None:
        args = parse_args()
    else:
        # If args provided (e.g. from tests), ensure they are parsed
        if not hasattr(args, 'command'):
             args = parse_args(args)

    # 1. Dispatch 'check' command (No config load needed yet)
    if args.command == "check":
        success = check_config(args.config)
        sys.exit(0 if success else 1)

    # 2. Load Config for other commands
    try:
        config = TelegramConfig.from_yaml(args.config)
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)

    # 3. Dispatch other commands
    if args.command == "launch":
        try:
            await launch_instances(
                config, instance_id=args.instance, launch_all=args.all
            )
        except Exception as e:
            print(f"❌ Launch Error: {e}")
            sys.exit(1)

    elif args.command == "list":
        print(f"Loaded {len(config.instances)} instances from {args.config}:")
        for inst in config.instances:
            print(f"  - [{inst.id}] Profile: {inst.profile_path}")

    elif args.command == "stop":
        # Placeholder for stop logic
        print(f"Stop command received for {args.instance_id} (Not implemented yet)")

    elif args.command == "council":
        from src.telegram_multi.cli.commands.council import start_council
        await start_council(config)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    except Exception as e:
        print(f"\n❌ Pre-execution Error: {e}")
        sys.exit(1)
