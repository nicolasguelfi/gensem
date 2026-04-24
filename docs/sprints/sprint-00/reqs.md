---
gse:
  type: requirement
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

## REQS (Sprint 0) — gensem dev loop hardening

### REQ-1 Repeatable Python environment (TASK-0002)
The repository provides a clear, repeatable way to install and run the Python tools used for development (generator + dashboard).

**Acceptance criteria**
- Given a fresh clone on Windows, when I follow the documented setup steps, then I can run the generator and the dashboard tool without import/module errors.
- Given a fresh clone on Linux, when I follow the documented setup steps, then I can run the generator and the dashboard tool without import/module errors.
- Given I run the documented “verify” command(s), when dependencies are missing, then the failure message indicates what to install and how.

**Non-requirement**
- macOS support is not required for sprint 0.

**Notes / constraints**
- This sprint should prefer minimal, standard tooling (e.g., `venv` + a single dependency file) over introducing complex build systems.

### REQ-2 Generator verification tests (TASK-0003)
The repository includes automated tests that detect regressions in the generator’s core behavior.

**Acceptance criteria**
- Given a clean working directory, when I run the tests locally, then they complete successfully.
- Given the generator is run in a test context, when it generates outputs, then the test suite verifies at least:
  - generated directories exist where expected
  - a small, representative set of generated files are non-empty
  - the generator completes without raising exceptions
- Given the generator behavior changes in a way that breaks expected outputs (e.g., missing a required generated file), when I run tests, then at least one test fails with a clear assertion message.

### REQ-3 Dashboard smoke test (TASK-0003)
The repository includes an automated check that dashboard generation runs successfully.

**Acceptance criteria**
- Given a clean working directory, when I run the dashboard generation command used in development, then it completes without errors.
- Given dashboard generation completes, then the produced HTML file exists and is non-empty (or another explicit artifact is verified).

### REQ-4 Continuous Integration gate (TASK-0004)
The repository runs the verification checks automatically in CI for pull requests.

**Acceptance criteria**
- Given a pull request targeting `main`, when CI runs, then it executes:
  - environment/setup step(s)
  - tests (including generator verification + dashboard smoke test)
- Given a regression in generator behavior, when CI runs on the PR, then CI fails and blocks merging.
- Given only documentation changes, when CI runs, then it still completes successfully (or skips heavy steps explicitly and deterministically).

### REQ-5 Developer ergonomics (cross-cutting)
The dev loop is discoverable and fast enough for iteration.

**Acceptance criteria**
- Given a contributor reads the repo’s main documentation, when they look for “how to verify changes,” then they find a short section that includes the exact command(s) to run locally.
- Given tests are run locally, when no changes are present, then the suite finishes in a reasonable time for a small tooling repo (target: under ~60s on a typical laptop).

