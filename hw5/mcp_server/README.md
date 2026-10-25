# Campus Customs MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that gives every agent in
Homework 5 a single, shared way to read real shop facts. Agents never query the
database on their own and never invent data — they call these tools, and the
tools return only rows that exist in the database.

## Database

The server talks to the **working copy**, `data/campus_customs_new.db`, resolved
relative to the project root. The original `data/campus_customs.db` is left
untouched so the shop can be reset before a full run.

## Tools

Read tools:

| Tool | Reads | What it returns |
|------|-------|-----------------|
| `check_stock(sku, size)` | `inventory` | Units on hand for a SKU/size, with an `in_stock` flag. |
| `get_lease(lease_id)` | `leases`, `desk` | Monthly rent, `next_due`, and whether it's overdue vs. today. |
| `get_pricing(sku)` | `pricing` | `unit_cost`, `list_price`, and margin. |
| `get_open_invoices(vendor_id?)` | `invoices` | Open/unpaid invoices, optionally for one vendor. |
| `list_open_tickets()` | `tickets` | All open tickets on the board. |
| `get_ticket(ticket_id)` | `tickets` | One ticket with its linked fields. |
| `get_vendor(vendor_id)` | `vendors` | Vendor specialty and lead time in days. |
| `get_cash_balance(account)` | `cash_accounts` | Current balance of a cash account. |

Decision / draft tools (no money moves):

| Tool | Reads | What it does |
|------|-------|--------------|
| `record_discount(sku, qty, discount_pct)` | `pricing` | Quotes a bulk discount's unit price and margin (no write). |
| `prepare_payment(kind, ref_id, amount, reason)` | — | Drafts a payment for human approval; moves no money. |

Write tools (change the database):

| Tool | Writes | Rules enforced |
|------|--------|----------------|
| `pay(kind, ref_id, amount, approved_by, account)` | `cash_accounts`, `payments`, `invoices`/`leases` | Requires a human `approved_by`; refuses if cash is insufficient (no negative balance). |
| `restock(sku, size, qty, vendor_id)` | `inventory` | Refuses while the vendor has an open invoice (they won't ship unpaid). |
| `resolve_ticket(ticket_id, outcome)` | `tickets` | Marks a ticket resolved and records the outcome. |

The agent team reaches these tools with `pay` **filtered out** — agents only
`prepare_payment`; a human approves and pays via the backend route (Problem 7).

## Run

No need to run it for Problem 3. When you do connect it later:

```bash
pip install -r ../requirements.txt
python server.py
```
