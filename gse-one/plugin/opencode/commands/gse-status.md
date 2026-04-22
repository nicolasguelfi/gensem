---
name: "gse-status"
description: "Show lifecycle status, sprint state, artefact inventory, health, git state. Triggered by /gse:status."
---


# GSE-One Status — Project Status

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Show full project status overview |
| `--branches`       | Show detailed git branch information |
| `--decisions`      | Show recent Gate decisions and their rationale |
| `--worktrees`      | Show detailed worktree status |
| `--compact`        | Show minimal one-line status |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state
2. `.gse/config.yaml` — project configuration
3. `.gse/backlog.yaml` — all tasks and their statuses
4. `.gse/profile.yaml` — user profile (for display preferences)

## Workflow

### Step 1 — Project Overview

Display high-level project state:

```
PROJECT: {project_name}
Sprint:  S{NN} ({current_phase})
Phase:   {current phase description}
Last:    {last_activity} on {last_activity_timestamp}
Health:  {overall_score}/10
```

### Step 2 — Sprint State

Display current sprint backlog summary:

```
SPRINT S{NN} — {sprint_goal}
Budget: {used}/{total} complexity points ({remaining} remaining)

| Task       | Type     | Status      | Complexity | Branch           |
|------------|----------|-------------|------------|------------------|
| TASK-{ID}  | {type}   | {status}    | {N}        | {branch or —}    |
```

Status symbols:
- `planned` — not started
- `in-progress` — actively being worked on
- `done` — completed, pending review
- `delivered` — merged and released

### Step 3 — Artefact Inventory

List all tracked artefacts with their status:

```
ARTEFACTS
| Type          | Count | Latest           |
|---------------|-------|------------------|
| Requirements  | {N}   | REQ-{last}       |
| Design        | {N}   | DES-{last}       |
| Code          | {N}   | {files changed}  |
| Tests         | {N}   | {pass/fail}      |
| Documentation | {N}   | {last updated}   |
```

### Step 4 — Pending Reviews

If any tasks have `status: review` (produced and awaiting `/gse:review`):

```
PENDING REVIEW
- TASK-{ID}: {title} (complexity: {N})
```

### Step 5 — Health Score

Display health dimensions as a compact dashboard:

```
HEALTH {overall}/10
  requirements_coverage:  {score}
  test_pass_rate:         {score}
  design_debt:            {score}
  review_findings:        {score}
  complexity_budget:      {score}
  traceability:           {score}
  git_hygiene:            {score}
  ai_integrity:           {score}
```

Flag any dimension below 5/10 with a warning marker.

### Step 6 — Git State

Display git-related information:

```
GIT
  Current branch:   {branch}
  Sprint branch:    gse/sprint-{NN}/integration

  Active worktrees:
    ✓ sprint-{NN}-feat-{name}    active    0 uncommitted   TASK-{ID}
    ◉ sprint-{NN}-feat-{name}    paused    3 uncommitted   TASK-{ID}
    ★ sprint-{NN}-fix-rvw-{ID}   ready     0 uncommitted   TASK-{ID}

  Merge queue:
    gse/sprint-{NN}/feat/{name}  reviewed  no conflicts    ready
    gse/sprint-{NN}/fix/rvw-{ID} reviewed  no conflicts    ready

  Stale branches: {none | list of branches not touched in >2 sprints}
  Main status: clean, tagged v{X.Y.Z}
```

#### `--branches` flag

If `--branches` is specified, show all `gse/*` branches with detailed information:

```
BRANCHES
  Active feature branches:
    gse/sprint-{NN}/{type}/{name} — TASK-{ID} ({status})
  
  Stale branches (not touched in >2 sprints):
    {branch} — last commit: {date} ({N} sprints ago)
```

#### `--worktrees` flag

If `--worktrees` is specified, show detailed worktree information:

```
WORKTREES
  .worktrees/sprint-{NN}-{type}-{name}
    Branch:     gse/sprint-{NN}/{type}/{name}
    Task:       TASK-{ID} ({title})
    Status:     {clean/uncommitted changes}
    Uncommitted: {N} files
```

Run `git worktree list` and cross-reference with `backlog.yaml` TASK entries.

#### `--decisions` flag

If `--decisions` is specified, show recent Gate decisions:

```
DECISIONS (last 10)
  {timestamp} | {activity} | {gate_type} | {choice} | {rationale}
```

### Step 7 — Recommendations

Based on current state, suggest next actions:

- If tasks are in-progress: "Continue with `/gse:produce`"
- If all tasks done: "Ready for `/gse:review`"
- If reviews complete: "Ready for `/gse:deliver`"
- If stale sprint detected ({N} sessions without progress > `lifecycle.stale_sprint_sessions`): "Sprint has had {N} sessions without progress — consider `/gse:go`"
- If health score below 5/10: "Health is low — consider addressing {worst dimension}"
