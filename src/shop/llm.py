"""Thin wrappers around the model API: retries with backoff, embeddings, JSON output."""
import json
import random
import time

import numpy as np
import openai

from .config import CHAT_MODEL, EMBED_DIM, EMBED_MODEL, FALLBACK_MODEL, client, embed_client

# Worth retrying: rate limits (429), timeouts, dropped connections, server errors (5xx).
# Not worth retrying: 400 (our request is wrong), 401/403 (bad key).
RETRYABLE = (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError, openai.InternalServerError)


def with_retries(fn, attempts: int = 6, base: float = 1.0):
    """Call fn(); on a retryable error wait 1, 2, 4, 8... seconds (+ jitter) and try again."""
    for i in range(attempts):
        try:
            return fn()
        except RETRYABLE as e:
            if i == attempts - 1:
                raise
            wait = base * 2**i + random.uniform(0, 1)  # jitter: many clients don't retry in lockstep
            print(f"  retry {i + 1}/{attempts - 1} in {wait:.1f}s ({type(e).__name__})")
            time.sleep(wait)


def embed(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts in one call. Returns float32 vectors of shape (n, EMBED_DIM), L2-normalised.

    Normalising matters: shortened Gemini embeddings (768 of 3072) are not unit length, and with unit
    vectors cosine similarity is a plain dot product.
    """
    resp = with_retries(lambda: embed_client().embeddings.create(model=EMBED_MODEL, input=texts, dimensions=EMBED_DIM))
    v = np.array([d.embedding for d in resp.data], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def json_call(model: str, system: str, user: str, schema: dict, name: str = "result", **kw) -> dict:
    """Ask for JSON that must match `schema` (structured output). Returns the parsed dict."""
    resp = with_retries(lambda: client().chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_schema", "json_schema": {"name": name, "schema": schema}},
        temperature=0,  # extraction, not creativity
        **kw,
    ))
    return json.loads(resp.choices[0].message.content)


def chat(messages: list[dict], tools: list[dict] | None = None, **kw):
    """One chat completion with tools. If the main model keeps failing (overloaded, rate-limited, timing out),
    fall back to a second model: the same idea a gateway such as LiteLLM implements with routing rules.
    Returns (response, model_used)."""
    last = None
    for model in dict.fromkeys([CHAT_MODEL, FALLBACK_MODEL]):  # de-duplicated, order kept
        try:
            resp = with_retries(lambda: client().chat.completions.create(
                model=model, messages=messages, tools=tools or None, temperature=0.2, **kw), attempts=3)
            return resp, model
        except RETRYABLE as e:
            print(f"  {model} unavailable ({type(e).__name__}); falling back")
            last = e
    raise last
