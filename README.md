<h1 align="center">GSE-One</h1>
<h2 align="center">Built by AI.<br>Governed by Humans.</h2>

GSE-One (Generative Software Engineering One) is an AI engineering companion that brings structured software development lifecycle (SDLC) management to coding agents. It works as a plugin for **Claude Code**, **Cursor**, and **opencode** — plus **Codex CLI** and **Gemini CLI** (experimental, pending runtime validation), guiding projects through requirements, design, testing, production, review, and knowledge transfer — with adaptive risk analysis and methodology guardrails.

**Why GSE-One:** it optimizes *trustworthy delegation* — not raw throughput. Three differentiators: **governance** (every decision classified, consequence-projected, journaled, guardrailed), **adaptivity** (calibrates to the human via the HUG profile and three modes), and **AI integrity** (devil's-advocate review + per-claim confidence levels).

<p align="center">
  <img src="assets/images/logo-gse-geni-with-shield-landscape_4x_slogan.png" width="700" alt="GSE-One — Built by AI, Governed by Humans">
</p>

---

## Table of Contents

1. [Key Features](#key-features)
2. [Choosing your installation](#choosing-your-installation)
3. [Quick install (curl | sh)](#quick-install-curl--sh)
4. [Environment variables](#environment-variables)
5. [Sandbox mode (isolated run)](#sandbox-mode-isolated-run)
6. [Advanced configurations](#advanced-configurations)
7. [Troubleshooting](#troubleshooting)
8. [Manual install (maintainers, forks, Windows without WSL)](#manual-install-maintainers-forks-windows-without-wsl)
9. [Mono-plugin Architecture](#mono-plugin-architecture)
10. [Develop and Generate](#develop-and-generate)
11. [Publish the Plugin](#publish-the-plugin)
12. [Command Reference](#command-reference)
13. [Deployment](#deployment)
14. [Auditing the plugin](#auditing-the-plugin)
15. [Versioning](#versioning)

---

## Key Features

- **24 commands** covering the full SDLC — from onboarding (`/gse:hug`) to capitalization (`/gse:compound`)
- **3 modes** — Micro, Lightweight, Full — auto-selected by complexity assessment, user-overridable
- **Adaptive risk analysis** — 3-tier decision system (Auto / Inform / Gate) calibrated to user expertise, backed by 3-level guardrails (Soft / Hard / Emergency) for high-consequence actions
- **Unified backlog** — single task tracking with git state per-task
- **8-dimension health dashboard** — generated HTML with radar chart, kanban, lifecycle checklist
- **AI integrity guardrails** — confidence levels, verification gates, devil's advocate agent
- **Cross-platform** — one plugin on Claude Code, Cursor, and opencode (plus experimental Codex CLI and Gemini CLI)

---

## Choosing your installation

Two setups cover the vast majority of users. Pick your situation, copy the command, run it — details and edge cases live in [Advanced configurations](#advanced-configurations).

### Situation 1 — Everything in the project folder *(most common)*

One GSE-One install **per project**, fully self-contained: nothing is written to your home directory, the project can be committed or synced whole (Dropbox, another machine — it keeps working), and each project pins its own GSE version. Run the command **inside the project folder**, naming your coding agent:

| Coding agent | Command (run inside your project) | Comments |
|---|---|---|
| Claude Code | `GSE_PLATFORM=claude sh -c "$(curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh)"` | Commands as `/gse:go` (plugin namespace, native `gse:*` subagents). Accept the workspace trust dialog + `/reload-plugins` on first open. Writes `.claude/` + `.gse/registry`. |
| Cursor | `GSE_PLATFORM=cursor sh -c "$(curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh)"` | Commands as `/gse-go`. Writes `.cursor/` + `.gse/registry`. |
| opencode | `GSE_PLATFORM=opencode sh -c "$(curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh)"` | Commands as `/gse-go`. Writes `.opencode/` + merges `opencode.json` + `.gse/registry`. |
| Codex CLI | `GSE_PLATFORM=codex sh -c "$(curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh)"` | Skills as `$gse-go` (no slash form on Codex). After install: open `/hooks` once and approve the GSE hooks. |
| Gemini CLI | `GSE_PLATFORM=gemini sh -c "$(curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh)"` | Commands as `/gse:go`. Accept the folder-trust prompt on first launch. |

**Updating this project:** re-run the same command inside the project — each project updates independently.

### Situation 2 — GSE once for the whole machine

GSE-One installs **into your home directory**; every project you open gets it, and one update updates them all. The project keeps only its own state (`.gse/`, sprint docs). From a clone of this repo:

| Coding agent | Command | Comments |
|---|---|---|
| Claude Code | `python3 install.py --platform claude --mode machine` | Plugin namespace `/gse:go`; installs to `~/.claude/skills/gse/` + `~/.gse-one.d/`. |
| Cursor | `python3 install.py --platform cursor --mode machine` | Installs to `~/.cursor/plugins/local/gse-one/`. |
| opencode | `python3 install.py --platform opencode --mode machine` | Installs to `~/.config/opencode/`. |
| Codex CLI | `python3 install.py --platform codex --mode machine` | `~/.codex/` + `~/.agents/skills/` + `~/.gse-one.d/`; approve the GSE hooks once in `/hooks`. |
| Gemini CLI | `python3 install.py --platform gemini --mode machine` | Extension at `~/.gemini/extensions/gse-one/`. |

*(Without a clone: the curl command of Situation 1 with `GSE_MODE=machine` does the same.)*

**One agent per project is the norm:** if several coding agents are on your PATH, the installer refuses to guess — name yours with `GSE_PLATFORM=…` (or `--platform`). With exactly one agent installed, it is picked automatically. To really install on every detected agent at once, set `GSE_PLATFORM=all` explicitly.

Other needs — throwaway isolated environments (training, evaluation), the full machine-vs-project matrix, and the pre-0.87.0 mode names — are covered in [Advanced configurations](#advanced-configurations).

---

## Quick install (curl | sh)

One command installs GSE-One for your coding agent — no clone, no prompts (see [Choosing your installation](#choosing-your-installation) to pick the right variables).

**Run it from inside your project folder** (create one first if needed) — the installer targets the current directory:

```bash
curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | sh
```

Uninstall and upgrade use the same URL:

```bash
curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | sh -s -- uninstall
curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | sh -s -- upgrade
```

The script detects which of Claude Code, Cursor, opencode, Codex CLI, and Gemini CLI are on your PATH. With **exactly one** agent installed it is picked automatically; with **several**, the script stops and asks you to name yours via `GSE_PLATFORM=…` (set `GSE_PLATFORM=all` to really target every detected agent). By default it installs **everything inside the current directory** (project mode): a `.claude/`, `.cursor/`, `.opencode/`, `.codex/` (+ `.agents/skills/`), or `.gemini/` subfolder, plus the registry marker `<project>/.gse/registry` — **nothing is written to your home directory**. Set `GSE_MODE=machine` for a whole-machine install instead (see [Choosing your installation](#choosing-your-installation)).

Once finished, open your coding agent and start GSE-One. The entry command differs per platform:

| Platform | First command |
|---|---|
| Claude Code | `/gse:go` |
| Cursor / opencode | `/gse-go` |
| Gemini CLI | `/gse:go` |
| Codex CLI | the activities are namespaced skills — type `$gse-go` (autocomplete) or pick `gse-go` from `/skills`; the `/gse-go` and `/gse:go` slash forms do **not** exist on Codex |

**Requirements:** `curl`, `tar`, and `python3 ≥ 3.8` on PATH. macOS and Linux are supported out of the box; Windows users should use WSL or the [Manual install](#manual-install-maintainers-forks-windows-without-wsl) path.

### Your first session

You only need four commands to start — the agent profiles you, proposes each next step, and explains as it goes; you never need the other 20 commands up front:

- `/gse-go` (`/gse:go` on Claude Code and Gemini) — the single entry point: onboarding on first run, then "what's next" forever after
- `/gse-status` — where am I? (sprint, tasks, open items)
- `/gse-health` — 8-dimension project health with a generated dashboard
- `/gse-pause` — checkpoint the session safely before stepping away

The full quickstart lives in the spec: `gse-one-spec.md` §0 — Getting Started ("Your First 20 Minutes").

---

## Environment variables

The curl installer reads five environment variables that override auto-detection. Set them inline before the `sh` to force a specific install shape.

| Variable | Values | Description |
|---|---|---|
| `GSE_PLATFORM` | `claude` \| `cursor` \| `opencode` \| `codex` \| `gemini` \| `all` \| `both` | Target platform — `both` = claude + cursor, `all` = every supported platform. Default: the single agent detected on PATH; with several agents detected the installer refuses to guess and asks for this variable |
| `GSE_MODE` | `project` \| `machine` \| `sandbox` | `project` (default) = everything in the project folder, registry at `<project>/.gse/registry`, **nothing under `$HOME`** (self-contained / committable). `machine` = one install for the whole machine, under `$HOME`. `sandbox` = **isolated `$HOME` in `.gse-sandbox/` + a `.gse-sandbox/run` launcher** (codex/gemini/opencode). The pre-0.87.0 names (`plugin`/`no-plugin`/`local`) and `GSE_SCOPE` were removed — the installer fails with the mapping if you use them |
| `GSE_VERSION` | `latest` \| `vX.Y.Z` | Release tag to install; `latest` resolves via the GitHub API (default: `latest`) |
| `GSE_PROJECT_DIR` | path | Target directory for `project` / `sandbox` modes (default: current working directory; relative paths are resolved against the invocation directory) |

> **Where the variables go:** put `GSE_*` variables just before the `sh` that runs the installer (as in the examples below) or use the `GSE_PLATFORM=… sh -c "$(curl …)"` form of the table. Written in front of `curl` (`GSE_VERSION=… curl … | sh`), they apply to `curl` only and the installer never sees them — the version is then not pinned.

Example — pin to an explicit version and install only for Cursor:

```bash
curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | \
  GSE_PLATFORM=cursor GSE_VERSION=v0.62.7 sh
```

Example — install into a specific project directory:

```bash
curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | \
  GSE_PROJECT_DIR=/path/to/myproject sh
```

---

## Sandbox mode (isolated run)

`GSE_MODE=sandbox` (or `python3 install.py --mode sandbox`) installs GSE-One under a **project-internal `$HOME`** at `<project>/.gse-sandbox/`, so nothing touches your real home directory. Supported on **Codex CLI, Gemini CLI, and opencode** (the file-based, `$HOME`-honoring agents); Claude Code and Cursor are rejected with a pointer to `--mode project`.

**Install and run are decoupled** — install once, then launch the isolated agent any day with the generated launcher:

```bash
# Install once (here: Codex into ./my-project)
curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | \
  GSE_MODE=sandbox GSE_PLATFORM=codex GSE_PROJECT_DIR=./my-project sh

# Run the agent isolated — any day, no reinstall
cd my-project
sh .gse-sandbox/run
```

A single `rm -rf .gse-sandbox` removes the isolated `$HOME` and the launcher; it never collides with the GSE state dir `.gse/`.

> **Gemini first launch:** Gemini's folder trust is on by default — in an untrusted folder it silently downgrades `--yolo`/`--approval-mode` to `default` and holds back project hooks. Accept the folder-trust prompt on first launch (a fresh sandbox `$HOME` has no trust state), or the GSE guardrails and the `--bypass`/`--auto` translations stay inert. Headless: set `GEMINI_CLI_TRUST_WORKSPACE=true`.

### Convenience flags: `--bypass` and `--auto`

The launcher accepts two **platform-agnostic** flags that it strips from the args and translates to the running agent's native equivalent. All other args pass through verbatim.

| Flag | Meaning | Codex | Gemini | Claude |
|---|---|---|---|---|
| `--bypass` | Fully unprotected (no approvals, no OS sandbox) | `--dangerously-bypass-approvals-and-sandbox` | `--yolo` | `--dangerously-skip-permissions` |
| `--auto` | Autonomous, but keep the OS sandbox / lighter scope | `--sandbox workspace-write --ask-for-approval on-request` | `--approval-mode=auto_edit` | `--permission-mode acceptEdits` |

```bash
sh .gse-sandbox/run --auto        # autonomous, OS sandbox kept
sh .gse-sandbox/run --bypass      # fully unprotected — use with care
```

> **opencode / Cursor:** permissions are config-driven (`.opencode/opencode.json` `permission`) or an app setting (Cursor → Settings → Agent → Auto-Run), so the launcher injects no flag and prints a note instead.

---

## Advanced configurations

The two situations of [Choosing your installation](#choosing-your-installation) cover most users. The remaining setups:

**The machine-vs-project matrix.** The mode answers one question — *who sees GSE*: the whole machine (`machine`, under `$HOME`) or one project (`project`, everything inside the project folder, registry at `<project>/.gse/registry`):

| Platform | `--mode machine` | `--mode project` |
|---|---|---|
| Claude Code | `~/.claude/skills/gse/` (skills-dir plugin) + `~/.gse-one.d/` | `.claude/skills/gse/` (skills-dir plugin) + `.claude/` assets — `/gse:go` namespace, native `gse:*` subagents, zero `$HOME` footprint; accept the workspace trust dialog + `/reload-plugins` on first open |
| Cursor | `~/.cursor/plugins/local/gse-one/` | `.cursor/` |
| opencode | `~/.config/opencode/` | `.opencode/` |
| Codex CLI | `~/.codex/` + `~/.agents/skills/` + `~/.gse-one.d/` | `.codex/` + `.agents/skills/` |
| Gemini CLI | `~/.gemini/extensions/gse-one/` | `.gemini/` |

**Opening a project install elsewhere (Claude Code).** A `--mode project` install travels with the project folder: when you open it on another machine (or someone else opens your project after cloning it), no install command is needed — Claude shows the workspace trust dialog on first open; accept it and run `/reload-plugins`, and the GSE skills and agents load. The deterministic guardrail hooks (carried by `.claude/settings.json`) are active immediately, even before the trust dialog.

**Pre-0.87.0 mode names (removed).** `plugin` → use `machine`; `no-plugin` and `local` → use `project`; the Claude-only `--scope` flag (and `GSE_SCOPE`) is gone — the level is carried by the mode. The installer fails with this mapping if an old name is used. Also gone with `no-plugin`: its machine-level registry pointer `~/.gse-one` for project installs (it was last-install-wins across projects); project installs now always keep their registry inside the project. Re-running a project install over a pre-0.87.0 layout cleans the old artifacts automatically.

**Sandbox** (previous section) is the third setup: a project-internal `$HOME` for training/evaluation — the only mode that also isolates the agent's *runtime* (auth included), not just the files.

---

## Troubleshooting

### `python3` not found (or version < 3.8)

GSE-One requires Python 3.8 or newer at runtime. Install it with your OS package manager, then re-run the curl one-liner.

```bash
# macOS (Homebrew)
brew install python3

# Debian / Ubuntu
sudo apt install python3

# RHEL / Fedora
sudo dnf install python3
```

Windows users without WSL should follow the [Manual install](#manual-install-maintainers-forks-windows-without-wsl) path, which calls `python install.py` directly.

### `curl` or `tar` missing

Both are required by the installer to fetch and extract the release tarball. They ship by default on macOS and on most Linux distributions; on a minimal container or stripped-down image, install them via `apt install curl tar`, `dnf install curl tar`, or the equivalent for your distro.

### GitHub API rate limit reached

When `GSE_VERSION` is `latest` (the default), the installer calls `https://api.github.com/repos/nicolasguelfi/gensem/releases/latest` to resolve the current tag. Unauthenticated GitHub API requests are capped at roughly 60 per hour per IP, so CI runners, shared networks, or tight install loops can hit the limit. Work around it by pinning an explicit version so the API call is skipped:

```bash
curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | \
  GSE_VERSION=v0.62.7 sh
```

---

## Manual install (maintainers, forks, Windows without WSL)

Clone the repo and run `install.py` directly when you are contributing to GSE-One, working on a fork, or running native Windows without WSL. This path exposes the full CLI surface and does not require the curl bootstrap.

The installer is **platform-symmetric** — the only thing that changes between the five agents is the `--platform` value. Set it once in a shell variable and the same recipe works for every agent.

### One recipe, any agent (project mode)

```bash
AGENT=claude        # claude | cursor | opencode | codex | gemini

# Set up the workspace
mkdir gse-quick-start && cd gse-quick-start
git clone https://github.com/nicolasguelfi/gensem.git
mkdir my-project && (cd my-project && git init)

# Install into the project (project mode — everything stays in my-project/)
python3 gensem/install.py --platform "$AGENT" --mode project \
  --project-dir "$PWD/my-project"

# Launch the agent in the project
cd my-project
"$AGENT"            # Cursor users: run `cursor .`
```

Then start GSE-One with your agent's entry command (`/gse-go`, `/gse:go`, or Codex's `$gse-go` — see [Your first session](#your-first-session)).

> **What project mode writes.** Artifacts go into the project's platform dir (`.claude/`, `.cursor/`, `.opencode/`, `.codex/`, or `.gemini/`) plus the registry marker `<project>/.gse/registry` — **nothing under `$HOME`**; the project is committable and syncs whole across machines. Commands use the `gse-` dash prefix, except Claude Code and Gemini which expose `/gse:<name>`. **Codex only:** after installing, launch `codex`, open `/hooks`, and approve the GSE-One hooks — unapproved hooks do not run, so the deterministic guardrails stay inert until then.

> **`git init`.** The `git init` above creates a fresh repository for YOUR project, independent of the `.git/` inside the `gensem/` clone (which tracks the plugin source). First-time git users: GSE-One configures your git identity automatically on the first commit — no prior `git config` needed.

### Maintainer dev-loop (edit src → regenerate → reinstall → run)

When editing the methodology source under `gse-one/src/`, regenerate the plugin before each reinstall and use **sandbox mode** — the install is fully isolated under the project and the launch step is identical for every agent:

```bash
AGENT=gemini                       # codex | gemini | opencode (sandbox is file-based only)
GENSEM=/path/to/gensem
PROJECT=/path/to/throwaway-test-project

# 1. Regenerate plugin/ from your src/ edits
( cd "$GENSEM/gse-one" && python3 gse_generate.py --verify )

# 2. Clean the previous isolated install (safe: holds only install artifacts)
rm -rf "$PROJECT/.gse-sandbox"

# 3. Reinstall into an isolated $HOME under the project
python3 "$GENSEM/install.py" --platform "$AGENT" --mode sandbox --project-dir "$PROJECT"

# 4. Launch — same command for every agent; pick an autonomy level:
cd "$PROJECT"
sh .gse-sandbox/run                # plain — per-action approvals
# sh .gse-sandbox/run --auto       # autonomous, OS sandbox kept
# sh .gse-sandbox/run --bypass     # fully unprotected (no approvals, no sandbox)
```

`--auto` / `--bypass` are translated to each agent's native flag; any other argument passes through verbatim. See [Sandbox mode](#sandbox-mode-isolated-run) for the per-agent translation table.

> **⚠️ The `--auto` / `--bypass` flags go on the launcher** (`sh .gse-sandbox/run --bypass`), **never on `install.py`** — the installer rejects unknown flags and the chain aborts before the launch.
>
> **⚠️ Never `rm -rf .gse`** (no suffix): that deletes project methodology state (backlog, plan, status). Only `.gse-sandbox/` is install scratch that is safe to wipe between reinstalls.

### Plugin mode (alternative)

To install via the platform's plugin system (prefixed commands `/gse:*` on Claude/Gemini, `/gse-*` on Cursor/opencode; contextual skills on Codex):

```bash
# Cursor (local plugin)
python3 install.py --platform cursor --mode machine

# Claude Code (user-scoped plugin)
python3 install.py --platform claude --mode machine

# opencode (global — ~/.config/opencode/)
python3 install.py --platform opencode --mode machine

# Codex CLI (global — ~/.codex/ + ~/.agents/skills/)
# After installing: launch codex, open /hooks, and approve the GSE-One hooks —
# unapproved hooks do NOT run (the deterministic guardrails stay inert).
# Headless-only escape hatch: --dangerously-bypass-hook-trust (not recommended).
python3 install.py --platform codex --mode machine

# Gemini CLI (global extension — ~/.gemini/extensions/gse-one/)
python3 install.py --platform gemini --mode machine

# All detected platforms at once (user/global scope)
python3 install.py --platform all --mode machine

# Interactive (the installer guides you)
python3 install.py
```

---

## Mono-plugin Architecture

GSE-One uses a **single deployable directory** (`plugin/`) that works on all five platforms (Claude Code, Cursor, opencode, Codex CLI, Gemini CLI):

```
gse-one/
├── src/                              # Single source of truth
│   ├── principles/                   # 16 principles (P1-P16)
│   ├── activities/                   # 24 activity definitions → skills
│   ├── agents/                       # 11 agents (10 specialized + orchestrator)
│   └── templates/                    # 28 templates
│
├── plugin/                           # Deployable directory
│   ├── .claude-plugin/plugin.json    # Claude Code manifest
│   ├── .cursor-plugin/plugin.json    # Cursor manifest
│   ├── skills/                       # 24 skills (shared, with name: field)
│   ├── commands/                     # 24 /gse-<name>.md (Cursor)
│   ├── agents/                       # 11 agents (shared)
│   ├── templates/                    # 28 templates (shared)
│   ├── tools/                        # Python tools (dashboard, etc.)
│   ├── rules/gse-orchestrator.mdc    # Cursor only
│   ├── hooks/                        # Platform-specific hooks
│   ├── settings.json                 # Claude only
│   └── opencode/                     # opencode subtree
│       ├── skills/                   # 24 skills (name: injected)
│       ├── commands/                 # 24 /gse-<name>.md
│       ├── agents/                   # 10 specialized (mode: subagent)
│       ├── plugins/gse-guardrails.ts # Native TS guardrails plugin
│       ├── AGENTS.md                 # Orchestrator body (markered)
│       └── opencode.json             # Default permissions
│
└── install.py                        # Cross-platform installer (5 platforms)
```

**Shared files:** skills, agents, templates, tools — single copy, zero divergence.
**Platform-specific:** manifests, hooks, settings, rules, opencode subtree — all generated from the same source.

---

## Develop and Generate

### Edit the Sources

All changes are made in `src/`. Never modify `plugin/` directly — it is regenerated.

### Regenerate the Plugin

After any modification:

```bash
cd gse-one/
python3 gse_generate.py --clean --verify
```

> **Windows:** If `python3` is not recognized, use `python` instead.

The generator:
1. Copies skills, specialized agents and templates (shared)
2. Generates the orchestrator and Cursor rule from the **same source** — verifies body parity
3. Generates hooks (Claude PascalCase / Cursor camelCase) from the same commands
4. Generates manifests and `settings.json`

---

## Publish the Plugin

Plugin visibility depends on the distribution method:

| Method | Visibility | Prerequisites |
|--------|-----------|---------------|
| Local test | You only | None |
| GitHub (private repo) | Invited collaborators | Private GitHub repo |
| GitHub (public repo) | Anyone with the link | Public GitHub repo |
| Marketplace | Everyone | Anthropic/Cursor approval |

### Install

```bash
# Interactive (recommended)
python3 install.py
```

#### `install.py` options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| *(no flags)* | — | — | **Interactive mode** — detects environment, guides step by step |
| `--platform` | `claude` \| `cursor` \| `opencode` \| `codex` \| `gemini` \| `both` \| `all` | *(interactive)* | Target platform (`both` = claude+cursor, `all` = every supported platform) |
| `--mode` | `project` \| `machine` \| `sandbox` | `project` | `project` (default) = everything in the project folder, nothing under `$HOME`; `machine` = whole machine, under `$HOME`; `sandbox` = isolated `$HOME` in `.gse-sandbox/` + a `.gse-sandbox/run` launcher (codex/gemini/opencode). Pre-0.87.0 names (`plugin`/`no-plugin`/`local`) and `--scope` were removed |
| `--project-dir` | path | current directory | No-plugin/local modes, and Claude plugin mode in `project` scope |
| `--uninstall` | *(flag)* | `false` | Remove GSE-One |

#### Examples

```bash
# Claude Code — plugin, project scope
# (copies the plugin to <project>/.claude/skills/gse/ — a "skills-directory
#  plugin", auto-loaded as gse@skills-dir; user scope uses ~/.claude/skills/gse/.
#  Project scope loads only in trusted workspaces: accept the trust dialog,
#  then run /reload-plugins.)
python3 install.py --platform claude --mode project

# Cursor — plugin (global)
python3 install.py --platform cursor --mode machine

# opencode — plugin (global, ~/.config/opencode/)
python3 install.py --platform opencode --mode machine

# opencode — non-plugin (project .opencode/)
python3 install.py --platform opencode --mode project --project-dir /path/to/myproject

# Codex CLI — plugin (global) / Gemini CLI — plugin (global extension)
python3 install.py --platform codex --mode machine
python3 install.py --platform gemini --mode machine

# Both Claude + Cursor
python3 install.py --platform both --mode machine

# All detected platforms at once
python3 install.py --platform all --mode machine

# Project mode (Claude)
python3 install.py --platform claude --mode project --project-dir /path/to/myproject

# Project mode — everything in the project, nothing under $HOME (self-contained / committable)
python3 install.py --platform codex --mode project --project-dir /path/to/myproject

# Uninstall
python3 install.py --uninstall --platform claude --mode machine
```

> **Windows:** If `python3` is not recognized, use `python` instead.

#### Marketplace (when available)

Not yet operational. After approval:
- Claude Code: `claude plugin marketplace add nicolasguelfi/gensem` then `claude plugin install gse@gse-one` (the CLI no longer accepts local paths — marketplace ids only)
- Cursor: search "gse-one" in `/add-plugin`
- opencode: installed via `install.py` (opencode uses direct filesystem loading — no marketplace step required)

---

## Command Reference

### Developer

```bash
# Regenerate plugin after modifying src/
cd gse-one/
python3 gse_generate.py --clean --verify

# Publish a new version
# 1. Update VERSION file
# 2. Update CHANGELOG.md
# 3. Regenerate + commit + tag + push
python3 gse_generate.py --clean --verify
git add .
git commit -m "feat: GSE-One vX.Y.Z — description"
git tag vX.Y.Z
git push origin main --tags
```

### User

```bash
# Install (interactive)
python3 install.py

# Install (scripted)
python3 install.py --platform claude --mode project

# Uninstall
python3 install.py --uninstall --platform claude --mode machine
```

### Verification

Type in your coding agent:

```
/gse:go
```

The GSE-One agent should respond, detect the project state and propose the next activity.

---

## Deployment

GSE-One includes `/gse:deploy` — a single-command deployment flow that provisions a Hetzner Cloud server, installs Coolify v4, configures DNS + SSL, and deploys the current project.

**Just run `/gse:deploy`.** On first use, the command displays a Step -1 Orientation menu and asks whether you are:

- **Solo** — deploying your own project to your own server (~1h setup, ~8.49 EUR/month)
- **Instructor** — preparing a shared training server, then distributing `.env.training` to learners (~1h setup)
- **Learner** — your instructor sent you a `.env.training` file (~5 min to deploy your app)
- **Skip** — experienced user, proceed directly to detection

The orientation tailors the subsequent 6-phase flow to your role. For scripting or experienced users, `/gse:deploy --silent` skips the orientation and goes straight to detection.

See `gse-one-implementation-design.md` §5.18 for the full design.

### Prerequisites

- **Python 3.8+** (the GSE-One runtime baseline — same requirement as the installer)
- **hcloud CLI** — installed automatically in Phase 1 if missing
- **SSH** — available natively on macOS / Linux / Windows 10+

### Maintaining upstream compatibility

`/gse:deploy` is **deliberately concrete**: every command, API endpoint, and UI step is embedded verbatim (see design doc §5.18 — Abstraction principle). This choice trades occasional maintenance work for deterministic, auditable, self-contained behavior.

Three areas drift upstream over time:

1. **Coolify API** — `plugin/tools/coolify_client.py` is pinned to **Coolify v4, API `v1`** (last verified 2026-04-20). A new API version, renamed field, or new auth scheme will surface as a `404` or unexpected JSON.
2. **DNS registrar UIs** — `src/activities/deploy.md` Phase 5 embeds step-by-step instructions for Namecheap, Gandi, OVH, and Cloudflare. UI labels and navigation paths may change.
3. **hcloud CLI install paths** — `Phase 1` embeds download URLs; releases move.

**When you hit a drift, we welcome your contribution.** Fixes are usually small and localized:

| Drift | File to update |
|---|---|
| Coolify API endpoint | `gse-one/plugin/tools/coolify_client.py` |
| Registrar UI step | `gse-one/src/activities/deploy.md` (Phase 5 subsection) |
| hcloud install | `gse-one/src/activities/deploy.md` (Phase 1 Step 1) |
| Cloudflare CDN setup | `gse-one/src/activities/deploy.md` (Phase 5 CDN proposal) |
| Coolify onboarding wizard | `gse-one/src/activities/deploy.md` (Phase 4) |

Suggested workflow:

1. Fork the repo and create a branch named `fix/<scope>-<short-desc>` (e.g. `fix/coolify-api-rename-fqdn`, `fix/registrar-gandi-new-ui`)
2. Update the relevant file(s)
3. Run a manual test: provision → deploy a sample project from scratch
4. Update the "last verified" date where applicable (Coolify: in `coolify_client.py` header + design §5.18)
5. Open a PR describing: the scope, what changed upstream, what you tested

Thank you — contributions keep `/gse:deploy` usable across releases of Hetzner, Coolify, Cloudflare, and domain registrars.

---

## Auditing the plugin

GSE-One ships with a **three-part audit tool** for maintainers and forkers of the methodology repository:

1. **Coherence audit** — checks internal consistency across spec, design, and implementation (23 parallel LLM jobs)
2. **Strategic critique** — evaluates methodology quality, relevance, and user value (4 of the 28 jobs)
3. **Distribution hygiene** — Category F invariants on the shipped plugin (5 deterministic jobs run by the Python engine)

Not for user projects — for those, use `/gse:status`, `/gse:health`, `/gse:review`, `/gse:assess`, `/gse:compound`, `/gse:collect`.

### Two access points

**Slash command (Claude Code, interactive):**

```
/gse-meta-audit                    # all 28 jobs (23 LLM in parallel + 5 engine F-jobs)
/gse-meta-audit --deterministic-only   # fast Python engine only
/gse-meta-audit --coherence-only   # skip strategic critique (19 LLM jobs + F)
/gse-meta-audit --strategic-only   # only Category E (4 jobs)
/gse-meta-audit --job deploy-cluster   # single job
```

When the maintainer later decides to address a batch of findings, the dedicated fix-session command `/gse-meta-audit-fix` takes over (verification pass against LLM false positives, in-place verdicts, cluster-based application, release).

Spawns **23 parallel sub-agents** (one per LLM job; the 5 Category F jobs run inside the Python engine), each with its own file list and checks defined in `.claude/audit-jobs.json`. Combines with the Python deterministic engine for a unified report.

**CLI (for CI or quick checks, Python only):**

```bash
cd gensem  # or your fork
python3 gse-one/audit.py                      # deterministic report (markdown)
python3 gse-one/audit.py --format json        # JSON for CI/scripting
python3 gse-one/audit.py --category version   # single category
python3 gse-one/audit.py --cluster deploy-cluster   # filter to cluster
python3 gse-one/audit.py --list-clusters      # list available jobs
python3 gse-one/audit.py --fail-on error      # exit code 1 on errors (CI)
python3 gse-one/audit.py --no-save            # stdout only, don't save to disk
python3 gse-one/audit.py --save-to report.md  # explicit output path
```

The commands above produce a **standalone deterministic report**. The `/gse-meta-audit` slash command instead drives the **canonical JSON registry** (see [Report persistence](#report-persistence-default-behavior) below) through these registry commands:

```bash
python3 gse-one/audit.py --emit-registry      # archive previous + seed _LOCAL/audit/audit.json with engine findings
python3 gse-one/audit.py --merge findings.json    # fold in LLM findings/recommendations/clusters
python3 gse-one/audit.py --set-verdicts v.json    # apply Phase 3.5 verdicts in place
python3 gse-one/audit.py --render             # render the registry to a throwaway /tmp markdown
python3 gse-one/audit.py --render --out report.md  # ...or to an explicit path
```

Pure Python stdlib. **Optional dependency:** `pip install pyyaml` enables YAML schema validation.

### Report persistence (default behavior)

The two flows persist differently (redesigned in v0.75.0 — single canonical registry):

**`/gse-meta-audit` slash command — one living JSON registry.** The full augmented audit (deterministic findings + LLM findings + strategic recommendations) is written to a single canonical artifact:

```
_LOCAL/audit/audit.json                   # single source of truth (schema_version, stable AUD-<hash> ids)
_LOCAL/audit/archive/audit-<ts>-v<ver>.json   # previous registry, auto-archived on each new run
```

Each finding carries its own lifecycle in place (`verdict` → `status` → `resolution`), so verification (Phase 3.5) and the later fix session update the same file rather than spawning new ones. Markdown is a **throwaway render** produced on demand to `/tmp` via `python3 gse-one/audit.py --render` — never persisted in the repo tree, so it can never diverge from the JSON.

**`audit.py` CLI standalone — deterministic markdown.** Invoked directly, the engine auto-saves its deterministic-only report to `_LOCAL/audits/audit-<ts>-v<version>.md` (+ a `latest.md` convenience copy). Use `--no-save` to disable, or `--save-to <path>` for an explicit location (e.g., CI artifact export).

`_LOCAL/` is gitignored, so audit history accumulates locally without ever reaching git. The retired pre-v0.75.0 multi-file output for the slash command (`audit-<ts>.md` / `latest.md` / `verify-*.md` / `reconciled`) is gone — its md/json divergence is exactly what the single-registry contract eliminates.

### What the audit covers (28 jobs, 6 categories)

**Category A — Single-file quality** *(2 jobs, non-directional)*
- `spec-file-quality` — internal quality of `gse-one-spec.md`
- `design-file-quality` — internal quality of `gse-one-implementation-design.md`

**Category B — Intra-layer uniformity** *(5 jobs, non-directional)*
- `activities-structure-uniformity` — all 24 activity skills follow their documented structural patterns
- `agents-structure-uniformity` — all 11 agents follow uniform skeleton
- `tools-quality-uniformity` — all Python tools (4 plugin tools + audit engine + catalog loader) follow SE standards
- `templates-completeness` — all ~28 templates valid + in MANIFEST
- `references-quality` — references/ docs fresh and self-contained

**Category C — Layer pair** *(1 job, bidirectional)*
- `spec-design-coherence` — design refines spec; may reveal spec improvements

**Category D — Horizontal clusters** *(11 jobs, mostly bidirectional)*
- `governance-cluster` — orchestrator + 16 principles + spec/design
- `deploy-cluster` — deploy activity + agent + refs + tools + templates + spec + design
- `sprint-lifecycle-cluster` — plan→reqs→design→preview→tests→produce→review→fix→deliver
- `state-management-cluster` — all state files + activities that read/write them
- `cross-cutting-cluster` — go/hug/learn/health/status
- `coach-pedagogy-cluster` — coach agent + pedagogy activities + profile
- `quality-assurance-cluster` — review+tests+produce+fix + 7 QA agents
- `delivery-compound-cluster` — deliver + compound + integrate
- `invocation-contract-consistency` — each agent's `Activated by:` contract matches real invocation steps in activities
- `distribution-channel-coherence` — installer + curl bootstrap + release workflow + README install/launcher prose stay coherent with the shipped reality
- `audit-system-self-coherence` — audit protocol + auditor role + catalog + Python engine + README audit section stay mutually coherent

**Category E — Strategic critique** *(4 jobs, bidirectional, severity `recommendation`)*
- `methodology-design-critique` — is the methodology the best design for its goals?
- `ai-era-adequacy-critique` — is it adapted to current LLM capabilities and risks?
- `user-value-critique` — does it deliver value to each user profile (solo/instructor/learner/forker)?
- `robustness-and-recovery-critique` — is it robust to failures?

**Category F — Distribution hygiene** *(5 deterministic jobs, run by `audit.py` — no LLM sub-agent)*
- `plugin-language-hygiene` — English-only distributed prose (marked multilingual zones excepted)
- `plugin-secret-leak-hygiene` — no keys, tokens, or credentials in the shipped plugin
- `plugin-personal-leak-hygiene` — no maintainer-personal paths or identities
- `plugin-debug-residue-hygiene` — no debug prints or dead branches in shipped code
- `plugin-runtime-path-integrity` — every `$(cat ~/.gse-one)/X` reference resolves against installed subpaths

### Catalog: `.claude/audit-jobs.json`

All 28 jobs are defined declaratively with explicit file lists, scopes, and checks. To add a job (e.g., when your fork adds a new subsystem), edit the catalog and validate:

```bash
python3 gse-one/audit_catalog.py --validate
python3 gse-one/audit_catalog.py --show deploy-cluster   # inspect one job
```

The next `/gse-meta-audit` invocation will automatically include any new job.

### Deterministic checks (Python engine — 12 coherence categories, plus the 5 Category F categories listed above and the `audit_layout` organization-hygiene check)

Complement the LLM jobs with fast syntactic/structural checks:

| # | Category | Examples |
|:-:|---|---|
| 1 | Version consistency | VERSION ↔ 3 manifests ↔ CHANGELOG latest |
| 2 | File integrity | `ACTIVITY_NAMES` + `SPECIALIZED_AGENTS` sources exist; no orphans |
| 3 | Plugin parity | Claude / Cursor / opencode counts match |
| 4 | Cross-file references | `/gse:X` mentions resolve |
| 5 | Numeric consistency | Spec "24 commands" = `len(ACTIVITY_NAMES)` |
| 6 | Link integrity | No dead `gse-one/...` paths |
| 7 | Git hygiene | No uncommitted `plugin/` |
| 8 | Python quality | Syntax OK; `@gse-tool` headers |
| 9 | Template schema | JSON + YAML valid; Dockerfiles have `ARG SOURCE_COMMIT` |
| 10 | TODO / FIXME scan | Open markers |
| 11 | Test coverage structural | Public functions have tests |
| 12 | Last-verified freshness | > 180 days flagged |

### Unified report structure

```
Part 1 — Coherence findings (Categories A-D)
  🔴 Errors       — contradictions, block release
  🟡 Warnings     — drifts, review
  🔵 Info         — passed checks + observations

Part 2 — Strategic recommendations (Category E)
  💡 Recommendations — per critique job, with impact level (high/medium/low)

Conclusion: ❌ errors | 🟡 warnings | 💡 recommendations | ✅ pass
```

Recommendations (Category E) are **proposals, not defects** — they never trigger CI exit codes. Warnings and errors do.

### When to run

- Before any release commit (catches coherence drift)
- After significant changes (new activity, agent, schema)
- In a fork, before proposing changes upstream (full audit)
- When planning a methodology evolution (use `--strategic-only`)
- In CI (use `--deterministic-only --fail-on error`, future)

### Fork inheritance

The `.claude/` directory at repo root is **included via `git clone`**. When you fork gensem, all maintainer tooling (`commands/gse-meta-audit.md`, `commands/gse-meta-audit-fix.md`, `commands/gse-release.md`, `agents/methodology-auditor.md`, `audit-jobs.json`, plus the minimal permission allowlist in `settings.json`) comes with your fork. No install step. Open your fork in Claude Code → `/gse-meta-audit` available.

The Python engine (`gse-one/audit.py` + `gse-one/audit_catalog.py`) also travels with the fork.

### Exit codes (CLI)

- `0` — all checks passed
- `1` — errors found (with `--fail-on error`)
- `2` — warnings or errors found (with `--fail-on warning`)
- `3` — not a GSE-One repository (context detection failed)

---

## Versioning

See [CHANGELOG.md](CHANGELOG.md) for version history.

To publish a new version:

1. Update the `VERSION` file at the repository root
2. Update `CHANGELOG.md`
3. Regenerate: `cd gse-one && python3 gse_generate.py --clean --verify`
4. Commit + tag: `git add . && git commit -m "feat: GSE-One vX.Y.Z" && git tag vX.Y.Z && git push origin main --tags`
