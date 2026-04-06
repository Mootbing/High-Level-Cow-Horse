#!/usr/bin/env python3
"""Run the audit worker — no pip install -e . needed."""

import subprocess
import sys
import os

# Add src/ to Python path so openclaw is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

REQUIRED = [
    "sqlalchemy",
    "asyncpg",
    "structlog",
    "pydantic_settings",
    "httpx",
    "slugify",
    "PIL",
]

missing = []
for pkg in REQUIRED:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    # Map import names to pip package names
    pip_names = {
        "PIL": "pillow",
        "pydantic_settings": "pydantic-settings",
        "slugify": "python-slugify",
    }
    to_install = [pip_names.get(m, m) for m in missing]
    print(f"Installing missing deps: {', '.join(to_install)}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", *to_install])

import asyncio
from openclaw.audit_worker.worker import run_audit_worker

if __name__ == "__main__":
    print("Audit worker starting — polling for tasks...")
    asyncio.run(run_audit_worker())
