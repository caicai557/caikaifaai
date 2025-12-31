"""
File System Tools for Agents
Provides safe file access within the project sandbox.
"""

import os
import logging

logger = logging.getLogger(__name__)


class FileTools:
    """
    文件系统工具集
    强制限制在项目根目录下，防止越权访问。
    """

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def _is_safe_path(self, path: str) -> bool:
        """检查路径是否在根目录下"""
        abs_path = os.path.abspath(os.path.join(self.root_dir, path))
        return abs_path.startswith(self.root_dir)

    def read_file(self, path: str) -> str:
        """读取文件内容"""
        if not self._is_safe_path(path):
            return f"Error: Access denied. Path must be within {self.root_dir}"

        full_path = os.path.join(self.root_dir, path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except Exception as e:
            return f"Error reading file {path}: {e}"

    def write_file(self, path: str, content: str) -> str:
        """写入文件内容 (覆盖模式)"""
        if not self._is_safe_path(path):
            return f"Error: Access denied. Path must be within {self.root_dir}"

        full_path = os.path.join(self.root_dir, path)

        # 保护关键目录
        if ".git" in full_path or ".env" in full_path:
            return f"Error: Write denied to protected path: {path}"

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Success: File written to {path}"
        except Exception as e:
            return f"Error writing file {path}: {e}"

    def list_dir(self, path: str = ".") -> str:
        """列出目录内容"""
        if not self._is_safe_path(path):
            return f"Error: Access denied. Path must be within {self.root_dir}"

        full_path = os.path.join(self.root_dir, path)
        try:
            entries = os.listdir(full_path)
            # 过滤隐藏文件
            visible = [e for e in entries if not e.startswith(".")]
            return "\n".join(visible)
        except Exception as e:
            return f"Error listing directory {path}: {e}"
