import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.telegram_multi.cortex.actors.agent import AgentActor
from src.telegram_multi.cortex.tools.browser_tool import BrowserTool
from src.telegram_multi.cortex.logger import LogActor

# Mock LLM Client Response Structure
# We assume LLM returns: {"content": str, "tool_calls": [{"name": "browser", "args": {...}}]}

class MockLLMClient:
    def __init__(self):
        self.responses = []
    
    def add_response(self, response):
        self.responses.append(response)
        
    async def generate(self, prompt, tools=None):
        if self.responses:
            return self.responses.pop(0)
        return {"content": "I don't know.", "tool_calls": []}

@pytest_asyncio.fixture
async def agent_with_tools():
    # Mock Logger
    mock_logger = MagicMock(spec=LogActor)
    mock_logger.log_span = MagicMock()
    future = asyncio.Future()
    future.set_result(None)
    mock_logger.log_span.return_value = future

    # Mock Browser Tool
    mock_browser = AsyncMock(spec=BrowserTool)
    mock_browser.execute.return_value = {"status": "success", "result": "Clicked"}

    # Mock LLM
    mock_llm = MockLLMClient()
    
    # Init Agent with tools and LLM
    # Note: We need to modify AgentActor to accept these
    agent = AgentActor("agent_test", mock_logger)
    agent.register_tool("browser", mock_browser)
    agent.set_llm_client(mock_llm)
    
    task = asyncio.create_task(agent.start())
    yield agent, mock_llm, mock_browser, mock_logger
    
    await agent.tell("STOP")
    await task

@pytest.mark.asyncio
async def test_agent_uses_tool_from_llm(agent_with_tools):
    agent, mock_llm, mock_browser, mock_logger = agent_with_tools
    
    # Setup LLM response to trigger a tool call
    mock_llm.add_response({
        "content": "I will click the button.",
        "tool_calls": [{
            "name": "browser",
            "args": {"action": "click", "selector": "#btn"}
        }]
    })
    
    # Send Task
    await agent.tell({"type": "THINK", "content": "Click the button"})
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # Verify Browser Tool was executed
    mock_browser.execute.assert_awaited_with({"action": "click", "selector": "#btn"})
    
    # Verify proper logging of the tool use?
    # log_span should be called for thought AND tool use
    assert mock_logger.log_span.call_count >= 1
