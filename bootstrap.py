#!/usr/bin/env python3
"""
AI Agent Lab - Universal Bootstrap
Detects OS and chooses the right setup method automatically.
"""
import platform
import subprocess
import sys
from pathlib import Path


def run(cmd, shell=False):
    print(f"→ {cmd}")
    subprocess.run(cmd, shell=shell, check=True)


def main():
    os_type = platform.system().lower()
    print(f"🧠 Bootstrapping environment for {os_type}...")

    # If macOS, prefer the brew script
    if os_type == "darwin" and Path("setup_mac.sh").exists():
        print("🍎 macOS detected → using setup_mac.sh")
        run(["bash", "setup_mac.sh"])
    else:
        print("🐍 Using cross-platform Python installer")
        run([sys.executable, "install.py"])

    print("✅ Environment setup complete!")


if __name__ == "__main__":
    main()