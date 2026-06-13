---
description: "Audit the GSE-One methodology repository for coherence (Categories A-D), strategic quality (Category E), and distribution hygiene (Category F). Orchestrates the Python deterministic engine (audit.py, including the 5 Category F distribution jobs) + 23 parallel LLM sub-agents — 28 jobs total, defined in .claude/audit-jobs.json. Invoked from the root of gensem or a fork."
---

# /gse-audit — Methodology audit (coherence + strategic critique)

Arguments: $ARGUMENTS

## Scope

This command audits a **GSE-One methodology repository** (upstream or a fork). It is **not** for auditing user projects — for that, use `/gse:status`, `/gse:health`, `/gse:review`, `/gse:assess`, `/gse:compound`, `/gse:collect`.

The audit covers **28 jobs** in 6 categories, listed in `.claude/audit-jobs.json` — 23 LLM sub-agent jobs (A-E, run in parallel) + 5 deterministic F-jobs run by `audit.py`. The category table below is the human-readable summary; **derive the expected job count at runtime from the catalog output (Phase 2), never from this document** — counts here are illustrative and may lag the catalog.

| Category | Purpose | # jobs | Non-directional | Directional |
|:-:|---|:-:|:-:|:-:|
| A | File quality (single file, intra-file) | 2 | ✓ | — |
| B | Intra-layer group (uniformity within a level) | 5 | ✓ | — |
| C | Layer pair (spec ↔ design) | 1 | — | ✓ |
| D | Horizontal cluster (impl + design + spec) | 11 | — | ✓ |
| E | Qualitative critique (strategic) | 4 | — | ✓ |
| F | Distribution hygiene (plugin-as-product invariants) | 5 | ✓ | — |

> **Note:** the 5 Category F jobs are executed deterministically by `audit.py` in Phase 1 — they are NEVER spawned as LLM sub-agents.

**Category F — Distribution hygiene** treats `gse-one/plugin/` as a finished product shipped to end users. It applies stricter invariants than the source tree: English-monolingual (except marked multilingual zones), no secret/credential leaks, no maintainer-personal paths/identities, no debug residue in Python/TypeScript code, and all runtime path references (`$(cat ~/.gse-one)/X`) must resolve against subpaths distributed by `install.py`. All 5 F-jobs run deterministically via `audit.py` (no LLM sub-agent needed) and are fast enough (<5s total) for CI use.

## Options

| Flag | Description |
|------|-------------|
| (no args) | Full audit: all 28 jobs — 23 LLM sub-agents in parallel + 5 F-jobs via the Python deterministic engine |
| `--deterministic-only` | Skip LLM jobs, run Python engine only. Fast (also covers all 5 Category F jobs, which are deterministic). |
| `--job <id>` | Run only a specific job by id (e.g. `deploy-cluster`, `plugin-language-hygiene`) |
| `--category <A\|B\|C\|D\|E\|F>` | Run only jobs in a specific category |
| `--coherence-only` | Skip Category E (no strategic recommendations) — keeps A, B, C, D, F |
| `--strategic-only` | Run only Category E (4 qualitative critique jobs) |
| `--distribution-only` | Run only Category F (5 distribution-hygiene jobs via `audit.py`) |
| `--format <json\|md>` | Output format (default: md) |
| `--fail-on <error\|warning>` | Exit non-zero if findings at this severity or higher |
| `--no-save` | Engine stdout only — do not write the registry (quick check) |
| `--save-to <path>` | Explicit output file path (overrides default) |
| `--help` | Show this usage guide |

## Required readings

1. `.claude/agents/methodology-auditor.md` — **adopt this role** for every sub-agent spawn
2. `.claude/audit-jobs.json` — the catalog of 28 jobs with exact file lists and checks per job
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

Unless `--strategic-only` is passed, **seed the canonical registry** with the engine findings (this also auto-archives any previous `_LOCAL/audit/audit.json` to `_LOCAL/audit/archive/`):

```
python3 gse-one/audit.py --emit-registry
```

This writes `_LOCAL/audit/audit.json` (`schema_version` + engine findings, each with a stable `AUD-<hash>` id, `verdict:"detected"`, `status:"open"`). The skill folds the LLM findings into this **same** registry in Phase 4 via `audit.py --merge`. The registry is the SINGLE output artifact (see "Audit output contract" in CLAUDE.md) — do NOT save separate `audit-<ts>.md` / `latest.md` / `verify-*.md` files. For a quick stdout-only check (e.g. `--deterministic-only`), `python3 gse-one/audit.py --no-save --format json` still works.

