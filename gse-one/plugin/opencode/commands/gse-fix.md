---
name: "gse-fix"
description: "Apply fixes from review findings in isolated branch. Triggered by /gse:fix."
---


# GSE-One Fix — Fix

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Fix all pending review findings for the current sprint |
| `--finding RVW-NNN` | Fix a specific finding |
| `--severity HIGH`  | Fix only findings at or above the given severity |
| `--task TASK-ID`   | Fix all findings for a specific task |
| `--dry-run`        | Show fix plan without executing |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state
2. `.gse/config.yaml` — git strategy (worktree/branch-only/none)
3. `.gse/backlog.yaml` — tasks with review findings
4. `docs/sprints/sprint-{NN}/review.md` — review findings (RVW-NNN entries)
5. `.gse/profile.yaml` — user profile (apply P9 Adaptive Communication to all output)

## Workflow

### Step 0 — Sprint Freeze Check (Hard guardrail)

Before applying any fix, verify the current sprint is writeable. This preflight implements the **Sprint Freeze** invariant defined in the orchestrator and the spec.

1. Read `.gse/plan.yaml`. If absent (Micro mode or pre-v0.20 projects), **skip this step** — proceed to Step 1.
2. If `plan.yaml.status == active`, proceed to Step 1.
3. If `plan.yaml.status ∈ {completed, abandoned}`, the current sprint is **frozen**. Do NOT transition any TASK forward and do NOT write to `backlog.yaml`. Present the Sprint Freeze Gate:

   > **Question:** The current sprint (S{NN}) plan status is `{completed|abandoned}` — it is frozen. Fixes cannot be applied to a frozen sprint.
   >
   > **Options:**
   > 1. **Start next sprint now** (recommended, default) — I'll run the next-sprint opening sequence: in Lightweight mode `/gse:plan --strategic`; in Full mode `/gse:collect` > `/gse:assess` > `/gse:plan --strategic`. Once Sprint S{NN+1} is active, I'll carry the fix there.
   > 2. **Cancel** — Abort this `/gse:fix` invocation. No changes will be made.
   > 3. **Discuss** — Explore the trade-offs.

4. On option 1: invoke the mode-appropriate opening sequence inline; after promotion, re-read `.gse/status.yaml → current_sprint` and proceed to Step 1 in the new sprint context.
5. On option 2: stop execution.
6. On option 3: explain the Sprint Freeze invariant, then re-present the Gate.

### Step 1 — Identify Findings to Fix

1. Read `docs/sprints/sprint-{NN}/review.md` for all RVW-NNN findings
2. Filter by arguments (severity, task, specific finding)
3. Sort by severity (HIGH first), then by task
4. **Verify TASK status** — Each TASK with findings should have `status: fixing` (set by REVIEW). If a TASK still has `status: review` (REVIEW not yet run) or `status: reviewed` (clean first-pass but user invokes `/gse:fix --severity LOW` to address non-blocking findings), set it to `fixing` now.
5. Present fix plan: list of findings to address with estimated effort
6. Wait for user confirmation (Gate)

### Step 2 — Git Setup (Per Task)

Group findings by their originating task/branch. For each group:

#### Strategy: `worktree`

1. Create fix branch from the reviewed feature branch:
   ```
   git branch gse/sprint-{NN}/fix/rvw-{ID} gse/sprint-{NN}/{type}/{name}
   ```
2. Create worktree for the fix branch:
   ```
   git worktree add .worktrees/sprint-{NN}-fix-rvw-{ID} gse/sprint-{NN}/fix/rvw-{ID}
   ```
3. All fix operations happen inside the fix worktree directory

#### Strategy: `branch-only`

1. Create fix branch from the reviewed feature branch:
   ```
   git branch gse/sprint-{NN}/fix/rvw-{ID} gse/sprint-{NN}/{type}/{name}
   git checkout gse/sprint-{NN}/fix/rvw-{ID}
   ```

#### Strategy: `none`

1. Fix in-place on the current branch

### Step 3 — Apply Fixes (Root-Cause Discipline)

For each finding (RVW-NNN), apply the **Root-Cause Discipline** protocol (spec P16 "Root-Cause Discipline before patching") BEFORE modifying any file. This protects against unsystematic debugging — applying speculative patches in rapid succession without first identifying the actual root cause.

#### 3.1 Read — open the file(s) in the current turn

1. Read the finding details: location (file, line), description, suggestion.
2. Open the relevant source file(s) via the Read tool **in the current turn**. A patch on code the agent has not just read is forbidden. If the file is already read from a previous turn, re-read it (state may have evolved).

#### 3.2 Symptom — state the defect in observable terms

