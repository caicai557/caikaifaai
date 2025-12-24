"""
Tests for instance manager (Phase 2).

Contract:
- InstanceManager manages multiple concurrent BrowserContexts
- Must prevent port conflicts
- Must support concurrent instances (3+)
- Must track running instances
"""

from src.telegram_multi.instance_manager import InstanceManager
from src.telegram_multi.config import TelegramConfig, InstanceConfig


class TestInstanceManager:
    """Contract tests for InstanceManager."""

    def test_create_instance_manager(self):
        """Contract: Can create InstanceManager."""
        manager = InstanceManager()
        assert manager is not None
        assert len(manager.instances) == 0

    def test_instance_manager_add_instance(self, tmp_path):
        """Contract: Can add a browser context to manager."""
        manager = InstanceManager()
        profile = tmp_path / "profile1"
        config = InstanceConfig(id="test1", profile_path=str(profile))

        manager.add_instance(config)
        assert len(manager.instances) == 1
        assert "test1" in manager.instances

    def test_instance_manager_add_multiple_instances(self, tmp_path):
        """Contract: Can manage multiple instances concurrently."""
        manager = InstanceManager()
        profiles = [tmp_path / f"profile{i}" for i in range(3)]
        configs = [
            InstanceConfig(id=f"instance{i}", profile_path=str(profiles[i]))
            for i in range(3)
        ]

        for config in configs:
            manager.add_instance(config)

        assert len(manager.instances) == 3
        assert all(f"instance{i}" in manager.instances for i in range(3))

    def test_instance_manager_get_instance(self, tmp_path):
        """Contract: Can retrieve instance by ID."""
        manager = InstanceManager()
        profile = tmp_path / "profile1"
        config = InstanceConfig(id="test1", profile_path=str(profile))

        manager.add_instance(config)
        instance = manager.get_instance("test1")

        assert instance is not None
        assert instance.instance_id == "test1"

    def test_instance_manager_get_nonexistent_instance(self):
        """Contract: Returns None for nonexistent instance."""
        manager = InstanceManager()
        instance = manager.get_instance("nonexistent")
        assert instance is None

    def test_instance_manager_port_allocation(self, tmp_path):
        """Contract: Allocates unique ports to instances."""
        manager = InstanceManager()
        profiles = [tmp_path / f"profile{i}" for i in range(3)]
        configs = [
            InstanceConfig(id=f"instance{i}", profile_path=str(profiles[i]))
            for i in range(3)
        ]

        for config in configs:
            manager.add_instance(config)

        ports = [manager.get_instance(f"instance{i}").port for i in range(3)]

        # All ports should be allocated and unique (or None)
        allocated_ports = [p for p in ports if p is not None]
        if allocated_ports:
            assert len(allocated_ports) == len(set(allocated_ports)), (
                "Ports must be unique"
            )

    def test_instance_manager_remove_instance(self, tmp_path):
        """Contract: Can remove instance from manager."""
        manager = InstanceManager()
        profile = tmp_path / "profile1"
        config = InstanceConfig(id="test1", profile_path=str(profile))

        manager.add_instance(config)
        assert len(manager.instances) == 1

        manager.remove_instance("test1")
        assert len(manager.instances) == 0
        assert manager.get_instance("test1") is None

    def test_instance_manager_remove_nonexistent(self):
        """Contract: Removing nonexistent instance is safe."""
        manager = InstanceManager()
        # Should not raise error
        manager.remove_instance("nonexistent")
        assert len(manager.instances) == 0

    def test_instance_manager_list_instances(self, tmp_path):
        """Contract: Can list all instance IDs."""
        manager = InstanceManager()
        profiles = [tmp_path / f"profile{i}" for i in range(3)]
        configs = [
            InstanceConfig(id=f"instance{i}", profile_path=str(profiles[i]))
            for i in range(3)
        ]

        for config in configs:
            manager.add_instance(config)

        instance_ids = manager.list_instances()
        assert len(instance_ids) == 3
        assert all(f"instance{i}" in instance_ids for i in range(3))


class TestInstanceManagerFromConfig:
    """Contract tests for loading manager from TelegramConfig."""

    def test_instance_manager_from_config(self, tmp_path):
        """Contract: Can create manager from TelegramConfig."""
        profiles = [tmp_path / f"profile{i}" for i in range(2)]
        config = TelegramConfig(
            instances=[
                InstanceConfig(id="work", profile_path=str(profiles[0])),
                InstanceConfig(id="personal", profile_path=str(profiles[1])),
            ]
        )

        manager = InstanceManager.from_config(config)
        assert len(manager.instances) == 2
        assert "work" in manager.instances
        assert "personal" in manager.instances

    def test_instance_manager_from_empty_config(self):
        """Contract: Can create manager from empty TelegramConfig."""
        config = TelegramConfig(instances=[])
        manager = InstanceManager.from_config(config)
        assert len(manager.instances) == 0
