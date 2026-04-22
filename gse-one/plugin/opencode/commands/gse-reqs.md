---
name: "gse-reqs"
description: "Define functional and non-functional requirements. Triggered by /gse:reqs."
---


# GSE-One Reqs — Requirements

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Start requirements elicitation for the current sprint |
| `--elicit`         | Run only the conversational elicitation phase (Step 0) |
| `--fr`             | Focus on functional requirements |
| `--nfr`            | Focus on non-functional requirements |
| `--show`           | Display current requirements without modification |
| `--validate`       | Check requirements for completeness and consistency |
| `--help`           | Show this command's usage summary |

## Mode-Specific Ceremony

The depth of the REQS activity depends on the project mode (`config.yaml → lifecycle.mode`):

| Step | Full mode | Lightweight mode |
|------|-----------|-----------------|
| Step 0 — Open Questions Gate (activity-entry scan) | Yes | Yes (only if pending OQ with `resolves_in: REQS` exists) |
| Step 0.5 — Conversational elicitation | Yes | Yes |
| Step 1 — Scope determination | Yes | Yes (simplified) |
| Step 2 — Functional requirements (test-driven) | Yes | Yes (fewer REQs expected: 2-5 concise items) |
| Step 3 — Non-functional requirements | Yes | Optional (agent proposes key NFRs, user decides) |
| Step 4 — User story format | Yes | No (acceptance criteria from Step 2 suffice) |
| Step 5 — Validation | Yes | Simplified (completeness + testability only) |
| Step 6 — Coverage analysis | Yes | No |
| Step 7 — Quality assurance checklist (ISO 25010) | Yes | No |
| Step 8 — Persist | Yes | Yes |

In Lightweight mode, the agent aims for 2-5 concise REQs with acceptance criteria. The quality checklist and coverage analysis are skipped — they add value for complex projects but are overhead for simple ones.

REQS is **not executed** in Micro mode.

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint number
2. `.gse/backlog.yaml` — sprint tasks that need requirements
3. `.gse/profile.yaml` — user preferences (decision involvement, verbosity)
4. `.gse/plan.yaml` — living sprint plan (for scope context)
5. `docs/sprints/sprint-{NN}/reqs.md` — existing requirements (if any)
6. `.gse/sources.yaml` — external sources that may inform requirements

## Workflow

### Step 0 — Open Questions Gate (activity-entry scan, spec P6)

Before any requirement elicitation, scan for pending Open Questions (`OQ-`) whose `resolves_in: REQS`.

1. **Enumerate sources** — list `docs/intent.md` (always) and `docs/sprints/sprint-{NN}/*.md` for the current sprint if it exists.
2. **Parse `## Open Questions`** sections. Extract entries where `status: pending` AND `resolves_in: REQS`.
3. **If zero matches** → skip this step, proceed to Step 0.5 (Conversational Elicitation).
4. **If ≥ 1 match** → enter the Open Questions Gate per the user's `decision_involvement` (see `/gse:plan` Step 0 for the canonical three-mode description — `autonomous` / `collaborative` / `supervised`). Resolutions are recorded in the origin artefact's `## Open Questions` entry in place (status flipped to `resolved`, all fields populated). Resolutions typically seed REQ-NNN acceptance criteria in the upcoming elicitation — the agent carries the resolved answers into the conversational elicitation as pre-validated input.
5. Proceed to Step 0.5.

### Step 0.5 — Conversational Elicitation

Before formalizing requirements, engage the user in a free-form conversation about their needs. This phase captures intent in natural language before imposing structure, and surfaces both functional needs and implicit quality expectations.

**Purpose:**
- Let the user articulate goals without technical constraints or format requirements
- Uncover implicit or overlooked requirements (especially quality expectations: speed, reliability, ease of use)
- Build shared understanding between agent and user on scope and priorities

**Process:**

1. **Open-ended question** — Ask: "Describe what this should do and what matters most to you. Don't worry about technical details — just describe the problem and what success looks like. Think also about how it should behave: speed, reliability, ease of use..."
2. **Active listening** — Ask clarifying questions as needed:
   - "Who will use this?" (actors)
   - "What's the main frustration it solves?" (rationale)
   - "Are there things it must never do?" (constraints)
   - "How fast should it be? Does it handle sensitive data?" (quality expectations)
3. **Synthesis** — Reformulate the user's input into 3-5 key themes, separating functional goals from quality expectations:
   - Functional themes: "Filter expenses by month", "Export to CSV"
   - Quality themes: "Must be fast even with large datasets", "Data must be secure"
4. **Validation** — Present the synthesis: "The main goals are: [theme 1], [theme 2], [theme 3]. Quality expectations: [quality 1], [quality 2]. Is that right? Anything missing?"
5. **Persist** — Save the user's original words and the agent's reformulation in the `elicitation_summary` field of the `reqs.md` frontmatter.

**Adaptation by expertise level:**

