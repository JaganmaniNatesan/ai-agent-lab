# 🚀 AI Agent Lab — ACTION PLAN

This document tracks the **current status, decisions made, and next milestones** for building our production-grade Research & Action AI Agent.

---

## ✅ Phase 1 — Foundations (Completed)
- [x] Project setup (repo, venv, scripts, bootstrap) — `setup_mac.sh`, `install.py`, requirements auto-export
- [x] Local LLM setup (Ollama) — default `llama3.1:latest`
- [x] Core API (FastAPI) — `/agent/react`, `/memory/*`
- [x] Tooling system — registry + validation
- [x] SQLite short-term memory — per-session append-only chat log
- [x] ReAct agent loop — multi-step tool planning + observation
- [x] JSON parsing & self-repair — fences, malformed JSON, placeholder quoting
- [x] Step-budget execution — intent-based caps
- [x] Basic evaluation scripts — `test_react_memory.sh` + suites A/B/C
- [x] Debug traces — thought → action → observation

## ✅ Phase 2 — Agent Intelligence (Completed)
- [x] Auto-finalization rules (math/greet/transform)
- [x] `<last_result>` placeholder filling
- [x] Memory-based identity (“Who am I?”)
- [x] First-calculation retrieval
- [x] One-line conversation summary (recent turns)
- [x] Goodbye personalization
- [x] Duplicate tool call detection
- [x] Intent classification: greet | math | transform | unknown

## 🔜 Phase 3 — Refactor & Improve (In Progress)
- [x] Modularize `agent/react_agent.py` into package
- [ ] Add docstrings + type hints
- [ ] Unit tests for tools (math, text, greeting)
- [ ] Integration tests for agent loop
- [ ] CI linting (ruff, black, mypy)
- [ ] Move test scripts into `/scripts/tests`
- [ ] Optional: richer summary (full history / compressed)

## 🔜 Phase 4 — RAG & Search (Next)
- [ ] Ingestion: split → embed → store (Chroma or SQLite-FAISS)
- [ ] `knowledge.search` tool with citations
- [ ] Anti-hallucination guardrails (answer only from retrieved)
- [ ] Retrieval eval (hit@k); add small benchmark set
- [ ] Offline embedder later (Qwen/OpenAI swap)

## 🔜 Phase 5 — Tooling Expansion (Soon)
- [ ] Web search + reader (SerpAPI/Tavily, `url.read`)
- [ ] Email draft tool (OAuth, least-priv)
- [ ] Calendar read-only tool
- [ ] Restricted shell tool
- [ ] “Dry-run” plan preview mode

## 🛠️ Technical Debt / Parking Lot
- [ ] Summary uses last N turns (not global)
- [ ] Better multilingual name extraction
- [ ] Division by zero -> graceful `[tool_error]`
- [ ] Guard against invented tools
- [ ] Optional JSON log traces for UI
- [ ] API schema: separate `message` vs `final_answer`

## 🚧 Future Enhancements (Wishlist)
- [ ] Async HTTP LLM driver (latency)
- [ ] OpenAI-style function calling (cloud/offline swap)
- [ ] Streaming responses (SSE/WebSocket)
- [ ] Execution graph viewer
- [ ] Cost/time budgets per request
- [ ] Long-term memory via embeddings + decay

## ✅ Next Action
- [x] You: Finish modularization of agent code
- [x] Run A/B/C suites on refactor (passed)
- [ ] Begin **Week 2 — RAG & embeddings**