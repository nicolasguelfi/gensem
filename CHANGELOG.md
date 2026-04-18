# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
