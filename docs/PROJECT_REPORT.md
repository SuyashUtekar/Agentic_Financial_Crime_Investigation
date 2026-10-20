# Sentinel: Agentic Financial Crime Investigation System

## Project report

**Project type:** Evidence-first, human-supervised investigation copilot  
**Domain:** Anti-money laundering (AML), fraud operations, financial-crime investigation  
**Implementation status:** Local MVP using synthetic data  
**Decision boundary:** The system assists investigation; a human remains responsible for every case decision.

---

## Abstract

Financial institutions receive transaction-monitoring alerts when activity appears unusual according to configured rules or models. The alert itself is not an explanation and is not evidence of criminal conduct. Analysts must manually gather transactions, calculate flow-of-funds facts, inspect connected counterparties, consider normal business explanations, and document their reasoning. This work is time-consuming and can be inconsistent across cases.

Sentinel is an agentic financial-crime investigation system designed to organize this initial investigation stage. Given a synthetic transaction alert, a LangGraph workflow validates the alert, creates an allowlisted investigation plan, retrieves bounded account activity, calculates deterministic transaction features, conditionally invokes graph analysis, tests transparent typology indicators, validates citations to source transaction IDs, constructs an evidence pack, and presents the result for human review. An optional large language model (LLM), currently configurable through the Gemini Developer API, may propose the constrained plan and rewrite a verified summary into neutral language. It cannot calculate figures, select arbitrary tools, choose evidence, make a risk decision, or initiate any external action.

The current MVP demonstrates rapid in-and-out movement, many-to-one aggregation, and one-to-many dispersion using invented data. It provides a FastAPI backend, interactive web dashboard, LangGraph state machine, NetworkX-based relationship view, bounded tools, workflow/audit checkpointing, configurable Gemini planning and narrative adapters, an isolated synthetic evaluation endpoint, and automated tests. The project is deliberately limited to synthetic data and does not file a suspicious activity report, block a transaction, freeze an account, or determine that any person has committed a crime.

**Keywords:** AML, financial crime, transaction monitoring, agentic AI, evidence provenance, human-in-the-loop, Gemini API, FastAPI, NetworkX.

---

## 1. Introduction

Financial crime controls often use rules or predictive models to detect activity requiring attention. For example, a rule may identify a large outgoing transfer soon after several incoming credits. This produces an alert, but it does not answer key questions: What happened? Which records support the alert? Is the activity consistent with a known pattern? What information is missing? Could an ordinary business explanation exist?

Sentinel addresses the investigation support problem after an alert already exists. Its aim is not to replace an investigator. Its aim is to prepare an auditable, evidence-linked first draft so an investigator can spend more time on judgement and less time locating records and recomputing basic facts.

---

## 2. Problem statement

### 2.1 Business problem

Analysts reviewing transaction-monitoring alerts frequently need to collect information from different systems, reconstruct the timing of fund movements, identify counterparties, understand network relationships, and write a case narrative. Manual processes can create several difficulties:

- Investigation time is spent on repetitive data gathering and calculations.
- Different analysts may document comparable cases inconsistently.
- A narrative may omit counter-evidence, data gaps, or the specific records supporting a statement.
- An LLM used without controls may fabricate facts, calculate incorrectly, or express an unsupported conclusion.
- A high alert volume may make it difficult to prioritize the cases with the clearest supporting evidence.

### 2.2 Technical problem

The challenge is to add useful automation while preserving traceability and human accountability. A credible system must calculate factual values in code, restrict any model to approved tasks, retain workflow state, cite source records, handle missing data safely, and make uncertainty visible.

### 2.3 Research question

Can a stateful, evidence-first investigation workflow improve the completeness and consistency of a synthetic AML case pack compared with a simple alert view or an unbounded single-LLM summary, while keeping a human decision-maker in control?

---

## 3. Aim and objectives

### 3.1 Aim

To build a local, human-supervised system that converts a synthetic financial-crime alert into a reviewable investigation pack containing deterministic evidence, candidate typologies, limitations, and an audit trail.

### 3.2 Objectives

