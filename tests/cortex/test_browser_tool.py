import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.telegram_multi.cortex.tools.browser_tool import BrowserTool
from src.telegram_multi.browser_context import BrowserContext

@pytest_asyncio.fixture
async def tool_setup():
    # Mock BrowserContext
    mock_ctx = MagicMock(spec=BrowserContext)
    # Mock page object inside context
    mock_page = AsyncMock()
    mock_ctx.page = mock_page
    
    tool = BrowserTool(mock_ctx)
    yield tool, mock_page

@pytest.mark.asyncio
async def test_tool_execute_click(tool_setup):
    tool, mock_page = tool_setup
    
    # Execute "click" action
    result = await tool.execute({
        "action": "click",
        "selector": "#login-button"
    })
    
    # Verify page.click called
    mock_page.click.assert_awaited_with("#login-button", timeout=5000)
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_tool_execute_type(tool_setup):
    tool, mock_page = tool_setup
    
    result = await tool.execute({
        "action": "type",
        "selector": "#input",
        "text": "hello"
    })
    
    mock_page.fill.assert_awaited_with("#input", "hello", timeout=5000)
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_tool_handles_error(tool_setup):
    tool, mock_page = tool_setup
    
    # Simulate error
    mock_page.click.side_effect = Exception("Element not found")
    
    result = await tool.execute({
        "action": "click",
        "selector": "#bad"
    })
    
    assert result["status"] == "error"
    assert "Element not found" in result["error"]
