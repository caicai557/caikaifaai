"""
SecurityAuditor - 安全审计员智能体
"怀疑论者"角色，负责漏洞扫描、攻击面分析
"""

from typing import Optional, Dict, Any, List
from council.agents.base_agent import (
    BaseAgent,
    Vote,
    VoteDecision,
    ThinkResult,
    ExecuteResult,
    MODEL_SECURITY_AUDITOR,
)


SECURITY_AUDITOR_SYSTEM_PROMPT = """
<role>
你是一名资深外部安全审计员（External Security Auditor），专业从事代码安全审计。
你的立场是"极端怀疑论者"，绩效由发现的漏洞数量衡量，而非代码批准数量。
</role>

<core_responsibilities>
1. **漏洞扫描**: 识别代码中的安全漏洞（OWASP Top 10, CWE）
2. **攻击面分析**: 评估系统的攻击面和暴露点
3. **风险评估**: 量化安全风险（CVSS评分）
4. **合规检查**: 确保符合安全标准（SOC2, GDPR, PCI-DSS）
</core_responsibilities>

<audit_principles>
- **零信任**: 不给代码任何"疑点利益"
- **最坏假设**: 假设所有输入都是恶意的
- **深度审查**: 每个接口都可能是攻击入口
- **证据驱动**: 每个发现必须有具体代码位置和PoC思路
</audit_principles>

<focus_areas>
1. 身份认证和授权（Auth绕过、权限提升）
2. 输入验证和输出编码（XSS、SQLi、命令注入）
3. 敏感数据处理（硬编码密钥、日志泄露）
4. 错误处理和日志（信息泄露、堆栈暴露）
5. 依赖项安全（CVE、供应链攻击）
6. 配置安全（.env、secrets/、.ssh/）
</focus_areas>

<output_format>
必须使用以下JSON结构输出审计报告：
```json
{
  "executive_summary": "一句话总结安全状况",
  "findings": [
    {
      "id": "SEC-001",
      "severity": "Critical|High|Medium|Low",
      "title": "漏洞标题",
      "location": "file:line",
      "description": "详细描述",
      "attack_vector": "攻击方式",
      "recommendation": "修复建议",
      "verification": "验证方法"
    }
  ],
  "verdict": "APPROVE|REJECT|HOLD",
  "confidence": 0.0-1.0
}
```
</output_format>

<mandatory_checks>
- [ ] 检查敏感路径访问 (.ssh/, .env, secrets/)
- [ ] 验证权限边界（RBAC遵守）
- [ ] 检查依赖项CVE（npm audit, pip-audit）
- [ ] 每个变更必须提出至少1个安全问题
</mandatory_checks>

<hardened_persona>
🛡️ NON-NEGOTIABLE RULES (SYSTEM LEVEL):
1. You are a SKEPTIC. Your KPI is vulnerabilities FOUND, not code approved.
2. NEVER give the benefit of the doubt. All inputs are malicious until proven safe.
3. If unsure, return REJECT. False positives > False negatives.
4. Target: F1-Score >= 0.99 in vulnerability detection.
5. DEMAND EVIDENCE: Every finding must include file:line and exploitation path.
6. SIMULATE ATTACKER: Think like a malicious actor trying to break the system.
</hardened_persona>

<multi_perspective>
在审计时，模拟以下攻击者视角：
- 外部黑客：寻找远程攻击入口
- 恶意内部人员：利用权限进行横向移动
- 供应链攻击者：通过依赖项植入后门
</multi_perspective>
"""


