# THE-AGENTS-WORKSTATION

A production-ready, autonomous, self-healing software engineering workstation with native Band of Agents integration.

![CI](https://github.com/Darkwarrior10110/The-Agents-Workstation/actions/workflows/ci.yml/badge.svg)

## Overview

Provide a high-level natural language prompt. The workstation spins up a team of specialized AI agents that collaborate, build, execute, test, and repair software inside an isolated sandbox until it's functional.

Features a cyberpunk Mission Control dashboard for real-time visualization and Band of Agents integration for live peer-to-peer agent telemetry.

## Architecture

| Agent | Role |
|-------|------|
| Planner | Parses requirements, creates dependency graph of tasks |
| Backend/Frontend | Generate code from structural snapshots |
| Terminal | Runs code, manages deps, spins up servers in sandbox |
| Supervisor | QA lead — validates, analyzes errors, triggers self-healing |
| Debug & Runtime Repair | Patches broken code using traceback + anti-loop memory |
| Band Integration | Real-time agent logging and state updates |

## Prerequisites

- Python 3.10+
- Node.js & npm (optional, for React/Vite frontends)

> Installation is recommended on Linux. Parrot OS 7.1 preferred.

## Quick Start

```bash
git clone https://github.com/Darkwarrior10110/The-Agents-Workstation.git
cd The-Agents-Workstation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python main.py
```

Open `http://127.0.0.1:8000/dashboard` in your browser.

## Configuration

### LLM Providers (`.env`)

Copy `.env.example` to `.env` and add at least one API key. Gemini is primary; GitHub Models, xAI, and Claude are fallbacks with automatic failover.

### Band of Agents

Copy the template files and fill in your credentials:

- `Planner.example.txt` → `Planner.txt`
- `Backend.example.txt` → `Backend.txt`
- `Supervisor.example.txt` → `Supervisor.txt`

## Development

```bash
pip install -r requirements.txt  # includes dev deps
pytest tests/ -v                  # run tests
ruff check .                      # lint
```

## License

MIT License — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
