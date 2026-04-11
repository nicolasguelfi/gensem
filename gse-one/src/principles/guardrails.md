# P11 — Guardrails

**Category:** Risk & Communication
**Principle:** Three levels of guardrails — Soft, Hard, and Emergency — protect the project from common pitfalls, calibrated by the user's expertise level.

## Description

Guardrails are proactive protections that prevent mistakes before they happen. Unlike risk classification (P7), which evaluates decisions as they arise, guardrails are standing rules that trigger automatically when specific conditions are detected. They are the project's immune system.

Guardrails operate at three severity levels. Soft guardrails advise. Hard guardrails block and require acknowledgment. Emergency guardrails halt all operations regardless of user expertise — they protect against catastrophic, irreversible actions.

## Operational Rules

1. **Three guardrail levels:**

   | Level | Behavior | Can Override? | Expertise Adjustment |
   |-------|----------|---------------|---------------------|
   | **Soft** | Agent warns, suggests alternative, continues if user confirms | Yes, with acknowledgment | Beginner: shown always. Expert: may be suppressed for known patterns. |
   | **Hard** | Agent blocks the action, requires explicit override with rationale | Yes, with documented rationale | Beginner: more triggers. Expert: fewer triggers. |
   | **Emergency** | Agent halts ALL operations, requires explicit acknowledgment | Only with explicit "I understand the risk" | NEVER adjusted. Always triggers for ALL users. |

2. **Git-specific guardrails:**

   | Condition | Level | Action |
   |-----------|-------|--------|
   | Working directly on `main` branch | **Hard** | Block commit. Propose creating a feature branch. |
   | Uncommitted changes before switching branch | **Hard** | Block switch. Require commit or stash first. |
   | Unreviewed merge (`/gse:deliver` before `/gse:review`) | **Hard** | Block merge. Review first. |
   | Merge conflict detected during merge | **Gate** | Present conflict, explain options, wait for user choice. |
   | Force push (`git push --force`) | **Emergency** | Halt. Explain data loss risk. Require explicit acknowledgment. |
   | Rewriting published history (`rebase` on pushed branch) | **Emergency** | Halt. Explain consequences for collaborators. |
   | Deleting a branch with unmerged commits | **Hard** | Block. Show unmerged commits. Require confirmation. |
   | Committing secrets (`.env`, credentials, API keys) | **Emergency** | Halt. Prevent commit. Explain exposure risk. |
   | Branch sprawl (>5 active branches) | **Soft** | Warn. Suggest cleanup or merging completed branches. |
   | Stale branches (not touched in >2 sprints) | **Soft** | Warn. Suggest deletion or archival. |
   | Large binary commit (>10MB) | **Soft** | Warn. Suggest Git LFS or `.gitignore`. |

3. **Project-specific guardrails:**

   | Condition | Level | Action |
   |-----------|-------|--------|
   | Deleting a file with trace links (P6) | Hard | Block. Show dependent artefacts. |
   | Modifying a `done` artefact without sprint plan update | Soft | Warn. Suggest creating a new task. |
   | Complexity budget >100% (P10) | Hard | Block new complexity additions. Require budget adjustment. |
   | Complexity budget >80% | Soft | Warn. Show remaining budget. |
   | Sprint plan not approved, starting work | Hard | Block. Require plan approval (P4, P5). |
   | Skipping tests for modified code | Soft | Warn. Suggest adding tests. |
   | No commit for >30 minutes of active work | Soft | Suggest checkpoint commit. |

4. **HUG expertise calibration:**

   - **Beginner profile:**
     - All Soft guardrails are active
     - Additional Hard guardrails: complex git operations (rebase, cherry-pick), dependency additions
     - Lower thresholds: complexity warning at 60% budget instead of 80%

   - **Intermediate profile:**
     - Standard Soft and Hard guardrails as listed above
     - Standard thresholds

   - **Expert profile:**
     - Some Soft guardrails suppressed (e.g., uncommitted changes warning if user has a known workflow)
     - Hard guardrails still active but with briefer explanations
     - Expert can pre-approve certain Hard guardrail overrides in HUG profile

5. **Emergency guardrails are immutable** — Regardless of expertise level, Emergency guardrails ALWAYS trigger with full explanation. An expert is just as capable of accidentally force-pushing to main as a beginner. The consequences are identical.

6. **Guardrail override logging** — Every guardrail override (Soft or Hard) is logged:
   ```yaml
   guardrail_override:
     level: hard
     condition: "commit directly to main"
     user_rationale: "Hotfix for production, will backport to branch after"
     sprint: 5
     timestamp: 2026-02-10T14:32:00
   ```

7. **Custom guardrails** — The project can define custom guardrails in `config/guardrails.yaml`. These are loaded at project initialization and enforced alongside the default guardrails.

## Examples

**Soft guardrail:**
```
Agent: [Soft Guardrail] You have uncommitted changes in 3 files.
Switching branches may cause conflicts.
Suggestion: Commit or stash changes before switching.
Proceed anyway? (1) Stash and switch (2) Commit and switch (3) Switch anyway (4) Discuss
```

**Hard guardrail:**
```
Agent: [HARD GUARDRAIL] You are about to commit directly to `main`.

GSE-One requires all changes to go through task branches
(gse/sprint-NN/type/description) and be merged after review.

To proceed, you must:
1. Create a branch: gse/sprint-03/fix/hotfix-description
2. Commit there
3. Merge to main after review

Override? This requires a documented rationale.
(1) Create branch and proceed (2) Override with rationale (3) Discuss
```

**Emergency guardrail:**
```
Agent: [EMERGENCY] HALT — Force push detected.

`git push --force` to `origin/main` would PERMANENTLY REWRITE
the remote history. Any collaborator who has pulled will face
irreconcilable conflicts. Lost commits may be UNRECOVERABLE.

This guardrail cannot be bypassed by expertise level.

To proceed, you must type: "I understand that force push to main
will rewrite remote history and may cause data loss."

(1) Abort force push (2) Use --force-with-lease instead (safer) (3) Discuss
```
