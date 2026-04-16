---
description: "Reload checkpoint, verify worktrees, brief user. Triggered by /gse:resume."
---

# GSE-One Resume — Session Resume

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Resume from the latest checkpoint |
| `--checkpoint FILE` | Resume from a specific checkpoint file |
| `--list`           | List all available checkpoints |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read (in priority order — load essential state first, defer the rest):
1. `.gse/status.yaml` — current state (highest priority)
2. `.gse/plan.yaml` — living sprint plan (if it exists) — source of workflow trajectory
3. `.gse/profile.yaml` — user profile and preferences
4. `.gse/config.yaml` — project configuration
5. `.gse/backlog.yaml` — sprint tasks only (current sprint filter)
6. Remaining files loaded on demand during workflow

## Workflow

### Step 1 — Load Checkpoint

1. If `--list` is specified:
   - List all files in `.gse/checkpoints/` sorted by date (newest first)
   - Display: timestamp, sprint, phase, note (if any)
   - Exit

2. If `--checkpoint FILE` is specified:
   - Load the specified checkpoint file
3. Otherwise:
   - Find the latest checkpoint in `.gse/checkpoints/` (sorted by filename, newest first)
   - If no checkpoints exist: report "No checkpoint found. Use `/gse:go` to start." and exit

4. Read the checkpoint YAML and extract: `git_state.worktrees`, `status_snapshot`, `backlog_sprint_snapshot`, `note`

### Step 2 — Verify Worktrees

Run `git worktree list` to get the current worktree state on disk.

For each worktree recorded in the checkpoint:

#### Worktree is present

1. Check for external changes since the checkpoint:
   ```
   git log {saved_last_commit}..HEAD --oneline
   ```
   (executed within the worktree directory)

2. If new commits exist: mark as `[CHANGED]` — someone (or another session) modified this branch
3. If no new commits: mark as `[OK]` — unchanged since pause
4. Check for uncommitted changes: mark as `[DIRTY]` if any

#### Worktree is missing

1. Mark as `[MISSING]`
2. Check if the branch still exists: `git branch --list {branch_name}`
3. If branch exists: propose recreation:
   ```
   git worktree add {original_path} {branch_name}
   ```
4. If branch is also missing: report as `[LOST]` — manual intervention needed

### Step 3 — Report Worktree State

Display worktree verification results with symbols:

```
WORKTREES
  [OK]      .worktrees/sprint-02-feat-api      — TASK-003 (unchanged)
  [CHANGED] .worktrees/sprint-02-feat-auth     — TASK-004 (2 new commits since pause)
  [DIRTY]   .worktrees/sprint-02-doc-readme    — TASK-005 (uncommitted changes)
  [MISSING] .worktrees/sprint-02-test-unit     — TASK-006 (branch exists, propose recreate)
  [LOST]    .worktrees/sprint-01-feat-old      — TASK-002 (branch deleted)
```

If any worktrees are `[MISSING]`, present Gate:
- **Recreate** — Recreate missing worktrees from their branches
- **Skip** — Continue without them
- **Discuss** — Investigate what happened

### Step 4 — Context Briefing

Present a summary of where the user left off:

```
SESSION RESUMED
  Paused: {checkpoint_timestamp} ({relative time, e.g., "2 days ago"})
  Sprint: S{NN} ({lifecycle_phase})
  Last activity: {last_activity}
  Last task: TASK-{ID} ({task_title})
```

If a note was attached to the checkpoint:
```
  Note: "{note text}"
```

Sprint progress:
```
  Tasks: {done}/{total} complete
  Budget: {used}/{total} complexity points
  Health: {overall_score}/100
```

**If `.gse/plan.yaml` exists with `status: active`,** append a workflow trajectory block:

```
  Next in plan: {workflow.active}
  Pending:      {workflow.pending}
  Completed:    {count} of {expected_count}
  {if coherence.alerts is non-empty}:
  ⚠ Alerts:     {list of active alerts}
```

This is more precise than `status.yaml.last_activity` alone (which says "where we were" but not "where we're going"). For beginners, translate the activity names per P9 Adaptive Communication (e.g., `reqs` → "writing down what the app should do", `produce` → "building").

### Step 5 — Propose Next Action

Determine the next action using, in priority order:
1. **Primary — `.gse/plan.yaml.workflow.active`** if `plan.yaml` exists with `status: active`. The workflow's `active` field is the declarative source of truth for "what comes next" (see orchestrator Decision Tree). This is more reliable than inferring from `last_activity`.
2. **Fallback — checkpoint `last_activity`** if `plan.yaml` is absent (Micro mode or pre-v0.20 projects). Use the table below.

| Checkpoint State | Proposed Action |
|------------------|-----------------|
| `last_activity: produce`, task in-progress | "Continue producing TASK-{ID}: {title}" → `/gse:produce --task {ID}` |
| `last_activity: produce`, task done | "All production done. Ready for review." → `/gse:review` |
| `last_activity: review`, fixes pending | "Review complete, fixes needed." → `/gse:fix` |
| `last_activity: fix` | "Fixes applied. Ready for delivery." → `/gse:deliver` |
| `last_activity: deliver` | "Sprint delivered. Time to capitalize." → `/gse:compound` |
| `last_activity: compound` | "Capitalization done. Ready to integrate." → `/gse:integrate` |
| `last_activity: pause` (nested) | Unwrap to the activity before the pause |

Present the proposal and wait for user confirmation.

### Step 6 — Finalize

1. Update `status.yaml`:
   - `session_paused: false`
   - `last_activity: resume`
   - `last_activity_timestamp: {now}`
   - Remove `pause_checkpoint` field
2. The session is now active. Proceed with the accepted action or wait for user command.
