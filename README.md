# Mini shopping assistant

A small shopping assistant for a sports store, built to learn AI engineering end to end: hybrid search, tool calling,
guardrails, evals, vision. Synthetic catalog (real brand names, invented products and prices); not affiliated with any
retailer.

Every step is explained in depth in the guide: https://claude.ai/artifact/YPMMMc34owP2ZLWq3Sx878 (source:
[docs/guide.html](docs/guide.html)).

## Run it (Mac)

```bash
brew install uv
```

```bash
git clone https://github.com/karthikeyan993/mini-shopping-assistant && cd mini-shopping-assistant
```

```bash
export GEMINI_API_KEY=...   # your Google AI Studio key; never commit it
```

```bash
uv sync --extra dev
```

```bash
uv run shop load            # catalog + the vectors shipped in vectors/: no embedding calls needed
```

```bash
uv run shop search "blue running shoes in stock under 3000 baht"
```

```bash
uv run shop search "รองเท้าวิ่ง ไนกี้ สีดำ ใส่วิ่งไกล"
```

```bash
uv run shop explain-sql '{"category": "running shoes", "in_stock": true, "max_price": 3000}'
```

```bash
uv run pytest -q
```

Embed with your own key: `uv run shop load --fresh --limit 45` embeds one batch. A full run is 486 texts, about 6
minutes at the free tier's 100 texts a minute, and the free tier also caps texts per day, so use `--limit` unless you
need all of them.

Point it at another model server without code changes: `LLM_BASE_URL=http://localhost:11434/v1` (Ollama),
`CHAT_MODEL=...`, `FAST_MODEL=...`, `EMBED_MODEL=...`.

## Steps

| Step | What | Status |
|---|---|---|
| A | Catalog, filter extraction, hybrid search (SQL + BM25 + vectors), Thai segmentation, incremental embedding job | done |
| B | Agent loop by hand: tools for search, stock and orders, date injection, follow-ups | done |
| C | Guardrails, PII masking, grounding check, eval set, cache, model gateway | next |
| D | Shirt photo → attributes → search, PDF size chart → rows, intent classifier | |

## Layout

```
src/shop/
  config.py   settings from environment variables; one OpenAI-compatible client
  llm.py      retries with backoff, embeddings, JSON (structured) output
  catalog.py  synthetic products, stock per store, orders
  thai.py     normalisation and Thai word segmentation
  db.py       SQLite schema, indexes, FTS5 keyword index, loading
  index.py    the embedding job: per model, content hashes, rate limiter, export/import
  query.py    message → validated filters + free text
  search.py   SQL filters → BM25 + vectors → RRF → one result per model → diversity
  timeutil.py the clock: Bangkok time, named periods resolved in code
  tools.py    tool schemas (from pydantic) and implementations; the user id comes from the session
  agent.py    the loop: model → tool calls → results → model, with a step limit
  cli.py      shop load | search | ask | chat | explain-sql | export-vectors
tests/        offline tests (no API calls)
vectors/      model_vectors.npz: 486 × 768 Gemini embeddings
```

## Decisions

- **SQLite + FTS5 + numpy, not PostgreSQL + pgvector.** Zero setup for a four-day build, with the same ideas: SQL
  filters on real indexes, BM25 keyword ranking, vector ranking. The production version is below.
- **Gemini through its OpenAI-compatible endpoint, with the `openai` SDK.** The same client talks to Gemini, Ollama,
  vLLM or a LiteLLM gateway; switching is an environment variable.
- **Filters are extracted, not embedded.** The model fills a fixed JSON schema; pydantic drops any value that isn't in
  the catalog; SQL applies the filters exactly. Embeddings only rank the fuzzy remainder.
- **One vector per model, not per row.** Colours and banners share a description and colour is a filter: 486 texts
  instead of 2,048.
- **A content hash per model** makes embedding incremental (only changed text) and resumable (a crash loses only the
  batches in flight).
- **A client-side rate limiter** at 90 texts a minute, under the free tier's 100, instead of retrying into 429s.
- **Reciprocal Rank Fusion** combines keyword and vector ranks without calibrating their scores.
- **Thai**: PyThaiNLP segmentation, with brand and colour spellings added to its dictionary so ไนกี้ stays one word.
- **Flash-Lite for filter extraction**: a small, frequent job. Its latency varies (1–8 s on the free tier), which the
  timing line in `shop search` shows.

## Production version of the search

```sql
-- PostgreSQL + pgvector 0.8+
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE model_vectors (model_id text PRIMARY KEY, embed_hash text, embedding vector(768));
CREATE INDEX ON model_vectors USING hnsw (embedding vector_cosine_ops);
SET hnsw.iterative_scan = relaxed_order;   -- keep scanning until enough rows pass the filters
SELECT p.product_id
FROM products p JOIN model_vectors v USING (model_id)
WHERE p.category = $1 AND p.in_stock AND p.price <= $2
ORDER BY v.embedding <=> $3                 -- cosine distance
LIMIT 50;
```

The keyword side usually moves to OpenSearch or Elasticsearch (they have a Thai analyzer) or to a managed service such
as Vertex AI Search.