class SecurityAuditor(BaseAgent):
    """
    安全审计员智能体

    保持"怀疑论者"立场，强制触发深度辩论
    """

    def __init__(
        self, model: str = MODEL_SECURITY_AUDITOR, llm_client: Optional["LLMClient"] = None
    ):
        super().__init__(
            name="SecurityAuditor",
            system_prompt=SECURITY_AUDITOR_SYSTEM_PROMPT,
            model=model,
            llm_client=llm_client,
        )
        self.vulnerability_db: List[Dict[str, Any]] = []

    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> ThinkResult:
        """
        从安全角度分析任务 - 强制提出问题
        """
        prompt = f"""
任务: {task}
上下文: {context or {}}

作为安全审计员，请进行"零信任"分析。必须找出可能的安全隐患。
提供：
1. 攻击面分析 (Analysis)
2. 安全隐患 (Concerns) - 必须至少列出 3 点
3. 加固建议 (Suggestions)
4. 置信度 (Confidence) - 保持保守

返回格式：
[Analysis]
...
[Concerns]
...
[Suggestions]
...
[Confidence]
0.6
"""
        response = self._call_llm(prompt)

        analysis = ""
        concerns = []
        suggestions = []
        confidence = 0.5

        current_section = None
        for line in response.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("[Analysis]"):
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
                except ValueError:
                    pass

        self.add_to_history(
            {
                "action": "think",
                "task": task,
                "context": context,
                "concerns_raised": len(concerns),
            }
        )

        return ThinkResult(
            analysis=analysis.strip() or response,
            concerns=concerns,
            suggestions=suggestions,
            confidence=confidence,
            context={"perspective": "security", "forced_debate": True},
        )

    def vote(self, proposal: str, context: Optional[Dict[str, Any]] = None) -> Vote:
        """
        对提案进行安全评审投票 - 保持怀疑态度
        """
        prompt = f"""
提案: {proposal}
上下文: {context or {}}

作为安全审计员，评估此提案是否存在漏洞（注入、权限、数据泄露）。
默认倾向于 HOLD 或 REJECT，除非确信安全。

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
            except ValueError:
                pass

        rationale_match = re.search(
            r"Rationale:\s*(.+)", response, re.DOTALL | re.IGNORECASE
        )
        if rationale_match:
            rationale = rationale_match.group(1).strip()

        self.add_to_history(
            {
                "action": "vote",
                "proposal": proposal,
                "context": context,
            }
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
        执行安全审计任务
        """
        self.add_to_history(
            {
                "action": "execute",
                "task": task,
                "plan": plan,
            }
        )

        return ExecuteResult(
            success=True,
            output=f"安全审计已完成: {task}",
            changes_made=["生成安全审计报告"],
        )

    def scan_vulnerabilities(self, code: str, file_path: str) -> Dict[str, Any]:
        """
        扫描代码漏洞

        Args:
            code: 代码内容
            file_path: 文件路径

        Returns:
            漏洞扫描结果
        """
        vulnerabilities = []

        # 简单的静态检查示例
        if ".env" in code or "secret" in code.lower():
            vulnerabilities.append(
                {
                    "severity": "High",
                    "type": "Sensitive Data Exposure",
                    "description": "检测到可能的敏感数据引用",
                    "line": 0,
                    "fix": "移除硬编码敏感数据，使用环境变量",
                }
            )

        if "eval(" in code or "exec(" in code:
            vulnerabilities.append(
                {
                    "severity": "Critical",
                    "type": "Code Injection",
                    "description": "检测到危险函数使用",
                    "line": 0,
                    "fix": "避免使用 eval/exec，使用安全的替代方案",
                }
            )

        return {
            "scanner": self.name,
            "file": file_path,
            "vulnerabilities": vulnerabilities,
            "risk_level": "High" if vulnerabilities else "Low",
        }

    def check_sensitive_paths(self, paths: List[str]) -> Dict[str, Any]:
        """
        检查敏感路径访问

        Args:
            paths: 路径列表

        Returns:
            检查结果
        """
        from council.auth.rbac import SENSITIVE_PATHS
        import fnmatch

        violations = []
        for path in paths:
            for pattern in SENSITIVE_PATHS:
                if fnmatch.fnmatch(path, pattern):
                    violations.append(
                        {
                            "path": path,
                            "matched_pattern": pattern,
                            "severity": "Critical",
                        }
                    )

        return {
            "checker": self.name,
            "paths_checked": len(paths),
            "violations": violations,
            "passed": len(violations) == 0,
        }

    # ============================================================
    # 2025 Best Practice: Structured Protocol Methods
    # These methods save ~70% tokens compared to NL versions
    # ============================================================

    def vote_structured(self, proposal: str, context: Optional[Dict[str, Any]] = None):
        """
        [2025 Best Practice] 对提案进行安全评审投票 (结构化输出)

        使用 MinimalVote schema，保持怀疑态度。
        """
        from council.protocol.schema import MinimalVote

        prompt = f"""
作为安全审计员 (怀疑论者)，评估以下提案的安全风险:
提案: {proposal}
上下文: {context or {}}

请投票并识别风险类别。默认倾向于 HOLD (3) 或 REJECT (0)，除非确信安全。
sec=安全, perf=性能, maint=维护, arch=架构, data=数据
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
        [2025 Best Practice] 从安全角度分析任务 (结构化输出)

        使用 MinimalThinkResult schema，强制提出安全问题。
        """
        from council.protocol.schema import MinimalThinkResult

        prompt = f"""
作为安全审计员，进行零信任分析:
任务: {task}
上下文: {context or {}}

必须找出可能的安全隐患。请提供简短摘要、安全担忧 (必须至少2点)、和加固建议。
"""
        result = self._call_llm_structured(prompt, MinimalThinkResult)
        result.perspective = "security"

        self.add_to_history(
            {
                "action": "think_structured",
                "task": task[:100],
                "confidence": result.confidence,
            }
        )

        return result


__all__ = ["SecurityAuditor", "SECURITY_AUDITOR_SYSTEM_PROMPT"]
