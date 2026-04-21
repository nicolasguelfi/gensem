---
description: "Audit the GSE-One methodology repository for coherence (Categories A-D) and strategic quality (Category E). Orchestrates the Python deterministic engine (audit.py) + 20 parallel LLM sub-agents defined in .claude/audit-jobs.json. Invoked from the root of gensem or a fork."
---

# /gse-audit — Methodology audit (coherence + strategic critique)

Arguments: $ARGUMENTS

## Scope

This command audits a **GSE-One methodology repository** (upstream or a fork). It is **not** for auditing user projects — for that, use `/gse:status`, `/gse:health`, `/gse:review`, `/gse:assess`, `/gse:compound`, `/gse:collect`.

The audit covers **20 jobs** in 5 categories, listed in `.claude/audit-jobs.json`. All jobs run in parallel.

| Category | Purpose | # jobs | Non-directional | Directional |
|:-:|---|:-:|:-:|:-:|
| A | File quality (single file, intra-file) | 2 | ✓ | — |
| B | Intra-layer group (uniformity within a level) | 5 | ✓ | — |
| C | Layer pair (spec ↔ design) | 1 | — | ✓ |
| D | Horizontal cluster (impl + design + spec) | 8 | — | ✓ |
| E | Qualitative critique (strategic) | 4 | — | ✓ |

## Options

| Flag | Description |
|------|-------------|
| (no args) | Full audit: all 20 jobs in parallel + Python deterministic engine |
| `--deterministic-only` | Skip LLM jobs, run Python engine only. Fast. |
| `--job <id>` | Run only a specific job by id (e.g. `deploy-cluster`) |
| `--category <A\|B\|C\|D\|E>` | Run only jobs in a specific category |
| `--coherence-only` | Skip Category E (no strategic recommendations) |
| `--strategic-only` | Run only Category E (4 qualitative critique jobs) |
| `--format <json\|md>` | Output format (default: md) |
| `--fail-on <error\|warning>` | Exit non-zero if findings at this severity or higher |
| `--help` | Show this usage guide |

## Required readings

1. `.claude/agents/methodology-auditor.md` — **adopt this role** for every sub-agent spawn
2. `.claude/audit-jobs.json` — the catalog of 20 jobs with exact file lists and checks per job
3. Sub-agents load their own files on-demand based on their assigned job specification

## Workflow

### Phase 0 — Context detection

Verify that the current working directory is the root of a GSE-One repository:
- `gse-one-spec.md` exists
- `gse-one/gse_generate.py` exists
- `.claude/audit-jobs.json` exists

If any marker is missing, abort with:

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

### Phase 1 — Deterministic engine (Python)

Unless `--strategic-only` is passed, invoke the Python engine:

```
python3 gse-one/audit.py --format json
```

This returns the 12 deterministic categories (version, file integrity, plugin parity, cross-refs, numeric, links, git, Python quality, template schema, TODOs, test coverage, freshness). Retain the JSON output for Phase 4 aggregation.

If `--deterministic-only` is passed: skip Phase 2-3, jump to Phase 4 rendering.

### Phase 2 — Load the audit catalog

Read `.claude/audit-jobs.json`:

```
python3 gse-one/audit_catalog.py --list
```

This gives the list of 20 jobs with their ids, categories, types, and file counts. Select which jobs to run based on the flags:

- Default (no flag): all 20 jobs
- `--coherence-only`: Categories A, B, C, D (16 jobs)
- `--strategic-only`: Category E (4 jobs)
- `--category X`: only jobs with that category
- `--job <id>`: only the named job

### Phase 3 — Parallel sub-agent spawns (ONE message, N Agent tool calls)

**This is the core parallelism step.** Spawn all selected jobs as parallel sub-agents in a SINGLE message with multiple Agent tool invocations.

For each selected job, construct a dedicated prompt and spawn a sub-agent with:
- `subagent_type=methodology-auditor`
- `description="Audit <job_id>"`
- `prompt=` (constructed per the template below)

#### Sub-agent prompt template

