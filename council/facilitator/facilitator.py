"""
Facilitator - 会议秘书 / 促进者 AI
负责维持逻辑连贯性，引导迭代审议，降低语义熵
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from council.agents.base_agent import Vote, VoteDecision
from council.facilitator.wald_consensus import (
    WaldConsensus,
    WaldConfig,
    ConsensusResult,
    ConsensusDecision,
)


@dataclass
class DebateRound:
    """辩论轮次记录"""

    round_number: int
    topic: str
    votes: List[Vote]
    consensus_result: Optional[ConsensusResult] = None
    clarification_questions: List[str] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MeetingMinutes:
    """会议纪要"""

    topic: str
    participants: List[str]
    rounds: List[DebateRound]
    final_decision: Optional[ConsensusDecision] = None
    final_reason: str = ""
    total_iterations: int = 0
    semantic_entropy_history: List[float] = field(default_factory=list)


class Facilitator:
    """
    会议秘书 / 促进者 AI

    核心职责:
    1. 引导迭代审议: 总结论据，识别矛盾，抛出澄清问题
    2. 降低语义熵: 通过多轮辩论将意见收敛至一致
    3. 自适应终止: 利用 Wald 算法决定何时停止

    使用示例:
        facilitator = Facilitator()

        # 开始会议
        facilitator.start_meeting("实现用户登录功能", ["Architect", "Coder", "SecurityAuditor"])

        # 收集投票
        votes = [architect.vote(...), coder.vote(...), auditor.vote(...)]

        # 处理投票
        result = facilitator.process_round(votes)

        # 检查是否达成共识
        if result.decision == ConsensusDecision.AUTO_COMMIT:
            # 会议结束，自动提交
            minutes = facilitator.end_meeting()
    """

    def __init__(
        self, wald_config: Optional[WaldConfig] = None, max_iterations: int = 5
    ):
        """
        初始化促进者

        Args:
            wald_config: Wald 算法配置
            max_iterations: 最大迭代轮次
        """
        self.wald = WaldConsensus(wald_config)
        self.max_iterations = max_iterations
        self.current_meeting: Optional[MeetingMinutes] = None
        self.current_round = 0

    def start_meeting(self, topic: str, participants: List[str]) -> None:
        """
        开始新会议

        Args:
            topic: 会议主题
            participants: 参与者列表
        """
        self.current_meeting = MeetingMinutes(
            topic=topic,
            participants=participants,
            rounds=[],
        )
        self.current_round = 0

    def process_round(self, votes: List[Vote]) -> ConsensusResult:
        """
        处理一轮投票

        Args:
            votes: 投票列表

        Returns:
            共识结果
        """
        if not self.current_meeting:
            raise ValueError("会议未开始，请先调用 start_meeting()")

        self.current_round += 1

        # 转换投票格式
        vote_dicts = [
            {
                "agent": v.agent_name,
                "decision": v.decision.value,
                "confidence": v.confidence,
                "rationale": v.rationale,
            }
            for v in votes
        ]

        # 计算共识
        result = self.wald.evaluate(vote_dicts)
        result.iteration = self.current_round

        # 计算语义熵
        entropy = self.wald.get_semantic_entropy(vote_dicts)
        self.current_meeting.semantic_entropy_history.append(entropy)

        # 识别矛盾
        contradictions = self._find_contradictions(votes)

        # 生成澄清问题
        questions = self._generate_clarification_questions(votes, contradictions)

        # 记录轮次
        round_record = DebateRound(
            round_number=self.current_round,
            topic=self.current_meeting.topic,
            votes=votes,
            consensus_result=result,
            clarification_questions=questions,
            contradictions=contradictions,
        )
        self.current_meeting.rounds.append(round_record)

        return result

    def _find_contradictions(self, votes: List[Vote]) -> List[Dict[str, Any]]:
        """
        识别投票中的矛盾

        Args:
            votes: 投票列表

        Returns:
            矛盾列表
        """
        contradictions = []

        # 分组
        approvals = [
            v
            for v in votes
            if v.decision in [VoteDecision.APPROVE, VoteDecision.APPROVE_WITH_CHANGES]
        ]
        rejections = [v for v in votes if v.decision == VoteDecision.REJECT]
        holds = [v for v in votes if v.decision == VoteDecision.HOLD]

        # 如果同时有批准和拒绝
        if approvals and rejections:
            contradictions.append(
                {
                    "type": "decision_conflict",
                    "approvers": [v.agent_name for v in approvals],
                    "rejectors": [v.agent_name for v in rejections],
                    "description": "部分成员批准，部分成员拒绝",
                }
            )

        # 如果有 hold 且其他人已决定
        if holds and (approvals or rejections):
            contradictions.append(
                {
                    "type": "certainty_gap",
                    "undecided": [v.agent_name for v in holds],
                    "decided": [v.agent_name for v in approvals + rejections],
                    "description": "部分成员尚未明确表态",
                }
            )

        return contradictions

    def _generate_clarification_questions(
        self, votes: List[Vote], contradictions: List[Dict[str, Any]]
    ) -> List[str]:
        """
        生成澄清问题

        Args:
            votes: 投票列表
            contradictions: 矛盾列表

        Returns:
            澄清问题列表
        """
        questions = []

        for contradiction in contradictions:
            if contradiction["type"] == "decision_conflict":
                questions.append(
                    f"请 {contradiction['rejectors']} 详细说明拒绝的具体原因和担忧"
                )
                questions.append(f"请 {contradiction['approvers']} 回应这些担忧")

            elif contradiction["type"] == "certainty_gap":
                questions.append(
                    f"请 {contradiction['undecided']} 说明需要什么信息才能做出决定"
                )

        # 基于低置信度投票生成问题
        for vote in votes:
            if vote.confidence < 0.6:
                questions.append(
                    f"{vote.agent_name} 的置信度较低 ({vote.confidence:.0%})，需要什么信息来提高确定性？"
                )

        return questions

    def should_continue(self) -> bool:
        """检查是否应该继续迭代"""
        if not self.current_meeting or not self.current_meeting.rounds:
            return True

        last_result = self.current_meeting.rounds[-1].consensus_result
        if not last_result:
            return True

        return self.wald.should_continue(last_result, self.max_iterations)

    def end_meeting(self) -> MeetingMinutes:
        """
        结束会议并生成纪要

        Returns:
            会议纪要
        """
        if not self.current_meeting:
            raise ValueError("会议未开始")

        if self.current_meeting.rounds:
            last_result = self.current_meeting.rounds[-1].consensus_result
            if last_result:
                self.current_meeting.final_decision = last_result.decision
                self.current_meeting.final_reason = last_result.reason

        self.current_meeting.total_iterations = self.current_round

        minutes = self.current_meeting
        self.current_meeting = None
        self.current_round = 0

        return minutes

    def get_summary(self) -> Dict[str, Any]:
        """
        获取当前会议摘要

        Returns:
            会议摘要
        """
        if not self.current_meeting:
            return {"status": "no_active_meeting"}

        return {
            "topic": self.current_meeting.topic,
            "participants": self.current_meeting.participants,
            "rounds_completed": self.current_round,
            "max_iterations": self.max_iterations,
            "entropy_trend": self.current_meeting.semantic_entropy_history,
            "current_status": (
                self.current_meeting.rounds[-1].consensus_result.decision.value
                if self.current_meeting.rounds
                and self.current_meeting.rounds[-1].consensus_result
                else "pending"
            ),
        }


# 导出
__all__ = ["Facilitator", "DebateRound", "MeetingMinutes"]
