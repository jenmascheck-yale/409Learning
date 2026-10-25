"""Campus Customs MCP server.

A FastMCP server that exposes the shop's tools over the working database
(data/campus_customs_new.db). Every agent in this homework calls these tools to
get and change real shop facts; the tools never invent data — they only read and
write rows in this one database.

Shop rules enforced here (not just in prompts):
  * `pay` requires a human approver (approved_by) and refuses if there is not
    enough cash — no negative balances.
  * `restock` refuses while the vendor still has an open (unpaid) invoice, because
    a vendor will not ship new product until it is paid.
  * `prepare_payment` never moves money; it only drafts a payment for a human to
    approve, which the backend approval route then runs through `pay`.
"""

from __future__ import annotations

import calendar
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# The server always talks to the WORKING COPY, never the untouched original.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"

mcp = FastMCP("campus-customs")


@contextmanager
def _db():
    """Open the working database; commit on success, always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _today(conn: sqlite3.Connection) -> str:
    """The shop's 'today' from the desk table."""
    row = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
    return row["date_today"] if row else ""


def _add_one_month(iso_date: str) -> str:
    """Advance an ISO date by one month (clamping the day), for rent next_due."""
    y, m, d = (int(x) for x in iso_date.split("-"))
    m += 1
    if m > 12:
        m, y = 1, y + 1
    d = min(d, calendar.monthrange(y, m)[1])
    return f"{y:04d}-{m:02d}-{d:02d}"


# --------------------------------------------------------------------------- #
# Read tools
# --------------------------------------------------------------------------- #

@mcp.tool()
def check_stock(sku: str, size: str) -> dict[str, Any]:
    """Return how many units of a SKU are in stock in a given size (table: inventory).

    Used for ticket 101 (customer wants CC-TEE-WHITE in size S) and ticket 103
    (20 CC-HOOD-NAVY in M) to see what is actually on hand. Returns the inventory
    row with an `in_stock` flag, or `found: false` when the SKU/size is unknown.
    """
    with _db() as conn:
        row = conn.execute(
            "SELECT sku, name, size, qty, location FROM inventory WHERE sku=? AND size=?",
            (sku, size),
        ).fetchone()
    if row is None:
        return {"found": False, "sku": sku, "size": size}
    return {
        "found": True,
        "sku": row["sku"],
        "name": row["name"],
        "size": row["size"],
        "qty": row["qty"],
        "location": row["location"],
        "in_stock": row["qty"] > 0,
    }


@mcp.tool()
def get_lease(lease_id: int) -> dict[str, Any]:
    """Return a lease: rent amount and next due date (table: leases).

    Used for ticket 102 (rent notice on lease 1) so Facilities/Accounting know the
    monthly rent and when it is due, compared against today's date.
    """
    with _db() as conn:
        today = _today(conn)
        row = conn.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due, notes "
            "FROM leases WHERE id=?",
            (lease_id,),
        ).fetchone()
    if row is None:
        return {"found": False, "lease_id": lease_id}
    return {
        "found": True,
        "id": row["id"],
        "space_name": row["space_name"],
        "landlord": row["landlord"],
        "monthly_rent": row["monthly_rent"],
        "next_due": row["next_due"],
        "overdue": row["next_due"] < today,
        "today": today,
        "notes": row["notes"],
    }


@mcp.tool()
def get_pricing(sku: str) -> dict[str, Any]:
    """Return unit cost, list price, and margin for a SKU (table: pricing).

    Used for ticket 103 (bulk hoodie discount) so Accounting can check the margin
    before agreeing to a discount.
    """
    with _db() as conn:
        row = conn.execute(
            "SELECT sku, unit_cost, list_price FROM pricing WHERE sku=?", (sku,)
        ).fetchone()
    if row is None:
        return {"found": False, "sku": sku}
    return {
        "found": True,
        "sku": row["sku"],
        "unit_cost": row["unit_cost"],
        "list_price": row["list_price"],
        "margin": round(row["list_price"] - row["unit_cost"], 2),
    }


@mcp.tool()
def get_open_invoices(vendor_id: int | None = None) -> dict[str, Any]:
    """Return open (unpaid) invoices, optionally for one vendor (table: invoices).

    Supports ticket 101: vendor 1 (Bulldog Print Co) has an open $840 invoice, and
    a vendor will not ship new product while an invoice is unpaid — so the team must
    see it before trying to restock the tee.
    """
    query = (
        "SELECT id, vendor_id, amount, due_date, status, description "
        "FROM invoices WHERE status='open'"
    )
    params: tuple[Any, ...] = ()
    if vendor_id is not None:
        query += " AND vendor_id=?"
        params = (vendor_id,)
    with _db() as conn:
        rows = conn.execute(query, params).fetchall()
    return {
        "count": len(rows),
        "invoices": [dict(r) for r in rows],
    }


