---
description: "Capitalize learnings across 3 axes. Triggered by /gse:compound at end of sprint."
---

# GSE-One Compound — Capitalization

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Run full capitalization across all 3 axes |
| `--axis project`   | Capitalize project learnings only (Axe 1) |
| `--axis methodology` | Capitalize methodology feedback only (Axe 2) |
| `--axis competencies` | Capitalize competency notes only (Axe 3) |
| `--learn`          | Proactively propose LEARN items for the user |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state
2. `.gse/config.yaml` — project configuration
3. `.gse/backlog.yaml` — completed sprint tasks and their history
4. `.gse/profile.yaml` — user profile, competency map, learning notes
5. `docs/sprints/sprint-{NN}/review.md` — review findings for the sprint
6. `docs/sprints/sprint-{NN}/release.md` — release notes (if delivery occurred)

## Workflow

### Step 1 — Axe 1: Project Capitalization

Analyze the sprint for project-level learnings:

1. **Patterns discovered** — Identify recurring code patterns, architectural decisions, or conventions that emerged during the sprint. Record as reusable patterns.

2. **Errors and anti-patterns** — Extract lessons from review findings (especially HIGH severity), failed tests, and fix cycles. Document what went wrong and how to prevent recurrence.

3. **Best practices confirmed** — Identify practices that worked well (clean test coverage, good naming, effective decomposition). Reinforce these as project conventions.

4. **Technical debt identified** — Flag shortcuts taken during the sprint that should be addressed in future sprints. Add to backlog pool with `artefact_type: refactor`.

5. Persist to `docs/sprints/sprint-{NN}/compound.md`:

```markdown
# Sprint S{NN} — Capitalization

## Patterns
- {pattern}: {description and when to apply}

## Lessons Learned
- {lesson}: {context and prevention strategy}

## Best Practices Confirmed
- {practice}: {evidence of effectiveness}

## Technical Debt
- {debt item}: {impact and remediation suggestion}
```

### Step 2 — Axe 2: Methodology Capitalization

Analyze what worked and what did not in the GSE-One methodology itself during this sprint:

1. **Effective practices** — Which GSE-One activities, principles, or agent perspectives added value?
2. **Friction points** — Where did the methodology slow down or add unnecessary ceremony?
3. **Missing capabilities** — What did the user need that GSE-One does not provide?
4. **Improvement proposals** — Concrete, actionable suggestions for GSE-One evolution

**Filtering criteria** (only propose issues that meet ALL):
- Actionable — has a clear implementation path
- Observed in 2+ sprints OR confirmed by user as important
- Not already reported (check existing issues if possible)

If proposals pass the filter:
1. Read `plugin.json` to get the `repository` field for the GSE-One repo
2. Present proposals to user (Gate): "I identified {N} methodology improvements. Shall I create issues on the GSE-One repository?"
3. If accepted, prepare issue drafts (actual creation happens in `/gse:integrate`)

### Step 3 — Axe 3: Competency Capitalization

Feed the user's learning journey:

1. **Update learning notes** — Based on sprint activity, aggregate contextual tips:
   - New tools or techniques the user encountered
   - Concepts that required explanation during the sprint
   - Skills demonstrated (evidence of growth)

2. **Update competency map** — In `profile.yaml`, adjust competency assessments:
   - Increase confidence for skills practiced successfully
   - Identify gaps revealed by sprint challenges
   - Suggest next learning targets

3. **Proactive LEARN proposals** — This is the natural moment to propose learning items:
   - "During this sprint, you worked with {topic}. Would you like me to add a learning note about {specific concept}?"
   - Present as low-pressure suggestions, not requirements

### Step 4 — Persist and Finalize

1. Write `docs/sprints/sprint-{NN}/compound.md` with all three axes
2. Update `status.yaml`:
   - `last_activity: compound`
   - `last_activity_timestamp: {now}`
   - `lifecycle_phase: LC03`
3. Report capitalization summary:
   - Patterns documented: {count}
   - Lessons learned: {count}
   - Methodology proposals: {count}
   - Learning notes added: {count}
4. Propose next step: `/gse:integrate` to route solutions to their targets
