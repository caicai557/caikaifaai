import uuid
import asyncio
import logging
from typing import Dict
from .base import BaseActor
from ..logger import LogActor

class CouncilActor(BaseActor):
    """
    The Orchestrator Logic.
    Manages Sessions (Traces) and Agent Voting.
    """
    def __init__(self, logger: LogActor):
        super().__init__("Council")
        self.logger = logger
        self.sessions: Dict[str, dict] = {} # active sessions

    async def start_session(self, goal: str) -> str:
        """Starts a new Council Session."""
        trace_id = str(uuid.uuid4())
        self.sessions[trace_id] = {
            "goal": goal,
            "votes": [],
            "status": "ACTIVE"
        }
        # Log the start
        # await self.logger.log_span(...) # In real imp
        return trace_id

    async def handle(self, msg):
        if not isinstance(msg, dict):
            return

        msg_type = msg.get("type")
        
        if msg_type == "VOTE":
            await self._handle_vote(msg)

    async def _handle_vote(self, msg: dict):
        trace_id = msg.get("trace_id")
        if not trace_id or trace_id not in self.sessions:
            logging.warning(f"Received vote for unknown session {trace_id}")
            return

        # Store vote
        self.sessions[trace_id]["votes"].append(msg)
        
        # Check Consensus (Mock Logic for Level 3)
        # In full implementation, we'd feed WaldConsensus here.
        # For now, we just acknowledge.
        # await self.logger.log_span(...)
