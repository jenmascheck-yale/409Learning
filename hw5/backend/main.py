"""Campus Customs desk backend (FastAPI).

Routes the React dashboard calls to watch the agent team and approve money:

  GET  /tickets                 list the three tickets with open/resolved status
  POST /tickets/{id}/run        run the agent team on one ticket (background)
  GET  /run-status              status of the current/last run
  GET  /events                  recent agent-loop events (the audit trail) for refresh
  POST /approve                 a human approves a prepared payment -> actually pays
  GET  /cash                    current checking balance from cash_accounts
  POST /reset                   reset the working DB to the original values

Run it from the backend/ folder:  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BACKEND_DIR = Path(__file__).resolve().parent
HW5_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(HW5_DIR / "mcp_server"))

import agents  # the agent team (run_ticket)  # noqa: E402
import audit  # append-only audit trail  # noqa: E402
import server as mcp_server  # MCP tools; the backend calls `pay` (agents can't)  # noqa: E402

DB_PATH = HW5_DIR / "data" / "campus_customs_new.db"
ORIG_DB = HW5_DIR / "data" / "campus_customs.db"

app = FastAPI(title="Campus Customs Desk API")

# Let the Vite dashboard (Problem 8) call these routes from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tracks the current/most-recent agent run so the dashboard can poll it.
_run_state: dict = {"ticket_id": None, "status": "idle", "summary": None, "error": None}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class ApproveBody(BaseModel):
    kind: str              # "invoice" | "rent" | "purchase_order"
    ref_id: int | None = None
    amount: float
    approved_by: str       # the human who approved (required for a real payment)
    account: str = "checking"


@app.get("/")
def health():
    with _connect() as conn:
        today = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()[0]
    return {"ok": True, "service": "campus-customs-desk", "today": today}


@app.get("/tickets")
def list_tickets():
    """The three tickets and whether each is open or resolved."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, type, requester, subject, sku, size, qty, status, notes "
            "FROM tickets ORDER BY id"
        ).fetchall()
    return {"tickets": [dict(r) for r in rows]}


@app.post("/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int):
    """Run the agent team on one ticket. Runs in the background so the board can
    poll /events and /run-status while the agents work."""
    if _run_state["status"] == "running":
        raise HTTPException(409, f"A run is already in progress for ticket {_run_state['ticket_id']}.")
    with _connect() as conn:
        exists = conn.execute("SELECT 1 FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    if not exists:
        raise HTTPException(404, f"No ticket {ticket_id}.")

    _run_state.update(ticket_id=ticket_id, status="running", summary=None, error=None)

    async def _background():
        try:
            summary = await agents.run_ticket(ticket_id)
            _run_state.update(status="done", summary=summary)
        except Exception as e:  # keep the API alive even if a run fails
            _run_state.update(status="error", error=str(e))

    asyncio.create_task(_background())
    return {"status": "started", "ticket_id": ticket_id}


@app.get("/run-status")
def run_status():
    return _run_state


@app.get("/events")
def events(since: int = 0):
    """Recent agent-loop events (the audit trail): which agent acted, what tool it
    used, and what it said. `since` lets the board fetch only new entries."""
    data = audit._load()
    return {"count": len(data), "events": data[since:]}


@app.post("/approve")
def approve(body: ApproveBody):
    """A human approves a prepared payment. The agents only PREPARE payments; this
    route is what actually moves cash and updates the tables (via the MCP `pay` tool,
    which enforces no-overdraft and requires an approver)."""
    result = mcp_server.pay(
        body.kind, body.ref_id, body.amount, body.approved_by, body.account
    )
    audit.append_events(
        [
            {
                "time": datetime.now(timezone.utc).isoformat(),
                "agent": "human",
                "action": "approve_pay",
                "detail": f"{body.kind} ref={body.ref_id} ${body.amount} by {body.approved_by}",
                "result": audit._short(result),
            }
        ]
    )
    if not result.get("paid"):
        raise HTTPException(400, result.get("reason", "Payment refused."))
    return result


@app.get("/cash")
def cash(account: str = "checking"):
    """Current balance of a cash account (checking by default)."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name=?", (account,)
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"No account {account}.")
    return {"account": row["name"], "balance": row["balance"], "date": row["date"]}


@app.post("/reset")
def reset():
    """Reset the working database to the original values for a fresh run."""
    if _run_state["status"] == "running":
        raise HTTPException(409, "Cannot reset while a run is in progress.")
    shutil.copyfile(ORIG_DB, DB_PATH)
    _run_state.update(ticket_id=None, status="idle", summary=None, error=None)
    with _connect() as conn:
        balance = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name='checking'"
        ).fetchone()[0]
        open_count = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE status='open'"
        ).fetchone()[0]
    return {"reset": True, "checking_balance": balance, "open_tickets": open_count}
