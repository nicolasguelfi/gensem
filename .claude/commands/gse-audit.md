---
description: "Audit the GSE-One methodology repository for coherence (Categories A-D) and strategic quality (Category E). Orchestrates the Python deterministic engine (audit.py) + 21 parallel LLM sub-agents defined in .claude/audit-jobs.json. Invoked from the root of gensem or a fork."
---

# /gse-audit — Methodology audit (coherence + strategic critique)

Arguments: $ARGUMENTS

## Scope

This command audits a **GSE-One methodology repository** (upstream or a fork). It is **not** for auditing user projects — for that, use `/gse:status`, `/gse:health`, `/gse:review`, `/gse:assess`, `/gse:compound`, `/gse:collect`.

The audit covers **21 jobs** in 5 categories, listed in `.claude/audit-jobs.json`. All jobs run in parallel.

| Category | Purpose | # jobs | Non-directional | Directional |
|:-:|---|:-:|:-:|:-:|
| A | File quality (single file, intra-file) | 2 | ✓ | — |
| B | Intra-layer group (uniformity within a level) | 5 | ✓ | — |
| C | Layer pair (spec ↔ design) | 1 | — | ✓ |
| D | Horizontal cluster (impl + design + spec) | 9 | — | ✓ |
| E | Qualitative critique (strategic) | 4 | — | ✓ |

## Options

| Flag | Description |
|------|-------------|
| (no args) | Full audit: all 21 jobs in parallel + Python deterministic engine |
| `--deterministic-only` | Skip LLM jobs, run Python engine only. Fast. |
| `--job <id>` | Run only a specific job by id (e.g. `deploy-cluster`) |
| `--category <A\|B\|C\|D\|E>` | Run only jobs in a specific category |
| `--coherence-only` | Skip Category E (no strategic recommendations) |
| `--strategic-only` | Run only Category E (4 qualitative critique jobs) |
| `--format <json\|md>` | Output format (default: md) |
| `--fail-on <error\|warning>` | Exit non-zero if findings at this severity or higher |
| `--no-save` | Do not save the report to `_LOCAL/audits/` |
| `--save-to <path>` | Explicit output file path (overrides default) |
| `--help` | Show this usage guide |

## Required readings

1. `.claude/agents/methodology-auditor.md` — **adopt this role** for every sub-agent spawn
2. `.claude/audit-jobs.json` — the catalog of 21 jobs with exact file lists and checks per job
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

This gives the list of 21 jobs with their ids, categories, types, and file counts. Select which jobs to run based on the flags:

- Default (no flag): all 21 jobs
- `--coherence-only`: Categories A, B, C, D (17 jobs)
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

AUDIT JOB: <job.id>           # REQUIRED: include this exact id in every Finding
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
Every Finding you return MUST include these fields:
  - job_id: "<job.id>"   # exactly the job id above — required for traceability
  - category: "<job.category>" (A | B | C | D | E)
  - severity: "error" | "warning" | "info" | "recommendation"
  - title: short one-line summary
  - location: file:line or file path
  - file: relative file path (for cluster mapping)
  - detail: evidence (text excerpt, counts, etc.)
  - fix_hint: concrete suggestion when applicable
  - direction: "downward" | "upward" | "none"   # only for bidirectional jobs
  - impact: "high" | "medium" | "low"           # only for severity=recommendation

Constraints:
- Do not over-report: apply Principle 3 (Severity discipline).
- Cite evidence (Principle 1) — no unverifiable claims.
- For refinement=bidirectional: actively look for cases where the
  lower-level artifact is BETTER than the upper-level reference
  (upward direction). Propose spec or design updates in such cases.
- For type=qualitative_critique (Category E): you are empowered to
  offer strategic recommendations (Principle 7). Use severity=recommendation,
  include impact level, justify rationale.

