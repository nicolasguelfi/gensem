# GSE-One Development Guide

## Project overview

This is the **gensem** repository — the source for the GSE-One plugin, an AI engineering companion for structured SDLC management. It produces a single plugin deployable on Claude Code, Cursor, and opencode.

## Repository structure

- `gse-one/src/` — Single source of truth (principles, activities, agents, templates)
- `gse-one/plugin/` — Generated deployable directory (NEVER edit directly)
- `gse-one/plugin/tools/` — Python tool scripts (dashboard, etc.) with `# @gse-tool` headers
- `gse-one/gse_generate.py` — Generator: rebuilds `plugin/` from `src/`
- `install.py` — Cross-platform installer (Claude Code + Cursor + opencode)
- `gse-one-spec.md` — Methodology specification
- `gse-one-implementation-design.md` — Implementation design document
- `assets/images/` — Branding assets (logos, banners)
- `_LOCAL/` — Local-only files (gitignored via `/_*/` pattern)
- `VERSION` — Single version source, read by generator and installer

## Critical rules

### Build pipeline — mandatory for every commit to main
Every commit to main MUST follow this full pipeline:
1. **Bump** `VERSION` (patch for fixes, minor for features)
2. **Update `CHANGELOG.md`** — add a `## [X.Y.Z] - YYYY-MM-DD` block at the top with `### Added/Changed/Fixed/Removed` sections per Keep a Changelog convention (plus an optional "Layers impacted" line)
3. **Generate** — `cd gse-one && python3 gse_generate.py --verify`
4. **Add all** — VERSION, CHANGELOG.md, manifests, all regenerated files in `plugin/`
5. **Commit** — with `feat:`, `fix:`, `docs:`, or `chore:` prefix, and `vX.Y.Z —` pattern in the subject
6. **Push** — `git push origin main`

Never skip a step. Never commit without regenerating. Never push without bumping. Never release a version without a matching CHANGELOG entry.

- Never edit files in `gse-one/plugin/` directly except `plugin/tools/` — the generator overwrites everything else from `src/`.
- Changes to activities go in `src/activities/`, changes to agents go in `src/agents/`.
- The orchestrator and .mdc rule are generated from the same source — body parity is verified automatically.

### Tool architecture
- Tools live in `plugin/tools/` and are resolved at runtime via the `~/.gse-one` registry file.
- `install.py` writes `~/.gse-one` (absolute plugin path) on install, removes it on uninstall.
- Skills execute tools via: `python3 "$(cat ~/.gse-one)/tools/dashboard.py"` — agents must never read+rewrite tool content.
- Each tool has a `# @gse-tool <name> <version>` header on line 2.

### Versioning
- Bump `VERSION` file, then run the generator — it propagates to both plugin.json manifests.
- Commit style: `feat:`, `fix:`, `docs:` prefixes. Check recent `git log` for conventions.

### Files to keep in sync (all via generator)
- `src/activities/*.md` → `plugin/skills/*/SKILL.md` (Claude Code) + `plugin/commands/gse-*.md` (Cursor) + `plugin/opencode/skills/*/SKILL.md` + `plugin/opencode/commands/gse-*.md`
- `src/agents/gse-orchestrator.md` → `plugin/agents/gse-orchestrator.md` + `plugin/rules/gse-orchestrator.mdc` + `plugin/opencode/AGENTS.md` (wrapped in `<!-- GSE-ONE START/END -->` markers)
- `src/agents/<specialized>.md` → `plugin/agents/*.md` + `plugin/opencode/agents/*.md` (with `mode: subagent` injected)
- `plugin/hooks/hooks.claude.json` → `plugin/opencode/plugins/gse-guardrails.ts` (transpiled)
- The orchestrator body, the `.mdc` rule body, and the opencode `AGENTS.md` block body are all verified identical by `--verify`.
- Changes in spec should be reflected in design doc changelog and vice versa.

### Memory policy — in-repo only
Any project convention, rule, preference, or decision that Claude must remember across sessions for this project MUST be recorded in a versioned file in this repo — typically this `CLAUDE.md`, or another markdown doc under source control. Do NOT write such information to Claude's per-machine auto-memory (`~/.claude/projects/<hash>/memory/`).

**Why:** The user works on this project from multiple machines via Dropbox. Files under `$HOME` do not travel; only the git-versioned repo does. Auto-memory entries are invisible to collaborators, lost on a fresh machine, and fragment the source of truth.

**How to apply:** When the user gives durable feedback or establishes a convention, update `CLAUDE.md` (or the appropriate in-repo doc) via the full build pipeline. Never silently save to auto-memory. If auto-memory entries are found for this project on any machine, they should be migrated into `CLAUDE.md` and deleted.

### Repo-level tooling (`.claude/`)

The `.claude/` directory at the repo root contains **maintainer tools** that are **not** part of the distributed plugin:

- `.claude/commands/gse-audit.md` — `/gse-audit` slash command for methodology coherence audits
- `.claude/agents/methodology-auditor.md` — agent adopted during `/gse-audit`

These are inherited automatically when someone clones gensem (or a fork of it). They are Claude Code-only (v1). The Python engine at `gse-one/audit.py` provides CLI access independent of the editor.

**Do not move these tools into `gse-one/plugin/`** — that would distribute them to all end users of GSE-One, polluting the methodology for people who only use the plugin without forking. Maintainer tools live at `.claude/` (repo-local) or `gse-one/` (e.g., `audit.py` alongside `gse_generate.py`), never in `gse-one/plugin/`.

## Language

The user communicates in French. Respond in French for conversation, English for code/commits.
