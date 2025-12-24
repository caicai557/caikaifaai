"""
SecurityAuditor - 安全审计员智能体
"怀疑论者"角色，负责漏洞扫描、攻击面分析
"""

from typing import Optional, Dict, Any, List
from council.agents.base_agent import (
    BaseAgent, Vote, VoteDecision, ThinkResult, ExecuteResult
)


SECURITY_AUDITOR_SYSTEM_PROMPT = """你是一名资深安全审计员，保持"怀疑论者"立场。

## 核心职责
1. **漏洞扫描**: 识别代码中的安全漏洞
2. **攻击面分析**: 评估系统的攻击面
3. **风险评估**: 量化安全风险
4. **合规检查**: 确保符合安全标准

## 审计原则 (强制辩论触发)
- **零信任**: 不给代码任何"疑点利益"
- **最坏假设**: 假设所有输入都是恶意的
- **深度审查**: 每个接口都可能是攻击入口
- **持续怀疑**: 即使看起来安全也要再检查

## 关注领域
1. 身份认证和授权
2. 输入验证和输出编码
3. 敏感数据处理
4. 错误处理和日志
5. 依赖项安全
6. 配置安全

## 输出格式
1. 漏洞清单 (严重性: Critical/High/Medium/Low)
2. 攻击向量描述
3. 修复建议
4. 验证方法

## 强制行为
- 必须对每个变更提出至少 1 个安全问题
- 必须检查敏感路径访问 (.ssh/, .env, secrets/)
- 必须验证权限边界
"""


class SecurityAuditor(BaseAgent):
    """
    安全审计员智能体
    
    保持"怀疑论者"立场，强制触发深度辩论
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        super().__init__(
            name="SecurityAuditor",
            system_prompt=SECURITY_AUDITOR_SYSTEM_PROMPT,
            model=model,
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
        for line in response.split('\n'):
            line = line.strip()
            if not line: continue
            
            if line.startswith("[Analysis]"): current_section = "analysis"
            elif line.startswith("[Concerns]"): current_section = "concerns"
            elif line.startswith("[Suggestions]"): current_section = "suggestions"
            elif line.startswith("[Confidence]"): current_section = "confidence"
            elif current_section == "analysis": analysis += line + "\n"
            elif current_section == "concerns": 
                if line.startswith("-") or line[0].isdigit(): concerns.append(line.lstrip("- 1234567890."))
            elif current_section == "suggestions":
                if line.startswith("-") or line[0].isdigit(): suggestions.append(line.lstrip("- 1234567890."))
            elif current_section == "confidence":
                try: confidence = float(line)
                except: pass

        self.add_to_history({
            "action": "think",
            "task": task,
            "context": context,
            "concerns_raised": len(concerns),
        })
        
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
        
        decision_match = re.search(r"Vote:\s*(APPROVE_WITH_CHANGES|APPROVE|HOLD|REJECT)", response, re.IGNORECASE)
        if decision_match:
            d_str = decision_match.group(1).upper()
            if d_str == "APPROVE": decision = VoteDecision.APPROVE
            elif d_str == "APPROVE_WITH_CHANGES": decision = VoteDecision.APPROVE_WITH_CHANGES
            elif d_str == "HOLD": decision = VoteDecision.HOLD
            elif d_str == "REJECT": decision = VoteDecision.REJECT
            
        conf_match = re.search(r"Confidence:\s*(\d*\.?\d+)", response)
        if conf_match:
            try: confidence = float(conf_match.group(1))
            except: pass
            
        rationale_match = re.search(r"Rationale:\s*(.+)", response, re.DOTALL | re.IGNORECASE)
        if rationale_match:
            rationale = rationale_match.group(1).strip()
            
        self.add_to_history({
            "action": "vote",
            "proposal": proposal,
            "context": context,
        })
        
        return Vote(
            agent_name=self.name,
            decision=decision,
            confidence=confidence,
            rationale=rationale,
        )
    
    def execute(self, task: str, plan: Optional[Dict[str, Any]] = None) -> ExecuteResult:
        """
        执行安全审计任务
        """
        self.add_to_history({
            "action": "execute",
            "task": task,
            "plan": plan,
        })
        
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
            vulnerabilities.append({
                "severity": "High",
                "type": "Sensitive Data Exposure",
                "description": "检测到可能的敏感数据引用",
                "line": 0,
                "fix": "移除硬编码敏感数据，使用环境变量",
            })
        
        if "eval(" in code or "exec(" in code:
            vulnerabilities.append({
                "severity": "Critical",
                "type": "Code Injection",
                "description": "检测到危险函数使用",
                "line": 0,
                "fix": "避免使用 eval/exec，使用安全的替代方案",
            })
        
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
                    violations.append({
                        "path": path,
                        "matched_pattern": pattern,
                        "severity": "Critical",
                    })
        
        return {
            "checker": self.name,
            "paths_checked": len(paths),
            "violations": violations,
            "passed": len(violations) == 0,
        }


__all__ = ["SecurityAuditor", "SECURITY_AUDITOR_SYSTEM_PROMPT"]
