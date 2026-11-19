"""Settings, all from environment variables, so the same code runs against Gemini, a local model or a gateway."""
import os
from functools import lru_cache

from openai import OpenAI

# Gemini's OpenAI-compatible endpoint. Point LLM_BASE_URL at Ollama (http://localhost:11434/v1)
# or a LiteLLM proxy and nothing else in the code changes.
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
BASE_URL = os.environ.get("LLM_BASE_URL", GEMINI_URL)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
API_KEY = os.environ.get("LLM_API_KEY", GEMINI_KEY)        # e.g. "ollama" for a local server
# Embeddings stay on their own setting: the shipped vectors were made by gemini-embedding-001, and a query
# embedded by any other model would land in a different vector space (see guide §2).
EMBED_BASE_URL = os.environ.get("EMBED_BASE_URL", GEMINI_URL)

CHAT_MODEL = os.environ.get("CHAT_MODEL", "gemini-flash-lite-latest")   # answers, tool use
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL", "gemini-2.5-flash")     # used when CHAT_MODEL keeps failing
FAST_MODEL = os.environ.get("FAST_MODEL", "gemini-flash-lite-latest")   # small jobs: filter extraction
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))                     # 3072 by default; 768 is 4x smaller

DB_PATH = os.environ.get("SHOP_DB", "data/shop.db")


def _need(key: str) -> str:
    if not key:
        raise SystemExit("Set GEMINI_API_KEY to your Google AI Studio key, e.g. export GEMINI_API_KEY=...")
    return key


@lru_cache
def client() -> OpenAI:
    # max_retries=0: llm.with_retries does it, visibly, so you can see backoff happen.
    return OpenAI(base_url=BASE_URL, api_key=_need(API_KEY), timeout=90, max_retries=0)


@lru_cache
def embed_client() -> OpenAI:
    return OpenAI(base_url=EMBED_BASE_URL, api_key=_need(GEMINI_KEY), timeout=60, max_retries=0)
