---
description: "Audit the GSE-One methodology repository for coherence across spec, design, and implementation. Combines deterministic checks (Python engine) with LLM-driven reasoning (methodology-auditor agent). Available only when invoked from the root of gensem or a fork of it."
---

# /gse-audit — Methodology coherence audit

Arguments: $ARGUMENTS

## Scope

This command audits a **GSE-One methodology repository** (upstream or a fork). It is **not** for auditing user projects — for that, see `/gse:status`, `/gse:health`, `/gse:review`, `/gse:assess`, `/gse:compound`, `/gse:collect`.

## Options

| Flag | Description |
|------|-------------|
| (no args) | Full audit: Phase 1 (deterministic) + Phases 2–3 (LLM reasoning) |
| `--deterministic-only` | Skip LLM phases, run Python engine only. Fast. |
| `--layer <spec\|design\|impl>` | LLM reasoning focused on one layer |
| `--cross-only` | Skip within-layer checks, only run the 3 cross-layer dimensions |
| `--format <json\|md>` | Output format (default: md) |
| `--fail-on <error\|warning>` | Exit non-zero if findings at this severity or higher (for scripting) |
| `--help` | Show this usage guide |

## Required readings

1. `.claude/agents/methodology-auditor.md` — adopt this role for the full audit
2. `gse-one-spec.md`, `gse-one-implementation-design.md` — loaded in Phases 2–3
3. `gse-one/src/**/*.md`, `gse-one/plugin/tools/*.py` — loaded on-demand

## Workflow

### Phase 0 — Context detection

Verify that we are in a GSE-One repository:
- `gse-one-spec.md` exists at cwd root
- `gse-one/gse_generate.py` exists

If missing, abort with:

> This command audits a **GSE-One methodology repository** (upstream or your fork of it). It doesn't apply to your project here.
>
> To inspect **your project**, try instead:
> - `/gse:status` — current project state
> - `/gse:health` — 8-dimension quantified health
> - `/gse:review` — code/design/tests quality review
> - `/gse:assess` — gap analysis against your project goals
> - `/gse:compound` — end-of-sprint capitalization (Axes 1–3)
> - `/gse:collect` — artefact inventory
>
> To audit gensem (or your fork), run `/gse-audit` from the root of that repo.

### Phase 1 — Deterministic engine

Invoke the Python engine for the 12 deterministic categories:

```
python3 gse-one/audit.py --format json
```

The engine returns a JSON report with findings classified by category and severity (error / warning / info). Parse the output, retain for unified rendering in Phase 4.

If `--deterministic-only` is passed: skip Phases 2–3, jump straight to Phase 4.

### Phase 2 — LLM reasoning (within-layer, 3 passes)

Adopt the `methodology-auditor` role (see its Core Principles, especially "evidence or silence"). Apply systematic review for each layer, producing Findings for any issue detected.

**2a. Within spec** — Read `gse-one-spec.md` (or the relevant sections if scope-limited by `--layer`). Check:

- **Terminology stability** — Are "activity", "command", "skill", "tier", "gate" used with consistent meanings throughout? Any synonym drift?
- **Principles consistency** — Are the 16 principles (P1–P16) applied consistently across their citations? Does any example contradict its own principle?
- **Modes distinctness** — Do Micro / Lightweight / Full remain logically distinct? No overlap or contradiction?
- **Gates strictness** — Are Gate decisions defined at a consistent severity level? Any weak-Gate that should be Hard, or vice versa?

**2b. Within design** — Read `gse-one-implementation-design.md`. Check:

- **Pattern consistency across §5.x** — Do the design subsections follow a uniform structure? Any §5.x with much more or less depth than peers?
- **Rationale documented** — Does each design decision cite its rationale? Any undocumented "because we chose X"?
- **Self-consistency** — Do the design decisions contradict each other anywhere?

**2c. Within implementation** — Read a sample of `src/activities/*.md` + `src/agents/*.md` + `plugin/tools/*.py`. Check:

- **Skill structure uniform** — Do skills follow the pattern (Options → Prerequisites → Workflow → Phases)? Notable outliers?
- **Error message tone** — Error messages formatted consistently across skills and tools?
- **`@gse-tool` headers** — All tools declare the header? (deterministic engine already catches absence; reasoning looks at semantic quality)
- **Docstring quality** — Are Python functions documented in a way that helps a forker understand the intent?

Each sub-phase (2a, 2b, 2c) produces `Finding` records tagged by dimension.

### Phase 3 — LLM reasoning (cross-layer, 3 passes)

**3a. Spec ↔ design** — Read both. Check:

- Every spec principle has a design implementation or explicit delegation
- Every design decision traces to a spec requirement (no orphan design decisions)
- No design decision contradicts a spec principle

**3b. Design ↔ implementation** — Read design §5.x and relevant implementation files. Check:

- The code matches what the design says it does (no silent deviation)
- No implementation pattern exists that is not described in design
- All design decisions are actually implemented (no "we said we'd do X, but code does Y")

**3c. Spec ↔ implementation** — Read spec and implementation constants. Check:

- Every `/gse:X` mentioned in spec exists in `ACTIVITY_NAMES`
- Every agent referenced in spec exists in `SPECIALIZED_AGENTS` (or is `gse-orchestrator`)
- Numeric counts (N commands, N agents, N modes) match reality

### Phase 4 — Unified report

Merge Phase 1 findings (deterministic) with Phase 2–3 findings (semantic). Format as:

```
# GSE-One Methodology Audit

**Repository:** /path/to/gensem
**VERSION:** X.Y.Z
**Timestamp:** YYYY-MM-DDThh:mm:ssZ
**Scope:** full (or --deterministic-only / --layer / --cross-only)

## Summary
- 🔴 Errors: N
- 🟡 Warnings: N
- 🔵 Info: N

## Errors (blocking)
[list]

## Warnings (should fix)
[list]

## Info (observations + passed checks)
[list]

## Conclusion
❌ Errors found — fix before release.
🟡 Warnings — review and address.
✅ Pass — all checks clean.
```

Each finding includes:
- Code (E01, W01, I01)
- Category (e.g. "within-spec", "spec↔impl", or Python category like "version")
- Title
- Detail (text excerpt or data)
- Location (`file:line` or file name)
- Fix hint

If `--format json`: emit structured JSON instead of markdown (for CI pipelines).

If `--fail-on error` and `report.errors() > 0`: exit with non-zero code indication for CI.

## Invocation examples

```
/gse-audit                                  # full audit (fullest depth)
/gse-audit --deterministic-only             # fast Python-only (~5s)
/gse-audit --cross-only                     # focus on cross-layer alignment
/gse-audit --layer impl                     # LLM review of implementation only
/gse-audit --format json --fail-on error    # CI mode
```

## Notes for forkers

When you fork gensem, `.claude/commands/gse-audit.md` and `.claude/agents/methodology-auditor.md` are inherited via `git clone` — no additional install step. Your Claude Code session opened at the root of your fork will automatically have `/gse-audit` available.

Use it regularly:
- Before committing significant changes (catches drift early)
- Before submitting a PR upstream (demonstrates coherence)
- After an upstream merge (validates your changes still align)
