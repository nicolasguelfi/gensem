---
gse:
  id: PLN-001                          # inherited from .gse/plan.yaml (preserves P6 traceability)
  type: plan-summary
  sprint: 1                            # numeric sprint number
  status: done                         # always `done` — archived at delivery
  created: ""                          # ISO 8601 date (from plan.yaml.created)
  updated: ""                          # ISO 8601 date (snapshot timestamp)
  traces:
    derives_from: []                   # e.g., [TASK-001, TASK-002]
---

# Sprint {NN} — Plan Summary

**Goal:** _One-sentence sprint goal (from plan.yaml.goal)._
**Mode:** _full | lightweight_ | **Budget:** _{total}_ pts (_{consumed}_ consumed, _{remaining}_ remaining)
**Period:** _{plan.yaml.created} → {now}_

## Tasks

| TASK | Description | Complexity | Final Status |
|------|-------------|-----------|--------------|
|      |             |           |              |

_Generated from `backlog.yaml` sprint items._

## Activity Flow

| # | Activity | Completed | Notes |
|---|----------|-----------|-------|
|   |          |           |       |

_Generated from `plan.yaml.workflow.completed`._

**Skipped:** _list from `plan.yaml.workflow.skipped` with reasons._

## Scope Changes

_Generated from `plan.yaml.coherence.scope_changes` — each entry: timestamp, trigger, description, budget impact._

## Coherence

_Summary of alerts raised during the sprint (budget pressure, scope drift, velocity risk) and whether they were resolved._

## Outcome Metrics (calibration data)

_Filled by /gse:deliver Step 9.1 from state files at archive time. Consumed by
/gse:compound Axe 2 (calibration falsifiability review) and coach trend axes.
All values come from existing state — no extra collection ledger._

| Metric | Value | Formula / source |
|--------|-------|------------------|
| velocity_points          |  | complexity points consumed vs planned — `plan.yaml.budget` |
| findings_per_point       |  | total review findings ÷ points consumed — `review.md` Summary ÷ `plan.yaml.budget.consumed` |
| review_rounds            |  | occurrences of `/gse:review` in `plan.yaml.workflow.completed` |
| fix_rounds               |  | occurrences of `/gse:fix` in `plan.yaml.workflow.completed` |
| pushback_dismissed_at_close |  | `status.yaml → pushback_dismissed` at delivery (P16) |
| consecutive_acceptances_at_close |  | `status.yaml → consecutive_acceptances` at delivery (P16) |
| da_escalations           |  | devil-advocate escalations this sprint — *best-effort (session memory; may be empty — no deterministic ledger by design)* |

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
|      |           |           |

_Generated from `plan.yaml.risks`._

## Notes

This is a read-only archive artefact. The living sprint plan is `.gse/plan.yaml`. Use this summary for human reference, COMPOUND process deviation analysis, and sprint history.
