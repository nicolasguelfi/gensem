# GSE-One — Implementation Design Document

**Input:** `gse-one-spec.md`, implementation inspection and restructuration pass

---

## 2. Plugin System Comparison

All three supported environments support git operations:
- Claude Code: via `Bash` tool (git commands) and `EnterWorktree`/`ExitWorktree` tools
- Cursor: via terminal commands and Composer agent (multi-file editing in worktree context)
- opencode: via `bash` tool (git commands) and native TS plugin hooks (`tool.execute.before/after`)

---

## 3. Architecture Overview

### 3.1 Repository Structure

> **Terminology mapping:** The directory structure maps to the concepts defined in the specification: `activities/` contains the 23 activity definitions (spec), each generated as a skill (`plugin/skills/`). `agents/` provides agent roles (spec). `templates/` provides templates. `hooks/` provides system hooks (spec P13).

```
gse-one/
├── README.md
├── LICENSE
├── src/                                 # Shared source of truth
│   ├── principles/                      # 16 principle definitions (P1-P16)
│   ├── activities/                      # 23 activity definitions
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
│   └── templates/                       # 19 templates
│
├── plugin/                              # Single deployable directory (Claude + Cursor + opencode)
│   ├── .claude-plugin/plugin.json       # Claude Code manifest
│   ├── .cursor-plugin/plugin.json       # Cursor manifest
│   ├── skills/                          # 23 skills (shared, `name:` field included)
│   ├── commands/                        # 23 flat /gse-<name>.md (Cursor + opencode)
│   ├── agents/                          # 9 agents (shared, incl. orchestrator)
│   ├── templates/                       # 19 templates (shared)
│   ├── rules/
│   │   └── gse-orchestrator.mdc         # Cursor-only (ignored by Claude/opencode)
│   ├── hooks/
│   │   ├── hooks.claude.json            # Claude Code format
│   │   └── hooks.cursor.json            # Cursor format
│   ├── settings.json                    # Claude-only (ignored by Cursor/opencode)
│   └── opencode/                        # opencode-specific subtree
│       ├── skills/                      # 23 skills with injected `name:`
│       ├── commands/                    # 23 gse-<name>.md slash commands
│       ├── agents/                      # 8 specialized (`mode: subagent`)
│       ├── plugins/gse-guardrails.ts    # Native TS plugin (transpiled from hooks.claude.json)
│       ├── AGENTS.md                    # Orchestrator body wrapped in markers
│       └── opencode.json                # Default permissions + version marker
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
  "description": "GSE-One — AI engineering companion for structured SDLC management. 23 commands, adaptive risk analysis, unified backlog, knowledge transfer, worktree isolation.",
  "version": "0.16.0",
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
  "description": "GSE-One — AI engineering companion for structured SDLC management. 23 commands, adaptive risk analysis, unified backlog, knowledge transfer, worktree isolation.",
  "version": "0.16.0",
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
| `rules/gse-orchestrator.mdc` | ignored | **used** | Cursor always-on methodology rule |
| `skills/` (23) | **shared** | **shared** | All activity skills |
| `agents/` (9 in source, 8 for Cursor) | **shared** (9: 8 specialized + orchestrator) | **shared** (8: specialized only) | Agent roles for sub-agent delegation |
| `templates/` (15) | **shared** | **shared** | All artefact/config templates |

Claude ignores the `rules/` directory silently. Cursor ignores `settings.json` silently. The orchestrator agent (`agents/gse-orchestrator.md`) exists in the source `plugin/` directory for Claude Code, but the installer **excludes it from Cursor** installations — Cursor loads the orchestrator identity via `rules/gse-orchestrator.mdc` instead, avoiding double-loading of the same ~400-line content.

---

## 4. Git-Integrated Skill Designs

> **Terminology:** This document describes the design of **skills** — the technical artifacts (`SKILL.md` files in `plugin/skills/`) that deliver the **activities** defined in the specification. Each skill implements exactly one activity: the skill `plan/SKILL.md` delivers the activity `/gse:plan`. See the specification for the formal relationship between activities, skills, commands, and inclusion policies.

> **Note:** This document details the 17 skills that required specific design decisions (git integration, new mechanisms, complex workflows). The following 5 activities are implemented directly from the spec without additional design: `/gse:reqs`, `/gse:design`, `/gse:preview`, `/gse:compound`, `/gse:integrate`. See the specification for their full definitions.

> **Spec-driven enrichments:** The following features are implemented in skills and principles directly from the specification, without additional design. See the specification for details: three-level language management (chat/artifacts/overrides) in HUG and P9; output formatting rules and emoji control in P9; recovery check for unsaved work in `/gse:go`; intent-first mode for beginner users in `/gse:go`; progressive expertise tracking by domain in P9 and the user profile; Hetzner deployment skill (`/gse:deploy`) with flexible starting points (solo full-flow, pre-configured server, training mode with shared Coolify); conversational elicitation and ISO 25010 quality checklist in `/gse:reqs`.

### 4.1 `/gse:plan` — Git Integration

**Added to the plan skill workflow** (writes branch assignments to `.gse/plan.yaml` and `.gse/backlog.yaml`):

```markdown
### Git Step (Step 6 — Git Integration, between Step 5 "Promote to Sprint" and Step 7 "Persist Plan")

