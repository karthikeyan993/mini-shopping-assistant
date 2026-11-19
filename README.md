# Mini shopping assistant

A small shopping assistant for a sports store, built to learn AI engineering end to end: hybrid search, tool calling,
guardrails, evals, vision. Synthetic catalog (real brand names, invented products and prices); not affiliated with any
retailer.

Built AI-native on 19–20 Nov 2026 as preparation for an AI Engineer interview (a retail chatbot team working with
Gemini and fine-tuned open models): every module is something to run, read and explain. Every step is explained in
depth in the guide: https://claude.ai/artifact/YPMMMc34owP2ZLWq3Sx878 (source: [docs/guide.html](docs/guide.html)).
Working context for coding agents (Claude Code, Codex): [AGENTS.md](AGENTS.md).

## Run it (Mac)

```bash
brew install uv
```

```bash
git clone https://github.com/karthikeyan993/mini-shopping-assistant && cd mini-shopping-assistant
```

```bash
export GEMINI_API_KEY=...   # Gemini API (default); or OPENROUTER_API_KEY=... SHOP_PROVIDER=openrouter
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

```bash
uv run shop ask "blue running shoes under 3000 baht" "is the second one in stock in size 42 at CentralWorld?"
```

```bash
uv run shop ask "show my orders from last week" --user u1
```

```bash
uv run shop eval            # 21 cases, about 40 s on the paid tier (3 min on the free tier)
```

```bash
uv run shop photo samples/shirt_photo.jpg    # or a photo of your own
```

```bash
uv run shop size-chart samples/size_chart.pdf --chest 102
```

```bash
uv run shop intents train "can I talk to a real person"
```

Re-embed with your own key: `uv run shop load --fresh` (486 texts, seconds on the paid tier). On the free tier
(100 texts a minute and a daily cap) set `EMBED_PER_MINUTE=90` and use `--limit 45` to embed one batch.

Point the chat at another provider without code changes. Embeddings keep their own settings (`EMBED_BASE_URL`,
`EMBED_API_KEY`, `EMBED_MODEL`, `EMBED_DIM`): the shipped vectors come from gemini-embedding-001, and queries must be
embedded by the same model. Switching the embedding model means `shop load --fresh` (re-embed everything).

```bash
# Gemini first, OpenRouter as the fallback when Gemini is rate-limited or down
export FALLBACK_BASE_URL=https://openrouter.ai/api/v1 FALLBACK_API_KEY=$OPENROUTER_API_KEY FALLBACK_MODEL=google/gemini-3.5-flash-lite
```

```bash
# OpenRouter for all chat calls (faster than Gemini's free tier)
export LLM_BASE_URL=https://openrouter.ai/api/v1 LLM_API_KEY=$OPENROUTER_API_KEY CHAT_MODEL=google/gemini-3.5-flash-lite FAST_MODEL=google/gemini-3.5-flash-lite
```

```bash
# A local model in Ollama for chat
export LLM_BASE_URL=http://localhost:11434/v1 LLM_API_KEY=ollama CHAT_MODEL=qwen3:8b FAST_MODEL=qwen3:8b
```

Fireworks works the same way (`https://api.fireworks.ai/inference/v1`), for chat and, after re-embedding, for
embeddings.

## Steps

| Step | What | Status |
|---|---|---|
| A | Catalog, filter extraction, hybrid search (SQL + BM25 + vectors), Thai segmentation, incremental embedding job | done |
| B | Agent loop by hand: tools for search, stock and orders, date injection, follow-ups | done |
| C | Guardrails, PII masking, grounding check, eval set, cache, model fallback | done |
| D | Shirt photo → attributes → search, PDF size chart → rows, intent classifier | done |

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
  agent.py    the loop: model → tool calls → results → model, with a step limit and the guard layers
  guard.py    PII masking (with checksums), scope and injection screening, price grounding
  cache.py    a TTL cache for search results (Redis in production)
  evals.py    the eval runner for evals/cases.json
  vision.py   photo → attributes (vision model, JSON schema) → filters → search
  pdftable.py PDF size chart → text layer vs page image read by the model → validated rows → size picked in code
  intents.py  intent classifier: generated labelled data, TF-IDF or embeddings + logistic regression
  cli.py      shop load | search | ask | chat | eval | photo | size-chart | intents | explain-sql | export-vectors
