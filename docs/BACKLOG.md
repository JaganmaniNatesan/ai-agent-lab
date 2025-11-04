# 📋 BACKLOG

> Tagged backlog for planning. Check things off as you complete them.

## 🧠 Agent & Reasoning
- [ ] Add tool-arg JSON Schema validation with helpful retries
- [ ] Add time budget per turn (e.g., 5s/tool call)
- [ ] Add overall step/latency budget per request

## 🧰 Tools
- [ ] Web search + `url.read` with safety filters
- [ ] Email draft (read-only) + Calendar read-only
- [ ] Restricted shell: `pwd`, `ls`, `cat` (whitelist)

## 📚 RAG
- [ ] Switchable vector stores: Chroma ↔ SQLite-FAISS
- [ ] Hybrid retrieval (BM25 + vectors)
- [ ] Source attribution in answers (citations)

## 🧪 Testing & Quality
- [ ] Unit tests: math/text/greeting tools
- [ ] Integration tests: ReAct plans (A/B/C suites automated)
- [ ] E2E tests: API + model + tools
- [ ] Golden tasks with replay/trace diffs

## 🔭 Observability
- [ ] JSON trace export for each turn (for UI)
- [ ] Metrics: tool-call latencies, token counts
- [ ] Error categories + dashboards

## 🚀 Delivery
- [ ] Streaming (SSE) output
- [ ] Minimal React/Streamlit UI with trace viewer
- [ ] Dockerfile for server (Linux deploy)

## 🧩 Nice-to-haves
- [ ] Long-term memory compression
- [ ] Cost/time budgets surfaced to users
- [ ] Multi-user sessions with auth