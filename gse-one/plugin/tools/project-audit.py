#!/usr/bin/env python3
# @gse-tool project-audit 0.1.0
"""
GSE-One Project Methodology Audit — Deterministic audit of project state.

Usage (via registry):
    python3 "$(cat ~/.gse-one)/tools/project-audit.py"              # Human-readable output
    python3 "$(cat ~/.gse-one)/tools/project-audit.py" --json       # JSON output (consumed by /gse:audit)
    python3 "$(cat ~/.gse-one)/tools/project-audit.py" --severity-filter HIGH
    python3 "$(cat ~/.gse-one)/tools/project-audit.py" --help

Detects methodology drift via deterministic checks. Outputs findings as
AUD-NNN entries. Runs the full set of 15 checks (checks 1-15).
Semantic layer (project-reviewer agent) ships in Phase 2.

See design §3.4 Dashboard parser format contracts and §5.Z /gse:audit
for the authoritative formats and activity workflow.

Exit codes (severity-graded):
    0 = no findings
    1 = findings at LOW or MEDIUM severity only
    2 = at least one HIGH finding
    3 = at least one CRITICAL finding
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUDIT_ENGINE_VERSION = "0.1.0"


def find_project_root():
    """Find the project root by looking for .gse/ directory (same pattern as dashboard.py)."""
    current = Path.cwd()
    if current.name == ".gse":
        return current.parent
    if (current / ".gse").is_dir():
        return current
    for parent in current.parents:
        if (parent / ".gse").is_dir():
            return parent
    return current


ROOT = find_project_root()
GSE_DIR = ROOT / ".gse"
DOCS_DIR = ROOT / "docs"


# ---------------------------------------------------------------------------
# Finding data structure
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A single audit finding. AUD-NNN ID allocated at emission time (J.2.a.4.B)."""
    id: str
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    category: str
    title: str
    detail: str
    evidence: str
    recommendation: str
    auto_fixable: bool = False
    fix_command: Optional[str] = None


# ---------------------------------------------------------------------------
# YAML parser — minimal, 2-level nesting. Mirrors dashboard.py's parse_yaml_simple
# (J.2.a.1.B: recopied rather than imported, for decoupling per CLAUDE.md tool convention).
# ---------------------------------------------------------------------------

def parse_yaml_simple(filepath):
    """Parse a YAML file with up to 2 levels of nesting. Returns flat dict with dotted keys."""
    if not filepath.exists():
        return {}
    try:
        content = filepath.read_text(encoding="utf-8")
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
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            if indent == 0:
                parent_key = None
                parent_indent = -1
            match_parent = re.match(r'^(\w[\w.-]*)\s*:\s*$', stripped)
            if match_parent:
                key = match_parent.group(1)
                if indent == 0:
                    parent_key = key
                    parent_indent = indent
                elif parent_key and indent > parent_indent:
                    parent_key = f"{parent_key}.{key}"
                continue
            match_kv = re.match(r'^(\w[\w.-]*)\s*:\s*(.+)$', stripped)
            if match_kv:
                key = match_kv.group(1)
                val = match_kv.group(2).strip().strip('"').strip("'")
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
                if parent_key and indent > parent_indent:
                    result[f"{parent_key}.{key}"] = val
                else:
                    result[key] = val
                    parent_key = None
                    parent_indent = -1
        return result
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_current_sprint_dir():
    """Return the current sprint directory, or None if no sprint is active."""
    status = parse_yaml_simple(GSE_DIR / "status.yaml")
    current_sprint = status.get("current_sprint", 0)
    if not current_sprint or current_sprint == 0:
        return None
    for pattern in (f"sprint-{int(current_sprint):02d}", f"sprint-{int(current_sprint)}"):
        sprint_dir = DOCS_DIR / "sprints" / pattern
        if sprint_dir.exists():
            return sprint_dir
    return None


def get_lifecycle_mode():
    """Return the project's lifecycle mode (full | lightweight | micro) or None."""
    config = parse_yaml_simple(GSE_DIR / "config.yaml")
    return config.get("lifecycle.mode") or config.get("mode")


def next_id(counter):
    """Allocate the next AUD-NNN ID."""
    counter[0] += 1
    return f"AUD-{counter[0]:03d}"