@mcp.tool()
def list_open_tickets() -> dict[str, Any]:
    """Return all open tickets on the board (table: tickets).

    The Boss reads this to see what needs work (101, 102, 103).
    """
    with _db() as conn:
        rows = conn.execute("SELECT * FROM tickets WHERE status='open'").fetchall()
    return {"count": len(rows), "tickets": [dict(r) for r in rows]}


@mcp.tool()
def get_ticket(ticket_id: int) -> dict[str, Any]:
    """Return one ticket with all its linked fields (table: tickets)."""
    with _db() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    if row is None:
        return {"found": False, "ticket_id": ticket_id}
    return {"found": True, **dict(row)}


@mcp.tool()
def get_vendor(vendor_id: int) -> dict[str, Any]:
    """Return a vendor's specialty and lead time in days (table: vendors).

    Inventory uses this to pick who can restock a shortfall and how long it takes.
    """
    with _db() as conn:
        row = conn.execute(
            "SELECT id, name, specialty, lead_days FROM vendors WHERE id=?",
            (vendor_id,),
        ).fetchone()
    if row is None:
        return {"found": False, "vendor_id": vendor_id}
    return {"found": True, **dict(row)}


@mcp.tool()
def get_cash_balance(account: str = "checking") -> dict[str, Any]:
    """Return the current balance of a cash account (table: cash_accounts).

    Accounting checks this before preparing any payment, since the shop can never go
    negative and no new money comes in.
    """
    with _db() as conn:
        row = conn.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name=?", (account,)
        ).fetchone()
    if row is None:
        return {"found": False, "account": account}
    return {"found": True, "account": row["name"], "balance": row["balance"], "date": row["date"]}


# --------------------------------------------------------------------------- #
# Decision / draft tools (no money moves)
# --------------------------------------------------------------------------- #

@mcp.tool()
def record_discount(sku: str, qty: int, discount_pct: float) -> dict[str, Any]:
    """Quote a bulk discount and its margin without changing the catalog (table: pricing).

    Used for ticket 103: given a discount percent off list, this returns the
    discounted unit price and the total margin at that price so Accounting can
    decide whether the bulk deal still makes money. It does not write to the
    database — the decision is recorded on the ticket via `resolve_ticket`.
    """
    with _db() as conn:
        row = conn.execute(
            "SELECT unit_cost, list_price FROM pricing WHERE sku=?", (sku,)
        ).fetchone()
    if row is None:
        return {"found": False, "sku": sku}
    discounted_unit = round(row["list_price"] * (1 - discount_pct / 100), 2)
    unit_margin = round(discounted_unit - row["unit_cost"], 2)
    return {
        "found": True,
        "sku": sku,
        "qty": qty,
        "list_price": row["list_price"],
        "unit_cost": row["unit_cost"],
        "discount_pct": discount_pct,
        "discounted_unit_price": discounted_unit,
        "unit_margin": unit_margin,
        "total_margin": round(unit_margin * qty, 2),
        "profitable": unit_margin > 0,
    }


@mcp.tool()
def prepare_payment(kind: str, ref_id: int | None, amount: float, reason: str) -> dict[str, Any]:
    """Draft a payment for HUMAN APPROVAL — this never moves money.

    `kind` is one of 'invoice', 'rent', or 'purchase_order'. Agents call this to
    propose a payment; the backend approval route (Problem 7) is what actually runs
    `pay` after a human clicks approve. Returns a pending-approval record.
    """
    return {
        "status": "pending_human_approval",
        "kind": kind,
        "ref_id": ref_id,
        "amount": amount,
        "reason": reason,
        "note": "No money has moved. A human must approve this before `pay` runs it.",
    }


# --------------------------------------------------------------------------- #
# Money / inventory write tools (change the database)
# --------------------------------------------------------------------------- #