1. Build an alert inbox and interactive case-review dashboard.
2. Store and process synthetic alerts, account metadata, and transaction records.
3. Compute transaction facts using deterministic code rather than LLM arithmetic.
4. Detect three transparent patterns: rapid in/out, many-to-one, and one-to-many.
5. Associate each material finding with transaction IDs that can be checked automatically.
6. Create a bounded transaction graph for account relationships.
7. Add a constrained Gemini planning layer and optional provider-independent narrative drafting.
8. Preserve case state and audit events across application restarts.
9. Require a human to close, continue, or escalate every reviewed case.
10. Provide an extensible foundation for PostgreSQL persistence, dataset ingestion, and broader evaluation.

### 3.3 Non-objectives

The MVP does not use real customer data, connect to a bank system, submit SAR/STR reports, block payments, freeze accounts, perform sanctions screening, or make legal/criminal decisions. It does not claim to detect all forms of money laundering.

---

## 4. Scope

### Included in the current MVP

- Synthetic alert queue with severity and priority fields.
- Account-centric transaction retrieval from an invented demo dataset.
- Deterministic calculation of counts, amounts, counterparties, and inbound/outbound ratio.
- Pattern detection and evidence-linked candidate findings.
- NetworkX directed graph construction for related transaction edges.
- Evidence-reference validation.
- Case lifecycle, human review, and audit events.
- LangGraph specialist nodes, conditional routes, bounded retries, and safe escalation.
- Local workflow trace, tool-run, retry, and audit checkpoint persistence in a JSON file.
- Responsive dashboard served by FastAPI.
- Gemini, Ollama, OpenAI-compatible, or disabled narrative adapter options.

### Deferred to later phases

- PostgreSQL persistence and migrations.
- Real external dataset ingestion (for example, AMLSim) with license review.
- Authentication, role-based access control, and multi-user coordination.
- PostgreSQL-backed LangGraph checkpointer.
- Separate React/TypeScript frontend application.
- Streaming case updates, richer graph visualization, and export controls.
- Formal held-out evaluation datasets and measured baseline comparison.
- Production governance, data-retention, privacy, and institutional policy integration.

---

## 5. Methodology

### 5.1 Design approach

The project uses a modular-monolith approach. A single Python application contains separate responsibilities for API routes, LangGraph orchestration, constrained tool calls, analytics, optional Gemini planning/narrative generation, and state persistence. This minimizes operational complexity while preserving clear boundaries for future replacement.

The central design principle is **evidence first**:

1. Retrieve available records in a limited case scope.
2. Calculate facts deterministically.
3. Apply transparent, configured pattern criteria.
4. Attach source references to each candidate finding.
5. Validate those references before the report is displayed.
6. Use a language model only to express already-verified information in readable language.
7. Route the result to a human reviewer.

### 5.2 Workflow methodology

```text
Alert selected
  → Create case and checkpoint
  → Triage and create an allowlisted investigation plan
  → Collect account-related transaction records
  → Compute features
  → Conditionally build a bounded transaction network
  → Detect supported patterns; route to graph analysis if a candidate requires it
  → Validate evidence references
  → Draft evidence pack
  → Await human review
  → Close / request more evidence / escalate
```

If the system cannot find transaction history for the alerted account, it does not produce a speculative report. Instead, it changes the case status to `escalated` and records the reason.

### 5.3 Pattern-detection methodology

The rules are intentionally simple, explainable, and suitable for unit testing.

| Indicator | Current rule | Why it may matter | Important limitation |
| --- | --- | --- | --- |
| Rapid in/out | Outbound transfers within six hours of incoming value, with ratio ≥ 70% of relevant preceding inbound funds | May show quick movement of recently received funds | Legitimate settlement or treasury activity can produce the same pattern |
| Many-to-one | Three or more distinct senders credit one account | May indicate aggregation of funds | Marketplace, payroll, donation, or merchant activity can also aggregate payments |
| One-to-many | One account pays three or more distinct receivers | May indicate dispersion of funds | Supplier, payroll, or customer-refund payments may be legitimate |

The thresholds are demonstration parameters, not regulatory thresholds. They must be calibrated, approved, and tested before use on any governed data.

### 5.4 Evidence-verification methodology

Every candidate finding includes a list of `EvidenceRef` objects. The current validator checks that each cited transaction ID exists in the loaded transaction set. This prevents a report from representing a nonexistent record as support.

Future versions should additionally verify claimed amounts, timestamps, graph paths, query scope, source dataset version, and relationships between a textual statement and its cited record.

