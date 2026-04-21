---
description: "Select backlog items for sprint, create/update sprint plan in `.gse/plan.yaml`. Cross-cutting — callable at any abstraction level."
---

# GSE-One Plan — Planning

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Default to `--strategic` if no sprint exists, `--tactical` otherwise |
| `--strategic`      | Sprint-level planning: select items from pool, create `.gse/plan.yaml` |
| `--tactical`       | Task-level planning: reorder, adjust scope, refine within active plan |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/backlog.yaml` — all work items (pool and sprint-assigned)
2. `.gse/status.yaml` — current sprint number and lifecycle state
3. `.gse/profile.yaml` — user preferences (decision involvement, preferred verbosity)
4. `.gse/config.yaml` — project configuration (complexity budget, GitHub settings)
5. `.gse/plan.yaml` — existing living plan for the current sprint (if any)

## Workflow

### Strategic Planning (`--strategic`)

Used to create a new sprint by selecting items from the backlog pool.

#### Step 0 — Open Questions Gate (activity-entry scan, spec P6)

Before selecting items or creating the plan, scan for pending Open Questions (`OQ-`) whose `resolves_in: PLAN`.

1. **Enumerate sources** — list `docs/intent.md` (always) and `docs/sprints/sprint-{NN}/*.md` for the current sprint if it exists.
2. **Parse `## Open Questions`** sections across those files. Extract entries where `status: pending` AND `resolves_in: PLAN`.
3. **If zero matches** → skip this step, proceed to Step 0.5.
4. **If ≥ 1 match** → enter the Open Questions Gate. Behavior depends on `profile.yaml → dimensions.decision_involvement`:

   - **`autonomous`**: the agent generates proposed answers using intent + project profile + GSE conventions. Low-impact questions (`impact: behavioral` | `cosmetic`) are applied as Inform-tier, resolutions recorded with `answered_by: agent`. High-impact questions (`impact: scope-shaping` | `architectural`) are escalated to a Gate for explicit user validation.

   - **`collaborative`** (default): per-question Gate — agent proposes answer + rationale + consequence horizons (P8). User validates or modifies. If ≥ 3 questions, batch by theme (e.g., *users & data / domain model / UX & output*) for readability. `answered_by: user` after confirmation.

   - **`supervised`**: each question is a neutral Gate — no pre-answer. User provides the answer directly. `answered_by: user`.

5. **Record resolutions** — for each resolved question:
   - Update the origin artefact's `## Open Questions` entry **in place**: set `status: resolved`, fill `resolved_at`, `resolved_in: PLAN`, `answer`, `answered_by`, `confidence` (P15 tag), `traces`.
   - If the resolution is substantial (`impact: scope-shaping` or `impact: architectural`), create a `DEC-NNN` in `.gse/decisions.md` with `traces.derives_from: [OQ-NNN]` and a short rationale.

6. **Scope-shaping propagation** — for any question resolved with `impact: scope-shaping`, refresh `backlog.yaml` task sizings affected by the resolution. If an assigned sprint exists and the change would push the plan over budget, raise a tactical replan notice (Inform-tier).

7. Proceed to Step 0.5 (Previous Sprint Analysis, if applicable), then Step 1 (Present Pool).

#### Step 0.5 — Previous Sprint Analysis (Sprint N+1 only)

If this is NOT the first sprint (`current_sprint > 1`):

1. **Velocity calibration** — Read the previous sprint's archive from `docs/sprints/sprint-{NN-1}/plan-summary.md`:
   - How many complexity points were planned vs delivered?
   - Use actual velocity to calibrate this sprint's budget (Inform tier)
   - Example: "Last sprint you planned 10 points and delivered 8. I recommend a budget of 8 for this sprint."

2. **Carryover detection** — Check `backlog.yaml` for tasks from the previous sprint with `status: deferred` or `status: in-progress`:
   - Present unfinished tasks: "These tasks were not completed in sprint {NN-1}. Include them in this sprint?"
   - Gate decision per task: Include / Return to pool / Discard / Discuss

#### Step 0.6 — Coach Sprint-Promotion Analysis (Sprint N+1 only)

After the raw velocity and carryover signals are collected, the orchestrator invokes the **coach agent** with `moment: sprint promotion (/gse:plan --strategic)` (per coach.md Invocation contract, design §5.17). The coach activates axes 3, 4, 5, and 8 (`sprint_velocity`, `workflow_health`, `quality_trends`, `sustainability`) to produce retrospective cross-sprint analysis. This complements the velocity calibration of Step 0.5 by drawing on the `workflow_observations[]` ledger (summarized entries from previous sprints) for deeper trend detection. Coach outputs (bounded by `config.yaml → coach.max_advice_per_check`, default 3) are surfaced as Inform-tier recommendations to the user before the pool is presented. If nothing meaningful surfaces, this step is silent.

#### Step 1 — Present Pool

Display all items in the pool (including any carryover from Step 0) with their metadata:

```
Backlog Pool — 8 items available
────────────────────────────────
  TASK-010 [code]        ◌  Add rate limiting middleware          complexity: ?
  TASK-011 [design]      ◌  Design notification system            complexity: ?
  TASK-012 [requirement] ◌  Define admin role permissions          complexity: ?
  TASK-013 [code]        ◌  Implement webhook handler              complexity: ?
  TASK-014 [test]        ◌  Write integration tests for auth       complexity: ?
  TASK-015 [doc]         ◌  Document API endpoints                 complexity: ?
  TASK-016 [code]        ◌  Add CSV export feature                 complexity: ?
  TASK-017 [design]      ◌  Design plugin architecture             complexity: ?
```

#### Step 2 — Complexity Assessment

For each candidate item, assess complexity on a 3-point scale:

| Level | Points | Meaning |
|-------|--------|---------|
| **S** (Small) | 1 | < 2 hours, well-understood, minimal risk |
| **M** (Medium) | 3 | 2-8 hours, some unknowns, moderate risk |
| **L** (Large) | 5 | > 8 hours, significant unknowns, high risk — consider splitting |

Present complexity estimates and ask for user validation (Gate).

#### Step 3 — Select Sprint Items

Based on user's decision involvement preference:
- **Autonomous**: Agent selects items up to the complexity budget, presents for approval
- **Collaborative**: Agent proposes a selection, user adjusts
- **Supervised**: User selects items, agent validates feasibility

#### Step 4 — Complexity Budget Check (Hard Guardrail)

Read `config.yaml` → `complexity.budget_per_sprint` (default: 10 points).

Compute total complexity of selected items:
- If total <= budget: proceed
- If total > budget: **Hard guardrail** —
  ```
  Sprint is over budget ({total}/{budget} points).
  1. Defer lower-priority items to next sprint (recommended)
  2. Split the sprint into two smaller ones
  3. Accept over-budget (increases defect risk, review will flag it)
  4. Discuss
  ```
  The agent MUST NOT silently proceed with an over-budget sprint.

#### Step 5 — Promote to Sprint

For each selected item:
1. Set `sprint: {next_sprint_number}`
2. Set `status: planned`
3. Set `complexity: <integer>` — complexity points from the P10 cost table (typically 1-6). For maintenance work (refactoring, tests, docs), use the Cost Assessment Grid for Maintenance Work (spec Appendix B) — values range from 0 (trivial) to 5 (structural impact). One point ≈ one pair-session hour (indicative anchor, see P10).

Increment sprint number in `status.yaml`.

**Initialize workflow.expected based on project mode:**

| Mode | workflow.expected |
|------|-------------------|
| **Full** | `[collect, assess, plan, reqs, design, preview, tests, produce, review, deliver]` |
| **Full (design skipped)** | `[collect, assess, plan, reqs, preview, tests, produce, review, deliver]` |
| **Lightweight** | `[plan, reqs, produce, deliver]` |
| **Micro** | (no plan.yaml is created in Micro mode) |

Conditional adjustments at PLAN-time:
- If `config.yaml → project.domain ∉ {web, mobile}`, move `preview` to `workflow.skipped` with reason `preview skipped — non-UI domain`. (PREVIEW stays in the baseline sequence per spec §14 but is explicitly skipped when not relevant.)
- `fix` is **not** in `workflow.expected` initially; it is inserted after `review` if review produces findings (recorded when review completes).

LC03 activities (`compound`, `integrate`) are tracked in `status.yaml`, not in this sprint's `plan.yaml`.

#### Step 6 — Git Integration

1. **Create sprint integration branch**: `gse/sprint-{NN}/integration` from `main`
2. **Assign branch names** to each task:

| Artefact Type | Branch Pattern |
|--------------|----------------|
| `code`       | `gse/sprint-{NN}/feat/{short-name}` |
| `test`       | `gse/sprint-{NN}/test/{short-name}` |
| `fix`        | `gse/sprint-{NN}/fix/{short-name}` |
| `design`     | `gse/sprint-{NN}/docs/{short-name}` |
| `doc`        | `gse/sprint-{NN}/docs/{short-name}` |
| `config`     | `gse/sprint-{NN}/chore/{short-name}` |

3. **Update TASK entries** in `backlog.yaml` with:
   ```yaml
   git:
     branch: "gse/sprint-02/feat/rate-limiting"
     branch_status: planned  # null | planned | active | merged | deleted
   ```

4. **Record branch name on each task** in `plan.yaml.tasks[].branch` for quick lookup during PRODUCE.

Note: Branches are NOT created yet — only named. They are created when production starts on each task.

#### Step 7 — Persist Plan

Initialize `.gse/plan.yaml` from the `plan.yaml` template (`plugin/templates/plan.yaml` — authoritative schema). Set the following fields from the planning session:

- `id`: next PLN-NNN artefact ID
- `sprint`: current sprint number (from `status.yaml.current_sprint`)
- `mode`: selected lifecycle mode
- `status`: `active` (set after user approval Gate)
- `goal`: user-provided sprint goal
- `tasks[]`: selected items with `id`, `order`, `complexity`, `branch` (from Step 6)
- `budget.total`: sum of selected task complexity (must not exceed `config.yaml complexity.budget_per_sprint`)
- `budget.consumed`: 0, `budget.remaining`: same as total
- `workflow.expected`: activity sequence for the mode (see §10.1 for per-mode lists)
- `workflow.completed`: pre-populate with COLLECT, ASSESS if already ran in LC01 + current PLAN
- `workflow.active`: `reqs` (next activity after PLAN in both Full and Lightweight)
- `workflow.pending`: remaining activities from expected minus completed minus active
- `workflow.skipped`: conditional skips (e.g., preview if not web/mobile)
- `coherence`: initialize with `last_evaluated: {now}`, empty `scope_changes` and `alerts`
- `risks[]`: optional, from user input during planning
- `created`, `updated`: current ISO 8601 timestamp

**workflow.completed initialization:**
- Pre-populate with COLLECT and ASSESS if LC01 already ran. Read their timestamps from `status.yaml.activity_history` filtered by `sprint == current_sprint` (authoritative source). If the history is empty or the entry is missing (e.g., migrated project), fall back to `status.yaml.last_activity_timestamp` for the last recorded activity and leave older entries with `completed_at: null`.
- Always append the current PLAN activity as completed.
- Reset `status.yaml.activity_history` to `[]` for the new sprint (the prior sprint's history is archived in the previous `plan-summary.md`).

**workflow.active:** Set to the next expected activity after PLAN — `reqs` in both Full and Lightweight modes. (Micro mode does not use `plan.yaml`.)

Present the plan for user approval (Gate). Set `status: active` once confirmed.

Also update `status.yaml` cursor fields:
- `last_activity: plan`
- `last_activity_timestamp: {now}`
- `current_sprint: {NN}`

### Tactical Planning (`--tactical`)

Used to adjust an existing sprint without changing its scope fundamentally. Operates on `.gse/plan.yaml`.

#### Step 1 — Show Current Sprint State

Read `.gse/plan.yaml` and display:
- Goal, mode, and budget (total / consumed / remaining)
- Tasks with their order, complexity, and current status (from `backlog.yaml`)
- Current workflow position: `active` activity, `pending` queue, `completed` history
- Active coherence alerts, if any

#### Step 2 — Available Actions

- **Reorder** — Change execution priority of planned items (`plan.yaml.tasks[].order`)
- **Split** — Break a large item into smaller sub-tasks (update both `backlog.yaml` and `plan.yaml.tasks`)
- **Defer** — Move an item back to pool (remove from `plan.yaml.tasks`, update `backlog.yaml`)
- **Add** — Pull an item from pool into the sprint (add to `plan.yaml.tasks`, with budget check)
- **Rename branch** — Update a task's `branch` field in both files

#### Step 3 — Apply Changes

Update `.gse/plan.yaml` (tasks, budget, `updated` timestamp) and `.gse/backlog.yaml` (TASK statuses).

If the change alters scope, append an entry to `plan.yaml.coherence.scope_changes`:

```yaml
scope_changes:
  - timestamp: "{iso8601}"
    trigger: tactical-replan
    description: "{what changed}"
    budget_impact: "{+/- N pts}"
```

Re-run the complexity budget check after any additions. If over budget, apply the Hard guardrail from Strategic Step 4.

### Notes

- `.gse/plan.yaml` is the **single source of truth** for sprint planning state. `backlog.yaml` remains the authority for TASK data.
- The orchestrator maintains `plan.yaml` (workflow, budget, coherence) at every activity transition — see the Plan Update Protocol in the orchestrator.
- At DELIVER, a read-only snapshot is archived to `docs/sprints/sprint-{NN}/plan-summary.md` and `plan.yaml.status` is set to `completed`.
