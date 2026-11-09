#!/usr/bin/env python3
"""GSE-One Installer — Cross-platform install for Claude Code, Cursor, opencode, Codex CLI, and Gemini CLI.

Usage:
    python3 install.py                        # Interactive mode
    python3 install.py --platform claude --mode project     # everything in the project (default mode)
    python3 install.py --platform cursor --mode machine     # once for the whole machine
    python3 install.py --platform codex --mode project --project-dir /path/to/project
    python3 install.py --platform codex --mode sandbox --project-dir /path/to/project
    python3 install.py --uninstall --platform gemini

Modes (renamed by user need in v0.87.0 — the old plugin/no-plugin/local names
and the --scope flag were removed in the same release, pre-1.0 clean break):
    project  — everything in the project folder; registry at <project>/.gse/registry;
               nothing under $HOME (ex 'local'; absorbs ex 'no-plugin')
    machine  — one install for the whole machine, under $HOME (ex 'plugin';
               on Claude this is the ex '--scope user' placement)
    sandbox  — project-internal $HOME + launcher (codex/gemini/opencode)
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent
VERSION_FILE = REPO_ROOT / "VERSION"
PLUGIN_DIR = REPO_ROOT / "gse-one" / "plugin"
OPENCODE_PLUGIN_DIR = PLUGIN_DIR / "opencode"
OPENCODE_GLOBAL_DIR = Path.home() / ".config" / "opencode"

# Codex CLI install targets. Skills live under .agents/skills/ (Codex scan
# path); agents are TOML under .codex/agents/; AGENTS.md is the always-on
# context (condensed lite edition); hooks live FLAT at .codex/hooks.json
# (the only standalone discovery path) and require the user's one-time
# /hooks trust approval to actually run.
CODEX_PLUGIN_DIR = PLUGIN_DIR / "codex"
CODEX_GLOBAL_DIR = Path.home() / ".codex"
CODEX_SKILLS_HOME = Path.home() / ".agents" / "skills"

# Gemini CLI install targets. Plugin mode = a dedicated extension dir under
# ~/.gemini/extensions/; project mode = project .gemini/ + root GEMINI.md.
GEMINI_PLUGIN_DIR = PLUGIN_DIR / "gemini"
GEMINI_GLOBAL_DIR = Path.home() / ".gemini"
GEMINI_EXT_DIR = GEMINI_GLOBAL_DIR / "extensions" / "gse-one"

# Markers used to surgically patch AGENTS.md on install/uninstall
AGENTS_MD_START = "<!-- GSE-ONE START -->"
AGENTS_MD_END = "<!-- GSE-ONE END -->"

if VERSION_FILE.exists():
    VERSION = VERSION_FILE.read_text().strip()
else:
    VERSION = "unknown"


# ---------------------------------------------------------------------------
# Colors (ANSI, with Windows support)
# ---------------------------------------------------------------------------

def _supports_color():
    """Detect whether the terminal supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if platform.system() == "Windows":
        # Enable ANSI on Windows 10+
        try:
            os.system("")  # enables ANSI escape processing
            return True
        except Exception:
            return False
    return True


USE_COLOR = _supports_color()


def _c(code, text):
    """Apply ANSI color code to text if supported."""
    if USE_COLOR:
        return f"\033[{code}m{text}\033[0m"
    return text


def green(t):   return _c("32", t)
def red(t):     return _c("31", t)
def yellow(t):  return _c("33", t)
def cyan(t):    return _c("36", t)
def bold(t):    return _c("1", t)
def dim(t):     return _c("2", t)


BANNER = f"""
  {bold(cyan('GSE-One Installer'))}  v{VERSION}
  {dim('Setup for Claude Code, Cursor, opencode, Codex CLI, and Gemini CLI')}
  {'─' * 50}
"""


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def info(msg):  print(f"  {dim('[INFO]')}  {msg}")
def ok(msg):    print(f"  {green('[ OK ]')}  {msg}")
def warn(msg):  print(f"  {yellow('[WARN]')}  {msg}")
def err(msg):   print(f"  {red('[ERR ]')}  {msg}", file=sys.stderr)
def step(msg):  print(f"\n  {bold(msg)}\n  {'─' * len(msg)}")


# ---------------------------------------------------------------------------
# Installation tracker (for summary table)
# ---------------------------------------------------------------------------

class InstallTracker:
    """Tracks installation actions and their results for the summary."""

    def __init__(self):
        self.rows = []  # list of (platform, mode, scope, location, status, detail)

    def add(self, plat, mode, scope, location, status, detail=""):
        self.rows.append((plat, mode, scope, str(location), status, detail))

    def display(self):
        """Print the final summary."""
        if not self.rows:
            return

        print()
        step("Summary")
        print()

        for plat, mode, scope, location, status, detail in self.rows:
            if status == "OK":
                status_str = green("OK")
            elif status == "WARN":
                status_str = yellow("WARN")
            else:
                status_str = red("FAIL")

            print(f"  {status_str}  {bold(plat)} — {mode} ({scope})")
            if detail:
                print(f"       {dim(detail)}")
            if location and location != "-":
                loc_short = location
                if len(loc_short) > 70:
                    loc_short = "..." + loc_short[-67:]
                print(f"       {dim(loc_short)}")
            print()

        all_ok = all(s == "OK" for _, _, _, _, s, _ in self.rows)
        if all_ok:
            print(f"  {green('All installations succeeded.')}")
        else:
            has_fail = any(s == "FAIL" for _, _, _, _, s, _ in self.rows)
            if has_fail:
                print(f"  {red('Some installations failed. See details above.')}")
            else:
                print(f"  {yellow('Completed with warnings. See details above.')}")

        print()
        # Per-platform AND per-mode invocation syntax (README "What gets installed"):
        # Claude exposes /gse:go in every mode since v0.87.0 (both routes are plugins);
        # Cursor/opencode use /gse-go in both modes; Gemini uses /gse:go; Codex
        # skills are invoked via $gse-go (or /skills) — NOT a colon/slash command.
        # Tracker rows store display names ("Claude Code") in most paths and
        # lowercase names in the sandbox path — normalize before lookup.
        def _norm_plat(name):
            n = name.lower()
            if "claude" in n:
                return "claude"
            for k in ("cursor", "opencode", "codex", "gemini"):
                if k in n:
                    return k
            return n

        def _go_hint(plat_key, mode):
            if plat_key == "claude":
                # Both machine and project routes are skills-dir plugins now —
                # the /gse: namespace applies everywhere on Claude.
                return "/gse:go"
            if plat_key in ("cursor", "opencode"):
                return "/gse-go"
            if plat_key == "gemini":
                return "/gse:go"
            if plat_key == "codex":
                return "$gse-go   (or /skills to browse)"
            return "/gse:go"

        ok_plats = []  # list of (display_name, plat_key, mode)
        for plat, mode, _, _, status, _ in self.rows:
            key = _norm_plat(plat)
            if status == "OK" and all(k != key for _, k, _ in ok_plats):
                ok_plats.append((plat, key, mode))
        if ok_plats:
            print(f"  {cyan('Next step')} — start GSE-One:")
            for disp, key, mode in ok_plats:
                print(f"       {bold(disp)}: type {bold(_go_hint(key, mode))}")
        else:
            print(f"  {cyan('Next step:')} Type {bold('/gse:go')} in your coding agent to start.")
        print()


tracker = InstallTracker()


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def ask(prompt, choices):
    """Ask the user to pick from a numbered list. Returns the chosen value."""
    print()
    for i, (label, _) in enumerate(choices, 1):
        print(f"    {bold(f'[{i}]')} {label}")
    print()
    while True:
        try:
            raw = input(f"  {prompt} [1-{len(choices)}]: ").strip()
            idx = int(raw)
            if 1 <= idx <= len(choices):
                return choices[idx - 1][1]
        except (ValueError, EOFError):
            pass
        warn(f"Please enter a number between 1 and {len(choices)}.")


def confirm(prompt):
    """Ask yes/no. Returns True for yes. Auto-accepts when stdin is not a TTY
    (e.g. under `curl | sh`), preserving install.sh's zero-prompt contract."""
    if not sys.stdin.isatty():
        info(f"  {prompt} [auto-yes: non-interactive stdin]")
        return True
    while True:
        try:
            raw = input(f"  {prompt} [{green('y')}/{red('n')}]: ").strip().lower()
        except EOFError:
            return True
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False


def command_exists(cmd):
    """Check if a command is available on PATH."""
    return shutil.which(cmd) is not None


def remove_path(path):
    """Remove a file, symlink, or directory tree."""
    path = Path(path)
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def copy_tree(src, dst):
    """Copy a directory tree, overwriting destination if it exists."""
    dst = Path(dst)
    remove_path(dst)
    shutil.copytree(src, dst)


def ensure_dir(path):
    """Create directory and parents if needed."""
    Path(path).mkdir(parents=True, exist_ok=True)


REGISTRY_FILE = Path.home() / ".gse-one"

# Side-install location used ONLY by claude plugin mode. Claude Code's CLI
# stores the plugin at an internal, version-dependent path that is not stable
# for shell-script resolution. To keep `$(cat ~/.gse-one)/tools/X.py` working
# regardless of claude-internals, install.py drops a self-contained copy of
# the runtime-resolvable assets (tools/, templates/, references/, VERSION)
# under ~/.gse-one.d/ and points the registry there. All other modes (cursor
# machine and project modes of every platform) point the registry at their
# own target install dir directly —
# no side-install needed.
GSE_ONE_DATA_DIR = Path.home() / ".gse-one.d"


# Fully-local install mode: when set to a project Path, the registry is written
# to <project>/.gse/registry (relative content) instead of the global
# ~/.gse-one — so the install touches NOTHING under $HOME and the project is
# self-contained / committable. Set by main()/menu when --mode project is chosen.
_LOCAL_REGISTRY_PROJECT = None


def _write_registry(plugin_path):
    """Write the install-target path to the registry so tools resolve at runtime.

    Global modes write the absolute path to ~/.gse-one. Local mode (when
    _LOCAL_REGISTRY_PROJECT is set) writes a path RELATIVE to the project root
    into <project>/.gse/registry — no $HOME file, and portable across machines
    (resolved relative to the project root, where the agent's CWD already is)."""
    if _LOCAL_REGISTRY_PROJECT is not None:
        proj = Path(_LOCAL_REGISTRY_PROJECT).resolve()
        reg = proj / ".gse" / "registry"
        ensure_dir(reg.parent)
        try:
            content = str(Path(plugin_path).resolve().relative_to(proj))
        except ValueError:
            content = str(Path(plugin_path).resolve())  # outside project → absolute
        reg.write_text(content + "\n", encoding="utf-8")
        ok(f"Local registry written: {reg} → {content} (no ~/.gse-one)")
        return
    REGISTRY_FILE.write_text(str(Path(plugin_path).resolve()) + "\n", encoding="utf-8")
    ok(f"Registry written: {REGISTRY_FILE} → {plugin_path}")


def _maybe_local(mode, project_dir):
    """Arm/disarm project-local registry placement based on the chosen mode.

    Sets _LOCAL_REGISTRY_PROJECT to project_dir when mode == 'project' (so
    _write_registry / _remove_registry target <project>/.gse/registry — the
    project mode writes NOTHING under $HOME), else clears it. Returns
    project_dir for call-site convenience."""
    global _LOCAL_REGISTRY_PROJECT
    _LOCAL_REGISTRY_PROJECT = Path(project_dir) if mode == "project" else None
    return project_dir


def _remove_registry():
    """Remove the registry file (local <project>/.gse/registry or global ~/.gse-one)."""
    if _LOCAL_REGISTRY_PROJECT is not None:
        reg = Path(_LOCAL_REGISTRY_PROJECT) / ".gse" / "registry"
        if reg.exists():
            reg.unlink()
            ok(f"Local registry removed: {reg}")
        return
    if REGISTRY_FILE.exists():
        REGISTRY_FILE.unlink()
        ok(f"Registry removed: {REGISTRY_FILE}")


