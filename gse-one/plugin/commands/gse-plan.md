---
name: "gse-plan"
description: "Select backlog items for sprint, create/update sprint plan in `.gse/plan.yaml`. Cross-cutting — callable at any abstraction level."
---


# GSE-One Plan — Planning

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Default to `--strategic` if no sprint exists, `--tactical` otherwise |
| `--strategic`      | Sprint-level planning: select items from pool, create `.gse/plan.yaml` |
| `--tactical`       | Task-level planning: reorder, adjust scope, refine within active plan |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/backlog.yaml` — all work items (pool and sprint-assigned)
2. `.gse/status.yaml` — current sprint number and lifecycle state
3. `.gse/profile.yaml` — user preferences (decision involvement, preferred verbosity)
4. `.gse/config.yaml` — project configuration (complexity budget, GitHub settings)
5. `.gse/plan.yaml` — existing living plan for the current sprint (if any)

## Workflow

### Strategic Planning (`--strategic`)

Used to create a new sprint by selecting items from the backlog pool.

#### Step 0 — Previous Sprint Analysis (Sprint N+1 only)

If this is NOT the first sprint (`current_sprint > 1`):

1. **Velocity calibration** — Read the previous sprint's archive from `docs/sprints/sprint-{NN-1}/plan-summary.md`:
   - How many complexity points were planned vs delivered?
   - Use actual velocity to calibrate this sprint's budget (Inform tier)
   - Example: "Last sprint you planned 10 points and delivered 8. I recommend a budget of 8 for this sprint."

2. **Carryover detection** — Check `backlog.yaml` for tasks from the previous sprint with `status: deferred` or `status: in-progress`:
   - Present unfinished tasks: "These tasks were not completed in sprint {NN-1}. Include them in this sprint?"
   - Gate decision per task: Include / Return to pool / Discard / Discuss

#### Step 1 — Present Pool

Display all items in the pool (including any carryover from Step 0) with their metadata:

```
Backlog Pool — 8 items available
────────────────────────────────
  TASK-010 [code]        ◌  Add rate limiting middleware          complexity: ?
  TASK-011 [design]      ◌  Design notification system            complexity: ?
  TASK-012 [requirement] ◌  Define admin role permissions          complexity: ?
  TASK-013 [code]        ◌  Implement webhook handler              complexity: ?
  TASK-014 [test]        ◌  Write integration tests for auth       complexity: ?
  TASK-015 [doc]         ◌  Document API endpoints                 complexity: ?
  TASK-016 [code]        ◌  Add CSV export feature                 complexity: ?
  TASK-017 [design]      ◌  Design plugin architecture             complexity: ?
```

#### Step 2 — Complexity Assessment

For each candidate item, assess complexity on a 3-point scale:

| Level | Points | Meaning |
|-------|--------|---------|
| **S** (Small) | 1 | < 2 hours, well-understood, minimal risk |
| **M** (Medium) | 3 | 2-8 hours, some unknowns, moderate risk |
| **L** (Large) | 5 | > 8 hours, significant unknowns, high risk — consider splitting |

Present complexity estimates and ask for user validation (Gate).

#### Step 3 — Select Sprint Items

Based on user's decision involvement preference:
- **Autonomous**: Agent selects items up to the complexity budget, presents for approval
- **Collaborative**: Agent proposes a selection, user adjusts
- **Supervised**: User selects items, agent validates feasibility

#### Step 4 — Complexity Budget Check (Hard Guardrail)

Read `config.yaml` → `complexity.budget_per_sprint` (default: 10 points).

Compute total complexity of selected items:
- If total <= budget: proceed
- If total > budget: **Hard guardrail** —
  ```
  Sprint is over budget ({total}/{budget} points).
  1. Defer lower-priority items to next sprint (recommended)
  2. Split the sprint into two smaller ones
  3. Accept over-budget (increases defect risk, review will flag it)
  4. Discuss
  ```
  The agent MUST NOT silently proceed with an over-budget sprint.

#### Step 5 — Promote to Sprint

For each selected item:
1. Set `sprint: {next_sprint_number}`
2. Set `status: planned`
3. Set `complexity: S|M|L`

Increment sprint number in `status.yaml`.

**Initialize workflow.expected based on project mode:**

| Mode | workflow.expected |
|------|-------------------|
| **Full** | `[collect, assess, plan, reqs, design, tests, produce, review, deliver]` |
| **Full (design skipped)** | `[collect, assess, plan, reqs, tests, produce, review, deliver]` |
| **Lightweight** | `[plan, produce, deliver]` |
| **Micro** | (no plan.yaml is created in Micro mode) |

Conditional insertions:
- Insert `preview` after `design` if `config.yaml → project.domain` is `web` or `mobile`
- Insert `fix` after `review` if review produces findings (recorded when review completes)

LC03 activities (`compound`, `integrate`) are tracked in `status.yaml`, not in this sprint's `plan.yaml`.

#### Step 6 — Git Integration

1. **Create sprint integration branch**: `gse/sprint-{NN}/integration` from `main`
2. **Assign branch names** to each task:

| Artefact Type | Branch Pattern |
|--------------|----------------|
| `code`       | `gse/sprint-{NN}/feat/{short-name}` |
| `test`       | `gse/sprint-{NN}/test/{short-name}` |
| `fix`        | `gse/sprint-{NN}/fix/{short-name}` |
| `design`     | `gse/sprint-{NN}/docs/{short-name}` |
| `doc`        | `gse/sprint-{NN}/docs/{short-name}` |
| `config`     | `gse/sprint-{NN}/chore/{short-name}` |

3. **Update TASK entries** in `backlog.yaml` with:
   ```yaml
   git:
     branch: "gse/sprint-02/feat/rate-limiting"
     branch_status: planned  # planned | created | merged | abandoned
   ```

4. **Record branch name on each task** in `plan.yaml.tasks[].branch` for quick lookup during PRODUCE.

Note: Branches are NOT created yet — only named. They are created when production starts on each task.

#### Step 7 — Persist Plan

Write the living sprint plan to `.gse/plan.yaml`:

```yaml
version: 1
id: PLN-{NNN}                        # artefact ID for traceability
sprint: {NN}
mode: full                           # full | lightweight | micro
status: active                       # active | completed | abandoned

