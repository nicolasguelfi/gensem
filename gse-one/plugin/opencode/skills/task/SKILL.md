---
name: task
description: "Execute a task outside standard lifecycle. Triggered by /gse:task."
---

# GSE-One Task — Ad-hoc Task

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| `<description>`    | Free-text description of the task to execute |
| `--type TYPE`      | Force artefact type (canonical enum per spec §P6 — Artefact ID allocation): `code` \| `requirement` \| `design` \| `test` \| `doc` \| `config` \| `import` \| `spike`. Default: inferred from description (see Step 1). |
| `--complexity N`   | Override complexity estimate (1-5) |
| `--no-review`      | Mark task as not requiring review (for trivial tasks) |
| `--spike`          | Create a spike (exploratory experiment). Complexity-boxed (max 3 points), non-deliverable, bypasses REQS/TESTS guardrails, must produce a DEC- |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state
2. `.gse/config.yaml` — git strategy, complexity budget
3. `.gse/backlog.yaml` — current sprint backlog (to add the task)
4. `.gse/profile.yaml` — user expertise level

## Workflow

### Step 0 — Sprint Freeze Check (Hard guardrail)

Before any other work, verify the current sprint is writeable. This preflight implements the **Sprint Freeze** invariant defined in the orchestrator and the spec.

1. Read `.gse/plan.yaml`. If absent (Micro mode or pre-v0.20 projects), **skip this step** — proceed to Step 1.
2. If `plan.yaml.status == active`, proceed to Step 1.
3. If `plan.yaml.status ∈ {completed, abandoned}`, the current sprint is **frozen**. Do NOT write anything to `backlog.yaml` or `status.yaml`. Present the Sprint Freeze Gate:

   > **Question:** The current sprint (S{NN}) plan status is `{completed|abandoned}` — it is frozen. New ad-hoc tasks cannot be added to a frozen sprint.
   >
   > **Options:**
   > 1. **Start next sprint now** (recommended, default) — I'll run the next-sprint opening sequence: in Lightweight mode `/gse:plan --strategic`; in Full mode `/gse:collect` > `/gse:assess` > `/gse:plan --strategic`. Once Sprint S{NN+1} is active, I'll execute your task there.
   > 2. **Cancel** — Abort this `/gse:task` invocation. No changes will be made.
   > 3. **Discuss** — Explore the trade-offs of opening a new sprint vs. cancelling.

4. On option 1:
   - Invoke the mode-appropriate opening sequence inline (read `config.yaml → lifecycle.mode` to decide).
   - After `/gse:plan --strategic` completes, re-read `.gse/status.yaml → current_sprint` (it now holds `{NN+1}`) and re-read `.gse/plan.yaml → status` (it now holds `active`).
   - Proceed to Step 1 in the new sprint context.
5. On option 2: stop execution. No state change.
6. On option 3: explain the Sprint Freeze invariant briefly (*"A delivered sprint is immutable — complementary work goes into a successor sprint, often named 'Sprint N+1 — Complementary tasks'."*), then re-present the Gate (options 1-3 only).

### Step 1 — Task Analysis

1. Parse the task description from `$ARGUMENTS`
2. Infer artefact type from description if `--type` not provided. The inferred value MUST belong to the canonical enum defined in spec §P6 — Artefact ID allocation: `code | requirement | design | test | doc | config | import | spike`. Note: the enum describes **the class of artefact produced by the TASK**, not the type of modification (no `feat`/`fix`/`refactor` — those describe git commit intent, not artefact class; a fix and a feature both produce the `code` artefact class).
   - `--spike` flag → `spike`
   - Keywords like "fix", "bug", "debug", "refactor", "clean", "reorganize", "add", "create", "implement", "update" → `code`
   - Keywords like "document", "readme", "comment", "write docs" → `doc`
   - Keywords like "test", "spec", "coverage", "write tests" → `test`
   - Keywords like "spike", "experiment", "try", "explore", "prototype" → `spike`
   - Keywords like "configure", "setup", "CI", "CD", "deploy config" → `config`
   - Keywords like "import", "migrate data", "ingest" → `import`
   - Keywords like "new requirement", "REQ-", "add feature spec" → `requirement`
   - Keywords like "architecture decision", "DES-", "design document" → `design`
   - Default: `code` (the majority case for ad-hoc TASKs that modify production code)
3. Estimate complexity (1-5) if `--complexity` not provided:
   - 1: trivial change (typo, config tweak)
   - 2: small change (single file, straightforward)
   - 3: medium change (multiple files, some design)
   - 4: large change (new feature, cross-cutting)
   - 5: complex change (architectural impact)

### Step 2 — Budget Check

1. Read current sprint complexity budget from `status.yaml`
2. Check if the task fits within remaining budget
3. If budget would be exceeded:
   - Report: "This task (complexity {N}) would exceed the sprint budget (remaining: {M})."
   - Present Gate:
     - **Proceed** — Accept budget overrun
     - **Reduce scope** — Discuss a simpler version
     - **Defer** — Add to pool for next sprint
     - **Discuss** — Explore alternatives

### Step 3 — Add to Backlog

Create a new TASK entry in `backlog.yaml`:

```yaml
- id: TASK-{next_id}
  title: "{description}"
  artefact_type: {inferred_type}
  complexity: {estimated}
  sprint: {current_NN}                # integer (not "S{NN}")
  status: planned
  priority: should                    # default — ad-hoc tasks rarely 'must'
  origin: ad-hoc                      # aligned with backlog.yaml template `origin` enum
  requires_review: {true unless --no-review or complexity <= 1}
  traces:
    derives_from: []
    implements: []
  git:
    branch: null
    branch_status: null
  github_issue: null
  created: {ISO-8601 timestamp}
  updated: {ISO-8601 timestamp}
```

