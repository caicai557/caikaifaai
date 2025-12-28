#!/usr/bin/env python3
"""
Telegram Multi-Instance CLI Entry Point

Usage:
    python run_telegram.py --config telegram.yaml launch --all
    python run_telegram.py --config telegram.yaml check
"""

import sys
import asyncio

from src.telegram_multi.cli.cli_main import main

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result if result else 0)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
