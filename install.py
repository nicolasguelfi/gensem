#!/usr/bin/env python3
"""GSE-One Installer — Cross-platform interactive installation for Claude Code, Cursor, and opencode.

Usage:
    python3 install.py                        # Interactive mode
    python3 install.py --platform claude --mode plugin --scope project
    python3 install.py --platform cursor --mode plugin
    python3 install.py --platform opencode --mode plugin
    python3 install.py --platform opencode --mode no-plugin --project-dir /path/to/project
    python3 install.py --platform all --mode plugin --scope user
    python3 install.py --uninstall --platform opencode
"""

import argparse
import json
import os
import platform
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
  {dim('Cross-platform setup for Claude Code, Cursor, and opencode')}
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
# plugin, cursor no-plugin, claude no-plugin, opencode plugin, opencode
# no-plugin) point the registry at their own target install dir directly —
# no side-install needed.
GSE_ONE_DATA_DIR = Path.home() / ".gse-one.d"


def _write_registry(plugin_path):
    """Write the plugin path to ~/.gse-one so tools can be resolved at runtime."""
    REGISTRY_FILE.write_text(str(Path(plugin_path).resolve()) + "\n", encoding="utf-8")
    ok(f"Registry written: {REGISTRY_FILE} → {plugin_path}")


def _remove_registry():
    """Remove ~/.gse-one if it exists."""
    if REGISTRY_FILE.exists():
        REGISTRY_FILE.unlink()
        ok(f"Registry removed: {REGISTRY_FILE}")


def _copy_common_assets(target):
    """Copy tools/, templates/, references/, and VERSION into target.

    These are the runtime-resolvable assets that skills reach via
    `$(cat ~/.gse-one)/<subdir>/...`. Having them co-located with the registry
    target makes every install mode self-contained — the gensem source repo
    can be deleted after install and nothing breaks.

    Idempotent: each subdir is removed-then-copied; VERSION is overwritten.
    """
    target = Path(target)
    ensure_dir(target)
    for subdir in ("tools", "templates", "references"):
        src = PLUGIN_DIR / subdir
        if src.is_dir():
            copy_tree(src, target / subdir)
    version_src = PLUGIN_DIR / "VERSION"
    if version_src.exists():
        shutil.copy2(version_src, target / "VERSION")


def _remove_common_assets(target):
    """Symmetric uninstaller for _copy_common_assets.

    Removes any of tools/, templates/, references/, VERSION that exist under
    target. Safe to call when target itself does not exist.
    """
    target = Path(target)
    if not target.exists():
        return
    for subdir in ("tools", "templates", "references"):
        d = target / subdir
        if d.is_dir():
            shutil.rmtree(d)
    vf = target / "VERSION"
    if vf.exists():
        vf.unlink()


# ---------------------------------------------------------------------------
# Duplicate installation detection
# ---------------------------------------------------------------------------