# ---------------------------------------------------------------------------
# Check 1 — Dashboard freshness
# ---------------------------------------------------------------------------

def check_dashboard_freshness(id_counter):
    """docs/dashboard.html must be regenerated at each activity transition
    (/gse:go Step 2.6 Dashboard Refresh). If state files are newer, it is stale.
    """
    findings = []
    dashboard = DOCS_DIR / "dashboard.html"
    if not dashboard.exists():
        findings.append(Finding(
            id=next_id(id_counter),
            severity="HIGH",
            category="dashboard-freshness",
            title="Dashboard file does not exist",
            detail="docs/dashboard.html is missing. It should be generated at every /gse:go invocation (Step 2.6 Dashboard Refresh).",
            evidence=f"{dashboard} not found",
            recommendation="Run the dashboard generator now.",
            auto_fixable=True,
            fix_command='python3 "$(cat ~/.gse-one)/tools/dashboard.py"',
        ))
        return findings

    dash_mtime = dashboard.stat().st_mtime
    state_max = 0.0
    if GSE_DIR.exists():
        for f in GSE_DIR.rglob("*.yaml"):
            if f.is_file():
                state_max = max(state_max, f.stat().st_mtime)
    sprints = DOCS_DIR / "sprints"
    if sprints.exists():
        for f in sprints.rglob("*.md"):
            if f.is_file():
                state_max = max(state_max, f.stat().st_mtime)

    lag_seconds = state_max - dash_mtime
    if lag_seconds > 30:
        dash_iso = datetime.fromtimestamp(dash_mtime, tz=timezone.utc).isoformat()
        state_iso = datetime.fromtimestamp(state_max, tz=timezone.utc).isoformat()
        findings.append(Finding(
            id=next_id(id_counter),
            severity="MEDIUM",
            category="dashboard-freshness",
            title="Dashboard is stale",
            detail=f"docs/dashboard.html is {int(lag_seconds)}s older than the latest state file change. Per /gse:go Step 2.6 Dashboard Refresh, it should be regenerated at each activity transition.",
            evidence=f"dashboard mtime={dash_iso}, latest state mtime={state_iso}",
            recommendation="Regenerate the dashboard.",
            auto_fixable=True,
            fix_command='python3 "$(cat ~/.gse-one)/tools/dashboard.py"',
        ))
    return findings


# ---------------------------------------------------------------------------
# Check 2 — Test evidence on must-priority REQs
# ---------------------------------------------------------------------------

def check_test_evidence(id_counter):
    """Per spec §6.3 Test Execution and Evidence: every TASK implementing a
    must-priority REQ must carry test_evidence.status = 'pass'.
    """
    findings = []
    sprint_dir = get_current_sprint_dir()
    if not sprint_dir:
        return findings

    reqs_file = sprint_dir / "reqs.md"
    if not reqs_file.exists():
        return findings

    content = reqs_file.read_text(encoding="utf-8")
    # Split into REQ sections and identify must-priority ones
    req_sections = re.split(r'(?m)^###\s+REQ-(\d+)', content)
    must_reqs = []
    for i in range(1, len(req_sections), 2):
        req_num = req_sections[i]
        req_body = req_sections[i + 1] if i + 1 < len(req_sections) else ""
        if re.search(r'(?im)\*\*Priority:\*\*\s*Must\b', req_body):
            must_reqs.append(f"REQ-{req_num}")

    if not must_reqs:
        return findings

    backlog_file = GSE_DIR / "backlog.yaml"
    if not backlog_file.exists():
        return findings
    backlog_content = backlog_file.read_text(encoding="utf-8")

    # Parse each TASK block (rough regex split by TASK-NNN id lines)
    task_blocks = re.split(r'(?m)^\s*-\s+id:\s*(TASK-\d+)', backlog_content)
    for i in range(1, len(task_blocks), 2):
        task_id = task_blocks[i]
        task_body = task_blocks[i + 1] if i + 1 < len(task_blocks) else ""
        implemented_must = [r for r in must_reqs if r in task_body]
        if not implemented_must:
            continue
        ev_match = re.search(r'test_evidence:\s*\n(?:\s+.*\n)*?\s+status:\s*(\w+)', task_body)
        status = ev_match.group(1).strip() if ev_match else None
        if status != "pass":
            findings.append(Finding(
                id=next_id(id_counter),
                severity="HIGH",
                category="test-evidence",
                title=f"{task_id} implementing must-priority REQs has no passing test evidence",
                detail=f"{task_id} implements {', '.join(implemented_must)} (priority: must) but test_evidence.status is {status or 'absent'}. Per spec §6.3 Test Execution and Evidence, every covered TASK must carry evidence after the canonical test run. /gse:deliver Step 1.5 will block delivery.",
                evidence=f"backlog.yaml {task_id} test_evidence.status={status or 'absent'}",
                recommendation=f"Run /gse:tests --run on {task_id} to populate the evidence.",
                auto_fixable=False,
                fix_command=None,
            ))
    return findings


