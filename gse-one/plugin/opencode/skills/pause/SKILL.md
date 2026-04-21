---
name: pause
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

Create a checkpoint file at `.gse/checkpoints/checkpoint-{YYYY-MM-DD-HHMM}.yaml` using the checkpoint.yaml template (`plugin/templates/checkpoint.yaml` — authoritative schema). Populate all fields from the current session state:

- `checkpoint.timestamp`: current ISO 8601 timestamp
- `timestamp`: ISO 8601 current time
- `user`: from `profile.yaml → user.name`
- `last_task`: current TASK from session context (e.g., task the user was producing)
- `note`: from `--note` flag if provided, else empty
- `status_snapshot`: extract `current_phase`, `current_sprint`, `last_activity`, `last_activity_timestamp`, `health.score` from `status.yaml`
- `backlog_sprint_snapshot.tasks`: for each TASK in current sprint, record `status`, `complexity`, `branch`
- `git_state.current_branch`: from `git branch --show-current`
- `git_state.worktrees[]`: from `git worktree list`, for each: `path`, `branch`, `task` (from backlog), `last_commit` (HEAD hash), `clean` (from `git status`)

### Step 3 — Update Status

1. Update `status.yaml`:
   - `last_activity: pause`
   - `last_activity_timestamp: {now}`
   - `session_paused: true`
   - `pause_checkpoint: checkpoint-{YYYY-MM-DD-HHMM}.yaml`

### Step 3.5 — Coach End-of-Session Check (sustainability + engagement)

After the checkpoint is saved and status updated, the orchestrator invokes the **coach agent** with `moment: /gse:pause` (per coach.md Invocation contract, design §5.17). The coach activates axes 2–8 (workflow axes) to surface end-of-session observations — particularly the `sustainability` axis (detecting long session durations, sprint point totals vs spec §8 guidance) and the `engagement_pattern` axis (accepting defaults without pushback over the session). Coach outputs (bounded by `config.yaml → coach.max_advice_per_check`, default 3) are included in the pause report (Step 4). If nothing meaningful surfaces, this step is silent.

### Step 4 — Report

```
SESSION PAUSED
  Checkpoint: .gse/checkpoints/checkpoint-{YYYY-MM-DD-HHMM}.yaml
  Auto-committed: {N} worktree(s)
  Sprint: S{NN} ({current_phase})
  Active tasks: {count}
  
  Resume with: /gse:resume
```
