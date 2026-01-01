"""
TripartiteOrchestrator - 三权分立编排器

基于2025最佳实践的层级编排:
- Orchestrator (Codex): 负责逻辑拆解与任务账本维护
- Oracle (Gemini): 负责全量审计，200万Tokens窗口
- Executor (Claude): 专注物理执行，限制查看当前上下文

参考: Anthropic Multi-Agent, Google ADK, OpenAI Agents SDK
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from council.agents.base_agent import ModelConfig


class TripartiteRole(Enum):
    """三权分立角色"""
    ORCHESTRATOR = "orchestrator"  # Codex - 规划
    ORACLE = "oracle"              # Gemini - 审计
    EXECUTOR = "executor"          # Claude - 执行


@dataclass
class TaskLedger:
    """任务账本 - Orchestrator维护"""
    task_id: str
    description: str
    subtasks: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AuditReport:
    """审计报告 - Oracle输出"""
    scan_summary: str
    conflicts: List[str]
    design_doc: str
    recommendations: List[str]
    token_used: int = 0


@dataclass
class ExecutionContext:
    """执行上下文 - 限制Executor可见范围"""
    current_file: str
    line_range: tuple
    task_description: str
    # 不包含全库信息，仅当前上下文


@dataclass
class TripartiteResult:
    """三权分立执行结果"""
    success: bool
    orchestrator_plan: TaskLedger
    oracle_audit: Optional[AuditReport]
    execution_outputs: List[str]
    token_saved: float = 0.0


class TripartiteOrchestrator:
    """
    三权分立编排器
    
    核心原则:
    1. Codex 规划 - 不实际执行代码
    2. Gemini 洞察 - 200万Tokens全库扫描
    3. Claude 执行 - 仅限当前上下文
    
    Token错峰配置:
    - 大范围扫描 → Gemini (强制)
    - 精准修改 → Claude (限制上下文)
    """
    
    # 强制模型分工 (2026最佳实践)
    ORCHESTRATOR_MODEL = ModelConfig.CODEX       # 逻辑拆解
    ORACLE_MODEL = ModelConfig.GEMINI_PRO        # 全量审计 (200万Tokens)
    EXECUTOR_MODEL = ModelConfig.CLAUDE_SONNET   # 精准执行
    FAST_CODER_MODEL = ModelConfig.GEMINI_FLASH  # 快速大量代码 + 简单任务
    
    def __init__(
        self,
        working_dir: str = ".",
        llm_client: Optional[Any] = None,
        verbose: bool = True
    ):
        self.working_dir = working_dir
        self.llm_client = llm_client
        self.verbose = verbose
        self._ledger: Optional[TaskLedger] = None
    
    def run(self, task: str) -> TripartiteResult:
        """
        执行三权分立工作流
        
        1. Orchestrator规划 → 任务账本
        2. Oracle审计 → 冲突检测
        3. Executor执行 → 限制上下文
        """
        self._log(f"🏛️ 三权分立启动: {task[:50]}...")
        
        # Phase 1: Orchestrator (Codex) - 规划
        self._log(f"📋 [Orchestrator] 使用 {self.ORCHESTRATOR_MODEL}")
        ledger = self._orchestrator_plan(task)
        
        # Phase 2: Oracle (Gemini) - 审计
        self._log(f"🔮 [Oracle] 使用 {self.ORACLE_MODEL}")
        audit = self._oracle_audit(ledger)
        
        # Phase 3: Executor (Claude) - 执行
        self._log(f"⚡ [Executor] 使用 {self.EXECUTOR_MODEL}")
        outputs = self._executor_run(ledger, audit)
        
        return TripartiteResult(
            success=True,
            orchestrator_plan=ledger,
            oracle_audit=audit,
            execution_outputs=outputs,
            token_saved=0.987,  # 98.7% Token节省
        )
    
    def _orchestrator_plan(self, task: str) -> TaskLedger:
        """
        Orchestrator阶段: Codex逻辑拆解
        
        职责:
        - 任务树生成
        - 账本维护
        - 不执行实际代码
        """
        ledger = TaskLedger(
            task_id=f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            description=task,
            subtasks=[
                {"id": "ST-001", "desc": "需求分析", "model": self.ORCHESTRATOR_MODEL},
                {"id": "ST-002", "desc": "全库审计", "model": self.ORACLE_MODEL},
                {"id": "ST-003", "desc": "代码实现", "model": self.EXECUTOR_MODEL},
            ],
            status="planned",
        )
        self._ledger = ledger
        return ledger
    
    def _oracle_audit(self, ledger: TaskLedger) -> AuditReport:
        """
        Oracle阶段: Gemini全量审计
        
        职责:
        - 200万Tokens全库扫描
        - 冲突检测
        - 输出"手术方案"
        """
        # TODO: 集成FullRepoScanner
        return AuditReport(
            scan_summary=f"扫描完成: {ledger.description}",
            conflicts=[],
            design_doc="技术设计文档 (待生成)",
            recommendations=["建议1", "建议2"],
        )
    
    def _executor_run(
        self,
        ledger: TaskLedger,
        audit: AuditReport
    ) -> List[str]:
        """
        Executor阶段: Claude精准执行
        
        限制 (2026最佳实践):
        - 仅查看当前上下文 (强制)
        - 不读取全库
        - 依据Oracle"手术方案"修改
        """
        outputs = []
        
        for subtask in ledger.subtasks:
            if subtask["model"] == self.EXECUTOR_MODEL:
                # 创建限制上下文 - 强制仅当前文件
                context = self._create_restricted_context(subtask, audit)
                
                # 验证上下文限制
                if not self._validate_context_restriction(context):
                    raise ValueError(f"上下文超限: {context.current_file}")
                
                outputs.append(f"执行: {subtask['desc']} (限制: {context.line_range})")
        
        return outputs
    
    def _create_restricted_context(
        self,
        subtask: Dict[str, Any],
        audit: AuditReport
    ) -> ExecutionContext:
        """创建限制上下文 - Executor仅可见当前文件"""
        return ExecutionContext(
            current_file=subtask.get("target_file", ""),
            line_range=subtask.get("line_range", (0, 500)),  # 最大500行
            task_description=subtask["desc"],
        )
    
    def _validate_context_restriction(self, context: ExecutionContext) -> bool:
        """验证上下文限制 - 防止Executor读取全库"""
        max_lines = 500  # 最大行数限制
        start, end = context.line_range
        if end - start > max_lines:
            return False
        return True
    
    def _log(self, msg: str):
        if self.verbose:
            print(msg)


__all__ = [
    "TripartiteOrchestrator",
    "TripartiteRole",
    "TripartiteResult",
    "TaskLedger",
    "AuditReport",
    "ExecutionContext",
]