Read `.gse/config.yaml` → `git.strategy`.

**If strategy is `worktree` or `branch-only`:**

0. **Precondition — git baseline exists:**
   ```bash
   git rev-parse --verify main
   ```
   If this fails → **Hard guardrail**: "`main` has no commits. Run `/gse:hug` to initialize the repository with a foundational commit before planning."

1. Check if sprint branch exists:
   ```bash
   git branch --list "gse/sprint-<N>/integration"
   ```

2. If strategic plan and no sprint integration branch:
   - Create sprint integration branch from main:
     ```bash
     git checkout -b gse/sprint-<N>/integration main
     git checkout main  # return to main
     ```
   - If strategy is `worktree`, create sprint worktree:
     ```bash
     git worktree add .worktrees/sprint-<N> gse/sprint-<N>/integration
     ```

3. For each planned task, assign a branch name:
   - Format: `gse/sprint-<N>/<type>/<short-description>`
   - Type is derived from task artefact type: requirement/design → `docs/`,
     code → `feat/`, test → `test/`, fix → `fix/`
   - Record branch name in `.gse/plan.yaml` (`tasks[].branch`) and in `.gse/backlog.yaml` for each task

4. Update each TASK entry in `.gse/backlog.yaml` with `git.branch` (planned, not yet created) and `git.branch_status: planned`.

**If strategy is `none`:** Skip all git operations.
```

### 4.2 `/gse:produce` — Git Integration

**Added to the produce skill workflow** (reads branch name from `.gse/plan.yaml` tasks or `.gse/backlog.yaml` git state):

```markdown
### Git Step (before production begins)

Read `.gse/config.yaml` → `git.strategy`.

**If strategy is `worktree`:**

1. Get the planned branch name from `.gse/plan.yaml` (`tasks[].branch`) or `.gse/backlog.yaml` (`git.branch`) for this task.

2. Create the feature branch from the sprint branch:
   ```bash
   git branch gse/sprint-<N>/<type>/<name> gse/sprint-<N>/integration
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
   git checkout -b gse/sprint-<N>/<type>/<name> gse/sprint-<N>/integration
   ```

2. All work happens on this branch. Switch back to integration branch when done.

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
   git diff gse/sprint-<N>/integration...gse/sprint-<N>/<type>/<name> --stat
   git diff gse/sprint-<N>/integration...gse/sprint-<N>/<type>/<name>
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
   git merge-tree $(git merge-base gse/sprint-<N>/integration gse/sprint-<N>/feat/X) \
     gse/sprint-<N>/integration gse/sprint-<N>/feat/X
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
   git checkout gse/sprint-<N>/integration
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
   git merge gse/sprint-<N>/integration --no-ff \
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
  Sprint branch:  gse/sprint-03/integration

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

