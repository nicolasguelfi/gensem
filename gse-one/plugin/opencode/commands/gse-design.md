---
name: "gse-design"
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
3. `.gse/plan.yaml` — living sprint plan (scope and constraints)
4. `docs/sprints/sprint-{NN}/design.md` — existing design (if any)
5. `.gse/decisions.md` — previous architecture decisions (for consistency)
6. `.gse/profile.yaml` — user preferences
7. `.gse/sources.yaml` — external sources that may influence design

## Workflow

### Step 0 — Open Questions Gate (activity-entry scan, spec P6)

Before any architecture work, scan for pending Open Questions (`OQ-`) whose `resolves_in: DESIGN`.

1. **Enumerate sources** — list `docs/intent.md` (always) and `docs/sprints/sprint-{NN}/*.md` for the current sprint if it exists.
2. **Parse `## Open Questions`** sections. Extract entries where `status: pending` AND `resolves_in: DESIGN`.
3. **If zero matches** → skip this step, proceed to Step 1.
4. **If ≥ 1 match** → enter the Open Questions Gate per the user's `decision_involvement` (see `/gse:plan` Step 0 for the canonical three-mode description — `autonomous` / `collaborative` / `supervised`). Resolutions are recorded in the origin artefact's `## Open Questions` entry in place. Resolutions typically seed DEC-NNN architecture decisions in the upcoming design work (questions tagged `impact: architectural` are especially relevant here).
5. Proceed to Step 1.

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

### Step 2.5 — Shared State Identification

For each piece of state (data, selection, session, filter, auth context, etc.) that must be **visible or consistent across multiple components or pages**, formalize it in the `## Shared State` section of `design.md`. The common failure mode is silent duplication: each component invents its own instance of what is logically one piece of state, leading to inconsistency (e.g., a month filter widget that must be synchronized across 3 pages but lives as 3 independent state slots).

**Algorithm:**

1. Walk through the REQs and the component decomposition from Step 2.
2. For each component pair, ask: *"Do they read or write any state that must stay consistent between them?"*
3. If yes, add an entry to `## Shared State`:

   | Name | Scope (components) | Mechanism | Rationale | Traces |
   |------|-------------------|-----------|-----------|--------|
   | `selected_month` | Dashboard, Expenses, Budgets | framework session state (e.g., Streamlit `st.session_state`, React context, URL query param) | Month filter must be consistent across all views | REQ-003, REQ-005 |
   | `current_user` | All pages | session cookie + server-side store | Identity needed everywhere for authorization | REQ-001 |

4. **If no shared state applies** (e.g., CLI tool, pure library, strictly independent components), write the explicit disclaimer:
   *"No shared state identified — components are independent."*

   **Never leave the section empty.** An empty section is indistinguishable from "we didn't think about it". The explicit disclaimer confirms the question was considered.

**Fields semantics:**

- **Name** — the conceptual state name, not an implementation detail (`selected_month`, not `SelectedMonthProvider.state`).
- **Scope** — list of components/pages/modules that read or write this state.
- **Mechanism** — how it is stored and synchronized (session state, URL param, global store, event bus, context, etc.). Choose the framework-appropriate mechanism.
- **Rationale** — one sentence on why this state must be shared (not duplicated).
- **Traces** — REQ IDs that motivate the sharing (e.g., a REQ saying "filter applies to all views").

**Domain adaptation (P9):**

- **Web / mobile projects** — typically has 1 to 5 shared state entries (selections, user identity, theme, navigation).
- **CLI / library / scientific projects** — often zero. The disclaimer line is common and legitimate.
- **API / backend projects** — usually has shared state in the form of request context, session, DB connection pool.

**Persist** the completed section as part of the design artefact.

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

### Step 7 — Inform-Tier Decisions Summary (Creator-Activity Closure, spec P16)

Close the activity with a retrospective list of the **Inform-tier decisions** the agent made during design work (per P7 risk classification). DESIGN often contains many small autonomous choices that were individually low-stakes — typing conventions, import style, interface naming conventions, diagramming notation — none of which warranted an interruptive Gate on their own.

1. **Assemble the list** from the agent's conversation memory for this activity. Examples: *"used TypeScript types instead of Zod schemas"*, *"interface methods return `Result<T, E>` rather than throwing"*, *"used Mermaid over ASCII for the component diagram"*.

2. **If the list is empty** (rare — all choices were Gated), display explicitly: *"No inform-tier decisions made this activity — all choices were Gated."* Then conclude DESIGN.

3. **If the list is non-empty, present it and the Gate:**

   ```
   **Inform-tier decisions made during this design:**
   - {decision 1}
   - {decision 2}
   - ...

   Any of these you want to promote to a Gate decision?

   **Options:**
   1. **Accept all as-is** (default) — Record as an `## Inform-tier Decisions` section at the end of `docs/sprints/sprint-{NN}/design.md`.
   2. **Promote one or more to Gate** — For each selected decision, walk through a standard Gate (Question / Context / Options with consequence horizons / Discuss). If the user picks an alternative, the agent updates the design to reflect the new choice, and the DEC-NNN is added to `decisions.md`.
   3. **Discuss** — Explore any of the decisions before accepting or promoting.
   ```

4. Execute the chosen option. Accepted decisions are serialized as a markdown list under an `## Inform-tier Decisions` section.
