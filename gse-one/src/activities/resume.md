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

### Step 0 — Verify Pause State

Read `status.yaml → session_paused` and `status.yaml → pause_checkpoint` to confirm the project is in a coherent paused state before searching for a checkpoint to load. This step closes the read-side gap of the `pause.md` ↔ `resume.md` state symmetry: pause Step 3 writes `session_paused: true` + `pause_checkpoint: checkpoint-{...}.yaml` and resume Step 6 clears them, but until v0.62.2 these two fields were write-only — never consulted to drive resume behavior.

**Skip conditions:**
- If `--list` is specified, skip this step entirely (read-only listing has no state to validate).
- If `--checkpoint FILE` is specified, this step still runs but only emits an informational note on inconsistency — it does not block the explicit override.

Three coherence cases:

1. **Coherent paused state** — `session_paused: true` AND `pause_checkpoint` is non-empty AND the file `.gse/checkpoints/{pause_checkpoint}` exists on disk.
   - Use `pause_checkpoint` as the default checkpoint for Step 1 (overrides the "latest by filename" search).
   - Proceed silently.

2. **Inconsistent paused state** — `session_paused: true` BUT `pause_checkpoint` is empty OR the named file is missing on disk.
   - Report:
     ```
     Status marked as paused, but the named checkpoint cannot be located.
       pause_checkpoint: "{value or '(empty)'}"
       .gse/checkpoints/ contains: {N} file(s)
     ```
   - Present Gate decision:
     - **Use latest** (default if any checkpoint exists) — Continue with the most recent checkpoint by filename.
     - **Repair status** — Reset `session_paused: false` and `pause_checkpoint: ""` in `status.yaml`, then suggest `/gse:go`.
     - **Discuss** — Investigate the divergence with the user.

3. **Not paused** — `session_paused: false` (or absent for pre-v0.47.8 projects).
   - Report:
     ```
     No active pause detected (status.yaml.session_paused = false).
       Last activity: {last_activity} at {last_activity_timestamp}
       Available checkpoints: {N}
     ```
   - Present Gate decision:
     - **Run /gse:go instead** (default) — Switch to normal orchestration; resume is not the right command here.
     - **Force resume from latest** — Override and resume anyway (rare: e.g., recovery from manual state corruption).
     - **Discuss** — Investigate.

### Step 1 — Load Checkpoint

1. If `--list` is specified:
   - List all files in `.gse/checkpoints/` sorted by date (newest first)
   - Display: timestamp, status_snapshot.current_sprint, status_snapshot.current_phase, note (if any)
   - Exit

2. If `--checkpoint FILE` is specified:
   - Load the specified checkpoint file
3. Otherwise:
   - Use the `pause_checkpoint` confirmed by Step 0 case 1 if a coherent paused state was detected.
   - Otherwise (Step 0 case 2 "Use latest" or case 3 "Force resume from latest"), find the latest checkpoint in `.gse/checkpoints/` (sorted by filename, newest first).
   - If no checkpoints exist: report "No checkpoint found. Use `/gse:go` to start." and exit.

4. Read the checkpoint YAML and extract: `git_state.worktrees`, `status_snapshot`, `backlog_sprint_snapshot`, `last_task`, `note`

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
  Sprint: S{NN} ({current_phase})
  Last activity: {last_activity}
  Last task: TASK-{ID} ({task_title})
```

Open the briefing with the session context: *"You paused while working on {last_task}."* (skip if `last_task` is empty).

If a note was attached to the checkpoint:
```
  Note: "{note text}"
```

Sprint progress:
```
  Tasks: {done}/{total} complete
  Budget: {used}/{total} complexity points
  Health: {health.score}/10
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
2. **Fallback — `status_snapshot.last_activity`** if `plan.yaml` is absent (Micro mode or pre-v0.20 projects). Use the table below.

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

1. Update `status.yaml` **session state only**:
   - `session_paused: false`
   - Reset `pause_checkpoint: ""` (empty string — preserves schema stability vs dropping the field; readers get a well-defined absence representation)
   - **Update `sessions_without_progress`** — compare current `backlog.yaml` TASK statuses against `status.yaml → task_status_snapshot` (map TASK-id → status written at the end of this step; treat an absent or empty snapshot as "first session" → reset to 0). If no TASK status has changed since the last session → increment `sessions_without_progress` by 1; if at least one has changed → reset to 0. Then refresh the snapshot: write the current map of `{TASK-id: status}` to `status.yaml → task_status_snapshot`. This drives the stale-sprint Gate (see `/gse:go` Step 4 — Stale Sprint Detection) and the coach `mid_sprint_stall` event trigger (feeds axes 3-4 — sprint velocity, workflow health; activates at `>= 2`).
   - **Integrity-counter backstop** — run `python3 "$(cat ~/.gse-one)/tools/counters.py" health`; if `"stale": true`, emit the same Inform note as `/gse:go` Step 4 — Stale Sprint Detection (P16 integrity counters unmoved across ≥ 5 transitions — re-check spec §P16 counting obligations).
   - *(Cursor fields `last_activity`, `last_activity_timestamp` are maintained centrally by the orchestrator after the activity closes — see `plugin/agents/gse-orchestrator.md` — section "Sprint Plan Maintenance", and `gse-one-implementation-design.md` §10.1 — Sprint Plan Lifecycle (v0.53.0). RESUME writes no cursor fields directly.)*
2. The session is now active. Proceed with the accepted action or wait for user command.
