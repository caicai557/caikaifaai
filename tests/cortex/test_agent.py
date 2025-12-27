import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock
from src.telegram_multi.cortex.actors.agent import AgentActor
from src.telegram_multi.cortex.logger import LogActor

@pytest_asyncio.fixture
async def agent_setup():
    # Mock Logger
    mock_logger = MagicMock(spec=LogActor)
    # Async mock for log_span
    mock_logger.log_span = MagicMock()
    future = asyncio.Future()
    future.set_result(None)
    mock_logger.log_span.return_value = future

    agent = AgentActor("agent_1", mock_logger)
    task = asyncio.create_task(agent.start())
    
    yield agent, mock_logger
    
    await agent.tell("STOP")
    await task

@pytest.mark.asyncio
async def test_agent_processes_task(agent_setup):
    agent, mock_logger = agent_setup
    
    # Send a "Task" (simulated)
    # In real imp, task might be a dict or object.
    task = {"type": "THINK", "content": "What is 2+2?"}
    
    await agent.tell(task)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # Verify it logged a span
    assert mock_logger.log_span.called
    
    # Verify result (if we had a way to check result, usually direct response or via another queue)
    # For now, AgentActor usually returns nothing to caller unless 'ask' is used, 
    # but it emits to logger.
