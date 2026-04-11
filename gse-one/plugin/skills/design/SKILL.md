---
description: "Define architecture decisions, component decomposition, interface contracts. Triggered by /gse:design."
---

# GSE-One Design — Design

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Start design activity for the current sprint |
| `--decision <topic>` | Log a specific architecture decision |
| `--show`           | Display current design document |
| `--interfaces`     | Focus on interface contract definitions |
| `--validate`       | Check design for completeness and consistency |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint number
2. `docs/sprints/sprint-{NN}/reqs.md` — requirements to design for
3. `docs/sprints/sprint-{NN}/plan.md` — sprint plan (scope and constraints)
4. `docs/sprints/sprint-{NN}/design.md` — existing design (if any)
5. `.gse/decisions.md` — previous architecture decisions (for consistency)
6. `.gse/profile.yaml` — user preferences
7. `.gse/sources.yaml` — external sources that may influence design

## Workflow

### Step 1 — Scope Analysis

Identify which requirements need design work:

- Group requirements by component/module they affect
- Identify cross-cutting concerns (logging, auth, error handling)
- Detect requirements that impact existing architecture

Present scope: "Sprint S02 design covers 3 components: AuthModule (REQ-001..003), RateLimiter (REQ-007..009), WebhookHandler (REQ-012..014)."

### Step 2 — Component Decomposition

For each component group, define:

```
Component: AuthModule
─────────────────────
  Responsibility: Handle user authentication and session management
  Dependencies:   Database (stable), ConfigService (stable)
  Dependents:     APIRouter, WebhookHandler
  Interface:      see Step 3
  Files:          src/auth/authenticator.py, src/auth/session.py, src/auth/models.py
  Requirements:   REQ-001, REQ-002, REQ-003
```

Rules for decomposition:
- Each component has a single, well-defined responsibility
- Dependencies flow from volatile to stable (never reverse)
- Components communicate through explicit interfaces (no direct field access)
- Circular dependencies are forbidden (hard guardrail)

### Step 3 — Interface Contracts

For each component, define its public interface:

```
Interface: AuthModule
─────────────────────

  authenticate(credentials: Credentials) -> Result[Session, AuthError]
    - Input: username (str, 3-50 chars), password (str, 8+ chars)
    - Output: Session object with token, expiry, user_id
    - Errors: InvalidCredentials, AccountLocked, RateLimited
    - Invariants: token is unique, expiry is always in the future
    - Side effects: creates session record in database

  validate_session(token: str) -> Result[User, AuthError]
    - Input: JWT token string
    - Output: User object if token is valid
    - Errors: TokenExpired, TokenInvalid, UserNotFound
    - Invariants: never returns a disabled user
    - Side effects: none (read-only)
```

### Step 4 — Architecture Decisions

For each significant technical choice, create a decision record as a Gate decision:

```
Decision: DEC-{NNN} — {Topic}
──────────────────────────────

Context:    {Why this decision is needed now}
Options:
  A. {Option A} — {Pros} / {Cons}
  B. {Option B} — {Pros} / {Cons}
  C. {Option C} — {Pros} / {Cons}

Recommendation: {Option X}
Rationale:      {Why this option best fits the requirements and constraints}

Consequence horizon:
  - Short-term (this sprint): {impact}
  - Medium-term (3 sprints): {impact}
  - Long-term (project lifetime): {impact}

Reversibility: easy | moderate | difficult | irreversible

Gate: [Accept recommendation] / [Choose different option] / [Discuss]
```

Each decision is appended to `.gse/decisions.md` (the decision journal, spec Section 11) with this format:

```yaml
---
id: DEC-{NNN}
artefact_type: decision
title: "{Topic}"
sprint: {NN}
status: draft | accepted | superseded
created: {date}
author: pair
traces:
  derives_from: [REQ-{NNN}, ...]
  impacts: [DES-{NNN}, SRC-{NNN}, ...]
  supersedes: []  # if replacing an earlier decision
---
```

### Step 5 — Design Validation (`--validate`)

Check the design for structural quality:

| Check | Rule |
|-------|------|
| **Coverage** | Every requirement is addressed by at least one component |
| **Circular dependencies** | No circular dependency chains (HARD STOP if found) |
| **Interface completeness** | Every component has a defined interface |
| **Error handling** | Every interface method defines its error cases |
| **Decision records** | Every significant choice has a DEC record |
| **Consistency** | New decisions do not contradict existing ones |

Report findings using the architect agent checklist (see `agents/architect.md`).

### Step 6 — Persist

Save the design document to `docs/sprints/sprint-{NN}/design.md`:

```yaml
---
id: DES-{NNN}
artefact_type: design
title: "Sprint {NN} Design"
sprint: {NN}
status: draft
created: {date}
author: pair
traces:
  derives_from: [REQ-{NNN}, ...]
  tested_by: []
  implemented_by: []
---
```

Content includes:
- Component diagram (text-based or Mermaid)
- Component descriptions with responsibilities
- Interface contracts
- Architecture decision references
- Dependency graph

Present the design for user approval (Gate). Set status to `approved` once confirmed.
