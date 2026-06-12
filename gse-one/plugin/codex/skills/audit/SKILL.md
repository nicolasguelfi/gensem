---
name: audit
description: "Audit the project for methodology drift. Detects format inconsistencies, missing evidence, skipped steps, and other deviations from the canonical methodology. Triggered manually by /gse:audit or auto-triggered by the orchestrator when drift signals accumulate (Phase 3)."
---

# GSE-One Audit — Project Methodology Audit

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Run a complete audit (deterministic checks in Phase 1; semantic layer added in Phase 2). Generate report. Present findings and propose corrections via Gate. |
| `--auto`           | Auto-triggered invocation (reserved for orchestrator use in Phase 3). Shorter presentation: Inform + Gate instead of full report. |
| `--fix`            | Auto-apply safe LOW-severity corrections flagged `auto_fixable: true`. HIGH and MEDIUM still require per-finding confirmation. |
| `--no-fix`         | Audit only — produce the report, no correction offered. Useful for CI or dry inspection. |
| `--quick`          | Deterministic checks only (in Phase 1 this is identical to `(no args)` since the semantic layer is not yet available). |
| `--help`           | Show this command's usage summary. |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint, phase, activity history, workflow observations
2. `.gse/config.yaml` — project config (mode, git strategy, coach config)
3. `.gse/backlog.yaml` — TASKs and their `test_evidence` fields
4. `.gse/plan.yaml` — living sprint plan (if exists)
5. `docs/sprints/sprint-{NN}/*` — current sprint artefacts (reqs.md, design.md, review.md, test-strategy.md)
6. `docs/dashboard.html` — for freshness check (mtime vs state changes)

## Workflow

### Step 1 — Run deterministic checks

1. **Validate tool registry** — `cat ~/.gse-one` must exist and point to a valid plugin path. If not, abort with: *"GSE-One registry not found. Run `python3 install.py` to fix."*
2. **Execute** `python3 "$(cat ~/.gse-one)/tools/project-audit.py" --json` — the deterministic audit engine produces a machine-readable list of findings on `stdout`.
3. **Parse findings** — each finding carries: `id` (`AUD-NNN`), `severity` (`HIGH` | `MEDIUM` | `LOW`; `CRITICAL` reserved for P15 escalation), `category` (dashboard, test-evidence, format, git-state, workflow, coach, intent, backlog, open-questions, sprint-freeze, file-structure, etc.), `title`, `detail`, `evidence`, `recommendation`, `auto_fixable` (bool), `fix_command` (optional shell command).

### Step 2 — (Phase 2 placeholder) Invoke project-reviewer sub-agent

*This step is defined for forward compatibility but is a no-op in Phase 1 (deterministic-only release).*

When Phase 2 ships:
1. Spawn the `project-reviewer` sub-agent (archetype: Reviewer; perspective: `project-methodology`) with fresh context.
2. Pass: current sprint artefacts, recent `activity_history` and `workflow_observations`, active profile, last N user messages.
3. The reviewer returns semantic findings (with `AUD-NNN` IDs interleaved with Step 1 findings).

Phase 1 behavior: emit a one-line Inform — *"[Inform] Semantic audit layer deferred to Phase 2. Deterministic checks completed. Some drift patterns (P9 jargon, P14 learning delivery, REQ/DESIGN coherence) may go undetected until the semantic layer ships."*

### Step 3 — Generate consolidated audit report

Write the audit report:
- **If a sprint is active** (`.gse/plan.yaml → status: active`): `docs/sprints/sprint-{NN}/audit-{YYYY-MM-DDThhmm}.md`
- **Otherwise** (greenfield, between sprints, delivered sprint frozen): `.gse/audits/audit-{YYYY-MM-DDThhmm}.md` (create `.gse/audits/` if absent)

Use the template `$(cat ~/.gse-one)/templates/sprint/audit.md` (created in sub-proposition J.3). Populate:
- Metadata: sprint, date, triggering context (`manual` | `auto-trigger` | `scheduled`), version of audit engine (from the `# @gse-tool` header)
- Summary: count of findings per severity
- Findings list (canonical format — see **Output Format** below)
- Recommendations and references

### Step 4 — Present findings to user (Gate)

**Zero findings:**
- Inform only: *"✅ All methodology checks passed. No drift detected."*
- No Gate, no correction, return control.

**Findings exist:**
- Display a P9-adapted summary.
  - **Beginner:** plain language, no jargon. Example: *"I found 3 small issues and 1 important issue in the project organization."*
  - **Intermediate/expert:** structured table with counts and category breakdown.
- Present Gate (4 options per P4):
  1. **Apply safe corrections now** (recommended default) — auto-applies `auto_fixable: true` findings; asks per-item for HIGH/MEDIUM findings in Step 5.
  2. **Review per-finding** — walks through each finding; user decides one by one (apply / defer / discuss).
  3. **Defer all** — no correction applied. Audit report persists for next `/gse:audit` invocation.
  4. **Discuss** — explain findings, rationale, implications, before deciding.

**Flag `--fix`:** skip Gate, auto-apply all LOW `auto_fixable: true` findings silently, emit Inform summary of applied corrections. HIGH and MEDIUM still require Step 5 per-item confirmation.

**Flag `--no-fix`:** skip Step 4 and Step 5 entirely. Report is written, activity terminates.

**Flag `--auto` (Phase 3):** present a single Inform *"[Inform] Methodology drift detected (N HIGH, M MEDIUM, K LOW findings). Report at `{report_path}`."* + compact Gate with 3 options: "Run full audit now" / "Defer" / "Discuss". No full-report display to avoid interrupting the user's current activity.

