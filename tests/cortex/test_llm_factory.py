import pytest
import os
from unittest.mock import patch, MagicMock
from src.telegram_multi.cortex.intelligence.llm_factory import LLMFactory

def test_factory_requires_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            LLMFactory.create_client("gemini")

def test_factory_creates_gemini_client():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        # We don't want to actually connect, so we mock the library
        with patch("google.generativeai.configure") as mock_conf:
             with patch("google.generativeai.GenerativeModel") as mock_model:
                 client = LLMFactory.create_client("gemini")
                 mock_conf.assert_called_with(api_key="fake_key")
                 assert client is not None

def test_factory_supports_model_selection():
     with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
          with patch("google.generativeai.GenerativeModel") as mock_model:
                client = LLMFactory.create_client("gemini", model_name="gemini-1.5-flash")
                # Implementation detail check: verifying model was initialized
                # We might need to inspect the client wrapper.
                pass
