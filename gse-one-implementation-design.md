# GSE-One — Implementation Design Document

**Version:** see `VERSION` file  
**Date:** 2026-04-12  
**Status:** Mono-plugin architecture — cross-platform parity, hooks aligned, terminology traceable  
**Input:** `gse-one-spec.md`, implementation inspection and restructuration pass

---

## 1. Key Changes

| Version | Changes |
|---------|---------|
| v0.2 → v0.3 | Plugin architecture for Claude Code and Cursor |
| v0.3 → v0.4 | Full git/worktree integration, renamed to GSE prefix |
| v0.4 → v0.6 | `/gse:learn`, `/gse:backlog`, unified backlog, external sources, adopt/lightweight modes, team profiles, P15-P16 AI integrity, testing strategy, COMPOUND 3 axes, mono-repo, GitHub sync. |
| v0.6 → v0.7 | **44-gap alignment with spec v0.7.** Eliminated `worktrees.yaml` (git state per-TASK in backlog). Added: assess skill, orchestrator decision logic (stale sprint, failure handling), safety/recovery (backup tags), status.yaml schema, checkpoint schema, state loading priority, deploy/rollback in deliver, dependency audit, framework drift detection, doc-as-artefact, concurrent access, team matching algorithm. Full config.yaml template (8 sections, ~50 keys). Principle count 16, agents 8, Cursor rules 9+3, templates 15. Spelling: `artefact_type`. |
| v0.7 → v0.8 | **Mono-plugin architecture.** `dist/claude/` + `dist/cursor/` merged into single `plugin/` directory. Agents 8→9 (added `gse-orchestrator` for Claude identity). Cursor rules consolidated from 9+3 `.mdc` to 1 single `000-gse-methodology.mdc`. Hooks: 5→3 system hooks (removed Write|Edit reminders, reclassified as agent behaviors), official event-based format (`PreToolUse`/`PostToolUse`), cross-platform Python commands, two platform-specific files. Settings simplified to `{"agent": "gse-orchestrator"}`. TIME→COMPLEXITY: `stale_sprint_days`→`stale_sprint_sessions`, all calendar-based metrics removed. Config.yaml: 11 sections, ~50 keys (hooks section aligned with 3 system hooks). Methodology parity: orchestrator body = `.mdc` body, generated from same source. Generator rewrite (~400 lines). |

---

## 2. Plugin System Comparison

*Unchanged from v0.2 — see that document for the full comparison table.*

**New addition:** Both environments support git operations:
- Claude Code: via `Bash` tool (git commands) and `EnterWorktree`/`ExitWorktree` tools
- Cursor: via terminal commands and Composer agent (multi-file editing in worktree context)

---

## 3. Architecture Overview

### 3.1 Repository Structure

> **Terminology mapping:** The directory structure maps to the concepts defined in the specification: `activities/` contains the 22 activity definitions (spec), each generated as a skill (`plugin/skills/`). `agents/` provides agent roles (spec). `templates/` provides templates. `hooks/` provides system hooks (spec P13).

```
gse-one/
├── README.md
├── LICENSE
├── src/                                 # Shared source of truth
│   ├── principles/                      # 16 principle definitions (P1-P16)
│   ├── activities/                      # 22 activity definitions
│   ├── agents/                          # 9 agent roles (8 specialized + gse-orchestrator)
│   │   ├── gse-orchestrator.md          # Identity agent — source for both platforms
│   │   ├── requirements-analyst.md
│   │   ├── architect.md
│   │   ├── test-strategist.md
│   │   ├── code-reviewer.md
│   │   ├── security-auditor.md
│   │   ├── ux-advocate.md
│   │   ├── guardrail-enforcer.md
│   │   └── devil-advocate.md
│   └── templates/                       # 15 templates (same as v0.7)
│
├── plugin/                              # Single deployable directory (both platforms)
│   ├── .claude-plugin/plugin.json       # Claude Code manifest
│   ├── .cursor-plugin/plugin.json       # Cursor manifest
│   ├── skills/                          # 22 skills (shared)
│   ├── agents/                          # 9 agents (shared, incl. orchestrator)
│   ├── templates/                       # 15 templates (shared)
│   ├── rules/
│   │   └── 000-gse-methodology.mdc      # Cursor-only (ignored by Claude)
│   ├── hooks/
│   │   ├── hooks.claude.json            # Claude Code format
│   │   └── hooks.cursor.json            # Cursor format
│   └── settings.json                    # Claude-only (ignored by Cursor)
│
├── marketplace/
│   └── .claude-plugin/marketplace.json
│
└── gse_generate.py                      # Generator: src/ → plugin/
```

### 3.2 Plugin Manifests

Both platforms use separate manifests with slightly different fields. The `repository` field is the **source of truth** for methodology feedback (COMPOUND Axe 2) — the agent reads this URL to create issues on the GSE-One repo. It is NOT configured in the user's `.gse/config.yaml`.

**Claude Code manifest** (`.claude-plugin/plugin.json`):

```json
{
  "name": "gse",
  "description": "GSE-One — AI engineering companion for structured SDLC management. 22 commands, adaptive risk analysis, unified backlog, knowledge transfer, worktree isolation.",
  "version": "0.7.0",
  "author": {
    "name": "GSE-One Project"
  },
  "repository": "https://github.com/gse-one/gse-one",
  "skills": "./skills/",
  "agents": "./agents/",
  "hooks": "./hooks/hooks.claude.json"
}
```

**Cursor manifest** (`.cursor-plugin/plugin.json`):

```json
{
  "name": "gse",
  "displayName": "GSE-One",
  "description": "GSE-One — AI engineering companion for structured SDLC management. 22 commands, adaptive risk analysis, unified backlog, knowledge transfer, worktree isolation.",
  "version": "0.7.0",
  "author": {
    "name": "GSE-One Project"
  },
  "repository": "https://github.com/gse-one/gse-one",
  "skills": "./skills/",
  "agents": "./agents/",
  "rules": "./rules/",
  "hooks": "./hooks/hooks.cursor.json"
}
```

Key differences:
- Claude uses `hooks` pointing to `hooks.claude.json`; Cursor uses `hooks` pointing to `hooks.cursor.json`
- Cursor has `displayName` and `rules` fields; Claude does not
- Claude loads methodology via `settings.json` → agent reference; Cursor loads via `rules/`

### 3.3 Mono-Plugin Architecture

ONE directory (`plugin/`) serves both platforms. Shared components — skills, agents, and templates — exist once. Platform-specific files are minimal:

| File | Claude Code | Cursor | Purpose |
|------|:-----------:|:------:|---------|
| `.claude-plugin/plugin.json` | **used** | ignored | Claude manifest |
| `.cursor-plugin/plugin.json` | ignored | **used** | Cursor manifest |
| `settings.json` | **used** | ignored | Agent identity reference |
| `hooks/hooks.claude.json` | **used** | ignored | Claude hook format (PascalCase) |
| `hooks/hooks.cursor.json` | ignored | **used** | Cursor hook format (camelCase) |
| `rules/000-gse-methodology.mdc` | ignored | **used** | Cursor always-on methodology rule |
| `skills/` (22) | **shared** | **shared** | All activity skills |
| `agents/` (9) | **shared** | **shared** | All agents incl. orchestrator |
| `templates/` (15) | **shared** | **shared** | All artefact/config templates |

Claude ignores the `rules/` directory silently. Cursor ignores `settings.json` silently. This means a single install (`claude --plugin-dir plugin/` or Cursor plugin install) works without any platform-specific preparation.

---

## 4. Git-Integrated Skill Designs

> **Terminology:** This document describes the design of **skills** — the technical artifacts (`SKILL.md` files in `plugin/skills/`) that deliver the **activities** defined in the specification. Each skill implements exactly one activity: the skill `plan/SKILL.md` delivers the activity `/gse:plan`. See the specification for the formal relationship between activities, skills, commands, and inclusion policies.

> **Note:** This document details the 17 skills that required specific design decisions (git integration, new mechanisms, complex workflows). The following 5 activities are implemented directly from the spec without additional design: `/gse:reqs`, `/gse:design`, `/gse:preview`, `/gse:compound`, `/gse:integrate`. See the specification for their full definitions.