# ---------------------------------------------------------------------------
# Check 3 — Required files per phase
# ---------------------------------------------------------------------------

def check_required_files(id_counter):
    """Each lifecycle phase requires specific artefacts (Full mode LC02+: reqs, design, test-strategy)."""
    findings = []
    mode = get_lifecycle_mode()
    if not mode:
        return findings
    sprint_dir = get_current_sprint_dir()
    if not sprint_dir:
        return findings
    status = parse_yaml_simple(GSE_DIR / "status.yaml")
    phase = status.get("current_phase", "LC00")

    if mode == "full" and phase in ("LC02", "LC03"):
        expected = {
            "reqs.md": "Requirements",
            "test-strategy.md": "Test strategy",
            "design.md": "Design (may be in workflow.skipped — not enforced here in Phase 1)",
        }
        for filename, description in expected.items():
            if not (sprint_dir / filename).exists():
                findings.append(Finding(
                    id=next_id(id_counter),
                    severity="MEDIUM",
                    category="file-structure",
                    title=f"Sprint artefact missing: {filename}",
                    detail=f"In Full mode phase {phase}, sprint directory should contain {filename} ({description}). File is missing.",
                    evidence=f"{sprint_dir / filename} not found",
                    recommendation=f"Run the matching activity to create it, or add to plan.yaml workflow.skipped if intentional.",
                    auto_fixable=False,
                    fix_command=None,
                ))
    return findings


# ---------------------------------------------------------------------------
# Check 4 — REQ format canonical (H3 heading)
# ---------------------------------------------------------------------------

def check_req_format(id_counter):
    """Per template src/templates/sprint/reqs.md and design §3.4, REQ entries
    must use `### REQ-NNN — {title}` (H3 heading).
    """
    findings = []
    sprint_dir = get_current_sprint_dir()
    if not sprint_dir:
        return findings
    reqs_file = sprint_dir / "reqs.md"
    if not reqs_file.exists():
        return findings
    content = reqs_file.read_text(encoding="utf-8")

    canonical = len(re.findall(r'(?im)^\s*###\s+REQ-\d+\b', content))
    legacy_id = len(re.findall(r'(?im)^\s*id:\s*REQ-\d+\b', content))

    if legacy_id > 0 and canonical == 0:
        findings.append(Finding(
            id=next_id(id_counter),
            severity="LOW",
            category="format",
            title="reqs.md uses legacy `id: REQ-NNN` format instead of canonical H3 heading",
            detail="Per template src/templates/sprint/reqs.md and design §3.4 Dashboard parser format contracts, REQ entries should use `### REQ-NNN — {title}` (H3 heading). The dashboard does not count the legacy format.",
            evidence=f"{legacy_id} `id: REQ-NNN` mentions found, {canonical} H3 heading mentions",
            recommendation="Reformat REQ entries to use `### REQ-NNN — {title}` H3 headings.",
            auto_fixable=False,
            fix_command=None,
        ))
    return findings


# ---------------------------------------------------------------------------
# Check 5 — Review severity format canonical (square brackets)
# ---------------------------------------------------------------------------

