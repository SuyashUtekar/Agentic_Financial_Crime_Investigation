# Understanding an investigation case

This is the easiest place to start. It explains the system as if you are the investigator reviewing an alert.

## What problem does Sentinel solve?

Banks and fintech companies often have rules that flag unusual transfers. A flag alone is not proof of wrongdoing. An investigator must inspect the related transactions, understand the flow of money, consider ordinary explanations, and decide what should happen next.

Sentinel reduces the evidence-gathering work. It takes a synthetic alert, finds the account's connected transactions, calculates facts, checks configured patterns, and creates an evidence pack for a human to review.

## The example case in the dashboard

Open alert `ALT-2026-001`. It concerns account `ACC-102` and uses the rule code `RAPID_FLOW`.

The important transactions are:

| Time relative to review | Transaction | Money flow | Amount |
| --- | --- | --- | ---: |
| 6h 30m earlier | TX-1001 | ACC-201 → ACC-102 | $4,200 |
| 6h earlier | TX-1002 | ACC-202 → ACC-102 | $3,800 |
| 5h 30m earlier | TX-1003 | ACC-203 → ACC-102 | $4,100 |
| 4h 45m earlier | TX-1004 | ACC-102 → ACC-301 | $10,800 |

In simple terms, account `ACC-102` received $12,100 from three separate accounts. Forty-five minutes after the last of those incoming transfers, it sent $10,800 onward. That is why the case is worth reviewing.

## What the system can say — and cannot say

The system can say:

- The records show multiple incoming payments followed by a high-value outgoing transfer in a short timeframe.
- This is **consistent with** the configured rapid in/out and many-to-one indicators.
- The findings cite the transaction IDs used to support them.

The system cannot say:

- That anyone laundered money.
- That the account owner intended to commit a crime.
- That the activity is definitely suspicious after reviewing transaction data alone.

For example, the transactions could be a legitimate business settlement. The demo has no invoices, verified merchant details, payroll evidence, or complete KYC context, so this benign explanation remains possible.

## What each dashboard section means

### Alert priority queue

This is the starting point. Each alert has a rule, severity, and a deterministic priority score. The score helps order work; it is not a legal or criminal-risk decision.

### Observed facts

These are calculated directly from transaction records. Examples include the total value received, total value sent, transaction count, and number of unique counterparties. The LLM does not do these calculations.

### Candidate typologies

A typology is a recognized pattern investigators may wish to examine. In this MVP:

- **Rapid in/out:** a significant incoming amount is followed by outgoing transfers within six hours. It needs a ratio of at least 70%.
- **Many-to-one:** at least three different senders pay into one account in the review window.
- **One-to-many:** one account pays at least three different receivers in the review window.

These are configurable indicators, not proof.

### Evidence validation

Every finding contains transaction references. Before a report is shown, the system checks that each referenced transaction ID exists in the loaded records. A broken reference prevents a finding from being treated as verified.

### Human decision

The analyst chooses one of three outcomes:

| Decision | Meaning |
| --- | --- |
| Close case | No further work is required in this demonstration. |
| Request more | More authorized evidence is needed; the case returns to evidence collection. |
| Escalate | A qualified reviewer should conduct additional review. |

Every action is added to the audit trail.

## The investigation sequence

```text
Alert selected
  → create an approved investigation plan
  → collect bounded transaction records
  → calculate deterministic facts
  → conditionally analyze the network when evidence requires it
  → test configured patterns
  → validate evidence references
  → draft neutral evidence pack
  → human decision
```

If there is no history for an alerted account, the system escalates rather than inventing a conclusion.

## Where Gemini fits

Gemini has two tightly restricted roles. It may propose a plan made only from pre-approved actions (`transaction_analysis`, `network_analysis`, `context_lookup`, and `typology_analysis`) and may rewrite the already-verified executive summary into clear, neutral language. It receives no tool access and does not calculate amounts, choose evidence, assign a numeric score, or make the human decision. If Gemini is unavailable or returns invalid output, the deterministic planner and summary remain available.
