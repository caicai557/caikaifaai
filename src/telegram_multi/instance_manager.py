"""
Instance Manager - 多实例管理器

Stub module to satisfy import requirements.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from src.telegram_multi.config import TelegramConfig, InstanceConfig
from src.telegram_multi.browser_context import BrowserContext


class InstanceManager:
    """
    多实例生命周期管理器
    
    管理多个 Telegram Web 实例的创建、启动、停止。
    """
    
    def __init__(self):
        self._instances: Dict[str, BrowserContext] = {}
        self._next_port = 9222
        
    @classmethod
    def from_config(cls, config: TelegramConfig) -> "InstanceManager":
        """从配置创建实例管理器"""
        manager = cls()
        for inst_cfg in config.instances:
            manager.add_instance(inst_cfg, config.global_settings)
        return manager
        
    def add_instance(self, config: InstanceConfig, global_settings: Any = None) -> BrowserContext:
        """添加实例"""
        ctx = BrowserContext(
            instance_config=config,
            global_settings=global_settings,
            port=self._next_port,
        )
        self._instances[config.id] = ctx
        self._next_port += 1
        return ctx
        
    def get_instance(self, instance_id: str) -> Optional[BrowserContext]:
        """获取实例"""
        return self._instances.get(instance_id)
        
    def remove_instance(self, instance_id: str) -> bool:
        """移除实例"""
        if instance_id in self._instances:
            del self._instances[instance_id]
            return True
        return False
        
    def list_instances(self) -> List[str]:
        """列出所有实例 ID"""
        return list(self._instances.keys())
        
    async def start_all(self) -> Dict[str, bool]:
        """启动所有实例"""
        results = {}
        for inst_id, ctx in self._instances.items():
            results[inst_id] = await ctx.start()
        return results
        
    async def stop_all(self) -> Dict[str, bool]:
        """停止所有实例"""
        results = {}
        for inst_id, ctx in self._instances.items():
            results[inst_id] = await ctx.stop()
        return results


__all__ = ["InstanceManager"]