def check_review_severity_format(id_counter):
    """Per agent src/agents/code-reviewer.md Output Format and design §3.4,
    findings use `RVW-NNN [SEVERITY] — {title}` (square brackets).
    """
    findings = []
    sprint_dir = get_current_sprint_dir()
    if not sprint_dir:
        return findings
    review_file = sprint_dir / "review.md"
    if not review_file.exists():
        return findings
    content = review_file.read_text(encoding="utf-8")

    canonical = len(re.findall(r'RVW-\d+\s*\[(?:HIGH|MEDIUM|LOW|CRITICAL)\]', content))
    parens = len(re.findall(r'RVW-\d+\s*\((?:HIGH|MEDIUM|LOW|CRITICAL)\)', content))

    if parens > 0 and canonical == 0:
        findings.append(Finding(
            id=next_id(id_counter),
            severity="LOW",
            category="format",
            title="review.md uses parentheses instead of canonical square brackets",
            detail="Per agent src/agents/code-reviewer.md Output Format and design §3.4, findings should use `RVW-NNN [SEVERITY] — {title}` with square brackets. Parentheses is a common LLM drift; the dashboard tolerates it but the canonical form is brackets.",
            evidence=f"{parens} findings in parentheses form, {canonical} in canonical brackets form",
            recommendation="Reformat all findings to use `[HIGH]`, `[MEDIUM]`, `[LOW]` (square brackets).",
            auto_fixable=True,
            fix_command="# Sed-like replacement: s/RVW-([0-9]+)\\s*\\(([A-Z]+)\\)/RVW-\\1 [\\2]/g on review.md",
        ))
    return findings


# ---------------------------------------------------------------------------
# Check 6 — Health dimensions nested path
# ---------------------------------------------------------------------------

def check_health_dimensions_nested(id_counter):
    """Per template src/templates/status.yaml, health scores live at
    health.dimensions.<dim>. Flat health.<dim> is legacy (design §3.4)."""
    findings = []
    status_file = GSE_DIR / "status.yaml"
    if not status_file.exists():
        return findings
    content = status_file.read_text(encoding="utf-8")
    has_nested = bool(re.search(r'(?m)^health:\s*\n\s+dimensions:', content))
    has_flat_dim = bool(re.search(
        r'(?m)^health:\s*\n(?!\s+dimensions:)\s+(test_pass_rate|review_findings|git_hygiene|design_debt|requirements_coverage|ai_integrity|complexity_budget|traceability)\s*:',
        content))
    if has_flat_dim and not has_nested:
        findings.append(Finding(
            id=next_id(id_counter), severity="LOW", category="format",
            title="status.yaml uses flat `health.<dim>` instead of canonical nested `health.dimensions.<dim>`",
            detail="Per template src/templates/status.yaml and design §3.4 Dashboard parser format contracts, health scores must be nested under health.dimensions. Dashboard primary lookup uses the nested path.",
            evidence="status.yaml has flat health dimension entries without health.dimensions.* nesting",
            recommendation="Restructure status.yaml to nest health scores under health.dimensions.",
            auto_fixable=False, fix_command=None,
        ))
    return findings


# ---------------------------------------------------------------------------
# Check 7 — Test reports directory non-empty (if strategy exists)
# ---------------------------------------------------------------------------

def check_test_reports_non_empty(id_counter):
    """If test-strategy.md exists, docs/sprints/NN/test-reports/ should have files."""
    findings = []
    sprint_dir = get_current_sprint_dir()
    if not sprint_dir:
        return findings
    strategy = sprint_dir / "test-strategy.md"
    if not strategy.exists():
        return findings
    reports_dir = sprint_dir / "test-reports"
    if not reports_dir.exists() or not any(reports_dir.iterdir()):
        findings.append(Finding(
            id=next_id(id_counter), severity="MEDIUM", category="test-evidence",
            title="Test strategy defined but no test reports emitted",
            detail=f"test-strategy.md exists but {reports_dir} is empty or missing. Per spec §6.3 Step 4, every canonical test run writes a TCP- campaign report to this directory.",
            evidence="test-strategy.md present, test-reports directory empty or missing",
            recommendation="Run /gse:tests --run to execute the test suite and emit a campaign report.",
            auto_fixable=False, fix_command=None,
        ))
    return findings


# ---------------------------------------------------------------------------
# Check 8 — Activity history coherence (status ↔ plan)
# ---------------------------------------------------------------------------

