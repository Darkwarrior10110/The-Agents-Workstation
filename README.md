# ⚡ THE-AGENTS-WORKSTATION

### A Production-Ready, Autonomous, Self-Healing Software Engineering Workstation with Native Band of Agents Integration

---

## 📖 Table of Contents
1. [Overview](#-overview)
2. [Key Architecture & The Agent Matrix](#-key-architecture--the-agent-matrix)
3. [Prerequisites](#%EF%B8%8F-prerequisites)
4. [Headache-Free Installation](#-headache-free-installation)
5. [Configuration Guide](#-configuration-guide)
   - [LLM Gateway Configuration (.env)](#1-llm-gateway-configuration-env)
   - [Band of Agents Credentials Configuration](#2-band-of-agents-credentials-configuration)
6. [How to Run & Launch](#-how-to-run--launch)
7. [Using the Cyberpunk Mission Control](#%EF%B8%8F-using-the-cyberpunk-mission-control)
8. [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## 🚀 Overview

**The-Agents-Workstation** is an autonomous, self-healing software development environment. Instead of writing code manually, you provide a high-level natural language prompt. The workstation dynamically spins up a team of specialized AI agents that collaborate, build, execute, test, and repair software inside an isolated sandbox until the application is fully functional.

It features a beautiful **Aetheric Cyberpunk Mission Control Dashboard** for real-time visualization and comes integrated with the **Band of Agents** network to enable live peer-to-peer agent telemetry.

---

## 🧠 Key Architecture & The Agent Matrix

The workstation orchestrates a multi-agent system where each agent is assigned a strict role:

*   **Planner (Architect):** Parses user requirements and creates a dependency graph of executable tasks.
*   **Backend & Frontend (Builders):** Generates code based on structural snapshots, avoiding generic boilerplate or code duplication.
*   **Terminal (DevOps):** Securely runs the code, setups dependencies, and spins up local servers (e.g., Node/Vite, Uvicorn) in a sandbox.
*   **Supervisor (QA Lead):** Assesses the execution environment, analyzes errors, and triggers self-healing cycles.
*   **Debug & Runtime Repair (Fixers):** Uses traceback logs and Anti-Loop memory to patch broken code at runtime.
*   **Band Integration Layer:** Communicates events, logs, and state updates dynamically between agents and the Band platform.

---

## 🛠️ Prerequisites

Before you begin, make sure you have the following installed:
*   **Python 3.10 or higher**
*   **pip** (Python package installer)
*   *Optional:* **Node.js & npm** (if you plan to generate and run modern frontend apps like React/Vite)

---


> [!IMPORTANT]
> # INSTALLTION IS NOT RECOMMENED ON WINDOWS AND macOS PREFER TO USE LINUX DISTRO.
> # RECOMMENED PARROT OS 7.1.


---

## ⚙️ Installation

Follow these simple commands to set up the workstation:

### 1. Clone the Repository
```bash
git clone https://github.com/Darkwarrior10110/The-Agents-Workstation.git
cd The-Agents-Workstation
```

### 2. Create and Activate a Virtual Environment
*   **Linux/macOS:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔒 Configuration Guide

The workstation requires two types of configurations: **LLM Provider API Keys** and **Band of Agents Credentials**.

### 1. LLM Gateway Configuration (`.env`)
Create a `.env` file in the root directory and add your API keys. The workstation has an automatic failover gateway, so you only need at least one key (Gemini is primary):

```env
# Primary LLM Provider (Recommended)
GEMINI_API_KEY=your_gemini_key_here
GEMINI_API_KEY_2=optional_second_gemini_key_for_failover

# Fallback LLM Providers (Optional)
GITHUB_MODELS_TOKEN=your_github_token_here
GITHUB_MODELS_ENDPOINT=https://models.inference.ai.azure.com/chat/completions
GITHUB_MODELS_MODEL=gpt-4o

XAI_API_KEY=your_xai_key_here
XAI_MODEL=grok-beta

CLAUDE_API_KEY=your_claude_key_here
CLAUDE_MODEL=claude-3-5-sonnet-latest
```

### 2. Band of Agents Credentials Configuration
To view agent communication logs in the **Band Communication Panel** on the dashboard, you must provide credential files for your three Band Agents.

We have provided templates to make this easy. Simply copy the template files and insert your Agent ID, API Key, and Handle:

1. **Planner Agent Configuration:**
   * Copy [Planner.example.txt](file:///home/dark_warrior/Projects/The-Agents-Workstations/Planner.example.txt) to a new file named `Planner.txt`
   * Open `Planner.txt` and fill in your Band details.
2. **Backend Agent Configuration:**
   * Copy [Backend.example.txt](file:///home/dark_warrior/Projects/The-Agents-Workstations/Backend.example.txt) to a new file named `Backend.txt`
   * Open `Backend.txt` and fill in your Band details.
3. **Supervisor Agent Configuration:**
   * Copy [Supervisor.example.txt](file:///home/dark_warrior/Projects/The-Agents-Workstations/Supervisor.example.txt) to a new file named `Supervisor.txt`
   * Open `Supervisor.txt` and fill in your Band details.
---

## 🏃 How to Run & Launch

With your virtual environment active and keys configured, start the workstation server:

```bash
python main.py
```
*(Alternatively, run `bash start.sh` on Unix/macOS)*

Once started, the backend server will launch on `http://127.0.0.1:8000`.

---

## 🖥️ Using the Cyberpunk Mission Control

1. Open your browser and navigate to: **`http://127.0.0.1:8000/dashboard`**
2. In the **Mission Composer** panel, type in what you want to build (e.g., *"Create a beautiful React-based Pomodoro timer application with sound alerts"*).
3. Recommended running dashboard in full screen
4. Click **LAUNCH MISSION**.
5. **Monitor the Live Pipeline:**
   * **Telemetry:** View real-time active LLM response times, token counts, and self-healing iterations.
   * **Band Communication Panel:** Watch the Planner, Backend, and Supervisor talk to each other in real-time as they hand over code, review structures, and request fixes.
   * **Sandbox Terminal Logs:** Watch terminal commands compile and run in real-time.

---

## 🛠️ Troubleshooting & FAQs

#### Q: The Band panel says "Band integration disabled." What is wrong?
*   **A:** Ensure you have installed the `band-sdk` package (`pip install -r requirements.txt`) and created the `Planner.txt`, `Backend.txt`, and `Supervisor.txt` files with valid Band Agent IDs and API keys. If credentials are missing, the workstation defaults to local agent operations safely.

#### Q: The sandbox cannot install packages or fails with command not found.
*   **A:** Make sure Node.js/npm (for frontend apps) or python/pip (for python apps) are installed globally on your machine. The workstation uses the host's terminal command runner to spin up the sandbox processes.

#### Q: Can I run this offline?
*   **A:** No, the workstation relies on external LLM provider endpoints (Gemini, Claude, Github Models) and the Band of Agents REST endpoints to orchestrate code synthesis and communications.
