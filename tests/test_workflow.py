import pytest
from app.workflow import execute_agentic_investigation
from app.evaluation import run_synthetic_evaluation


@pytest.mark.asyncio
async def test_agentic_workflow_routes_to_network_for_aggregation_alert():
    state = await execute_agentic_investigation("TEST-AGENTIC-001", "ALT-2026-001")
    nodes = [entry["node"] for entry in state["trace"]]
    assert state["status"] == "awaiting_human_review"
    assert "planner" in nodes
    assert "network_analyst" in nodes
    assert "evidence_verifier" in nodes
    assert state["validation"]["valid"] is True
    assert state["plan"]["actions"]


@pytest.mark.asyncio
async def test_unknown_alert_escalates_without_a_narrative():
    state = await execute_agentic_investigation("TEST-AGENTIC-002", "ALT-DOES-NOT-EXIST")
    assert state["status"] == "escalated"
    assert state["report"]["model"]["used"] is False
    assert state["report"]["data_gaps"] == ["alert_not_found"]


def test_evaluation_is_isolated_and_reports_reference_validity():
    evaluation = run_synthetic_evaluation()
    assert evaluation["scope"].startswith("hand-authored synthetic")
    assert evaluation["rules_only_baseline"]["evidence_reference_validity"] == 1.0
    assert len(evaluation["per_alert"]) == 4