> **Spec-driven enrichments (v0.10+):** The following features are implemented in skills and principles directly from the specification, without additional design. See the specification for details: three-level language management (chat/artifacts/overrides) in HUG and P9; output formatting rules and emoji control in P9; recovery check for unsaved work in `/gse:go`; intent-first mode for beginner users in `/gse:go`; progressive expertise tracking by domain in P9 and the user profile.

### 4.1 `/gse:plan` — Git Integration

**Added to the plan skill workflow:**

```markdown
### Git Step (after Step 5 — Persist)

Read `.gse/config.yaml` → `git.strategy`.

**If strategy is `worktree` or `branch-only`:**

1. Check if sprint branch exists:
   ```bash
   git branch --list "gse/sprint-<N>"
   ```

2. If strategic plan and no sprint branch:
   - Create sprint branch from main:
     ```bash
     git checkout -b gse/sprint-<N> main
     git checkout main  # return to main
     ```
   - If strategy is `worktree`, create sprint worktree:
     ```bash
     git worktree add .worktrees/sprint-<N> gse/sprint-<N>
     ```

3. For each planned task, assign a branch name:
   - Format: `gse/sprint-<N>/<type>/<short-description>`
   - Type is derived from task artefact type: requirement/design → `docs/`,
     code → `feat/`, test → `test/`, fix → `fix/`
   - Record branch name in the plan artefact for each task

4. Update each TASK entry in `.gse/backlog.yaml` with `git.branch` (planned, not yet created) and `git.branch_status: planned`.

**If strategy is `none`:** Skip all git operations.
```

### 4.2 `/gse:produce` — Git Integration

**Added to the produce skill workflow:**

```markdown
### Git Step (before production begins)

Read `.gse/config.yaml` → `git.strategy`.

**If strategy is `worktree`:**

1. Get the planned branch name from the plan artefact for this task.

2. Create the feature branch from the sprint branch:
   ```bash
   git branch gse/sprint-<N>/<type>/<name> gse/sprint-<N>
   ```

3. Create a worktree for this branch:
   ```bash
   git worktree add .worktrees/sprint-<N>-<type>-<name> gse/sprint-<N>/<type>/<name>
   ```

4. Update the TASK entry in `.gse/backlog.yaml`:
   ```yaml
   - id: TASK-<ID>
     status: in-progress
     git:
       branch: gse/sprint-<N>/<type>/<name>
       branch_status: active
       worktree: .worktrees/sprint-<N>-<type>-<name>
       worktree_status: active
       commits: 0
       uncommitted_changes: 0
   ```

5. All subsequent file operations for this task happen inside the worktree directory.
   The agent must use the worktree path as the working directory.

**If strategy is `branch-only`:**

1. Create feature branch and switch to it:
   ```bash
   git checkout -b gse/sprint-<N>/<type>/<name> gse/sprint-<N>
   ```

2. All work happens on this branch. Switch back to sprint branch when done.

**If strategy is `none`:** Work directly on current branch.

### Commit Convention

During production, commit frequently using the convention:

```
gse(sprint-<N>/<type>): <description>

Sprint: <N>
Traces: <artefact IDs>
```

Commit at logical checkpoints:
- After each file is complete
- After each test passes
- Before switching to a different sub-task
```

### 4.3 `/gse:review` — Git Integration

**Added to the review skill workflow:**

```markdown
### Git Step (at review start)

Read `.gse/config.yaml` → `git.strategy`.

**If strategy is `worktree` or `branch-only`:**

1. Identify the branch to review (from plan or user argument).

2. Generate the diff against the sprint branch:
   ```bash
   git diff gse/sprint-<N>...gse/sprint-<N>/<type>/<name> --stat
   git diff gse/sprint-<N>...gse/sprint-<N>/<type>/<name>
   ```

3. The review operates on this **diff**, not on the full file state.
   This means reviewers see exactly what changed, making the review
   more focused and efficient.

4. If the worktree exists, read files from the worktree path.
   If not (branch-only), read files from the branch:
   ```bash
   git show gse/sprint-<N>/<type>/<name>:<filepath>
   ```

5. Review findings reference both the file path and the branch:
   ```
   RVW-005 [HIGH] — Missing input validation
     Location: gse/sprint-03/feat/user-auth:src/auth.py:42
     ...
   ```

**If strategy is `none`:** Review files in-place as before.
```

### 4.4 `/gse:fix` — Git Integration

**Added to the fix skill workflow:**

```markdown
### Git Step (before applying fixes)

Read `.gse/config.yaml` → `git.strategy`.

**If strategy is `worktree`:**

1. Create a fix branch from the reviewed feature branch:
   ```bash
   git branch gse/sprint-<N>/fix/rvw-<ID> gse/sprint-<N>/<type>/<name>
   ```

2. Create a worktree for the fix:
   ```bash
   git worktree add .worktrees/sprint-<N>-fix-rvw-<ID> gse/sprint-<N>/fix/rvw-<ID>
   ```

3. Apply fixes in the fix worktree.

4. After fixes are complete and verified:
   - Merge fix branch back into the feature branch (fast-forward if possible)
   - Delete fix worktree and branch
   - Update TASK in backlog.yaml: `status: done`, `git.branch_status: active` (ready to merge)

**If strategy is `branch-only`:**

1. Create fix branch, switch to it, apply fixes, merge back.

**If strategy is `none`:** Apply fixes in-place.
```

### 4.5 `/gse:deliver` — Git Integration

**This is the most git-heavy skill. Full workflow:**

```markdown
### Delivery Workflow

Read `.gse/config.yaml` → `git.strategy`.

**If strategy is `none`:**
- Generate changelog from `.gse/decisions.md` and sprint artefacts
- Tag current state (if git repo exists): `git tag v<version>`
- Done

**If strategy is `worktree` or `branch-only`:**

#### Step 1 — Pre-flight Check

1. Verify all feature branches have been reviewed:
   ```bash
   # Check backlog.yaml — all sprint TASKs should have status: done
   ```
   If any are `active` or `paused` → **Hard guardrail**: "These branches
   have not been reviewed: [list]. Review them first or exclude from delivery."

2. Check for merge conflicts between feature branches and sprint branch:
   ```bash
   git merge-tree $(git merge-base gse/sprint-<N> gse/sprint-<N>/feat/X) \
     gse/sprint-<N> gse/sprint-<N>/feat/X
   ```
   If conflicts → **Gate**: present conflicts, options to resolve.

3. Check for uncommitted changes in worktrees:
   If any → **Hard guardrail**: "Commit or discard changes first."

#### Step 2 — Merge Feature Branches into Sprint Branch

For each feature branch in the merge queue (ordered by dependency):

1. **Gate decision** — merge strategy:
   Present the structured interaction pattern with squash/merge/rebase options
   (see spec Section 10.4). Default proposal from `git.merge_strategy_default`.

2. Execute the chosen merge:
   ```bash
   # Example: squash merge
   git checkout gse/sprint-<N>
   git merge --squash gse/sprint-<N>/feat/<name>
   git commit -m "gse(sprint-<N>/deliver): merge feat/<name> (squash)

   Sprint: <N>
   Traces: TASK-<ID>, [artefact IDs]"
   ```

3. Repeat for each feature branch.

#### Step 3 — Merge Sprint Branch into Main

1. **Gate decision** — merge sprint into main:
   ```
   **Question:** Merge sprint <N> into main?
   
   **Context:** Sprint branch has <M> merged features, 
     all reviewed, no conflicts with main.
   
   **Options:**
   1. Merge — create a merge commit on main
   2. Squash — all sprint work becomes one commit on main
   3. Defer — keep sprint branch, don't merge yet
   4. Discuss
   ```

2. Execute merge:
   ```bash
   git checkout main
   git merge gse/sprint-<N> --no-ff \
     -m "gse(deliver): sprint <N> — <summary>

   Sprint: <N>"
   ```

#### Step 4 — Tag Release

If `git.tag_on_deliver` is true:
```bash
git tag -a v<version> -m "Release v<version> — Sprint <N>"
```

Version is determined by:
- Read current latest tag
- Increment based on sprint content (major/minor/patch — Gate decision if ambiguous)

#### Step 5 — Cleanup

If `git.cleanup_on_deliver` is true:
1. Delete merged feature branches:
   ```bash
   git branch -d gse/sprint-<N>/feat/<name>
   ```
2. Remove worktree directories:
   ```bash
   git worktree remove .worktrees/sprint-<N>-feat-<name>
   ```
3. Optionally delete sprint branch (Gate — user may want to keep for history).
4. Update each delivered TASK in `.gse/backlog.yaml`: `status: delivered`, `git.branch_status: deleted`, `git.worktree_status: removed`.

#### Step 6 — Generate Release Notes

Create `docs/sprints/sprint-<N>/release.md`:
- Features delivered (from plan)
- Review findings resolved
- Decisions made (from journal)
- Health score at delivery
- Git tag and commit hash

Report:
```
Delivered: Sprint <N> — v<version>
  Features merged: X
  Review findings resolved: Y
  Tag: v<version> (commit <hash>)
  Health at delivery: Z/10
