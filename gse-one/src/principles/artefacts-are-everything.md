# P3 — Artefacts Are Everything

**Category:** Foundations
**Principle:** Every project file is an artefact — code, requirements, design, tests, configuration, plans, decisions, and learning notes — tracked and managed uniformly.

## Description

In GSE-One, the concept of "artefact" is deliberately broad. An artefact is any file that contributes to the project's knowledge base, whether it is source code, a requirements specification, a design diagram, a test case, a configuration file, a sprint plan, an architectural decision record, or a learning note. There is no second-class citizen: a decision log is as much a managed artefact as a Python module.

This principle ensures that nothing falls through the cracks. Every piece of project knowledge is tracked, versioned, and traceable (P6). The agent treats all artefacts with the same rigour: they have identifiers, frontmatter metadata, sprint associations (P1), and lifecycle states.

## Operational Rules

1. **Artefact types** — The following artefact types are recognized:
   | Type | Prefix | Description | Examples |
   |------|--------|-------------|----------|
   | `requirement` | REQ- | What the system must do or be | User stories, constraints, NFRs |
   | `requirement` | REQ- | What the system must do | Functional and non-functional requirements |
   | `design` | DES- | How the system is structured | Architecture docs, component designs, API specs |
   | `code` | — | Implementation files | Python modules, scripts, configurations |
   | `test` | TST- | Verification artefacts | Test cases, test plans, test reports |
   | `doc` | — | Documentation | User guides, tutorials, READMEs |
   | `config` | — | Configuration | CI/CD configs, environment settings, tool configs |
   | `import` | SRC- | Imported external content | External source with provenance (traced in `.gse/sources.yaml`) |

   Additional ID prefixes (not artefact types, but tracked entities):

   | Prefix | Entity | Examples |
   |--------|--------|----------|
   | `DEC-` | Decision | Architecture decisions logged in `.gse/decisions.md` |
   | `TASK-` | Work item | Sprint tasks and backlog items in `.gse/backlog.yaml` |
   | `RVW-` | Review finding | Findings from `/gse:review` |
   | `LRN-` | Learning note | Knowledge transfer notes in `docs/learning/` |

2. **YAML frontmatter** — Every artefact MUST have YAML frontmatter with at minimum:
   ```yaml
   ---
   id: REQ-012
   artefact_type: requirement
   title: "User can reset password via email"
   sprint: 3
   status: draft | in-progress | review | done | deprecated
   created: 2026-01-15
   updated: 2026-01-18
   author: human | agent | pair
   traces:
     derives_from: [REQ-001]
     tested_by: [TST-030, TST-031]
   ---
   ```

3. **No orphan files** — Every file in the project directory (excluding `.git/`, `__pycache__/`, and other tool-generated directories) MUST be either:
   - A tracked artefact with proper frontmatter, OR
   - Listed in a project manifest as an infrastructure file (e.g., `pyproject.toml`, `.gitignore`)

4. **Artefact lifecycle** — Every artefact follows the lifecycle: `draft` -> `in-progress` -> `review` -> `done`. An artefact can also be `deprecated` when it is superseded. Deprecated artefacts are not deleted; they remain in the repository with their status updated.

5. **Uniform treatment** — The agent applies the same quality standards to all artefact types. A sprint plan receives the same frontmatter discipline as a source code module. A learning note receives the same traceability as a requirement.

6. **File-system organization** — Artefacts are organized by type in the project structure:
   ```
   project/
   ├── docs/
   │   ├── requirements/      # REQ- artefacts
   │   ├── design/            # DES- artefacts
   │   ├── decisions/         # DEC- artefacts
   │   ├── learning/          # LRN- artefacts
   │   ├── reviews/           # RVW- artefacts
   │   ├── sprints/           # Sprint plans, reviews, retrospectives
   │   └── glossary.md        # Project glossary (P2)
   ├── src/                   # SRC- artefacts
   ├── tests/                 # TST- artefacts
   └── config/                # CFG- artefacts
   ```

## Examples

**Agent creating a new artefact:**
```
Agent: Creating decision record DEC-003 for the database choice.
File: docs/decisions/DEC-003-database-selection.md

---
id: DEC-003
artefact_type: decision
title: "Select SQLite for local development database"
sprint: 2
status: done
created: 2026-01-20
author: pair
traces:
  derives_from: [REQ-005, REQ-008]
  impacts: [DES-004, SRC-010]
---
```

**Agent detecting an orphan file:**
```
Agent: I notice `scripts/cleanup.sh` has no frontmatter and is not in the
infrastructure manifest. Should I:
1. Add it as artefact SRC-045 with proper metadata
2. Add it to the infrastructure manifest
3. Discuss
```
