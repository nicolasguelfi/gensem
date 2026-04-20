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
| `--review-strategy` | Run the strategy review pass manually (tag `[STRATEGY]`, see spec §6.5) |
| `--review-specs`   | Run the TST- specifications review pass manually (tag `[TST-SPEC]`, see spec §6.5) |
| `--deep-review`    | Run both strategy and TST-spec review passes, regardless of auto-triggers |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint number
2. `.gse/config.yaml` — project configuration (language, framework, domain)
3. `.gse/profile.yaml` — user preferences
4. `docs/sprints/sprint-{NN}/reqs.md` — requirements to test against (including quality coverage matrix and checklist results from Step 7)
5. `docs/sprints/sprint-{NN}/design.md` — design to test against
6. `docs/sprints/sprint-{NN}/test-reports/` — existing test reports (if any)
7. `.gse/status.yaml` — project health metrics (health section)

## Workflow

### Step 1 — Strategy (`--strategy`)

**Test strategy is derived from three sources:**
- **Validation tests** (acceptance, E2E) → derived from **REQS acceptance criteria** (Given/When/Then). Each acceptance criterion in `reqs.md` becomes a TST- artefact with `traces.validates: [REQ-NNN]`. These verify the app does what the user asked.
- **Verification tests** (unit, integration) → derived from **DESIGN decisions** (DES-). These verify the code is built correctly (interfaces, module boundaries, data contracts).
- **Policy tests** (new in v0.35, spec §6 Policy column) → derived from **structural rules** captured in `design.md` (Component Diagram, Shared State, Architecture Overview) and in `decisions.md` (DEC- entries with architectural intent). These guard the codebase's shape via static analysis (no runtime). Examples: layering enforcement, license compliance, naming conventions, file-size limits. Baseline 5% of the pyramid, raisable to 10-15% for strict-architecture projects.

**Prerequisite:** REQS must exist with testable acceptance criteria. DESIGN should exist if applicable. If either is missing, report and redirect to the missing activity.

For beginners: "I'll take each feature description you confirmed and turn it into a checklist of things to verify. Some checks are from the user's point of view (does the app do what you want?) and some are technical (is the code structured correctly?)."

Define the test pyramid calibrated by project domain. **The canonical distribution is defined in the spec §6.1** (columns: Unit / Integration / E2E-Visual / Acceptance / Other) and covers 8 domains: Web frontend, API backend, CLI tool, Data pipeline, Mobile, Library/SDK, Embedded, Scientific. The agent reads the appropriate row from that table based on `config.yaml → project.domain`.

**Monorepo sub-domains:** When `config.yaml → project.sub_domains` is defined, create a separate pyramid section per sub-domain in the test strategy. For example:
- `frontend/` (domain: web) → web pyramid from spec §6.1
- `backend/` (domain: api) → api pyramid from spec §6.1
Files outside any sub-domain path use the top-level `project.domain` pyramid as fallback.

The strategy document defines:
- Test pyramid distribution for this project (or per sub-domain if applicable)
- Coverage targets per level
- Test naming conventions (TST-NNN)
- Test data management approach
- CI/CD integration plan
- **Validation test derivation** (see below)

#### Validation test derivation (from REQS acceptance criteria)

**This is the concrete link between test-driven requirements and test execution.**

For each acceptance criterion (Given/When/Then) in `reqs.md`, create a corresponding TST- artefact:

1. **One TST per scenario** — Each Given/When/Then scenario in a REQ becomes at least one test
2. **Naming** — Reference the REQ: e.g., `TST-001` validates `REQ-001` scenario 1
3. **Exact conditions** — The test MUST check the exact conditions stated in the criterion, not a different interpretation
4. **Traceability** — Each TST carries `traces: { validates: [REQ-NNN] }`
5. **Distinction from verification tests** — Validation tests (from REQS) verify the app does what the user asked. Verification tests (from DESIGN) verify the code is built correctly. Both appear in the test campaign summary but are clearly labeled.