goal: "Short sprint goal description"

tasks:
  - id: TASK-010
    order: 1
    complexity: M                    # S (1pt) | M (3pt) | L (5pt)
    branch: "gse/sprint-{NN}/feat/rate-limiting"
  - id: TASK-011
    order: 2
    complexity: S
    branch: "gse/sprint-{NN}/feat/notifications"

budget:
  total: 8                           # sum of selected complexity points
  consumed: 0                        # updated as tasks complete
  remaining: 8

workflow:
  expected: [collect, assess, plan, reqs, design, tests, produce, review, deliver]
  completed:
    - activity: collect              # if COLLECT already ran in LC01
      completed_at: "{iso8601}"
      notes: "{short summary}"
    - activity: assess               # if ASSESS already ran in LC01
      completed_at: "{iso8601}"
      notes: "{short summary}"
    - activity: plan                 # this run
      completed_at: "{iso8601}"
  active: reqs                       # next activity to execute
  pending: [design, tests, produce, review, deliver]
  skipped:
    - activity: preview              # if project_domain is not web/mobile
      reason: "project_domain: {value} — not applicable"

coherence:
  last_evaluated: "{iso8601}"
  scope_changes: []                  # populated at each transition if scope drifts
  alerts: []                         # active alerts; cleared when resolved

risks:
  - description: "{risk description}"
    likelihood: low | medium | high
    mitigation: "{mitigation plan}"

created: "{iso8601}"
updated: "{iso8601}"
```

**workflow.completed initialization:**
- Pre-populate with COLLECT and ASSESS if LC01 already ran. Read their timestamps from `status.yaml.activity_history` filtered by `sprint == current_sprint` (authoritative source). If the history is empty or the entry is missing (e.g., migrated project), fall back to `status.yaml.last_activity_date` for the last recorded activity and leave older entries with `completed_at: null`.
- Always append the current PLAN activity as completed.
- Reset `status.yaml.activity_history` to `[]` for the new sprint (the prior sprint's history is archived in the previous `plan-summary.md`).

**workflow.active:** Set to the next expected activity after PLAN — typically `reqs` in Full mode, `produce` in Lightweight mode.

Present the plan for user approval (Gate). Set `status: active` once confirmed.

Also update `status.yaml` cursor fields:
- `last_activity: plan`
- `last_activity_timestamp: {now}`
- `current_sprint: {NN}`

### Tactical Planning (`--tactical`)

Used to adjust an existing sprint without changing its scope fundamentally. Operates on `.gse/plan.yaml`.

#### Step 1 — Show Current Sprint State

Read `.gse/plan.yaml` and display:
- Goal, mode, and budget (total / consumed / remaining)
- Tasks with their order, complexity, and current status (from `backlog.yaml`)
- Current workflow position: `active` activity, `pending` queue, `completed` history
- Active coherence alerts, if any

#### Step 2 — Available Actions

- **Reorder** — Change execution priority of planned items (`plan.yaml.tasks[].order`)
- **Split** — Break a large item into smaller sub-tasks (update both `backlog.yaml` and `plan.yaml.tasks`)
- **Defer** — Move an item back to pool (remove from `plan.yaml.tasks`, update `backlog.yaml`)
- **Add** — Pull an item from pool into the sprint (add to `plan.yaml.tasks`, with budget check)
- **Rename branch** — Update a task's `branch` field in both files

#### Step 3 — Apply Changes

Update `.gse/plan.yaml` (tasks, budget, `updated` timestamp) and `.gse/backlog.yaml` (TASK statuses).

If the change alters scope, append an entry to `plan.yaml.coherence.scope_changes`:

```yaml
scope_changes:
  - timestamp: "{iso8601}"
    trigger: tactical-replan
    description: "{what changed}"
    budget_impact: "{+/- N pts}"
```

Re-run the complexity budget check after any additions. If over budget, apply the Hard guardrail from Strategic Step 4.

### Notes

- `.gse/plan.yaml` is the **single source of truth** for sprint planning state. `backlog.yaml` remains the authority for TASK data.
- The orchestrator maintains `plan.yaml` (workflow, budget, coherence) at every activity transition — see the Plan Update Protocol in the orchestrator.
- At DELIVER, a read-only snapshot is archived to `docs/sprints/sprint-{NN}/plan-summary.md` and `plan.yaml.status` is set to `completed`.
