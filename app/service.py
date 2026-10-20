from datetime import datetime, timezone
from uuid import uuid4
from .data import ALERTS
from .schemas import Case, Finding, ReviewRequest
from .state_store import load_state, save_state
from .workflow import execute_agentic_investigation

CASES, AUDIT = load_state()


def event(case_id: str, action: str, outcome: str, detail: dict | None = None):
    AUDIT.append({"event_id": f"AUD-{uuid4().hex[:8]}", "case_id": case_id, "timestamp": datetime.now(timezone.utc).isoformat(), "actor_type": "system", "action": action, "outcome": outcome, "detail": detail or {}})
    save_state(CASES, AUDIT)


def get_alert(alert_id: str):
    return next((alert for alert in ALERTS if alert.alert_id == alert_id), None)


def create_case(alert_id: str) -> Case | None:
    alert = get_alert(alert_id)
    if not alert:
        return None
    existing = next((case for case in CASES.values() if case.alert_id == alert_id and case.investigation_status not in {"completed", "cancelled"}), None)
    if existing:
        return existing
    case = Case(case_id=f"CASE-{uuid4().hex[:8].upper()}", alert_id=alert_id, created_at=datetime.now(timezone.utc))
    CASES[case.case_id] = case
    event(case.case_id, "case_created", "success", {"alert_id": alert_id})
    return case


async def run_case(case_id: str) -> Case | None:
    case = CASES.get(case_id)
    if not case:
        return None
    # A completed evidence pack is immutable until the human explicitly asks
    # for more investigation. This prevents accidental duplicate agent runs.
    if case.investigation_status in {"awaiting_human_review", "completed"}:
        return case
    state = await execute_agentic_investigation(case_id, case.alert_id, case.workflow_state)
    case.investigation_status = state.get("status", "failed")
    case.workflow_state = {"retry_counts": state.get("retry_counts", {}), "trace": state.get("trace", []), "tool_runs": state.get("tool_runs", [])}
    case.workflow_trace = state.get("trace", [])
    case.tool_runs = state.get("tool_runs", [])
    case.findings = [Finding.model_validate(item) for item in state.get("findings", [])]
    case.report = state.get("report")
    for item in state.get("trace", []):
        event(case_id, f"agent.{item['node']}", item["outcome"], item.get("detail", {}))
    save_state(CASES, AUDIT)
    return case


def review_case(case_id: str, review: ReviewRequest) -> Case | None:
    case = CASES.get(case_id)
    if not case:
        return None
    case.reviewer_decision, case.decision_reason = review.decision, review.reason
    case.investigation_status = "completed" if review.decision == "close" else ("escalated" if review.decision == "escalate" else "collecting_evidence")
    AUDIT.append({"event_id": f"AUD-{uuid4().hex[:8]}", "case_id": case_id, "timestamp": datetime.now(timezone.utc).isoformat(), "actor_type": "human", "actor_id": review.reviewer_id, "action": "case_reviewed", "outcome": review.decision, "detail": {"reason": review.reason}})
    save_state(CASES, AUDIT)
    return case
