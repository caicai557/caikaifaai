import os
import logging

logger = logging.getLogger(__name__)

__all__ = ["load_prompt"]


def load_prompt(name: str) -> str:
    """
    Load a prompt from the prompts directory.

    Args:
        name: Name of the prompt file (without extension)

    Returns:
        The content of the prompt file.
    """
    # Get the directory of this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, f"{name}.txt")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {file_path}")
        raise ValueError(f"Prompt '{name}' not found")
    except Exception as e:
        logger.error(f"Failed to load prompt {name}: {e}")
        raise
