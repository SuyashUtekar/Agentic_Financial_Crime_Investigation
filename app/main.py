from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .data import ACCOUNTS, ALERTS, TRANSACTIONS
from .schemas import ReviewRequest
from .service import AUDIT, CASES, create_case, get_alert, review_case, run_case
from .evaluation import run_synthetic_evaluation

app = FastAPI(title="Sentinel AML Investigation API", version="0.1.0")
static = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static), name="static")

@app.get("/")
def home(): return FileResponse(static / "index.html")

@app.get("/api/v1/health")
def health(): return {"status": "ok", "mode": "synthetic-demo", "safety": "Human review required"}

@app.get("/api/v1/alerts")
def list_alerts(status: str | None = None, severity: str | None = None):
    rows = [a for a in ALERTS if (not status or a.status == status) and (not severity or a.severity == severity)]
    return {"items": rows, "total": len(rows)}

@app.get("/api/v1/alerts/{alert_id}")
def alert_detail(alert_id: str):
    alert = get_alert(alert_id)
    if not alert: raise HTTPException(404, "Alert not found")
    return {"alert": alert, "account": ACCOUNTS.get(alert.account_id, {}), "transactions": [t for t in TRANSACTIONS if alert.account_id in (t.sender_account_id, t.receiver_account_id)]}

@app.post("/api/v1/cases", status_code=201)
def new_case(payload: dict):
    case = create_case(payload.get("alert_id", ""))
    if not case: raise HTTPException(404, "Alert not found")
    return case

@app.get("/api/v1/cases/{case_id}")
def case_detail(case_id: str):
    if case_id not in CASES: raise HTTPException(404, "Case not found")
    return CASES[case_id]

@app.post("/api/v1/cases/{case_id}/run")
async def execute_case(case_id: str):
    case = await run_case(case_id)
    if not case: raise HTTPException(404, "Case not found")
    return case

@app.get("/api/v1/cases/{case_id}/report")
def report(case_id: str):
    case = CASES.get(case_id)
    if not case or not case.report: raise HTTPException(404, "Report not found")
    return case.report

@app.post("/api/v1/cases/{case_id}/review")
def review(case_id: str, payload: ReviewRequest):
    case = review_case(case_id, payload)
    if not case: raise HTTPException(404, "Case not found")
    return case

@app.get("/api/v1/audit-events")
def audit(case_id: str | None = None):
    return [item for item in AUDIT if not case_id or item["case_id"] == case_id]

@app.post("/api/v1/evaluations/run")
def evaluation():
    return run_synthetic_evaluation()
