# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