This returns the 17 deterministic categories — 12 coherence categories (version, file integrity, plugin parity, cross-refs, numeric, links, git, Python quality, template schema, TODOs, test coverage, freshness) + the 5 Category F distribution-hygiene categories (`plugin_language`, `plugin_secrets`, `plugin_personal`, `plugin_debug`, `plugin_runtime_paths`), which fully cover the catalog's 5 F-jobs. Retain the JSON output for Phase 4 aggregation.

If `--deterministic-only` is passed: skip Phase 2-3, jump to Phase 4 — Aggregation, then Phase 5 — Unified report rendering.

**Engine-side inspection flags** (implemented by `audit.py` / `audit_catalog.py`, useful beyond the skill flow): `audit.py --cluster <job-id>` filters deterministic findings to one catalog job's file set (handy for the Phase 3.5 verification pass); `audit.py --list-clusters` and `audit_catalog.py --list` enumerate the catalog; `audit_catalog.py --show <job-id>` prints one job's full spec.

### Phase 2 — Load the audit catalog

Read `.claude/audit-jobs.json`:

```
python3 gse-one/audit_catalog.py --list
```

This gives the list of 28 jobs with their ids, categories, types, and file counts. **Derive the expected job count from this catalog output, never from this document.** Select which jobs to spawn based on the flags:

- Default (no flag): all jobs — Categories A-E as LLM sub-agent spawns; the 5 Category F jobs are already covered by the Phase 1 engine run and are NEVER spawned as sub-agents
- `--coherence-only`: Categories A, B, C, D as LLM spawns; Category F remains covered by the Phase 1 engine — only Category E is skipped (matches the Options table)
- `--strategic-only`: Category E (4 jobs)
- `--category X`: only jobs with that category. `--category F` or `--distribution-only` routes to the engine, no sub-agents: invoke `python3 gse-one/audit.py --category <engine-name> --format json` per the mapping below
- `--job <id>`: only the named job. If the id is a Category F job, route to the engine likewise

F-job id → engine category mapping: `plugin-language-hygiene`→`plugin_language`, `plugin-secret-leak-hygiene`→`plugin_secrets`, `plugin-personal-leak-hygiene`→`plugin_personal`, `plugin-debug-residue-hygiene`→`plugin_debug`, `plugin-runtime-path-integrity`→`plugin_runtime_paths`. Note: the engine's `--category` flag takes these engine names, not catalog letters.

### Phase 3 — Parallel sub-agent spawns (ONE message, N Agent tool calls)

**This is the core parallelism step.** Spawn all selected jobs as parallel sub-agents in a SINGLE message with multiple Agent tool invocations.

For each selected job, construct a dedicated prompt and spawn a sub-agent with:
- `subagent_type=methodology-auditor`
- `description="Audit <job_id>"`
- `prompt=` (constructed per the template below)

**Path resolution:** the FILES TO AUDIT list is resolved by the orchestrator (you) to absolute paths BEFORE substitution into the template — expand each glob from the catalog against the repo root and paste the resolved absolute paths verbatim. Sub-agents must use absolute paths for all reads.

#### Sub-agent prompt template