```
```

### 4.6 `/gse:pause` — Git Integration

```markdown
### Git Step (before checkpoint save)

Read `.gse/config.yaml` → `git.auto_commit_on_pause`.

If true:
1. For each active TASK in `.gse/backlog.yaml` (where `git.worktree_status: active`):
   ```bash
   cd <worktree-path>
   git add -A
   git status --short
   # If there are changes:
   git commit -m "gse(pause): checkpoint — work in progress

   Sprint: <N>
   Task: TASK-<ID>"
   ```

2. Update each TASK in backlog: set `git.uncommitted_changes: 0`.

3. Include worktree state in checkpoint:
   ```yaml
   # checkpoint-YYYY-MM-DD-HHMM.yaml
   ...
   git:
     current_branch: gse/sprint-03/feat/user-auth
     worktrees: <extracted from backlog.yaml TASK git states>
     last_commit_per_worktree:
       sprint-03-feat-user-auth: <commit-hash>
       sprint-03-feat-dashboard: <commit-hash>
   ```
```

### 4.7 `/gse:resume` — Git Integration

```markdown
### Git Step (after checkpoint load)

1. Verify all worktrees from the checkpoint still exist:
   ```bash
   git worktree list
   ```

2. For each expected worktree:
   - If present: check for external changes since checkpoint
     ```bash
     cd <worktree-path>
     git log <saved-hash>..HEAD --oneline
     ```
     If new commits exist: "This worktree was modified since your last session.
     N new commits found. Review them?"
   
   - If missing: "Worktree <name> is missing. Recreate it?"
     If yes: `git worktree add <path> <branch>`

3. Report worktree state:
   ```
   Worktrees restored:
     ✓ sprint-03-feat-user-auth — active, no external changes
     ✓ sprint-03-feat-dashboard — paused, 2 external commits detected
     ✗ sprint-03-fix-rvw-005 — missing (branch exists, worktree deleted)
   ```

4. Propose next action based on where work stopped.
```

### 4.8 `/gse:status` — Git Extension

```markdown
### Git Status Section

Add to status output:

```
Git:
  Current branch: gse/sprint-03/feat/user-auth
  Sprint branch:  gse/sprint-03

  Active worktrees:
    ✓ sprint-03-feat-user-auth    active    0 uncommitted   TASK-003
    ◉ sprint-03-feat-dashboard    paused    3 uncommitted   TASK-005
    ★ sprint-03-fix-rvw-005       ready     0 uncommitted   TASK-008

  Merge queue:
    gse/sprint-03/feat/login     reviewed  no conflicts    ready

  Stale branches: none
  Main status: clean, tagged v0.2.1
```

Flags:
  --branches    Show all gse/* branches
  --decisions   Show auto-decision log
  --worktrees   Show detailed worktree info
```

### 4.9 `/gse:health` — Git Hygiene Sub-Score

```markdown
### Git Hygiene Computation

Score 0–10 based on:

| Factor | Weight | Score 10 | Score 0 |
|--------|--------|----------|---------|
| Active branches | 20% | ≤3 | >10 |
| Stale branches | 20% | 0 | >3 |
| Uncommitted changes | 20% | 0 across all worktrees | >5 files |
| Merge conflicts | 20% | 0 | >0 |
| Main branch clean | 10% | Clean + tagged | Dirty |
| Unreviewed branches | 10% | 0 | >2 |

Report as one of 8 dimensions in health dashboard:
```
  Git hygiene:             █████░░░░░  3 branches, 1 stale      (5/10)
```

Git-specific alerts:
```
  ⚠ GIT: 2 worktrees have uncommitted changes
  ⚠ GIT: Branch gse/sprint-02/feat/old not touched in 12 days
  ✓ GIT: No merge conflicts detected
  ✓ GIT: main is clean and tagged (v0.2.1)
```
```

---

## 5. New Skill Designs (v0.6)

### 5.1 `/gse:learn` — Knowledge Transfer Skill

```markdown
# skills/learn/SKILL.md
---
description: "Start or continue a learning session. Triggered when the user asks to learn, understand, or be taught a concept. Also triggered proactively by the agent at natural workflow transition points when a competency gap is detected. Covers: /gse:learn <topic>, /gse:learn --notes, /gse:learn --roadmap."
---

# GSE-One Learn — Knowledge Transfer

Arguments: $ARGUMENTS

## Options

- `<topic>` — Start a reactive learning session on the given topic
- `--notes` — List all learning notes by topic
- `--notes <topic>` — Show the learning note on a specific topic
- `--notes --recent` — Show notes from the current sprint
- `--roadmap` — Show the competency map: learned, gaps, recommendations
- `--quick` — Force quick mode (5 min)
- `--deep` — Force deep mode (15 min)
- `--help` — Show learning help

## Prerequisites

1. Read `.gse/profile.yaml` → competency_map section
2. Read `.gse/profile.yaml` → user.language, user.it_expertise, user.domain_background
3. If `--notes`, read `docs/learning/` directory listing

## Workflow

### If `--notes` or `--roadmap`
Consultation mode — read and display, no session.

### If reactive (user provides topic)

1. Check if a learning note exists for this topic in `docs/learning/`
2. If exists: offer to review/extend. If not: create new.
3. Determine mode: `--quick` or `--deep` or auto-detect from topic complexity
4. Generate the session content calibrated to user level (P9):
   - Key concepts explained with analogies from user's domain_background
   - Application to the user's actual project (reference real files, branches, artefacts)
   - Practice exercise (deep mode only) — a small task in the project context
   - Quick reference card at the end
5. Save/update learning note in `docs/learning/<topic-slug>.md`
6. Update competency_map in profile

### If proactive (agent-initiated)

This is triggered by other skills (go, compound, plan, review) at transition points.
The learn skill receives the topic and trigger context.

1. Present using the structured interaction pattern:
   ```
   **Learning opportunity:** <topic>
   **Context:** <why this matters now>
   **Options:**
   1. Quick overview (5 min)
   2. Deeper session (15 min)
   3. Not now — remind me next sprint
   4. Not interested in this topic
   ```
2. If accepted: run the reactive workflow above
3. If "not now": record in profile as deferred
4. If "not interested": record in profile as declined (never propose again)

## Contextual Tips (cross-cutting)

Not part of the learn skill itself, but embedded in the `settings.json` agent key
(Claude Code) or the identity rule (Cursor). Logic:

1. After any action where a technical concept was involved:
   - Check competency_map: has this concept been explained?
   - If not, and the concept is relevant: insert 2-3 sentence explanation
   - Mark concept as explained in competency_map
2. Aggregate contextual tips into a learning note at sprint end (during /gse:compound)
```

### 5.2 `/gse:backlog` — Unified Work Item Management (NEW)

