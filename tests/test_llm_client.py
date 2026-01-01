"""
Tests for LLMClient structured completion behavior.
"""

from typing import List, Dict
import sys
import types


def _ensure_litellm_stub():
    if "litellm" not in sys.modules:
        stub = types.ModuleType("litellm")
        stub.completion = lambda *args, **kwargs: None
        sys.modules["litellm"] = stub


def test_structured_completion_does_not_mutate_messages():
    _ensure_litellm_stub()
    from pydantic import BaseModel
    from council.core.llm_client import LLMClient

    class DummyResponse(BaseModel):
        value: str

    class RecordingClient(LLMClient):
        def __init__(self):
            super().__init__(default_model="test")
            self.recorded_messages: List[Dict[str, str]] = []

        def completion(
            self,
            messages: List[Dict[str, str]],
            model: str | None = None,
            temperature: float = 0.7,
            max_tokens: int | None = None,
            json_mode: bool = False,
        ) -> str:
            self.recorded_messages = messages
            return '{"value": "ok"}'

    client = RecordingClient()
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello"},
    ]
    snapshot = [m.copy() for m in messages]

    result = client.structured_completion(
        messages=messages, response_model=DummyResponse
    )

    assert result.value == "ok"
    assert messages == snapshot