### 5.5 LLM methodology

The LLM is optional. When Gemini is enabled, it first receives only alert metadata and can propose a JSON plan composed exclusively of approved actions. The application validates the response and rejects unsupported actions. After evidence validation, the LLM may receive a deterministic executive summary with the instruction not to add facts, figures, conclusions, or recommendations. The Gemini native REST adapter calls `generateContent` server-side using `GEMINI_API_KEY` from `.env.secrets`.

If the provider is disabled, unavailable, returns malformed content, or lacks a key, the deterministic summary is returned instead. This is a safe-degradation behavior: a provider failure does not prevent evidence calculation or cause the system to invent an answer.

---

## 6. System architecture

### 6.1 Technology stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Backend | Python, FastAPI, Pydantic | Typed API and application service |
| Analytics | Decimal, NetworkX | Precise monetary arithmetic and relationship graph |
| Frontend | HTML, CSS, JavaScript | Responsive analyst dashboard |
| Orchestration | LangGraph StateGraph | Typed specialist nodes, conditional routes, checkpoints |
| LLM | Gemini Developer API, optional | Validated allowlisted planning and controlled narrative refinement |
| Packaging | uv | Dependency locking, environment, and command execution |
| Persistence | Local JSON checkpoint | Local synthetic-MVP case/audit recovery |
| Tests | pytest | Verification of core pattern and reference logic |

### 6.2 Component responsibilities

| Component | Responsibility |
| --- | --- |
| `app/main.py` | Serves dashboard and versioned API endpoints |
| `app/data.py` | Provides the current synthetic alerts, accounts, and transactions |
| `app/analytics.py` | Computes features, patterns, graphs, and evidence checks |
| `app/service.py` | Coordinates case state, report construction, human review, audit events |
| `app/workflow.py` | Defines LangGraph specialist nodes, conditional routes, bounded retry, and escalation |
| `app/tools.py` | Defines the only permitted bounded data/analysis tools |
| `app/llm.py` | Isolates Gemini structured planning and provider-specific narrative calls |
| `app/state_store.py` | Persists and restores synthetic local case/audit checkpoints |
| `app/static/` | Dashboard UI and browser-side API interactions |

### 6.3 Security boundary

The browser communicates only with the local backend API. Gemini credentials remain in `.env.secrets`, which is ignored by Git. The browser is never given the key. The present implementation is a local demo and intentionally lacks production authentication; it must not be exposed publicly or connected to real financial data without a full security design.

---

## 7. Data model

### 7.1 Transaction data

Each transaction has a unique ID, timestamp, sending account, receiving account, amount, currency, type, channel, status, and optional memo. Source IDs make each displayed fact traceable.

### 7.2 Alert data

An alert identifies an account and contains a trigger time, rule code, trigger reason, severity, status, and priority score.

### 7.3 Case and finding data

A case links an alert to an investigation status, candidate findings, generated report, and reviewer decision. A finding records its typology, feature values, evidence references, counter-evidence, and verification status.

### 7.4 Audit data

The audit record captures system actions such as case creation, evidence collection, typology analysis, validation, report drafting, and human review. The local store is append-oriented within the process and persists it alongside the synthetic case state.

---

## 8. Example case analysis

For alert `ALT-2026-001`, account `ACC-102` receives three credits of $4,200, $3,800, and $4,100. It subsequently sends $10,800 to another account. The detector identifies:

1. **Many-to-one aggregation:** three distinct senders paid into the account.
2. **Rapid in/out:** a high proportion of the relevant preceding incoming value moved outward within the six-hour rule window.

The report cites the corresponding transaction records. It also shows counter-evidence: the synthetic environment does not provide validated invoices, merchant-settlement context, payroll information, or counterparty relationships. Therefore, the system uses neutral language such as “consistent with a configured indicator,” and asks a human reviewer to decide the next step.

---

## 9. Testing and validation

The automated test suite currently verifies:

- Rapid-flow pattern detection has evidence references and meets the configured ratio threshold.
- Many-to-one and one-to-many patterns are identified for relevant synthetic cases.
- All cited transaction references resolve to actual source records.
- Missing transaction history is explicit rather than silently interpreted as normal activity.
- A high-connectivity case conditionally routes through the network-analysis node.
- An unknown alert safely escalates without producing a narrative.
- The isolated synthetic evaluation reports evidence-reference validity without exposing labels to the workflow.