Example derivation:
```
REQ-003 — Filter expenses by month
  Scenario 1: Given 5 expenses across 3 months,
              When filtering by "March 2026",
              Then only the 2 March expenses appear
  
  → TST-007: filterByMonth returns only March expenses
    traces: { validates: [REQ-003] }

  Scenario 2: Given no expenses in April,
              When filtering by "April 2026", 
              Then an empty list is shown
  
  → TST-008: filterByMonth returns empty for month with no data
    traces: { validates: [REQ-003] }
```

For beginners: "For each feature you confirmed in the requirements, I'll create a test that checks it works exactly as described."

#### Policy test derivation (from DESIGN and DECISIONS — new in v0.35)

For each structural rule in `design.md` or `decisions.md`, propose a corresponding policy test:

1. **Scan `design.md`** — specifically *Architecture Overview*, *Component Diagram*, and *Shared State* sections. If layered architecture is documented (e.g., "domain layer / storage layer / UI layer"), propose a policy test enforcing the layering.
2. **Scan `decisions.md`** — DEC- entries with architectural intent (e.g., *"DEC-005: framework-free domain module"*). Each such decision becomes a candidate policy test.
3. **Apply domain baseline** — read `config.yaml → project.domain` and use the Policy percentage from the spec §6.1 pyramid (default: 5%). Adjust upward if the project has strict architecture or licensing requirements.

**Proposals are Inform-tier** — each candidate policy test is presented with:
- The rule being enforced (one sentence)
- The source (DEC-NNN or design section)
- A concrete tool recommendation based on the project language (see the design doc "Policy tests — Design Mechanics" table: `pytest-archon` for Python, `ts-arch` for TypeScript, `ArchUnit` for Java, etc.)

The user accepts, adjusts, or declines each proposal. Each accepted policy test gets its own TST-NNN artefact with `level: policy` in its frontmatter and `traces: { enforces: [DEC-NNN, design-section-ref] }`.

**Policy tests must be:**
- **Fast** — full run in seconds (static scan, no runtime)
- **Deterministic** — pass/fail is a function of code state, not environment
- **Actionable on failure** — the error message names the violating file + the rule + a fix hint

They run at the same trigger points as other test levels (pre-commit hook, CI, `/gse:tests --run`).

#### Quality-driven tests (from REQS quality checklist)

When the requirements phase identifies quality gaps via the ISO 25010-inspired checklist (Step 7 of `/gse:reqs`), the test strategy must include corresponding tests to close those gaps. Read the quality coverage matrix in `reqs.md` and for each gap that was **not deferred or acknowledged**:

1. **Create a TST- artefact** targeting the gap — e.g., a load test for an unspecified performance threshold, a security test for missing rate limiting
2. **Link via `quality_gap` trace** — Each gap-closing test carries `traces: { validates: [REQ-NNN], quality_gap: true }` to distinguish it from standard validation tests
3. **Assign to the appropriate pyramid level** — These are not a new pyramid level; they are constraints on existing levels (unit for performance conditions, integration for security contracts, E2E for accessibility)

Example:
```
Quality gap: REQ-005 "API response time" — stress test conditions not specified
  → TST-050: Load test with 500 concurrent users for 5 minutes
    traces: { validates: [REQ-005], quality_gap: true }
    level: performance
```

For beginners: "The quality checklist found some details we should verify with tests. I'll add those tests to the plan."

Save to `docs/sprints/sprint-{NN}/test-strategy.md`.

#### Strategy review pass (spec §6.5 — STRATEGY tier)

After saving the strategy, check the auto-trigger conditions. The strategy review runs when **any** of the following is true:
- `config.yaml → project.domain` is security-sensitive (auth / crypto / payment / PII)
- The current sprint's `complexity_budget > 15`
- The flag `--review-strategy` or `--deep-review` was passed