```markdown
# skills/backlog/SKILL.md
---
description: "View and manage the project backlog — the unified list of all work items (TASK). Filter by sprint, pool, or artefact type. Add items manually. Sync with GitHub Issues. Triggered when user asks about tasks, backlog, work items, what's left to do, or issue management."
---

# GSE-One Backlog — Unified Work Item Management

Arguments: $ARGUMENTS

## Sub-commands

- (no args) — Show full backlog (pool + current sprint)
- `add <description>` — Add a new item to the pool
- `sprint` — Show current sprint items only
- `pool` — Show unplanned items only
- `--type <type>` — Filter by artefact_type (code/test/requirement/design/doc/config/import)
- `sync` — Synchronize with GitHub Issues
- `--help` — Show backlog help

## Prerequisites

1. Read `.gse/backlog.yaml`
2. Read `.gse/config.yaml` → `github` section
3. Read `.gse/status.yaml` → current sprint number

## Workflow

### Display mode (no args, sprint, pool, --type)

1. Read backlog items
2. Filter by requested view
3. Present grouped by sprint assignment:
   ```
   Sprint 3 (current):
     ● TASK-038  code   Implement auth        in-progress  branch: active
     ● TASK-039  test   Auth unit tests       done         branch: active (ready to merge)
     ○ TASK-040  design API architecture      planned      branch: planned

   Pool (unplanned):
     ○ TASK-042  code   Add dark mode         open
     ○ TASK-047  req    Payment NFR           open
   ```

4. If `--type` filter: show only matching artefact_type

### Add mode

1. Create a new TASK with auto-incremented ID
2. Ask for artefact_type if not obvious from description (Inform tier)
3. Set sprint: null, status: open
4. If github.enabled: create GitHub Issue and record number
5. Append to `.gse/backlog.yaml`

### Sync mode

1. Read `.gse/config.yaml` → github settings
2. If not enabled: "GitHub sync is not configured. Enable it?" (Gate)
3. If enabled:
   - Pull: fetch open issues not in backlog → create TASK entries
   - Push: create issues for local items without github_issue
   - Update: sync status changes bidirectionally
   - Report: "Synced: N new from GitHub, M pushed to GitHub, K status updates"

## Auto-creation by other skills

The backlog skill is also called internally by:
- REVIEW: creates TASK for findings that need future work
- PLAN: creates TASK for newly planned items
- COLLECT: creates TASK for imported GitHub Issues
- DELIVER: closes TASK (status: delivered), auto-closes GitHub Issues

These internal calls don't show the backlog display — they just modify backlog.yaml.
```

### 5.3 `/gse:collect` — External Source Mode Extension

```markdown
### External Source Workflow (added to collect skill)

Triggered when $ARGUMENTS contains paths or URLs.

1. Parse arguments: separate local paths from URLs
2. For each local path:
   - Verify it exists
   - Scan recursively for source files, tests, docs, configs
   - Detect language/framework from file extensions and package manifests
3. For each URL (GitHub):
   - Use `gh api` or `git clone --depth 1` to shallow-clone
   - Read README, package manifest, directory structure
   - Detect license
4. For each discovered element, compute reusability assessment:
   - Compare language/framework with current project (from `.gse/config.yaml`)
   - Check dependency compatibility
   - Estimate integration cost in complexity points
   - Classify: reusable as-is / adaptable / incompatible
5. Present as Gate decision (one choice per element: Include / Skip / Discuss)
6. Save all results to `.gse/sources.yaml` (retained + skipped)
7. For retained elements: prepare import/adapt task entries for PLAN

### Provenance in produced artefacts

When PRODUCE executes an import task, it must add provenance fields:
```yaml
gse:
  source: SRC-001
  source_origin: ~/other-project/src/auth.py
  adaptation: "Replaced Flask with FastAPI"
```
```

### 5.4 `/gse:go` — Adopt Mode

```markdown
### Adopt Mode (added to go skill)

Triggered when:
- `.gse/` does not exist AND the project has existing files (>0 source files)
- OR user passes `--adopt`

Workflow:

1. **Detect** — "This project has existing code but no GSE-One state.
   Would you like to onboard it?" (Inform tier — can skip)

2. **Scan** — Run `/gse:collect` (internal mode) to inventory artefacts

3. **Infer state**:
   - Read git log: count commits, identify tags, detect branch patterns
   - Estimate "sprint 0" baseline: current main HEAD is the starting point
   - Detect project domain from package manifests / file extensions

4. **Initialize `.gse/`**:
   - Create config.yaml with inferred domain and git strategy
   - Create profile.yaml (trigger HUG interview)
   - Create status.yaml with sprint: 0, phase: LC01

5. **Propose annotation** (Gate):
   "I found N existing artefacts. Add GSE-One traceability metadata?"
   - Option 1: Yes, annotate all (add frontmatter to existing .md files)
   - Option 2: Annotate new artefacts only (leave existing files untouched)
   - Option 3: Skip annotation entirely

6. **Transition** — proceed to normal LC01 for sprint 1
```

### 5.5 Lightweight Mode (Go Skill Extension)

```markdown
### Lightweight Mode Detection (added to go skill)

At start of /gse:go:

1. If `.gse/config.yaml` exists → read `lifecycle.mode`
2. If `.gse/` does not exist:
   - Count project files
   - If < 5 files → propose lightweight mode (Inform)
   - If >= 5 files → propose full mode

In lightweight mode:
- Skip LC01 (no formal collect/assess)
- Simplified plan: single task list, no sprint branch (use feature branch from main)
- No worktrees: `git.strategy` forced to `branch-only`
- No complexity budget tracking
- Health: 3 dimensions only (test pass, review findings, git hygiene)
- No sprint artefact directory (plan is inline in `.gse/status.yaml`)
- Decision tiers: Auto + Gate only (no Inform — keep it simple)

User can upgrade to full mode anytime via `/gse:go` — the agent scaffolds
the missing structure.
```

### 5.6 Team Profile Detection (HUG Skill Extension)

```markdown
### Team Mode (added to hug skill)

At start of /gse:hug:

1. Detect current git user: `git config user.name`
2. Check if `.gse/profiles/` directory exists
3. If team mode (multiple profiles):
   - Look for `.gse/profiles/<username>.yaml`
   - If found: load and offer to update
   - If not found: create new profile via interview
   - Symlink `.gse/profile.yaml` → `.gse/profiles/<username>.yaml`
4. If solo mode (no profiles/ directory):
   - Use `.gse/profile.yaml` directly (current behavior)
   - If user answers "team" to team_context question → create profiles/ directory
     and move profile.yaml into it
```

### 5.7 Merge Strategy Expertise Adaptation (Deliver Skill Extension)

```markdown
### Adaptive Merge Presentation (added to deliver skill)

At merge Gate decision, read user profile → it_expertise:

**Beginner:**
- Hide git terminology (squash, merge, rebase)
- Present as: "Clean summary" vs "Full history" vs "Let me decide"
- Agent recommends one option
- Map user's choice to git command silently

**Intermediate:**
- Plain-language + technical term in parentheses
- "Clean summary (squash merge)" / "Full history (merge commit)" / "Linear (rebase)"

**Expert:**
- Direct technical options with consequence horizons
- squash / merge / rebase with pros/cons
```

### 5.8 Non-Code Health Dimensions (Health Skill Extension)

```markdown
### Configurable Dimensions (added to health skill)

Read `.gse/config.yaml` → `health.disabled_dimensions`

If dimensions are disabled:
- Exclude from score computation
- Exclude from dashboard display
- Adjust score denominator (e.g., 5 active dimensions → score out of 5, normalized to 10)

Default enabled:
- requirements_coverage
- test_pass_rate
- design_debt
- review_findings
- complexity_budget
- traceability
- git_hygiene
- ai_integrity
```

### 5.9 `/gse:tests` — Testing Strategy Skill (Extended)

