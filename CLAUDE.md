# GSE-One Development Guide

## Project overview

This is the **gensem** repository — the source for the GSE-One plugin, an AI engineering companion for structured SDLC management. It produces a single plugin deployable on Claude Code, Cursor, opencode, Codex CLI, and Gemini CLI.

## Repository structure

- `gse-one/src/` — Single source of truth (principles, activities, agents, templates)
- `gse-one/plugin/` — Generated deployable directory (NEVER edit directly)
- `gse-one/plugin/tools/` — Python tool scripts (dashboard, etc.) with `# @gse-tool` headers
- `gse-one/gse_generate.py` — Generator: rebuilds `plugin/` from `src/`
- `install.py` — Cross-platform installer (Claude Code + Cursor + opencode + Codex CLI + Gemini CLI)
- `gse-one-spec.md` — Methodology specification
- `gse-one-implementation-design.md` — Implementation design document
- `assets/images/` — Branding assets (logos, banners)
- `_LOCAL/` — Local-only files (gitignored via `/_*/` pattern)
- `VERSION` — Single version source, read by generator and installer

## Agent archetypes

The 11 agents in `src/agents/` (10 spawnable + 1 cross-cutting rule reference, guardrail-enforcer) deliberately use **5 structural archetypes** (a 12th file, `gse-orchestrator-lite.md`, is a condensed Identity-archetype derivative used only as the Codex `AGENTS.md` under its 32 KiB cap — see "Files to keep in sync" — not a distinct spawnable role). Differences reflect agent roles — don't force one-size-fits-all uniformity.

| Archetype | Agent(s) | Standard sections |
|---|---|---|
| **Identity** | `gse-orchestrator` | Role / Activated by / Perspective / Core Principles (P1-P16) / Command Reference / Orchestration Decision Tree / Sprint Plan Maintenance |
| **Reviewer** (output to `review.md` via `/gse:review`) | `architect`, `code-reviewer`, `security-auditor`, `requirements-analyst`, `devil-advocate`, `ux-advocate`, `test-strategist` | Role / Activated by / Perspective / Checklist / Output Format (RVW-NNN + `perspective:` + HIGH/MEDIUM/LOW) |
| **Operational** (multi-step workflow execution) | `deploy-operator` | Role / Activated by / Perspective / Required readings / Core Principles / Anti-patterns / Output Format |
| **Observational** (8-axis monitoring) | `coach` | Role / Activated by / Perspective / 8 axes / Invocation contract / Evaluation algorithm / Output Formats (plural) / Anti-spam / Recipes / Persistence |
| **Compliance** (real-time guardrail enforcement) | `guardrail-enforcer` | Role / Activated by / Perspective / Guardrail Tiers / Decision Tier Compliance / Checklist / Output Format (GUARD-NNN + EMERGENCY/HARD/SOFT) |

Common to all 11 agents: YAML frontmatter with `name` + `description`; opening `**Role:**` + `**Activated by:**` lines; `## Perspective` section. Reviewer archetype agents output `RVW-NNN` findings with `perspective:` field (per spec §6.5) and the canonical 3-tier severity scale `HIGH / MEDIUM / LOW` (+ P15 escalation to CRITICAL). The Compliance archetype (guardrail-enforcer) uses a distinct format (`GUARD-NNN` + `EMERGENCY/HARD/SOFT` guardrail tiers) because its outputs are real-time action alerts, not artefact review findings — the tier labels carry action semantics (WARN / BLOCK / HALT) that would be lost in the severity scale.

## Critical rules

### Build pipeline — mandatory for every commit to main
Every commit to main MUST follow this full pipeline:
1. **Bump** `VERSION` — **patch only** (third number: `0.93.0` → `0.93.1`), whatever the change; see Versioning — Version freeze
2. **Update `CHANGELOG.md`** — add a `## [X.Y.Z] - YYYY-MM-DD` block at the top with `### Added/Changed/Fixed/Removed` sections per Keep a Changelog convention
3. **Generate** — `cd gse-one && python3 gse_generate.py --verify`
4. **Add all** — VERSION, CHANGELOG.md, manifests, all regenerated files in `plugin/`
5. **Commit** — with `feat:`, `fix:`, `docs:`, or `chore:` prefix, and `vX.Y.Z —` pattern in the subject
6. **Push** — `git push origin main`

Never skip a step. Never commit without regenerating. Never push without bumping. Never release a version without a matching CHANGELOG entry.

**Exception — gitignored / `_LOCAL/` files.** The build pipeline above applies only to files that will be committed to `main`. Edits to gitignored paths (matched by `/_*/` in `.gitignore`, primarily everything under `_LOCAL/`) are local-only work artifacts and do NOT require any pipeline step: no `VERSION` bump, no `CHANGELOG.md` entry, no `gse_generate.py --verify` run, no commit. This covers scratch notes, draft documents, audit working files, exploration sandboxes, and any maintainer-only material kept under `_LOCAL/`. If such a file is later promoted into the tracked corpus (e.g., moved out of `_LOCAL/` into `gse-one/src/` or `docs/`), the promotion itself becomes a normal tracked change and re-enters the full pipeline.

**Why:** Pre-release iteration, audit drafts, and maintainer notebooks live under `_LOCAL/` precisely because they must not trigger the release pipeline. Forcing a version bump for a scratch document would inflate the version history and pollute the CHANGELOG with non-shipping changes.

**How to apply:** Before initiating the build pipeline (or asking the user to validate one), check whether the edited files are gitignored. If every edited file is under `_LOCAL/` (or otherwise untracked), skip the pipeline entirely and just save. If a session edits both gitignored and tracked files, run the pipeline only for the tracked files.

**Distribution (since v0.62.7):** In addition to the 6-step pipeline above, distribution to end users now happens through `.github/workflows/release.yml`. On every `v*` tag push to `origin`, that workflow runs `gse_generate.py --verify` as a safety net, packages `gse-one/plugin/`, `install.py`, `VERSION`, `CHANGELOG.md`, `README.md`, and `install.sh` into a `gse-one.tar.gz` release asset, and publishes it via `gh release create`. The asset is the tarball consumed by the curl-based `install.sh` bootstrap. Pushing the tag is therefore the release act — it does not replace any step of the 6-step pipeline, but it does add an implicit post-condition: after `git push origin main`, maintainers should push the matching `vX.Y.Z` tag so the release asset is produced.

