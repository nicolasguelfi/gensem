# P12 — Version Control

**Category:** Infrastructure
**Principle:** Main is sacred; one branch per task; worktree isolation; merge is a Gate decision; adaptive presentation by expertise level.

## Description

Version control is the backbone of iterative-incremental development (P1). GSE-One enforces a disciplined branching model that protects the `main` branch, isolates work in task branches, and treats merge as a consequential decision requiring human approval.

The version control presentation adapts to the user's expertise level. Beginners receive step-by-step guidance with explanations. Experts receive terse commands. The underlying discipline is identical — only the communication changes.

## Operational Rules

1. **Main is sacred** — The `main` branch always contains a working, consistent baseline. Direct commits to `main` are blocked by a Hard guardrail (P11). All changes reach `main` through merge from task branches.

2. **One branch per task** — Each task (TASK-NNN) gets its own branch. This provides isolation, traceability, and easy rollback.

3. **Branch naming convention:**
   ```
   gse/sprint-NN/type/short-description
   ```
   Where `type` is one of:
   - `feat` — New feature or capability
   - `fix` — Bug fix
   - `docs` — Documentation only
   - `refactor` — Code restructuring without behavior change
   - `test` — Adding or modifying tests
   - `config` — Configuration changes

   Examples: `gse/sprint-03/feat/user-authentication`, `gse/sprint-03/fix/rvw-005`

4. **Worktree isolation (default mode)** — Each active branch is checked out in its own git worktree — a separate directory on disk linked to the same repository. Worktrees are the **default** working mode (`config.yaml → git.strategy: worktree`).

   ```
   <project-root>/                          # main branch (always clean)
   ├── .worktrees/                          # Worktree directories (gitignored)
   │   ├── sprint-03-feat-user-auth/        # Full working copy for user-auth
   │   ├── sprint-03-feat-dashboard/        # Full working copy for dashboard
   │   └── sprint-03-fix-rvw-005/           # Full working copy for fix
   └── src/, tests/, docs/, ...             # Main branch files
   ```

   **Why worktrees, not just branches:**
   - Each task has its own directory — no `git stash` or `git switch` needed
   - User can review one task while the agent works on another
   - Failed experiments are discarded by deleting the worktree — no trace on `main`
   - Merge conflicts are detectable before they happen (compare worktree diffs)
   - Beginners never need to understand `git checkout`

   **Small project escape hatch:** Set `git.strategy: branch-only` (branches without worktrees) or `git.strategy: none` (no branching) in `config.yaml`.

5. **Merge is a Gate decision** — Merging a task branch into `main` is always a Gate-tier decision (P7). The agent presents:
   - Summary of changes (files modified, lines added/removed)
   - Trace links affected
   - Tests passing/failing
   - Complexity points consumed
   - Structured interaction with approval options

6. **Merge checklist** — Before requesting merge approval, the agent verifies:
   - [ ] All tests pass
   - [ ] No linting errors
   - [ ] Frontmatter is complete on all new/modified artefacts
   - [ ] Trace links are bidirectionally consistent (P6)
   - [ ] Complexity budget is not exceeded (P10)
   - [ ] No secrets in committed files
   - [ ] Sprint plan is updated if scope changed

7. **Clean up after merge** — After a successful merge to `main`:
   - The task branch is deleted (local and remote)
   - Merge commit uses convention: `gse(sprint-03/deliver): merge feat/user-auth (squash)`
   - Sprint activity log is updated

8. **Safety tags before destructive operations** — Before any destructive git operation (merge, branch delete, worktree remove, tag delete), the agent creates a backup tag:
   ```bash
   # Before merging:
   git tag gse-backup/sprint-03-pre-merge-feat-auth $(git rev-parse gse/sprint-03)
   # Before deleting a branch:
   git tag gse-backup/sprint-03-feat-auth-deleted $(git rev-parse gse/sprint-03/feat/auth)
   ```
   Safety tags are prefixed `gse-backup/` and retained for `git.backup_retention_days` (default: 30 days, configurable in `config.yaml`). Cleanup during `/gse:deliver`.

   **Recovery procedures:**
   - Branch recovery: `git checkout -b gse/sprint-03/feat/auth gse-backup/sprint-03-feat-auth-deleted`
   - Merge reversal: `git checkout gse/sprint-03 && git reset --hard gse-backup/sprint-03-pre-merge-feat-auth`
   - State file recovery: `git checkout HEAD~1 -- .gse/backlog.yaml`

