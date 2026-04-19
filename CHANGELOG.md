# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
