import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from .base import BaseActor
from ..logger import LogActor

class AgentActor(BaseActor):
    """
    Represents a specific AI persona (e.g. 'Gemini-Pro', 'Claude-3.5').
    Receives tasks, calls LLM, executes Tools, and emits Spans.
    """
    def __init__(self, name: str, logger: LogActor):
        super().__init__(name)
        self.logger = logger
        self.trace_id = str(uuid.uuid4())
        self.tools: Dict[str, Any] = {}
        self.llm_client = None

    def register_tool(self, name: str, tool_instance: Any):
        """Register a tool instance."""
        self.tools[name] = tool_instance

    def set_llm_client(self, client: Any):
        """Set the LLM Client."""
        self.llm_client = client

    async def handle(self, msg):
        """
        Msg structure expected:
        {
            "type": "THINK" | "VOTE",
            "content": str,
            "trace_id": str (optional)
        }
        """
        if not isinstance(msg, dict):
            return

        msg_type = msg.get("type", "UNKNOWN")
        content = msg.get("content", "")
        trace_id = msg.get("trace_id", self.trace_id)
        
        # 1. Start Span (User Input)
        span_id = str(uuid.uuid4())
        await self.logger.log_span((span_id, trace_id, self.name, "INPUT", content, "", 1.0))
        
        # 2. LLM Call
        if self.llm_client:
            from src.telegram_multi.cortex.intelligence.prompts import CORE_SYSTEM_PROMPT
            
            # Combine System Prompt with User Prompt
            # Optimization: Chat history management would go here
            full_prompt = f"{CORE_SYSTEM_PROMPT}\n\nUser Task: {content}"
            
            response = await self.llm_client.generate(full_prompt, tools=list(self.tools.keys()))
            llm_content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            
            # Log Thought
            await self.logger.log_span((str(uuid.uuid4()), trace_id, self.name, "THINK", content, llm_content, 0.9))
            
            # 3. Handle Tool Calls
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                
                if tool_name in self.tools:
                    # Log Tool Call
                    await self.logger.log_span((str(uuid.uuid4()), trace_id, self.name, "TOOL_CALL", str(tool_args), tool_name, 1.0))
                    
                    try:
                        result = await self.tools[tool_name].execute(tool_args)
                        # Log Tool Result
                        await self.logger.log_span((str(uuid.uuid4()), trace_id, self.name, "TOOL_RESULT", tool_name, str(result), 1.0))
                    except Exception as e:
                        logging.error(f"Tool {tool_name} failed: {e}")
                else:
                    logging.warning(f"Agent {self.name} tried to call unknown tool {tool_name}")
            
        else:
            # Fallback / Mock behavior for legacy tests
            await asyncio.sleep(0.01) 
            response = f"Processed: {content}"
            # Log Simulated Output
            await self.logger.log_span((str(uuid.uuid4()), trace_id, self.name, "OUTPUT", content, response, 0.95))
