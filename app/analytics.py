from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
import networkx as nx
from .schemas import Finding, EvidenceRef, Transaction


def account_transactions(account_id: str, transactions: list[Transaction]) -> list[Transaction]:
    return sorted([t for t in transactions if account_id in (t.sender_account_id, t.receiver_account_id)], key=lambda t: t.event_timestamp)


def features(account_id: str, transactions: list[Transaction]) -> dict:
    rows = account_transactions(account_id, transactions)
    incoming = [t for t in rows if t.receiver_account_id == account_id]
    outgoing = [t for t in rows if t.sender_account_id == account_id]
    inbound = sum((t.amount for t in incoming), Decimal("0"))
    outbound = sum((t.amount for t in outgoing), Decimal("0"))
    counterparties = {t.sender_account_id if t.receiver_account_id == account_id else t.receiver_account_id for t in rows}
    return {
        "transaction_count": len(rows), "inbound_count": len(incoming), "outbound_count": len(outgoing),
        "inbound_total": float(inbound), "outbound_total": float(outbound),
        "outbound_inbound_ratio": round(float(outbound / inbound), 2) if inbound else None,
        "unique_counterparties": len(counterparties),
        "data_complete": bool(rows),
    }


def detect_patterns(account_id: str, transactions: list[Transaction]) -> list[Finding]:
    rows = account_transactions(account_id, transactions)
    incoming = [t for t in rows if t.receiver_account_id == account_id]
    outgoing = [t for t in rows if t.sender_account_id == account_id]
    result: list[Finding] = []
    inbound_total = sum((t.amount for t in incoming), Decimal("0"))
    rapid_outgoing = []
    for outbound in outgoing:
        if any(t.event_timestamp <= outbound.event_timestamp <= t.event_timestamp + timedelta(hours=6) for t in incoming):
            rapid_outgoing.append(outbound)
    rapid_total = sum((t.amount for t in rapid_outgoing), Decimal("0"))
    # Scope the denominator to inbound funds that could actually precede the
    # candidate outflow; later credits must not dilute this temporal feature.
    first_rapid_outflow = min((t.event_timestamp for t in rapid_outgoing), default=None)
    matched_inbound = [t for t in incoming if first_rapid_outflow and t.event_timestamp <= first_rapid_outflow]
    matched_inbound_total = sum((t.amount for t in matched_inbound), Decimal("0"))
    ratio = rapid_total / matched_inbound_total if matched_inbound_total else Decimal("0")
    if matched_inbound_total and ratio >= Decimal("0.70"):
        refs = [EvidenceRef(type="transaction", id=t.transaction_id) for t in incoming + rapid_outgoing]
        result.append(Finding(finding_id=f"FIND-{account_id}-RAPID", typology_id="RAPID_IN_OUT", status="candidate",
            summary="A substantial proportion of identified inbound value was followed by outgoing transfers within the configured six-hour window.",
            features={"inbound_total": float(matched_inbound_total), "outbound_within_6h": float(rapid_total), "outbound_within_window_ratio": round(float(ratio), 2), "window_hours": 6},
            evidence_refs=refs, counter_evidence=["Available demo data does not include invoice, payroll, or merchant-settlement corroboration."], verification_status="verified"))
    senders = {t.sender_account_id for t in incoming}
    if len(senders) >= 3:
        result.append(Finding(finding_id=f"FIND-{account_id}-MTO", typology_id="MANY_TO_ONE", status="candidate",
            summary="Multiple distinct counterparties credited the account in the reviewed window.",
            features={"distinct_senders": len(senders), "inbound_total": float(inbound_total), "review_window_hours": 24},
            evidence_refs=[EvidenceRef(type="transaction", id=t.transaction_id) for t in incoming], counter_evidence=["Counterparty relationships are not available in the synthetic profile."], verification_status="verified"))
    receivers = {t.receiver_account_id for t in outgoing}
    outbound_total = sum((t.amount for t in outgoing), Decimal("0"))
    if len(receivers) >= 3:
        result.append(Finding(finding_id=f"FIND-{account_id}-OTM", typology_id="ONE_TO_MANY", status="candidate",
            summary="The account sent funds to multiple distinct counterparties in the reviewed window.",
            features={"distinct_receivers": len(receivers), "outbound_total": float(outbound_total), "review_window_hours": 24},
            evidence_refs=[EvidenceRef(type="transaction", id=t.transaction_id) for t in outgoing], counter_evidence=["Payment purpose data is limited to unverified synthetic memos."], verification_status="verified"))
    if not result:
        result.append(Finding(finding_id=f"FIND-{account_id}-NONE", typology_id="INSUFFICIENT_EVIDENCE", status="not_observed",
            summary="No configured candidate pattern could be verified from the available transaction records.", features=features(account_id, transactions), evidence_refs=[], counter_evidence=["Insufficient transaction history for a conclusive pattern assessment."], verification_status="not_observed"))
    return result


def network(account_id: str, transactions: list[Transaction]) -> dict:
    relevant = account_transactions(account_id, transactions)
    graph = nx.DiGraph()
    for row in relevant:
        graph.add_edge(row.sender_account_id, row.receiver_account_id, transaction_id=row.transaction_id, amount=float(row.amount), timestamp=row.event_timestamp.isoformat())
    nodes = [{"id": node, "label": node, "focus": node == account_id, "degree": graph.degree(node)} for node in graph.nodes]
    edges = [{"id": edge[2]["transaction_id"], "source": edge[0], "target": edge[1], "amount": edge[2]["amount"], "timestamp": edge[2]["timestamp"]} for edge in graph.edges(data=True)]
    cycles = list(nx.simple_cycles(graph))[:5]
    return {"nodes": nodes, "edges": edges, "metrics": {"node_count": len(nodes), "edge_count": len(edges), "cycles": cycles, "truncated": False}}


def validate_references(findings: list[Finding], transactions: list[Transaction]) -> dict:
    known = {t.transaction_id for t in transactions}
    broken = [ref.id for finding in findings for ref in finding.evidence_refs if ref.type == "transaction" and ref.id not in known]
    return {"valid": not broken, "references_checked": sum(len(f.evidence_refs) for f in findings), "broken_references": broken}
