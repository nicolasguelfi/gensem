# P1 — Iterative-Incremental Development

**Category:** Foundations
**Principle:** All documents and artefacts are produced as increments within sprints, modular at the file-system level.

## Description

Development proceeds through time-boxed sprints. Each sprint produces a coherent increment of the project: a set of artefacts that are individually complete and collectively integrate into the existing baseline. Artefacts are not monolithic documents revised in-place; they are modular files that can be added, replaced, or versioned independently.

Every artefact version is associated with exactly one sprint. This association is recorded in the artefact's YAML frontmatter and mirrored in the file-system layout. Sprint artefacts are stored in a dedicated directory structure that makes temporal provenance immediately visible.

## Operational Rules

1. **Sprint directory structure** — Each sprint has a dedicated directory:
   ```
   docs/sprints/sprint-NN/
   ├── plan.md              # Sprint plan (goals, tasks, acceptance criteria)
   ├── review.md            # Sprint review (what was done, what was learned)
   ├── retrospective.md     # Sprint retrospective (process improvements)
   └── artefacts/           # Artefacts produced or modified in this sprint
   ```

2. **YAML frontmatter** — Every artefact MUST include sprint metadata:
   ```yaml
   ---
   id: REQ-012
   title: "User authentication requirements"
   sprint: 3
   status: draft | in-progress | review | done
   created: 2026-01-15
   updated: 2026-01-18
   author: human | agent | pair
   ---
   ```

3. **Git branching per sprint** — Each sprint has a base branch, and tasks within the sprint have sub-branches:
   ```
   gse/sprint-03/feat/user-auth
   gse/sprint-03/fix/login-validation
   gse/sprint-03/docs/api-reference
   ```

4. **Increment completeness** — At the end of each sprint, the `main` branch MUST contain a working, consistent baseline. No half-finished artefacts on main.

5. **Sprint numbering** — Sprints are numbered sequentially starting at 01, zero-padded to two digits (sprint-01, sprint-02, ..., sprint-99).

6. **Artefact granularity** — Prefer many small files over few large files. Each file should address one concern. A requirements document with 20 requirements should be 20 files (or grouped by feature into 4-5 files), not one monolithic document.

7. **Sprint backlog** — Each sprint begins with a plan that lists tasks derived from the product backlog. The agent MUST NOT start work without an agreed sprint plan.

## Examples

**Starting a new sprint:**
```
Agent: We're beginning Sprint 04. Here's the proposed sprint plan:

Goal: Implement user notification system
Tasks:
- TASK-041: Define notification requirements (REQ-030..REQ-035)
- TASK-042: Design notification service (DES-015)
- TASK-043: Implement email notifications (SRC-020)
- TASK-044: Write notification tests (TST-025..TST-028)

Estimated complexity budget: 12/15 points consumed.
Shall I create the sprint directory and plan? (1) Yes (2) Adjust tasks (3) Discuss
```

**Artefact file in sprint directory:**
```
docs/sprints/sprint-04/artefacts/REQ-030-notification-triggers.md
```
