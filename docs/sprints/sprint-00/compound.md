---
gse:
  type: decision
  sprint: 0
  branch: main
  status: draft
  created: "2026-04-17"
  updated: "2026-04-17"
  traces:
    derives_from: [TASK-0002, TASK-0003, TASK-0004]
    implements: []
    tested_by: []
    decided_by: []
---

## COMPOUND (Sprint 0) — learnings + improvements

### Axe 1 — Project / codebase
**What went well**
- Added a repeatable local workflow: venv + `requirements-dev.txt` + `pytest -q`.
- Added smoke tests that validate the two highest-risk scripts (generator + dashboard).
- CI now runs tests on PRs across OS (Windows + Ubuntu).

**What to improve next**
- Consider stabilizing dev dependencies to reduce CI drift (pin `pytest` or add constraints).
- Consider extending CI to macOS if/when macOS support becomes a requirement.

### Axe 2 — Methodology (GSE-One process)
**What worked**
- The artefact chain was clear: REQS → DESIGN → TEST STRATEGY → tests → evidence → review.
- Writing test evidence into `docs/sprints/sprint-00/test-reports/` made “done” measurable.

**Process improvements**
- Ensure the review step explicitly closes (or re-scopes) any cross-platform claims early (REQ-1 macOS scope needed tightening).

### Axe 3 — Learning / team habits
**Key takeaways**
- On Windows, Python may ship without pip; `python -m ensurepip --upgrade` is a necessary bootstrap step in some environments.
- Smoke tests should align fixtures with the actual parser expectations (dashboard test YAML needed alignment).

**Next sprint candidate tasks**
- Add a short troubleshooting section (“pip missing”, “venv activation”, common Windows issues).
- Optional: add a constraints/lock file for CI stability.

