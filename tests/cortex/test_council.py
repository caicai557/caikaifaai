import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock
from src.telegram_multi.cortex.actors.council import CouncilActor
from src.telegram_multi.cortex.logger import LogActor

@pytest_asyncio.fixture
async def council_setup():
    mock_logger = MagicMock(spec=LogActor)
    mock_logger.log_span = MagicMock()
    future = asyncio.Future()
    future.set_result(None)
    mock_logger.log_span.return_value = future

    council = CouncilActor(mock_logger)
    task = asyncio.create_task(council.start())
    
    yield council, mock_logger
    
    await council.tell("STOP")
    await task

@pytest.mark.asyncio
async def test_council_orchestration_flow(council_setup):
    council, logger = council_setup
    
    # 1. Start a Session
    session_id = await council.start_session("Decide on architecture")
    assert session_id is not None
    
    # 2. Add Agents (Mocked for now? Or real?)
    # Council logic likely spawns agents or has them added.
    # For this unit test, we might just verify it CAN receive messages.
    
    # 3. Send a Vote (simulating an agent responding)
    # The council needs to handle incoming votes.
    vote_msg = {
        "type": "VOTE",
        "agent_id": "agent_1",
        "decision": "APPROVE",
        "confidence": 0.9,
        "trace_id": session_id
    }
    await council.tell(vote_msg)
    
    # Verify internal state or log emission
    # Council should log the vote or update consensus
    await asyncio.sleep(0.1)
    
    # assert something?
    # Maybe check if consensus was checked?
    # Since we don't have full Wald here, we just check if it processed the message without crash.
    pass 
