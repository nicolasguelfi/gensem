---
gse:
  type: requirement
  sprint: 1                            # numeric sprint number
  branch: gse/sprint-{NN}/integration    # replaced at instantiation by /gse:reqs
  elicitation_summary: ""              # Step 0 output: user's needs in their own words + agent reformulation
  traces:
    derives_from: []                   # e.g., [PLN-NNN] — plan that scheduled these REQs
    decided_by: []                     # e.g., [DEC-NNN] — shaping decisions
  status: draft                        # draft | reviewed | approved
  created: ""
  updated: ""
---

# Requirements — Sprint {sprint}

> ID convention: REQ-001..REQ-099 for functional requirements, REQ-101..REQ-199
> for non-functional requirements. The `type` field per REQ remains authoritative.

## Functional Requirements

### REQ-001 — {title}

- **Type:** functional
- **Actor:** {who}
- **Capability:** {what}
- **Rationale:** {why}
- **Priority:** Must | Should | Could
- **Acceptance Criteria:**
  1. {measurable criterion 1}
  2. {measurable criterion 2}
- **Traces:** derives_from (TASK-NNN) | tested_by (TST-001, TST-002)

### REQ-002 — {title}

- **Type:** functional
- **Actor:** {who}
- **Capability:** {what}
- **Rationale:** {why}
- **Priority:** Must | Should | Could
- **Acceptance Criteria:**
  1. {measurable criterion 1}
  2. {measurable criterion 2}
- **Traces:** implements (—) | tested_by (—)

## Non-Functional Requirements

### REQ-101 — Performance

- **Type:** non-functional
- **Metric:** {e.g., response time}
- **Target:** {e.g., < 200ms at p95}
- **Measurement:** {how it will be verified}
- **Priority:** Must | Should | Could

### REQ-102 — Security

- **Type:** non-functional
- **Metric:** {e.g., OWASP compliance}
- **Target:** {e.g., no critical vulnerabilities}
- **Measurement:** {how it will be verified}
- **Priority:** Must | Should | Could

### REQ-103 — Accessibility

- **Type:** non-functional
- **Metric:** {e.g., WCAG level}
- **Target:** {e.g., WCAG 2.1 AA}
- **Measurement:** {how it will be verified}
- **Priority:** Must | Should | Could

## Traceability Matrix

| Req ID  | Design | Tests | Status   |
|---------|--------|-------|----------|
| REQ-001 |        |       | draft    |
| REQ-002 |        |       | draft    |
| REQ-101 |        |       | draft    |
| REQ-102 |        |       | draft    |
| REQ-103 |        |       | draft    |

## Quality Coverage Matrix

_Results of the ISO 25010-inspired quality assurance checklist (Step 7 of `/gse:reqs`)._

| Quality Dimension | Covered? | Requirements | Gaps / Deferred |
|-------------------|----------|--------------|-----------------|
| Performance       |          |              |                 |
| Security          |          |              |                 |
| Reliability       |          |              |                 |
| Usability         |          |              |                 |
| Maintainability   |          |              |                 |
| Accessibility     |          |              |                 |
| Compatibility     |          |              |                 |

## Open Questions

_Questions that need resolution before requirements are finalized._

1. {question}
