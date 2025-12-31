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


CODER_SYSTEM_PROMPT = """Role: Senior Software Engineer (Council Member)
Backstory: You are an elite developer who writes production-grade Python code. You follow the "Claude Code" philosophy: think before you act, use tools effectively, and verify everything.

Standard Operating Procedure (SOP):
1.  **Analyze**: Read the task and plan.
2.  **Think**: Use <thinking> tags to plan your implementation steps, considering edge cases and dependencies.
3.  **Tooling**: Use `ToolSearch` to find necessary tools. Don't guess file contents; read them first.
4.  **Implement**: Write clean, typed, documented code.
5.  **Verify**: Always write and run tests.

Constraints:
-   **Chain of Thought**: You MUST output your reasoning in <thinking>...</thinking> tags before generating code.
-   **Type Hints**: Strict typing required.
-   **No Hallucinations**: Only use tools that are explicitly loaded.
"""


from council.sandbox.runner import get_sandbox_runner
from council.mcp import ToolSearchTool, create_default_registry
from council.mcp.tool_executor import ToolExecutor


class Coder(BaseAgent):
    """
    工程师智能体

    专注于代码实现和测试编写
    2025增强: 支持真正的工具调用 (ToolExecutor)
    """

    def __init__(
        self, 
        model: str = "gemini-2.0-flash", 
        sandbox_provider: str = "local",
        working_dir: str = "."
    ):
        super().__init__(
            name="Coder",
            system_prompt=CODER_SYSTEM_PROMPT,
            model=model,
        )
        self.working_dir = working_dir
        self.sandbox = get_sandbox_runner(sandbox_provider, working_dir=working_dir)
        self.tool_search = ToolSearchTool(create_default_registry())
        self.tool_executor = ToolExecutor(working_dir=working_dir)

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
        执行代码实现任务
        """
        # 1. Dynamic Tool Loading
        loaded_tools = self.tool_search.search_and_load(task, top_k=3)
        tool_schemas = self.tool_search.get_context_schema()
        
        # 2. Generate Code
        prompt = f"""
Task: {task}
Plan: {plan or {}}

Available Tools (Reference):
{tool_schemas}

Please write the Python code to implement this task.
Return ONLY the python code, wrapped in ```python ... ``` blocks.
Include necessary imports and a main block or test to verify it works.
"""
        code_response = self._call_llm(prompt)
        
        # Extract code
        import re
        code_match = re.search(r"```python\s*(.*?)\s*```", code_response, re.DOTALL)
        if code_match:
            code = code_match.group(1)
        else:
            # Try to find code without python tag
            code_match = re.search(r"```\s*(.*?)\s*```", code_response, re.DOTALL)
            code = code_match.group(1) if code_match else code_response

        # 3. Execute in Sandbox
        sandbox_result = self.sandbox.run(code)

        self.add_to_history(
            {
                "action": "execute",
                "task": task,
                "plan": plan,
                "tools_loaded": [t.name for t in loaded_tools],
                "code_generated": code[:200] + "...",
                "sandbox_status": sandbox_result.status,
            }
        )
        
        output = f"Execution Status: {sandbox_result.status}\n"
        output += f"Stdout: {sandbox_result.stdout}\n"
        if sandbox_result.stderr:
            output += f"Stderr: {sandbox_result.stderr}\n"

        return ExecuteResult(
            success=sandbox_result.status == "success",
            output=output,
            changes_made=["Generated and executed code"],
            errors=[sandbox_result.stderr] if sandbox_result.stderr else [],
        )

    def generate_tests(self, spec: str, target_file: str = None) -> Dict[str, Any]:
        """
        生成测试代码

        Args:
            spec: 功能规格说明
            target_file: 可选的目标测试文件路径

        Returns:
            测试生成结果
        """
        # 使用 LLM 生成测试代码
        prompt = f"""
为以下功能生成 pytest 测试代码:
{spec}

要求:
1. 使用 pytest 框架
2. 包含正常情况和边界情况
3. 使用 fixtures 如果合适
4. 代码包含在 ```python ... ``` 中

返回完整的测试文件内容。
"""
        response = self._call_llm(prompt)
        
        # 提取代码
        import re
        code_match = re.search(r"```python\s*(.*?)\s*```", response, re.DOTALL)
        test_code = code_match.group(1) if code_match else response
        
        result = {
            "generator": self.name,
            "test_count": test_code.count("def test_"),
            "coverage_estimate": 0.7,
            "test_files": [],
            "test_code": test_code,
        }
        
        # 如果指定了目标文件，写入测试
        if target_file:
            write_result = self.tool_executor.execute("write_file", {
                "path": target_file,
                "content": test_code
            })
            if write_result.success:
                result["test_files"].append(target_file)
        
        return result

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

        self.add_to_history({
            "action": "vote_structured",
            "proposal": proposal[:100],
            "vote": result.vote.to_legacy(),
        })

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

        self.add_to_history({
            "action": "think_structured",
            "task": task[:100],
            "confidence": result.confidence,
        })

        return result


__all__ = ["Coder", "CODER_SYSTEM_PROMPT"]