```markdown
# skills/tests/SKILL.md
---
description: "Define test strategy, set up test environment, write tests, execute campaigns, and produce evidence. Triggered when the user asks about testing, wants to add tests, or when /gse:produce needs to run tests after code production. Covers unit, integration, E2E, visual, and acceptance tests."
---

# GSE-One Tests — Full Testing Lifecycle

Arguments: $ARGUMENTS

## Options

- `--strategy` — Define/update the test strategy (pyramid, coverage targets)
- `--setup` — Install and configure test environment (frameworks, browsers)
- `--run` — Execute all tests and produce campaign report
- `--run <test-id>` — Execute a specific test
- `--visual` — Run visual tests only (screenshots + analysis)
- `--coverage` — Show coverage report
- `--evidence` — Browse test evidence (screenshots, videos)
- `--help` — Show testing help

## Prerequisites

1. Read `.gse/config.yaml` → `testing` section
2. Read `.gse/config.yaml` → `project.domain` (for pyramid calibration)
3. Read `.gse/profile.yaml` → `user.it_expertise` (for interaction depth)
4. Read latest `docs/sprints/sprint-NN/tests.md` if exists

## Workflow

### Step 1 — Strategy (if --strategy or first time)

1. Detect project domain from config
2. Propose test pyramid calibrated to domain (see spec Section 6.1):
   - Web frontend: 20% unit, 20% integration, 40% E2E/visual, 20% acceptance
   - API backend: 50% unit, 30% integration, 5% E2E, 15% acceptance
   - etc.
3. Present as Inform (expert) or Gate (beginner) decision
4. For web/mobile projects, propose visual testing setup (Gate)
5. Save strategy in `docs/sprints/sprint-NN/tests.md`

### Step 2 — Environment Setup (if --setup or first time)

1. Detect language/framework from package manifest
2. Select test framework:
   - Python → pytest + coverage.py
   - JS/TS → vitest or jest + c8
   - Go → go test + cover
3. Install as dev dependency (auto or with user confirmation by expertise)
4. If visual testing enabled:
   ```bash
   npx playwright install --with-deps chromium
   ```
5. Create test directory structure: `tests/unit/`, `tests/integration/`, `tests/e2e/`
6. Configure test runner (config file, scripts in package.json / pyproject.toml)

### Step 3 — Write Tests

For each TASK in the sprint with testing needs:
1. Read the requirements (REQ) and design (DES) traced to this TASK
2. Generate tests at the appropriate level (from strategy):
   - Unit tests for individual functions
   - Integration tests for module interactions
   - E2E tests for user workflow scenarios
   - Visual tests (if enabled): navigate pages, capture screenshots
3. Each test has a TST-NNN ID and traces to its REQ/DES
4. Adapt test complexity to user level:
   - Beginner: simple, readable tests with comments
   - Expert: property-based, edge-case-heavy tests

### Step 4 — Execute Campaign (if --run)

1. Run the test suite in the appropriate worktree:
   ```bash
   cd .worktrees/sprint-NN-feat-name/
   uv run pytest --cov --cov-report=json -v
   ```
2. If visual testing enabled:
   ```bash
   npx playwright test --reporter=json
   ```
3. Capture evidence:
   - Test results (pass/fail per test)
   - Coverage report
   - Screenshots (from visual tests)
   - Video on failure (if `testing.visual.video` enabled)
4. Save evidence to `tests/evidence/sprint-NN/TASK-NNN/`

### Step 5 — Analyze Screenshots (if visual tests)

Using multimodal capability:
1. Read each captured screenshot
2. Check for: misaligned elements, truncated text, missing images,
   contrast issues, responsive layout problems
3. Compare with reference screenshots (if they exist from previous sprint)
4. Report visual findings tagged `[VISUAL]`

### Step 6 — Generate Campaign Report

Create `docs/sprints/sprint-NN/test-reports/TASK-NNN-campaign.md` with:
- Summary: executed, passed, failed, duration, coverage
- Failure details with links to evidence
- Coverage map per module
- Visual findings (if applicable)
- Traces to REQ and DES

### Step 7 — Update Health

Update `.gse/status.yaml` health dimensions:
- test_pass_rate: % passing
- code_coverage: % covered
- requirements_coverage: % REQ with linked passing tests
```

### 5.10 `/gse:produce` — Test Execution After Production

```markdown
### Test Execution (added to produce skill, after code is written)

After completing code production for a TASK:

1. Check if tests exist for this TASK (from `/gse:tests`)
2. If yes: execute them automatically
   - Run in the task's worktree
   - Capture evidence
   - If tests fail: report and propose fix before marking task as done
3. If no tests exist:
   - Check test strategy: does this TASK need tests?
   - If yes and user is beginner: write tests automatically, then run
   - If yes and user is expert: propose writing tests (Inform)
   - If no (per strategy): skip, but log as Inform decision
4. Generate campaign report
5. Attach report and evidence to the TASK in backlog:
   ```yaml
   - id: TASK-038
     test_campaign: docs/sprints/sprint-03/test-reports/TASK-038-campaign.md
     test_pass_rate: 91.7
     code_coverage: 78
   ```
```

### 5.11 `/gse:review` — Devil's Advocate Agent (P16)

```markdown
### Devil's Advocate (added to review skill)

After the standard quality review, activate the devil-advocate agent:

1. **Scope:** Only the agent's own productions from this sprint (not user-written code)

2. **Checks:**
   a. **Hallucination hunt:**
      - For each library/dependency recommended: verify it exists
        ```bash
        pip show <lib>  # or npm list <lib>
        ```
      - For each API call: verify the endpoint/method exists in the actual docs
      - For each pattern cited: verify the source exists

   b. **Assumption challenge:**
      - List all implicit assumptions in the design
      - For each: "What if this assumption is wrong?"
      - Flag assumptions that have no supporting evidence

   c. **Complaisance detection:**
      - Review decision history: did the agent always agree with the user?
      - Were alternatives genuinely explored or dismissed quickly?
      - Were any user ideas that should have been challenged accepted without pushback?

   d. **Edge case coverage:**
      - For each function: what happens with null, empty, very large, malicious input?
      - For each API: what happens on timeout, 5xx, rate limit?

   e. **Temporal validity:**
      - Flag any recommendation based on ecosystem state that may have changed
      - Check: "Is this library still maintained? Has the API changed?"

3. **Output:** Findings tagged `[AI-INTEGRITY]` in the review report:
   ```
   RVW-012 [AI-INTEGRITY] [HIGH] — Library does not exist
     Agent recommended `fastapi-magic-auth`. Not found on PyPI.
     Fix: Replace with `fastapi-users` (verified: exists, 2.3k stars).

   RVW-013 [AI-INTEGRITY] [MEDIUM] — Unchallenged user decision
     User chose MongoDB for relational data (DEC-008). Agent agreed without
     presenting PostgreSQL as alternative. Risk: relational queries will be
     complex and slow.

   RVW-014 [AI-INTEGRITY] [LOW] — Outdated pattern
     Agent used `datetime.utcnow()` which is deprecated since Python 3.12.
     Fix: Use `datetime.now(UTC)`.
   ```

4. **Integration with P15 confidence:**
   - Findings where confidence was "Moderate" or "Low" are flagged with higher severity
   - Findings where confidence was "Verified" but verification was wrong → CRITICAL
```

### 5.12 User Pushback Detection (Cross-cutting, in settings.json)

```markdown
### Pushback Logic (embedded in settings.json agent key)

The agent tracks a `consecutive_acceptances` counter in `.gse/status.yaml`:

1. After each Gate decision:
   - If user chose the recommended option without discussion: increment counter
   - If user chose "Discuss", modified, or chose non-recommended: reset counter

2. Threshold check (calibrated by expertise):
   - Beginner: trigger at 3
   - Intermediate: trigger at 5
   - Expert: trigger at 8

3. When threshold reached:
   - Read the last N decisions from `.gse/decisions.md`
   - Select the 3 most impactful (highest risk tier)
   - Present the critical checkpoint pattern (see spec P16)

4. After checkpoint:
   - If user says "everything looks good": reset counter, don't trigger
     again until next sprint
   - If user revisits a decision: reset counter, re-enter Gate for that decision
   - If user says "overwhelmed": switch to more Gate decisions, reduce pace
```

### 5.13 `/gse:assess` — Gap Analysis Skill (NEW — G-002)

