#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    content = read_text(path)
    if old not in content:
        raise ValueError(f"Pattern not found in {path}")
    write_text(path, content.replace(old, new, 1))


def replace_between(path: Path, start: str, end: str, replacement: str) -> None:
    content = read_text(path)
    start_idx = content.find(start)
    if start_idx == -1:
        raise ValueError(f"Start marker not found in {path}")
    end_idx = content.find(end, start_idx)
    if end_idx == -1:
        raise ValueError(f"End marker not found in {path}")
    new_content = content[:start_idx] + replacement + content[end_idx:]
    write_text(path, new_content)


def update_redis_store() -> None:
    path = ROOT / "council" / "persistence" / "redis_store.py"
    replace_once(
        path,
        "return await self.load(thread_id, int(step))",
        "return await self.load_at_step(thread_id, int(step))",
    )


def update_governance_gateway() -> None:
    path = ROOT / "council" / "governance" / "gateway.py"
    content = read_text(path)

    marker = "\n\n@dataclass\nclass ApprovalRequest:"
    if "class DecisionType(Enum):" not in content:
        insert = """

class DecisionType(Enum):
    \"\"\"Decision types requiring human approval\"\"\"

    MODEL_SELECTION = "model_selection"
    ARCHITECTURE_CHANGE = "architecture_change"
    DEPLOY_STRATEGY = "deploy_strategy"
    DATA_RETENTION = "data_retention"
    SECURITY_EXCEPTION = "security_exception"


class ApprovalKind(Enum):
    \"\"\"Approval request kind\"\"\"

    ACTION = "action"
    DECISION = "decision"
"""
        content = content.replace(marker, insert + marker, 1)
        write_text(path, content)

    approval_request_block = """@dataclass
class ApprovalRequest:
    \"\"\"审批请求\"\"\"

    request_id: str
    risk_level: RiskLevel
    description: str
    affected_resources: List[str]
    rationale: str
    action_type: Optional[ActionType] = None
    decision_type: Optional[DecisionType] = None
    request_kind: ApprovalKind = ApprovalKind.ACTION
    council_decision: Optional[Dict[str, Any]] = None
    requestor: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    approved: Optional[bool] = None
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        \"\"\"转换为字典\"\"\"
        return {
            "request_id": self.request_id,
            "request_kind": self.request_kind.value,
            "action_type": self.action_type.value if self.action_type else None,
            "decision_type": self.decision_type.value if self.decision_type else None,
            "risk_level": self.risk_level.value,
            "description": self.description,
            "affected_resources": self.affected_resources,
            "rationale": self.rationale,
            "council_decision": self.council_decision,
            "requestor": self.requestor,
            "created_at": self.created_at.isoformat(),
            "approved": self.approved,
            "approver": self.approver,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


"""

    replace_between(
        path,
        "@dataclass\nclass ApprovalRequest:",
        "# 高风险动作定义",
        approval_request_block,
    )

    content = read_text(path)
    if "HIGH_RISK_DECISIONS" not in content:
        insert = """
# 高风险决策定义
HIGH_RISK_DECISIONS = {
    DecisionType.ARCHITECTURE_CHANGE: RiskLevel.HIGH,
    DecisionType.DEPLOY_STRATEGY: RiskLevel.HIGH,
    DecisionType.SECURITY_EXCEPTION: RiskLevel.CRITICAL,
    DecisionType.DATA_RETENTION: RiskLevel.MEDIUM,
    DecisionType.MODEL_SELECTION: RiskLevel.LOW,
}

"""
        marker = "\n# 危险内容模式 (Regex)"
        content = content.replace(marker, insert + marker, 1)
        write_text(path, content)

    replace_once(
        path,
        "return False\n\n    def auto_approve_with_council(",
        """return False\n\n    def requires_decision_approval(\n        self,\n        decision_type: DecisionType,\n    ) -> bool:\n        \"\"\"\n        检查关键决策是否需要人工审批\n        \"\"\"\n        risk = HIGH_RISK_DECISIONS.get(decision_type, RiskLevel.LOW)\n        return risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]\n\n    def auto_approve_with_council(""",
    )

    replace_once(
        path,
        "request = ApprovalRequest(\n            request_id=request_id,\n            action_type=action_type,\n            risk_level=risk_level,\n            description=description,\n            affected_resources=affected_resources,\n            rationale=rationale,\n            council_decision=council_decision,\n            requestor=requestor,\n        )",
        "request = ApprovalRequest(\n            request_id=request_id,\n            action_type=action_type,\n            decision_type=None,\n            request_kind=ApprovalKind.ACTION,\n            risk_level=risk_level,\n            description=description,\n            affected_resources=affected_resources,\n            rationale=rationale,\n            council_decision=council_decision,\n            requestor=requestor,\n        )",
    )

    replace_once(
        path,
        'def approve(self, request_id: str, approver: str = "human") -> bool:',
        """def create_decision_request(
        self,
        decision_type: DecisionType,
        description: str,
        affected_resources: List[str],
        rationale: str,
        council_decision: Optional[Dict[str, Any]] = None,
        requestor: str = "system",
    ) -> ApprovalRequest:
        \"\"\"
        创建关键决策审批请求
        \"\"\"
        self._request_counter += 1
        request_id = (
            f"REQ-{datetime.now().strftime('%Y%m%d')}-{self._request_counter:04d}"
        )

        risk_level = HIGH_RISK_DECISIONS.get(decision_type, RiskLevel.LOW)

        request = ApprovalRequest(
            request_id=request_id,
            action_type=None,
            decision_type=decision_type,
            request_kind=ApprovalKind.DECISION,
            risk_level=risk_level,
            description=description,
            affected_resources=affected_resources,
            rationale=rationale,
            council_decision=council_decision,
            requestor=requestor,
        )

        self.pending_requests[request_id] = request
        return request

    def approve(self, request_id: str, approver: str = "human") -> bool:""",
    )

    replace_once(
        path,
        'print(f"类型: {request.action_type.value}")',
        """if request.request_kind == ApprovalKind.DECISION:\n            if request.decision_type:\n                type_label = f\"decision:{request.decision_type.value}\"\n            else:\n                type_label = \"decision:unknown\"\n        else:\n            type_label = request.action_type.value if request.action_type else \"action:unknown\"\n        print(f\"类型: {type_label}\")""",
    )


