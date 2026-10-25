# Campus Customs — Multi-Agent Operations (HW5)

A multi-agent "operations desk" for the Campus Customs shop. Open tickets land on a
board; a team of PydanticAI agents (Boss, Inventory, Accounting, Facilities, Customer
Service) reads each ticket, delegates, and resolves it — while a human approves any
payment. Three pieces talk to each other:

- **MCP server** (`mcp_server/`, FastMCP) — the only way agents touch shop data, over the
  working database `data/campus_customs_new.db`.
- **FastAPI backend** (`backend/`) — runs the agent team and exposes routes for the board.
- **React dashboard** (`frontend/`, Vite + TypeScript) — watch the agents work and approve
  payments.

All AI calls use **`gpt-6-luna` through the Portkey gateway** (and only that model).

## Prerequisites

- Python 3.11+ and Node 18+
- A Portkey API key with access to `gpt-6-luna`

## Setup

1. **Python env + deps** (from `hw5/`):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows (use source .venv/bin/activate on macOS/Linux)
   pip install -r requirements.txt
   ```
2. **Secrets** — copy the example env and add your key. Keep the real `.env` out of git.
   ```bash
   copy .env.example .env         # cp on macOS/Linux
   # then set PORTKEY_API_KEY in .env
   ```
3. **Working database** — the repo ships both DBs under `data/`. Before a clean run, copy
   the untouched original over the working copy:
   ```bash
   copy data\campus_customs.db data\campus_customs_new.db
   ```
   The MCP server and backend only ever write to `campus_customs_new.db`; the original
   `campus_customs.db` stays pristine so you can reset anytime.

## Run it

- **MCP server** (optional to run standalone; the backend launches it for the agents):
  ```bash
  python mcp_server/server.py
  ```
- **Backend** (from `backend/`): this turns on the API at http://localhost:8000
  ```bash
  cd backend
  uvicorn main:app --reload --port 8000
  ```
- **Dashboard** (from `frontend/`): opens the board at http://localhost:5173
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  The backend allows the Vite origin (`http://localhost:5173`) via CORS.

## Resolve the three tickets

1. Make sure the working DB is fresh (copy the original over it, as above), or click
   **Reset board** in the dashboard (calls `POST /reset`).
2. In the dashboard, pick a ticket (101, 102, 103) and **Run the agent team**. Watch the
   agents delegate and call tools live.
3. When the team prepares a payment, **approve** it in the dashboard — only then does cash
   actually move (agents never pay; the no-overdraft rule is enforced).
4. Reset before any fresh full run so cash and tickets start clean.

## What's where

- `AI_prompts.md` — the log of every prompt given to the vibe coder, one section per problem.
- `mcp_server/` — `server.py` (tools) and its README.
- `backend/` — `main.py` (API), `models.py`, `llm.py`, `agents.py`, `audit.py`, and
  `prompts/` (one file per agent).
- `frontend/` — the React + Vite + TypeScript dashboard.
- `data/` — `campus_customs.db` (original) and `campus_customs_new.db` (working copy).
- `output/` — `harness.md` (full system write-up), `mcp_smoke.json`, `desk_tickets.html`
  (Expected/Actual/Cash/Reflection), `design.md`, `resolved_tickets.json`,
  `resolved_board.html`, `audit_trail.json`, `github_url.txt`.