- Never edit files in `gse-one/plugin/` directly except `plugin/tools/` — the generator overwrites everything else from `src/`.
- Changes to activities go in `src/activities/`, changes to agents go in `src/agents/`.
- The orchestrator and .mdc rule are generated from the same source — body parity is verified automatically.

#### CHANGELOG style discipline (adopted v0.62.1)

CHANGELOG entries must stay scan-friendly. The commit message (`git log`) carries the "why" and the "how"; spec/design/CLAUDE.md carry the methodological rationale. The CHANGELOG answers only "what changed".

**Rules for new entries:**

1. **Header only**: `## [X.Y.Z] - YYYY-MM-DD`. No `Layers impacted: ...` line — the sections below make it explicit by listing the changed files.
2. **Optional 1-sentence intro in italics** (≤30 words), only if a release carries a non-obvious framing. Default: no intro.
3. **Sections limited to**: `### Added`, `### Changed`, `### Fixed`, `### Removed`, `### Deprecated`, `### Security`. No `### Rationale`, `### Design decisions`, `### Methodology notes`, `### Verification`, `### Notes`, `### Audit trail`, `### Notes for users`, `### Deferred`.
4. **Bullets ≤ 25 words each**, single line, verb-first (`Added X`, `Changed Y`, `Fixed Z`). No multi-paragraph bullets. No embedded "Rationale:" sub-explanation.
5. **No tables, no synthesis blocks spanning multiple releases**. If a synthesis adds value (release-series summary, post-audit report, migration guide), create a dedicated file under `docs/post-audit-reports/<date>-<theme>.md` and reference it from the CHANGELOG entry in one line.
6. **No enumeration fichier-par-fichier avec numéros de ligne**. Use git diff / git log for that. Summarize the change at the semantic level.

**Budget**: aim for ≤ 15 lines per release. Exceptionally up to 25 for a genuinely multi-facet release; beyond that, migrate the detail to `docs/post-audit-reports/`.

**Why**: pre-v0.62, releases frequently reached 30-50 lines with prose introductions, section meta (rationale, notes, verification, audit trail), and exhaustive bullet-level detail. The triple redundancy (commit / spec / CHANGELOG) alourdit le fichier sans bénéfice lecteur. The v0.62.1 retroactive condensation reduced v0.48.0-v0.62.0 from ~950 to ~290 lines (-69%) without information loss — the migrated content lives in `docs/post-audit-reports/` for audit-trail preservation.

### Tool architecture — registry-based resolution, self-contained installs

GSE-One skills shell out to Python tools (`dashboard.py`, `deploy.py`, `project-audit.py`, `coolify_client.py`), read templates (`templates/config.yaml`, `Dockerfile.*`, …) and reference docs (`references/hetzner-infrastructure.md`, `references/ssh-operations.md`), and read the plugin version from a unified `VERSION` file. Every such read is routed through a single indirection: the **registry file** `~/.gse-one` (a plain text file containing an absolute directory path).

**Registry invariant (since v0.61.0):** the registry always points to the install target — *not* to the gensem source repo. Skills use a single generic incantation across all install modes, and the gensem source repo can be deleted after install without breaking anything. The registry is `~/.gse-one` (machine mode) or `<project>/.gse/registry` (project mode — the default); the deployed incantation tries the project-local file first and falls back to the global one (see "Project mode" below).

**Per-mode registry target:**

| Platform | Mode | Registry target | Where common assets live |
|---|---|---|---|
| Claude Code | machine | `~/.gse-one.d/` (side-install) | `~/.gse-one.d/tools/`, `templates/`, `references/`, `VERSION` (plugin body → skills-dir `~/.claude/skills/gse/` — selective copy, auto-loaded as `gse@skills-dir`) |
| Claude Code | project | `<project>/.claude/` | `.claude/tools/`, `templates/`, `references/`, `VERSION` (plugin body → skills-dir `<project>/.claude/skills/gse/` — selective copy, `/gse:` namespace + native `gse:*` subagents, zero `$HOME` footprint; workspace trust + `/reload-plugins` required on first open) |
| Cursor | machine | `~/.cursor/plugins/local/gse-one/` | co-located with plugin body (full `copy_tree` of `plugin/`) |
| Cursor | project | `<project>/.cursor/` | `.cursor/tools/`, `.cursor/templates/`, `.cursor/references/`, `.cursor/VERSION` |
| opencode | machine | `~/.config/opencode/` | `~/.config/opencode/tools/`, `templates/`, `references/`, `VERSION` |
| opencode | project | `<project>/.opencode/` | `.opencode/tools/`, `.opencode/templates/`, `.opencode/references/`, `.opencode/VERSION` |
| Codex CLI | machine | `~/.gse-one.d/` (side-install) | `~/.gse-one.d/tools/`, `templates/`, `references/`, `VERSION` (skills → `~/.agents/skills/`, agents → `~/.codex/agents/`, AGENTS.md → `~/.codex/AGENTS.md`, hooks → `~/.codex/hooks/`) |
| Codex CLI | project | `<project>/.codex/` | `.codex/tools/`, `templates/`, `references/`, `VERSION` (skills → `.agents/skills/`, agents → `.codex/agents/`, AGENTS.md → project root, hooks → `.codex/hooks.json` FLAT + one-time `/hooks` trust approval) |
| Gemini CLI | machine (extension) | `~/.gemini/extensions/gse-one/` | co-located with extension body (full `copy_tree` of `plugin/gemini/`) |
| Gemini CLI | project | `<project>/.gemini/` | `.gemini/tools/`, `templates/`, `references/`, `VERSION` (commands → `.gemini/commands/gse/`, agents → `.gemini/agents/`, GEMINI.md → project root) |