## 5. Skill Designs

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
### Mode Selection (Complexity Assessment — added to go skill)

At start of /gse:go, when no sprint is defined:

1. If `.gse/config.yaml` exists with `lifecycle.mode` → use stored mode
2. Otherwise → run complexity assessment:
   - Scan 7 structural complexity signals: dependencies (manifest), persistence (ORM/SQL/DB config), entry points, multi-component, tests, CI/CD, git maturity
   - Apply rules: no manifest + no git + ≤2 source files (trivialiy pre-filter) → Micro; persistence/multi-component/CI/deps>10/entry>10 → Full; otherwise → Lightweight
   - Present as Gate decision with rationale
   - Store chosen mode in `config.yaml → lifecycle.mode`

3. If beginner + first sprint → Intent-First mode runs BEFORE complexity assessment (captures intent, then assesses)

Three project modes based on complexity assessment:

| Mode | Selection | Lifecycle | Git | Health | REQS | TESTS |
|------|-----------|-----------|-----|--------|------|-------|
| **Micro** | Trivial (script, no manifest) | PRODUCE → DELIVER | direct commit | none | Not enforced | Not enforced |
| **Lightweight** | Simple (few deps, no persistence) | PLAN → REQS → PRODUCE → DELIVER | branch-only | 3 dims | Hard (reduced ceremony) | Soft (auto-generated) |
| **Full** | Complex (persistence, multi-component, CI) | LC01 → LC02 → LC03 | worktree | 8 dims | Hard (full ceremony) | Hard (formal strategy) |

Micro mode: 1 state file only (`.gse/status.yaml` with inline profile + task list).
No REQS/TESTS guardrails. No health. No complexity budget.

User can upgrade Micro → Lightweight → Full anytime via `/gse:go`.
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
4. Read latest `docs/sprints/sprint-NN/test-strategy.md` if exists

## Workflow

### Step 1 — Strategy (if --strategy or first time)

1. Detect project domain from config
2. Propose test pyramid calibrated to domain (see spec Section 6.1):
   - Web frontend: 20% unit, 20% integration, 30% E2E/visual, 20% acceptance, 10% other
   - API backend: 50% unit, 25% integration, 5% E2E, 10% acceptance, 10% other
   - etc.
3. Present as Inform (expert) or Gate (beginner) decision
4. For web/mobile projects, propose visual testing setup (Gate)
5. Save strategy in `docs/sprints/sprint-NN/test-strategy.md`
6. **Conditional strategy review** (spec §6.5 — STRATEGY tier) — Runs when `project.domain` is security-sensitive OR `complexity_budget > 15` OR the flag `--review-strategy` / `--deep-review` was passed. Spawns the `test-strategist` sub-agent with the "Strategy checklist" scope. Findings `[STRATEGY]` append to `review.md`. HIGH blocks `/gse:produce` via the Hard guardrail.

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
5. **Conditional TST specs review** (spec §6.5 — TST-SPEC tier) — Runs when ≥ 1 TST carries `quality_gap: true` OR total TST count ≥ 20 OR the flag `--review-specs` / `--deep-review` was passed. Spawns the `test-strategist` sub-agent with the "Specifications checklist" scope. Findings `[TST-SPEC]` append to `review.md`. HIGH blocks `/gse:produce`.

### Step 4 — Execute (if --run)

Invoke the **canonical test run** defined in spec §6.3. Argument handling determines scope (full suite / TST-NNN / `--level X` / visual-only). The canonical run covers: execution, evidence capture, `tests/evidence/sprint-NN/TASK-NNN/` save, TCP-NNN campaign creation, `test_evidence` write, inline chat summary, and health + dashboard refresh.

TESTS does NOT auto-generate missing tests; they must already exist. If not, redirect to `--strategy` / Step 3.

