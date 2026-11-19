"""Settings, all from environment variables, so the same code runs against Gemini, a local model or a gateway."""
import os
from functools import lru_cache

from openai import OpenAI

# Gemini's OpenAI-compatible endpoint. Point LLM_BASE_URL at Ollama (http://localhost:11434/v1)
# or a LiteLLM proxy and nothing else in the code changes.
BASE_URL = os.environ.get("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
API_KEY = os.environ.get("GEMINI_API_KEY", "")

CHAT_MODEL = os.environ.get("CHAT_MODEL", "gemini-flash-latest")        # answers, tool use
FAST_MODEL = os.environ.get("FAST_MODEL", "gemini-flash-lite-latest")   # small jobs: filter extraction
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))                     # 3072 by default; 768 is 4x smaller

DB_PATH = os.environ.get("SHOP_DB", "data/shop.db")


@lru_cache
def client() -> OpenAI:
    if not API_KEY:
        raise SystemExit("Set GEMINI_API_KEY to your Google AI Studio key, e.g. export GEMINI_API_KEY=...")
    # max_retries=0: llm.with_retries does it, visibly, so you can see backoff happen.
    return OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=90, max_retries=0)
