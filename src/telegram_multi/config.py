"""
Telegram Multi Configuration - Stub Module

This is a stub to satisfy import requirements.
Full implementation pending.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
import yaml


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = False
    executable_path: Optional[str] = None


@dataclass
class TranslationConfig:
    """翻译配置"""
    enabled: bool = True
    provider: str = "google"
    source_lang: str = "zh"
    target_lang: str = "en"


@dataclass
class InstanceConfig:
    """单实例配置"""
    id: str = "default"
    profile_path: str = "./profiles/default"
    translation: TranslationConfig = field(default_factory=TranslationConfig)


@dataclass  
class GlobalSettings:
    """全局设置"""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    debug: bool = False


@dataclass
class TelegramConfig:
    """Telegram 多开配置"""
    global_settings: GlobalSettings = field(default_factory=GlobalSettings)
    instances: List[InstanceConfig] = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, path: str) -> "TelegramConfig":
        """从 YAML 文件加载配置"""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            
        return cls(
            global_settings=GlobalSettings(
                browser=BrowserConfig(**data.get('browser', {})),
                debug=data.get('debug', False),
            ),
            instances=[
                InstanceConfig(
                    id=inst.get('id', 'default'),
                    profile_path=inst.get('profile_path', './profiles/default'),
                    translation=TranslationConfig(**inst.get('translation', {})),
                )
                for inst in data.get('instances', [])
            ],
        )


__all__ = [
    "TelegramConfig",
    "InstanceConfig", 
    "BrowserConfig",
    "TranslationConfig",
    "GlobalSettings",
]
