#!/usr/bin/env python3
"""
AI Agent Lab – Cross-Platform Installer
---------------------------------------
Sets up Python environment, dependencies, and model tools
for macOS, Linux, or Windows.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def run(cmd, shell=False):
    """Run a shell command safely."""
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=shell, check=True)


def create_venv():
    """Create and activate virtual environment."""
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("🐍 Creating virtual environment...")
        run([sys.executable, "-m", "venv", str(venv_path)])
    else:
        print("✅ Virtual environment already exists.")
    return venv_path


def install_python_packages():
    """Install all required Python dependencies."""
    print("📦 Installing Python libraries...")
    pip = str(Path(".venv") / "bin" / "pip") if os.name != "nt" else str(Path(".venv") / "Scripts" / "pip.exe")

    pkgs = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "sqlalchemy",
        "redis",
        "chromadb",
        "sentence-transformers",
        "openpyxl",
        "requests",
        "python-dotenv",
        "black",
        "ruff",
        "mypy",
        "faiss-cpu",
        "sentence-transformers",
        "numpy",
        "scipy",
        "scikit-learn"
    ]
    run([pip, "install", "--upgrade", "pip"])
    run([pip, "install", *pkgs])


def check_ollama():
    """Optional: check or install Ollama for local models."""
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
        print("✅ Ollama detected.")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠️ Ollama not found.")
        if platform.system() == "Darwin":
            print("🍺 Try installing via Homebrew:")
            print("   brew install ollama")
        elif platform.system() == "Linux":
            print("🐧 Install from https://ollama.ai/download")
        else:
            print("💡 Windows users: install Ollama manually from the website.")


def main():
    print("🚀 AI Agent Lab Setup")
    print(f"🖥️  Detected OS: {platform.system()}")

    venv = create_venv()
    install_python_packages()
    check_ollama()

    print("\n✅ Setup complete!")
    print("Next steps:")
    print("1️⃣ Activate your environment:")
    if platform.system() == "Windows":
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    print("2️⃣ Run the API server:")
    print("   uvicorn main:api --reload")
    print("3️⃣ Visit http://127.0.0.1:8000/docs")
    subprocess.run(["python", "tools/export_requirements.py"])

if __name__ == "__main__":
    main()
