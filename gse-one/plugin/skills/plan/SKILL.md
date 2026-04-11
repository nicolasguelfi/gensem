---
description: "Select backlog items for sprint, create sprint plan. Cross-cutting — callable at any abstraction level."
---

# GSE-One Plan — Planning

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Default to `--strategic` if no sprint exists, `--tactical` otherwise |
| `--strategic`      | Sprint-level planning: select items from pool, create sprint |
| `--tactical`       | Task-level planning: reorder, adjust scope, refine within current sprint |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/backlog.yaml` — all work items (pool and sprint-assigned)
2. `.gse/status.yaml` — current sprint number and state
3. `.gse/profile.yaml` — user preferences (decision involvement, preferred verbosity)
4. `.gse/config.yaml` — project configuration (complexity budget, GitHub settings)
5. `docs/sprints/sprint-{NN}/plan.md` — existing plan for current sprint (if any)

## Workflow

### Strategic Planning (`--strategic`)

Used to create a new sprint by selecting items from the backlog pool.

#### Step 0 — Previous Sprint Analysis (Sprint N+1 only)

If this is NOT the first sprint (`current_sprint > 1`):

1. **Velocity calibration** — Read the previous sprint's results from `docs/sprints/sprint-{NN-1}/`:
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

#### Step 6 — Git Integration

1. **Create sprint branch**: `gse/sprint-{NN}` from `main`
2. **Assign branch names** to each task:

| Artefact Type | Branch Pattern |
|--------------|----------------|
| `code`       | `gse/sprint-{NN}/feat/{short-name}` |
| `test`       | `gse/sprint-{NN}/test/{short-name}` |
| `fix`        | `gse/sprint-{NN}/fix/{short-name}` |
| `design`     | `gse/sprint-{NN}/docs/{short-name}` |
| `doc`        | `gse/sprint-{NN}/docs/{short-name}` |
| `config`     | `gse/sprint-{NN}/chore/{short-name}` |

3. **Update TASK entries** with:
   ```yaml
   git:
     branch: "gse/sprint-02/feat/rate-limiting"
     branch_status: planned  # planned | created | merged | abandoned
   ```

Note: Branches are NOT created yet — only named. They are created when production starts on each task.

#### Step 7 — Persist Plan

Save the sprint plan to `docs/sprints/sprint-{NN}/plan.md`:

```yaml
---
id: PLN-{NNN}
artefact_type: task
title: "Sprint {NN} Plan"
sprint: {NN}
status: draft
created: {date}
author: pair
---
```

Content includes:
- Sprint goal (one sentence)
- Selected items with complexity and branch assignments
- Total complexity vs budget
- Dependencies between items (execution order)
- Definition of done for the sprint

Present the plan for user approval (Gate). Set status to `approved` once confirmed.

### Tactical Planning (`--tactical`)

Used to adjust an existing sprint without changing its scope fundamentally.

#### Step 1 — Show Current Sprint State

Display current sprint items with their statuses and progress.

#### Step 2 — Available Actions

- **Reorder** — Change execution priority of planned items
- **Split** — Break a large item into smaller sub-tasks
- **Defer** — Move an item back to pool (reduce scope)
- **Add** — Pull an item from pool into the sprint (with budget check)
- **Rename branch** — Update a task's branch name

#### Step 3 — Apply Changes

Update `.gse/backlog.yaml` and `docs/sprints/sprint-{NN}/plan.md` with changes.

Re-run complexity budget check after any additions.
