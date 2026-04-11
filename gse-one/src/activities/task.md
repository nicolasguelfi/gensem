---
description: "Execute a task outside standard lifecycle. Triggered by /gse:task."
---

# GSE-One Task — Ad-hoc Task

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| `<description>`    | Free-text description of the task to execute |
| `--type TYPE`      | Force artefact type (feat/fix/doc/test/refactor/task) |
| `--complexity N`   | Override complexity estimate (1-5) |
| `--no-review`      | Mark task as not requiring review (for trivial tasks) |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state
2. `.gse/config.yaml` — git strategy, complexity budget
3. `.gse/backlog.yaml` — current sprint backlog (to add the task)
4. `.gse/profile.yaml` — user expertise level

## Workflow

### Step 1 — Task Analysis

1. Parse the task description from `$ARGUMENTS`
2. Infer artefact type from description if `--type` not provided:
   - Keywords like "fix", "bug" -> `fix`
   - Keywords like "add", "create", "implement" -> `feat`
   - Keywords like "document", "readme", "comment" -> `doc`
   - Keywords like "test", "spec" -> `test`
   - Keywords like "refactor", "clean", "reorganize" -> `refactor`
   - Default: `task`
3. Estimate complexity (1-5) if `--complexity` not provided:
   - 1: trivial change (typo, config tweak)
   - 2: small change (single file, straightforward)
   - 3: medium change (multiple files, some design)
   - 4: large change (new feature, cross-cutting)
   - 5: complex change (architectural impact)

### Step 2 — Budget Check

1. Read current sprint complexity budget from `status.yaml`
2. Check if the task fits within remaining budget
3. If budget would be exceeded:
   - Report: "This task (complexity {N}) would exceed the sprint budget (remaining: {M})."
   - Present Gate:
     - **Proceed** — Accept budget overrun
     - **Reduce scope** — Discuss a simpler version
     - **Defer** — Add to pool for next sprint
     - **Discuss** — Explore alternatives

### Step 3 — Add to Backlog

Create a new TASK entry in `backlog.yaml`:

```yaml
TASK-{next_id}:
  title: "{description}"
  artefact_type: {inferred_type}
  complexity: {estimated}
  sprint: S{current_NN}
  status: planned
  source: ad-hoc
  requires_review: {true unless --no-review or complexity <= 1}
  created_at: {timestamp}
```

### Step 4 — Git Setup

Create a dedicated branch and worktree following the same logic as `/gse:produce` Step 2:

- Branch name: `gse/sprint-{NN}/task/{slug}`
- Worktree: `.worktrees/sprint-{NN}-task-{slug}`

The git strategy (worktree/branch-only/none) is read from `config.yaml`.

### Step 5 — Execute Task

1. Execute the work described in the task
2. Commit at logical checkpoints:
   ```
   gse(sprint-{NN}/task): {description}

   Sprint: S{NN}
   Task: TASK-{ID}
   Source: ad-hoc
   ```

### Step 6 — Finalize

1. Update TASK in `backlog.yaml`:
   - `status: done`
   - `completed_at: {timestamp}`
2. Consume complexity budget: subtract task complexity from sprint remaining
3. Update `status.yaml`:
   - `last_activity: task`
   - `last_activity_timestamp: {now}`
   - `last_task: TASK-{ID}`
4. Review scheduling:
   - If `requires_review: true`: task will be included in next `/gse:review`
   - If `requires_review: false` (complexity <= 1 or `--no-review`): task is ready for delivery
5. Report task summary:
   - Task created and completed: TASK-{ID}
   - Complexity consumed: {N}
   - Remaining budget: {M}
   - Review required: {yes/no}
