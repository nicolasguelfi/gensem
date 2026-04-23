#!/usr/bin/env python3
# @gse-tool audit 1.0
"""GSE-One methodology repository auditor — deterministic checks only.

Usage:
    python3 gse-one/audit.py                       # full, markdown output + auto-save
    python3 gse-one/audit.py --format json         # for CI / scripting
    python3 gse-one/audit.py --category version    # only one category
    python3 gse-one/audit.py --cluster deploy-cluster  # only files in a cluster
    python3 gse-one/audit.py --list-clusters       # show catalog clusters
    python3 gse-one/audit.py --fail-on error       # exit 1 on errors
    python3 gse-one/audit.py --no-save             # stdout only, don't save
    python3 gse-one/audit.py --save-to <path>      # explicit output path

By default the report is saved to `_LOCAL/audits/audit-<ISO-timestamp>.md`
(and copied to `_LOCAL/audits/latest.md` for convenience). The `_LOCAL/`
directory is gitignored, so saved reports never leak into git. Use
`--no-save` to disable the auto-save (stdout only).

For reasoning-based checks (LLM), use the `/gse-audit` slash command in
Claude Code — it invokes this script for deterministic checks, then
performs semantic reasoning via the methodology-auditor agent across 20
audit jobs defined in .claude/audit-jobs.json. The slash command saves
its augmented report (deterministic + LLM findings) to the same
`_LOCAL/audits/` directory.

This tool audits the gensem repo itself (not user projects). It lives in
gse-one/ alongside gse_generate.py (both are maintainer tools).

Dependencies:
    stdlib only for all core checks. PyYAML is an optional dependency used
    by audit_templates() to validate YAML schema files under src/templates/;
    when missing, template YAML validation is skipped and other checks are
    unaffected (see the try/except block below).
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
    # Category F — Distribution hygiene (plugin-as-product invariants)
    "plugin_language",
    "plugin_secrets",
    "plugin_personal",
    "plugin_debug",
    "plugin_runtime_paths",
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
    job_id: str = "python-engine"  # which job produced this finding (for traceability)


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
    """Check VERSION file consistency across plugin manifests (Claude, Cursor) and generator."""
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
    """Check spec / design / activity / agent file presence against generator constants."""
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
    """Check Claude / Cursor / opencode plugin deployment has matching skill / agent / template counts."""
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
    """Check section and activity references across spec, design, activities, and agents resolve."""
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
    """Scan all relevant markdown and Python files for numeric claims that
    drift from reality (commands, agents, principles, modes).

    Extended in v0.47.0 to scan gse_generate.py, activities, agents, and
    repo-level docs (previously only spec + design).
    """
    findings: list = []
    consts = _extract_constants()
    n_act = len(consts["ACTIVITY_NAMES"])
    n_ag = len(consts["SPECIALIZED_AGENTS"])
    n_principles = 16  # P1-P16
    n_modes = 3  # Micro, Lightweight, Full

    # Files to scan for numeric claims.
    # CHANGELOG.md is intentionally excluded — its entries are historical
    # records of past states, not claims about the current state. Scanning it
    # flags every commit-level change as a drift, which is wrong by design.
    files_to_scan = []
    for name in ("gse-one-spec.md", "gse-one-implementation-design.md",
                 "README.md", "CLAUDE.md"):
        p = REPO_ROOT / name
        if p.exists():
            files_to_scan.append(p)

    gen_py = GSE_ONE / "gse_generate.py"
    if gen_py.exists():
        files_to_scan.append(gen_py)

    if (SRC / "activities").exists():
        files_to_scan.extend(sorted((SRC / "activities").glob("*.md")))
    if (SRC / "agents").exists():
        files_to_scan.extend(sorted((SRC / "agents").glob("*.md")))

    # Patterns: (regex, expected value, human label)
    # - Prefix `(?:^|\s)` (whitespace or start-of-line before the digit) avoids
    #   matching section numbers like "3.10 Commands" (digit after a dot) or
    #   principle identifiers like "P10 principle" (digit after a letter).
    # - "specialized" has a negative lookahead to exclude non-agent contexts
    #   like "4 specialized templates" (Dockerfile count, not agent count).
    patterns = [
        (re.compile(
            r"(?:^|\s)(\d+)\s+specialized\b(?!\s+(?:templates?|files?|Dockerfiles?|rules?|settings?|categories?))",
            re.IGNORECASE), n_ag, "specialized"),
        (re.compile(r"(?:^|\s)(\d+)\s+commands?\b", re.IGNORECASE), n_act,
         "commands"),
        # Negative lookahead skips partitive phrasing like "10 principle titles"
        # (a partition — 10 out of 16 titles — not a claim of 10 principles total).
        # Flagged as false positive class by audit v0.50 WC6 on CLAUDE.md:205.
        (re.compile(r"(?:^|\s)(\d+)\s+principles?\b(?!\s+(?:titles?|IDs?|names?|headers?|bullets?|entries?|of\s+\d+))", re.IGNORECASE),
         n_principles, "principles"),
    ]

    # Scan each file; aggregate by (file, pattern, claimed_value) to list
    # all line numbers
    for f in files_to_scan:
        text = _read_text(f)
        try:
            rel = f.relative_to(REPO_ROOT)
        except ValueError:
            rel = f
        lines = text.split("\n")
        for pattern, expected, what in patterns:
            # Key: claimed value; Value: (severity, line_numbers)
            # severity is "info" for ±1 drift (acceptable — often includes/excludes orchestrator),
            # "warning" for ≥2 drift (likely a real stale claim)
            claims_by_value: dict = {}
            for i, line in enumerate(lines, 1):
                for m in pattern.finditer(line):
                    claimed = int(m.group(1))
                    diff = abs(claimed - expected)
                    if diff == 0:
                        continue
                    severity = "info" if diff == 1 else "warning"
                    claims_by_value.setdefault((claimed, severity), []).append(i)
            for (claimed, severity), line_nums in claims_by_value.items():
                lines_summary = (
                    ", ".join(str(n) for n in line_nums[:6])
                    + (" ..." if len(line_nums) > 6 else "")
                )
                if severity == "info":
                    title = f"{rel.name} claims '{claimed} {what}' — expected {expected} (±1 drift, often includes/excludes orchestrator)"
                else:
                    title = f"{rel.name} claims '{claimed} {what}' — actual is {expected}"
                findings.append(
                    Finding(
                        "numeric",
                        severity,
                        title,
                        f"{len(line_nums)} occurrence(s) at lines: {lines_summary}",
                        f"Update to '{expected} {what}'" if severity == "warning" else "Verify: ±1 drift may be intentional (e.g., specialized vs total agent count)",
                        location=str(rel),
                        file=str(rel),
                    )
                )

    if not findings:
        findings.append(
            Finding(
                "numeric",
                "info",
                f"numeric claims consistent across {len(files_to_scan)} files "
                f"({n_act} commands, {n_ag} specialized agents, "
                f"{n_principles} principles)",
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Category 6 — Link integrity
# ---------------------------------------------------------------------------


def audit_links() -> list:
    """Check internal documentation link targets resolve (relative paths, anchors)."""
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
        # CHANGELOG.md is intentionally excluded — its entries are historical
        # records of past release states (Keep-a-Changelog convention), NOT
        # claims about the current repo state. A reference to a removed file
        # inside a past release block is correct historical narrative, not a
        # broken link. (False positive class flagged by audit v0.50 WC7.)
        if f.name == "CHANGELOG.md":
            continue
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
    """Check git working tree state relative to the main branch."""
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
    """Check Python syntax and @gse-tool headers on plugin/tools/*.py and maintainer scripts."""
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
    """Check template YAML schemas validate (requires optional PyYAML — skipped gracefully if absent)."""
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
    """Scan for TODO / FIXME / XXX / HACK markers across the corpus (excluding CHANGELOG historical narrative)."""
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
    """Check deploy.py test coverage — public functions in deploy.py should have matching tests in test_deploy.py."""
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
    """Check 'Last verified: YYYY-MM-DD' markers against a 180-day freshness budget (references/ volatile data)."""
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
# Categories 13-17 — Distribution hygiene (plugin as distributed product)
# These checks treat gse-one/plugin/ as a finished product with stricter
# invariants than the source tree (no French residuals, no secrets, no
# maintainer leaks, no debug residue, intact runtime-path references).
# ---------------------------------------------------------------------------


_PLUGIN_TEXT_EXTS = (".md", ".mdc", ".py", ".ts", ".json", ".yaml", ".yml")


def _iter_plugin_files(exts: tuple = _PLUGIN_TEXT_EXTS):
    for f in PLUGIN.rglob("*"):
        if not f.is_file() or f.suffix not in exts:
            continue
        if "__pycache__" in f.parts or ".venv" in f.parts:
            continue
        yield f


def audit_plugin_language() -> list:
    """Detect residual non-English prose in the distributed plugin.

    Rule: all content under gse-one/plugin/ must be English, except zones
    explicitly marked with `<!-- multilingual by design: <reason> -->`
    and language-selection UI labels (Français, Español, 日本語, etc.).

    Exclusion-zone semantics:
      - Opened by  `<!-- multilingual by design: <reason> -->`
      - Closed by  `<!-- /multilingual by design -->`  (explicit)
                   OR by the next markdown header (`### `, `## `, `# ` …)
                   (implicit; useful when the zone is an entire subsection).
    """
    findings: list = []
    accent_re = re.compile(r"[àâäçéèêëîïôöùûüÿœæÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒÆ]")
    marker_start_re = re.compile(
        r"<!--\s*multilingual by design", re.IGNORECASE
    )
    marker_end_re = re.compile(
        r"<!--\s*/\s*multilingual by design", re.IGNORECASE
    )
    header_re = re.compile(r"^#{1,6}\s")
    label_re = re.compile(
        r'label:\s*"(Français|Español|日本語|Deutsch|English)"'
    )
    prompt_re = re.compile(
        r"(Quelle langue|¿Qué idioma|どの言語|Welche Sprache)"
    )
    hits: list = []
    for f in _iter_plugin_files():
        text = _read_text(f)
        in_exclusion = False
        for i, line in enumerate(text.split("\n"), start=1):
            # Start has priority over end: a start-marker line may contain a
            # textual mention of the end-marker (documentation of the protocol).
            if marker_start_re.search(line):
                in_exclusion = True
                continue
            if marker_end_re.search(line):
                in_exclusion = False
                continue
            if header_re.match(line) and in_exclusion:
                in_exclusion = False
                # fall through — the header line itself is still audited
            if label_re.search(line) or prompt_re.search(line):
                continue
            if in_exclusion:
                continue
            if accent_re.search(line):
                hits.append(
                    f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()[:100]}"
                )

    if hits:
        findings.append(
            Finding(
                "plugin_language",
                "error",
                f"{len(hits)} residual non-English character(s) in distributed plugin",
                "\n".join(hits[:15]) + ("\n..." if len(hits) > 15 else ""),
                "Translate to English or protect the block with "
                "`<!-- multilingual by design: <reason> -->`",
            )
        )
    else:
        findings.append(
            Finding(
                "plugin_language",
                "info",
                "plugin/ is English-monolingual (excluded zones respected)",
            )
        )
    return findings