- **Beginner:** "Before I write down what the app should do, help me understand what you really need. Just talk naturally — I'll organize it later. Think about what the app does, but also how it should feel: fast? reliable? easy to use?"
- **Intermediate:** "Let's start with a quick conversation about your needs before I formalize requirements. This helps me capture priorities and quality expectations I might otherwise miss."
- **Expert:** Skip this phase if the user provides a detailed specification upfront or says "I have clear requirements." But offer: "Would a quick elicitation conversation help me understand your priorities better?" (Inform tier). If skipped, record `elicitation_summary: "Skipped — user provided detailed spec"`.

**If `--elicit` flag is used:** Run only this step, then stop. The user can continue later with `/gse:reqs` to proceed to formalization.

### Step 1 — Scope Determination

Identify which backlog items in the current sprint need requirements:

- Items of type `requirement` → these ARE the requirements to define
- Items of type `code`, `config` → derive requirements from their descriptions
- Items of type `test` → requirements should already exist (check traces)
- Items of type `design` → requirements should already exist (check traces)

Present the scope: "Sprint S02 has 5 tasks. I'll define requirements for: TASK-010 (rate limiting), TASK-013 (webhook handler), TASK-016 (CSV export)."

### Step 2 — Functional Requirements (FR) — Test-Driven

**REQS is test-driven:** every requirement MUST include testable acceptance criteria. These criteria are not decorative — they become the specification for validation tests during the TESTS activity. A requirement without testable acceptance criteria is incomplete.

For beginners: "For each feature, I'll describe what the app should do AND how we'll check it works. You'll confirm before I build anything."

**Open technical questions:** For each requirement, the agent MUST identify technical choices that are not yet resolved (e.g., data format, persistence strategy, library choice). These are listed as `open_questions` and become Gate decisions before PRODUCE. This prevents the agent from making silent arbitrary choices during coding.

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
  open_questions:          # technical choices not yet resolved → become Gate decisions before PRODUCE
    - "Persistence: localStorage, IndexedDB, or server-side?"
    - "Currency format: EUR, USD, or user-configurable?"
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

### Step 6 — Requirements Coverage Analysis

After drafting requirements, perform a proactive coverage analysis against standard requirement dimensions. For each dimension not addressed by the user's requirements, inform the user of the gap and its potential consequences, giving them the opportunity to add requirements if desired.

Standard dimensions (adapt to project type and domain):

| Dimension | Typical question |
|-----------|-----------------|
| **Functionality** | Are all user-facing features described? |
| **Data & persistence** | Where and how is data stored, backed up, migrated? |
| **User interface & visual quality** | Is there a desired look and feel, style guide, or visual standard? |
| **Accessibility** | Should the app meet accessibility standards (screen readers, contrast, keyboard nav)? |
| **Performance** | Are there response time, throughput, or resource constraints? |
| **Security** | Are there authentication, authorization, or data protection needs? |
| **Error handling** | How should the app behave when things go wrong? |
| **Deployment & operations** | Where and how will the app be deployed? |
| **Internationalization** | Does the app need to support multiple languages or locales? |

Present the analysis as a helpful summary — not a blocker. For beginners, use plain language: "I noticed you haven't mentioned how the app should look. Without guidance, I'll use a very basic design. Would you like to describe the visual style you'd prefer?" For experts, a concise gap list is sufficient. The user may choose to add requirements, explicitly defer them, or acknowledge the gap as acceptable.

### Step 7 — Quality Assurance Checklist (ISO 25010 Inspired)

After the coverage analysis, verify that non-functional requirements are **complete and measurable** using a quality checklist inspired by ISO 25010. This checklist is a **Soft guardrail** (inform + suggest), not a blocker.

#### 7a — Quality Dimensions Checklist

For each NFR written in Step 3, verify completeness against these quality dimensions:

| Quality Dimension | Checklist Items |
|-------------------|----------------|
| **Performance** | ☐ Target metric defined (e.g., "< 200ms at p95") · ☐ Measurement method specified (e.g., "k6 load test") · ☐ Load/stress conditions defined (e.g., "500 concurrent users") |
| **Security** | ☐ Threat model or attack surface identified · ☐ Authentication/authorization mechanism specified · ☐ Compliance requirements stated (e.g., "OWASP Top 10") |
| **Reliability** | ☐ Availability target defined (e.g., "99.5% uptime") · ☐ Failure mode handling described · ☐ Recovery procedure specified |
| **Usability** | ☐ Error message clarity requirement · ☐ Input validation feedback specified · ☐ Learning curve or onboarding requirement |
| **Maintainability** | ☐ Test coverage target defined · ☐ Documentation requirements stated · ☐ Modularity or coupling constraints |
| **Accessibility** | ☐ WCAG target level specified (e.g., "AA") · ☐ Keyboard navigation required · ☐ Screen reader support specified |
| **Compatibility** | ☐ Target platforms/browsers listed · ☐ Minimum versions specified · ☐ Responsive breakpoints defined |

