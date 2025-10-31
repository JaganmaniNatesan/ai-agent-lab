# 🧠 AI Agent Lab

> A hands-on journey to build a **local-first AI Agent** from scratch — powered by FastAPI, Ollama, and ReAct reasoning.

This project walks through the complete development of a production-style “Research & Action” agent capable of:
- Conversing and reasoning using local LLMs
- Calling structured tools (math, text, API)
- Storing short-term memory
- Planning multi-step actions via ReAct loops
- Running entirely offline (via Ollama)

---

## 🚀 Features

| Capability | Description |
|-------------|--------------|
| 🧩 **Modular Architecture** | `agent/`, `models/`, `tools/`, and `schemas/` for clean separation |
| ⚡ **FastAPI Backend** | REST API for chat, tools, and reasoning |
| 🧠 **Local LLMs** | Integrated with [Ollama](https://ollama.ai) (e.g. `mistral`, `llama3.1`) |
| 🧮 **Structured Tools** | Example tools: `add_numbers`, `to_uppercase`, extendable via registry |
| 🔁 **ReAct Loop** | Thought → Action → Observation → Final Answer cycle |
| 💾 **SQLite Memory** | Local persistent chat and short-term memory |
| 🧰 **Health Check** | Verifies Python, Redis, Ollama, DB, and FastAPI endpoints |
| 🧾 **Auto Setup** | Cross-platform installers (`bootstrap.py`, `setup_mac.sh`, `install.py`) |

---

## 🧰 Tech Stack

- **Python** 3.12+
- **FastAPI** + **Uvicorn**
- **SQLite** (WAL mode)
- **Redis** (optional for caching)
- **Ollama** (local model runner)
- **ChromaDB** (for embeddings, upcoming)
- **Sentence Transformers** (RAG support)
- **Pydantic** / **SQLAlchemy**

---

## 🪜 Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/JaganmaniNatesan/ai-agent-lab.git
cd ai-agent-lab