### Step 5 — Screenshot analysis

Part of the canonical run when visual testing is enabled (see spec §6.3 "Screenshot analysis").

### Step 6 — Sprint evidence aggregate (--evidence only)

Only invoked by `--evidence`. Aggregates all per-run TCPs of the current sprint into a single sprint-level campaign (also TCP-prefixed), with `traces.derives_from` pointing at the rolled-up TCPs. No test execution is performed.

### Step 7 — (removed)

Health dimensions and TASK `test_evidence` are updated automatically by the canonical run (spec §6.3 step 7 and step 5). No separate step needed here.
```

### 5.10 `/gse:produce` — Test Execution After Production

```markdown
### Test Execution (added to produce skill, after code is written)

PRODUCE invokes the **canonical test run** (spec §6.3) as its test execution phase. This section documents only the PRODUCE-specific pre/post-conditions:

**Pre-condition — `--skip-tests`:** Gate decision, DEC- logged, `test_evidence.status: skipped` on the TASK, canonical run is NOT invoked.

**Pre-condition — no tests exist:** per expertise level, auto-generate (beginner), propose (intermediate), or offer options (expert). After generation, invoke the canonical run.

**Post-condition — canonical run returns `status: fail`:** Gate decision (Fix / Skip / Discuss). Fix re-invokes the canonical run.

The canonical run produces TCP-NNN campaign, `test_evidence` update on the TASK, inline summary in chat, and health + dashboard refresh. Example of the written `test_evidence` block on the TASK:
```yaml
- id: TASK-038
  test_evidence:
    status: pass
    campaign_ref: docs/sprints/sprint-03/test-reports/campaign-2026-04-10-TASK-038.md
    timestamp: 2026-04-10T14:30:00Z
    pass_rate: 91.7
    code_coverage: 78
    summary: "24 tests, 22 passed, 2 failed"
```
```

### 5.11 `/gse:review` — Devil's Advocate Agent (P16) — `[IMPL]` Tier

```markdown
### Devil's Advocate — [IMPL] review tier (added to review skill)

After the standard quality review (the `[IMPL]` tier per spec §6.5), activate the devil-advocate agent:

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
| Sprint, review done, HIGH/MEDIUM findings exist | Start FIX (conditionally inserted by orchestrator) |
| Sprint, review done, no HIGH/MEDIUM findings | Skip FIX → Start DELIVER |
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
git tag gse-backup/sprint-NN-pre-merge-<feat> $(git rev-parse gse/sprint-NN/integration)
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
# plan status lives in .gse/plan.yaml (active | completed | abandoned)

activity_history:
  - activity: collect
    completed_at: "2026-04-08T09:15:00Z"
    sprint: 3
  - activity: assess
    completed_at: "2026-04-08T09:30:00Z"
    sprint: 3
  - activity: plan
    completed_at: "2026-04-08T10:00:00Z"
    sprint: 3

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

**Sprint Freeze — Design Mechanics (spec §3.1 / lifecycle guardrail 3):**

The spec-level *Sprint Freeze* guardrail materializes as follows:

- **Conceptual trigger:** *the sprint plan status is completed* → **Concrete realization:** `.gse/plan.yaml` contains `status: completed`
- **Conceptual state:** *the number of the sprint in progress* → **Concrete realization:** `.gse/status.yaml` → `current_sprint: N`

**Writeable window:** a sprint is writeable by activities only while `.gse/plan.yaml` exists with `status: active`. When `/gse:deliver` Step 9 sets `status: completed`, the sprint becomes frozen for write operations.

**Activities that MUST consult `.gse/plan.yaml.status` before any write to `.gse/backlog.yaml` or transition of a TASK:**

- `/gse:task` (creates a new TASK)
- `/gse:produce` (transitions TASK `planned` → `in-progress` → `review`)
- `/gse:fix` (transitions TASK `review` → `fixing` → `done`)
- `/gse:review` (adds RVW findings, transitions TASK `in-progress` → `review`)