**Scoring:** For each NFR, count checked items. Target: at least 2 out of 3 items checked per applicable dimension.

#### 7b — Gap Classification and Action

Classify gaps by priority and act accordingly:

| Priority | Dimensions | Action |
|----------|-----------|--------|
| **HIGH** | Security, Reliability, Performance | **Soft guardrail:** Agent explicitly suggests adding the missing detail. Present consequences of the gap. |
| **MEDIUM** | Usability, Maintainability, Accessibility | **Soft guardrail:** Agent suggests, user decides. |
| **LOW** | Compatibility details | **Inform only:** Mention the gap, no pressure. |

For each gap found, the user may: (1) add the missing detail to the NFR, (2) explicitly defer to a future sprint, or (3) acknowledge the gap as acceptable. Record the decision.

#### 7c — Quality Coverage Matrix

Generate a summary matrix and persist it in the requirements document:

```
Quality Assurance Summary — Sprint S{NN}
─────────────────────────────────────────

Performance:
  ✓ REQ-005 "API response < 200ms" — target metric + measurement plan defined
  ⚠ REQ-005 — stress test conditions not specified (recommend: define concurrent user count)

Security:
  ✓ REQ-003 "JWT authentication" — mechanism + token expiry defined
  ✗ Missing: rate limiting per endpoint (HIGH — recommend adding)

Reliability:
  ✓ No reliability NFRs — user acknowledged as acceptable for MVP

... (one section per applicable quality dimension)
```

**Adaptation by expertise level:**

- **Beginner:** "I checked whether each quality requirement is fully detailed. Here's what's complete and what might need more detail: [plain-language summary, one dimension at a time]"
- **Intermediate:** Present the summary matrix with brief explanations.
- **Expert:** "Quality checklist: 7/8 NFRs fully specified. Rate limiting unspecified — add to REQ-007 or defer?"

### Step 7.5 — Requirements Quality Pass (requirements-analyst sub-agent)

Once the REQ list is drafted (Steps 1-6) and the inline Quality Checklist (Step 7) has surfaced dimension-level gaps, invoke the `requirements-analyst` sub-agent (`$(cat ~/.gse-one)/agents/requirements-analyst.md` — adopt this role) to run its **checklist against the drafted REQ entries**. This is a REQ-level audit (per-REQ) complementing Step 7's dimension-level audit.

The agent returns findings tagged `[REQ-QUALITY]` covering:
- **Completeness** — no orphan REQ without acceptance criteria, no incomplete FR/NFR pair.
- **Testability** — each REQ has at least one measurable verification path (Given/When/Then or equivalent).
- **Ambiguity** — no vague terms ("fast", "secure", "user-friendly") without a numeric threshold or observable criterion.
- **Inter-REQ consistency** — no pair of REQs contradicts the other (REQ-003 "JWT with 15 min expiry" vs REQ-008 "sessions persist across browser restarts" is a contradiction).
- **Alignment with INT-001** — no REQ strays from the intent described in `docs/intent.md` (if present).

**Triage:**
- HIGH or MEDIUM findings **must be resolved before Persist**: the user may amend the REQ inline, or accept the REQ as-is and create a DEC-NNN documenting the accepted risk.
- LOW findings are appended to the sprint's `reqs.md` under an `## Open Questions` section with `resolves_in: DESIGN | PRODUCE` or `status: accepted` if deemed acceptable.

**Beginner adaptation** (per P9): instead of listing findings with tags, present them as plain-language questions: *"REQ-003 talks about 'fast response' — do you have a specific time limit in mind? e.g., under 1 second."*

### Step 8 — Persist

Save requirements to `docs/sprints/sprint-{NN}/reqs.md`:

```yaml
---
gse:
  type: requirement
  sprint: {NN}
  branch: gse/sprint-{NN}/integration
  elicitation_summary: "{user's original words + agent's reformulation from Step 0.5}"
  status: draft                        # draft | reviewed | approved
  created: "{YYYY-MM-DD}"
  updated: "{YYYY-MM-DD}"
  traces:
    derives_from: [PLN-{NNN}]          # Plan that scheduled this sprint's REQs
    decided_by: []                     # e.g., [DEC-NNN] — shaping decisions
---
```

Present requirements for user approval (Gate). Set status to `approved` once confirmed.

**Beginner presentation rule:** For beginner users, do NOT just give the file path and ask the user to open it. Instead, display a **summary of the requirements inline in the chat** including:
- Each requirement title and its acceptance criteria (Given/When/Then) in plain language
- Any open technical questions that need the user's decision
- The file path for reference ("The full document is saved at `docs/sprints/sprint-{NN}/reqs.md` if you want to read the details")
- A clear validation question: "Does this match what you want? Is anything wrong or missing?"

This ensures the beginner can validate without navigating the file system.