```markdown
# skills/assess/SKILL.md
---
description: "Evaluate project artefact status against goals. Identifies covered, partial, and uncovered goals. Triggered when user asks to assess, evaluate progress, or check readiness."
---

# GSE-One Assess — Gap Analysis

## Workflow

### Step 1 — Gather Inputs
1. Read artefact inventory from latest COLLECT (or run inline)
2. Read project goals from `.gse/config.yaml → project` or ask user
3. Read backlog pool for pending items

### Step 2 — Analyze Coverage
For each project goal:
- **Covered:** artefacts exist, status = approved or implemented
- **Partial:** artefacts exist, status = draft or reviewed (incomplete)
- **Uncovered:** no artefacts linked to this goal
- **At risk:** high-complexity or security-sensitive gaps

### Step 3 — External Source Assessment
If external sources were collected (`.gse/sources.yaml`):
- For each retained source: evaluate compatibility and integration cost
- Flag sources that no longer match project direction

### Step 4 — Output Gap Report
Present to user with Inform tier:
```
Gap Analysis — Sprint N

  ✓ COVERED: User auth (REQ-007) — implemented, tested
  ◐ PARTIAL: API docs (REQ-012) — design done, no implementation
  ✗ UNCOVERED: Payment processing (REQ-015) — no artefacts
  ⚠ AT RISK: Data encryption (REQ-009) — security-sensitive, no tests

  Recommendation: 2 uncovered goals should become TASK items for next sprint.
```

### Step 5 — Feed PLAN
Uncovered goals → candidate TASK items in backlog pool (auto-created with `origin: assess`)
```

### 5.14 `/gse:go` — Orchestrator Decision Logic (NEW — G-007)

```markdown
### Orchestrator Decision Tree (added to go skill)

When `/gse:go` is invoked:

**Step 1 — Detect project state:**

| Condition | Action |
|-----------|--------|
| `.gse/` absent + project has files | Adopt mode (see 5.5) |
| `.gse/` absent + project empty | HUG (LC00) |
| `.gse/` exists | Read `status.yaml` → Step 2 |

**Step 2 — Determine next action:**

| Current state | Next action |
|--------------|-------------|
| No sprint exists | Start LC01: GO > COLLECT > ASSESS > PLAN |
| Sprint, plan not approved | Resume PLAN |
| Sprint, tasks in-progress | Resume PRODUCE on current task |
| Sprint, tasks done, not reviewed | Start REVIEW |
| Sprint, review done, fixes pending | Start FIX |
| Sprint, all delivered | Start LC03: COMPOUND > INTEGRATE |
| Sprint, compound done | Propose next sprint → LC01 |
| Sprint stale (> `lifecycle.stale_sprint_sessions` sessions without progress) | Step 3 |

Progression is defined as any TASK status change (e.g., `planned` → `in-progress`, `in-progress` → `done`). A session where no TASK status changes counts as a session without progress, incrementing `sessions_without_progress` in `status.yaml`.

**Step 3 — Stale sprint detection (Gate):**
```
Sprint N has had X sessions without progress.
1. Resume — pick up where we left off
2. Partial delivery — deliver completed tasks, defer rest to pool
3. Discard — abandon sprint, move all tasks to pool, delete branches
4. Discuss
```

**Step 4 — Failure handling:**
If any activity fails:
1. Save checkpoint
2. Report error with agent's assessment
3. Gate: retry / skip (if skippable) / pause / discuss
4. Never silently continue
```

### 5.15 `/gse:deliver` — Deploy & Recovery Extensions (NEW — G-003, G-009)

```markdown
### Deploy Step (added after Step 4 — Tag Release)

If `git.post_tag_hook` is configured:
1. Execute the hook: `bash -c "$post_tag_hook"`
2. If success: report "Deployed successfully"
3. If failure → **Gate**:
   ```
   Deployment failed (exit code X). Options:
   1. Retry deployment
   2. Rollback tag: git tag -d v<version>
   3. Investigate manually (pause)
   4. Discuss
   ```

### Safety Backup (added as Step 0 — before any merge)

Before EVERY destructive git operation:
```bash
git tag gse-backup/sprint-NN-pre-merge-<feat> $(git rev-parse gse/sprint-NN)
```

Recovery if something goes wrong:
```bash
# Branch recovery:
git checkout -b gse/sprint-NN/feat/<name> gse-backup/sprint-NN-<feat>-deleted

# Merge reversal:
git reset --hard gse-backup/sprint-NN-pre-merge-<feat>
```

Cleanup: delete backup tags older than `git.backup_retention_days` during deliver.
```

### 5.16 State Schemas (NEW — G-004, G-005, G-006)

**status.yaml schema (spec §12.4):**
```yaml
gse_version: "0.7.0"
current_sprint: 3
current_phase: LC02
plan_status: approved

health:
  score: 6.7
  dimensions:
    requirements_coverage: 8
    test_pass_rate: 9
    design_debt: 3
    review_findings: 8
    complexity_budget: 6
    traceability: 9
    git_hygiene: 5
    ai_integrity: 6
  last_computed: 2026-04-11

complexity:
  budget: 10
  consumed: 6.5
  remaining: 3.5

# P16 pushback detection
consecutive_acceptances: 2
never_discusses: false
terse_responses: 0
never_modifies: false
never_questions: false

last_activity: /gse:produce
last_activity_date: 2026-04-11

# Stale sprint detection (complexity/session-based, not calendar-based)
sessions_without_progress: 0

# Review findings counter (used by hooks)
review_findings_open: 0
```

**Checkpoint schema (spec §12.5):**
```yaml
timestamp: 2026-04-11T16:30:00
user: alice
sprint: 3
phase: LC02
last_activity: /gse:produce
last_task: TASK-038
status_snapshot: <copy of status.yaml>
backlog_sprint_snapshot: <current sprint items from backlog.yaml>
git:
  current_branch: gse/sprint-03/feat/auth
  worktrees:
    - branch: gse/sprint-03/feat/auth
      last_commit: abc123
notes: "Working on auth module, 2 tests remain"
```

**State loading priority (spec §12.6):**

| Priority | File | Load when |
|----------|------|-----------|
| 1 | status.yaml | Always |
| 2 | profile.yaml | Always |
| 3 | config.yaml | Always |
| 4 | backlog.yaml (sprint only) | Always |
| 5 | backlog.yaml (pool) | On demand |
| 6 | decisions.md (last 5) | On demand |
| 7 | sources.yaml | During COLLECT |
| 8 | decisions-auto.log | Never auto |

Essential context: ~100-200 lines. Agent must NEVER load all at once.

### 5.17 Additional Skill Extensions (G-008 to G-014, G-025 to G-028)

**P16 pushback — full signal tracking (G-008):**
In addition to the `consecutive_acceptances` counter, track:
- User never selects "Discuss" → `never_discusses` boolean
- User responds with single-word confirmations → `terse_responses` counter
- User never modifies proposals → `never_modifies` boolean
- User never asks "why?" → `never_questions` boolean
All signals stored in `status.yaml`. Threshold calibrated by expertise.

**Documentation as first-class artefact (G-010):**
When `/gse:produce` handles a TASK with `artefact_type: doc`:
- Auto-generate API docs from code docstrings if available
- Generate in the worktree branch `gse/sprint-NN/docs/<name>`
- Review alongside code artefacts

**Dependency audit (G-011):**
When `/gse:tests` runs, if `testing.dependency_audit: true`:
```bash
pip-audit  # or npm audit, depending on detected framework
```
Report findings in health alerts as `⚠ DEPS:` items.

**Framework drift detection (G-014):**
At start of `/gse:tests --run` or `/gse:produce`:
- Compare current framework (from package manifest) with `config.yaml → testing.framework`
- If different → Inform: "Framework changed from X to Y. Update config?"

**Complexity budget ranges (G-025):**
Use the spec §8.1 range table. Agent selects within range based on context, presents as Inform.

**Team matching algorithm (G-026):**
User detection in priority order:
1. `.gse/current-user` file → use content
2. `GSE_USER` env var → use value
3. `git config user.name` → use value
4. Ask user (Inform)
Match case-insensitive, spaces→hyphens against `.gse/profiles/`.