**Why `~/.gse-one.d/` for claude machine mode (and Codex machine mode):** since v0.85.x the Claude plugin body is installed as a **skills-directory plugin** (selective copy of the Claude components — manifest, `skills/`, `agents/`, `hooks.claude.json`, `settings.json` — auto-loaded as `gse@skills-dir`; the CLI's `claude plugin install` only accepts marketplace ids since 2.1.x, and a full `copy_tree` would let the commands/skills unification absorb the Cursor `commands/` files as 24 duplicate skills). The selective copy carries no `tools/`/`templates/`/`references/`: in machine mode those runtime-resolvable assets live in the `~/.gse-one.d/` side-install (single registry-file convention); in project mode (since v0.87.0) they live in `<project>/.claude/` with the registry at `<project>/.gse/registry` — the Claude project install is fully self-contained. Codex's plugin cache (`~/.codex/plugins/cache/`) is likewise not a stable shell target, hence the same side-install. Note: project-level skills-dir plugins load only after the workspace trust dialog is accepted (+ `/reload-plugins`), which the installer prints as a post-install step. **Codex specifics:** the orchestrator's full body (~68 KB) exceeds Codex's `AGENTS.md` 32 KiB cap, so Codex uses a **condensed lite edition** (`src/agents/gse-orchestrator-lite.md`) as `AGENTS.md` and ships the **full** orchestrator as a loadable `gse-orchestrator` skill (the parity-of-hash contract does NOT apply to `plugin/codex/AGENTS.md` — it is a deliberate condensation; `plugin/gemini/GEMINI.md` DOES keep full parity, like opencode). Codex hooks are installed FLAT at `<target>/hooks.json` (the only standalone discovery path — the `hooks/hooks.json` sub-directory form is honored solely inside a real Codex plugin; installs ≤ 0.85.x shipped a dead file there) and only run after the user's one-time `/hooks` trust approval (since Codex 0.129) — these two are the real activation requirements. `[features] hooks = true` in `config.toml` (canonical; the old top-level `codex_hooks = true` is a deprecated alias) is now the Codex default; the installer still writes it as a safety belt for older versions and explicit opt-outs.

**Unified VERSION source:** `plugin/VERSION` (a one-line text file) is generated by `gse_generate.py` from the root `VERSION` and distributed by `install.py` to every install target. Skills read it uniformly as `cat "$(cat ~/.gse-one)/VERSION"` — no per-platform branching on manifest files.

**Generic read patterns in skills (authored form):**
- Tool invocation: `python3 "$(cat ~/.gse-one)/tools/dashboard.py"`
- Template copy: `cp "$(cat ~/.gse-one)/templates/config.yaml" .gse/`
- Reference read: `cat "$(cat ~/.gse-one)/references/hetzner-infrastructure.md"`
- Version read: `cat "$(cat ~/.gse-one)/VERSION"`

**Project mode + project-local-first resolution (project registry since v0.73.0; mode names renamed by user need in v0.87.0 — `project`/`machine`/`sandbox`, clean pre-1.0 break, old `plugin`/`no-plugin`/`local` names and the Claude `--scope` flag removed).** Sources author the simple global incantation `$(cat ~/.gse-one)/X`, but the generator rewrites it in every DEPLOYED artefact (skills, commands, agents, AGENTS.md, GEMINI.md, `.mdc`, Codex skills, Gemini TOMLs) to a project-local-first form:

```
$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/X
```

This is done by `_localize_registry_resolution()` — the FINAL step of `gse_generate.py:generate()`, run after all builders so it transforms every copy uniformly (preserving cross-platform orchestrator body parity). `--verify` asserts `count(bare) == count(resolved)` (no un-localized incantation remains). The Python dashboard hook resolves the registry in its own one-liner (`.gse/registry` if present, else `~/.gse-one`).

**`project` mode** (`install.py --mode project`, or `GSE_MODE=project` — the DEFAULT) writes the registry to `<project>/.gse/registry` with a path **relative** to the project root (e.g., `.codex`) — the install writes **nothing under `$HOME`** and the project is self-contained / committable (resolved relative to the agent's CWD, which is the project root — the same assumption the hooks already make when they read `.gse/config.yaml`). Machine mode is unaffected: with no `.gse/registry`, the `||` fallback uses `~/.gse-one`. History: the pre-0.87.0 `no-plugin` mode (project files + a machine-level `~/.gse-one` pointer, last-install-wins across projects) was absorbed into `project`; on Claude, `project` installs the skills-dir plugin body into `<project>/.claude/skills/gse/` (replacing the old gse-* prefixed-skills copy — re-installing over a pre-0.87.0 layout cleans the legacy artifacts).

**Sandbox mode (`--mode sandbox`, since v0.74.0).** The third mode, for **full `$HOME` isolation** — distinct from `project` (which only avoids `$HOME` *files* but still runs the agent under the real `$HOME`, so a pre-existing machine install co-loads). `sandbox` installs GSE under a project-internal `$HOME` at `<project>/.gse-sandbox/` and drops a generic launcher at `<project>/.gse-sandbox/run` (+ metadata `<project>/.gse-sandbox/launch.env`) — colocated with the isolated `$HOME` so a single `rm -rf .gse-sandbox` removes everything and there is no collision with the GSE state dir `.gse/`. **Install and run are decoupled**: install once, then `sh .gse-sandbox/run` over many days (no reinstall). Implementation: `install_sandbox()` **re-execs** `install.py --mode machine` with `HOME=<project>/.gse-sandbox` and `XDG_CONFIG_HOME` unset (so the normal machine install lands entirely inside the sandbox — no `install.py` path-logic change), then writes the launcher. The launcher (generated as `plugin/gse-run`, copied to `.gse-sandbox/run`) reads `.gse-sandbox/launch.env` sitting next to it, `cd`s to the project root, and in sandbox mode exports `HOME=<project>/.gse-sandbox` (= its own directory; + unsets `XDG_CONFIG_HOME`) before `exec`-ing the agent. Supported for **codex / gemini / opencode** only (file-based, `$HOME`-honoring installs); **Claude** (CLI/Keychain-mediated) and **Cursor** (GUI app) are rejected with a pointer to `--mode project`. The re-exec'd child runs with `GSE_CHILD=1` so it suppresses its banner/summary. Single user entry point preserved: `install.sh` forwards `GSE_MODE=sandbox` to `install.py` unchanged. The launcher also accepts two **platform-agnostic convenience flags** (since v0.80.0) that it strips from the args and translates to the running agent's native equivalent: `--bypass` (fully unprotected — codex `--dangerously-bypass-approvals-and-sandbox`, gemini `--yolo`, claude `--dangerously-skip-permissions`) and `--auto` (autonomous but keep the OS sandbox / lighter scope where supported — codex `--sandbox workspace-write --ask-for-approval on-request`, gemini `--approval-mode=auto_edit`, claude `--permission-mode acceptEdits`); opencode/cursor have no launch-flag equivalent (config / app-setting driven) so the launcher prints a note and injects nothing. All other args pass through verbatim. The launcher also **inherits the real global git identity** (`git config --global user.name/email`) into the sandbox as `GIT_AUTHOR_*` / `GIT_COMMITTER_*` env vars, read **before** the `$HOME` redirection (since v0.83.0) — otherwise the isolated `$HOME` hides `~/.gitconfig` and every commit would trigger a HUG git-identity prompt. Only unset vars are filled (explicit env overrides and project-local `git config` still win); no file is written into the sandbox.

**Install.py contract:**
- Exactly one helper `_copy_common_assets(target)` drops `tools/`, `templates/`, `references/`, `VERSION` into the registry target.
- Symmetric `_remove_common_assets(target)` cleans up on uninstall.
- Each install function ends with `_write_registry(<target>)` where `<target>` is the mode's install location. `_write_registry`/`_remove_registry` honor the module-level `_LOCAL_REGISTRY_PROJECT` (armed by `_maybe_local()` when `--mode project`) to target `<project>/.gse/registry` instead of `~/.gse-one`.
- Agents must never read+rewrite tool content — Python tools are maintained by hand in `plugin/tools/` per the build pipeline rule.

**Tool header convention:** each Python tool carries a `# @gse-tool <name> <version>` header on line 2. Both 2-part versions (`1.0`) and SemVer 3-part versions (`0.1.0`, signaling pre-1.0 maturity) are accepted — do not force alignment.

**Configuration policy — project-local files, no durable env vars.** All durable configuration and state live in project-local files (`.gse/*.yaml`, `.env`, `.gse/deploy.json`) or, for the install registry only, the user-level file `~/.gse-one`. Environment variables are reserved for: (1) ephemeral invocation parameters (the `GSE_*` overrides of `install.sh` — they live only for the duration of the command), (2) platform/OS conventions (`HOME`, `LOCALAPPDATA`, `NO_COLOR`/`FORCE_COLOR`). No tool, hook, or skill may read durable methodology state from a global environment variable.

**Why:** env vars are invisible state — undiagnosable from the repo, divergent across machines (the user works from several via Dropbox), and the root cause of the v0.62 hooks no-op (the fictional `CLAUDE_TOOL_INPUT` variable that silently disabled the whole deterministic guardrail layer). The audit job `tools-quality-uniformity` enforces this policy (sanctioned-list check).

**Curl-based entry point (since v0.62.7):** end users install via a POSIX-sh bootstrap `install.sh` at the repo root, served at `https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh`. The bootstrap detects the platforms present on PATH (claude, cursor, opencode, codex, gemini): exactly one → auto-picked; several → it fails fast asking for `GSE_PLATFORM` (one agent per project is the norm; `GSE_PLATFORM=all` opts into everything). The mode is NOT detected — it defaults to `project`, overridable via `GSE_MODE=machine` or `GSE_MODE=sandbox`. It resolves the release tarball and delegates to `install.py` — it does not duplicate install logic. Shell-level env-var overrides (`GSE_PLATFORM`, `GSE_MODE`, `GSE_VERSION`, `GSE_PROJECT_DIR`) let advanced users bypass auto-detection; they are documented for end users in README's "Environment variables" section. The registry invariant and the per-mode registry table above remain authoritative for all resolution; `install.sh` simply auto-selects one of those modes at run time. Maintainers adding a new install mode update the table and `install.py` — `install.sh` inherits the change automatically through the delegation.

### Versioning
- **Version freeze — the second number never moves without the maintainer's explicit decision (rule set in stone, 2026-11-23).** Every release bumps the third number only: `0.93.0` → `0.93.1` → `0.93.2` …, for fixes and for features alike. Moving to `0.94.0` (or `1.0.0`) is decided explicitly by the maintainer, in their own words, for that release; never infer it from the size of the change, from a version matrix, or from a peer session. **Why:** v0.93.0 was cut as a minor bump without being asked (the release should have been 0.92.2); the maintainer reserves the minor/major numbers for deliberate milestones. **How to apply:** before Step 1 of the build pipeline, read `VERSION` and add one to the third number; if a change seems to call for more, ask, and default to the patch bump.
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
- `src/activities/*.md` → `plugin/skills/*/SKILL.md` (Claude Code) + `plugin/commands/gse-*.md` (Cursor) + `plugin/opencode/skills/*/SKILL.md` + `plugin/opencode/commands/gse-*.md` + `plugin/codex/skills/*/SKILL.md` (Codex) + `plugin/gemini/commands/gse/*.toml` (Gemini)
- `src/agents/gse-orchestrator.md` → `plugin/agents/gse-orchestrator.md` + `plugin/rules/gse-orchestrator.mdc` + `plugin/opencode/AGENTS.md` + `plugin/gemini/GEMINI.md` + `plugin/codex/skills/gse-orchestrator/SKILL.md` (full body, loadable skill) — all wrapped/derived from the same source
- `src/agents/gse-orchestrator-lite.md` → `plugin/codex/AGENTS.md` (condensed ≤ 32 KiB — Codex-only; NOT byte-parity with the full orchestrator by design)
- `src/agents/<specialized>.md` → `plugin/agents/*.md` + `plugin/opencode/agents/*.md` (with `mode: subagent` injected) + `plugin/codex/agents/*.toml` (markdown→TOML, `developer_instructions`) + `plugin/gemini/agents/*.md`
- `plugin/hooks/hooks.claude.json` → `plugin/opencode/plugins/gse-guardrails.ts` (transpiled) + `plugin/codex/hooks/hooks.json` + `plugin/gemini/hooks/hooks.json` (all from the shared `_guardrail_commands()`; parity asserted by `--verify` **by intent, not byte**: two deliberate per-platform divergences exist — Claude's post-push review warning uses the JSON `additionalContext` channel (plain stdout is debug-log-only on Claude), and Cursor uses the `Shell` matcher + native `afterFileEdit` event (Cursor has no `Bash`/`Edit`/`MultiEdit` tools). Both are asserted by dedicated `--verify` checks.)
- The orchestrator body, the `.mdc` rule body, the opencode `AGENTS.md` block, and the Gemini `GEMINI.md` block are all verified identical by `--verify`. The Codex `AGENTS.md` is verified to derive from `gse-orchestrator-lite.md` (condensed, not identical).
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
- Principle titles follow a separate convention (spec carries the full descriptive title; orchestrator and principle source file carry the short form). See "Principle title convention" subsection below.
- For internal steps within a single document (e.g., "see Step 3" when the current document has a Step 3), the numeric form alone is acceptable — the local scope makes the reference unambiguous.

### Principle title convention — "spec long / implementation short"

The 16 principles (P1-P16) have titles declared in three locations. By design, the three locations use two different forms:

- **Spec §2 headers** (`gse-one-spec.md`) carry the full descriptive title, optionally with a parenthetical sub-title. Pedagogically complete — source of truth for cross-references.
- **Orchestrator bullets** (`gse-one/src/agents/gse-orchestrator.md` Core Principles section) carry the short form.
- **Principle source file H1** (`gse-one/src/principles/<name>.md`) carries the short form.

Examples of the pattern:

| # | Spec (long) | Orchestrator + file (short) |
|---|---|---|
| P4 | Human-in-the-Loop by Default | Human-in-the-Loop |
| P7 | Risk-Based Decision Classification | Risk Classification |
| P8 | Consequence Visibility (Risk Analysis Presentation) | Consequence Visibility |
| P12 | Version Control Isolation | Version Control |
| P14 | Knowledge Transfer (Coaching) | Knowledge Transfer |
| P15 | Agent Fallibility (Self-Awareness) | Agent Fallibility |
| P16 | Adversarial Self-Review and User Pushback | Adversarial Review |

**Invariants:**
1. The spec carries the pedagogically complete form. Cross-references to principles should use the spec form per the "number + name" convention above (e.g., `§P14 — Knowledge Transfer (Coaching)`).
2. The short form MUST be identical between orchestrator and principle source file. Divergences between these two sources are bugs — they were caught and fixed in v0.48.8 P13 for P1.
3. The short form is the main title before any parenthetical, OR a coherent shorter phrasing when the spec title doesn't use a parenthetical (e.g., "Risk Classification" for spec "Risk-Based Decision Classification"; "Adversarial Review" for spec "Adversarial Self-Review and User Pushback").

**Why the two forms coexist:** the spec needs pedagogical completeness (a reader discovering the principle benefits from "Knowledge Transfer (Coaching)" making the scope explicit). The orchestrator and file H1 need visual compactness — forcing long titles into bullet lists and file headers adds verbosity without methodological benefit.

**Noted exception — P13:** spec says "Event-Driven Behaviors (Hooks)" (main title "Event-Driven Behaviors", parenthetical "(Hooks)"), but orchestrator and file H1 both say just "Hooks" (the parenthetical, not the main title). This inversion is accepted because "Hooks" is the vernacular term used throughout the methodology code and prose (`hooks.claude.json`, `PreToolUse hooks`, spec P13 description itself uses "hook" 7+ times). The exception can be revisited later if it causes confusion.

### Activity path reference conventions

Activity files (`gse-one/src/activities/*.md`) refer to templates, agents, and tools through **three** deliberate path forms, each carrying a distinct semantic. Do NOT force uniformity (per Meta-1 — Anti-rigidity discipline): the forms carry information.

- **`$(cat ~/.gse-one)/X`** — **runtime-executable**. Use this form inside shell commands, Python invocations, or explicit "adopt this role" agent references — ANY form that must resolve on the end-user's machine at runtime. The registry (`~/.gse-one` for global modes, or `<project>/.gse/registry` for fully-local mode since v0.73.0) contains the path to the **install target** — one of `.claude/`, `.cursor/`, `.opencode/`, `.codex/`, `.gemini/`, `~/.config/opencode/`, `~/.cursor/plugins/local/gse-one/`, `~/.gemini/extensions/gse-one/`, or `~/.gse-one.d/` depending on mode. Every install mode exposes the same sub-paths (`tools/`, `templates/`, `references/`, `VERSION`, and platform-specific `skills/` / `commands/` / `agents/`) so a single generic incantation works everywhere; the deployed form is `$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/X` (project-local-first, global fallback). Examples: `python3 "$(cat ~/.gse-one)/tools/dashboard.py"`, `cp "$(cat ~/.gse-one)/templates/config.yaml" .gse/`, `cat "$(cat ~/.gse-one)/VERSION"`, `"$(cat ~/.gse-one)/agents/security-auditor.md" — adopt this role`. See "Tool architecture" above for the full per-mode table.

- **`plugin/X/...`** — **authoritative-format pedagogical pointer**. Use this form in prose when referencing the authoritative schema/format of a template or agent as distributed in the plugin. Examples: *"authoritative format in `plugin/templates/X`"*, *"authoritative specification in `plugin/agents/coach.md`"*. Never executed; read by humans.

- **`gse-one/src/X/...`** — **methodology-source pointer**. Use this form when the reference explicitly targets the methodology source tree (the maintainer/forker view — what a contributor edits, not what a generator produces). Typical uses: *"the methodology default is defined in `gse-one/src/templates/config.yaml`"*, *"see `gse-one/src/templates/intent.md` for the template copied by `/gse:go`"*. Distinct from `plugin/X` because it addresses maintainers/forkers, not end users.

**Retired form:** bare unrooted references (`agents/X`, `templates/X`) — these were ambiguous ("relative to what?") and have been upgraded to `plugin/X` in prose contexts. If a new bare reference appears in an activity, upgrade to `plugin/X` (documentation pointer) or `$(cat ~/.gse-one)/X` (runtime-executable) based on the surrounding intent.

### Activity structural conventions

GSE-One activities use three structural patterns for the `## Workflow` section. Each pattern carries semantic information and is intentional — do NOT force uniformity (per Meta-1).

- **Flat Step sequence (default, ~18 activities)** — `### Step 1`, `### Step 2`, …, `### Step N`. Used when the activity is a linear pipeline with no disjoint modes. Examples: `reqs`, `design`, `preview`, `tests`, `produce`, `review`, `fix`, `deliver`, `compound`, `integrate`, `status`, `health`, `assess`, `hug`, `go`, `pause`, `resume`, `task`.

- **Multi-mode `### Mode → #### Step N` (4 activities)** — `### Mode A` with `#### Step 1..N`, then `### Mode B` with `#### Step 1..M`, etc. Step numbering resets per mode because each mode is a disjoint execution path (user invokes exactly ONE mode per call). Examples: `backlog` (Display / Add / Sync), `plan` (Strategic / Tactical), `collect` (Internal / External), `learn` (Reactive / Proactive). Each file carries an inline "Workflow structure note" explaining the pattern to the reader (per Meta-2 — Document exceptions inline).

- **Phase-over-Step `### Phase N / #### Step M` (1 activity)** — `deploy` only, which has 6 server-level phases each containing multiple steps. `deploy.md:36-41` documents the pattern inline. Phase boundaries are idempotent milestones tracked in `deploy.json → phases_completed`; steps within a phase are the concrete shell commands.

When authoring a new activity, pick the pattern that matches the semantic:
- Single linear pipeline → Flat Step.
- Disjoint modes selected by flag/arg → Multi-mode (add an inline workflow structure note per Meta-2).
- Long-running operation with idempotent milestones → Phase-over-Step (deploy is the reference).

Forward-authoring convention for sub-step headings: `#### Step N.M — Title`. Applies to new sub-steps only — existing variant forms stay as-is (no retroactive sweep).

### Corpus example policy — no live training case studies

Illustrative examples in the distributed corpus (spec, `src/activities/`, `src/agents/`, templates) must NEVER reuse the case study of a current or planned training session, and file paths in examples stay technology-neutral (`<ext>` placeholder) unless the example is specifically about a technology. The canonical running example is a **personal reading tracker** (web app, beginner profile — REQ-003 filter by month, REQ-005 export CSV, TST-007/TST-008).

**Why:** examples in activities/agents are few-shot prompt material — coding agents imitate them. When the corpus example equals the user's actual project, derivation and parroting become indistinguishable: an agent building the training's expense tracker that outputs "Filter expenses by month" may be listening to the learner or copying its own prompt. A distinct canonical domain makes contamination detectable. The 2026 training→methodology capitalization loop deposited the live training case (expense tracker, CalcApp) verbatim into the corpus, and `Expense.tsx` silently biased examples toward React/TS (purity findings A1/A2, fixed 2026-07-10).

**How to apply:** when capitalizing a lesson from a training session (`/gse:compound` Axe 2 feeds, failure-mode notes, new examples), strip the case-study identity — keep the lesson, re-express the illustration in the canonical running example or a neutral domain.

### Vocabulary convention — "Axe N" (capitalization axes) vs "axes" (coach)

The corpus deliberately uses two distinct axis vocabularies (~50 occurrences, 15+ files): **"Axe 1/2/3"** (capitalized, French-origin proper noun) names the three capitalization axes of `/gse:compound` / `/gse:integrate` (project learnings / methodology feedback / competencies) — including machine-ish contract strings (coach moment tags like `/gse:compound Axe 2 feed`, sprint template headings); **"axis/axes"** (lowercase English) names the coach's 8 monitoring axes. The divergence carries semantic information (two systems, never confused) — per Meta-1, do NOT force-align or partially rename. A full "Axe → Axis" rename remains possible as a dedicated contract-change release (tracked in the audit registry recommendations); a partial rename is the only wrong move.

### Memory policy — in-repo only
Any project convention, rule, preference, or decision that Claude must remember across sessions for this project MUST be recorded in a versioned file in this repo — typically this `CLAUDE.md`, or another markdown doc under source control. Do NOT write such information to Claude's per-machine auto-memory (`~/.claude/projects/<hash>/memory/`).

**Why:** The user works on this project from multiple machines via Dropbox. Files under `$HOME` do not travel; only the git-versioned repo does. Auto-memory entries are invisible to collaborators, lost on a fresh machine, and fragment the source of truth.

**How to apply:** When the user gives durable feedback or establishes a convention, update `CLAUDE.md` (or the appropriate in-repo doc) via the full build pipeline. Never silently save to auto-memory. If auto-memory entries are found for this project on any machine, they should be migrated into `CLAUDE.md` and deleted.

### Repo-level tooling (`.claude/`)

The `.claude/` directory at the repo root contains **maintainer tools** that are **not** part of the distributed plugin:

- `.claude/commands/gse-meta-audit.md` — `/gse-meta-audit` slash command for methodology coherence audits (named *meta*-audit since v0.84.0 to avoid colliding with the distributed project activity `/gse:audit`, exposed as `gse-audit` on Cursor/opencode/Codex)
- `.claude/commands/gse-meta-audit-fix.md` — `/gse-meta-audit-fix` slash command driving the post-audit fix session (operationalizes the "Post-audit fix workflow" below)
- `.claude/commands/gse-release.md` — `/gse-release` slash command: thin executable checklist over the Build pipeline critical rule (CLAUDE.md stays canonical)
- `.claude/agents/methodology-auditor.md` — agent adopted during `/gse-meta-audit` and `/gse-meta-audit-fix`
- `.claude/settings.json` — minimal committed permission allowlist (audit engine, catalog, generator, tests) so `/gse-meta-audit` runs friction-free on every machine and fork; keep it minimal — every entry auto-approves command execution for anyone who trusts the project settings

These are inherited automatically when someone clones gensem (or a fork of it). They are Claude Code-only (v1). The Python engine at `gse-one/audit.py` provides CLI access independent of the editor.

**Do not move these tools into `gse-one/plugin/`** — that would distribute them to all end users of GSE-One, polluting the methodology for people who only use the plugin without forking. Maintainer tools live at `.claude/` (repo-local) or `gse-one/` (e.g., `audit.py` alongside `gse_generate.py`), never in `gse-one/plugin/`.

#### Audit output contract (single canonical registry — since v0.75.0)

An audit produces ONE living machine artifact — its primary consumer is the coding agent that later processes the fixes, not a human reading markdown. The contract:

- **Single source of truth:** `_LOCAL/audit/audit.json` (JSON, `schema_version` field). Detection writes it; verification (Phase 3.5) updates verdicts **in place**; the fix session updates `status`/`resolution` **in place**. There is exactly one such file in the working path at any time.
- **Durable backlog (split since 2026-07-10):** `_LOCAL/audit/backlog.json` — the **cross-run work registry**. `audit.json` is a per-run photograph (archived wholesale on each `--emit-registry`); `backlog.json` is updated **in place across runs and is NEVER archived or relocated**. Items carry a stable `BKL-<8 hex of sha1(normalized title)>` id, a solution proposal, provenance (audit run, REC id, job) and a status (`proposed | backlog | accepted | in_progress | done | rejected`). Recommendations enter it via `audit.py --backlog-promote` (dedup by BKL id); on later runs, `--merge` links re-discovered recommendations to existing items (`backlog_id`) instead of duplicating, and `--render` appends a Backlog section showing each open item's age in audit runs.
- **Layout hygiene (deterministic category `audit_layout`):** the engine inspects `_LOCAL/audit/` for organization drift — the only expected entries are `audit.json`, `backlog.json` and `archive/` (flat tool-written snapshots). Manually relocated registries (e.g., ad-hoc dated folders) are flagged as warnings: manual moves break the in-place lifecycle and steal the regression-diff baseline.
- **Markdown is a throwaway render**, produced on demand to `/tmp` via `python3 gse-one/audit.py --render` (default target `/tmp/gse-audit-<ts>.md`, or `--out PATH`). It is **never** persisted in the repo tree — so it can never diverge from the JSON.
- **Auto-archive (systematic):** every `audit.py --emit-registry` moves the previous `audit.json` into `_LOCAL/audit/archive/audit-<ts>-v<version>.json` before writing the new one. The working path stays noise-free; history lives out of the way (rarely consulted; the previous registry is the cross-run diff baseline).
- **Stable finding identity:** `AUD-<8 hex of sha1(category|file|normalized title)>` (recommendations: `REC-…`). Stable across runs → enables new/resolved/persisting diff and lets commits/CHANGELOG reference a finding id.
- **Finding lifecycle (fields, not files):** `verdict: detected → CONFIRMED|FALSE_POSITIVE|NEEDS_REFINEMENT|SCOPE_CHANGE`; `status: open → in_progress → fixed|wontfix|deferred`. FALSE_POSITIVE → `wontfix` + a `detector_issues[]` entry (audit.py work item). Category E recommendations live in their own array (`status: proposed|accepted|rejected|backlog`).
- **`audit.py` registry commands:** `--emit-registry` (archive + engine seed), `--merge <file>` (fold in LLM findings/recommendations/clusters, link to backlog), `--set-verdicts <file>` (apply Phase 3.5 verdicts), `--render [registry] [--out]`, `--backlog-promote` / `--backlog-list` / `--backlog-set BKL-ID=STATUS` (durable backlog). The legacy `--format json`/`--no-save` stdout flow is preserved for piping.
- **Never** write `audit-<ts>.md` / `latest.md` / `verify-*.md` / `reconciled` files in the slash-command/registry flow — those are the retired pre-v0.75.0 multi-file pattern (their drift was the reason for this contract). The CLI-standalone `audit.py` auto-save (deterministic markdown to `_LOCAL/audits/`, documented in README) stays sanctioned. Full spec: `_LOCAL/maintenance/2026-06-13-audit-output-redesign.md`.

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

### Methodology meta-principles

These are meta-rules that govern how the methodology itself is maintained and evolved. They are NOT numbered as P1-P16 principles (which describe how GSE-One users work) — they describe how maintainers and contributors treat the corpus.

**Meta-1 — Anti-rigidity discipline.** Before enforcing uniformity across the corpus (renaming, aligning formats, merging variants, forcing a single convention on what appears to be divergent content), verify that the observed divergence does not carry semantic information, technical necessity, or user-facing clarity. Uniformity is not a virtue in itself — it is only valuable when it eliminates drift that causes bugs or confusion. If a divergence is intentional, the correct response is to **document the convention** (in CLAUDE.md, in the file itself, or via an explanatory inline note) rather than **force alignment**. This rule saved the 2026-04-21 audit session from wrongly renaming `deploy.md` Phase/Step hierarchy, force-aligning 10 principle titles on the spec long form, and force-fitting `guardrail-enforcer` into the Reviewer archetype — each of which would have erased useful methodological information. Applies to audits, refactors, schema migrations, prose style sweeps, and any proposal that starts with "let's make X match Y".

**Meta-2 — Document exceptions inline.** When a file, activity, agent, or template deliberately deviates from a corpus-wide convention (e.g., `deploy.md` uses Phase/Step hierarchy instead of flat Step numbering; P13 uses "Hooks" vernacular instead of spec main title), prefer a short inline note at the site of deviation over a silent divergence. The note should be brief (1-3 lines), explain WHY the deviation exists, and point to the canonical convention for comparison. Informal rule, not strict — use judgment. Examples in the codebase: `deploy.md` Workflow structure note on Phase/Step (v0.48.7), `compound.md` Step 2.7 explanation of summarization mechanism (v0.48.0), the "P13 noted exception" in the Principle title convention section above.

**Meta-3 — Deterministic-guard placement.** Before adding a new deterministic safeguard, route it to the mechanism that already owns its layer: **executable Python code → unit tests** (`gse-one/tests/`); **prose/template corpus coherence → the audit engine** (`gse-one/audit.py` deterministic categories, surfaced by `/gse-meta-audit`); **semantic judgment → LLM audit jobs** (`.claude/audit-jobs.json`). Never create a dedicated Python file to guard a single prose property — that pattern multiplies maintenance surface and contradicts the trust model (half the code watching the other half). Additionally, a new guard must clear an evidence bar: the property has actually drifted before (cite the incident), or it is recovery-critical (state files, checkpoint schema, guardrail layer). Speculative guards are refused. Precedent: v0.66.1 routed the checkpoint round-trip property into `audit.py` (templates category) instead of a proposed `test_checkpoint.py`, after the maintainer flagged the over-engineering risk.

**Meta-4 — Lightness discipline.** A method that is too heavy or too constraining is abandoned, and engineers go back to unstructured vibe coding (maintainer's directive, 2026-11-21; analysis in `_LOCAL/maintenance/2026-11-21-lightness-analysis.md`). Before adding a Gate, a Hard stop or a mandatory step: (1) **name its exit** — every Hard stop offers *Override — proceed anyway*, recorded as a DEC-, unless it guards a security or destructive action (Emergency tier: force push, committing a secret, destroying data, infrastructure or shared history); (2) **state its cost** — one more question per task, per sprint or per project — in the commit message; (3) prefer folding it into an existing question. A configuration switch must have a reader: a key that no activity, agent or tool applies is wired or removed in the same release. When a change alters what the user is asked, replay a sprint without a human before releasing (the classroom rehearsal harness takes about 7 minutes).

**Why meta-principles live here (not in spec §2).** Spec §2 principles (P1-P16) are user-facing methodological rules that ship with the plugin. Meta-principles are maintainer rules that govern how we evolve the methodology. Keeping them separate avoids inflating the user-facing principle count and keeps maintainer discipline visible to contributors without burdening end users.

### Post-audit fix workflow

When an audit (`/gse-meta-audit`) produces a batch of findings that the maintainer decides to address, the fix session follows a 4-phase protocol observed across the v0.51.0 → v0.55.0 release train (76 corrections applied, 5 false positives documented, 0 regression on 72 unit tests). Each phase matters — skipping one is the documented failure mode. The executable form of this protocol is the `/gse-meta-audit-fix` command (`.claude/commands/gse-meta-audit-fix.md`); this section remains the canonical rationale.

**Phase 1 — Parallel anti-false-positive verification.** Before applying any fix, spawn a dedicated methodology-auditor sub-agent per cluster (not per finding — the cluster is the unit of verification). Each sub-agent re-reads the cited files, applies Principles 1 (evidence), 8 (verification), 9 (anti-rigidity), and returns a structured verdict per finding:

- **CONFIRMED** — problem exists, proposed fix is correct → ready to apply.
- **FALSE_POSITIVE** — problem misidentified; justification documented; no action.
- **NEEDS_REFINEMENT** — problem exists but the proposed fix must be adjusted; alternative proposed.
- **SCOPE_CHANGE** — warning reclassified (e.g., simple → structurant, defer to later release).

This phase detected 4 false positives out of 12 clusters in the first post-audit batch (33%) and caught zero false positives in subsequent batches after the lesson was absorbed. Skipping it means mechanically applying audit claims that LLM sub-agents fabricated — the 2026-04-22 session verified at least 5 such fabrications that would have silently degraded the corpus.

**Phase 2 — Consolidation + user validation.** Present the verified plan to the user as a structured list: CONFIRMED findings with exact file:line changes, FALSE_POSITIVE findings with root cause documentation, NEEDS_REFINEMENT findings with the updated proposal. The user validates in bulk (not one by one) — the verification phase is what earns the bulk-validation trust. Use the Communication style Rule 2 (single-default question) for the final "ok to apply?".

**Phase 3 — Cluster-based application.** Apply fixes grouped by cluster theme (same cause root), not by file. A cluster may touch multiple files atomically — that's fine. The benefit is a commit message that tells a coherent story ("TASK state machine drift", "invocation contract drift", "decisions.md path unification") rather than a flat list of unrelated edits. Each cluster → one or more files → one commit message rationale.

**Phase 4 — Version bump + CHANGELOG + regen + commit + push.** Apply the full build pipeline per the `Build pipeline` rule. **Since 2026-11-23 every bump is a patch bump (Versioning — Version freeze); the matrix below is historical and only tells which releases would have deserved a milestone — a minor or major bump needs the maintainer's explicit decision.**

| Release scope | Bump | Example |
|---|:-:|---|
| Pure documentation / cosmetic (no schema / behavior change) | patch | v0.51.0 → v0.51.1 (cross-refs, opt-in/opt-out labels, ISO freshness markers) |
| Schema drops / feature activation / audit engine semantics change / new spec subsection | minor | v0.52.0 (schema orphans retired), v0.53.0 (cursor write centralization), v0.54.0 (new §3.2.2 + partitive detection) |
| Contract change / new signature / breaking schema shape | minor (pre-1.0) or major (post-1.0) | v0.55.0 record_* status-wrapped contract (pre-1.0 minor) |

**Phase 5 — CHANGELOG FP documentation.** Each false positive detected in Phase 1 is explicitly documented in the CHANGELOG entry of the resolving release, with (a) what was claimed, (b) what was actually true, (c) root cause (if known) in the detector. False positives where the detector can be fixed at source (e.g., audit.py regex) are tracked as work items — 3 of 5 FP in the v0.51 → v0.55 train were eliminated at source in `audit.py` v0.54.0. The CHANGELOG FP section is not a blame trace — it's a learning asset for future detector improvement.

**Pattern: contract change release isolation.** When a fix requires changing a function signature, return shape, or state schema in a way that could cascade to skills/tests/callers, DO NOT bundle it with unrelated fixes. Defer to a dedicated release (v0.55.0 pattern: WC17.4+5 deferred from v0.53.0 → v0.55.0 specifically to allow a cohesive bundle: contract change + docstring sweep + contract tests all in one atomic release). Mixed-intent commits obscure rollback scope.

**Pattern: three refinement directions (not two).** The methodology-auditor Principle 6 originally described two directions — `downward` (impl aligns to spec) and `upward` (spec catches up to impl). A third direction proved necessary in practice:

- **Downward** — spec/design is canonical, impl must align (most common).
- **Upward** — impl is more complete/correct, spec/design catch up.
- **Retraction** — dead code, duplicate writes, orphan fields, obsolete tags are removed from the source layer with no equivalent insertion elsewhere. Examples from v0.52 → v0.53: drop `never_*` P16 quartet from status.yaml (pure aspiration, never written); drop top-level `complexity:` block (duplicates plan.yaml.budget); drop `git.commits` (git is authoritative source); strip 15 G-NNN gap-analysis tags (no registry, no traceability value); remove duplicate cursor writes from 5 activities (central protocol handles it). Retraction is NOT the same as downward: it produces a net deletion rather than an alignment.

When an auditor proposes a fix, the three-direction framing is the first classification step. Many "contradictions" are actually retractions (one side is dead) — forcing downward alignment propagates the dead code, forcing upward enshrines it in the spec. Both are worse than retraction.

## Language

The user communicates in French. Respond in French for conversation, English for code/commits.