Run the suite with:

```bash
uv run pytest
```

At the current project state, the test suite contains seven passing tests. This indicates only that the implemented functions and routes behave as expected on curated synthetic examples. It does not establish real-world detection accuracy, regulatory compliance, or effectiveness on live data.

---

## 10. Evaluation framework for the next phase

Before making performance claims, the system should be evaluated on an approved synthetic or public dataset with ground truth hidden from the investigation workflow. Suggested comparisons include:

1. Rules-only template report.
2. Fixed retrieval-and-analysis pipeline.
3. Single-LLM narrative over a fixed evidence bundle.
4. Stateful agentic workflow with conditional routing and validation.

Suggested metrics:

- Valid evidence-reference rate.
- Typology precision and recall by pattern.
- Unsupported material-claim rate in narratives.
- Completeness of required report sections.
- Correct escalation for missing/inconsistent evidence.
- Median analyst review time and correction effort.
- End-to-end latency and LLM cost per case.

The MVP exposes `POST /api/v1/evaluations/run`, which compares the current rules-only detector and the agentic workflow on four hand-authored synthetic alerts. Its current results are 0.8 typology precision, 1.0 typology recall, and 1.0 evidence-reference validity. These figures are reproducible demo results only, not a held-out benchmark or a production performance claim. The agentic workflow intentionally shares the deterministic detection rules with the baseline; its intended added value is conditional routing, traceability, safe escalation, and reviewability.

---

## 11. Ethical, security, and governance considerations

Financial-crime systems can affect people and businesses significantly. A transaction pattern should never be treated as proof of intent. The project therefore follows these controls:

- Human review is mandatory for case outcome.
- Findings are called candidates or indicators, not confirmed offences.
- Counter-evidence and missing information are visible in the report.
- The LLM is prevented by architecture from being the source of numeric facts.
- Secrets remain outside source control in `.env.secrets`.
- The demo uses only synthetic data.
- The current system cannot initiate any payment, account, customer, or regulatory action.

Future work must add data minimization, access control, encryption, retention controls, prompt-injection testing for all untrusted text, and independent compliance/model-risk review before any institutional use.

---

## 12. Limitations

The current MVP has intentional limitations:

- It uses a small hand-authored synthetic dataset rather than AMLSim or a large validated dataset.
- Case state is local JSON, not PostgreSQL.
- Graphs use direct account-related edges and are not yet a full multi-hop investigation engine.
- The frontend is static JavaScript rather than the planned separate React application.
- Authentication and role-based access control are not implemented.
- The narrative adapter has no production rate-limit, observability, or model-evaluation layer.
- The calculations are for USD demo records and do not implement a currency-conversion policy.
- Pattern thresholds are illustrative and not calibrated for any real organization.

These limitations should be presented openly in a demo or assessment.

---

## 13. Future enhancement roadmap

### Phase 1 — Data and persistence

Replace demo records with a validated canonical schema, add CSV/Parquet ingestion, preserve source lineage, and move case/audit data to PostgreSQL.

### Phase 2 — Durable orchestration

Replace the local in-memory LangGraph checkpointer and JSON checkpoint with a PostgreSQL-backed durable checkpointer; add node-level timeouts, production observability, and more evidence-retrieval tools.

### Phase 3 — Analyst experience

Create a dedicated React/TypeScript frontend, interactive Cytoscape network explorer, advanced filtering, reviewer assignments, exports, and accessibility testing.

### Phase 4 — Evaluation and governance

Run a held-out synthetic evaluation, build a reviewer rubric, measure evidence and narrative quality, document model versions, add security tests, and obtain required governance review.

---

## 14. Conclusion

Sentinel demonstrates a practical approach to agentic AI for financial-crime investigation: do not let a language model decide the facts. Instead, use a LangGraph workflow with conditional routes and constrained tools to calculate and verify evidence, use constrained language generation only for communication, preserve workflow/audit state, and require a human to make the decision.

The current MVP is a credible technical foundation for an evidence-first investigation copilot. Its value lies not in asserting that it can identify criminal conduct, but in showing how transaction evidence can be assembled, checked, explained, and handed to a qualified human reviewer responsibly.