def update_governance_init() -> None:
    path = ROOT / "council" / "governance" / "__init__.py"
    replace_once(
        path,
        "    ActionType,\n    RiskLevel,\n)",
        "    ActionType,\n    DecisionType,\n    ApprovalKind,\n    RiskLevel,\n)",
    )
    replace_once(
        path,
        '"ActionType",\n    "RiskLevel",\n]',
        '"ActionType",\n    "DecisionType",\n    "ApprovalKind",\n    "RiskLevel",\n]',
    )


def update_pyproject() -> None:
    path = ROOT / "pyproject.toml"
    content = read_text(path)
    if "distributed = [" not in content:
        insert = """distributed = [
    "celery>=5.3",
    "redis>=5.0",
]

"""
        content = content.replace("enhancements = [\n", "enhancements = [\n", 1)
        content = content.replace("]\n\nall = [", "]\n\n" + insert + "all = [", 1)
        write_text(path, content)

    replace_once(
        path,
        '"cesi-council[dev,council,enhancements]",',
        '"cesi-council[dev,council,enhancements,distributed]",',
    )


def add_distributed_files() -> None:
    distributed_dir = ROOT / "council" / "distributed"
    write_text(
        distributed_dir / "__init__.py",
        """# Distributed Module
from council.distributed.config import CeleryConfig
from council.distributed.celery_app import make_celery_app, HAS_CELERY
from council.distributed.tasks import app, run_agent_task

__all__ = [
    "CeleryConfig",
    "make_celery_app",
    "HAS_CELERY",
    "app",
    "run_agent_task",
]
""",
    )

    write_text(
        distributed_dir / "config.py",
        """from dataclasses import dataclass
import os
from typing import Tuple


@dataclass
class CeleryConfig:
    broker_url: str = os.environ.get(
        "CELERY_BROKER_URL",
        "amqp://guest:guest@localhost:5672//",
    )
    result_backend: str = os.environ.get(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/0",
    )
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: Tuple[str, ...] = ("json",)
    timezone: str = "UTC"
    enable_utc: bool = True

    def to_dict(self) -> dict:
        return {
            "broker_url": self.broker_url,
            "result_backend": self.result_backend,
            "task_serializer": self.task_serializer,
            "result_serializer": self.result_serializer,
            "accept_content": list(self.accept_content),
            "timezone": self.timezone,
            "enable_utc": self.enable_utc,
        }
""",
    )

    write_text(
        distributed_dir / "celery_app.py",
        """from typing import Optional

from council.distributed.config import CeleryConfig

try:
    from celery import Celery

    HAS_CELERY = True
except ImportError:  # pragma: no cover - depends on optional dependency
    Celery = None
    HAS_CELERY = False


def make_celery_app(name: str = "council", config: Optional[CeleryConfig] = None):
    if not HAS_CELERY:
        raise ImportError("celery is required. Install with: pip install celery")

    cfg = config or CeleryConfig()
    app = Celery(name, broker=cfg.broker_url, backend=cfg.result_backend)
    app.conf.update(
        task_serializer=cfg.task_serializer,
        result_serializer=cfg.result_serializer,
        accept_content=list(cfg.accept_content),
        timezone=cfg.timezone,
        enable_utc=cfg.enable_utc,
        task_track_started=True,
        broker_connection_retry_on_startup=True,
    )
    return app
""",
    )

    write_text(
        distributed_dir / "tasks.py",
        """import importlib.util
import sys
from typing import Dict, Any

from council.distributed.celery_app import make_celery_app, HAS_CELERY

if HAS_CELERY:
    app = make_celery_app()

    @app.task(name="council.run_agent")
    def run_agent_task(script_path: str, task: str) -> Dict[str, Any]:
        if not script_path:
            raise ValueError("script_path is required")

        spec = importlib.util.spec_from_file_location("agent_module", script_path)
        if not spec or not spec.loader:
            raise ImportError(f"Could not load script: {script_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["agent_module"] = module
        spec.loader.exec_module(module)

        agent = getattr(module, "agent", None)
        if not agent:
            from council.agents.base_agent import BaseAgent

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, BaseAgent):
                    agent = attr
                    break

        if not agent:
            raise ValueError(f"No agent instance found in {script_path}")

        result = agent.execute(task)
        return {
            "success": result.success,
            "output": result.output,
            "changes_made": result.changes_made,
            "errors": result.errors,
        }
else:
    app = None

    def run_agent_task(*_args, **_kwargs):
        raise ImportError("celery is required. Install with: pip install celery")
""",
    )


def main() -> None:
    update_redis_store()
    update_governance_gateway()
    update_governance_init()
    update_pyproject()
    add_distributed_files()


if __name__ == "__main__":
    main()
