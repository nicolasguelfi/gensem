# GSE-One Development Guide

## Project overview

This is the **gensem** repository — the source for the GSE-One plugin, an AI engineering companion for structured SDLC management. It produces a single plugin deployable on both Claude Code and Cursor.

## Repository structure

- `gse-one/src/` — Single source of truth (principles, activities, agents, templates)
- `gse-one/plugin/` — Generated deployable directory (NEVER edit directly)
- `gse-one/plugin/tools/` — Python tool scripts (dashboard, etc.) with `# @gse-tool` headers
- `gse-one/gse_generate.py` — Generator: rebuilds `plugin/` from `src/`
- `install.py` — Cross-platform installer (Claude Code + Cursor)
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
- `src/activities/*.md` → `plugin/skills/*/SKILL.md` (Claude Code) + `plugin/commands/gse-*.md` (Cursor)
- `src/agents/gse-orchestrator.md` → `plugin/agents/gse-orchestrator.md` + `plugin/rules/gse-orchestrator.mdc`
- Changes in spec should be reflected in design doc changelog and vice versa.

## Language

The user communicates in French. Respond in French for conversation, English for code/commits.
