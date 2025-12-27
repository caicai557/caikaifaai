import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from src.telegram_multi.cli.commands.council import start_council
from src.telegram_multi.config import TelegramConfig

@pytest_asyncio.fixture
async def mock_deps():
    with patch("src.telegram_multi.cli.commands.council.CortexDB") as MockDB, \
         patch("src.telegram_multi.cli.commands.council.LogActor") as MockLogger, \
         patch("src.telegram_multi.cli.commands.council.CouncilActor") as MockCouncil, \
         patch("src.telegram_multi.cli.commands.council.AgentActor") as MockAgent, \
         patch("src.telegram_multi.cli.commands.council.BrowserContext") as MockBrowser, \
         patch("src.telegram_multi.cli.commands.council.BrowserTool") as MockTool:
         
        # Setup Async Mocks for start methods
        mock_db_instance = MockDB.return_value
        mock_db_instance.initialize = AsyncMock()
        
        mock_logger_instance = MockLogger.return_value
        mock_logger_instance.start = AsyncMock() # actually start runs loop
        
        # We need to mock start to be an async task or just return immediately for test
        # Ideally we capture the actors.
        
        yield MockDB, MockLogger, MockCouncil, MockAgent, MockBrowser, MockTool

@pytest.mark.asyncio
async def test_start_council_initialization(mock_deps):
    MockDB, MockLogger, MockCouncil, MockAgent, MockBrowser, MockTool = mock_deps
    
    config = MagicMock(spec=TelegramConfig)
    config.instances = [MagicMock(id="inst1", profile_path="/tmp")]
    config.global_settings = MagicMock()
    
    # We call the function (it will likely run forever in real life, so we test initialization)
    # But start_council might be designed to block?
    # We should design it to take a "stop_event" or run in task.
    
    # Let's assume start_council initializes everything and starts the loop.
    # We verify it creates the actors correctly.
    
    # Executing the function partially?
    # Or just verifying the wiring logic if extracted.
    pass

    # Actually, let's test a "bootstrap" function that returns the wired actors, 
    # ensuring they are connected.
    
    from src.telegram_multi.cli.commands.council import bootstrap_system
    
    system = await bootstrap_system(config)
    
    assert system["db"] is not None
    assert system["council"] is not None
    assert system["agent"] is not None
    
    # Verify Wiring
    MockDB.assert_called()
    MockLogger.assert_called()
    MockBrowser.assert_called()
    MockTool.assert_called() # Tool created from browser
    
    # Verify Agent has tool?
    # MockAgent.return_value.register_tool.assert_called_with("browser", ...)
