import pytest
import pytest_asyncio
import os
import asyncio
from src.telegram_multi.cli.commands.council import bootstrap_system
from src.telegram_multi.config import TelegramConfig
from unittest.mock import MagicMock, AsyncMock

# @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
@pytest.mark.asyncio
async def test_awakening_first_breath():
    """
    The First Breath: A real E2E test with Gemini.
    """
    # 1. Config with a real (or mocked) instance path
    config = MagicMock(spec=TelegramConfig)
    config.instances = [] # No browser for this specific breath test if we want to isolate thought? 
    # The plan says "Open Telegram Web", so we need browser.
    # But usually we don't have a real X server in CI.
    # We will assume headles browser is fine.
    
    # We actually need a real config to bootstrap browser? 
    # bootstrapping creates BrowserContext. 
    # We might mock Browser interaction but keep Real LLM.
    
    # Let's mock the BrowserContext part to assume it works, 
    # but use REAL LLM Factory.
    
    # However, bootstrap_system uses config to create browser.
    # Let's manually assemble for this test to have finer control.
    
    from src.telegram_multi.cortex.db import CortexDB
    from src.telegram_multi.cortex.logger import LogActor
    from src.telegram_multi.cortex.actors.agent import AgentActor
    from src.telegram_multi.cortex.intelligence.llm_factory import LLMFactory

    # Infrastructure
    db = CortexDB(":memory:")
    # if os.path.exists("test_debug.db"):
    #     os.remove("test_debug.db")
    # db = CortexDB("test_debug.db")
    await db.initialize()
    logger = LogActor(db)
    
    # Brain
    agent = AgentActor("AwakenedAgent", logger)
    
    # Connect Real Brain
    api_key = os.getenv("GEMINI_API_KEY")
    client = LLMFactory.create_client("gemini", model_name="gemini-2.0-flash") # or flash
    agent.set_llm_client(client)
    
    # Mock Body (Browser Tool) to avoid needing real Telegram login
    mock_browser_tool = MagicMock()
    # Mock execute to return a fixed "Telegram Web" title
    async def side_effect(args):
        if args.get("action") == "read_title":
            return "Telegram Web"
        return "Done"
    
    mock_browser_tool.execute = AsyncMock(side_effect=side_effect)
    
    agent.register_tool("browser", mock_browser_tool)
    
    # Start Agent
    agent_task = asyncio.create_task(agent.start())
    logger_task = asyncio.create_task(logger.start())
    
    # The Task (First Breath)
    task_content = "Check the current page title using the browser tool."
    
    # We need to wait for result.
    # Since agent.tell() is fire-and-forget, we check the DB logs or mock tool call.
    
    await agent.tell({"type": "THINK", "content": task_content})
    
    # Wait for thought loop (2 seconds)
    await asyncio.sleep(5.0)
    
    # Verify:
    # 1. Tool was called (Real LLM decided to call it)
    mock_browser_tool.execute.assert_called() 
    # args = mock_browser_tool.execute.call_args[0][0]
    # assert args["action"] == "read_title" (LLM might vary)
    
    # 2. Agent outputted final answer?
    # We can check DB traces if we want.
    
    # Cleanup
    await agent.tell("STOP")
    await logger.tell("STOP")
    await asyncio.gather(agent_task, logger_task)
