# 🗺️ ROADMAP

> High-level sequence of milestones with tracking checkboxes.

## Milestone 1 — Core Agent & API (Done)
- [x] FastAPI service with `/agent/react`, `/memory/*`
- [x] Local LLM with Ollama (`llama3.1:latest`)
- [x] Tool registry: math, transform, greeting
- [x] SQLite short-term memory

## Milestone 2 — ReAct & Guardrails (Done)
- [x] ReAct loop (Thought → Action → Observation → Answer)
- [x] JSON repair + placeholder handling
- [x] Intent-based heuristics + early-stops
- [x] Debug tracing

## Milestone 3 — Refactor & Tests (In Progress)
- [x] Modularize `agent/react`
- [ ] Unit tests: tools
- [ ] Integration tests: agent loop
- [ ] CI: ruff/black/mypy
- [ ] Improve summary & name handling

## Milestone 4 — RAG (Next)
- [ ] Ingest `/docs` → embed → store
- [ ] Retrieval tool + citations
- [ ] RAG evaluation set (hit@k)

## Milestone 5 — Real Tools & Safety
- [ ] Web search + page reader
- [ ] Email (draft), Calendar (read-only)
- [ ] Restricted shell
- [ ] “Dry-run” planning mode

## Milestone 6 — Shipping & UI
- [ ] Streaming endpoints
- [ ] Trace viewer (minimal UI)
- [ ] Containerization (Docker)