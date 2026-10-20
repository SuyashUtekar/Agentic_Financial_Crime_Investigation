# Operations guide

## Requirements

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/)
- A Gemini Developer API key only if you want Gemini-assisted planning and LLM-polished summaries

## First-time setup

```bash
cd "/Users/suyashutekar/Projects/Agentic Financial Crime Investigation System"
cp .env.example .env
cp .env.secrets.example .env.secrets
```

Edit `.env.secrets` and add only your key:

```env
GEMINI_API_KEY=your_key_here
```

The ordinary `.env` already selects Gemini and `gemini-2.5-flash`. `GEMINI_BASE_URL` is optional because the app has a secure default.

Install the locked environment and start the app:

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. Stop the local server with `Ctrl+C`.

## Everyday commands

```bash
uv run pytest                    # run tests
uv run uvicorn app.main:app --reload  # run the dashboard
uv add package-name              # add a runtime package
uv add --dev package-name        # add a development package
uv lock --upgrade                # intentionally upgrade locked packages
```

Commit `pyproject.toml` and `uv.lock` together whenever dependencies change. Do not commit `.env`, `.env.secrets`, generated checkpoints, data files, or model keys.

## API quick reference

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Service status and demo safety mode |
| GET | `/api/v1/alerts` | List the synthetic alert queue |
| GET | `/api/v1/alerts/{alert_id}` | Alert, account context, and related transactions |
| POST | `/api/v1/cases` | Create a case with `{ "alert_id": "ALT-2026-001" }` |
| POST | `/api/v1/cases/{case_id}/run` | Run or resume the investigation |
| GET | `/api/v1/cases/{case_id}` | Get current case state |
| GET | `/api/v1/cases/{case_id}/report` | Get the evidence pack after it is drafted |
| POST | `/api/v1/cases/{case_id}/review` | Record human disposition and reason |
| GET | `/api/v1/audit-events?case_id=...` | Read the relevant audit trail |
| POST | `/api/v1/evaluations/run` | Run the isolated synthetic-demo evaluation |

Review requests must include a decision (`close`, `continue_investigation`, or `escalate`) and a reason.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `uv` is not found | Install uv, reopen Terminal, then run `uv --version`. |
| Dashboard is unavailable | Ensure the server terminal is still running and use `http://127.0.0.1:8000`. |
| Report says Gemini was not used | Confirm `.env.secrets` has `GEMINI_API_KEY`, restart the server, and verify the selected Gemini model is available to your key. The agentic workflow still works with a deterministic fallback plan and summary. |
| A key appeared in Git or a screenshot | Revoke it in Google AI Studio immediately, create a replacement, and update `.env.secrets`. |
| Old cases appear after restart | Delete only `data/runtime/workflow_state.json`; it contains local synthetic demo checkpoints. |
