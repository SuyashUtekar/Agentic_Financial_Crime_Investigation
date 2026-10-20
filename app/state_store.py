"""Small local checkpoint store for the MVP.

Replace this with a transactional PostgreSQL/LangGraph checkpointer before a
multi-user deployment. It intentionally stores only synthetic demo state.
"""
import json
from pathlib import Path
from .schemas import Case

STATE_PATH = Path(__file__).parents[1] / "data" / "runtime" / "workflow_state.json"


def load_state() -> tuple[dict[str, Case], list[dict]]:
    if not STATE_PATH.exists():
        return {}, []
    try:
        payload = json.loads(STATE_PATH.read_text())
        return {key: Case.model_validate(value) for key, value in payload.get("cases", {}).items()}, payload.get("audit", [])
    except (OSError, ValueError):
        # A damaged local demo checkpoint must not cause an investigation to
        # invent a recovery state. Start empty and let the user reopen a case.
        return {}, []


def save_state(cases: dict[str, Case], audit: list[dict]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps({"cases": {key: value.model_dump(mode="json") for key, value in cases.items()}, "audit": audit}, indent=2))
    temporary.replace(STATE_PATH)
