"""Append-only audit trail of agent-loop activity (output/audit_trail.json).

Every agent run and every delegation appends entries — the time, which agent
acted, what it did (a tool call, a delegation, or its final answer), with short
args and results. The file is never wiped between runs; new entries are added to
the existing list so a full three-ticket run accumulates a complete record.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
AUDIT_PATH = OUTPUT_DIR / "audit_trail.json"

MAX_LEN = 300  # keep args/result snippets short


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short(value) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    text = " ".join(text.split())
    return text if len(text) <= MAX_LEN else text[:MAX_LEN] + "…"


def _load() -> list:
    if AUDIT_PATH.exists():
        try:
            return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def append_events(events: list[dict]) -> None:
    """Append events without wiping what is already there."""
    if not events:
        return
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = _load()
    data.extend(events)
    AUDIT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_delegation(caller: str, to_agent: str, task: str) -> None:
    append_events(
        [
            {
                "time": _now(),
                "agent": caller,
                "action": "delegate",
                "detail": f"-> {to_agent}: {_short(task)}",
                "result": "",
            }
        ]
    )


def record_run(agent_name: str, prompt: str, result) -> None:
    """Pull each tool call/return out of a finished run and append them, plus a
    final entry for the agent's answer."""
    events: list[dict] = []
    calls: dict[str, tuple[str, object]] = {}
    for msg in result.all_messages():
        for part in getattr(msg, "parts", []):
            kind = getattr(part, "part_kind", "")
            if kind == "tool-call":
                calls[getattr(part, "tool_call_id", "")] = (
                    getattr(part, "tool_name", "?"),
                    getattr(part, "args", None),
                )
            elif kind == "tool-return":
                name, args = calls.get(
                    getattr(part, "tool_call_id", ""),
                    (getattr(part, "tool_name", "?"), None),
                )
                events.append(
                    {
                        "time": _now(),
                        "agent": agent_name,
                        "action": "tool",
                        "detail": f"{name}({_short(args) if args is not None else ''})",
                        "result": _short(getattr(part, "content", "")),
                    }
                )
    events.append(
        {
            "time": _now(),
            "agent": agent_name,
            "action": "final",
            "detail": _short(prompt),
            "result": _short(getattr(result, "output", "")),
        }
    )
    append_events(events)
