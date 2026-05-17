# 🤖 Autonomous Code Intelligence & Testing Pipeline

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![PydanticAI](https://img.shields.io/badge/Agent_Framework-PydanticAI-ec4a3f.svg)](https://ai.pydantic.dev/)
[![Testing](https://img.shields.io/badge/Testing-pytest-yellow.svg)](https://docs.pytest.org/en/stable/)
[![GitHub API](https://img.shields.io/badge/Integration-PyGithub-black.svg)](https://pygithub.readthedocs.io/)

An autonomous, multi-agent pipeline designed to perform continuous codebase profiling, test suite generation, and self-healing validation before orchestrating Human-in-the-Loop (HITL) Pull Requests via the GitHub API.

## 🧠 System Architecture

This system moves beyond simple LLM wrappers by utilizing a highly decoupled, stateful multi-agent graph architecture:

1. **The AST Profiler (Agent 1):** Bypasses massive LLM context windows by utilizing Python's built-in `ast` module to dynamically parse local directories, identify missing test coverage, and extract isolated source-code context packets.
2. **The Reasoner (Agent 2):** Powered by `PydanticAI` and open-source models, this agent enforces type-safe, structured outputs to generate edge-case-aware `pytest` suites.
3. **The Self-Healing Sandbox (Agent 3):** An isolated execution loop that automatically runs generated tests against the local environment. If syntax or logic errors occur, it captures CLI `stderr`/`stdout` traces and feeds them back to the Reasoner for autonomous self-correction (up to 3 retries).
4. **The Git Orchestrator (Agent 4):** A Human-in-the-Loop (HITL) engine that pauses for explicit manual approval before branching off `main`, committing the validated test files, and opening formatted Pull Requests via the GitHub API.

## 🚀 Key Engineering Features

* **Deterministic Control Loops:** Implements strict validation cycles around stochastic LLM outputs to guarantee perfectly compiling Python code.
* **Smart Context Injection:** Eliminates "lost-in-the-middle" syndrome by feeding the LLM exact function blocks rather than entire script files.
* **Automated Exception Handling:** Prompts dynamically adjust to ensure AI-generated tests catch explicit custom exceptions (e.g., `ValueError`) rather than hallucinating generic Python errors.
* **Anti-Spam PR Engine:** HITL checkpoints ensure open-source maintainers receive zero automated garbage.

## 🛠️ Quick Start & Setup

This project uses `uv` for lightning-fast dependency management.

```bash
# 1. Clone the repository
git clone [https://github.com/Vinay1223/Automated_Testing_and_Code_Intelligence.git](https://github.com/Vinay1223/Automated_Testing_and_Code_Intelligence.git)
cd Automated_Testing_and_Code_Intelligence

# 2. Install dependencies via uv
uv sync

# 3. Configure Environment Variables
# Create a .env file in the root directory:
GROQ_API_KEY=your_groq_api_key
GITHUB_ACCESS_TOKEN=your_classic_github_token_with_repo_scope

# 4. Run the Pipeline
uv run python revision_4_pr_engine.py
