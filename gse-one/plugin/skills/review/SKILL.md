---
name: review
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
3. `.gse/backlog.yaml` — tasks with `status: review` (candidates for review — set by `/gse:produce`)
4. `.gse/profile.yaml` — user expertise level (affects finding presentation)

## Workflow

### Step 0 — Pre-review Guardrails (Hard)

**Sprint Freeze Check** (applied before test-evidence verification) — Read `.gse/plan.yaml`. If absent (Micro mode), skip this check. If `plan.yaml.status == active`, proceed to the test-evidence check below. If `plan.yaml.status ∈ {completed, abandoned}`, the current sprint is **frozen**: do NOT transition any TASK forward and do NOT add RVW findings to the frozen sprint's `review.md`. Present the Sprint Freeze Gate:

> **Question:** The current sprint (S{NN}) plan status is `{completed|abandoned}` — it is frozen. Review cannot add findings to a frozen sprint.
>
> **Options:**
> 1. **Start next sprint now** (recommended, default) — I'll run the next-sprint opening sequence: in Lightweight mode `/gse:plan --strategic`; in Full mode `/gse:collect` > `/gse:assess` > `/gse:plan --strategic`. Once Sprint S{NN+1} is active, I'll run the review there.
> 2. **Cancel** — Abort this `/gse:review` invocation. No changes will be made.
> 3. **Discuss** — Explore the trade-offs.

On option 1: invoke the mode-appropriate opening sequence inline; after promotion, re-read `.gse/status.yaml → current_sprint` and proceed to the test-evidence check below in the new sprint context. On option 2: stop execution. On option 3: explain the Sprint Freeze invariant, then re-present the Gate.

**Test-evidence verification (applied after Sprint Freeze passes):**

Before reviewing any TASK, verify test execution:

1. **Check test evidence** — For each TASK with `status: review` (i.e., produced and awaiting review), read `test_evidence` in `backlog.yaml`.
2. **If test evidence is absent or `status: skipped`** — **Hard guardrail: block review.** Report: "Tests were not run for this task. Tests must pass before review." For beginners: "I need to verify that what I built works correctly before I check my own work. Let me run the tests first." Then execute tests for this TASK and return to review only after tests pass.
3. **If test evidence `status: fail`** — **Soft guardrail: warn and continue.** Report: "Tests are currently failing for this task. Review will proceed, but test failures will be included as findings." Add a RVW- finding with severity HIGH for the failing tests.
4. **If test evidence `status: pass`** — Proceed to Step 1.

### Step 1 — Identify Review Scope

1. Read `backlog.yaml` and select tasks with `status: review` (i.e., TASKs that `/gse:produce` has marked ready for review and that have not yet been reviewed). The `review` status is set by PRODUCE; REVIEW consumes it and promotes it to either `reviewed` (clean) or `fixing` (findings) at Step 6.
2. For each task, identify the feature branch: `git.branch` field
3. Generate the diff against the sprint branch:
   ```
   git diff gse/sprint-{NN}/integration...gse/sprint-{NN}/{type}/{name}
   ```
4. The review operates on the **diff**, not the full file state. This ensures focus on what changed.

### Step 2 — Parallel Review via Sub-agents

**REVIEW is a parallel isolated activity** — each review perspective runs as a **separate sub-agent** with its own isolated context. This provides both a fresh context for each reviewer and faster execution.

**Before delegation**, the orchestrator:
1. Saves a mini-checkpoint (`.gse/checkpoints/pre-review-{timestamp}.yaml`)
2. Prepares the review context: diff output (from Step 1), state files, sprint artefacts
3. Spawns review sub-agents **in parallel**:
   - **Claude Code:** Multiple `Agent` tool calls in a single message (parallel execution)
   - **Cursor:** Multiple subagents (up to 8 in parallel)

**Each sub-agent receives:**
- Its specialized agent definition (from `agents/` directory)
- The diff to review (from Step 1)
- Relevant sprint artefacts (reqs.md, design.md, test-strategy.md)
- `profile.yaml` (for P9 adaptation)
- Instructions to return findings in the RVW-NNN format

