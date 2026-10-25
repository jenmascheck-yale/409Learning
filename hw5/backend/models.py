"""Data types for the Campus Customs agent team.

`TeamDeps` is the shared dependency object passed into every agent run (who the
work is for, the human approver, and the delegation depth). The pydantic models
describe the structured shapes the agents and tools pass around so the board and
the audit trail stay consistent.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass
class TeamDeps:
    """Context carried through a ticket run and into every delegated sub-run."""

    ticket_id: int | None = None
    # The human who approved payments for this run. Agents never pay; this is only
    # filled by the backend approval route (Problem 7). Left None during agent work.
    approver: str | None = None
    # Guards against delegation loops under full connectivity.
    depth: int = 0


class PreparedPayment(BaseModel):
    """A payment an agent drafted for a human to approve — no money has moved."""

    kind: str = Field(description="invoice | rent | purchase_order")
    ref_id: int | None = Field(default=None, description="invoice id, lease id, or vendor id")
    amount: float
    reason: str
    status: str = "pending_human_approval"


class DiscountQuote(BaseModel):
    """Accounting's margin check for a bulk-discount request (ticket 103)."""

    sku: str
    qty: int
    discount_pct: float
    discounted_unit_price: float
    unit_margin: float
    total_margin: float
    profitable: bool


class TicketOutcome(BaseModel):
    """The final result recorded when a ticket is resolved."""

    ticket_id: int
    status: str = "resolved"
    summary: str
    agents_involved: list[str] = Field(default_factory=list)
    human_approvals: list[str] = Field(default_factory=list)


class AuditEntry(BaseModel):
    """One line in output/audit_trail.json."""

    time: str
    agent: str
    action: str = Field(description="delegate | tool | final")
    detail: str = ""
    result: str = ""