```
You are the methodology-auditor (defined in .claude/agents/methodology-auditor.md — principles 1-7 apply).

AUDIT JOB: <job.id>
CATEGORY: <job.category>
TYPE: <job.type>
REFINEMENT: <job.refinement>

SCOPE
<job.scope>

FILES TO AUDIT
<list of job.files, one per line, resolved to absolute paths>

CHECKS TO APPLY
<numbered list from job.checks>

OUTPUT REQUIREMENTS
- Return a list of Finding records (YAML or JSON), each with:
  job_id, category, severity, title, location, detail, fix_hint,
  direction (for bidirectional jobs), impact (for recommendation findings).
- Do not over-report: apply Principle 3 (Severity discipline).
- Cite evidence (Principle 1) — no unverifiable claims.
- For refinement=bidirectional: actively look for cases where the
  lower-level artifact is BETTER than the upper-level reference
  (upward direction). Propose spec or design updates in such cases.
- For type=qualitative_critique (Category E): you are empowered to
  offer strategic recommendations (Principle 7). Use severity=recommendation,
  include impact level, justify rationale.

Begin the audit now. Read only the FILES TO AUDIT (do not expand scope).
Return findings structured, with no preamble.
```

#### Expected concurrency

- 20 sub-agents running in parallel
- Each reads only its assigned files (no duplication of context)
- Total latency ≈ latency of the slowest sub-agent (not sum of all)
- If Claude Code limits concurrent sub-agent count, the skill may need to spawn in batches — but this is infrastructure-level, not skill concern

### Phase 4 — Aggregation and dedup

After all sub-agents return:

1. **Collect** all findings from sub-agents into a single list
2. **Augment** with findings from Phase 1 (Python deterministic engine)
3. **Deduplicate** findings where (category, title, file) are identical. Keep the most detailed copy.
4. **Classify** by severity: error, warning, info, recommendation
5. **Render** the report (markdown by default)

### Phase 5 — Unified report with 2 sections

The report has **two distinct sections** reflecting the category A-D vs E distinction:

```markdown
# GSE-One Methodology Audit

**Repository:** /path/to/gensem
**VERSION:** X.Y.Z
**Timestamp:** YYYY-MM-DDThh:mm:ssZ
**Jobs run:** 20 (A=2, B=5, C=1, D=8, E=4)
**Scope:** full (or --coherence-only / --strategic-only / --job / --category)

## Summary
- 🔴 Errors: N
- 🟡 Warnings: N
- 🔵 Info: N
- 💡 Recommendations: N (strategic, from Category E)

---

## Part 1 — Coherence findings (Categories A-D)

### 🔴 Errors
[list]

### 🟡 Warnings
[list]

### 🔵 Info
[list]

---

## Part 2 — Strategic recommendations (Category E)

### 💡 methodology-design-critique
[recommendations with impact levels]

### 💡 ai-era-adequacy-critique
[...]

### 💡 user-value-critique
[...]

### 💡 robustness-and-recovery-critique
[...]

---

## Conclusion
❌ Errors found — fix before release.
🟡 Warnings — review and address.
💡 Strategic recommendations — consider for future evolution.
✅ Pass — all checks clean.
```

If `--format json`: emit structured JSON with the same two-section structure (`coherence_findings` and `strategic_recommendations` arrays).

If `--fail-on error` and errors > 0: exit with non-zero indication.
If `--fail-on warning` and (errors > 0 or warnings > 0): exit with non-zero.
Recommendations NEVER trigger exit codes (they are proposals, not defects).

## Invocation examples

```
/gse-audit                                  # full: 20 jobs + Python engine
/gse-audit --deterministic-only             # fast Python-only (~5s)
/gse-audit --coherence-only                 # 16 jobs, skip Category E
/gse-audit --strategic-only                 # 4 jobs, critique only
/gse-audit --category D                     # only horizontal clusters (8 jobs)
/gse-audit --job deploy-cluster             # single cluster audit
/gse-audit --format json --fail-on error    # CI mode
```

## For forkers

When you fork gensem, `.claude/commands/gse-audit.md`, `.claude/agents/methodology-auditor.md`, and `.claude/audit-jobs.json` are inherited via `git clone` — no additional install. Your Claude Code session opened at the fork root will have `/gse-audit` available immediately.

Use it regularly:
- Before committing significant changes (catches drift early)
- After forking upstream additions (validates your deviations are intentional)
- Before submitting a PR upstream (demonstrates coherence + may reveal strategic opportunities)

## Customizing the catalog

To add a job (e.g., new cluster for a new subsystem you've added to your fork):
1. Edit `.claude/audit-jobs.json`, add a new entry following the schema
2. Validate: `python3 gse-one/audit_catalog.py --validate`
3. The next `/gse-audit` run will pick it up automatically

Schema for each job:
- `id` — stable identifier (kebab-case)
- `category` — A | B | C | D | E
- `type` — file_quality | intra_layer_group | layer_pair | horizontal_cluster | qualitative_critique
- `refinement` — none | downward | bidirectional
- `files` — explicit paths (globs like `src/activities/*.md` supported)
- `scope` — one-sentence description
- `checks` — numbered list of criteria to apply
