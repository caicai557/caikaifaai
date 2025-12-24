#!/usr/bin/env python3
"""
Multi-Instance Telegram Web A Runner with Bidirectional Translation.

Usage:
    python run_telegram.py --instances 2 --source zh --target en

Requirements:
    pip install playwright
    playwright install chromium
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.telegram_multi.config import TelegramConfig, InstanceConfig, TranslationConfig
from src.telegram_multi.instance_manager import InstanceManager
from src.telegram_multi.translator import TranslatorFactory
from src.telegram_multi.message_interceptor import MessageInterceptor


async def launch_instance(
    instance_id: str,
    profile_path: str,
    interceptor: MessageInterceptor,
    headless: bool = False
):
    """Launch a single Telegram Web A browser instance.
    
    Args:
        instance_id: Unique identifier for logging
        profile_path: Path to store browser profile data
        interceptor: MessageInterceptor with translation config
        headless: Run in headless mode (default: False for visibility)
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: Playwright not installed. Run: pip install playwright && playwright install chromium")
        return

    async with async_playwright() as p:
        # Launch browser with persistent context (saves login state)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=headless,
            viewport={"width": 1200, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = await context.new_page()
        
        # Navigate to Telegram Web A
        print(f"[{instance_id}] Navigating to Telegram Web A...")
        await page.goto("https://web.telegram.org/a/", wait_until="domcontentloaded")
        
        # Inject translation script
        injection_script = interceptor.get_injection_script()
        await page.add_init_script(injection_script)
        
        print(f"[{instance_id}] Instance ready. Press Ctrl+C to close all instances.")
        
        # Keep browser open until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await context.close()
            print(f"[{instance_id}] Closed.")


async def main(num_instances: int, source_lang: str, target_lang: str, profile_base: str):
    """Main entry point to launch multiple Telegram instances."""
    
    # Create translation config
    translation_config = TranslationConfig(
        enabled=True,
        provider="google",
        source_lang=source_lang,
        target_lang=target_lang
    )
    
    # Create translator
    try:
        translator = TranslatorFactory.create(translation_config)
    except Exception as e:
        print(f"Warning: Could not initialize translator: {e}")
        translator = None
    
    # Create interceptor
    interceptor = MessageInterceptor(config=translation_config, translator=translator)
    
    # Prepare instance configs
    tasks = []
    for i in range(num_instances):
        instance_id = f"telegram_{i+1}"
        profile_path = os.path.join(profile_base, instance_id)
        os.makedirs(profile_path, exist_ok=True)
        
        task = launch_instance(
            instance_id=instance_id,
            profile_path=profile_path,
            interceptor=interceptor,
            headless=False
        )
        tasks.append(task)
    
    print(f"\n🚀 Launching {num_instances} Telegram instance(s)...")
    print(f"   Translation: {source_lang} ↔ {target_lang}")
    print(f"   Profile Base: {profile_base}\n")
    
    # Run all instances concurrently
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down all instances...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Launch multiple Telegram Web A instances with translation"
    )
    parser.add_argument(
        "--instances", "-n",
        type=int,
        default=2,
        help="Number of browser instances to launch (default: 2)"
    )
    parser.add_argument(
        "--source", "-s",
        type=str,
        default="zh",
        help="User's source language code (default: zh)"
    )
    parser.add_argument(
        "--target", "-t",
        type=str,
        default="en",
        help="Target/foreign language code (default: en)"
    )
    parser.add_argument(
        "--profile-base", "-p",
        type=str,
        default=os.path.expanduser("~/.telegram_profiles"),
        help="Base directory for browser profiles (default: ~/.telegram_profiles)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main(
            num_instances=args.instances,
            source_lang=args.source,
            target_lang=args.target,
            profile_base=args.profile_base
        ))
    except KeyboardInterrupt:
        print("\nBye!")
