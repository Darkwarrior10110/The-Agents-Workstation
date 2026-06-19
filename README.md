# THE-AGENTS-WORKSTATION 🚀

**The-Agents-Workstation** is a Production-Ready, Autonomous, Self-Healing Software Engineering Workstation. You give it a natural language prompt, and it acts as an entire engineering team—planning, writing, testing, and fixing its own code in an isolated sandbox until the application actually works.

## 🌟 Key Features

*   **Autonomous Self-Healing Loop:** Code is generated, validated via AST, executed in a headless CI sandbox, and health-checked. If it crashes, a Traceback Analyzer feeds the exact errors to a Debug Agent for surgical patching.
*   **Aetheric Cyberpunk Mission Control:** A real-time, zero-simulation React dashboard served via FastApi WebSockets. Watch the agents work, monitor active LLM providers, and view live telemetry.
*   **Universal LLM Gateway:** Multi-provider failover system. Automatically rotates and falls back across **Google Gemini** (Primary), **GitHub Models/Azure** (Secondary), **xAI**, and **Anthropic Claude**. Handles rate limits with exponential cooldowns.
*   **Project-Aware Engineering:** Frontend and Backend agents don't generate blind code. They use deterministic AST and regex scanners to build project snapshots, dependency maps, and semantic code summaries to reuse existing architecture and avoid hallucinations.
*   **Cross-Platform Terminal Engine:** Bulletproof subprocess execution across Windows, macOS, and Linux. Automatically syncs dynamic ports and runs headless setups.

## 🧠 The Agent Matrix

*   **Planner:** The Architect. Breaks prompts into a dependency graph of executable tasks.
*   **Backend & Frontend:** The Builders. Specialized code generators that read structural and semantic maps before writing code.
*   **Terminal:** The DevOps Engineer. A secure execution engine that runs code (e.g., `npm run dev`, `uvicorn`) in a sandbox.
*   **Supervisor:** The QA Lead. Reviews generated files, grades stability, predicts architectural risks, and triggers repair loops.
*   **Debug & Runtime Repair:** The Fixers. Analyze tracebacks, parse errors, and surgically patch broken files using Anti-Loop Memory to avoid repeating past mistakes.

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd The-Agents-Workstation
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   # Primary Provider (Required)
   GEMINI_API_KEY=your_gemini_key_here
   GEMINI_API_KEY_2=optional_second_gemini_key
   
   # Fallback Providers (Optional)
   GITHUB_MODELS_TOKEN=your_github_token_here
   GITHUB_MODELS_ENDPOINT=https://models.inference.ai.azure.com/chat/completions
   GITHUB_MODELS_MODEL=gpt-4o
   
   XAI_API_KEY=your_xai_key_here
   XAI_MODEL=grok-beta
   
   CLAUDE_API_KEY=your_claude_key_here
   CLAUDE_MODEL=claude-3-5-sonnet-latest
   ```

5. **Configure Band of Agents Credentials (Optional for Judges):**
   To enable live Band of Agents coordination and show the cyberpunk Band Communication panel:
   * Copy `Planner.example.txt` to `Planner.txt`
   * Copy `Backend.example.txt` to `Backend.txt`
   * Copy `Supervisor.example.txt` to `Supervisor.txt`
   
   Open each newly created file and fill in your respective Band Agent ID, API Key, and Handle details.
   
   *(Note: The real `.txt` files containing your private credentials are excluded via `.gitignore` to ensure your keys are never leaked to public repositories.)*


## 🚀 Usage

1. **Start the Workstation:**
   ```bash
   python main.py
   ```
   *(Alternatively, run `bash start.sh`)*

2. **Open Mission Control:**
   Navigate to `http://127.0.0.1:8000/dashboard` in your browser.

3. **Initiate a Mission:**
   Type your project goal into the Mission Composer in the dashboard and click **LAUNCH MISSION**. The workstation will handle the rest autonomously.