### Step 5 — Apply corrections

For each correction approved in Step 4:
1. **Execute the fix** — either run `fix_command` (shell) or invoke the appropriate activity (e.g., `/gse:tests --run` to populate `test_evidence`, `/gse:hug --update` to set missing profile fields).
2. **Verify the fix** — re-run the single deterministic check that flagged the finding (if possible). If still failing, report and stop for that finding.
3. **Log a DEC-NNN** in `.gse/decisions.md` if the correction is non-trivial (scope-shaping, reclassification, manual override of a HIGH finding).
4. **Update `status.yaml`** → append to `workflow_observations`: `{axis: audit, moment: <trigger>, severity_counts: {...}, applied: N, deferred: M, report: <path>, timestamp: <iso8601>}`.
5. **Regenerate dashboard** — this is itself an audit check; if it was flagged as stale, the correction regenerates it.

After all corrections applied: re-run Step 1 (deterministic checks) **once** to verify. If new findings appear (regression), report them but do NOT loop — prevent infinite audit.

### Step 6 — Finalize

1. **Display post-audit summary** — adapted P9 by expertise level.
   - Beginner: *"Audit done. I fixed N things automatically. M things need your attention later."*
   - Expert: *"Audit complete. N findings applied, M deferred. Full report: `audit-{timestamp}.md`."*
2. **Persist audit index** in `status.yaml → audit_history` (list of `{timestamp, trigger, findings_total, findings_applied, findings_deferred, report_ref}`). Capped at last 20 audits; older entries are summarized.
3. **Return control** — audit is non-blocking on the lifecycle. The agent returns to the previous activity (if auto-triggered) or awaits user input (if manually invoked).

## Output Format

Findings use the prefix `AUD-NNN` to distinguish from review findings (`RVW-NNN`). Canonical format per spec §P6 (after J.4 spec update):

```
AUD-001 [HIGH] — Dashboard not regenerated since last activity
  category: dashboard-freshness
  detail: docs/dashboard.html mtime is 3 hours older than the latest change to .gse/ state files. Per /gse:go Step 2.6 Dashboard Refresh, it should be regenerated at each activity transition.
  evidence: dashboard mtime=2026-04-22T10:14, state mtime=2026-04-22T13:22
  recommendation: Regenerate the dashboard.
  auto_fixable: true
  fix_command: python3 "$(cat ~/.gse-one)/tools/dashboard.py"

AUD-002 [HIGH] — Must-priority REQ has no test evidence
  category: test-evidence
  detail: REQ-003 (priority: must) is implemented by TASK-003, but TASK-003.test_evidence.status is "absent". Per spec §6.3 Test Execution and Evidence, every covered TASK must have evidence.
  evidence: backlog.yaml TASK-003 has no test_evidence field populated
  recommendation: Run /gse:tests --run on TASK-003 to populate the evidence.
  auto_fixable: false
  fix_command: null

AUD-003 [LOW] — Review format uses parentheses instead of canonical brackets
  category: format
  detail: review.md contains "RVW-001 (MEDIUM)" but the canonical format (per src/agents/code-reviewer.md Output Format) is "RVW-001 [MEDIUM]". Minor — the dashboard parser tolerates both, but the agent should converge on brackets.
  evidence: review.md line 22: ### RVW-001 (MEDIUM) - Custom categories...
  recommendation: Reformat to square brackets.
  auto_fixable: true
  fix_command: (applied by the activity via in-place regex replace)
```

Severity scale baseline: `HIGH` / `MEDIUM` / `LOW` (identical to review severity scale, spec §6.5). `CRITICAL` is reserved for P15 escalation cases detected during audit (e.g., silently corrupted state file, diverging git history).

## Invocation scenarios

- **Manual by user** — `/gse:audit` invoked at any moment. Typical contexts: before `/gse:deliver` as a self-check, after suspicion of drift, periodic (weekly) review, after a training day to understand what happened.
- **Auto by orchestrator (Phase 3)** — the orchestrator's *Methodology Audit Auto-Trigger Invariant* (documented in `plugin/agents/gse-orchestrator.md` after Phase 3 sub-proposition lands) detects drift signals in conversation history (user pushback patterns + coach correlation) and invokes `/gse:audit --auto`.
- **Scheduled / CI** — `plugin/tools/project-audit.py` can be invoked directly from CI or cron for headless execution, bypassing the activity workflow entirely.

## Interaction with other activities

- **Non-blocking** — `/gse:audit` does not mutate sprint workflow state (`plan.yaml → workflow`) unless a correction explicitly does. It is a read-and-propose activity by default.
- **Complementary to `/gse:review`** — review focuses on the *outputs of a sprint* (code quality, security, tests). Audit focuses on *methodology compliance* (format, evidence presence, step fidelity, drift signals). The two do not overlap.
- **Complementary to coach** — coach observes *during* activities and appends to `workflow_observations`. Audit reads those observations *between* activities and produces a structured, corrective report.
- **Does NOT replace inline guardrails** — specifically, `/gse:deliver` Step 1.5 — Test Execution Evidence (sub-proposition B) remains in force as an inline hard guardrail. Audit is a second net, not a replacement.

## Sprint Freeze interaction

Per spec §14.3 Sprint Freeze Invariant, `/gse:audit` is exempt from the Sprint Freeze Gate (it does not write to the backlog or advance workflow state except for appending to `workflow_observations` and `audit_history`, which are both session-level not sprint-level).