```
You are the methodology-auditor (defined in .claude/agents/methodology-auditor.md — principles apply, notably 1 evidence, 8 verify-before-report, 9 anti-rigidity, 11 product-vs-source dualism).

AUDIT JOB: <job.id>           # REQUIRED: include this exact id in every Finding
CATEGORY: <job.category>
TYPE: <job.type>
REFINEMENT: <job.refinement>
REPO ROOT: <absolute path to the repo root>

SCOPE
<job.scope>

FILES TO AUDIT
<list of job.files, one per line, resolved by the orchestrator to absolute paths>

CHECKS TO APPLY
<numbered list from job.checks>

OUTPUT REQUIREMENTS
Every Finding you return MUST include these fields:
  - job_id: "<job.id>"   # exactly the job id above — required for traceability
  - category: "<job.category>" (A | B | C | D | E | F)   # F only appears in verification passes — F jobs are not spawned in initial audits
  - severity: "error" | "warning" | "info" | "recommendation"
  - title: short one-line summary
  - location: file:line or file path
  - file: relative file path (for cluster mapping)
  - detail: evidence (text excerpt, counts, etc.)
  - fix_hint: concrete suggestion when applicable
  - direction: "downward" | "upward" | "retraction" | "none"   # only for directional jobs
  - impact: "high" | "medium" | "low"           # only for severity=recommendation

Constraints:
- Do not over-report: apply Principle 3 (Severity discipline).
- Cite evidence (Principle 1) — no unverifiable claims.
- Before emitting any finding, apply Principle 8 (verify-before-report):
  re-open the cited line; for absence claims run an explicit Grep over
  the whole file. Discard findings that fail verification.
- Apply Principle 9 (anti-rigidity): if a divergence carries semantic
  information or is a documented convention (CLAUDE.md Meta-1/Meta-2),
  classify it "info" with a document-the-convention hint, not error/warning.
- For refinement=bidirectional: actively look for cases where the
  lower-level artifact is BETTER than the upper-level reference
  (upward direction). Propose spec or design updates in such cases.
  Also check for retraction cases (Principle 6): content dead/orphan on
  BOTH sides should be flagged for deletion (direction: retraction),
  not alignment.
- For type=qualitative_critique (Category E): you are empowered to
  offer strategic recommendations (Principle 7). Use severity=recommendation,
  include impact level, justify rationale.

Return EXACTLY ONE fenced ```json block containing a single JSON array
of Finding objects — no preamble, no epilogue, no other format.
Begin the audit now. Read only the FILES TO AUDIT (do not expand scope).
```

#### Expected concurrency

- 23 LLM sub-agents running in parallel (Categories A-E; derive the exact number from the Phase 2 catalog output)
- Each reads only its assigned files (no duplication of context)
- Total latency ≈ latency of the slowest sub-agent (not sum of all)
- If Claude Code limits concurrent sub-agent count, the skill may need to spawn in batches — but this is infrastructure-level, not skill concern

#### Failure recovery (retry-once)

If a sub-agent errors, times out, or returns unparseable output, re-spawn that ONE job once with the same prompt before declaring it failed. Jobs still failing after the retry are recorded as skipped in the Phase 4 completion tally — never silently dropped.

### Phase 3.5 — Anti-false-positive verification pass (post-audit, on-demand)

This phase is NOT part of the initial audit run — it is invoked by the maintainer **after** Phase 5 rendering, when the maintainer decides to address a batch of findings. It is documented here for discoverability because the post-audit fix workflow (CLAUDE.md > Post-audit fix workflow) expects it.

**When to use it.** Before applying any fix from the audit report, spawn a verification pass to separate real findings from LLM fabrication. Evidence from the 2026-04-22 post-audit session: on the first batch of 12 warning clusters, 4 turned out to be false positives (33%). Skipping verification applies fabricated fixes to the corpus.

**How to spawn it.** For each cluster the maintainer wants to address, spawn ONE methodology-auditor sub-agent with a focused verification prompt:

```
You are the methodology-auditor (principles 1, 8, 9, 10, 11 apply — evidence, verify-before-report, anti-rigidity, structured verdict, product-vs-source dualism).

MISSION: verify cluster <cluster-id> findings from audit <report-path>.
For each finding, produce a structured verdict per Principle 10.

FINDINGS TO VERIFY:
- <finding 1 with location + claim + proposed fix>
- <finding 2 ...>
- ...

For each finding, output (YAML):
  finding_id: <id or brief handle>
  verdict: CONFIRMED | FALSE_POSITIVE | NEEDS_REFINEMENT | SCOPE_CHANGE
  verdict_rationale: "<short explanation>"
  current_state: "<evidence as file:line excerpts>"
  proposed_fix: "<confirmed, adjusted, or 'no action — false positive'>"
  anti_rigidity_check: "<is the divergence deliberate? is the fix forcing uniformity?>"

