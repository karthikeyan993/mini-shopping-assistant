"""Settings, all from environment variables, so the same code runs against Gemini, a local model or a gateway."""
import os
from functools import lru_cache

from openai import OpenAI

# Gemini's OpenAI-compatible endpoint. Point LLM_BASE_URL at Ollama (http://localhost:11434/v1)
# or a LiteLLM proxy and nothing else in the code changes.
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_URL = "https://openrouter.ai/api/v1"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# One switch for the usual setups; every single setting below can still be overridden by its own variable.
#   gemini      (default) everything on the Gemini API with GEMINI_API_KEY
#   openrouter  chat and embeddings through OpenRouter with OPENROUTER_API_KEY. Same embedding model
#               (google/gemini-embedding-001: identical vectors, so the shipped ones stay valid); the fallback
#               goes to the Gemini API directly when GEMINI_API_KEY is set.
PROVIDER = os.environ.get("SHOP_PROVIDER", "gemini")
if PROVIDER == "openrouter":
    _d = dict(url=OPENROUTER_URL, key=OPENROUTER_KEY, chat="google/gemini-3.5-flash-lite",
              fast="google/gemini-3.5-flash-lite", embed="google/gemini-embedding-001",
              fb_url=GEMINI_URL if GEMINI_KEY else OPENROUTER_URL, fb_key=GEMINI_KEY or OPENROUTER_KEY,
              fb_model="gemini-flash-lite-latest" if GEMINI_KEY else "google/gemini-3.5-flash")
else:
    _d = dict(url=GEMINI_URL, key=GEMINI_KEY, chat="gemini-flash-lite-latest", fast="gemini-flash-lite-latest",
              embed="gemini-embedding-001", fb_url=GEMINI_URL, fb_key=GEMINI_KEY, fb_model="gemini-2.5-flash")

# Chat. Point LLM_BASE_URL at Ollama (http://localhost:11434/v1) or a LiteLLM proxy and nothing else changes.
BASE_URL = os.environ.get("LLM_BASE_URL", _d["url"])
API_KEY = os.environ.get("LLM_API_KEY", _d["key"])
CHAT_MODEL = os.environ.get("CHAT_MODEL", _d["chat"])          # answers, tool use
FAST_MODEL = os.environ.get("FAST_MODEL", _d["fast"])          # small jobs: filter extraction, screening
# The fallback can be another provider, so one provider's outage or quota doesn't stop the bot.
FALLBACK_BASE_URL = os.environ.get("FALLBACK_BASE_URL", _d["fb_url"])
FALLBACK_API_KEY = os.environ.get("FALLBACK_API_KEY", _d["fb_key"])
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL", _d["fb_model"])
# Embeddings keep their own settings: the shipped vectors come from gemini-embedding-001, and a query embedded by
# any other model lands in a different vector space (guide §2). Switching models means `shop load --fresh`.
EMBED_BASE_URL = os.environ.get("EMBED_BASE_URL", _d["url"])
EMBED_API_KEY = os.environ.get("EMBED_API_KEY", _d["key"])
EMBED_MODEL = os.environ.get("EMBED_MODEL", _d["embed"])
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))            # 3072 by default; 768 is 4x smaller
# Client-side rate limit for embedding jobs: the Gemini free tier allows 100 texts a minute.
EMBED_PER_MINUTE = int(os.environ.get("EMBED_PER_MINUTE", "90" if PROVIDER == "gemini" else "3000"))

DB_PATH = os.environ.get("SHOP_DB", "data/shop.db")


def _need(key: str) -> str:
    if not key:
        raise SystemExit("Set GEMINI_API_KEY (or OPENROUTER_API_KEY with SHOP_PROVIDER=openrouter); see the README.")
    return key


@lru_cache
def client() -> OpenAI:
    # max_retries=0: llm.with_retries does it, visibly, so you can see backoff happen.
    return OpenAI(base_url=BASE_URL, api_key=_need(API_KEY), timeout=90, max_retries=0)


@lru_cache
def embed_client() -> OpenAI:
    return OpenAI(base_url=EMBED_BASE_URL, api_key=_need(EMBED_API_KEY), timeout=60, max_retries=0)


@lru_cache
def fallback_client() -> OpenAI:
    return OpenAI(base_url=FALLBACK_BASE_URL, api_key=_need(FALLBACK_API_KEY), timeout=90, max_retries=0)