def _copy_common_assets(target):
    """Copy tools/, templates/, references/, VERSION, and gse.json into target.

    These are the runtime-resolvable assets that skills reach via
    `$(cat ~/.gse-one)/<subdir>/...`. Having them co-located with the registry
    target makes every install mode self-contained — the gensem source repo
    can be deleted after install and nothing breaks. gse.json carries the
    Axe 2 upstream-repository metadata, uniform across all platforms.

    Idempotent: each subdir is removed-then-copied; files are overwritten.
    """
    target = Path(target)
    ensure_dir(target)
    for subdir in ("tools", "templates", "references"):
        src = PLUGIN_DIR / subdir
        if src.is_dir():
            copy_tree(src, target / subdir)
    for meta_file in ("VERSION", "gse.json"):
        meta_src = PLUGIN_DIR / meta_file
        if meta_src.exists():
            shutil.copy2(meta_src, target / meta_file)


def _remove_common_assets(target):
    """Symmetric uninstaller for _copy_common_assets.

    Removes any of tools/, templates/, references/, VERSION, gse.json that
    exist under target. Safe to call when target itself does not exist.
    """
    target = Path(target)
    if not target.exists():
        return
    for subdir in ("tools", "templates", "references"):
        d = target / subdir
        if d.is_dir():
            shutil.rmtree(d)
    for meta_file in ("VERSION", "gse.json"):
        mf = target / meta_file
        if mf.exists():
            mf.unlink()



# ---------------------------------------------------------------------------
# Duplicate installation detection
# ---------------------------------------------------------------------------

