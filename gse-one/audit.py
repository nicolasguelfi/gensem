#!/usr/bin/env python3
# @gse-tool audit 1.0
"""GSE-One methodology repository auditor — deterministic checks only.

Usage:
    python3 gse-one/audit.py                       # full, markdown output
    python3 gse-one/audit.py --format json         # for CI / scripting
    python3 gse-one/audit.py --category version    # only one category
    python3 gse-one/audit.py --cluster deploy-cluster  # only files in a cluster
    python3 gse-one/audit.py --list-clusters       # show catalog clusters
    python3 gse-one/audit.py --fail-on error       # exit 1 on errors

For reasoning-based checks (LLM), use the `/gse-audit` slash command in
Claude Code — it invokes this script for deterministic checks, then
performs semantic reasoning via the methodology-auditor agent across 20
audit jobs defined in .claude/audit-jobs.json.

This tool audits the gensem repo itself (not user projects). It lives in
gse-one/ alongside gse_generate.py (both are maintainer tools).
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Optional PyYAML for YAML schema validation
try:
    import yaml  # type: ignore[import-not-found]
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


# ---------------------------------------------------------------------------
# Paths (relative to repo root, computed from this file's location)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
GSE_ONE = REPO_ROOT / "gse-one"
SRC = GSE_ONE / "src"
PLUGIN = GSE_ONE / "plugin"

CATEGORIES = [
    "version",
    "file_integrity",
    "plugin_parity",
    "cross_refs",
    "numeric",
    "links",
    "git",
    "python",
    "templates",
    "todos",
    "test_coverage",
    "freshness",
]


# ---------------------------------------------------------------------------
# Finding + Report dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    category: str
    severity: str  # "error" | "warning" | "info" | "recommendation"
    title: str
    detail: str = ""
    fix_hint: str = ""
    location: str = ""
    file: str = ""  # canonical file path (relative to repo root) for cluster mapping


@dataclass
class Report:
    version: str
    timestamp: str
    repo_root: str
    findings: list = field(default_factory=list)

    def errors(self) -> list:
        return [f for f in self.findings if f.severity == "error"]

    def warnings(self) -> list:
        return [f for f in self.findings if f.severity == "warning"]

    def info(self) -> list:
        return [f for f in self.findings if f.severity == "info"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_text(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def _read_json(p: Path) -> dict:
    try:
        data = json.loads(_read_text(p))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _extract_constants() -> dict:
    """Parse gse_generate.py to extract ACTIVITY_NAMES and SPECIALIZED_AGENTS."""
    gen = _read_text(GSE_ONE / "gse_generate.py")
    result = {"ACTIVITY_NAMES": [], "SPECIALIZED_AGENTS": []}
    for key in result:
        match = re.search(
            rf"^{key}\s*=\s*\[(.*?)\]",
            gen,
            re.DOTALL | re.MULTILINE,
        )
        if match:
            content = match.group(1)
            items = re.findall(r'"([^"]+)"', content)
            result[key] = items
    return result


def _strip_md_ext(names: list) -> list:
    return [n[:-3] if n.endswith(".md") else n for n in names]


# ---------------------------------------------------------------------------
# Category 1 — Version consistency
# ---------------------------------------------------------------------------


def audit_version() -> list:
    findings: list = []
    version = _read_text(REPO_ROOT / "VERSION").strip()
    if not version:
        return [Finding("version", "error", "VERSION file missing or empty")]

    claude_v = _read_json(PLUGIN / ".claude-plugin" / "plugin.json").get("version", "")
    cursor_v = _read_json(PLUGIN / ".cursor-plugin" / "plugin.json").get("version", "")
    opencode_json = _read_json(PLUGIN / "opencode" / "opencode.json")
    opencode_v = ""
    if isinstance(opencode_json.get("gse"), dict):
        opencode_v = opencode_json["gse"].get("version", "")

    for name, v in [("Claude", claude_v), ("Cursor", cursor_v), ("opencode", opencode_v)]:
        if not v:
            findings.append(
                Finding(
                    "version",
                    "warning",
                    f"{name} manifest has no version field",
                    "",
                    "Check manifest generation in gse_generate.py",
                )
            )
        elif v != version:
            findings.append(
                Finding(
                    "version",
                    "error",
                    f"{name} manifest version mismatch",
                    f"VERSION={version}, manifest={v}",
                    "Regenerate: cd gse-one && python3 gse_generate.py --clean --verify",
                )
            )

    changelog = _read_text(REPO_ROOT / "CHANGELOG.md")
    m = re.search(r"##\s+\[(\d+\.\d+\.\d+)\]", changelog)
    if m:
        latest = m.group(1)
        if latest != version:
            findings.append(
                Finding(
                    "version",
                    "warning",
                    "CHANGELOG latest entry does not match VERSION",
                    f"VERSION={version}, latest CHANGELOG={latest}",
                    "Add a CHANGELOG entry for the current VERSION, or bump VERSION",
                )
            )

    if not findings:
        findings.append(
            Finding("version", "info", f"version consistency OK (all at {version})")
        )
    return findings


# ---------------------------------------------------------------------------
# Category 2 — File integrity
# ---------------------------------------------------------------------------


def audit_file_integrity() -> list:
    findings: list = []
    consts = _extract_constants()
    activity_names = consts["ACTIVITY_NAMES"]
    agents = _strip_md_ext(consts["SPECIALIZED_AGENTS"])

    # Activities
    missing_act = []
    for name in activity_names:
        if not (SRC / "activities" / f"{name}.md").exists():
            missing_act.append(name)
    if missing_act:
        findings.append(
            Finding(
                "file_integrity",
                "error",
                f"{len(missing_act)} activity sources missing in src/activities/",
                ", ".join(missing_act),
                "Create the missing .md files or remove from ACTIVITY_NAMES",
            )
        )

    # Orphan activities
    if (SRC / "activities").exists():
        files = {p.stem for p in (SRC / "activities").glob("*.md")}
        orphans = files - set(activity_names)
        if orphans:
            findings.append(
                Finding(
                    "file_integrity",
                    "warning",
                    f"{len(orphans)} orphan activity file(s) not in ACTIVITY_NAMES",
                    ", ".join(sorted(orphans)),
                    "Add to ACTIVITY_NAMES or delete the file",
                )
            )

    # Agents
    missing_ag = []
    for name in agents:
        if not (SRC / "agents" / f"{name}.md").exists():
            missing_ag.append(name)
    if missing_ag:
        findings.append(
            Finding(
                "file_integrity",
                "error",
                f"{len(missing_ag)} specialized agent sources missing in src/agents/",
                ", ".join(missing_ag),
                "Create the missing .md files or remove from SPECIALIZED_AGENTS",
            )
        )

    # Orphan agents
    if (SRC / "agents").exists():
        files = {p.stem for p in (SRC / "agents").glob("*.md")}
        known = set(agents) | {"gse-orchestrator"}
        orphans = files - known
        if orphans:
            findings.append(
                Finding(
                    "file_integrity",
                    "warning",
                    f"{len(orphans)} orphan agent file(s) in src/agents/",
                    ", ".join(sorted(orphans)),
                    "Add to SPECIALIZED_AGENTS or delete the file",
                )
            )

    if not findings:
        findings.append(
            Finding(
                "file_integrity",
                "info",
                f"all {len(activity_names)} activities + {len(agents)} agents + orchestrator present",
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Category 3 — Plugin parity
# ---------------------------------------------------------------------------


def audit_plugin_parity() -> list:
    findings: list = []
    consts = _extract_constants()
    n_act = len(consts["ACTIVITY_NAMES"])
    n_ag = len(consts["SPECIALIZED_AGENTS"])

    checks = [
        (
            "Claude skills count",
            len(list((PLUGIN / "skills").glob("*/SKILL.md"))) if (PLUGIN / "skills").exists() else 0,
            n_act,
        ),
        (
            "Cursor commands count",
            len(list((PLUGIN / "commands").glob("gse-*.md"))) if (PLUGIN / "commands").exists() else 0,
            n_act,
        ),
        (
            "opencode skills count",
            len(list((PLUGIN / "opencode" / "skills").glob("*/SKILL.md"))) if (PLUGIN / "opencode" / "skills").exists() else 0,
            n_act,
        ),
        (
            "opencode commands count",
            len(list((PLUGIN / "opencode" / "commands").glob("gse-*.md"))) if (PLUGIN / "opencode" / "commands").exists() else 0,
            n_act,
        ),
        (
            "Claude specialized agents count",
            len([p for p in (PLUGIN / "agents").glob("*.md") if p.stem != "gse-orchestrator"]) if (PLUGIN / "agents").exists() else 0,
            n_ag,
        ),
        (
            "opencode specialized agents count",
            len(list((PLUGIN / "opencode" / "agents").glob("*.md"))) if (PLUGIN / "opencode" / "agents").exists() else 0,
            n_ag,
        ),
    ]

    for name, actual, expected in checks:
        if actual != expected:
            findings.append(
                Finding(
                    "plugin_parity",
                    "error",
                    name,
                    f"expected {expected}, got {actual}",
                    "Regenerate plugin: cd gse-one && python3 gse_generate.py --clean --verify",
                )
            )

    if not findings:
        findings.append(
            Finding(
                "plugin_parity",
                "info",
                "plugin parity OK (Claude / Cursor / opencode all match expected counts)",
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Category 4 — Cross-file references
# ---------------------------------------------------------------------------


def audit_cross_refs() -> list:
    findings: list = []
    consts = _extract_constants()
    activity_names = set(consts["ACTIVITY_NAMES"])
    agent_names = set(_strip_md_ext(consts["SPECIALIZED_AGENTS"]))

    # Grep spec + design for /gse:X mentions
    for doc_path in [REPO_ROOT / "gse-one-spec.md", REPO_ROOT / "gse-one-implementation-design.md"]:
        text = _read_text(doc_path)
        mentioned = set(re.findall(r"/gse:([a-z-]+)", text))
        # Filter out known sub-options (e.g., /gse:plan --strategic)
        unknown = mentioned - activity_names
        # Also ignore any that's a prefix (like "deliver" in "/gse:deliver")
        if unknown:
            findings.append(
                Finding(
                    "cross_refs",
                    "warning",
                    f"{doc_path.name} mentions /gse:X not in ACTIVITY_NAMES",
                    ", ".join(sorted(unknown)),
                    "Either add to ACTIVITY_NAMES, or correct the reference",
                )
            )

    # Check agent references in activities
    unknown_agents = set()
    if (SRC / "activities").exists():
        for act_file in (SRC / "activities").glob("*.md"):
            text = _read_text(act_file)
            # Match patterns like "agents/X.md" or "X agent"
            for m in re.findall(r"agents/([a-z][a-z-]+)\.md", text):
                if m not in agent_names and m != "gse-orchestrator":
                    unknown_agents.add(f"{act_file.stem}.md → {m}")
    if unknown_agents:
        findings.append(
            Finding(
                "cross_refs",
                "warning",
                f"{len(unknown_agents)} activity references to unknown agents",
                ", ".join(sorted(unknown_agents)[:5]),
                "Fix the reference or add the agent to SPECIALIZED_AGENTS",
            )
        )

    if not findings:
        findings.append(
            Finding("cross_refs", "info", "cross-file references resolve correctly")
        )
    return findings


# ---------------------------------------------------------------------------
# Category 5 — Numeric consistency
# ---------------------------------------------------------------------------


def audit_numeric() -> list:
    findings: list = []
    consts = _extract_constants()
    n_act = len(consts["ACTIVITY_NAMES"])
    n_ag = len(consts["SPECIALIZED_AGENTS"])

    spec = _read_text(REPO_ROOT / "gse-one-spec.md")
    design = _read_text(REPO_ROOT / "gse-one-implementation-design.md")

    # Check for numeric claims in spec
    for doc_name, text in [("spec", spec), ("design", design)]:
        # "N commands"
        for m in re.finditer(r"(\d+)\s+commands?\b", text):
            claimed = int(m.group(1))
            if claimed != n_act and claimed not in (n_act - 1, n_act + 1):
                findings.append(
                    Finding(
                        "numeric",
                        "warning",
                        f"{doc_name} claims '{claimed} commands' — actual ACTIVITY_NAMES count is {n_act}",
                        f"text: ...{text[max(0, m.start()-30):m.end()+30]}...",
                        f"Update to '{n_act} commands'",
                        location=f"{doc_name}",
                    )
                )
        # "N specialized agents"
        for m in re.finditer(r"(\d+)\s+specialized(?:\s+agents?|\s+roles?)?", text):
            claimed = int(m.group(1))
            if claimed != n_ag:
                findings.append(
                    Finding(
                        "numeric",
                        "warning",
                        f"{doc_name} claims '{claimed} specialized' — actual SPECIALIZED_AGENTS count is {n_ag}",
                        f"text: ...{text[max(0, m.start()-30):m.end()+30]}...",
                        f"Update to '{n_ag} specialized'",
                        location=f"{doc_name}",
                    )
                )

    if not findings:
        findings.append(
            Finding(
                "numeric",
                "info",
                f"numeric claims consistent: {n_act} commands, {n_ag} specialized agents",
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Category 6 — Link integrity
# ---------------------------------------------------------------------------


def audit_links() -> list:
    findings: list = []
    broken = []

    # Scan .md files under repo for gse-one/ paths
    md_files = []
    for base in [REPO_ROOT, GSE_ONE]:
        if base.exists():
            md_files.extend(base.rglob("*.md"))

    # De-duplicate and exclude _LOCAL/, plugin/ regenerated dirs
    seen = set()
    unique_md = []
    for f in md_files:
        if "_LOCAL" in f.parts or "_ARCHIVED" in f.parts:
            continue
        if f in seen:
            continue
        seen.add(f)
        unique_md.append(f)

    for f in unique_md:
        text = _read_text(f)
        # Match `gse-one/...` paths (simple heuristic)
        for m in re.finditer(r"`(gse-one/[a-zA-Z0-9_./-]+)`", text):
            path = m.group(1)
            target = REPO_ROOT / path
            if not target.exists():
                broken.append(f"{f.relative_to(REPO_ROOT)} → {path}")

    if broken:
        findings.append(
            Finding(
                "links",
                "warning",
                f"{len(broken)} broken documentation link(s)",
                "; ".join(broken[:5]) + ("..." if len(broken) > 5 else ""),
                "Fix the path or remove the reference",
            )
        )
    else:
        findings.append(
            Finding("links", "info", "all gse-one/ documentation links resolve")
        )
    return findings


# ---------------------------------------------------------------------------
# Category 7 — Git hygiene
# ---------------------------------------------------------------------------


def audit_git() -> list:
    findings: list = []
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode != 0:
            return [Finding("git", "info", "not a git repository or git not available")]
        lines = [line for line in r.stdout.splitlines() if line.strip()]
        if not lines:
            findings.append(Finding("git", "info", "working tree clean"))
        else:
            plugin_dirty = [l for l in lines if "gse-one/plugin/" in l]
            if plugin_dirty:
                findings.append(
                    Finding(
                        "git",
                        "warning",
                        f"{len(plugin_dirty)} uncommitted plugin/ file(s) — should be regenerated and committed",
                        "\n".join(plugin_dirty[:5]),
                        "Run `python3 gse_generate.py --clean --verify` and commit",
                    )
                )
            else:
                findings.append(
                    Finding(
                        "git",
                        "info",
                        f"{len(lines)} uncommitted source file(s) (plugin/ is clean)",
                    )
                )
    except FileNotFoundError:
        findings.append(Finding("git", "info", "git not available"))
    except subprocess.TimeoutExpired:
        findings.append(Finding("git", "warning", "git status timed out"))
    return findings


# ---------------------------------------------------------------------------
# Category 8 — Python quality
# ---------------------------------------------------------------------------


def audit_python() -> list:
    findings: list = []
    py_files = []
    for base in [GSE_ONE, REPO_ROOT / ".claude"]:
        if base.exists():
            py_files.extend(base.rglob("*.py"))

    # Skip __pycache__ and venvs
    py_files = [
        f
        for f in py_files
        if "__pycache__" not in f.parts and ".venv" not in f.parts
    ]

    syntax_errors = []
    for f in py_files:
        try:
            ast.parse(_read_text(f))
        except SyntaxError as e:
            syntax_errors.append(f"{f.relative_to(REPO_ROOT)}: {e}")
    if syntax_errors:
        findings.append(
            Finding(
                "python",
                "error",
                f"{len(syntax_errors)} Python file(s) with syntax errors",
                "\n".join(syntax_errors[:3]),
                "Fix the syntax errors",
            )
        )

    # Check @gse-tool header on plugin/tools/*.py
    tools_dir = PLUGIN / "tools"
    missing_header = []
    if tools_dir.exists():
        for f in tools_dir.glob("*.py"):
            if f.name.startswith("__"):
                continue
            text = _read_text(f)
            lines = text.split("\n", 3)
            header_present = any("# @gse-tool" in l for l in lines[:3])
            if not header_present:
                missing_header.append(f.name)
    if missing_header:
        findings.append(
            Finding(
                "python",
                "warning",
                f"{len(missing_header)} tool(s) missing @gse-tool header",
                ", ".join(missing_header),
                "Add `# @gse-tool <name> <version>` on line 2 of the file",
            )
        )

    if not findings:
        findings.append(
            Finding(
                "python",
                "info",
                f"{len(py_files)} Python files: syntax OK, headers present",
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Category 9 — Template schema
# ---------------------------------------------------------------------------


def audit_templates() -> list:
    findings: list = []
    templates_dir = SRC / "templates"
    if not templates_dir.exists():
        return [Finding("templates", "info", "no src/templates/ directory")]

    # JSON templates: parse
    json_errors = []
    for f in templates_dir.rglob("*.json"):
        try:
            json.loads(_read_text(f))
        except json.JSONDecodeError as e:
            json_errors.append(f"{f.relative_to(templates_dir)}: {e}")
    if json_errors:
        findings.append(
            Finding(
                "templates",
                "error",
                f"{len(json_errors)} JSON template(s) invalid",
                "\n".join(json_errors),
                "Fix the JSON syntax",
            )
        )

    # YAML templates
    if _HAS_YAML:
        yaml_errors = []
        for f in templates_dir.rglob("*.yaml"):
            try:
                yaml.safe_load(_read_text(f))
            except yaml.YAMLError as e:  # type: ignore[attr-defined]
                yaml_errors.append(f"{f.relative_to(templates_dir)}: {str(e)[:100]}")
        if yaml_errors:
            findings.append(
                Finding(
                    "templates",
                    "error",
                    f"{len(yaml_errors)} YAML template(s) invalid",
                    "\n".join(yaml_errors),
                    "Fix the YAML syntax",
                )
            )
        else:
            yaml_count = len(list(templates_dir.rglob("*.yaml")))
            if yaml_count:
                findings.append(
                    Finding(
                        "templates",
                        "info",
                        f"{yaml_count} YAML template(s) parse correctly (PyYAML available)",
                    )
                )
    else:
        yaml_count = len(list(templates_dir.rglob("*.yaml")))
        if yaml_count:
            findings.append(
                Finding(
                    "templates",
                    "info",
                    f"{yaml_count} YAML template(s) not validated (PyYAML not installed)",
                    "Install with: pip install pyyaml",
                    "Optional dependency for deeper YAML validation",
                )
            )

    # Dockerfile.* have ARG SOURCE_COMMIT
    missing_arg = []
    for f in templates_dir.glob("Dockerfile.*"):
        text = _read_text(f)
        if "ARG SOURCE_COMMIT" not in text:
            missing_arg.append(f.name)
    if missing_arg:
        findings.append(
            Finding(
                "templates",
                "warning",
                f"{len(missing_arg)} Dockerfile template(s) missing ARG SOURCE_COMMIT",
                ", ".join(missing_arg),
                "Add `ARG SOURCE_COMMIT=unknown` after FROM (see references/hetzner-infrastructure.md §7)",
            )
        )

    if not findings or all(f.severity == "info" for f in findings):
        findings.append(
            Finding("templates", "info", "template schemas OK"),
        )
    return findings


# ---------------------------------------------------------------------------
# Category 10 — TODO/FIXME scan
# ---------------------------------------------------------------------------


def audit_todos() -> list:
    findings: list = []
    hits: list = []
    pattern = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")

    scan_roots = [REPO_ROOT, GSE_ONE]
    seen = set()
    for base in scan_roots:
        for ext in ("*.md", "*.py", "*.yaml"):
            for f in base.rglob(ext):
                if "_LOCAL" in f.parts or "_ARCHIVED" in f.parts:
                    continue
                if "__pycache__" in f.parts or ".venv" in f.parts:
                    continue
                if f in seen:
                    continue
                seen.add(f)
                text = _read_text(f)
                for i, line in enumerate(text.split("\n"), start=1):
                    if pattern.search(line):
                        hits.append(f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()[:80]}")

    if hits:
        findings.append(
            Finding(
                "todos",
                "info",
                f"{len(hits)} TODO/FIXME/XXX/HACK occurrence(s) found",
                "\n".join(hits[:10]) + ("\n..." if len(hits) > 10 else ""),
                "Review and resolve when possible",
            )
        )
    else:
        findings.append(Finding("todos", "info", "no TODO/FIXME/XXX/HACK markers"))
    return findings


# ---------------------------------------------------------------------------
# Category 11 — Test coverage (structural heuristic)
# ---------------------------------------------------------------------------


def audit_test_coverage() -> list:
    findings: list = []
    deploy_py = PLUGIN / "tools" / "deploy.py"
    test_deploy = REPO_ROOT / "gse-one" / "tests" / "test_deploy.py"

    if not deploy_py.exists() or not test_deploy.exists():
        return [Finding("test_coverage", "info", "deploy.py or test_deploy.py missing (skip)")]

    # Extract public functions from deploy.py
    try:
        tree = ast.parse(_read_text(deploy_py))
    except SyntaxError:
        return [Finding("test_coverage", "warning", "deploy.py has syntax errors, skip coverage")]

    public_funcs = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]

    test_text = _read_text(test_deploy)

    uncovered = []
    for fn in public_funcs:
        # Heuristic: either function name or TestClassName(Tests) mentions fn
        if fn in test_text or fn.replace("_", "") in test_text.replace("_", ""):
            continue
        uncovered.append(fn)

    if uncovered:
        findings.append(
            Finding(
                "test_coverage",
                "warning",
                f"{len(uncovered)}/{len(public_funcs)} public function(s) in deploy.py without matching test",
                ", ".join(uncovered),
                "Add tests or document why no test is needed (e.g., infra-dependent)",
            )
        )
    else:
        findings.append(
            Finding(
                "test_coverage",
                "info",
                f"all {len(public_funcs)} public functions in deploy.py have a matching test heuristic",
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Category 12 — Last-verified freshness
# ---------------------------------------------------------------------------


def audit_freshness() -> list:
    findings: list = []
    pattern = re.compile(r"last\s+verified\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
    today = datetime.now(timezone.utc).date()
    stale_days = 180
    hits = []

    for base in [REPO_ROOT, GSE_ONE]:
        for ext in ("*.md", "*.py"):
            for f in base.rglob(ext):
                if "_LOCAL" in f.parts or "_ARCHIVED" in f.parts:
                    continue
                text = _read_text(f)
                for m in pattern.finditer(text):
                    try:
                        date_str = m.group(1)
                        verified = datetime.strptime(date_str, "%Y-%m-%d").date()
                        age = (today - verified).days
                        hits.append(
                            {
                                "file": f.relative_to(REPO_ROOT),
                                "date": date_str,
                                "age": age,
                            }
                        )
                    except ValueError:
                        continue

    stale = [h for h in hits if h["age"] > stale_days]
    if stale:
        findings.append(
            Finding(
                "freshness",
                "warning",
                f"{len(stale)} 'last verified' marker(s) older than {stale_days} days",
                "; ".join(f"{h['file']}: {h['date']} ({h['age']}d ago)" for h in stale[:5]),
                "Re-verify the referenced content and update the date",
            )
        )
    elif hits:
        findings.append(
            Finding(
                "freshness",
                "info",
                f"{len(hits)} 'last verified' marker(s), all recent (< {stale_days} days)",
            )
        )
    else:
        findings.append(
            Finding("freshness", "info", "no 'last verified' markers found")
        )
    return findings


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------


_CATEGORY_FUNCS = {
    "version": audit_version,
    "file_integrity": audit_file_integrity,
    "plugin_parity": audit_plugin_parity,
    "cross_refs": audit_cross_refs,
    "numeric": audit_numeric,
    "links": audit_links,
    "git": audit_git,
    "python": audit_python,
    "templates": audit_templates,
    "todos": audit_todos,
    "test_coverage": audit_test_coverage,
    "freshness": audit_freshness,
}


def run_audit(categories: Optional[list] = None) -> Report:
    cats = categories or CATEGORIES
    version = _read_text(REPO_ROOT / "VERSION").strip() or "unknown"
    report = Report(
        version=version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        repo_root=str(REPO_ROOT),
    )
    for cat in cats:
        fn = _CATEGORY_FUNCS.get(cat)
        if fn is None:
            continue
        try:
            report.findings.extend(fn())
        except Exception as e:  # noqa: BLE001
            report.findings.append(
                Finding(
                    cat,
                    "error",
                    f"audit of category '{cat}' failed with exception",
                    str(e),
                    "Report this as a bug in audit.py",
                )
            )
    return report


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_markdown(report: Report) -> str:
    lines = []
    lines.append("# GSE-One Methodology Audit")
    lines.append("")
    lines.append(f"**Repository:** `{report.repo_root}`")
    lines.append(f"**VERSION:** {report.version}")
    lines.append(f"**Timestamp:** {report.timestamp}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- 🔴 **Errors:** {len(report.errors())}")
    lines.append(f"- 🟡 **Warnings:** {len(report.warnings())}")
    lines.append(f"- 🔵 **Info:** {len(report.info())}")
    lines.append("")

    if report.errors():
        lines.append("## 🔴 Errors")
        lines.append("")
        for i, f in enumerate(report.errors(), 1):
            lines.append(f"### E{i:02d} — [{f.category}] {f.title}")
            if f.detail:
                lines.append(f"**Detail:** {f.detail}")
            if f.location:
                lines.append(f"**Location:** `{f.location}`")
            if f.fix_hint:
                lines.append(f"**Fix hint:** {f.fix_hint}")
            lines.append("")

    if report.warnings():
        lines.append("## 🟡 Warnings")
        lines.append("")
        for i, f in enumerate(report.warnings(), 1):
            lines.append(f"### W{i:02d} — [{f.category}] {f.title}")
            if f.detail:
                lines.append(f"**Detail:** {f.detail}")
            if f.location:
                lines.append(f"**Location:** `{f.location}`")
            if f.fix_hint:
                lines.append(f"**Fix hint:** {f.fix_hint}")
            lines.append("")

    if report.info():
        lines.append("## 🔵 Info")
        lines.append("")
        for i, f in enumerate(report.info(), 1):
            title = f"I{i:02d} — [{f.category}] {f.title}"
            if f.detail:
                lines.append(f"- **{title}** — {f.detail}")
            else:
                lines.append(f"- **{title}**")
        lines.append("")

    # Conclusion
    lines.append("## Conclusion")
    lines.append("")
    if report.errors():
        lines.append("❌ **Errors found** — fix before release.")
    elif report.warnings():
        lines.append("🟡 **Warnings** — review and address when possible.")
    else:
        lines.append("✅ **Pass** — all checks clean.")
    lines.append("")

    return "\n".join(lines)


def render_json(report: Report) -> str:
    data = {
        "version": report.version,
        "timestamp": report.timestamp,
        "repo_root": report.repo_root,
        "summary": {
            "errors": len(report.errors()),
            "warnings": len(report.warnings()),
            "info": len(report.info()),
        },
        "findings": [asdict(f) for f in report.findings],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="audit.py",
        description="GSE-One methodology repository auditor (deterministic checks).",
    )
    p.add_argument(
        "--format",
        choices=["md", "json"],
        default="md",
        help="Output format (default: md)",
    )
    p.add_argument(
        "--category",
        choices=CATEGORIES,
        action="append",
        help="Run only specified categories (can be repeated)",
    )
    p.add_argument(
        "--cluster",
        metavar="JOB_ID",
        help="Filter findings to files within the named catalog job (e.g. deploy-cluster)",
    )
    p.add_argument(
        "--list-clusters",
        action="store_true",
        help="List all catalog jobs with their IDs and file counts, then exit",
    )
    p.add_argument(
        "--fail-on",
        choices=["error", "warning"],
        default=None,
        help="Exit non-zero if findings at this severity or higher",
    )
    return p


def _filter_by_cluster(report: Report, job_id: str) -> Report:
    """Return a new Report with findings filtered to files in the named job.

    Findings without a file attribution (global checks like 'version',
    'plugin_parity', 'git') are retained as context; only file-scoped
    findings are filtered.
    """
    # Import locally to avoid hard dependency at module load
    try:
        from audit_catalog import load_catalog, files_in_cluster, CatalogError
    except ImportError:
        # audit_catalog.py not importable — return report unchanged
        return report
    try:
        jobs = load_catalog(REPO_ROOT)
    except CatalogError as e:
        report.findings.append(
            Finding(
                "catalog",
                "warning",
                "Cluster filter requested but catalog load failed",
                str(e),
                "Check .claude/audit-jobs.json exists and is valid",
            )
        )
        return report

    target = next((j for j in jobs if j.id == job_id), None)
    if not target:
        report.findings.append(
            Finding(
                "catalog",
                "error",
                f"Cluster '{job_id}' not found in catalog",
                "Available: " + ", ".join(j.id for j in jobs),
                "Check the catalog or use --list-clusters",
            )
        )
        return report

    cluster_files = files_in_cluster(target, REPO_ROOT)
    kept = []
    for f in report.findings:
        # Keep findings without a file attribution (global checks)
        if not f.file:
            kept.append(f)
            continue
        # Keep findings whose file is in the cluster
        abs_path = str((REPO_ROOT / f.file).resolve())
        if abs_path in cluster_files:
            kept.append(f)
    report.findings = kept
    return report


def _list_clusters() -> int:
    try:
        from audit_catalog import load_catalog, CatalogError
    except ImportError:
        print("error: audit_catalog module not available", file=sys.stderr)
        return 2
    try:
        jobs = load_catalog(REPO_ROOT)
    except CatalogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    by_cat = {}
    for job in jobs:
        by_cat.setdefault(job.category, []).append(job)
    for cat in sorted(by_cat):
        print(f"\nCategory {cat}:")
        for job in by_cat[cat]:
            file_count = len(job.files)
            print(
                f"  {job.id:40s} [{job.type:22s}] files={file_count}"
            )
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Sidebar: --list-clusters is a standalone mode
    if args.list_clusters:
        return _list_clusters()

    # Context detection: must be in a gensem-like repo
    if not (REPO_ROOT / "gse-one-spec.md").exists():
        print(
            "error: this command audits a GSE-One methodology repository.\n"
            f"Missing marker: {REPO_ROOT / 'gse-one-spec.md'}",
            file=sys.stderr,
        )
        return 3
    if not (GSE_ONE / "gse_generate.py").exists():
        print(
            "error: this command audits a GSE-One methodology repository.\n"
            f"Missing marker: {GSE_ONE / 'gse_generate.py'}",
            file=sys.stderr,
        )
        return 3

    report = run_audit(args.category)

    if args.cluster:
        report = _filter_by_cluster(report, args.cluster)

    if args.format == "json":
        print(render_json(report))
    else:
        print(render_markdown(report))

    if args.fail_on == "error" and report.errors():
        return 1
    if args.fail_on == "warning" and (report.errors() or report.warnings()):
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