**Activities exempt from the Sprint Freeze preflight** (operate only on closed sprints or do not mutate TASK state within a frozen sprint): `/gse:compound`, `/gse:integrate`, `/gse:pause`, `/gse:resume`, `/gse:go`, `/gse:status`, `/gse:health`, `/gse:backlog`, `/gse:learn`, `/gse:hug`, `/gse:collect`, `/gse:assess`, `/gse:plan --strategic`, `/gse:deploy`, `/gse:deliver`.

**Promotion sequence for option 1 of the Sprint Freeze Gate:**

1. The agent invokes the mode-appropriate opening sequence inline:
   - **Lightweight mode:** `/gse:plan --strategic`
   - **Full mode:** `/gse:collect` > `/gse:assess` > `/gse:plan --strategic`
2. `/gse:plan --strategic` increments `.gse/status.yaml → current_sprint` from N to N+1 and creates a fresh `.gse/plan.yaml` with `status: active` and a clean `workflow` array.
3. Once the new sprint is active, the originally-invoked activity (`/gse:task`, `/gse:produce`, `/gse:fix`, or `/gse:review`) resumes its normal Step 1 in the new sprint context.

**Persistence:** no new field is added to `.gse/status.yaml`. The source of truth for sprint freeze is `.gse/plan.yaml.status`. `current_sprint` in `.gse/status.yaml` continues to hold the number of the sprint in progress, whether frozen or active.

**Dashboard Sync — Design Mechanics (spec §7 automatic regeneration policy):**

The *automatic regeneration policy* declared in the spec materializes as two complementary mechanisms, plus a failure-surfacing subsystem.

**1. Hook-based regeneration (primary mechanism):**
- Trigger: any invocation of an editor tool (`Edit`, `Write`, `MultiEdit`) on any file.
- Action: the hook invokes `python3 "$(cat ~/.gse-one)/tools/dashboard.py" --if-stale`. The `--if-stale` flag makes the tool self-arbitrating: it reads the debounce window from `.gse/config.yaml → dashboard.regen_debounce_seconds` (default: 5 seconds, fallback if the field is absent or malformed), compares the max mtime of `.gse/**/*.yaml` and `docs/sprints/**/*.md` against the mtime of `docs/dashboard.html`, and regenerates only if state is newer AND the last regeneration is older than the debounce window.
- Cross-platform realization (**three separate matcher entries** per platform for maximum portability — no regex reliance, ensures identical behavior on Claude Code, Cursor, and opencode including local-model setups):
  - Claude Code: `plugin/hooks/hooks.claude.json` → `PostToolUse` with three entries: `matcher: "Edit"`, `matcher: "Write"`, `matcher: "MultiEdit"`, each sharing the same command.
  - Cursor: `plugin/hooks/hooks.cursor.json` → `postToolUse` with the same three entries.
  - opencode: inside `plugin/opencode/plugins/gse-guardrails.ts`, the `tool.execute.after` handler dispatches on `input?.tool ∈ {"edit", "write", "multiedit"}` via a plain `includes()` check.
- All three implementations call the same Python tool (`dashboard.py --if-stale`), guaranteeing identical behavior across platforms.

**2. Explicit-call regeneration (secondary, belt-and-suspenders):**
- Six activities call `dashboard.py` explicitly at the end of their workflow: `/gse:hug`, `/gse:go`, `/gse:produce`, `/gse:review`, `/gse:deliver`, `/gse:compound`. These are kept as-is — they provide a guaranteed pulse at every major checkpoint even if the hook is unavailable (e.g., platform does not register the hook, tool registry `~/.gse-one` is missing).
- These explicit calls do NOT use `--if-stale`. They unconditionally regenerate, which is acceptable: the debounce in `--if-stale` prevents the hook from firing right after, avoiding double work.

