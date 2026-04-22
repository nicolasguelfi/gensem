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

## Agent archetypes

The 11 agents in `src/agents/` deliberately use **4 structural archetypes**. Differences reflect agent roles — don't force one-size-fits-all uniformity.

| Archetype | Agent(s) | Standard sections |
|---|---|---|
| **Identity** | `gse-orchestrator` | Role / Activated by / Perspective / Core Principles (P1-P16) / Skill activation / Sub-agent dispatch |
| **Reviewer** (output to `review.md` via `/gse:review`) | `architect`, `code-reviewer`, `security-auditor`, `requirements-analyst`, `devil-advocate`, `ux-advocate`, `test-strategist` | Role / Activated by / Perspective / Checklist / Output Format (RVW-NNN + `perspective:` + HIGH/MEDIUM/LOW) |
| **Operational** (multi-step workflow execution) | `deploy-operator` | Role / Activated by / Perspective / Required readings / Core Principles / Anti-patterns / Output Format |
| **Observational** (8-axis monitoring) | `coach` | Role / Activated by / Perspective / 8 axes / Invocation contract / Evaluation algorithm / Output Formats (plural) / Anti-spam / Recipes / Persistence |
| **Compliance** (real-time guardrail enforcement) | `guardrail-enforcer` | Role / Activated by / Perspective / Guardrail Tiers / Decision Tier Compliance / Checklist / Output Format (GUARD-NNN + EMERGENCY/HARD/SOFT) |

Common to all 11: YAML frontmatter with `name` + `description`; opening `**Role:**` + `**Activated by:**` lines; `## Perspective` section. Reviewer archetype agents output `RVW-NNN` findings with `perspective:` field (per spec §6.5) and the canonical 3-tier severity scale `HIGH / MEDIUM / LOW` (+ P15 escalation to CRITICAL). The Compliance archetype (guardrail-enforcer) uses a distinct format (`GUARD-NNN` + `EMERGENCY/HARD/SOFT` guardrail tiers) because its outputs are real-time action alerts, not artefact review findings — the tier labels carry action semantics (WARN / BLOCK / HALT) that would be lost in the severity scale.

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

### Pre-release backward-compatibility — not required (temporary rule)

As long as the GSE-One plugin is not yet distributed to public end users, **backward-compatibility is not a concern** for any methodology schema, state file format, or artefact structure. Concretely:

- Breaking schema changes in templates (`backlog.yaml`, `plan.yaml`, `status.yaml`, `checkpoint.yaml`, `profile.yaml`, learning notes, sprint docs, etc.) may be applied directly. No migration path, no deprecation window, no compatibility shim needed.
- Renaming or removing fields is acceptable. Existing downstream consumers (activities, tools, agents) are all in-tree and can be updated atomically with the schema change.
- Changing enum values (e.g., `origin`, `app_type`, `project_domain`, `status`) does not require preserving old values for legacy data.
- Restructuring principle titles, agent outputs, or activity workflows is permitted without retroactive adapters.

This rule **will be removed** once the plugin hits its first public release (distribution through Claude Code marketplace, Cursor marketplace, npm, etc.). After that release, standard SemVer compatibility rules apply: breaking changes require a major version bump and a documented migration guide.

**Why:** Pre-release iteration needs to be fast and unconstrained. Locking in an unripe schema creates permanent debt. Once users depend on the plugin, protection becomes mandatory. The cutoff is distribution, not an arbitrary date.

**When the rule expires, update CLAUDE.md:** remove this entire section and replace with the post-release compatibility policy (SemVer discipline, deprecation windows, migration tooling requirements).

### Files to keep in sync (all via generator)
- `src/activities/*.md` → `plugin/skills/*/SKILL.md` (Claude Code) + `plugin/commands/gse-*.md` (Cursor) + `plugin/opencode/skills/*/SKILL.md` + `plugin/opencode/commands/gse-*.md`
- `src/agents/gse-orchestrator.md` → `plugin/agents/gse-orchestrator.md` + `plugin/rules/gse-orchestrator.mdc` + `plugin/opencode/AGENTS.md` (wrapped in `<!-- GSE-ONE START/END -->` markers)
- `src/agents/<specialized>.md` → `plugin/agents/*.md` + `plugin/opencode/agents/*.md` (with `mode: subagent` injected)
- `plugin/hooks/hooks.claude.json` → `plugin/opencode/plugins/gse-guardrails.ts` (transpiled)
- The orchestrator body, the `.mdc` rule body, and the opencode `AGENTS.md` block body are all verified identical by `--verify`.
- Changes in spec should be reflected in design doc changelog and vice versa.

