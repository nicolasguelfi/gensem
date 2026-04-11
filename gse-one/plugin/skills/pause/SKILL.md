---
description: "Auto-commit work, save session checkpoint. Triggered by /gse:pause."
---

# GSE-One Pause — Session Pause

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Auto-commit all active worktrees and save checkpoint |
| `--no-commit`      | Save checkpoint without auto-committing |
| `--note "text"`    | Attach a note to the checkpoint (context for future resume) |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state
2. `.gse/config.yaml` — git strategy
3. `.gse/backlog.yaml` — active tasks and their worktree assignments

## Workflow

### Step 1 — Auto-Commit Active Worktrees

Unless `--no-commit` was specified:

For each TASK in `backlog.yaml` with `git.worktree_status: active`:

1. Navigate to the worktree directory: `.worktrees/{worktree_name}`
2. Check for uncommitted changes: `git status --porcelain`
3. If changes exist:
   ```
   git add -A
   git commit -m "gse(pause): checkpoint — {task_title}

   Sprint: S{NN}
   Task: TASK-{ID}
   Reason: session pause
   "
   ```
4. Update TASK in `backlog.yaml`:
   - `git.uncommitted_changes: 0`
   - `git.last_pause_commit: {hash}`

If no worktrees are active (strategy is `branch-only` or `none`):
1. Check current branch for uncommitted changes
2. If changes exist, auto-commit with the same convention

Report: "Auto-committed {N} worktree(s) with changes."

### Step 2 — Save Checkpoint

Create a checkpoint file at `.gse/checkpoints/checkpoint-{YYYY-MM-DD-HHMM}.yaml`:

```yaml
checkpoint:
  timestamp: "{ISO-8601 timestamp}"
  user: "{profile.yaml user name}"
  sprint: S{NN}
  phase: "{lifecycle_phase}"
  last_activity: "{last_activity}"
  last_task: "TASK-{ID}"
  note: "{user note if --note provided}"

status_snapshot:
  lifecycle_phase: "{phase}"
  current_sprint: {NN}
  last_activity: "{activity}"
  last_activity_timestamp: "{timestamp}"
  health_score: {overall}

backlog_sprint_snapshot:
  tasks:
    TASK-{ID}:
      status: "{status}"
      complexity: {N}
      branch: "{branch or null}"

git_state:
  current_branch: "{active branch}"
  worktrees:
    - path: ".worktrees/{name}"
      branch: "gse/sprint-{NN}/{type}/{name}"
      task: "TASK-{ID}"
      last_commit: "{hash}"
      clean: true
    - path: ".worktrees/{name2}"
      branch: "gse/sprint-{NN}/{type}/{name2}"
      task: "TASK-{ID2}"
      last_commit: "{hash2}"
      clean: true
```

### Step 3 — Update Status

1. Update `status.yaml`:
   - `last_activity: pause`
   - `last_activity_timestamp: {now}`
   - `session_paused: true`
   - `pause_checkpoint: checkpoint-{YYYY-MM-DD-HHMM}.yaml`

### Step 4 — Report

```
SESSION PAUSED
  Checkpoint: .gse/checkpoints/checkpoint-{YYYY-MM-DD-HHMM}.yaml
  Auto-committed: {N} worktree(s)
  Sprint: S{NN} ({lifecycle_phase})
  Active tasks: {count}
  
  Resume with: /gse:resume
```