def audit_plugin_secrets() -> list:
    """Scan plugin/ for patterns that look like leaked secrets or credentials.

    Allow-lists:
      - Explicit placeholders: placeholder, example, dummy, fake, YOUR_, <tag>
      - Example strings: abc<digits>, test<digits>, live-abc<...>, sample-,
        changeme, xyz<digits>
      - Path-level: plugin/agents/security-auditor.md and its opencode
        mirror document secret detection patterns by role — their
        example strings are content, not leaks.
    """
    findings: list = []
    patterns = [
        (
            r"-----BEGIN\s+(RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "PEM private key",
        ),
        (r"\bsk-[a-zA-Z0-9]{20,}", "OpenAI-style API key"),
        (r"\bghp_[a-zA-Z0-9]{36}\b", "GitHub personal access token"),
        (r"\bxox[baprs]-[0-9]{10,}-", "Slack token"),
        (r"\bAKIA[0-9A-Z]{16}\b", "AWS access key ID"),
        (r"\bAIza[0-9A-Za-z\-_]{35}\b", "Google API key"),
        (r"\bBearer\s+[A-Za-z0-9._\-]{30,}", "Bearer token"),
        (
            r'(?i)\b(api_key|apikey|secret_key|auth_token|password)\s*[:=]\s*["\']([^"\']{16,})["\']',
            "assigned secret",
        ),
    ]
    placeholder_re = re.compile(
        r"(?i)(placeholder|example|dummy|fake|your[-_]|YOUR_|<[a-z]+>|"
        r"\babc[0-9a-z]+\b|\btest[0-9a-z]+\b|\bxyz[0-9a-z]*\b|"
        r"\blive[-_]abc|\bsample[-_]|changeme)"
    )
    path_allowlist = {
        "gse-one/plugin/agents/security-auditor.md",
        "gse-one/plugin/opencode/agents/security-auditor.md",
    }
    hits: list = []
    for f in _iter_plugin_files():
        rel = str(f.relative_to(REPO_ROOT))
        if rel in path_allowlist:
            continue
        text = _read_text(f)
        for i, line in enumerate(text.split("\n"), start=1):
            if placeholder_re.search(line):
                continue
            for pat, label in patterns:
                if re.search(pat, line):
                    hits.append(
                        f"{rel}:{i}: [{label}] {line.strip()[:80]}"
                    )
                    break

    for ext in (".env", ".pem", ".key", ".pfx", ".p12"):
        for f in PLUGIN.rglob(f"*{ext}"):
            hits.append(
                f"{f.relative_to(REPO_ROOT)}: forbidden file extension '{ext}'"
            )

    if hits:
        findings.append(
            Finding(
                "plugin_secrets",
                "error",
                f"{len(hits)} potential secret/credential leak(s) in plugin/",
                "\n".join(hits[:10]) + ("\n..." if len(hits) > 10 else ""),
                "Remove the secret or replace with an explicit placeholder "
                "(e.g., 'your-api-key-here')",
            )
        )
    else:
        findings.append(
            Finding(
                "plugin_secrets",
                "info",
                "no secret/credential patterns detected in plugin/",
            )
        )
    return findings


