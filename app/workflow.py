"""LangGraph orchestration for bounded AML investigation work."""
from __future__ import annotations
from typing import Any, Literal, TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from .analytics import detect_patterns, validate_references
from .data import ALERTS, TRANSACTIONS
from .llm import plan_investigation, polish_summary
from .tools import build_bounded_network, compute_transaction_features, get_account_context, get_transactions


class InvestigationState(TypedDict, total=False):
    case_id: str
    alert_id: str
    account_id: str
    status: str
    plan: dict[str, Any]
    context: dict[str, Any]
    transactions: dict[str, Any]
    features: dict[str, Any]
    findings: list[dict[str, Any]]
    network: dict[str, Any]
    validation: dict[str, Any]
    report: dict[str, Any]
    tool_runs: list[dict[str, Any]]
    trace: list[dict[str, Any]]
    retry_counts: dict[str, int]
    escalation_reason: str | None


def _alert(alert_id: str):
    return next((item for item in ALERTS if item.alert_id == alert_id), None)


def _record(state: InvestigationState, node: str, outcome: str, detail: dict | None = None) -> dict:
    trace = list(state.get("trace", []))
    trace.append({"node": node, "outcome": outcome, "detail": detail or {}})
    return {"trace": trace}


def _tool(state: InvestigationState, name: str, args: dict, outcome: str = "success") -> dict:
    runs = list(state.get("tool_runs", []))
    runs.append({"tool_name": name, "arguments": args, "outcome": outcome})
    return {"tool_runs": runs}


def triage_node(state: InvestigationState) -> dict:
    alert = _alert(state["alert_id"])
    if not alert:
        result = {"status": "escalated", "escalation_reason": "alert_not_found"}
        result.update(_record(state, "triage", "escalated", {"reason": "alert_not_found"}))
        return result
    result = {"status": "planning", "account_id": alert.account_id}
    result.update(_record(state, "triage", "success", {"severity": alert.severity, "rule_code": alert.rule_code}))
    return result


async def planner_node(state: InvestigationState) -> dict:
    alert = _alert(state["alert_id"])
    if not alert:
        return {}
    plan = await plan_investigation(alert.model_dump(mode="json"))
    result = {"status": "collecting_evidence", "plan": plan}
    result.update(_record(state, "planner", "success", {"actions": plan["actions"], "source": plan["model"]["source"]}))
    return result


def collection_node(state: InvestigationState) -> dict:
    retries = dict(state.get("retry_counts", {}))
    try:
        transactions = get_transactions(state["account_id"], limit=100, window_days=30)
        context = get_account_context(state["account_id"])
        result = {"status": "analyzing_transactions", "transactions": transactions, "context": context, "retry_counts": retries}
        result.update(_tool(state, "get_transactions", {"account_id": state["account_id"], "limit": 100, "window_days": 30}))
        result.update(_tool({**state, "tool_runs": result["tool_runs"]}, "get_account_context", {"account_id": state["account_id"]}))
        result.update(_record(state, "evidence_collection", "success", {"record_count": transactions["record_count"]}))
        return result
    except (ValueError, RuntimeError) as error:
        attempts = retries.get("get_transactions", 0) + 1
        retries["get_transactions"] = attempts
        outcome = "retryable_failure" if attempts < 2 else "escalated"
        result = {"retry_counts": retries, "status": "collecting_evidence" if attempts < 2 else "escalated"}
        if attempts >= 2:
            result["escalation_reason"] = "transaction_tool_failed_after_bounded_retries"
        result.update(_tool(state, "get_transactions", {"account_id": state["account_id"]}, outcome))
        result.update(_record(state, "evidence_collection", outcome, {"attempt": attempts, "error": str(error)}))
        return result


def transaction_analysis_node(state: InvestigationState) -> dict:
    facts = compute_transaction_features(state["account_id"])
    result = {"features": facts, "status": "routing_analysis"}
    result.update(_tool(state, "compute_transaction_features", {"account_id": state["account_id"]}))
    result.update(_record(state, "transaction_analyst", "success", {"unique_counterparties": facts["unique_counterparties"]}))
    return result


def route_after_transaction(state: InvestigationState) -> Literal["network", "typology", "escalate", "retry_collection"]:
    if state.get("status") == "escalated":
        return "escalate"
    if state.get("status") == "collecting_evidence":
        return "retry_collection"
    if not state.get("features", {}).get("data_complete"):
        return "escalate"
    planned = state.get("plan", {}).get("actions", [])
    if "network_analysis" in planned or state["features"].get("unique_counterparties", 0) >= 3:
        return "network"
    return "typology"


def network_node(state: InvestigationState) -> dict:
    graph = build_bounded_network(state["account_id"], max_nodes=50, max_edges=100)
    result = {"network": graph, "status": "testing_typologies"}
    result.update(_tool(state, "build_bounded_network", {"account_id": state["account_id"], "max_nodes": 50, "max_edges": 100}))
    result.update(_record(state, "network_analyst", "success", graph["metrics"]))
    return result


def typology_node(state: InvestigationState) -> dict:
    findings = [item.model_dump() for item in detect_patterns(state["account_id"], TRANSACTIONS)]
    candidates = [item["typology_id"] for item in findings if item["status"] == "candidate"]
    result = {"findings": findings, "status": "verifying_evidence"}
    result.update(_record(state, "typology_analyst", "success", {"candidates": candidates}))
    return result


