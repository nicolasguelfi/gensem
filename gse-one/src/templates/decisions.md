# Decision Journal

<!-- Append DEC-NNN entries below. Gate/Inform: full format. Auto-tier: logged in decisions-auto.log. -->
<!-- Target: .gse/decisions.md -->
<!-- This is the AUTHORITATIVE format — spec §11 and activities reference this template. -->

## Format

Each DEC-NNN entry follows this canonical structure. The `sprint:` field is REQUIRED — it lets `/gse:compound` Axis 2 filter entries by sprint.

### DEC-NNN — <Short title>

- **Sprint:** {NN}                           <!-- integer sprint number; `null` for pre-sprint-1 decisions (e.g., Intent Capture, Adopt Mode choices) -->
- **Type:** scope-shaping | architectural | methodology-deviation | behavioral | cosmetic
- **Tier:** Gate | Inform | Auto             <!-- per spec §P7 — Risk-Based Decision Classification -->
- **Date:** YYYY-MM-DD
- **Decision:** <what was decided, one sentence>
- **Context:** <why this decision was needed — the situation that prompted it>
- **Options considered:** <if Tier=Gate: list the options presented to the user; otherwise: "not applicable (Inform/Auto tier)">
- **Rationale:** <why this option was chosen — link to requirements, constraints, or trade-offs>
- **Consequences:** <P8 consequence horizons — impact on scope, time, cost, quality, security, reversibility>
- **Traces:** derives_from: [OQ-NNN | REQ-NNN | DES-NNN | ...]   <!-- optional, list of related artefact IDs -->

<!-- Begin DEC entries below this line. Entries are appended chronologically. -->
