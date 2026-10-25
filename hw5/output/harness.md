# Campus Customs — Harness

Working database: `data/campus_customs_new.db` (a copy of `data/campus_customs.db`, which stays untouched so we can reset before a full run). The shop's "today" is `desk.date_today` = **2026-08-31**, and that is the date agents use to decide what is overdue.

This file grows as the assignment goes — later problems add the MCP tools, the five agents, the API routes, the dashboard, and the safety rules.

## Database tables

### desk
**Fields:** `date_today`, `notes`
The shop's clock — agents read `date_today` to judge what is overdue (rent, invoices) instead of the real-world date.

### tickets
**Fields:** `id`, `type`, `requester`, `subject`, `sku`, `size`, `qty`, `lease_id`, `invoice_id`, `status`, `notes`, `created_at`
The work queue — each row is a job the Boss reads and routes, and its `sku` / `size` / `qty` / `lease_id` / `invoice_id` are the links the agents follow into the other tables.

### inventory
**Fields:** `sku`, `name`, `size`, `qty`, `location`
Stock on hand by SKU and size — the Inventory agent checks this to fill customer orders and spot shortfalls that need a restock.

### pricing
**Fields:** `sku`, `unit_cost`, `list_price`
Cost vs. list price per SKU — the Accounting agent uses it to check margins and judge discount requests.

### vendors
**Fields:** `id`, `name`, `specialty`, `lead_days`
Who can restock and how fast — Inventory matches a shortfall to a vendor by `specialty` and uses `lead_days` for timing.

### invoices
**Fields:** `id`, `vendor_id`, `amount`, `due_date`, `status`, `description`
Money the shop owes vendors — Accounting watches these, and the shop rule is that a vendor with an open (unpaid) invoice will not ship new product until it is paid.

### leases
**Fields:** `id`, `space_name`, `landlord`, `monthly_rent`, `next_due`, `notes`
The shop space and its rent schedule — the Facilities agent compares `next_due` to `date_today` to see whether rent is due or overdue.

### cash_accounts
**Fields:** `name`, `balance`, `date`
How much cash is available — the pay tool must refuse any payment that would overdraw it (no negative balances; cash only goes out in this homework).

### payments
**Fields:** `id`, `kind`, `ref_id`, `amount`, `account`, `paid_at`, `approved_by`
The record of money that has gone out — a row is written here only after a human approves the payment, including who approved it (`approved_by`). Starts empty.

## The three open tickets and how they link

**Ticket 101 — customer_order (Tauhid Zaman): 1× white Bulldog tee, size S**
- `sku` CC-TEE-WHITE → **inventory** size S = **0** (out of stock) and **pricing** (cost 8 / list 28).
- `invoice_id` 501 → **invoices**: $840 **open** to vendor 1 (Bulldog Print Co) for "Rush reprint CC-TEE-WHITE S".
- To restock the tee the vendor must ship, but the rule blocks shipping while invoice 501 is open → Accounting pays 501 (with human approval) before Inventory can restock.

**Ticket 102 — rent_notice (Elm City Properties): rent due**
- `lease_id` 1 → **leases**: Chapel Street shop, $2,400/mo, `next_due` 2026-09-02 (2 days out from today, 2026-08-31).
- Facilities confirms it is due; Accounting prepares the $2,400 payment → human approval → write to **payments** and reduce **cash_accounts**.

**Ticket 103 — price_override (Yale AI Club): 20× navy hoodie, size M, bulk discount**
- `sku` CC-HOOD-NAVY → **inventory** size M = **8** (short 12 for a 20-unit order) and **pricing** (cost 22 / list 58).
- Inventory flags the shortfall; a restock would come from vendor 1 (apparel reprint, 5-day lead), which is again blocked until invoice 501 is paid.
- Accounting checks margin to decide how deep a bulk discount can go; Customer Service drafts the reply to the club.

**Cash sanity check:** checking starts at **$3,400**. Invoice 501 ($840) + rent ($2,400) = $3,240, leaving $160 — so both fit, but any hoodie restock purchase has to respect whatever cash is left and the pay tool's no-overdraw rule.

## MCP tools (Problem 3)

