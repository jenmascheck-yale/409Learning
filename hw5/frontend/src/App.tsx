import { useEffect, useMemo, useRef, useState } from "react";
import { api, EventRow, RunStatus, Ticket } from "./api";

const AGENT_LABEL: Record<string, string> = {
  boss: "Boss",
  inventory: "Inventory",
  accounting: "Accounting",
  facilities: "Facilities",
  customer_service: "Customer Service",
  human: "Human (you)",
};

const TICKET_TYPE_LABEL: Record<string, string> = {
  customer_order: "Customer order",
  rent_notice: "Rent notice",
  price_override: "Discount request",
};

// Pull a prepared-payment proposal out of the event stream so the human can
// approve it. Parsed field-by-field so a truncated audit line still works.
function parsePrepared(events: EventRow[]) {
  for (let i = events.length - 1; i >= 0; i--) {
    const e = events[i];
    if (e.action === "tool" && e.detail.startsWith("prepare_payment(")) {
      const kind = e.detail.match(/"kind":\s*"([^"]+)"/)?.[1];
      const refRaw = e.detail.match(/"ref_id":\s*(\d+|null)/)?.[1];
      const amount = e.detail.match(/"amount":\s*([\d.]+)/)?.[1];
      if (kind && amount) {
        return {
          kind,
          ref_id: refRaw && refRaw !== "null" ? Number(refRaw) : null,
          amount: Number(amount),
        };
      }
    }
  }
  return null;
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [cash, setCash] = useState<number | null>(null);
  const [events, setEvents] = useState<EventRow[]>([]);
  const [run, setRun] = useState<RunStatus>({ ticket_id: null, status: "idle", summary: null, error: null });
  const [approver, setApprover] = useState("Desk Manager");
  const [approveNote, setApproveNote] = useState<string | null>(null);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | null>(null);
  // Baseline into the append-only audit trail so the feed shows only THIS run.
  const sinceRef = useRef(0);

  const selected = tickets.find((t) => t.id === selectedId) || null;
  const running = run.status === "running";
  const prepared = useMemo(() => parsePrepared(events), [events]);
  const paidAlready = events.some((e) => e.action === "approve_pay");

  async function loadBase() {
    try {
      const [ts, c] = await Promise.all([api.tickets(), api.cash()]);
      setTickets(ts);
      setCash(c.balance);
    } catch (e: any) {
      setError("Cannot reach the backend on http://localhost:8000 — is it running? " + e.message);
    }
  }

  useEffect(() => {
    loadBase();
  }, []);

  // Poll events + status + cash while a run is in progress.
  useEffect(() => {
    if (!running) {
      if (timer.current) window.clearInterval(timer.current);
      return;
    }
    timer.current = window.setInterval(async () => {
      try {
        const [ev, rs, c] = await Promise.all([api.events(sinceRef.current), api.runStatus(), api.cash()]);
        setEvents(ev.events);
        setRun(rs);
        setCash(c.balance);
        if (rs.status !== "running") {
          const ts = await api.tickets();
          setTickets(ts);
        }
      } catch {
        /* keep polling */
      }
    }, 1500);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [running]);

  async function startRun() {
    if (selectedId == null) return;
    setError(null);
    setApproveNote(null);
    setApproved(false);
    setEvents([]);
    try {
      // Only show events appended from here on, not the whole historical trail.
      const base = await api.events();
      sinceRef.current = base.count;
      await api.run(selectedId);
      setRun({ ticket_id: selectedId, status: "running", summary: null, error: null });
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function approvePayment() {
    if (!prepared) return;
    setError(null);
    try {
      const res = await api.approve({
        kind: prepared.kind,
        ref_id: prepared.ref_id,
        amount: prepared.amount,
        approved_by: approver || "Desk Manager",
      });
      setCash(res.new_balance);
      setApproved(true);
      setApproveNote(`Approved — $${prepared.amount.toFixed(2)} paid. New balance $${res.new_balance.toFixed(2)}.`);
      const ev = await api.events(sinceRef.current);
      setEvents(ev.events);
    } catch (e: any) {
      setError("Approval refused: " + e.message);
    }
  }

  async function resetBoard() {
    setError(null);
    try {
      const r = await api.reset();
      setCash(r.checking_balance);
      setEvents([]);
      sinceRef.current = 0;
      setRun({ ticket_id: null, status: "idle", summary: null, error: null });
      setApproveNote(null);
      setApproved(false);
      await loadBase();
    } catch (e: any) {
      setError(e.message);
    }
  }

  const ticketEvents = events; // the audit trail is per-run (cleared on a fresh run)

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <h1>Campus Customs</h1>
          <span className="sub">Multi-Agent Operations Desk</span>
        </div>
        <div className="top-right">
          <div className="cash-card" title="Checking balance">
            <span className="cash-label">Checking</span>
            <span className="cash-value">{cash == null ? "—" : `$${cash.toLocaleString()}`}</span>
          </div>
          <button className="ghost" onClick={resetBoard} disabled={running}>↺ Reset board</button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <div className="layout">
        {/* LEFT: ticket queue */}
        <aside className="queue">
          <h2 className="col-title">Open board</h2>
          {tickets.map((t) => (
            <button
              key={t.id}
              className={`ticket ${selectedId === t.id ? "active" : ""}`}
              onClick={() => setSelectedId(t.id)}
            >
              <div className="ticket-top">
                <span className="ticket-id">#{t.id}</span>
                <span className={`status ${t.status}`}>{t.status}</span>
              </div>
              <div className="ticket-subject">{t.subject}</div>
              <div className="ticket-meta">
                {TICKET_TYPE_LABEL[t.type] || t.type} · {t.requester}
              </div>
            </button>
          ))}
        </aside>

        {/* CENTER: the work */}
        <main className="work">
          {!selected ? (
            <div className="empty">Pick a ticket from the board to begin.</div>
          ) : (
            <>
              <div className="work-head">
                <div>
                  <h2>#{selected.id} — {selected.subject}</h2>
                  <p className="work-meta">
                    {TICKET_TYPE_LABEL[selected.type] || selected.type} · {selected.requester}
                    {selected.sku ? ` · ${selected.sku}${selected.size ? " / " + selected.size : ""}` : ""}
                    {selected.qty ? ` · qty ${selected.qty}` : ""}
                  </p>
                </div>
                <div className="work-actions">
                  <span className={`status big ${selected.status}`}>{selected.status}</span>
                  <button className="primary" onClick={startRun} disabled={running}>
                    {running ? "Agents working…" : "▶ Run the agent team"}
                  </button>
                </div>
              </div>

              {/* Approval card */}
              {prepared && !paidAlready && !approved && (
                <div className="approve-card">
                  <h3>Approval needed</h3>
                  <p>
                    The team prepared a <strong>{prepared.kind}</strong> payment of{" "}
                    <strong>${prepared.amount.toLocaleString()}</strong>
                    {prepared.ref_id != null ? ` (ref ${prepared.ref_id})` : ""}. Agents cannot pay —
                    you approve it.
                  </p>
                  <div className="approve-row">
                    <label>
                      Approver
                      <input value={approver} onChange={(e) => setApprover(e.target.value)} />
                    </label>
                    <button className="approve-btn" onClick={approvePayment}>✓ Approve &amp; pay</button>
                  </div>
                </div>
              )}
              {approveNote && <div className="approve-done">{approveNote}</div>}

              {/* Summary */}
              {run.status === "done" && run.summary && (
                <div className="summary-card">
                  <h3>Run summary</h3>
                  <p>{run.summary}</p>
                </div>
              )}
              {run.status === "error" && (
                <div className="error-banner">Run error: {run.error}</div>
              )}

              {/* Agent activity feed */}
              <div className="feed">
                <h3 className="feed-title">
                  Agent activity {running && <span className="pulse">live</span>}
                </h3>
                {ticketEvents.length === 0 && !running && (
                  <p className="feed-empty">No activity yet — run the team to watch the agents work.</p>
                )}
                <ul className="timeline">
                  {ticketEvents.map((e, i) => (
                    <li key={i} className={`event agent-${e.agent}`}>
                      <span className={`badge agent-${e.agent}`}>{AGENT_LABEL[e.agent] || e.agent}</span>
                      <div className="event-body">
                        <div className="event-action">
                          {e.action === "delegate" && <span className="tag delegate">delegates</span>}
                          {e.action === "tool" && <span className="tag tool">tool</span>}
                          {e.action === "final" && <span className="tag final">reply</span>}
                          {e.action === "approve_pay" && <span className="tag pay">human pay</span>}
                          <span className="event-detail">{e.detail}</span>
                        </div>
                        {e.result && <div className="event-result">{e.result}</div>}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </main>
      </div>
      <footer className="foot">Campus Customs Multi-Agent Operations · agents prepare, humans approve</footer>
    </div>
  );
}
