# Council 2025: Implementation Proof of Concept (PoC)

> **Goal**: Provide concrete Python implementations for the "Zero-Waste Token Protocol" defined in the research.
> **Scope**: Context Management, Protocol Communication, and Speculative Consensus.

## 1. Rolling Context Manager (The "Summary Window")

This class replaces the raw string concatenation of history. It maintains a "Sliding Window" of recent detailed turns and a "Rolling Summary" of the past.

```python
# council/context/rolling_context.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class RoundEntry:
    role: str
    content: str
    token_count: int

class RollingContext:
    def __init__(self, max_tokens: int = 8000, summary_model: str = "gemini-2.0-flash"):
        self.max_tokens = max_tokens
        self.summary_model = summary_model
        
        # State
        self.static_context: str = ""        # Immutable "System Prompt" + "Task"
        self.past_summary: str = ""          # Compressed history
        self.recent_history: List[RoundEntry] = []  # Detailed recent turns

    def add_turn(self, role: str, content: Any) -> None:
        """Add a new conversation turn."""
        text = json.dumps(content) if isinstance(content, dict) else str(content)
        # In production, use tiktoken or similar
        est_tokens = len(text) // 4
        
        self.recent_history.append(RoundEntry(role, text, est_tokens))
        self._prune_if_needed()

    def _prune_if_needed(self):
        """Check if we exceed token limit and trigger summarization."""
        current_load = sum(r.token_count for r in self.recent_history)
        if current_load > self.max_tokens * 0.7:  # Threshold
            self._compress_oldest_turns()
            
    def _compress_oldest_turns(self):
        """
        [MOCK] In real implementation, this calls an LLM to summarize.
        Here we simulate moving the oldest 50% turns to summary.
        """
        cut_idx = len(self.recent_history) // 2
        to_compress = self.recent_history[:cut_idx]
        self.recent_history = self.recent_history[cut_idx:]
        
        # Simulate LLM summarization
        new_summary_text = f"Previous discussion covered: {[r.content[:20] for r in to_compress]}..."
        
        # Append to existing summary
        self.past_summary += f"\n- {new_summary_text}"

    def get_context_for_prompt(self, include_summary: bool = True) -> str:
        """Generate the final prompt context."""
        parts = [self.static_context]
        
        if include_summary and self.past_summary:
            parts.append("=== PREVIOUSLY ===")
            parts.append(self.past_summary)
            
        parts.append("=== CURRENT CONVERSATION ===")
        for r in self.recent_history:
            parts.append(f"{r.role}: {r.content}")
            
        return "\n\n".join(parts)
```

## 2. Protocol Buffer Communication (Structured Enums)

Enforcing strict schemas for Agent-to-Agent communication.

```python
# council/protocol/schema.py
from pydantic import BaseModel, Field
from enum import Enum, IntEnum
from typing import List, Optional

class VoteEnum(IntEnum):
    REJECT = 0
    APPROVE = 1
    ABSTAIN = 2

class RiskCategory(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTENANCE = "maintenance"
    NONE = "none"

class MinimalVote(BaseModel):
    """
    Zero-Waste Vote Structure. 
    Agents output this JSON instead of verbose text.
    """
    vote: VoteEnum
    risks: List[RiskCategory] = Field(default_factory=list)
    # Only allowed if vote is REJECT or ABSTAIN
    blocking_reason: Optional[str] = Field(None, max_length=100) 
```

## 3. Shadow Facilitator (Speculative Consensus)

The logic for running "Cheap Swarms" before "Expensive Experts".

```python
# council/facilitator/shadow_facilitator.py
from typing import List
from council.agents.base_agent import BaseAgent

class ShadowFacilitator:
    def __init__(self, shadow_agents: List[BaseAgent], pro_agents: List[BaseAgent]):
        self.shadow_cabinet = shadow_agents  # e.g., gemini-2.0-flash
        self.full_council = pro_agents       # e.g., gemini-2.0-pro/ultra

    def run_speculative_round(self, proposal: str) -> str:
        """
        Try to resolve with Shadow Cabinet first.
        """
        print("[Shadow] Convening Flash models...")
        votes = [agent.vote(proposal) for agent in self.shadow_cabinet]
        
        # Check consensus (example logic)
        approve_count = sum(1 for v in votes if v.decision.value == "approve")
        total = len(votes)
        
        # Strict Unanimity required for Shadow approval
        if approve_count == total:
            return "Speculative Commit: Approved by Shadow Cabinet (Cost Saved: 90%)"
            
        # If any disagreement, escalate
        print("[Shadow] Disagreement detected. Escalating to Full Council...")
        return self.run_full_council(proposal, shadow_votes=votes)

    def run_full_council(self, proposal: str, shadow_votes: List) -> str:
        """
        Run the expensive models, using shadow votes as context context.
        """
        # We summarize the shadow debate so Pro models start ahead
        shadow_summary = f"Shadow Cabinet concerns: {[v.rationale for v in shadow_votes if v.decision.value != 'approve']}"
        
        print("[Full] Convening Pro models with Shadow context...")
        # context = {"previous_debate": shadow_summary}
        # real_votes = [agent.vote(proposal, context) for agent in self.full_council]
        
## 4. Blast Radius Analyzer (Impact-Aware Routing)

Mechanism to determine if a task is "Low Risk" (Leaf Node) or "High Risk" (Core Dependency), enabling the **Fast Track** skipping of voting.

```python
# council/governance/impact_analyzer.py
import ast
import os
from typing import List, Set

class BlastRadiusAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def calculate_impact(self, target_files: List[str]) -> str:
        """
        Determine impact level based on how many other files import the target.
        """
        incoming_deps = 0
        all_files = self._get_all_python_files()
        
        for f in all_files:
            if f in target_files: continue
            imports = self._get_imports(f)
            # Check if 'f' imports any of our 'target_files'
            if any(self._is_importing(imports, t) for t in target_files):
                incoming_deps += 1
                
        if incoming_deps == 0:
            return "LOW (Leaf Node)"
        elif incoming_deps < 5:
            return "MEDIUM (Local Util)"
        else:
            return "HIGH (Core Interface)"

    def _get_all_python_files(self) -> List[str]:
        # ... os.walk implementation ...
        return []

    def _get_imports(self, file_path: str) -> Set[str]:
        # ... ast.parse implementation ...
        return set()
        
    def _is_importing(self, imports: Set[str], target: str) -> bool:
        # Check if target module name is in imports
        target_mod = os.path.splitext(os.path.basename(target))[0]
        return target_mod in imports
```
