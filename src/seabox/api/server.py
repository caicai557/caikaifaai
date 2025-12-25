import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

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

@app.get("/health")
def read_root():
    return {"status": "ok", "service": "seabox-api"}

@app.get("/stats")
def get_stats():
    # Mock data for dashboard
    return {
        "chars_available": 99818,
        "expiry_date": "2025-06-23",
        "active_instances": 3
    }

@app.post("/translate")
def translate(req: TranslationRequest):
    try:
        config = TranslationConfig(
            enabled=True,
            provider="google",
            source_lang="auto",
            target_lang=req.target_lang
        )
        translator = TranslatorFactory.create(config)
        result = translator.translate(req.text, "auto", req.target_lang)
        return {"translated": result}
    except Exception as e:
        return {"error": str(e), "translated": req.text}

if __name__ == "__main__":
    # Electron will spawn this process
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port)
