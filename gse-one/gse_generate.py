#!/usr/bin/env python3
"""
GSE-One Generator — Builds plugin/ from src/

Usage:
    python gse_generate.py [--clean] [--verify]

Mono-plugin architecture: ONE directory deployable on Claude Code, Cursor and opencode.

Source layout:
    src/principles/    → 16 principle definitions (P1-P16)
    src/activities/    → 23 activity definitions (→ skills for Claude, commands for Cursor/opencode)
    src/agents/        → 11 agent roles (10 specialized + gse-orchestrator)
    src/templates/     → 29 artefact & config templates

Generated output:
    plugin/            → Single deployable directory
        .claude-plugin/plugin.json    ← Claude Code manifest
        .cursor-plugin/plugin.json    ← Cursor manifest
        skills/                       ← Claude Code activities (SKILL.md in subdirs)
        commands/                     ← Cursor activities (flat gse-<name>.md files)
        agents/                       ← 11 agents (10 specialized + orchestrator for Claude; installer excludes orchestrator for Cursor)
        templates/                    ← Shared (29 templates)
        rules/gse-orchestrator.mdc    ← Cursor-specific (generated)
        hooks/hooks.claude.json       ← Claude-specific (generated)
        hooks/hooks.cursor.json       ← Cursor-specific (generated)
        settings.json                 ← Claude-specific (generated)
        opencode/                     ← opencode deployable subtree (generated)
            skills/<name>/SKILL.md    ← with injected `name:` frontmatter
            commands/gse-<name>.md    ← identical to Cursor commands
            agents/<name>.md          ← 10 specialized, `mode: subagent`, tools object
            plugins/gse-guardrails.ts ← hooks transpiled to opencode TS plugin
            AGENTS.md                 ← orchestrator body wrapped in GSE-ONE markers
            opencode.json             ← default permissions + GSE-One metadata

Activities are generated to the correct concept per platform:
  - Claude Code: skills/ (SKILL.md in subdirs) → /gse:go, /gse:plan (auto-namespaced)
  - Cursor: commands/ (flat gse-<name>.md) → /gse-go, /gse-plan (prefixed kebab-case)
  - opencode: skills/ + commands/ → /gse-go, /gse-plan (prefixed kebab-case)

The orchestrator agent, the .mdc rule, and the opencode AGENTS.md block are
generated from the SAME source, ensuring identical methodology on all platforms.
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
REFERENCES_DIR = SRC / "references"

ACTIVITY_NAMES = [
    "go", "hug", "learn", "backlog", "collect", "assess", "plan",
    "reqs", "design", "preview", "tests", "produce", "deliver",
    "review", "fix", "compound", "integrate", "deploy", "task", "status",
    "health", "pause", "resume", "audit",
]

SPECIALIZED_AGENTS = [
    "requirements-analyst.md", "architect.md", "test-strategist.md",
    "code-reviewer.md", "security-auditor.md", "ux-advocate.md",
    "guardrail-enforcer.md", "devil-advocate.md", "coach.md",
    "deploy-operator.md",
]

PLUGIN_DESCRIPTION = (
    "GSE-One — AI engineering companion for structured SDLC management. "
    "24 commands, adaptive risk analysis, unified backlog, knowledge transfer, "
    "worktree isolation."
)

# Canonical upstream repository URL — single source of truth.
# Propagated to all platform manifests (Claude plugin.json, Cursor plugin.json,
# opencode.json under the `gse` key) so that /gse:integrate Axe 2 can resolve
# the methodology feedback target uniformly across platforms.
UPSTREAM_REPO = "https://github.com/nicolasguelfi/gensem"


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

def copy_skill_with_name(src: Path, dst: Path, skill_name: str) -> None:
    """Copy a source activity as SKILL.md, injecting `name:` in frontmatter.

    opencode's skill loader requires both `name` and `description`. Claude Code
    accepts extra frontmatter fields silently, so the injected `name:` is safe
    across all targets and lets the same SKILL.md serve both platforms.
    """
    content = src.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3 and "name:" not in parts[1]:
            fm = parts[1].rstrip("\n")
            parts[1] = f'\nname: {skill_name}\n{fm.lstrip(chr(10))}\n'
            content = "---".join(parts)
    write_file(dst, content)

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


# Registry resolution incantations.
# Sources author the simple global form `$(cat ~/.gse-one)`; the generator
# rewrites it in the DEPLOYED artefacts to a project-local-first form so a
# fully project-local install mode (registry at <project>/.gse/registry, no
# $HOME file) works, while the global modes keep working via the fallback.
REGISTRY_GLOBAL = "cat ~/.gse-one"
REGISTRY_RESOLVED = "[ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one"


def _localize_registry_resolution() -> None:
    """Rewrite `cat ~/.gse-one` → project-local-first resolution in every
    generated text artefact under plugin/.

    Run as the final generate() step so it catches skills, commands, agents,
    AGENTS.md / GEMINI.md, the .mdc rule, Codex skills/AGENTS.md, and Gemini
    command TOMLs uniformly — which preserves the cross-platform body parity
    (all orchestrator copies receive the identical rewrite). Idempotent per
    run: artefacts are rebuilt from src (plain form) on every generate, then
    transformed once; str.replace does not re-scan its own replacement.

    The Python dashboard hook resolves the registry separately (it prefers
    .gse/registry in its own one-liner), so it carries no `cat ~/.gse-one`.
    """
    count = 0
    files = 0
    for path in sorted(PLUGIN.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in (".md", ".mdc", ".toml"):
            continue
        text = path.read_text(encoding="utf-8")
        if REGISTRY_GLOBAL not in text:
            continue
        n = text.count(REGISTRY_GLOBAL)
        path.write_text(text.replace(REGISTRY_GLOBAL, REGISTRY_RESOLVED), encoding="utf-8")
        count += n
        files += 1
    print(f"  registry resolution: rewrote {count} incantation(s) in {files} file(s)")


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate(clean: bool = False) -> None:
    print(f"GSE-One Generator v{VERSION}")
    print(f"Root: {ROOT}\n")

    if clean and PLUGIN.exists():
        # Preserve plugin/tools/: this is the only subdirectory not managed by
        # the generator (hand-maintained per CLAUDE.md). Wiping it would delete
        # critical runtime scripts (e.g., dashboard.py) the generator cannot
        # reconstruct.
        for child in PLUGIN.iterdir():
            if child.name == "tools":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        print("  cleaned plugin/ (preserved tools/)\n")

    # 1. Activities → Skills (Claude Code) + Commands (Cursor)
    activity_count = sum(1 for n in ACTIVITY_NAMES if (ACTIVITIES_DIR / f"{n}.md").exists())

    print("Skills (Claude Code):")
    for name in ACTIVITY_NAMES:
        src_file = ACTIVITIES_DIR / f"{name}.md"
        dst_file = PLUGIN / "skills" / name / "SKILL.md"
        if src_file.exists():
            copy_skill_with_name(src_file, dst_file, name)
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

    # 2. Agents — 10 specialized (shared) + orchestrator (generated)
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
            'software development lifecycle with 24 commands under the /gse: prefix. '
            'Adapts language, decisions, and autonomy to the user\'s profile."\n'
            '---\n\n'
            f'{body}\n'
        )
        write_file(PLUGIN / "agents" / "gse-orchestrator.md", orchestrator_content)

        # Cursor: rules/gse-orchestrator.mdc
        mdc_content = (
            '---\n'
            'description: "GSE-One methodology — 16 core principles, state management, '
            'orchestration decision tree. This is the agent\'s permanent identity."\n'
            'alwaysApply: true\n'
            '---\n\n'
            f'{body}\n'
        )
        write_file(PLUGIN / "rules" / "gse-orchestrator.mdc", mdc_content)

        # Verify identical body
        agent_body = extract_body(PLUGIN / "agents" / "gse-orchestrator.md")
        mdc_body = extract_body(PLUGIN / "rules" / "gse-orchestrator.mdc")
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

    # 4.1. References (shared) — consulted by agents at runtime
    print("References:")
    ref_count = 0
    if REFERENCES_DIR.exists():
        for src_file in sorted(REFERENCES_DIR.rglob("*")):
            if src_file.is_file():
                rel = src_file.relative_to(REFERENCES_DIR)
                copy_file(src_file, PLUGIN / "references" / rel)
                ref_count += 1
    print(f"  {ref_count}\n")

    # 4.5. Tools directory (dashboard etc.)
    print("Tools:")
    tools_src = ROOT / "plugin" / "tools"
    if tools_src.is_dir():
        print(f"  tools/ already in plugin ({sum(1 for _ in tools_src.glob('*.py'))} scripts)\n")
    else:
        print(f"  WARNING: plugin/tools/ not found\n")

    # 4.6. Unified VERSION file at plugin/ root
    # Written here so every install target (claude .claude/, cursor .cursor/,
    # opencode .opencode/, ~/.config/opencode/, ~/.gse-one.d/ side-install for
    # claude plugin) can distribute a single version source, readable by skills
    # uniformly as `cat "$(cat ~/.gse-one)/VERSION"` regardless of platform or
    # install mode.
    print("VERSION file:")
    write_file(PLUGIN / "VERSION", f"{VERSION}\n")
    print()

    # 5. Manifests
    print("Manifests:")
    claude_manifest = {
        "name": "gse",
        "description": PLUGIN_DESCRIPTION,
        "version": VERSION,
        "author": {"name": "GSE-One Project"},
        "repository": UPSTREAM_REPO,
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
        "repository": UPSTREAM_REPO,
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

    # 8. opencode subtree
    print("opencode:")
    build_opencode()
    print()

    # 9. Codex CLI subtree
    print("Codex CLI:")
    build_codex()
    print()

    # 10. Gemini CLI subtree
    print("Gemini CLI:")
    build_gemini()
    print()

    # 10.5. Project launcher (gse-run)
    print("Launcher:")
    build_launcher()
    print()

    # 11. Registry resolution rewrite (project-local-first, global fallback) —
    # MUST run last so it transforms every emitted artefact uniformly.
    print("Registry resolution (project-local-first):")
    _localize_registry_resolution()
    print()

    print(f"Plugin generated: {PLUGIN.relative_to(ROOT)}/")
    total = sum(1 for _ in PLUGIN.rglob("*") if _.is_file())
    print(f"Total files: {total}\n")


def _guardrail_commands() -> dict:
    """Return the four cross-platform guardrail hook commands as a dict.

    Authored once and shared by every platform hook generator (Claude, Cursor,
    Codex, Gemini) so the guardrail logic never drifts between platforms — a
    parity check in verify() asserts the Codex/Gemini hooks reuse these exact
    strings. Transport: each runtime delivers the tool input as JSON on stdin
    ({"tool_input": {"command": ...}}); config toggles are read from
    .gse/config.yaml (regex, stdlib only — no PyYAML in a one-liner).
    """
    _read_cmd = (
        "raw=sys.stdin.read(); "
        "d=json.loads(raw) if raw.lstrip().startswith('{') else {}; "
        "t=str((d.get('tool_input') or {}).get('command') or ''); "
    )
    pre_bash_commit = (
        "python3 -c \""
        "import sys,json,os,re,subprocess; "
        + _read_cmd +
        "c=bool(re.search(r'(?:^|[;&|]\\s*)git\\s+(-C\\s+\\S+\\s+)?commit\\b',t)); "
        "p=os.path.join('.gse','config.yaml'); "
        "cfg=open(p).read() if c and os.path.isfile(p) else ''; "
        "off=bool(re.search(r'^\\s*protect_main:\\s*false',cfg,re.M)) "
        "or bool(re.search(r'^\\s*strategy:\\s*none',cfg,re.M)); "
        "b=subprocess.run(['git','branch','--show-current'],"
        "capture_output=True,text=True).stdout.strip() if c and not off else ''; "
        "init=bool(b=='main' and subprocess.run(['git','rev-parse','--verify','HEAD'],"
        "capture_output=True).returncode!=0); "
        "(c and not off and not init and b=='main') and (print("
        "'GUARDRAIL: Direct commit to main detected. Use a feature branch. '"
        "'(Sanctioned exceptions: hooks.protect_main: false or git.strategy: none "
        "in .gse/config.yaml; repository-initialization commit.)'"
        ",file=sys.stderr),sys.exit(2))"
        "\""
    )
    pre_bash_force = (
        "python3 -c \""
        "import sys,json,os,re; "
        + _read_cmd +
        "bad=bool(re.search(r'\\bgit\\s[^|;&]*\\bpush\\b[^|;&]*(\\s-f\\b|--force\\b)',t)); "
        "p=os.path.join('.gse','config.yaml'); "
        "cfg=open(p).read() if bad and os.path.isfile(p) else ''; "
        "off=bool(re.search(r'^\\s*block_force_push:\\s*false',cfg,re.M)); "
        "(bad and not off) and (print("
        "'EMERGENCY GUARDRAIL: Force push detected (-f / --force / --force-with-lease). "
        "This can cause permanent data loss. Aborting.'"
        ",file=sys.stderr),sys.exit(2))"
        "\""
    )
    post_bash_review = (
        "python3 -c \""
        "import sys,json,os,re; "
        + _read_cmd +
        "p=os.path.join('.gse','config.yaml'); "
        "cfg=open(p).read() if os.path.isfile(p) else ''; "
        "off=bool(re.search(r'^\\s*review_findings_on_push:\\s*false',cfg,re.M)); "
        "f=os.path.join('.gse','status.yaml'); "
        "c=open(f).read() if (not off) and re.search(r'\\bgit\\s[^|;&]*\\bpush\\b',t) "
        "and os.path.isfile(f) else ''; "
        "m=re.search(r'review_findings_open:\\s*(\\d+)',c); "
        "o=int(m.group(1)) if m else 0; "
        "(o>0) and print('WARNING: '+str(o)+' open review findings')"
        "\""
    )

    # Dashboard sync hook (ENH-02 / spec §7 automatic regeneration policy).
    # Fires on every Edit/Write/MultiEdit. Invokes dashboard.py --if-stale which
    # self-arbitrates via configurable mtime-based debounce. Double-defense:
    # if the subprocess exits non-zero (dashboard.py crashed before its own
    # try/except ran), this wrapper writes a minimal error marker so the next
    # successful regeneration shows the failure banner.
    post_edit_dashboard = (
        "python3 -c \""
        "import os,subprocess,datetime,json; "
        "r='.gse/registry' if os.path.isfile('.gse/registry') else os.path.expanduser('~/.gse-one'); "
        "p=open(r).read().strip() if os.path.isfile(r) else ''; "
        "t=os.path.join(p,'tools','dashboard.py') if p else ''; "
        "res=subprocess.run(['python3',t,'--if-stale'],capture_output=True,text=True) "
        "if os.path.isfile(t) else None; "
        "(res and res.returncode!=0) and os.makedirs('.gse',exist_ok=True) or None; "
        "(res and res.returncode!=0) and open(os.path.join('.gse','.dashboard-error.yaml'),'w').write("
        "'timestamp: \\\"'+datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')+'\\\"\\n"
        "message: '+json.dumps('dashboard.py exited with code '+str(res.returncode))+'\\n"
        "traceback: |\\n  '+(res.stderr or '(no stderr)').replace(chr(10),chr(10)+'  '))"
        "\""
    )

    return {
        "pre_commit": pre_bash_commit,
        "pre_force": pre_bash_force,
        "post_review": post_bash_review,
        "post_dashboard": post_edit_dashboard,
    }


def generate_hooks() -> None:
    """Generate platform-specific hooks (Claude + Cursor) from shared commands."""
    cmds = _guardrail_commands()
    pre_bash_commit = cmds["pre_commit"]
    pre_bash_force = cmds["pre_force"]
    post_bash_review = cmds["post_review"]
    post_edit_dashboard = cmds["post_dashboard"]

    # Claude Code format (PascalCase events, explicit type).
    # Three separate matcher entries for Edit/Write/MultiEdit — maximum portability
    # across coding agents (no regex matcher dependency). Needed for opencode +
    # local-model setups where JSON matcher parsing may be strict.
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
                {"matcher": "Edit", "hooks": [
                    {"type": "command", "command": post_edit_dashboard},
                ]},
                {"matcher": "Write", "hooks": [
                    {"type": "command", "command": post_edit_dashboard},
                ]},
                {"matcher": "MultiEdit", "hooks": [
                    {"type": "command", "command": post_edit_dashboard},
                ]},
            ],
        },
    }
    write_file(PLUGIN / "hooks" / "hooks.claude.json",
               json.dumps(claude_hooks, indent=2) + "\n")

    # Cursor format (camelCase events, implicit type, version field).
    # Same three-matcher pattern as Claude for cross-platform portability.
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
                {"matcher": "Edit", "hooks": [
                    {"command": post_edit_dashboard},
                ]},
                {"matcher": "Write", "hooks": [
                    {"command": post_edit_dashboard},
                ]},
                {"matcher": "MultiEdit", "hooks": [
                    {"command": post_edit_dashboard},
                ]},
            ],
        },
    }
    write_file(PLUGIN / "hooks" / "hooks.cursor.json",
               json.dumps(cursor_hooks, indent=2) + "\n")


# ---------------------------------------------------------------------------
# opencode builder
# ---------------------------------------------------------------------------

OPENCODE_AGENTS_MD_START = "<!-- GSE-ONE START -->"
OPENCODE_AGENTS_MD_END = "<!-- GSE-ONE END -->"


def build_opencode() -> None:
    """Assemble plugin/opencode/ from the already-generated plugin/ tree."""
    oc = PLUGIN / "opencode"
    if oc.exists():
        shutil.rmtree(oc)
    ensure_dir(oc)
    _oc_build_skills(oc)
    _oc_build_commands(oc)
    _oc_build_agents(oc)
    _oc_build_plugins_ts(oc)
    _oc_build_agents_md(oc)
    _oc_build_config_json(oc)


def _oc_build_skills(oc: Path) -> None:
    """Copy plugin/skills/**/SKILL.md to opencode/skills/. The `name:` field
    was already injected during the Claude skills step, so a plain copy
    suffices here.
    """
    src = PLUGIN / "skills"
    dst = oc / "skills"
    ensure_dir(dst)
    count = 0
    for skill_dir in sorted(src.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        out = dst / skill_dir.name / "SKILL.md"
        ensure_dir(out.parent)
        shutil.copy2(skill_file, out)
        count += 1
    print(f"  skills: {count}")


def _oc_build_commands(oc: Path) -> None:
    """Copy plugin/commands/gse-*.md verbatim — opencode uses the same format
    as Cursor for slash commands.
    """
    src = PLUGIN / "commands"
    dst = oc / "commands"
    ensure_dir(dst)
    count = 0
    for cmd_file in sorted(src.glob("gse-*.md")):
        shutil.copy2(cmd_file, dst / cmd_file.name)
        count += 1
    print(f"  commands: {count}")


def _oc_build_agents(oc: Path) -> None:
    """Copy the 10 specialized agents, adding `mode: subagent` and translating
    any `tools:` list into opencode's object form. The orchestrator is not
    emitted as an agent — it ships via AGENTS.md instead.
    """
    src = PLUGIN / "agents"
    dst = oc / "agents"
    ensure_dir(dst)
    count = 0
    for agent_file in sorted(src.glob("*.md")):
        if agent_file.name == "gse-orchestrator.md":
            continue
        content = agent_file.read_text(encoding="utf-8")
        new_content = _oc_translate_agent_frontmatter(content)
        (dst / agent_file.name).write_text(new_content, encoding="utf-8")
        count += 1
    print(f"  agents: {count}")


def _oc_translate_agent_frontmatter(content: str) -> str:
    """Return the agent content with opencode-compatible frontmatter.

    - Adds `mode: subagent` if absent.
    - Converts `tools: [A, B]` (list) into `tools:\\n  a: true\\n  b: true` (object).
    """
    if not content.startswith("---"):
        return content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content
    fm = parts[1]
    body = parts[2]

    # Translate tools list → object
    tools_match = re.search(r'^tools:\s*\[(.*?)\]\s*$', fm, re.MULTILINE)
    if tools_match:
        items = [t.strip().strip('"').strip("'") for t in tools_match.group(1).split(",") if t.strip()]
        object_lines = "\n".join(f"  {item.lower()}: true" for item in items)
        fm = fm.replace(tools_match.group(0), f"tools:\n{object_lines}")

    # Add mode if missing
    if not re.search(r'^mode:\s*', fm, re.MULTILINE):
        fm = fm.rstrip("\n") + "\nmode: subagent\n"

    return f"---{fm}---{body}"


def _oc_build_plugins_ts(oc: Path) -> None:
    """Write plugins/gse-guardrails.ts — a native opencode TS plugin that
    reproduces the guardrails from hooks.claude.json:
      - block `git commit` on main
      - block `git push --force`
      - post-`git push` warning when .gse/status.yaml has open review findings
      - dashboard sync on edit/write/multiedit (ENH-02, spec §7)
    """
    dst = oc / "plugins" / "gse-guardrails.ts"
    ts = f'''// Generated by gse_generate.py — DO NOT EDIT
// GSE-One version: {VERSION}
// Reproduces hooks/hooks.claude.json guardrails as a native opencode plugin.
import type {{ Plugin }} from "@opencode-ai/plugin"
import {{ $ }} from "bun"

export const GseGuardrails: Plugin = async () => {{
  return {{
    "tool.execute.before": async (input: any, output: any) => {{
      if (input?.tool !== "bash") return
      const cmd = String(output?.args?.command ?? "")

      // Project-local config toggles (.gse/config.yaml -> hooks section)
      let cfg = ""
      try {{ cfg = await Bun.file(".gse/config.yaml").text() }} catch {{ /* no config */ }}

      if (/\\bgit\\s[^|;&]*\\bpush\\b[^|;&]*(\\s-f\\b|--force\\b)/.test(cmd)) {{
        if (!/^\\s*block_force_push:\\s*false/m.test(cfg)) {{
          throw new Error(
            "EMERGENCY GUARDRAIL: Force push detected (-f / --force / --force-with-lease). This can cause permanent data loss. Aborting."
          )
        }}
      }}

      if (/(?:^|[;&|]\\s*)git\\s+(-C\\s+\\S+\\s+)?commit\\b/.test(cmd)) {{
        const off = /^\\s*protect_main:\\s*false/m.test(cfg) || /^\\s*strategy:\\s*none/m.test(cfg)
        if (!off) {{
          const branch = (await $`git branch --show-current`.text()).trim()
          if (branch === "main") {{
            // Repository-initialization exception: no HEAD yet (foundational commit)
            const head = await $`git rev-parse --verify HEAD`.nothrow().quiet()
            if (head.exitCode === 0) {{
              throw new Error(
                "GUARDRAIL: Direct commit to main detected. Use a feature branch. (Sanctioned exceptions: hooks.protect_main: false or git.strategy: none in .gse/config.yaml; repository-initialization commit.)"
              )
            }}
          }}
        }}
      }}
    }},

    "tool.execute.after": async (input: any, _output: any) => {{
      // Bash / git push — open review findings warning
      if (input?.tool === "bash") {{
        const cmd = String(input?.args?.command ?? "")
        if (/\\bgit\\s[^|;&]*\\bpush\\b/.test(cmd)) {{
          try {{
            let cfgAfter = ""
            try {{ cfgAfter = await Bun.file(".gse/config.yaml").text() }} catch {{ /* no config */ }}
            if (/^\\s*review_findings_on_push:\\s*false/m.test(cfgAfter)) return
            const status = await Bun.file(".gse/status.yaml").text()
            const m = status.match(/review_findings_open:\\s*(\\d+)/)
            const open = m ? parseInt(m[1], 10) : 0
            if (open > 0) {{
              console.warn(`WARNING: ${{open}} open review findings`)
            }}
          }} catch {{
            // .gse/status.yaml absent — nothing to report
          }}
        }}
        return
      }}

      // Dashboard sync — fire on edit/write/multiedit (ENH-02).
      // Mirrors the PostToolUse hooks in hooks.claude.json / hooks.cursor.json,
      // including the double-defense error marker on subprocess failure.
      const toolName = String(input?.tool ?? "").toLowerCase()
      if (["edit", "write", "multiedit"].includes(toolName)) {{
        try {{
          const home = process.env.HOME ?? ""
          const registryPath = `${{home}}/.gse-one`
          const registryFile = Bun.file(registryPath)
          if (!(await registryFile.exists())) return
          const pluginPath = (await registryFile.text()).trim()
          if (!pluginPath) return
          const tool = `${{pluginPath}}/tools/dashboard.py`
          if (!(await Bun.file(tool).exists())) return
          const result = await $`python3 ${{tool}} --if-stale`.nothrow().quiet()
          if (result.exitCode !== 0) {{
            // Double-defense: dashboard.py crashed before its own try/except ran
            const now = new Date().toISOString().replace(/\\.\\d+Z$/, "Z")
            const stderr = result.stderr?.toString() ?? "(no stderr)"
            const msg = JSON.stringify(`dashboard.py exited with code ${{result.exitCode}}`)
            const indented = stderr.split("\\n").map((l: string) => `  ${{l}}`).join("\\n")
            const content =
              `timestamp: "${{now}}"\\n` +
              `message: ${{msg}}\\n` +
              `traceback: |\\n${{indented}}\\n`
            try {{
              await Bun.write(".gse/.dashboard-error.yaml", content)
            }} catch {{ /* best-effort */ }}
          }}
        }} catch {{
          // Hook wrapper must never block the edit
        }}
      }}
    }},
  }}
}}

export default GseGuardrails
'''
    write_file(dst, ts)


def _oc_build_agents_md(oc: Path) -> None:
    """Assemble opencode/AGENTS.md with the orchestrator body wrapped in
    GSE-ONE markers, so installers can do surgical merge/replace.
    """
    mdc = PLUGIN / "rules" / "gse-orchestrator.mdc"
    if not mdc.exists():
        print("  AGENTS.md: SKIPPED (rules/gse-orchestrator.mdc missing)")
        return
    body = extract_body(mdc)
    content = (
        f"{OPENCODE_AGENTS_MD_START}\n"
        f"<!-- gse-one-version: {VERSION} -->\n"
        f"# GSE-One Methodology (opencode edition)\n\n"
        f"This section is managed by GSE-One. Edit `gse-one/src/` and regenerate — "
        f"do not hand-edit between the START/END markers.\n\n"
        f"{body}\n\n"
        f"{OPENCODE_AGENTS_MD_END}\n"
    )
    write_file(oc / "AGENTS.md", content)


def _oc_build_config_json(oc: Path) -> None:
    """Write a minimal opencode.json with safe defaults and GSE-One metadata.

    Kept small to make installer deep-merge predictable. Unknown top-level
    `gse` key is used for version metadata — opencode's schema validator
    warns on unknowns but does not reject them.
    """
    config = {
        "$schema": "https://opencode.ai/config.json",
        "permission": {
            "skill": {"*": "allow"},
            "question": "allow",
            "bash": {
                "git push --force *": "deny",
                "rm -rf /*": "deny"
            }
        },
        "gse": {
            "version": VERSION,
            "repository": UPSTREAM_REPO
        }
    }
    write_file(oc / "opencode.json", json.dumps(config, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Codex CLI builder
# ---------------------------------------------------------------------------

# Codex AGENTS.md hard size cap (project_doc_max_bytes default). The full
# orchestrator (~68 KB) exceeds it, so Codex carries the condensed lite edition
# as AGENTS.md and ships the full orchestrator as a loadable skill.
CODEX_AGENTS_MD_MAX_BYTES = 32 * 1024

# Specialized agents that run read-only under Codex (reviewer/observer
# archetypes). deploy-operator runs shell operations → default sandbox.
CODEX_READONLY_AGENTS = {
    "requirements-analyst", "architect", "test-strategist", "code-reviewer",
    "security-auditor", "ux-advocate", "guardrail-enforcer", "devil-advocate",
    "coach",
}


def build_codex() -> None:
    """Assemble plugin/codex/ from the already-generated plugin/ tree + src lite."""
    cx = PLUGIN / "codex"
    if cx.exists():
        shutil.rmtree(cx)
    ensure_dir(cx)
    _cx_build_skills(cx)
    _cx_build_agents(cx)
    _cx_build_agents_md(cx)
    _cx_build_hooks(cx)
    _cx_build_manifest(cx)


def _cx_build_skills(cx: Path) -> None:
    """Emit the activity skills with their directory AND frontmatter `name:`
    prefixed `gse-<name>`, so Codex's `/` skill menu shows them namespaced
    (`gse-go`, `gse-assess`, …) — filterable by typing `/gse`, no collision with
    built-in skills. Plus the FULL orchestrator as a loadable `gse-orchestrator`
    skill (Codex AGENTS.md carries only the condensed lite edition — B1)."""
    src = PLUGIN / "skills"
    dst = cx / "skills"
    ensure_dir(dst)
    count = 0
    for skill_dir in sorted(src.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        content = skill_file.read_text(encoding="utf-8")
        # Prefix the frontmatter name (`name: go` -> `name: gse-go`); idempotent.
        content = re.sub(r'(?m)^(name:\s*)(?!gse-)([A-Za-z0-9-]+)\s*$',
                         r'\1gse-\2', content, count=1)
        out = dst / f"gse-{skill_dir.name}" / "SKILL.md"
        ensure_dir(out.parent)
        out.write_text(content, encoding="utf-8")
        count += 1
    orch = PLUGIN / "agents" / "gse-orchestrator.md"
    if orch.exists():
        body = extract_body(orch)
        content = (
            "---\n"
            "name: gse-orchestrator\n"
            'description: "Full GSE-One orchestrator methodology — load when you need '
            "the complete invariant text, failure modes, and edge cases beyond the "
            'condensed AGENTS.md summary."\n'
            "---\n\n"
            f"{body}\n"
        )
        write_file(dst / "gse-orchestrator" / "SKILL.md", content)
        count += 1
    print(f"  skills: {count} (incl. full orchestrator)")


def _cx_build_agents(cx: Path) -> None:
    """Translate the 10 specialized agents (markdown) into Codex sub-agent TOML."""
    src = PLUGIN / "agents"
    dst = cx / "agents"
    ensure_dir(dst)
    count = 0
    for agent_file in sorted(src.glob("*.md")):
        if agent_file.name == "gse-orchestrator.md":
            continue
        toml = _cx_agent_to_toml(agent_file)
        (dst / f"{agent_file.stem}.toml").write_text(toml, encoding="utf-8")
        count += 1
    print(f"  agents (toml): {count}")


def _cx_agent_to_toml(agent_file: Path) -> str:
    """Convert an agent markdown file to a Codex sub-agent TOML definition.

    name/description from frontmatter; the markdown body becomes
    developer_instructions as a TOML multi-line *literal* string ('''…''') so
    backticks, backslashes and quotes pass through unescaped. No agent body
    contains ''' (asserted in verify())."""
    content = agent_file.read_text(encoding="utf-8")
    name = agent_file.stem
    desc = f"GSE-One {name} agent"
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            m = re.search(r'description:\s*"(.+?)"', parts[1], re.DOTALL)
            if m:
                desc = m.group(1).replace('"', "'").replace("\n", " ").strip()
            body = parts[2].strip()
    sandbox = "read-only" if name in CODEX_READONLY_AGENTS else "workspace-write"
    return (
        f'name = "{name}"\n'
        f'description = "{desc}"\n'
        f'sandbox_mode = "{sandbox}"\n'
        f"developer_instructions = '''\n{body}\n'''\n"
    )


def _cx_build_agents_md(cx: Path) -> None:
    """Codex AGENTS.md = condensed lite orchestrator (≤ 32 KiB), wrapped in
    GSE-ONE markers for surgical install/uninstall."""
    lite = AGENTS_DIR / "gse-orchestrator-lite.md"
    if not lite.exists():
        print("  AGENTS.md: SKIPPED (gse-orchestrator-lite.md missing)")
        return
    body = extract_body(lite)
    content = (
        f"{OPENCODE_AGENTS_MD_START}\n"
        f"<!-- gse-one-version: {VERSION} -->\n"
        f"# GSE-One Methodology (Codex edition — condensed)\n\n"
        f"This section is managed by GSE-One. Edit `gse-one/src/` and regenerate — "
        f"do not hand-edit between the START/END markers. The full orchestrator is "
        f"available as the `gse-orchestrator` skill.\n\n"
        f"{body}\n\n"
        f"{OPENCODE_AGENTS_MD_END}\n"
    )
    write_file(cx / "AGENTS.md", content)
    size = len(content.encode("utf-8"))
    flag = "OK" if size <= CODEX_AGENTS_MD_MAX_BYTES else "OVERSIZE!"
    print(f"  AGENTS.md: {size} bytes ({flag}, cap {CODEX_AGENTS_MD_MAX_BYTES})")


def _cx_build_hooks(cx: Path) -> None:
    """codex/hooks/hooks.json reproducing the 3 guardrails from shared commands.
    Codex requires `codex_hooks = true` in config.toml — set by the installer."""
    cmds = _guardrail_commands()
    hooks = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [
                    {"type": "command", "command": cmds["pre_commit"]},
                    {"type": "command", "command": cmds["pre_force"]},
                ]},
            ],
            "PostToolUse": [
                {"matcher": "Bash", "hooks": [
                    {"type": "command", "command": cmds["post_review"]},
                ]},
                {"matcher": "Edit", "hooks": [
                    {"type": "command", "command": cmds["post_dashboard"]},
                ]},
                {"matcher": "Write", "hooks": [
                    {"type": "command", "command": cmds["post_dashboard"]},
                ]},
            ],
        },
    }
    write_file(cx / "hooks" / "hooks.json", json.dumps(hooks, indent=2) + "\n")


def _cx_build_manifest(cx: Path) -> None:
    """codex/.codex-plugin/plugin.json — component pointers (relative ./ paths)."""
    manifest = {
        "name": "gse-one",
        "version": VERSION,
        "description": PLUGIN_DESCRIPTION,
        "skills": "./skills/",
        "agents": "./agents/",
        "hooks": "./hooks/hooks.json",
        "repository": UPSTREAM_REPO,
    }
    write_file(cx / ".codex-plugin" / "plugin.json", json.dumps(manifest, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Gemini CLI builder
# ---------------------------------------------------------------------------

def build_gemini() -> None:
    """Assemble plugin/gemini/ from the already-generated plugin/ tree."""
    gm = PLUGIN / "gemini"
    if gm.exists():
        shutil.rmtree(gm)
    ensure_dir(gm)
    _gm_build_commands(gm)
    _gm_build_agents(gm)
    _gm_build_context(gm)
    _gm_build_hooks(gm)
    _gm_build_manifest(gm)


def _gm_neutralize(body: str) -> str:
    """Neutralize Gemini template triggers in a command prompt.

    Gemini substitutes {{args}} and treats other {{…}} as template syntax. The
    corpus has exactly one stray occurrence ({{.Names}} in a docker example).
    Replacing `{{` with `{ {` renders near-identically and is never parsed as a
    template. {{args}} is unused by GSE prompts (arguments are appended by
    Gemini's default handling), so this is unconditional."""
    return body.replace("{{", "{ {")


def _gm_build_commands(gm: Path) -> None:
    """Each activity → commands/gse/<name>.toml ⇒ /gse:<name>. Body becomes a
    TOML multi-line *literal* prompt ('''…'''); no body contains ''' (verified)."""
    dst = gm / "commands" / "gse"
    ensure_dir(dst)
    count = 0
    for name in ACTIVITY_NAMES:
        src_file = ACTIVITIES_DIR / f"{name}.md"
        if not src_file.exists():
            continue
        content = src_file.read_text(encoding="utf-8")
        desc = f"GSE-One {name} command"
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                m = re.search(r'description:\s*"(.+?)"', parts[1], re.DOTALL)
                if m:
                    desc = m.group(1).replace('"', "'").replace("\n", " ").strip()
                body = parts[2].strip()
        body = _gm_neutralize(body)
        toml = (
            f'description = "{desc}"\n'
            f"prompt = '''\n{body}\n'''\n"
        )
        (dst / f"{name}.toml").write_text(toml, encoding="utf-8")
        count += 1
    print(f"  commands (toml): {count}")


def _gm_build_agents(gm: Path) -> None:
    """Copy the 10 specialized agents as markdown (Gemini sub-agent format)."""
    src = PLUGIN / "agents"
    dst = gm / "agents"
    ensure_dir(dst)
    count = 0
    for agent_file in sorted(src.glob("*.md")):
        if agent_file.name == "gse-orchestrator.md":
            continue
        shutil.copy2(agent_file, dst / agent_file.name)
        count += 1
    print(f"  agents: {count}")


def _gm_build_context(gm: Path) -> None:
    """GEMINI.md = FULL orchestrator body (parity with .mdc, like opencode)."""
    mdc = PLUGIN / "rules" / "gse-orchestrator.mdc"
    if not mdc.exists():
        print("  GEMINI.md: SKIPPED (rules/gse-orchestrator.mdc missing)")
        return
    body = extract_body(mdc)
    content = (
        f"{OPENCODE_AGENTS_MD_START}\n"
        f"<!-- gse-one-version: {VERSION} -->\n"
        f"# GSE-One Methodology (Gemini edition)\n\n"
        f"This section is managed by GSE-One. Edit `gse-one/src/` and regenerate — "
        f"do not hand-edit between the START/END markers.\n\n"
        f"{body}\n\n"
        f"{OPENCODE_AGENTS_MD_END}\n"
    )
    write_file(gm / "GEMINI.md", content)


def _gm_build_hooks(gm: Path) -> None:
    """gemini/hooks/hooks.json — guardrails via Gemini tool-name matchers
    (run_shell_command, write_file, replace)."""
    cmds = _guardrail_commands()
    hooks = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "run_shell_command", "hooks": [
                    {"type": "command", "command": cmds["pre_commit"]},
                    {"type": "command", "command": cmds["pre_force"]},
                ]},
            ],
            "PostToolUse": [
                {"matcher": "run_shell_command", "hooks": [
                    {"type": "command", "command": cmds["post_review"]},
                ]},
                {"matcher": "write_file", "hooks": [
                    {"type": "command", "command": cmds["post_dashboard"]},
                ]},
                {"matcher": "replace", "hooks": [
                    {"type": "command", "command": cmds["post_dashboard"]},
                ]},
            ],
        },
    }
    write_file(gm / "hooks" / "hooks.json", json.dumps(hooks, indent=2) + "\n")


def _gm_build_manifest(gm: Path) -> None:
    """gemini-extension.json — manifest (commands/hooks/agents live in subdirs)."""
    manifest = {
        "name": "gse-one",
        "version": VERSION,
        "description": PLUGIN_DESCRIPTION,
        "contextFileName": "GEMINI.md",
    }
    write_file(gm / "gemini-extension.json", json.dumps(manifest, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Project launcher (gse-run) — generic, mode-detecting agent launcher
# ---------------------------------------------------------------------------

# Body of the launcher dropped into a project's .gse/run by the installer.
# Generic: reads .gse/launch.env (platform, mode) at runtime and starts the
# right agent with the right environment. In sandbox mode it isolates HOME
# inside the project so nothing under the real $HOME is read or written.
# POSIX sh, no jq/bash dependency. No `cat ~/.gse-one` (untouched by the
# registry-resolution rewrite).
_LAUNCHER_BODY = '''set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(CDPATH= cd -- "$script_dir/.." && pwd)
meta="$root/.gse/launch.env"

[ -f "$meta" ] || { echo "GSE-One: $meta not found - is this a GSE-One project?" >&2; exit 1; }

platform=$(sed -n 's/^platform=//p' "$meta" | head -n1)
mode=$(sed -n 's/^mode=//p' "$meta" | head -n1)

[ -n "${platform:-}" ] || { echo "GSE-One: 'platform' missing in $meta" >&2; exit 1; }

case "$platform" in
  codex) bin=codex ;;
  gemini) bin=gemini ;;
  opencode) bin=opencode ;;
  claude) bin=claude ;;
  cursor) bin=cursor ;;
  *) echo "GSE-One: unknown platform '$platform' in $meta" >&2; exit 1 ;;
esac

if [ "${mode:-}" = "sandbox" ]; then
  HOME="$root/.gse-sandbox"; export HOME
  unset XDG_CONFIG_HOME 2>/dev/null || true
  echo "GSE-One: launching '$bin' in project sandbox (HOME=$HOME)" >&2
else
  echo "GSE-One: launching '$bin' (mode: ${mode:-local})" >&2
fi

command -v "$bin" >/dev/null 2>&1 || { echo "GSE-One: '$bin' not found on PATH" >&2; exit 127; }
exec "$bin" "$@"
'''


def build_launcher() -> None:
    """Emit plugin/gse-run — the generic project launcher copied into a
    project's .gse/run by the installer (for --mode sandbox / local)."""
    content = (
        "#!/bin/sh\n"
        f"# GSE-One launcher v{VERSION} - generated by gse_generate.py - DO NOT EDIT\n"
        f"{_LAUNCHER_BODY}"
    )
    write_file(PLUGIN / "gse-run", content)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_external_docs() -> list:
    """Check that hand-maintained docs mention the source-of-truth counts.

    Detects future drift on descriptive prose in README.md / install.py /
    gse-one/README.md when SPECIALIZED_AGENTS, ACTIVITY_NAMES, src/templates/
    or src/principles/ change but the prose is forgotten.

    Returns a list of mismatch strings (empty = all aligned). Called by
    verify() as a *warning-level* check — mismatches are reported but do
    NOT fail the build. The definitive numeric-drift audit lives in
    gse-one/audit.py (/gse-audit Python engine), which can fail on warning
    via --fail-on warning. This function is an early alert at generate time.
    """
    mismatches = []
    n_specialized = len(SPECIALIZED_AGENTS)
    n_agents = n_specialized + 1  # + orchestrator
    n_activities = len(ACTIVITY_NAMES)
    n_principles = sum(1 for _ in PRINCIPLES_DIR.glob("*.md")) if PRINCIPLES_DIR.exists() else 0
    n_templates = sum(
        1 for f in TEMPLATES_DIR.rglob("*")
        if f.is_file() and f.name != "MANIFEST.yaml"
    ) if TEMPLATES_DIR.exists() else 0

    checks = {
        REPO_ROOT / "README.md": [
            f"{n_agents} agents ({n_specialized} specialized + orchestrator)",
            f"{n_agents} agents (shared)",
            f"{n_specialized} specialized (mode: subagent)",
            f"# {n_templates} templates",
            f"# {n_templates} templates (shared)",
            f"{n_activities} commands",
            f"{n_principles} principles (P1-P{n_principles})",
            f"{n_activities} activity definitions",
        ],
        REPO_ROOT / "install.py": [
            f"{n_specialized} specialized agents",
        ],
        ROOT / "README.md": [
            f"{n_agents} agents ({n_specialized} specialized + orchestrator)",
            f"{n_agents} agents (shared)",
            f"{n_templates} artefact & config templates",
            f"{n_templates} templates (shared)",
            f"{n_activities} commands",
            f"{n_activities} activity definitions",
        ],
    }

    for path, phrases in checks.items():
        if not path.exists():
            mismatches.append(f"External doc missing: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                rel = path.relative_to(REPO_ROOT)
                mismatches.append(f"{rel}: missing phrase '{phrase}'")

    return mismatches


def verify() -> None:
    print("=== Verification ===\n")
    errors = []

    # Shared components
    agents = sum(1 for f in SPECIALIZED_AGENTS if (PLUGIN / "agents" / f).exists())
    orchestrator = (PLUGIN / "agents" / "gse-orchestrator.md").exists()
    templates = sum(1 for _ in (PLUGIN / "templates").rglob("*") if _.is_file()) if (PLUGIN / "templates").exists() else 0
    references = sum(1 for _ in (PLUGIN / "references").rglob("*") if _.is_file()) if (PLUGIN / "references").exists() else 0

    print(f"  Agents:      {agents}/{len(SPECIALIZED_AGENTS)} specialized + orchestrator={'OK' if orchestrator else 'MISSING'}")
    print(f"  Templates:   {templates}")
    print(f"  References:  {references}")

    # Unified VERSION file — consumed by skills across all 6 install modes
    version_file = PLUGIN / "VERSION"
    if version_file.exists():
        vf_content = version_file.read_text(encoding="utf-8").strip()
        if vf_content == VERSION:
            print(f"  VERSION:     OK ({vf_content})")
        else:
            print(f"  VERSION:     MISMATCH (file={vf_content}, expected={VERSION})")
            errors.append(f"plugin/VERSION mismatch: {vf_content} != {VERSION}")
    else:
        print(f"  VERSION:     MISSING")
        errors.append("Missing plugin/VERSION file")

    # Hand-maintained tools (not regenerated) — presence is critical because
    # hooks and skills invoke them at runtime.
    required_tools = {
        "dashboard.py": "dashboard hook",
        "coolify_client.py": "/gse:deploy skill (Coolify API client library)",
        "deploy.py": "/gse:deploy skill (orchestrator)",
    }
    missing_tools = []
    for name, purpose in required_tools.items():
        path = PLUGIN / "tools" / name
        if not path.exists():
            missing_tools.append(f"{name} ({purpose})")
    if missing_tools:
        print(f"  Tools:       MISSING {', '.join(missing_tools)}")
        for m in missing_tools:
            errors.append(f"Missing plugin/tools/{m}")
    else:
        print(f"  Tools:       OK ({len(required_tools)} scripts)")

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
        "gse-orchestrator.mdc": PLUGIN / "rules" / "gse-orchestrator.mdc",
        "hooks.cursor.json": PLUGIN / "hooks" / "hooks.cursor.json",
    }.items():
        ok = path.exists()
        print(f"    {name}: {'OK' if ok else 'MISSING'}")
        if not ok: errors.append(f"Cursor: missing {name}")

    # opencode-specific
    oc = PLUGIN / "opencode"
    print(f"\n  opencode:")
    oc_skills = sum(1 for n in ACTIVITY_NAMES if (oc / "skills" / n / "SKILL.md").exists())
    oc_commands = sum(1 for n in ACTIVITY_NAMES if (oc / "commands" / f"gse-{n}.md").exists())
    oc_agents = sum(1 for f in SPECIALIZED_AGENTS if (oc / "agents" / f).exists())
    print(f"    Skills:    {oc_skills}/{len(ACTIVITY_NAMES)}")
    print(f"    Commands:  {oc_commands}/{len(ACTIVITY_NAMES)}")
    print(f"    Agents:    {oc_agents}/{len(SPECIALIZED_AGENTS)} (specialized only — orchestrator via AGENTS.md)")
    if oc_skills < len(ACTIVITY_NAMES): errors.append(f"opencode: missing {len(ACTIVITY_NAMES)-oc_skills} skills")
    if oc_commands < len(ACTIVITY_NAMES): errors.append(f"opencode: missing {len(ACTIVITY_NAMES)-oc_commands} commands")
    if oc_agents < len(SPECIALIZED_AGENTS): errors.append(f"opencode: missing {len(SPECIALIZED_AGENTS)-oc_agents} agents")

    for name, path in {
        "AGENTS.md": oc / "AGENTS.md",
        "opencode.json": oc / "opencode.json",
        "plugins/gse-guardrails.ts": oc / "plugins" / "gse-guardrails.ts",
    }.items():
        ok_exists = path.exists()
        print(f"    {name}: {'OK' if ok_exists else 'MISSING'}")
        if not ok_exists: errors.append(f"opencode: missing {name}")

    # Skill frontmatter `name:` check (required by opencode loader)
    missing_name = []
    for n in ACTIVITY_NAMES:
        skill_md = oc / "skills" / n / "SKILL.md"
        if skill_md.exists():
            fm = skill_md.read_text(encoding="utf-8").split("---", 2)
            if len(fm) >= 3 and f"name: {n}" not in fm[1]:
                missing_name.append(n)
    if missing_name:
        errors.append(f"opencode: {len(missing_name)} SKILL.md missing `name:` field ({', '.join(missing_name[:3])}...)")
    else:
        print(f"    SKILL.md name: all {oc_skills} skills have correct `name:`")

    # Guardrails content check
    ts = oc / "plugins" / "gse-guardrails.ts"
    if ts.exists():
        ts_text = ts.read_text(encoding="utf-8")
        for needle in ("commit\\b", "--force\\b", "review_findings_open",
                       "protect_main", "block_force_push", "rev-parse --verify HEAD"):
            if needle not in ts_text:
                errors.append(f"opencode: gse-guardrails.ts missing pattern '{needle}'")

    # Codex-specific
    cx = PLUGIN / "codex"
    print(f"\n  Codex CLI:")
    cx_skills = sum(1 for n in ACTIVITY_NAMES if (cx / "skills" / f"gse-{n}" / "SKILL.md").exists())
    cx_orch_skill = (cx / "skills" / "gse-orchestrator" / "SKILL.md").exists()
    cx_agents = sum(1 for f in SPECIALIZED_AGENTS if (cx / "agents" / f"{Path(f).stem}.toml").exists())
    print(f"    Skills:    {cx_skills}/{len(ACTIVITY_NAMES)} (+ orchestrator={'OK' if cx_orch_skill else 'MISSING'})")
    print(f"    Agents:    {cx_agents}/{len(SPECIALIZED_AGENTS)} (toml, specialized only)")
    if cx_skills < len(ACTIVITY_NAMES): errors.append(f"codex: missing {len(ACTIVITY_NAMES)-cx_skills} skills")
    if not cx_orch_skill: errors.append("codex: missing full orchestrator skill")
    if cx_agents < len(SPECIALIZED_AGENTS): errors.append(f"codex: missing {len(SPECIALIZED_AGENTS)-cx_agents} agent toml")
    for name, path in {
        "AGENTS.md": cx / "AGENTS.md",
        "hooks/hooks.json": cx / "hooks" / "hooks.json",
        ".codex-plugin/plugin.json": cx / ".codex-plugin" / "plugin.json",
    }.items():
        ok_e = path.exists()
        print(f"    {name}: {'OK' if ok_e else 'MISSING'}")
        if not ok_e: errors.append(f"codex: missing {name}")
    cx_md = cx / "AGENTS.md"
    if cx_md.exists():
        size = len(cx_md.read_text(encoding="utf-8").encode("utf-8"))
        if size <= CODEX_AGENTS_MD_MAX_BYTES:
            print(f"    AGENTS.md size: {size} bytes (OK <= {CODEX_AGENTS_MD_MAX_BYTES})")
        else:
            print(f"    AGENTS.md size: {size} bytes (OVERSIZE > {CODEX_AGENTS_MD_MAX_BYTES})")
            errors.append(f"codex: AGENTS.md {size} bytes exceeds {CODEX_AGENTS_MD_MAX_BYTES}")
    # Agent TOML structural sanity (no tomllib on py<3.11): balanced ''' + keys
    bad_toml = []
    for f in SPECIALIZED_AGENTS:
        p = cx / "agents" / f"{Path(f).stem}.toml"
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            if (txt.count("'''") != 2 or "developer_instructions = '''" not in txt
                    or not txt.startswith("name =")):
                bad_toml.append(Path(f).stem)
    if bad_toml:
        errors.append(f"codex: malformed agent toml ({', '.join(bad_toml)})")
    elif cx_agents:
        print(f"    Agent toml: all {cx_agents} structurally valid")
    # Hook guardrail parity with shared commands
    cx_hooks_f = cx / "hooks" / "hooks.json"
    if cx_hooks_f.exists():
        shared = _guardrail_commands()
        ht = cx_hooks_f.read_text(encoding="utf-8")
        for key in ("pre_commit", "pre_force", "post_review", "post_dashboard"):
            if json.dumps(shared[key])[1:-1] not in ht:
                errors.append(f"codex: hooks.json missing/diverged guardrail '{key}'")

    # Gemini-specific
    gm = PLUGIN / "gemini"
    print(f"\n  Gemini CLI:")
    gm_cmds = sum(1 for n in ACTIVITY_NAMES if (gm / "commands" / "gse" / f"{n}.toml").exists())
    gm_agents = sum(1 for f in SPECIALIZED_AGENTS if (gm / "agents" / f).exists())
    print(f"    Commands:  {gm_cmds}/{len(ACTIVITY_NAMES)} (/gse:<name>)")
    print(f"    Agents:    {gm_agents}/{len(SPECIALIZED_AGENTS)}")
    if gm_cmds < len(ACTIVITY_NAMES): errors.append(f"gemini: missing {len(ACTIVITY_NAMES)-gm_cmds} commands")
    if gm_agents < len(SPECIALIZED_AGENTS): errors.append(f"gemini: missing {len(SPECIALIZED_AGENTS)-gm_agents} agents")
    for name, path in {
        "GEMINI.md": gm / "GEMINI.md",
        "hooks/hooks.json": gm / "hooks" / "hooks.json",
        "gemini-extension.json": gm / "gemini-extension.json",
    }.items():
        ok_e = path.exists()
        print(f"    {name}: {'OK' if ok_e else 'MISSING'}")
        if not ok_e: errors.append(f"gemini: missing {name}")
    # No raw {{ left in any command prompt (template-collision guard)
    raw_braces = [n for n in ACTIVITY_NAMES
                  if (gm / "commands" / "gse" / f"{n}.toml").exists()
                  and "{{" in (gm / "commands" / "gse" / f"{n}.toml").read_text(encoding="utf-8")]
    if raw_braces:
        errors.append(f"gemini: un-neutralized template braces in command prompt ({', '.join(raw_braces)})")
    elif gm_cmds:
        print(f"    Template guard: no raw template braces in {gm_cmds} prompts")
    # Command TOML structural sanity (balanced ''')
    gm_bad = [n for n in ACTIVITY_NAMES
              if (gm / "commands" / "gse" / f"{n}.toml").exists()
              and (gm / "commands" / "gse" / f"{n}.toml").read_text(encoding="utf-8").count("'''") != 2]
    if gm_bad:
        errors.append(f"gemini: malformed command toml ({', '.join(gm_bad)})")

    # Body parity
    print("\n  Cross-platform parity:")
    if orchestrator and (PLUGIN / "rules" / "gse-orchestrator.mdc").exists():
        agent_body = extract_body(PLUGIN / "agents" / "gse-orchestrator.md")
        mdc_body = extract_body(PLUGIN / "rules" / "gse-orchestrator.mdc")
        parity = agent_body == mdc_body
        print(f"    Orchestrator vs .mdc body: {'IDENTICAL' if parity else 'DIVERGENT!'}")
        if not parity: errors.append("Orchestrator and .mdc body content differ!")

        # opencode AGENTS.md body parity (strip markers + header)
        agents_md = oc / "AGENTS.md"
        if agents_md.exists():
            md_text = agents_md.read_text(encoding="utf-8")
            inside = md_text.split(OPENCODE_AGENTS_MD_START, 1)[-1].split(OPENCODE_AGENTS_MD_END, 1)[0]
            # Strip the header lines we injected and compare the remainder against the .mdc body
            oc_body = inside
            if mdc_body.strip() in oc_body:
                print(f"    AGENTS.md vs .mdc body:    IDENTICAL")
            else:
                print(f"    AGENTS.md vs .mdc body:    DIVERGENT!")
                errors.append("opencode AGENTS.md body differs from .mdc body")

        # Gemini GEMINI.md body parity (full orchestrator, like opencode)
        gemini_md = (PLUGIN / "gemini" / "GEMINI.md")
        if gemini_md.exists():
            gm_text = gemini_md.read_text(encoding="utf-8")
            gm_inside = gm_text.split(OPENCODE_AGENTS_MD_START, 1)[-1].split(OPENCODE_AGENTS_MD_END, 1)[0]
            if mdc_body.strip() in gm_inside:
                print(f"    GEMINI.md vs .mdc body:    IDENTICAL")
            else:
                print(f"    GEMINI.md vs .mdc body:    DIVERGENT!")
                errors.append("gemini GEMINI.md body differs from .mdc body")

        # Codex AGENTS.md is the CONDENSED lite edition (B1) — NOT byte-parity
        # with the full orchestrator by design. We assert it derives from the
        # lite source instead (its body must appear inside AGENTS.md).
        codex_md = (PLUGIN / "codex" / "AGENTS.md")
        lite_src = AGENTS_DIR / "gse-orchestrator-lite.md"
        if codex_md.exists() and lite_src.exists():
            lite_body = extract_body(lite_src).strip()
            cx_inside = codex_md.read_text(encoding="utf-8")
            if lite_body in cx_inside:
                print(f"    Codex AGENTS.md vs lite:   IDENTICAL (condensed by design)")
            else:
                print(f"    Codex AGENTS.md vs lite:   DIVERGENT!")
                errors.append("codex AGENTS.md body differs from gse-orchestrator-lite source")

    # Registry resolution: every `cat ~/.gse-one` in deployed artefacts must be
    # wrapped in the project-local-first form (count of bare == count of resolved,
    # since each resolved form contains exactly one trailing bare form).
    print("\n  Registry resolution (project-local-first):")
    g = r = 0
    for path in PLUGIN.rglob("*"):
        if path.is_file() and path.suffix in (".md", ".mdc", ".toml"):
            t = path.read_text(encoding="utf-8")
            g += t.count(REGISTRY_GLOBAL)
            r += t.count(REGISTRY_RESOLVED)
    if r > 0 and g == r:
        print(f"    OK ({r} incantation(s) localized, global fallback preserved)")
    elif g != r:
        print(f"    DRIFT: {g - r} bare `cat ~/.gse-one` not localized")
        errors.append(f"registry resolution: {g - r} bare incantation(s) not localized")
    else:
        print(f"    (no registry incantations in artefacts)")

    # Project launcher
    print("\n  Launcher (gse-run):")
    launcher = PLUGIN / "gse-run"
    if launcher.exists():
        lt = launcher.read_text(encoding="utf-8")
        missing = [m for m in ("launch.env", "GSE-One: launching", "exec \"$bin\"",
                               ".gse-sandbox", "XDG_CONFIG_HOME") if m not in lt]
        if missing:
            errors.append(f"gse-run launcher missing: {', '.join(missing)}")
            print(f"    MISSING markers: {', '.join(missing)}")
        elif not lt.startswith("#!/bin/sh"):
            errors.append("gse-run launcher missing shebang")
            print("    MISSING shebang")
        else:
            print("    OK (generic, mode-detecting)")
    else:
        errors.append("Missing plugin/gse-run launcher")
        print("    MISSING plugin/gse-run")

    # External docs consistency — warning-level (non-blocking).
    # Build-time early alert: visible but not fatal so prose can evolve
    # (reformulation, localization). Definitive numeric-drift audit is in
    # gse-one/audit.py (/gse-audit Python engine).
    ext_mismatches = verify_external_docs()
    print(f"\n  External docs consistency:")
    if ext_mismatches:
        print(f"    WARNING: {len(ext_mismatches)} phrase(s) out of sync (non-blocking):")
        for m in ext_mismatches:
            print(f"      - {m}")
        print(f"    Run `python3 gse-one/audit.py` for full numeric drift analysis.")
    else:
        print(f"    OK (README.md, install.py, gse-one/README.md aligned with registries)")

    # Run unit tests if available (opt-in via directory presence).
    tests_dir = ROOT / "tests"
    if tests_dir.exists() and any(tests_dir.glob("test_*.py")):
        print("\n  Unit tests:")
        import io
        import unittest
        try:
            loader = unittest.TestLoader()
            suite = loader.discover(str(tests_dir), pattern="test_*.py")
            stream = io.StringIO()
            runner = unittest.TextTestRunner(verbosity=1, stream=stream)
            result = runner.run(suite)
            if not result.wasSuccessful():
                print(stream.getvalue())
                errors.append(
                    f"Unit tests failed: {len(result.failures)} failures, "
                    f"{len(result.errors)} errors"
                )
            else:
                print(f"    OK ({result.testsRun} tests, "
                      f"{result.skipped and len(result.skipped) or 0} skipped)")
        except Exception as e:  # noqa: BLE001
            errors.append(f"Unit test runner failed: {e}")

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
