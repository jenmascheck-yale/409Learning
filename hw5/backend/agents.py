"""The Campus Customs agent team (PydanticAI), with full connectivity.

Five agents — Boss, Inventory, Accounting, Facilities, Customer Service — each
loads its own prompt from prompts/, talks to gpt-6-luna through Portkey, and
shares ONE MCP server (mcp_server/server.py over data/campus_customs_new.db) for
all shop facts. Every agent has a `delegate` tool so any agent can hand work to
any other agent. The `pay` tool is filtered out of the team: agents only prepare
payments; a human approves and pays via the backend route (Problem 7).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.usage import RunUsage, UsageLimits

import audit
import llm
from models import TeamDeps

BACKEND_DIR = Path(__file__).resolve().parent
HW5_DIR = BACKEND_DIR.parent
PROMPTS_DIR = BACKEND_DIR / "prompts"
VENV_PY = HW5_DIR / ".venv" / "Scripts" / "python.exe"
SERVER_PY = HW5_DIR / "mcp_server" / "server.py"

AGENT_NAMES = ["boss", "inventory", "accounting", "facilities", "customer_service"]

# Safety limits that keep the multi-agent loop (and token use) bounded. The usage
# object is shared across the whole ticket (boss + every delegated sub-run), so
# REQUEST_LIMIT is really a per-ticket ceiling on total model requests.
REQUEST_LIMIT = 30  # total model requests allowed per ticket
MAX_DEPTH = 2       # how deep delegation may nest (boss -> specialist -> one hand-off)

# Tools the agents may never call directly. `pay` moves real money and requires a
# human approver, so it is reachable only through the backend approval route.
BLOCKED_TOOLS = {"pay"}


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def make_mcp_server() -> MCPToolset:
    """One shared MCP server connection (stdio) for the whole team."""
    transport = StdioTransport(
        command=str(VENV_PY), args=[str(SERVER_PY)], cwd=str(HW5_DIR)
    )
    return MCPToolset(transport)


def _agent_view(server: MCPToolset) -> MCPToolset:
    """The team's view of the MCP server, with blocked tools (pay) hidden."""
    return server.filtered(lambda ctx, tool_def: tool_def.name not in BLOCKED_TOOLS)


def build_team() -> tuple[dict[str, Agent], MCPToolset]:
    """Build all five agents (sharing one model) and wire full-connectivity delegation."""
    model = llm.build_model()
    team: dict[str, Agent] = {
        name: Agent(model, name=name, system_prompt=_load_prompt(name), deps_type=TeamDeps)
        for name in AGENT_NAMES
    }
    for name, agent in team.items():
        _register_delegate(agent, name, team)
    server = make_mcp_server()
    return team, server


async def run_agent(
    agent: Agent, prompt: str, deps: TeamDeps, view: MCPToolset, usage=None
):
    """Run one agent against the shared MCP view, then append its run to the audit."""
    result = await agent.run(
        prompt,
        deps=deps,
        toolsets=[view],
        usage=usage,
        usage_limits=UsageLimits(request_limit=REQUEST_LIMIT),
    )
    audit.record_run(agent.name, prompt, result)
    return result


# Set when a run starts, so the delegate tool can reach the team and the MCP view.
_TEAM: dict[str, Agent] = {}
_VIEW: MCPToolset | None = None


def _register_delegate(agent: Agent, caller: str, team: dict[str, Agent]) -> None:
    others = [n for n in AGENT_NAMES if n != caller]

    @agent.tool
    async def delegate(ctx: RunContext[TeamDeps], to_agent: str, task: str) -> str:
        """Hand a task to another agent and return their answer.

        `to_agent` must be one of: boss, inventory, accounting, facilities,
        customer_service. Use this when the work needs another specialist.
        """
        target = to_agent.strip().lower().replace(" ", "_")
        if target not in _TEAM or target == caller:
            return f"Cannot delegate to '{to_agent}'. Valid teammates: {', '.join(others)}."
        # Full connectivity: any agent may delegate to any other (including the boss).
        # Loops are bounded by the depth cap below, not by blocking any path.
        if ctx.deps.depth >= MAX_DEPTH:
            return "Delegation depth limit reached; answer with what you already have."
        audit.record_delegation(caller, target, task)
        child_deps = dataclasses.replace(ctx.deps, depth=ctx.deps.depth + 1)
        try:
            result = await run_agent(_TEAM[target], task, child_deps, _VIEW, usage=ctx.usage)
        except UsageLimitExceeded:
            return f"{target} could not finish within the request budget; proceed with what you have."
        return result.output


async def run_ticket(ticket_id: int, approver: str | None = None) -> str:
    """Resolve one open ticket by running the Boss, who delegates as needed."""
    global _TEAM, _VIEW
    team, server = build_team()
    _TEAM = team
    deps = TeamDeps(ticket_id=ticket_id, approver=approver)
    usage = RunUsage()  # one shared budget across the boss and every delegated sub-run

    prompt = (
        f"Work open ticket {ticket_id}. Read it first, decide which specialist(s) to "
        "call, delegate to them, and make the final call. Agents only PREPARE payments "
        "for human approval — never pay. When the work is done (and any payment is "
        "prepared for a human), resolve the ticket with a clear outcome and give a short "
        "summary of what each agent did."
    )
    async with server:
        _VIEW = _agent_view(server)
        try:
            result = await run_agent(team["boss"], prompt, deps, _VIEW, usage=usage)
            return result.output
        except UsageLimitExceeded:
            return (
                f"Ticket {ticket_id} hit the per-ticket request budget "
                f"({REQUEST_LIMIT}) before the boss finished. See output/audit_trail.json "
                "for what the team completed."
            )
