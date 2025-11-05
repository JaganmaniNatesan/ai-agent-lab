#!/bin/bash
#
# =========================================
# 🍎 AI Agent Lab - macOS Setup Script
# =========================================
#
# This script:
#  1. Checks for Homebrew + installs dependencies
#  2. Sets up a Python virtual environment (3.12 preferred)
#  3. Installs required Python packages
#  4. Exports dependencies to requirements.txt
# =========================================

set -e
set -o pipefail

# ---- Color helpers ----
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

log()   { echo -e "${GREEN}→ $1${RESET}"; }
warn()  { echo -e "${YELLOW}⚠️  $1${RESET}"; }
error() { echo -e "${RED}❌ $1${RESET}"; }

# ---- Homebrew setup ----
log "Checking Homebrew..."
if ! command -v brew &>/dev/null; then
  warn "Homebrew not found. Installing..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  log "Homebrew is installed ✅"
fi

# ---- Python installation (prefer 3.12) ----
log "Checking Python installation..."
if brew list --versions python@3.12 >/dev/null; then
  log "Python 3.12 already installed ✅"
else
  warn "Installing Python 3.12 (recommended version)..."
  if brew install python@3.12; then
    log "Python 3.12 installed successfully."
  else
    warn "Python 3.12 not available, installing latest brew python instead..."
    brew install python
  fi
fi

# ---- Redis, SQLite, Git, Ollama ----
log "Installing core formulae..."
brew install redis sqlite git ollama || warn "Some brew packages already installed."

# ---- Determine active Python binary ----
PYTHON_BIN="$(brew --prefix)/opt/python@3.12/bin/python3.12"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3)"
fi
log "Using Python binary: $PYTHON_BIN"

# ---- Virtual environment ----
log "Creating Python virtual environment..."
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  warn "Virtual environment already exists."
fi

# ---- Activate venv ----
source "$VENV_DIR/bin/activate"

# ---- Python packages ----
log "Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn pydantic sqlalchemy redis chromadb sentence-transformers python-dotenv black ruff mypy openpyxl faiss-cpu sentence-transformers numpy scipy scikit-learn

# ---- Ollama check ----
if command -v ollama &>/dev/null; then
  log "Ollama detected ✅"
else
  warn "Ollama not found. Install from https://ollama.ai/download"
fi

# ---- Export requirements ----
log "📦 Exporting requirements.txt ..."
"$VENV_DIR/bin/python" tools/export_requirements.py || warn "Skipped export (tools/export_requirements.py not found)."

# ---- Final messages ----
log "✅ Setup complete!"
echo
echo "Next steps:"
echo "1️⃣ Activate your environment:"
echo "   source .venv/bin/activate"
echo "2️⃣ Run the FastAPI server:"
echo "   uvicorn main:api --reload"
echo "3️⃣ (Optional) Run health check:"
echo "   python tools/health_check.py"
echo
echo -e "${GREEN}✨ AI Agent Lab environment ready!${RESET}"