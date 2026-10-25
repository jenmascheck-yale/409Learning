# Campus Customs Agent Desk — Design Notes (Problem 8)

The dashboard (`frontend/`, React + Vite + TypeScript) is built to feel like a real
operations desk a shop manager would actually want to sit at: calm, collegiate, and
honest about what the agents are doing with the shop's money.

## Look and feel
- **Yale / Bulldog Blue**, consistent with the rest of Campus Customs: Yale Blue
  (`#00356B`) headers and primary actions, white cards on a soft cream background with a
  faint radial glow at the top so the page feels lit, not flat.
- **Garamond headings + Verdana body** — the same collegiate serif/sans pairing as the
  shop, so the desk reads as part of the brand, not a separate tool.
- Subtle motion only: ticket cards lift on hover, new agent events fade in, and a
  "live" badge pulses while a run is in progress — enough to feel alive, nothing noisy.

## Layout
- **Top bar**: the brand on the left; on the right, the **Checking balance as a hero
  card** and a Reset button. Money is always in view, because every decision the desk
  makes is ultimately about cash.
- **Left column — "Open board"**: the three tickets as a queue of cards, each with its
  id, subject, type, requester, and a status pill. Click one to select it (it highlights
  with a blue spine).
- **Right column — the work area**: the selected ticket's header with a big status pill
  and the **Run the agent team** button, then (as they appear) the approval card, the run
  summary, and the live agent-activity feed.
- Responsive: the two columns stack on a narrow screen and the top bar wraps.

## How each agent reads differently
Every agent speaks in its own color, so the multi-agent conversation is scannable at a
glance instead of a wall of text:
- **Boss** — Yale navy · **Inventory** — teal · **Accounting** — gold ·
  **Facilities** — purple · **Customer Service** — rose · **Human (you)** — deep navy.

Each event also carries an **action tag** — `delegates`, `tool`, `reply`, or
`human pay` — so you can see at a glance whether an agent handed work off, called a
database tool, gave its answer, or whether *you* moved money. The feed streams in every
1.5 seconds while the run is live.

## Resolved tickets and cash
- A ticket's status pill is **blue for open** and **green for resolved**; the moment a
  run finishes, the ticket card and header flip to **RESOLVED** green.
- After a run, a **Run summary** card shows the Boss's short account of what the team did.
- The **Checking balance** in the top bar is polled live and **visibly drops after an
  approved payment** — e.g. $3,400 → $1,000 once a $2,400 rent is approved — so the money
  consequence is immediate and obvious.

## The approval moment (the point of the whole desk)
When the agents prepare a payment, an amber **"Approval needed"** card appears with the
exact kind and amount and the line *"Agents cannot pay — you approve it."* You type your
name and click **Approve & pay**; only then does the balance move. This makes the core
safety rule visible in the UI: **agents prepare, humans approve.** After approval, a green
confirmation replaces the card.

## Why these choices help
- **Trust through transparency**: a manager sees the real tool calls and the honest
  "no money has moved" status, so they can believe the board.
- **Control over money**: the approval card puts a human in the loop by design, not by
  policy alone — the balance literally cannot change without a click.
- **Fast to read**: color-coded agent voices and action tags turn a long agent
  transcript into something a busy person can skim and act on.
