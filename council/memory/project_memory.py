"""
Project Memory - 项目级记忆系统

类似 CLAUDE.md 的项目配置加载，让 Agent 自动获取：
- 项目上下文 (WHY/WHAT/HOW)
- 代码风格指南
- 自定义命令和工具
- 已知问题和注意事项

Based on 2025 Best Practices from Anthropic Claude Code
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProjectConfig:
    """项目配置数据"""

    project_root: Path
    name: str = ""
    description: str = ""
    style_guide: str = ""
    custom_commands: Dict[str, str] = field(default_factory=dict)
    caveats: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    raw_configs: Dict[str, str] = field(default_factory=dict)


class ProjectMemory:
    """
    项目级记忆 - 类似 CLAUDE.md

    自动加载项目根目录的配置文件：
    - CLAUDE.md: Claude Code 项目配置
    - CODEMAP.md: 代码地图
    - PROJECT.md: 项目文档
    - .agent/workflows/*.md: 工作流定义

    Usage:
        memory = ProjectMemory("/path/to/project")

        # 获取完整项目上下文
        context = memory.get_context()

        # 获取代码风格指南
        style = memory.get_style_guide()

        # 获取自定义命令
        commands = memory.get_custom_commands()
    """

    # 配置文件优先级 (按顺序加载)
    CONFIG_FILES = [
        "CLAUDE.md",
        "CODEMAP.md",
        "PROJECT.md",
        "README.md",
        ".agent/config.md",
    ]

    # 工作流目录
    WORKFLOW_DIR = ".agent/workflows"

    def __init__(self, project_root: str):
        """
        初始化项目记忆

        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root).resolve()
        self.config = self._load_configs()

    def _load_configs(self) -> ProjectConfig:
        """加载所有项目配置文件"""
        config = ProjectConfig(project_root=self.project_root)

        # 加载主配置文件
        for filename in self.CONFIG_FILES:
            path = self.project_root / filename
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8")
                    config.raw_configs[filename] = content

                    # 解析特定配置
                    if filename == "CLAUDE.md":
                        self._parse_claude_md(content, config)
                    elif filename == "CODEMAP.md":
                        config.description += f"\n\n[Code Map]\n{content[:2000]}"
                    elif filename == "README.md" and not config.name:
                        # 从 README 提取项目名
                        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                        if match:
                            config.name = match.group(1).strip()

                    logger.info(f"[ProjectMemory] 已加载: {filename}")
                except Exception as e:
                    logger.warning(f"[ProjectMemory] 加载 {filename} 失败: {e}")

        # 加载工作流
        workflow_dir = self.project_root / self.WORKFLOW_DIR
        if workflow_dir.exists():
            for wf_file in workflow_dir.glob("*.md"):
                try:
                    content = wf_file.read_text(encoding="utf-8")
                    command_name = wf_file.stem
                    config.custom_commands[command_name] = content
                    logger.info(f"[ProjectMemory] 已加载工作流: {command_name}")
                except Exception as e:
                    logger.warning(f"[ProjectMemory] 加载工作流 {wf_file} 失败: {e}")

        return config

    def _parse_claude_md(self, content: str, config: ProjectConfig) -> None:
        """解析 CLAUDE.md 配置"""
        # 提取项目名称
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            config.name = match.group(1).strip()

        # 提取代码风格指南
        style_match = re.search(
            r"##\s*(?:Style Guide|代码风格|风格指南)\s*\n(.*?)(?=\n##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if style_match:
            config.style_guide = style_match.group(1).strip()

        # 提取注意事项/caveats
        caveats_match = re.search(
            r"##\s*(?:Caveats|注意事项|已知问题)\s*\n(.*?)(?=\n##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if caveats_match:
            caveats_text = caveats_match.group(1).strip()
            config.caveats = [
                line.strip().lstrip("- ")
                for line in caveats_text.split("\n")
                if line.strip().startswith("-")
            ]

        # 提取依赖
        deps_match = re.search(
            r"##\s*(?:Dependencies|依赖)\s*\n(.*?)(?=\n##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if deps_match:
            deps_text = deps_match.group(1).strip()
            config.dependencies = [
                line.strip().lstrip("- ")
                for line in deps_text.split("\n")
                if line.strip().startswith("-")
            ]

    def get_context(self, max_chars: int = 8000) -> str:
        """
        获取格式化的项目上下文

        Args:
            max_chars: 最大字符数限制

        Returns:
            格式化的项目上下文字符串
        """
        parts = []

        # 项目名称和描述
        if self.config.name:
            parts.append(f"# 项目: {self.config.name}")

        # 代码风格
        if self.config.style_guide:
            parts.append(f"\n## 代码风格\n{self.config.style_guide}")

        # 注意事项
        if self.config.caveats:
            parts.append("\n## 注意事项")
            for caveat in self.config.caveats[:5]:
                parts.append(f"- {caveat}")

        # 依赖
        if self.config.dependencies:
            parts.append("\n## 主要依赖")
            for dep in self.config.dependencies[:10]:
                parts.append(f"- {dep}")

        # 可用命令
        if self.config.custom_commands:
            parts.append("\n## 可用工作流命令")
            for cmd in list(self.config.custom_commands.keys())[:10]:
                parts.append(f"- /{cmd}")

        context = "\n".join(parts)

        # 截断到最大长度
        if len(context) > max_chars:
            context = context[:max_chars] + "\n...(truncated)"

        return context

    def get_style_guide(self) -> str:
        """获取代码风格指南"""
        return self.config.style_guide

    def get_custom_commands(self) -> Dict[str, str]:
        """获取自定义命令/工作流"""
        return self.config.custom_commands

    def get_command(self, command_name: str) -> Optional[str]:
        """
        获取特定工作流命令

        Args:
            command_name: 命令名称 (不带 / 前缀)

        Returns:
            工作流内容，不存在时返回 None
        """
        return self.config.custom_commands.get(command_name)

    def get_caveats(self) -> List[str]:
        """获取注意事项列表"""
        return self.config.caveats

    def get_raw_config(self, filename: str) -> Optional[str]:
        """
        获取原始配置文件内容

        Args:
            filename: 配置文件名

        Returns:
            文件内容，不存在时返回 None
        """
        return self.config.raw_configs.get(filename)

    def has_config(self, filename: str) -> bool:
        """检查是否有特定配置文件"""
        return filename in self.config.raw_configs

    def get_stats(self) -> Dict[str, Any]:
        """获取项目记忆统计"""
        return {
            "project_name": self.config.name,
            "config_files_loaded": len(self.config.raw_configs),
            "custom_commands": len(self.config.custom_commands),
            "caveats": len(self.config.caveats),
            "dependencies": len(self.config.dependencies),
            "has_style_guide": bool(self.config.style_guide),
        }


__all__ = ["ProjectMemory", "ProjectConfig"]