def audit_plugin_personal() -> list:
    """Scan plugin/ for maintainer-specific personal information leaks.

    Allow-list: standard Linux service-user home paths (deploy, root,
    ubuntu, admin, www-data, app, user, ec2-user, debian, pi, git,
    docker, jenkins, postgres, mysql) do NOT count as personal leaks —
    they are generic infrastructure conventions.
    """
    findings: list = []
    service_users = (
        "deploy|root|ubuntu|admin|www-data|app|user|ec2-user|debian|"
        "pi|git|docker|jenkins|postgres|mysql|redis|nginx|apache"
    )
    patterns = [
        (r"/Users/[a-z][a-z0-9._\-]*", "macOS personal path"),
        (
            rf"/home/(?!({service_users})\b)[a-z][a-z0-9._\-]*",
            "Linux personal path (non-service user)",
        ),
        (r"/Volumes/[A-Z][A-Za-z0-9_\-]*", "macOS volume path"),
        (r"\bnicolas\.guelfi\b", "maintainer email local-part"),
        (r"\bmessir\s+Dropbox\b", "Dropbox workspace hint"),
        (r"\bDropbox-[a-z0-9._\-]+\b", "Dropbox-account path"),
        (
            r"\b[a-zA-Z0-9._%+\-]+@(laposte\.net|uni\.lu)\b",
            "maintainer personal email",
        ),
    ]
    hits: list = []
    for f in _iter_plugin_files():
        text = _read_text(f)
        for i, line in enumerate(text.split("\n"), start=1):
            for pat, label in patterns:
                if re.search(pat, line):
                    hits.append(
                        f"{f.relative_to(REPO_ROOT)}:{i}: [{label}] "
                        f"{line.strip()[:80]}"
                    )
                    break

    if hits:
        findings.append(
            Finding(
                "plugin_personal",
                "error",
                f"{len(hits)} maintainer-identity leak(s) in plugin/",
                "\n".join(hits[:10]) + ("\n..." if len(hits) > 10 else ""),
                "Replace with generic placeholders: <user>, <project>, "
                "/path/to/...",
            )
        )
    else:
        findings.append(
            Finding(
                "plugin_personal",
                "info",
                "no maintainer-personal paths/identities in plugin/",
            )
        )
    return findings


