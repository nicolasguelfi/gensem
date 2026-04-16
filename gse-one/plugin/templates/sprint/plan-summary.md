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
**Mode:** _full | lightweight | micro_ | **Budget:** _{total}_ pts (_{consumed}_ consumed, _{remaining}_ remaining)
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

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
|      |           |           |

_Generated from `plan.yaml.risks`._

## Notes

This is a read-only archive artefact. The living sprint plan is `.gse/plan.yaml`. Use this summary for human reference, COMPOUND process deviation analysis, and sprint history.
