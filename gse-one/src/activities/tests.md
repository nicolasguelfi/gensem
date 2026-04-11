---
description: "Define test strategy, set up environment, write tests, execute campaigns, produce evidence. Triggered by /gse:tests."
---

# GSE-One Tests — Testing Strategy

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Show current test status and suggest next action |
| `--strategy`       | Define or update the test strategy for the project |
| `--setup`          | Set up test environment and framework |
| `--run`            | Execute the full test suite |
| `--run <test-id>`  | Execute a specific test (e.g., `TST-005`) |
| `--visual`         | Run visual/screenshot tests (web/mobile projects) |
| `--coverage`       | Generate and display code coverage report |
| `--evidence`       | Produce test evidence package for the current sprint |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint number
2. `.gse/config.yaml` — project configuration (language, framework, domain)
3. `.gse/profile.yaml` — user preferences
4. `docs/sprints/sprint-{NN}/reqs.md` — requirements to test against
5. `docs/sprints/sprint-{NN}/design.md` — design to test against
6. `docs/sprints/sprint-{NN}/test-reports/` — existing test reports (if any)
7. `.gse/status.yaml` — project health metrics (health section)

## Workflow

### Step 1 — Strategy (`--strategy`)

Define the test pyramid calibrated by project domain:

| Domain | Unit | Integration | E2E/Visual | Other |
|--------|------|-------------|------------|-------|
| **Web frontend** | 20% | 20% | 40% (visual) | 20% (a11y, perf) |
| **API / backend** | 50% | 30% | 5% (smoke) | 15% (load, security) |
| **CLI tool** | 60% | 20% | 10% (smoke) | 10% (compat) |
| **Data pipeline** | 40% | 30% | 5% | 25% (data quality) |
| **Mobile app** | 25% | 20% | 35% (visual) | 20% (device compat) |
| **Library / SDK** | 70% | 20% | 0% | 10% (compat, docs) |
| **Embedded** | 50% | 25% | 0% | 25% (hardware sim) |

The strategy document defines:
- Test pyramid distribution for this project
- Coverage targets per level
- Test naming conventions (TST-NNN)
- Test data management approach
- CI/CD integration plan

Save to `docs/sprints/sprint-{NN}/test-strategy.md`.

### Risk-Based Prioritization (Spec 6.1)

Not all code needs equal test coverage. Prioritize testing based on risk:

| Factor | Testing Priority | Action |
|--------|-----------------|--------|
| Module touched by a review finding (RVW) | **High priority** | Add regression tests |
| Module with a Gate-tier decision (DEC) | **Regression test mandatory** | Ensure decision is validated |
| Module imported from external source (SRC) | **Compatibility tests mandatory** | Verify in project context |
| Security-sensitive code (auth, crypto, input) | **Comprehensive coverage** | Unit + integration + edge cases |
| Simple configuration / static content | **Minimal tests** | Smoke test only |

### Coverage Guardrail (Spec 6.4)

When code coverage drops below the configured minimum (`config.yaml → testing.coverage.minimum`, default: 60%):

**Hard guardrail triggers:**
```
GUARDRAIL [HARD]: Code coverage is {current}% (minimum: {minimum}%).
Add tests before proceeding to DELIVER.
```

The same applies to requirements coverage:
- 100% for `must` priority requirements
- 80% for `should` priority requirements

Risk coverage target: 100% of high-risk modules (security, Gate decisions, imports) must have dedicated tests.

### Adaptation to User Expertise (Spec 6.5)

The agent's testing behavior adapts to the user's level (`profile.yaml → user.it_expertise`):

| Level | Agent's Testing Behavior |
|-------|------------------------|
| **Beginner** | The agent writes all tests, executes them, and shows visual results. "8 tests pass, 2 fail — here are the screenshots." No jargon. The user sees evidence, not code. |
| **Intermediate** | The agent proposes the test strategy, writes the tests, explains what each test verifies in plain language. The user can modify tests. Technical terms introduced progressively (P14). |
| **Advanced** | The agent discusses strategy (TDD vs test-after), proposes the test pyramid, co-writes tests with the user. Coverage targets are negotiated. |
| **Expert** | Full collaboration. The agent proposes advanced techniques (property-based testing, mutation testing, contract testing). The user drives, the agent assists. |

### Step 2 — Setup (`--setup`)

Detect project language and select the appropriate test framework:

| Language | Framework | Install Command | Config File |
|----------|-----------|----------------|-------------|
| Python | pytest | `uv add --group dev pytest pytest-cov` | `pyproject.toml` |
| JavaScript/TypeScript | vitest | `npm install -D vitest @vitest/coverage-v8` | `vitest.config.ts` |
| JavaScript (legacy) | jest | `npm install -D jest` | `jest.config.js` |
| Go | go test | (built-in) | — |
| Rust | cargo test | (built-in) | — |
| Java | JUnit 5 | (Maven/Gradle dependency) | `build.gradle` |

**Visual testing setup** (for web/mobile projects):

