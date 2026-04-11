# GSE-One — Plugin Publication Guide

This repository contains the specification (`gse-one-spec-v0.8.md`), the design document (`gse-one-implementation-design-v0.8.md`) and the complete plugin implementation (`gse-one/`).

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
│   ├── activities/                   # 22 skills SKILL.md
│   ├── agents/                       # 9 agents (8 specialized + orchestrator)
│   └── templates/                    # 15 templates
│
├── plugin/                           # Deployable directory (52 files)
│   ├── .claude-plugin/plugin.json    # Claude Code manifest
│   ├── .cursor-plugin/plugin.json    # Cursor manifest
│   ├── skills/                       # 22 skills (shared)
│   ├── agents/                       # 9 agents (shared)
│   ├── templates/                    # 15 templates (shared)
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

### For Claude Code

GSE-One adds 22 `/gse:*` commands. Choose the installation scope based on where you want them available:

| Scope | When active | Command |
|-------|------------|---------|
| **Project** | Only inside a specific project directory | `claude plugin install ~/gensem/gse-one/plugin --scope project` |
| **Project (personal)** | Same, but not committed to git | `claude plugin install ~/gensem/gse-one/plugin --scope local` |
| **Global** | Every session, every directory | `claude plugin install ~/gensem/gse-one/plugin --scope user` |
| **One-time** | Current terminal session only | `claude --plugin-dir ~/gensem/gse-one/plugin/` |

> **Tip:** Use `--scope project` or `--scope local` to keep your `/` menu clean when working with multiple plugins. Reserve `--scope user` for plugins you need everywhere.

#### Official Anthropic Marketplace (when available)

1. Submit via [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit) or [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit)
2. Plugin path: `gse-one/plugin`
3. After approval: `claude plugin install gse-one`

### For Cursor

> **Note:** Cursor does not currently support project-scoped plugin installation. Local plugins are installed globally via `~/.cursor/plugins/`.

```bash
mkdir -p ~/.cursor/plugins/local
ln -sf ~/gensem/gse-one/plugin ~/.cursor/plugins/local/gse-one
```

The plugin is active in all projects opened in Cursor. Using a symlink keeps it in sync with the cloned repository.

#### Cursor Marketplace (when available)

1. Submit via [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish)
2. The plugin already contains `.cursor-plugin/plugin.json` with the correct paths
3. After approval: users install via `/add-plugin`

---

## 4. Command Reference

### Developer

```bash
# Regenerate after modification
python3 gse_generate.py --clean --verify

# Publish a new version
# 1. Update version in gse_generate.py (VERSION constant)
# 2. Regenerate
python3 gse_generate.py --clean --verify
# 3. Commit + tag + push
git add .
git commit -m "feat: GSE-One v0.8.1 — description"
git tag v0.8.1
git push origin main --tags
```

### Claude Code User

```bash
# Project-scoped install (recommended)
cd /path/to/your-project
claude plugin install ~/gensem/gse-one/plugin --scope project

# Global install (available everywhere)
claude plugin install ~/gensem/gse-one/plugin --scope user

# One-time session test
claude --plugin-dir ~/gensem/gse-one/plugin/
```

### Cursor User

```bash
# Global install (symlink)
mkdir -p ~/.cursor/plugins/local
ln -sf ~/gensem/gse-one/plugin ~/.cursor/plugins/local/gse-one
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

1. Update the `VERSION` constant in `gse_generate.py`
2. Regenerate: `python3 gse_generate.py --clean --verify`
3. Update `CHANGELOG.md`
4. Commit + tag: `git tag vX.Y.Z && git push origin main --tags`
