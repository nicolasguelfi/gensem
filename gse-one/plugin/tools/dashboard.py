#!/usr/bin/env python3
# @gse-tool dashboard 0.17.0
"""
GSE-One Dashboard Generator — Generates docs/dashboard.html from .gse/ state files.

Usage (via registry):
    python3 "$(cat ~/.gse-one)/tools/dashboard.py"              # Generate once (CDN mode)
    python3 "$(cat ~/.gse-one)/tools/dashboard.py" --watch      # Live updates
    python3 "$(cat ~/.gse-one)/tools/dashboard.py" --no-cdn     # Offline mode
    python3 "$(cat ~/.gse-one)/tools/dashboard.py" --output X   # Custom output path

The dashboard is a single self-contained HTML file showing:
  - Project state (sprint, phase, TASK kanban, complexity budget)
  - Workflow progress (from .gse/plan.yaml — activities completed/active/pending)
  - Coherence alerts (from .gse/plan.yaml — non-blocking plan health warnings)
  - Health radar (8 dimensions, trends)
  - REQS → TESTS traceability
  - Quality (review findings, regressions, AI integrity)
  - Methodology checklist (lifecycle phases completed)
"""

import argparse
import html
import json
import os
import re
import subprocess
import sys
import time
import traceback as tb_module
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def find_project_root():
    """Find the project root by looking for .gse/ directory."""
    current = Path.cwd()
    # If running from .gse/, go up one level
    if current.name == ".gse":
        return current.parent
    # If .gse/ exists here, this is the root
    if (current / ".gse").is_dir():
        return current
    # Walk up
    for parent in current.parents:
        if (parent / ".gse").is_dir():
            return parent
    return current


ROOT = find_project_root()
GSE_DIR = ROOT / ".gse"
DOCS_DIR = ROOT / "docs"
DEFAULT_OUTPUT = DOCS_DIR / "dashboard.html"
ERROR_MARKER = GSE_DIR / ".dashboard-error.yaml"


# ---------------------------------------------------------------------------
# Debounce config + error-marker helpers (AMÉL-02 / spec §7 policy)
# ---------------------------------------------------------------------------

def _read_debounce_seconds(default=5.0):
    """Read dashboard.regen_debounce_seconds from .gse/config.yaml.
    Falls back to `default` if the file, section, or field is absent/malformed.
    """
    cfg = GSE_DIR / "config.yaml"
    if not cfg.is_file():
        return default
    try:
        text = cfg.read_text(encoding="utf-8")
        in_dashboard = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("dashboard:"):
                in_dashboard = True
                continue
            if in_dashboard:
                if stripped and not line.startswith((" ", "\t")):
                    # Left the dashboard: section
                    in_dashboard = False
                    continue
                m = re.match(r"regen_debounce_seconds:\s*([\d.]+)", stripped)
                if m:
                    return float(m.group(1))
    except Exception:
        pass
    return default


def _write_error_marker(message, traceback_str=None):
    """Write .gse/.dashboard-error.yaml with timestamp and error details.
    Best-effort — swallow any I/O error since we're already in a failure path.
    """
    try:
        if traceback_str is None:
            traceback_str = tb_module.format_exc()
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        content = (
            f"timestamp: \"{ts}\"\n"
            f"message: {json.dumps(str(message))}\n"
            f"traceback: |\n"
        )
        for line in str(traceback_str).splitlines():
            content += f"  {line}\n"
        ERROR_MARKER.parent.mkdir(parents=True, exist_ok=True)
        ERROR_MARKER.write_text(content, encoding="utf-8")
    except Exception:
        pass  # best-effort — never raise from error handler


def _read_and_clear_error_marker():
    """Return (timestamp, message) if an error marker exists, else (None, None).
    Deletes the marker on successful read so the banner does not persist."""
    if not ERROR_MARKER.is_file():
        return None, None
    try:
        text = ERROR_MARKER.read_text(encoding="utf-8")
        ts_m = re.search(r'timestamp:\s*"?([^"\n]+)"?', text)
        # message may be JSON-escaped (quoted string on single line) or plain
        msg_m = re.search(r'message:\s*(.+?)$', text, re.MULTILINE)
        ts = ts_m.group(1).strip() if ts_m else "unknown time"
        msg_raw = msg_m.group(1).strip() if msg_m else "unknown error"
        # Try to decode as JSON string (quoted), else keep raw
        try:
            msg = json.loads(msg_raw) if msg_raw.startswith('"') else msg_raw
        except Exception:
            msg = msg_raw
        ERROR_MARKER.unlink()
        return ts, msg
    except Exception:
        return None, None


# ---------------------------------------------------------------------------
# YAML parser (minimal, no dependencies)
# ---------------------------------------------------------------------------

