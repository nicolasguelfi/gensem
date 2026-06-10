---
gse:
  type: test
  sprint: 1
  branch: gse/sprint-{NN}/integration    # replaced at instantiation by /gse:tests
  traces:
    derives_from: []                   # e.g., [TASK-005] — task being tested
    implements: []                     # e.g., [REQ-001, DES-001] — doc-level rollup; per-TST links use validates / enforces (spec P6 — Trace link types)
    decided_by: []                     # e.g., [DEC-007] — shaping decisions (esp. for policy tests)
  status: draft                        # draft | reviewed | approved
  created: ""
  updated: ""
---

# Test Definitions — Sprint {sprint}

> Test ID convention: TST-001..TST-009 for unit tests, TST-010..TST-019 for
> integration, TST-020..TST-029 for E2E, TST-030..TST-039 for policy tests.
> Frontmatter `level:` field remains authoritative; ID ranges are visual convenience.

## Test Strategy

- **Domain:** {web | cli | library | embedded | scientific | mobile}
- **Pyramid target:** Unit {N}% / Integration {N}% / E2E {N}% / Policy {N}%
- **Coverage target:** {N}%
- **Framework:** {pytest | jest | ...}

## Unit Tests

### TST-001 — {test title}

- **Implements:** REQ-001
- **Component:** {module or class under test}
- **Scenario:** {what is being tested}
- **Given:** {preconditions}
- **When:** {action}
- **Then:** {expected outcome}
- **Edge cases:**
  - {edge case 1}
  - {edge case 2}

### TST-002 — {test title}

- **Implements:** REQ-001
- **Component:** {module or class under test}
- **Scenario:** {what is being tested}
- **Given:** {preconditions}
- **When:** {action}
- **Then:** {expected outcome}

## Integration Tests

### TST-010 — {test title}

- **Implements:** REQ-001, REQ-002
- **Components:** {components interacting}
- **Scenario:** {integration scenario}
- **Setup:** {fixtures, test data, external mocks}
- **Steps:**
  1. {step}
  2. {step}
- **Expected:** {integrated behavior}
- **Teardown:** {cleanup}

## E2E Tests

> **E2E Evidence (default):** every E2E test captures a final screenshot as execution evidence (saved to `tests/e2e/screenshots/` or the framework's default screenshot directory). Screenshots are preserved per campaign for visual verification and regression diffing. This is **distinct** from full visual-regression testing (activated via `/gse:tests --visual`), which adds pixel-diff comparison against reference images.

### TST-020 — {test title}

- **Implements:** REQ-001
- **User flow:** {complete user journey}
- **Preconditions:** {system state, test user}
- **Steps:**
  1. {user action}
  2. {expected response}
  3. {user action}
  4. {expected response}
- **Success criteria:** {what constitutes a pass}

## Policy Tests

> Enforce structural rules on the codebase via static analysis (no runtime).
> Derived from design decisions (DEC-) and architecture rules in design.md.
> Baseline: 5% of test pyramid (spec §6). Raisable to 10-15% for strict-architecture projects.

### TST-030 — {rule name}

- **Enforces:** {one-sentence rule, e.g., "src/domain/** must not import src/ui/**"}
- **Source:** {DEC-NNN or design.md section reference}
- **Tool:** {pytest-archon | ts-arch | ArchUnit | eslint-plugin | custom}
- **Traces:**
  - enforces: [{DEC-NNN, design-section-ref}]
- **Level:** policy

## Test Data

| Dataset        | Purpose              | Location                  |
|---------------|----------------------|---------------------------|
|               |                      |                           |

## Coverage Map

| Requirement | Unit Tests       | Integration | E2E      | Risk Level |
|-------------|------------------|-------------|----------|------------|
| REQ-001     | TST-001, TST-002 | TST-010     | TST-020  | high       |
| REQ-002     |                  | TST-010     |          | medium     |

## Notes

_Test environment requirements, known limitations, or special setup instructions._
