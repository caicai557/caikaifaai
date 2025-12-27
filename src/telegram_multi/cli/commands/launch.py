import asyncio
from typing import Optional
from src.telegram_multi.config import TelegramConfig
from src.telegram_multi.instance_manager import InstanceManager

async def launch_instances(
    config: TelegramConfig,
    instance_id: Optional[str] = None,
    launch_all: bool = False,
) -> None:
    """Launch requested Telegram instances.

    Args:
        config: Loaded Telegram configuration.
        instance_id: Specific instance ID to launch.
        launch_all: Whether to launch all instances.
    """
    print("Initializing Instance Manager...")
    manager = InstanceManager.from_config(config)

    tasks = []

    if launch_all:
        for i_id in manager.list_instances():
            inst = manager.get_instance(i_id)
            if inst:
                print(f"🚀 Launching instance '{i_id}'...")
                tasks.append(inst.start())
    elif instance_id:
        inst = manager.get_instance(instance_id)
        if inst:
            print(f"🚀 Launching instance '{instance_id}'...")
            tasks.append(inst.start())
        else:
            print(f"❌ Error: Instance '{instance_id}' not found in config.")
            raise ValueError(f"Instance '{instance_id}' not found in config")

    if not tasks:
        print("⚠️ No instances to launch.")
        return

    # Execute all start tasks concurrently
    try:
        await asyncio.gather(*tasks)
        print("✨ All requested instances launched.")

        # Keep-alive: Wait until user interrupts
        print("Press Ctrl+C to stop all instances...")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    except Exception as e:
        print(f"❌ Error during launch: {e}")
        raise  # Propagate to cli_main for non-0 exit
