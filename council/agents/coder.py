"""
Coder - 工程师智能体
负责代码实现、测试编写、功能开发
"""

from typing import Optional, Dict, Any
from council.agents.base_agent import (
    BaseAgent,
    Vote,
    VoteDecision,
    ThinkResult,
    ExecuteResult,
)
from council.tools.file_system import FileTools
import os


CODER_SYSTEM_PROMPT = """你是一名高级软件工程师，专注于代码实现和测试。

## 核心职责
1. **代码实现**: 将设计转化为高质量代码
2. **测试编写**: TDD 驱动，确保覆盖率 ≥ 90%
3. **代码审查**: 识别代码质量问题

## 编码原则
- Small Diffs: 每次改动尽量小 (≤200 行)
- 防御性编程: 空值/异常/竞态必须处理
- 可读性优先: 代码是写给人看的
- 测试先行: 先写测试，后写实现

## 输出格式
1. 实现计划 (步骤列表)
2. 代码差异 (unified diff)
3. 验证命令 + 预期结果
4. 回滚步骤

## 禁止行为
- 不做无测试的实现
- 不引入大量新依赖
- 不做无依据的大重构
"""


class Coder(BaseAgent):
    """
    工程师智能体

    专注于代码实现和测试编写
    """

    def __init__(
        self, model: str = "gemini-2.0-flash", llm_client: Optional["LLMClient"] = None
    ):
        super().__init__(
            name="Coder",
            system_prompt=CODER_SYSTEM_PROMPT,
            model=model,
            llm_client=llm_client,
        )
        self.file_tools = FileTools(root_dir=os.getcwd())

    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """
        从实现角度分析任务
        """
        prompt = f"""
任务: {task}
上下文: {context or {}}

作为高级工程师，请分析实现方案。请提供：
1. 实现计划 (Plan) - 步骤列表
2. 潜在问题 (Concerns) - 每行一个
3. 建议 (Suggestions) - 每行一个
4. 置信度 (Confidence) - 0.0 到 1.0

返回格式：
[Plan]
...
[Concerns]
...
[Suggestions]
...
[Confidence]
0.9
"""
        response = self._call_llm(prompt)

        # 解析逻辑 (与 Architect 类似，复用结构)
        analysis = ""
        concerns = []
        suggestions = []
        confidence = 0.5

        current_section = None
        for line in response.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("[Plan]"):
                current_section = "analysis"
            elif line.startswith("[Concerns]"):
                current_section = "concerns"
            elif line.startswith("[Suggestions]"):
                current_section = "suggestions"
            elif line.startswith("[Confidence]"):
                current_section = "confidence"
            elif current_section == "analysis":
                analysis += line + "\n"
            elif current_section == "concerns":
                if line.startswith("-") or line[0].isdigit():
                    concerns.append(line.lstrip("- 1234567890."))
            elif current_section == "suggestions":
                if line.startswith("-") or line[0].isdigit():
                    suggestions.append(line.lstrip("- 1234567890."))
            elif current_section == "confidence":
                try:
                    confidence = float(line)
                except:
                    pass

        self.add_to_history({"action": "think", "task": task, "context": context})

        return ThinkResult(
            analysis=analysis.strip() or response,
            concerns=concerns,
            suggestions=suggestions,
            confidence=confidence,
            context={"perspective": "implementation"},
        )

    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """
        对提案进行实现可行性投票
        """
        prompt = f"""
提案: {proposal}
上下文: {context or {}}

作为工程师，请评估实现的可行性、复杂度和测试可测性。
投票选项: APPROVE, APPROVE_WITH_CHANGES, HOLD, REJECT

返回格式：
Vote: [DECISION]
Confidence: [0.0-1.0]
Rationale: [理由]
"""
        response = self._call_llm(prompt)

        import re

        decision = VoteDecision.HOLD
        confidence = 0.5
        rationale = response

        decision_match = re.search(
            r"Vote:\s*(APPROVE_WITH_CHANGES|APPROVE|HOLD|REJECT)",
            response,
            re.IGNORECASE,
        )
        if decision_match:
            d_str = decision_match.group(1).upper()
            if d_str == "APPROVE":
                decision = VoteDecision.APPROVE
            elif d_str == "APPROVE_WITH_CHANGES":
                decision = VoteDecision.APPROVE_WITH_CHANGES
            elif d_str == "HOLD":
                decision = VoteDecision.HOLD
            elif d_str == "REJECT":
                decision = VoteDecision.REJECT

        conf_match = re.search(r"Confidence:\s*(\d*\.?\d+)", response)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
            except:
                pass

        rationale_match = re.search(
            r"Rationale:\s*(.+)", response, re.DOTALL | re.IGNORECASE
        )
        if rationale_match:
            rationale = rationale_match.group(1).strip()

        self.add_to_history(
            {"action": "vote", "proposal": proposal, "decision": decision.value}
        )

        return Vote(
            agent_name=self.name,
            decision=decision,
            confidence=confidence,
            rationale=rationale,
        )

    def execute(
        self, task: str, plan: Optional[Dict[str, Any]] = None
    ) -> ExecuteResult:
        """
        执行编码任务 - 2025: 集成 FileTools
        """
        # 简单解析任务以确定是否写入文件 (模拟)
        # 实际应让 LLM 生成 tool 调用

        output_log = []
        changes = []

        # 模拟: 如果任务包含 "Create file", 尝试写入
        if "Create file" in task or "write" in task.lower():
            # 这里是一个硬编码演示，实际中应由 LLM 解析目标路径和内容
            # 假设任务是 "Create file test.txt with content hello"
            if "test.txt" in task:
                result = self.file_tools.write_file("test.txt", "hello world")
                output_log.append(result)
                changes.append("Written test.txt")
            else:
                output_log.append(
                    "Coder received task but needs explicit path parsing (TODO)."
                )
        else:
            output_log.append(f"Coder executed: {task}")

        self.add_to_history(
            {"action": "execute", "task": task, "plan": plan, "output": output_log}
        )

        return ExecuteResult(
            success=True,
            output="\n".join(output_log),
            changes_made=changes,
        )

    def generate_tests(self, spec: str) -> Dict[str, Any]:
        """
        生成测试代码

        Args:
            spec: 功能规格说明

        Returns:
            测试生成结果
        """
        return {
            "generator": self.name,
            "test_count": 0,
            "coverage_estimate": 0.0,
            "test_files": [],
        }

    def review_code(self, code: str) -> Dict[str, Any]:
        """
        代码审查

        Args:
            code: 待审查代码

        Returns:
            审查结果
        """
        return {
            "reviewer": self.name,
            "issues": [],
            "suggestions": [],
            "approval": True,
        }

    # ============================================================
    # 2025 Best Practice: Structured Protocol Methods
    # These methods save ~70% tokens compared to NL versions
    # ============================================================

    def vote_structured(self, proposal: str, context: Optional[Dict[str, Any]] = None):
        """
        [2025 Best Practice] 对提案进行实现可行性投票 (结构化输出)

        使用 MinimalVote schema，节省 ~70% Token。
        """
        from council.protocol.schema import MinimalVote

        prompt = f"""
作为工程师，评估以下提案的实现可行性:
提案: {proposal}
上下文: {context or {}}

请投票并识别风险类别 (sec=安全, perf=性能, maint=维护, arch=架构)。
"""
        result = self._call_llm_structured(prompt, MinimalVote)

        self.add_to_history(
            {
                "action": "vote_structured",
                "proposal": proposal[:100],
                "vote": result.vote.to_legacy(),
            }
        )

        return result

    def think_structured(self, task: str, context: Optional[Dict[str, Any]] = None):
        """
        [2025 Best Practice] 从实现角度分析任务 (结构化输出)

        使用 MinimalThinkResult schema，限制输出长度。
        """
        from council.protocol.schema import MinimalThinkResult

        prompt = f"""
作为工程师，分析以下任务的实现方案:
任务: {task}
上下文: {context or {}}

请提供简短摘要 (最多200字)、潜在问题 (最多3点)、和建议 (最多3点)。
"""
        result = self._call_llm_structured(prompt, MinimalThinkResult)
        result.perspective = "implementation"

        self.add_to_history(
            {
                "action": "think_structured",
                "task": task[:100],
                "confidence": result.confidence,
            }
        )

        return result


__all__ = ["Coder", "CODER_SYSTEM_PROMPT"]
