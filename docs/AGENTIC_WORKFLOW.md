# Agentic workflow

## What makes the current workflow agentic

Sentinel now uses a LangGraph `StateGraph`, not a fixed controller sequence. Specialist nodes share typed investigation state, select the next bounded action from evidence, and record their work in a local persisted case checkpoint.

```text
Triage
  → Planner (Gemini structured plan or deterministic fallback)
  → Evidence collection
  → Transaction analyst
  ├─ high connectivity / plan requires graph → Network analyst
  └─ otherwise → Typology analyst
  → Evidence verifier
  ├─ valid evidence → Narrative agent → Human review
  └─ invalid or unavailable evidence → Escalation
```

The typology analyst can independently route back to network analysis if a candidate flow pattern requires a graph and the graph has not yet been created. That makes routes case-dependent rather than a fixed workflow for every alert.

## Specialist responsibilities

| Node | Authority and output |
| --- | --- |
| Triage | Validates the alert and determines whether the case can proceed. |
| Planner | Produces a validated allowlisted action plan. Gemini may suggest actions, but cannot add a tool. |
| Evidence collector | Calls bounded transaction and account-context tools. Retries a retriable failure once, then escalates. |
| Transaction analyst | Computes deterministic counts, totals, and counterparty features. |
| Network analyst | Builds a capped NetworkX graph with at most 50 nodes and 100 edges. |
| Typology analyst | Tests the transparent rapid-flow, aggregation, and dispersion indicators. |
| Evidence verifier | Checks that cited transaction IDs exist before a narrative may be drafted. |
| Narrative agent | Uses Gemini only to polish verified facts into neutral language. |
| Human reviewer | Closes, requests more evidence, or escalates. This is the decision boundary. |

## Constrained tool layer

The LLM never receives raw database, shell, browser, or arbitrary HTTP access. The workflow may call only functions in `app/tools.py`, which validate result limits and scope. Current tool limits include 200 transaction rows, a 90-day window, 50 graph nodes, and 100 graph edges.

## Gemini planner safety

Gemini can return only this JSON-compatible allowlist:

```text
transaction_analysis
network_analysis
context_lookup
typology_analysis
```

Any malformed, unavailable, or unsupported Gemini response is discarded. The workflow uses a deterministic plan selected from alert severity and rule code instead. Gemini cannot make an escalation decision, change a tool argument, access hidden labels, or determine that wrongdoing occurred.

## Persistence and resume

LangGraph uses a thread ID equal to the case ID while the application runs. The case's workflow trace, tool runs, and retry counts are also saved in `data/runtime/workflow_state.json`. This allows a case to be run again after a restart with its prior visible workflow history retained.

For production, replace the local file with a PostgreSQL-backed application store and LangGraph checkpointer. The MVP's local checkpoint is suitable only for a single-user synthetic demonstration.

## How to observe it

Run an alert from the dashboard. The evidence pack now shows:

- the approved investigation plan;
- each agentic workflow node and outcome;
- bounded tool calls;
- evidence validation result;
- model metadata showing whether Gemini or the deterministic fallback created the plan and narrative.

The workflow tests in `tests/test_workflow.py` verify both a dynamic network-analysis route and safe escalation of an unknown alert.

## Evaluation boundary

`POST /api/v1/evaluations/run` runs a small rules-only versus agentic-workflow comparison against four hand-authored synthetic alerts. The labels are imported only by `app/evaluation.py`, never by a workflow node or tool. The current agentic workflow deliberately shares the detector with the baseline; its measured benefit is therefore not higher detection accuracy, but evidence traceability, conditional routing, escalation, and reviewability. Do not treat the small synthetic results as production metrics.