def _detect_claude_plugin_installed():
    """Return True if the 'gse' plugin is registered in Claude Code.

    Runs `claude plugin list` and looks for a line whose first token is 'gse'.
    Returns False if the CLI is absent, times out, or the plugin is not listed.
    """
    if not command_exists("claude"):
        return False
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
        tokens = line.strip().split()
        if tokens and tokens[0].lower() == "gse":
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
        if mode == "plugin":
            # Check for no-plugin install in current project (prefixed or legacy GSE skills)
            local = Path(project_dir or Path.cwd()) / ".claude" / "skills"
            if _has_gse_skills_in_dir(local):
                conflicts.append(("no-plugin (project)", str(local)))
            # Check for home-level skills (~/.claude/skills) — relevant for user scope,
            # but also a duplicate source for any scope since home skills are always loaded.
            home = Path.home() / ".claude" / "skills"
            if _has_gse_skills_in_dir(home):
                conflicts.append(("no-plugin (home)", str(home)))
        elif mode == "no-plugin":
            # Check for a registered 'gse' plugin via the Claude CLI
            if _detect_claude_plugin_installed():
                conflicts.append(("plugin (registered via claude CLI)", "claude plugin list → gse"))

    elif platform_name == "cursor":
        if mode == "plugin" and env:
            # Check for no-plugin install in current project
            local = Path.cwd() / ".cursor" / "commands"
            if local.is_dir() and any(local.iterdir()):
                conflicts.append(("no-plugin (project)", str(local)))
        elif mode == "no-plugin" and env:
            # Check for global plugin install
            global_plugin = env["cursor_dir"] / "plugins" / "local" / "gse-one"
            if global_plugin.is_dir():
                conflicts.append(("plugin (global)", str(global_plugin)))

    elif platform_name == "opencode":
        if mode == "plugin":
            # Global install — check for local .opencode/ in the current project
            local = Path(project_dir or Path.cwd()) / ".opencode" / "commands"
            if local.is_dir() and any(local.glob("gse-*.md")):
                conflicts.append(("no-plugin (project)", str(local.parent)))
        elif mode == "no-plugin":
            # Local install — check for a global install that would duplicate skills
            global_skills = OPENCODE_GLOBAL_DIR / "skills"
            if global_skills.is_dir() and any(d.name in _get_skill_names()
                                              for d in global_skills.iterdir() if d.is_dir()):
                conflicts.append(("plugin (global)", str(OPENCODE_GLOBAL_DIR)))
            # Also warn if a .claude/skills layout exists — opencode loads those too
            claude_skills = Path(project_dir or Path.cwd()) / ".claude" / "skills"
            if _has_gse_skills_in_dir(claude_skills):
                conflicts.append((".claude/skills (auto-loaded by opencode)", str(claude_skills)))

    if conflicts:
        warn(f"Existing GSE-One installation(s) detected for {bold(platform_name)}:")
        for conflict_mode, conflict_path in conflicts:
            warn(f"  → {conflict_mode}: {dim(conflict_path)}")
        warn("Having both will cause duplicate commands (skills appear twice).")
        warn(f"Uninstall the other first: python3 install.py --uninstall --platform {platform_name} --mode {conflicts[0][0].split(' ')[0]}")
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
    """Verify a non-plugin installation. Returns (ok, detail)."""
    location = Path(location)

    if platform_name == "claude":
        base = location / ".claude"
    else:
        base = location / ".cursor"

    if not base.is_dir():
        return False, f"{base.name}/ not found"

    agents = base / "agents"
    if not agents.is_dir():
        return False, "agents/ not found"
    agent_count = sum(1 for f in agents.glob("*.md"))

    if platform_name == "cursor":
        # Cursor uses commands/ (flat files) for activities
        commands = base / "commands"
        if not commands.is_dir():
            return False, "commands/ not found"
        cmd_count = sum(1 for f in commands.glob("*.md"))
        return True, f"{cmd_count} commands, {agent_count} agents"
    else:
        # Claude Code uses skills/ (subdirectories with SKILL.md)
        skills = base / "skills"
        if not skills.is_dir():
            return False, "skills/ not found"
        skill_count = sum(1 for d in skills.iterdir() if d.is_dir())
        return True, f"{skill_count} skills, {agent_count} agents"


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect_environment():
    """Detect OS, Claude Code CLI, Cursor, and opencode availability."""
    os_name = platform.system()
    os_display = {"Darwin": "macOS", "Linux": "Linux", "Windows": "Windows"}.get(os_name, os_name)

    has_claude = command_exists("claude")
    has_cursor = _detect_cursor(os_name)
    has_opencode = _detect_opencode()

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
        "home": home,
        "claude_dir": claude_dir,
        "cursor_dir": cursor_dir,
        "opencode_dir": opencode_dir,
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


