"""
Collaboration Patterns Module (2026)

Provides structured collaboration patterns for multi-agent workflows:
- Pair programming (coder + reviewer)
- Design review (architect + auditor)
- Brainstorming (multiple agents)
- Consensus building
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """Collaboration modes."""
    PAIR = "pair"           # Two agents working together
    REVIEW = "review"       # One agent reviews another's work
    BRAINSTORM = "brainstorm"  # Multiple agents generate ideas
    CONSENSUS = "consensus"    # Agents vote on decisions
    DELEGATE = "delegate"      # One agent delegates to another


@dataclass
class CollaborationResult:
    """
    Result of a collaboration session.

    Attributes:
        session_id: Unique session identifier
        mode: Collaboration mode used
        participants: List of participating agents
        outcome: The final outcome/result
        iterations: Number of iteration rounds
        duration_ms: Total duration in milliseconds
        decisions: List of decisions made
        artifacts: Any produced artifacts (code, designs, etc.)
        consensus_score: Agreement score (0-1) if applicable
    """
    session_id: str
    mode: CollaborationMode
    participants: List[str]
    outcome: Any
    iterations: int = 0
    duration_ms: float = 0.0
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    consensus_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mode": self.mode.value,
            "participants": self.participants,
            "outcome": self.outcome,
            "iterations": self.iterations,
            "duration_ms": self.duration_ms,
            "decisions": self.decisions,
            "artifacts": self.artifacts,
            "consensus_score": self.consensus_score,
        }


@dataclass
class Vote:
    """A vote from an agent."""
    agent: str
    choice: str
    confidence: float = 1.0
    rationale: str = ""


@dataclass
class BrainstormIdea:
    """An idea from brainstorming."""
    agent: str
    idea: str
    category: str = ""
    votes: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# Type aliases for agent functions
AgentFunc = Callable[[str, Dict[str, Any]], Any]
AsyncAgentFunc = Callable[[str, Dict[str, Any]], Any]


class CollaborationOrchestrator:
    """
    Orchestrates collaboration patterns between agents (2026).

    Provides:
    - Pair programming sessions
    - Design reviews
    - Brainstorming sessions
    - Consensus building

    Example:
        collab = CollaborationOrchestrator()

        # Pair programming
        result = await collab.pair_programming(
            coder=coder_agent,
            reviewer=reviewer_agent,
            task="Implement user authentication",
        )

        # Brainstorming
        result = await collab.brainstorm(
            agents=[agent1, agent2, agent3],
            topic="API design patterns",
            rounds=3,
        )
    """

    def __init__(self):
        self._sessions: Dict[str, CollaborationResult] = {}

    async def pair_programming(
        self,
        coder: AsyncAgentFunc,
        reviewer: AsyncAgentFunc,
        task: str,
        max_iterations: int = 3,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationResult:
        """
        Run a pair programming session.

        The coder writes code, the reviewer reviews it.
        Iterates until approved or max iterations reached.

        Args:
            coder: Coder agent function (task, context) -> code
            reviewer: Reviewer agent function (code, context) -> feedback
            task: The task description
            max_iterations: Maximum review iterations
            context: Additional context

        Returns:
            CollaborationResult
        """
        import time
        start_time = time.time()

        session_id = uuid.uuid4().hex[:8]
        ctx = context or {}
        decisions = []
        code = ""
        feedback = ""
        approved = False

        for iteration in range(max_iterations):
            logger.info(f"Pair programming iteration {iteration + 1}/{max_iterations}")

            # Coder writes/updates code
            coder_input = {
                **ctx,
                "task": task,
                "iteration": iteration,
                "previous_code": code,
                "feedback": feedback,
            }

            if asyncio.iscoroutinefunction(coder):
                code = await coder(task, coder_input)
            else:
                code = coder(task, coder_input)

            decisions.append({
                "iteration": iteration,
                "agent": "coder",
                "action": "write_code",
                "output_preview": str(code)[:200],
            })

            # Reviewer reviews code
            reviewer_input = {
                **ctx,
                "task": task,
                "code": code,
                "iteration": iteration,
            }

            if asyncio.iscoroutinefunction(reviewer):
                review_result = await reviewer(code, reviewer_input)
            else:
                review_result = reviewer(code, reviewer_input)

            # Parse review result
            if isinstance(review_result, dict):
                approved = review_result.get("approved", False)
                feedback = review_result.get("feedback", "")
            elif isinstance(review_result, bool):
                approved = review_result
                feedback = "" if approved else "Needs revision"
            else:
                approved = "approved" in str(review_result).lower()
                feedback = str(review_result)

            decisions.append({
                "iteration": iteration,
                "agent": "reviewer",
                "action": "review",
                "approved": approved,
                "feedback": feedback,
            })

            if approved:
                logger.info(f"Code approved at iteration {iteration + 1}")
                break

        duration_ms = (time.time() - start_time) * 1000

        result = CollaborationResult(
            session_id=session_id,
            mode=CollaborationMode.PAIR,
            participants=["coder", "reviewer"],
            outcome=code if approved else None,
            iterations=iteration + 1,
            duration_ms=duration_ms,
            decisions=decisions,
            artifacts={"code": code, "final_feedback": feedback},
            consensus_score=1.0 if approved else 0.0,
        )

        self._sessions[session_id] = result
        return result

    async def design_review(
        self,
        architect: AsyncAgentFunc,
        auditor: AsyncAgentFunc,
        design: str,
        criteria: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationResult:
        """
        Run a design review session.

        The architect presents a design, the auditor evaluates it.

        Args:
            architect: Architect agent function
            auditor: Auditor agent function
            design: The design to review
            criteria: Review criteria
            context: Additional context

        Returns:
            CollaborationResult
        """
        import time
        start_time = time.time()

        session_id = uuid.uuid4().hex[:8]
        ctx = context or {}
        criteria = criteria or ["security", "scalability", "maintainability"]
        decisions = []

        # Architect explains design
        architect_input = {
            **ctx,
            "design": design,
            "criteria": criteria,
        }

        if asyncio.iscoroutinefunction(architect):
            explanation = await architect(design, architect_input)
        else:
            explanation = architect(design, architect_input)

        decisions.append({
            "agent": "architect",
            "action": "explain_design",
            "output": str(explanation)[:500],
        })

        # Auditor evaluates against criteria
        audit_results = {}
        overall_score = 0.0

        for criterion in criteria:
            auditor_input = {
                **ctx,
                "design": design,
                "explanation": explanation,
                "criterion": criterion,
            }

            if asyncio.iscoroutinefunction(auditor):
                evaluation = await auditor(criterion, auditor_input)
            else:
                evaluation = auditor(criterion, auditor_input)

            # Parse evaluation
            if isinstance(evaluation, dict):
                score = evaluation.get("score", 0.5)
                feedback = evaluation.get("feedback", "")
            elif isinstance(evaluation, (int, float)):
                score = float(evaluation)
                feedback = ""
            else:
                score = 0.5
                feedback = str(evaluation)

            audit_results[criterion] = {
                "score": score,
                "feedback": feedback,
            }
            overall_score += score

            decisions.append({
                "agent": "auditor",
                "action": f"evaluate_{criterion}",
                "score": score,
                "feedback": feedback,
            })

        overall_score /= len(criteria) if criteria else 1

        duration_ms = (time.time() - start_time) * 1000

        result = CollaborationResult(
            session_id=session_id,
            mode=CollaborationMode.REVIEW,
            participants=["architect", "auditor"],
            outcome={
                "approved": overall_score >= 0.7,
                "overall_score": overall_score,
                "criteria_scores": audit_results,
            },
            iterations=1,
            duration_ms=duration_ms,
            decisions=decisions,
            artifacts={"design": design, "explanation": explanation},
            consensus_score=overall_score,
        )

        self._sessions[session_id] = result
        return result

    async def brainstorm(
        self,
        agents: List[Tuple[str, AsyncAgentFunc]],
        topic: str,
        rounds: int = 2,
        ideas_per_round: int = 3,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationResult:
        """
        Run a brainstorming session.

        Multiple agents generate and build on ideas.

        Args:
            agents: List of (name, agent_func) tuples
            topic: Brainstorming topic
            rounds: Number of brainstorming rounds
            ideas_per_round: Ideas each agent generates per round
            context: Additional context

        Returns:
            CollaborationResult
        """
        import time
        start_time = time.time()

        session_id = uuid.uuid4().hex[:8]
        ctx = context or {}
        all_ideas: List[BrainstormIdea] = []
        decisions = []

        for round_num in range(rounds):
            logger.info(f"Brainstorm round {round_num + 1}/{rounds}")

            # Each agent generates ideas
            for agent_name, agent_func in agents:
                agent_input = {
                    **ctx,
                    "topic": topic,
                    "round": round_num,
                    "existing_ideas": [i.idea for i in all_ideas],
                    "ideas_requested": ideas_per_round,
                }

                if asyncio.iscoroutinefunction(agent_func):
                    response = await agent_func(topic, agent_input)
                else:
                    response = agent_func(topic, agent_input)

                # Parse response into ideas
                if isinstance(response, list):
                    ideas = response
                elif isinstance(response, str):
                    ideas = [line.strip() for line in response.split("\n") if line.strip()]
                else:
                    ideas = [str(response)]

                for idea in ideas[:ideas_per_round]:
                    all_ideas.append(BrainstormIdea(
                        agent=agent_name,
                        idea=idea,
                        category=f"round_{round_num}",
                    ))

                decisions.append({
                    "round": round_num,
                    "agent": agent_name,
                    "action": "generate_ideas",
                    "ideas_count": len(ideas[:ideas_per_round]),
                })

        # Optional: voting round
        if len(all_ideas) > 0 and len(agents) > 1:
            for agent_name, agent_func in agents:
                vote_input = {
                    **ctx,
                    "topic": topic,
                    "ideas": [i.idea for i in all_ideas],
                    "vote_count": min(3, len(all_ideas)),
                }

                if asyncio.iscoroutinefunction(agent_func):
                    votes = await agent_func("vote", vote_input)
                else:
                    votes = agent_func("vote", vote_input)

                # Parse votes (expecting list of indices or ideas)
                if isinstance(votes, list):
                    for vote in votes:
                        if isinstance(vote, int) and 0 <= vote < len(all_ideas):
                            all_ideas[vote].votes += 1
                        elif isinstance(vote, str):
                            for idea in all_ideas:
                                if vote in idea.idea:
                                    idea.votes += 1
                                    break

        # Sort by votes
        all_ideas.sort(key=lambda x: x.votes, reverse=True)

        duration_ms = (time.time() - start_time) * 1000

        result = CollaborationResult(
            session_id=session_id,
            mode=CollaborationMode.BRAINSTORM,
            participants=[name for name, _ in agents],
            outcome={
                "total_ideas": len(all_ideas),
                "top_ideas": [i.idea for i in all_ideas[:5]],
            },
            iterations=rounds,
            duration_ms=duration_ms,
            decisions=decisions,
            artifacts={
                "all_ideas": [
                    {"agent": i.agent, "idea": i.idea, "votes": i.votes}
                    for i in all_ideas
                ],
            },
        )

        self._sessions[session_id] = result
        return result

    async def build_consensus(
        self,
        agents: List[Tuple[str, AsyncAgentFunc]],
        question: str,
        options: List[str],
        threshold: float = 0.66,
        max_rounds: int = 3,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationResult:
        """
        Build consensus among agents.

        Agents vote and discuss until consensus is reached.

        Args:
            agents: List of (name, agent_func) tuples
            question: The question to decide
            options: Available options
            threshold: Consensus threshold (0-1)
            max_rounds: Maximum voting rounds
            context: Additional context

        Returns:
            CollaborationResult
        """
        import time
        start_time = time.time()

        session_id = uuid.uuid4().hex[:8]
        ctx = context or {}
        decisions = []
        consensus_reached = False
        final_choice = None
        final_score = 0.0

        for round_num in range(max_rounds):
            logger.info(f"Consensus round {round_num + 1}/{max_rounds}")

            votes: List[Vote] = []
            vote_counts: Dict[str, float] = {opt: 0.0 for opt in options}

            # Collect votes
            for agent_name, agent_func in agents:
                vote_input = {
                    **ctx,
                    "question": question,
                    "options": options,
                    "round": round_num,
                    "previous_votes": [v.__dict__ for v in votes] if round_num > 0 else [],
                }

                if asyncio.iscoroutinefunction(agent_func):
                    response = await agent_func(question, vote_input)
                else:
                    response = agent_func(question, vote_input)

                # Parse vote
                if isinstance(response, dict):
                    choice = response.get("choice", options[0] if options else "")
                    confidence = response.get("confidence", 1.0)
                    rationale = response.get("rationale", "")
                elif isinstance(response, str):
                    choice = response
                    confidence = 1.0
                    rationale = ""
                else:
                    choice = str(response)
                    confidence = 1.0
                    rationale = ""

                vote = Vote(
                    agent=agent_name,
                    choice=choice,
                    confidence=confidence,
                    rationale=rationale,
                )
                votes.append(vote)

                if choice in vote_counts:
                    vote_counts[choice] += confidence

                decisions.append({
                    "round": round_num,
                    "agent": agent_name,
                    "action": "vote",
                    "choice": choice,
                    "confidence": confidence,
                })

            # Check for consensus
            total_weight = sum(vote_counts.values())
            if total_weight > 0:
                for option, count in vote_counts.items():
                    score = count / total_weight
                    if score >= threshold:
                        consensus_reached = True
                        final_choice = option
                        final_score = score
                        break

            if consensus_reached:
                logger.info(f"Consensus reached: {final_choice} ({final_score:.0%})")
                break

        if not consensus_reached and vote_counts:
            # Pick highest voted option
            final_choice = max(vote_counts.keys(), key=lambda k: vote_counts[k])
            final_score = vote_counts[final_choice] / sum(vote_counts.values())

        duration_ms = (time.time() - start_time) * 1000

        result = CollaborationResult(
            session_id=session_id,
            mode=CollaborationMode.CONSENSUS,
            participants=[name for name, _ in agents],
            outcome={
                "consensus_reached": consensus_reached,
                "final_choice": final_choice,
                "vote_distribution": vote_counts,
            },
            iterations=round_num + 1,
            duration_ms=duration_ms,
            decisions=decisions,
            consensus_score=final_score,
        )

        self._sessions[session_id] = result
        return result

    def get_session(self, session_id: str) -> Optional[CollaborationResult]:
        """Get a collaboration session by ID."""
        return self._sessions.get(session_id)

    def get_all_sessions(self) -> List[CollaborationResult]:
        """Get all collaboration sessions."""
        return list(self._sessions.values())


# Default orchestrator instance
default_collaboration = CollaborationOrchestrator()


__all__ = [
    "CollaborationMode",
    "CollaborationResult",
    "CollaborationOrchestrator",
    "Vote",
    "BrainstormIdea",
    "default_collaboration",
]
