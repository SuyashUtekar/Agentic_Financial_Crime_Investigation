from datetime import datetime, timedelta, timezone
from decimal import Decimal
from .schemas import Alert, Transaction

UTC = timezone.utc
NOW = datetime(2026, 10, 20, 9, 30, tzinfo=UTC)


def tx(identifier: str, minutes: int, sender: str, receiver: str, amount: str, memo: str) -> Transaction:
    return Transaction(
        transaction_id=identifier,
        event_timestamp=NOW + timedelta(minutes=minutes),
        sender_account_id=sender,
        receiver_account_id=receiver,
        amount=Decimal(amount),
        memo=memo,
    )


TRANSACTIONS = [
    tx("TX-1001", -390, "ACC-201", "ACC-102", "4200.00", "Invoice settlement"),
    tx("TX-1002", -360, "ACC-202", "ACC-102", "3800.00", "Transfer"),
    tx("TX-1003", -330, "ACC-203", "ACC-102", "4100.00", "Service payment"),
    tx("TX-1004", -285, "ACC-102", "ACC-301", "10800.00", "Vendor transfer"),
    tx("TX-1005", -220, "ACC-301", "ACC-401", "9000.00", "Settlement"),
    tx("TX-1006", -185, "ACC-401", "ACC-102", "8500.00", "Return transfer"),
    tx("TX-1007", -11000, "ACC-102", "ACC-501", "300.00", "Prior purchase"),
    tx("TX-1008", -9000, "ACC-102", "ACC-502", "220.00", "Prior purchase"),
    tx("TX-2001", -600, "ACC-601", "ACC-103", "1750.00", "Marketplace payout"),
    tx("TX-2002", -540, "ACC-602", "ACC-103", "1900.00", "Marketplace payout"),
    tx("TX-2003", -500, "ACC-603", "ACC-103", "1650.00", "Marketplace payout"),
    tx("TX-2004", -450, "ACC-604", "ACC-103", "2100.00", "Marketplace payout"),
    tx("TX-3001", -1200, "ACC-104", "ACC-701", "950.00", "Supplier payment"),
    tx("TX-3002", -1150, "ACC-104", "ACC-702", "1020.00", "Supplier payment"),
    tx("TX-3003", -1100, "ACC-104", "ACC-703", "970.00", "Supplier payment"),
    tx("TX-3004", -1050, "ACC-104", "ACC-704", "1100.00", "Supplier payment"),
    tx("TX-4001", -5000, "ACC-801", "ACC-105", "650.00", "Salary"),
]

ALERTS = [
    Alert(alert_id="ALT-2026-001", account_id="ACC-102", triggered_at=NOW, rule_code="RAPID_FLOW", trigger_reason="High value outflow after multiple inbound transfers", severity="critical", priority_score=92),
    Alert(alert_id="ALT-2026-002", account_id="ACC-103", triggered_at=NOW - timedelta(minutes=30), rule_code="AGGREGATION", trigger_reason="Multiple counterparties credited one account", severity="high", priority_score=78),
    Alert(alert_id="ALT-2026-003", account_id="ACC-104", triggered_at=NOW - timedelta(hours=2), rule_code="DISPERSION", trigger_reason="One account paid multiple counterparties", severity="medium", priority_score=61),
    Alert(alert_id="ALT-2026-004", account_id="ACC-105", triggered_at=NOW - timedelta(hours=6), rule_code="VELOCITY_REVIEW", trigger_reason="Limited context available for unusual activity review", severity="low", priority_score=34),
]

ACCOUNTS = {
    "ACC-102": {"name": "Northbridge Trading", "type": "Business checking", "country": "US", "risk": "Medium", "opened": "2024-03-12"},
    "ACC-103": {"name": "Harbor Marketplace", "type": "Business checking", "country": "US", "risk": "Low", "opened": "2025-01-07"},
    "ACC-104": {"name": "Cedar Wholesale", "type": "Business checking", "country": "US", "risk": "Medium", "opened": "2024-09-19"},
    "ACC-105": {"name": "Demo Account 105", "type": "Personal checking", "country": "US", "risk": "Unknown", "opened": "2026-08-01"},
}