**Minimum viable project size (G-027):**
In lightweight mode detection: add note that for truly one-off tasks, don't use GSE-One.

**Concurrent access (G-028):**
- Each team member works in own worktree → no file conflicts during production
- `backlog.yaml` conflicts handled by git merge; agent detects on pull, proposes resolution (Gate)
- `decisions.md` is append-only → no conflicts
- Checkpoints are per-user → no conflicts

---

## 6. Methodology Deployment: Cross-Platform Parity

The GSE-One methodology is loaded as the agent's permanent identity on both platforms through a dual-mechanism approach, ensuring identical behavior regardless of the tool used.

### 6.1 Claude Code: Agent Reference

Claude Code uses `settings.json` to load the orchestrator agent as session identity:

```json
{
  "agent": "gse-orchestrator"
}
```

This causes Claude Code to load `agents/gse-orchestrator.md` at session start, making the full methodology body (16 principles, state management, orchestration decision tree) the agent's permanent context.

### 6.2 Cursor: Always-On Rule

Cursor uses `rules/000-gse-methodology.mdc` with `alwaysApply: true` to inject the methodology permanently into every interaction:

```yaml
---
description: "GSE-One methodology — 16 core principles, state management, orchestration decision tree. This is the agent's permanent identity."
alwaysApply: true
---
```

The body following this frontmatter is identical to the body of `agents/gse-orchestrator.md`.

### 6.3 Generation and Parity

Both files are generated from the same source: `src/agents/gse-orchestrator.md`. The generator:

1. Extracts the body (everything after the YAML frontmatter `---...---`)
2. Wraps the body with **agent frontmatter** for Claude Code (`name`, `description` fields)
3. Wraps the same body with **.mdc frontmatter** for Cursor (`description`, `alwaysApply` fields)
4. Verifies body parity at generation time — if the two generated bodies differ, the generator reports `DIVERGENT!`

This ensures that Claude Code and Cursor users experience the exact same methodology, decision logic, and orchestration behavior.

---

## 7. Hooks Design

GSE-One implements **3 system hooks** (spec P13 — Event-Driven Behaviors) — deterministic, rigid checks where the risk of the AI forgetting is too high. All hook commands use cross-platform Python (`python3 -c`). The commands are defined as shared constants in the generator and emitted in platform-specific JSON wrappers.

| Hook | Event | Matcher | Level | Exit |
|------|-------|---------|-------|------|
| Protect main | PreToolUse | Bash | Hard | 2 (block) |
| Block force-push | PreToolUse | Bash | Emergency | 2 (block) |
| Review findings on push | PostToolUse | Bash | Informational | 0 (warn) |

Blocking hooks (exit 2) write to **stderr** so the agent receives the feedback. Informational hooks (exit 0) write to **stdout**.

### 7.1 Claude Code: `hooks/hooks.claude.json`

Claude Code uses PascalCase event names (`PreToolUse`, `PostToolUse`) and an explicit `type` field:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import os,subprocess,sys; t=os.environ.get('CLAUDE_TOOL_INPUT',''); c=t.startswith('git commit'); b=subprocess.run(['git','branch','--show-current'],capture_output=True,text=True).stdout.strip() if c else ''; (c and b=='main') and (print('GUARDRAIL: Direct commit to main detected. Use a feature branch.',file=sys.stderr),sys.exit(2))\""
          },
          {
            "type": "command",
            "command": "python3 -c \"import os,sys; t=os.environ.get('CLAUDE_TOOL_INPUT',''); t.startswith('git push --force') and (print('EMERGENCY GUARDRAIL: Force push detected. This can cause permanent data loss. Aborting.',file=sys.stderr),sys.exit(2))\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import os,re; t=os.environ.get('CLAUDE_TOOL_INPUT',''); f=os.path.join('.gse','status.yaml'); c=open(f).read() if t.startswith('git push') and os.path.isfile(f) else ''; m=re.search(r'review_findings_open:\\s*(\\d+)',c); o=int(m.group(1)) if m else 0; (o>0) and print('WARNING: '+str(o)+' open review findings')\""
          }
        ]
      }
    ]
  }
}
```

### 7.2 Cursor: `hooks/hooks.cursor.json`

Cursor uses camelCase event names (`preToolUse`, `postToolUse`), a top-level `version` field, and omits the `type` field (implicit):

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "command": "python3 -c \"import os,subprocess,sys; t=os.environ.get('CLAUDE_TOOL_INPUT',''); c=t.startswith('git commit'); b=subprocess.run(['git','branch','--show-current'],capture_output=True,text=True).stdout.strip() if c else ''; (c and b=='main') and (print('GUARDRAIL: Direct commit to main detected. Use a feature branch.',file=sys.stderr),sys.exit(2))\""
          },
          {
            "command": "python3 -c \"import os,sys; t=os.environ.get('CLAUDE_TOOL_INPUT',''); t.startswith('git push --force') and (print('EMERGENCY GUARDRAIL: Force push detected. This can cause permanent data loss. Aborting.',file=sys.stderr),sys.exit(2))\""
          }
        ]
      }
    ],
    "postToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "command": "python3 -c \"import os,re; t=os.environ.get('CLAUDE_TOOL_INPUT',''); f=os.path.join('.gse','status.yaml'); c=open(f).read() if t.startswith('git push') and os.path.isfile(f) else ''; m=re.search(r'review_findings_open:\\s*(\\d+)',c); o=int(m.group(1)) if m else 0; (o>0) and print('WARNING: '+str(o)+' open review findings')\""
          }
        ]
      }
    ]
  }
}
```

### 7.3 Format Differences Summary

| Aspect | Claude Code | Cursor |
|--------|------------|--------|
| Event names | PascalCase (`PreToolUse`) | camelCase (`preToolUse`) |
| `type` field | Required (`"type": "command"`) | Omitted (implicit) |
| `version` field | Absent | Required (`"version": 1`) |
| Hook commands | Identical (cross-platform Python) | Identical (cross-platform Python) |

---

## 8. Non-Git Project Handling

Some projects may not use git (rare but possible). The skills handle this gracefully:

```markdown
### Git Detection (run once per session)

At the start of any skill that involves git:
1. Check if `.git` exists in the project root
2. If not: set `git_available = false`
3. If yes: read `.gse/config.yaml` → `git.strategy`

If `git_available` is false OR `git.strategy` is `none`:
- Skip all git operations silently
- Do not mention branches, worktrees, or merges
- Work directly on files in place
- Health dashboard omits the "Git hygiene" sub-dimension (score out of 6 dimensions)
- Log: `Inform: git not available or disabled — working without version control`

If this is the first session and git IS available but `git.strategy` is not set:
- **Gate decision**: "This project uses git. How should GSE-One manage branches?"
  1. Worktree (recommended) — isolated directories per task
  2. Branch-only — branches without worktrees (simpler but requires switching)
  3. None — no branch management (GSE-One won't touch git)
```

---

## 9. Marketplace & Distribution

*Unchanged from v0.2 — see that document for Claude Code marketplace, Cursor marketplace, and installation flow.*

**Note:** The `marketplace.json` install path is `"plugin"` (not `"dist/claude"`), reflecting the mono-plugin architecture.

---

## 10. Shared Project State (`.gse/`)

```
.gse/                               # Created by /gse:hug or /gse:go
├── config.yaml                      # Project configuration (git, lifecycle, health, github)
├── profile.yaml                     # HUG user profile (solo) or symlink to profiles/
├── profiles/                        # Per-user profiles (team mode)
│   ├── alice.yaml
│   └── bob.yaml
├── status.yaml                      # Sprint state, health score, complexity budget, phase
├── backlog.yaml                     # Unified work items (TASK) with git state per item
├── sources.yaml                     # External source registry
├── decisions.md                     # Decision journal (Inform + Gate tiers)
├── decisions-auto.log               # Auto-tier decision log
└── checkpoints/                     # Session checkpoints
    └── checkpoint-YYYY-MM-DD-HHMM.yaml
```

**.gitignore additions** (applied by `/gse:hug` on first run):

