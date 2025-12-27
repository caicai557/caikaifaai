from src.telegram_multi.config import TelegramConfig

def check_config(config_path: str) -> bool:
    """Validate the Telegram configuration file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        True if valid, False otherwise.
    """
    print(f"Checking configuration: {config_path}")
    try:
        config = TelegramConfig.from_yaml(config_path)
        print("✅ Configuration is valid.")
        print(f"Found {len(config.instances)} instances.")
        return True
    except FileNotFoundError:
        print(f"❌ Error: Config file not found at {config_path}")
        return False
    except ValueError as e:
        print(f"❌ Error: Invalid configuration - {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