**If `artefact_type: spike`:**
```yaml
- id: TASK-{next_id}
  title: "{description}"
  artefact_type: spike
  # Spike-specific fields (spec §12.3 artefact_type=spike extensions):
  question: "{the technical question to answer}"
  complexity_cap: {estimated, max 3}
  deliverable: false                  # cannot be merged to main
  outcome: pending                    # pending | yes | no | partial (after completion)
  complexity: {estimated}
  sprint: {current_NN}
  status: planned
  priority: should
  origin: ad-hoc
  requires_review: false
  traces:
    derives_from: []
  git:
    branch: null
    branch_status: null
  github_issue: null
  created: {ISO-8601 timestamp}
  updated: {ISO-8601 timestamp}
```

**Spike rules:**
1. **Complexity-boxed** — maximum 3 points. If estimated > 3, reject: "A spike must stay small (max 3 complexity points). Split into a smaller experiment or create a normal task."
2. **Non-deliverable** — the spike branch is deleted after completion. Code cannot be merged to main. If reusable code emerges, create a normal TASK to implement properly with REQS/TESTS.
3. **Must produce DEC-** — at completion, the agent creates a DEC- artefact documenting: the question, the approach tried, the answer (yes/no/partial), and next steps.
4. **Beginner Gate** — if `it_expertise: beginner`, present a Gate before starting: "This is an experiment — the code won't be kept. It's useful to test an idea before committing to it. Should I proceed?"
5. **Bypasses REQS/TESTS guardrails** — the spike does not need requirements or test strategy. The question IS the requirement; the experiment IS the test.

### Step 4 — Git Setup

Create a dedicated branch and worktree following the same logic as `/gse:produce` Step 2:

- Branch name: `gse/sprint-{NN}/task/{slug}`
- Worktree: `.worktrees/sprint-{NN}-task-{slug}`

The git strategy (worktree/branch-only/none) is read from `config.yaml`.

**Config Application Transparency (Inform, spec P7):** before creating the first branch or worktree of this ad-hoc task, emit a one-line Inform note labelling the applied `git.strategy` value and its origin (methodology default vs. user choice), using the same format as `/gse:produce` Step 2 Config Application Transparency block. Emit ONCE per task invocation — do not repeat if `/gse:task` was already invoked earlier in the same sprint (deduplicate via `status.yaml → last_activity` trail).

**Record activity start SHA** — after the branch/worktree is ready, run `git rev-parse HEAD` and save the result to `.gse/status.yaml → activity_start_sha`. This will be used in Step 5.5 (Scope Reconciliation) to compute the task's file-level contribution. Skip in Micro mode or `git.strategy: none` with empty history.

### Step 5 — Execute Task

1. Execute the work described in the task
2. Commit at logical checkpoints:
   ```
   gse(sprint-{NN}/task): {description}

   Sprint: S{NN}
   Task: TASK-{ID}
   Source: ad-hoc
   ```

### Step 5.5 — Scope Reconciliation (Creator-Activity Closure, spec P6)

Before Finalize, compare what was delivered to what was planned for this ad-hoc task. Deterministic, based on version-control history.

**Precondition:** `status.yaml → activity_start_sha` was recorded in Step 4. If missing (Micro mode, `git.strategy: none` with empty history, or session interrupted), skip this step with an Inform note.

For ad-hoc tasks, the "plan" is the task's own description in `backlog.yaml` (the TASK title, `artefact_type`, and any `Traces:` specified at creation). The reconciliation applies the same protocol as `/gse:produce` Step 4.5:

1. Enumerate changes: `git diff --name-status {activity_start_sha}..HEAD`.
2. Extract commit `Traces:` trailers via `git log --pretty=format:"%H%n%B%n---"`.
3. Build `planned_ids` from the task's own traces. If the task has no traces (common for spikes and quick fixes), `planned_ids = {TASK-{ID}}` and any file commit with `Task: TASK-{ID}` in the trailer is considered aligned.
4. Categorize deltas (ADDED out of scope / OMITTED / MODIFIED beyond plan / aligned).
5. If all aligned: skip the Gate silently, proceed to Step 6.
6. If any non-aligned delta exists, present the Scope Reconciliation table and Gate with the four options (Accept as deliberate / Revert / Amend / Discuss) per spec P6.
7. Clear `activity_start_sha` to empty string after reconciliation.

### Step 6 — Finalize

1. Update TASK in `backlog.yaml`:
   - `status: done`
   - `completed_at: {timestamp}`
2. Consume complexity budget: subtract task complexity from sprint remaining
3. Update `status.yaml`:
   - `last_activity: task`
   - `last_activity_timestamp: {now}`
   - `last_task: TASK-{ID}`
4. Review scheduling:
   - If `requires_review: true`: task will be included in next `/gse:review`
   - If `requires_review: false` (complexity <= 1 or `--no-review`): task is ready for delivery
5. Report task summary:
   - Task created and completed: TASK-{ID}
   - Complexity consumed: {N}
   - Remaining budget: {M}
   - Review required: {yes/no}

### Step 6.5 — Inform-Tier Decisions Summary (Creator-Activity Closure, spec P16)

Close the activity with a retrospective list of the Inform-tier decisions made during task execution (per P7 risk classification).

1. Assemble the list from conversation memory.
2. If empty: display *"No inform-tier decisions made this activity — all choices were Gated."* and proceed.
3. If non-empty, present the list and the Gate with three options: Accept all as-is (default, decisions appended to the task commit message body) / Promote one or more to Gate (walk through standard Gate for each, roll back inform-tier choice if a different option is picked) / Discuss.