```gitignore
# GSE-One worktrees (managed by /gse:produce and /gse:deliver)
.worktrees/

# GSE-One local state (user-specific)
.gse/checkpoints/
.gse/decisions-auto.log
```

---

## 11. Generator Script Design

### 11.1 Evolution

| Version | Principles | Activities | Cursor rules | Templates |
|---------|-----------|------------|-------------|-----------|
| v0.2 | 7 | 19 | 5+2 | 10 |
| v0.4 | 9 (+P12, P13) | 19 | 6+3 | 12 |
| v0.6a | 10 (+P14) | 20 (+learn) | 7+3 | 14 |
| v0.6b | 10 | 21 (+backlog) | 7+3 | 14 |
| v0.6c | 12 (+P15, P16) | 21 | 9+3 | 15 |
| v0.7 | 16 (all P1-P16) | 21 | 9+3 | 15 |
| **v0.8** | **16** | **22** | **1 (consolidated)** | **15** |

Note: Agents now 9 (8 specialized + gse-orchestrator). Generator ~400 lines.

### 11.2 Generation Steps

| Step | Input | Output | Shared? |
|------|-------|--------|---------|
| 1 | `src/agents/gse-orchestrator.md` (body) | `plugin/agents/gse-orchestrator.md` + `plugin/rules/000-gse-methodology.mdc` | Body identical, frontmatter differs |
| 2 | `src/activities/*.md` (22) | `plugin/skills/<name>/SKILL.md` | Shared |
| 3 | `src/agents/*.md` (8 specialized) | `plugin/agents/<name>.md` | Shared |
| 4 | `src/templates/*` (15) | `plugin/templates/*` | Shared |
| 5 | Constants | `plugin/.claude-plugin/plugin.json` + `plugin/.cursor-plugin/plugin.json` | Two manifests |
| 6 | Shared shell commands | `plugin/hooks/hooks.claude.json` + `plugin/hooks/hooks.cursor.json` | Same logic, different format |
| 7 | — | `plugin/settings.json` | Claude-only |

---

## 12. File Inventory

| Category | Shared | Claude-only | Cursor-only | Source |
|----------|--------|-------------|-------------|--------|
| Skills | 22 | — | — | 22 activities |
| Agents | 9 (incl. orchestrator) | — | — | 9 agents |
| Templates | 15 | — | — | 15 templates |
| Manifest | — | 1 | 1 | — |
| Rules | — | — | 1 (.mdc) | from orchestrator |
| Hooks | — | 1 | 1 | shared constants |
| Settings | — | 1 | — | — |
| **Total** | **46** | **3** | **3** | **46 sources** |

Grand total: **52 files**. Generator: ~400 lines.

---

## 13. Implementation Priorities

### Phase 1 — Foundation + Git (week 1)

1. Create repository structure
2. Write `plugin.json` manifests
3. Write source files for 5 foundation skills: `hug`, `status`, `plan`, `produce`, `learn`
4. Write source files for 4 core principles: `identity`, `decision-tiers`, `version-control`, `knowledge-transfer`
5. Write the generator (skills, manifests, rules, templates)
6. Implement git operations in plan (create sprint branch) and produce (create worktree)
7. Implement adopt mode detection in `go` skill
8. Test locally: `claude --plugin-dir plugin/`
9. Verify `/gse:hug` → `/gse:plan` → `/gse:produce` creates branch + worktree

### Phase 2 — Core Lifecycle + Learning (week 2)

10. Add review (diff-based), fix (fix branch), deliver (merge + tag + cleanup)
11. Add collect with external source mode + `sources.yaml`
12. Add learn skill with contextual tips + proactive proposals + learning notes
13. Add remaining activity sources (8 remaining)
14. Add remaining principle sources (6 remaining)
15. Add all 8 agents + Cursor P14 always-on rule
16. Add hooks (git guardrails)
17. Test full LC02 cycle with learning integration

### Phase 3 — Modes & Distribution (week 3)

18. Implement lightweight mode (auto-detect + simplified flows)
19. Implement team profiles (per-user profiles, role assignment)
20. Implement merge strategy expertise adaptation (beginner/intermediate/expert)
21. Set up GitHub repository + marketplace.json
22. Cursor marketplace submission or npm package
23. Documentation (README, install guide, quickstart)
24. Test team auto-install flow

### Phase 4 — Polish (week 4)

25. Non-code project configuration (health dimension toggle)
26. Risk analysis multi-dimension assessment refinement
27. Health dashboard with git hygiene
28. Complexity budget calibration
29. Consequence horizon examples library
30. Guardrail sensitivity tuning
31. Cross-environment state consistency tests
32. Non-git fallback + multi-worktree stress testing

---

## 14. Open Questions

| # | Question | Impact | Recommendation |
|---|----------|--------|----------------|
| 1 | ~~Should GSE-One principles be in `settings.json` agent key or separate skills?~~ | ~~Context efficiency~~ | **RESOLVED.** Principles are embedded in the orchestrator agent body (`agents/gse-orchestrator.md`), which also generates the Cursor `.mdc` rule. `settings.json` contains only the agent reference. |
| 2 | Cursor marketplace or npm or both? | Reach | Both |
| 3 | How to handle `.gse/` version upgrades? | UX | `gse_version` field + migration logic in skills |
| 4 | How to handle git conflicts during deliver? | User experience | Gate decision with 3 options: resolve manually, use theirs, use ours |
| 5 | Should worktrees be created eagerly (at plan time) or lazily (at produce time)? | Resource usage | **Lazily** — create at produce time. Plan only assigns names. |
| 6 | How deep should git hygiene check go? | Scope | Start with branch-level checks. Dependency audit in Phase 4. |
| 7 | Should `.gse/` itself live on main or on each branch? | State consistency | **Main only.** Worktrees get a symlink or copy. |
| 8 | How to handle contextual tip frequency? Too many tips = annoying, too few = useless. | User experience | Max 1 tip per activity step. User can disable via HUG. Track and adapt. |
| 9 | Should external source shallow clones be cached or re-cloned each time? | Performance | Cache in `.gse/cache/` with TTL. Clean on `/gse:deliver`. |
| 10 | How to handle state recovery when user manually breaks `.gse/` or deletes branches? | Robustness | Best-effort reconstruction from git history. Warn, don't crash. |

---

## Appendix A — Changelog

> **Note:** Versions 0.1.0 through 0.8.0 were developed during an intensive design session. Future versions will follow standard release cadence.

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-04-10 | Initial design with raw file generation |
| 0.2.0 | 2026-04-10 | Plugin-native architecture for Claude Code and Cursor |
| 0.3.0 | 2026-04-10 | Full git integration: worktree isolation, guardrail hooks, version control rule, commit convention, merge strategy as Gate. |
| 0.4.0 | 2026-04-10 | Renamed to `gse`/`GSE-One`. Dropped `/g1:` alias. |
| 0.6.0 | 2026-04-10 | Spec v0.6 alignment. Learn, backlog, tests, P15-P16, devil-advocate agent, unified backlog, git state per-TASK. |
| 0.7.0 | 2026-04-11 | **44-gap alignment with spec v0.7.** Eliminated worktrees.yaml (git state per-TASK in backlog). 16 principle source files (P1-P16). Added: assess skill (5.14), orchestrator decision logic with stale sprint (5.15), deploy/rollback + safety backup tags (5.16), status.yaml/checkpoint/state-loading schemas (5.17), full pushback signal tracking (5.18), doc-as-artefact, dependency audit, framework drift, team matching algorithm, concurrent access, min project size. Spelling: artefact_type. All worktrees.yaml refs replaced. Config template now covers 11 sections (~50 keys). |
| 0.8.0 | 2026-04-11 | **Mono-plugin architecture.** `dist/` merged into single `plugin/` directory. 9 agents (added `gse-orchestrator`). Cursor rules consolidated to 1 `.mdc`. Hooks format: official event-based with platform-specific files. Settings simplified to agent reference. TIME→COMPLEXITY: `stale_sprint_days`→`stale_sprint_sessions`. Generator rewrite (~400 lines). Body parity verification for cross-platform methodology. |
