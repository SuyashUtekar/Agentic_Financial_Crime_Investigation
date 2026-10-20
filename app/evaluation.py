"""Offline-only evaluation for the synthetic demonstration set.

Ground-truth expectations live here rather than in workflow tools, preventing
the investigation graph from using labels to decide findings.
"""
from .analytics import detect_patterns, validate_references
from .data import ALERTS, TRANSACTIONS

EVALUATION_LABELS = {
    "ALT-2026-001": {"RAPID_IN_OUT", "MANY_TO_ONE"},
    "ALT-2026-002": {"MANY_TO_ONE"},
    "ALT-2026-003": {"ONE_TO_MANY"},
    "ALT-2026-004": set(),
}


def run_synthetic_evaluation() -> dict:
    true_positive = false_positive = false_negative = 0
    valid_references = checked_references = 0
    per_alert = []
    for alert in ALERTS:
        expected = EVALUATION_LABELS[alert.alert_id]
        findings = detect_patterns(alert.account_id, TRANSACTIONS)
        predicted = {item.typology_id for item in findings if item.status == "candidate"}
        true_positive += len(predicted & expected)
        false_positive += len(predicted - expected)
        false_negative += len(expected - predicted)
        validation = validate_references(findings, TRANSACTIONS)
        valid_references += validation["references_checked"] - len(validation["broken_references"])
        checked_references += validation["references_checked"]
        per_alert.append({"alert_id": alert.alert_id, "expected": sorted(expected), "predicted": sorted(predicted), "references_valid": validation["valid"]})
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    metrics = {"typology_precision": round(precision, 3), "typology_recall": round(recall, 3), "evidence_reference_validity": round(valid_references / checked_references, 3) if checked_references else 1.0}
    return {"scope": "hand-authored synthetic demo; not a production performance claim", "rules_only_baseline": metrics, "agentic_workflow": {**metrics, "note": "The agentic layer changes routing, tracing, escalation, and reviewability; it intentionally shares the deterministic detection rules with the baseline."}, "per_alert": per_alert}
