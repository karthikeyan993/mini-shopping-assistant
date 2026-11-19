# Agent instructions: mini-shopping-assistant

Read this before changing anything. It applies to every coding agent (Claude Code, Codex, others).

## Why this repo exists

- **Interview preparation.** The owner is preparing for an **AI Engineer interview at Central Tech**, the IT division of
  Central Retail (Thailand), expected **Tue 24 Nov 2026** (date confirmed by Fri 20 Nov evening; best case a few days
  later). The team builds shopping chatbots for Central's sites (Supersports, Central, Tops) on **fine-tuned open
  models plus Gemini**; their backend may be Go. The interview is AI-heavy, with backend and database concepts, and
  asks practical questions: "what's today's date?" for an LLM, "my orders from last week", retrieving the right
  rules from documents where one keyword appears everywhere, guardrails that actually work, fine-tuning on their
  website, reading a customer's shirt photo, tables in PDFs, and how the candidate uses AI to get work done.
- **What the repo is for**: a small, working version of that kind of bot, built AI-native on 19–20 Nov 2026 (Claude
  wrote it, the owner reviews it), so the owner can (1) learn each concept by running and reading real code, and
  (2) talk about a concrete AI project. Every entry in README's **Decisions** section is an interview answer.
- **Where the rest lives**:
  - The guide (study path with resources, explanations with diagrams, 26 practical scenarios, the build explained
    step by step): https://claude.ai/artifact/YPMMMc34owP2ZLWq3Sx878, source [docs/guide.html](docs/guide.html).
  - The owner's schedule and learning plan: repo `karthikeyan993/todoist`, ROADMAP.md, section "Interview sprint".
    Mornings are study, 19:00 IST is repo work on the Mac, 20:30 is practice out loud.

## How to work with the owner

- **This is a learning repo. Explain, don't only do.** Each change comes with a short explanation the owner could
  repeat in an interview: what changed, why, the alternative, what can go wrong. A line the owner can't explain
  doesn't go in.
- **Small, reviewable steps.** Deterministic code gets offline tests (`tests/`, no API calls). Model behaviour gets
  evals: after any change to a prompt, model, tool, guard or search, run `uv run shop eval` and report the numbers
  before and after.
- **Keep it small and explainable.** No new frameworks, services or dependencies unless the owner asks. Before the
  interview, anything that doesn't help explain an AI-engineering concept goes on a "later" list, not into the code.
- **Keep the docs in sync.** When the build changes, update the matching section of `docs/guide.html` (text and
  figures) and republish it to the same artifact URL, and keep README's Decisions and Layout current.
- **Git: always `main`.** Commit and push to `main`; no feature branches, no pull requests (the owner's standing
  permission). A cloud session that starts on a `claude/...` branch switches to `main`.
- **Secrets**: keys only in environment variables (`GEMINI_API_KEY`; optional `OPENROUTER_API_KEY`). Never in code,
  commits, logs or chat. `data/` is git-ignored; the trace log `data/turns.jsonl` holds masked text only.
- State times in IST. The owner uses dictation, so expect odd words and ask when the meaning is unclear.

## Current state (19 Nov 2026)

- Steps A–D are done: hybrid search, the agent loop with tools, guardrails and evals, photo search, PDF tables, the
  intent classifier. 39 offline tests pass; `shop eval` passes 21/21.
- **Provider**: the Gemini API, paid tier (prepaid credits from 19 Nov), through its OpenAI-compatible endpoint
  with the `openai` SDK. Chat and small jobs: `gemini-flash-lite-latest`; fallback: `gemini-flash-latest`;
  embeddings: `gemini-embedding-001` at 768 dimensions. `SHOP_PROVIDER=openrouter` is an optional route (same
  embedding model, identical vectors).
- **Shipped data**: `vectors/model_vectors.npz` (486 product-model vectors) and `evals/intents_vectors.npz`
  (classifier vectors) are Gemini embeddings. Changing the embedding model means re-embedding both
  (`shop load --fresh`, `shop intents train --features embed`).
- **Quirks of Gemini's OpenAI-compatible endpoint** found during the build: send an assistant tool-call message back
  unchanged (it carries a thought signature); PDF file parts are rejected with a 400 (render pages to images);
  `reasoning_effort: "none"` is rejected for Flash-Lite. The free tier allowed 100 embedded texts a minute, about
  1,000 a day, and no image generation.

## Commands

```bash
uv sync --extra dev
uv run pytest -q
uv run shop load
uv run shop search "blue running shoes in stock under 3000 baht"
uv run shop ask "show my orders from last week" --user u1
uv run shop eval
uv run shop photo samples/shirt_photo.jpg
uv run shop size-chart samples/size_chart.pdf --chest 102
uv run shop intents train --features embed
```

The file map is in README, "Layout".

## After the interview

Decide with the owner whether this continues (for example a LoRA fine-tune on Fireworks for the "fine-tuned open
models" story, a LangGraph version of the loop, or a deployed demo), then update this file. If the repo is ever made
public, remove the company and interview specifics from README and this file first.
