# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.54.0] - 2026-04-22

Layers impacted: **spec** (§3.2.2 NEW, §14.3 Step 5 skip matrix, §P13 opencode wording), **design** (§7 P11 citation), **activities** (preview, hug), **templates** (profile.yaml comment), **audit engine** (audit.py CHANGELOG filter, partitive lookahead, ±1 info drift), **maintainer tooling** (.claude/audit-jobs.json indent-tolerant perspective guideline)

**Minor release — v0.50 audit warnings batch 4 (upward refinements + audit engine improvements).** Applies 10 confirmed corrections from 4 warning clusters + 1 bonus, verified by 4 parallel methodology-auditor sub-agents. One FALSE POSITIVE (WC22.1) documented with cosmetic comment clarification; one cluster (WC17.4+5) deferred to dedicated v0.55.0 release for bundled deploy.py contract change.

### Added

- **Spec §3.2.2 Profile Update Mode** — new subsection under §3 Command Catalog documenting the `/gse:hug --update` behavior: dimension-to-impact-to-notification table (5 dimensions with user-visible behavioral consequences), silent-update dimensions, and the invariant that --update never interrupts in-flight activities. Upward refinement (WC21.2) — the activity artefact (`hug.md` Step 4.5) already formalized this table; the spec now catches up.
- **Spec §14.3 Step 5 skip matrix** — new clause #7 enumerating the 3 Intent Capture skip conditions (non-greenfield, adopt mode, existing `intent.md`) that design §5 Intent Capture already documented. Upward refinement (WC21.1) — closes the spec/design gap.
- **Spec §P13 opencode wording** — Hooks paragraph now explicitly documents all 3 platforms (Claude Code + Cursor via PreToolUse/PostToolUse command hooks; opencode via native TS plugin with `tool.execute.before/after` handlers). Upward refinement (WC21.3) — the design + implementation had supported opencode since the opencode subtree was introduced; the spec P13 text was never refreshed.
- **Design §7 P11 citation** — opening paragraph now explicitly cites spec §P11 — Guardrails as the source of the Soft/Hard/Emergency tier taxonomy used by hooks. Upward refinement (WC21.4) — the design used the P11 vocabulary 10+ times without attribution, whereas P12/P13/P14/P15/P16 are cited by name; this breadcrumb restores the traceability chain.
- **hug.md learning_goals Inform** — Step 2 dimensions table row 10 now documents the 3 entry points into `/gse:learn` (direct invocation, coach proactive gap detection, compound Axe 3 retrospective proposal). Clarifies that leaving `learning_goals` empty does NOT disable learning — the opt-in design of the coach preserves user consent while the documentation previously made the paths invisible (WC22.3).

### Changed

- **preview.md Step 2.5 applicability widened** — the UX Heuristic Pass is no longer gated to `project.domain ∈ {web, mobile}` (a narrow 2-domain positive list). Replaced with a **surface-based decision matrix** covering all 9 canonical domain values (spec §3.2.1): `web`/`mobile` always run; `other`/`embedded`/`scientific`/`data` run when the preview artefact has a UI surface; `api`/`cli`/`library` skip. This matches the step's stated intent ("UX issues at prototype stage"), allows scientific Streamlit dashboards and embedded HMIs to benefit from Nielsen + WCAG checks, and eliminates the domain-list drift (WC22.2 NEEDS_REFINEMENT).
- **profile.yaml dimensions comment clarified** — line 21 comment now explicitly states "12 here + 1 in user.name above = 13 total" to disambiguate the deliberate split between `user.name` and the `dimensions:` block. WC22.1 FALSE POSITIVE from audit v0.50 documented; cosmetic-only (no schema change).
- **audit.py WC24.1 CHANGELOG filter** — `audit_links()` now skips `CHANGELOG.md` entirely from broken-link detection. CHANGELOG historical entries about removed/merged files (e.g., the v0.37.0 `tutor.md → coach.md` merge narrative) are correct Keep-a-Changelog history, not broken links. False positive class flagged by audit v0.50 WC7 — now eliminated at source.
- **audit.py WC24.2 partitive lookahead** — the `audit_numeric()` principles-count regex now has a negative lookahead blocking partitive phrasing (`N principle titles/IDs/names/headers/bullets/entries/of N`). Previously "10 principle titles" in CLAUDE.md:205 (a partition 10/16, not a total) triggered a warning "claims 10 — actual is 16". False positive class flagged by audit v0.50 WC6 — now eliminated at source.
- **audit.py BONUS-3 off-by-one ±1 info drift** — numeric drift of exactly 1 (e.g., "10 specialized agents" vs actual 11) now emits an `info` finding with rationale ("often includes/excludes orchestrator") instead of being silently absorbed. Drift ≥2 remains a `warning`. Makes previously-invisible ±1 drifts auditable without false-positive noise.
- **.claude/audit-jobs.json WC24.3 indent-tolerant perspective check** — `quality-assurance-cluster` job's checks array now documents that `perspective:` fields in Reviewer-archetype agents live inside Output Format example blocks at indented positions (2-space indent typical), not at top-level YAML. Guides LLM sub-agents to use indent-tolerant matching. False positive class flagged by audit v0.50 WC10 on devil-advocate.md — now documented at source.

### Deferred (v0.55.0)

- **WC17.4 + WC17.5 deploy.py contract unification** — 5 `record_*` functions + 5 `_cmd_record_*` wrappers + 17 docstrings + 10 new contract tests. Scoped to a dedicated release because the unified status-wrapped return contract is a breaking change for Python importers (transparent to the deploy.md skill which parses only exit codes). The v0.54.0 verification pass confirmed: 0 skill impact (14 fire-and-forget call sites in deploy.md), 0 existing-test breakage (49 tests preserved), ~+143/-11 LOC estimate. See v0.53.0 audit-auditor report for the full migration plan.

### Deferred (v0.56.0+ audit engine refactor)

- **BONUS-1** — `audit_cross_refs()` regex charset narrow (`[a-z][a-z-]+` for agent names). Broaden to `[A-Za-z0-9][A-Za-z0-9_-]+` in a future audit engine refresh to tolerate forker agent naming conventions.
- **BONUS-2** — `audit_links()` regex only matches `gse-one/` prefix. Broaden to include `.claude/`, `assets/`, repo-root files (`VERSION`, `CHANGELOG.md`, `install.py`, `gse-one-spec.md`, …) in a future refresh.

### Notes

- **Direction mix** — 4 upward fixes (WC21.1/2/3/4: spec/design catch up to implementation maturity), 5 downward fixes (WC22.2/3 activity + audit engine improvements + profile.yaml comment), 1 pure refactor (WC24.3 audit-jobs.json).
- **False positive eliminated at source** — v0.54.0 closes 3 of the 4 false positives detected by the v0.51.1 anti-false-positive protocol (WC6 partitive, WC7 CHANGELOG, WC10 indent-tolerant). WC11 (fix.md dashboard regen covered by PostToolUse hook) remains a documented-as-intentional non-issue.
- **CLAUDE.md unchanged this release** — v0.53.0 already added the Activity path / structural convention sections. v0.54.0 focuses on spec + design + activities + audit engine, not meta-conventions.
- **Release 4 of 5 post-audit** — cumulative tally: v0.51.0 errors (15), v0.51.1 simple warnings (31), v0.52.0 structural warnings (8), v0.53.0 structural + Python hygiene (10), v0.54.0 upward + audit improvements (10). Total: **74 corrections applied, 5 false positives documented**.
- Pipeline: 61 unit tests pass; cross-platform parity identical; `gse_generate.py --verify` clean.
- **Minor bump rationale (0.53.0 → 0.54.0)** — adds spec §3.2.2 (new sub-chapter), changes audit.py detection semantics (partitive, CHANGELOG filter, ±1 info), widens preview.md applicability rule (surface-based gate). Pre-release backward-compat rule permits the changes without migration tooling.

## [0.53.0] - 2026-04-22

Layers impacted: **spec** (no-op), **design** (§5.18 subcommand list + state schema), **CLAUDE.md** (2 new convention sections), **agents** (deploy-operator), **activities** (plan, produce, review, fix, deliver, backlog, collect, learn, design, go), **tools** (dashboard.py, audit.py)

**Minor release — v0.50 audit warnings batch 3 (structural refinements + Python hygiene).** Applies 10 confirmed corrections from 4 warning clusters verified by 4 parallel methodology-auditor sub-agents. Zero false positives this batch. 2 sub-findings deferred to a dedicated v0.54+ release (deploy.py record_* contract unification + matching docstring sweep).

### Changed

- **Tool quality sweep — partial (WC17)** — applied 4 of 6 sub-findings; 2 (WC17.4 + WC17.5) deferred to v0.54+ for a bundled contract-change release:
  - **WC17.1** — normalized `gse-one/plugin/tools/dashboard.py:2` `@gse-tool dashboard 0.17.0` → `1.0` (align on two-digit form used by the 4 other tools; the field is presence-only, not parsed by any consumer).
  - **WC17.2** — added a `Dependencies:` paragraph to `gse-one/audit.py` module docstring documenting PyYAML as an optional dependency (used by `audit_templates()`; gracefully skipped if absent).
  - **WC17.3** — added one-line docstrings to the 11 `audit_*` category entry points in `gse-one/audit.py` that lacked them (audit_version, audit_file_integrity, audit_plugin_parity, audit_cross_refs, audit_links, audit_git, audit_python, audit_templates, audit_todos, audit_test_coverage, audit_freshness; audit_numeric was already documented).
  - **WC17.6** — moved validation-warning `print()` calls out of the `collect_data()` library function and into `generate()` (the CLI entry point). Eliminates stderr noise from any future programmatic caller of `collect_data()`; preserves the CLI user-facing warning banner via `data["_validation_warnings"]` already populated by the library.
- **Sprint lifecycle cursor write centralization (WC18, direction=upward)** — 5 activities (plan, produce, review, fix, deliver) previously wrote `status.yaml` cursor fields (`last_activity`, `last_activity_timestamp`, `current_sprint`, `current_phase`) directly in their Finalize steps, DUPLICATING the central Sprint Plan Maintenance protocol documented in `gse-orchestrator.md` §Sprint Plan Maintenance and `gse-one-implementation-design.md` §10.1. Retired the duplicate writes; left a short inline "State transition note (v0.53.0)" in each activity pointing to the central protocol. Activity-local state (TASK statuses, health scores, `last_task`, `activity_history` init at plan, `current_phase: LC03` transition at deliver) REMAINS in the activities where it belongs. Impact: ~15 lines retired, ~10 lines of explanatory pointer added across 5 files, authority ambiguity resolved (one canonical owner of cursor fields: the orchestrator).
- **Deploy-cluster upward refinements (WC19)** — 3 sub-findings CONFIRMED, all direction=upward:
  - **WC19.1** — `gse-one-implementation-design.md:2424` subcommand enumeration expanded from 14 to 20 entries (added `record-role`, `record-cdn`, `wait-dns`, `preflight`, `training-init`, `training-reap`; grouped by purpose). The tool had grown past the design paragraph.
  - **WC19.2** — `gse-one-implementation-design.md:2398` state schema paragraph now lists `user_role` (set by Step -1 Orientation) and `cdn { provider, enabled, bot_protection }` (set during Phase 5 Step 7) as top-level blocks.
  - **WC19.3** — `gse-one/src/agents/deploy-operator.md` Anti-patterns list: fused 2 overlapping bullets into one, correcting `/start (full rebuild)` → `GET /api/v1/deploy?uuid=...&force=true` (the real redeploy path used by `deploy.py:554`; exposed as `CoolifyClient.trigger_deploy(uuid, force=True)`). The old `/start` guidance contradicted both the real tool behavior and the adjacent bullet at :120.
  - **Bonus BC19.a** — `gse-one/src/agents/deploy-operator.md` "Deployment lifecycle" block now clarifies inline (per Meta-2) that Phases 1-5 are server-level (tracked in `phases_completed`) while Phase 6 is per-application (tracked via `applications[].status` + `coolify.app_uuid`). Resolves the implicit 6-phases-but-5-keys convention.
- **Activity conventions documented (WC20, Meta-1 anti-rigidity preserved)** —
  - **WC20.1** — added a new **"Activity path reference conventions"** section to CLAUDE.md (between "Memory policy" predecessor and "Repo-level tooling"). Documents the 3 deliberate path forms (`$(cat ~/.gse-one)/X` runtime-executable; `plugin/X/...` authoritative-format pointer; `gse-one/src/X/...` methodology-source pointer) with their semantic distinctions. The 4th bare form (`agents/X`) is documented as retired; upgraded 2 remaining occurrences: `gse-one/src/activities/design.md:201` (`agents/architect.md` → `plugin/agents/architect.md — authoritative checklist`) and `gse-one/src/activities/go.md:157` (bare `agents/coach.md` + `gse-orchestrator.md` → `plugin/agents/coach.md` + `plugin/agents/gse-orchestrator.md`).
  - **WC20.2** — added a new **"Activity structural conventions"** section to CLAUDE.md documenting the 3 Workflow structural patterns as first-class citizens: Flat Step (default, ~18 activities), Multi-mode `### Mode → #### Step N` (4 activities: backlog, plan, collect, learn), Phase-over-Step (deploy only). Added inline "Workflow structure note" in the 4 multi-mode activities per Meta-2 (document exceptions inline). `fix.md` was excluded from scope (audit false positive partial: fix.md uses Flat Step, not multi-mode). Author guidance added to CLAUDE.md for choosing the right pattern when creating a new activity.

### Deferred (v0.54+)

- **WC17.4 + WC17.5** — `gse-one/plugin/tools/deploy.py` public function docstring sweep (9 functions in `record_*` family + 3 private helpers) + error-handling contract unification (record_phase uses `_err()`/sys.exit, record_role returns `{"status": "ok"|"error"}` dict, others return bare dicts — unify on the record_role pattern). Deferred because the contract change touches `_cmd_record_*` CLI wrappers AND potentially `src/activities/deploy.md` skill steps that read these returns; it benefits from a coordinated release where the NEW contract is documented alongside the refactor, avoiding a two-step documentation churn. Pre-release backward-compat rule (CLAUDE.md) permits the breaking change without migration tooling, so v0.54 is the right window before any public marketplace release locks the contract.

### Notes

