#!/usr/bin/env python3
"""
AI Agent Lab - Project Health Check
-----------------------------------
Checks:
✅ Python environment
✅ Package imports
✅ SQLite & Redis
✅ Ollama local models
✅ FastAPI server startup and route health
"""

import subprocess
import sqlite3
import importlib
import sys
import time
import urllib.request
from pathlib import Path


# ──────────────────────────────────────────────
def check_python():
    print("🐍 Checking Python environment...")
    print(f"Version: {sys.version.split()[0]}")
    if not Path(".venv").exists() and not Path("venv").exists():
        print("⚠️  Virtual environment not found.")
    else:
        print("✅ Virtual environment detected.")


def check_imports():
    print("\n📦 Verifying Python packages...")
    packages = ["fastapi", "uvicorn", "pydantic", "sqlalchemy", "redis", "chromadb"]
    for pkg in packages:
        try:
            importlib.import_module(pkg)
            print(f"✅ {pkg}")
        except ImportError:
            print(f"❌ {pkg} not installed. Run: pip install {pkg}")


def check_sqlite():
    print("\n🗄️  Checking SQLite database...")
    db_path = Path("chat_memory.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"✅ Connected to {db_path} (Tables: {tables if tables else 'none'})")
        conn.close()
    except Exception as e:
        print(f"❌ SQLite error: {e}")


def check_redis():
    print("\n🧱 Checking Redis connection...")
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        print("✅ Redis reachable at localhost:6379")
    except Exception as e:
        print(f"⚠️  Redis not responding: {e}")


def check_ollama():
    print("\n🧠 Checking Ollama models...")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        models = [line.split()[0] for line in result.stdout.strip().split("\n")[1:]]
        if models:
            print("✅ Ollama models installed:", ", ".join(models))
        else:
            print("⚠️  No models found. Try: ollama pull mistral")
    except Exception as e:
        print(f"❌ Ollama check failed: {e}")


def check_fastapi():
    print("\n🌐 Checking FastAPI server startup...")
    try:
        # Launch Uvicorn in a subprocess
        process = subprocess.Popen(
            ["uvicorn", "main:api", "--port", "9999", "--log-level", "error"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(3)  # give it a moment to start

        # Test HTTP GET /
        try:
            with urllib.request.urlopen("http://127.0.0.1:9999/") as resp:
                if resp.status == 200:
                    print("✅ FastAPI running and responding at /")
                else:
                    print(f"⚠️  FastAPI responded with status {resp.status}")
        except Exception as e:
            print(f"❌ Unable to reach FastAPI: {e}")
        finally:
            process.terminate()
            process.wait(timeout=3)
            print("🛑 FastAPI server stopped.")
    except Exception as e:
        print(f"❌ FastAPI launch failed: {e}")


# ──────────────────────────────────────────────
def main():
    print("🩺 Running AI Agent Lab Health Check...\n")
    check_python()
    check_imports()
    check_sqlite()
    check_redis()
    check_ollama()
    check_fastapi()
    print("\n✅ Health check complete.")


if __name__ == "__main__":
    main()