def parse_yaml_simple(filepath):
    """Parse a simple YAML file into a dict with dotted keys for nested values.

    Handles up to 2 levels of nesting using indentation detection.
    Nested keys are stored as 'parent.child' in a flat dict.
    Example: 'dimensions:\\n  it_expertise: beginner' → {'dimensions.it_expertise': 'beginner'}
    Top-level keys are also stored without prefix for backward compatibility.
    """
    if not filepath.exists():
        return {}
    try:
        content = filepath.read_text(encoding="utf-8")
        # Strip YAML frontmatter markers if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[1]
            elif len(parts) == 2:
                content = parts[1]
        result = {}
        parent_key = None
        parent_indent = -1
        for line in content.split("\n"):
            if not line.strip() or line.strip().startswith("#"):
                continue
            # Measure indentation
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            # If indentation dropped back to top level, reset parent
            if indent == 0:
                parent_key = None
                parent_indent = -1
            # Key with no value → start of nested section
            match_parent = re.match(r'^(\w[\w.-]*)\s*:\s*$', stripped)
            if match_parent:
                key = match_parent.group(1)
                if indent == 0:
                    parent_key = key
                    parent_indent = indent
                elif parent_key and indent > parent_indent:
                    # Sub-parent (2nd level nesting) — use dotted key as new parent
                    parent_key = f"{parent_key}.{key}"
                continue
            # Key: value pair
            match_kv = re.match(r'^(\w[\w.-]*)\s*:\s*(.+)$', stripped)
            if match_kv:
                key = match_kv.group(1)
                val = match_kv.group(2).strip().strip('"').strip("'")
                # Type coercion
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                elif val.lower() == "null" or val == "~":
                    val = None
                else:
                    try:
                        val = int(val)
                    except ValueError:
                        try:
                            val = float(val)
                        except ValueError:
                            pass
                # Store with dotted prefix if nested
                if parent_key and indent > parent_indent:
                    result[f"{parent_key}.{key}"] = val
                else:
                    # Top-level key — also reset parent
                    result[key] = val
                    parent_key = None
                    parent_indent = -1
        return result
    except Exception:
        return {}


def parse_plan_yaml(filepath):
    """Extract dashboard-relevant fields from .gse/plan.yaml.

    Returns a dict with: status, mode, goal, budget (dict),
    workflow_active, workflow_expected (list), workflow_completed (list of activity names),
    workflow_pending (list), workflow_skipped (list of {activity, reason}), alerts (list).

    Returns None if the file does not exist. Uses targeted regex rather than
    a full YAML parser because plan.yaml mixes scalars, inline lists, and
    nested lists of dicts — more than parse_yaml_simple can handle.
    """
    if not filepath.exists():
        return None
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    plan = {
        "status": None, "mode": None, "goal": None,
        "budget": {"total": None, "consumed": None, "remaining": None},
        "workflow_active": None,
        "workflow_expected": [],
        "workflow_completed": [],
        "workflow_pending": [],
        "workflow_skipped": [],
        "alerts": [],
    }

    def _scalar(key):
        m = re.search(rf'^{key}\s*:\s*(.+?)\s*$', content, re.MULTILINE)
        if not m:
            return None
        val = m.group(1).strip().strip('"').strip("'")
        return val if val and val != "null" else None

    plan["status"] = _scalar("status")
    plan["mode"] = _scalar("mode")
    plan["goal"] = _scalar("goal")

    def _inline_list(key):
        m = re.search(rf'^{key}\s*:\s*\[(.*?)\]\s*$', content, re.MULTILINE)
        if not m:
            return []
        return [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]

    plan["workflow_expected"] = _inline_list("  expected")
    plan["workflow_pending"] = _inline_list("  pending")

    m_active = re.search(r'^  active\s*:\s*(.+?)\s*$', content, re.MULTILINE)
    if m_active:
        val = m_active.group(1).strip().strip('"').strip("'")
        plan["workflow_active"] = val if val and val != "null" else None

    def _section_block(section_header):
        m = re.search(
            rf'^  {section_header}\s*:\s*\n((?:    .+\n?)+)',
            content, re.MULTILINE)
        return m.group(1) if m else ""

    completed_block = _section_block("completed")
    plan["workflow_completed"] = re.findall(r'-\s*activity\s*:\s*(\S+)', completed_block)

    skipped_block = _section_block("skipped")
    for m in re.finditer(r'-\s*activity\s*:\s*(\S+)\s*\n\s*reason\s*:\s*(.+?)\s*(?=\n\s*-|\n\S|\Z)',
                         skipped_block, re.DOTALL):
        plan["workflow_skipped"].append({
            "activity": m.group(1).strip(),
            "reason": m.group(2).strip().strip('"').strip("'"),
        })

    for field in ("total", "consumed", "remaining"):
        m = re.search(rf'^  {field}\s*:\s*(\d+(?:\.\d+)?)\s*$', content, re.MULTILINE)
        if m:
            try:
                plan["budget"][field] = float(m.group(1)) if "." in m.group(1) else int(m.group(1))
            except ValueError:
                pass

    alerts_block = _section_block("alerts")
    if alerts_block.strip():
        for m in re.finditer(r'-\s*(\S+)', alerts_block):
            plan["alerts"].append(m.group(1).strip().strip('"').strip("'"))

    return plan


