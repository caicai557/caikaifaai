"""
PreToolUse Hook - 工具执行前拦截钩子

在任何工具执行前强制介入，实现安全安检系统。
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

from council.hooks.base import (
    BaseHook,
    HookType,
    HookAction,
    HookResult,
    HookContext,
)

logger = logging.getLogger(__name__)


# 危险命令黑名单
DANGEROUS_COMMANDS: Set[str] = {
    "rm -rf",
    "rm -r /",
    "rm -rf /",
    "dd if=",
    "mkfs",
    "format c:",
    "> /dev/sda",
    "chmod -R 777",
    "chmod 777 /",
}

# 敏感路径黑名单
SENSITIVE_PATHS: Set[str] = {
    ".ssh",
    ".ssh/",
    ".gnupg",
    ".gnupg/",
    ".env",
    ".env.local",
    ".env.production",
    "secrets/",
    "credentials/",
    "/etc/passwd",
    "/etc/shadow",
    "~/.bashrc",
    "~/.zshrc",
}

# 危险正则模式
DANGEROUS_PATTERNS: List[re.Pattern] = [
    re.compile(
        r"rm\s+-[rf]+\s+/(?!\w)", re.IGNORECASE
    ),  # rm -rf / 但不匹配 rm -rf /tmp
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
    re.compile(r"__import__\s*\(", re.IGNORECASE),
    re.compile(r"subprocess\.(?:run|call|Popen)", re.IGNORECASE),
    re.compile(r"os\.system\s*\(", re.IGNORECASE),
    re.compile(r"DROP\s+(?:TABLE|DATABASE)", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM\s+\w+\s*;?\s*$", re.IGNORECASE),  # DELETE 不带 WHERE
]


class PreToolUseHook(BaseHook):
    """
    执行前置拦截钩子

    功能：
    1. 拦截工具调用参数
    2. 检查危险命令
    3. 检查敏感路径
    4. RBAC 策略验证
    5. 可选的合规审计

    Usage:
        hook = PreToolUseHook()
        result = await hook.execute(context)
        if result.action == HookAction.BLOCK:
            print(f"Blocked: {result.message}")
    """

    def __init__(
        self,
        dangerous_commands: Optional[Set[str]] = None,
        sensitive_paths: Optional[Set[str]] = None,
        allowed_tools: Optional[Set[str]] = None,
        sudo_token: Optional[str] = None,
        priority: int = 50,
    ):
        """
        初始化前置拦截钩子

        Args:
            dangerous_commands: 额外的危险命令集合
            sensitive_paths: 额外的敏感路径集合
            allowed_tools: 允许的工具白名单（None 表示允许所有）
            sudo_token: sudo 令牌（用于授权危险操作）
            priority: 优先级
        """
        super().__init__(name="pre_tool_use", priority=priority)
        self._dangerous_commands = DANGEROUS_COMMANDS | (dangerous_commands or set())
        self._sensitive_paths = SENSITIVE_PATHS | (sensitive_paths or set())
        self._allowed_tools = allowed_tools
        self._sudo_token = sudo_token

    @property
    def hook_type(self) -> HookType:
        return HookType.PRE_TOOL_USE

    def set_sudo_token(self, token: str) -> None:
        """设置 sudo 令牌"""
        self._sudo_token = token

    def clear_sudo_token(self) -> None:
        """清除 sudo 令牌"""
        self._sudo_token = None

    async def execute(self, context: HookContext) -> HookResult:
        """
        执行前置安全检查

        Args:
            context: 钩子上下文

        Returns:
            HookResult: 检查结果
        """
        tool_name = context.tool_name or ""
        tool_args = context.tool_args or {}

        metadata = {
            "tool_name": tool_name,
            "checks_performed": [],
        }

        # Check 1: 工具白名单
        if self._allowed_tools and tool_name not in self._allowed_tools:
            return HookResult(
                action=HookAction.BLOCK,
                message=f"Tool '{tool_name}' is not in the allowed list",
                metadata={**metadata, "reason": "tool_not_allowed"},
            )
        metadata["checks_performed"].append("tool_whitelist")

        # Check 2: 危险命令检查
        content = self._extract_content(tool_args)
        if content:
            danger_check = self._check_dangerous_content(content)
            if danger_check:
                if self._sudo_token:
                    logger.warning(
                        f"Dangerous command allowed with sudo: {danger_check}"
                    )
                    metadata["sudo_override"] = True
                else:
                    return HookResult(
                        action=HookAction.BLOCK,
                        message=f"Dangerous command blocked: {danger_check}",
                        metadata={
                            **metadata,
                            "reason": "dangerous_command",
                            "pattern": danger_check,
                        },
                    )
        metadata["checks_performed"].append("dangerous_commands")

        # Check 3: 敏感路径检查
        paths = self._extract_paths(tool_args)
        for path in paths:
            if self._is_sensitive_path(path):
                if self._sudo_token:
                    logger.warning(f"Sensitive path access allowed with sudo: {path}")
                    metadata["sudo_override"] = True
                else:
                    return HookResult(
                        action=HookAction.BLOCK,
                        message=f"Access to sensitive path blocked: {path}",
                        metadata={**metadata, "reason": "sensitive_path", "path": path},
                    )
        metadata["checks_performed"].append("sensitive_paths")

        # Check 4: 特定工具的额外检查
        if tool_name in {"bash", "shell", "execute"}:
            cmd_check = self._check_shell_command(content)
            if cmd_check:
                if self._sudo_token:
                    metadata["sudo_override"] = True
                else:
                    return HookResult(
                        action=HookAction.BLOCK,
                        message=f"Shell command blocked: {cmd_check}",
                        metadata={
                            **metadata,
                            "reason": "shell_command",
                            "detail": cmd_check,
                        },
                    )
        metadata["checks_performed"].append("shell_specific")

        logger.debug(f"PreToolUse check passed for {tool_name}")
        return HookResult(
            action=HookAction.ALLOW,
            message="All security checks passed",
            metadata=metadata,
        )

    def _extract_content(self, args: Dict[str, Any]) -> str:
        """从工具参数中提取内容"""
        content_keys = [
            "content",
            "command",
            "code",
            "script",
            "query",
            "text",
            "input",
        ]
        for key in content_keys:
            if key in args:
                value = args[key]
                if isinstance(value, str):
                    return value
        return ""

    def _extract_paths(self, args: Dict[str, Any]) -> List[str]:
        """从工具参数中提取路径"""
        paths = []
        path_keys = [
            "path",
            "file",
            "filepath",
            "filename",
            "directory",
            "dir",
            "target",
        ]
        for key in path_keys:
            if key in args:
                value = args[key]
                if isinstance(value, str):
                    paths.append(value)
                elif isinstance(value, list):
                    paths.extend([p for p in value if isinstance(p, str)])
        return paths

    def _check_dangerous_content(self, content: str) -> Optional[str]:
        """检查内容是否包含危险命令"""
        content_lower = content.lower()

        # 检查黑名单命令
        for cmd in self._dangerous_commands:
            if cmd.lower() in content_lower:
                return cmd

        # 检查危险正则模式
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(content):
                return pattern.pattern

        return None

    def _is_sensitive_path(self, path: str) -> bool:
        """检查路径是否敏感"""
        path_lower = path.lower()
        for sensitive in self._sensitive_paths:
            if sensitive.lower() in path_lower:
                return True
        return False

    def _check_shell_command(self, command: str) -> Optional[str]:
        """检查 shell 命令的额外规则"""
        if not command:
            return None

        # 检查管道到危险命令
        if "|" in command:
            parts = command.split("|")
            for part in parts:
                if any(d in part.lower() for d in ["rm ", "dd ", "mkfs"]):
                    return f"Pipe to dangerous command: {part.strip()}"

        # 检查重定向覆盖关键文件
        if ">" in command:
            match = re.search(r">\s*([^\s]+)", command)
            if match:
                target = match.group(1)
                if self._is_sensitive_path(target):
                    return f"Redirect to sensitive path: {target}"

        return None


# 导出
__all__ = ["PreToolUseHook", "DANGEROUS_COMMANDS", "SENSITIVE_PATHS"]