def audit_plugin_debug() -> list:
    """Scan plugin/ for debug residue (prints, dead branches, commented-out code)."""
    findings: list = []
    cli_tools = {"dashboard.py", "deploy.py", "project-audit.py"}
    hits: list = []

    for f in PLUGIN.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        is_cli_tool = f.name in cli_tools and f.parent.name == "tools"
        text = _read_text(f)
        for i, line in enumerate(text.split("\n"), start=1):
            stripped = line.strip()
            if not is_cli_tool and re.match(r"(print|pprint)\s*\(", stripped):
                hits.append(
                    f"{f.relative_to(REPO_ROOT)}:{i}: debug print — "
                    f"{stripped[:80]}"
                )
            if re.match(
                r'if\s+(False|0|__name__\s*==\s*["\']debug["\'])\s*:', stripped
            ):
                hits.append(
                    f"{f.relative_to(REPO_ROOT)}:{i}: dead branch — "
                    f"{stripped[:80]}"
                )

    for f in PLUGIN.rglob("*.ts"):
        text = _read_text(f)
        for i, line in enumerate(text.split("\n"), start=1):
            if re.search(r"\bconsole\.(log|debug|info)\s*\(", line):
                hits.append(
                    f"{f.relative_to(REPO_ROOT)}:{i}: console.log — "
                    f"{line.strip()[:80]}"
                )

    code_comment_re = re.compile(r"^\s*(#|//)\s+.*[=(){};]")
    for f in list(PLUGIN.rglob("*.py")) + list(PLUGIN.rglob("*.ts")):
        if "__pycache__" in f.parts:
            continue
        text = _read_text(f)
        lines = text.split("\n")
        run = 0
        start = 0
        for i, line in enumerate(lines, start=1):
            if code_comment_re.match(line):
                if run == 0:
                    start = i
                run += 1
            else:
                if run >= 4:
                    hits.append(
                        f"{f.relative_to(REPO_ROOT)}:{start}: "
                        f"commented-out code block ({run} lines)"
                    )
                run = 0
        if run >= 4:
            hits.append(
                f"{f.relative_to(REPO_ROOT)}:{start}: "
                f"commented-out code block ({run} lines)"
            )

    if hits:
        findings.append(
            Finding(
                "plugin_debug",
                "warning",
                f"{len(hits)} debug residue occurrence(s) in plugin/",
                "\n".join(hits[:15]) + ("\n..." if len(hits) > 15 else ""),
                "Remove debug prints / dead branches / commented-out code. "
                "CLI tools (dashboard.py, deploy.py, project-audit.py) are "
                "allow-listed for print().",
            )
        )
    else:
        findings.append(
            Finding("plugin_debug", "info", "no debug residue in plugin/")
        )
    return findings