def check_activity_history_coherence(id_counter):
    """status.yaml.activity_history and plan.yaml.workflow.completed should agree."""
    findings = []
    status_file = GSE_DIR / "status.yaml"
    plan_file = GSE_DIR / "plan.yaml"
    if not status_file.exists() or not plan_file.exists():
        return findings
    status_content = status_file.read_text(encoding="utf-8")
    plan_content = plan_file.read_text(encoding="utf-8")
    activities_in_history = set(re.findall(r'(?m)^\s+-\s+activity:\s*(\S+)', status_content))
    plan_completed_block = re.search(
        r'(?s)workflow:\s*\n(?:.*?\n)*?\s+completed:\s*\n((?:\s+-\s+activity:.*?\n(?:\s+\w+:.*\n)*)+)',
        plan_content)
    if not plan_completed_block:
        return findings
    activities_in_plan = set(re.findall(r'(?m)^\s+-\s+activity:\s*(\S+)', plan_completed_block.group(1)))
    missing = activities_in_plan - activities_in_history
    if missing:
        findings.append(Finding(
            id=next_id(id_counter), severity="MEDIUM", category="workflow",
            title="plan.yaml workflow.completed and status.yaml activity_history disagree",
            detail=f"Activities in plan.yaml workflow.completed missing from status.yaml activity_history: {sorted(missing)}. Per gse-orchestrator.md Sprint Plan Maintenance, both files must be updated atomically at each transition.",
            evidence=f"Plan-only activities: {sorted(missing)}",
            recommendation="Review Sprint Plan Maintenance application; may indicate a silent skip.",
            auto_fixable=False, fix_command=None,
        ))
    return findings


# ---------------------------------------------------------------------------
# Check 9 — Workflow completed matches reality (artefacts exist)
# ---------------------------------------------------------------------------

def check_workflow_completed_artefacts(id_counter):
    """For each activity in plan.yaml.workflow.completed, verify expected artefact exists."""
    findings = []
    plan_file = GSE_DIR / "plan.yaml"
    sprint_dir = get_current_sprint_dir()
    if not plan_file.exists() or not sprint_dir:
        return findings
    plan_content = plan_file.read_text(encoding="utf-8")
    expected_artefacts = {
        "reqs": "reqs.md", "design": "design.md", "preview": "preview.md",
        "tests": "test-strategy.md", "review": "review.md",
    }
    completed_block = re.search(
        r'(?s)workflow:\s*\n(?:.*?\n)*?\s+completed:\s*\n((?:\s+-\s+activity:.*?\n(?:\s+\w+:.*\n)*)+)',
        plan_content)
    if not completed_block:
        return findings
    completed_activities = re.findall(r'(?m)^\s+-\s+activity:\s*(\S+)', completed_block.group(1))
    for activity in completed_activities:
        expected = expected_artefacts.get(activity)
        if expected and not (sprint_dir / expected).exists():
            findings.append(Finding(
                id=next_id(id_counter), severity="HIGH", category="workflow",
                title=f"Activity '{activity}' marked completed but expected artefact '{expected}' is missing",
                detail=f"plan.yaml lists '{activity}' in workflow.completed but {sprint_dir / expected} does not exist. The activity was marked complete without producing its artefact — a silent methodology violation.",
                evidence=f"plan.yaml completed: {activity}; file {expected} not found in sprint dir",
                recommendation=f"Either re-run /gse:{activity} to produce the artefact, or remove the entry from plan.yaml workflow.completed.",
                auto_fixable=False, fix_command=None,
            ))
    return findings


# ---------------------------------------------------------------------------
# Check 10 — Git state consistency
# ---------------------------------------------------------------------------