When the review fires, spawn the `test-strategist` sub-agent (see `agents/test-strategist.md`, "Strategy checklist") on the just-saved `test-strategy.md`. Findings are tagged `[STRATEGY]` and written into `docs/sprints/sprint-{NN}/review.md` using the standard RVW-NNN format. HIGH findings block `/gse:produce` (Hard guardrail) until resolved; MEDIUM / LOW warn but do not block.

When none of the triggers fire, skip this pass — the strategy is trusted on the fly to keep light sprints agile. The user can always force it later with `--review-strategy`.

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

### Adaptation to User Expertise (Spec 6.6)

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

#### TST specs review pass (spec §6.5 — TST-SPEC tier)

After all TST- artefacts are drafted, check the auto-trigger conditions. The specs review runs when **any** of the following is true:
- At least one TST- carries `traces.quality_gap: true`
- The total count of TST- drafted in this sprint is ≥ 20
- The flag `--review-specs` or `--deep-review` was passed

When the review fires, spawn the `test-strategist` sub-agent (see `agents/test-strategist.md`, "Specifications checklist") on the TST- specs. The reviewer checks: exact Given/When/Then correspondence between each TST- and its source REQ-, absence of tautological tests, boundary / empty / error case coverage, coherence of `traces` fields, and that every REQ `priority: must` has at least one TST-. Findings are tagged `[TST-SPEC]` and written into `docs/sprints/sprint-{NN}/review.md`. HIGH findings block `/gse:produce` (Hard guardrail) until resolved.

When none of the triggers fire, skip this pass to keep sprints with few or low-risk tests agile. The user can always force it later with `--review-specs`.

### Step 4 — Execute (`--run`)

TESTS invokes the **canonical test run** defined in spec §6.3. Argument handling determines the scope:

| Invocation | Scope |
|------------|-------|
| `--run` (no arg) | Full suite |
| `--run TST-005` | Single test identified by TST-NNN |
| `--run --level unit` | All tests at the specified pyramid level (unit / integration / e2e / visual / performance) |

Unlike PRODUCE, TESTS does **not** auto-generate missing tests — tests must already exist. If no tests exist for the requested scope, report and redirect to `--strategy` / Step 3.

All outputs (TCP-NNN campaign, test_evidence update on every covered TASK, inline summary, health refresh) are produced by the canonical run — no capture logic is duplicated here.

### Step 5 — Visual Testing (`--visual`)

For web and mobile projects, `--visual` invokes the canonical test run (spec §6.3) **with visual testing enabled**. The canonical run's screenshot analysis sub-step is mandatory in this mode: multimodal analysis of captured screenshots, `[VISUAL]`-tagged findings in the campaign, and video on failure when configured. See spec §6.3 "Screenshot analysis (visual runs only)" for the full behavior and best-effort caveat.

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

### Step 7 — Sprint Evidence Package (`--evidence`)

Unlike the per-run TCP-NNN emitted by the canonical run (one per `--run` invocation, scoped to a single TASK or test), `--evidence` produces a **sprint-level aggregate** rolling up all TCPs of the current sprint.

Save to `docs/sprints/sprint-{NN}/test-reports/sprint-evidence-{date}.md`:

```yaml
---
gse:
  id: TCP-{NNN}                      # unique campaign ID (sprint-level aggregate)
  type: test-campaign
  title: "Sprint {NN} Evidence Package — {date}"
  sprint: {NN}
  status: done
  created: {date}
  author: agent
  traces:
    derives_from: [TCP-{NNN}, TCP-{NNN}, ...]  # the per-TASK campaigns rolled up
    implements: [REQ-{NNN}, ...]                # all REQs covered this sprint
---
```

Content includes:
- Test pyramid coverage vs targets
- Pass/fail summary by level (aggregated across all TCPs)
- Code coverage summary (weighted or latest, as appropriate)
- Requirements coverage matrix (which REQs have at least one passing test)
- Visual test results with screenshot references
- Failed tests with root cause analysis
- Recommendations for next sprint

Health dimensions and the dashboard are refreshed automatically because each underlying canonical run already updated them. `--evidence` only aggregates — it does not re-run tests.

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
