import os
import re
import sys
from functools import lru_cache

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path to import translate modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.telegram_multi.translator import TranslatorFactory
from src.telegram_multi.config import TranslationConfig

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranslationRequest(BaseModel):
    text: str
    target_lang: str = "zh-CN"


class GovernanceConfig(BaseModel):
    """Dynamic CSS Selectors for Telegram Web"""

    # Incoming Messages
    message_selector: str = ".message, .bubble, [class*='message']"
    text_content_selector: str = ".text-content"
    container_selector: str = (
        ".messages-container, .bubbles, .bubbles-group, #MiddleColumn"
    )


@app.get("/health")
def read_root():
    return {"status": "ok", "service": "seabox-api"}


@app.get("/config")
def get_config():
    """Return dynamic governance configuration"""
    return GovernanceConfig()


@app.get("/stats")
def get_stats():
    # Mock data for dashboard
    return {
        "chars_available": 99818,
        "expiry_date": "2025-06-23",
        "active_instances": 3,
    }


def redact_pii(text: str) -> str:
    """Simple Regex-based PII Redaction (Level 1 Governance)"""
    # Email
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", text)
    # Phone (Simple international format)
    text = re.sub(r"(\+\d{1,3}[- ]?)?\d{10,14}", "[PHONE]", text)
    # Crypto Address (Simple ETH/BTC check - very basic)
    text = re.sub(r"0x[a-fA-F0-9]{40}", "[CRYPTO_ETH]", text)
    return text


def has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r"[\u4e00-\u9fa5]", text))


@lru_cache(maxsize=1)
def get_translator():
    """Singleton Translator Factory"""
    config = TranslationConfig(
        enabled=True,
        provider="google",
        source_lang="auto",
        target_lang="en",  # Default, overridden in call
    )
    return TranslatorFactory.create(config)


@app.post("/translate")
def translate(req: TranslationRequest):
    try:
        # 1. PII Redaction (Governance)
        clean_text = redact_pii(req.text)

        # 2. Translation (Using Singleton)
        translator = get_translator()
        # Note: We pass target_lang dynamically here, overriding config
        # defaults if needed. But wait, Translator.translate() takes
        # dest_lang! The Translator instance has a config, but translate()
        # method args override it. So we can reuse the SAME instance for
        # different target langs.
        result = translator.translate(clean_text, "auto", req.target_lang)

        # 3. Quality Check (Outgoing Governance)
        # If target is English-like but result still has Chinese, flag it
        blocked = False
        if req.target_lang in ("en", "en-US", "en-GB") and has_chinese(result):
            blocked = True

        return {
            "translated": result,
            "original": req.text,
            "clean_text": clean_text,
            "blocked": blocked,
            "reason": "Translation incomplete (Chinese detected)" if blocked else None,
        }
    except Exception as e:
        return {"error": str(e), "translated": req.text}


if __name__ == "__main__":
    # Electron will spawn this process
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port)