def route_after_typology(state: InvestigationState) -> Literal["network", "verify"]:
    candidate_types = {item["typology_id"] for item in state.get("findings", []) if item["status"] == "candidate"}
    if candidate_types.intersection({"RAPID_IN_OUT", "MANY_TO_ONE", "ONE_TO_MANY"}) and not state.get("network"):
        return "network"
    return "verify"


def verification_node(state: InvestigationState) -> dict:
    findings = detect_patterns(state["account_id"], TRANSACTIONS)
    validation = validate_references(findings, TRANSACTIONS)
    status = "drafting_case" if validation["valid"] else "escalated"
    result = {"validation": validation, "status": status}
    if not validation["valid"]:
        result["escalation_reason"] = "evidence_references_failed_validation"
    result.update(_record(state, "evidence_verifier", "success" if validation["valid"] else "failed", validation))
    return result


async def narrative_node(state: InvestigationState) -> dict:
    alert = _alert(state["alert_id"])
    candidate_names = [item["typology_id"].replace("_", " ").lower() for item in state.get("findings", []) if item["status"] == "candidate"]
    observed = ", ".join(candidate_names) or "no configured candidate typologies"
    facts = state["features"]
    summary = (f"The review of alert {alert.alert_id} for account {alert.account_id} identified {facts['transaction_count']} transactions, "
        f"with inbound total {facts['inbound_total']:.2f} and outbound total {facts['outbound_total']:.2f}. "
        f"The evidence is consistent with the configured {observed} indicator(s). These are candidate indicators only; "
        "available synthetic records do not establish intent or rule out benign explanations.")
    narrative, model = await polish_summary(summary)
    report = {
        "case_summary": {"alert_id": alert.alert_id, "account_id": alert.account_id, "trigger": alert.trigger_reason, "time_range": "Bounded synthetic transaction history"},
        "executive_summary": narrative,
        "observed_facts": facts,
        "timeline": state["transactions"]["records"],
        "network": state.get("network", {"nodes": [], "edges": [], "metrics": {"truncated": True}}),
        "findings": state["findings"],
        "analysis_plan": state["plan"],
        "workflow_trace": state.get("trace", []),
        "tool_runs": state.get("tool_runs", []),
        "alternative_explanations": [item for finding in state["findings"] for item in finding["counter_evidence"]],
        "data_gaps": ["Synthetic demonstration dataset; no real KYC, invoice, sanctions, or external counterparty data is connected."],
        "recommended_next_steps": ["Validate payment purpose with authorized supporting records.", "Assess relationships between identified counterparties.", "Human reviewer to determine whether more investigation is warranted."],
        "evidence_validation": state["validation"], "model": model,
        "safety_notice": "Candidate indicators are not a finding of criminal activity. Human review is required.",
    }
    result = {"report": report, "status": "awaiting_human_review"}
    result.update(_record(state, "narrative_agent", "success", {"llm_used": model["used"]}))
    return result


def escalation_node(state: InvestigationState) -> dict:
    reason = state.get("escalation_reason") or "required_evidence_unavailable"
    report = {"status": "escalated", "data_gaps": [reason], "workflow_trace": state.get("trace", []), "tool_runs": state.get("tool_runs", []), "model": {"used": False}, "safety_notice": "No conclusion was generated because required evidence was unavailable or invalid."}
    result = {"status": "escalated", "report": report}
    result.update(_record(state, "escalation", "escalated", {"reason": reason}))
    return result


def route_after_verify(state: InvestigationState) -> Literal["narrative", "escalate"]:
    return "narrative" if state.get("validation", {}).get("valid") else "escalate"


def build_graph():
    builder = StateGraph(InvestigationState)
    builder.add_node("triage", triage_node)
    builder.add_node("planner", planner_node)
    builder.add_node("collect", collection_node)
    builder.add_node("transaction_analysis", transaction_analysis_node)
    builder.add_node("network", network_node)
    builder.add_node("typology", typology_node)
    builder.add_node("verify", verification_node)
    builder.add_node("narrative", narrative_node)
    builder.add_node("escalate", escalation_node)
    builder.add_edge(START, "triage")
    builder.add_conditional_edges("triage", lambda state: "escalate" if state.get("status") == "escalated" else "planner")
    builder.add_edge("planner", "collect")
    builder.add_edge("collect", "transaction_analysis")
    builder.add_conditional_edges("transaction_analysis", route_after_transaction, {"network": "network", "typology": "typology", "escalate": "escalate", "retry_collection": "collect"})
    builder.add_edge("network", "typology")
    builder.add_conditional_edges("typology", route_after_typology, {"network": "network", "verify": "verify"})
    builder.add_conditional_edges("verify", route_after_verify, {"narrative": "narrative", "escalate": "escalate"})
    builder.add_edge("narrative", END)
    builder.add_edge("escalate", END)
    return builder.compile(checkpointer=InMemorySaver())


GRAPH = build_graph()


async def execute_agentic_investigation(case_id: str, alert_id: str, prior: dict | None = None) -> InvestigationState:
    seed: InvestigationState = {"case_id": case_id, "alert_id": alert_id, "trace": list((prior or {}).get("trace", [])), "tool_runs": list((prior or {}).get("tool_runs", [])), "retry_counts": dict((prior or {}).get("retry_counts", {}))}
    return await GRAPH.ainvoke(seed, {"configurable": {"thread_id": case_id}, "recursion_limit": 20})
