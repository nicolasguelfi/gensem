---
description: "Execute production plan in isolated worktree. Creates feature branch + worktree per task. Triggered by /gse:produce."
---

# GSE-One Produce — Production

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Execute next pending task from current sprint backlog |
| `--task TASK-ID`   | Execute a specific task by ID |
| `--all`            | Execute all pending tasks sequentially |
| `--dry-run`        | Show what would be produced without executing |
| `--skip-tests`     | Skip automatic test execution after production (**Gate guardrail** — requires confirmation, logged as DEC-, penalizes health score) |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state
2. `.gse/config.yaml` — project configuration, especially `git.strategy` (worktree/branch-only/none)
3. `.gse/backlog.yaml` — sprint tasks, their status, and assignment
4. `.gse/profile.yaml` — user expertise level (affects test generation behavior)
5. `docs/sprints/sprint-{NN}/reqs.md` — requirements for the current sprint (**mandatory**)
6. `docs/sprints/sprint-{NN}/test-strategy.md` — test strategy (**mandatory**)


## Workflow

### Step 0 — Pre-production Guardrails (Hard — cannot be skipped)

Before starting ANY task, verify these conditions. If any check fails, **STOP and do not proceed**.

1. **Requirements check** — Verify that `docs/sprints/sprint-{NN}/reqs.md` exists and contains at least one REQ- artefact traced to the TASK about to start. If missing: report "Requirements not defined for this task. I need to write down what the app should do first." Then run REQS.
2. **Test strategy check** — Verify that a test strategy exists (`docs/sprints/sprint-{NN}/test-strategy.md` or a `tests` section in `plan.md`). If missing: report "Test strategy not defined. I need to describe how we'll verify each feature works." Then run TESTS `--strategy`.
**Decision tier override:**
3. **Supervised mode** — If `profile.decision_involvement` is `supervised`, ALL technical choices in this TASK are escalated to **Gate-tier** decisions. This includes: library/dependency selection, data format, folder structure, persistence strategy, API design, naming conventions. The agent MUST present options and wait for user confirmation — it MUST NOT make these choices silently.

### Step 1 — Select Task

Read `backlog.yaml` and identify tasks for the current sprint with `status: planned` or `status: ready`.

If multiple tasks are pending:
1. Sort by priority (P1 > P2 > P3), then by dependency order
2. Present the next task to produce with summary: ID, title, artefact_type, estimated complexity
3. Wait for user confirmation (Gate) unless `--all` was specified

If no tasks are pending:
1. Report: "All tasks for sprint S{NN} are complete or in-progress."
2. Propose `/gse:review` if unreviewed tasks exist, otherwise `/gse:deliver`

### Step 2 — Git Setup (Before Production)

Read `config.yaml` field `git.strategy` and branch accordingly:

#### Strategy: `worktree` (default)

1. Determine the sprint branch name: `gse/sprint-{NN}`
2. Create feature branch from sprint branch:
   ```
   git branch gse/sprint-{NN}/{type}/{name} gse/sprint-{NN}
   ```
   Where `{type}` is the artefact type (feat, fix, doc, test, refactor) and `{name}` is a slug of the task title.
3. Create worktree for the feature branch:
   ```
   git worktree add .worktrees/sprint-{NN}-{type}-{name} gse/sprint-{NN}/{type}/{name}
   ```
4. Update the TASK in `backlog.yaml`:
   - `status: in-progress`
   - `git.branch: gse/sprint-{NN}/{type}/{name}`
   - `git.branch_status: active`
   - `git.worktree: .worktrees/sprint-{NN}-{type}-{name}`
   - `git.worktree_status: active`
5. All subsequent file operations happen inside the worktree directory.

#### Strategy: `branch-only`

1. Determine base branch:
   - If sprint branch `gse/sprint-{NN}` exists (full mode): branch from it.
   - If no sprint branch exists (Lightweight mode): branch from `main` directly.
2. Create feature branch:
   ```
   # Full mode:
   git branch gse/sprint-{NN}/{type}/{name} gse/sprint-{NN}
   git checkout gse/sprint-{NN}/{type}/{name}

   # Lightweight mode (no sprint branch):
   git branch gse/{type}/{name} main
   git checkout gse/{type}/{name}
   ```
