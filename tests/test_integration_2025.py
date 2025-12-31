import pytest
from unittest.mock import MagicMock, patch
from council.dev_orchestrator import DevOrchestrator
from council.agents.coder import Coder
from council.context.rolling_context import RollingContext
from council.sandbox.runner import SandboxRunner
from council.mcp.tool_search import ToolSearchTool

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Verify DevOrchestrator initializes with RollingContext"""
    orchestrator = DevOrchestrator(verbose=False)
    assert isinstance(orchestrator.context, RollingContext)
    assert orchestrator.context.max_tokens == 8000

@pytest.mark.asyncio
async def test_coder_initialization():
    """Verify Coder initializes with Sandbox and ToolSearch"""
    coder = Coder(sandbox_provider="local")
    assert isinstance(coder.sandbox, SandboxRunner)
    assert isinstance(coder.tool_search, ToolSearchTool)

@pytest.mark.asyncio
async def test_coder_execution_flow():
    """Verify Coder.execute uses ToolSearch and Sandbox"""
    coder = Coder(sandbox_provider="local")
    
    # Mock dependencies
    coder._call_llm = MagicMock(return_value="```python\nprint('Hello World')\n```")
    
    mock_sandbox_result = MagicMock()
    mock_sandbox_result.status = "success"
    mock_sandbox_result.stdout = "Hello World"
    mock_sandbox_result.stderr = ""
    coder.sandbox.run = MagicMock(return_value=mock_sandbox_result)
    
    coder.tool_search.search_and_load = MagicMock(return_value=[])
    coder.tool_search.get_context_schema = MagicMock(return_value={})
    
    # Execute
    result = coder.execute("Write a hello world script")
    
    # Verify interactions
    coder.tool_search.search_and_load.assert_called_once()
    coder.tool_search.get_context_schema.assert_called_once()
    coder._call_llm.assert_called_once()
    coder.sandbox.run.assert_called_once_with("print('Hello World')")
    
    assert result.success
    assert "Generated and executed code" in result.changes_made

@pytest.mark.asyncio
async def test_orchestrator_context_flow():
    """Verify DevOrchestrator records context correctly"""
    orchestrator = DevOrchestrator(verbose=False)
    
    # Mock agents to avoid LLM calls
    orchestrator.architect.think_structured = MagicMock()
    orchestrator.architect.think_structured.return_value.summary = "Plan Summary"
    orchestrator.architect.think_structured.return_value.suggestions = ["Task 1"]
    
    orchestrator.coder.execute = MagicMock()
    orchestrator.coder.execute.return_value.success = True
    orchestrator.coder.execute.return_value.output = "Code Output"
    
    orchestrator.healing_loop.run = MagicMock()
    orchestrator.healing_loop.run.return_value.status.value = "success"
    orchestrator.healing_loop.run.return_value.iterations = 1
    orchestrator.healing_loop.run.return_value.final_error = None
    
    orchestrator.reviewer.vote_structured = MagicMock()
    orchestrator.reviewer.vote_structured.return_value.vote.value = "approve"
    orchestrator.reviewer.vote_structured.return_value.blocking_reason = None
    
    orchestrator.architect.vote_structured = MagicMock()
    orchestrator.architect.vote_structured.return_value.vote.value = "approve"
    
    orchestrator.coder.vote_structured = MagicMock()
    orchestrator.coder.vote_structured.return_value.vote.value = "approve"
    
    # Run a simple flow
    state = await orchestrator.dev("Test Task")
    
    # Verify context turns
    history = orchestrator.context.recent_history
    roles = [entry.role for entry in history]
    
    assert "User" in roles
    assert "Architect" in roles
    assert "Coder" in roles
    assert "System" in roles  # Healing report
    assert "Reviewer" in roles
    
    # Verify context was passed to votes
    orchestrator.architect.vote_structured.assert_called()
    call_args = orchestrator.architect.vote_structured.call_args
    assert "context" in call_args.kwargs
    assert "history" in call_args.kwargs["context"]

@pytest.mark.asyncio
async def test_base_agent_features():
    """Verify BaseAgent 2025 features (Streaming & Caching)"""
    from council.agents.base_agent import BaseAgent
    
    class TestAgent(BaseAgent):
        def think(self, task, context=None): pass
        def vote(self, proposal, context=None): pass
        def execute(self, task, plan=None): pass

    agent = TestAgent("TestAgent", "System Prompt")
    
    # Mock Gemini availability and module
    agent._has_gemini = True
    agent.cache_manager = MagicMock()
    
    # Mock google.generativeai module
    mock_genai = MagicMock()
    mock_google = MagicMock()
    mock_google.generativeai = mock_genai
    
    with patch.dict("sys.modules", {"google": mock_google, "google.generativeai": mock_genai}):
        # Test Caching Logic in _call_llm
        # Case 1: Cache creation returns None (not cached)
        agent.cache_manager.create.return_value = None
        
        # Setup Mock Model and Response
        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        
        # Configure GenerativeModel constructor to return our mock instance
        mock_genai.GenerativeModel.return_value = mock_model_instance
        
        response = agent._call_llm("Prompt")
        assert response == "Response"
        agent.cache_manager.create.assert_called_once()
        
        # Test Streaming Logic
        # Mock streaming response (iterator)
        mock_chunk1 = MagicMock(); mock_chunk1.text = "Hello "
        mock_chunk2 = MagicMock(); mock_chunk2.text = "World"
        mock_model_instance.generate_content.return_value = [mock_chunk1, mock_chunk2]
        
        chunks = list(agent._call_llm_stream("Prompt"))
        assert chunks == ["Hello ", "World"]