Return a YAML or JSON list of Finding objects, no preamble.
Begin the audit now. Read only the FILES TO AUDIT (do not expand scope).
```

#### Expected concurrency

- 21 sub-agents running in parallel
- Each reads only its assigned files (no duplication of context)
- Total latency ≈ latency of the slowest sub-agent (not sum of all)
- If Claude Code limits concurrent sub-agent count, the skill may need to spawn in batches — but this is infrastructure-level, not skill concern

### Phase 4 — Aggregation, tracking, and dedup

After all sub-agents return:

1. **Track completion per job.** For each of the N jobs you spawned, record whether it returned successfully. Example tally:
   - 21/21 jobs completed successfully ✓
   - 20/21 jobs completed, 1 skipped (`<job-id>`, reason: timeout/error) ⚠
   - 16/21 jobs completed, 5 errored ⚠

   This information MUST appear in the Summary section of the final report.

2. **Collect** all findings from sub-agents into a single list. Every finding must carry its `job_id` (see the sub-agent prompt requirements).

3. **Augment** with findings from Phase 1 (Python deterministic engine — `job_id="python-engine"`).

4. **Deduplicate** findings where `(category, title, file)` are identical. Keep the most detailed copy. When two jobs report the same issue from different angles (e.g., `governance-cluster` and `spec-design-coherence` both catch a count drift), merge their detail and retain both job_ids in the finding's `job_ids` list.

5. **Classify** by severity: error, warning, info, recommendation.

6. **Group coherence findings into thematic clusters.** When multiple findings share a common theme (same drift type across files), group them and present as a cluster heading with sub-findings. Example clusters observed in past runs: "Count inconsistencies", "Schema field drifts", "Severity scale drift", "Sprint lifecycle drift", "Structural defects". This grouping is a QUALITY requirement — not optional. It dramatically improves the report's actionability.

7. **Render** the unified report (markdown by default) per the template in Phase 5.

### Phase 5 — Unified report rendering

The report must follow this structure. A table-of-contents is **required** whenever the report exceeds 100 lines (typically always in a full audit).

```markdown
# GSE-One Methodology Audit

**Repository:** /path/to/gensem
**VERSION:** X.Y.Z
**Timestamp:** YYYY-MM-DDThh:mm:ssZ
**Jobs run:** N/21 completed (A=2, B=5, C=1, D=9, E=4)
**Scope:** full (or --coherence-only / --strategic-only / --job / --category)

## Table of Contents
- Summary
- Part 1 — Coherence findings (Categories A-D)
  - Cluster 1: <theme name>
  - Cluster 2: <theme name>
  - ...
  - Warnings
  - Info
- Part 2 — Strategic recommendations (Category E)
  - methodology-design-critique
  - ai-era-adequacy-critique
  - user-value-critique
  - robustness-and-recovery-critique
- Conclusion
  - Fix priority recommendations
  - Files to consult first

## Summary

| Severity | Count | Source |
|---|:-:|---|
| 🔴 Errors | N | A=n, B=n, C=n, D=n, Python=n |
| 🟡 Warnings | N | A=n, B=n, C=n, D=n, Python=n |
| 🔵 Info | N | passes + observations |
| 💡 Recommendations | N | Category E (strategic) |

**Jobs run:** X/21 completed. [If any skipped or errored, list them.]

---

## Part 1 — Coherence findings (Categories A-D)

### 🔴 Errors (grouped into clusters by theme)

**Cluster 1 — <Theme name, e.g., "Count inconsistencies across layers">**
- <finding with file:line citations>
- <finding ...>

**Cluster 2 — <Theme name>**
- ...

### 🟡 Warnings
[Grouped by category or theme, with file citations and fix hints]

### 🔵 Info
[Passes and neutral observations]

---

## Part 2 — Strategic recommendations (Category E)

### 💡 methodology-design-critique

| # | Recommendation | Impact | Direction |
|:-:|---|:-:|:-:|
| 1 | ... | high/medium/low | upward/downward |

### 💡 ai-era-adequacy-critique
[Same table format]

### 💡 user-value-critique
[Same table format]

### 💡 robustness-and-recovery-critique
[Same table format]

---

## Conclusion

**Overall verdict:**
- ❌ Errors found — fix before next release
- 🟡 Warnings — review and address
- 💡 Strategic recommendations — consider for future evolution
- ✅ Pass — all checks clean

**Fix priority recommendations (maintainer view):**
1. <highest-priority fix with scope across files>
2. <next priority>
3. ...

**Files to consult first when fixing:** <list of 3-5 files that appear in the most findings, sorted by finding count>