def _detect_claude_plugin_installed(project_dir=None):
    """Return True if a GSE plugin install exists for Claude Code.

    Checks (1) skills-directory installs (gse/ with a plugin manifest under
    <project>/.claude/skills/ or ~/.claude/skills/ — pure filesystem, no CLI
    registration), then (2) CLI-registered plugins via
    `claude plugin list --json` (id 'gse' or 'gse@<marketplace>'), with a
    tolerant text fallback for older CLIs. Returns False when nothing is
    found or the CLI is absent/failing.
    """
    for scope in ("project", "user"):
        target = _claude_skillsdir_root(scope, project_dir) / "gse"
        if (target / ".claude-plugin" / "plugin.json").exists():
            return True
    if not command_exists("claude"):
        return False
    try:
        result = subprocess.run(
            ["claude", "plugin", "list", "--json"],
            capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    if result.returncode == 0:
        try:
            plugins = json.loads(result.stdout)
            for p in plugins:
                pid = str(p.get("id", ""))
                if pid == "gse" or pid.startswith("gse@"):
                    return True
            return False
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass
    # Fallback for CLIs without --json: tolerant text scan.
    try:
        result = subprocess.run(
            ["claude", "plugin", "list"],
            capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    for line in result.stdout.splitlines():
        tokens = line.strip().lstrip("❯").split()
        if tokens and (tokens[0].lower() == "gse"
                       or tokens[0].lower().startswith("gse@")):
            return True
    return False


def _has_gse_skills_in_dir(skills_dir):
    """Return True if skills_dir contains GSE-One skills (prefixed or legacy)."""
    if not skills_dir.is_dir():
        return False
    known = set(_get_skill_names())
    for d in skills_dir.iterdir():
        if not d.is_dir():
            continue
        # New prefixed layout: gse-<name>
        if d.name.startswith("gse-") and d.name[4:] in known:
            return True
        # Legacy unprefixed layout (<= v0.20.4)
        if d.name in known:
            return True
    return False


def _check_duplicate_install(platform_name, mode, project_dir=None, env=None):
    """Warn if another installation mode already exists for this platform.

    Returns True if the user wants to proceed despite the warning, False to abort.
    """
    conflicts = []

    if platform_name == "claude":
        if mode == "machine":
            # A project-level install in the CURRENT project would co-load with
            # the machine install (legacy gse-* skills or the project plugin).
            local = Path(project_dir or Path.cwd()) / ".claude" / "skills"
            if _has_gse_skills_in_dir(local):
                conflicts.append(("legacy project skills", str(local)))
            if (local / "gse" / ".claude-plugin" / "plugin.json").exists():
                conflicts.append(("project install", str(local / "gse")))
            # Legacy gse-* skills at home level (pre-0.87.0 layouts).
            home = Path.home() / ".claude" / "skills"
            if _has_gse_skills_in_dir(home):
                conflicts.append(("legacy machine skills", str(home)))
        elif mode == "project":
            # Only MACHINE-level installs conflict (they co-load in every
            # project); the project's own prior install is replaced in place.
            home_plugin = Path.home() / ".claude" / "skills" / "gse"
            if (home_plugin / ".claude-plugin" / "plugin.json").exists():
                conflicts.append(("machine install", str(home_plugin)))
            home = Path.home() / ".claude" / "skills"
            if _has_gse_skills_in_dir(home):
                conflicts.append(("legacy machine skills", str(home)))

    elif platform_name == "cursor":
        if mode == "machine" and env:
            # Check for a project install in the current project
            local = Path.cwd() / ".cursor" / "commands"
            if local.is_dir() and any(local.iterdir()):
                conflicts.append(("project install", str(local)))
        elif mode == "project" and env:
            # Check for global plugin install
            global_plugin = env["cursor_dir"] / "plugins" / "local" / "gse-one"
            if global_plugin.is_dir():
                conflicts.append(("plugin (global)", str(global_plugin)))
        # Legacy pre-0.87.0 Claude layouts left GSE agent .md files in
        # .claude/agents/, which Cursor auto-loads as subagents (the
        # orchestrator would leak in, redundant with the .mdc rule). Current
        # Claude installs keep agents inside the plugin body — re-running the
        # Claude install cleans the legacy files up.
        legacy_agents = Path(project_dir or Path.cwd()) / ".claude" / "agents"
        if legacy_agents.is_dir() and (legacy_agents / "gse-orchestrator.md").exists():
            conflicts.append(("legacy Claude layout (.claude/agents auto-loaded by Cursor"
                              " — re-run the Claude install to clean)", str(legacy_agents)))

    elif platform_name == "opencode":
        if mode == "machine":
            # Global install — check for local .opencode/ in the current project
            local = Path(project_dir or Path.cwd()) / ".opencode" / "commands"
            if local.is_dir() and any(local.glob("gse-*.md")):
                conflicts.append(("project install", str(local.parent)))
            # opencode also scans ~/.agents/skills/ — where Codex machine
            # installs put their skills: co-loads every gse-* skill twice.
            if (CODEX_SKILLS_HOME / "gse-go").is_dir():
                conflicts.append(("Codex machine install (~/.agents/skills"
                                  " auto-loaded by opencode)", str(CODEX_SKILLS_HOME)))
        elif mode == "project":
            # Local install — check for a global install that would duplicate skills
            global_skills = OPENCODE_GLOBAL_DIR / "skills"
            if global_skills.is_dir() and any(d.name in _get_skill_names()
                                              for d in global_skills.iterdir() if d.is_dir()):
                conflicts.append(("plugin (global)", str(OPENCODE_GLOBAL_DIR)))
            # Also warn if a .claude/skills layout exists — opencode loads those too
            claude_skills = Path(project_dir or Path.cwd()) / ".claude" / "skills"
            if _has_gse_skills_in_dir(claude_skills):
                conflicts.append((".claude/skills (auto-loaded by opencode)", str(claude_skills)))
            # ... and the project-level Codex scan path (.agents/skills)
            codex_proj_skills = Path(project_dir or Path.cwd()) / ".agents" / "skills"
            if (codex_proj_skills / "gse-go").is_dir():
                conflicts.append((".agents/skills (Codex project install,"
                                  " auto-loaded by opencode)", str(codex_proj_skills)))

    elif platform_name == "codex":
        if mode == "machine":
            local = Path(project_dir or Path.cwd()) / ".agents" / "skills"
            if local.is_dir() and (local / "gse-go").is_dir():
                conflicts.append(("project install", str(local)))
        elif mode == "project":
            home_skills = CODEX_SKILLS_HOME
            if home_skills.is_dir() and (home_skills / "gse-go").is_dir():
                conflicts.append(("plugin (global)", str(home_skills)))

    elif platform_name == "gemini":
        if mode == "machine":
            local = Path(project_dir or Path.cwd()) / ".gemini" / "commands" / "gse"
            if local.is_dir() and any(local.glob("*.toml")):
                conflicts.append(("project install", str(local.parent.parent)))
        elif mode == "project":
            if GEMINI_EXT_DIR.is_dir():
                conflicts.append(("plugin (global extension)", str(GEMINI_EXT_DIR)))

    if conflicts:
        warn(f"Existing GSE-One installation(s) detected for {bold(platform_name)}:")
        for conflict_mode, conflict_path in conflicts:
            warn(f"  → {conflict_mode}: {dim(conflict_path)}")
        warn("Having both will cause duplicate commands (skills appear twice).")
        warn(f"Uninstall the other first: python3 install.py --uninstall --platform {platform_name} --mode <machine|project>")
        if not confirm("Proceed anyway?"):
            err("Installation cancelled to avoid duplicates.")
            return False
    return True


# ---------------------------------------------------------------------------
# Post-install verification
# ---------------------------------------------------------------------------

def verify_plugin(location, platform_name):
    """Verify a plugin installation is valid. Returns (ok, detail)."""
    location = Path(location)

    # 1. Directory exists
    if not location.is_dir():
        return False, "directory not found"

    # 2. Find and parse manifest
    if platform_name == "claude":
        manifest = location / ".claude-plugin" / "plugin.json"
    else:
        manifest = location / ".cursor-plugin" / "plugin.json"

    if not manifest.exists():
        return False, "manifest not found"

    try:
        data = json.loads(manifest.read_text())
    except (json.JSONDecodeError, OSError):
        return False, "manifest is not valid JSON"

    # 3. Version present and matches
    manifest_version = data.get("version", "")
    if manifest_version == VERSION:
        return True, f"v{manifest_version}"
    elif manifest_version:
        return True, f"v{manifest_version} (expected {VERSION})"
    else:
        return False, "no version in manifest"


def verify_no_plugin(location, platform_name):
    """Verify a project-mode Cursor installation. Returns (ok, detail).

    Cursor-only since v0.87.0 — the Claude project route installs a
    skills-directory plugin and verifies inline."""
    base = Path(location) / ".cursor"
    if not base.is_dir():
        return False, f"{base.name}/ not found"
    agents = base / "agents"
    if not agents.is_dir():
        return False, "agents/ not found"
    agent_count = sum(1 for f in agents.glob("*.md"))
    commands = base / "commands"
    if not commands.is_dir():
        return False, "commands/ not found"
    cmd_count = sum(1 for f in commands.glob("*.md"))
    return True, f"{cmd_count} commands, {agent_count} agents"


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect_environment():
    """Detect OS and Claude Code, Cursor, opencode, Codex, Gemini availability."""
    os_name = platform.system()
    os_display = {"Darwin": "macOS", "Linux": "Linux", "Windows": "Windows"}.get(os_name, os_name)

    has_claude = command_exists("claude")
    has_cursor = _detect_cursor(os_name)
    has_opencode = _detect_opencode()
    has_codex = _detect_codex()
    has_gemini = _detect_gemini()

    home = Path.home()
    claude_dir = home / ".claude"
    cursor_dir = home / ".cursor"
    opencode_dir = OPENCODE_GLOBAL_DIR

    return {
        "os": os_display,
        "os_raw": os_name,
        "has_claude": has_claude,
        "has_cursor": has_cursor,
        "has_opencode": has_opencode,
        "has_codex": has_codex,
        "has_gemini": has_gemini,
        "home": home,
        "claude_dir": claude_dir,
        "cursor_dir": cursor_dir,
        "opencode_dir": opencode_dir,
        "codex_dir": CODEX_GLOBAL_DIR,
        "gemini_dir": GEMINI_GLOBAL_DIR,
    }


def _detect_cursor(os_name):
    """Detect if Cursor is installed."""
    home = Path.home()
    if os_name == "Darwin":
        return (Path("/Applications/Cursor.app").exists()
                or (home / "Applications" / "Cursor.app").exists()
                or (home / ".cursor").exists())
    elif os_name == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        return (local / "Programs" / "cursor").exists() or (home / ".cursor").exists()
    else:  # Linux
        return (command_exists("cursor")
                or (home / ".cursor").exists())


def _detect_opencode():
    """Detect if opencode is installed (CLI on PATH or ~/.config/opencode/ dir)."""
    return command_exists("opencode") or OPENCODE_GLOBAL_DIR.exists()


def _detect_codex():
    """Detect if Codex CLI is installed (CLI on PATH or ~/.codex/ dir)."""
    return command_exists("codex") or CODEX_GLOBAL_DIR.exists()


def _detect_gemini():
    """Detect if Gemini CLI is installed (CLI on PATH or ~/.gemini/ dir)."""
    return command_exists("gemini") or GEMINI_GLOBAL_DIR.exists()


def display_environment(env):
    """Print detected environment."""
    step("Environment")
    info(f"Operating system : {bold(env['os'])}")
    info(f"Home directory   : {env['home']}")
    info(f"Claude Code CLI  : {green('found') if env['has_claude'] else yellow('not found')}")
    info(f"Cursor           : {green('found') if env['has_cursor'] else yellow('not found')}")
    info(f"opencode         : {green('found') if env['has_opencode'] else yellow('not found')}")
    info(f"Codex CLI        : {green('found') if env['has_codex'] else yellow('not found')}")
    info(f"Gemini CLI       : {green('found') if env['has_gemini'] else yellow('not found')}")
    info(f"Plugin source    : {PLUGIN_DIR}")
    info(f"Version          : {bold(VERSION)}")

    if not PLUGIN_DIR.exists():
        err(f"Plugin directory not found: {PLUGIN_DIR}")
        err("Make sure you run this script from the gensem repository root.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Claude Code — machine mode (whole-$HOME) and project mode (self-contained)
# ---------------------------------------------------------------------------

def _claude_copy_plugin_body(target, include_hooks=True):
    """Copy the Claude plugin body (skills-directory plugin form) to target.

    Claude Code >= 2.1.x removed local-path `claude plugin install` (the CLI
    only accepts marketplace ids). The supported CLI-free route is a
    "skills-directory plugin": a directory under ~/.claude/skills/ or
    <project>/.claude/skills/ containing .claude-plugin/plugin.json
    auto-loads as `gse@skills-dir` — same file-copy style as every other
    platform.

    The copy is SELECTIVE (Claude components only: manifest, skills/, agents/,
    hooks.claude.json, settings.json). Copying all of plugin/ would let the
    commands/skills unification absorb the Cursor commands/ files as duplicate
    skills (48 instead of 24, doubled namespace + context cost). tools/,
    templates/ and references/ are NOT in this copy — they live at the
    registry target (~/.gse-one.d/ in machine mode, <project>/.claude/ in
    project mode).

    include_hooks=False (project mode): the hooks stay OUT of the plugin and
    the manifest `hooks` pointer is stripped — project-level skills-dir
    plugins only load after the workspace trust dialog, which would leave the
    deterministic guardrails inert in headless/untrusted contexts. Project
    mode merges the hooks into <project>/.claude/settings.json instead
    (verified to fire even without workspace trust): safety is
    trust-independent, UX (skills, agents) arrives with trust. Machine mode
    keeps hooks in the plugin (user-scope plugins are trusted by definition).
    """
    target = Path(target)
    if target.exists():
        remove_path(target)
    ensure_dir(target)
    copy_tree(PLUGIN_DIR / ".claude-plugin", target / ".claude-plugin")
    copy_tree(PLUGIN_DIR / "skills", target / "skills")
    copy_tree(PLUGIN_DIR / "agents", target / "agents")
    if include_hooks:
        ensure_dir(target / "hooks")
        shutil.copy2(PLUGIN_DIR / "hooks" / "hooks.claude.json",
                     target / "hooks" / "hooks.claude.json")
    else:
        manifest_file = target / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest.pop("hooks", None)
        manifest_file.write_text(json.dumps(manifest, indent=2) + "\n",
                                 encoding="utf-8")
    settings_src = PLUGIN_DIR / "settings.json"
    if settings_src.exists():
        shutil.copy2(settings_src, target / "settings.json")
    ok(f"Plugin copied to {target} (auto-loads as gse@skills-dir)")


def _claude_merge_hooks_into_settings(settings_file):
    """Merge the GSE hook entries into <project>/.claude/settings.json.

    Used by project mode so the deterministic guardrails run even before the
    workspace trust dialog is accepted (plugin-carried hooks would not).
    Preserves user keys and non-GSE hook entries; replaces previous GSE
    entries (marker: the one-liners read .gse/ state) in place.
    """
    src = json.loads((PLUGIN_DIR / "hooks" / "hooks.claude.json").read_text())
    settings_file = Path(settings_file)
    ensure_dir(settings_file.parent)
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except (json.JSONDecodeError, OSError):
            warn(f"Could not parse existing {settings_file}; leaving it untouched.")
            warn("  GSE hooks NOT installed — fix the file and re-run the installer.")
            return False
    else:
        settings = {}
    hooks = settings.setdefault("hooks", {})
    for event, entries in src.get("hooks", {}).items():
        kept = [e for e in hooks.get(event, []) if ".gse" not in json.dumps(e)]
        hooks[event] = kept + entries
    settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    ok(f"Merged GSE hooks into {settings_file}")
    return True


def install_claude_machine():
    """Install GSE-One for the whole machine: skills-directory plugin under
    ~/.claude/skills/gse/ + common runtime assets at the ~/.gse-one.d/
    side-install (stable shell path), global registry ~/.gse-one."""
    step("Claude Code — Machine install (skills-dir plugin, ~/.claude)")

    if not _check_duplicate_install("claude", "machine"):
        tracker.add("Claude Code", "machine", "-", "-", "FAIL", "cancelled (duplicate)")
        return False

    target = Path.home() / ".claude" / "skills" / "gse"
    _claude_copy_plugin_body(target)

    _copy_common_assets(GSE_ONE_DATA_DIR)
    ok(f"Common assets copied to {GSE_ONE_DATA_DIR}")
    _write_registry(GSE_ONE_DATA_DIR)
    tracker.add("Claude Code", "machine", "-", str(target), "OK", f"v{VERSION}")
    return True


def uninstall_claude_machine():
    """Uninstall the machine-level Claude install (user skills-dir plugin,
    legacy CLI-registered plugins, side-install, global registry)."""
    step("Claude Code — Machine uninstall")

    removed_any = False
    target = Path.home() / ".claude" / "skills" / "gse"
    if (target / ".claude-plugin" / "plugin.json").exists():
        remove_path(target)
        ok(f"Removed skills-dir plugin: {target}")
        removed_any = True

    # Legacy cleanup — installs registered through the old CLI flow.
    if command_exists("claude"):
        for scope in ("project", "user", "local"):
            try:
                result = subprocess.run(
                    ["claude", "plugin", "uninstall", "gse", "--scope", scope],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0:
                    ok(f"Legacy CLI-registered plugin uninstalled (scope: {scope})")
                    removed_any = True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

    if not removed_any:
        info("No machine-level Claude install found — cleaning up shared assets anyway.")

    # Symmetric removal of the side-install dropped at install time
    _remove_common_assets(GSE_ONE_DATA_DIR)
    if GSE_ONE_DATA_DIR.exists() and not any(GSE_ONE_DATA_DIR.iterdir()):
        GSE_ONE_DATA_DIR.rmdir()
        ok(f"Removed {GSE_ONE_DATA_DIR}")
    _remove_registry()
    tracker.add("Claude Code", "uninstall", "-", "-", "OK", "removed")
    return True


# ---------------------------------------------------------------------------
# Claude Code — project mode (self-contained skills-dir plugin)
# ---------------------------------------------------------------------------

def _claude_remove_legacy_project_artifacts(claude_dir):
    """Remove pre-0.87.0 'no-plugin' artifacts from a project .claude/.

    Old layout: gse-* (or unprefixed <= v0.20.4) skill directories, copied
    agent .md files, GSE hook entries and the gse-orchestrator default agent
    in settings.json. The 0.87.0 project route replaces all of it with the
    single skills-dir plugin directory — upgrading in place must not leave a
    duplicate command surface. Returns the number of artifacts removed."""
    claude_dir = Path(claude_dir)
    removed = 0
    skills_dir = claude_dir / "skills"
    if skills_dir.is_dir():
        for name in _get_skill_names():
            for candidate in (skills_dir / f"gse-{name}", skills_dir / name):
                if candidate.is_dir() and (candidate / "SKILL.md").exists():
                    shutil.rmtree(candidate)
                    removed += 1
    agents_dir = claude_dir / "agents"
    if agents_dir.is_dir():
        for f in (PLUGIN_DIR / "agents").glob("*.md"):
            t = agents_dir / f.name
            if t.exists():
                t.unlink()
                removed += 1
    settings_file = claude_dir / "settings.json"
    if settings_file.exists():
        try:
            s = json.loads(settings_file.read_text())
        except (json.JSONDecodeError, OSError):
            s = None
        if isinstance(s, dict):
            changed = False
            hooks = s.get("hooks")
            if isinstance(hooks, dict):
                for event in list(hooks.keys()):
                    entries = hooks[event]
                    kept = [e for e in entries if ".gse" not in json.dumps(e)]
                    if len(kept) != len(entries):
                        changed = True
                        removed += len(entries) - len(kept)
                    if kept:
                        hooks[event] = kept
                    else:
                        del hooks[event]
                if not hooks:
                    s.pop("hooks", None)
            if s.get("agent") == "gse-orchestrator":
                s.pop("agent")
                changed = True
                removed += 1
            if changed:
                if s:
                    settings_file.write_text(json.dumps(s, indent=2) + "\n",
                                             encoding="utf-8")
                else:
                    settings_file.unlink()
                    ok(f"Removed {settings_file} (only GSE-One content)")
    if removed:
        ok(f"Removed {removed} legacy pre-0.87.0 artifact(s) from {claude_dir}")
    return removed


def install_claude_project(project_dir):
    """Install GSE-One entirely inside the project (nothing under $HOME).

    Skills-directory plugin at <project>/.claude/skills/gse/ (namespace
    /gse:<name>, native gse:* subagents, hooks + default agent carried by the
    plugin body) + common runtime assets at <project>/.claude/ + registry at
    <project>/.gse/registry. The project is self-contained: committable,
    syncable across machines, version pinned per project.
    """
    step("Claude Code — Project install (self-contained skills-dir plugin)")

    if not _check_duplicate_install("claude", "project", project_dir=project_dir):
        tracker.add("Claude Code", "project", "-", str(project_dir), "FAIL", "cancelled (duplicate)")
        return False

    project_dir = Path(project_dir)
    claude_dir = project_dir / ".claude"
    ensure_dir(claude_dir)

    # Upgrading a pre-0.87.0 'no-plugin' install in place: clear the old layout
    # first so the plugin and the legacy skills don't expose commands twice.
    _claude_remove_legacy_project_artifacts(claude_dir)

    _claude_copy_plugin_body(claude_dir / "skills" / "gse", include_hooks=False)
    _claude_merge_hooks_into_settings(claude_dir / "settings.json")
    info("Commands available as /gse:<name>; specialized agents as gse:* subagents")
    info("Guardrail hooks live in .claude/settings.json (active immediately).")
    info("Skills/agents load in trusted workspaces only:")
    info("  open the project in claude, accept the trust dialog, then run /reload-plugins.")

    _copy_common_assets(claude_dir)
    ok(f"Copied common assets (tools, templates, references, VERSION) to {claude_dir}")
    _write_registry(claude_dir)

    n_skills = sum(1 for d in (claude_dir / "skills" / "gse" / "skills").iterdir()
                   if d.is_dir() and (d / "SKILL.md").exists())
    tracker.add("Claude Code", "project", "-", str(claude_dir), "OK",
                f"v{VERSION}, {n_skills} skills")
    return True


def uninstall_claude_project(project_dir):
    """Remove the project-contained Claude install (plugin body, legacy
    no-plugin artifacts, common assets, project registry)."""
    step("Claude Code — Project uninstall")

    claude_dir = Path(project_dir) / ".claude"
    target = claude_dir / "skills" / "gse"
    if (target / ".claude-plugin" / "plugin.json").exists():
        remove_path(target)
        ok(f"Removed skills-dir plugin: {target}")
    skills_dir = claude_dir / "skills"
    if skills_dir.is_dir() and not any(skills_dir.iterdir()):
        skills_dir.rmdir()

    _claude_remove_legacy_project_artifacts(claude_dir)
    _remove_common_assets(claude_dir)
    ok(f"Removed common assets (tools, templates, references, VERSION) from {claude_dir}")
    _remove_registry()
    tracker.add("Claude Code", "uninstall", "-", str(claude_dir), "OK", "removed")
    return True


# ---------------------------------------------------------------------------
# Cursor — Plugin mode
# ---------------------------------------------------------------------------

def install_cursor_plugin(env):
    """Install GSE-One as a Cursor plugin by copying to ~/.cursor/plugins/."""
    step("Cursor — Machine install (~/.cursor/plugins)")

    if not _check_duplicate_install("cursor", "machine", env=env):
        tracker.add("Cursor", "machine", "global", "-", "FAIL", "cancelled (duplicate)")
        return False

    plugins_dir = env["cursor_dir"] / "plugins" / "local"
    ensure_dir(plugins_dir)

    dst = plugins_dir / "gse-one"
    if dst.exists() or dst.is_symlink():
        info(f"Removing previous installation at {dst}")
        remove_path(dst)

    copy_tree(PLUGIN_DIR, dst)
    # Cursor loads the orchestrator via rules/gse-orchestrator.mdc (always-on).
    # Remove it from agents/ to avoid double-loading the same content.
    orch_agent = dst / "agents" / "gse-orchestrator.md"
    if orch_agent.exists():
        orch_agent.unlink()
    ok(f"Plugin copied to {dst} (orchestrator via rules/, 10 specialized agents)")

    _write_registry(dst)

    # Verify
    is_ok, detail = verify_plugin(dst, "cursor")
    if is_ok:
        ok(f"Verified: {detail}")
        tracker.add("Cursor", "machine", "global", str(dst), "OK", detail)
    else:
        warn(f"Verification issue: {detail}")
        tracker.add("Cursor", "machine", "global", str(dst), "WARN", detail)

    return True


def uninstall_cursor_plugin(env):
    """Remove GSE-One from Cursor plugins."""
    step("Cursor — Machine uninstall")

    dst = env["cursor_dir"] / "plugins" / "local" / "gse-one"
    if dst.exists() or dst.is_symlink():
        remove_path(dst)
        ok(f"Removed {dst}")
        _remove_registry()
        tracker.add("Cursor", "uninstall", "global", str(dst), "OK", "removed")
    else:
        info("No Cursor plugin installation found.")
        tracker.add("Cursor", "uninstall", "global", str(dst), "WARN", "not found")
    return True


# ---------------------------------------------------------------------------
# Cursor — Non-plugin mode
# ---------------------------------------------------------------------------

def install_cursor_no_plugin(project_dir):
    """Install GSE-One artifacts directly into .cursor/ of a project."""
    step("Cursor — Project install")

    if not _check_duplicate_install("cursor", "project", project_dir=project_dir, env=detect_environment()):
        tracker.add("Cursor", "project", "project", str(project_dir), "FAIL", "cancelled (duplicate)")
        return False

    cursor_dir = Path(project_dir) / ".cursor"
    ensure_dir(cursor_dir)

    # Commands (Cursor uses commands/ for step-by-step activities)
    commands_dst = cursor_dir / "commands"
    ensure_dir(commands_dst)
    commands_src = PLUGIN_DIR / "commands"
    count = 0
    for cmd_file in sorted(commands_src.glob("*.md")):
        shutil.copy2(cmd_file, commands_dst / cmd_file.name)
        count += 1
    ok(f"Copied {count} commands to {commands_dst}")
    info("Commands will be /gse-name (e.g., /gse-go, /gse-plan)")

    # Agents (specialized only — orchestrator is delivered via rules/gse-orchestrator.mdc)
    agents_dst = cursor_dir / "agents"
    ensure_dir(agents_dst)
    agents_src = PLUGIN_DIR / "agents"
    agent_count = 0
    for agent_file in sorted(agents_src.glob("*.md")):
        if agent_file.name == "gse-orchestrator.md":
            continue  # Cursor loads the orchestrator via rules/, not agents/
        shutil.copy2(agent_file, agents_dst / agent_file.name)
        agent_count += 1
    ok(f"Copied {agent_count} specialized agents to {agents_dst}")

    # Rules (.mdc)
    rules_dst = cursor_dir / "rules"
    ensure_dir(rules_dst)
    rules_src = PLUGIN_DIR / "rules"
    for rule_file in sorted(rules_src.glob("*.mdc")):
        shutil.copy2(rule_file, rules_dst / rule_file.name)
    ok(f"Copied rule(s) to {rules_dst}")

    # Common runtime assets (tools/, templates/, references/, VERSION)
    _copy_common_assets(cursor_dir)
    ok(f"Copied common assets (tools, templates, references, VERSION) to {cursor_dir}")

    # Hooks
    hooks_src = PLUGIN_DIR / "hooks" / "hooks.cursor.json"
    hooks_dst = cursor_dir / "hooks.json"
    if hooks_src.exists():
        shutil.copy2(hooks_src, hooks_dst)
        ok(f"Copied hooks to {hooks_dst}")

    # Registry points to the local install dir — self-contained, gensem source
    # repo can be deleted after install and nothing breaks.
    _write_registry(cursor_dir)

    # Verify
    is_ok, detail = verify_no_plugin(project_dir, "cursor")
    if is_ok:
        tracker.add("Cursor", "project", "project", str(cursor_dir), "OK", detail)
    else:
        tracker.add("Cursor", "project", "project", str(cursor_dir), "WARN", detail)

    return True


def uninstall_cursor_no_plugin(project_dir):
    """Remove GSE-One artifacts from .cursor/."""
    step("Cursor — Project uninstall")

    cursor_dir = Path(project_dir) / ".cursor"

    for subdir in ("commands", "agents"):
        d = cursor_dir / subdir
        if d.exists():
            shutil.rmtree(d)
            ok(f"Removed {d}")

    # Symmetric removal of common runtime assets (tools, templates, references, VERSION)
    _remove_common_assets(cursor_dir)
    ok(f"Removed common assets (tools, templates, references, VERSION) from {cursor_dir}")

    rules_dir = cursor_dir / "rules"
    if rules_dir.exists():
        for f in rules_dir.glob("*gse*"):
            f.unlink()
            ok(f"Removed {f}")

    hooks_file = cursor_dir / "hooks.json"
    if hooks_file.exists():
        hooks_file.unlink()
        ok(f"Removed {hooks_file}")

    _remove_registry()
    tracker.add("Cursor", "uninstall", "project", str(cursor_dir), "OK", "removed")
    return True


# ---------------------------------------------------------------------------
# opencode — Plugin mode (global, ~/.config/opencode/)
# ---------------------------------------------------------------------------

def install_opencode_plugin(env):
    """Install GSE-One into the opencode global config dir (~/.config/opencode/).

    Copies .opencode subtree content (skills, commands, agents, plugins), merges
    AGENTS.md, and deep-merges opencode.json. Produces /gse-<name> slash commands.
    """
    step("opencode — Machine install (~/.config/opencode)")

    if not OPENCODE_PLUGIN_DIR.is_dir():
        err(f"opencode artefacts not found at {OPENCODE_PLUGIN_DIR}")
        err("Run: cd gse-one && python3 gse_generate.py --verify")
        tracker.add("opencode", "machine", "global", "-", "FAIL", "artefacts missing")
        return False

    if not _check_duplicate_install("opencode", "machine"):
        tracker.add("opencode", "machine", "global", "-", "FAIL", "cancelled (duplicate)")
        return False

    target = env["opencode_dir"]

    counts = _opencode_copy_tree(OPENCODE_PLUGIN_DIR, target)
    if counts is None:
        tracker.add("opencode", "machine", "global", str(target), "FAIL", "guardrail selection failed")
        return False
    # Common runtime assets (tools/, templates/, references/, VERSION) —
    # needed because opencode skills shell out to $(cat ~/.gse-one)/tools/...
    # and templates/references are consulted by activities at runtime.
    _copy_common_assets(target)
    ok(f"Copied common assets (tools, templates, references, VERSION) to {target}")
    _merge_agents_md(target / "AGENTS.md", OPENCODE_PLUGIN_DIR / "AGENTS.md")
    _merge_opencode_json(target / "opencode.json", OPENCODE_PLUGIN_DIR / "opencode.json")

    # Registry points to the opencode install dir — self-contained, gensem source
    # repo can be deleted after install and nothing breaks.
    _write_registry(target)

    detail = (f"{counts['skills']} skills, {counts['commands']} commands, "
              f"{counts['agents']} agents, plugin+AGENTS.md")
    ok(f"opencode plugin installed at {target}")
    info("Commands available as /gse-<name> (e.g., /gse-go, /gse-plan)")
    tracker.add("opencode", "machine", "global", str(target), "OK", detail)
    return True


def uninstall_opencode_plugin(env):
    """Remove GSE-One artefacts from the opencode global config dir."""
    step("opencode — Machine uninstall")

    target = env["opencode_dir"]
    if not target.is_dir():
        info("opencode global config dir not present — nothing to uninstall.")
        tracker.add("opencode", "uninstall", "global", str(target), "WARN", "not found")
        return True

    removed = _opencode_remove_content(target)
    # Symmetric removal of common runtime assets (tools, templates, references, VERSION)
    _remove_common_assets(target)
    _strip_agents_md_block(target / "AGENTS.md")
    _strip_opencode_json_marker(target / "opencode.json")

    _remove_registry()
    ok(f"Removed {removed} GSE-One file(s) from {target}")
    tracker.add("opencode", "uninstall", "global", str(target), "OK", f"{removed} files")
    return True


# ---------------------------------------------------------------------------
# opencode — Non-plugin mode (project, .opencode/)
# ---------------------------------------------------------------------------

def install_opencode_no_plugin(project_dir):
    """Install GSE-One into a project's .opencode/ directory + root AGENTS.md."""
    step("opencode — Project install")

    if not OPENCODE_PLUGIN_DIR.is_dir():
        err(f"opencode artefacts not found at {OPENCODE_PLUGIN_DIR}")
        err("Run: cd gse-one && python3 gse_generate.py --verify")
        tracker.add("opencode", "project", "project", str(project_dir), "FAIL", "artefacts missing")
        return False

    if not _check_duplicate_install("opencode", "project", project_dir=project_dir):
        tracker.add("opencode", "project", "project", str(project_dir), "FAIL", "cancelled (duplicate)")
        return False

    project_dir = Path(project_dir)
    target = project_dir / ".opencode"

    counts = _opencode_copy_tree(OPENCODE_PLUGIN_DIR, target)
    if counts is None:
        tracker.add("opencode", "project", "project", str(target), "FAIL", "guardrail selection failed")
        return False
    # Common runtime assets (tools/, templates/, references/, VERSION) —
    # needed because opencode skills shell out to $(cat ~/.gse-one)/tools/...
    # and templates/references are consulted by activities at runtime.
    _copy_common_assets(target)
    ok(f"Copied common assets (tools, templates, references, VERSION) to {target}")
    # AGENTS.md lives at the project root in project mode (opencode convention)
    _merge_agents_md(project_dir / "AGENTS.md", OPENCODE_PLUGIN_DIR / "AGENTS.md")
    # opencode.json also at project root
    _merge_opencode_json(project_dir / "opencode.json", OPENCODE_PLUGIN_DIR / "opencode.json")

    # Registry points to the .opencode install dir — self-contained, gensem source
    # repo can be deleted after install and nothing breaks.
    _write_registry(target)

    detail = (f"{counts['skills']} skills, {counts['commands']} commands, "
              f"{counts['agents']} agents, plugin+AGENTS.md")
    ok(f"opencode artefacts installed at {target}")
    info("AGENTS.md and opencode.json written at project root")
    info("Commands available as /gse-<name> (e.g., /gse-go, /gse-plan)")
    tracker.add("opencode", "project", "project", str(target), "OK", detail)
    return True


def uninstall_opencode_no_plugin(project_dir):
    """Remove GSE-One artefacts from a project's .opencode/ + root AGENTS.md."""
    step("opencode — Project uninstall")

    project_dir = Path(project_dir)
    target = project_dir / ".opencode"
    if not target.is_dir():
        info("No .opencode/ directory in project — nothing to uninstall.")
        tracker.add("opencode", "uninstall", "project", str(target), "WARN", "not found")
        return True

    removed = _opencode_remove_content(target)
    # Symmetric removal of common runtime assets (tools, templates, references, VERSION)
    _remove_common_assets(target)
    _strip_agents_md_block(project_dir / "AGENTS.md")
    _strip_opencode_json_marker(project_dir / "opencode.json")

    _remove_registry()
    ok(f"Removed {removed} GSE-One file(s) from {target}")
    tracker.add("opencode", "uninstall", "project", str(target), "OK", f"{removed} files")
    return True


# ---------------------------------------------------------------------------
# opencode — helpers
# ---------------------------------------------------------------------------

def _opencode_guardrails_source(src):
    """Select one loader-compatible adapter; absent CLI preserves V1 installs."""
    legacy = src / "plugins" / "gse-guardrails.ts"
    try:
        result = subprocess.run(
            ["opencode", "--version"], capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        warn("Cannot detect OpenCode version; installing V1 guardrails. Reinstall after upgrading to OpenCode 2.")
        return legacy
    match = re.fullmatch(r"(?:opencode\s+)?v?(\d+)\.\d+\.\d+(?:[-+][\w.-]+)?", result.stdout.strip())
    if result.returncode != 0 or not match:
        warn("Unrecognized OpenCode version; installing V1 guardrails. Reinstall after upgrading to OpenCode 2.")
        return legacy
    major = int(match.group(1))
    if major == 2:
        info("Selecting OpenCode 2 guardrails")
        return src / "compat" / "gse-guardrails-v2.ts"
    if major > 2:
        err(f"Unsupported OpenCode major version: {major}; no files installed")
        return None
    return legacy


def _opencode_copy_tree(src, target):
    """Copy opencode artefacts (skills/, commands/, agents/, plugins/) into target.

    Overwrites existing GSE-named items. Returns counts, or None on adapter selection failure.
    """
    guardrails = _opencode_guardrails_source(src)
    if guardrails is None:
        return None
    if not guardrails.is_file():
        err(f"Missing OpenCode guardrails: {guardrails}; regenerate before installing")
        return None
    counts = {"skills": 0, "commands": 0, "agents": 0, "plugins": 0}
    # Skills (copy each subdir individually so we don't wipe user-added skills)
    src_skills = src / "skills"
    dst_skills = target / "skills"
    ensure_dir(dst_skills)
    for skill_dir in sorted(src_skills.iterdir()):
        if skill_dir.is_dir():
            copy_tree(skill_dir, dst_skills / skill_dir.name)
            counts["skills"] += 1
    # Commands (only overwrite gse-*)
    src_cmd = src / "commands"
    dst_cmd = target / "commands"
    ensure_dir(dst_cmd)
    for cmd in sorted(src_cmd.glob("gse-*.md")):
        shutil.copy2(cmd, dst_cmd / cmd.name)
        counts["commands"] += 1
    # Agents
    src_ag = src / "agents"
    dst_ag = target / "agents"
    ensure_dir(dst_ag)
    for ag in sorted(src_ag.glob("*.md")):
        shutil.copy2(ag, dst_ag / ag.name)
        counts["agents"] += 1
    # Plugins (TS guardrails)
    src_pl = src / "plugins"
    dst_pl = target / "plugins"
    ensure_dir(dst_pl)
    for pl in sorted(src_pl.glob("*.ts")):
        shutil.copy2(guardrails if pl.name == "gse-guardrails.ts" else pl, dst_pl / pl.name)
        counts["plugins"] += 1
    return counts


def _opencode_remove_content(target):
    """Remove GSE-One-owned files from an opencode target dir."""
    removed = 0

    # Skills — remove any skill dir whose name matches a known GSE skill
    skills_dir = target / "skills"
    if skills_dir.is_dir():
        for name in _get_skill_names():
            d = skills_dir / name
            if d.is_dir():
                shutil.rmtree(d)
                removed += 1
        # Clean up empty skills/ dir
        if not any(skills_dir.iterdir()):
            skills_dir.rmdir()

    # Commands — remove only gse-*.md
    cmd_dir = target / "commands"
    if cmd_dir.is_dir():
        for cmd in cmd_dir.glob("gse-*.md"):
            cmd.unlink()
            removed += 1
        if not any(cmd_dir.iterdir()):
            cmd_dir.rmdir()

    # Agents — remove only the ones GSE ships
    ag_dir = target / "agents"
    if ag_dir.is_dir():
        for ag_file in (OPENCODE_PLUGIN_DIR / "agents").glob("*.md"):
            target_file = ag_dir / ag_file.name
            if target_file.exists():
                target_file.unlink()
                removed += 1
        if not any(ag_dir.iterdir()):
            ag_dir.rmdir()

    # Plugins — remove only our gse-guardrails.ts
    pl_dir = target / "plugins"
    if pl_dir.is_dir():
        ts = pl_dir / "gse-guardrails.ts"
        if ts.exists():
            ts.unlink()
            removed += 1
        if not any(pl_dir.iterdir()):
            pl_dir.rmdir()

    return removed


def _merge_agents_md(target_file, source_file):
    """Write or surgically merge the GSE-One block into an AGENTS.md file.

    - If target missing → write source as-is.
    - If target has markers → replace block between markers.
    - If target present without markers → append block, warn.
    """
    if not source_file.exists():
        return
    block = source_file.read_text(encoding="utf-8").rstrip() + "\n"

    if not target_file.exists():
        target_file.write_text(block, encoding="utf-8")
        ok(f"Wrote {target_file}")
        return

    current = target_file.read_text(encoding="utf-8")
    if AGENTS_MD_START in current and AGENTS_MD_END in current:
        before, _, rest = current.partition(AGENTS_MD_START)
        _, _, after = rest.partition(AGENTS_MD_END)
        merged = before.rstrip() + "\n\n" + block.rstrip() + "\n" + after.lstrip("\n")
        target_file.write_text(merged, encoding="utf-8")
        ok(f"Replaced GSE-One block in {target_file}")
    else:
        merged = current.rstrip() + "\n\n" + block
        target_file.write_text(merged, encoding="utf-8")
        warn(f"Appended GSE-One block to existing {target_file} (no prior markers)")


def _strip_agents_md_block(target_file):
    """Remove the GSE-One block from AGENTS.md. Deletes file if it becomes empty."""
    if not target_file.exists():
        return
    current = target_file.read_text(encoding="utf-8")
    if AGENTS_MD_START not in current or AGENTS_MD_END not in current:
        return
    before, _, rest = current.partition(AGENTS_MD_START)
    _, _, after = rest.partition(AGENTS_MD_END)
    merged = (before.rstrip() + "\n" + after.lstrip("\n")).strip()
    if merged:
        target_file.write_text(merged + "\n", encoding="utf-8")
        ok(f"Stripped GSE-One block from {target_file}")
    else:
        target_file.unlink()
        ok(f"Removed empty {target_file}")


def _merge_opencode_json(target_file, source_file):
    """Deep-merge GSE-One defaults into an existing opencode.json.

    Never overwrites user-set keys. Adds missing keys only.

    Also removes any root-level `gse` key: opencode >= 1.17 fatally rejects
    unknown root keys ("Unrecognized key: gse"), so installs <= 0.85.x that
    wrote the marker left opencode unable to start — reinstalling repairs
    them. GSE metadata now lives in the registry-target `gse.json`.
    """
    if not source_file.exists():
        return
    source = json.loads(source_file.read_text())

    if target_file.exists():
        try:
            target = json.loads(target_file.read_text())
        except (json.JSONDecodeError, OSError):
            warn(f"Could not parse existing {target_file}; leaving it untouched.")
            return
    else:
        target = {}

    merged = _deep_merge(target, source)
    if merged.pop("gse", None) is not None:
        ok(f"Removed legacy root 'gse' key from {target_file} (fatal on opencode >= 1.17)")
    target_file.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    ok(f"Merged GSE-One defaults into {target_file}")


def _deep_merge(base, overlay):
    """Merge overlay into base without overwriting existing base values.

    - Existing keys in base are preserved.
    - Missing keys from overlay are added.
    - Nested dicts are merged recursively under the same rule.
    """
    result = dict(base)
    for k, v in overlay.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        elif k not in result:
            result[k] = v
    return result


def _strip_opencode_json_marker(target_file):
    """Remove the legacy GSE-One `gse` marker (written by installs <= 0.85.x)
    from opencode.json; drop the file if empty."""
    if not target_file.exists():
        return
    try:
        data = json.loads(target_file.read_text())
    except (json.JSONDecodeError, OSError):
        return
    if "gse" in data:
        del data["gse"]
    # Remove our specific bash denies only if they match exactly
    perms = data.get("permission", {}).get("bash", {})
    for key in ("git push --force *", "rm -rf /*"):
        if perms.get(key) == "deny":
            del perms[key]
    if perms == {}:
        data.get("permission", {}).pop("bash", None)
    if data.get("permission", {}).get("skill") == {"*": "allow"}:
        data["permission"].pop("skill", None)
    if data.get("permission", {}).get("question") == "allow":
        data["permission"].pop("question", None)
    if data.get("permission") == {}:
        del data["permission"]
    # If only the schema remains → delete the file
    remaining_keys = [k for k in data.keys() if k != "$schema"]
    if not remaining_keys:
        target_file.unlink()
        ok(f"Removed {target_file} (only GSE-One content)")
    else:
        target_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        ok(f"Stripped GSE-One content from {target_file}")


# ---------------------------------------------------------------------------
# Codex CLI — shared component helpers
# ---------------------------------------------------------------------------

def _codex_copy_skills(skills_target):
    """Copy all Codex skills (24 activities + full orchestrator) into
    skills_target/<name>/SKILL.md. Returns count."""
    src = CODEX_PLUGIN_DIR / "skills"
    ensure_dir(skills_target)
    count = 0
    for d in sorted(src.iterdir()):
        if d.is_dir() and (d / "SKILL.md").exists():
            copy_tree(d, Path(skills_target) / d.name)
            count += 1
    return count


def _codex_copy_agents(agents_target):
    """Copy the 10 specialized sub-agent TOML files into agents_target/. Returns count."""
    src = CODEX_PLUGIN_DIR / "agents"
    ensure_dir(agents_target)
    count = 0
    for f in sorted(src.glob("*.toml")):
        shutil.copy2(f, Path(agents_target) / f.name)
        count += 1
    return count


def _codex_copy_hooks(codex_dir):
    """Copy codex hooks.json to the FLAT discovery path <codex_dir>/hooks.json.

    Standalone (non-plugin) Codex hook discovery only reads ~/.codex/hooks.json,
    <repo>/.codex/hooks.json and the config.toml entries — the hooks/hooks.json
    sub-directory form is honored only inside a real Codex plugin, so installs
    that used it shipped dead files (guardrails silently inert). Refuses to
    overwrite a pre-existing non-GSE hooks.json; removes the legacy sub-directory
    form left by installs <= 0.85.x.
    """
    src = CODEX_PLUGIN_DIR / "hooks" / "hooks.json"
    codex_dir = Path(codex_dir)
    ensure_dir(codex_dir)
    dst = codex_dir / "hooks.json"
    if dst.exists():
        try:
            existing = dst.read_text(encoding="utf-8")
        except OSError:
            existing = ""
        if "GUARDRAIL" not in existing:
            warn(f"{dst} already exists and is not GSE-managed — left untouched.")
            warn(f"  Merge the GSE hooks manually from {src} if you want the guardrails.")
            return
    shutil.copy2(src, dst)
    ok(f"Copied hooks to {dst}")
    legacy = codex_dir / "hooks"
    if (legacy / "hooks.json").exists():
        remove_path(legacy)
        ok(f"Removed legacy {legacy}/ (not a Codex discovery path)")


def _codex_print_trust_notice():
    """Post-install notice: since Codex 0.129, command hooks only run after the
    user approves them in the /hooks TUI — without that approval the installed
    guardrails do not execute (headless `codex exec` included)."""
    info("Codex hook trust: launch `codex`, open /hooks, and approve the")
    info("  GSE-One hooks — unapproved hooks do NOT run (guardrails inert).")
    info("  For headless automation only, `--dangerously-bypass-hook-trust`")
    info("  exists; GSE does not set it for you (it defeats the trust model).")


def _codex_enable_hooks_flag(config_toml_path):
    """Ensure `hooks = true` under `[features]` in a Codex config.toml.

    Hooks are enabled BY DEFAULT on current Codex versions — this flag is a
    safety belt for older versions and for users who explicitly set
    `hooks = false`, not the cause of guardrail inertia (the real activation
    requirements are the flat hooks.json discovery path and the /hooks trust
    approval). The old top-level `codex_hooks = true` is a deprecated alias
    (removed here if present to avoid ambiguity). Minimal stdlib TOML edit,
    section-aware: preserves the rest of the file, comments, and sections."""
    import re
    config_toml_path = Path(config_toml_path)
    ensure_dir(config_toml_path.parent)
    text = config_toml_path.read_text(encoding="utf-8") if config_toml_path.exists() else ""

    # Drop the deprecated top-level alias if present.
    text = re.sub(r'(?m)^[ \t]*codex_hooks[ \t]*=.*\n?', '', text)

    lines = text.splitlines()
    out, in_features, features_seen, hooks_set = [], False, False, False
    for line in lines:
        if re.match(r'^\s*\[', line):                      # a section header
            if in_features and not hooks_set:              # leaving [features] w/o hooks
                out.append("hooks = true")
                hooks_set = True
            in_features = line.strip() == "[features]"
            features_seen = features_seen or in_features
            out.append(line)
            continue
        if in_features and re.match(r'^\s*hooks\s*=', line):
            out.append("hooks = true")                     # flip existing key
            hooks_set = True
            continue
        out.append(line)
    if in_features and not hooks_set:                      # [features] was the last section
        out.append("hooks = true")
        hooks_set = True
    if not features_seen:                                  # no [features] at all → append one
        if out and out[-1].strip() != "":
            out.append("")
        out += ["[features]", "hooks = true"]
    result = "\n".join(out)
    if not result.endswith("\n"):
        result += "\n"
    config_toml_path.write_text(result, encoding="utf-8")
    ok(f"Enabled [features] hooks = true in {config_toml_path}")


def _codex_remove_components(skills_target, agents_target, codex_dir_for_hooks):
    """Remove GSE-One Codex artefacts from the given target dirs. Returns count."""
    removed = 0
    skills_target = Path(skills_target)
    known = [f"gse-{n}" for n in _get_skill_names()] + ["gse-orchestrator"]
    if skills_target.is_dir():
        for name in known:
            d = skills_target / name
            if d.is_dir():
                shutil.rmtree(d)
                removed += 1
    agents_target = Path(agents_target)
    if agents_target.is_dir():
        for f in (CODEX_PLUGIN_DIR / "agents").glob("*.toml"):
            t = agents_target / f.name
            if t.exists():
                t.unlink()
                removed += 1
    # Flat discovery path (current) + legacy hooks/ sub-directory (<= 0.85.x)
    codex_dir = Path(codex_dir_for_hooks)
    for hooks_json in (codex_dir / "hooks.json", codex_dir / "hooks" / "hooks.json"):
        if hooks_json.exists():
            hooks_json.unlink()
            removed += 1
    legacy_dir = codex_dir / "hooks"
    if legacy_dir.is_dir() and not any(legacy_dir.iterdir()):
        legacy_dir.rmdir()
    return removed


def verify_codex(skills_target, agents_md_path):
    """Post-install check. Returns (ok, detail)."""
    skills_target = Path(skills_target)
    n = sum(1 for d in skills_target.iterdir() if d.is_dir() and (d / "SKILL.md").exists()) \
        if skills_target.is_dir() else 0
    if n == 0:
        return False, "no skills copied"
    if not Path(agents_md_path).exists():
        return False, "AGENTS.md missing"
    return True, f"{n} skills, AGENTS.md present"


# ---------------------------------------------------------------------------
# Codex CLI — Plugin mode (global)
# ---------------------------------------------------------------------------

def install_codex_plugin(env):
    """Install GSE-One into Codex global locations (~/.codex/, ~/.agents/skills/).

    Skills → ~/.agents/skills/, sub-agents → ~/.codex/agents/, condensed
    orchestrator → ~/.codex/AGENTS.md, hooks → ~/.codex/hooks/hooks.json with
    `[features] hooks = true` set in ~/.codex/config.toml. Registry → side-install
    ~/.gse-one.d/ (Codex's plugin cache path is not stable for shell
    resolution — same rationale as the Claude plugin side-install)."""
    step("Codex CLI — Machine install (~/.codex)")

    if not CODEX_PLUGIN_DIR.is_dir():
        err(f"Codex artefacts not found at {CODEX_PLUGIN_DIR}")
        err("Run: cd gse-one && python3 gse_generate.py --verify")
        tracker.add("Codex", "machine", "global", "-", "FAIL", "artefacts missing")
        return False

    if not _check_duplicate_install("codex", "machine"):
        tracker.add("Codex", "machine", "global", "-", "FAIL", "cancelled (duplicate)")
        return False

    n_skills = _codex_copy_skills(CODEX_SKILLS_HOME)
    n_agents = _codex_copy_agents(CODEX_GLOBAL_DIR / "agents")
    _merge_agents_md(CODEX_GLOBAL_DIR / "AGENTS.md", CODEX_PLUGIN_DIR / "AGENTS.md")
    _codex_copy_hooks(CODEX_GLOBAL_DIR)
    _codex_enable_hooks_flag(CODEX_GLOBAL_DIR / "config.toml")
    _codex_print_trust_notice()

    # Common runtime assets at the side-install location (stable shell path).
    _copy_common_assets(GSE_ONE_DATA_DIR)
    ok(f"Common assets copied to {GSE_ONE_DATA_DIR}")
    _write_registry(GSE_ONE_DATA_DIR)

    is_ok, detail = verify_codex(CODEX_SKILLS_HOME, CODEX_GLOBAL_DIR / "AGENTS.md")
    status = "OK" if is_ok else "WARN"
    ok(f"Codex installed — {n_skills} skills, {n_agents} agents")
    info("Skills load contextually; full methodology in ~/.codex/AGENTS.md (load `gse-orchestrator` skill for the complete text)")
    tracker.add("Codex", "machine", "global", str(CODEX_GLOBAL_DIR), status,
                f"{n_skills} skills, {n_agents} agents")
    return True


def uninstall_codex_plugin(env):
    """Remove GSE-One Codex artefacts from global locations."""
    step("Codex CLI — Machine uninstall")
    removed = _codex_remove_components(CODEX_SKILLS_HOME, CODEX_GLOBAL_DIR / "agents",
                                       CODEX_GLOBAL_DIR)
    _strip_agents_md_block(CODEX_GLOBAL_DIR / "AGENTS.md")
    _remove_common_assets(GSE_ONE_DATA_DIR)
    if GSE_ONE_DATA_DIR.exists() and not any(GSE_ONE_DATA_DIR.iterdir()):
        GSE_ONE_DATA_DIR.rmdir()
    _remove_registry()
    info("Left `[features] hooks` flag in ~/.codex/config.toml untouched (remove manually if desired)")
    ok(f"Removed {removed} GSE-One file(s) from Codex global locations")
    tracker.add("Codex", "uninstall", "global", str(CODEX_GLOBAL_DIR), "OK", f"{removed} files")
    return True


# ---------------------------------------------------------------------------
# Codex CLI — Non-plugin mode (project)
# ---------------------------------------------------------------------------

def install_codex_no_plugin(project_dir):
    """Install GSE-One Codex artefacts into a project.

    Skills → <project>/.agents/skills/, sub-agents → <project>/.codex/agents/,
    condensed orchestrator → <project>/AGENTS.md (root), hooks →
    <project>/.codex/hooks/hooks.json with `[features] hooks = true` in
    <project>/.codex/config.toml. Registry → <project>/.codex/."""
    step("Codex CLI — Project install")

    if not CODEX_PLUGIN_DIR.is_dir():
        err(f"Codex artefacts not found at {CODEX_PLUGIN_DIR}")
        err("Run: cd gse-one && python3 gse_generate.py --verify")
        tracker.add("Codex", "project", "project", str(project_dir), "FAIL", "artefacts missing")
        return False

    if not _check_duplicate_install("codex", "project", project_dir=project_dir):
        tracker.add("Codex", "project", "project", str(project_dir), "FAIL", "cancelled (duplicate)")
        return False

    project_dir = Path(project_dir)
    codex_dir = project_dir / ".codex"
    n_skills = _codex_copy_skills(project_dir / ".agents" / "skills")
    n_agents = _codex_copy_agents(codex_dir / "agents")
    _merge_agents_md(project_dir / "AGENTS.md", CODEX_PLUGIN_DIR / "AGENTS.md")
    _codex_copy_hooks(codex_dir)
    _codex_enable_hooks_flag(codex_dir / "config.toml")
    _codex_print_trust_notice()

    _copy_common_assets(codex_dir)
    ok(f"Copied common assets (tools, templates, references, VERSION) to {codex_dir}")
    _write_registry(codex_dir)

    is_ok, detail = verify_codex(project_dir / ".agents" / "skills", project_dir / "AGENTS.md")
    status = "OK" if is_ok else "WARN"
    ok(f"Codex artefacts installed — {n_skills} skills, {n_agents} agents")
    info("AGENTS.md written at project root; skills under .agents/skills/")
    tracker.add("Codex", "project", "project", str(codex_dir), status,
                f"{n_skills} skills, {n_agents} agents")
    return True


def uninstall_codex_no_plugin(project_dir):
    """Remove GSE-One Codex artefacts from a project."""
    step("Codex CLI — Project uninstall")
    project_dir = Path(project_dir)
    codex_dir = project_dir / ".codex"
    removed = _codex_remove_components(project_dir / ".agents" / "skills",
                                       codex_dir / "agents", codex_dir)
    _strip_agents_md_block(project_dir / "AGENTS.md")
    _remove_common_assets(codex_dir)
    _remove_registry()
    info("Left `[features] hooks` flag in .codex/config.toml untouched (remove manually if desired)")
    ok(f"Removed {removed} GSE-One file(s) from {codex_dir}")
    tracker.add("Codex", "uninstall", "project", str(codex_dir), "OK", f"{removed} files")
    return True


# ---------------------------------------------------------------------------
# Gemini CLI — shared component helpers
# ---------------------------------------------------------------------------

def _gemini_copy_commands(commands_target):
    """Copy commands/gse/*.toml into commands_target/gse/. Returns count."""
    src = GEMINI_PLUGIN_DIR / "commands" / "gse"
    dst = Path(commands_target) / "gse"
    ensure_dir(dst)
    count = 0
    for f in sorted(src.glob("*.toml")):
        shutil.copy2(f, dst / f.name)
        count += 1
    return count


def _gemini_copy_agents(agents_target):
    """Copy the 10 specialized agent .md files into agents_target/. Returns count."""
    src = GEMINI_PLUGIN_DIR / "agents"
    ensure_dir(agents_target)
    count = 0
    for f in sorted(src.glob("*.md")):
        shutil.copy2(f, Path(agents_target) / f.name)
        count += 1
    return count


def _gemini_hooks_is_gse(entry):
    """True if a settings.json hook entry is GSE-managed (its commands read
    .gse/ state — the stable marker of the shared guardrail one-liners)."""
    return ".gse" in json.dumps(entry)


def _gemini_merge_hooks_into_settings(settings_file):
    """Merge the GSE hook entries into <project>/.gemini/settings.json.

    Gemini CLI loads project-level hooks ONLY from the `hooks` object of
    .gemini/settings.json (a standalone .gemini/hooks/hooks.json is honored
    exclusively inside an extension directory — installs <= 0.85.x shipped a
    dead file there, guardrails silently inert). Preserves user keys and
    non-GSE hook entries; replaces previous GSE entries in place.
    """
    src = json.loads((GEMINI_PLUGIN_DIR / "hooks" / "hooks.json").read_text())
    settings_file = Path(settings_file)
    ensure_dir(settings_file.parent)
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except (json.JSONDecodeError, OSError):
            warn(f"Could not parse existing {settings_file}; leaving it untouched.")
            warn("  GSE hooks NOT installed — fix the file and re-run the installer.")
            return False
    else:
        settings = {}
    hooks = settings.setdefault("hooks", {})
    for event, entries in src.get("hooks", {}).items():
        kept = [e for e in hooks.get(event, []) if not _gemini_hooks_is_gse(e)]
        hooks[event] = kept + entries
    settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    ok(f"Merged GSE hooks into {settings_file}")
    return True


def _gemini_strip_hooks_from_settings(settings_file):
    """Remove GSE hook entries from .gemini/settings.json (keeps user content)."""
    settings_file = Path(settings_file)
    if not settings_file.exists():
        return 0
    try:
        settings = json.loads(settings_file.read_text())
    except (json.JSONDecodeError, OSError):
        return 0
    removed = 0
    hooks = settings.get("hooks", {})
    for event in list(hooks.keys()):
        kept = [e for e in hooks[event] if not _gemini_hooks_is_gse(e)]
        removed += len(hooks[event]) - len(kept)
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    if not hooks:
        settings.pop("hooks", None)
    if settings:
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    else:
        settings_file.unlink()
        ok(f"Removed {settings_file} (only GSE-One content)")
    return removed


def _gemini_remove_components(commands_target, agents_target, hooks_dir):
    """Remove GSE-One Gemini artefacts. Returns count."""
    removed = 0
    gse_cmd = Path(commands_target) / "gse"
    if gse_cmd.is_dir():
        for f in (GEMINI_PLUGIN_DIR / "commands" / "gse").glob("*.toml"):
            t = gse_cmd / f.name
            if t.exists():
                t.unlink()
                removed += 1
        if gse_cmd.is_dir() and not any(gse_cmd.iterdir()):
            gse_cmd.rmdir()
    agents_target = Path(agents_target)
    if agents_target.is_dir():
        for f in (GEMINI_PLUGIN_DIR / "agents").glob("*.md"):
            t = agents_target / f.name
            if t.exists():
                t.unlink()
                removed += 1
    hooks_json = Path(hooks_dir) / "hooks.json"
    if hooks_json.exists():
        hooks_json.unlink()
        removed += 1
    return removed


def verify_gemini(commands_target, context_md_path):
    """Post-install check. Returns (ok, detail)."""
    gse_cmd = Path(commands_target) / "gse"
    n = sum(1 for _ in gse_cmd.glob("*.toml")) if gse_cmd.is_dir() else 0
    if n == 0:
        return False, "no commands copied"
    if not Path(context_md_path).exists():
        return False, "GEMINI.md missing"
    return True, f"{n} commands, GEMINI.md present"


# ---------------------------------------------------------------------------
# Gemini CLI — Plugin mode (global extension)
# ---------------------------------------------------------------------------

def install_gemini_plugin(env):
    """Install GSE-One as a Gemini extension at ~/.gemini/extensions/gse-one/.

    Copies the self-contained plugin/gemini/ tree (commands, agents, GEMINI.md,
    hooks, gemini-extension.json) and the common runtime assets. Registry →
    the extension dir."""
    step("Gemini CLI — Machine install (~/.gemini/extensions)")

    if not GEMINI_PLUGIN_DIR.is_dir():
        err(f"Gemini artefacts not found at {GEMINI_PLUGIN_DIR}")
        err("Run: cd gse-one && python3 gse_generate.py --verify")
        tracker.add("Gemini", "machine", "global", "-", "FAIL", "artefacts missing")
        return False

    if not _check_duplicate_install("gemini", "machine"):
        tracker.add("Gemini", "machine", "global", "-", "FAIL", "cancelled (duplicate)")
        return False

    ensure_dir(GEMINI_EXT_DIR.parent)
    copy_tree(GEMINI_PLUGIN_DIR, GEMINI_EXT_DIR)
    _copy_common_assets(GEMINI_EXT_DIR)
    ok(f"Common assets copied to {GEMINI_EXT_DIR}")
    _write_registry(GEMINI_EXT_DIR)

    n_cmds = sum(1 for _ in (GEMINI_EXT_DIR / "commands" / "gse").glob("*.toml"))
    is_ok, detail = verify_gemini(GEMINI_EXT_DIR / "commands", GEMINI_EXT_DIR / "GEMINI.md")
    status = "OK" if is_ok else "WARN"
    ok(f"Gemini extension installed at {GEMINI_EXT_DIR}")
    info("Commands available as /gse:<name> (e.g., /gse:go, /gse:plan)")
    tracker.add("Gemini", "machine", "global", str(GEMINI_EXT_DIR), status, f"{n_cmds} commands")
    return True


def uninstall_gemini_plugin(env):
    """Remove the GSE-One Gemini extension."""
    step("Gemini CLI — Machine uninstall")
    if not GEMINI_EXT_DIR.is_dir():
        info("No GSE-One Gemini extension present — nothing to uninstall.")
        tracker.add("Gemini", "uninstall", "global", str(GEMINI_EXT_DIR), "WARN", "not found")
        return True
    remove_path(GEMINI_EXT_DIR)
    _remove_registry()
    ok(f"Removed Gemini extension {GEMINI_EXT_DIR}")
    tracker.add("Gemini", "uninstall", "global", str(GEMINI_EXT_DIR), "OK", "removed")
    return True


# ---------------------------------------------------------------------------
# Gemini CLI — Non-plugin mode (project)
# ---------------------------------------------------------------------------

def install_gemini_no_plugin(project_dir):
    """Install GSE-One Gemini artefacts into a project.

    Commands → <project>/.gemini/commands/gse/, agents →
    <project>/.gemini/agents/, hooks → merged into the `hooks` object of
    <project>/.gemini/settings.json (the ONLY project-level hook load path —
    a standalone .gemini/hooks/hooks.json is extension-only), context →
    <project>/GEMINI.md (root, surgical merge). Registry → <project>/.gemini/."""
    step("Gemini CLI — Project install")

    if not GEMINI_PLUGIN_DIR.is_dir():
        err(f"Gemini artefacts not found at {GEMINI_PLUGIN_DIR}")
        err("Run: cd gse-one && python3 gse_generate.py --verify")
        tracker.add("Gemini", "project", "project", str(project_dir), "FAIL", "artefacts missing")
        return False

    if not _check_duplicate_install("gemini", "project", project_dir=project_dir):
        tracker.add("Gemini", "project", "project", str(project_dir), "FAIL", "cancelled (duplicate)")
        return False

    project_dir = Path(project_dir)
    gemini_dir = project_dir / ".gemini"
    n_cmds = _gemini_copy_commands(gemini_dir / "commands")
    n_agents = _gemini_copy_agents(gemini_dir / "agents")
    _gemini_merge_hooks_into_settings(gemini_dir / "settings.json")
    # Clean up the dead standalone file shipped by installs <= 0.85.x
    legacy_hooks = gemini_dir / "hooks" / "hooks.json"
    if legacy_hooks.exists():
        legacy_hooks.unlink()
        if not any((gemini_dir / "hooks").iterdir()):
            (gemini_dir / "hooks").rmdir()
        ok(f"Removed legacy {legacy_hooks} (not a Gemini project-level load path)")
    # GEMINI.md at project root (Gemini's worktree context convention)
    _merge_agents_md(project_dir / "GEMINI.md", GEMINI_PLUGIN_DIR / "GEMINI.md")

    _copy_common_assets(gemini_dir)
    ok(f"Copied common assets (tools, templates, references, VERSION) to {gemini_dir}")
    _write_registry(gemini_dir)

    is_ok, detail = verify_gemini(gemini_dir / "commands", project_dir / "GEMINI.md")
    status = "OK" if is_ok else "WARN"
    ok(f"Gemini artefacts installed — {n_cmds} commands, {n_agents} agents")
    info("GEMINI.md written at project root")
    info("Commands available as /gse:<name> (e.g., /gse:go, /gse:plan)")
    tracker.add("Gemini", "project", "project", str(gemini_dir), status,
                f"{n_cmds} commands, {n_agents} agents")
    return True


def uninstall_gemini_no_plugin(project_dir):
    """Remove GSE-One Gemini artefacts from a project."""
    step("Gemini CLI — Project uninstall")
    project_dir = Path(project_dir)
    gemini_dir = project_dir / ".gemini"
    removed = _gemini_remove_components(gemini_dir / "commands", gemini_dir / "agents",
                                        gemini_dir / "hooks")
    removed += _gemini_strip_hooks_from_settings(gemini_dir / "settings.json")
    _strip_agents_md_block(project_dir / "GEMINI.md")
    _remove_common_assets(gemini_dir)
    _remove_registry()
    ok(f"Removed {removed} GSE-One file(s) from {gemini_dir}")
    tracker.add("Gemini", "uninstall", "project", str(gemini_dir), "OK", f"{removed} files")
    return True


# ---------------------------------------------------------------------------
# Sandbox mode — HOME-isolated install + project launcher (run over many days)
# ---------------------------------------------------------------------------

# Sandbox is supported for CLI agents whose "global" install is a plain
# file-copy that honors $HOME (so re-running the installer under HOME=<sandbox>
# lands everything inside the project). Claude (CLI/Keychain-mediated) and
# Cursor (GUI app) do not isolate cleanly via $HOME → use --mode project instead.
SANDBOX_PLATFORMS = {"codex", "gemini", "opencode"}


def _write_launcher(project_dir, platform_name, mode):
    """Drop the generic launcher (.gse-sandbox/run) + metadata
    (.gse-sandbox/launch.env) into a project. The launcher detects mode+platform
    at runtime and starts the agent with the right environment (sets HOME to
    .gse-sandbox/ for sandbox mode while running from the project root)."""
    gse = Path(project_dir).resolve() / ".gse-sandbox"
    ensure_dir(gse)
    (gse / "launch.env").write_text(f"platform={platform_name}\nmode={mode}\n", encoding="utf-8")
    src = PLUGIN_DIR / "gse-run"
    dst = gse / "run"
    if not src.exists():
        err(f"Launcher template not found at {src} — run: cd gse-one && python3 gse_generate.py")
        return False
    shutil.copy2(src, dst)
    try:
        dst.chmod(0o755)
    except OSError:
        pass
    ok(f"Launcher installed: {dst}")
    info("Start the agent any time with:  sh .gse-sandbox/run   (add .gse-sandbox/ to .gitignore)")
    return True


def install_sandbox(platform_name, project_dir):
    """Install GSE-One into a project-internal sandbox $HOME and drop the
    launcher. Re-executes the normal machine-mode install under HOME=<project>/
    .gse-sandbox, so nothing is written under the real $HOME. Idempotent on the
    launcher; re-run to refresh the install."""
    step(f"{platform_name} — Sandbox install (project-internal $HOME)")

    if platform_name not in SANDBOX_PLATFORMS:
        err(f"--mode sandbox is not supported for '{platform_name}'.")
        err("Use --mode project instead (Claude is CLI/Keychain-mediated; Cursor is a GUI app).")
        tracker.add(platform_name, "sandbox", "project", "-", "FAIL", "unsupported platform")
        return False

    if not PLUGIN_DIR.is_dir():
        err(f"Plugin not found at {PLUGIN_DIR}")
        tracker.add(platform_name, "sandbox", "project", "-", "FAIL", "plugin missing")
        return False

    project_dir = Path(project_dir).resolve()
    sandbox = project_dir / ".gse-sandbox"
    ensure_dir(sandbox)

    # Re-exec the installer with HOME pointed at the sandbox: the child sees
    # HOME=<sandbox>, so its plugin-mode install lands entirely inside it.
    env = os.environ.copy()
    env["HOME"] = str(sandbox)
    env.pop("XDG_CONFIG_HOME", None)     # otherwise opencode escapes the sandbox
    env.pop("OPENCODE_CONFIG_DIR", None) # opencode-specific config overrides —
    env.pop("OPENCODE_CONFIG", None)     # same escape vector as XDG
    env["GSE_CHILD"] = "1"             # silence the child's banner/summary
    info(f"Installing into project sandbox HOME: {sandbox}")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()),
         "--platform", platform_name, "--mode", "machine"],
        env=env,
    )
    if result.returncode != 0:
        err(f"Sandbox install failed (exit {result.returncode})")
        tracker.add(platform_name, "sandbox", "project", str(sandbox), "FAIL",
                    f"install exit {result.returncode}")
        return False

    _write_launcher(project_dir, platform_name, "sandbox")
    ok(f"{platform_name} installed in project sandbox — nothing under your real $HOME")
    tracker.add(platform_name, "sandbox", "project", str(sandbox), "OK",
                "HOME-isolated + .gse-sandbox/run launcher")
    return True


def uninstall_sandbox(platform_name, project_dir):
    """Remove the project sandbox + launcher."""
    step(f"{platform_name} — Sandbox uninstall (project)")
    project_dir = Path(project_dir).resolve()
    sandbox = project_dir / ".gse-sandbox"
    removed = 0
    if sandbox.is_dir():
        # .gse-sandbox/ holds the isolated $HOME *and* the launcher (run +
        # launch.env), so a single removal covers everything.
        remove_path(sandbox)
        removed += 1
    ok(f"Removed sandbox + launcher ({removed} item(s)) from {project_dir}")
    tracker.add(platform_name, "uninstall", "project", str(sandbox), "OK", f"{removed} items")
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_skill_names():
    """Return the list of skill directory names."""
    skills_src = PLUGIN_DIR / "skills"
    return [d.name for d in sorted(skills_src.iterdir()) if d.is_dir()]




# ---------------------------------------------------------------------------
# Interactive menu
# ---------------------------------------------------------------------------

def interactive_menu(env):
    """Run the interactive installation menu."""

    platform_choices = []
    if env["has_claude"]:
        platform_choices.append(("Claude Code", "claude"))
    if env["has_cursor"]:
        platform_choices.append(("Cursor", "cursor"))
    if env["has_opencode"]:
        platform_choices.append(("opencode", "opencode"))
    if env["has_codex"]:
        platform_choices.append(("Codex CLI", "codex"))
    if env["has_gemini"]:
        platform_choices.append(("Gemini CLI", "gemini"))
    if all(env[k] for k in ("has_claude", "has_cursor", "has_opencode", "has_codex", "has_gemini")):
        platform_choices.append(("All five (Claude + Cursor + opencode + Codex + Gemini)", "all"))
    elif env["has_claude"] and env["has_cursor"] and env["has_opencode"]:
        platform_choices.append(("All three (Claude Code + Cursor + opencode)", "all3"))
    elif env["has_claude"] and env["has_cursor"]:
        platform_choices.append(("Both (Claude Code + Cursor)", "both"))
    if not env["has_claude"]:
        platform_choices.append(("Claude Code (not detected — install anyway)", "claude"))
    if not env["has_cursor"]:
        platform_choices.append(("Cursor (not detected — install anyway)", "cursor"))
    if not env["has_opencode"]:
        platform_choices.append(("opencode (not detected — install anyway)", "opencode"))
    if not env["has_codex"]:
        platform_choices.append(("Codex CLI (not detected — install anyway)", "codex"))
    if not env["has_gemini"]:
        platform_choices.append(("Gemini CLI (not detected — install anyway)", "gemini"))

    chosen_platform = ask("Install for which platform?", platform_choices)

    if chosen_platform == "all":
        platforms = ["claude", "cursor", "opencode", "codex", "gemini"]
    elif chosen_platform == "all3":
        platforms = ["claude", "cursor", "opencode"]
    elif chosen_platform == "both":
        platforms = ["claude", "cursor"]
    else:
        platforms = [chosen_platform]
    results = []

    # One mode question per platform, phrased by need. 'project' = everything
    # in the project folder (registry at <project>/.gse/registry, nothing
    # under $HOME); 'machine' = one install for the whole machine, under $HOME;
    # 'sandbox' = project-internal $HOME (codex/gemini/opencode only).
    def _mode_choices(plat_key, project_target, machine_target, sandbox_ok):
        choices = [
            (f"Everything in this project — {project_target}, nothing under ~ (recommended)", "project"),
            (f"Whole machine — {machine_target}", "machine"),
        ]
        if sandbox_ok:
            choices.append(("Sandbox — isolated $HOME in .gse-sandbox/ + .gse-sandbox/run launcher", "sandbox"))
        return choices

    PLATFORM_MENU = {
        "claude": (".claude/ + .claude/skills/gse plugin", "~/.claude/skills/gse + ~/.gse-one.d", False),
        "cursor": (".cursor/", "~/.cursor/plugins/local/gse-one", False),
        "opencode": (".opencode/", "~/.config/opencode", True),
        "codex": (".codex/ + .agents/skills/", "~/.codex + ~/.agents/skills + ~/.gse-one.d", True),
        "gemini": (".gemini/", "~/.gemini/extensions/gse-one", True),
    }
    PROJECT_INSTALLERS = {
        "claude": install_claude_project,
        "cursor": install_cursor_no_plugin,
        "opencode": install_opencode_no_plugin,
        "codex": install_codex_no_plugin,
        "gemini": install_gemini_no_plugin,
    }

    for plat in platforms:
        proj_target, mach_target, sandbox_ok = PLATFORM_MENU[plat]
        mode = ask(f"Installation mode for {plat}?",
                   _mode_choices(plat, proj_target, mach_target, sandbox_ok))
        if mode == "sandbox":
            results.append(install_sandbox(plat, _ask_project_dir()))
        elif mode == "project":
            project_dir = _ask_project_dir()
            _maybe_local(mode, project_dir)
            results.append(PROJECT_INSTALLERS[plat](project_dir))
        else:
            _maybe_local(mode, None)
            if plat == "claude":
                results.append(install_claude_machine())
            elif plat == "cursor":
                results.append(install_cursor_plugin(env))
            elif plat == "opencode":
                results.append(install_opencode_plugin(env))
            elif plat == "codex":
                results.append(install_codex_plugin(env))
            elif plat == "gemini":
                results.append(install_gemini_plugin(env))

    return all(results)


def interactive_uninstall(env):
    """Run the interactive uninstall menu."""
    chosen = ask(
        "Uninstall from which platform?",
        [
            ("Claude Code — project install (current project)", "claude-project"),
            ("Claude Code — machine install", "claude-machine"),
            ("Cursor — project install (current project)", "cursor-project"),
            ("Cursor — machine install", "cursor-machine"),
            ("opencode — project install (current project)", "opencode-project"),
            ("opencode — machine install", "opencode-machine"),
            ("Codex CLI — project install (current project)", "codex-project"),
            ("Codex CLI — machine install", "codex-machine"),
            ("Gemini CLI — project install (current project)", "gemini-project"),
            ("Gemini CLI — machine install", "gemini-machine"),
        ],
    )

    plat, mode = chosen.rsplit("-", 1)
    if mode == "project":
        project_dir = _ask_project_dir()
        _maybe_local(mode, project_dir)
        return {
            "claude": uninstall_claude_project,
            "cursor": uninstall_cursor_no_plugin,
            "opencode": uninstall_opencode_no_plugin,
            "codex": uninstall_codex_no_plugin,
            "gemini": uninstall_gemini_no_plugin,
        }[plat](project_dir)
    if plat == "claude":
        return uninstall_claude_machine()
    return {
        "cursor": uninstall_cursor_plugin,
        "opencode": uninstall_opencode_plugin,
        "codex": uninstall_codex_plugin,
        "gemini": uninstall_gemini_plugin,
    }[plat](env)


def _ask_project_dir():
    """Ask the user for the project directory."""
    cwd = Path.cwd()
    print(f"\n  Current directory: {bold(str(cwd))}")
    if confirm("Use current directory as the project?"):
        return cwd
    raw = input("  Enter project path: ").strip()
    p = Path(raw).expanduser().resolve()
    if not p.is_dir():
        warn(f"Directory not found: {bold(str(p))}")
        if confirm(f"Create it?"):
            p.mkdir(parents=True, exist_ok=True)
            ok(f"Created {bold(str(p))}")
        else:
            err("Cannot proceed without a valid project directory.")
            sys.exit(1)
    return p


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description=f"GSE-One Installer v{VERSION} — setup for Claude Code, Cursor, opencode, Codex CLI, Gemini CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 install.py                                          # Interactive
  python3 install.py --platform claude --mode project        # everything in the project (default mode)
  python3 install.py --platform codex --mode project --project-dir /path/to/project
  python3 install.py --platform cursor --mode machine        # once for the whole machine
  python3 install.py --platform codex --mode sandbox --project-dir /path/to/project # isolated $HOME + .gse-sandbox/run launcher
  python3 install.py --platform all --mode machine
  python3 install.py --uninstall --platform gemini --mode machine
""",
    )
    parser.add_argument("--platform",
                        choices=["claude", "cursor", "opencode", "codex", "gemini", "both", "all"],
                        help="Target platform ('both' = claude+cursor, 'all' = all five)")
    parser.add_argument("--mode", choices=["project", "machine", "sandbox"],
                        help="Installation mode (default: project). 'project' = everything in "
                             "the project folder, registry at <project>/.gse/registry, nothing "
                             "under $HOME. 'machine' = one install for the whole machine, under "
                             "$HOME. 'sandbox' = HOME-isolated install inside "
                             "<project>/.gse-sandbox + a .gse-sandbox/run launcher "
                             "(codex/gemini/opencode only). The pre-0.87.0 names "
                             "(plugin/no-plugin/local) and --scope were removed.")
    parser.add_argument("--project-dir", type=str,
                        help="Project directory for project/sandbox modes (default: current directory)")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall GSE-One")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # GSE_CHILD is set when install_sandbox re-execs us under a sandbox HOME;
    # suppress the banner / environment table / summary so only the inner
    # install steps show.
    quiet = bool(os.environ.get("GSE_CHILD"))

    if not quiet:
        print(BANNER)

    env = detect_environment()
    if not quiet:
        display_environment(env)
    args = parse_args()

    # Interactive mode
    if args.platform is None:
        if args.uninstall:
            success = interactive_uninstall(env)
        else:
            success = interactive_menu(env)

        tracker.display()
        sys.exit(0 if success else 1)

    # Non-interactive mode
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()
    if args.platform == "all":
        platforms = ["claude", "cursor", "opencode", "codex", "gemini"]
    elif args.platform == "both":
        platforms = ["claude", "cursor"]
    else:
        platforms = [args.platform]
    mode = args.mode or "project"
    # Project mode is fully project-contained: arm the project-local registry
    # (<project>/.gse/registry — nothing under $HOME).
    _maybe_local(mode, project_dir)
    results = []

    for plat in platforms:
        if mode == "sandbox":
            results.append(uninstall_sandbox(plat, project_dir) if args.uninstall
                           else install_sandbox(plat, project_dir))
            continue
        if args.uninstall:
            if plat == "claude":
                results.append(uninstall_claude_machine() if mode == "machine"
                               else uninstall_claude_project(project_dir))
            elif plat == "cursor":
                results.append(uninstall_cursor_plugin(env) if mode == "machine"
                               else uninstall_cursor_no_plugin(project_dir))
            elif plat == "opencode":
                results.append(uninstall_opencode_plugin(env) if mode == "machine"
                               else uninstall_opencode_no_plugin(project_dir))
            elif plat == "codex":
                results.append(uninstall_codex_plugin(env) if mode == "machine"
                               else uninstall_codex_no_plugin(project_dir))
            elif plat == "gemini":
                results.append(uninstall_gemini_plugin(env) if mode == "machine"
                               else uninstall_gemini_no_plugin(project_dir))
        else:
            if plat == "claude":
                results.append(install_claude_machine() if mode == "machine"
                               else install_claude_project(project_dir))
            elif plat == "cursor":
                results.append(install_cursor_plugin(env) if mode == "machine"
                               else install_cursor_no_plugin(project_dir))
            elif plat == "opencode":
                results.append(install_opencode_plugin(env) if mode == "machine"
                               else install_opencode_no_plugin(project_dir))
            elif plat == "codex":
                results.append(install_codex_plugin(env) if mode == "machine"
                               else install_codex_no_plugin(project_dir))
            elif plat == "gemini":
                results.append(install_gemini_plugin(env) if mode == "machine"
                               else install_gemini_no_plugin(project_dir))

    if not quiet:
        tracker.display()
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