def count_tasks_by_status(filepath):
    """Count TASKs by status from backlog.yaml."""
    if not filepath.exists():
        return {}
    content = filepath.read_text(encoding="utf-8")
    statuses = re.findall(r'status:\s*(\S+)', content)
    counts = {}
    for s in statuses:
        s = s.strip('"').strip("'")
        counts[s] = counts.get(s, 0) + 1
    return counts


def count_reqs(sprint_dir):
    """Count REQ- entries in reqs.md."""
    reqs_file = sprint_dir / "reqs.md"
    if not reqs_file.exists():
        return 0, 0  # total, approved
    content = reqs_file.read_text(encoding="utf-8")
    total = len(re.findall(r'id:\s*REQ-', content))
    approved = 1 if "status: approved" in content else 0
    return total, approved


def count_tests(sprint_dir):
    """Count TST- entries and results from test reports."""
    strategy = sprint_dir / "test-strategy.md"
    has_strategy = strategy.exists()
    reports_dir = sprint_dir / "test-reports"
    report_count = sum(1 for _ in reports_dir.glob("*")) if reports_dir.exists() else 0
    return has_strategy, report_count


def count_review_findings(sprint_dir):
    """Count review findings by severity."""
    review_file = sprint_dir / "review.md"
    if not review_file.exists():
        return {}
    content = review_file.read_text(encoding="utf-8")
    findings = {}
    for sev in ["HIGH", "MEDIUM", "LOW"]:
        count = len(re.findall(rf'severity:\s*{sev}', content))
        if count > 0:
            findings[sev] = count
    ai_integrity = len(re.findall(r'\[AI-INTEGRITY\]', content))
    if ai_integrity > 0:
        findings["AI-INTEGRITY"] = ai_integrity
    return findings