| Tool | Purpose | Install |
|------|---------|---------|
| Playwright | Browser automation + screenshots | `uv add --group dev playwright` / `npm install -D @playwright/test` |
| Percy | Visual regression (cloud) | Percy SDK for chosen language |

Steps:
1. Install test framework as dev dependency
2. Create test directory structure (`tests/unit/`, `tests/integration/`, `tests/e2e/`)
3. Create test configuration file
4. Create a sample test to verify setup works
5. Run the sample test to confirm green

### Step 3 — Write Tests

For each requirement (REQ) and design component (DES), generate tests at the appropriate level:

Each test has a unique identifier:

```yaml
---
id: TST-{NNN}
artefact_type: test
title: "Test description"
level: unit | integration | e2e | visual | performance
sprint: {NN}
status: draft
created: {date}
author: agent
traces:
  derives_from: [REQ-{NNN}]
  tests: [SRC-{NNN}]
---
```

Test file naming: `tests/{level}/test_{component}_{feature}.py` (Python example)

Test structure:
```python
# TST-007: Verify rate limiter rejects requests over threshold
# Traces: REQ-007 (rate limiting), DES-003 (RateLimiter component)
def test_rate_limiter_rejects_over_threshold():
    """Given a user at the rate limit, when they send another request,
    then the request is rejected with 429."""
    limiter = RateLimiter(max_requests=100, window_seconds=60)
    for _ in range(100):
        limiter.record_request(user_id="test-user")
    
    result = limiter.check_request(user_id="test-user")
    assert result.allowed is False
    assert result.retry_after > 0
```

### Step 4 — Execute (`--run`)

Run tests in an isolated environment:

1. **Full suite** (`--run`): Execute all tests, capture output
2. **Single test** (`--run TST-005`): Execute only the specified test
3. **By level** (`--run --level unit`): Execute tests at a specific level

Capture for each test run:
- Pass/fail status per test
- Execution time
- Stdout/stderr output
- Stack traces for failures

### Step 5 — Visual Testing (`--visual`)

For web and mobile projects:

1. **Capture screenshots** — Use Playwright to navigate to each page/view and capture screenshots
2. **Multimodal analysis** — Analyze screenshots for visual defects:
   - Layout issues (overlapping elements, misalignment)
   - Missing content (blank areas, broken images)
   - Styling anomalies (wrong colors, font issues)
   - Responsive issues (content overflow, hidden elements)
3. **Best-effort caveat** — Always note: "Visual analysis is best-effort. The agent identifies obvious issues but cannot guarantee detection of all visual defects. Human review of screenshots is recommended."
4. **Save screenshots** — Store in `docs/sprints/sprint-{NN}/test-reports/screenshots/`
5. **Video on failure** — If a test fails, capture video of the failing interaction

### Step 6 — Coverage (`--coverage`)

Generate code coverage report:

1. Run tests with coverage enabled:
   - Python: `uv run pytest --cov=src --cov-report=html --cov-report=term`
   - JS/TS: `npx vitest --coverage`
   - Go: `go test -coverprofile=coverage.out ./...`
2. Parse coverage results:
   - Total line coverage percentage
   - Per-file coverage breakdown
   - Uncovered lines/branches
3. Compare against targets from strategy
4. Flag files below threshold

### Step 7 — Campaign Report (`--evidence`)

Generate a comprehensive test evidence package:

Save to `docs/sprints/sprint-{NN}/test-reports/campaign-{date}.md`:

```yaml
---
id: RVW-{NNN}
artefact_type: review
title: "Sprint {NN} Test Campaign — {date}"
sprint: {NN}
status: done
created: {date}
author: agent
traces:
  derives_from: [TST-{NNN}, ...]
---
```

Content includes:
- Test pyramid coverage vs targets
- Pass/fail summary by level
- Code coverage summary
- Requirements coverage matrix (which REQs have passing tests)
- Visual test results with screenshot references
- Failed tests with root cause analysis
- Recommendations for next sprint

### Step 8 — Update Health Metrics

Update `.gse/status.yaml` health dimensions with test metrics:

```yaml
testing:
  test_pass_rate: 95.2        # percentage of tests passing
  code_coverage: 82.1          # line coverage percentage
  requirements_coverage: 90.0  # percentage of REQs with at least one test
  last_run: "2026-01-20T14:30:00Z"
  tests_total: 42
  tests_passed: 40
  tests_failed: 2
  tests_skipped: 0
```

### Framework Drift Detection

On each `--run` or `--setup`:

1. Compare the currently installed test framework version against `.gse/config.yaml`
2. If version has changed (e.g., someone ran `npm update`):
   - Report: "Test framework version changed: vitest 2.0.1 -> 2.1.0"
   - Check for breaking changes in changelog
   - Propose updating config if compatible

### Dependency Audit

If enabled in `.gse/config.yaml` (`security.dependency_audit: true`):

1. Run audit tool:
   - Python: `uv run pip-audit`
   - JavaScript: `npm audit`
   - Go: `govulncheck ./...`
   - Rust: `cargo audit`
2. Report vulnerabilities by severity
3. Create TASK items in backlog for critical vulnerabilities
