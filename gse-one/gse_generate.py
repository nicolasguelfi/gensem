#!/usr/bin/env python3
"""
GSE-One Generator — Builds plugin/ from src/

Usage:
    python gse_generate.py [--clean] [--verify]

Mono-plugin architecture: ONE directory deployable on both Claude Code and Cursor.

Source layout:
    src/principles/    → 16 principle definitions (P1-P16)
    src/activities/    → 23 activity definitions (→ skills for Claude, commands for Cursor)
    src/agents/        → 9 agent roles (8 specialized + gse-orchestrator)
    src/templates/     → 15 artefact & config templates

Generated output:
    plugin/            → Single deployable directory
        .claude-plugin/plugin.json    ← Claude Code manifest
        .cursor-plugin/plugin.json    ← Cursor manifest
        skills/                       ← Claude Code activities (22 SKILL.md in subdirs)
        commands/                     ← Cursor activities (22 flat gse-<name>.md files)
        agents/                       ← Shared (9 agents, incl. orchestrator)
        templates/                    ← Shared (15 templates)
        rules/000-gse-methodology.mdc ← Cursor-specific (generated)
        hooks/hooks.claude.json       ← Claude-specific (generated)
        hooks/hooks.cursor.json       ← Cursor-specific (generated)
        settings.json                 ← Claude-specific (generated)

Activities are generated to the correct concept per platform:
  - Claude Code: skills/ (SKILL.md in subdirs) → /gse:go, /gse:plan (auto-namespaced)
  - Cursor: commands/ (flat gse-<name>.md) → /gse-go, /gse-plan (prefixed kebab-case)

The orchestrator agent and the .mdc rule are generated from the SAME
src/principles/ content, ensuring identical methodology on both platforms.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
VERSION = (REPO_ROOT / "VERSION").read_text().strip()
SRC = ROOT / "src"
PLUGIN = ROOT / "plugin"

PRINCIPLES_DIR = SRC / "principles"
ACTIVITIES_DIR = SRC / "activities"
AGENTS_DIR = SRC / "agents"
TEMPLATES_DIR = SRC / "templates"

ACTIVITY_NAMES = [
    "go", "hug", "learn", "backlog", "collect", "assess", "plan",
    "reqs", "design", "preview", "tests", "produce", "deliver",
    "review", "fix", "compound", "integrate", "deploy", "task", "status",
    "health", "pause", "resume",
]

SPECIALIZED_AGENTS = [
    "requirements-analyst.md", "architect.md", "test-strategist.md",
    "code-reviewer.md", "security-auditor.md", "ux-advocate.md",
    "guardrail-enforcer.md", "devil-advocate.md",
]

PLUGIN_DESCRIPTION = (
    "GSE-One — AI engineering companion for structured SDLC management. "
    "23 commands, adaptive risk analysis, unified backlog, knowledge transfer, "
    "worktree isolation."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def write_file(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote: {path.relative_to(ROOT)}")

def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)

def generate_command(src: Path, dst: Path, cmd_name: str) -> None:
    """Convert a SKILL.md source to a flat Cursor command file (gse-<name>.md).

    Injects name/description frontmatter in kebab-case for Cursor auto-discovery.
    """
    content = src.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            # Extract description from source frontmatter
            desc_match = re.search(r'description:\s*"(.+?)"', parts[1])
            desc = desc_match.group(1) if desc_match else f"GSE-One {cmd_name} command"
            body = parts[2]
            content = (
                f'---\n'
                f'name: "gse-{cmd_name}"\n'
                f'description: "{desc}"\n'
                f'---\n{body}'
            )
    write_file(dst, content)

def extract_body(filepath: Path) -> str:
    """Extract markdown body after YAML frontmatter (after second ---)."""
    content = filepath.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate(clean: bool = False) -> None:
    print(f"GSE-One Generator v{VERSION}")
    print(f"Root: {ROOT}\n")

    if clean and PLUGIN.exists():
        shutil.rmtree(PLUGIN)
        print("  cleaned plugin/\n")

    # 1. Activities → Skills (Claude Code) + Commands (Cursor)
    activity_count = sum(1 for n in ACTIVITY_NAMES if (ACTIVITIES_DIR / f"{n}.md").exists())

    print("Skills (Claude Code):")
    for name in ACTIVITY_NAMES:
        src_file = ACTIVITIES_DIR / f"{name}.md"
        dst_file = PLUGIN / "skills" / name / "SKILL.md"
        if src_file.exists():
            copy_file(src_file, dst_file)
        else:
            print(f"  WARNING: missing {name}.md")
    print(f"  {activity_count}/{len(ACTIVITY_NAMES)}\n")

    print("Commands (Cursor):")
    for name in ACTIVITY_NAMES:
        src_file = ACTIVITIES_DIR / f"{name}.md"
        dst_file = PLUGIN / "commands" / f"gse-{name}.md"
        if src_file.exists():
            generate_command(src_file, dst_file, name)
        else:
            print(f"  WARNING: missing {name}.md")
    print(f"  {activity_count}/{len(ACTIVITY_NAMES)}\n")

    # 2. Agents — 8 specialized (shared) + orchestrator (generated)
    print("Agents (specialized):")
    for agent_file in SPECIALIZED_AGENTS:
        src_file = AGENTS_DIR / agent_file
        if src_file.exists():
            copy_file(src_file, PLUGIN / "agents" / agent_file)
        else:
            print(f"  WARNING: missing {agent_file}")
    print(f"  {sum(1 for f in SPECIALIZED_AGENTS if (AGENTS_DIR / f).exists())}/{len(SPECIALIZED_AGENTS)}\n")

    # 3. Generate orchestrator + .mdc from src/principles/
    print("Methodology (from src/principles/ + src/agents/gse-orchestrator.md):")
    orchestrator_src = AGENTS_DIR / "gse-orchestrator.md"
    if orchestrator_src.exists():
        body = extract_body(orchestrator_src)

        # Claude: agents/gse-orchestrator.md
        orchestrator_content = (
            '---\n'
            'name: gse-orchestrator\n'
            'description: "GSE-One main orchestrator agent. Manages the full '
            'software development lifecycle with 23 commands under the /gse: prefix. '
            'Adapts language, decisions, and autonomy to the user\'s profile."\n'
            '---\n\n'
            f'{body}\n'
        )
        write_file(PLUGIN / "agents" / "gse-orchestrator.md", orchestrator_content)

        # Cursor: rules/000-gse-methodology.mdc
        mdc_content = (
            '---\n'
            'description: "GSE-One methodology — 16 core principles, state management, '
            'orchestration decision tree. This is the agent\'s permanent identity."\n'
            'alwaysApply: true\n'
            '---\n\n'
            f'{body}\n'
        )
        write_file(PLUGIN / "rules" / "000-gse-methodology.mdc", mdc_content)

        # Verify identical body
        agent_body = extract_body(PLUGIN / "agents" / "gse-orchestrator.md")
        mdc_body = extract_body(PLUGIN / "rules" / "000-gse-methodology.mdc")
        status = "IDENTICAL" if agent_body == mdc_body else "DIVERGENT!"
        print(f"  Body parity check: {status}\n")
    else:
        print("  ERROR: src/agents/gse-orchestrator.md not found!\n")

    # 4. Templates (shared)
    print("Templates:")
    count = 0
    if TEMPLATES_DIR.exists():
        for src_file in sorted(TEMPLATES_DIR.rglob("*")):
            if src_file.is_file():
                rel = src_file.relative_to(TEMPLATES_DIR)
                copy_file(src_file, PLUGIN / "templates" / rel)
                count += 1
    print(f"  {count}\n")

    # 4.5. Tools directory (dashboard etc.)
    print("Tools:")
    tools_src = ROOT / "plugin" / "tools"
    if tools_src.is_dir():
        print(f"  tools/ already in plugin ({sum(1 for _ in tools_src.glob('*.py'))} scripts)\n")
    else:
        print(f"  WARNING: plugin/tools/ not found\n")

    # 5. Manifests
    print("Manifests:")
    claude_manifest = {
        "name": "gse",
        "description": PLUGIN_DESCRIPTION,
        "version": VERSION,
        "author": {"name": "GSE-One Project"},
        "repository": "https://github.com/gse-one/gse-one",
        "skills": "./skills/",
        "agents": "./agents/",
        "hooks": "./hooks/hooks.claude.json",
    }
    write_file(PLUGIN / ".claude-plugin" / "plugin.json",
               json.dumps(claude_manifest, indent=2) + "\n")

    cursor_manifest = {
        "name": "gse",
        "displayName": "GSE-One",
        "description": PLUGIN_DESCRIPTION,
        "version": VERSION,
        "author": {"name": "GSE-One Project"},
        "repository": "https://github.com/gse-one/gse-one",
        "commands": "./commands/",
        "agents": "./agents/",
        "rules": "./rules/",
        "hooks": "./hooks/hooks.cursor.json",
    }
    write_file(PLUGIN / ".cursor-plugin" / "plugin.json",
               json.dumps(cursor_manifest, indent=2) + "\n")
    print()

    # 6. Settings (Claude-specific)
    print("Settings:")
    write_file(PLUGIN / "settings.json", '{\n  "agent": "gse-orchestrator"\n}\n')
    print()

    # 7. Hooks
    print("Hooks:")
    generate_hooks()
    print()

    print(f"Plugin generated: {PLUGIN.relative_to(ROOT)}/")
    total = sum(1 for _ in PLUGIN.rglob("*") if _.is_file())
    print(f"Total files: {total}\n")


def generate_hooks() -> None:
    """Generate platform-specific hooks with cross-platform Python commands."""
    # Shared hook logic (Python — works on macOS, Linux, and Windows)
    pre_bash_commit = (
        "python3 -c \""
        "import os,subprocess,sys; "
        "t=os.environ.get('CLAUDE_TOOL_INPUT',''); "
        "c=t.startswith('git commit'); "
        "b=subprocess.run(['git','branch','--show-current'],"
        "capture_output=True,text=True).stdout.strip() if c else ''; "
        "(c and b=='main') and (print("
        "'GUARDRAIL: Direct commit to main detected. Use a feature branch.'"
        ",file=sys.stderr),sys.exit(2))"
        "\""
    )
    pre_bash_force = (
        "python3 -c \""
        "import os,sys; "
        "t=os.environ.get('CLAUDE_TOOL_INPUT',''); "
        "t.startswith('git push --force') and (print("
        "'EMERGENCY GUARDRAIL: Force push detected. "
        "This can cause permanent data loss. Aborting.'"
        ",file=sys.stderr),sys.exit(2))"
        "\""
    )
    post_bash_review = (
        "python3 -c \""
        "import os,re; "
        "t=os.environ.get('CLAUDE_TOOL_INPUT',''); "
        "f=os.path.join('.gse','status.yaml'); "
        "c=open(f).read() if t.startswith('git push') and os.path.isfile(f) else ''; "
        "m=re.search(r'review_findings_open:\\s*(\\d+)',c); "
        "o=int(m.group(1)) if m else 0; "
        "(o>0) and print('WARNING: '+str(o)+' open review findings')"
        "\""
    )

    # Claude Code format (PascalCase events, explicit type)
    claude_hooks = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [
                    {"type": "command", "command": pre_bash_commit},
                    {"type": "command", "command": pre_bash_force},
                ]},
            ],
            "PostToolUse": [
                {"matcher": "Bash", "hooks": [
                    {"type": "command", "command": post_bash_review},
                ]},
            ],
        },
    }
    write_file(PLUGIN / "hooks" / "hooks.claude.json",
               json.dumps(claude_hooks, indent=2) + "\n")

    # Cursor format (camelCase events, implicit type, version field)
    cursor_hooks = {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {"matcher": "Bash", "hooks": [
                    {"command": pre_bash_commit},
                    {"command": pre_bash_force},
                ]},
            ],
            "postToolUse": [
                {"matcher": "Bash", "hooks": [
                    {"command": post_bash_review},
                ]},
            ],
        },
    }
    write_file(PLUGIN / "hooks" / "hooks.cursor.json",
               json.dumps(cursor_hooks, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify() -> None:
    print("=== Verification ===\n")
    errors = []

    # Shared components
    agents = sum(1 for f in SPECIALIZED_AGENTS if (PLUGIN / "agents" / f).exists())
    orchestrator = (PLUGIN / "agents" / "gse-orchestrator.md").exists()
    templates = sum(1 for _ in (PLUGIN / "templates").rglob("*") if _.is_file()) if (PLUGIN / "templates").exists() else 0

    print(f"  Agents:      {agents}/{len(SPECIALIZED_AGENTS)} specialized + orchestrator={'OK' if orchestrator else 'MISSING'}")
    print(f"  Templates:   {templates}")

    if agents < len(SPECIALIZED_AGENTS): errors.append(f"Missing {len(SPECIALIZED_AGENTS)-agents} specialized agents")
    if not orchestrator: errors.append("Missing gse-orchestrator.md")
    if templates == 0: errors.append("No templates found")

    # Claude-specific
    skills = sum(1 for n in ACTIVITY_NAMES if (PLUGIN / "skills" / n / "SKILL.md").exists())
    print(f"\n  Claude Code:")
    print(f"    Skills:    {skills}/{len(ACTIVITY_NAMES)}")
    if skills < len(ACTIVITY_NAMES): errors.append(f"Claude: missing {len(ACTIVITY_NAMES)-skills} skills")
    for name, path in {
        "plugin.json": PLUGIN / ".claude-plugin" / "plugin.json",
        "settings.json": PLUGIN / "settings.json",
        "hooks.claude.json": PLUGIN / "hooks" / "hooks.claude.json",
    }.items():
        ok = path.exists()
        print(f"    {name}: {'OK' if ok else 'MISSING'}")
        if not ok: errors.append(f"Claude: missing {name}")

    # Cursor-specific
    commands = sum(1 for n in ACTIVITY_NAMES if (PLUGIN / "commands" / f"gse-{n}.md").exists())
    print(f"\n  Cursor:")
    print(f"    Commands:  {commands}/{len(ACTIVITY_NAMES)}")
    if commands < len(ACTIVITY_NAMES): errors.append(f"Cursor: missing {len(ACTIVITY_NAMES)-commands} commands")
    for name, path in {
        "plugin.json": PLUGIN / ".cursor-plugin" / "plugin.json",
        "000-gse-methodology.mdc": PLUGIN / "rules" / "000-gse-methodology.mdc",
        "hooks.cursor.json": PLUGIN / "hooks" / "hooks.cursor.json",
    }.items():
        ok = path.exists()
        print(f"    {name}: {'OK' if ok else 'MISSING'}")
        if not ok: errors.append(f"Cursor: missing {name}")

    # Body parity
    print("\n  Cross-platform parity:")
    if orchestrator and (PLUGIN / "rules" / "000-gse-methodology.mdc").exists():
        agent_body = extract_body(PLUGIN / "agents" / "gse-orchestrator.md")
        mdc_body = extract_body(PLUGIN / "rules" / "000-gse-methodology.mdc")
        parity = agent_body == mdc_body
        print(f"    Orchestrator vs .mdc body: {'IDENTICAL' if parity else 'DIVERGENT!'}")
        if not parity: errors.append("Orchestrator and .mdc body content differ!")

    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    - {e}")
        return False
    else:
        print("\n  All checks passed!")
        return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="GSE-One Generator — Build mono-plugin from source"
    )
    parser.add_argument("--clean", action="store_true", help="Remove plugin/ before generating")
    parser.add_argument("--verify", action="store_true", help="Verify completeness after generation")

    args = parser.parse_args()

    generate(clean=args.clean)

    if args.verify:
        success = verify()
        if not success:
            sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