def get_git_info():
    """Get basic git info."""
    info = {"branches": 0, "last_commit": "unknown", "tags": []}
    try:
        result = subprocess.run(
            ["git", "branch", "--list"], capture_output=True, text=True, cwd=str(ROOT)
        )
        if result.returncode == 0:
            info["branches"] = len([b for b in result.stdout.strip().split("\n") if b.strip()])

        result = subprocess.run(
            ["git", "log", "--oneline", "-1"], capture_output=True, text=True, cwd=str(ROOT)
        )
        if result.returncode == 0 and result.stdout.strip():
            info["last_commit"] = result.stdout.strip()

        result = subprocess.run(
            ["git", "tag", "--list", "--sort=-creatordate"], capture_output=True, text=True, cwd=str(ROOT)
        )
        if result.returncode == 0:
            info["tags"] = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()][:5]
    except FileNotFoundError:
        pass
    return info


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def collect_data():
    """Collect all project data for the dashboard."""
    data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_root": str(ROOT),
    }

    # Config — try dotted keys (project.name) and flat keys (name) for compatibility
    config = parse_yaml_simple(GSE_DIR / "config.yaml")
    data["project_name"] = (config.get("project.name")
                            or config.get("name")
                            or config.get("project")
                            or "Unknown Project")
    data["domain"] = (config.get("project.domain")
                      or config.get("domain")
                      or "unknown")
    data["mode"] = config.get("mode", config.get("lifecycle.mode", "full"))

    # Status
    status = parse_yaml_simple(GSE_DIR / "status.yaml")
    data["current_sprint"] = status.get("current_sprint", 0)
    data["current_phase"] = status.get("current_phase", "LC00")
    data["last_activity"] = status.get("last_activity", "none")
    data["last_activity_timestamp"] = status.get("last_activity_timestamp", "never")

    # Health scores (may be at top level or under a 'health:' parent)
    data["health"] = {}
    for dim in ["test_pass_rate", "review_findings", "git_hygiene", "design_debt",
                 "complexity_ratio", "requirements_coverage", "ai_integrity", "delivery_velocity"]:
        val = status.get(f"health.{dim}", status.get(dim))
        if val is not None:
            data["health"][dim] = val

    # Profile — use dotted keys from nested YAML (dimensions.it_expertise, user.name)
    profile = parse_yaml_simple(GSE_DIR / "profile.yaml")
    data["user_name"] = (profile.get("user.name")
                         or profile.get("name")
                         or "Unknown")
    data["it_expertise"] = profile.get("dimensions.it_expertise") or "unknown"
    data["decision_involvement"] = (profile.get("dimensions.decision_involvement")
                                    or "collaborative")

    # Living sprint plan (.gse/plan.yaml) — optional, present in Full/Lightweight modes
    data["plan"] = parse_plan_yaml(GSE_DIR / "plan.yaml")

    # Backlog — cumulative: active backlog + archive
    data["task_counts"] = count_tasks_by_status(GSE_DIR / "backlog.yaml")
    archive_counts = count_tasks_by_status(GSE_DIR / "backlog-archive.yaml")
    for s, c in archive_counts.items():
        data["task_counts"][s] = data["task_counts"].get(s, 0) + c
    total_tasks = sum(data["task_counts"].values())
    done_tasks = data["task_counts"].get("done", 0) + data["task_counts"].get("delivered", 0)
    data["total_tasks"] = total_tasks
    data["done_tasks"] = done_tasks
    data["progress_pct"] = round(done_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Complexity budget — authoritative source is plan.yaml.budget (per gse-orchestrator.md
    # Sprint Plan Maintenance protocol). status.yaml does NOT store the live sprint budget —
    # it was a stale read path prior to v0.52.0.
    _plan_budget = (data["plan"] or {}).get("budget") if data["plan"] else None
    data["complexity_budget"] = _plan_budget.get("total") if _plan_budget else None
    data["complexity_used"] = _plan_budget.get("consumed") if _plan_budget else None

    # Sprint directories — collect all (active + archived)
    all_sprint_dirs = []
    sprints_dir = DOCS_DIR / "sprints"
    if sprints_dir.exists():
        all_sprint_dirs.extend(sorted(d for d in sprints_dir.iterdir() if d.is_dir() and "sprint" in d.name))
    archive_dir = DOCS_DIR / "archive"
    if archive_dir.exists():
        all_sprint_dirs.extend(sorted(d for d in archive_dir.iterdir() if d.is_dir() and "sprint" in d.name))

    # Current sprint artefacts (for lifecycle checklist — shows current sprint state)
    sprint_num = data["current_sprint"]
    sprint_dir = DOCS_DIR / "sprints" / f"sprint-{sprint_num:02d}"
    if not sprint_dir.exists() and sprint_num > 0:
        sprint_dir = DOCS_DIR / "sprints" / f"sprint-{sprint_num}"

    data["has_design"] = (sprint_dir / "design.md").exists()
    data["has_review"] = (sprint_dir / "review.md").exists()
    data["has_compound"] = (sprint_dir / "compound.md").exists()

    # Quality metrics — cumulative across ALL sprints
    data["reqs_total"] = 0
    data["reqs_approved"] = 0
    data["has_test_strategy"] = False
    data["test_report_count"] = 0
    data["review_findings"] = {}
    for sd in all_sprint_dirs:
        rt, ra = count_reqs(sd)
        data["reqs_total"] += rt
        data["reqs_approved"] += ra
        has_ts, rc = count_tests(sd)
        if has_ts:
            data["has_test_strategy"] = True
        data["test_report_count"] += rc
        rf = count_review_findings(sd)
        for sev, count in rf.items():
            data["review_findings"][sev] = data["review_findings"].get(sev, 0) + count

    # Git
    data["git"] = get_git_info()

    # Sprint history
    data["sprint_history"] = []
    if sprints_dir.exists():
        for d in sorted(sprints_dir.iterdir()):
            if d.is_dir() and "sprint" in d.name:
                data["sprint_history"].append(d.name)

    # Archive
    data["archived_sprints"] = []
    if archive_dir.exists():
        data["archived_sprints"] = sorted([d.name for d in archive_dir.iterdir() if d.is_dir()])

    # Smoke test — validate required fields and warn on placeholders
    warnings = []
    if data["project_name"] == "Unknown Project":
        warnings.append("config.yaml: project name is missing or unset (showing 'Unknown Project')")
    if data["domain"] == "unknown":
        warnings.append("config.yaml: project domain is missing or unset")
    if not data.get("current_phase"):
        warnings.append("status.yaml: current_phase is missing")
    if data.get("user_name") == "Unknown":
        warnings.append("profile.yaml: user name is missing")
    if warnings:
        print(f"[dashboard] WARNING — {len(warnings)} validation issue(s) in .gse/ files:", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)
    data["_validation_warnings"] = warnings

    return data


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def generate_html(data, use_cdn=True):
    """Generate the dashboard HTML."""

    chart_js_include = ""
    if use_cdn:
        chart_js_include = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>'

    # Health radar data
    health_labels = list(data.get("health", {}).keys())
    health_values = list(data.get("health", {}).values())
    health_labels_json = json.dumps([l.replace("_", " ").title() for l in health_labels])
    health_values_json = json.dumps(health_values)

    # Task kanban counts
    tc = data.get("task_counts", {})
    kanban_labels = json.dumps(list(tc.keys()))
    kanban_values = json.dumps(list(tc.values()))

    # Lifecycle checklist
    phase = data.get("current_phase", "LC00")
    sprint = data.get("current_sprint", 0)

    def phase_status(check_phase, current):
        order = ["LC00", "LC01", "LC02", "LC03"]
        if check_phase not in order or current not in order:
            return "pending"
        return "done" if order.index(check_phase) < order.index(current) else (
            "active" if check_phase == current else "pending"
        )

    # Plan workflow HTML
    plan = data.get("plan")
    workflow_html = ""
    alerts_card_html = ""
    if plan:
        rows = []
        for act in plan.get("workflow_completed", []):
            rows.append(f'<li class="done">{act}</li>')
        if plan.get("workflow_active"):
            rows.append(f'<li class="active">{plan["workflow_active"]} <span class="muted">(active)</span></li>')
        for act in plan.get("workflow_pending", []):
            rows.append(f'<li class="pending">{act}</li>')
        for sk in plan.get("workflow_skipped", []):
            rows.append(f'<li class="skipped">{sk["activity"]} <span class="muted">(skipped — {sk["reason"]})</span></li>')
        rows_html = "\n      ".join(rows) if rows else '<li class="muted">(plan.yaml present but workflow empty)</li>'

        budget = plan.get("budget", {})
        bt, bc, br = budget.get("total"), budget.get("consumed"), budget.get("remaining")
        budget_html = ""
        if bt is not None:
            consumed_pct = round((bc or 0) / bt * 100) if bt else 0
            bar_color = "#e74c3c" if consumed_pct >= 80 else "#f39c12" if consumed_pct >= 60 else "#2ecc71"
            budget_html = f"""
    <div class="metric"><span class="metric-label">Budget</span>
      <span class="metric-value">{bc or 0}/{bt} pts ({consumed_pct}%)</span></div>
    <div class="progress-bar"><div class="progress-fill" style="width:{consumed_pct}%;background:{bar_color}"></div></div>"""

        status_badge = plan.get("status") or "unknown"
        mode_label = plan.get("mode") or "?"
        workflow_html = f"""
  <div class="card">
    <div class="card-title">Sprint Workflow <span class="muted">({mode_label} mode · {status_badge})</span></div>
    <ul class="checklist">
      {rows_html}
    </ul>{budget_html}
  </div>"""

        alerts = plan.get("alerts", [])
        if alerts:
            alert_items = "".join(f'<li class="active" style="color:var(--amber)">{a}</li>' for a in alerts)
            alerts_card_html = f"""
  <div class="card" style="border-color:var(--amber)">
    <div class="card-title" style="color:var(--amber)">⚠ Coherence Alerts ({len(alerts)})</div>
    <ul class="checklist">{alert_items}</ul>
    <div class="muted" style="margin-top:6px">Non-blocking — consider <code>/gse:plan --tactical</code> to re-plan.</div>
  </div>"""

    # Review findings HTML
    findings_html = ""
    rf = data.get("review_findings", {})
    if rf:
        for sev, count in rf.items():
            color = "#e74c3c" if sev == "HIGH" else "#f39c12" if sev == "MEDIUM" else "#95a5a6"
            if sev == "AI-INTEGRITY":
                color = "#9b59b6"
            findings_html += f'<span class="badge" style="background:{color}">{sev}: {count}</span> '
    else:
        findings_html = '<span class="muted">No findings yet</span>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="30">
<title>GSE-One Dashboard — {data.get('project_name', 'Project')}</title>
{chart_js_include}
<style>
  :root {{
    --bg: #1a1a2e; --card: #16213e; --accent: #0f3460; --text: #e0e0e0;
    --green: #2ecc71; --amber: #f39c12; --red: #e74c3c; --blue: #3498db;
    --purple: #9b59b6; --muted: #7f8c8d;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: var(--bg); color: var(--text); padding: 20px; }}
  h1 {{ color: var(--blue); margin-bottom: 5px; }}
  h2 {{ color: var(--text); font-size: 1.1em; margin: 20px 0 10px; border-bottom: 1px solid var(--accent); padding-bottom: 5px; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
  .header-right {{ text-align: right; color: var(--muted); font-size: 0.85em; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
  .card {{ background: var(--card); border-radius: 8px; padding: 15px; border: 1px solid var(--accent); }}
  .card-title {{ font-weight: 600; margin-bottom: 10px; font-size: 0.95em; color: var(--blue); }}
  .metric {{ display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.9em; }}
  .metric-label {{ color: var(--muted); }}
  .metric-value {{ font-weight: 600; }}
  .progress-bar {{ background: var(--accent); border-radius: 4px; height: 8px; margin: 5px 0; }}
  .progress-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; color: white; margin: 2px; }}
  .muted {{ color: var(--muted); font-size: 0.85em; }}
  .checklist {{ list-style: none; }}
  .checklist li {{ padding: 3px 0; font-size: 0.9em; }}
  .checklist .done::before {{ content: "\\2705 "; }}
  .checklist .active::before {{ content: "\\25B6 "; color: var(--blue); }}
  .checklist .pending::before {{ content: "\\25CB "; color: var(--muted); }}
  .checklist .skipped::before {{ content: "\\2014 "; color: var(--muted); }}
  .kanban {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .kanban-col {{ flex: 1; min-width: 80px; text-align: center; padding: 8px; border-radius: 6px; }}
  .kanban-count {{ font-size: 1.5em; font-weight: bold; }}
  .kanban-label {{ font-size: 0.75em; color: var(--muted); background: rgba(0,0,0,0.4); border-radius: 8px; padding: 1px 8px; display: inline-block; }}
  .refresh-btn {{ background: var(--accent); color: var(--text); border: 1px solid var(--blue);
                  padding: 6px 14px; border-radius: 4px; cursor: pointer; font-size: 0.85em; }}
  .refresh-btn:hover {{ background: var(--blue); }}
  canvas {{ max-height: 250px; }}
  .no-data {{ color: var(--muted); font-style: italic; font-size: 0.9em; padding: 10px 0; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85em; }}
  th, td {{ padding: 5px 8px; text-align: left; border-bottom: 1px solid var(--accent); }}
  th {{ color: var(--blue); }}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>{data.get('project_name', 'Project')}</h1>
    <span class="muted">GSE-One Dashboard &mdash; {data.get('domain', '')} &mdash; {data.get('mode', 'full')} mode</span>
  </div>
  <div class="header-right">
    <div>Updated: {data['generated_at']}</div>
    <button class="refresh-btn" onclick="location.reload()">Refresh</button>
    <div class="muted" style="margin-top:4px">Auto-refresh every 30s</div>
  </div>
</div>

<div class="grid">

  <!-- Project State -->
  <div class="card">
    <div class="card-title">Project State</div>
    <div class="metric"><span class="metric-label">Sprint</span><span class="metric-value">{data.get('current_sprint', 0)}</span></div>
    <div class="metric"><span class="metric-label">Phase</span><span class="metric-value">{data.get('current_phase', 'LC00')}</span></div>
    <div class="metric"><span class="metric-label">Last Activity</span><span class="metric-value">{data.get('last_activity', 'none')}</span></div>
    <div class="metric"><span class="metric-label">User</span><span class="metric-value">{data.get('user_name', '?')} ({data.get('it_expertise', '?')})</span></div>
    <div class="metric"><span class="metric-label">Decisions</span><span class="metric-value">{data.get('decision_involvement', '?')}</span></div>
  </div>

  <!-- Task Progress -->
  <div class="card">
    <div class="card-title">Tasks ({data.get('total_tasks', 0)} total)</div>
    <div class="kanban">
      <div class="kanban-col" style="background:#2c3e50">
        <div class="kanban-count">{tc.get('planned', 0)}</div><div class="kanban-label">Planned</div>
      </div>
      <div class="kanban-col" style="background:#2980b9">
        <div class="kanban-count">{tc.get('in-progress', 0)}</div><div class="kanban-label">In Progress</div>
      </div>
      <div class="kanban-col" style="background:#f39c12">
        <div class="kanban-count">{tc.get('review', 0) + tc.get('fixing', 0)}</div><div class="kanban-label">Review/Fix</div>
      </div>
      <div class="kanban-col" style="background:#27ae60">
        <div class="kanban-count">{tc.get('done', 0) + tc.get('delivered', 0)}</div><div class="kanban-label">Done</div>
      </div>
    </div>
    <div class="progress-bar" style="margin-top:10px">
      <div class="progress-fill" style="width:{data.get('progress_pct', 0)}%;background:var(--green)"></div>
    </div>
    <div class="muted">{data.get('progress_pct', 0)}% complete</div>
  </div>

  <!-- Lifecycle Checklist -->
  <div class="card">
    <div class="card-title">Lifecycle — Sprint {data.get('current_sprint', 0)} ({len(data.get('sprint_history', [])) + len(data.get('archived_sprints', []))} total)</div>
    <ul class="checklist">
      <li class="{phase_status('LC00', phase)}">Onboarding (HUG)</li>
      <li class="{'done' if data['has_design'] or data['reqs_total'] > 0 else phase_status('LC01', phase)}">Discovery (COLLECT &gt; ASSESS &gt; PLAN)</li>
      <li class="{'done' if data['reqs_approved'] else 'pending'}">Requirements ({data['reqs_total']} REQs{', approved' if data['reqs_approved'] else ''})</li>
      <li class="{'done' if data['has_design'] else 'pending'}">Design</li>
      <li class="{'done' if data['has_test_strategy'] else 'pending'}">Test Strategy</li>
      <li class="{phase_status('LC02', phase)}">Production ({tc.get('reviewed', 0) + tc.get('done', 0) + tc.get('delivered', 0)}/{data.get('total_tasks', 0)} tasks)</li>
      <li class="{'done' if data['has_review'] else 'pending'}">Review{' (' + findings_html + ')' if rf else ''}</li>
      <li class="{'done' if data['has_compound'] else 'pending'}">Capitalization (COMPOUND)</li>
    </ul>
  </div>
{workflow_html}
{alerts_card_html}
  <!-- Health Radar -->
  <div class="card">
    <div class="card-title">Project Health</div>
    {'<canvas id="healthRadar"></canvas>' if use_cdn and health_values else '<div class="no-data">No health data yet (available after first review)</div>'}
    {_health_table(data) if not use_cdn and health_values else ''}
  </div>

  <!-- Quality -->
  <div class="card">
    <div class="card-title">Quality</div>
    <div class="metric"><span class="metric-label">Review Findings</span><span class="metric-value">{findings_html}</span></div>
    <div class="metric"><span class="metric-label">Test Reports</span><span class="metric-value">{data.get('test_report_count', 0)}</span></div>
    <div class="metric"><span class="metric-label">Test Strategy</span><span class="metric-value">{'Yes' if data.get('has_test_strategy') else 'No'}</span></div>
    <div class="metric"><span class="metric-label">REQS Coverage</span><span class="metric-value">{data.get('reqs_total', 0)} REQs defined</span></div>
  </div>

  <!-- Git -->
  <div class="card">
    <div class="card-title">Version Control</div>
    <div class="metric"><span class="metric-label">Active Branches</span><span class="metric-value">{data['git']['branches']}</span></div>
    <div class="metric"><span class="metric-label">Last Commit</span><span class="metric-value" style="font-size:0.8em">{data['git']['last_commit'][:50]}</span></div>
    <div class="metric"><span class="metric-label">Tags</span><span class="metric-value">{', '.join(data['git']['tags'][:3]) or 'none'}</span></div>
    <div class="metric"><span class="metric-label">Sprint History</span><span class="metric-value">{len(data.get('sprint_history', []))} active, {len(data.get('archived_sprints', []))} archived</span></div>
  </div>

</div>

{'<script>' + _chart_js_script(health_labels_json, health_values_json) + '</script>' if use_cdn and health_values else ''}

<div class="muted" style="text-align:center; margin-top:20px; padding:10px">
  GSE-One Dashboard &mdash; Generated from <code>.gse/</code> state files &mdash;
  <code>python3 &quot;$(cat ~/.gse-one)/tools/dashboard.py&quot; --watch</code> for live updates
</div>

</body>
</html>"""

    return html


def _health_table(data):
    """Fallback health display when CDN is not available."""
    rows = ""
    for dim, val in data.get("health", {}).items():
        color = "#2ecc71" if val >= 7 else "#f39c12" if val >= 5 else "#e74c3c"
        label = dim.replace("_", " ").title()
        pct = val * 10
        rows += f"""<div class="metric">
          <span class="metric-label">{label}</span>
          <span class="metric-value" style="color:{color}">{val}/10</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width:{pct}%;background:{color}"></div></div>"""
    return rows


def _chart_js_script(labels_json, values_json):
    """Chart.js radar chart script."""
    return f"""
    new Chart(document.getElementById('healthRadar'), {{
      type: 'radar',
      data: {{
        labels: {labels_json},
        datasets: [{{
          label: 'Health Score',
          data: {values_json},
          fill: true,
          backgroundColor: 'rgba(52, 152, 219, 0.2)',
          borderColor: 'rgba(52, 152, 219, 1)',
          pointBackgroundColor: 'rgba(52, 152, 219, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(52, 152, 219, 1)'
        }}]
      }},
      options: {{
        responsive: true,
        scales: {{
          r: {{
            min: 0, max: 10,
            ticks: {{ stepSize: 2, color: '#7f8c8d' }},
            grid: {{ color: 'rgba(127, 140, 141, 0.3)' }},
            pointLabels: {{ color: '#e0e0e0', font: {{ size: 11 }} }},
            angleLines: {{ color: 'rgba(127, 140, 141, 0.3)' }}
          }}
        }},
        plugins: {{ legend: {{ display: false }} }}
      }}
    }});
    """


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate(output_path, use_cdn=True):
    """Generate the dashboard HTML file. Consumes any pending error marker
    and injects a red warning banner at the top of the page if present."""
    data = collect_data()
    html_content = generate_html(data, use_cdn=use_cdn)

    # Consume error marker (if any) and inject failure banner
    err_ts, err_msg = _read_and_clear_error_marker()
    if err_ts:
        banner = (
            '<div style="background:#c0392b;color:#fff;padding:16px;margin:16px;'
            'border-radius:8px;font-weight:600;font-family:system-ui,sans-serif">'
            f'⚠ Dashboard regeneration previously failed at {html.escape(err_ts)} — '
            f'{html.escape(str(err_msg))}. State files may have been edited after the '
            'failure; this dashboard reflects the most recent successful regeneration.'
            '</div>'
        )
        html_content = html_content.replace("<body>", f"<body>\n{banner}", 1)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"  Dashboard generated: {output_path}")
    return output_path


def if_stale(output_path, use_cdn=True):
    """Regenerate only if sprint state is newer than the existing dashboard,
    with configurable debounce window. Non-fatal on failure — writes
    .gse/.dashboard-error.yaml on any exception."""
    try:
        debounce = _read_debounce_seconds(default=5.0)
        out = Path(output_path)
        if out.exists():
            dash_mtime = out.stat().st_mtime
            if time.time() - dash_mtime < debounce:
                return
        else:
            dash_mtime = 0

        state_max = 0.0
        if GSE_DIR.exists():
            for f in GSE_DIR.rglob("*.yaml"):
                if f.is_file():
                    try:
                        state_max = max(state_max, f.stat().st_mtime)
                    except OSError:
                        pass
        sprints_dir = DOCS_DIR / "sprints"
        if sprints_dir.exists():
            for f in sprints_dir.rglob("*.md"):
                if f.is_file():
                    try:
                        state_max = max(state_max, f.stat().st_mtime)
                    except OSError:
                        pass

        if state_max <= dash_mtime:
            return

        generate(output_path, use_cdn=use_cdn)
    except Exception as e:
        _write_error_marker(str(e))
        raise


def watch(output_path, use_cdn=True):
    """Watch .gse/ for changes and regenerate."""
    print(f"  Watching {GSE_DIR} for changes... (Ctrl+C to stop)")
    last_mtime = 0
    while True:
        current_mtime = max(
            (f.stat().st_mtime for f in GSE_DIR.rglob("*") if f.is_file()),
            default=0
        )
        # Also check docs/sprints/
        sprints_dir = DOCS_DIR / "sprints"
        if sprints_dir.exists():
            sprint_mtime = max(
                (f.stat().st_mtime for f in sprints_dir.rglob("*") if f.is_file()),
                default=0
            )
            current_mtime = max(current_mtime, sprint_mtime)

        if current_mtime > last_mtime:
            last_mtime = current_mtime
            generate(output_path, use_cdn=use_cdn)
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser(
        description="GSE-One Dashboard — Generate project health dashboard from .gse/ state"
    )
    parser.add_argument("--output", "-o", type=str, default=str(DEFAULT_OUTPUT),
                        help=f"Output HTML path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--no-cdn", action="store_true",
                        help="Offline mode — no external CDN dependencies")
    parser.add_argument("--watch", "-w", action="store_true",
                        help="Watch mode — regenerate on file changes")
    parser.add_argument("--if-stale", dest="if_stale", action="store_true",
                        help="Regenerate only if sprint state is newer than the dashboard "
                             "(configurable debounce via .gse/config.yaml → "
                             "dashboard.regen_debounce_seconds, default 5s). "
                             "Used by PostToolUse hooks.")

    args = parser.parse_args()
    use_cdn = not args.no_cdn

    if not GSE_DIR.exists():
        # --if-stale is meant to be called from PostToolUse hooks that may fire
        # in any cwd (including non-GSE projects). Exit silently with code 0
        # so the hook wrapper does not treat it as a failure and does not
        # write an error marker — we are simply in a directory that is not a
        # GSE-managed project, which is normal and expected.
        if args.if_stale:
            sys.exit(0)
        print(f"  No .gse/ directory found at {ROOT}")
        print("  Run /gse:go to initialize the project first.")
        sys.exit(1)

    try:
        if args.if_stale:
            if_stale(args.output, use_cdn=use_cdn)
        elif args.watch:
            generate(args.output, use_cdn=use_cdn)
            watch(args.output, use_cdn=use_cdn)
        else:
            generate(args.output, use_cdn=use_cdn)
    except Exception as e:
        # Top-level safety net: write error marker and re-raise so the caller
        # (hook wrapper or CI) sees the non-zero exit.
        _write_error_marker(str(e))
        raise


if __name__ == "__main__":
    main()
