#!/usr/bin/env python3
"""
Auto-generate a clean requirements.txt file for the AI Agent Lab.
Run this after you install or update dependencies.

Usage:
    python tools/export_requirements.py
"""

import subprocess
from datetime import datetime
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parents[1]
    req_file = project_root / "requirements.txt"
    venv_pip = project_root / ".venv" / "bin" / "pip"
    if not venv_pip.exists():
        venv_pip = project_root / "venv" / "bin" / "pip"
    if not venv_pip.exists():
        venv_pip = "pip"  # fallback

    print("📦 Exporting current dependencies...")
    result = subprocess.run(
        [str(venv_pip), "freeze"], capture_output=True, text=True, check=True
    )

    with open(req_file, "w") as f:
        f.write(f"# AI Agent Lab dependencies\n# Last updated: {datetime.now()}\n\n")
        f.write(result.stdout)

    print(f"✅ requirements.txt updated at {req_file}")

if __name__ == "__main__":
    main()
