---
description: "Detect project state, propose next activity. Triggered by /gse:go. Includes --adopt mode for existing projects."
---

# GSE-One Go — Orchestrate

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Detect current project state and propose the next activity |
| `--adopt`          | Adopt an existing project that was not created with GSE-One |
| `--status`         | Display current state without proposing an action |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state (if it exists)
2. `.gse/config.yaml` — project configuration (if it exists)
3. `.gse/backlog.yaml` — work items and their statuses (if it exists)
4. `.gse/profile.yaml` — user profile (if it exists)


## Workflow

### Step 1 — Detect Project State

Examine the working directory to classify the situation:

| Condition | State | Action |
|-----------|-------|--------|
| No `.gse/` directory AND project files exist | **Adopt candidate** | Transition to Adopt mode (Step 5) |
| No `.gse/` directory AND directory is empty/near-empty | **New project** | Transition to HUG (`/gse:hug`) |
| `.gse/` exists | **Existing project** | Read `status.yaml` and proceed to Step 2 |

### Step 2 — Determine Next Action (Decision Tree)

Read `status.yaml` fields: `current_sprint`, `lifecycle_phase`, `last_activity`, `last_activity_timestamp`.

| Current State | Proposed Action |
|---------------|-----------------|
| No sprint defined | Start LC01 — run sequence: `/gse:collect` > `/gse:assess` > `/gse:plan --strategic` |
| Plan exists, not approved | Resume PLAN — present plan summary, ask for approval Gate |
| Tasks with status `in-progress` | Resume PRODUCE — show current task, propose continuation |
| All sprint tasks `done`, no review | Start REVIEW — propose `/gse:review` |
| Review done, fixes pending | Start FIX — propose `/gse:fix` |
| All tasks delivered, no compound | Start LC03 — propose `/gse:compound` |
| Compound done | Propose next sprint — increment sprint number, transition to LC01 (`COLLECT` > `ASSESS` > `PLAN`) |

Present the proposal and wait for user confirmation before executing.

### Step 3 — Stale Sprint Detection

Read `config.yaml → lifecycle.stale_sprint_sessions` (default: 3 sessions).

Track the number of sessions (invocations of `/gse:go` or `/gse:resume`) where no TASK has progressed to a new status. A "progression" is any TASK moving from one status to the next (open→planned, planned→in-progress, in-progress→done, etc.).

If the session-without-progress count reaches the configured threshold:

1. Report: "Sprint {NN} has had {N} sessions without progress."
2. Present Gate decision:
   - **Resume** — Continue where we left off (default)
   - **Partial delivery** — Deliver completed tasks, move remaining to pool
   - **Discard** — Abandon sprint, return all tasks to pool
   - **Discuss** — Explain the situation and help decide

### Step 4 — Failure Handling

If the last activity ended with an error or incomplete state:

1. Create a checkpoint of current state
2. Report what failed and why (if determinable)
3. Present Gate decision:
   - **Retry** — Re-attempt the failed activity
   - **Skip** — Mark as skipped, proceed to next activity
   - **Pause** — Save state and stop (user will return later)
   - **Discuss** — Explore alternatives

### Step 5 — Lightweight Mode Detection

If `.gse/` does not exist AND the project has < 5 files:

1. Propose lightweight mode (Inform tier — user can override to full):
   "This is a small project. I recommend lightweight mode — reduced overhead while preserving traceability."
2. Operational restrictions in lightweight mode (spec Section 13.2):

| Aspect | Full Mode | Lightweight Mode |
|--------|-----------|-----------------|
| Lifecycle | LC01 > LC02 > LC03 | PLAN > PRODUCE > DELIVER |
| Git strategy | `worktree` (sprint + feature branches) | `branch-only` (single feature branch from main, no sprint branch) |
| Sprint artefacts | Full set (plan, reqs, design, tests, review, compound) | Plan only (inline in `.gse/status.yaml`, no separate file) |
| Health dashboard | 8 dimensions | 3 only (test_pass_rate, review_findings, git_hygiene) |
| Complexity budget | Tracked | Not tracked |
| Decision tiers | Full P7 assessment (Auto + Inform + Gate) | Simplified (Auto + Gate only, no Inform) |

3. User can upgrade to full mode anytime via `/gse:go` — the agent scaffolds the missing structure.
4. **Minimum viable project size:** For truly one-off tasks (single script, quick fix), using GSE-One adds more overhead than value. Suggest working without GSE-One and adopting later if the project grows.

### Step 6 — Adopt Mode (`--adopt`)

When adopting an existing project not created with GSE-One.

**Non-destructive guarantee:** The adopt flow NEVER modifies existing files without explicit user approval. It can be interrupted and resumed at any point.

1. **Detect** — Confirm project files exist, identify language/framework from manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.)
2. **Scan** — Run `/gse:collect` (internal mode) to inventory all existing artefacts
3. **Infer state** — Analyze git history to estimate:
   - How many sprints of work exist (commits, age, tags)
   - What was the last stable release (latest tag)
   - Are there lingering branches
   - Project domain from dependencies
   - Git strategy from existing branch patterns
   - Team context from git log (multiple committers?)
4. **Initialize** — Create `.gse/` directory with:
   - `config.yaml` — populated with inferred domain and git strategy
   - `status.yaml` — set to `current_sprint: 0`, `current_phase: LC01`
   - `backlog.yaml` — empty, ready for population
   - `profile.yaml` — trigger `/gse:hug` if no profile exists
5. **Set baseline** — Record current state as **sprint 0** — the starting point for the first GSE-managed sprint. Current `main` HEAD is the baseline.
6. **Propose annotation** (Gate decision):
   ```
   I found N existing artefacts. Add GSE-One traceability metadata?
   1. Yes, annotate all — add YAML frontmatter to existing .md files
   2. Annotate new artefacts only — leave existing files untouched
   3. Skip annotation entirely
   4. Discuss
   ```
7. **Transition** — Proceed to normal LC01 for sprint 1: `COLLECT` > `ASSESS` > `PLAN`