**3. Failure visibility (ensures users are never silently misinformed):**
- When `dashboard.py` encounters an internal exception (YAML parse error, file I/O failure, template error, etc.), its top-level `try/except` writes a marker file `.gse/.dashboard-error.yaml` containing a timestamp, a human-readable message, and a traceback.
- When the hook wrapper (the Python one-liner invoked by the PostToolUse hook) detects a non-zero exit code from the `dashboard.py` subprocess (e.g., `dashboard.py` crashed before reaching its own exception handler), it writes a minimal marker: `timestamp`, `message: "dashboard.py exited with code N"`, and the captured stderr. This is the double-defense layer — it covers catastrophic failures where `dashboard.py` cannot write the marker itself.
- On the next successful dashboard regeneration, `dashboard.py` reads `.gse/.dashboard-error.yaml` if present, injects a prominent red warning banner at the top of the generated HTML with the recorded timestamp and message, then deletes the marker. The banner reappears only if a new failure occurs.
- Marker file format:
  ```yaml
  timestamp: "2026-04-19T14:32:15Z"
  message: "YAML parse error in .gse/plan.yaml at line 42"
  traceback: |
    Traceback (most recent call last):
    ...
  ```

**Configuration:** a new field `dashboard.regen_debounce_seconds` is added to the `config.yaml` template (default: 5). The field is optional; if absent, `dashboard.py --if-stale` falls back to 5 seconds.

**Failure modes and fallbacks:**
- Tool registry `~/.gse-one` missing → hook exits silently (`os.path.isfile` guard), no marker, no user error — same behavior as any other `~/.gse-one`-dependent tool.
- `.gse/` missing in the current working directory (e.g., user is editing a non-GSE project with the plugin installed globally) → `dashboard.py --if-stale` exits 0 silently without creating any files. The hook wrapper does not treat this as a failure and does not write an error marker.
- `dashboard.py` fails inside its logic → marker written by the try/except; user sees banner on next regen.
- `dashboard.py` fails before try/except (very rare — syntax/import error) → hook wrapper captures non-zero exit and writes minimal marker.
- Hook wrapper itself fails → no marker (but this is a Python one-liner with no dependencies; extremely unlikely).

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

Cursor uses `rules/gse-orchestrator.mdc` with `alwaysApply: true` to inject the methodology permanently into every interaction:

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

### 6.4 Installer Differentiation

Although the `plugin/` source directory contains both `agents/gse-orchestrator.md` and `rules/gse-orchestrator.mdc`, the installer (`install.py`) ensures each platform only receives the appropriate file:

- **Claude Code:** Receives `agents/gse-orchestrator.md` (loaded via `settings.json → "agent"`). The `.mdc` file is ignored by Claude.
- **Cursor:** Receives `rules/gse-orchestrator.mdc` (loaded via `alwaysApply: true`). The installer **excludes** `agents/gse-orchestrator.md` from Cursor installations to prevent the orchestrator content from being loaded twice — once as an always-on rule and once as a named agent.

Cursor still receives the 8 specialized agents (`code-reviewer.md`, `architect.md`, etc.) in `agents/` for sub-agent delegation during REVIEW and other activities.

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

The `marketplace.json` install path is `"plugin"` (not `"dist/claude"`), reflecting the mono-plugin architecture.

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
├── plan.yaml                        # Living sprint plan (workflow, budget, coherence)
├── backlog.yaml                     # Unified work items (TASK) with git state per item
├── sources.yaml                     # External source registry
├── decisions.md                     # Decision journal (Inform + Gate tiers)
├── decisions-auto.log               # Auto-tier decision log
└── checkpoints/                     # Session checkpoints
    └── checkpoint-YYYY-MM-DD-HHMM.yaml
