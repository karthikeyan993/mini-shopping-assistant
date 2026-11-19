# Agent instructions

A small shopping assistant built as **AI Engineer interview preparation** (interview expected Tue 24 Nov 2026). It is a
learning repo: the owner must be able to explain every line.

## Rules
- Explain each change in a few lines the owner could repeat in an interview: what, why, the alternative, what can go
  wrong. A line the owner can't explain doesn't go in.
- Deterministic code gets offline tests. After any change to a prompt, model, tool, guard or search, run
  `uv run shop eval` and report the numbers before and after.
- Keep it small: no new frameworks, services or dependencies unless the owner asks.
- When the build changes, update the matching part of `docs/guide.html`, republish it to the same artifact URL, and
  keep README's Decisions and Layout current.
- Commit and push to `main`; no feature branches, no pull requests.
- Keys only in environment variables (`GEMINI_API_KEY`), never in code, commits, logs or chat.
- Times in IST. The owner uses dictation: expect odd words, ask when unclear.

## Commands
```bash
uv sync --extra dev
uv run pytest -q
uv run shop eval
```

## Map
- `docs/context/interview.md`: the company, the date, what they ask, how this repo serves it.
- `docs/context/state.md`: what's built, provider and models, shipped vectors, quirks, measured numbers.
- `README.md`: how to run, file layout, decisions.
- `docs/guide.html`: the guide (https://claude.ai/artifact/YPMMMc34owP2ZLWq3Sx878).