9. **Adaptive presentation by expertise level:**

   **Beginner:**
   ```
   Agent: Let's save your changes and put them on the main timeline.
   Step 1: I'll switch to the main branch (the "official" version)
   Step 2: I'll bring your changes in (merge)
   Step 3: I'll clean up the working branch
   Ready? (1) Yes, proceed step by step (2) Explain more (3) Discuss
   ```

   **Intermediate:**
   ```
   Agent: Ready to merge gse/sprint-03/feat/user-auth into main.
   Changes: 4 files, +120/-15 lines, tests pass, complexity 3/12 pts.
   (1) Merge (2) Review diff first (3) Discuss
   ```

   **Expert:**
   ```
   Agent: Merge gse/sprint-03/feat/user-auth -> main?
   4 files, +120/-15, green, 3/12 pts. (1) Go (2) Diff (3) Discuss
   ```

10. **Commit message convention** — All commits follow the `gse()` convention:
    ```
    gse(<scope>): <description>

    Sprint: <N>
    Traces: <artefact IDs>
    ```
    Examples:
    ```
    gse(sprint-03/feat): implement user authentication flow

    Sprint: 3
    Traces: REQ-007, DES-003

    gse(sprint-03/fix): resolve XSS vulnerability in login form

    Sprint: 3
    Traces: RVW-005, SEC-002
    ```
    Commit at logical checkpoints: after each file is complete, after each test passes, before switching sub-tasks.

## Lifecycle Integration (Spec 10.3)

| Activity | Git Actions |
|----------|------------|
| **PLAN (strategic)** | Create sprint branch `gse/sprint-NN` from `main`. Assign branch names to each planned task. |
| **PLAN (tactical)** | Assign branch names to newly planned tasks. No branch creation yet. |
| **PRODUCE** | Create feature branch from sprint branch + create worktree in `.worktrees/`. All work in worktree. |
| **REVIEW** | Review on branch diff: `git diff gse/sprint-NN...gse/sprint-NN/feat/X`. |
| **FIX** | Create fix branch `gse/sprint-NN/fix/rvw-NNN` from reviewed feature branch. Fix in worktree. |
| **DELIVER** | Gate: merge strategy. Merge features → sprint → main. Tag. Delete branches/worktrees. |
| **PAUSE** | Auto-commit all uncommitted work in all active worktrees. Save worktree map in checkpoint. |
| **RESUME** | Verify all worktrees exist and are intact. Report external changes. |
| **STATUS** | Show branch tree, worktree state, merge queue, stale branches. |
| **HEALTH** | Compute git hygiene sub-score (branches, stale, conflicts, uncommitted, main status). |
| **COLLECT** | Inventory branches and worktrees alongside artefact files. |
| **TASK** | Create ad-hoc branch `gse/sprint-NN/task/description` + worktree. |

## Examples

**Safety tag before destructive operation:**
```
Agent: You've asked to rebase the feature branch. Before proceeding,
I'm creating a backup tag for recovery.

git tag gse-backup/sprint-03-pre-rebase-feat-auth $(git rev-parse HEAD)
git rebase main

If anything goes wrong:
git reset --hard gse-backup/sprint-03-pre-rebase-feat-auth
```

**Merge Gate decision:**
```
Agent: [GATE] Merge request for TASK-027.

Branch: gse/sprint-03/feat/user-authentication -> main
Changes: 4 files modified, 2 files added
Lines: +120 / -15
Tests: 12/12 passing
Linting: clean
Artefacts: SRC-015, SRC-016 (new), TST-030..TST-032 (new)
Traces: implements DES-007, satisfies REQ-010..REQ-012
Complexity: 3 points consumed this sprint (total 9/12)

Merge checklist: all items verified.

Options:
1. Approve merge
2. Review full diff
3. Review specific file
4. Discuss
```
