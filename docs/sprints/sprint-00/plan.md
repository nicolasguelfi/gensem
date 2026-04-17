---
gse:
  type: decision
  sprint: 0
  branch: main
  status: draft
  created: "2026-04-17"
  updated: "2026-04-17"
  traces:
    derives_from: [TASK-0001, TASK-0002, TASK-0003, TASK-0004]
    implements: []
    tested_by: []
    decided_by: []
---

## PLAN (Sprint 0) — gensem dev loop hardening

### Sprint goal
Make the repo easy to develop safely by adding a **repeatable environment**, **minimal tests**, and **CI verification** around the generator + dashboard.

### Scope (what we will do)
- **TASK-0002**: Add a Python dependency/packaging setup so contributors can run the tools consistently.
- **TASK-0003**: Add a small automated test suite covering the highest-risk paths (generator output + dashboard generation smoke test).
- **TASK-0004**: Add CI to run the checks automatically on PRs.

### Out of scope (this sprint)
- Major refactors of the generator or templates.
- Marketplace publishing / distribution changes.
- Deploy automation (Coolify/Hetzner).

### Order of execution
1) Environment/packaging (unblocks everything else)
2) Tests (define the “known good” baseline)
3) CI (locks in the baseline)

### Success checks (definition of done)
- A new contributor can run a single documented setup to execute:
  - generator verification
  - dashboard generation
  - tests locally
- CI runs automatically and fails on regressions.

### Budget (complexity points)
- Packaging/deps: 3
- Tests: 4
- CI: 3
Total: 10

