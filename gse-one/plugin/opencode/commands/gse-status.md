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
Health:  {health.score}/10
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

Status symbols (full 9-value lifecycle, per `backlog.yaml` — the authoritative schema):
- `open` — in the backlog pool, not part of a sprint
- `planned` — in the sprint, not started
- `in-progress` — actively being worked on
- `review` — produced, awaiting `/gse:review`
- `reviewed` — reviewed clean (no HIGH/MEDIUM findings) — ready to merge
- `fixing` — FIX in progress on review findings
- `done` — reviewed + fixed (FIX applied) — ready to merge
- `delivered` — merged by `/gse:deliver`
- `deferred` — pushed to a later sprint

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

### Step 6.5 — Open Items (pedagogical visibility)

Synthesize the project's **unresolved state** from sources that are already present. The goal is to answer two recurring user questions in one place: *"what's still open?"* and *"did I fix that issue?"* — observed verbatim in cross-session feedback. Display only the sections that contain at least one entry.

```
OPEN ITEMS
  Review findings unresolved
    docs/sprints/sprint-{NN}/review.md
      • RVW-{NNN} [HIGH]   {short title}   age: {N} day(s)
      • RVW-{NNN} [MEDIUM] {short title}   age: {N} day(s)

  TASKs not at a terminal status (in-progress / review / fixing / planned)
      • TASK-{NNN}  {status}    {short title}    sprint: S{NN}

  Open Questions awaiting resolution
    docs/intent.md and docs/sprints/sprint-{NN}/*.md
      • OQ-{NNN}  resolves_in: {PLAN|REQS|DESIGN}  {short text}

  Worktrees not aligned with current git state
      • {path}    {OK | CHANGED | DIRTY | MISSING | LOST}

  Hotfixes / patches applied since last DELIVER
    git log --since={last_deliver_timestamp} --grep='^fix:' --oneline
```

Sourcing rules (read-only, deterministic — no inference):
- **Findings**: parse `docs/sprints/sprint-{NN}/review.md` for RVW-NNN entries with `status` not in `{fixed, accepted-as-is, deferred}`.
- **TASKs**: filter `backlog.yaml` items where `status ∈ {planned, in-progress, review, fixing}` AND `sprint == current_sprint`.
- **Open Questions**: scan `## Open Questions` blocks in `docs/intent.md` and the current sprint's artefacts; report entries with `status: pending`.
- **Worktrees**: cross-reference `git worktree list` with `backlog.yaml` TASK branches (same logic as `--worktrees` flag, but summarised to one line per worktree).
- **Hotfixes since deliver**: list commit subjects from `main` since the last `v*` tag matching `gse(deliver):*`.

When all five sections are empty, display: `OPEN ITEMS — none. State is consistent.` This positive confirmation is itself pedagogically valuable: it tells the user there is nothing hidden in the corners.

This step is **purely a read of existing files** — it does not modify state, does not call other activities, and adds no Gate. It is the most reliable answer to *"where do I stand?"* and replaces ad-hoc "where are we?" exchanges with a single deterministic snapshot.

### Step 7 — Recommendations

Based on current state, suggest next actions:

- If tasks are in-progress: "Continue with `/gse:produce`"
- If tasks are in `review`: "Ready for `/gse:review`"
- If all tasks `done` or `reviewed`: "Ready for `/gse:deliver`"
- If stale sprint detected ({N} sessions without progress > `lifecycle.stale_sprint_sessions`): "Sprint has had {N} sessions without progress — consider `/gse:go`"
- If health score below 5/10: "Health is low — consider addressing {worst dimension}"
