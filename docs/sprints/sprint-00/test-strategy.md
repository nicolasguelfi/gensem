---
gse:
  type: test
  sprint: 0
  branch: main
  status: draft
  created: "2026-04-17"
  updated: "2026-04-17"
  traces:
    derives_from: [TASK-0003, TASK-0004]
    implements: [REQ-2, REQ-3, REQ-4, REQ-5]
    tested_by: []
    decided_by: []
---

## TEST STRATEGY (Sprint 0) — generator + dashboard verification

### Goals
- Catch regressions in `gse-one/gse_generate.py` output generation.
- Ensure dashboard generation runs successfully and produces a valid artifact.
- Make verification fast and repeatable locally and in CI.

### Test levels
#### 1) Unit-level (light)
- Pure functions/helpers (only if they exist and are easy to isolate).
- Keep minimal for now; focus is on behavior-level checks.

#### 2) Behavior / integration (primary)
- Run generator as a subprocess (or imported entrypoint if stable) in a temp directory.
- Assert key outputs exist and are non-empty (not a full tree diff).

#### 3) Smoke checks
- Run dashboard generation and assert output exists + non-empty.

### Tooling
- **Runner**: `pytest`
- **Temp dirs**: `tmp_path` fixture
- **Subprocess**: `subprocess.run(..., check=False)` with explicit assertions on `returncode` and stderr/stdout

### What we assert (minimum set)
#### Generator
- Exit code is 0
- Output directory tree exists (generated `plugin/` or equivalent)
- Representative files exist + are non-empty:
  - one manifest (Cursor/Claude) file
  - at least one generated skill file
  - at least one generated template file

#### Dashboard
- Exit code is 0
- Output HTML exists and is non-empty

### Evidence
- Local: `pytest -q` output is sufficient for sprint 0.
- CI: store test output via job logs (no artifacts required initially).

### Non-goals (to avoid brittleness)
- Full snapshot/golden diffs of generated directories
- Verifying exact formatting/whitespace of generated files