The MCP server (`mcp_server/server.py`, FastMCP) reads the working copy
`data/campus_customs_new.db`. These are the three tools, one per open ticket,
plus a supporting invoice tool. They are read-only and never invent data.

| Tool | Reads table | Unlocks ticket | Why it's the right tool for that ticket |
|------|-------------|----------------|------------------------------------------|
| `check_stock(sku, size)` | `inventory` | **101** | Ticket 101 is a size-S CC-TEE-WHITE order, and this tool reports that size as 0 on hand — the exact shortfall the ticket is about. |
| `get_lease(lease_id)` | `leases` | **102** | Ticket 102 is a rent notice on lease 1, and this returns the $2,400 monthly rent and the 2026-09-02 due date the team needs to act on it. |
| `get_pricing(sku)` | `pricing` | **103** | Ticket 103 asks for a bulk hoodie discount, and this returns CC-HOOD-NAVY's $22 cost / $58 list so Accounting can check margin before discounting. |

**Supporting tool (also for ticket 101):**

| Tool | Reads table | Supports ticket | Why |
|------|-------------|-----------------|-----|
| `get_open_invoices(vendor_id?)` | `invoices` | **101** | The tee reprint comes from vendor 1, who has an open $840 invoice; this tool surfaces that unpaid invoice so the team honors the "no shipping while unpaid" rule before restocking. |

More tools (restock, prepare payment, human-approved pay) are added in Problem 5.

## The agent team (Problem 5)

Five PydanticAI agents, all running **gpt-6-luna through Portkey**, sharing one MCP
server (`mcp_server/server.py` over `data/campus_customs_new.db`). Full connectivity:
any agent can hand work to any other via a `delegate` tool (specialists return to
their caller rather than looping back to the Boss). Prompts live in `backend/prompts/`.

| Agent | Prompt file | Role | MCP tools it leans on |
|-------|-------------|------|------------------------|
| **Boss** | `prompts/boss.md` | Reads each ticket, routes it, makes the final call, resolves it | `list_open_tickets`, `get_ticket`, `resolve_ticket`, `delegate` |
| **Inventory** | `prompts/inventory.md` | Stock by SKU/size, shortfalls, which vendor restocks | `check_stock`, `get_vendor`, `get_open_invoices`, `restock` |
| **Accounting** | `prompts/accounting.md` | Cash, invoices, margins; prepares payments for approval | `get_cash_balance`, `get_open_invoices`, `get_pricing`, `record_discount`, `prepare_payment` |
| **Facilities** | `prompts/facilities.md` | Leases and rent | `get_lease` |
| **Customer Service** | `prompts/customer_service.md` | Drafts customer messages (drafts only) | `get_ticket`, `check_stock`, `get_vendor` |

## MCP tools — full list (Problem 5)

All tools read/write the single working database `data/campus_customs_new.db`. No shop
facts come from anywhere else (no second tools layer bypasses MCP).

| Tool | Table(s) used | What it does |
|------|---------------|--------------|
| `check_stock(sku, size)` | inventory | On-hand qty for a SKU/size, with an `in_stock` flag |
| `get_lease(lease_id)` | leases, desk | Rent amount, next due date, and whether overdue vs. today |
| `get_pricing(sku)` | pricing | Unit cost, list price, margin |
| `get_open_invoices(vendor_id?)` | invoices | Open/unpaid invoices, optionally for one vendor |
| `list_open_tickets()` | tickets | All open tickets on the board |
| `get_ticket(ticket_id)` | tickets | One ticket with its linked fields |
| `get_vendor(vendor_id)` | vendors | Vendor specialty and lead time |
| `get_cash_balance(account)` | cash_accounts | Current balance of a cash account |
| `record_discount(sku, qty, discount_pct)` | pricing | Quotes a bulk discount's unit price + margin (no write) |
| `prepare_payment(kind, ref_id, amount, reason)` | — (draft only) | Drafts a payment for human approval; moves no money |
| `pay(kind, ref_id, amount, approved_by, account)` | cash_accounts, payments, invoices/leases | Runs an **approved** payment; refuses on no approver or insufficient cash |
| `restock(sku, size, qty, vendor_id)` | invoices, inventory | Adds stock **only if** the vendor has no open invoice |
| `resolve_ticket(ticket_id, outcome)` | tickets | Marks a ticket resolved and records the outcome |

