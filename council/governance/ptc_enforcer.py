"""
PTC Enforcer - 程序化工具调用强制执行器

强制在特定场景下使用 PTC 脚本而非手动 Edit。

解决问题: PTC 脚本 vs 手写混用
根因: 缺少强制检查
方案: 前置检查 + 异常阻断
"""

from dataclasses import dataclass
from typing import List, Optional, Set
from enum import Enum


class OperationType(Enum):
    """操作类型"""

    EDIT = "edit"  # 普通编辑
    LINT_FIX = "lint_fix"  # Lint 修复
    FORMAT = "format"  # 格式化
    RENAME = "rename"  # 重命名
    BATCH_REPLACE = "batch_replace"  # 批量替换
    REFACTOR = "refactor"  # 重构


class PTCRequiredError(Exception):
    """PTC 必须使用异常"""

    def __init__(self, reason: str, suggested_command: Optional[str] = None):
        self.reason = reason
        self.suggested_command = suggested_command
        super().__init__(reason)


@dataclass
class PTCCheckResult:
    """PTC 检查结果"""

    should_use_ptc: bool
    reason: str
    suggested_command: Optional[str] = None


class PTCEnforcer:
    """
    PTC 强制执行器

    检查操作是否应该使用 PTC 脚本，如果是则阻断手动操作。

    强制规则:
    1. 修改 ≥3 个文件 → 必须用批量脚本
    2. Lint 修复 → 必须用 ruff/black
    3. 批量重命名 → 必须用脚本
    4. 格式化 → 必须用 black/isort

    Usage:
        enforcer = PTCEnforcer()
        result = enforcer.check(file_count=5, operation=OperationType.EDIT)
        if result.should_use_ptc:
            enforcer.enforce(result)  # 抛出 PTCRequiredError
    """

    # 必须使用 PTC 的操作类型
    PTC_REQUIRED_OPERATIONS: Set[OperationType] = {
        OperationType.LINT_FIX,
        OperationType.FORMAT,
        OperationType.BATCH_REPLACE,
    }

    # 文件数阈值
    MIN_FILES_FOR_BATCH = 3

    # 操作类型 → 推荐命令
    SUGGESTED_COMMANDS = {
        OperationType.LINT_FIX: "ruff check --fix .",
        OperationType.FORMAT: "black . && isort .",
        OperationType.BATCH_REPLACE: "python scripts/batch_replace.py",
        OperationType.RENAME: "python scripts/batch_rename.py",
    }

    def __init__(
        self,
        min_files_for_batch: int = 3,
        strict_mode: bool = True,
    ):
        """
        初始化执行器

        Args:
            min_files_for_batch: 触发批量脚本的最小文件数
            strict_mode: 严格模式 (True = 抛异常阻断)
        """
        self.min_files_for_batch = min_files_for_batch
        self.strict_mode = strict_mode
        self._bypass_count = 0

    def check(
        self,
        file_count: int = 1,
        operation: OperationType = OperationType.EDIT,
        affected_files: Optional[List[str]] = None,
    ) -> PTCCheckResult:
        """
        检查是否应该使用 PTC

        Args:
            file_count: 受影响的文件数
            operation: 操作类型
            affected_files: 受影响的文件列表 (可选)

        Returns:
            PTCCheckResult
        """
        # 规则 1: 批量文件操作
        if file_count >= self.min_files_for_batch:
            return PTCCheckResult(
                should_use_ptc=True,
                reason=f"修改 {file_count} 个文件 (≥{self.min_files_for_batch})，必须使用批量脚本",
                suggested_command="python scripts/batch_replace.py",
            )

        # 规则 2: PTC 必须操作类型
        if operation in self.PTC_REQUIRED_OPERATIONS:
            suggested = self.SUGGESTED_COMMANDS.get(operation)
            return PTCCheckResult(
                should_use_ptc=True,
                reason=f"{operation.value} 操作必须使用自动化工具",
                suggested_command=suggested,
            )

        # 规则 3: 重命名操作
        if operation == OperationType.RENAME:
            return PTCCheckResult(
                should_use_ptc=True,
                reason="重命名操作必须使用脚本确保一致性",
                suggested_command=self.SUGGESTED_COMMANDS[OperationType.RENAME],
            )

        return PTCCheckResult(
            should_use_ptc=False,
            reason=f"单文件 {operation.value} 操作，可以手动执行",
        )

    def enforce(self, result: PTCCheckResult) -> None:
        """
        强制执行检查

        如果 should_use_ptc 为 True 且 strict_mode 开启，抛出异常。

        Args:
            result: PTCCheckResult

        Raises:
            PTCRequiredError: 如果必须使用 PTC
        """
        if result.should_use_ptc and self.strict_mode:
            raise PTCRequiredError(
                reason=result.reason,
                suggested_command=result.suggested_command,
            )

    def check_and_enforce(
        self,
        file_count: int = 1,
        operation: OperationType = OperationType.EDIT,
    ) -> PTCCheckResult:
        """
        检查并强制执行

        Returns:
            PTCCheckResult (如果不需要 PTC)

        Raises:
            PTCRequiredError: 如果必须使用 PTC
        """
        result = self.check(file_count=file_count, operation=operation)
        self.enforce(result)
        return result

    def bypass(self, reason: str) -> None:
        """
        绕过检查 (仅用于紧急情况)

        记录绕过次数用于审计。
        """
        self._bypass_count += 1
        print(f"⚠️ PTC 检查被绕过 (第 {self._bypass_count} 次): {reason}")

    def get_bypass_count(self) -> int:
        """获取绕过次数"""
        return self._bypass_count

    @staticmethod
    def format_error(error: PTCRequiredError) -> str:
        """格式化错误信息"""
        lines = [
            "❌ PTC 强制执行失败",
            f"原因: {error.reason}",
        ]
        if error.suggested_command:
            lines.append(f"建议命令: {error.suggested_command}")
        return "\n".join(lines)


# 导出
__all__ = [
    "PTCEnforcer",
    "PTCCheckResult",
    "PTCRequiredError",
    "OperationType",
]