def audit_plugin_runtime_paths() -> list:
    """Verify that every `$(cat ~/.gse-one)/<subpath>` in plugin/ points to a
    subpath distributed by install.py in at least one install mode.
    """
    findings: list = []
    allowed_subpaths = {
        "tools",
        "templates",
        "references",
        "VERSION",
        "skills",
        "commands",
        "agents",
        "rules",
        "hooks",
        "opencode",
    }
    ref_re = re.compile(r"\$\(cat\s+~/\.gse-one\)/([A-Za-z0-9_\-]+)")
    hits_unknown: list = []
    seen_paths: dict = {}
    for f in _iter_plugin_files((".md", ".mdc", ".py", ".ts")):
        text = _read_text(f)
        for i, line in enumerate(text.split("\n"), start=1):
            for m in ref_re.finditer(line):
                top = m.group(1)
                seen_paths[top] = seen_paths.get(top, 0) + 1
                if top not in allowed_subpaths:
                    hits_unknown.append(
                        f"{f.relative_to(REPO_ROOT)}:{i}: "
                        f"unknown subpath '{top}' — {line.strip()[:80]}"
                    )

    if hits_unknown:
        findings.append(
            Finding(
                "plugin_runtime_paths",
                "error",
                f"{len(hits_unknown)} runtime path reference(s) to unknown subpath(s)",
                "\n".join(hits_unknown[:10])
                + ("\n..." if len(hits_unknown) > 10 else ""),
                f"Either add the subpath to install.py distribution or fix "
                f"the reference. Allowed roots: {sorted(allowed_subpaths)}",
            )
        )
    else:
        findings.append(
            Finding(
                "plugin_runtime_paths",
                "info",
                f"all $(cat ~/.gse-one)/X references valid "
                f"({len(seen_paths)} distinct roots used)",
            )
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
    "plugin_language": audit_plugin_language,
    "plugin_secrets": audit_plugin_secrets,
    "plugin_personal": audit_plugin_personal,
    "plugin_debug": audit_plugin_debug,
    "plugin_runtime_paths": audit_plugin_runtime_paths,
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
    p.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save the report to _LOCAL/audits/ (stdout only)",
    )
    p.add_argument(
        "--save-to",
        metavar="PATH",
        default=None,
        help="Explicit output file path (overrides default _LOCAL/audits/audit-<ts>.md)",
    )
    return p