def check_git_state_consistency(id_counter):
    """If git.strategy = worktree | branch-only, git repo must exist with commits on main."""
    findings = []
    config = parse_yaml_simple(GSE_DIR / "config.yaml")
    git_strategy = config.get("git.strategy")
    if git_strategy not in ("worktree", "branch-only"):
        return findings
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        findings.append(Finding(
            id=next_id(id_counter), severity="HIGH", category="git-state",
            title=f"config declares git.strategy: {git_strategy} but no git repository exists",
            detail=f"config.yaml sets git.strategy: {git_strategy} which requires a git repo with commits on main. {git_dir} is missing. Per HUG Step 4 Git Initialization, the foundational commit is mandatory before branching operations.",
            evidence=f"config.yaml: git.strategy={git_strategy}, {git_dir} not found",
            recommendation="Run /gse:go (auto-triggers Step 2.7 Git Baseline Verification) or initialize git manually.",
            auto_fixable=False, fix_command=None,
        ))
        return findings
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "main"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=5,
        )
        if result.returncode != 0:
            findings.append(Finding(
                id=next_id(id_counter), severity="HIGH", category="git-state",
                title="main branch has no verifiable commit",
                detail=f"config.yaml git.strategy={git_strategy} requires commits on main. git rev-parse --verify main failed.",
                evidence=f"git rev-parse --verify main failed: {result.stderr.strip()}",
                recommendation="Create a foundational commit on main (chore: initialize repository) per spec §P12.",
                auto_fixable=False, fix_command=None,
            ))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return findings


# ---------------------------------------------------------------------------
# Check 11 — Sprint freeze honored
# ---------------------------------------------------------------------------

def check_sprint_freeze_honored(id_counter):
    """If plan.yaml.status = completed, no TASK in that sprint should have non-terminal status."""
    findings = []
    plan_file = GSE_DIR / "plan.yaml"
    if not plan_file.exists():
        return findings
    plan = parse_yaml_simple(plan_file)
    if plan.get("status") != "completed":
        return findings
    backlog_file = GSE_DIR / "backlog.yaml"
    if not backlog_file.exists():
        return findings
    backlog_content = backlog_file.read_text(encoding="utf-8")
    sprint_num = plan.get("sprint")
    if not sprint_num:
        return findings
    task_blocks = re.split(r'(?m)^\s*-\s+id:\s*(TASK-\d+)', backlog_content)
    for i in range(1, len(task_blocks), 2):
        task_id = task_blocks[i]
        task_body = task_blocks[i + 1] if i + 1 < len(task_blocks) else ""
        if f"sprint: {sprint_num}" not in task_body:
            continue
        status_match = re.search(r'status:\s*(\w+)', task_body)
        if not status_match:
            continue
        task_status = status_match.group(1).strip()
        if task_status in ("planned", "in-progress", "review", "fixing"):
            findings.append(Finding(
                id=next_id(id_counter), severity="HIGH", category="sprint-freeze",
                title=f"{task_id} in frozen sprint {sprint_num} has non-terminal status '{task_status}'",
                detail=f"plan.yaml.status='completed' (sprint {sprint_num} frozen per Sprint Freeze Invariant spec §14.3), but {task_id} has status={task_status}. Sprint closure immutability violated.",
                evidence=f"plan.yaml.status=completed, {task_id} status={task_status}",
                recommendation="Either resolve the TASK to a terminal state (delivered/done/reviewed) before freezing, or open a successor sprint for pending work.",
                auto_fixable=False, fix_command=None,
            ))
    return findings


# ---------------------------------------------------------------------------
# Check 12 — Intent artefact exists for greenfield
# ---------------------------------------------------------------------------

def check_intent_artefact_greenfield(id_counter):
    """If greenfield (no package manifest, no source dir), docs/intent.md should exist."""
    findings = []
    intent = DOCS_DIR / "intent.md"
    if intent.exists():
        return findings
    package_manifests = ["package.json", "pyproject.toml", "Cargo.toml", "go.mod", "requirements.txt"]
    has_manifest = any((ROOT / m).exists() for m in package_manifests)
    source_dirs = ["src", "app", "lib", "source"]
    has_source_dir = any((ROOT / d).is_dir() for d in source_dirs)
    if has_manifest or has_source_dir:
        return findings
    status = parse_yaml_simple(GSE_DIR / "status.yaml")
    sprint = status.get("current_sprint", 0)
    if sprint >= 1:
        findings.append(Finding(
            id=next_id(id_counter), severity="MEDIUM", category="intent",
            title="Greenfield project has no intent artefact (INT-001)",
            detail="Per spec §3 Step 5 Intent Capture, greenfield projects must produce INT-001 at docs/intent.md before complexity assessment. Current sprint ≥ 1 but no intent file.",
            evidence="docs/intent.md not found; no package manifest or source directory detected",
            recommendation="Re-run /gse:go; the orchestrator will enter Intent Capture if the project is still greenfield.",
            auto_fixable=False, fix_command=None,
        ))
    return findings


