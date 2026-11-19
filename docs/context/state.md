# Current state (as of 19 Nov 2026)

## Built
Steps A–D are done: hybrid search (A), the agent loop with tools (B), guardrails, PII masking, cache and evals (C),
photo search, PDF tables and the intent classifier (D). All 49 offline tests passed. The live suite grew from
21/21 to 36/36 on Gemini. The expanded run checked 34/34 filter fields and 60/60 returned products.

## Provider and models
- The Gemini API, paid tier (prepaid credits from 19 Nov), through its OpenAI-compatible endpoint with the `openai`
  SDK. Key: `GEMINI_API_KEY`.
- Chat and small jobs: `gemini-flash-lite-latest`. Fallback: `gemini-flash-latest`. Embeddings:
  `gemini-embedding-001`, 768 dimensions.
- Optional route: `SHOP_PROVIDER=openrouter` with `OPENROUTER_API_KEY`. OpenRouter serves the same embedding model
  (identical vectors), so the shipped vectors stay valid. All settings: `src/shop/config.py`.

## Shipped data
- `shop load` builds the Git-ignored `data/shop.db` from `src/shop/catalog.py`. The expanded seed has 2,327 listings
  across 24 categories, 49,770 size/store inventory records and 180 orders. The original had 2,048 listings,
  44,760 inventory records and 60 orders. Supersports and Central have separate offers for the same navy trail shoe.
- `vectors/model_vectors.npz`: 552 product-model vectors. `evals/intents_vectors.npz`: classifier vectors.
- Both are Gemini embeddings. Changing the embedding model means re-embedding both (`shop load --fresh`,
  `shop intents train --features embed`).

## Quirks found during the build
- Gemini's compatible endpoint: send an assistant tool-call message back unchanged (it carries a thought signature).
- PDF file parts are rejected with a 400; render pages to images (`pdftable.page_images`).
- `reasoning_effort: "none"` is rejected for Flash-Lite.
- The free tier allowed 100 embedded texts a minute, about 1,000 a day, and no image generation. On the free tier set
  `EMBED_PER_MINUTE=90`.

## Measured
Eval 21/21 on three routes: free tier 3.2 min, OpenRouter 1.0 min, paid tier 0.6 min. One search: 7.7 s free tier,
about 1.1 s paid tier, almost all of it the filter-extraction LLM call. Classifier macro F1: 0.70 (TF-IDF) and 0.97
(embeddings) on 65 held-out, model-generated messages.
