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

### Step 2 — Recovery Check (Unsaved Work Detection)

If `.gse/` exists, scan for unsaved work before proceeding:

1. **Check worktrees** — For each worktree listed in `config.yaml → git.worktree_dir` (default `.worktrees/`), run `git status`. Detect uncommitted changes.
2. **Check main working directory** — Run `git status` on the project root.
3. **If uncommitted changes are found:**
   - Report clearly: *"I found unsaved changes in N worktree(s). This usually means the previous session ended without `/gse:pause`."*
   - List each worktree with changes (branch name, number of modified files)
   - Present Gate decision:
     - **Recover** (default) — Auto-commit changes with message `gse(recovery): checkpoint — unsaved work from previous session`
     - **Review first** — Show the diff before committing
     - **Discard** — Discard uncommitted changes (confirm twice — destructive)
     - **Skip** — Continue without committing (changes remain uncommitted)
4. **If no uncommitted changes** — Proceed silently (no message).

### Step 3 — Determine Next Action (Decision Tree)

Read `status.yaml` fields: `current_sprint`, `lifecycle_phase`, `last_activity`, `last_activity_timestamp`.

| Current State | Proposed Action |
|---------------|-----------------|
| No sprint defined | If `it_expertise: beginner` and new project: start Intent-First mode (Step 7). Otherwise: start LC01 — run sequence: `/gse:collect` > `/gse:assess` > `/gse:plan --strategic` |
| Plan exists, not approved | Resume PLAN — present plan summary, ask for approval Gate |
| Tasks with status `in-progress` | Resume PRODUCE — show current task, propose continuation |
| All sprint tasks `done`, no review | Start REVIEW — propose `/gse:review` |
| Review done, fixes pending | Start FIX — propose `/gse:fix` |
| All tasks delivered, no compound | Start LC03 — propose `/gse:compound` |
| Compound done | Propose next sprint — increment sprint number, transition to LC01 (`COLLECT` > `ASSESS` > `PLAN`) |

Present the proposal and wait for user confirmation before executing.

### Step 4 — Stale Sprint Detection

Read `config.yaml → lifecycle.stale_sprint_sessions` (default: 3 sessions).

Track the number of sessions (invocations of `/gse:go` or `/gse:resume`) where no TASK has progressed to a new status. A "progression" is any TASK moving from one status to the next (open→planned, planned→in-progress, in-progress→done, etc.).

If the session-without-progress count reaches the configured threshold:

1. Report: "Sprint {NN} has had {N} sessions without progress."
2. Present Gate decision:
   - **Resume** — Continue where we left off (default)
   - **Partial delivery** — Deliver completed tasks, move remaining to pool
   - **Discard** — Abandon sprint, return all tasks to pool
   - **Discuss** — Explain the situation and help decide

### Step 5 — Failure Handling

If the last activity ended with an error or incomplete state:

1. Create a checkpoint of current state
2. Report what failed and why (if determinable)
3. Present Gate decision:
   - **Retry** — Re-attempt the failed activity
   - **Skip** — Mark as skipped, proceed to next activity
   - **Pause** — Save state and stop (user will return later)
   - **Discuss** — Explore alternatives

### Step 6 — Lightweight Mode Detection

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

### Step 7 — Intent-First Mode (Beginner + New Project)

When `profile.it_expertise` is `beginner` and no sprint has been defined yet (first time through LC01), the orchestrator enters a conversational mode to clarify the user's intent before starting the formal lifecycle:

1. **Elicit intent** — Ask in simple terms:
   *"Describe in a few sentences what you'd like to build or achieve."*
   Let the user express freely. Do not ask for technical details.

2. **Reformulate and validate** — Translate the intent into a structured summary using the user's vocabulary (no jargon):
   *"If I understand correctly, you want: [bulleted list in plain language]. Is that right?"*
   Iterate until the user confirms.

3. **Translate to backlog** — Convert the validated intent into initial TASK items in `backlog.yaml`. Present them as concrete goals, not technical work items:
   *"Here's what we'll work on: [list of goals]. I'll guide you through each step."*

4. **Transition to LC01** — Enter the normal lifecycle (`COLLECT` > `ASSESS` > `PLAN`), but present each activity in plain language:
   - COLLECT → *"Let me look at what we have to work with"*
   - ASSESS → *"Let me figure out what's missing"*
   - PLAN → *"Let me organize the work into manageable steps"*
   - REQS → *"Let me write down exactly what the application should do"*
   - PRODUCE → *"Now I'll build it"*
   - REVIEW → *"Let me check my own work for mistakes"*
   - DELIVER → *"Let me finalize and package the result"*

5. **Exit condition** — The user can say *"I know the process, let's skip ahead"* at any point. The agent switches to normal orchestration immediately and updates the profile: `it_expertise: intermediate`.

### Step 8 — Adopt Mode (`--adopt`)

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