Return YAML list, no preamble. Cite file:line for every claim.
```

**Parallelism rules.** Clusters are typically independent (each touches a distinct subset of files). Spawn all verification sub-agents in a SINGLE message with multiple Agent tool invocations — same pattern as Phase 3. The user is notified as verdicts come in asynchronously.

**Aggregation.** After all verification sub-agents return, consolidate into three groups:

1. **CONFIRMED** findings — present to the user as an actionable batch with exact file:line changes.
2. **FALSE_POSITIVE** findings — document each with root cause; if the detector can be fixed at source (e.g., `audit.py` regex, `.claude/audit-jobs.json` check wording), add a work item for the next audit engine refresh.
3. **NEEDS_REFINEMENT** findings — present the adjusted fix proposal alongside the original for user validation.
4. **SCOPE_CHANGE** findings — reclassify and note the new scope (defer to release X, bundle with contract change Y).

**Persist verdicts INTO the registry (not a side file).** Write the verdicts to a JSON file (e.g. `/tmp/gse-verdicts.json`: a list of `{finding_id | finding_title, verdict, verdict_rationale, current_state, proposed_fix}`) and apply them in place:
```
python3 gse-one/audit.py --set-verdicts /tmp/gse-verdicts.json
```
This updates each matched finding's `verdict`/`status` in `_LOCAL/audit/audit.json` (FALSE_POSITIVE → `wontfix` + a `detector_issues[]` entry; SCOPE_CHANGE → `deferred`), sets `meta.verify_run_at`, and recomputes the summary. **Do NOT write a `verify-*.md` file** — the registry is the single source of truth.

**User validation.** Present the consolidated plan as a single structured message with the 4 groups clearly separated. Use Communication style Rule 2 (single-default question) for the final "ok to apply all CONFIRMED + NEEDS_REFINEMENT (with adjustments), skip FALSE_POSITIVE, defer SCOPE_CHANGE". Do NOT apply per-finding — the verification phase is what earns the bulk-validation trust.

**False-positive documentation.** Once fixes are applied and committed, the CHANGELOG of the resolving release MUST document each FALSE_POSITIVE with:
- What the audit claimed
- What was actually true
- Root cause in the detector (if identified)
- Whether the detector was fixed at source in the same release

This turns the FP log into a learning asset for detector improvement. Three of the five FP detected in v0.51.0 → v0.55.0 were eliminated at source in `audit.py` v0.54.0 (partitive detection, CHANGELOG historical filter, indent-tolerant perspective guideline).

### Phase 4 — Aggregation, tracking, and dedup

After all sub-agents return:

1. **Track completion per job.** For each of the N LLM jobs you spawned (after retry-once, see Phase 3), record whether it returned successfully. Example tally (the denominator is the spawned-job count derived in Phase 2):
   - 23/23 LLM jobs completed successfully ✓
   - 22/23 LLM jobs completed, 1 skipped (`<job-id>`, reason: timeout/error after retry) ⚠
   - 18/23 LLM jobs completed, 5 errored ⚠

   This information MUST appear in the Summary section of the final report.

2. **Collect** all findings from sub-agents into a single list. Every finding must carry its `job_id` (see the sub-agent prompt requirements).

3. **Augment** with findings from Phase 1 (Python deterministic engine — `job_id="python-engine"`, which includes the 5 Category F jobs).

4. **Deduplicate** same-issue findings. Exact `(category, title, file)` equality almost never fires across independent LLM outputs — instead, treat two findings as duplicates when they cite the **same file AND the same underlying defect** (same drifting value, same broken reference, same missing element), regardless of title wording; judge this during the thematic clustering of step 6. Keep the most detailed copy. When two jobs report the same issue from different angles (e.g., `governance-cluster` and `spec-design-coherence` both catch a count drift), merge their detail and retain both job_ids in the finding's `job_ids` list.

5. **Classify** by severity: error, warning, info, recommendation.

6. **Group coherence findings into thematic clusters.** When multiple findings share a common theme (same drift type across files), group them and present as a cluster heading with sub-findings. Example clusters observed in past runs: "Count inconsistencies", "Schema field drifts", "Severity scale drift", "Sprint lifecycle drift", "Structural defects". This grouping is a QUALITY requirement — not optional. It dramatically improves the report's actionability.

7. **Regression diff (when history exists).** The previous registry was just auto-archived to `_LOCAL/audit/archive/` by `--emit-registry`. Compare the new registry's finding ids (`AUD-<hash>`, stable across runs) against the newest archived `audit-*.json`: which are new, resolved, persisting. Add a short "Since last audit" line to the Summary (e.g., "+3 new, -7 resolved, 12 persisting vs <archived ts>").

8. **Render** the unified report (markdown by default) per the template in Phase 5.

### Phase 5 — Rendering (on demand, from the registry)

Markdown is a **throwaway view rendered on demand from the registry**, never persisted in-repo. Render with `python3 gse-one/audit.py --render` (default: `/tmp/gse-audit-<ts>.md`; `--out PATH` to target a path; or render to chat). The renderer reproduces the structure below from `_LOCAL/audit/audit.json`, so it always reflects current verdicts and fix status. A table-of-contents is **required** whenever the report exceeds 100 lines.

```markdown
# GSE-One Methodology Audit

**Repository:** /path/to/gensem
**VERSION:** X.Y.Z
**Timestamp:** YYYY-MM-DDThh:mm:ssZ
**Model:** <model id that ran the LLM jobs>
**Jobs run:** N/23 LLM jobs completed (A=2, B=5, C=1, D=11, E=4) + 5/5 F-jobs via audit.py
**Scope:** full (or --coherence-only / --strategic-only / --job / --category)

