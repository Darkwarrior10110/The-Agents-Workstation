#!/bin/bash

# THE-AGENTS-WORKSTATION - Start Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "[OK] Virtual environment activated"
else
    echo "[WARN] No venv found. Create one: python3 -m venv venv"
fi

if [ ! -f ".env" ]; then
    echo "[WARN] No .env file found. Copy .env.example to .env and configure it."
fi

echo "Starting THE-AGENTS-WORKSTATION..."
exec python3 main.py "$@"
