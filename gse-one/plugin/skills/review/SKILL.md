---
description: "Review all artefacts in current sprint. Operates on branch diff. Includes devil's advocate (P16). Triggered by /gse:review."
---

# GSE-One Review — Review

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Review all unreviewed tasks in the current sprint |
| `--task TASK-ID`   | Review a specific task |
| `--devil-only`     | Run only the devil's advocate pass (skip standard review) |
| `--standard-only`  | Run only the standard review (skip devil's advocate) |
| `--severity HIGH`  | Filter findings by minimum severity |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state
2. `.gse/config.yaml` — project configuration (language, framework, review settings)
3. `.gse/backlog.yaml` — tasks with `status: done` (candidates for review)
4. `.gse/profile.yaml` — user expertise level (affects finding presentation)

## Workflow

### Step 0 — Pre-review Guardrails (Hard)

Before reviewing any TASK, verify test execution:

1. **Check test evidence** — For each TASK with `status: done`, read `test_evidence` in `backlog.yaml`.
2. **If test evidence is absent or `status: skipped`** — **Hard guardrail: block review.** Report: "Tests were not run for this task. Tests must pass before review." For beginners: "I need to verify that what I built works correctly before I check my own work. Let me run the tests first." Then execute tests for this TASK and return to review only after tests pass.
3. **If test evidence `status: fail`** — **Soft guardrail: warn and continue.** Report: "Tests are currently failing for this task. Review will proceed, but test failures will be included as findings." Add a RVW- finding with severity HIGH for the failing tests.
4. **If test evidence `status: pass`** — Proceed to Step 1.

### Step 1 — Identify Review Scope

1. Read `backlog.yaml` and select tasks with `status: done` that have not been reviewed
2. For each task, identify the feature branch: `git.branch` field
3. Generate the diff against the sprint branch:
   ```
   git diff gse/sprint-{NN}...gse/sprint-{NN}/{type}/{name}
   ```
4. The review operates on the **diff**, not the full file state. This ensures focus on what changed.

### Step 2 — Standard Review

Execute review from multiple specialized perspectives. Each perspective produces findings tagged with its agent role.

#### 2a — Code Quality (code-reviewer agent)

- Clean code principles (naming, structure, duplication)
- Language-specific idioms and best practices
- Error handling completeness
- Performance considerations
- Documentation quality (comments, docstrings)

#### 2b — Security (security-auditor agent)

- Input validation
- Authentication and authorization patterns
- Secrets exposure (hardcoded credentials, API keys)
- Dependency vulnerabilities (if manifest changed)
- Injection risks (SQL, XSS, command injection)

#### 2c — Requirements Completeness (requirements-analyst agent)

- Trace each change back to a requirement (REQ-NNN)
- Identify untested requirements
- Detect scope creep (changes not traced to any requirement)
- Verify acceptance criteria satisfaction

#### 2d — Design Coherence (architect agent)

- Consistency with documented design decisions (DES-NNN)
- Architectural pattern adherence
- Module coupling and cohesion
- Interface contract compliance

#### 2e — Test Coverage (test-strategist agent)

- Test existence for new/changed code
- Test quality (meaningful assertions, edge cases)
- Coverage gaps
- Test naming and organization

#### 2f — UX Review (ux-advocate agent, for web/UI projects)

- Only activated if project type involves UI (detected from config or file extensions)
- Accessibility compliance
- Responsive design
- User flow consistency
- Error state handling in UI

### Step 3 — Devil's Advocate (P16)

After the standard review completes, run the devil's advocate pass. This is a meta-review that challenges the AI's own work.

#### 3a — Hallucination Hunt

- Verify all referenced libraries exist: run `pip show {lib}` / `npm list {lib}` / equivalent
- Verify all referenced APIs exist in the library version used
- Check that URLs in code or documentation are plausible
- Flag any assertion that cannot be verified from the codebase

#### 3b — Assumption Challenge

- Identify implicit assumptions in the code
- Challenge "happy path only" implementations
- Question default values and magic numbers
- Verify error messages match actual error conditions

#### 3c — Complaisance Detection

- Detect if the AI accepted user instructions that conflict with best practices
- Flag cases where the AI should have pushed back
- Identify over-engineering driven by user request rather than need
- Check for cargo-cult patterns (copied without understanding)

#### 3d — Edge Case Coverage

- Identify untested boundary conditions
- Check for off-by-one errors
- Verify null/empty/zero handling
- Test concurrent access scenarios (if applicable)

#### 3e — Temporal Validity

- Check that referenced tools/APIs are not deprecated
- Verify version compatibility claims
- Flag patterns that are outdated for the language version in use

All devil's advocate findings are tagged with `[AI-INTEGRITY]`.

#### 3f — Passive Acceptance Detection (P16)

Track these 5 signals at the **root level** of `status.yaml` (per spec Section 12.4 — flat fields, not nested):
- `consecutive_acceptances` — count of review rounds where user accepted all findings without discussion
- `never_discusses` — user has never chosen "Discuss" on any Gate decision this sprint
- `terse_responses` — user responds with single words ("ok", "yes", "fine") >80% of the time
- `never_modifies` — user has never requested a change to agent output this sprint
- `never_questions` — user has never asked a clarifying question this sprint

When `consecutive_acceptances` reaches threshold (beginner=3, intermediate=5, expert=8): trigger a pushback checkpoint — present the 3 most impactful recent decisions and ask: "I want to make sure we're aligned. Do these choices still look right?"

**Suppression rule:** If the user responds "Everything looks good" (or equivalent affirmation) to **two consecutive** pushback checkpoints, suppress further pushback for the rest of the sprint. Record in `status.yaml` at root level: `pushback_suppressed: true`. This prevents the agent from harassing a user who has genuinely reviewed and approved.

#### P15 Confidence Integration (Design 5.11)

After collecting devil's advocate findings, cross-reference with the original confidence level of each claim:

- Findings where original confidence was **Moderate** or **Low**: severity is **escalated one level** (LOW → MEDIUM, MEDIUM → HIGH)
- Findings where original confidence was **Verified** but the verification turns out to be **wrong**: severity becomes **CRITICAL** — this is the most dangerous failure mode (false certainty)

### Step 4 — Generate Review Report

For each finding, create a structured entry:

```
RVW-{NNN}:
  severity: HIGH | MEDIUM | LOW
  perspective: {agent-role}
  location:
    branch: gse/sprint-{NN}/{type}/{name}
    file: {path}
    line: {range}
  finding: "{description}"
  suggestion: "{proposed fix}"
  tags: [AI-INTEGRITY]  # if from devil's advocate
  task: TASK-{ID}
```

Persist findings to `docs/sprints/sprint-{NN}/review.md`.

### Step 5 — Update Health Score

Compute impact on health dimensions:
- `review_findings`: based on count and severity of findings
- `ai_integrity`: based on `[AI-INTEGRITY]` findings
- `test_coverage`: based on test-strategist findings
- `design_debt`: based on architect findings

Update `.gse/status.yaml` health scores.

### Step 6 — Present Summary

Report:
- Total findings: {count} (HIGH: {n}, MEDIUM: {n}, LOW: {n})
- AI-INTEGRITY findings: {count}
- Tasks reviewed: {list}
- Health score delta

If findings with severity HIGH exist:
- Recommend `/gse:fix` before delivery
- Present findings sorted by severity

Update `status.yaml`:
- `last_activity: review`
- `last_activity_timestamp: {now}`