**Strategic recommendations for future evolution:** consider the high-impact Category E items around <theme 1> and <theme 2> as next-quarter themes.
```

### Phase 5 — Quality requirements (preserve LLM-natural behaviors observed in real runs)

Past audit runs have shown that a well-executed audit naturally produces these qualities. **Preserve them** — do not regress:

1. **Thematic clustering of errors/warnings.** Group related findings (same drift type across multiple files) under a shared "Cluster N — <theme>" heading. Do not list 20 individual findings when 4 clusters of 5 tell the same story better.

2. **Precise citations.** Every finding cites file:line (e.g., `[spec:309 vs 431]`, `[gse_generate.py:13,22,31,...]`). No vague "somewhere in spec".

3. **Strategic recommendations as tables** with Impact and Direction columns — already prescribed above.

4. **Fix priority list** in the conclusion — numbered items showing what to tackle first, often cross-file.

5. **Files-to-consult-first** — derivable from counting file mentions; surface the top 3-5.

6. **Action-oriented phrasing.** "Fix before next release", "Sweep all 5 activities", "Rename X→Y across 3 templates". Imperative, scoped, measurable.

7. **Separation of immediate fixes (Part 1) vs future evolution (Part 2).** Keep the "this sprint" vs "next quarter" horizon distinct — do not mix strategic recommendations into the fix priority list.

If `--format json`: emit structured JSON with the same two-section structure (`coherence_findings` and `strategic_recommendations` arrays).

If `--fail-on error` and errors > 0: exit with non-zero indication.
If `--fail-on warning` and (errors > 0 or warnings > 0): exit with non-zero.
Recommendations NEVER trigger exit codes (they are proposals, not defects).

### Phase 6 — Save the augmented report (MANDATORY)

Unless `--no-save` was passed, you **MUST** persist the final rendered report. This is not optional — the audit trail is the primary value of running the audit.

**Exact procedure** (perform in this order):

1. **Create the directory** using the Bash tool:
   ```
   mkdir -p _LOCAL/audits/
   ```

2. **Compute the filename** using current UTC date+time + VERSION:
   - Pattern: `audit-YYYY-MM-DD-HHMMSS-vX.Y.Z.md`
   - Example: `audit-2026-04-21-074512-v0.47.0.md`
   - Read VERSION from the file at repo root to get the version string

3. **Write TWO files** using the Write tool, in the same message:
   - `_LOCAL/audits/audit-YYYY-MM-DD-HHMMSS-vX.Y.Z.md` — timestamped archive (unique per run)
   - `_LOCAL/audits/latest.md` — always overwritten, convenience pointer to most recent

4. **Both files must contain the FULL rendered markdown report** from Phase 5 (summary, TOC, Part 1, Part 2, conclusion — everything).

5. **Verify the save succeeded** using the Bash tool:
   ```
   ls -la _LOCAL/audits/latest.md
   ```

6. **Report to the user** with the exact saved path:
   > Full audit saved to `_LOCAL/audits/audit-YYYY-MM-DD-HHMMSS-vX.Y.Z.md` (and `latest.md`).

If `--save-to <path>` was passed, write to that exact path instead (no `latest.md` copy). Useful for CI exports.

If `--no-save` was passed, skip this entire phase and only output the report to the chat.

**Why mandatory?** The audit trail is the audit's primary value. A run without save leaves no evidence, no diff capability, no comparison across time. An LLM that skips this phase silently wastes the run.

**The `_LOCAL/` directory is gitignored** (via `/_*/` in `.gitignore`), so saved reports never leak into commits. Forkers accumulate audit history in their working tree without polluting their repo.

**Division of work with Python engine:** the Python engine (`audit.py`) saves its own deterministic-only report when invoked standalone. When `/gse-audit` runs the full flow, the skill invokes the engine with `--no-save --format json` internally to skip engine-side saving, then the skill saves the AUGMENTED report (Python findings + LLM findings from the 20 sub-agents) in Phase 6. **No duplicate files.**

## Invocation examples

```
/gse-audit                                  # full: 21 jobs + Python engine
/gse-audit --deterministic-only             # fast Python-only (~5s)
/gse-audit --coherence-only                 # 17 jobs, skip Category E
/gse-audit --strategic-only                 # 4 jobs, critique only
/gse-audit --category D                     # only horizontal clusters (9 jobs)
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
