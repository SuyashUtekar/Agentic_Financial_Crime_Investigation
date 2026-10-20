from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    transaction_id: str
    event_timestamp: datetime
    sender_account_id: str
    receiver_account_id: str
    amount: Decimal
    currency: str = "USD"
    transaction_type: str = "transfer"
    channel: str = "online"
    transaction_status: str = "completed"
    memo: str | None = None


class Alert(BaseModel):
    alert_id: str
    account_id: str
    triggered_at: datetime
    rule_code: str
    trigger_reason: str
    severity: Literal["critical", "high", "medium", "low"]
    status: str = "new"
    priority_score: int
    source_model_score: float | None = None


class EvidenceRef(BaseModel):
    type: Literal["transaction", "computed_feature", "graph_path"]
    id: str


class Finding(BaseModel):
    finding_id: str
    typology_id: str
    status: Literal["candidate", "not_observed"]
    summary: str
    features: dict = Field(default_factory=dict)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    counter_evidence: list[str] = Field(default_factory=list)
    verification_status: Literal["verified", "needs_review", "not_observed"]


class Case(BaseModel):
    case_id: str
    alert_id: str
    created_at: datetime
    investigation_status: str = "created"
    reviewer_decision: str | None = None
    decision_reason: str | None = None
    findings: list[Finding] = Field(default_factory=list)
    report: dict | None = None
    workflow_state: dict = Field(default_factory=dict)
    workflow_trace: list[dict] = Field(default_factory=list)
    tool_runs: list[dict] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    decision: Literal["close", "continue_investigation", "escalate"]
    reason: str = Field(min_length=3, max_length=1000)
    reviewer_id: str = Field(default="demo.analyst", max_length=100)
