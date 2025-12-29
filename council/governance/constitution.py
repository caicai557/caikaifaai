"""
Constitution - 规则拦截器 (Rule Interceptor)

在任何 LLM 推理之前运行的静态硬编码规则集。
实现 FSM 状态感知的访问控制。

Reference: doc/GOVERNANCE_BEST_PRACTICES.md - Pattern A
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Set
from enum import Enum


class SpeakerState(Enum):
    """议长状态机状态"""
    IDLE = "idle"
    DEBATING = "debating"
    VOTING = "voting"
    EXECUTING = "executing"


class Violation(Exception):
    """宪法违规异常"""
    def __init__(self, rule: str, message: str):
        self.rule = rule
        self.message = message
        super().__init__(f"[VIOLATION:{rule}] {message}")


@dataclass
class ConstitutionConfig:
    """宪法配置"""
    # 危险命令黑名单
    dangerous_commands: Set[str] = None
    # 最大重复内容相似度 (0-1)
    max_repetition_similarity: float = 0.8
    # 需要 sudo_token 的操作
    sudo_required_actions: Set[str] = None

    def __post_init__(self):
        if self.dangerous_commands is None:
            self.dangerous_commands = {"rm -rf", "dd if=", "mkfs", "DROP TABLE", "DELETE FROM"}
        if self.sudo_required_actions is None:
            self.sudo_required_actions = {"deploy", "push_to_main", "delete_branch"}


class Constitution:
    """
    宪法拦截器

    在 Agent 消息进入 LLM 之前进行规则校验。

    Usage:
        constitution = Constitution()
        constitution.set_state(SpeakerState.VOTING)

        try:
            constitution.check({"tool": "think", "content": "..."})
        except Violation as e:
            print(f"Blocked: {e.message}")
    """

    def __init__(self, config: Optional[ConstitutionConfig] = None):
        self.config = config or ConstitutionConfig()
        self.speaker_state = SpeakerState.IDLE
        self._recent_messages: list = []  # For repetition detection

    def set_state(self, state: SpeakerState) -> None:
        """设置当前议长状态"""
        self.speaker_state = state

    def check(self, msg: Dict[str, Any], sudo_token: Optional[str] = None) -> bool:
        """
        检查消息是否违反宪法

        Args:
            msg: 消息字典，应包含 "tool" 和 "content" 字段
            sudo_token: 可选的 sudo 令牌，用于授权危险操作

        Returns:
            True if valid

        Raises:
            Violation: if any rule is violated
        """
        tool = msg.get("tool", "")
        content = msg.get("content", "")

        # Rule 1: Voting Phase Silence
        self._check_voting_phase(tool)

        # Rule 2: Dangerous Commands
        self._check_dangerous_commands(content, sudo_token)

        # Rule 3: Repetition Detection
        self._check_repetition(content)

        # Rule 4: Sudo-Required Actions
        self._check_sudo_required(tool, sudo_token)

        # Record for repetition tracking
        self._recent_messages.append(content)
        if len(self._recent_messages) > 10:
            self._recent_messages.pop(0)

        return True

    def _check_voting_phase(self, tool: str) -> None:
        """Rule 1: 投票阶段只允许 vote 工具"""
        if self.speaker_state == SpeakerState.VOTING and tool != "vote":
            raise Violation(
                rule="VOTING_SILENCE",
                message="Silence in court! Only votes are allowed during VOTING phase."
            )

    def _check_dangerous_commands(self, content: str, sudo_token: Optional[str]) -> None:
        """Rule 2: 危险命令需要 sudo"""
        content_lower = content.lower()
        for cmd in self.config.dangerous_commands:
            if cmd.lower() in content_lower:
                if not sudo_token:
                    raise Violation(
                        rule="DANGEROUS_COMMAND",
                        message=f"Dangerous command '{cmd}' requires sudo_token authorization."
                    )

    def _check_repetition(self, content: str) -> None:
        """Rule 3: 禁止重复内容"""
        if not content or len(content) < 50:
            return

        for prev in self._recent_messages[-3:]:  # Check last 3 messages
            if prev and self._similarity(content, prev) > self.config.max_repetition_similarity:
                raise Violation(
                    rule="REPETITION",
                    message="Do not repeat yourself. Add new information or conclude."
                )

    def _check_sudo_required(self, tool: str, sudo_token: Optional[str]) -> None:
        """Rule 4: 特定操作需要 sudo"""
        if tool in self.config.sudo_required_actions and not sudo_token:
            raise Violation(
                rule="SUDO_REQUIRED",
                message=f"Action '{tool}' requires sudo_token authorization."
            )

    def _similarity(self, a: str, b: str) -> float:
        """简单的 Jaccard 相似度计算"""
        if not a or not b:
            return 0.0
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0


# 导出
__all__ = [
    "Constitution",
    "ConstitutionConfig",
    "SpeakerState",
    "Violation",
]