tests/        offline tests (no API calls)
vectors/      model_vectors.npz: 486 × 768 Gemini embeddings
evals/        cases.json (21 eval cases), intents.jsonl (324 labelled messages, Thai and English)
samples/      shirt_photo.jpg (generated with Gemini's image model), shirt.png (a drawing), size_chart.pdf,
              and the script that makes the drawing and the PDF
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
- **A client-side rate limiter** (`EMBED_PER_MINUTE`: 1,500 by default, 90 on the free tier's 100-a-minute limit)
  instead of retrying into 429s.
- **Reciprocal Rank Fusion** combines keyword and vector ranks without calibrating their scores.
- **Thai**: PyThaiNLP segmentation, with brand and colour spellings added to its dictionary so ไนกี้ stays one word.
- **The agent loop is written by hand** (about 60 lines in `agent.py`): every step visible; a framework (LangGraph)
  would add checkpoints and branching when needed.
- **The user id is never a tool argument.** It comes from the session; `get_order` answers the same way for "doesn't
  exist" and "someone else's".
- **Dates are computed in code.** The model picks a named period; `timeutil.resolve` returns exact Bangkok dates; the
  answer states them. "Last week" = the previous Monday–Sunday.
- **Guardrails in layers**: PII masked before the model or the log sees it (Thai ID and card numbers validated by
  checksum, so order numbers and prices stay); regex rules then a small model screen scope and injection; every
  price in the answer must appear in a tool result, else one rewrite, else it is removed.
- **Evals before opinions**: `shop eval` runs 21 cases (search, agent, guard). The first run caught a real false
  positive: "what's the date today?" was blocked as out of scope.
- **Photo search reads attributes, then reuses the text search.** The dominant colour is the filter; a second
  colour goes into the ranking text (a striped navy-and-white shirt filtered on "navy OR white" returned white shirts).
- **PDF tables: the model reads the page image, code validates and decides.** The compatible endpoint rejected a PDF
  part, so pages are rendered to images (what Gemini's native API does internally).
- **The classifier ladder, measured** on the same 65 held-out messages: character n-gram TF-IDF + logistic regression,
  macro F1 0.70 ("out of scope" 0.18: spelling can't capture "not about shopping"); Gemini embeddings + logistic
  regression, macro F1 0.97 ("out of scope" 1.00). The messages are model-generated, so real chats will score lower.
- **OpenRouter serves the same embedding model** (google/gemini-embedding-001): cosine 1.0 against the stored vector,
  so `SHOP_PROVIDER=openrouter` keeps the shipped vectors. OpenAI's text-embedding-3-small scored Thai vs English
  "blue running shoe" at 0.36 against Gemini's 0.86: for a Thai shop, test multilingual quality before choosing.
- **Three routes, one eval set.** Same 21 cases, 21/21 on each: Gemini API free tier 3.2 min (11.6 s per agent
  case); Gemini 3.5 Flash-Lite through OpenRouter 1.0 min (4.3 s); Gemini API paid tier 0.6 min (3.4 s), now the
  default. The fallback can be a different provider (`FALLBACK_BASE_URL`); a simulated Gemini outage was answered
  through OpenRouter.
- **Free-tier limits met during the build**: 100 embedded texts a minute and a 1,000 limit named in the daily-quota
  error, and no image generation. Hence the shipped vectors and the cached classifier vectors. The paid tier (from
  19 Nov) removed all three; on the free tier set `EMBED_PER_MINUTE=90`.
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
