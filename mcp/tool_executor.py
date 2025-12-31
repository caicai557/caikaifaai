"""
Tool Executor - 工具执行器

实际执行工具调用，桥接 ToolSearch 定义与真实操作。
2025 最佳实践: 工具是能力的载体 + 最小权限原则
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    data: Optional[Any] = None


@dataclass
class ToolPermission:
    """工具权限定义"""
    name: str
    allowed: bool = True
    requires_approval: bool = False
    max_calls_per_session: int = -1  # -1 = 无限制
    allowed_paths: List[str] = field(default_factory=list)  # 空 = 所有路径


class ToolAllowlist:
    """
    工具白名单 - 最小权限原则
    
    参考: Anthropic Claude Code SDK 安全最佳实践
    - 默认拒绝所有工具
    - 显式允许需要的工具
    - 支持调用次数限制
    """
    
    def __init__(self, default_allow: bool = False):
        self.default_allow = default_allow
        self.permissions: Dict[str, ToolPermission] = {}
        self.call_counts: Dict[str, int] = {}
    
    def allow(
        self, 
        tool_name: str, 
        requires_approval: bool = False,
        max_calls: int = -1,
        paths: List[str] = None
    ) -> "ToolAllowlist":
        """添加工具到白名单"""
        self.permissions[tool_name] = ToolPermission(
            name=tool_name,
            allowed=True,
            requires_approval=requires_approval,
            max_calls_per_session=max_calls,
            allowed_paths=paths or []
        )
        return self  # 链式调用
    
    def deny(self, tool_name: str) -> "ToolAllowlist":
        """从白名单移除工具"""
        self.permissions[tool_name] = ToolPermission(tool_name, allowed=False)
        return self
    
    def can_execute(self, tool_name: str, path: str = None) -> Tuple[bool, str]:
        """检查是否可以执行工具"""
        perm = self.permissions.get(tool_name)
        
        # 检查是否在白名单
        if perm is None:
            if self.default_allow:
                return True, ""
            return False, f"Tool '{tool_name}' not in allowlist"
        
        if not perm.allowed:
            return False, f"Tool '{tool_name}' is denied"
        
        # 检查调用次数
        if perm.max_calls_per_session > 0:
            current = self.call_counts.get(tool_name, 0)
            if current >= perm.max_calls_per_session:
                return False, f"Tool '{tool_name}' exceeded max calls ({perm.max_calls_per_session})"
        
        # 检查路径限制
        if path and perm.allowed_paths:
            path_ok = any(path.startswith(p) for p in perm.allowed_paths)
            if not path_ok:
                return False, f"Path '{path}' not in allowed paths"
        
        return True, ""
    
    def record_call(self, tool_name: str):
        """记录工具调用"""
        self.call_counts[tool_name] = self.call_counts.get(tool_name, 0) + 1
    
    def reset_counts(self):
        """重置调用计数"""
        self.call_counts.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "allowed_tools": [k for k, v in self.permissions.items() if v.allowed],
            "denied_tools": [k for k, v in self.permissions.items() if not v.allowed],
            "call_counts": dict(self.call_counts),
        }


def create_default_allowlist() -> ToolAllowlist:
    """创建默认白名单 (安全模式)"""
    return (
        ToolAllowlist(default_allow=False)
        .allow("read_file")
        .allow("list_dir")
        .allow("grep_search")
        .allow("git_status")
        .allow("write_file", requires_approval=True)
        .allow("git_commit", requires_approval=True)
        .allow("run_command", requires_approval=True, max_calls=10)
    )


class ToolExecutor:
    """
    工具执行器 - 执行实际的工具操作
    
    将 ToolSearch 中定义的工具连接到真实操作。
    所有操作都限制在 working_dir 内以确保安全。
    2025增强: 支持工具白名单
    """
    
    def __init__(self, working_dir: str = ".", allowlist: ToolAllowlist = None):
        self.working_dir = Path(working_dir).resolve()
        self.allowlist = allowlist or create_default_allowlist()
    
    def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        # 1. 白名单检查
        path = params.get("path")
        allowed, reason = self.allowlist.can_execute(tool_name, path)
        if not allowed:
            return ToolResult(
                success=False,
                output="",
                error=f"Permission denied: {reason}"
            )
        
        # 记录调用
        self.allowlist.record_call(tool_name)
        
        # 2. 工具路由
        handlers = {
            "read_file": self._read_file,
            "write_file": self._write_file,
            "list_dir": self._list_dir,
            "grep_search": self._grep_search,
            "git_status": self._git_status,
            "git_commit": self._git_commit,
            "run_command": self._run_command,
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}"
            )
        
        try:
            return handler(params)
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def _safe_path(self, path: str) -> Path:
        """确保路径在 working_dir 内"""
        full_path = (self.working_dir / path).resolve()
        if not str(full_path).startswith(str(self.working_dir)):
            raise ValueError(f"Path escape attempt: {path}")
        return full_path
    
    def _read_file(self, params: Dict[str, Any]) -> ToolResult:
        """读取文件"""
        path = self._safe_path(params.get("path", ""))
        if not path.exists():
            return ToolResult(False, "", f"File not found: {path}")
        
        try:
            content = path.read_text(encoding="utf-8")
            return ToolResult(True, content, data={"lines": len(content.splitlines())})
        except UnicodeDecodeError:
            return ToolResult(False, "", "Binary file, cannot read as text")
    
    def _write_file(self, params: Dict[str, Any]) -> ToolResult:
        """写入文件"""
        path = self._safe_path(params.get("path", ""))
        content = params.get("content", "")
        
        # 创建父目录
        path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_text(content, encoding="utf-8")
        return ToolResult(True, f"Written {len(content)} bytes to {path.name}")
    
    def _list_dir(self, params: Dict[str, Any]) -> ToolResult:
        """列出目录"""
        path = self._safe_path(params.get("path", "."))
        if not path.is_dir():
            return ToolResult(False, "", f"Not a directory: {path}")
        
        items = []
        for item in path.iterdir():
            prefix = "📁" if item.is_dir() else "📄"
            items.append(f"{prefix} {item.name}")
        
        return ToolResult(True, "\n".join(sorted(items)), data={"count": len(items)})
    
    def _grep_search(self, params: Dict[str, Any]) -> ToolResult:
        """搜索文件内容"""
        pattern = params.get("pattern", "")
        path = self._safe_path(params.get("path", "."))
        
        try:
            result = subprocess.run(
                ["grep", "-rn", pattern, str(path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.working_dir
            )
            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout[:2000],  # 限制输出
                error=result.stderr if result.returncode != 0 else None
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, "", "Search timeout")
        except FileNotFoundError:
            # grep 不可用时使用 Python 实现
            return self._python_grep(pattern, path)
    
    def _python_grep(self, pattern: str, path: Path) -> ToolResult:
        """Python 实现的 grep"""
        import re
        matches = []
        
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                for i, line in enumerate(content.splitlines(), 1):
                    if re.search(pattern, line):
                        rel_path = file_path.relative_to(self.working_dir)
                        matches.append(f"{rel_path}:{i}: {line[:100]}")
            except (UnicodeDecodeError, PermissionError):
                continue
        
        return ToolResult(
            success=len(matches) > 0,
            output="\n".join(matches[:50]),  # 限制结果数
            data={"match_count": len(matches)}
        )
    
    def _git_status(self, params: Dict[str, Any]) -> ToolResult:
        """Git 状态"""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=self.working_dir
        )
        return ToolResult(
            success=result.returncode == 0,
            output=result.stdout or "No changes",
            error=result.stderr if result.returncode != 0 else None
        )
    
    def _git_commit(self, params: Dict[str, Any]) -> ToolResult:
        """Git 提交"""
        message = params.get("message", "Auto commit")
        
        # 先 add
        subprocess.run(["git", "add", "."], cwd=self.working_dir)
        
        # 然后 commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            cwd=self.working_dir
        )
        return ToolResult(
            success=result.returncode == 0,
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else None
        )
    
    def _run_command(self, params: Dict[str, Any]) -> ToolResult:
        """执行命令"""
        command = params.get("command", "")
        
        # 安全检查：禁止危险命令
        dangerous = ["rm -rf /", "sudo", "mkfs", ":(){:|:&};:"]
        if any(d in command for d in dangerous):
            return ToolResult(False, "", f"Dangerous command blocked: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.working_dir
            )
            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout[:5000],  # 限制输出
                error=result.stderr if result.returncode != 0 else None
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, "", "Command timeout (60s)")


# 导出
__all__ = [
    "ToolExecutor", 
    "ToolResult",
    "ToolPermission",
    "ToolAllowlist",
    "create_default_allowlist"
]
