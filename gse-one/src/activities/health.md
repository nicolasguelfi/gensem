---
description: "Display project health dashboard with 8 dimensions. Triggered by /gse:health."
---

# GSE-One Health — Health Dashboard

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Show full health dashboard |
| `--dimension DIM`  | Show detail for a specific dimension |
| `--trend`          | Show health score trend across sprints |
| `--alerts-only`    | Show only dimensions with risk alerts |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current health scores and sprint state
2. `.gse/config.yaml` — `health.disabled_dimensions` (if any)
3. `.gse/backlog.yaml` — task statuses for computation
4. `.gse/profile.yaml` — user engagement metrics (consecutive_acceptances)
5. `docs/sprints/sprint-{NN}/review.md` — review findings (if exists)

## Workflow

### Step 1 — Compute Health Dimensions

Calculate each of the 8 health dimensions on a **0-10 scale** (spec 7.1). If `config.yaml` specifies `health.disabled_dimensions`, exclude those dimensions and adjust the overall score denominator accordingly.

#### 1. requirements_coverage (0-10)

- Count requirements (REQ-NNN) that have at least one traced implementation
- Score = (traced requirements / total requirements) * 10
- If no requirements artefact exists: score = N/A (excluded from overall)

#### 2. test_pass_rate (0-10)

- Read latest test campaign results from backlog task entries
- Score = (passing tests / total tests) * 10
- If no tests exist: score = 0 with alert "No tests found"

#### 3. design_debt (0-10)

- Count review findings tagged as architectural/design concerns
- Score = 10 - (design_findings * weight_per_finding)
- Weight: HIGH = 2.0, MEDIUM = 1.0, LOW = 0.5
- Floor at 0

#### 4. review_findings (0-10)

- Count unresolved review findings by severity
- Score = 10 - (HIGH * 1.5 + MEDIUM * 0.8 + LOW * 0.3)
- Floor at 0

#### 5. complexity_budget (0-10)

- Score = (remaining_budget / total_budget) * 10
- Alert if below 2: "Sprint budget nearly exhausted"

#### 6. traceability (0-10)

- Count tasks with proper traces (requirement -> design -> code -> test)
- Score = (fully_traced_tasks / total_tasks) * 10
- Partial traces count proportionally

#### 7. git_hygiene (0-10)

Computed from 6 sub-metrics (each on 0-10, then weighted):

| Sub-metric | Weight | Score 10 | Score 0 |
|------------|--------|----------|---------|
| Active branches | 20% | ≤3 | >10 |
| Stale branches | 20% | 0 | >3 |
| Uncommitted changes | 20% | 0 across all worktrees | >5 files |
| Merge conflicts | 20% | 0 | >0 |
| Main clean | 10% | Clean + tagged | Dirty |
| Unreviewed branches | 10% | 0 | >2 |

```
git_hygiene = sum(sub_metric * weight)
```

#### 8. ai_integrity (0-10)

Computed from 3 factors (each on 0-10, then weighted):

| Factor | Weight | Computation |
|--------|--------|-------------|
| Unverified assertions | 40% | Count of `[AI-INTEGRITY]` findings from devil's advocate |
| Hallucination findings | 30% | Libraries or APIs flagged as non-existent |
| User engagement | 30% | Based on `consecutive_acceptances` — high count indicates complaisance risk |

Engagement scoring:
- 0-3 consecutive acceptances: 10 (healthy interaction)
- 4-6 consecutive acceptances: 7.5 (mild concern)
- 7-9 consecutive acceptances: 5 (notable pattern)
- 10+ consecutive acceptances: 2.5 (significant concern — user may not be reviewing)

### Step 2 — Compute Overall Score

```
overall = sum(enabled_dimensions) / count(enabled_dimensions)
```

Dimensions listed in `health.disabled_dimensions` are excluded from both numerator and denominator.

### Step 3 — Risk Alerts

Generate actionable warnings for concerning dimensions:

```
RISK ALERTS
  [!] test_pass_rate: 4.5/10 — 3 failing tests in TASK-005
      Action: run /gse:fix --task TASK-005
  
  [!] git_hygiene: 5.5/10 — 2 stale branches, 1 worktree with uncommitted changes
      Action: review stale branches, commit or stash uncommitted work
  
  [!] ai_integrity: 6.0/10 — 8 consecutive user acceptances without modification
      Action: review recent outputs critically, consider challenging assumptions
```

Threshold for alert: dimension score below 7.

### Step 4 — Trend Display

If `--trend` is specified, show health evolution across sprints:

```
HEALTH TREND
  Sprint | Overall | Req  | Test | Debt | Review | Budget | Trace | Git  | AI
  S01    |   7.2   | 8.0  | 6.5  | 7.0  |  7.5   |  9.0   | 6.0   | 7.0  | 6.5
  S02    |   7.8   | 8.5  | 7.0  | 7.5  |  8.0   |  8.5   | 7.0   | 7.5  | 8.0
  S03    |   6.8   | 8.5  | 4.5  | 7.0  |  6.0   |  4.0   | 7.5   | 7.0  | 6.0
                            ^^                        ^^
                        declining                 declining
```

Mark dimensions with declining trend (2+ consecutive drops).

### Step 5 — Dimension Detail

If `--dimension DIM` is specified, show detailed breakdown:

```
DIMENSION: git_hygiene (5.5/10)

Sub-metrics:
  Active branches:      8/10 (weight 20%)  — 3 active (expected: 2-4)
  Stale branches:       6/10 (weight 20%)  — 2 stale: gse/sprint-01/feat/old, gse/sprint-01/doc/readme
  Uncommitted changes:  4/10 (weight 20%)  — .worktrees/sprint-02-feat-api has 5 uncommitted files
  Merge conflicts:     10/10 (weight 20%)  — no conflicts detected
  Main clean:          10/10 (weight 10%)  — main matches last delivery
  Unreviewed branches:  0/10 (weight 10%)  — 1 unreviewed: gse/sprint-02/feat/api

Recommendations:
  1. Commit or stash changes in sprint-02-feat-api worktree
  2. Review or delete stale branches from sprint-01
  3. Run /gse:review for unreviewed feature branches
```

### Step 6 — Persist

1. Update `status.yaml` with computed health scores
2. If trend data does not exist, initialize `docs/health-history.yaml` with current sprint scores
3. Append current sprint scores to health history for future trend analysis
