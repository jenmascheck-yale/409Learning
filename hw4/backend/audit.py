"""Append-only audit trail of agent-loop activity (Problem 12).

Every agent run appends entries to output/audit_trail.json: the time, the tool
name, short args and result, and the stop reason. The file is never wiped between
runs — new entries are added to the existing list.
"""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
AUDIT_PATH = OUTPUT_DIR / "audit_trail.json"

MAX_LEN = 200  # keep args/result snippets short


def _short(value) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    text = " ".join(text.split())  # collapse whitespace
    return text if len(text) <= MAX_LEN else text[:MAX_LEN] + "…"


def _load() -> list:
    if AUDIT_PATH.exists():
        try:
            return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def append_events(events: list[dict]) -> None:
    """Append events to the audit trail without wiping what is already there."""
    if not events:
        return
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = _load()
    data.extend(events)
    AUDIT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