## Safety and limits

Guardrails a real business would want when agents touch real customers and real money:

- **Human approval for money.** The `pay` tool is **filtered out of the agent team** —
  agents can only `prepare_payment`. Real cash moves only when a human approves it
  through the backend route (Problem 7). `pay` also requires a non-empty `approved_by`.
- **No overdrafts.** `pay` refuses any payment larger than the account balance; cash
  only goes out (no revenue is modeled), so the balance can never go negative.
- **Vendors won't ship while unpaid.** `restock` refuses when the vendor still has an
  open invoice, matching the shop rule.
- **Truth only, from the database.** Every shop fact comes from an MCP tool over the
  real DB; agents never invent stock, prices, dates, or balances.
- **Drafts stay on the board.** Customer Service writes drafts; no real emails or vendor
  calls are sent.
- **Working copy is isolated.** All writes hit `campus_customs_new.db`; the original
  `campus_customs.db` is untouched so a run can always be reset.

Limits that keep token use in check (multi-agent chats burn tokens fast):

- **Per-ticket request budget** of `REQUEST_LIMIT = 30` model requests, shared across
  the Boss and every delegated sub-run (a `RunUsage` passed through the chain).
- **Delegation depth cap** of `MAX_DEPTH = 2`. Full connectivity is allowed — any agent
  may delegate to any other, including back to the Boss — and the depth cap plus prompt
  guidance (specialists prefer to return their answer to the caller) keep delegation from
  looping.
- **One shared model and one shared MCP server** for the whole team, so each ticket
  spins up a single connection, not five.
- Budget overruns **degrade gracefully** (a sub-agent returning a short note) instead of
  crashing the run.

## API routes (Problem 7)

FastAPI app in `backend/main.py`; run it from `backend/` with
`uvicorn main:app --reload --port 8000`. CORS allows the Vite dashboard origin
(`http://localhost:5173`).

| Route | What it does |
|-------|--------------|
| `GET /` | Health check — service name and the shop's "today". |
| `GET /tickets` | Returns the three tickets, each with its open/resolved status. |
| `POST /tickets/{id}/run` | Runs the agent team on one ticket (in the background so the board can poll while it works). |
| `GET /run-status` | Status of the current/last run (running / done / error, with the boss summary). |
| `GET /events?since=N` | Recent agent-loop events from the audit trail, so the board can refresh (`since` fetches only new ones). |
| `POST /approve` | A human approves a prepared payment — this route actually moves cash via the MCP `pay` tool (which refuses overdrafts). |
| `GET /cash?account=checking` | Current balance from `cash_accounts`. |
| `POST /reset` | Resets the working DB to the original values for a fresh run. |

## Dashboard (Problem 8)

React + Vite + TypeScript board in `frontend/` (Yale/Bulldog Blue, Garamond + Verdana),
started with `npm run dev` on `http://localhost:5173`. It calls the backend on
`http://localhost:8000` and lets a human run and supervise the team:

- **Open board** — lists the three tickets with an open/resolved pill; click to select one.
- **Run the agent team** — starts a run; the **agent activity feed** streams events live,
  color-coded per agent (Boss / Inventory / Accounting / Facilities / Customer Service /
  Human) with delegate / tool / reply / human-pay tags.
- **Resolved + summary** — the ticket flips to RESOLVED when the run finishes and a short
  run summary appears.
- **Approval card** — when the team prepares a payment, the human approves it here; only
  then does money move (agents cannot pay).
- **Checking balance** — shown in the top bar and drops after an approved pay.
- **Reset board** — calls `POST /reset` for a clean run.

The feed uses a `since` baseline into the audit trail so it shows only the current run.
See `output/design.md` for the full design rationale.

## Full run result (Problem 9)

A reset-and-run over all three tickets: started at **$3,400** checking, ended at **$160**,
matching `cash_accounts`. Human-approved payments: invoice #501 ($840, ticket 101) and rent
($2,400, ticket 102); ticket 103's $264 restock PO was correctly refused for insufficient
cash. All three tickets resolved. Per-ticket Actual vs. Expected and the cash itemization are
in `output/desk_tickets.html`; the structured record is in `output/resolved_tickets.json`;
real agent-loop events are appended to `output/audit_trail.json`.
