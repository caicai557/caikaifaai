import os
import sys
from unittest.mock import MagicMock, patch

# Mock google.generativeai before importing gemini_cache
sys.modules["google.generativeai"] = MagicMock()
import google.generativeai as genai

from council.context.gemini_cache import GeminiCacheManager


def test_auth_logic():
    print("🧪 Testing Auth Logic...")

    # Case 1: Explicit API Key
    mgr = GeminiCacheManager(api_key="explicit_key")
    mgr._get_client()
    genai.configure.assert_called_with(api_key="explicit_key")
    print("✅ Explicit API Key worked")

    # Reset
    genai.configure.reset_mock()
    mgr._client = None

    # Case 2: GOOGLE_API_KEY env var
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "env_google_key"}):
        mgr = GeminiCacheManager(api_key=None)
        mgr._get_client()
        genai.configure.assert_called_with(api_key="env_google_key")
        print("✅ GOOGLE_API_KEY env var worked")

    # Reset
    genai.configure.reset_mock()
    mgr._client = None

    # Case 3: GEMINI_API_KEY env var
    with patch.dict(os.environ, {"GEMINI_API_KEY": "env_gemini_key"}):
        # Ensure GOOGLE_API_KEY is NOT present
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]

        mgr = GeminiCacheManager(api_key=None)
        mgr._get_client()
        genai.configure.assert_called_with(api_key="env_gemini_key")
        print("✅ GEMINI_API_KEY env var worked")


if __name__ == "__main__":
    test_auth_logic()
