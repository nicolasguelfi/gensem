---
name: assess
description: "Evaluate artefact status against project goals. Identifies covered, partial, and uncovered goals."
---

# GSE-One Assess — Gap Analysis

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Run full gap analysis against project goals |
| `--sprint`         | Assess only the current sprint's coverage |
| `--external`       | Focus assessment on external source compatibility |
| `--report`         | Generate a formal gap report document |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. Project artefacts — scan the project directory and sprint artefacts inline (same scan as `/gse:collect` Steps 1-5) to establish what exists
2. `.gse/config.yaml` — project goals and scope definition
3. `.gse/backlog.yaml` — current backlog (pool and sprint items)
4. `.gse/sources.yaml` — external sources (if any)
5. `docs/sprints/sprint-{NN}/reqs.md` — requirements for current sprint (if any)
6. `.gse/profile.yaml` — user profile (apply P9 Adaptive Communication to all output)

## Workflow

### Step 0 — Open Questions Gate (activity-entry scan, spec P6)

Before running the gap analysis, scan for pending Open Questions (`OQ-`) whose `resolves_in: ASSESS`.

1. **Enumerate sources** — list `docs/intent.md` (always) and `docs/sprints/sprint-{NN}/*.md` for the current sprint if it exists.
2. **Parse `## Open Questions`** sections. Extract entries where `status: pending` AND `resolves_in: ASSESS`.
3. **If zero matches** → skip this step, proceed to Step 1.
4. **If ≥ 1 match** → enter the Open Questions Gate per the user's `decision_involvement` (see `/gse:plan` Step 0 for the canonical three-mode description — `autonomous` / `collaborative` / `supervised`). Resolutions are recorded in the origin artefact's `## Open Questions` entry (status flipped to `resolved`, all fields populated). Substantial resolutions produce a `DEC-NNN`.
5. Proceed to Step 1.

### Step 1 — Gather Inputs

Collect all inputs needed for the analysis:

| Input | Source | Purpose |
|-------|--------|---------|
| Artefact scan | Inline scan (project files, sprint dirs, git state) | What exists |
| Project goals | `.gse/config.yaml` → `goals` | What is expected |
| Backlog items | `.gse/backlog.yaml` | What is planned |
| External sources | `.gse/sources.yaml` | What is available from outside |
| Requirements | `docs/sprints/*/reqs.md` | Formal requirements |

If the project has not been scanned recently in this session, run the artefact scan inline (Steps 1-5 of `/gse:collect`). This is lightweight — it reads the filesystem and git state, producing in-memory aggregates without persisting a file.

### Step 2 — Analyze Coverage Per Goal

For each project goal defined in `config.yaml`:

Evaluate coverage status:

| Status | Symbol | Meaning |
|--------|--------|---------|
| **Covered** | `✓` | Goal is fully addressed by existing artefacts |
| **Partial** | `◐` | Goal is partially addressed — some artefacts exist but gaps remain |
| **Uncovered** | `✗` | No artefacts address this goal |
| **At risk** | `⚠` | Artefacts exist but have quality concerns or dependency risks |

For each goal, document:
- Which artefacts contribute to it (by ID)
- What is missing (specific gaps)
- Suggested actions to close gaps

### Step 3 — External Source Assessment

For each included external source (from `.gse/sources.yaml`):

| Criterion | Evaluation |
|-----------|-----------|
| **Compatibility** | Language, framework, and paradigm alignment with project |
| **Integration cost** | Estimated effort to integrate (trivial / moderate / significant) |
| **Risk** | Dependency risk, maintenance burden, license concerns |
| **Coverage contribution** | Which goals this source helps address |

Flag sources where integration cost exceeds the benefit of building from scratch.

### Step 4 — Output Gap Report

Present the analysis in a structured format:

```
Gap Analysis — Sprint S02 — 2026-01-20
═══════════════════════════════════════

Project Goals Coverage
──────────────────────
  ✓  G1: User authentication     REQ-001, REQ-002, SRC-010..015, TST-001..005
  ◐  G2: API rate limiting       REQ-003 (defined), no implementation yet
  ✗  G3: Admin dashboard         No artefacts
  ⚠  G4: Data export             SRC-020 exists but has no tests, DES-005 incomplete

External Sources
────────────────
  SRC-001 jwt.py         → G1 (reusable as-is, trivial integration)
  SRC-002 oauth.py       → G1 (adaptable, moderate integration)
  SRC-010 rate-limit.js  → G2 (incompatible — wrong language)

Gaps Requiring Action
─────────────────────
  GAP-01: G2 needs implementation — suggest TASK for rate limiting middleware
  GAP-02: G3 entirely uncovered — suggest requirements + design tasks
  GAP-03: G4 at risk — SRC-020 needs tests, DES-005 needs completion

Summary: 1/4 goals covered, 1 partial, 1 uncovered, 1 at risk
```

### Step 5 — Feed PLAN

For each uncovered or partially covered goal, automatically generate candidate work items:

1. Create TASK entries in the backlog pool:
   - One TASK per identified gap
   - Set `traces.derives_from` to the gap ID
   - Set `status: open` and `sprint: null` (the combination `status: open` + `sprint: null` represents a task in the backlog pool — unassigned to any sprint — per the backlog.yaml schema)

2. Report created items:
```
Created 3 candidate tasks in the backlog pool:
  TASK-014 [code]        Implement rate limiting middleware (from GAP-01)
  TASK-015 [requirement] Define admin dashboard requirements (from GAP-02)
  TASK-016 [test]        Write tests for data export module (from GAP-03)

These items are in the pool. Use /gse:plan to assign them to a sprint.
```

If `--report` flag is set, save the full gap report to `docs/sprints/sprint-{NN}/assess.md` with proper artefact frontmatter.