```

### 10.1 Sprint Plan Lifecycle (`.gse/plan.yaml`)

`.gse/plan.yaml` is a **living document** maintained by the orchestrator, not a static artefact. Its schema (goal, tasks, budget, workflow, coherence, risks) is defined in `src/activities/plan.md`.

**Creation** — Written by `/gse:plan --strategic` at sprint start. `workflow.expected` is initialized from the project mode:

| Mode | workflow.expected |
|------|-------------------|
| Full | `[collect, assess, plan, reqs, design, tests, produce, review, deliver]` (plus `preview` after `design` for web/mobile) |
| Lightweight | `[plan, reqs, produce, deliver]` |
| Micro | no `plan.yaml` — orchestrator falls back to file-existence checks |

**Maintenance** — After every activity transition, the orchestrator executes the **Sprint Plan Maintenance** protocol (defined in `gse-orchestrator.md`):
1. Move current activity from `workflow.active` to `workflow.completed` (with `completed_at` + notes).
2. **Post-REVIEW mutation (conditional FIX insertion):** If the activity just completed is `review`: if `review.md` contains at least one finding with severity HIGH or MEDIUM → insert `fix` at the head of `workflow.pending`. If no such finding exists → do not insert `fix`; if `fix` was previously in `workflow.expected`, move it to `workflow.skipped` with `reason: "no review findings"`.
3. Pop the next item from `workflow.pending` → `workflow.active`; record conditional skips in `workflow.skipped` with reason.
4. Evaluate non-blocking coherence: `budget_pressure` (>80% consumed with tasks remaining), `significant_scope_drift` (>50% tasks changed), `velocity_risk` (produce phase only).
5. React by mode: Full → Inform; Lightweight → one-line Inform; Micro → silent.
6. Update `status.yaml` cursor fields (`last_activity`, `last_activity_timestamp`, `lifecycle_phase`).

**Archival** — At DELIVER Step 9, the orchestrator reads `.gse/plan.yaml`, generates `docs/sprints/sprint-{NN}/plan-summary.md` (using the `plan-summary.md` template), and sets `plan.yaml.status: completed`. The snapshot is read-only — never consumed by the orchestrator, only used for human reference and COMPOUND process-deviation analysis.

**Reset** — At the start of the next sprint, `/gse:plan --strategic` overwrites `.gse/plan.yaml` with a fresh plan for the new sprint. The prior sprint's `plan-summary.md` remains in its sprint directory as the durable archive.

**Resilience** — `.gse/plan.yaml` is validated on write (YAML parseable). On corruption, the orchestrator restores from the latest checkpoint in `.gse/checkpoints/` and reports the error.

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

### 11.1 Generation Steps

| Step | Input | Output | Shared? |
|------|-------|--------|---------|
| 1 | `src/agents/gse-orchestrator.md` (body) | `plugin/agents/gse-orchestrator.md` + `plugin/rules/gse-orchestrator.mdc` | Body identical, frontmatter differs |
| 2 | `src/activities/*.md` (23) | `plugin/skills/<name>/SKILL.md` | Shared |
| 3 | `src/agents/*.md` (8 specialized) | `plugin/agents/<name>.md` | Shared |
| 4 | `src/templates/*` (19) | `plugin/templates/*` | Shared |
| 5 | Constants | `plugin/.claude-plugin/plugin.json` + `plugin/.cursor-plugin/plugin.json` | Two manifests |
| 6 | Shared shell commands | `plugin/hooks/hooks.claude.json` + `plugin/hooks/hooks.cursor.json` | Same logic, different format |
| 7 | — | `plugin/settings.json` | Claude-only |

---

## 12. File Inventory

| Category | Shared | Claude-only | Cursor-only | Source |
|----------|--------|-------------|-------------|--------|
| Skills | 23 | — | — | 23 activities |
| Agents | 9 (incl. orchestrator) | — | — | 9 agents |
| Templates | 19 | — | — | 19 templates |
| Manifest | — | 1 | 1 | — |
| Rules | — | — | 1 (.mdc) | from orchestrator |
| Hooks | — | 1 | 1 | shared constants |
| Settings | — | 1 | — | — |
| **Total** | **51** | **3** | **3** | **51 sources** |

Grand total: **57 files**. Generator: ~400 lines.

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
