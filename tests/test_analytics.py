from app.analytics import detect_patterns, features, validate_references
from app.data import TRANSACTIONS


def test_rapid_flow_is_evidence_backed():
    findings = detect_patterns("ACC-102", TRANSACTIONS)
    rapid = next(f for f in findings if f.typology_id == "RAPID_IN_OUT")
    assert rapid.features["outbound_within_window_ratio"] >= 0.70
    assert rapid.verification_status == "verified"
    assert all(ref.id.startswith("TX-") for ref in rapid.evidence_refs)


def test_aggregation_and_dispersion_are_detected():
    assert any(f.typology_id == "MANY_TO_ONE" for f in detect_patterns("ACC-103", TRANSACTIONS))
    assert any(f.typology_id == "ONE_TO_MANY" for f in detect_patterns("ACC-104", TRANSACTIONS))


def test_evidence_references_resolve():
    findings = detect_patterns("ACC-102", TRANSACTIONS)
    report = validate_references(findings, TRANSACTIONS)
    assert report["valid"] is True
    assert report["broken_references"] == []


def test_empty_history_is_explicit():
    result = features("ACC-NOT-FOUND", TRANSACTIONS)
    assert result["data_complete"] is False
    assert result["transaction_count"] == 0