# ---------------------------------------------------------------------------
# Check 13 — Backlog traces.derives_from populated
# ---------------------------------------------------------------------------

def check_backlog_traces_populated(id_counter):
    """Each TASK should have traces.derives_from with at least one entry."""
    findings = []
    backlog_file = GSE_DIR / "backlog.yaml"
    if not backlog_file.exists():
        return findings
    content = backlog_file.read_text(encoding="utf-8")
    task_blocks = re.split(r'(?m)^\s*-\s+id:\s*(TASK-\d+)', content)
    missing = []
    for i in range(1, len(task_blocks), 2):
        task_id = task_blocks[i]
        task_body = task_blocks[i + 1] if i + 1 < len(task_blocks) else ""
        derives_nested = re.search(r'derives_from:\s*\n\s*-\s+\S+', task_body)
        derives_inline = re.search(r'derives_from:\s*\[([^\]]*)\]', task_body)
        has_entry = bool(derives_nested) or (derives_inline and derives_inline.group(1).strip())
        if not has_entry:
            missing.append(task_id)
    if missing:
        findings.append(Finding(
            id=next_id(id_counter), severity="LOW", category="backlog",
            title=f"{len(missing)} TASK(s) missing traces.derives_from",
            detail=f"Per spec §P6 Traceability, every artefact must trace to its origin. TASKs without derives_from lose provenance. Missing: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}.",
            evidence=f"TASKs with empty or missing derives_from: {missing}",
            recommendation="Populate traces.derives_from for each TASK (INT-NNN, PLN-NNN, user request, etc.).",
            auto_fixable=False, fix_command=None,
        ))
    return findings


# ---------------------------------------------------------------------------
# Check 14 — Coach workflow_observations consistent
# ---------------------------------------------------------------------------

def check_coach_observations(id_counter):
    """If coach.enabled, workflow_observations should have entries during active sprints."""
    findings = []
    config = parse_yaml_simple(GSE_DIR / "config.yaml")
    if not config.get("coach.enabled", False):
        return findings
    status = parse_yaml_simple(GSE_DIR / "status.yaml")
    sprint = status.get("current_sprint", 0)
    if sprint < 1:
        return findings
    status_file = GSE_DIR / "status.yaml"
    if not status_file.exists():
        return findings
    status_content = status_file.read_text(encoding="utf-8")
    observation_count = len(re.findall(r'(?m)^\s*-\s+axis:', status_content))
    history_count = len(re.findall(r'(?m)^\s+-\s+activity:', status_content))
    if history_count >= 5 and observation_count == 0:
        findings.append(Finding(
            id=next_id(id_counter), severity="MEDIUM", category="coach",
            title="Coach enabled but no workflow observations recorded",
            detail=f"config.yaml coach.enabled: true, but status.yaml workflow_observations is empty after {history_count} activities. Coach is silent or invocation is skipped.",
            evidence=f"activity_history: {history_count} entries, workflow_observations: 0 entries",
            recommendation="Verify the orchestrator invokes the coach per its delegation invariant (src/agents/gse-orchestrator.md).",
            auto_fixable=False, fix_command=None,
        ))
    return findings


# ---------------------------------------------------------------------------
# Check 15 — Open questions resolution status
# ---------------------------------------------------------------------------

