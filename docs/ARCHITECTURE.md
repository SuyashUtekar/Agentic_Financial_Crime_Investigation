# Architecture

## Current MVP architecture

```text
Browser dashboard
  │  static HTML, CSS, JavaScript
  ▼
FastAPI application
  ├── alert and case routes
  ├── LangGraph investigation service / conditional state transitions
  ├── deterministic analytics (Decimal + NetworkX)
  ├── evidence-reference validation
  ├── optional Gemini / Ollama / OpenAI-compatible narrative adapter
  └── local JSON checkpoint and audit store
```

The frontend lives in `app/static/` and is served by the same FastAPI process. It calls the versioned `/api/v1/*` endpoints; no API key is present in browser code.

## Investigation lifecycle

| State | What occurs |
| --- | --- |
| `created` | An analyst creates a case from an alert. |
| `planning` | Gemini or the deterministic fallback creates an allowlisted investigation plan. |
| `collecting_evidence` | The workflow retrieves bounded transaction and account-context records. |
| `routing_analysis` | LangGraph chooses graph analysis or typology analysis from plan and evidence. |
| `testing_typologies` | Deterministic pattern checks create candidate findings. |
| `verifying_evidence` | Transaction IDs referenced by findings are checked against source records. |
| `awaiting_human_review` | The report, agent trace, and tool-run list are ready for an analyst. |
| `completed`, `collecting_evidence`, or `escalated` | A human decision closes, requests more work, or escalates the case. |

## Data and computation boundaries

`app/data.py` holds the invented transaction, account, and alert records for the demo. In a later ingestion implementation, this module should be replaced with validated reads from a database or canonical dataset store.

`app/workflow.py` defines the LangGraph specialist nodes, conditional routes, bounded retry/escalation path, and per-case graph thread. `app/analytics.py` is deliberately deterministic:

- Amounts are represented by `Decimal` during calculation.
- Pattern thresholds are code-defined and testable.
- Network data is built with NetworkX from in-scope transaction edges.
- Evidence validation ensures cited transaction IDs exist.

## LLM provider boundary

`app/llm.py` implements `plan_investigation` and `polish_summary`. Gemini is currently used for the structured planner because the plan is constrained to an allowlist and validated before graph routing. The narrative adapter supports `gemini`, `ollama`, `openai_compatible`, and `disabled`.

The planner's output is an input only to allowlisted graph routing; it cannot choose arbitrary tools or arguments. Narrative generation is called only after deterministic analytics and evidence validation. Neither output affects features, typologies, evidence selection, or human disposition. On timeout, API failure, missing key, or invalid structured output, the application uses deterministic fallback behavior.

## Persistence

`app/state_store.py` saves synthetic case state and audit events to `data/runtime/workflow_state.json`. Writes use a temporary file followed by replacement to avoid a partially written checkpoint.

This is appropriate only for a local, single-process demonstration. Before a multi-user or production deployment, use PostgreSQL with transactional case/audit tables and a durable workflow checkpointer.

## Security and deployment limits

- `.env.secrets` is loaded only in the backend process and is ignored by Git.
- The current UI is not authenticated because it is a local synthetic demo.
- The project must not be connected to live banking data, credentials, or decisioning actions in its current form.
- No automated SAR/STR filing, account freeze, or payment block exists.