@mcp.tool()
def pay(
    kind: str,
    ref_id: int | None,
    amount: float,
    approved_by: str,
    account: str = "checking",
) -> dict[str, Any]:
    """Run an APPROVED payment: deduct cash and record it (tables: cash_accounts, payments, invoices/leases).

    Shop rules enforced here:
      * `approved_by` must be set (human approval) — refuses otherwise.
      * Refuses if the account does not hold enough cash (no negative balances).
    On success it deducts the cash, writes a payments row, and updates the related
    table: an 'invoice' is marked paid; 'rent' advances the lease's next_due by a
    month. `kind` may also be 'purchase_order' (ref_id = vendor id).
    """
    if not approved_by or not str(approved_by).strip():
        return {"paid": False, "reason": "Human approval required: approved_by is empty."}

    with _db() as conn:
        acct = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name=?", (account,)
        ).fetchone()
        if acct is None:
            return {"paid": False, "reason": f"No such account: {account}."}
        balance = acct["balance"]
        if amount > balance:
            return {
                "paid": False,
                "reason": f"Not enough cash: balance ${balance:.2f} < payment ${amount:.2f}.",
                "balance": balance,
            }

        paid_at = _today(conn)
        new_balance = round(balance - amount, 2)
        conn.execute(
            "UPDATE cash_accounts SET balance=?, date=? WHERE name=?",
            (new_balance, paid_at, account),
        )
        next_id = (conn.execute("SELECT COALESCE(MAX(id), 0) FROM payments").fetchone()[0]) + 1
        conn.execute(
            "INSERT INTO payments (id, kind, ref_id, amount, account, paid_at, approved_by) "
            "VALUES (?,?,?,?,?,?,?)",
            (next_id, kind, ref_id, amount, account, paid_at, approved_by),
        )

        updated = None
        if kind == "invoice" and ref_id is not None:
            conn.execute("UPDATE invoices SET status='paid' WHERE id=?", (ref_id,))
            updated = f"invoice {ref_id} marked paid"
        elif kind == "rent" and ref_id is not None:
            lease = conn.execute(
                "SELECT next_due FROM leases WHERE id=?", (ref_id,)
            ).fetchone()
            if lease:
                conn.execute(
                    "UPDATE leases SET next_due=? WHERE id=?",
                    (_add_one_month(lease["next_due"]), ref_id),
                )
                updated = f"lease {ref_id} next_due advanced one month"

    return {
        "paid": True,
        "payment_id": next_id,
        "kind": kind,
        "ref_id": ref_id,
        "amount": amount,
        "approved_by": approved_by,
        "new_balance": new_balance,
        "updated": updated,
    }


@mcp.tool()
def restock(sku: str, size: str, qty: int, vendor_id: int) -> dict[str, Any]:
    """Add restocked units to inventory, if the vendor is clear to ship (tables: invoices, inventory).

    Refuses when the vendor still has an open (unpaid) invoice, because a vendor
    will not ship new product until it is paid. On success it increases the on-hand
    quantity for that SKU/size. Use `pay` to clear the blocking invoice first, and
    `prepare_payment`/`pay` for the restock's own purchase-order cost.
    """
    with _db() as conn:
        open_inv = conn.execute(
            "SELECT id, amount FROM invoices WHERE status='open' AND vendor_id=?",
            (vendor_id,),
        ).fetchall()
        if open_inv:
            ids = ", ".join(str(r["id"]) for r in open_inv)
            return {
                "restocked": False,
                "reason": f"Vendor {vendor_id} has open invoice(s) {ids}; they will not ship until paid.",
            }
        row = conn.execute(
            "SELECT qty FROM inventory WHERE sku=? AND size=?", (sku, size)
        ).fetchone()
        if row is None:
            return {"restocked": False, "reason": f"No inventory row for {sku} size {size}."}
        new_qty = row["qty"] + qty
        conn.execute(
            "UPDATE inventory SET qty=? WHERE sku=? AND size=?", (new_qty, sku, size)
        )
    return {"restocked": True, "sku": sku, "size": size, "added": qty, "new_qty": new_qty}


@mcp.tool()
def resolve_ticket(ticket_id: int, outcome: str) -> dict[str, Any]:
    """Mark a ticket resolved and record its outcome (table: tickets).

    Sets status to 'resolved' and appends the outcome to the ticket's notes so the
    board and the resolved-tickets export show what happened.
    """
    with _db() as conn:
        row = conn.execute("SELECT notes FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if row is None:
            return {"resolved": False, "reason": f"No such ticket {ticket_id}."}
        notes = (row["notes"] or "").strip()
        notes = f"{notes} | RESOLVED: {outcome}" if notes else f"RESOLVED: {outcome}"
        conn.execute(
            "UPDATE tickets SET status='resolved', notes=? WHERE id=?", (notes, ticket_id)
        )
    return {"resolved": True, "ticket_id": ticket_id, "outcome": outcome}


if __name__ == "__main__":
    mcp.run()
