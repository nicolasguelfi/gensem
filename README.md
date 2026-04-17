<h1 align="center">GSE-One</h1>
<h2 align="center">Built by AI.<br>Governed by Humans.</h2>

GSE-One is an AI engineering companion that brings structured software development lifecycle (SDLC) management to coding agents. It works as a plugin for **Claude Code** and **Cursor**, guiding projects through requirements, design, testing, production, review, and knowledge transfer — with adaptive risk analysis and methodology guardrails.

<p align="center">
  <img src="assets/images/logo-gse-geni-with-shield-landscape_4x_slogan.png" width="700" alt="GSE-One — Built by AI, Governed by Humans">
</p>

---

## Table of Contents

1. [Key Features](#key-features)
2. [Quick Start](#quick-start)
3. [Mono-plugin Architecture](#mono-plugin-architecture)
4. [Develop and Generate](#develop-and-generate)
5. [Publish the Plugin](#publish-the-plugin)
6. [Command Reference](#command-reference)
7. [Versioning](#versioning)

---

## Key Features

- **23 commands** covering the full SDLC — from onboarding (`/gse:hug`) to capitalization (`/gse:compound`)
- **3 modes** — Micro, Lightweight, Full — auto-selected by complexity assessment, user-overridable
- **Adaptive risk analysis** — 3-tier decision system (Auto / Gate / Hard) calibrated to user expertise
- **Unified backlog** — single task tracking with git state per-task
- **8-dimension health dashboard** — generated HTML with radar chart, kanban, lifecycle checklist
- **AI integrity guardrails** — confidence levels, verification gates, devil's advocate agent
- **Cross-platform** — one plugin, identical methodology on Claude Code and Cursor

---

## Quick Start

### Option A — Cursor

```bash
# Set up the workspace
mkdir gse-quick-start && cd gse-quick-start
mkdir my-project
git clone https://github.com/nicolasguelfi/gensem.git

# Install GSE-One (local mode — everything stays in the project)
cd gensem
python3 install.py --platform cursor --mode no-plugin --project-dir ../my-project

# Initialize and launch your project
cd ../my-project && git init
cursor .
```

In Cursor, type: `/go`

### Option B — Claude Code

```bash
# Set up the workspace
mkdir gse-quick-start && cd gse-quick-start
mkdir my-project
git clone https://github.com/nicolasguelfi/gensem.git

# Install GSE-One (local mode — everything stays in the project)
cd gensem
python3 install.py --platform claude --mode no-plugin --project-dir ../my-project

# Initialize and launch your project
cd ../my-project && git init
claude
```

In Claude Code, type: `/go`

> **Note:** The `no-plugin` mode copies all GSE-One artifacts into your project's `.cursor/` or `.claude/` directory — nothing is installed globally. The only file created outside the project is `~/.gse-one` (1 line containing the plugin path, removed by `python3 install.py --uninstall`).
>
> In `no-plugin` mode, commands are unprefixed: `/go`, `/plan`, `/reqs`... instead of `/gse:go`, `/gse:plan`, `/gse:reqs`.

### Plugin mode (alternative)

To install via the platform's plugin system (prefixed commands `/gse:*`):

```bash
# Cursor (local plugin)
python3 install.py --platform cursor --mode plugin

# Claude Code (user-scoped plugin)
python3 install.py --platform claude --mode plugin --scope user

# Interactive (the installer guides you)
python3 install.py
```

---

## Mono-plugin Architecture

GSE-One uses a **single deployable directory** (`plugin/`) that works on both platforms:

```
gse-one/
├── src/                              # Single source of truth
│   ├── principles/                   # 16 principles (P1-P16)
│   ├── activities/                   # 23 activity definitions → skills
│   ├── agents/                       # 9 agents (8 specialized + orchestrator)
│   └── templates/                    # 19 templates
│
├── plugin/                           # Deployable directory
│   ├── .claude-plugin/plugin.json    # Claude Code manifest
│   ├── .cursor-plugin/plugin.json    # Cursor manifest
│   ├── skills/                       # 23 skills (shared)
│   ├── agents/                       # 9 agents (shared)
│   ├── templates/                    # 19 templates (shared)
│   ├── tools/                        # Python tools (dashboard, etc.)
│   ├── rules/gse-orchestrator.mdc    # Cursor only
│   ├── hooks/                        # Platform-specific hooks
│   └── settings.json                 # Claude only
│
└── install.py                        # Cross-platform installer
```

**Shared files:** skills, agents, templates, tools — single copy, zero divergence.
**Platform-specific:** manifests, hooks, settings, rules — generated as equivalent pairs.

---

## Develop and Generate

### Edit the Sources

All changes are made in `src/`. Never modify `plugin/` directly — it is regenerated.

### Local development setup (recommended)

Create a virtual environment and install dev dependencies:

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dev dependencies:

```bash
python -m pip install -U pip
pip install -r requirements-dev.txt
```

### Verify changes (local)

```bash
cd gse-one/
python gse_generate.py --clean --verify
cd ..
pytest -q
```

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
| `--platform` | `claude` \| `cursor` \| `both` | *(interactive)* | Target platform |
| `--mode` | `plugin` \| `no-plugin` | *(interactive)* | `plugin` (recommended) or `no-plugin` (copies artifacts directly) |
| `--scope` | `project` \| `local` \| `user` | `project` | Claude Code plugin scope only |
| `--project-dir` | path | current directory | No-plugin mode only |
| `--uninstall` | *(flag)* | `false` | Remove GSE-One |

#### Examples

```bash
# Claude Code — plugin, project scope
python3 install.py --platform claude --mode plugin --scope project

# Cursor — plugin (global)
python3 install.py --platform cursor --mode plugin

# Both platforms at once
python3 install.py --platform both --mode plugin --scope user

# Non-plugin mode
python3 install.py --platform claude --mode no-plugin --project-dir /path/to/myproject

# Uninstall
python3 install.py --uninstall --platform claude --mode plugin
```

> **Windows:** If `python3` is not recognized, use `python` instead.

#### Marketplace (when available)

Not yet operational. After approval:
- Claude Code: `claude plugin install gse-one`
- Cursor: search "gse-one" in `/add-plugin`

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
python3 install.py --platform claude --mode plugin --scope project

# Uninstall
python3 install.py --uninstall --platform claude --mode plugin
```

### Verification

Type in your coding agent:

```
/gse:go
```

The GSE-One agent should respond, detect the project state and propose the next activity.

---

## Versioning

See [CHANGELOG.md](CHANGELOG.md) for version history.

To publish a new version:

1. Update the `VERSION` file at the repository root
2. Update `CHANGELOG.md`
3. Regenerate: `cd gse-one && python3 gse_generate.py --clean --verify`
4. Commit + tag: `git add . && git commit -m "feat: GSE-One vX.Y.Z" && git tag vX.Y.Z && git push origin main --tags`
