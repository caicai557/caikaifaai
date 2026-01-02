"""
Workflow Engine - 2026 SOP 状态机

强制执行 PM -> Architecture -> QA 的三阶段流程。
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """开发流程阶段"""

    PM = "pm_phase"  # 交互式需求析构
    ARCH = "arch_phase"  # 多智能体理事会审议
    QA = "qa_phase"  # TDD 前置物理约束
    COMPLETE = "complete"  # 完成


@dataclass
class WorkflowState:
    """工作流状态"""

    phase: WorkflowPhase = WorkflowPhase.PM
    context: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)  # path -> description
    checks_passed: List[str] = field(default_factory=list)


class WorkflowEngine:
    """
    SOP 强制执行引擎

    Hard constraints:
    - No Arch phase without PRD
    - No QA phase without Architectural Consensus
    - No Merge without Tests & Coverage
    """

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.state = WorkflowState(context=context or {})

    def current_phase(self) -> WorkflowPhase:
        return self.state.phase

    def transition_to(self, new_phase: WorkflowPhase) -> bool:
        """尝试流转到新阶段"""
        if new_phase == self.state.phase:
            return True

        # 验证转换条件
        if new_phase == WorkflowPhase.ARCH:
            return self._can_enter_arch()
        elif new_phase == WorkflowPhase.QA:
            return self._can_enter_qa()
        elif new_phase == WorkflowPhase.COMPLETE:
            return self._can_complete()

        # 允许回退
        if self._is_rollback(new_phase):
            logger.info(f"Rolling back to {new_phase}")
            self.state.phase = new_phase
            return True

        logger.warning(f"Invalid transition from {self.state.phase} to {new_phase}")
        return False

    def check_prerequisites(self, phase: WorkflowPhase) -> List[str]:
        """检查进入某阶段的先决条件"""
        missing = []
        if phase == WorkflowPhase.ARCH:
            if not self.has_artifact("PRD.md") and not self.has_artifact(
                "implementation_plan.md"
            ):
                missing.append("PRD or Implementation Plan")
        elif phase == WorkflowPhase.QA:
            if "architectural_consensus" not in self.state.checks_passed:
                missing.append("Architectural Consensus (Vote)")
        elif phase == WorkflowPhase.COMPLETE:
            if "tests_passed" not in self.state.checks_passed:
                missing.append("Passing Tests")
            if "coverage_check" not in self.state.checks_passed:
                missing.append("Test Coverage > 90%")
        return missing

    def register_artifact(self, name: str, path: str):
        """注册产物"""
        self.state.artifacts[name] = path
        logger.info(f"Registered artifact: {name} at {path}")

    def record_check(self, check_name: str):
        """记录检查通过"""
        if check_name not in self.state.checks_passed:
            self.state.checks_passed.append(check_name)
            logger.info(f"Check passed: {check_name}")

    def has_artifact(self, name_fragment: str) -> bool:
        """检查是否有某类产物"""
        return any(name_fragment in name for name in self.state.artifacts)

    def _can_enter_arch(self) -> bool:
        # PM -> Arch
        if self.state.phase != WorkflowPhase.PM:
            return False

        # 必须有 PRD
        if not self.check_prerequisites(WorkflowPhase.ARCH):
            self.state.phase = WorkflowPhase.ARCH
            return True
        return False

    def _can_enter_qa(self) -> bool:
        # Arch -> QA
        if self.state.phase != WorkflowPhase.ARCH:
            return False

        # 必须有共识
        if not self.check_prerequisites(WorkflowPhase.QA):
            self.state.phase = WorkflowPhase.QA
            return True
        return False

    def _can_complete(self) -> bool:
        # QA -> Complete
        if self.state.phase != WorkflowPhase.QA:
            return False

        if not self.check_prerequisites(WorkflowPhase.COMPLETE):
            self.state.phase = WorkflowPhase.COMPLETE
            return True
        return False

    def _is_rollback(self, new_phase: WorkflowPhase) -> bool:
        """检查是否是回退操作"""
        order = [
            WorkflowPhase.PM,
            WorkflowPhase.ARCH,
            WorkflowPhase.QA,
            WorkflowPhase.COMPLETE,
        ]
        current_idx = order.index(self.state.phase)
        new_idx = order.index(new_phase)
        return new_idx < current_idx

    def force_phase(self, phase: WorkflowPhase):
        """强制设置阶段 (仅用于调试或人工干预)"""
        logger.warning(f"Forcing phase to {phase}")
        self.state.phase = phase


__all__ = ["WorkflowEngine", "WorkflowPhase", "WorkflowState"]