- **Direction mix** — 7 downward fixes (tool docstrings, sprint cursor cleanup, activity conventions, anti-pattern fix), 3 upward fixes (design §5.18 state schema + subcommand list, Compliance archetype invocation pattern via CLAUDE.md convention documentation).
- **WC18 upward pattern validated** — v0.51.0 introduced the pattern "where the lower layer is more complete or more correct, the spec/design catches up" (7 upward fixes in that release). WC18 is the MIRROR pattern: "where the central protocol is already complete, the duplicates in activity files retreat". Both are valid direction-of-travel; the 2026-04-22 audit session has now practiced both forms.
- **CLAUDE.md governance growth** — now hosts 7 convention/governance sections: Build pipeline, Tool architecture, Versioning, Pre-release backward-compat, Cross-reference convention, Principle title convention, Activity path reference conventions (NEW), Activity structural conventions (NEW), Memory policy, Repo-level tooling, Communication style, Methodology meta-principles. This accretion is healthy — each section documents a forker-visible convention, not internal drift.
- Pipeline: 61 unit tests pass; cross-platform parity identical; `gse_generate.py --verify` clean.
- **Patch bump candidate vs minor** — considered 0.52.1 (patch) since zero user-facing breaking change. Chose 0.53.0 (minor) because WC18 retires direct writes from 5 activities (internal behavior change, even if net-visible result is identical via the orchestrator's central protocol) and CLAUDE.md gains 2 new first-class convention sections. Minor bump reflects the methodological refinement volume.

## [0.52.0] - 2026-04-22

Layers impacted: **spec** (§1.6 guardrail-enforcer row), **design** (§5.13-5.17 G-NNN cleanup, §5.14 Preflight sequence extension, §5.16 status.yaml sample), **agents** (gse-orchestrator, guardrail-enforcer), **activities** (go, resume, review), **principles** (adversarial-review), **templates** (status.yaml, backlog.yaml), **tools** (dashboard.py), **docs** (CHANGELOG v0.34.0 cross-ref)

**Minor release — v0.50 audit warnings batch 2 (structural refinements).** Applies 8 confirmed corrections from 4 warning clusters verified by 4 parallel methodology-auditor sub-agents with anti-false-positive discipline. Mix of schema cleanup (retire dead fields), feature activation (wire up dormant writer), doc clarification (archetype + cross-refs), and code bug fix. Zero false positives this batch.

### Changed

- **Schema orphans retired (WC13 — 3 DROP + 1 ADD_WRITER + 1 CODE_FIX)** —
  - **WC13.1 — retired P16 `never_*` quartet** (4 booleans: `never_discusses`, `terse_responses`, `never_modifies`, `never_questions`). Pure aspiration: named in design + principle + review but never in the `status.yaml` template schema and never written. P16 remains fully operational via `consecutive_acceptances` (primary trigger) and `pushback_dismissed` (per-sprint suppression). Updated: `gse-one/src/principles/adversarial-review.md` (§Passive acceptance signals simplified to 2 signals), `gse-one/src/activities/review.md` (§3f Passive Acceptance Detection simplified), `gse-one-implementation-design.md` (§5.16 status.yaml sample + §5.17 P16 signal-tracking paragraph).
  - **WC13.2 — retired top-level `complexity:` block from `status.yaml` template.** Dead schema: no writer, no reader used it; the authoritative source is `plan.yaml.budget.{total,consumed,remaining}` (written by `/gse:plan`, `/gse:produce`, `/gse:task`, read by orchestrator and dashboard). Micro mode — which has no `plan.yaml` — explicitly has no budget by design. Replaced the block with a short explanatory comment.
  - **WC13.3 — retired `git.commits: 0` field from `backlog.yaml` template.** Dead schema: no writer, no reader. `git rev-list --count` provides the value on demand without staleness risk.
  - **WC13.4 — ADD WRITER for `sessions_without_progress`.** The counter was declared in `status.yaml:87` and referenced by `gse-orchestrator.md:171` + `coach.md` for `mid_sprint_stall` axis activation, but no activity incremented or reset it — rendering stale-sprint detection and the coach mid-sprint-stall axis dormant. Added the writer logic to `/gse:go` Step 4 — Stale Sprint Detection (compare current backlog TASK statuses against `activity_history[-1]` snapshot; increment if no change, reset if changed) and mirrored to `/gse:resume` Step 6 — Finalize. This activates two documented features that existed in prose only.
  - **WC13.5 — FIX code bug in `dashboard.py:442-443`.** The two lines read `status.get('complexity_budget')` and `status.get('complexity_used')` — top-level keys that never existed in the `status.yaml` schema, silently returning `None`. Redirected to `data['plan']['budget']['total']` and `data['plan']['budget']['consumed']` (the live `plan.yaml` already parsed at line 428), with graceful Micro-mode fallback.
- **G-NNN identifiers retired (WC14 — 15 tags stripped)** — legacy gap-analysis markers (G-002, G-003, G-004, G-005, G-006, G-007, G-008, G-009, G-010, G-011, G-014, G-025, G-026, G-027, G-028) that cluttered design §5 subsection titles and inline labels have been removed. The tags had no legend, no registry, no archive — they were opaque to any reader. Only one external reference existed (CHANGELOG.md v0.34.0), updated to a descriptive "design §5.17 — Complexity budget ranges mechanics note" cross-reference per CLAUDE.md "number + name" convention. Net effect: cleaner design doc navigation, zero semantic loss.
- **guardrail-enforcer documented as Compliance archetype (WC15)** — spec §1.6 line 443 + `gse-one/src/agents/guardrail-enforcer.md` opening block clarified to reflect the observed reality: the agent is a **canonical rule reference** for the Soft/Hard/Emergency tier taxonomy and GUARD-NNN output format, NOT a runtime sub-agent spawn. Runtime enforcement happens via system hooks (`plugin/hooks/hooks.claude.json`) and inline Step 0 preflights in activities. Parallel to P13 Hooks and deploy.md Phase/Step exceptions documented under CLAUDE.md Meta-2 ("document exceptions inline"). Zero wire-up needed — the divergence carries semantic information (the Compliance archetype is deliberately invocation-less).
- **Design §5.14 Preflight sequence extension (WC16)** — added 3 new short subsections to design §5.14 between the existing Step 1 and Step 2: Step 1.5 — Recovery Check, Step 1.6 — Dependency Vulnerability Check, Step 1.7 — Git Baseline Verification — each citing spec §14.3 for full semantics and `gse-one/src/activities/go.md` for concrete commands (number + name convention). Added a separate "Implementation-only preflight extensions" note covering Step 2.6 — Dashboard Refresh and Step 2.8 — Coach Workflow Overview (present in go.md but not in spec §14.3; Option C hybrid per the audit). Net: design §5.14 becomes a navigable map without duplicating spec/go.md content. ~45 lines added.

### Notes

- **Verification methodology** — 4 parallel methodology-auditor sub-agents (one per cluster: WC13, WC14, WC15, WC16) applied Principles 1 (evidence-based), 8 (verify-before-report), 9 (anti-rigidity) to each candidate warning. All 4 clusters returned CONFIRMED; zero false positives. For WC13 (5 sub-findings), the auditor distinguished between DROP (3 cases: pure aspiration), ADD_WRITER (1 case: genuine need, cross-session state), and CODE_FIX (1 case: wrong read path in tool).
- **Direction mix** — 4 downward fixes (schema drops, dashboard.py fix, design §5.14 extension, design §5.17 sample cleanup), 3 upward fixes (spec §1.6 archetype clarification, feature activation for sessions_without_progress, CHANGELOG cross-ref upgrade), 1 neutral (G-NNN strip).
- **Feature activation caveat** — the `sessions_without_progress` writer now runs on every `/gse:go` / `/gse:resume`. Existing projects that do not have the field in their `status.yaml` will start from 0 (absent → default 0). No migration needed per pre-release backward-compatibility rule.
- **Archetype clarification payoff** — the guardrail-enforcer is the 2nd agent (after the coach pedagogy axis 1 clarified in v0.51.0) documented as cross-cutting orchestrator-delegated rather than spawned. This pattern — a distinct archetype invocation contract — is now visible in CLAUDE.md §Agent archetypes + spec §1.6 + the agent file itself.
- **Minor bump rationale (0.51.1 → 0.52.0)** — mix of schema changes (drop 3 fields from templates), feature activation (stale sprint Gate + coach mid_sprint_stall axis become live), code bug fix (dashboard.py wrong read path), archetype clarification (guardrail-enforcer = Compliance). Pre-release backward-compat rule (CLAUDE.md) permits direct schema drops without migration.
- Pipeline: 61 unit tests pass; cross-platform parity identical; `gse_generate.py --verify` clean.

## [0.51.1] - 2026-04-22

Layers impacted: **spec** (§P1 verified in v0.51.0, §P6 row consistency, §14.3 narrative, Appendix C cascade table), **agents** (gse-orchestrator, coach), **activities** (hug, go, plan, task, learn), **references** (hetzner-infrastructure, ssh-operations), **templates** (backlog.yaml, config.yaml, deploy-env.example, sprint/compound.md)

**Patch release — v0.50 audit warnings (first batch: simple documentation and consistency fixes).** Applies 31 corrections from 8 confirmed warning clusters out of 12 verified by parallel methodology-auditor sub-agents with anti-false-positive discipline (Principles 1, 8, 9). Four additional clusters were verified as FALSE POSITIVES and documented below to refine future audits.

### Changed

- **Cross-reference convention sweep (WC1 — 13 fixes)** — applied CLAUDE.md "number + name" convention to number-only cross-references found across the corpus:
  - `go.md:77` — "HUG Step 5.5" → "HUG Step 5.5 — Dashboard Initialization"
  - `sprint/compound.md:46` — "§2.1–§2.6" → "§2.1–§2.6 — Axe 2 (Methodology Capitalization) steps"
  - `sprint/compound.md:71` — "§3" → "§3 — Axe 3 (Competency Capitalization) steps"
  - `spec Appendix C cascade table` — three rows (§14.3, §12.1, artefact_type) now cite "§N — Name" form; critically, the `artefact_type` row pointed to the WRONG section (§4 Collect, which is unrelated) and is corrected to `§P6 — Traceability (artefact_type enum at lines 549-560)`.
  - `hug.md:229` — "§14.3 Step 6" → "§14.3 — Orchestrator Decision Logic, Step 6 — Complexity Assessment"
  - `go.md:88` + `go.md:94` + `spec §14.3:2884` — "HUG Step 4" → "HUG Step 4 — Git Initialization"
  - `plan.md:186` — "see §10.1 for per-mode lists" (WRONG: §10.1 is Branch Model) → "see spec §14 — Standard Activity Groups (Lifecycle Phases) for per-mode lists"
  - `task.md:115` + `backlog.yaml:40` — "spec §12.3" → "spec §12.3 — Unified Backlog"
- **Coach opt-in → opt-out label (WC2)** — `coach.md:136` header corrected from "(pedagogy axis, opt-in)" to "(pedagogy axis, opt-out — on by default; set `coach.proactive_gap_detection: false` in `config.yaml` to disable)". The `config.yaml` default is `true`, so the feature is opt-out, not opt-in; the previous label was factually inverted.
- **SSH ConnectTimeout consistency (WC3 — 7 fixes)** — added `-o ConnectTimeout=10` to every SSH invocation in `ssh-operations.md` §"Connection patterns" and sub-sections. The file's §"Timeouts and retries" declares this timeout mandatory ("Always use…"), but the example invocations did not include it. Deploy.md's actual real-usage examples (lines 207, 241) already apply the rule; the reference file is now self-consistent.
- **Hetzner freshness markers (WC4 — 5 updates)** — added `> Last verified: 2026-04-22` markers to §1 (Server Types), §2 (Load Balancers), §3 (Other Pricing), §4 (Datacenters), §5 (Application Resource Profiles). Prior state: only §1 had a month-level "April 2026" parenthetical; now all five volatile sections carry ISO-date markers scannable by future audit passes.
- **deploy-env.example completeness (WC5)** — added commented placeholders for `SERVER_IP`, `SSH_USER`, `SSH_KEY` under a new "Filled automatically during Phase 2 (Provision) — or set manually if BYO server" banner, parallel to the existing Coolify banner. Keeps the reference template complete for forkers and BYO-server advanced users (deploy.py writes these keys programmatically during provisioning, but the template documentation was incomplete).
- **config.yaml section ordering and count (WC8)** — swapped Section 14 (Compound) and Section 15 (Coach) to restore monotone 1..15 numbering (Compound now physically precedes Coach). Updated header comment from "~50 keys across 11 sections" to "~60 keys across 15 sections" (the previous claim was stale since v0.49 feature additions).
- **Orchestrator P6 bullet completeness (WC9)** — extended the P6 bullet in `gse-orchestrator.md:31` to match spec §P6 canonical enums:
  - ID prefixes: 8 → 11 values (added TCP-, INT-, OQ-; each actively used elsewhere — TCP- in test-campaign reports, INT-001 in Intent Capture, OQ- in Open Questions Resolution).
  - `artefact_type`: 7 → 8 values (added `spike`; already referenced in the orchestrator's own lifecycle guardrails at lines 431-432 but missing from the enum line — self-inconsistency fixed).
- **LRN frontmatter completeness (WC12)** — `learn.md` Step 4 frontmatter template now emits the full canonical set per spec §P14: added `topic`, `trigger` (with canonical enum `reactive | proactive | contextual`), `related_activity`, `traces.derives_from`. The `mode` enum is expanded from 2 values (`quick | deep`) to 3 (`contextual | quick | deep`) aligning with spec §P14. The `gse-one/src/templates/learning-note.md` template was already correct — only the activity's embedded template drifted.

### Notes

- **Verified false positives (4 clusters — no action, documented for future audit refinement):**
  - **WC6** — Python audit flagged "CLAUDE.md line 178 claims '10 principles'". Verified: the phrase is "10 principle titles" (partial count of titles affected by a near-mistake in the 2026-04-21 audit session, NOT a total count). Same paragraph cites P1-P16 three times nearby. Audit engine's numeric detector should recognize partitive semantics.
  - **WC7** — Python audit flagged broken doc links in CHANGELOG.md and README.md. Verified: CHANGELOG references to `tutor.md` are historical (file legitimately removed in v0.37.0 when merged into coach.md; Keep-a-Changelog mandates preserving past release narratives). README.md all 10 referenced paths resolve. Audit engine's link checker should exclude CHANGELOG historical references and may have a path-resolution bug in the README scan.
  - **WC10** — Audit flagged devil-advocate.md missing `perspective:` field. Verified: the field IS present on lines 60, 68, 76, 84 under each RVW-NNN example, positioned identically to the other 6 reviewer agents. Likely detector missed 2-space indentation under RVW-NNN headers.
  - **WC11** — Audit flagged fix.md missing explicit dashboard regeneration call (which review.md and produce.md have). Verified: the PostToolUse hook on Edit/Write/MultiEdit (hooks.claude.json:28-54) runs `dashboard.py --if-stale` automatically after every structured-artefact write. The explicit calls in review.md/produce.md are belt-and-suspenders for pedagogical user-facing moments; fix.md's summary-driven finalization tone legitimately omits the explicit call without loss of correctness.
- **Verification methodology** — each warning cluster was independently verified by a dedicated methodology-auditor sub-agent applying Principles 1 (evidence-based), 8 (verify-before-report), and 9 (anti-rigidity check). 12 sub-agents ran in parallel; each returned a verdict CONFIRMED | FALSE_POSITIVE | NEEDS_REFINEMENT. Two clusters were NEEDS_REFINEMENT — their corrections were applied with the auditor-proposed refinements (WC1.4 target corrected from wrong §4 to correct §P6; WC1.9 target corrected from wrong §10.1 to correct §14; WC5 scope clarified to reference-only placeholders).
- **Patch bump rationale (0.51.0 → 0.51.1)** — no schema changes, no behavior changes, no new activities or fields. All modifications are documentation consistency, cross-reference conventions, and template completeness. Per SemVer, patch is appropriate.
- Pipeline: 61 unit tests pass; cross-platform parity identical; `gse_generate.py --verify` clean.

## [0.51.0] - 2026-04-22

Layers impacted: **spec** (§P1, §1.6, §12.3, §13.1), **design** (§3.1, §5 Intent Capture, §5.16, §5.17, §10.1), **agents** (gse-orchestrator, coach, deploy-operator, test-strategist), **activities** (reqs, design, preview, produce, review, fix, deliver, task, status, compound), **templates** (backlog.yaml, decisions.md), **tools** (dashboard.py), **references** (ssh-operations.md), **maintainer tooling** (.claude/audit-jobs.json)

**Audit v0.50 error cluster corrections.** Applies fixes for the 15 errors + 5 high-impact invocation-contract drifts surfaced by the 21-job methodology audit run at v0.50.0. Corrections are grouped in 6 coherent clusters; each cluster was validated individually before application.

### Changed

- **TASK status state machine (Cluster 1)** — introduced `reviewed` status between `review` and `fixing`/`done` in `backlog.yaml` enum. `/gse:produce` now transitions `in-progress → review` (was: directly to `done`); `/gse:review` transitions `review → reviewed` (no HIGH/MEDIUM findings) or `review → fixing` (findings); `/gse:fix` transitions `fixing → done`; `/gse:deliver` accepts `reviewed` OR `done` as ready-to-merge. Rationale: the `reviewed` vs `done` distinction preserves a quality trend signal for coach Axis 5 (a high ratio of `reviewed` vs `done` indicates high PRODUCE quality). Impacted: spec §12.3 status table (added row `reviewed` + clarifying note), design §10.1 lines 1337-1339 (canonical transition triplets), `src/templates/backlog.yaml` (enum + inline documentation), `produce.md:284`, `review.md:25 + 47 + 54 + 245`, `deliver.md:62`, `fix.md:55`, `status.md:78`, `task.md:14 + Step 1`, `gse-orchestrator.md` (new "TASK status state machine" section), `plugin/tools/dashboard.py:718` (counts `reviewed + done + delivered` as productive).
- **Ad-hoc TASK artefact_type alignment (Cluster 1)** — `/gse:task` Step 1 now maps user intent to the canonical spec §P6 enum (`code | requirement | design | test | doc | config | import | spike`) instead of the previous invalid values (`feat / fix / refactor / task`). Free-text modifier keywords ("fix", "add", "refactor") all map to `code` because the enum describes the artefact class produced, not the commit-message intent. Default: `code`.
- **Invocation-contract drift (Cluster 2)** — four specialized agents that declared an activation for activities that never invoked them are now reconciled. Direction was chosen per-case based on methodological value:
  - `requirements-analyst` + `/gse:reqs` → **downward**: added `reqs.md` Step 7.5 "Requirements Quality Pass" invoking the agent to audit drafted REQs for completeness, testability, ambiguity, inter-REQ consistency, INT-001 alignment.
  - `security-auditor` + `/gse:design` → **downward**: added `design.md` Step 5.5 "Security Design Pass" invoking the agent for threat modeling at the design layer (OWASP + CWE lens, DES-NNN review). Front-loads AI-integrity checks per spec §P15/§P16.
  - `ux-advocate` + `/gse:preview` → **downward**: added `preview.md` Step 2.5 "UX Heuristic Pass" invoking the agent for Nielsen + WCAG AA + cognitive-load checks on prototypes before soliciting human feedback. Conditional on `project.domain ∈ {web, mobile}`.
  - `test-strategist` + `/gse:produce` → **upward**: removed `/gse:produce` from the agent's `Activated by:` declaration (spec §1.6 table + `test-strategist.md` frontmatter + opening block). Rationale: the code-vs-tests relationship is evaluated by the IMPL tier at REVIEW per spec §6.5 — duplicating it in PRODUCE would double-spend and break the produce/review separation.
  - `coach` axis 1 (pedagogy) — documented explicitly as cross-cutting orchestrator-delegated in `coach.md` Invocation contract table (parallel to guardrail-enforcer via hooks). Updated `.claude/audit-jobs.json` `invocation-contract-consistency` check 6 to whitelist this row.
- **`decisions.md` canonical path (Cluster 3)** — unified on `.gse/decisions.md` (project-wide, per spec §11). Corrected `gse-orchestrator.md:150` and `compound.md:96` which wrongly pointed to a non-existent `docs/sprints/sprint-{NN}/decisions.md`. The `sprint: {NN}` field in each DEC-NNN entry is now the sole filtering mechanism for sprint-scoped consumers. Enriched `src/templates/decisions.md` with a `## Format` section documenting the canonical DEC-NNN structure (type / tier / date / sprint / consequences / traces).
- **Deploy phase names (Cluster 4)** — aligned `deploy-operator.md:104-105` and `ssh-operations.md:50-51` on the canonical phase keys `coolify` and `dns` (were: `install-coolify`, `configure-domain` — invalid per `deploy.py:49 PHASE_NAMES`, `deploy.json` template, `deploy.md`).
- **Count / enum drifts (Cluster 5)** —
  - spec §P1:466 broken cross-reference "Section 9" → "Section 10 — Version Control Strategy" (applied number+name convention per CLAUDE.md to all three refs in the sentence).
  - spec §13.1:2511 config example `project.domain` enum: 6 → 9 canonical values (aligned with §3.2.1:1143).
  - design §3.1 three occurrences of "28 templates" → "29 templates (MANIFEST.yaml is one of them, acting as self-descriptor)" — aligned with §11.1, §12, and MANIFEST.yaml real count.
  - design §5.16 Intent Capture blocks (Exempt/skip conditions + Failure modes) relocated from State Schemas section to the Intent Capture section they describe (moved ~11 lines from §5.16 area back to §5 Intent Capture Design Mechanics, after "Pivot / re-capture command").
  - spec §13.1 github block: added `upstream_repo: ""` field with cascade resolution order (user override → plugin manifest default → skip). Removes the contradiction with design §5.17:1956 + compound.md:140 + integrate.md:27 which all reference the field.
- **Coach schema contract (Cluster 6)** — design §5.17 aligned on `coach.md` + `compound.md` (the implementations were canonical):
  - Output schema: top-level key `verdict:` → `coach:` (match implementation); severity enum `inform | gate` → `low | medium | high` (richer prioritization, spec §P14 compliance).
  - Invocation table: moments renamed from abstract tags (`sprint_close`, `compound_axe_3`) to explicit activity references (`/gse:compound Axe 2 feed`, `/gse:compound Axe 3 feed`); axes corrected to match `compound.md:81` (Axe 2 feed fires 7 axes 2-8) and `compound.md:219` (Axe 3 feed fires axes 1, 2) — previously wrongly documented as 3 axes and 8 axes respectively.
  - Removed the dead `severity: gate` branch (line 2248) — all workflow-axis outputs are Inform-tier per spec §P14; the escalation path was never implemented. Replaced with a note documenting future-extension potential.

### Notes

- **Direction mix** — of the 20 fixes, ~13 are downward (implementation follows spec/design), ~5 are upward (spec/design catches up with better implementation), 2 are bidirectional (impl and spec both modified to converge). Upward fixes concern: spec §13.1 upstream_repo declaration, design §5.17 coach schema + invocation taxonomy, design §5.14 decision tree (partially), spec §1.6 test-strategist activation row.
- **Volume** — ~35 files touched in `gse-one/src/` and 1 in `gse-one/plugin/tools/`. Plugin regenerated via `gse_generate.py --verify` to propagate src changes to `plugin/skills/`, `plugin/agents/`, `plugin/commands/`, `plugin/opencode/` (all three target platforms).
- **Deliberate scope limits** — this release addresses **error-class findings only**. The audit surfaced 69 warnings and 53 strategic recommendations that remain queued for subsequent sprints. Warnings will be addressed in v0.52.x patches; strategic recommendations (Category E) will be evaluated for a roadmap discussion.
- **Pre-release backward-compat** — per CLAUDE.md "Pre-release backward-compatibility — not required" rule, the schema changes (new `reviewed` TASK status, new config field `github.upstream_repo`, DEC-NNN format enrichment with `sprint:` field) apply directly without migration tooling. Existing downstream consumers (activities, tools, dashboard) are updated atomically in this same commit.
- Minor version bump (0.50.0 → 0.51.0) reflects the methodological refinements (new TASK status, new activity steps, new agent invocations) which are feature-level even though each individually is modest.

## [0.50.0] - 2026-04-22

Layers impacted: **spec** (§12.2), **CLAUDE.md** (meta-principles), **maintainer tooling** (methodology-auditor, audit-jobs catalog, audit tests), **`.claude/` command** (gse-audit job counts)

**Retrospective capitalization of session learnings.** Based on the rétrospective analysis at the end of the 2026-04-21/22 audit cleanup session, applies the "high-confidence" improvements to audit instructions and methodology elements. Codifies patterns that emerged repeatedly during the session into durable methodology artifacts.

### Added
- **`.claude/agents/methodology-auditor.md` — Principle 8 "Verification before report"**. Every finding claiming a fact about file content MUST be verified (re-open the file at the cited line, confirm verbatim; for absence claims, grep for the pattern; for numeric claims, check context for historical/section-number/semantic false positives; for structural claims, read the full relevant section). Motivated by the session's discovery that sub-agents produced several false-positive findings (e.g., "deploy.md and hug.md miss `Arguments: $ARGUMENTS`" — both files actually contained the line).
- **`.claude/agents/methodology-auditor.md` — Principle 9 "Anti-rigidity check"**. Before classifying a divergence as error/warning, the auditor MUST ask whether the divergence carries semantic information (example: deploy.md Phase/Step hierarchy reflects idempotent-milestone tracking) or is a deliberate design choice (example: principle titles spec-long / impl-short pattern). If yes, classify as `severity: info` with "document the convention" recommendation. Counters the LLM uniformity bias that proposes forced alignment regardless of intent.
- **`.claude/agents/methodology-auditor.md` — "Number + name" cross-reference convention in Output format**. Findings must cite referenced sections/steps with both numeric identifier and section/step name (e.g., `§14.3 Step 1.6 — "Dependency vulnerability check"`). Consistent with the same convention now in CLAUDE.md > Critical rules.
- **`.claude/agents/methodology-auditor.md` — Two new anti-patterns**. Added "Never proposes forced uniformity when the divergence carries semantic information" and "Never emits a finding without first verifying the cited content" to the explicit anti-patterns list.
- **`CLAUDE.md` — Methodology meta-principles section** (sub-section of Communication style). Two meta-principles:
  - **Meta-1 Anti-rigidity discipline** — corpus-wide rule for any contributor: verify divergence meaning before forcing alignment. Names the 3 examples from the session (deploy.md, principle titles, guardrail-enforcer archetype) that would have been erased by naive uniformity.
  - **Meta-2 Document exceptions inline** — informal guidance: prefer explaining deviations at the site of deviation over silent divergences. Example codebase references (deploy.md v0.48.7, compound.md v0.48.0, Principle title P13 exception).
  - Explicit rationale on why meta-principles live in CLAUDE.md and not in spec §2 (user-facing vs maintainer-facing separation).
- **`gse-one-spec.md` §12.2 — "two storage patterns" paragraph**. Makes explicit the previously implicit distinction between **section-level artefacts** (multiple per document: REQ, DES, TST, RVW, DEC, TCP, plan-summary, compound, decision, code, test-campaign — use nested `gse:` frontmatter) and **document-level artefacts** (one per file: intent, learning, external-source — use flat `id: XXX-NNN / artefact_type:` frontmatter). Discovered during v0.48.4 P9 but the convention was not named; now named and propagated.
- **`.claude/audit-jobs.json` — new job `invocation-contract-consistency`** (Category D, horizontal_cluster, bidirectional). Verifies that every specialized agent's "Activated by:" declaration is honored by actual invocation in the cited activity files, and vice versa. Motivated by v0.48.0 P4 discovery that coach declared invocation at `/gse:pause` and `/gse:compound` but pause.md/compound.md contained zero invocation steps — 3 of 8 coach axes were silently inoperant. Catalog total: 20 → 21 jobs (Category D: 8 → 9).
- **`gse-one/tests/test_audit.py` — 12 regression guards** against known false-positive classes in `audit.py` numeric patterns (section numbers, principle IDs, specialized-templates, CHANGELOG exclusion, specialized-with-orchestrator, digit-after-letter). Includes a categories completeness smoke test. Joins the existing test_deploy.py (49 tests) for a total of 61 unit tests run by `gse_generate.py --verify`.

### Changed
- **`.claude/commands/gse-audit.md` — job counts updated** from 20 to 21 and Category D from 8 to 9 jobs (matches the new `invocation-contract-consistency` added to `audit-jobs.json`). Updates affect: frontmatter description, workflow intro, options table, Phase 2 job count, Phase 3 concurrency, Phase 4 tally, Phase 5 summary templates, and invocation examples. All references are now internally consistent.

### Notes
- Session retrospective: this commit is the "close-loop" on learnings from the v0.48.0 → v0.49.1 post-audit session. Five of the "high-confidence" recommendations from the retrospective analysis are applied (A1, A2, A4, A5 on audit instructions; M5 and M8 on methodology elements). Alternatives were preferred over original recommendations for M1 (meta-principle in CLAUDE.md rather than P17) and M3 (informal note rather than strict rule) — both documented inline in CLAUDE.md with explicit reasoning.
- Recommendations intentionally NOT applied: M4 (summarize-pattern generalization — YAGNI, 1 use case), M6 (rule-lifecycle formalism — too meta), M7 (Compliance archetype blueprint — speculative), M9 (vernacular-exception pattern — single case).
- Previous session commits v0.48.0 → v0.49.1 are the immediate context. See CHANGELOG entries for the specific propositions (P1-P14) and conventions adopted.
- Pipeline: 61 unit tests pass; cross-platform parity identical; `gse_generate.py --verify` clean.
- Minor version bump (0.49.1 → 0.50.0) reflects the introduction of a new audit job, a new test module, a new methodology concept (document-level vs section-level artefacts), and meta-principles in CLAUDE.md. These aggregate to feature-level changes even though individually each is modest.

## [0.49.1] - 2026-04-22

Layers impacted: **CLAUDE.md only** (methodology governance rules)

**PRINCIPLE-TITLES — Document the "spec long / implementation short" convention in CLAUDE.md.** Task #23, created during v0.48.8 P13. Completes Option B's CLAUDE.md consolidation pass.

### Added
- **`CLAUDE.md` — "Principle title convention — 'spec long / implementation short'"** subsection added under Critical rules (between Cross-reference convention and Memory policy). Documents that the 16 principles (P1-P16) have titles declared in three locations (spec §2 headers, orchestrator bullets, principle source file H1) using two deliberate forms — the spec carries the full descriptive title (optionally with parenthetical sub-title), while the orchestrator and principle source file carry the short form. Includes:
  - A 7-row example table showing the pattern for P4, P7, P8, P12, P14, P15, P16.
  - Three invariants (spec is canon for cross-refs; orch/file short forms must match; short form is main title before parenthetical or coherent shorter phrasing).
  - Rationale for coexistence (pedagogical completeness vs visual compactness).
  - P13 noted exception ("Hooks" as vernacular) with rationale and "can be revisited" note.

### Changed
- **`CLAUDE.md` — "Cross-reference convention" subsection** — the forward-reference to the principle-title section (previously saying "pending addition to CLAUDE.md") is updated to point to the now-present section.

### Notes
- This commit closes the 3 durable-rule tasks from the audit session (PEDAGOGY done in v0.48.0, BACKWARD-COMPAT + Cross-ref in v0.49.0, PRINCIPLE-TITLES here).
- CLAUDE.md now documents 5 governance rules: Build pipeline (existing), Tool architecture (existing), Versioning (existing), Pre-release backward-compat (new v0.49.0), Cross-reference convention (new v0.49.0), Principle title convention (new here), Memory policy (existing), Communication style (Rule 1 + Rule 2, existing).
- 49 unit tests pass; cross-platform parity identical.

## [0.49.0] - 2026-04-22

Layers impacted: **CLAUDE.md only** (methodology governance rules)

**Option B — Batch consolidation of durable CLAUDE.md rules.** Consolidates two rules adopted during the 2026-04-22 post-audit session into `CLAUDE.md` where they belong (per the existing "Memory policy — in-repo only" invariant that forbids Claude auto-memory for project conventions). These rules apply to all future sessions and to forkers.

### Added
- **`CLAUDE.md` — "Pre-release backward-compatibility — not required (temporary rule)"** subsection added under Critical rules (between Versioning and Files to keep in sync). Documents that while the GSE-One plugin is not yet distributed to public end users, schema changes, field renames, enum modifications, and artefact structure refactoring may be applied directly without migration paths. Rule self-dates: will be removed at first public release (Claude/Cursor marketplace, npm) with a pointer to replace it with post-release SemVer discipline. Rationale: pre-release iteration speed vs locking in unripe schema debt.
- **`CLAUDE.md` — "Cross-reference convention — 'number + name'"** subsection added under Critical rules (between Files to keep in sync and Memory policy). Documents the rule adopted during v0.48.6 P11: cross-references to sections / steps / numbered artefacts MUST include both the numeric identifier AND the section/step name (e.g., `§14.3 Step 1.6 — "Dependency vulnerability check"` rather than `§14.3 Step 1.6`). Includes 6 example forms (✅ and ❌), the stability rationale, application guidance (new refs follow the rule, opportunistic upgrades for existing refs, bulk sweep tracked as `P-NAMED-REFS`), and 3 edge cases (principles cited by ID, intra-document refs, title conventions).

### Notes
- This commit intentionally touches only `CLAUDE.md` — no methodology source files are modified. The 2 sections added are governance rules for future work.
- Rules already in `CLAUDE.md`'s "Communication style" section (Rule 1 pedagogical phrasing, Rule 2 single-default questions — both added in v0.48.0) remain unchanged.
- Deferred work (to be handled separately): `PRINCIPLE-TITLES` convention (pending user decision after explanation); `META.1` numeric registry centralization (big chantier — see `_LOCAL/maintenance/2026-04-21-numeric-registry-centralization.md`); `P-NAMED-REFS` retroactive cross-reference sweep across the whole corpus.
- 49 unit tests pass; cross-platform parity identical; `audit.py` numeric category clean (post-P14).

## [0.48.9] - 2026-04-22

Layers impacted: **maintainer tooling** (`gse-one/audit.py` only)

**Post-audit proposition P14 — Audit engine hygiene.** The numeric-drift category of `gse-one/audit.py` (invoked by `/gse-audit` and standalone) produced 8 false positives during the 2026-04-21 audit cycle. Root cause: three regex imprecisions (no distinction between descriptive text and historical CHANGELOG entries; no handling of section numbers; no semantic filter between "specialized agents" and "specialized templates"). Fixed all three.

### Fixed
- **`audit.py` `audit_numeric()` — CHANGELOG.md removed from scan.** The CHANGELOG documents historical states (e.g., "Agent count — '8 specialized' updated to '10 specialized'" is an entry that DOCUMENTS the fix that went from 8→10). Flagging these as drifts is sclerotically wrong — you'd rewrite history to "fix" it. CHANGELOG remains scanned by other categories (todos, broken links) where its content is relevant; only the numeric-claim scan ignores it.
- **`audit.py` `audit_numeric()` — regex prefix `(?:^|\s)` added to all 3 patterns.** The patterns `(\d+)\s+specialized`, `(\d+)\s+commands?`, `(\d+)\s+principles?` previously matched the digit suffix of section numbers (e.g., "10 Commands" in "### 3.10 Commands") and principle identifiers (e.g., "10 principle" in "P10 principle rule 8"). The new prefix requires the digit to be preceded by whitespace or a start-of-line, excluding these positional false positives while preserving legitimate matches like "23 commands" or "has 10 specialized agents".
- **`audit.py` `audit_numeric()` — negative lookahead on `specialized` pattern.** Added `(?!\s+(?:templates?|files?|Dockerfiles?|rules?|settings?|categories?))` to exclude "4 specialized templates" (Dockerfile count context) while preserving "10 specialized agents", "10 specialized + orchestrator", etc. The exclusion list is open-ended — forkers can add more terms if they hit other false-positive contexts.

### Verification
- Before P14: 8 warnings in `numeric` category, all false positives.
- After P14: 0 warnings in `numeric` category; 1 info entry "numeric claims consistent across 39 files (23 commands, 10 specialized agents, 16 principles)".
- Other categories unchanged (3 warnings remain in cross_refs + links + test_coverage, unrelated to P14).
- Ran `python3 gse-one/audit.py --format json --no-save` to verify.

### Not applied
- **LLM sub-agent false positive on "Arguments: $ARGUMENTS" line in deploy.md and hug.md** — this was the `activities-structure-uniformity` LLM sub-agent misreading the files (both files DO have the line). Prompt-level improvement, not a `audit.py` code fix. Deferred; will address if the issue recurs.

### Notes
- 1 file modified (`gse-one/audit.py`), no regen impact (audit.py is not part of the distributed plugin — it's a maintainer tool alongside `gse_generate.py`).
- Cross-platform parity identical; 49 unit tests pass.
- Anti-rigidity preserved: the negative lookahead is open-ended (add words without restructuring), CHANGELOG exclusion narrows the scan scope (reduces false positives without constraining real findings).

## [0.48.8] - 2026-04-22

Layers impacted: **implementation** (`principles/iterative-incremental.md` only)

**Post-audit proposition P13 — Principle title alignment (minimalist scope).** The audit flagged title drift across spec/orchestrator/principle file for P1, P4, P7, P8, P11, P12, P13, P14, P15, P16 (10 principles). Analysis revealed only 1 real bug; the other 9 cases follow an intentional "spec long title / implementation short title" pattern that is consistent between orchestrator and principle source files. Fixed only the single genuine divergence and documented the convention.

### Fixed
- **`gse-one/src/principles/iterative-incremental.md` H1** — "P1 — Iterative-Incremental Development" → "P1 — Iterative & Incremental". The file was the sole source using "Iterative-Incremental Development" (with hyphen and "Development" suffix) while the orchestrator bullet used "Iterative & Incremental" (with ampersand, no suffix) and the spec §2 used "Iterative & Incremental Lifecycle". The three-way divergence is eliminated by aligning the file on the orchestrator's short form.

### Adopted (methodology convention, to be documented in CLAUDE.md at next batch)
- **Principle title pattern — "spec long / implementation short"**:
  - **Spec §2 headers** carry the full descriptive title, optionally with a parenthetical sub-title (e.g., "Knowledge Transfer (Coaching)", "Agent Fallibility (Self-Awareness)", "Consequence Visibility (Risk Analysis Presentation)"). The full form is pedagogical and stable for cross-references under the "number + name" convention (P-NAMED-REFS task).
  - **Orchestrator bullets + principle source file H1** use the short form: main title before any parenthetical, or a coherent shorter phrasing. Example: spec "Knowledge Transfer (Coaching)" → short "Knowledge Transfer"; spec "Risk-Based Decision Classification" → short "Risk Classification".
  - **Critical rule**: the short form MUST be identical between orchestrator and principle file. Divergences between these two sources are bugs (as was the P1 case fixed above).
  - **P13 noted exception**: the spec title "Event-Driven Behaviors (Hooks)" uses "Event-Driven Behaviors" as the main title and "(Hooks)" as the parenthetical. However, the orchestrator and principle file use "Hooks" (the parenthetical) as their short form — inverted from the usual pattern. This is preserved as vernacular usage: "Hooks" is the term used throughout the methodology (`hooks.claude.json`, `PreToolUse hooks`, etc.). Can be revisited later if it causes confusion.

### Not applied (after analysis — intentional pattern, not bugs)
- **P4, P7, P8, P11, P12, P13, P14, P15, P16** — 9 principles flagged by the audit as having divergent titles. On inspection: orchestrator and principle file use the short form consistently with each other; spec §2 uses the long form. This is not an error — it's a deliberate two-form convention that the audit mis-classified as drift. Forcing spec long form into all sources would add verbosity without methodological benefit, violating the anti-rigidity principle.

### Notes
- 1 file modified + CHANGELOG entry + new task (`PRINCIPLE-TITLES`) to add the convention to CLAUDE.md at next batch.
- 49 unit tests pass, cross-platform parity identical.

## [0.48.7] - 2026-04-22

Layers impacted: **implementation** (`deploy.md` only)

**Post-audit proposition P12 — deploy.md targeted structural alignment.** The audit flagged 4 structural divergences between `deploy.md` and the other 22 activities. On inspection, only 2 were genuine style alignments; 1 was a legitimate intentional structural choice to preserve (not force-align); 1 was a false positive from the audit.

### Changed
- **`deploy.md:11` Options table header** — `| Flag | Description |` → `| Flag / Sub-command | Description |`, matching the canonical form used by the 22 other activities. The column can contain either a flag (e.g., `--silent`) or a sub-command-style trigger (e.g., `--training-init`), so the wider label is informative.
- **`deploy.md:25` Prerequisites preamble** — `Read before execution:` → `Before executing, read:`, matching the canonical form. Semantics identical, word-order aligned for scanning consistency across the corpus.

### Added
- **`deploy.md:34` Workflow structure note** — new short explanatory paragraph inserted at the top of the `## Workflow` section, documenting `/gse:deploy`'s two-level Phase/Step hierarchy. The note explains that this structure is deliberate and specific to `/gse:deploy`, reflecting the idempotent-milestone nature of deployment (each `### Phase N` is tracked in `.gse/deploy.json → phases_completed.<phase_name>` and can be skipped on re-run; `Step N` inside a Phase is a sub-step). Rationale: renaming `Phase N` → `Step N` to force uniformity with other activities would lose this semantic and require inventing new sub-step terminology. Documenting the exception is the anti-rigidity choice — the divergence is intentional, not accidental.

### Not applied (audit false positive)
- **Audit finding "`deploy.md` and `hug.md` miss `Arguments: $ARGUMENTS` line"** — verified incorrect. Both files have the line on line 7. No action needed. Audit engine hygiene (task P14) will cover this class of false positive.

### Notes
- 3 modifications in a single file (deploy.md). Other 22 activities untouched — they were already canonical.
- 49 unit tests pass, cross-platform parity identical.
- The anti-rigidity principle (adopted 2026-04-21) was explicitly invoked to reject the naive "rename all Phase to Step" approach. Deploy.md's internal structure carries methodological meaning (milestone idempotence via `phases_completed`) and the correct response was to document the convention, not erase it.

## [0.48.6] - 2026-04-22

Layers impacted: **design** (§13, §14, §3.2), **implementation** (`deliver.md`, `coach.md`)

**Post-audit proposition P11 — Broken cross-references and stale mentions cleanup.** A bundle of 6 surgical fixes: 2 broken cross-references, 1 strengthened historical disclaimer, 2 frozen version numbers in design examples, 1 obsolete historical phrase in an agent description. New cross-reference convention adopted on the same day (`P-NAMED-REFS` task created for retroactive sweep of the whole corpus).

### Fixed
- **`deliver.md` Step 0 (line 54) broken reference** — "Cleanup happens at the next `/gse:deliver` (see Step 10)" replaced with "(see Step 8 — Cleanup Backup Tags)". `deliver.md` only has Steps 0-9; the non-existent "Step 10" was a historical number that never survived a renumbering. The replacement uses the new "number + name" convention for stability.
- **Design §14 Open Questions row 6 (line 2806) self-contradictory step reference** — the cell said "runs at `/gse:go` Step 2.5 (spec §14.3 Step 1.6)", contradicting itself. Corrected to "runs at `/gse:go` Step 1.6 — 'Dependency vulnerability check' (defined in spec §14.3 Step 1.6 — 'Dependency vulnerability check')". Both references now carry the step name for stability.

### Changed
- **Design §13 vintage disclaimer strengthened** — the existing "Note on opencode" at line 2747 only warned about opencode's retrofit but did not warn about the other stale content in §13 (principle counts like "4 core principles" + "6 remaining" = 10, contradicting the current 16). New disclaimer makes the historical nature of ALL numeric counts in §13 explicit and points to authoritative sources with named references: §11.1 "Generation Steps", §12 "File Inventory", spec §2 "Core Principles".
- **Design §3.2 Plugin Manifest examples (lines 100, 118)** — frozen `"version": "0.16.0"` replaced with `"X.Y.Z"` placeholder on both the Claude and Cursor manifest JSON blocks. Explanatory note added above each block: *"example; `"version"` is generated from the `VERSION` file by `gse_generate.py` at build time, so the `"X.Y.Z"` placeholder below is illustrative"*.
- **`coach.md` frontmatter description** — removed the historical phrase "Absorbs the v0.36 tutor agent." which was a changelog-style mention polluting the description field. The other 9 specialized agents have purely declarative descriptions about their current role — `coach.md` is now consistent. Historical information preserved in `CHANGELOG.md` v0.36 entry.

### Adopted (methodology convention)
- **"Number + name" cross-reference convention** — cross-references to sections/steps must include both the numeric identifier (for quick navigation) and the section/step name (for stability when renumbering occurs). Example: `§14.3 Step 1.6 — "Dependency vulnerability check"` instead of just `§14.3 Step 1.6`. Retroactive sweep of existing references is captured as task `P-NAMED-REFS` (deferred — will run after P12-P14). The rule itself will be added to `CLAUDE.md` Communication style section at the next CLAUDE.md batch.

### Notes
- Fixes (1), (2) apply the new naming convention immediately. Fixes (3), (4), (5) did not involve numeric-only cross-references.
- No regeneration impact beyond the natural flow through the generator; `coach.md` and `deliver.md` propagate to their Claude/Cursor/opencode copies.
- 49 unit tests pass, cross-platform parity identical.

## [0.48.5] - 2026-04-22

Layers impacted: **spec** (§3.2.1), **implementation** (`hug.md`)

**Post-audit proposition P10 — `project_domain` enum unification.** Three sources listed different values for the same `project_domain` enumeration: template `profile.yaml` (9 values, canonical) had `web | api | cli | data | mobile | embedded | library | scientific | other`; activity `hug.md:98` had 7 (missing `library` and `scientific`); spec §3.2.1:1143 had 6 capitalized examples (`Web / Embedded / Scientific / CLI / Library / Mobile`, missing `api`, `data`, `other`). Aligned hug.md and spec on the 9-value canonical lowercase form.

### Changed
- **`hug.md:98` Dimension 8 "Project domain" values** — added `library` and `scientific` to the enumeration presented to users during HUG interview. Previously users working on a code library or a scientific/research project had to fall back on `other`, losing the domain-specific calibrations (test pyramid, activity skip rules, velocity baselines).
- **Spec §3.2.1:1143 "Project domain" examples** — now lists the 9 canonical lowercase values with an explicit pointer to the authoritative schema (`plugin/templates/profile.yaml`). Previously listed only 6 capitalized examples, which was ambiguous (case-sensitive vs not? examples of a larger set or the full enum?). The clarification note `(9 canonical values — see ...)` removes both ambiguities.

### Notes
- No changes to `profile.yaml` or `config.yaml` templates — they were already the canonical sources with correct 9-value lists. The drift was strictly in descriptive layers (spec + activity prose).
- Users whose projects legitimately fall into `library` or `scientific` categories will now receive proper domain-specific behavior: test pyramids per spec §6.1 (Library/SDK and Scientific rows), conditional skip of `/gse:preview` (non-UI domains), etc.
- No regeneration impact beyond the natural flow through generator to plugin/skills + plugin/commands for the hug activity.

## [0.48.4] - 2026-04-22

Layers impacted: **spec** (§P14, §12.2 enum), **implementation** (`learning-note.md` template, `knowledge-transfer.md` principle)

**Post-audit proposition P9 — Learning-note frontmatter unification.** Three sources (template, spec §P14, principle file) used a legacy `gse:` nested schema for learning notes, while the activity `learn.md` Step 4 used a flat `id: LRN-NNN` + `artefact_type: learning` schema consistent with the document-level artefact pattern established by `intent.md`. This created a 3-way contradiction. Resolution: align all sources on the flat schema (the canonical form per spec §4 traceability table which lists `LRN-` as a prefix, and per `MANIFEST.yaml` which declares the filename pattern `LRN-{NNN}-{topic-slug}.md`).

### Changed
- **Template `gse-one/src/templates/learning-note.md`** — rewrote frontmatter from the nested `gse:{type,topic,sprint,mode,trigger,related_activity,traces,created}` form to the flat form `id / artefact_type / title / topic / sprint / status / mode / trigger / related_activity / author / created / traces:{triggered_by, derives_from}`. Added previously-missing fields: `id` (canonical prefix per spec §4), `title`, `status`, `author`, `traces.triggered_by`. Content sections of the template (Key Concepts / How This Applies to Your Project / Practice Exercise / Quick Reference Card) unchanged.
- **Spec §P14 frontmatter example (lines 853-865)** — rewrote to the same flat format as the template. Now consistent with `learn.md` Step 4 and with `intent.md` (the existing document-level artefact precedent).
- **Spec §P14 path example (line 893)** — `docs/learning/testing-strategies.md` → `docs/learning/LRN-{NNN}-testing-strategies.md`, matching `MANIFEST.yaml` ligne 123 target pattern.
- **Spec §12.2 `gse.type` enumeration (line 2169)** — removed `learning-note` from the list. The `gse.type` field lives in the *nested* frontmatter schema used by section-level artefacts (requirements, designs, tests, reviews, plan-summary, compound, decision, code, test-campaign — all multi-artefact-per-file). Document-level artefacts (intent, learning) use the flat schema with `artefact_type:` at the top level and do not belong in this enum. `intent` was already absent from the list — the removal of `learning-note` completes the separation.
- **Principle `gse-one/src/principles/knowledge-transfer.md` frontmatter example (lines 65-79)** — rewrote to the same flat format. Added explanatory note: *"flat schema, per spec §P14 canonical format"*.
- **Principle filename tree (lines 57-64)** — `git-branching.md`/etc. → `LRN-001-git-branching.md`/etc. Tree preamble rewritten to point to the canonical MANIFEST pattern.

### Notes
- Plugin not yet distributed — schema change applied directly without migration path. No generated learning notes exist in production user projects yet; future notes will be created with the flat schema from day one.
- `learn.md` Step 4 (the activity that actually creates learning notes) was already correct and unchanged. The work was to align the descriptive sources (template, spec, principle) with the prescriptive activity.
- No impact on MANIFEST.yaml (already correct), `coach.md` (only references `docs/learning/LRN-*` pattern), or any other file. Cross-platform parity identical; 49 unit tests pass.

## [0.48.3] - 2026-04-22

Layers impacted: **implementation** (`principles/knowledge-transfer.md` only)

**Post-audit proposition P8 — P14 preamble labels sweep (principle file).** The spec §P14 (lines 935-945) declares the 5-option learning-preamble labels as canonical — explicitly stating "Labels are canonical — implementations use this exact wording." A previous version sweep aligned spec, `learn.md`, `coach.md`, and `gse-orchestrator.md` to the canonical form. The principle source file `gse-one/src/principles/knowledge-transfer.md` was missed. P8 fixes that omission.

### Fixed
- **`knowledge-transfer.md` Example 1 (Merge strategies, lines 45-46)** — option labels `Yes, quick overview (5 min)` and `Yes, deeper session (15 min)` now match the canonical `Quick overview (5 min)` and `Deep session (15 min)` (spec §P14 lines 939-940). Descriptions after the em-dash are preserved (they are context-adapted per axis — the label before the em-dash is what must be canonical).
- **`knowledge-transfer.md` Example 2 (Acceptance criteria, lines 159-160)** — same two label corrections.

### Notes
- Options 3 (`Not now`), 4 (`Not interested`), 5 (`Discuss`) were already canonical in both examples; no change.
- Descriptions after the em-dash remain context-adapted ("key concepts + examples from your REQs" etc.) — this is the documented pattern: the label identifies the option canonically, the description is tailored to the pedagogy topic.
- No spec/design/template/tool changes — the canonical source of truth (spec §P14) was already correct; the work is fully inside the principle source file whose prose had drifted.
- 4 lines changed in 1 source file; plugin/ regens propagate to `plugin/skills/*`, `plugin/commands/*`, `plugin/opencode/*` where applicable.

## [0.48.2] - 2026-04-22

Layers impacted: **implementation** (`pause.md` only)

**Post-audit proposition P7 — State-management errors in `pause.md`.** Two localized bugs in the `/gse:pause` activity (session pause — auto-commit active worktrees and save a checkpoint for later resume).

### Fixed
- **`pause.md` Step 2 duplicate line with invalid nested path removed.** The list of checkpoint fields to populate previously contained both `checkpoint.timestamp: current ISO 8601 timestamp` (using a nested path that has no corresponding structure in the `checkpoint.yaml` template) AND `timestamp: ISO 8601 current time` (flat, correct). The nested-path line was a historical editing artifact — deleting it removes the ambiguity. The surviving flat line gains a parenthetical annotation ("flat top-level field per `checkpoint.yaml` schema") to prevent the duplication from recurring.
- **`pause.md` Step 1 orphan field `git.last_pause_commit` replaced by schema-declared `git.last_commit`.** The activity previously wrote `git.last_pause_commit: {hash}` into each TASK entry's `git:` block in `backlog.yaml`. This field was undeclared in the `backlog.yaml` template schema AND had no reader anywhere in the repo (`resume.md` uses `saved_last_commit` from the checkpoint file, not from backlog). Since pause creates a real commit, it now updates the schema-declared `git.last_commit: {ISO 8601 timestamp}` field instead — aligning the behavior with the existing schema and giving the field a real-time semantic (previously unused).

### Notes
- Plugin is not yet distributed to end users, so backward-compatibility is not required. Schema changes can remove or rename fields without migration paths. This rule will be added to CLAUDE.md at the next batch update.
- No spec/design modifications — the spec does not descend to this level of per-activity field lists, and the design does not describe `pause.md` line-by-line. The work is fully localized to the implementation layer of a single file.
- No impact on `backlog.yaml` template (already correct — `last_commit` is declared, `last_pause_commit` was never part of the schema) or on `checkpoint.yaml` template (already authoritative and flat). `resume.md` is unaffected — it reads from the checkpoint, not from the now-removed `last_pause_commit` backlog field.

## [0.48.1] - 2026-04-22

Layers impacted: **spec** (§12.3 origin enum, §13.1 deploy.app_type enum), **implementation** (3 activities: reqs.md, assess.md, backlog.md)

**Post-audit proposition P6 — Schema drift bundle (template ↔ activity ↔ spec).** Four small schema inconsistencies surfaced by the 2026-04-21 audit, grouped because they share the same root cause: the spec lagged behind the template + code (upward drifts), and two activities used invalid enum values (downward fixes).

### Changed
- **Spec §12.3 `origin` enum extended to 6 values** (was 5). The backlog.yaml template (line 23), task.md (line 95), and backlog.md (line 122) already declared and used the 6th value `ad-hoc` (for tasks created on-demand by `/gse:task` outside the sprint planning flow). The spec example block at line 2206 now documents the same 6-value enumeration: `plan | review | collect | user | import | ad-hoc`. **Upward refinement** — the spec catches up with the runtime reality.
- **Spec §13.1 `deploy.app_type` enum extended to 6 values** (was 4). The design doc §5.18 (line 2406) and the deploy.py tool already supported 6 values (`auto | streamlit | python | node | static | custom`). The spec example config block at line 2596 now matches: previously listed only `auto | python | streamlit | static`, missing `node` (for which a Dockerfile.node template exists) and `custom` (which bypasses template generation for user-provided Dockerfiles). **Upward refinement** — the spec catches up with the design + code.

### Fixed
- **`reqs.md` Step 8 persist block now includes `elicitation_summary`** — Step 0.5 ("Needs Elicitation") mandates saving a résumé of the user's stated needs plus the agent's reformulation into the `elicitation_summary` frontmatter field. The template `sprint/reqs.md` (line 6) includes this field as part of the canonical schema. But Step 8's persist block (the YAML frontmatter the activity writes at file creation time) previously omitted the field, meaning agents executing `/gse:reqs` could silently skip it. Step 8 now lists `elicitation_summary: "{user's original words + agent's reformulation from Step 0.5}"` inline in the persisted YAML.
- **`assess.md` Step 5 no longer writes an invalid status value** — previously said "Set `status: pool` and `sprint: null`" when creating candidate tasks from assessment gaps. `pool` is NOT a valid value of the TASK status enumeration (the canonical 8 values are `open | planned | in-progress | review | fixing | done | delivered | deferred` per `backlog.yaml` template line 19). The pool concept is expressed by the combination `status: open` + `sprint: null`, not by a status value named "pool". Fixed to `status: open` with a parenthetical clarification for readers.
- **`backlog.md` Step 3 GitHub-sync mapping table corrected** — the first row previously mapped a non-existent GSE-One status `pool` to GitHub `open (label: pool)`. Rewrote the first column header from "GSE-One Status" to "GSE-One Status (+ condition)" and the first row to `open` AND `sprint: null (pool)`, which reflects the actual data model. GitHub side keeps the `pool` label (meaningful as a GitHub Issue classifier).

### Notes
- No modifications to `backlog.yaml` template, the orchestrator, the `origin` enum at the template level, or `deploy.py` — those were already correct. Work was on the *descriptive* and *prescriptive* layers (spec + 3 activities) to match the runtime reality.
- No regeneration impact — 3 activity files touched flow through the generator to `plugin/skills/*/SKILL.md` and `plugin/commands/gse-*.md`. Verified via `--verify`.

## [0.48.0] - 2026-04-22

Layers impacted: **spec** (no change — already canonical), **design** (§11.1 + §12 count alignment, new `--verify` paragraph), **implementation** (6 agents, 4 activities, 1 template, generator), **CLAUDE.md** (archetype table + communication rules)

**Post-audit propositions P1–P5 batched commit.** Five methodology coherence fixes surfaced by the 2026-04-21 /gse-audit run, applied incrementally with explicit user validation per proposition. Audit report archive: `_LOCAL/audits/audit-2026-04-21-112532-v0.47.10.md`.

### Added
- **New agent archetype `Compliance`** — `guardrail-enforcer` moved from Reviewer archetype to a dedicated Compliance archetype in `CLAUDE.md`. Rationale: guardrail-enforcer emits real-time action alerts (`GUARD-NNN` + `EMERGENCY/HARD/SOFT` guardrail tiers carrying action semantics WARN/BLOCK/HALT), not artefact review findings. Forcing HIGH/MEDIUM/LOW would lose the tier semantics. Archetype count: 5 (Identity, Reviewer [7 agents], Operational, Observational, Compliance).
- **Coach invocation contract now implemented in 4 activities** — per `coach.md:44-55`. New steps: `pause.md` Step 3.5 (moment `/gse:pause`, axes 2-8 — sustainability + engagement end-of-session check); `compound.md` Step 2.0 (moment `/gse:compound Axe 2 feed`, axes 2-8 — cross-sprint trend analysis); `compound.md` Step 3 intro paragraph (moment `/gse:compound Axe 3 feed`, axes 1+2 — pedagogy + profile drift); `plan.md --strategic` Step 0.6 (moment `sprint promotion`, axes 3+4+5+8 — retrospective cross-sprint analysis). Previously these moments existed only in coach.md's contract without corresponding activity-side invocation — 3 of 8 coach axes (quality_trends, sprint_velocity, sustainability) were silently inoperant.
- **`compound.md` Step 2.7 — "Summarize raw workflow observations (coach ledger maintenance)"** — new substep describing the ledger maintenance mechanism: group raw entries by axis, produce one condensed summary entry per axis, mark with `summarized: true`, keep growth bounded (≤ 7 entries per sprint). Format of summary entries left to the coach's judgment (anti-rigidity).
- **`gse_generate.py` — new `verify_external_docs()` function** — warning-level check asserting hand-maintained docs (README.md, install.py, gse-one/README.md) mention the expected counts derived from source-of-truth registries (`SPECIALIZED_AGENTS`, `ACTIVITY_NAMES`, `src/templates/`, `src/principles/`). Non-blocking by design — prose must be able to evolve, localize, and reformulate without breaking the build. Definitive numeric-drift audit remains in `gse-one/audit.py`.
- **CLAUDE.md — new "Communication style (development sessions)" section** — two durable rules for Claude during interactive sessions: (1) pedagogical phrasing with parenthetical term reminders, no cryptic jargon chains; (2) propositions must use single-default questions, one action per question, with the default explicitly stated.

### Changed
- **`workflow_observations[]` lifecycle clarified across 4 files** — design §5.17 was already correct ("persistent cross-sprint ledger for trending, summarized at /gse:compound"). The template (`status.yaml:67-70`), orchestrator description (`gse-orchestrator.md:160`), and coach agent (`coach.md:152`) previously claimed "transient, cleared at sprint close", contradicting the design and breaking the 3 trend-based axes (quality_trends, sprint_velocity, sustainability) that each require ≥ 3 sprints of history. All three are now aligned with the design.
- **`review.md` Step 6 FIX insertion threshold** — now says "HIGH or MEDIUM findings → `status: fixing`" (was "HIGH only"). Aligns with spec §14, design §10.1, and `plan.yaml` template comment — previously 3 of 4 sources said HIGH-or-MEDIUM while review.md said HIGH-only, forcing `fix.md` Step 1.4 to compensate at runtime. User retains `/gse:fix --severity HIGH` for scope narrowing.
- **`code-reviewer.md`** aligned to Reviewer archetype — added missing `perspective: code-reviewer` field on all 3 RVW examples, added `(baseline)` qualifier to severity legend, added CRITICAL reservation note (all 6 other Reviewer agents already had these).
- **Fix-label prose harmonized to `Suggestion:`** in `code-reviewer.md` and `security-auditor.md` (was `Fix:`), matching the canonical YAML schema field name `suggestion:` in `review.md` Step 4 and the majority pattern (architect, requirements-analyst, test-strategist, ux-advocate). `devil-advocate.md` intentionally retains `Action:` — more directive semantics appropriate for AI-integrity findings (hallucinations, fabrications).
- **`gse-one-implementation-design.md` §11.1 + §12** — templates count 28 → 29 (actual count excluding MANIFEST.yaml descriptor). Grand total file count 150 → 151. Added §11.1 paragraph documenting what `--verify` asserts (plugin structure, body parity, guardrails patterns, external-docs warning-level check).

### Fixed
- **Numeric drift across user-facing docs**: `install.py:726` now emits "10 specialized agents" (was "8"). `README.md` arborescence: "11 agents (10 specialized + orchestrator)", "29 templates", "10 specialized (mode: subagent)". `gse-one/README.md` arborescence: same pattern + "29 artefact & config templates". `gse-one/gse_generate.py` docstring: "29 artefact & config templates" and "Shared (29 templates)". `CHANGELOG.md` historical entries and section numbers like "§3.10 Commands" intentionally NOT modified (historical record / false positives flagged by audit engine).

### Deferred (planned work captured in `_LOCAL/maintenance/`)
- **META.1 — Numeric Registry Centralization** — structural fix for numeric drift via per-document `{doc}_registry.md` files regenerated from SSOT registries, prose references instead of inlined counts. Full plan in `_LOCAL/maintenance/2026-04-21-numeric-registry-centralization.md`. Execute after remaining audit propositions (P6–P14).
- **P-MOMENT-TAGS** — unify coach moment tag vocabulary (currently natural-language in `coach.md:44-55` vs snake_case in `design §5.17:2200-2212`). Flagged as warning in audit.

### Notes
- No spec modifications in this release — all spec-level rules were already canonical. The work consisted of aligning design, implementation, and CLAUDE.md to the spec (downward refinement) plus one upward propagation (`workflow_observations` lifecycle — design was source of truth, other layers were stale).
- VERSION bumped to 0.48.0 (minor) because of new archetype (Compliance), new coach invocation moments (structural activity changes), and new summarization mechanism (semantic lifecycle change). Individual propositions were pure fixes, but the aggregate crosses into feature territory.

## [0.47.10] - 2026-04-21

Layers impacted: **design** (docs only)

**Methodology coherence pass — tenth batch (closure)** from the /gse-audit run against v0.45.0. Closes the sole remaining audit item deferred from Prop 9 (structural spec/design corrections).

### Changed
- **design §14 Open Questions** — added explicit `Status` column (OPEN / RESOLVED / DEFERRED) and renamed `Recommendation` to `Recommendation / Resolution` across all 10 entries. Each row now clearly states whether the recommendation is implemented in current code or still pending:
  - **RESOLVED (6):** #1 orchestrator principles embedding; #5 lazy worktree creation; #6 branch-level git hygiene + dependency audit; #7 `.gse/` main-only; #8 contextual tip frequency caps; #10 state-recovery resilience.
  - **OPEN (4):** #2 Cursor marketplace + npm packaging (Claude marketplace done); #3 `.gse/` version upgrades (field done, migration logic pending); #4 git conflicts during deliver (no 3-option Gate); #9 external source shallow-clone caching (throwaway currently).
- Entry #1 un-strike-through'd: keeping a single plain "RESOLVED" label is more readable than mixing strikethrough for one row vs plain text for nine others.

### Notes
- Pure documentation change in the design doc. No plugin impact, no behavioral change.
- The 4 OPEN items are now actionable pending tasks with explicit "what's done vs what remains" text. They can be promoted to individual propositions in a future audit cycle.
- This closes the treatment plan from the initial /gse-audit run against v0.45.0: **16 of 16 propositions delivered** over commits v0.47.1 → v0.47.10.

## [0.47.9] - 2026-04-21

Layers impacted: **implementation**, **docs** (agents uniformity + archetype documentation)

**Methodology coherence pass — ninth batch (final mechanical pass)** from the /gse-audit run against v0.45.0. Closes the agent-file uniformity findings while deliberately preserving legitimate archetype differences.

### Fixed
- **Output Format heading casing** unified across agents:
  - `deploy-operator.md`: "Output format" (lowercase f) → "Output Format"
  - `coach.md`: "Output formats" (lowercase f) → "Output Formats" (plural preserved — coach legitimately has 3 output formats: skip, propose, advise)
  - 8 other agents already on "Output Format" — unchanged.
- **gse-orchestrator.md header** — added canonical `**Role:**` and `**Activated by:**` lines + wrapped the opening narrative in `## Perspective`. All 10 other agents use this structure; the orchestrator was the sole exception. Now any parser / `/gse-audit` sub-agent / forker reading the agent frontmatter finds consistent metadata.

### Added
- **CLAUDE.md `## Agent archetypes` section** documenting the 4 deliberate structural archetypes:
  - **Identity** (gse-orchestrator) — orchestrator-specific structure
  - **Reviewer** (8 agents) — Checklist + Output Format pattern (output to review.md)
  - **Operational** (deploy-operator) — Required readings + Core Principles + Anti-patterns
  - **Observational** (coach) — 8 axes + Invocation contract + Recipes + Persistence
  
  This documentation prevents future confusion about "why don't all agents have the same structure" — the differences are intentional and reflect distinct agent roles. The common elements (frontmatter, Role/Activated by/Perspective, finding output format) are called out.

### Notes
- Closes Prop 15 of the Prop 1-15 audit treatment plan. 14 of 15 props completed; 1 item deferred (design §14 Open Questions status labeling, pending per-row judgment).
- No spec or design edit — purely agent file uniformity + developer documentation.

## [0.47.8] - 2026-04-21

Layers impacted: **implementation**, **templates** (state management cluster pass)

**Methodology coherence pass — eighth batch** from the /gse-audit run against v0.45.0. Six state-management drifts: stale hardcoded version, missing pause/resume fields, task.md using the wrong YAML shape (mapping vs list), backlog schema incomplete, config enum missing Micro, deploy templates still marked PENDING, and one config key referenced but non-existent.

### Fixed
- **`status.yaml` template `gse_version: "0.9.0"`** hardcoded → `""` (filled by /gse:hug from VERSION registry). Prevents newly-seeded projects from inheriting a stale version.
- **`status.yaml` template missing `session_paused` and `pause_checkpoint`** added. Previously written by pause.md Step 3 and cleared by resume.md Step 6, but the template didn't declare them — schema drift.
- **task.md §Step 3 YAML shape** fixed: was writing `TASK-{next_id}: {fields}` (mapping form) into `items: []` (list). YAML-incompatible — would either corrupt backlog or write to the wrong location. Now uses canonical list-of-objects form `- id: TASK-{next_id}\n  title: ...`.
- **task.md field names** aligned on backlog.yaml template:
  - `source: ad-hoc` → `origin: ad-hoc` (template's canonical enum)
  - `created_at: {timestamp}` → `created: {ISO-8601 timestamp}` (template's field name)
  - Sprint values: `S{NN}` → `{NN}` (integer, as template specifies)
  - Added `priority`, `traces`, `git`, `github_issue`, `updated` fields to match template structure.
- **config.yaml `lifecycle.mode` comment** extended from `full | lightweight` to `full | lightweight | micro (see spec §13.2)`. Micro was a valid third mode already used elsewhere but the enum comment hid it.
- **MANIFEST.yaml deploy PENDING block removed** — `/gse:deploy` is production-ready since v0.42.0. Registered 8 deploy templates: `deploy.json`, `deploy-env.example`, `deploy-env-training.example`, `Dockerfile.streamlit`, `Dockerfile.python`, `Dockerfile.node`, `Dockerfile.static`, `.dockerignore`. MANIFEST now declares 29 templates (was 21).
- **backlog.md `github.issues_sync`** (non-existent config key) replaced with canonical `github.enabled: true AND github.sync_mode ∈ {on-activity, real-time}` across 2 occurrences. Prevents silent broken check.
- **backlog.md `github_issue` nesting** corrected: previously `github_issue: null` was placed **inside** `traces: {}`, but the backlog.yaml template has it at the item top-level. backlog.md example now matches.

### Changed
- **backlog.yaml template extended** with 8 new documented fields to formalize the canonical schema: `description`, `requires_review`, `completed_at`, and 4 spike-specific fields (`question`, `complexity_cap`, `deliverable`, `outcome`). All optional; existing backlogs remain valid.
- **config.yaml `project.domain` enum comment** aligned with the fused `project_domain` enum from Prop 6: `web | api | cli | data | mobile | embedded | library | scientific | other`. Previously used the old template enum `web | embedded | scientific | cli | library | mobile`.

### Notes
- No activity, agent, or principle added/removed.
- MANIFEST deploy entries now make the template system the single source of truth for what `/gse:deploy` copies into user projects.
- A future pass could address: checkpoint.yaml `health_score` flat vs status.yaml `health.score` nested naming asymmetry (cosmetic drift flagged by audit but not functional).

## [0.47.7] - 2026-04-21

Layers impacted: **spec**, **design**, **implementation** (coach/pedagogy cluster pass)

**Methodology coherence pass — seventh batch** from the /gse-audit run against v0.45.0. Targets coach axis naming drift (functional bug: config keys not matching), `workflow_observations[]` lifecycle contradiction, P14 preamble 5-option divergence across 3 documents, and a gap in spec coverage of the 7 workflow axes.

### Fixed
- **Coach axis naming** — design §5.17 output schema aligned on snake_case full names from coach.md: `sprint_velocity`, `workflow_health`, `quality_trends`, `engagement_pattern`, `process_deviation`, `sustainability`, `profile_calibration`. Previously design used shortened ambiguous tokens (`velocity`, `health`, `quality`, `engagement`, `deviation`, `profile-calibration` kebab) that did not match coach.md — breaking the `config.yaml → coach.axes.<name>: false` toggle (user-written snake_case would not match the design-side check).
- **`workflow_observations[]` lifecycle** — design §5.17 persistence table corrected from "Transient — cleared at sprint close after consumption by compound" to "**Persistent** — cross-sprint ledger for trending". Quality trends, sprint velocity, and sustainability axes all require ≥ 3 sprints of history to compute meaningful trends; purging at sprint close broke trending.
- **P14 preamble 5-option labels** unified across 3 documents onto canonical wording:
  - Option 1: "Quick overview (5 min) — concise introduction"
  - Option 2: "Deep session (15 min) — worked example + practice"
  - Options 3-5 unchanged (Not now / Not interested / Discuss).
  Previously: spec §P14 used "Yes, quick overview (5 min)" / "Yes, deeper session (15 min)"; learn.md used "Quick overview (5 min) — core REST principles" / "Deep dive (15 min) — REST design patterns"; coach.md used compact "Quick overview" / "Deep session". Now all three agree.

### Added
- **spec §P14 "Workflow monitoring axes"** subsection listing the 7 non-pedagogy axes (profile_calibration through sustainability) with signal source and output type per axis. Previously §P14 described pedagogy in detail but never enumerated the 7 workflow axes at the spec layer — readers had to discover them in design §5.17 or coach.md.
- **spec §P14 "P14 preamble — 5-option format (canonical)"** subsection formalizing the 5 options with their canonical labels and persistence rules (options 3/4 recorded in `status.yaml → learning_preambles[]`). Serves as the shared reference for coach.md / learn.md / orchestrator preambles.
- **go.md Step 2.8 "Coach Workflow Overview (post-recovery)"** — explicit invocation of the coach agent after recovery checks complete, activating axes 2-8 for cross-sprint drift signals. Previously coach.md cited "/gse:go after recovery" as an invocation moment but go.md didn't document the invocation.

### Changed
- **learn.md "Proactive Workflow" section** simplified to a pointer to coach.md + design §5.17 + spec §P14. Previously learn.md documented its own 4-trigger list (duplicating coach.md's 8 moments + design's 9 moments with different vocabulary). Now `/gse:learn` owns the Reactive path; the Proactive path is owned by the coach agent.
- **learn.md Structured Interaction Pattern** aligned on canonical 5-option labels.

### Notes
- No functional regression: the persistence change for `workflow_observations[]` enables trending that was implicitly required by quality_trends/velocity/sustainability axes. Existing projects with an empty `workflow_observations[]` list continue to work — the coach fills it across upcoming sprints.
- Open: design §5.17 invocation moments table (lines 2202-2212) uses tokens like `activity_start:/gse:*`, `compound_axe_3` which don't match coach.md's prose (e.g. "/gse:compound Axe 3 feed"). This is moment-naming convention (machine-facing vs human-facing) and is kept as-is for now — both are unambiguous and reference the same moments.

## [0.47.6] - 2026-04-21

Layers impacted: **implementation**, **templates** (delivery/compound cluster pass)

**Methodology coherence pass — sixth batch** from the /gse-audit run against v0.45.0. Targets deliver/compound/integrate cluster drifts: dangerous backup-tag format divergence, LC02/LC03 ambiguity, compound template axes mismatched with activity, integrate missing github.enabled gate, and template gaps.

### Fixed
- **Safety backup tag format** — deliver.md Step 0 was tagging the wrong ref (feature branch instead of integration branch) with a format (`gse-backup/sprint-{NN}-pre-merge-{type}-{name}` on `gse/sprint-{NN}/{type}/{name}`) that diverged from spec §10.6 and design §5.15. **Functional bug**: the merge-reversal procedure in spec §10.6:2023 (`git reset --hard gse-backup/...`) could not work because the tag didn't point at the right ref. deliver.md now documents **two tag classes** aligned with spec + design:
  - **Class 1 (merge reversal):** `gse-backup/sprint-{NN}-pre-merge-{type}-{name}` on `gse/sprint-{NN}/integration` BEFORE merge — enables `git reset --hard` rollback.
  - **Class 2 (branch recovery):** `gse-backup/sprint-{NN}-{type}-{name}-deleted` on `gse/sprint-{NN}/{type}/{name}` BEFORE branch delete — enables branch recreation.
- **LC02/LC03 deliver ambiguity** — deliver.md Step 9.3 write `current_phase: LC03` now carries an explicit comment: `/gse:deliver` is the **last LC02 activity** per spec §14 ladder; its Step 9.3 marks the post-delivery transition to LC03. Compound and integrate operate in LC03.
- **compound template Axis 2** renamed from "Ecosystem Feedback" to **"Methodology Capitalization"** with tables aligned on activity §2.1–§2.6 (Observations Gathered / Themes Consolidated / Closure Gate Outcome). Previous Ecosystem Feedback tables (Tool Effectiveness / Configuration Adjustments / Issues to Report) were never filled by the activity.
- **compound template Axis 3** renamed from "Development Governance" to **"Competency Capitalization"** with tables aligned on activity §3 (Learning Notes / Competency Map / Proactive LEARN Proposals). Previous Governance tables (Decision Tier Review / Guardrail Effectiveness / Process Improvements) were never filled.
- **integrate.md Axe 2 `github.enabled: false` short-circuit** — previously absent. compound.md already respected `github.enabled: false` (export local only), but integrate would still try to submit any pending `.gse/compound-tickets-draft.yaml`. Integrate now checks `github.enabled` first and deletes the draft file if disabled (user's intent is clearly "export only").

### Added
- **methodology-feedback.md template** extended with Theme 2 scaffold block, separator convention (`---` between themes), **Totals** section (observations/themes/severity split/route), and **Next steps** section. Previously the template ended after Theme 1 with no closing — users had no guidance on formatting additional themes.
- **compound.md Step 5 `.gse/plan.yaml` handling clarified** with explicit "no-op" sub-step. The durable sprint-plan archive is `docs/sprints/sprint-{NN}/plan-summary.md` (produced by `/gse:deliver` Step 9.1 with `gse.id: PLN-NNN` inherited); `.gse/plan.yaml` itself stays in place with `status: completed` (sprint-freeze marker) until `/gse:plan --strategic` opens the next sprint and overwrites it. Eliminates the audit's concern about plan.yaml getting stranded after sprint-directory archival.

### Notes
- compound.md Step 5 sub-step numbering shifted from 4 to 6 due to the new "plan.yaml handling" sub-step between archive accessibility and dashboard regeneration.
- These fixes close the delivery/compound cluster audit findings except for the two reported items (LC02/LC03 documentation and backup tag format) that were the most material.

## [0.47.5] - 2026-04-21

Layers impacted: **spec**, **design**, **implementation** (cross-cutting cluster pass)

**Methodology coherence pass — fifth batch** from the /gse-audit run against v0.45.0. Four cross-cutting defects around onboarding flow, artefact placement, mode-aware orchestration, and one upward refinement bringing design up to the implementation's quality.

### Fixed
- **`docs/intent.md` placement officialized** in spec §12.1 Project Layout. Previously, go.md wrote the artefact to `docs/intent.md` (top-level, correct since intent is project-level) but the spec's canonical layout diagram never mentioned it — artefact was effectively undocumented. Bonus: added `docs/sprints/sprint-NN/preview.md` (created in Prop 10) and `docs/archive/intent-vNN.md` (mentioned in §14.3 Step 5.7 pivot but absent from layout).
- **hug.md Step 4.2 now creates `config.yaml`** from the template when `.gse/` is scaffolded. Previously only `profile.yaml` was written, leaving `/gse:go` Step 6.3 (which writes `config.yaml.lifecycle.mode`) to crash on missing file. `checkpoints/` subdirectory also added explicitly.
- **health.md mode-awareness** added at the top of Step 1: Micro → skip entirely with Inform note; Lightweight → compute only the 3 dimensions mandated by spec §13.2 (`test_pass_rate`, `review_findings`, `git_hygiene`); Full → compute all 8. Frontmatter description updated to reflect the mode-dependent count.

### Changed
- **design §5.14 Step 2 decision tree** upgraded to plan.yaml-primary (mirrors go.md Step 3, which is the authoritative implementation). Previous table was file/status-based ("Sprint, tasks in-progress", "Sprint, tasks done, not reviewed") which predates the `plan.yaml.workflow.active` single source of truth. This is an **upward refinement** — the implementation was ahead of the design, now aligned.

### Notes
- No backward-compatibility break. Projects that already have `config.yaml` will not be overwritten — hug.md Step 4.2 creates it only if `.gse/` itself is being created.
- health.md mode branching assumes `config.yaml.lifecycle.mode` is populated. Older projects without this field default to Full behavior (backward compatible) — the agent should advise re-running `/gse:go` to set the mode explicitly.

## [0.47.4] - 2026-04-21

Layers impacted: **spec**, **implementation**, **templates** (sprint lifecycle schema drift pass)

**Methodology coherence pass — fourth batch** from the /gse-audit run against v0.45.0. Targets sprint lifecycle schema inconsistencies: DEC destination drift, ghost TASK status value, branch_status enum split, missing sprint template, PREVIEW sequence formulation, and hardcoded sprint-01 placeholders.

### Added
- **`src/templates/sprint/preview.md`** template. Previously, `preview.md` activity wrote `preview_variant`, `scaffold_path`, and `Inform-tier Decisions` to a file with no template reference — each sprint invented the schema. The new template formalizes: gse: namespace with `preview_variant` / `scaffold_path` frontmatter; sections for UI, API, Architecture, Data, Feature Walkthroughs, Import previews; Inform-tier Decisions closure section.
- **MANIFEST.yaml** entry for `sprint/preview.md → docs/sprints/sprint-{NN}/preview.md` (created_by: /gse:preview, scope: sprint).

### Fixed
- **DEC-NNN destination** in plan.md:50 corrected from `docs/sprints/sprint-{NN}/decisions.md` (sprint-local, not read by downstream) to `.gse/decisions.md` (canonical — template, MANIFEST, design all agree). Restores P6 traceability of decisions made during Open Questions Gate.
- **`status: ready` ghost value** removed from produce.md:91 selector. `ready` was not in the `backlog.yaml` enum (`open | planned | in-progress | review | fixing | done | delivered | deferred`) and no activity transitioned into it — dead code. Produce now selects only `status: planned`.
- **`branch_status` enum** in plan.md:163 aligned from `planned | created | merged | abandoned` to the canonical `null | planned | active | merged | deleted` (matches backlog.yaml template + produce.md + deliver.md + backlog.md — 4 out of 5 sources). `created` and `abandoned` were unused anywhere.
- **`micro` removed from plan-summary.md template mode line** (Micro mode has no plan.yaml, so plan-summary is never generated for Micro — the option was unreachable).
- **Sprint templates branch hardcoded `sprint-01`** replaced by placeholder `gse/sprint-{NN}/integration` across 6 files (reqs.md, design.md, tests.md, review.md, release.md, compound.md) with explicit "replaced at instantiation by /gse:<activity>" comment. Sprint 2+ artifacts now carry their correct sprint branch.

### Changed
- **PREVIEW in Full-mode sequence** reconciled across 3 documents. Previously: spec §14 treated PREVIEW as baseline always-included; plan.md §7 baseline excluded PREVIEW with "insert conditionally if domain ∈ {web, mobile}"; design §10.1 baseline excluded PREVIEW with "plus preview after design for web/mobile" addendum. Now all three agree on spec §14 semantics: **PREVIEW is in the Full-mode baseline sequence** `[collect, assess, plan, reqs, design, preview, tests, produce, review, deliver]`. At PLAN-time, when `project.domain ∉ {web, mobile}`, PREVIEW is moved to `workflow.skipped` with an explicit reason. Plan.md §7 and design §10.1 reformulated accordingly.
- **plan.md §7 "Conditional insertions"** renamed to "Conditional adjustments at PLAN-time" and clarified: PREVIEW is moved to skipped (not inserted), FIX is inserted after review (when findings exist).

### Notes
- MANIFEST.yaml now declares 21 templates (was 20). Grand totals in design §12 will reconcile the new template count in a future count-refresh pass.

## [0.47.3] - 2026-04-21

Layers impacted: **spec**, **design** (structural cleanup pass)

**Methodology coherence pass — third batch (structural corrections)** from the /gse-audit run against v0.45.0. Targets dangling cross-references, missing TOC entries, undefined steps referenced multiple times, and one missing introduction section.

### Fixed
- **spec TOC** now lists Appendix B (Cost Assessment Grid for Maintenance Work) and Appendix C (Maintainer Guide) separately. Previous entry "B. Maintainer Guide" pointed at Appendix B but Appendix B is actually the Cost Grid — Maintainer Guide is Appendix C.
- **spec §14.3 "Step 6 (Complexity Assessment)"** now exists as a dedicated section. Previously referenced 4 times (§14.3 Step 2 tables, §13.2 cross-ref, Step 5 transition lines) but never defined. The new Step 6 consolidates the 8 structural signals scanned, the mode mapping (Micro / Lightweight / Full), and the Gate decision format.
- **spec §3.2.1 line 1123** corrected from "not 11" to "not 13" — the HUG interview has 13 dimensions (confirmed by spec §14.1 and the 13-row table in hug.md).
- **spec §7.2 Risk Alerts example** corrected `DS-002` → `DES-002`. `DS-` is not a canonical P6 prefix; design decisions use `DES-`.
- **spec §10 commit convention example** corrected `Traces: RVW-005, SEC-002` → `Traces: RVW-005, RVW-012`. `SEC-` is not a canonical P6 prefix; since Prop 7 unified all reviewer findings to `RVW-NNN` with `perspective:`, the example now reflects that.
- **design §1 Introduction** added. The document previously started at §2 (Plugin System Comparison), which disoriented readers. The new §1 clarifies scope, out-of-scope, and reading order.
- **design §5.14 ligne 1167** corrected cross-ref `Adopt mode (see 5.5)` → `Adopt mode (see 5.4)`. §5.4 is Adopt Mode; §5.5 is Lightweight Mode (different concept).
- **design §5.9 "Step 7 — (removed)"** dead section marker removed. The info it carried ("health auto-updated by canonical run") is already covered by its reference to spec §6.3.

### Notes
- No plugin impact — these are spec/design documentation corrections. Regeneration is a no-op.
- design §14 Open Questions status labeling (some items "RESOLVED", others "Recommendation" without status) is deliberately deferred to a future dedicated proposition — each row needs individual analysis.

## [0.47.2] - 2026-04-21

Layers impacted: **spec**, **implementation** (schema + artefact identification pass)

**Methodology coherence pass — second batch** from the /gse-audit run against v0.45.0. Addresses profile.yaml schema drift (major — activities and agents were divided between two reading paths), QA severity scale harmonization across 6 reviewer agents, and sprint template artefact identification (IDs + frontmatter namespace).

### Fixed
- **profile.yaml root structure** split into `user: {name, git_email}` + `dimensions: {13}` (previously flat under `user:`). The split was already used by 8 consumers (plan, fix, coach×4, orchestrator×2) but contradicted by 4 (produce, tests, guardrail-enforcer, spec §1537). The 4 flat readers are now aligned on `dimensions.*`.
- **6 dimension enum values** aligned on `hug.md` Step 2 canonical interview spec: `scientific_expertise` → `practitioner` (was proficient), `abstraction_capability` → `concrete-first | balanced | abstract-first`, `preferred_verbosity` → `terse | normal | detailed`, `domain_background` → free text (was closed enum), `decision_involvement` → `autonomous | collaborative | supervised`, `team_context` adds `pair`.
- **project_domain enum fused** into 9 values: `web | api | cli | data | mobile | embedded | library | scientific | other` (combines hug's `api/data/other` and template's `library/scientific`).
- **learning_goals type** unified as list of strings (was `[]` in template, `"free text"` in hug.md example — incompatible).
- **contextual_tips / emoji** standardized on native YAML booleans `true/false` (hug.md example had `on/off` strings).
- **hug.md "12 HUG dimensions" → "13"** (table has 13 rows; spec §14.1 says "all 13").
- **learn.md `mother_tongue` → `language.chat`** (non-existent dimension corrected).
- **QA severity scale** harmonized on `HIGH | MEDIUM | LOW` (spec §6.5 canonical) across 6 reviewer agents: security-auditor (was CRITICAL/HIGH/MEDIUM/LOW), requirements-analyst, architect, test-strategist, ux-advocate, devil-advocate (all were CRITICAL/WARNING/INFO). CRITICAL is now reserved exclusively for the P15 "Verified but wrong" escalation applied at review merge time.
- **Finding ID format** unified to `RVW-NNN` with `perspective: <agent-name>` field across all 7 reviewer agents (previously each had own prefix: SEC-, REQ-, DES-, TST-, UX-, DEVIL-). Eliminates collisions with artefact IDs (REQ-, DES-, TST- are reserved for Requirements, Design decisions, Test specs per spec §P6).
- **sprint/review.md template** severity table: 6 rows (CRITICAL/HIGH/WARNING/MEDIUM/LOW/INFO) → 4 rows (CRITICAL/HIGH/MEDIUM/LOW) with note explaining CRITICAL is P15 escalation only.
- **Sprint template body IDs** aligned on canonical prefixes: reqs.md uses `REQ-001..REQ-099` (functional) and `REQ-101..REQ-199` (non-functional) — was `R01/R02/NFR01/NFR02/NFR03`. design.md uses `DES-001/DES-002` — was `D01/D02`. tests.md uses `TST-001..TST-009` (unit), `TST-010..TST-019` (integration), `TST-020..TST-029` (E2E), `TST-030..TST-039` (policy) — was `T01/T02/T10/T20/T30`.
- **Activity Persist step frontmatter** for reqs/design/tests aligned on orchestrator §331 `gse:` namespace (was flat `id/artefact_type/title/author`). Canonical traces fields: `derives_from`, `implements`, `tested_by`, `decided_by`. Removed non-canonical `implemented_by` (design.md) and `tests: [SRC-]` (tests.md).

### Changed
- **profile.yaml template** gains meta fields (`version: 1`, `inferred: {}`, `created`, `updated`) previously present in hug.md Step 5 example only. `expertise_domains` and `competency_map` unchanged (agent-populated, not asked at HUG).
- **hug.md Step 5 YAML example** updated to reflect new template shape (split structure, list learning_goals, bool flags, no `on/off` strings).
- **dashboard.py** profile reading simplified from `dimensions.X OR flat X` fallback to canonical `dimensions.X` only (both `it_expertise` and `decision_involvement`).
- **devil-advocate P15 escalation rules** rewritten to match the 3+1 tier structure: Moderate → one-level escalation (LOW→MEDIUM, MEDIUM→HIGH); Low → HIGH + user verification; Verified-but-wrong → CRITICAL (only path to CRITICAL).
- **test-strategist severity blocks** now document that `[STRATEGY] [TST-SPEC] [IMPL]` tags are orthogonal to severity (they identify review tier, not severity level).
- **sprint/design.md template traces** extended to 4 canonical fields (was 2: `derives_from`, `decided_by`; added: `implements`, `tested_by`).
- **Test level added to `gse:` namespace** (`gse.level: unit | integration | e2e | visual | performance | policy`) in tests.md activity Persist step.
- **Requirements references in design.md template** renamed from "Requirements: R01, R02" to "Implements: REQ-001, REQ-002" (aligns with canonical `implements` trace).

### Notes
- Not backward-compatible for old profile.yaml with flat structure (schema change; users must re-run `/gse:hug --update` after upgrade — or the agent auto-detects and migrates on first read, which is a TODO for a future minor).
- No activity, agent, or principle added/removed — only schema/descriptions harmonized.
- `git_email` kept as denormalization in `user:` for dashboard/coach read performance (source of truth remains `git config user.email`).

## [0.47.1] - 2026-04-21

Layers impacted: **spec**, **design**, **implementation** (3-layer coherence pass)

**Methodology coherence pass — first batch** from the /gse-audit run against v0.45.0. Addresses 5 clusters of drift across spec, design, and src/ that had accumulated over the last minor versions (coach + deploy-operator added without propagating counts; opencode added without backfilling the design doc; activity-side writes using stale schema field names; checkpoint schema diverging from spec; template/descriptor confusion).

### Fixed
- **Agent count** — "8 specialized" updated to "10 specialized" (and "9 agents" → "11 agents") in spec §1.1.4, gse-one-implementation-design §3.1/§3.3/§6.4/§12, gse_generate.py docstrings/comments, and gse-one/README.md. The source-of-truth (SPECIALIZED_AGENTS list in gse_generate.py) was already correct; only descriptions were stale.
- **Template count** — "15" (spec) and "19" (design) replaced by the actual count of 28 artifact templates across spec §1.1.4, design §3.1/§3.3/§11.1/§12, gse_generate.py docstrings, and README. MANIFEST.yaml is now explicitly flagged as a descriptor (not itself a template).
- **Schema field `lifecycle_phase` → `current_phase`** across 9 source files (5 activities + orchestrator + checkpoint template + design text + go.md reading path). Spec §12.4, status.yaml template, and dashboard.py were already canonical; the drift was confined to activity-side writes/reads. Fixes a silent bug where /gse:compound and /gse:deliver wrote to a field the dashboard never read, leaving the phase display stuck at LC00.
- **design §12 inventory totals recomputed** — Shared 51→62, Grand total 57→150 (adding opencode-only column with 59 files counted correctly for the first time).

### Changed
- **design §6 Cross-Platform Parity** restructured to include opencode as a first-class platform (§6.3 "opencode: AGENTS.md Embedding" inserted, §6.4/§6.5 renumbered, §6 intro updated from "both platforms" to "all three supported platforms", §6.4 "Generation and Parity" extended to cover 3 outputs + 3-way body parity verification, §6.5 "Installer Differentiation" extended with opencode installer merging between GSE-ONE START/END markers).
- **design §7.3 Format Differences** adds an opencode column documenting native TS plugin delivery (`plugins/gse-guardrails.ts`) vs Claude/Cursor JSON hooks.
- **design §11.1 Generation Steps** extends each row to show all opencode outputs (opencode/skills/, opencode/commands/, opencode/agents/, opencode/AGENTS.md, opencode.json, gse-guardrails.ts).
- **design §13 Implementation Priorities** — added an introductory note stating the 4 phases document the original Claude+Cursor roadmap; opencode was a separate follow-up effort (v0.31+); fixed Phase 2 Step 15 from "8 agents + Cursor P14 always-on rule" to "10 specialized agents + Cursor orchestrator always-on rule".
- **checkpoint.yaml schema** refactored to flat top-level (no `checkpoint:` wrapper), zero duplication between checkpoint metadata and `status_snapshot` block, with explicit structured sub-blocks for `status_snapshot`, `backlog_sprint_snapshot`, and `git_state`. Obsolete duplicate fields removed: `checkpoint.sprint`, `checkpoint.phase`, `checkpoint.last_activity` (kept only in `status_snapshot` where they belong).
- **spec §12.5 and design §5.16 checkpoint schemas** updated to match the new flat + structured template schema (previously spec had `status_snapshot: <copy of status.yaml>` as a free string and used `git:` / `notes:`; now aligned with template: structured subblocks, `git_state:`, `note:` singular).
- **pause.md Step 2** — rewrote the checkpoint field mapping to reflect the flat schema (removed writes to obsolete `checkpoint.sprint`, `checkpoint.phase`, `checkpoint.last_activity` duplicates).
- **resume.md** — Step 1 --list display now references `status_snapshot.current_sprint/current_phase`; Step 5 fallback references `status_snapshot.last_activity` instead of non-existent `checkpoint.last_activity`.

### Notes
- Not backward-compatible for old `checkpoint-*.yaml` files (schema change). Checkpoints are short-lived session artifacts so this is acceptable; running a fresh /gse:pause after upgrading produces the new schema.
- No activity, agent, or principle was added or removed — only the descriptions counting them and the schema names used in their workflow text.
- All modifications applied after a deep audit using /gse-audit; the audit output is archived in _LOCAL/audits/ (gitignored).

## [0.47.0] - 2026-04-21

Layers impacted: **tooling** (repo-level, not plugin)

**Audit reliability pass** — based on observations from the first full `/gse-audit` run against v0.45.0 (which produced 45 errors / 85 warnings / 31 recommendations spontaneously with excellent clustering, but revealed concrete gaps in the tool itself). Addresses: Python engine missing numeric drift in gse_generate.py, skill's save phase being too permissive, missing per-job completion tracking, absent finding→job traceability, and preservation of LLM-natural behaviors across future LLM versions.

### Added
- **`job_id` field** in the `Finding` dataclass (`gse-one/audit.py`) and in the agent's required output format (`methodology-auditor.md`). Python-engine findings carry `job_id="python-engine"`; each LLM sub-agent MUST tag its findings with its catalog `job.id`. This enables traceability (which job produced what) and filtered re-runs in future versions.
- **Per-job completion tracking** in Phase 4 aggregation: the orchestrator now records and reports "N/20 jobs completed" in the summary. Skipped or errored sub-agents are explicitly called out.
- **Table of Contents** at the top of the report (required when > 100 lines). Lists Summary, Clusters, Warnings, Info, Strategic recommendations per critique job, Conclusion.
- **Phase 5 quality requirements** section in the skill: documents 7 LLM-natural behaviors observed in real audits (thematic clustering, precise citations, strategic tables with Impact/Direction, fix-priority lists, files-to-consult-first, action-oriented phrasing, separation of immediate vs future horizons). Preserves quality against future LLM regression.

### Changed
- **`audit_numeric()` extended** to scan: spec, design, README, CLAUDE.md, CHANGELOG.md, gse_generate.py, all activity files, all agent files. Previously only spec + design — missing 7 occurrences in `gse_generate.py`. Now also detects "N principles" drift (not just "N commands" and "N specialized"). Finding aggregation is per-file: one warning per (file, pattern, claimed_value) with all line numbers listed, instead of N warnings per N occurrences.
- **Filename format** for saved reports changed to `audit-YYYY-MM-DD-HHMMSS-vX.Y.Z.md` (was `audit-<ISO-timestamp>.md`). More readable, includes version for trace continuity across releases. Adopted from observed behavior in a spontaneous manual save by Claude Code.
- **Phase 6 save made MANDATORY** in the skill (was "unless --no-save"). Explicit procedure: mkdir → compute filename with VERSION + UTC date+time → Write 2 files (timestamped + latest.md) → verify via `ls` → report exact path to user. Rationale stated: audit trail is the primary value of running an audit.
- **Phase 4 aggregation** now prescribes thematic clustering of findings (Cluster 1 — Count drift, Cluster 2 — Schema drift, etc.) as a quality REQUIREMENT, not optional. Observed spontaneously by LLM in real runs; now codified so future LLMs don't regress.
- **Sub-agent prompt template** enriched: `job_id` field now REQUIRED in output, with explicit examples of all Finding fields (category, severity, location, file, detail, fix_hint, direction, impact).

### Notes
- A1 (actionable synthesis prescription), A2 (multi-location merging prescription), B2 (atomic fix commit suggestions) were considered but abandoned as redundant — the LLM produces these spontaneously with high quality. Phase 5 quality requirements capture the essence to prevent regression.
- C1 (impact-sorted recommendations) was already present in Principle 7 of the agent and naturally implemented by the LLM.
- `audit.py` total file count expanded from 6 to 7 scan targets (gse_generate.py + repo-level docs). Expected to catch ~2-3× more numeric drift findings.

## [0.46.0] - 2026-04-21

Layers impacted: **tooling** (repo-level, not plugin)

### Added
- **Automatic audit persistence** — `/gse-audit` slash command and `audit.py` CLI now save their reports to `_LOCAL/audits/` by default. Two files produced per run:
  - `_LOCAL/audits/audit-<ISO-timestamp>.md` — timestamped archive (one per run, accumulates)
  - `_LOCAL/audits/latest.md` — convenience copy, always overwritten (points to the most recent run)
  
  The `_LOCAL/` directory is gitignored (via `/_*/` in `.gitignore`), so audit history never leaks into commits. Forkers accumulate their own audit trail locally without polluting their repo.

- **`--no-save` flag** on `audit.py` and `/gse-audit` to disable persistence (stdout only).
- **`--save-to <path>` flag** for explicit output path (useful for CI artifact export or integration with external reporting).

### Changed
- **`gse-one/audit.py`** — default behavior is now to save + print. Previously: print only. Breaking change in default output, but opt-out via `--no-save` restores the old behavior.
- **`.claude/commands/gse-audit.md`** — new Phase 6 "Save the augmented report" documents the skill-side save (deterministic findings + LLM findings + strategic recommendations merged before persistence). The skill invokes `audit.py --no-save --format json` internally to avoid duplicate engine-side saves.
- **README "Auditing the plugin" section** — documents the new `_LOCAL/audits/` default, `latest.md` convenience, and save flags.

### Notes
- When the skill runs a full audit, only ONE file is saved (the augmented report). When `audit.py` is invoked standalone, its deterministic-only report is saved.
- Historical audits can be compared diffing two files under `_LOCAL/audits/`.

## [0.45.0] - 2026-04-21

Layers impacted: **tooling** (repo-level, not plugin)

**Tooling refactor** — massively expands `/gse-audit` with a declarative catalog of 20 parallel audit jobs spanning 5 categories, including 4 strategic critique jobs that empower the LLM to offer opinions on methodology design. No changes to the distributed plugin (spec, design, activities, agents, tools, templates all unchanged).

### Added
- **`.claude/audit-jobs.json`** — declarative catalog of 20 audit jobs across 5 categories:
  - A: File quality (2 jobs, non-directional)
  - B: Intra-layer uniformity (5 jobs, non-directional)
  - C: Layer pair spec ↔ design (1 job, bidirectional)
  - D: Horizontal clusters (8 jobs, bidirectional): governance, deploy, sprint-lifecycle, state-management, cross-cutting, coach-pedagogy, quality-assurance, delivery-compound
  - E: Strategic critique (4 jobs, bidirectional): methodology-design, ai-era-adequacy, user-value, robustness-and-recovery
- **`gse-one/audit_catalog.py`** — loader + validator (stdlib only). Validates schema, resolves globs, provides `find_job` / `is_file_in_cluster` helpers. CLI for inspection: `--list`, `--show <id>`, `--validate`.
- **Refinement taxonomy**: `none` (intra-file or intra-layer, no cross-level), `downward` (high level = reference), `bidirectional` (may propose upward corrections when lower level is better).
- **Bidirectional refinement Principle 6** in `methodology-auditor` agent: for `bidirectional` jobs, actively look for cases where implementation reveals a better formulation than design, or design a better formulation than spec. Propose upward updates.
- **Strategic critique Principle 7** in `methodology-auditor`: for Category E (`qualitative_critique`), the auditor is empowered to offer opinions and recommendations about methodology design itself. Severity `recommendation` (not error/warning/info). Each recommendation must include impact level (high/medium/low), rationale, alternative views.
- **New severity level `recommendation`**: distinct from error/warning/info. Never triggers CI exit codes. Reserved for Category E jobs.
- **Cluster-aware `audit.py`**: new flags `--cluster <id>` to filter findings to a specific catalog job, and `--list-clusters` to display all catalog entries.
- **Segmented report**: final output has two parts — **Part 1** coherence findings (Categories A-D), **Part 2** strategic recommendations (Category E).

### Changed
- **`.claude/commands/gse-audit.md`** rewritten as a parallel orchestrator: reads the catalog, spawns N sub-agents in ONE message (parallel via Agent tool calls), aggregates findings, renders segmented report. New flags: `--job`, `--category`, `--coherence-only`, `--strategic-only`.
- **`.claude/agents/methodology-auditor.md`** extended with Principles 6 (bidirectional refinement) and 7 (strategic critique). Output format now includes `direction` and `impact` fields.
- **`gse-one/audit.py`** `Finding` dataclass gained a `file` field for cluster-filtering support. Docstring updated with new flags.
- **README "Auditing the plugin" section** rewritten to reflect: 20 jobs in 5 categories, parallel execution, segmented report (coherence vs strategic), catalog customization workflow for forkers.

### Design decisions

1. **Why 5 categories (A-E) instead of merging A+B?** File-quality and intra-layer-uniformity serve different purposes: A audits individual files (can't be a group), B audits groups of same-level files (uniformity across a set). Keeping them distinct preserves clarity.

2. **Why `recommendation` as a separate severity?** Strategic critiques (Category E) are judgment-based and should never block CI. Keeping them separate from `error`/`warning` means they're surfaced as proposals, not defects.

3. **Why `bidirectional` default for cross-layer and Category E?** The refinement direction is normally downward (spec → design → impl), but the methodology may genuinely improve by recognizing cases where the implementation reveals a better abstraction than the spec captured. Allowing upward propositions keeps the methodology evolving.

4. **Why JSON catalog instead of YAML?** To stay within stdlib (Q4 validation). A forker can add a job without needing PyYAML.

### Notes for users
- End users who installed GSE-One for their project: unaffected. No new plugin command.
- Forkers: inherit all 20 jobs automatically via `git clone`. Add custom jobs by editing `.claude/audit-jobs.json`.
- CI integration: use `python3 gse-one/audit.py --fail-on error` (deterministic only; strategic recommendations never block).

## [0.44.0] - 2026-04-21

Layers impacted: **tooling** (repo-level, not plugin)

**Tooling-only release** — adds a methodology coherence audit tool for maintainers and forkers of the gensem repository. No changes to the distributed plugin (spec, design, activities, agents, tools, templates all unchanged). The audit does NOT apply to user projects — for those, existing commands `/gse:status`, `/gse:health`, `/gse:review`, `/gse:assess`, `/gse:compound`, `/gse:collect` remain the right surface.

### Added
- **`.claude/commands/gse-audit.md`** — slash command for Claude Code, invokable as `/gse-audit` from the root of gensem or a fork. Orchestrates Phase 0 context detection + Phase 1 deterministic Python engine + Phases 2–3 LLM semantic reasoning + Phase 4 unified report.
- **`.claude/agents/methodology-auditor.md`** — specialized agent adopted during `/gse-audit`. Evidence-based, severity-classified, constructive, forker-respectful. Not part of the distributed plugin (local to repo).
- **`gse-one/audit.py`** — Python engine (stdlib-only, ~600 L). 12 deterministic categories: version consistency, file integrity, plugin parity, cross-file references, numeric consistency, link integrity, git hygiene, Python quality, template schema, TODO/FIXME scan, test coverage structural, last-verified freshness. CLI with `--format {md,json}`, `--category`, `--fail-on {error,warning}`. Exit codes: 0 pass, 1 errors, 2 warnings, 3 not-a-gensem-repo.
- **Optional PyYAML dependency** — `gse-one/audit.py` uses PyYAML if installed for YAML schema validation; skips gracefully with an info finding otherwise.
- **README section "Auditing the plugin"** — documents slash command + CLI access, 12 deterministic categories, 6 LLM dimensions, fork inheritance via `git clone`.
- **CLAUDE.md paragraph on `.claude/` repo-level tooling** — documents that maintainer tools live at `.claude/` or `gse-one/`, never in `gse-one/plugin/` (would pollute end-user distribution).

### Architecture rationale
The audit was deliberately placed **outside the plugin** for three reasons:
1. **Scope discrimination** — the plugin has 6 existing commands already covering user-project inspection (status, health, review, assess, compound, collect). Adding a 24th `/gse:audit` activity would create overlap and confuse end users.
2. **Forker ergonomics** — `.claude/` directories are inherited automatically via `git clone`. Forkers of gensem get the audit tool with zero install step.
3. **Maintainer-tool separation** — `.claude/` (repo-local) and `gse-one/audit.py` (alongside `gse_generate.py`) both clearly signal "maintainer only". The plugin distribution (`gse-one/plugin/`) remains focused on end-user methodology.

### Notes for users
- End users who installed GSE-One for their project are **unaffected**. No new command appears in `/gse:` autocomplete.
- Forkers automatically inherit `/gse-audit` in their fork's Claude Code session.
- CI integration (GitHub Actions running `audit.py --fail-on error`) is documented as future work.

## [0.43.0] - 2026-04-21

Layers impacted: **spec**, **design**, **implementation**, **tools**, **tests**, **docs**

### Added
- **Step -1 Orientation in `/gse:deploy`** — first-time users are greeted by a 4-option menu that identifies their role (Solo / Instructor / Learner / Skip). Each role triggers a tailored briefing (estimated duration, cost, next actions) before proceeding to Step 0. Integrated directly into `/gse:deploy` (single command to remember) rather than `/gse:hug`, for novice-friendly discoverability.
- **`user_role` field in `.gse/deploy.json`** — persists `"solo"`, `"instructor"`, `"learner"`, or `""` (if Skip/--silent). Purely informational in v1; no behavioral branching beyond Step -1.
- **`deploy.py record-role <role>`** subcommand — CLI handler invoked by the skill to persist the role with validation (VALID_ROLES = {solo, instructor, learner}).
- **`--silent` flag** on `/gse:deploy` — skips Step -1 entirely (for scripting, CI, or experienced users). Keeps all other Gates (costly operations, destroy confirmations).
- **Learner preconditions** — for role 3, the skill verifies (a) `.env.training` was copied to `.env`, (b) `DEPLOY_USER` is set, before proceeding. Exits with clear instructions if not.
- **5 new unit tests** (`RecordRoleTests`): empty-state shape includes `user_role`, record_role for each of 3 valid roles persists correctly, invalid role returns `status: "error"`. Total: 49 tests.

### Changed
- **`/gse:deploy --help`** reformatted with a "Who are you?" role-first narrative (3 paragraphs: Solo / Instructor / Learner) followed by the full Options table. Novices see their relevant flow first.
- **README "Deployment" section** simplified: the long 3-situations paragraph is replaced by a concise "Just run `/gse:deploy`" pointer to the Step -1 Orientation, plus the 4 role summary lines.
- **Spec §1.6 `/gse:deploy` row** extended to mention Step -1 and the `--silent` flag.
- **Design §5.18** new subsection "Onboarding orientation (Step -1)" documenting the trigger conditions, the 4-option menu, the role-based routing, and the `--silent` bypass.
- **`src/templates/deploy.json`** schema: added `user_role: ""` field between `last_updated_at` and `phases_completed`.
- **`plugin/tools/deploy.py`** — added `VALID_ROLES`, `record_role()`, CLI handler, subparser, and `user_role` to `_empty_state()`.

### Design decision
The onboarding was integrated directly into `/gse:deploy` (not into `/gse:hug`) because novices looking to deploy will naturally type the deploy command first. Separating onboarding from action would fragment the UX, especially for instructors briefing learners ("just run /gse:deploy" stays a one-sentence instruction). The slight entorse to the "onboarding = hug" convention is justified by significantly better discoverability and cohesion.

## [0.42.0] - 2026-04-21

Layers impacted: **spec**, **design**, **implementation**, **tools**, **tests**, **docs**

### Added
- **`/gse:deploy` production-ready.** Concrete, deterministic, auditable deployment activity for Hetzner Cloud + Coolify v4 (23rd command). Adaptive to solo / partial / training situations with 6-phase workflow (setup → provision → secure → install-coolify → configure-domain → deploy).
- **Subdomain derivation**: solo `<project>.<domain>`, training `<user>-<project>.<domain>` with full sanitization and RFC 1035 length checks.
- **Multi-application state schema**: `.gse/deploy.json` with `applications[]` array, Coolify hierarchy mapping (`gse` / `gse-<user>` projects + `production` environment), `cdn` block.
- **New artifact type `src/references/`**: reference material consulted by agents at runtime. Ships with `hetzner-infrastructure.md` (pricing, sizing, Coolify API endpoints, security checklist) and `ssh-operations.md` (connection patterns, credential resolution).
- **Four Dockerfile templates**: `Dockerfile.streamlit`, `Dockerfile.python`, `Dockerfile.node`, `Dockerfile.static` + shared `.dockerignore`. All include `ARG SOURCE_COMMIT=unknown` for Docker cache-bust.
- **`deploy-operator` agent**: 10th specialized agent, 7 core principles (safety, idempotence, user interaction, step numbering, error handling, credential management, SSH), 6-phase lifecycle, anti-patterns.
- **Python execution tools**: `plugin/tools/coolify_client.py` (Coolify v1 API HTTP client, stdlib-only, 3x retries on 5xx) + `plugin/tools/deploy.py` (orchestrator with 18 subcommands: state, env, subdomain, detect, preflight, record-*, deploy-app, destroy, wait-dns, training-*).
- **Concrete production-readiness**: 4 DNS registrar sections (Namecheap, Gandi, OVH, Cloudflare), Cloudflare CDN/DDoS/WAF proposal with 10-step opt-in flow, `ufw-docker` hardening (prevents Docker from bypassing UFW), detailed Coolify onboarding wizard, `wait-dns` polling with `@8.8.8.8` fallback resolver.
- **Training tools**: `--training-init` generates redacted `.env.training` (safe secrets only, security warning embedded), `--training-reap` deletes per-learner or all `gse-*` Coolify projects (preserves `gse` solo project).
- **Two-Gate `--destroy`** with dry-run preview, cost savings surfacing, retry-safe state preservation on partial failure, post-destroy warnings (DNS, Cloudflare, Let's Encrypt, SSH key).
- **Typed preflight**: `deploy.py preflight` subcommand returns type + port + 15+ structured checks (git state, entry points, Streamlit CORS/XSRF, Dockerfile `ARG SOURCE_COMMIT`, Node `start` script, Next.js build hint, static `index.html`).
- **Unit test foundation**: 44 stdlib unittest tests covering deterministic functions (sanitize, build_subdomain, detect_type, preflight rollup, env parsing, state I/O, cost hints). Runs automatically via `gse_generate.py --verify`.
- **`TESTING.md`** at `gse-one/` root: documents unit test runner + manual E2E checklist (solo full, solo partial, training, edge cases).
- **`--registrar <name>`, `--redeploy`, `--training-init`, `--training-reap`, `--help` flags** documented in skill `deploy.md`.
- **README "Deployment" section** with Prerequisites + "Maintaining upstream compatibility" contribution workflow (covers Coolify API, registrar UIs, hcloud install, Cloudflare UI, Coolify onboarding).
- **Abstraction principle doctrine** formalized in design §5.18: GSE-One prefers concrete, deterministic instructions over goal-level abstractions, for reproducibility, auditability, self-containment, testability.
- **Destroy semantics** documented: retry-safe, best-effort, dry-run supported, state preserved on partial failure.

### Changed
- **Design doc §5.18** expanded from an empty section to 12 subsections covering the full `/gse:deploy` design.
- **Spec §1.6 agent count corrected**: text said "8 specialized" while table listed 9. Now "10 specialized" (9 existing + deploy-operator) with matching table row.
- **Spec `/gse:deploy` row** options list extended to include all 7 flags (`--status`, `--redeploy`, `--destroy`, `--registrar`, `--training-init`, `--training-reap`, `--help`).
- **`src/templates/deploy.json`** redesigned: single `app` object → `applications: []` array, added `cdn` block, per-app Coolify UUIDs, resources.
- **`src/templates/config.yaml` `deploy.app_type`** extended to `auto | streamlit | python | node | static | custom`.
- **`src/templates/deploy-env-training.example`** enriched with URL pattern examples.
- **Generator `gse_generate.py`**: added `REFERENCES_DIR` + copy logic, extended tools verify, unit test runner in `--verify`, registered `deploy-operator.md` as 10th specialized agent.
- **Skill `deploy.md`** fully restructured (~600 lines): Step 0 delegates to tool `detect`, all phases persist completion via `record-phase`, Phase 6 consolidated into single `deploy-app` call, `--status`/`--destroy`/`--training-*` delegate to tool with skill-orchestrated Gates.

### Fixed
- **`destroy()` data-loss bug**: state was reset unconditionally even on partial failure, losing server tracking (user kept being billed with no trace in state). Now state is preserved on `status: "partial"` for retry.
- **Pre-existing spec inconsistency** (§1.6): text said "9 agents / 8 specialized" while table listed 9 specialized rows. Corrected to "11 agents / 10 specialized" with matching table.

### Removed
- **`src/templates/Dockerfile`** (old Streamlit-only default) — replaced by 4 specialized templates.
- **`gse-deploy-plan.md`, `gse-deploy-minimal-plan.md`** (design drafts at repo root) — archived outside the repo (`_LOCAL/archive/`, gitignored).

### Notes for contributors
The deploy implementation is deliberately concrete (not abstracted to LLM + Context7 MCP). Upstream drift (Coolify API, registrar UIs, hcloud install) is absorbed via PRs. See `README.md → Deployment → Maintaining upstream compatibility` and `TESTING.md`.

## [0.41.0] - 2026-04-20

Layers impacted: **spec**, **design**, **implementation** (templates, activities, generator)

### Added
- **Template `plan.yaml`** — authoritative schema for the living sprint plan (previously defined only inline in `plan.md`). All three layers (spec, design, activities) now reference this template as the single source of truth.
- **Template `decisions.md`** — decision journal header with unified DEC-NNN format (merged spec §11.2 Markdown format + design.md YAML traceability fields into a single Markdown format with 16 fields).
- **Template `checkpoint.yaml`** — session pause snapshot schema (previously defined only inline in `pause.md`).
- **Template `methodology-feedback.md`** — methodology feedback export format for COMPOUND Axe 2.
- **Template `MANIFEST.yaml`** — declarative index of all templates with target paths, creator activities, and scope. Prepares future `/gse:upgrade` and generator verification.
- **Section "Policy Tests"** in `sprint/tests.md` template — aligns template with v0.35.0 AMÉL-13 (policy test pyramid level, baseline 5%).
- **Section "Inform-tier Decisions"** in `sprint/design.md` template — aligns template with DESIGN Step 7 closure.
- **Section "Methodology Feedback Summary"** in `sprint/compound.md` template — aligns template with COMPOUND Step 2.6.

### Changed
- **`backlog.yaml` template** — replaced 2 example items (TASK-001, TASK-002) with empty list + commented structure. Added missing `delivered_at: null` field. Added `spike` to `artefact_type` enum.
- **`profile.yaml` template** — replaced orphan `competency_map` section (4 flat lists never read by any activity) with the rich `topics: {}` schema actually used by `/gse:learn` (level/last_session/mode/note per concept). Redirected `learn.md` to read/write `profile.yaml → competency_map.topics` instead of a separate `.gse/competency_map.yaml` file.
- **`status.yaml` template** — renamed `last_activity_date` → `last_activity_timestamp` (aligns with all 12 activities that write this field + dashboard.py that reads it). Fixed internal contradiction in orchestrator (line 465 said `_date`, line 485 said `_timestamp`).
- **Activities `plan.md`, `pause.md`** — replaced inline YAML schema blocks with references to authoritative templates + field population lists (eliminates schema duplication).
- **Activity `design.md`** — DEC-NNN format changed from YAML frontmatter (8 fields) to unified Markdown format (16 fields, merging spec consequence horizons + implementation traceability).
- **Spec §11.2** — enriched DEC-NNN example with `Activity`, `Traces`, `Status`, `Decided by` fields + renamed `Why` → `Rationale`.
- **Spec §12 tree** — `plan.yaml` description enriched with key fields summary + template pointer.

### Removed
- **`inventory.yaml`** — removed from the methodology. The artefact scan performed by `/gse:collect` is now ephemeral (console output only, not persisted to a file). `/gse:assess` runs its own inline scan instead of reading a stale file. Rationale: single consumer, immediately stale after any file change, redundant with git for file-level queries. The scan itself (Steps 1-5) and console summary remain unchanged.
- **`--refresh` flag** from `/gse:collect` — no longer meaningful without a persisted inventory file.

## [0.40.0] - 2026-04-20

Layers impacted: **documentation**

### Removed
- `docs/training-feedback-report.md` — pedagogical training-feedback report (added in v0.38.1) removed from the repository; it is now managed outside the repo.

## [0.38.1] - 2026-04-20

Layers impacted: **documentation**

### Added
- **`docs/training-feedback-report.md`** — a pedagogical report (~20 pages, English) recapping the 20 improvements from the DLH training-feedback cycle. One card per AMÉL with uniform structure (problem / what we did / before-after / go further), a typed synthesis table (🛡 / 🔧 / 📐 / 🎯 / 🤝), sections on reshaped/deferred items and intentionally out-of-scope observations, plus release-chronology, glossary, and install annexes. Written without learner attributions; links point to commits and spec/design anchors.

## [0.38.0] - 2026-04-20

Layers impacted: **milestone** (no code / spec / design changes)

### Milestone
- **Closure of the 20-AMÉL training-feedback cycle.** Improvements derived from the DLH training sessions (12 learners × 3 days) have been processed end-to-end from v0.23.0 to v0.37.4. Summary of the cycle:

  | AMÉL | Version | Commit | Summary |
  |---|---|---|---|
  | 01 | v0.23.0 | `b6f76e4` | Sprint Freeze guardrail |
  | 02 | v0.24.0 | `5d9a501` | Automatic dashboard regeneration via editor hooks |
  | 03 | v0.26.0 | `0206978` | Root-Cause Discipline guardrail (P16) |
  | 04 | v0.25.0 | `53d111d` | Git Identity Verification guardrail |
  | 05 | v0.27.0 | `67aa68e` | Scope Reconciliation + Inform-Tier Summary (absorbs AMÉL-17) |
  | 06 | v0.32.0 | `a7aca0e` | Shared State section in design artefact |
  | 07 | v0.28.0 | `9846172` | Intent Capture for greenfield projects |
  | 08 | v0.29.0 | `d013d6d` | Open Questions + activity-entry scan |
  | 09 | v0.33.0 | `37bf6ff` | Scaffold-as-preview variant |
  | 10 | v0.34.0 | `910934d` | Unified complexity-point semantics |
  | 11 | v0.34.1 | `a1ecc3e` | Preview skip condition + anti-preview-ahead rule |
  | 12 | v0.30.0 | `544766f` | Config Application Transparency |
  | 13 | v0.35.0 | `95e4ffd` | Policy tests as first-class pyramid level |
  | 14 | v0.31.0 | `fc85447` | Methodology feedback via compound Axe 2 |
  | 15 | v0.36.0 | `661c247` | Tutor specialized agent (superseded by v0.37.0) |
  | 16 | v0.37.0 | `84a6684` | Unified coach agent (pedagogy + workflow, 8 axes) |
  | 17 | (v0.27.0) | `67aa68e` | Absorbed by AMÉL-05 |
  | 18 | v0.37.2 | `bacc968` | Framework isolation check in `architect` agent |
  | 19 | v0.37.3 | `e6d373e` | Connectivity preflight for scaffolders |
  | 20 | v0.37.4 | `78c8397` | Upstream repo resolution + URL fix |

  Additional in-cycle fixes: v0.37.1 (`9198e4b`) generator `--clean` preserves `plugin/tools/`.

## [0.37.4] - 2026-04-20

Layers impacted: **design**, **implementation** (generator, config template, integrate/compound, orchestrator)

### Fixed
- **Upstream repository URL corrected.** The hardcoded manifest URL pointed to `https://github.com/gse-one/gse-one` (non-existent) — replaced by the real upstream `https://github.com/nicolasguelfi/gensem` via a new `UPSTREAM_REPO` constant in `gse_generate.py` (single source of truth, propagated to all three manifests). Observed impact: `/gse:integrate` Axe 2 could not submit methodology feedback (learner10 training session hit the dead URL).
- **opencode manifest gained the repository field.** `opencode.json` now carries `gse.repository` alongside `gse.version`, so `/gse:integrate` Axe 2 works uniformly on opencode. Previously the Axe 2 flow was silently disabled on opencode because the methodology mandated reading `plugin.json → repository`, a file absent on that platform.

### Added
- **User-level override for the feedback target** — new `github.upstream_repo` field in `config.yaml` (default empty). When set, it takes precedence over the plugin manifest. Supports private forks, corporate issue trackers, and training-environment redirections without editing the shipped plugin.
- **Formal resolution order** for Axe 2 documented in `orchestrator.md`, `integrate.md`, `compound.md`, and `gse-one-implementation-design.md`: (1) `config.yaml → github.upstream_repo` if set, (2) plugin manifest (`plugin.json → repository` on Claude/Cursor, `opencode.json → gse.repository` on opencode), (3) skip Axe 2 with an Inform note.
- **Privacy acknowledgment strengthened in the final submission Gate.** The Gate before `gh issue create` now states explicitly that issues are public and visible to anyone with repo access, surfacing consequences before submission (P4 consequence visibility).

### Rationale
Learner10 deferred methodology feedback during `/gse:integrate` because the repo URL failed to resolve. Initial analysis proposed adding a new `upstream.issues_url` field, but a critical relecture found that the `repository` field already existed in plugin manifests and was referenced by the methodology — the real problems were (a) a hardcoded wrong URL in the generator, (b) opencode missing the field entirely, and (c) no user-facing override for environments where the default target isn't appropriate. Alt. B — fix the three defects without duplicating existing infrastructure — was preferred to Alt. A (new field) to avoid semantic duplication with `repository`. The override field (`github.upstream_repo`) addresses the remaining methodological gap: users can redirect feedback without patching shipped files.

## [0.37.3] - 2026-04-20

Layers impacted: **design**, **implementation** (`/gse:preview` scaffold-as-preview variant)

### Added
- **Connectivity preflight before invoking any external scaffolder** in `/gse:preview` scaffold-as-preview variant (AMÉL-19 from training feedback). Before running a scaffold command (`create-next-app`, `create-vite`, `streamlit init`, …), the agent issues a short, ecosystem-appropriate reachability probe to confirm the registry is reachable from the current environment. **The exact probe command is left to the coding agent's judgment** based on the detected ecosystem — the methodology specifies the principle (what to verify, when), not the command (how). On probe failure, the agent does NOT retry the scaffold command: it presents a **4-option Gate** — *(1) Retry*, *(2) Run locally, then resume*, *(3) Fallback to static preview*, *(4) Discuss*. Option 2 prints the exact scaffold command, the user runs it in their own terminal, confirms completion, and the agent resumes from the created directory.
- Design doc fail-modes section now distinguishes *scaffolder invocation fails* (covered by the preflight + Gate) from *scaffold build fails* (already covered) — two independent fail modes with independent resolutions.

### Rationale
Training feedback observed learner10 (v01 Codex) hitting a sandbox/proxy block on `registry.npmjs.org` during `create-next-app`; the agent retried three times identically before the user manually granted broader network access (~5 minutes of blind-retry pantomime). The methodology provided no anchor for the fail case of *invocation* — only for the fail case of *build*. Adding a lightweight, principle-level preflight (no commands prescribed, no timeout prescribed, no config field) closes the gap without overreaching to other activities (`/gse:produce` dep installs, `/gse:tests` framework installs) on the basis of a single observation. If additional signals emerge, the pattern extends naturally. A separate, broader concern — *agents looping on any external operation that fails* — is noted for potential AMÉL follow-up (generic loop/blockage monitoring, potentially an extension of P16 Root-Cause Discipline).

## [0.37.2] - 2026-04-20

Layers impacted: **implementation** (`architect` agent + `/gse:design` Step 2)

### Added
- **Framework isolation check in the `architect` agent** (AMÉL-18 from training feedback). New **Priorities** entry and new **Checklist** item ("Framework isolation") invoked during `/gse:design` and `/gse:review`. When the design includes a heavy UI or I/O framework (Streamlit, React, Next.js, Django, Flask, FastAPI, Express, Spring, …) AND non-trivial business logic, the agent proposes a framework-free domain module (`src/domain/**` imports stdlib only) and flags a DEC + a policy test enforcing the import boundary. Skipped when `config.yaml → project.domain ∈ {cli, library, scientific, embedded}` or when the design does not reference a UI/I/O framework.
- New `DES-004 [INFO] — Framework isolation opportunity` example in the agent's Output Format, showing the canonical finding (location, detail, DEC name, policy-test hint).
- One-line guideline in `/gse:design` Step 2 (Component Decomposition) pointing to the architect checklist so the rule is visible in the workflow, not only inside the agent file.

### Rationale
Training feedback observed two learners (05, 06) adopting the framework-free domain pattern **spontaneously** to satisfy reversibility/quality-fit trade-offs (e.g., Streamlit app with `logic/budget.py` kept free of Streamlit imports). Learner05 explicitly requested promotion to a GSE-level guideline. A dedicated **principle P17** was considered but rejected: the pattern is a corollary of existing principles (Dependency direction, Separation of concerns, Layering violations) rather than a transversal invariant, and it is conditional on the project type — elevating it to a P-level rule would break the universality of P1–P16. Enriching the `architect` agent (already invoked at DESIGN and REVIEW) is minimal, conditional, and carries the recommendation exactly where it applies, with infrastructure (DEC + policy test from v0.35) already in place.

## [0.37.1] - 2026-04-20

Layers impacted: **implementation** (generator)

### Fixed
- **Generator `--clean` no longer wipes `plugin/tools/`.** The previous `shutil.rmtree(PLUGIN)` erased the hand-maintained `plugin/tools/` directory, which is the only subtree not regenerated from `src/` (per `CLAUDE.md`). Running `gse_generate.py --clean` silently deleted runtime-critical scripts like `dashboard.py` — discovered when a commit-in-progress showed `dashboard.py` as deleted. `--clean` now iterates `plugin/`'s children and skips `tools/`.
- **Hard verify check for `plugin/tools/dashboard.py`.** `verify()` now fails with a non-zero exit and an explicit error when the dashboard script is missing, instead of producing only a silent `WARNING`. Any future accidental deletion is surfaced immediately in CI.

### Rationale
The bug was latent: the generator's `--clean` flag assumed `plugin/` was fully reproducible from `src/`, but `plugin/tools/` is a deliberate asymmetry. Encoding the asymmetry directly in the clean logic (rather than only in documentation) removes the footgun. The hard verify check is defense-in-depth — if `plugin/tools/dashboard.py` disappears for any other reason (mis-merge, human error), the next `--verify` run catches it.

## [0.37.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (tutor agent merged into unified `coach` agent)

### Changed
- **Tutor agent merged into unified `coach` agent** (AMÉL-16 from training feedback). The v0.36 `tutor` and the earlier proto-`coach` observation concern are now a single specialized sub-agent (`agents/coach.md`) observing the AI+user collaboration along **8 axes** grouped into two categories:
  - **Pedagogy** (axis 1, ex-tutor): explicit `learning_goals` + inferred competency gaps → 5-option P14 preambles, LRN- learning notes.
  - **Workflow** (axes 2–8): profile calibration (HUG drift), sprint velocity, workflow health, quality trends, engagement pattern (P16 acceptance/pushback), process deviation, sustainability (session cadence).
- **Per-axis toggles** in `config.yaml → coach.axes.*` — users disable what's irrelevant (e.g., sustainability off for async solo work, engagement off when P16 is already visible enough). Master switch `coach.enabled` and per-invocation caps (`max_preambles_per_sprint`, `max_advice_per_check`) preserved.
- **Invocation contract** — orchestrator passes a `moment` tag (`activity_start:/gse:*`, `sprint_close`, `mid_sprint_stall`, `gate_sequence_end`, `activity_skip_event`, `session_boundary`, `compound_axe_3`, `inferred_gap_trigger`, `profile_drift_recurrence`); coach returns zero or more YAML blocks (`skip | propose | advise`) materialized as P14 Gates (pedagogy) or Inform/Gate lines (workflow).
- Specialized-agent count unchanged at 9 — `tutor.md` removed, `coach.md` added.

### Added
- **`profile_drift_signals{}` field** in `status.yaml` — persistent map of HUG-profile drift observations, debounced across sessions, consumed by profile-calibration axis at `/gse:compound` Axe 3 to propose `/gse:hug --update`.
- **`workflow_observations[]` field** in `status.yaml` — transient scratchpad for velocity/health/quality/engagement/deviation/sustainability observations during the sprint, cleared at sprint close after consumption by compound.
- **Coaching recipes section** in `agents/coach.md` — extensible, tagged `for: pedagogy | workflow | both`, dual-maintenance (user-editable + agent-updatable via `/gse:compound` Axe 3). Replaces the v0.36 tutor "Pedagogical recipes" section with broader scope.

### Removed
- `gse-one/src/agents/tutor.md` (content absorbed into `coach.md`).
- `pedagogy:` section in `config.yaml` templates (replaced by `coach:` section with the same defaults plus per-axis toggles).
- *Tutor agent — Design Mechanics* subsection in `gse-one-implementation-design.md` (replaced by *Coach agent — Design Mechanics* covering all 8 axes).

### Rationale
Both the tutor (pedagogy) and the proto-coach (workflow monitoring) read from overlapping signal sources — `profile.yaml`, `status.yaml` history, activity transitions, P16 counters. Keeping them as two separate agents duplicates the signal-reading layer and splits extensibility (two recipes files, two sets of toggles, two invocation contracts). A single unified agent holds the full observational picture in one fresh-context invocation, exposes a single extensibility surface (recipes tagged per axis), and lets users turn observation on/off dimension by dimension rather than all-or-nothing. The 8-axis framing makes the agent's mandate legible while preserving P14 pedagogy semantics bit-for-bit (same 5-option gate, same persistence fields, same anti-spam caps).

## [0.36.0] - 2026-04-20

Layers impacted: **spec**, **design**, **implementation** (new agent + orchestrator + config/status templates + generator)

### Added
- **New `tutor` specialized agent** (AMÉL-15 from training feedback) — dedicated sub-agent managing user upskilling along two axes: (1) explicit `learning_goals` from HUG, (2) inferred competency gaps detected from friction patterns (repeated questions, hesitations, explicit confusion, shotgun-fix correlation with P16 root-cause counter). Delivers P14 knowledge transfer via contextual evaluation + 5-option P14 preambles with precise, context-aware topic formulation (e.g., "property-based testing specifically relevant to the state invariants in your design" — not just "testing"). Architecture consistent with the other advocates (architect, security-auditor, ux-advocate, devil-advocate). Count of specialized agents: 8 → 9.
- **Pedagogical evaluation invariant in the orchestrator** — at activity start, if `learning_goals` is non-empty AND `pedagogy.enabled: true` AND sprint cap not exhausted, the orchestrator spawns the tutor for contextual evaluation. Tutor returns skip (silent) or propose with a topic and 5-option preamble content.
- **Extensible pedagogical recipes in `agents/tutor.md`** — a dedicated section users can edit manually AND the agent can auto-update via `/gse:compound` Axe 3 when a presentation strategy proves effective. Examples seeded: concrete-first preference, abstract-first preference, methodology self-improvement topics.
- **New `pedagogy` config section** (`config.yaml`): `enabled` (boolean, default true), `max_preambles_per_sprint` (cap, default 3), `proactive_gap_detection` (boolean, default true — monitors friction patterns to infer gaps).
- **New `learning_preambles[]` and `detected_gaps[]` fields** in `status.yaml` — persistent history of tutor interactions (respects `not-interested` permanently and `not-now` per-activity) and inferred-gap ledger reviewed at `/gse:compound` Axe 3.
- New *Tutor agent — Design Mechanics* subsection in `gse-one-implementation-design.md` with invocation contract, inputs/outputs, persistence model, and dual-maintenance rules for pedagogical recipes.
- `tutor.md` added to `SPECIALIZED_AGENTS` list in `gse_generate.py` so it is copied to the three platform targets (Claude skills, Cursor, opencode).

### Rationale
Observed training feedback (learner05): *"Consider making this an auto-propose behaviour when `profile.learning_goals` intersects with the next activity. Currently it's ad-hoc — formalising would remove guesswork."* After analysis, a static `goal → activity` lookup table is too rigid (misses precise goals, orthogonal goals, abstract goals, task-content-driven goals). A dedicated **tutor agent** performs contextual evaluation instead: objective (fresh context), precise (topic tied to what the activity will actually exercise), extensible (pedagogical recipes file), non-saturating (caps, persistence of user choices). Pattern consistent with the other specialized advocates.

## [0.35.0] - 2026-04-20

Layers impacted: **spec**, **design**, **implementation** (test pyramid + tests activity)

### Added
- **Policy tests as a first-class pyramid level** (AMÉL-13 from training feedback). New "Policy" column in the spec §6 test pyramid (5% baseline across all domains, raisable to 10-15% for strict-architecture projects). Policy tests enforce **structural rules** on the codebase via static analysis: architecture layering (e.g., `src/domain/** must not import src/ui/**`), license compliance (`no GPL dependency`), naming conventions, file-size limits, docstring requirements, dependency rules.
- New *Policy tests — Design Mechanics* subsection in `gse-one-implementation-design.md` with tooling suggestions per language (`pytest-archon`, `grimp`, `ts-arch`, `dependency-cruiser`, `ArchUnit`, `go-arch-lint`, `cargo-deny`, `license-checker`, etc.) and the rationale for making Policy first-class rather than a subset of Other.
- New *Policy test derivation* section in `/gse:tests` Step 1 — automatic scan of `design.md` (Architecture Overview / Component Diagram / Shared State) and `decisions.md` (DEC- entries with architectural intent) to propose policy tests as Inform-tier suggestions. Each accepted proposal becomes a TST-NNN with `level: policy` and `traces: { enforces: [DEC-NNN, ...] }`.
- Distinction clarified: **Policy** = purely structural (static scan, no runtime); **Other** = dynamic-constraint checks attached to behavioral tests (accessibility, performance, compatibility, hardware simulation, data quality).

### Changed
- Spec §6.1 pyramid table: Policy column inserted before Other. Unit and Other percentages lightly rebalanced across all 8 domains to make room for Policy's 5% baseline. Totals preserved.
- `/gse:tests` command description in spec §3 now mentions Policy as a covered test level.
- `/gse:tests --strategy` Step 1 description updated: test strategy is now derived from **three sources** (validation from REQS, verification from DESIGN, policy from DESIGN+DECISIONS structural rules).

### Rationale
Observed training feedback (learner05): *"Policy tests don't fit the unit/integration/e2e pyramid. These are real tests that guard the codebase's shape, not its behaviour. Promote to a first-class level."* Matches observed industry practice in mature codebases (ArchUnit in Java, ts-arch in TypeScript, pytest-archon in Python). Making Policy explicit in the pyramid forces honest budgeting at strategy time and surfaces the architecture-enforcement concern that would otherwise stay invisible.

## [0.34.1] - 2026-04-20

Layers impacted: **spec**, **implementation** (activity preview — documentation clarification only, no new mechanism)

### Added
- **Sprint-level skip condition for PREVIEW** (AMÉL-11 from training feedback, documentation clarification). When the current sprint contains no task producing a user-visible or demonstrable artefact (foundation sprints doing infrastructure, reqs, design, tests only), PREVIEW is legitimately skipped. Recorded in `plan.yaml → workflow.skipped` with reason *"no user-visible tasks in this sprint — preview will apply in a future sprint when demonstrable work is scheduled"*. Standard skip, no DEC- created.
- Explicit anti-pattern documented: **preview-ahead is NOT supported**. Tasks scheduled for future sprints must not be previewed during the current sprint's PREVIEW. Rationale: staleness risk if target scope evolves, blurred sprint boundaries, traceability disruption. PREVIEW is just-in-time.

### Changed
- `/gse:preview` Step 1 enriched with the skip condition and the anti-preview-ahead rule.
- Spec §3 `/gse:preview` command description mentions the skip and the anti-preview-ahead rule.

### Rationale
Observed training feedback (learner05): *"PREVIEW in a foundation-only sprint is semantically odd — there's no UI code in Sprint 1 to preview. Solution: preview the Sprint 2 screens during Sprint 1."* After analysis, the just-in-time principle is more aligned with the methodology than preview-ahead: each sprint runs its own PREVIEW when it contains the tasks concerned. The skip is the clean, faithful answer — zero new mechanism introduced.

## [0.34.0] - 2026-04-20

Layers impacted: **spec**, **design**, **implementation** (P10 principle + activity plan + config template)

### Added
- **Semantic redefinition of the complexity point** (AMÉL-10 from training feedback). One complexity point now officially measures **coupled effort and complexity for the AI + user pair**: code complexity added + AI generation effort + human review effort, treated as a single scalar because these dimensions are entangled in practice.
- **Indicative temporal anchor**: 1 point ≈ 1 pair-session hour (AI generation + user review + decision). A 10-point sprint ≈ 1-3 working days with AI, or ~1-2 weeks for a solo human without AI (speedup ratio typically 10×, varying 5-20× by domain — CRUD-standard ~15-20×, algorithmic / research ~3-5×). The anchor is **indicative, not prescriptive** — spec §2 "Sprint = complexity-boxed, no fixed duration" is preserved.
- **Appendix B in spec: Cost Assessment Grid for Maintenance Work** — four-criteria grid (fan-out, review burden, rework risk, coupling) yielding 0 / 1 / 2-5 pt for refactoring, tests, docs, renaming, bug-fixing. Replaces the pre-v0.34 "zero-cost items" blanket rule that underestimated maintenance load.
- Full definition propagated to: spec §2 P10, spec §8.1 Concept, spec glossary (2 entries), P10 principle file (new "Definition of a complexity point" + "Temporal anchor (indicative)" sections), config.yaml template (enriched comment), design doc §5.17 "Complexity budget ranges" mechanics note.

### Changed
- **`/gse:plan` sizing scale** — the S/M/L letter scale (S=1, M=3, L=5) is abandoned. Tasks are now sized directly in integer complexity points (typically 1-6 from the P10 cost table). Rationale: the letter scale required a mental translation step between two coexisting scales (learner05 training feedback); with the new semantic unifying complexity + effort in a single unit, the letter scale became redundant.
- **P10 principle rule 8** replaced: the "zero-cost items" blanket (refactoring / tests / docs / bug fixes / removals = 0 pt always) becomes a case-by-case judgment using the new Appendix B grid. Removing code / dependencies remains a simplification credit (negative points) regardless of scale.
- Spec §8.1 and glossary entries updated with the temporal anchor and the new definition.
- `config.yaml` template comment for `complexity.budget_per_sprint` now explains the pair-effort semantics and the indicative temporal anchor.

### Preserved
- Sprint = complexity-boxed, no fixed duration (spec §2). The temporal anchor is a calibration aid, not a deadline.
- P10 cost table values (1-6 pt per decision type) unchanged — only the semantic interpretation is enriched.
- Simplification credit rule — unchanged.
- Default budget values — config.yaml defaults to 10 pt/sprint; spec §8 recommendations remain 15/12/8 for foundation/feature/stabilization sprint types.
- Backward compatibility — existing `complexity: 3` in backlog.yaml files is valid as-is with the enriched interpretation.

### Fixed
- Translation friction observed in training session learner05 ("Two scales coexist [P10 fine-grained and S/M/L] which took a mental translation step"). One unit now — complexity points with a pair-effort semantic.
- Underestimation of sprint load when the sprint is mostly maintenance (previously zero-cost under the blanket rule). The grid forces honest sizing.

## [0.33.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (activities preview + produce)

### Added
- **Scaffold-as-preview** as an officially-supported PREVIEW variant (AMÉL-09 from training feedback). New Step 1.5 "Preview Variant Selection" Gate at the start of `/gse:preview` lets the user pick between:
  - **(1) static description** — wireframes, ASCII diagrams, user story walkthroughs written into `preview.md` (default for API / CLI / library / scientific / data previews).
  - **(2) scaffold-as-preview** — minimal runnable project using the chosen framework (Vite+React, Streamlit, Next.js, etc.) that becomes the base for the following `/gse:produce`. Placeholder code marked with `PREVIEW:` comments (language-idiomatic: `//`, `#`, `<!-- -->`, `/* */`). Build evidence: exit 0 on the framework's build command.
- **Agent recommendation** per project domain (web/mobile → scaffold recommended; api/cli/library/scientific → static recommended).
- **`PREVIEW:` comment convention** documented: each marker must include a descriptor explaining what will replace it, ideally with a TASK- reference.
- **`/gse:produce` Step 1 scan** — when the sprint used scaffold-as-preview, a grep-based Inform-tier scan of residual `PREVIEW:` markers is presented at task selection as a visibility cue (not a guardrail).
- **`preview_variant` and `scaffold_path` fields** added to the preview artefact frontmatter for traceability.
- New *Preview Variants — Design Mechanics* subsection in `gse-one-implementation-design.md` detailing when each variant applies, the comment convention per language family, and integration with PRODUCE.
- `/gse:preview` command description in spec §3 updated to mention the two variants.

### Scope for v0.33
- Scaffold-as-preview applies only to UI and feature walkthrough preview types. API / architecture / data model / import previews remain static (they describe concepts that don't benefit from a runnable scaffold).

### Fixed
- Silent scaffold-as-preview improvisation observed in training sessions (learner05 justified it as DEC-011 methodology deviation; learner06 and learner10 did it implicitly without formal documentation). The pattern is now a first-class variant with a clear contract, preventing the "is this a deviation?" ambiguity.

## [0.32.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (activity design + sprint template)

### Added
- **Shared State section in design artefact** (AMÉL-06 from training feedback) — The sprint design template (`gse-one/src/templates/sprint/design.md`) gains a new mandatory `## Shared State` section between Data Model and Technology Choices. Each entry captures: name (conceptual), scope (components/pages), mechanism (framework-appropriate storage + sync), rationale (one sentence), traces (REQ IDs). When no shared state applies, an explicit disclaimer line is mandatory — empty section is not permitted.
- **New Step 2.5 "Shared State Identification"** in `/gse:design` between Component Decomposition and Interface Contracts. Walks through component pairs and asks whether each reads/writes state that must stay consistent. Populates the design artefact's Shared State section with an algorithm, examples, and domain-adapted expectations (web/mobile: 1-5 entries typical; CLI/library: often zero; API: request context, session).
- New *Shared State — Design Mechanics* subsection in `gse-one-implementation-design.md`.
- `/gse:design` command description in spec §3 updated to mention shared state identification.

### Fixed
- Silent duplication of state across components (training session learner06: 3 independent Streamlit month widgets instead of one shared `st.session_state["selected_month"]`, despite REQS stating "filter by month on all pages"). The design artefact now formalizes shared state as a first-class decision, surfacing the question at DESIGN time rather than after the fact.

## [0.31.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (activities compound/integrate + config template)

### Added
- **Methodology feedback routing via `/gse:compound` Axe 2** (AMÉL-14 from training feedback). Instead of introducing a new `/gse:journal` skill, the existing `/gse:compound` Axe 2 is enriched with a closure Gate offering three options: *(1) Export as a local feedback document only* (produces `docs/sprints/sprint-{NN}/methodology-feedback.md` — shareable markdown, no GitHub interaction), *(2) Propose GitHub tickets* (quality-filtered, theme-grouped, deduplicated, capped by `compound.max_proposed_issues_per_sprint`, each validated by the user individually), *(3) Both*. Users who opt out of upstream feedback (no `github.repo` configured) only see option 1.
- New `compound.max_proposed_issues_per_sprint` config field (default: **3**) — hard cap to prevent upstream ticket spam. Excess themes consolidate into the local export.
- Quality rules for ticket proposals: concrete (cites at least one specific example), theme-grouped (one ticket per theme), deduplicated via `gh issue list` (fallback: "dedup unverified" marker), capped, user-validated per ticket.
- `.gse/compound-tickets-draft.yaml` handoff file between COMPOUND and INTEGRATE Axe 2 — ensures tickets are validated at COMPOUND, then submitted at INTEGRATE without re-opening the choice.
- New *Methodology Feedback — Design Mechanics* subsection in `gse-one-implementation-design.md`.
- Sources scanned by Axe 2: RVW findings tagged `[METHOD-FEEDBACK]`, DEC- entries with `type: methodology-deviation`, `status.yaml → activity_history[*].notes`, and agent conversation memory.

### Changed
- Spec §3 `/gse:compound` command description updated to reference the 3-option Gate.
- Spec §2 P14 Methodology self-improvement section rewritten to describe the new flow (local export + curated tickets + quality rules).
- `/gse:compound` Step 2 (Axe 2) fully rewritten with explicit sub-steps: gather observations → synthesize themes → closure Gate → local export / ticket Gate / persist summary.
- `/gse:integrate` Step 2 (Axe 2) rewritten to consume the draft file produced by COMPOUND, with a final confirmation Gate and cleanup on successful submission.

### Fixed
- Ad-hoc student-notes improvisation observed in training session learner05 (participant manually requested and structured a `docs/student_notes.md`). The formalized COMPOUND Axe 2 export now provides a first-class path for this feedback without introducing a new skill or daily-journaling mechanism. Quality cap prevents the ticket-pollution anti-pattern when feeding upstream.

## [0.30.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (orchestrator + activities produce/task)

### Added
- **Config Application Transparency** (AMÉL-12 from training feedback) — Every activity that materializes a `config.yaml` field with user-visible consequences (creates files/directories, modifies git state, enforces hard thresholds, changes delivery behavior) MUST emit a one-line Inform note at the moment of materialization. Format: `"Config applied: <field> = <value> (<origin> — to change: /gse:hug --update or edit .gse/config.yaml)"`. Origin computed at display time by comparing current value to the methodology default. Adapted to P9 for beginners (plain-language translation). Pure Inform-tier discipline — no Gate, no new state, no interruption. Prevents the surprise pattern where users discover unexpected behavior (e.g., worktree directories) after the fact.
- New paragraph in spec P7 (Risk-Based Decision Classification) documenting the general discipline.
- New *Config Application Transparency — Design Mechanics* subsection in `gse-one-implementation-design.md` with the standard format, origin classification algorithm, beginner adaptation, and extension pattern.
- New *Config Application Transparency Discipline* section in the orchestrator.

### Changed
- `/gse:produce` Step 2 (Git Setup) — adds the Inform note before creating the first branch or worktree, covering the three `git.strategy` values (worktree / branch-only / none) with appropriate wording for each.
- `/gse:task` Step 4 (Git Setup) — same pattern, deduplicated within a sprint via `status.yaml → last_activity` trail.

### Scope for v0.30
- Covered: `git.strategy` materialized by `/gse:produce` and `/gse:task`. Directly addresses the training feedback (learner05: surprise worktree creation).
- Extension path documented — future materializations (e.g., `testing.coverage.minimum` at `/gse:tests`, `git.tag_on_deliver` at `/gse:deliver`) follow the same pattern by adding the Inform line to their relevant step.

### Fixed
- Silent application of `git.strategy` default observed during training session learner05 (pragmatic deviation from config logged as DEC-015 after the fact). The Inform note now surfaces the choice and its origin at the moment of action, without requiring a Gate.

## [0.29.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (orchestrator + 5 activities + intent template)

### Added
- **Open Questions mechanism — first-class concept** (AMÉL-08 + AMÉL-07 retrofit) — Ambiguities raised in artefacts are now structured entries with a full schema: `id` (new prefix `OQ-`), `question`, `resolves_in` (ASSESS | PLAN | REQS | DESIGN), `impact` (scope-shaping | behavioral | architectural | cosmetic), `status`, provenance (`raised_at`), and on resolution `resolved_at`, `resolved_in`, `answer`, `answered_by`, `confidence`, `traces`. Schema formalized in spec P6.
- **Activity-entry scan (transversal rule)** — The four lifecycle activities `/gse:assess`, `/gse:plan`, `/gse:reqs`, `/gse:design` each begin with a new **Step 0 Open Questions Gate** that scans `docs/intent.md` and the current sprint's artefacts for pending `OQ-` whose `resolves_in` matches the current activity. Resolutions are recorded in place (origin artefact updated, status flipped).
- **Scope-resolve absorbed as `/gse:plan` Step 0** — No separate `/gse:scope` skill is introduced. Open questions tagged `impact: scope-shaping` with `resolves_in: PLAN` are resolved at the beginning of `/gse:plan --strategic`, before item selection. Respects P5 (planning transversality) and keeps the catalog at 23 activities.
- **Mode-calibrated interaction via `decision_involvement`** — The Open Questions Gate behavior adapts to the HUG profile field: `autonomous` (agent pre-answers, Gate only for high-impact), `collaborative` (per-question Gate with agent proposal, default), `supervised` (neutral Gate, no pre-answer). Reuses existing infrastructure — no new mode concept introduced.
- New `OQ-` prefix added to spec P6 traceability table, `Open Question` glossary entry, `Activity-entry scan` glossary entry.
- New **Open Questions Resolution Invariant** section in the orchestrator listing concerned activities, scan mechanics, and mode behavior.
- New **Open Questions Resolution — Design Mechanics** subsection in `gse-one-implementation-design.md` detailing source enumeration, markdown format (human-readable bullet list with sub-fields), parsing rules, recording format, scope-shaping propagation, and failure modes.

### Changed
- **Retrofit AMÉL-07 terminology** — The informal term `natural home` introduced in v0.28 is **renamed to `resolves_in`** across all artefacts (spec, design, orchestrator, template, go.md) and given a formal schema. The valid values are now `ASSESS | PLAN | REQS | DESIGN` (previously included the informal `scope-lock`, which is removed — scope-resolve is folded into PLAN Step 0).
- `gse-one/src/templates/intent.md` — Open Questions section rewritten as structured markdown entries (not plain bullet list), consumable by the activity-entry scan.
- `/gse:go` Step 7 Intent Capture — updates the wording to reflect the new `resolves_in` / `impact` fields.
- `/gse:plan --strategic` Step 0 renamed from "Previous Sprint Analysis" to "Open Questions Gate" (now primary); the previous analysis becomes Step 0.5.
- `/gse:reqs` — new Step 0 "Open Questions Gate"; previous "Conversational Elicitation" renumbered to Step 0.5. Mode-Specific Ceremony table updated accordingly.
- `/gse:assess`, `/gse:design` — new Step 0 "Open Questions Gate" inserted before their first existing step.

### Fixed
- Greenfield experts (training session learner05) previously had to improvise ad-hoc scope-lock elicitation outside the lifecycle (DEC-003 methodology deviation, 9-question ad-hoc elicitation). With the Open Questions mechanism + activity-entry scan, scope-shaping questions now flow from Intent Capture → `/gse:plan` Step 0 automatically, respecting the methodology.

## [0.28.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (activities go/collect + orchestrator + new template)

### Added
- **Intent Capture for greenfield projects** (AMÉL-07 from training feedback) — When `/gse:go` detects a greenfield project (no source files after standard exclusions) AND no existing intent artefact, it now enters Intent Capture BEFORE the complexity assessment. Produces a formal `INT-001` artefact at the canonical path `docs/intent.md` with four mandatory sections (Description verbatim, Reformulated understanding, Users, Boundaries) + optional Open questions tagged with their natural resolution home. Applies to **all expertise levels** — tone and cadence adapted via P9. Seeded backlog items carry `traces.derives_from: [INT-001]` preserving intent-to-backlog provenance.
- New artefact type `intent` with prefix `INT-` added to spec P6 (Traceability) table.
- New template file `gse-one/src/templates/intent.md` with standardized structure.
- New `/gse:collect` Step 0 "Verify Intent Exists" — preflight check on greenfield that redirects to Intent Capture if no intent artefact is present.
- New *Intent Capture for Greenfield Projects* section in the orchestrator.
- New *Intent Capture — Design Mechanics* subsection in `gse-one-implementation-design.md` detailing trigger detection, artefact structure, elicitation loop, integration with downstream activities (REQS, ASSESS, PLAN), and failure modes.

### Changed
- Spec §3 decision tree: previous trigger *"`it_expertise: beginner` + `current_sprint: 0`"* replaced by *"greenfield project + no intent artefact"*. The trigger is now project state, not user profile. Experts greenfield no longer bypass intent capture silently.
- Spec §3 Step 5 "Intent-first mode" renamed to "Intent Capture" and rewritten to reflect the new trigger and formal artefact output.
- `/gse:go` Step 7 "Intent-First Mode" renamed to "Intent Capture", trigger broadened, explicit step to write `docs/intent.md` added, existing artefact detection added.
- Spec §15 glossary: "Intent-first mode" entry updated to "Intent Capture" with the new semantics; new "Intent artefact (`INT-`)" entry added.

### Fixed
- Greenfield experts (training session learner05) previously bypassed the agent's Intent-First flow and had to improvise an ad-hoc `docs/intent.md` file without a standard structure. The formal artefact + broadened trigger now serves all expertise levels.

### Migration note
Pre-v0.28 projects without an `INT-` artefact are unaffected — the trigger fires only on greenfield new projects. Existing projects with improvised `intent.md` files can adopt the new format manually by renaming their file to match the canonical template (frontmatter `id: INT-001` + four standard sections).

## [0.27.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (activities design/preview/produce/task + orchestrator + status.yaml schema)

### Added
- **Scope Reconciliation guardrail** (AMÉL-05 from training feedback, also closes AMÉL-17) — At the end of every creator activity that produces code (`/gse:produce`, `/gse:task`), the agent compares delivered files against the planned REQ/DEC set. Detection is deterministic via `git diff --name-status {activity_start_sha}..HEAD` cross-referenced with per-commit `Traces:` trailers. Deltas categorized as `ADDED out of scope`, `OMITTED`, or `MODIFIED beyond plan`. If non-empty, a 4-option Gate fires: *Accept as deliberate* (grouped DEC-NNN summarizing additions by theme, OMITTED items move to backlog pool), *Revert out-of-scope*, *Amend* (lightweight REQ/DEC appended without re-elicitation), *Discuss*. Skipped silently when all deltas are aligned.
- **Inform-Tier Decisions Summary** — At the end of every creator activity (`/gse:design`, `/gse:preview`, `/gse:produce`, `/gse:task`), the agent lists the Inform-tier decisions it made autonomously (P7) and offers a 3-option Gate: *Accept all as-is* (default, appended as `## Inform-tier Decisions` section in the activity's artefact), *Promote one or more to Gate* (retrospective elevation with standard Gate format), *Discuss*. Empty-list case shown explicitly as *"No inform-tier decisions made this activity — all choices were Gated."*
- New `activity_start_sha` field in `.gse/status.yaml` — HEAD SHA recorded at creator-activity start, used exclusively for Scope Reconciliation, cleared on closure.
- New *Creator-Activity Closure Invariant* section in the orchestrator combining both mechanisms.
- New *Scope Reconciliation & Inform-Tier Summary — Design Mechanics* subsection in `gse-one-implementation-design.md` with full git-diff mechanics, trace parsing, delta categorization, Gate formats, and failure modes.
- New *Scope Reconciliation — creator-activity closure check* paragraph in spec P6 (Traceability); new *Inform-Tier Decisions Summary* subsection in spec P16 (AI Integrity).

### Changed
- `/gse:produce` — added Step 2 sub-step "Record activity start SHA", new Step 4.5 (Scope Reconciliation) between test run and Finalize, new Step 5.5 (Inform-Tier Summary) between Finalize and dashboard regen, Finalize step renumbered.
- `/gse:task` — same pattern (SHA record in Step 4, Step 5.5 Scope Reconciliation, Step 6.5 Inform-Tier Summary).
- `/gse:design` — new final Step 7 Inform-Tier Summary.
- `/gse:preview` — new final Step 4 Inform-Tier Summary.

### Fixed
- Silent scope drift during PRODUCE observed in training sessions learner06 (Opus autonomous additions: `note` column, `sort_order` field, monthly total widget — none in approved plan) and learner09 (Composer2 `Uncategorized` feature added without request). The reconciliation block now surfaces these drifts at activity closure with a clear override window.

### Closed
- **AMÉL-17** (Inform-tier decisions summary) — absorbed into this release.

## [0.26.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (activity fix + orchestrator + devil-advocate agent + status.yaml schema)

### Added
- **Root-Cause Discipline guardrail** (AMÉL-03 from training feedback) — When a defect is reported (either a review finding during `/gse:fix`, or a user-reported bug during any activity), the agent MUST follow a 4-step protocol *Read → Symptom → Hypothesis+Evidence → Patch* before modifying any file. A blind patch on unread code is forbidden; hypotheses must be evidence-tested before patching.
- **Failed-patch counter** `fix_attempts_on_current_symptom` in `.gse/status.yaml`. Increments on each patch that does not resolve the symptom. Resets on user confirmation of resolution, explicit symptom change, or new sprint promotion.
- **Devil-advocate escalation** at counter threshold (beginner=2, intermediate=3, expert=4). The agent stops patching and spawns the devil-advocate in new `focused-review` mode, which receives the symptom, chain of failed hypotheses, patches applied, and files under suspicion, and returns findings including an *external-cause suggestion* when the code itself appears sound. At least one finding must be addressed before further patching on the same symptom.
- New *Root-Cause Discipline Invariant* section in the orchestrator listing concerned vs exempt activities and transversal counter semantics.
- New *Root-Cause Discipline — Design Mechanics* subsection in `gse-one-implementation-design.md` mapping protocol steps to concrete actions, counter mechanics, devil-advocate input format, and failure modes.
- New subsection P16 *"Root-Cause Discipline before patching"* in the spec with the 4-step protocol, threshold table, and rationale.

### Changed
- `/gse:fix` Step 3 entirely rewritten as "Apply Fixes (Root-Cause Discipline)" with 5 sub-steps (3.1 Read / 3.2 Symptom / 3.3 Hypothesis+Evidence / 3.4 Patch / 3.5 Counter and Escalation). Commit trailer now REQUIRES `Root cause:` and `Evidence:` lines.
- Devil-advocate agent extended with a `focused-review` mode (on-demand invocation with symptom + hypotheses + patches + suspect files). The standard `/gse:review` mode is preserved unchanged.

### Fixed
- Unsystematic debugging ("shotgun patching") observed during training session learner02: agent applied 3 consecutive speculative patches on a theme-toggle bug before the user forced a static code review, which immediately revealed the real cause was external (CORS `file://`) — not in the patched code at all.

## [0.25.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (activities hug/go + orchestrator), **docs** (README)

### Added
- **Git Identity Verification guardrail** (AMÉL-04 from training feedback) — `/gse:hug` Step 4 and `/gse:go` Step 2.7 now verify that a git identity (user name + email) is configured globally OR locally before attempting the foundational / auto-fix commit. If missing, the agent presents a 5-option Git Identity Gate: *Set global* (default) / *Set local* / *Quick placeholder* (sets `GSE User` / `user@local` locally, with a one-shot reminder to replace before sharing) / *I'll set it myself* / *Discuss*. Email format validation (`@` + dotted domain) on options 1 and 2. Prevents silent commit failures on fresh machines, classroom laptops, and CI containers.
- New *Git Identity Verification Invariant* section in the orchestrator listing writing vs exempt activities and the Gate shape.
- New *Git Identity Verification — Design Mechanics* subsection in `gse-one-implementation-design.md` mapping conceptual terms to concrete `git config` commands, with the email validation rule and the placeholder reminder policy.
- Enriched P12.0 *Foundational commit* rule in the spec with explicit identity precondition; new rule P12.6 formalizes the Git Identity Gate.

### Changed
- README quickstart (shared note after all 3 platform options) now clarifies that `git init` in `my-project/` creates an independent repository, distinct from the `.git/` of the gensem clone, and that GSE-One handles git identity setup automatically on first commit. Addresses the "when should git init happen?" ambiguity raised in training feedback (learner05).

### Fixed
- Silent commit failure on fresh machines when `user.name` / `user.email` are not configured (learner03 training session: first commit blocked, had to run `git config` commands manually before proceeding).

## [0.24.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (tool `dashboard.py`, generator hooks, opencode TS plugin, config template)

### Added
- **Automatic dashboard regeneration via editor hooks** (AMÉL-02 from training feedback) — `docs/dashboard.html` is now kept in sync with project state automatically. A cross-platform `PostToolUse` hook with **three separate matcher entries** (`Edit`, `Write`, `MultiEdit`) fires on every editor write and invokes `dashboard.py --if-stale`, which regenerates only if sprint state is newer than the existing dashboard, with a **configurable debounce window** (default: 5 seconds). The three-matcher approach ensures portability across Claude Code, Cursor, and opencode (including local-model setups) without relying on regex matcher support. Covers the 17 previously-uncovered activities.
- New `--if-stale` flag on `dashboard.py` with self-arbitrating mtime comparison.
- New `dashboard.regen_debounce_seconds` field in the `config.yaml` template (default: 5).
- **Failure visibility** — on internal exception, `dashboard.py` writes `.gse/.dashboard-error.yaml`. On next successful regeneration, a prominent red warning banner is injected at the top of the dashboard HTML, then the marker is cleared. A hook-wrapper double-defense covers the case where `dashboard.py` cannot start at all (subprocess non-zero exit writes a minimal marker).
- Opencode TS plugin extended to dispatch on `edit`/`write`/`multiedit` with the same marker-writing behavior on subprocess failure.

### Changed
- The 6 existing explicit regeneration calls in `hug`, `go`, `produce`, `review`, `deliver`, `compound` are preserved as belt-and-suspenders — the new hook is complementary, not substitutive.

### Fixed
- Dashboard staleness: previously 17 of 23 activities left the dashboard untouched, causing learners to see outdated sprint/phase/activity info between checkpoints (observed during training sessions learner02 and learner05).

## [0.23.0] - 2026-04-19

Layers impacted: **spec**, **design**, **implementation** (activities task/produce/fix/review + orchestrator)

### Added
- **Sprint Freeze guardrail** (AMÉL-01 from training feedback) — Once a sprint has been delivered, its plan transitions to *completed* and the sprint is frozen. Four writing activities (`/gse:task`, `/gse:produce`, `/gse:fix`, `/gse:review`) now present a Hard Sprint Freeze Gate when invoked on a frozen sprint, with default option to open the successor sprint via the mode-appropriate opening sequence. Three Gate options only: *Start next sprint now* / *Cancel* / *Discuss* — no "amend closed sprint" escape hatch. Complementary work is captured by opening a new sprint (e.g. titled *"Sprint N+1 — Complementary tasks"*).
- New *Sprint Freeze Invariant* section in the orchestrator (`src/agents/gse-orchestrator.md`) listing writing activities, exempt activities, Gate semantics, and promotion mechanics.
- New *Sprint Freeze — Design Mechanics* subsection in `gse-one-implementation-design.md` bridging spec-level concepts (*sprint plan status*, *the number of the sprint in progress*) to concrete implementation artefacts (`.gse/plan.yaml.status`, `.gse/status.yaml → current_sprint`).

### Changed
- `/gse:task` description in spec (§3.1) no longer fuit les noms de champs YAML (`artefact_type`, `sprint`) — vocabulaire conceptuel only, avec renvoi explicite au garde-fou Sprint Freeze.
- Decision tree in spec (§12) clarifies when the *number of the sprint in progress* advances: only `/gse:plan --strategic` increments it. The window between `/gse:integrate` and the next `/gse:plan --strategic` is naturally frozen and now handled by the Sprint Freeze Gate.

### Fixed
- Sprint closure is no longer silently violated by ad-hoc tasks / production / fix / review activities invoked post-delivery (bug observed during training session learner02).

## [0.22.0] - 2026-04-18

Layers impacted: **spec** (docs, major refactor)

### Changed
- `INSTALL-OPENCODE.md` §6.1 restructured into **three unified tables** sorted descending by SWE-bench Verified (April 2026):
  - §6.1.1 **Recommended local coding models** — merges the previous commodity (8–32 GB) and high-RAM (≥ 128 GB) tiers into a single 15-row table; adds `qwen3.6:35b-a3b` (73.4 % SWE-V) as the new top local pick, plus `qwen3.5:27b` (72.4 %), `qwen3.5:122b-a10b` (72.0 %), `qwen3.5:35b-a3b` (69.2 %), `qwen3:235b-a22b`.
  - §6.1.2 **Frontier open-weight models (via a cloud endpoint)** — 12 rows topped by MiniMax M2.5 (80.2 %), MiMo-V2-Pro (78.0 %), GLM-5 (77.8 %); adds the full MiMo V2 family (Pro / Omni / Flash), Qwen3.5-397B-A17B, Step-3.5-Flash.
  - §6.1.3 **Best SWE/coding models on OpenRouter** — 15 rows topped by Claude Opus 4.7 (87.6 %), Opus 4.6 (80.8 %), Gemini 3.1 Pro (80.6 %); new additions: Gemini 3.1/3 Pro Preview, GPT-5.2, Qwen3.6 Plus, Grok 4.20 (2 M context, multi-agent), Z.AI GLM-5 (replaces GLM-4.5), Xiaomi MiMo-V2-Flash.
- All three tables share a **9-column schema** (Model, Org, Params, Min VRAM/RAM, SWE-bench V., Context, GSE-One fit, Features, Best for/Notes). New **Features** column codes tool-calling, vision, thinking mode, agentic capabilities, websearch, FIM, long-ctx, multi-agent.

### Added
- §6.1 intro — legend for the Features column and explanation of the three-source sourcing strategy (local / open-weight cloud / OpenRouter).
- §8 references — added SWE-bench.com, LLM-Stats, BenchLM leaderboards.

## [0.21.7] - 2026-04-18

Layers impacted: **spec** (docs)

### Added
- `INSTALL-OPENCODE.md` §6.1.4 — Claude model family rows on OpenRouter: **Claude Opus 4.7** (★★★★★, 87.6 % SWE-Verified — new table leader), **Claude Sonnet 4.6** (★★★★★, 79.6 %) and **Claude Haiku 4.5** (★★★★☆, > 73 %). Provider snippet and GSE-One recommendations updated to reference them per activity.

### Fixed
- Corrected OpenRouter model ID for Claude Sonnet: `anthropic/claude-4.6-sonnet` → `anthropic/claude-sonnet-4.6` (OpenRouter uses the `<line>-<version>` order).

## [0.21.6] - 2026-04-18

Layers impacted: **spec** (docs)

### Added
- `INSTALL-OPENCODE.md` §6.1.3 and §6.1.4 — new "GSE-One fit" column (1–5 stars) on both model tables (frontier open-weight via cloud, OpenRouter). Ratings weight tool-calling reliability, context ≥ 128 k, SWE-bench Verified, and multi-step reasoning — the four capabilities GSE-One relies on for its full 23-activity lifecycle. Legend explains the scale under the OpenRouter table.

### Changed
- Clarified in the OpenRouter table that ★★☆☆☆ models (e.g. Codestral 25.08) are niche-only for inline completion, not recommended as primary for GSE-One agentic flow.

## [0.21.5] - 2026-04-18

Layers impacted: **spec** (docs)

### Added
- `INSTALL-OPENCODE.md` §6.1.4 — "Via OpenRouter (unified gateway)" with a ready-to-paste `opencode.json` provider snippet and a table of the top coding/SWE models on OpenRouter as of April 2026: MiniMax M2.5, Claude 4.6 Sonnet, Zhipu GLM-4.5, DeepSeek V3.2, Mistral Devstral (Medium/2512/Small), Qwen3-Coder, Kimi K2.5, **Codestral 25.08**, Mistral Large 3. Each row gives exact model ID, license, SWE-bench Verified score, context, input/output price per 1 M tokens, and best-fit GSE-One activity. Explicit note that Codestral is a fill-in-the-middle specialist, not a full agentic model.
- §8 references expanded with OpenRouter programming collection, Mistral provider page, OpenRouter rankings (April 2026), Codestral benchmarks review, and Codestral local deployment guide.

## [0.21.4] - 2026-04-18

Layers impacted: **spec** (docs)

### Added
- `INSTALL-OPENCODE.md` §6.1.3 — "Frontier open-weight models (via a cloud endpoint)" table: MiniMax M2.5 (80.2 % SWE-bench V.), GLM-5 (77.8), Kimi K2.5 (76.8), Step-3.5-Flash (74.4), GLM-4.7 (73.8), DeepSeek V3.2 (~73), Qwen3-Coder-480B (SWE-Pro 38.7), DeepSeek R1 (49.2). Each row gives license, MoE total/active, context, and opencode-specific usage note. Includes GSE-One-oriented recommendations (solo/cost-sensitive, privacy-critical, best-quality).
- §8 references expanded with Scale SWE-Bench Pro leaderboard, SWE-bench.com, BenchLM, Vellum, MorphLLM.

## [0.21.3] - 2026-04-18

Layers impacted: **spec** (docs)

### Added
- `INSTALL-OPENCODE.md` §6.1.2 — "High-RAM workstations (≥ 128 GB)" tier with Qwen 2.5 Coder 72B (Q8), Llama 3.3 70B (Q8), DeepSeek R1 70B distill, Mistral Large 123B (Q5), Llama 4 Scout (Q6), Qwen3 235B-A22B (Q4). Includes RAM-footprint estimates, MLX performance note for Apple Silicon, expected tok/s, and a "still out of reach at 128 GB" list (Qwen3-Coder 480B, DeepSeek V3/R1 full).
- §6.1 renamed §6.1.1 to "Commodity hardware (8–32 GB)" for clarity against the new tier.
- Extra references added to §8 (Apple Silicon guide, DeepSeek models guide, DeepSeek GPU requirements, opencode Tools doc).

## [0.21.2] - 2026-04-18

Layers impacted: **spec** (docs, trivial)

### Added
- `INSTALL-OPENCODE.md` §6.4 — clarification that opencode's built-in `websearch` tool requires `OPENCODE_ENABLE_EXA=1` + an Exa API key when running on a local provider (Ollama, LM Studio). `webfetch` stays available in all cases.

## [0.21.1] - 2026-04-18

Layers impacted: **spec** (docs)

### Changed
- `INSTALL-OPENCODE.md` — slimmed to opencode-specific content only (prerequisites, install/upgrade/uninstall, troubleshooting). Duplicated GSE-One background, command reference, and lifecycle moved to references to `README.md` and `gse-one-spec.md`.

### Added
- `INSTALL-OPENCODE.md` §6 — "Run opencode with a local model (Ollama / LM Studio)" with curated list of 2026-current local coding models (Qwen3-Coder-Next, Qwen 2.5 Coder 32B, Llama 3.3 70B, DeepSeek R1 14B, GPT-OSS 20B, Devstral Small 2), exact `opencode.json` provider snippets for Ollama and LM Studio, and agentic-flow tuning notes (context ≥ 64k, tool-calling on, temperature low). Model choices backed by April 2026 benchmarks — see references list in the doc.

## [0.21.0] - 2026-04-18

Layers impacted: **production** (major — new platform), **spec**, **design**

### Added
- **opencode platform support.** GSE-One now deploys natively on [opencode](https://opencode.ai) alongside Claude Code and Cursor. Installer gains `--platform opencode` and `--platform all` (all three platforms at once). Two install modes supported: `plugin` (global, `~/.config/opencode/`) and `no-plugin` (project, `.opencode/`).
- `gse-one/plugin/opencode/` — new generated subtree assembled from existing sources. Contains: `skills/<name>/SKILL.md` (with injected `name:` frontmatter required by opencode's loader), `commands/gse-<name>.md` (identical to Cursor), `agents/<name>.md` (8 specialized, `mode: subagent`, opencode `tools` object format), `plugins/gse-guardrails.ts` (native TS plugin reproducing the 3 guardrails from `hooks.claude.json`), `AGENTS.md` (orchestrator body wrapped in `<!-- GSE-ONE START/END -->` markers for surgical merge), `opencode.json` (default permissions + version marker).
- `install.py` — 4 new install/uninstall functions (`install_opencode_plugin`, `install_opencode_no_plugin`, and their uninstall counterparts), plus `_merge_agents_md`, `_strip_agents_md_block`, `_merge_opencode_json`, `_strip_opencode_json_marker`, `_deep_merge`, `_detect_opencode`. Interactive menu updated for opencode and "all three platforms".
- `gse_generate.py` — `build_opencode()` phase with 6 builders. SKILL.md files now receive `name:` injection globally (harmless for Claude, required by opencode).
- `INSTALL-OPENCODE.md` — user-facing quickstart for opencode installation and first-project setup.
- README files updated to list opencode as a supported platform.

### Changed
- `gse_generate.py` — generator docstring and `--verify` checks extended to cover the opencode subtree (skills, commands, agents, AGENTS.md body parity with `.mdc`, guardrails pattern presence).
- `install.py` — `--platform` choices extended to `opencode`, `all`; environment detection displays opencode status; duplicate detection warns on `.claude/skills` + `.opencode/` coexistence (opencode loads both).
- `CLAUDE.md` — "Files to keep in sync" updated with the opencode subtree.

## [0.20.8] - 2026-04-18

Layers impacted: **spec** (trivial)

### Added
- `CLAUDE.md` — new "Memory policy — in-repo only" section: any convention, rule, or preference Claude must remember across sessions for this project MUST live in a versioned file in the repo, never in Claude's per-machine auto-memory under `$HOME`. Rationale: the user works on this project from multiple machines via Dropbox; only the repo travels.

## [0.20.7] - 2026-04-18

Layers impacted: **spec** (trivial)

### Changed
- `CLAUDE.md` — Build pipeline now explicitly requires a `CHANGELOG.md` update between the VERSION bump and the generator run (step 2 of 6). Rationale: the v0.20.5 release shipped without a changelog entry; promoting the convention to a hard rule prevents recurrence.

## [0.20.6] - 2026-04-18

Layers impacted: **production** (trivial)

### Changed
- CHANGELOG catch-up release — documents the v0.20.5 fix that shipped without a changelog entry

## [0.20.5] - 2026-04-18

Layers impacted: **production** (minor)

### Fixed
- Claude Code no-plugin install: skills are now copied as `gse-<name>/` so commands appear as `/gse-<name>` in the TUI (e.g. `/gse-go`, `/gse-plan`) instead of the bare `/<name>` that project-level skills would otherwise receive — closest no-plugin UX to the `/gse:<name>` namespace produced by plugin mode

### Changed
- `install.py` — no-plugin mode now requires explicit confirmation of the naming trade-off before writing anything to disk
- `install.py` — legacy unprefixed skill directories from a prior install (≤ v0.20.4) are cleaned up automatically before the new prefixed layout is written
- `install.py` — `uninstall_claude_no_plugin` removes both prefixed (current) and unprefixed (legacy) layouts, making reinstall idempotent across versions

### Added
- Duplicate detection for Claude Code plugin mode now also checks `~/.claude/skills/` (home-level) in addition to the current project, catching conflicts for user-scope installs across all projects
- Duplicate detection for Claude Code no-plugin mode now probes `claude plugin list` to detect a registered `gse` plugin (previously skipped)
- New helpers `_detect_claude_plugin_installed()` and `_has_gse_skills_in_dir()` in `install.py`

## [0.20.4] - 2026-04-17

Layers impacted: **spec** (moderate), **design** (moderate), **source** (minor)

### Changed
- Lightweight `workflow.expected` aligned to `[plan, reqs, produce, deliver]` across all sources (was `[plan, produce, deliver]` in `plan.md` and design §10.1)
- FIX activity documented as conditional: `[FIX]` notation in LC02 sequence, glossary, ASCII diagram (spec); post-REVIEW mutation protocol added to design §10.1 and §5.14 decision table
- Complexity assessment: 7 structural signals (was 8) — source file count reclassified as trivialiy pre-filter for Micro detection, not a complexity signal (spec glossary, design §5.5, `go.md`, orchestrator)
- File inventory updated: 23 skills (was 22), 19 templates (was 15), 57 total files (was 52) in design §3.1, §11, §12
- Test review tier `[IMPL]` explicitly named in design §5.11
- Document versioning references removed from spec and design (version history consolidated in this file)
- Design §11.1 Evolution table removed (version history belongs in CHANGELOG.md)
- Design §5 renamed from "New Skill Designs (v0.6)" to "Skill Designs"
- Design §2, §9: removed "Unchanged from v0.2" cross-references to old document versions

### Fixed
- `plan_status` field: confirmed absent from both documents (removed in v0.20.1, no residual references)

## [0.17.1] - 2026-04-14

Layers impacted: **spec** (moderate), **design** (minor), **production** (minor)

### Added
- P12 rule 0: mandatory foundational commit on `main` after `git init` in HUG Step 4 — without it, all branching operations fail
- `/gse:go` Step 2.7: git baseline verification as safety net before branching (auto-fixes missing foundational commit)
- `/gse:plan` and `/gse:produce`: precondition check verifying `main` has at least one commit before creating branches
- Section 14.0.1: activity ceremony table by expertise level — defines minimum ceremony for each activity at beginner/intermediate/advanced levels
- Non-fusion rule in orchestrator Process Discipline and spec — activities MUST be executed as separate steps, adaptation is in communication not lifecycle structure
- Section 12.4.1: required fields specification for `config.yaml` and `status.yaml` — normative schema for dashboard and tool consumers
- Dashboard smoke test: validation warnings on stderr when required fields are missing or contain placeholder values

### Changed
- P16 passive acceptance counter: clarified increment rules (Gate decisions, single-word artefact confirmations) and reset rules (Discuss, why, modifications, rejections)
- `status.yaml` template: simplified P16 fields to `consecutive_acceptances` + `pushback_dismissed`, removed redundant boolean signals
- `dashboard.py`: fixed nested key lookup (`project.name`, `project.domain`, `lifecycle.mode`) for compatibility with spec-compliant config files

## [0.17.0] - 2026-04-14

Layers impacted: **spec** (major), **design** (minor), **production** (moderate)

### Added
- Conversational elicitation (Step 0) in `/gse:reqs` — free-form user dialogue before formalization captures functional needs and implicit quality expectations
- ISO 25010-inspired quality assurance checklist (Step 7) in `/gse:reqs` — verifies NFR completeness across 7 dimensions (Performance, Security, Reliability, Usability, Maintainability, Accessibility, Compatibility) with gap classification (HIGH/MEDIUM/LOW)
- Quality coverage matrix persisted in `reqs.md` template
- Quality-driven test derivation in `/gse:tests` — gaps from the quality checklist generate corresponding TST- artefacts with `quality_gap` trace
- Quality checklist completion check in `/gse:review` (Step 2c, requirements-analyst perspective)
- `--elicit` option in `/gse:reqs` — run only the conversational elicitation phase
- `elicitation_summary` field in requirements template frontmatter
- Section 0 "Getting Started" in spec — prerequisites and 20-minute quickstart for first-time learners
- "Essential Concepts" card (20 terms) at the top of the glossary (Section 15)
- 12 missing glossary terms: spike, acceptance criteria, lifecycle phases, intent-first mode, supervised mode, micro mode, stale sprint, design debt, regression test, quality gap, dependency audit, quality coverage matrix
- Commands-by-phase table (Section 3.10) mapping all 23 commands to lifecycle phases
- Spike documentation in `/gse:task` description (Section 3.1) — `--spike` flag with full rules
- Micro mode row in orchestrator decision tree (Section 14.3, Step 2) — was missing from spec

### Changed
- `/gse:reqs` workflow: 7 steps → 9 steps (added Step 0 elicitation, Step 7 quality checklist, renumbered Step 7 Persist → Step 8)
- Orchestrator guardrail "No PRODUCE without REQS" now also requires quality checklist completion
- Beginner output filter: 5 new entries (elicitation, quality checklist, quality gap, quality coverage matrix, updated `/gse:reqs` description)
- Lightweight mode row in decision tree now explicitly names the 3 health dimensions (test_pass_rate, review_findings, git_hygiene)
- Version notes and changelogs externalized from spec and design doc to this file (single source of truth)

## [0.16.0] - 2026-04-13

Layers impacted: **spec** (major), **design** (minor), **production** (major)

### Added
- Process discipline rule: lifecycle default is always the next step, no proactive shortcuts
- Beginner artefact approval via plain-language summaries (not raw technical files)
- Git branch check in PRODUCE (reminder, not blocker)
- Mandatory test campaign reports in `test-reports/` after every PRODUCE test run
- Requirements coverage analysis step in REQS (proactive gap detection across 9 dimensions)
- Dashboard: cumulative view (all sprints + archive), YAML parser handles nested keys
- HUG dimension #13: user name
- Compound auto-captures process deviations from review findings
- Tool registry `~/.gse-one` written by `install.py`

### Changed
- Branch naming: sprint integration branch renamed to `gse/sprint-NN/integration` (avoids git path conflict)
- Manual testing procedure in PRODUCE (adapted to project type and user level)
- Health scores written by review and deliver activities

## [0.15.0] - 2026-04-13

Layers impacted: **spec** (minor), **design** (minor), **production** (moderate)

### Added
- `~/.gse-one` registry file (written by `install.py`) for runtime tool resolution
- Dashboard moved to `plugin/tools/dashboard.py` with `# @gse-tool` header
- `install.py` writes/removes registry on install/uninstall
- README branding (header, banner, key features)

### Changed
- Kanban label readability (dark pill background)

## [0.14.0] - 2026-04-13

Layers impacted: **spec** (major), **design** (moderate), **production** (major)

### Added
- §1.2 Agile Foundations (principles, adaptations, originals)
- Test-driven requirements: acceptance criteria (Given/When/Then) mandatory in REQS, validation test derivation in TESTS
- Lifecycle guardrails (Hard): no PRODUCE without REQS, no PRODUCE without test strategy
- Spike mode (`artefact_type: spike`): complexity-boxed (max 3 pts), non-deliverable, bypasses REQS/TESTS guardrails
- Micro mode (< 3 files): PRODUCE → DELIVER, direct commit, 1 state file
- Supervised mode: `decision_involvement: supervised` escalates all PRODUCE choices to Gate
- Beginner output filter (28-entry translation table in orchestrator)
- Interactive question support (AskUserQuestion / Cursor clarifying questions)
- Language-first onboarding with locale detection
- Dashboard (`docs/dashboard.html` via `~/.gse-one` registry + `tools/dashboard.py`, Chart.js CDN)
- Cross-sprint regression scan during REVIEW
- Pre-commit self-review (5 checks)
- P16 passive acceptance signals + suppression rule
- Sprint archival during COMPOUND
- Monorepo `sub_domains` for per-directory test pyramid calibration
- Resilience: YAML validation, context overflow prevention, graceful degradation
- Maintainer Guide (spec Appendix B)
- Installer duplicate detection

### Changed
- LC02 order corrected: REQS → DESIGN → PREVIEW → TESTS → PRODUCE
- Complexity budget >100% downgraded from Hard to Gate guardrail
- P7 composite rule + uncertainty escalation in orchestrator
- P14: 5-option learning format + progressive reduction
- P15: confidence escalation to Gate for critical claims
- 23 commands, 3 modes (Micro/Lightweight/Full), 8 health dimensions

## [0.13.0] - 2026-04-12

Layers impacted: **spec** (moderate), **production** (minor)

### Added
- Interactive QCM via AskUserQuestion (Claude Code) and clarifying questions (Cursor)
- Language-first onboarding flow
- Adaptive question cadence by user expertise
- Beginner git init flow

## [0.12.0] - 2026-04-12

Layers impacted: **spec** (moderate), **design** (minor), **production** (major)

### Added
- `/gse:deploy` skill (23rd command): deploy current project to Hetzner server via Coolify
- Flexible starting points: from zero infrastructure (solo) to pre-configured shared server (training mode)
- 6-phase workflow: setup → provision → secure → install Coolify → configure DNS → deploy application
- Situation detection (Step 0): reads `.env` variables to skip completed phases automatically
- Training mode: `DEPLOY_USER` variable for per-learner subdomains on shared servers
- Templates: `deploy.json` (state schema), `Dockerfile` (Python/Streamlit), `deploy-env.example` (solo), `deploy-env-training.example` (training)
- Config section 12: `deploy:` (provider, server_type, datacenter, app_type, health_check_timeout)
- Options: `--status`, `--redeploy`, `--destroy` (Gate, double confirmation)
- Spec: new "Deployment" category (§3.8), glossary entries (Coolify, Deploy state), config deploy section, appendix updated

### Changed
- Command count: 22 → 23 (updated in spec, design, READMEs, plugin description)
- Template count: 15 → 19 (added deploy.json, Dockerfile, deploy-env.example, deploy-env-training.example)
- Plugin file count: 52 → 57

## [0.11.0] - 2026-04-12

Layers impacted: **spec** (major), **production** (moderate), **design** (minor)

### Added
- Three-level language management: `chat` (agent communication), `artifacts` (produced files, default: en), `overrides` (per-artefact-type). Configured at HUG, changeable at any time.
- Output formatting rules in P9: bold/italic/lists/code blocks conventions for cross-platform readability. Emoji dimension (on/off) added to HUG profile.
- Recovery check in `/gse:go` (Step 2): detects uncommitted changes from sessions that ended without `/gse:pause`, proposes recovery commit.
- Intent-first mode in `/gse:go` (Step 6): conversational intent elicitation for `beginner` users with new projects, plain language activity descriptions.
- Progressive expertise by domain: `expertise_domains` field in profile (empty at start, populated by agent observation). Per-domain calibration of communication depth and decision tiers.

### Changed
- HUG profile: `mother_tongue` replaced by `language: {chat, artifacts, overrides}`. Added `emoji` field. Profile now has 12 dimensions.
- P9 (Adaptive Communication): 6 rules → 9 rules (added domain-specific expertise, ask-don't-assume refinement, no condescension, output formatting).
- `/gse:go` workflow: 5 steps → 8 steps (added recovery check, intent-first mode, renumbered).
- Spec §14.3 (orchestrator decision logic): aligned with production go.md steps.

## [0.10.0] - 2026-04-12

Layers impacted: **spec** (major), **design** (moderate), **production** (major)

### Added
- Conceptual framework in spec: coding agent architecture, abstract execution loop, Claude Code and Cursor platform sections, inclusion policy mapping
- Agent Roles section in spec (9 agents with invocation mapping)
- Cross-platform installer (`install.py`): interactive + CLI, plugin + non-plugin modes, post-install verification
- Unified versioning: single `VERSION` file at repo root, read by generator and installer
- Stable filenames: `gse-one-spec.md`, `gse-one-implementation-design.md` (no version suffix)
- Terminology traceability notes across all three layers (spec activities, design skills, production SKILL.md)

### Changed
- P13 hooks reclassified: 7 hooks → 3 system hooks + 6 agent behaviors
- Hooks rewritten as cross-platform Python commands (exit 2 + stderr for blocking, exit 0 for informational)
- Config hooks section reduced to 3 keys (`protect_main`, `block_force_push`, `review_findings_on_push`)
- All documentation, templates, and examples neutralized for macOS/Linux/Windows
- `verbosity` default: `concise` → `standard`
- `post_tag_hook` example: `./scripts/deploy.sh` → `python scripts/deploy.py`
- Design §7 rewritten with Python hooks, 3 hooks only
- Installation docs in both READMEs simplified to reference `install.py`

### Removed
- Version suffixes in filenames (git history preserves old versions)
- Write|Edit reminder hooks (reclassified as agent behaviors)
- Manual platform-specific install commands from READMEs (replaced by installer)

## [0.9.0] - 2026-04-12

Layers impacted: **spec** (major), **design** (moderate), **production** (moderate)

### Added
- Conceptual framework (spec §1.1): coding agent, agent, skill (with inclusion policies), hook, template, tool definitions
- Platform-specific sections: Claude Code and Cursor execution loops, artifact delivery mechanisms, inclusion policy mapping
- GSE-One mono-plugin architecture mapping table
- Agent Roles section in spec (9 agents with invocation mapping)
- Terminology traceability notes across all three layers (spec → design → production)

### Changed
- **Unified versioning**: single `VERSION` file at repo root, read by generator — replaces per-file version management
- **Stable filenames**: `gse-one-spec.md` and `gse-one-implementation-design.md` (no version suffix)
- **P13 hooks reclassified**: 7 hooks → 3 system hooks (protect main, block force-push, review findings on push) + 6 agent behaviors
- Hooks rewritten as cross-platform Python commands with correct exit codes (exit 2 + stderr for blocking)
- Config hooks section reduced to 3 keys (`protect_main`, `block_force_push`, `review_findings_on_push`)
- `verbosity` default: `concise` → `standard`
- `post_tag_hook` example: `./scripts/deploy.sh` → `python scripts/deploy.py`
- All documentation, templates, and examples neutralized for macOS/Linux/Windows (symlinks → copy, bash → Python, tilde notes)
- Design §7 rewritten with Python hooks, exit 2, stderr, 3 hooks only
- Design cross-references updated to stable filenames

### Removed
- Version suffixes in filenames (git history preserves old versions)
- Write|Edit reminder hooks (reclassified as agent behaviors)
- `Supersedes` field in document headers (replaced by `VERSION` file + CHANGELOG)

## [0.8.0] - 2026-04-11

### Added
- Mono-plugin architecture: single `plugin/` directory deployable on both Claude Code and Cursor
- 22 commands covering the full SDLC: orchestration, planning, engineering, quality, capitalization
- 16 core principles (P1-P16): human-in-the-loop, guardrails, traceability, complexity budget, adversarial review, etc.
- 9 agents: 8 specialized (architect, code-reviewer, security-auditor, test-strategist, requirements-analyst, ux-advocate, guardrail-enforcer, devil-advocate) + 1 orchestrator
- 15 artefact and configuration templates
- Generator script (`gse_generate.py`): builds `plugin/` from `src/` with cross-platform parity verification
- Hooks support for both platforms (Claude PascalCase / Cursor camelCase)
- Marketplace metadata for Claude Code

### Changed
- Complexity-based sprint sizing replaces time-based estimation (adapted for AI-assisted engineering)
- Plugin manifests updated to point to `nicolasguelfi/gensem` repository

## [0.7.0] - 2026-04-10

### Added
- Initial implementation of the plugin structure
- Specification document (`gse-one-spec-v0.7.md`)
- Implementation design document (`gse-one-implementation-design-v0.7.md`)
- Cross-inspection and alignment between spec and design

## [0.6.0] - 2026-04-09

### Added
- Critical review and final inspection reports
- Cross-platform deployment analysis (Claude Code + Cursor)

## [0.4.0] - 2026-04-08

### Added
- Design review report (v0.4 vs spec v0.6)
- Specification v0.4, v0.5, v0.6

## [0.1.0] - 2026-04-06

### Added
- Initial project creation (originally named "gone")
- First specification and implementation design drafts
- Requirements document

[0.20.4]: https://github.com/nicolasguelfi/gensem/compare/v0.20.3...v0.20.4
[0.17.0]: https://github.com/nicolasguelfi/gensem/compare/v0.16.0...v0.17.0
[0.16.0]: https://github.com/nicolasguelfi/gensem/compare/v0.15.0...v0.16.0
[0.15.0]: https://github.com/nicolasguelfi/gensem/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/nicolasguelfi/gensem/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/nicolasguelfi/gensem/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/nicolasguelfi/gensem/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/nicolasguelfi/gensem/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/nicolasguelfi/gensem/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/nicolasguelfi/gensem/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/nicolasguelfi/gensem/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/nicolasguelfi/gensem/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/nicolasguelfi/gensem/compare/v0.4.0...v0.6.0
[0.4.0]: https://github.com/nicolasguelfi/gensem/compare/v0.1.0...v0.4.0
[0.1.0]: https://github.com/nicolasguelfi/gensem/releases/tag/v0.1.0