### Cross-reference convention — "number + name"

Cross-references to sections, steps, or numbered artefacts within the corpus (spec, design, activities, agents, principles, CLAUDE.md, CHANGELOG) MUST include both the numeric identifier AND the section/step name. Example forms:

- ✅ `spec §14.3 Step 1.6 — "Dependency vulnerability check"` (number + name)
- ✅ `see Step 8 — Cleanup Backup Tags` (step number + title)
- ✅ `see §11.1 Generation Steps for the generator step table` (section number + heading)
- ✅ `per §P14` (acceptable when the principle is being cited by its canonical ID — the principle ID itself is a stable name)
- ❌ `spec §14.3 Step 2.5` (number only — breaks if sections are renumbered)
- ❌ `see Step 10` (number only, for a step that doesn't exist — actual example of a broken ref caught by audit)

**Why:** Section numbers are unstable. Inserting a new section shifts all downstream numbering, silently breaking every cross-reference to shifted sections. Section names are anchored to content and change far less often. The "number + name" form gives the reader dual resolution: if the number drifts, the name still resolves; if the name changes, the number still hints at the location.

**How to apply in practice:**
- When creating a new cross-reference, use the full "number + name" form.
- When modifying existing prose that contains number-only references, upgrade them opportunistically to the new form (within your diff scope — do not create unbounded sweep diffs).
- The task `P-NAMED-REFS` tracks a dedicated retroactive sweep across the whole corpus; individual propositions need not close all legacy references.

**Edge cases:**
- For principles (P1-P16), the principle ID itself is a stable name — `§P14` alone is acceptable because "P14" is the name (the principle's canonical identifier). Adding the descriptive title is still encouraged: `§P14 — Knowledge Transfer`.
- Principle titles follow a separate convention (spec carries the full descriptive title; orchestrator and principle source file carry the short form). See task `PRINCIPLE-TITLES` for the convention details pending addition to CLAUDE.md.
- For internal steps within a single document (e.g., "see Step 3" when the current document has a Step 3), the numeric form alone is acceptable — the local scope makes the reference unambiguous.

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

### Communication style (development sessions)

When proposing changes, applying fixes, or explaining methodology concepts during interactive sessions with the user, follow these two rules.

**Rule 1 — Pedagogical phrasing, not cryptic jargon.** The GSE-One methodology introduces many internal terms (TASK, REVIEW, FIX, `workflow.pending`, RVW-NNN, DEC-NNN, LRN-NNN, axes, moments, archetypes, tiers, Gate, Inform, backlog pool, sprint freeze, etc.). When writing propositions, explanations, or analyses, do NOT chain these terms as if the reader has mastered them. Instead:
- Introduce each term with a brief parenthetical reminder of its meaning the first time it appears in a document (e.g., "the coach (an AI sub-agent observing the collaboration)" rather than just "the coach").
- Re-introduce terms periodically if the document is long, not just once at the top.
- Accept longer paragraphs for better pedagogical clarity — density is not a virtue here.
- Counter-example (bad, too compressed): *"The methodology defines a TASK state-machine and a conditional FIX insertion rule into workflow.pending after REVIEW."*
- Better phrasing (pedagogical): *"Each task of the project (called TASK in the vocabulary) has a life-cycle. After the code-review phase (called REVIEW, which produces a list of problems), the methodology may automatically add a correction phase (called FIX) into the list of activities still to be done for the current sprint — this list of pending activities is stored in a structured field named `workflow.pending` inside `plan.yaml`."*

**Rule 2 — One question = one default answer explicitly stated.** When asking the user to validate a proposition, do NOT write composite questions with multiple sub-points bundled. Each question must:
- Carry a single proposed action.
- State explicitly the default that will be applied if the user says "ok" (e.g., "Si tu dis ok, c'est X qui sera appliqué.").
- Optionally mention alternatives as a side note, not as another question to answer.
- Counter-example (bad, composite): *"Pour la modification X, es-tu d'accord avec (a) le positionnement, (b) le nombre de sous-étapes, (c) le choix du tag ?"*
- Better phrasing: *"Q_x — Je propose [action concrète]. Si tu dis ok, c'est [action exacte] qui sera appliqué. Alternative disponible : [option]."*

**Why these rules.** The user works with the methodology from multiple sessions and machines, sometimes coming back cold. Cryptic phrasing forces them to reload context mentally; pedagogical phrasing preserves flow. Composite questions hide decisions — the user might approve the proposition intending to validate point (a) while point (c) was also smuggled in. Single-default questions make consent explicit and auditable.

## Language

The user communicates in French. Respond in French for conversation, English for code/commits.