3. Update the TASK in `backlog.yaml`:
   - `status: in-progress`
   - `git.branch: gse/sprint-{NN}/{type}/{name}` (full) or `gse/{type}/{name}` (lightweight)
   - `git.branch_status: active`

#### Strategy: `none`

1. Work directly on current branch (no branch creation).
2. Update the TASK in `backlog.yaml`:
   - `status: in-progress`

### Step 3 — Execute Production

Produce the artefact according to the task specification:

1. Read the task description and acceptance criteria from `backlog.yaml`
2. If the task references requirements (REQ-NNN), read them from the requirements artefact
3. If the task references design decisions (DES-NNN), read them from the design artefact
4. Execute the work, creating or modifying files as specified
5. **Pre-commit self-review (P16 — before every commit):**
   Before committing, the agent MUST run these 5 checks on the changes about to be committed:
   - **(a) Hallucination hunt** — verify that all referenced APIs, libraries, and functions actually exist in the versions used
   - **(b) Assumption check** — list any assumptions made during implementation; flag those not validated by a REQ-
   - **(c) Complaisance check** — does the code match exactly what was asked in the requirements? No extra features, no missing features?
   - **(d) Edge cases** — have boundary conditions been considered (empty input, max values, concurrent access, error states)?
   - **(e) Temporal validity** — are the dependency versions, API endpoints, and syntax current and not deprecated?
   If any check fails, fix before committing. If uncertain, flag as a finding for REVIEW.
6. Commit at logical checkpoints using the convention:
   ```
   gse(sprint-{NN}/{type}): description

   Sprint: {NN}
   Task: TASK-{ID}
   Traces: [REQ-NNN, DES-NNN] (if applicable)
   ```

### Step 4 — Test Execution (After Production)

**If `--skip-tests` was specified:**
1. Present a **Gate decision** (cannot be silently bypassed):
   - "Skipping tests means we won't verify this task works correctly. Are you sure?"
   - Options: **Skip tests** / **Run tests anyway** / **Discuss**
   - For beginners: "I'd normally check that what I built works correctly. Do you want me to skip that check? I don't recommend it."
2. If confirmed: record a DEC- artefact in the decision journal with rationale.
3. Decrement health score: `test_pass_rate` receives a penalty for the skipped task.
4. In `supervised` mode: require **double confirmation** ("This is unusual — please confirm again").

**If `--skip-tests` was NOT specified (normal flow):**

1. **Check if tests exist** for the produced artefact:
   - Look for test files matching the artefact (e.g., `test_*.py`, `*.test.ts`, `*_test.go`)
   - Check for a test configuration (`pytest.ini`, `jest.config.*`, etc.)

2. **If tests exist** — run them automatically:
   - Execute the test suite relevant to the changed artefact
   - Capture output as evidence
   - If tests **pass**: record in TASK `test_evidence: { status: pass, timestamp, summary }`
   - If tests **fail**:
     1. Report failure details
     2. Present Gate decision:
        - **Fix** — Attempt to fix the failing tests (default)
        - **Skip** — Mark tests as failing, continue
        - **Discuss** — Explore the failure with the user

3. **If no tests exist** and the artefact type warrants testing:
   - Read `profile.yaml` expertise level:
     - **beginner**: Auto-generate tests, inform user: "I've created tests for this task."
     - **intermediate**: Propose: "This task should have tests. Shall I generate them?"
     - **expert**: Propose with options: "No tests found. Options: generate unit tests / generate integration tests / skip / discuss"
   - If tests are generated, run them and capture evidence

4. **Generate campaign report**:
   - Summary: tests run, passed, failed, skipped
   - Coverage delta if measurable
   - Attach report to TASK in `backlog.yaml`: `test_campaign: { ... }`

### Step 5 — Finalize

1. Ensure all changes are committed (no uncommitted work in worktree)
2. Update TASK in `backlog.yaml`:
   - `status: done`
   - `completed_at: {timestamp}`
   - `git.uncommitted_changes: 0`
3. Update `status.yaml`:
   - `last_activity: produce`
   - `last_activity_timestamp: {now}`
   - `last_task: TASK-{ID}`
4. Update complexity budget: subtract task complexity from sprint remaining budget
5. Report production summary:
   - What was produced (files created/modified)
   - Test results
   - Remaining sprint budget
   - Next task suggestion (if any)
