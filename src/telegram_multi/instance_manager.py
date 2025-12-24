"""
Instance manager for coordinating multiple Telegram browser contexts.

Contract:
- Manages multiple concurrent BrowserContexts
- Prevents port conflicts (unique port allocation)
- Supports 3+ simultaneous instances
- Loads from TelegramConfig
"""

from typing import Dict, List, Optional
from src.telegram_multi.config import TelegramConfig, InstanceConfig
from src.telegram_multi.browser_context import BrowserContext


class InstanceManager:
    """Manages multiple concurrent Telegram browser instances."""

    def __init__(self):
        """Initialize instance manager."""
        self.instances: Dict[str, BrowserContext] = {}
        self._next_port = 9222  # Starting debug port

    def add_instance(self, config: InstanceConfig) -> BrowserContext:
        """Add a new browser instance to the manager.

        Args:
            config: InstanceConfig with id and profile_path

        Returns:
            Created BrowserContext instance
        """
        if config.id in self.instances:
            raise ValueError(f"Instance '{config.id}' already exists")

        # Allocate unique port
        port = self._next_port
        self._next_port += 1

        context = BrowserContext(
            instance_id=config.id, profile_path=config.profile_path, port=port
        )
        self.instances[config.id] = context
        return context

    def get_instance(self, instance_id: str) -> Optional[BrowserContext]:
        """Retrieve instance by ID.

        Args:
            instance_id: Instance identifier

        Returns:
            BrowserContext or None if not found
        """
        return self.instances.get(instance_id)

    def remove_instance(self, instance_id: str) -> None:
        """Remove instance from manager.

        Args:
            instance_id: Instance identifier
        """
        if instance_id in self.instances:
            del self.instances[instance_id]

    def list_instances(self) -> List[str]:
        """List all instance IDs.

        Returns:
            List of instance identifiers
        """
        return list(self.instances.keys())

    @classmethod
    def from_config(cls, config: TelegramConfig) -> "InstanceManager":
        """Create manager from TelegramConfig.

        Args:
            config: TelegramConfig with instances list

        Returns:
            Populated InstanceManager
        """
        manager = cls()
        for instance_config in config.instances:
            manager.add_instance(instance_config)
        return manager
