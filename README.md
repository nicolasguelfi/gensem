<h1 align="center">GSE-One</h1>
<h2 align="center">Built by AI.<br>Governed by Humans.</h2>

GSE-One is an AI engineering companion that brings structured software development lifecycle (SDLC) management to coding agents. It works as a plugin for **Claude Code**, **Cursor**, and **opencode**, guiding projects through requirements, design, testing, production, review, and knowledge transfer — with adaptive risk analysis and methodology guardrails.

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
- **Cross-platform** — one plugin, identical methodology on Claude Code, Cursor, and opencode

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

### Option C — opencode

See [INSTALL-OPENCODE.md](INSTALL-OPENCODE.md) for the full opencode quickstart.

```bash
# Set up the workspace
mkdir gse-quick-start && cd gse-quick-start
mkdir my-project
git clone https://github.com/nicolasguelfi/gensem.git

# Install GSE-One into the project's .opencode/
cd gensem
python3 install.py --platform opencode --mode no-plugin --project-dir ../my-project

# Launch opencode in the project
cd ../my-project && git init
opencode
```

In opencode, type: `/gse-go`.

> **Note (git init):** The `git init` step above creates a fresh, independent repository for YOUR project inside `my-project/` — it is distinct from the `.git/` folder inside the `gensem/` clone, which tracks the plugin source. The two repositories do not interact. If this is your first time using git on this machine, GSE-One will help you configure your git identity (name + email) automatically the first time it creates a commit — no prerequisite `git config` needed.

### Plugin mode (alternative)

To install via the platform's plugin system (prefixed commands `/gse:*` on Claude, `/gse-*` on Cursor/opencode):

```bash
# Cursor (local plugin)
python3 install.py --platform cursor --mode plugin

# Claude Code (user-scoped plugin)
python3 install.py --platform claude --mode plugin --scope user

# opencode (global — ~/.config/opencode/)
python3 install.py --platform opencode --mode plugin

# All three at once (user/global scope)
python3 install.py --platform all --mode plugin --scope user

# Interactive (the installer guides you)
python3 install.py
```

---

## Mono-plugin Architecture

GSE-One uses a **single deployable directory** (`plugin/`) that works on all three platforms:

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
│   ├── skills/                       # 23 skills (shared, with name: field)
│   ├── commands/                     # 23 /gse-<name>.md (Cursor)
│   ├── agents/                       # 9 agents (shared)
│   ├── templates/                    # 19 templates (shared)
│   ├── tools/                        # Python tools (dashboard, etc.)
│   ├── rules/gse-orchestrator.mdc    # Cursor only
│   ├── hooks/                        # Platform-specific hooks
│   ├── settings.json                 # Claude only
│   └── opencode/                     # opencode subtree
│       ├── skills/                   # 23 skills (name: injected)
│       ├── commands/                 # 23 /gse-<name>.md
│       ├── agents/                   # 8 specialized (mode: subagent)
│       ├── plugins/gse-guardrails.ts # Native TS guardrails plugin
│       ├── AGENTS.md                 # Orchestrator body (markered)
│       └── opencode.json             # Default permissions
│
└── install.py                        # Cross-platform installer (3 platforms)
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
| `--platform` | `claude` \| `cursor` \| `opencode` \| `both` \| `all` | *(interactive)* | Target platform (`both` = claude+cursor, `all` = all three) |
| `--mode` | `plugin` \| `no-plugin` | *(interactive)* | `plugin` (recommended) or `no-plugin` (copies artifacts directly) |
| `--scope` | `project` \| `local` \| `user` | `project` | Claude Code plugin scope only (ignored by Cursor/opencode) |
| `--project-dir` | path | current directory | No-plugin mode only |
| `--uninstall` | *(flag)* | `false` | Remove GSE-One |

#### Examples

```bash
# Claude Code — plugin, project scope
python3 install.py --platform claude --mode plugin --scope project

# Cursor — plugin (global)
python3 install.py --platform cursor --mode plugin

# opencode — plugin (global, ~/.config/opencode/)
python3 install.py --platform opencode --mode plugin

# opencode — non-plugin (project .opencode/)
python3 install.py --platform opencode --mode no-plugin --project-dir /path/to/myproject

# Both Claude + Cursor
python3 install.py --platform both --mode plugin --scope user

# All three platforms at once
python3 install.py --platform all --mode plugin --scope user

# Non-plugin mode (Claude)
python3 install.py --platform claude --mode no-plugin --project-dir /path/to/myproject

# Uninstall
python3 install.py --uninstall --platform claude --mode plugin
```

> **Windows:** If `python3` is not recognized, use `python` instead.

#### Marketplace (when available)

Not yet operational. After approval:
- Claude Code: `claude plugin install gse-one`
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
