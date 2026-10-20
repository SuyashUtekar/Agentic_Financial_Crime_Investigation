"""Narrow, deterministic investigation tools available to the workflow.

The LLM never receives database, shell, network, or arbitrary-query access.
"""
from datetime import datetime, timedelta
from .analytics import account_transactions, features, network
from .data import ACCOUNTS, TRANSACTIONS

MAX_TRANSACTION_LIMIT = 200
MAX_WINDOW_DAYS = 90


def get_account_context(account_id: str) -> dict:
    return {"account_id": account_id, "profile": ACCOUNTS.get(account_id), "data_complete": account_id in ACCOUNTS}


def get_transactions(account_id: str, *, limit: int = 100, window_days: int = 30) -> dict:
    if not 1 <= limit <= MAX_TRANSACTION_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_TRANSACTION_LIMIT}")
    if not 1 <= window_days <= MAX_WINDOW_DAYS:
        raise ValueError(f"window_days must be between 1 and {MAX_WINDOW_DAYS}")
    rows = account_transactions(account_id, TRANSACTIONS)[-limit:]
    return {"records": [row.model_dump(mode="json") for row in rows], "record_count": len(rows), "limit": limit, "window_days": window_days, "truncated": len(rows) == limit}


def compute_transaction_features(account_id: str) -> dict:
    return features(account_id, TRANSACTIONS)


def build_bounded_network(account_id: str, *, max_nodes: int = 50, max_edges: int = 100) -> dict:
    if not 1 <= max_nodes <= 100 or not 1 <= max_edges <= 200:
        raise ValueError("network bounds exceed approved maximum")
    graph = network(account_id, TRANSACTIONS)
    graph["metrics"]["max_nodes"] = max_nodes
    graph["metrics"]["max_edges"] = max_edges
    graph["metrics"]["truncated"] = len(graph["nodes"]) > max_nodes or len(graph["edges"]) > max_edges
    graph["nodes"] = graph["nodes"][:max_nodes]
    graph["edges"] = graph["edges"][:max_edges]
    return graph
