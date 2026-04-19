---
id: INT-001
artefact_type: intent
title: "{project_name} — Project Intent"
sprint: 0
status: approved
created: "{YYYY-MM-DD}"
author: pair
traces:
  derives_from: []
---

# {project_name} — Project Intent

## Description (verbatim user statement)

> {exact user statement, quoted literally — no paraphrasing at this stage}

## Reformulated understanding

{agent's reformulation in plain language, validated by the user in the elicitation loop. A short bulleted list is usually clearest.}

- {bullet 1}
- {bullet 2}
- {bullet 3}

## Users

{one-line description of who uses the product — e.g., "single user, no accounts", "small shared pool (family, 2-5 people)", "public multi-user with authentication", "specific role: medical staff in a hospital ward"}

## Boundaries (explicit out-of-scope)

- {thing 1 — e.g., "no multi-device sync"}
- {thing 2 — e.g., "no server component, browser-local only"}
- {thing 3 — e.g., "no real-time collaboration"}

## Open Questions

_Optional section. Structured ambiguities auto-consumed by the **activity-entry scan** (spec P6). Each entry is scanned at the first step of `/gse:assess`, `/gse:plan`, `/gse:reqs`, or `/gse:design` based on its `resolves_in` tag._

- **OQ-001** — {question 1}
  - resolves_in: ASSESS | PLAN | REQS | DESIGN
  - impact: scope-shaping | behavioral | architectural | cosmetic
  - status: pending
  - raised_at: INT-001

- **OQ-002** — {question 2}
  - resolves_in: ...
  - impact: ...
  - status: pending
  - raised_at: INT-001