def display_environment(env):
    """Print detected environment."""
    step("Environment")
    info(f"Operating system : {bold(env['os'])}")
    info(f"Home directory   : {env['home']}")
    info(f"Claude Code CLI  : {green('found') if env['has_claude'] else yellow('not found')}")
    info(f"Cursor           : {green('found') if env['has_cursor'] else yellow('not found')}")
    info(f"opencode         : {green('found') if env['has_opencode'] else yellow('not found')}")
    info(f"Plugin source    : {PLUGIN_DIR}")
    info(f"Version          : {bold(VERSION)}")

    if not PLUGIN_DIR.exists():
        err(f"Plugin directory not found: {PLUGIN_DIR}")
        err("Make sure you run this script from the gensem repository root.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Claude Code — Plugin mode
# ---------------------------------------------------------------------------

def install_claude_plugin(scope):
    """Install GSE-One as a Claude Code plugin using the CLI."""
    step(f"Claude Code — Plugin install (scope: {scope})")

    if not _check_duplicate_install("claude", "plugin"):
        tracker.add("Claude Code", "plugin", scope, "-", "FAIL", "cancelled (duplicate)")
        return False

    if not command_exists("claude"):
        err("Claude Code CLI not found on PATH.")
        err("Install it from https://claude.ai/download and try again.")
        tracker.add("Claude Code", "plugin", scope, "-", "FAIL", "CLI not found")
        return False

    plugin_path = str(PLUGIN_DIR)
    cmd = ["claude", "plugin", "install", plugin_path, "--scope", scope]
    info(f"Running: {dim(' '.join(cmd))}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            ok(f"Plugin installed (scope: {scope})")
            if result.stdout.strip():
                info(result.stdout.strip())
            # Side-install common runtime assets at ~/.gse-one.d/ so that
            # shell-resolved paths remain stable even after the gensem source
            # repo is deleted and regardless of where claude stores the plugin
            # internally.
            _copy_common_assets(GSE_ONE_DATA_DIR)
            ok(f"Common assets copied to {GSE_ONE_DATA_DIR}")
            _write_registry(GSE_ONE_DATA_DIR)
            tracker.add("Claude Code", "plugin", scope, plugin_path, "OK", f"v{VERSION}")
            return True
        else:
            err(f"Installation failed (exit {result.returncode})")
            if result.stderr.strip():
                err(result.stderr.strip())
            tracker.add("Claude Code", "plugin", scope, plugin_path, "FAIL", f"exit {result.returncode}")
            return False
    except FileNotFoundError:
        err("Claude Code CLI not found.")
        tracker.add("Claude Code", "plugin", scope, "-", "FAIL", "CLI not found")
        return False
    except subprocess.TimeoutExpired:
        err("Installation timed out.")
        tracker.add("Claude Code", "plugin", scope, "-", "FAIL", "timeout")
        return False


def uninstall_claude_plugin():
    """Uninstall GSE-One from Claude Code."""
    step("Claude Code — Plugin uninstall")

    if not command_exists("claude"):
        err("Claude Code CLI not found on PATH.")
        tracker.add("Claude Code", "plugin", "-", "-", "FAIL", "CLI not found")
        return False

    cmd = ["claude", "plugin", "uninstall", "gse"]
    info(f"Running: {dim(' '.join(cmd))}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            ok("Plugin uninstalled from Claude Code")
            # Symmetric removal of the side-install dropped at install time
            _remove_common_assets(GSE_ONE_DATA_DIR)
            if GSE_ONE_DATA_DIR.exists() and not any(GSE_ONE_DATA_DIR.iterdir()):
                GSE_ONE_DATA_DIR.rmdir()
                ok(f"Removed {GSE_ONE_DATA_DIR}")
            _remove_registry()
            tracker.add("Claude Code", "uninstall", "-", "-", "OK", "removed")
            return True
        else:
            warn(f"Uninstall returned exit {result.returncode}")
            if result.stderr.strip():
                warn(result.stderr.strip())
            tracker.add("Claude Code", "uninstall", "-", "-", "WARN", f"exit {result.returncode}")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        err("Could not run claude CLI.")
        tracker.add("Claude Code", "uninstall", "-", "-", "FAIL", "CLI error")
        return False


# ---------------------------------------------------------------------------
# Claude Code — Non-plugin mode
# ---------------------------------------------------------------------------

def install_claude_no_plugin(project_dir):
    """Install GSE-One artifacts directly into .claude/ of a project.

    Skills are copied with a `gse-` prefix on their directory name so that
    Claude Code exposes them as `/gse-<name>` (e.g. /gse-go) instead of the
    bare `/<name>` that project-level skills would otherwise receive. This is
    the closest no-plugin UX to the `/gse:<name>` namespace produced by the
    plugin installation path, which remains the recommended mode.
    """
    step("Claude Code — Non-plugin install")

    # Non-plugin mode has a different invocation syntax than plugin mode.
    # Make the tradeoff explicit before anything is written to disk.
    warn("No-plugin mode — invocation syntax:")
    warn("  Commands appear as /gse-<name> (e.g., /gse-go, /gse-plan).")
    warn("  Plugin mode gives /gse:<name> (colon) — install as a plugin if you prefer that.")
    if not confirm("Continue with no-plugin install?"):
        err("Installation cancelled by user.")
        tracker.add("Claude Code", "no-plugin", "project", str(project_dir), "FAIL", "cancelled by user")
        return False

    if not _check_duplicate_install("claude", "no-plugin", project_dir=project_dir):
        tracker.add("Claude Code", "no-plugin", "project", str(project_dir), "FAIL", "cancelled (duplicate)")
        return False

    claude_dir = Path(project_dir) / ".claude"
    ensure_dir(claude_dir)

    # Skills (prefixed as gse-<name> to namespace commands in the TUI)
    skills_dst = claude_dir / "skills"
    ensure_dir(skills_dst)
    skills_src = PLUGIN_DIR / "skills"

    # Clean legacy unprefixed GSE skills from a prior install (<= v0.20.4)
    legacy_removed = 0
    for name in _get_skill_names():
        legacy = skills_dst / name
        if legacy.is_dir() and (legacy / "SKILL.md").exists():
            shutil.rmtree(legacy)
            legacy_removed += 1
    if legacy_removed:
        info(f"Removed {legacy_removed} legacy unprefixed skill(s) from a previous install")

    count = 0
    for skill_dir in sorted(skills_src.iterdir()):
        if skill_dir.is_dir():
            copy_tree(skill_dir, skills_dst / f"gse-{skill_dir.name}")
            count += 1
    ok(f"Copied {count} skills to {skills_dst} (prefixed as gse-<name>)")
    info("Commands available as /gse-<name> (e.g., /gse-go, /gse-plan)")

    # Agents
    agents_dst = claude_dir / "agents"
    ensure_dir(agents_dst)
    agents_src = PLUGIN_DIR / "agents"
    agent_count = 0
    for agent_file in sorted(agents_src.glob("*.md")):
        shutil.copy2(agent_file, agents_dst / agent_file.name)
        agent_count += 1
    ok(f"Copied {agent_count} agents to {agents_dst}")

    # Common runtime assets (tools/, templates/, references/, VERSION)
    _copy_common_assets(claude_dir)
    ok(f"Copied common assets (tools, templates, references, VERSION) to {claude_dir}")

    # Hooks
    hooks_file = PLUGIN_DIR / "hooks" / "hooks.claude.json"
    settings_file = claude_dir / "settings.json"
    _merge_hooks_into_settings(hooks_file, settings_file)
    ok(f"Merged hooks into {settings_file}")

    # Default agent
    _set_default_agent(settings_file, "gse-orchestrator")
    ok(f"Set default agent to gse-orchestrator")

    # Registry points to the local install dir — self-contained, gensem source
    # repo can be deleted after install and nothing breaks.
    _write_registry(claude_dir)

    # Verify
    is_ok, detail = verify_no_plugin(project_dir, "claude")
    if is_ok:
        tracker.add("Claude Code", "no-plugin", "project", str(claude_dir), "OK", detail)
    else:
        tracker.add("Claude Code", "no-plugin", "project", str(claude_dir), "WARN", detail)

    return True


def uninstall_claude_no_plugin(project_dir):
    """Remove GSE-One artifacts from .claude/."""
    step("Claude Code — Non-plugin uninstall")

    claude_dir = Path(project_dir) / ".claude"

    skills_dir = claude_dir / "skills"
    if skills_dir.exists():
        removed = 0
        for name in _get_skill_names():
            # Remove both the prefixed layout (current) and the legacy unprefixed
            # layout (<= v0.20.4) to keep uninstall idempotent across versions.
            for candidate in (skills_dir / f"gse-{name}", skills_dir / name):
                if candidate.exists():
                    shutil.rmtree(candidate)
                    removed += 1
        ok(f"Removed {removed} GSE-One skill(s) from {skills_dir}")

    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        for f in (PLUGIN_DIR / "agents").glob("*.md"):
            target = agents_dir / f.name
            if target.exists():
                target.unlink()
        ok(f"Removed GSE-One agents from {agents_dir}")

    # Symmetric removal of common runtime assets (tools, templates, references, VERSION)
    _remove_common_assets(claude_dir)
    ok(f"Removed common assets (tools, templates, references, VERSION) from {claude_dir}")

    info("Hooks and settings.json were not modified (manual cleanup if needed)")
    _remove_registry()
    tracker.add("Claude Code", "uninstall", "project", str(claude_dir), "OK", "removed")
    return True


# ---------------------------------------------------------------------------
# Cursor — Plugin mode
# ---------------------------------------------------------------------------

def install_cursor_plugin(env):
    """Install GSE-One as a Cursor plugin by copying to ~/.cursor/plugins/."""
    step("Cursor — Plugin install")

    if not _check_duplicate_install("cursor", "plugin", env=env):
        tracker.add("Cursor", "plugin", "global", "-", "FAIL", "cancelled (duplicate)")
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
        tracker.add("Cursor", "plugin", "global", str(dst), "OK", detail)
    else:
        warn(f"Verification issue: {detail}")
        tracker.add("Cursor", "plugin", "global", str(dst), "WARN", detail)

    return True


def uninstall_cursor_plugin(env):
    """Remove GSE-One from Cursor plugins."""
    step("Cursor — Plugin uninstall")

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
    step("Cursor — Non-plugin install")

    if not _check_duplicate_install("cursor", "no-plugin", project_dir=project_dir, env=detect_environment()):
        tracker.add("Cursor", "no-plugin", "project", str(project_dir), "FAIL", "cancelled (duplicate)")
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
        tracker.add("Cursor", "no-plugin", "project", str(cursor_dir), "OK", detail)
    else:
        tracker.add("Cursor", "no-plugin", "project", str(cursor_dir), "WARN", detail)

    return True


def uninstall_cursor_no_plugin(project_dir):
    """Remove GSE-One artifacts from .cursor/."""
    step("Cursor — Non-plugin uninstall")

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
    step("opencode — Plugin install (global)")

    if not OPENCODE_PLUGIN_DIR.is_dir():
        err(f"opencode artefacts not found at {OPENCODE_PLUGIN_DIR}")
        err("Run: cd gse-one && python3 gse_generate.py --verify")
        tracker.add("opencode", "plugin", "global", "-", "FAIL", "artefacts missing")
        return False

    if not _check_duplicate_install("opencode", "plugin"):
        tracker.add("opencode", "plugin", "global", "-", "FAIL", "cancelled (duplicate)")
        return False

    target = env["opencode_dir"]
    ensure_dir(target)

    counts = _opencode_copy_tree(OPENCODE_PLUGIN_DIR, target)
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
    tracker.add("opencode", "plugin", "global", str(target), "OK", detail)
    return True


def uninstall_opencode_plugin(env):
    """Remove GSE-One artefacts from the opencode global config dir."""
    step("opencode — Plugin uninstall (global)")

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
    step("opencode — Non-plugin install (project)")

    if not OPENCODE_PLUGIN_DIR.is_dir():
        err(f"opencode artefacts not found at {OPENCODE_PLUGIN_DIR}")
        err("Run: cd gse-one && python3 gse_generate.py --verify")
        tracker.add("opencode", "no-plugin", "project", str(project_dir), "FAIL", "artefacts missing")
        return False

    if not _check_duplicate_install("opencode", "no-plugin", project_dir=project_dir):
        tracker.add("opencode", "no-plugin", "project", str(project_dir), "FAIL", "cancelled (duplicate)")
        return False

    project_dir = Path(project_dir)
    target = project_dir / ".opencode"
    ensure_dir(target)

    counts = _opencode_copy_tree(OPENCODE_PLUGIN_DIR, target)
    # Common runtime assets (tools/, templates/, references/, VERSION) —
    # needed because opencode skills shell out to $(cat ~/.gse-one)/tools/...
    # and templates/references are consulted by activities at runtime.
    _copy_common_assets(target)
    ok(f"Copied common assets (tools, templates, references, VERSION) to {target}")
    # AGENTS.md lives at the project root in no-plugin mode (opencode convention)
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
    tracker.add("opencode", "no-plugin", "project", str(target), "OK", detail)
    return True


def uninstall_opencode_no_plugin(project_dir):
    """Remove GSE-One artefacts from a project's .opencode/ + root AGENTS.md."""
    step("opencode — Non-plugin uninstall (project)")

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

def _opencode_copy_tree(src, target):
    """Copy opencode artefacts (skills/, commands/, agents/, plugins/) into target.

    Overwrites existing GSE-named items. Returns counts dict.
    """
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
        shutil.copy2(pl, dst_pl / pl.name)
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
    # Ensure the `gse` marker reflects this install's version
    merged["gse"] = {"version": VERSION}
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
    """Remove the GSE-One `gse` marker from opencode.json; drop the file if empty."""
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
# Helpers
# ---------------------------------------------------------------------------

def _get_skill_names():
    """Return the list of skill directory names."""
    skills_src = PLUGIN_DIR / "skills"
    return [d.name for d in sorted(skills_src.iterdir()) if d.is_dir()]


def _merge_hooks_into_settings(hooks_file, settings_file):
    """Merge hooks from a hooks JSON file into a settings.json file."""
    if not hooks_file.exists():
        return

    hooks_data = json.loads(hooks_file.read_text())

    if settings_file.exists():
        settings = json.loads(settings_file.read_text())
    else:
        settings = {}

    if "hooks" not in settings:
        settings["hooks"] = {}

    src_hooks = hooks_data.get("hooks", {})
    for event, groups in src_hooks.items():
        if event == "version":
            continue
        if event not in settings["hooks"]:
            settings["hooks"][event] = []
        settings["hooks"][event].extend(groups)

    settings_file.write_text(json.dumps(settings, indent=2) + "\n")


def _set_default_agent(settings_file, agent_name):
    """Set the default agent in settings.json."""
    if settings_file.exists():
        settings = json.loads(settings_file.read_text())
    else:
        settings = {}

    settings["agent"] = agent_name
    settings_file.write_text(json.dumps(settings, indent=2) + "\n")


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
    if env["has_claude"] and env["has_cursor"] and env["has_opencode"]:
        platform_choices.append(("All three (Claude Code + Cursor + opencode)", "all"))
    elif env["has_claude"] and env["has_cursor"]:
        platform_choices.append(("Both (Claude Code + Cursor)", "both"))
    if not env["has_claude"]:
        platform_choices.append(("Claude Code (not detected — install anyway)", "claude"))
    if not env["has_cursor"]:
        platform_choices.append(("Cursor (not detected — install anyway)", "cursor"))
    if not env["has_opencode"]:
        platform_choices.append(("opencode (not detected — install anyway)", "opencode"))

    chosen_platform = ask("Install for which platform?", platform_choices)

    if chosen_platform == "all":
        platforms = ["claude", "cursor", "opencode"]
    elif chosen_platform == "both":
        platforms = ["claude", "cursor"]
    else:
        platforms = [chosen_platform]
    results = []

    for plat in platforms:
        if plat == "claude":
            mode = ask(
                "Installation mode for Claude Code?",
                [
                    ("Plugin — project scope (recommended)", "plugin-project"),
                    ("Plugin — personal scope (gitignored)", "plugin-local"),
                    ("Plugin — global scope (all projects)", "plugin-user"),
                    ("Non-plugin — copy artifacts to .claude/", "no-plugin"),
                ],
            )
            if mode == "no-plugin":
                project_dir = _ask_project_dir()
                results.append(install_claude_no_plugin(project_dir))
            else:
                scope = mode.split("-")[1]
                results.append(install_claude_plugin(scope))

        elif plat == "cursor":
            mode = ask(
                "Installation mode for Cursor?",
                [
                    ("Plugin — global (copy to ~/.cursor/plugins/)", "plugin"),
                    ("Non-plugin — copy artifacts to .cursor/", "no-plugin"),
                ],
            )
            if mode == "no-plugin":
                project_dir = _ask_project_dir()
                results.append(install_cursor_no_plugin(project_dir))
            else:
                results.append(install_cursor_plugin(env))

        elif plat == "opencode":
            mode = ask(
                "Installation mode for opencode?",
                [
                    ("Plugin — global (copy to ~/.config/opencode/)", "plugin"),
                    ("Non-plugin — copy artifacts to .opencode/ (project)", "no-plugin"),
                ],
            )
            if mode == "no-plugin":
                project_dir = _ask_project_dir()
                results.append(install_opencode_no_plugin(project_dir))
            else:
                results.append(install_opencode_plugin(env))

    return all(results)


def interactive_uninstall(env):
    """Run the interactive uninstall menu."""
    chosen = ask(
        "Uninstall from which platform?",
        [
            ("Claude Code — plugin", "claude-plugin"),
            ("Claude Code — non-plugin (current project)", "claude-no-plugin"),
            ("Cursor — plugin", "cursor-plugin"),
            ("Cursor — non-plugin (current project)", "cursor-no-plugin"),
            ("opencode — plugin (global)", "opencode-plugin"),
            ("opencode — non-plugin (current project)", "opencode-no-plugin"),
        ],
    )

    if chosen == "claude-plugin":
        return uninstall_claude_plugin()
    elif chosen == "claude-no-plugin":
        return uninstall_claude_no_plugin(_ask_project_dir())
    elif chosen == "cursor-plugin":
        return uninstall_cursor_plugin(env)
    elif chosen == "cursor-no-plugin":
        return uninstall_cursor_no_plugin(_ask_project_dir())
    elif chosen == "opencode-plugin":
        return uninstall_opencode_plugin(env)
    elif chosen == "opencode-no-plugin":
        return uninstall_opencode_no_plugin(_ask_project_dir())


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
        description=f"GSE-One Installer v{VERSION} — Cross-platform setup for Claude Code, Cursor, and opencode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 install.py                                          # Interactive
  python3 install.py --platform claude --mode plugin --scope project
  python3 install.py --platform cursor --mode plugin
  python3 install.py --platform opencode --mode plugin
  python3 install.py --platform opencode --mode no-plugin --project-dir /path/to/project
  python3 install.py --platform both --mode plugin --scope user
  python3 install.py --platform all --mode plugin --scope user
  python3 install.py --uninstall --platform opencode --mode plugin
""",
    )
    parser.add_argument("--platform", choices=["claude", "cursor", "opencode", "both", "all"],
                        help="Target platform ('both' = claude+cursor, 'all' = all three)")
    parser.add_argument("--mode", choices=["plugin", "no-plugin"], help="Installation mode")
    parser.add_argument("--scope", choices=["project", "local", "user"], default="project",
                        help="Plugin scope for Claude Code (default: project). Ignored for Cursor/opencode.")
    parser.add_argument("--project-dir", type=str,
                        help="Project directory for non-plugin mode (default: current directory)")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall GSE-One")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(BANNER)

    env = detect_environment()
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
        platforms = ["claude", "cursor", "opencode"]
    elif args.platform == "both":
        platforms = ["claude", "cursor"]
    else:
        platforms = [args.platform]
    mode = args.mode or "plugin"
    results = []

    for plat in platforms:
        if args.uninstall:
            if plat == "claude":
                results.append(uninstall_claude_plugin() if mode == "plugin"
                               else uninstall_claude_no_plugin(project_dir))
            elif plat == "cursor":
                results.append(uninstall_cursor_plugin(env) if mode == "plugin"
                               else uninstall_cursor_no_plugin(project_dir))
            elif plat == "opencode":
                results.append(uninstall_opencode_plugin(env) if mode == "plugin"
                               else uninstall_opencode_no_plugin(project_dir))
        else:
            if plat == "claude":
                results.append(install_claude_plugin(args.scope) if mode == "plugin"
                               else install_claude_no_plugin(project_dir))
            elif plat == "cursor":
                results.append(install_cursor_plugin(env) if mode == "plugin"
                               else install_cursor_no_plugin(project_dir))
            elif plat == "opencode":
                results.append(install_opencode_plugin(env) if mode == "plugin"
                               else install_opencode_no_plugin(project_dir))

    tracker.display()
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
