---
gse:
  type: plan
  sprint: 1                            # numeric sprint number
  branch: gse/sprint-01                # sprint branch
  traces:
    derives_from: []                   # e.g., [TASK-001, TASK-002]
  status: draft                        # draft | reviewed | approved
  created: ""                          # ISO 8601 date
  updated: ""                          # ISO 8601 date
---

# Sprint Plan — {sprint}

## Goal

_One-sentence sprint goal describing the value delivered._

## Scope

### Included Items

| Item ID  | Title                    | Type    | Priority | Complexity |
|----------|--------------------------|---------|----------|------------|
|          |                          |         |          |            |

### Complexity Budget

| Metric     | Value |
|------------|-------|
| Budget     |       |
| Allocated  |       |
| Remaining  |       |

### Excluded / Deferred

_Items considered but not included in this sprint, with reasons._

## Phase Plan

| Phase    | Key Activities                          | Deliverables                |
|----------|-----------------------------------------|-----------------------------|
| reqs     |                                         | reqs.md                     |
| design   |                                         | design.md                   |
| produce  |                                         | Source code, tests          |
| tests    |                                         | test-campaign.md            |
| review   |                                         | review.md                   |
| compound |                                         | compound.md                 |

## Risks

| Risk                        | Likelihood | Impact | Mitigation                  |
|-----------------------------|------------|--------|-----------------------------|
|                             |            |        |                             |

## Dependencies

_External dependencies, blockers, or prerequisites._

## Definition of Done

- [ ] All requirements have acceptance criteria met
- [ ] All tests pass with target coverage
- [ ] Review findings addressed (no CRITICAL remaining)
- [ ] Documentation updated
- [ ] Health score above minimum threshold