## Table of Contents
- Summary
- Part 1 — Coherence findings (Categories A-D)
  - Cluster 1: <theme name>
  - Cluster 2: <theme name>
  - ...
  - Warnings
  - Info
  - Distribution hygiene (Category F)
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
| 🔴 Errors | N | A=n, B=n, C=n, D=n, F=n, Python=n |
| 🟡 Warnings | N | A=n, B=n, C=n, D=n, F=n, Python=n |
| 🔵 Info | N | passes + observations |
| 💡 Recommendations | N | Category E (strategic) |

**Jobs run:** X/23 LLM jobs completed + 5/5 F-jobs via audit.py. [If any skipped or errored after retry, list them.]
**Since last audit:** [+N new, -N resolved, N persisting vs <previous report> — omit when no previous run exists]

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

### Distribution hygiene (Category F)
[Findings from the 5 deterministic F-jobs run by audit.py in Phase 1 — language, secrets, personal leaks, debug residue, runtime paths. When all pass, a single "5/5 F-jobs clean" line suffices.]

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

#### Quality requirements (preserve LLM-natural behaviors observed in real runs)

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

### Phase 6 — Persist the registry (MANDATORY)

The audit's output is the **single canonical registry** `_LOCAL/audit/audit.json` — NOT a markdown report. By the end of a full run it must contain the engine findings (seeded in Phase 1) **plus** the LLM findings, recommendations, and cluster grouping. Markdown is never persisted in-repo (it is a `/tmp` render, Phase 5).

**Exact procedure:**

1. **The engine findings are already in the registry** (Phase 1 `--emit-registry` wrote `_LOCAL/audit/audit.json` and auto-archived the previous one to `_LOCAL/audit/archive/`).

2. **Fold in the LLM findings + recommendations + clusters.** Write a JSON additions file (e.g. `/tmp/gse-merge.json`) with the shape `{ "findings": [...], "recommendations": [...], "clusters": [{id, theme, finding_ids}], "meta": {model, scope, jobs} }` — the A–D LLM findings go in `findings` (with their `category`/`severity`/`title`/`location`/`detail`/`fix_hint`/`direction`/`cluster`), the Category E items go in `recommendations`. Then:
   ```
   python3 gse-one/audit.py --merge /tmp/gse-merge.json
   ```
   This dedups by stable id, sets cluster grouping, and recomputes the summary in place.

3. **Verify the registry:**
   ```
   python3 -c "import json;r=json.load(open('_LOCAL/audit/audit.json'));print(r['summary'])"
   ```

4. **Report to the user** the single artifact path:
   > Audit registry written to `_LOCAL/audit/audit.json` (N findings, M recommendations). Render a human view with `python3 gse-one/audit.py --render`.

**Markdown on demand only:** to show a human view, `python3 gse-one/audit.py --render` (default: a throwaway `/tmp/gse-audit-<ts>.md`; or `--out PATH`, or render to chat). Never write `audit-<ts>.md` / `latest.md` into the repo.

**Verification (Phase 3.5) writes back into the same registry** via `audit.py --set-verdicts` — it does NOT create a `verify-*.md` file.

**Why a single registry?** It is the agent-consumed source of truth for the subsequent fix session, and it carries each finding's lifecycle (verdict → status → resolution) in place. One file, no divergence, sequentially processable. See "Audit output contract" in CLAUDE.md and `_LOCAL/maintenance/2026-06-13-audit-output-redesign.md`.

**The `_LOCAL/` directory is gitignored** (via `/_*/`), so the registry never leaks into commits; forkers accumulate `archive/` history without polluting their repo.

## Invocation examples

```
/gse-audit                                  # full: 23 LLM jobs + Python engine (incl. 5 F-jobs)
/gse-audit --deterministic-only             # fast Python-only (~5s)
/gse-audit --coherence-only                 # 19 LLM jobs (A-D) + engine F-jobs, skip Category E
/gse-audit --strategic-only                 # 4 jobs, critique only
/gse-audit --category D                     # only horizontal clusters (11 jobs)
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
- `category` — A | B | C | D | E | F
- `type` — file_quality | intra_layer_group | layer_pair | horizontal_cluster | qualitative_critique
- `refinement` — none | downward | bidirectional
- `files` — explicit paths (globs like `src/activities/*.md` supported)
- `scope` — one-sentence description
- `checks` — numbered list of criteria to apply