**After all sub-agents return**, the orchestrator merges all findings into a single `review.md`, deduplicates, and proceeds to Step 3 (Devil's Advocate).

#### Sub-agents to spawn in parallel:

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
- Verify quality checklist was completed during REQS (Step 7). If the quality coverage matrix is absent from `reqs.md` → create finding severity MEDIUM: "Quality assurance checklist was not run during requirements phase — NFR completeness unverified"

#### 2d — Design Coherence (architect agent)

- Consistency with documented design decisions (DES-NNN)
- Architectural pattern adherence
- Module coupling and cohesion
- Interface contract compliance

#### 2e — Test Implementation Review & Regression Scan (test-strategist agent — IMPL tier)

Findings tagged `[IMPL]`. This is the **always-on** third tier of the Test Review Layering (spec §6.5). The two upstream tiers (STRATEGY, TST-SPEC) run during `/gse:tests` under their own triggers.

Focus of this pass — **alimentation** (are the written tests meaningful?):
- Assertions that truly exercise the behavior (no tautological tests like `assert True` or `assert result == result`)
- Fixtures realistic and isolated (no shared mutable state between tests)
- Edge cases actually covered (empty, null, boundary values, error states)
- Test names map cleanly to the TST- they implement (if a TST- review finding exists, flag the inconsistency)
- Test quality (meaningful messages, descriptive names, no dead code)
- Coverage gaps on touched files (not strategy-level — that was tier STRATEGY)

**Regression scan** (unchanged, part of this step): Execute the **full test suite** (not just tests for the current TASK). Compare pass/fail counts with the last sprint's test report in `docs/sprints/sprint-{NN-1}/test-reports/`. If tests that passed in the previous sprint now fail → create a finding with severity **HIGH** and tag `[REGRESSION]`. For beginners: "I found that something that worked before stopped working after this change."

#### 2f — UX Review (ux-advocate agent, for web/UI projects)

- Only activated if project type involves UI (detected from config or file extensions)
- Accessibility compliance
- Responsive design
- User flow consistency
- Error state handling in UI

#### Finding merge protocol

After all parallel sub-agents return:
1. Collect all findings from each sub-agent
2. Deduplicate: if two agents report the same issue (same file, same line range, same category), keep the higher-severity finding and note both perspectives
3. Assign sequential RVW-NNN IDs to the merged findings
4. Write the merged findings to `docs/sprints/sprint-{NN}/review.md`

### Step 3 — Devil's Advocate (P16)

After the standard review completes, **spawn the devil-advocate sub-agent in its own fresh context** (`"$(cat ~/.gse-one)/agents/devil-advocate.md"` via the runtime's subprocess/spawn facility, with a context brief per the orchestrator's Sub-agent delegation protocol — NOT inline role adoption: the pass must not inherit the main conversation's accumulated rationalizations, or it will re-validate them). This is a meta-review that challenges the AI's own work.

**Fallback and trace:** if the runtime cannot spawn a sub-agent, run the pass inline AND emit an Inform note (*"[Inform] Devil's advocate pass running inline — sub-agent spawn unavailable on this runtime."*, same pattern as the P4 runtime-forced fallback). In both cases, record the execution mode in the AI Integrity Findings section of `review.md`: `DA execution: isolated` or `DA execution: inline-degraded`. Opportunistic enhancement: if the spawn facility exposes model selection, prefer a different model than the one that produced the artefacts (best-effort — weights-level blind spots are context-independent).

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

Track these 2 signals at the **root level** of `status.yaml` (per spec §12.4 — Status State File, flat fields, not nested):
- `consecutive_acceptances` — count of review rounds where the user accepted all findings without discussion (primary trigger)
- `pushback_dismissed` — number of times the user dismissed a pushback checkpoint with "Everything looks good" (governs per-sprint suppression)

Both counters are written via `counters.py` (incr/reset — registry incantation; writer contract in spec §P16 — the orchestrator owns the writes, never hand-edits the YAML).

When `consecutive_acceptances` reaches threshold (beginner=3, intermediate=5, expert=8): trigger a pushback checkpoint — present the 3 most impactful recent decisions and ask: "I want to make sure we're aligned. Do these choices still look right?"

**Suppression rule:** If the user responds "Everything looks good" (or equivalent affirmation) to **two consecutive** pushback checkpoints (`pushback_dismissed >= 2`), suppress further pushback for the rest of the sprint. This prevents the agent from harassing a user who has genuinely reviewed and approved. **Beginner exception** (`profile.yaml → dimensions.it_expertise: beginner`): suppress for the next **3 Gates** only, and have the coach emit one Inform note when suppression activates (per spec §P16 — User Pushback Encouragement).

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
  status: open          # open | fixed — flipped to `fixed` by /gse:fix Step 5; counted by status.yaml review_findings_open
  fixed_by_commit: ""   # optional — set by /gse:fix when resolved
```

Persist findings to `docs/sprints/sprint-{NN}/review.md` (authoritative format in `plugin/templates/sprint/review.md`).

### Step 5 — Update Health Score

*(Merged into Step 6 — health dimensions are written once, by the mandatory 8-dimension update in Step 6 — Present Summary. This heading is retained to keep step numbering stable for cross-references; do not perform a separate write here.)*

### Step 6 — Present Summary

Report:
- Total findings: {count} (HIGH: {n}, MEDIUM: {n}, LOW: {n})
- AI-INTEGRITY findings: {count}
- Tasks reviewed: {list}
- Health score delta

**Update TASK statuses** in `backlog.yaml` based on review results:
- If HIGH or MEDIUM findings exist for a TASK → set `status: fixing` (requires `/gse:fix` before delivery)
- If no HIGH or MEDIUM findings → set `status: reviewed` and `completed_at: {timestamp}` (the TASK reached a terminal pre-merge state — per the backlog.yaml schema, `completed_at` is set when status → `done` or `reviewed`). LOW findings are tracked but non-blocking; the user can still address them via `/gse:fix --severity LOW`, which would transition `reviewed` → `fixing` → `done`

**Rationale:** this threshold aligns with the canonical rule in spec §14 and design §10.1 (FIX is inserted into `workflow.pending` if HIGH or MEDIUM findings exist). MEDIUM findings weight significantly in the `review_findings` health formula (×0.8); letting them pass without triage would silently accumulate tech debt. The user retains full agency via `/gse:fix --severity HIGH` to narrow the fix scope. The distinction between `reviewed` (clean first pass) and `done` (fixed after findings) preserves the signal for coach Axis 5 (`quality_trends`): a high ratio of `reviewed` vs `done` indicates high PRODUCE quality.

If findings with severity HIGH or MEDIUM exist:
- Recommend `/gse:fix` before delivery
- Present findings sorted by severity (HIGH first, then MEDIUM, then LOW)

> **State transition note (v0.53.0):** `status.yaml` cursor fields (`last_activity`, `last_activity_timestamp`) are maintained centrally by the orchestrator after the activity closes — see `plugin/agents/gse-orchestrator.md` — section "Sprint Plan Maintenance", and `gse-one-implementation-design.md` §10.1 — Sprint Plan Lifecycle. Activity-local state (TASK statuses, health scores) remains authored here.

**Update health scores in `status.yaml`** (MANDATORY after every review). Compute the 8 health dimensions (`requirements_coverage`, `test_pass_rate`, `design_debt`, `review_findings`, `complexity_budget`, `traceability`, `git_hygiene`, `ai_integrity`) exactly as specified in `/gse:health` Step 2 — Calculate Dimensions — the canonical formula source in the distributed plugin (mirrors spec §7.1 — Dimension computation). Write them under the canonical nested path `status.yaml → health.dimensions.<dimension>`, then update `health.score` (mean of enabled dimensions) and `health.last_computed` (ISO 8601). These values are read by the dashboard to populate the health radar chart. Without them, the radar shows empty.

**Update `status.yaml.review_findings_open`** — set this counter to the total count of HIGH + MEDIUM findings currently unresolved across all sprint `review.md` files (i.e., findings without `status: fixed`). This counter is consumed by the git-push hook (spec §P13 — System hooks; design §7 — Hooks Design) which warns the user before pushing a branch with open findings. The counter is decremented by `/gse:fix` Step 6 when findings are resolved. If all findings are resolved (clean review or post-FIX), set to 0.

**Regenerate dashboard** — Run `python3 "$(cat ~/.gse-one)/tools/dashboard.py"` to update `docs/dashboard.html` with review findings, health scores, and quality metrics. After review is a key moment to check the dashboard — inform the user:
- For beginners: "The project dashboard has been updated with the verification results. You can open it at `docs/dashboard.html`." (adapt wording to the user's language)
- For intermediate/expert: "Dashboard updated with review findings and health scores."
