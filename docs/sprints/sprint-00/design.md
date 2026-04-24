---
gse:
  type: design
  sprint: 0
  branch: main
  status: draft
  created: "2026-04-17"
  updated: "2026-04-17"
  traces:
    derives_from: [TASK-0002, TASK-0003, TASK-0004]
    implements: [REQ-1, REQ-2, REQ-3, REQ-4, REQ-5]
    tested_by: []
    decided_by: []
---

## DESIGN (Sprint 0) — concrete decisions

### Decision 1 — Test framework
**Choice**: `pytest` (plus `pytest-cov` optional later).

**Rationale**
- Minimal setup, cross-platform, good ergonomics for CLI/tooling repos.
- Plays well with subprocess-based “smoke” verification.

### Decision 2 — Dependency management (minimal)
**Choice**: `python -m venv .venv` + `requirements-dev.txt` at repo root.

**Rationale**
- Matches REQ-1 constraint: minimal standard tooling.
- Avoids introducing a packaging system as a first move (can upgrade later to `pyproject.toml` if needed).

### Decision 3 — Test + scripts layout
**Choice**
- `tests/` at repo root
- Add tiny helpers in `tests/_helpers.py` (if needed)
- Keep “golden” fixtures minimal and explicit under `tests/fixtures/`

**Rationale**
- Keeps tests discoverable and CI-simple.
- Avoids coupling tests to generated plugin outputs on disk.

### Decision 4 — What artifacts to assert (generator)
**Generator verification approach**
- Tests run the generator in an **isolated temporary directory**.
- Assertions verify:
  - the generator process exits successfully
  - expected output directories exist (e.g. a generated `plugin/` tree)
  - a representative set of files exist and are non-empty (e.g. manifests, at least one skill, one template)

**Avoid**
- Exact full-directory diffs (too brittle across minor formatting changes).

### Decision 5 — Dashboard smoke test
**Approach**
- Run `gse-one/plugin/tools/dashboard.py` against a minimal, temporary project state (fixture directory) or by pointing it at repo-local state if it supports it safely.
- Assert: command exits 0 and output HTML exists and is non-empty.

### Decision 6 — CI provider + matrix
**Choice**: GitHub Actions

**Workflow**
- Trigger: `pull_request` and `push` to `main`
- Matrix: Python 3.10, 3.11, 3.12 (can prune if needed)
- Steps:
  - checkout
  - setup-python
  - install dev deps (`pip install -r requirements-dev.txt`)
  - run tests (`pytest -q`)

### Decision 7 — “Verify” commands (developer ergonomics)
We will standardize and document:
- Setup: create venv + install dev deps
- Verify: run tests (which include generator + dashboard smoke checks)

This directly satisfies REQ-5: “how to verify” is a single section with exact commands.

