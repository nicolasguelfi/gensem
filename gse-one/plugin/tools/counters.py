#!/usr/bin/env python3
# @gse-tool counters 1.0
"""
GSE-One P15/P16 integrity-counter helper.

Deterministic arithmetic + persistence for the three scalar integrity
counters of `.gse/status.yaml` (whitelist below). Event DETECTION remains
conversational — the orchestrator recognizes the triggering event (Gate
accepted without modification, failed patch, ...) and invokes this tool;
that part is best-effort by nature (spec §P16, Meta-2). What this tool makes
deterministic: the arithmetic, the persistence (line-based, comment-
preserving), the `counters_last_write` timestamp, and the `health` backstop
that flags >= STALE_THRESHOLD activity transitions without any counter
write (i.e., "the guardrail looks switched off").

All outputs are status-wrapped JSON: {"status": "ok"|"error", ...}.
Exit code 0 on ok, 2 on error.

Usage:
  python3 counters.py get <name>
  python3 counters.py incr <name>
  python3 counters.py reset <name>
  python3 counters.py health

See docs: gse-one-implementation-design.md §5.18 — Execution tools
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_PATH = Path(".gse/status.yaml")

# Whitelist: the three P15/P16 integrity counters. sessions_without_progress
# is deliberately excluded — it is written every session (go/resume), so
# including it would blind the `health` backstop (counters_last_write would
# always look fresh).
COUNTERS = (
    "consecutive_acceptances",
    "pushback_dismissed",
    "fix_attempts_on_current_symptom",
)

LAST_WRITE_FIELD = "counters_last_write"
STALE_THRESHOLD = 5  # activity transitions without any counter write


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _fail(msg: str) -> dict:
    return {"status": "error", "error": msg}


def _counter_re(name: str) -> re.Pattern:
    # Top-level scalar with optional trailing comment, e.g.:
    #   consecutive_acceptances: 0             # primary counter — ...
    return re.compile(rf"^({re.escape(name)}:\s*)(\d+)(\s*#.*)?$")


def _read_text() -> str | None:
    if not STATUS_PATH.exists():
        return None
    return STATUS_PATH.read_text(encoding="utf-8")


def get_counter(name: str) -> dict:
    """Read a whitelisted counter from status.yaml (status-wrapped)."""
    if name not in COUNTERS:
        return _fail(f"unknown counter {name!r} — allowed: {list(COUNTERS)}")
    text = _read_text()
    if text is None:
        return _fail(f"{STATUS_PATH} not found — run /gse:hug or /gse:go first")
    pattern = _counter_re(name)
    for line in text.splitlines():
        m = pattern.match(line)
        if m:
            return {"status": "ok", "name": name, "value": int(m.group(2))}
    return _fail(
        f"field {name!r} not found in {STATUS_PATH} — schema drift? "
        "(authoritative template: plugin/templates/status.yaml)"
    )


def set_counter(name: str, value: int) -> dict:
    """Write a whitelisted counter, preserving comments and field order.

    Also stamps `counters_last_write` (appended at end of file if the field
    is missing — pre-v0.66 status.yaml files)."""
    if name not in COUNTERS:
        return _fail(f"unknown counter {name!r} — allowed: {list(COUNTERS)}")
    text = _read_text()
    if text is None:
        return _fail(f"{STATUS_PATH} not found — run /gse:hug or /gse:go first")

    pattern = _counter_re(name)
    lines = text.splitlines()
    replaced = False
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            lines[i] = f"{m.group(1)}{value}{m.group(3) or ''}"
            replaced = True
            break
    if not replaced:
        return _fail(
            f"field {name!r} not found in {STATUS_PATH} — schema drift? "
            "(authoritative template: plugin/templates/status.yaml)"
        )

    stamp = _now()
    lw_pattern = re.compile(
        rf'^({re.escape(LAST_WRITE_FIELD)}:\s*)("[^"]*"|\S*)(\s*#.*)?$'
    )
    stamped = False
    for i, line in enumerate(lines):
        m = lw_pattern.match(line)
        if m:
            lines[i] = f'{m.group(1)}"{stamp}"{m.group(3) or ""}'
            stamped = True
            break
    if not stamped:
        lines.append(
            f'{LAST_WRITE_FIELD}: "{stamp}"          '
            "# ISO 8601 — last integrity-counter write by counters.py"
        )

    STATUS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "status": "ok",
        "name": name,
        "value": value,
        LAST_WRITE_FIELD: stamp,
    }


def incr_counter(name: str) -> dict:
    current = get_counter(name)
    if current["status"] != "ok":
        return current
    return set_counter(name, current["value"] + 1)


def reset_counter(name: str) -> dict:
    # get first so a missing field fails before any write
    current = get_counter(name)
    if current["status"] != "ok":
        return current
    return set_counter(name, 0)


def counters_health() -> dict:
    """Deterministic backstop: count activity_history entries newer than
    counters_last_write. stale=true at >= STALE_THRESHOLD transitions
    without any integrity-counter write (status-wrapped)."""
    text = _read_text()
    if text is None:
        return _fail(f"{STATUS_PATH} not found — run /gse:hug or /gse:go first")

    last_write = ""
    m = re.search(
        rf'^{re.escape(LAST_WRITE_FIELD)}:\s*"?([^"\s#]*)"?', text, re.M
    )
    if m:
        last_write = m.group(1)

    # Extract the activity_history block (up to the next top-level key).
    transitions = 0
    block = re.search(
        r"^activity_history:.*?(?=^\S|\Z)", text, re.M | re.S
    )
    if block:
        stamps = re.findall(
            r'completed_at:\s*["\']?([0-9][0-9T:.Z+-]*)', block.group(0)
        )
        if last_write:
            transitions = sum(1 for s in stamps if s > last_write)
        else:
            transitions = len(stamps)

    return {
        "status": "ok",
        "stale": transitions >= STALE_THRESHOLD,
        "transitions_since_last_write": transitions,
        "threshold": STALE_THRESHOLD,
        "last_write": last_write or None,
    }


def main(argv: list[str]) -> int:
    usage = "usage: counters.py get|incr|reset <name> | counters.py health"
    if not argv:
        print(json.dumps(_fail(usage)))
        return 2
    cmd = argv[0]
    if cmd == "health":
        result = counters_health()
    elif cmd in ("get", "incr", "reset"):
        if len(argv) != 2:
            result = _fail(usage)
        else:
            fn = {
                "get": get_counter,
                "incr": incr_counter,
                "reset": reset_counter,
            }[cmd]
            result = fn(argv[1])
    else:
        result = _fail(f"unknown subcommand {cmd!r} — {usage}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") == "ok" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
