# GSE-One — Plugin Publication Guide

This repository contains the specification (`gse-one-spec.md`), the design document (`gse-one-implementation-design.md`) and the complete plugin implementation (`gse-one/`). All three share the same version number, defined in the `VERSION` file at the repository root.

This guide describes all the steps to publish the GSE-One plugin and make it installable by Claude Code and Cursor users.

---

## Table of Contents

1. [Mono-plugin Architecture](#1-mono-plugin-architecture)
2. [Develop and Generate](#2-develop-and-generate)
3. [Publish the Plugin](#3-publish-the-plugin)
4. [Command Reference](#4-command-reference)

---

## 1. Mono-plugin Architecture

GSE-One uses a **single deployable directory** (`plugin/`) that works on both platforms:

```
gse-one/
├── src/                              # Single source of truth (62 files)
│   ├── principles/                   # 16 principles (P1-P16)
│   ├── activities/                   # 23 activity definitions, each generated as a skill
│   ├── agents/                       # 9 agents (8 specialized + orchestrator)
│   └── templates/                    # 19 templates
│
├── plugin/                           # Deployable directory (57 files)
│   ├── .claude-plugin/plugin.json    # Claude Code manifest
│   ├── .cursor-plugin/plugin.json    # Cursor manifest
│   ├── skills/                       # 23 skills (shared)
│   ├── agents/                       # 9 agents (shared)
│   ├── templates/                    # 19 templates (shared)
│   ├── rules/000-gse-methodology.mdc # Cursor only (ignored by Claude)
│   ├── hooks/hooks.claude.json       # Claude Code format
│   ├── hooks/hooks.cursor.json       # Cursor format
│   └── settings.json                 # Claude only (ignored by Cursor)
│
├── marketplace/
│   └── .claude-plugin/marketplace.json
│
└── gse_generate.py                   # Generator: src/ → plugin/
```

**Shared files (46):** skills, agents, templates — single copy, zero divergence.
**Platform-specific files (6):** 2 manifests + 2 hooks + 1 settings + 1 .mdc — generated as equivalent pairs.

---

## 2. Develop and Generate

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
2. Generates the orchestrator (`agents/gse-orchestrator.md`) and the Cursor rule (`rules/000-gse-methodology.mdc`) from the **same source** — verifies that the body is identical
3. Generates the 2 hooks (Claude PascalCase / Cursor camelCase) from the same commands
4. Generates the 2 manifests and `settings.json`

### Create the GitHub Repository

```bash
cd gse-one/
git init
git add .
git commit -m "feat: GSE-One v0.8.0 — initial release"
gh repo create gse-one/gse-one --public --source=. --push
```

> **Important:** Update the `repository` field in `plugin/.claude-plugin/plugin.json`, `plugin/.cursor-plugin/plugin.json` and `marketplace/.claude-plugin/marketplace.json` with the actual repository URL.

---

## 3. Publish the Plugin

Plugin visibility depends entirely on the distribution method chosen and the GitHub repository visibility:

| Method | Visibility | Prerequisites |
|--------|-----------|---------------|
| A — Local test | You only, on your machine | None |
| B — GitHub distribution (private repo) | You + invited collaborators | Private GitHub repo |
| B — GitHub distribution (public repo) | Anyone with the link | Public GitHub repo |
| C — Official marketplace | Everyone (public catalog) | Submission and approval by Anthropic/Cursor |

> **Important:** As long as the GitHub repository remains **private**, no one can view the code or install the plugin without being explicitly invited as a collaborator. Method B with a private repo is suitable for personal use or small teams.

### Install the plugin

Run the interactive installer (works on macOS, Linux, Windows):

```bash
python3 install.py
```

The installer detects your environment and guides you through platform selection (Claude Code, Cursor, or both), installation mode (plugin or non-plugin), and scope (project, personal, global).

For non-interactive or scripted installation, use the CLI options described below.

#### `install.py` options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| *(no flags)* | — | — | **Interactive mode** — the installer detects your environment and guides you step by step |
| `--platform` | `claude` \| `cursor` \| `both` | *(interactive)* | Target platform. `both` installs on Claude Code and Cursor in one run |
| `--mode` | `plugin` \| `no-plugin` | *(interactive)* | **plugin**: uses the platform's plugin system (recommended). **no-plugin**: copies artifacts directly into `.claude/` or `.cursor/` (fallback if plugin system is unavailable) |
| `--scope` | `project` \| `local` \| `user` | `project` | **Claude Code plugin scope only** (ignored for Cursor). `project`: visible to all users of the project (committed to git). `local`: project-scoped but gitignored. `user`: global, applies to all projects for this user |
| `--project-dir` | path | current directory | **no-plugin mode only**. The project directory where artifacts are installed. If the directory does not exist, the installer proposes to create it |
| `--uninstall` | *(flag)* | `false` | Remove GSE-One from the specified platform and mode |

#### Examples

```bash
# Interactive (recommended for first install)
python3 install.py

# Claude Code — plugin, project scope
python3 install.py --platform claude --mode plugin --scope project

# Claude Code — plugin, global (all projects)
python3 install.py --platform claude --mode plugin --scope user

# Claude Code — plugin, gitignored
python3 install.py --platform claude --mode plugin --scope local

# Cursor — plugin (global, copied to ~/.cursor/plugins/)
python3 install.py --platform cursor --mode plugin

# Both platforms at once
python3 install.py --platform both --mode plugin --scope user

# Non-plugin mode (copy to .claude/ in a specific project)
python3 install.py --platform claude --mode no-plugin --project-dir /path/to/myproject

# Uninstall — Claude Code plugin
python3 install.py --uninstall --platform claude --mode plugin

# Uninstall — Cursor non-plugin from a specific project
python3 install.py --uninstall --platform cursor --mode no-plugin --project-dir /path/to/myproject
```

> **Windows:** If `python3` is not recognized, use `python` instead.

#### Marketplace (when available)

Not yet operational. After approval:
- Claude Code: `claude plugin install gse-one`
- Cursor: search "gse-one" in `/add-plugin`

---

## 4. Command Reference

### Developer

```bash
# Regenerate plugin after modifying src/
cd gse-one/
python3 gse_generate.py --clean --verify

# Publish a new version
# 1. Update VERSION file at repo root
# 2. Update CHANGELOG.md
# 3. Regenerate
python3 gse_generate.py --clean --verify
# 4. Commit + tag + push
git add .
git commit -m "feat: GSE-One vX.Y.Z — description"
git tag vX.Y.Z
git push origin main --tags
```

> **Windows:** If `python3` is not recognized, use `python` instead.

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

Regardless of the method, type:

```
/gse:go
```

The GSE-One agent should respond, detect the project state and propose the next activity.

---

## Versioning

See [CHANGELOG.md](CHANGELOG.md) for version history.

To publish a new version:

1. Update the `VERSION` file at the repository root
2. Update `CHANGELOG.md` (include "Layers impacted: spec, design, production" as applicable)
3. Regenerate: `cd gse-one && python3 gse_generate.py --clean --verify`
4. Commit + tag: `git add . && git commit -m "feat: GSE-One vX.Y.Z" && git tag vX.Y.Z && git push origin main --tags`