def _save_report(rendered: str, fmt: str, save_to: Optional[Path] = None) -> Path:
    """Write the rendered report to disk. Returns the saved path.

    Default filename format (v0.47.0+): `audit-YYYY-MM-DD-HHMMSS-vX.Y.Z.<ext>`
    The date + version combo is readable and uniquely identifies each run.
    A convenience copy is also written as `latest.<ext>`.

    With save_to explicitly set: that exact path (no latest copy).
    """
    ext = "json" if fmt == "json" else "md"
    if save_to:
        save_to.parent.mkdir(parents=True, exist_ok=True)
        save_to.write_text(rendered, encoding="utf-8")
        return save_to

    audits_dir = REPO_ROOT / "_LOCAL" / "audits"
    audits_dir.mkdir(parents=True, exist_ok=True)
    # Date + time + version: readable and unique across same-day runs
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip() or "unknown"
    main_path = audits_dir / f"audit-{ts}-v{version}.{ext}"
    main_path.write_text(rendered, encoding="utf-8")

    # Convenience copy — always overwritten
    latest_path = audits_dir / f"latest.{ext}"
    latest_path.write_text(rendered, encoding="utf-8")

    return main_path


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

    rendered = render_json(report) if args.format == "json" else render_markdown(report)
    print(rendered)

    # Auto-save to _LOCAL/audits/ unless --no-save
    if not args.no_save:
        try:
            save_to = Path(args.save_to) if args.save_to else None
            saved_path = _save_report(rendered, args.format, save_to)
            rel = saved_path.relative_to(REPO_ROOT) if saved_path.is_absolute() else saved_path
            print(f"\n(saved to: {rel})", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"\nwarning: could not save report: {e}", file=sys.stderr)

    if args.fail_on == "error" and report.errors():
        return 1
    if args.fail_on == "warning" and (report.errors() or report.warnings()):
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
