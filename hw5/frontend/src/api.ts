// Thin client for the Campus Customs desk backend (FastAPI on port 8000).
const BASE = "http://localhost:8000";

export type Ticket = {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku?: string | null;
  size?: string | null;
  qty?: number | null;
  status: string;
  notes?: string | null;
};

export type EventRow = {
  time: string;
  agent: string;
  action: string; // delegate | tool | final | approve_pay
  detail: string;
  result: string;
};

export type RunStatus = {
  ticket_id: number | null;
  status: string; // idle | running | done | error
  summary: string | null;
  error: string | null;
};

async function j<T>(res: Response): Promise<T> {
  const data = await res.json();
  if (!res.ok) throw new Error((data && data.detail) || res.statusText);
  return data as T;
}

export const api = {
  tickets: () =>
    fetch(`${BASE}/tickets`).then((r) => j<{ tickets: Ticket[] }>(r)).then((d) => d.tickets),
  cash: (account = "checking") =>
    fetch(`${BASE}/cash?account=${account}`).then((r) =>
      j<{ account: string; balance: number; date: string }>(r)
    ),
  events: (since = 0) =>
    fetch(`${BASE}/events?since=${since}`).then((r) =>
      j<{ count: number; events: EventRow[] }>(r)
    ),
  runStatus: () => fetch(`${BASE}/run-status`).then((r) => j<RunStatus>(r)),
  run: (id: number) =>
    fetch(`${BASE}/tickets/${id}/run`, { method: "POST" }).then((r) =>
      j<{ status: string; ticket_id: number }>(r)
    ),
  approve: (body: {
    kind: string;
    ref_id: number | null;
    amount: number;
    approved_by: string;
    account?: string;
  }) =>
    fetch(`${BASE}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => j<any>(r)),
  reset: () => fetch(`${BASE}/reset`, { method: "POST" }).then((r) => j<any>(r)),
};
