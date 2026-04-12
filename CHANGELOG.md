# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.11.0]: https://github.com/nicolasguelfi/gensem/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/nicolasguelfi/gensem/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/nicolasguelfi/gensem/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/nicolasguelfi/gensem/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/nicolasguelfi/gensem/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/nicolasguelfi/gensem/compare/v0.4.0...v0.6.0
[0.4.0]: https://github.com/nicolasguelfi/gensem/compare/v0.1.0...v0.4.0
[0.1.0]: https://github.com/nicolasguelfi/gensem/releases/tag/v0.1.0
