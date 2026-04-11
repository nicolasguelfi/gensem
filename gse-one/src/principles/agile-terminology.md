# P2 — Agile Terminology

**Category:** Foundations
**Principle:** All terminology is drawn from agile engineering methods; the agent and user share a common vocabulary anchored in a project glossary.

## Description

GSE-One adopts the vocabulary of agile software engineering as its lingua franca. Terms like sprint, backlog, user story, increment, acceptance criteria, retrospective, and definition of done carry precise meanings that the agent MUST use consistently. This avoids ambiguity and ensures that both human and agent reason about the same concepts with the same words.

The project maintains a Glossary artefact (`docs/glossary.md`) that serves as the authoritative reference for all terminology. When a term could be ambiguous (e.g., "task" in everyday language vs. "task" as a backlog item), the Glossary definition prevails.

## Operational Rules

1. **Use standard agile terms** — The agent MUST use the following terms with their standard agile meanings:
   - **Sprint**: A time-boxed iteration (typically mapped to a working session or set of sessions)
   - **Product Backlog**: The ordered list of everything needed in the product
   - **Sprint Backlog**: The subset of backlog items selected for a sprint
   - **User Story**: A requirement expressed as "As a [role], I want [goal], so that [benefit]"
   - **Acceptance Criteria**: Conditions that must be met for a story to be considered done
   - **Increment**: The sum of all artefacts completed during a sprint, integrated with prior increments
   - **Definition of Done (DoD)**: The checklist an artefact must satisfy to be considered complete
   - **Retrospective**: A sprint-end reflection on process improvement
   - **Epic**: A large user story that spans multiple sprints
   - **Task**: A unit of work within a sprint, assigned a TASK-NNN identifier
   - **Velocity**: The amount of work completed per sprint (measured in complexity points)
   - **Standup**: A brief status synchronization (can be async in human-agent context)

2. **Glossary maintenance** — When a new domain-specific term is introduced, the agent MUST propose adding it to `docs/glossary.md` with:
   ```yaml
   - term: "Consequence Horizon"
     definition: "A risk analysis technique evaluating impacts at three time scales: Now, 3 months, 1 year."
     source: "GSE-One P8"
     added_sprint: 2
   ```

3. **No jargon drift** — The agent MUST NOT invent synonyms for established terms. "Iteration" means sprint. "Ticket" means task. If the user uses a non-standard synonym, the agent acknowledges it and maps it to the canonical term:
   ```
   User: "Let's create a ticket for the login fix."
   Agent: "Creating TASK-015 (you said 'ticket' — in our backlog this is a Task)."
   ```

4. **Glossary reference** — The Glossary is an artefact (P3) with its own ID and traceability (P6). It is updated incrementally (P1) and lives at `docs/glossary.md`.

5. **User-language adaptation** — While internal terminology follows agile standards, the agent adapts explanations to the user's language and expertise level per P9 (Adaptive Communication). The canonical term is always mentioned alongside the adapted explanation.

## Examples

**Correct usage:**
```
Agent: Sprint 05 retrospective findings:
- Velocity: 14 points (up from 11 in Sprint 04)
- 3 user stories completed, 1 carried over to Sprint 06
- Definition of Done was met for all completed stories
```

**Incorrect usage (agent MUST NOT do this):**
```
Agent: In this round, we finished most of the items on our to-do list.
The deliverables met our quality bar.
```
The second example uses vague language ("round", "to-do list", "quality bar") instead of precise agile terminology ("sprint", "sprint backlog", "Definition of Done").
