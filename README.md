# Sentinel — Agentic Financial Crime Investigation System

An evidence-first, human-supervised AML investigation copilot for **synthetic data only**. It never files reports, blocks payments, or makes a criminal determination.

## Quick start

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. The app seeds a synthetic data set automatically.

## Documentation

Start with the [plain-language case walkthrough](docs/CASE_WALKTHROUGH.md), then use the [formal project report](docs/PROJECT_REPORT.md), [agentic workflow guide](docs/AGENTIC_WORKFLOW.md), [architecture guide](docs/ARCHITECTURE.md), and [operations guide](docs/OPERATIONS.md) as needed.

`uv` creates and manages `.venv` and installs the locked dependency set. Do not use `pip` or manually activate the virtual environment for normal project commands.

### Everyday commands

```bash
# Start the dashboard
uv run uvicorn app.main:app --reload

# Run automated checks
uv run pytest

# Add a production dependency
uv add package-name

# Add a development-only dependency
uv add --dev package-name

# Upgrade dependencies deliberately, then commit uv.lock
uv lock --upgrade
uv sync --extra dev
```

## LLM configuration

The system is useful with `LLM_PROVIDER=disabled`: all numbers, pattern detection, graph analysis, evidence validation, and fallback investigation planning stay deterministic. When Gemini is enabled, it may propose an allowlisted investigation plan and polish a verified narrative; it cannot calculate facts, call arbitrary tools, or decide a case.

| Mode | Configuration | Cost |
| --- | --- | --- |
| No LLM | `LLM_PROVIDER=disabled` | Free |
| Gemini Developer API | `LLM_PROVIDER=gemini`, `LLM_MODEL=gemini-2.5-flash`, `GEMINI_API_KEY=...` | Free-tier quotas subject to Google’s current limits |
| Local/free | `LLM_PROVIDER=ollama`, `LLM_MODEL=qwen3:4b` | Free; run Ollama locally |
| Paid or hosted | `LLM_PROVIDER=openai_compatible`, base URL/key/model | Provider-dependent |

Set non-sensitive values in `.env` (copy `.env.example`) and keep credentials in `.env.secrets` (copy `.env.secrets.example`). Provider-specific API calls are isolated behind one adapter, so changing a provider does not affect the investigation workflow.

### Gemini Developer API setup

1. Create an API key in Google AI Studio / Gemini Developer API and keep it private.
2. Copy `.env.example` to `.env` and set:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
```

3. Copy `.env.secrets.example` to `.env.secrets`, then set:

```env
GEMINI_API_KEY=your_key_here
```

4. Restart the server. The key stays on the API server and is never exposed to the browser.

Gemini model availability and free-tier quotas can change, so select a currently available text model in AI Studio if `gemini-2.5-flash` is unavailable. The native Gemini adapter uses Google's `generateContent` endpoint and API-key header as documented in the [Gemini API reference](https://ai.google.dev/api).

## What is included

- Alert inbox, priority scoring, filters, and case creation
- Deterministic rapid in/out, many-to-one, and one-to-many pattern detection
- Evidence-linked timeline, bounded NetworkX graph, and validation
- Stateful investigation progression with safe escalation for missing evidence
- Draft report, human disposition, and append-only in-process audit trail
- LangGraph agentic workflow, conditional routing, bounded retries, and safe escalation
- Tests for deterministic analytics, agentic routes, escalation, and synthetic evaluation

The demo data is invented and must not be interpreted as a real-world risk decision.

