# P6 — Traceability

**Category:** Foundations
**Principle:** Every artefact is traceable to its origin and related artefacts through a unique identifier and explicit trace links.

## Description

Traceability is the ability to follow an artefact from its origin (why it exists) through its implementation (how it was built) to its verification (how we know it works). In GSE-One, traceability is achieved through a systematic identification scheme and explicit trace links recorded in YAML frontmatter.

Every artefact receives a unique identifier upon creation. These identifiers are never recycled: if artefact REQ-012 is deprecated, no future artefact will ever be assigned REQ-012. Trace links connect artefacts across types, enabling impact analysis ("if this requirement changes, which tests are affected?") and coverage analysis ("which requirements have no tests?").

## Operational Rules

1. **ID allocation prefixes** — Each artefact type has a designated prefix:

   | Prefix | Artefact Type | Example |
   |--------|---------------|---------|
   | `REQ-` | Requirement | REQ-001, REQ-042 |
   | `DES-` | Design | DES-001, DES-015 |
   | `TST-` | Test | TST-001, TST-030 |
   | `RVW-` | Review | RVW-001, RVW-008 |
   | `DEC-` | Decision | DEC-001, DEC-003 |
   | `TASK-` | Task | TASK-001, TASK-055 |
   | `SRC-` | External source | SRC-001, SRC-003 |
   | `LRN-` | Learning note | LRN-001, LRN-012 |

2. **ID uniqueness** — IDs are unique within the project scope. The agent maintains a counter per prefix. IDs are NEVER recycled. If REQ-005 is deprecated, the next requirement is REQ-006 (or whatever the next unused number is), never REQ-005 again.

3. **ID registry** — The agent maintains an ID registry at `docs/id-registry.md` (or `.yaml`) that maps each allocated ID to its file path and status. This is the authoritative source for "what IDs exist."

4. **Trace link types** — Four typed link categories are used in frontmatter:

   | Link type | Meaning | Example |
   |-----------|---------|---------|
   | `derives_from` | "I come from..." | REQ derives from TASK, DES derives from REQ |
   | `implements` | "I realize/validates..." | Code implements DES, test validates REQ |
   | `decided_by` | "This choice is justified by..." | DES justified by DEC |
   | `related_to` | "Related to..." | Catch-all for weak/informational links |

   ```yaml
   traces:
     derives_from: []    # This artefact was derived from these artefacts
     implements: []      # This artefact implements or validates these artefacts
     decided_by: []      # This artefact was shaped by these decisions
     related_to: []      # Informational relationship (no formal dependency)
   ```

   Only include the link types that apply — omit empty ones for brevity:
   ```yaml
   # Minimal example — only 1 link type needed:
   traces:
     derives_from: [REQ-007]
   ```

5. **Bidirectional consistency** — Trace links imply a reverse relationship. If artefact A says `implements: [REQ-007]`, then REQ-007 is implemented by A. The agent MUST maintain bidirectional consistency when creating or updating trace links.

   | If A says... | Then B should reference A via... |
   |-------------|--------------------------------|
   | `derives_from: [B]` | B is derived into A |
   | `implements: [B]` | B is implemented/validated by A |
   | `decided_by: [B]` | B justifies A |
   | `related_to: [B]` | B is related to A |

6. **artefact_type field** — Every artefact's frontmatter MUST include an `artefact_type` field with one of: `code`, `requirement`, `design`, `test`, `doc`, `config`, `decision`, `task`, `review`, `learning`, `import`.

7. **Impact analysis** — Before modifying any artefact, the agent MUST check its trace links to identify potentially impacted artefacts. If impacts are found, they are reported to the human:
   ```
   Agent: Modifying REQ-012 will impact:
   - DES-007 (implements REQ-012)
   - TST-030, TST-031 (test REQ-012)
   - SRC-015 (source implementing DES-007)
   Shall I proceed and update the impacted artefacts?
   ```

8. **Coverage analysis** — The agent can generate coverage reports on request:
   - Requirements without tests
   - Designs without implementations
   - Decisions without traceability to requirements

## Examples

**Full frontmatter with traceability:**
```yaml
---
id: DES-007
artefact_type: design
title: "Authentication service component design"
sprint: 3
status: done
created: 2026-01-20
updated: 2026-01-22
author: pair
traces:
  derives_from: [REQ-010, REQ-011, REQ-012]
  decided_by: [DEC-003]
---
```

**ID registry excerpt:**
```markdown
| ID       | File                                    | Status     | Sprint |
|----------|-----------------------------------------|------------|--------|
| REQ-001  | docs/requirements/REQ-001-login.md      | done       | 1      |
| REQ-002  | docs/requirements/REQ-002-logout.md     | done       | 1      |
| REQ-003  | docs/requirements/REQ-003-register.md   | deprecated | 2      |
| DES-001  | docs/design/DES-001-architecture.md     | done       | 1      |
| TASK-001 | docs/sprints/sprint-01/plan.md#task-001  | done       | 1      |
```
