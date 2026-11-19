# Interview context

- **Role**: AI Engineer at Central Tech, the IT division of Central Retail (Thailand).
- **Date**: expected Tue 24 Nov 2026 (confirmed by Fri 20 Nov evening; best case a few days later).
- **The team**: shopping chatbots for Central's sites (Supersports, Central, Tops), on fine-tuned open models plus
  Gemini. Backend possibly Go. Public examples: the Tops Chef Bot (Gemini grounded with Vertex AI Search, on LINE)
  and the Tops chatbot with real-time in-store stock checks.
- **What they ask** (from someone who works there): mostly AI, plus backend and database concepts, as practical
  problems: "what's today's date?" for an LLM, "my orders from last week", retrieving the right rules from documents
  where one keyword appears everywhere, guardrails that actually work, fine-tuning on their website, reading a
  customer's shirt photo, tables in PDFs, 2 million records and filter combinations, and how the candidate uses AI to
  get work done.
- **How this repo serves it**: each concept is something to run, read and explain; every README Decisions entry is an
  answer. The 26 practical scenarios, the study path and the system design are in the guide
  (https://claude.ai/artifact/YPMMMc34owP2ZLWq3Sx878, source `docs/guide.html`).
- **The owner's schedule**: repo `karthikeyan993/todoist`, ROADMAP.md, "Interview sprint". Mornings are study, 19:00
  IST is repo work on the Mac, 20:30 is practice out loud.
- **After the interview**: decide with the owner whether the repo continues (a LoRA fine-tune for the "fine-tuned open
  models" story, a LangGraph version, a deployed demo). If it ever goes public, remove the company and interview
  specifics first.