3. Re-state the defect using specific, observable terms (e.g., *"the toggle button's background color does not change when clicked"* — not *"the toggle does not work"*). For RVW findings, the finding description usually suffices. For user-reported bugs arriving outside the review cycle, request one concrete observable fact if the report is vague (console error, screenshot, specific interaction).

#### 3.3 Hypothesis + Evidence test

4. Write in the chat:
   - **Hypothesis:** the hypothesized root cause of the symptom.
   - **Evidence test:** a concrete test that would validate or invalidate the hypothesis (command to run, file to inspect, unit test to execute, or user action to perform).
   - **Confidence:** P15 tag (Verified / High / Moderate / Low).
5. Run the evidence test (execute the command, inspect the file, request the user to perform the action).
6. Evaluate the result:
   - **Confirms the hypothesis** → proceed to 3.4.
   - **Contradicts the hypothesis** → return to 3.3 with a new hypothesis. Do NOT patch.

#### 3.4 Patch — only after evidence confirms

7. Apply the fix according to the finding's suggestion (or the hypothesis-informed fix for ad-hoc bugs).
8. Commit with traceability — the trailer MUST include `Root cause:` and `Evidence:` lines:
   ```
   gse(sprint-{NN}/fix): fix RVW-{NNN} — {short description}

   Sprint: S{NN}
   Traces: RVW-{NNN}
   Finding: {finding summary}
   Root cause: {one-line summary of the confirmed root cause}
   Evidence: {what confirmed the hypothesis — command output, test result, etc.}
   ```
9. Verify the fix resolves the finding (re-run the relevant check if possible; ask the user if no automated check exists).

#### 3.5 Failed-patch counter and devil-advocate escalation

After applying a patch, if the symptom persists (user reports it again, or the evidence re-run still fails):

1. **Increment** `status.yaml → fix_attempts_on_current_symptom` by 1.
2. Read `profile.yaml → dimensions.it_expertise` to determine the threshold:
   - `beginner` → threshold = 2
   - `intermediate` → threshold = 3
   - `expert` → threshold = 4
3. **At threshold:** STOP patching. Spawn the **devil-advocate** sub-agent in *focused-review* mode with the following input:
   ```yaml
   mode: focused-review
   symptom: "<precise observable>"
   hypotheses_tried:
     - hypothesis: "<text>"
       evidence: "<result that contradicted>"
       confidence: <tag>
   patches_applied:
     - file: "<path>"
       summary: "<what was changed>"
       commit: "<hash>"
   files_under_suspicion:
     - "<path>"
   ```
4. The devil-advocate returns a list of findings. Display them to the user. **At least one finding MUST be addressed** (fixed, explicitly dismissed with a DEC-, or resolved via user input) before any further patch on this symptom is attempted.
5. **Reset** `fix_attempts_on_current_symptom` to 0 when:
   - The user confirms resolution ("it works now", "fixed", user moves on to a different topic).
   - The symptom explicitly changes (a different observable defect is reported).
   - A new sprint is promoted (`/gse:plan --strategic`).

### Step 4 — Merge Fix Back

#### Strategy: `worktree`

1. Merge fix branch into the original feature branch (fast-forward preferred):
   ```
   git checkout gse/sprint-{NN}/{type}/{name}
   git merge --ff-only gse/sprint-{NN}/fix/rvw-{ID}
   ```
   If fast-forward is not possible, use `--no-ff`.
2. Delete fix worktree:
   ```
   git worktree remove .worktrees/sprint-{NN}-fix-rvw-{ID}
   ```
3. Delete fix branch:
   ```
   git branch -d gse/sprint-{NN}/fix/rvw-{ID}
   ```

#### Strategy: `branch-only`

1. Merge fix branch into the original feature branch:
   ```
   git checkout gse/sprint-{NN}/{type}/{name}
   git merge --ff-only gse/sprint-{NN}/fix/rvw-{ID}
   git branch -d gse/sprint-{NN}/fix/rvw-{ID}
   ```

#### Strategy: `none`

1. Fixes are already applied in-place; no merge needed.

### Step 5 — Update Findings

Mark each fixed finding as resolved in `docs/sprints/sprint-{NN}/review.md`:
- `status: fixed`
- `fixed_by_commit: {hash}`

### Step 6 — Finalize

1. Update TASK in `backlog.yaml`:
   - `status: done` (ready to merge)
   - `review_findings_fixed: {count}`
2. Update `status.yaml`:
   - `last_activity: fix`
   - `last_activity_timestamp: {now}`
3. Report fix summary:
   - Findings fixed: {count}
   - Findings remaining: {count}
   - If all findings resolved: recommend `/gse:deliver`
   - If HIGH findings remain: recommend another `/gse:fix` pass
