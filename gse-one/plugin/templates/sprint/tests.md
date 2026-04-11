---
gse:
  type: test
  sprint: 1
  branch: gse/sprint-01
  traces:
    implements: []                     # e.g., [REQ-001, DES-001] — what these tests validate
  status: draft                        # draft | reviewed | approved
  created: ""
  updated: ""
---

# Test Definitions — Sprint {sprint}

## Test Strategy

- **Domain:** {web | cli | library | embedded | scientific | mobile}
- **Pyramid target:** Unit {N}% / Integration {N}% / E2E {N}%
- **Coverage target:** {N}%
- **Framework:** {pytest | jest | ...}

## Unit Tests

### T01 — {test title}

- **Tests requirement:** R01
- **Component:** {module or class under test}
- **Scenario:** {what is being tested}
- **Given:** {preconditions}
- **When:** {action}
- **Then:** {expected outcome}
- **Edge cases:**
  - {edge case 1}
  - {edge case 2}

### T02 — {test title}

- **Tests requirement:** R01
- **Component:** {module or class under test}
- **Scenario:** {what is being tested}
- **Given:** {preconditions}
- **When:** {action}
- **Then:** {expected outcome}

## Integration Tests

### T10 — {test title}

- **Tests requirement:** R01, R02
- **Components:** {components interacting}
- **Scenario:** {integration scenario}
- **Setup:** {fixtures, test data, external mocks}
- **Steps:**
  1. {step}
  2. {step}
- **Expected:** {integrated behavior}
- **Teardown:** {cleanup}

## End-to-End Tests

### T20 — {test title}

- **Tests requirement:** R01
- **User flow:** {complete user journey}
- **Preconditions:** {system state, test user}
- **Steps:**
  1. {user action}
  2. {expected response}
  3. {user action}
  4. {expected response}
- **Success criteria:** {what constitutes a pass}

## Test Data

| Dataset        | Purpose              | Location                  |
|---------------|----------------------|---------------------------|
|               |                      |                           |

## Coverage Map

| Requirement | Unit Tests | Integration | E2E  | Risk Level |
|-------------|-----------|-------------|------|------------|
| R01         | T01, T02  | T10         | T20  | high       |
| R02         |           | T10         |      | medium     |

## Notes

_Test environment requirements, known limitations, or special setup instructions._