def check_open_questions_resolution(id_counter):
    """Open questions (OQ-NNN) should be resolved by their target activity."""
    findings = []
    intent = DOCS_DIR / "intent.md"
    if not intent.exists():
        return findings
    content = intent.read_text(encoding="utf-8")
    pending_oqs = re.findall(
        r'id:\s*(OQ-\d+)[\s\S]*?resolves_in:\s*(\w+)[\s\S]*?status:\s*pending',
        content)
    if not pending_oqs:
        return findings
    status_file = GSE_DIR / "status.yaml"
    status_content = status_file.read_text(encoding="utf-8") if status_file.exists() else ""
    for oq_id, resolves_in in pending_oqs:
        resolves_in_lower = resolves_in.lower()
        if re.search(rf'(?m)activity:\s*{resolves_in_lower}\b', status_content):
            findings.append(Finding(
                id=next_id(id_counter), severity="MEDIUM", category="open-questions",
                title=f"{oq_id} is still pending but {resolves_in} activity has already completed",
                detail=f"{oq_id} in docs/intent.md declares resolves_in: {resolves_in} with status: pending, but {resolves_in} is listed as completed in status.yaml activity_history. Per Open Questions Resolution Invariant, each OQ must be resolved in-place when its target activity runs.",
                evidence=f"{oq_id} status=pending, {resolves_in} listed as completed",
                recommendation=f"Update {oq_id} in docs/intent.md: set status: resolved, fill resolved_at, answer, answered_by, confidence.",
                auto_fixable=False, fix_command=None,
            ))
    return findings


# ---------------------------------------------------------------------------
# Main audit runner
# ---------------------------------------------------------------------------

def run_audit():
    """Run all deterministic checks and return a list of findings."""
    id_counter = [0]  # mutable box for allocation order (J.2.a.4.B)
    findings = []
    # Phase 1 checks 1-5 (J.2.a):
    findings.extend(check_dashboard_freshness(id_counter))
    findings.extend(check_test_evidence(id_counter))
    findings.extend(check_required_files(id_counter))
    findings.extend(check_req_format(id_counter))
    findings.extend(check_review_severity_format(id_counter))
    # Phase 1 checks 6-15 (J.2.b):
    findings.extend(check_health_dimensions_nested(id_counter))
    findings.extend(check_test_reports_non_empty(id_counter))
    findings.extend(check_activity_history_coherence(id_counter))
    findings.extend(check_workflow_completed_artefacts(id_counter))
    findings.extend(check_git_state_consistency(id_counter))
    findings.extend(check_sprint_freeze_honored(id_counter))
    findings.extend(check_intent_artefact_greenfield(id_counter))
    findings.extend(check_backlog_traces_populated(id_counter))
    findings.extend(check_coach_observations(id_counter))
    findings.extend(check_open_questions_resolution(id_counter))
    return findings


def format_human_readable(findings):
    """Format findings for human reading (CLI default output)."""
    if not findings:
        return "✅ All methodology checks passed. No drift detected.\n"
    lines = [f"Methodology audit — {len(findings)} finding(s) detected:"]
    by_sev = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        items = by_sev.get(sev, [])
        if not items:
            continue
        lines.append(f"\n## {sev} ({len(items)})")
        for f in items:
            lines.append(f"\n{f.id} [{f.severity}] — {f.title}")
            lines.append(f"  category: {f.category}")
            lines.append(f"  detail: {f.detail}")
            lines.append(f"  evidence: {f.evidence}")
            lines.append(f"  recommendation: {f.recommendation}")
            lines.append(f"  auto_fixable: {f.auto_fixable}")
            if f.fix_command:
                lines.append(f"  fix_command: {f.fix_command}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="GSE-One Project Audit — Deterministic methodology audit"
    )
    parser.add_argument("--json", action="store_true",
                        help="Output findings as JSON (consumed by /gse:audit activity)")
    parser.add_argument("--severity-filter",
                        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                        default=None,
                        help="Only report findings at or above this severity")
    args = parser.parse_args()

    if not GSE_DIR.exists():
        sys.stderr.write(f"No .gse/ directory found at {ROOT}. Run /gse:go to initialize.\n")
        sys.exit(1)

    findings = run_audit()

    if args.severity_filter:
        order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        threshold = order[args.severity_filter]
        findings = [f for f in findings if order.get(f.severity, 0) >= threshold]

    if args.json:
        output = {
            "audit_version": AUDIT_ENGINE_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_root": str(ROOT),
            "phase": "Phase 1 deterministic (checks 1-15)",
            "findings": [asdict(f) for f in findings],
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_human_readable(findings))

    if not findings:
        sys.exit(0)
    order_val = {"LOW": 1, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    max_val = max(order_val.get(f.severity, 1) for f in findings)
    sys.exit(max_val)


if __name__ == "__main__":
    main()
