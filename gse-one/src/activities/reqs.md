---
description: "Define functional and non-functional requirements. Triggered by /gse:reqs."
---

# GSE-One Reqs — Requirements

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Start requirements elicitation for the current sprint |
| `--fr`             | Focus on functional requirements |
| `--nfr`            | Focus on non-functional requirements |
| `--show`           | Display current requirements without modification |
| `--validate`       | Check requirements for completeness and consistency |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint number
2. `.gse/backlog.yaml` — sprint tasks that need requirements
3. `.gse/profile.yaml` — user preferences (decision involvement, verbosity)
4. `docs/sprints/sprint-{NN}/plan.md` — sprint plan (for scope context)
5. `docs/sprints/sprint-{NN}/reqs.md` — existing requirements (if any)
6. `.gse/sources.yaml` — external sources that may inform requirements

## Workflow

### Step 1 — Scope Determination

Identify which backlog items in the current sprint need requirements:

- Items of type `requirement` → these ARE the requirements to define
- Items of type `code`, `config` → derive requirements from their descriptions
- Items of type `test` → requirements should already exist (check traces)
- Items of type `design` → requirements should already exist (check traces)

Present the scope: "Sprint S02 has 5 tasks. I'll define requirements for: TASK-010 (rate limiting), TASK-013 (webhook handler), TASK-016 (CSV export)."

### Step 2 — Functional Requirements (FR)

For each in-scope item, define functional requirements using the standard format:

```yaml
- id: REQ-{NNN}
  type: functional
  title: "Short descriptive title"
  description: |
    As a [role],
    I want to [action],
    so that [benefit].
  priority: must | should | could
  acceptance_criteria:
    - "Given [context], when [action], then [result]"
    - "Given [context], when [action], then [result]"
  traces:
    derives_from: [TASK-{NNN}]
    tested_by: []        # filled by TESTS activity
    implemented_by: []   # filled by PRODUCE activity
  sprint: {NN}
  status: draft
```

Priority levels follow MoSCoW:

| Priority | Meaning |
|----------|---------|
| `must`   | Critical — sprint fails without it |
| `should` | Important — expected but sprint can succeed without it |
| `could`  | Desirable — nice to have if time permits |

### Step 3 — Non-Functional Requirements (NFR)

Define NFRs organized by category:

| Category | Examples | Measurement |
|----------|----------|-------------|
| **Performance** | Response time, throughput, latency | "API responds in < 200ms at p95" |
| **Security** | Authentication, authorization, data protection | "All endpoints require valid JWT" |
| **Usability** | Error messages, input validation, accessibility | "Error responses include actionable message" |
| **Reliability** | Uptime, error handling, data integrity | "System handles 1000 concurrent requests" |
| **Maintainability** | Code coverage, documentation, modularity | "Test coverage > 80% for new code" |

NFR format:

```yaml
- id: REQ-{NNN}
  type: non-functional
  category: performance | security | usability | reliability | maintainability
  title: "API response time under load"
  description: "All API endpoints must respond within 200ms at p95 under 500 concurrent users"
  priority: must
  measurement: "Load test with k6, 500 virtual users, 5-minute duration"
  acceptance_criteria:
    - "p95 response time < 200ms"
    - "Error rate < 0.1%"
    - "No memory leaks over 5-minute test"
  traces:
    derives_from: [TASK-{NNN}]
    tested_by: []
  sprint: {NN}
  status: draft
```

### Step 4 — User Story Format for Validation

For each functional requirement, generate a user story suitable for validation testing:

```
Story: REQ-007 — Rate Limiting
  As an API consumer,
  I want the API to enforce rate limits,
  so that the service remains available for all users.

  Scenario 1: Under limit
    Given a user with 0 requests in the current window
    When they send a valid API request
    Then the request succeeds with 200
    And the response includes X-RateLimit-Remaining header

  Scenario 2: At limit
    Given a user with 100 requests in the current window (limit = 100)
    When they send another API request
    Then the request fails with 429 Too Many Requests
    And the response includes Retry-After header

  Scenario 3: Window reset
    Given a user who hit the rate limit
    When the rate limit window expires
    Then their next request succeeds with 200
```

### Step 5 — Validation (`--validate`)

Check requirements for common issues:

| Check | Rule |
|-------|------|
| **Completeness** | Every sprint task has at least one requirement |
| **Testability** | Every requirement has acceptance criteria |
| **Consistency** | No contradicting requirements |
| **Traceability** | Every requirement traces to a task |
| **Ambiguity** | Flag vague terms: "fast", "easy", "user-friendly" without metrics |
| **Duplicates** | Flag requirements with > 80% semantic overlap |

Report findings:
```
Requirements Validation — Sprint S02
─────────────────────────────────────
  ✓ Completeness: 5/5 tasks have requirements
  ✓ Testability: 12/12 requirements have acceptance criteria
  ⚠ Ambiguity: REQ-009 uses "quickly" without metric — suggest "< 500ms"
  ✓ Consistency: No contradictions found
  ✓ Traceability: All requirements trace to tasks
  ✓ Duplicates: None detected
```

### Step 6 — Persist

Save requirements to `docs/sprints/sprint-{NN}/reqs.md`:

```yaml
---
id: DOC-{NNN}
artefact_type: doc
title: "Sprint {NN} Requirements"
sprint: {NN}
status: draft
created: {date}
author: pair
traces:
  derives_from: [PLN-{NNN}]
---
```

Present requirements for user approval (Gate). Set status to `approved` once confirmed.
