# GSE-One — Implementation Design Document

**Input:** `gse-one-spec.md`, implementation inspection and restructuration pass

---

## 1. Introduction

This document details the implementation design of GSE-One: how the abstract concepts defined in `gse-one-spec.md` are realized as concrete artifacts (skills, agents, templates, tools, hooks) deployed across three coding agent platforms (Claude Code, Cursor, opencode).

**Scope:**
- Repository structure and generator mechanics (§3, §11)
- Skill designs that required non-trivial decisions (§4, §5)
- Cross-platform parity (§6)
- Hook system mechanics (§7)
- File inventory (§12) and implementation roadmap (§13)

**Out of scope:**
- Methodological principles (see spec §2)
- Per-activity workflow details (see each `src/activities/<name>.md`)
- Agent persona prompts (see each `src/agents/<name>.md`)

**Reading order:** start at §3 (architecture), then §4-§5 (skills), §6-§7 (cross-platform), §11-§12 (generator + inventory). Sections §8-§10 handle edge cases.

---

## 2. Plugin System Comparison

All three supported environments support git operations:
- Claude Code: via `Bash` tool (git commands) and `EnterWorktree`/`ExitWorktree` tools
- Cursor: via terminal commands and Composer agent (multi-file editing in worktree context)
- opencode: via `bash` tool (git commands) and native TS plugin hooks (`tool.execute.before/after`)

---

## 3. Architecture Overview

### 3.1 Repository Structure

> **Terminology mapping:** The directory structure maps to the concepts defined in the specification: `activities/` contains the 24 activity definitions (spec), each generated as a skill (`plugin/skills/`). `agents/` provides agent roles (spec). `templates/` provides templates. `hooks/` provides system hooks (spec P13).

```
gse-one/
├── README.md
├── LICENSE
├── src/                                 # Shared source of truth
│   ├── principles/                      # 16 principle definitions (P1-P16)
│   ├── activities/                      # 24 activity definitions
│   ├── agents/                          # 11 agent roles (10 specialized + gse-orchestrator)
│   │   ├── gse-orchestrator.md          # Identity agent — source for both platforms
│   │   ├── requirements-analyst.md
│   │   ├── architect.md
│   │   ├── test-strategist.md
│   │   ├── code-reviewer.md
│   │   ├── security-auditor.md
│   │   ├── ux-advocate.md
│   │   ├── guardrail-enforcer.md
│   │   ├── devil-advocate.md
│   │   ├── coach.md
│   │   └── deploy-operator.md
│   └── templates/                       # 30 templates (MANIFEST.yaml acts as self-descriptor and is not counted; after the sprint/audit.md MANIFEST entry is added (Cluster 10), template count and MANIFEST entries converge)
│
├── plugin/                              # Single deployable directory (Claude + Cursor + opencode)
│   ├── .claude-plugin/plugin.json       # Claude Code manifest
│   ├── .cursor-plugin/plugin.json       # Cursor manifest
│   ├── skills/                          # 24 skills (shared, `name:` field included)
│   ├── commands/                        # 24 flat /gse-<name>.md (Cursor + opencode)
│   ├── agents/                          # 11 agents (shared, incl. orchestrator)
│   ├── templates/                       # 30 templates (shared — MANIFEST.yaml acts as self-descriptor, excluded from count)
│   ├── rules/
│   │   └── gse-orchestrator.mdc         # Cursor-only (ignored by Claude/opencode)
│   ├── hooks/
│   │   ├── hooks.claude.json            # Claude Code format
│   │   └── hooks.cursor.json            # Cursor format
│   ├── settings.json                    # Claude-only (ignored by Cursor/opencode)
│   └── opencode/                        # opencode-specific subtree
│       ├── skills/                      # 24 skills with injected `name:`
│       ├── commands/                    # 24 gse-<name>.md slash commands
│       ├── agents/                      # 10 specialized (`mode: subagent`)
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

Both platforms use separate manifests with slightly different fields. The `repository` field is the **canonical default** for methodology feedback (COMPOUND Axe 2) — the agent reads this URL to create issues on the GSE-One repo. On opencode the equivalent lives at `opencode.json → gse.repository` (same constant, different manifest schema). The canonical default can be **overridden** by the user via `config.yaml → github.upstream_repo` (e.g., for private forks or corporate issue trackers). Full resolution order: `config.yaml → github.upstream_repo` → plugin manifest `repository` → skip Axe 2.

**Claude Code manifest** (`.claude-plugin/plugin.json`) — example; `"version"` is generated from the `VERSION` file by `gse_generate.py` at build time, so the `"X.Y.Z"` placeholder below is illustrative:

```json
{
  "name": "gse",
  "description": "GSE-One — AI engineering companion for structured SDLC management. 24 commands, adaptive risk analysis, unified backlog, knowledge transfer, worktree isolation.",
  "version": "X.Y.Z",
  "author": {
    "name": "GSE-One Project"
  },
  "repository": "https://github.com/gse-one/gse-one",
  "skills": "./skills/",
  "agents": "./agents/",
  "hooks": "./hooks/hooks.claude.json"
}
```

**Cursor manifest** (`.cursor-plugin/plugin.json`) — same note: `"version"` is build-generated:

```json
{
  "name": "gse",
  "displayName": "GSE-One",
  "description": "GSE-One — AI engineering companion for structured SDLC management. 24 commands, adaptive risk analysis, unified backlog, knowledge transfer, worktree isolation.",
  "version": "X.Y.Z",
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

**opencode manifest** (`opencode.json`) — opencode differs from Claude/Cursor: it does not declare `skills`/`agents`/`hooks` at top level (those are discovered from well-known directories), and its `repository` equivalent lives under the non-standard `gse.repository` key (opencode's schema has no top-level `repository` field). Instead, `opencode.json` declares a `permission` block with methodology defaults: `skill: { "*": "allow" }` (all GSE-One skills enabled), `question: "allow"` (native interactive-question tool — supports P4 interactive mode QCM across runtimes, cf. Activity Execution Fidelity Invariant §14.3), and a short `bash` denylist (`git push --force`, `rm -rf /`). Removing any of these from the default silently degrades functionality — notably, removing `question` forces QCM interactions into per-call permission prompts or text fallback.

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
| `skills/` (24) | **shared** | **shared** | All activity skills |
| `agents/` (11 in source, 10 for Cursor) | **shared** (11: 10 specialized + orchestrator) | **shared** (10: specialized only) | Agent roles for sub-agent delegation |
| `templates/` (29) | **shared** | **shared** | All artefact/config templates (MANIFEST.yaml included — self-descriptor) |

Claude ignores the `rules/` directory silently. Cursor ignores `settings.json` silently. The orchestrator agent (`agents/gse-orchestrator.md`) exists in the source `plugin/` directory for Claude Code, but the installer **excludes it from Cursor** installations — Cursor loads the orchestrator identity via `rules/gse-orchestrator.mdc` instead, avoiding double-loading of the same ~400-line content.

### 3.4 Dashboard parser format contracts

`plugin/tools/dashboard.py` reads `.gse/` state + sprint artefacts and reports project health. It is a **consumer** of the canonical artefact formats defined elsewhere — not a format authority. The contracts it depends on are:

- **REQ counting**: `reqs.md` emits `### REQ-NNN — {title}` (H3 heading) per template `src/templates/sprint/reqs.md`.
- **Review findings**: `review.md` emits `RVW-NNN [SEVERITY] — {title}` per reviewer agent output format (e.g., `src/agents/code-reviewer.md` "Output Format" section); baseline severity is `HIGH / MEDIUM / LOW` (plus `CRITICAL` reserved for P15 escalation at review merge time, spec §6.5). The parser tolerates square brackets `[HIGH]` (canonical) and parentheses `(HIGH)` (observed LLM drift) to stay robust against minor variations.
- **Health scores**: `status.yaml` stores them under `health.dimensions.<dim>` (nested) per `src/templates/status.yaml`.
- **Test evidence**: `docs/sprints/sprint-NN/test-reports/` per spec §6.3.

When any of these canonical formats changes, `dashboard.py` must be updated in the same commit. The generator does not regenerate `dashboard.py` — it is a direct-edit file carrying a `# @gse-tool dashboard <version>` header (per CLAUDE.md §Tool architecture).

---

## 4. Git-Integrated Skill Designs

> **Terminology:** This document describes the design of **skills** — the technical artifacts (`SKILL.md` files in `plugin/skills/`) that deliver the **activities** defined in the specification. Each skill implements exactly one activity: the skill `plan/SKILL.md` delivers the activity `/gse:plan`. See the specification for the formal relationship between activities, skills, commands, and inclusion policies.

> **Note:** This document details the skills that required specific design decisions (git integration, new mechanisms, complex workflows) — see §5 for the full index. The remaining activities are implemented directly from the spec without additional design and carry no dedicated §5.x subsection; their full definitions live in the specification.

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

1. Present using the canonical 5-option P14 preamble — see spec §P14 — P14 preamble — 5-option format (canonical) for the authoritative source. The preamble block is:
   ```
   **Learning opportunity:** <topic>
   **Context:** <why this matters now>
   **Options:**
   1. Quick overview (5 min) — concise introduction
   2. Deep session (15 min) — worked example + practice
   3. Not now — remind me next sprint
   4. Not interested — don't propose this topic again
   5. Discuss — tell me more before I decide
   ```
2. If accepted (option 1 or 2): run the reactive workflow above with the matching mode
3. If "Not now" (option 3): record in `status.yaml → learning_preambles[]` as deferred
4. If "Not interested" (option 4): record in `status.yaml → learning_preambles[]` as declined (never propose again)
5. If "Discuss" (option 5): engage conversationally; re-propose the preamble after clarification

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

### 5.13 `/gse:assess` — Gap Analysis Skill

```markdown
# skills/assess/SKILL.md
---
description: "Evaluate project artefact status against goals. Identifies covered, partial, and uncovered goals. Triggered when user asks to assess, evaluate progress, or check readiness."
---

# GSE-One Assess — Gap Analysis

## Workflow

### Step 1 — Gather Inputs
1. Run artefact scan inline (same as COLLECT Steps 1-5 — project files, sprint dirs, git state)
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

### 5.14 `/gse:go` — Orchestrator Decision Logic

```markdown
### Orchestrator Decision Tree (added to go skill)

When `/gse:go` is invoked:

**Activity Execution Fidelity Invariant (spec §14.3).** Realized by two rules operating at different granularities:

1. **Activity load** — whenever the orchestrator or an activity file resolves an execution (direct, inline-routed, or auto-triggered), the agent MUST open the target's source file — Claude Code: `$(cat ~/.gse-one)/skills/<name>/SKILL.md`; Cursor: `$(cat ~/.gse-one)/commands/gse-<name>.md`; opencode: `$(cat ~/.gse-one)/opencode/skills/<name>/SKILL.md`.

2. **Step execution** — the agent MUST execute every Step in order. Legitimate skip conditions: conditional Step (source declares a guard), user override, or frontmatter-declared exempt. Agent-driven skips MUST emit an Inform-tier note. Exempt activities (display-only): `/gse:status`, `/gse:health`, `/gse:backlog` display, `/gse:audit`.

The cross-reference convention "number + name" (CLAUDE.md) supports unambiguous Step identification for partial resumption (e.g., "resume at Step 2.7 — Git Baseline Verification").

**Step 1 — Detect project state:**

| Condition | Action |
|-----------|--------|
| `.gse/` absent + project has files | Adopt mode (see 5.4) |
| `.gse/` absent + project empty | HUG (LC00) |
| `.gse/` exists | Read `status.yaml` → Preflight sequence (Steps 1.5 / 1.6 / 1.7) → Step 2 |

**Preflight sequence (Steps 1.5 / 1.6 / 1.7):** three short checks run after project-state detection and before determining the next action. They mirror `gse-one-spec.md §14.3` numbering exactly; full semantics are in the spec, concrete shell commands are in `gse-one/src/activities/go.md`.

**Step 1.5 — Recovery Check:** scan every active worktree + `main` for uncommitted changes since the last session's checkpoint. If any are found, present a Gate (*Recover and resume / Review first / Discard / Skip*). Full rules in spec §14.3 Step 1.5 — Recovery Check; concrete detection in `gse-one/src/activities/go.md` Step 2 — Recovery Check (Unsaved Work Detection).

**Step 1.6 — Dependency Vulnerability Check:** when `config.yaml → testing.dependency_audit: true`, run the ecosystem-appropriate audit (`npm audit --audit-level=critical`, `pip-audit`, etc.). **Soft guardrail** on CRITICAL vulnerabilities: warn and propose remediation, continue on acknowledgment. Full rules in spec §14.3 Step 1.6 — Dependency vulnerability check; concrete tool invocation per ecosystem in `gse-one/src/activities/go.md` Step 2.5 — Dependency Vulnerability Check.

**Step 1.7 — Git Baseline Verification:** when `config.yaml → git.strategy` is `worktree` or `branch-only`, verify `main` has at least one commit. If not: **Hard guardrail** — auto-fix by committing `.gitignore` (creating it if missing), gated behind the Git Identity Verification preflight (P12.6) to avoid commits with a missing or placeholder author identity. Full rules in spec §14.3 Step 1.7 — Git baseline verification; concrete commands + Git Identity Gate in `gse-one/src/activities/go.md` Step 2.7 — Git Baseline Verification.

**Step 2 — Determine next action:**

**Primary source — `.gse/plan.yaml`:** when `plan.yaml` exists with `status: active`, the orchestrator uses `workflow.active` and `workflow.pending` to decide the next activity. This is more robust than checking for individual artefact files because `plan.yaml` is the declarative source of truth for sprint progression.

**Fallback:** if `plan.yaml` is absent (Micro mode or pre-v0.20 projects), fall back to file-existence checks against sprint artefacts (`reqs.md`, `design.md`, `test-strategy.md`, …) in `docs/sprints/sprint-{NN}/`.

Evaluate states in order — the first matching row wins.

| Current state | Next action |
|---------------|-------------|
| No sprint exists | Sub-decision: greenfield + no `docs/intent.md` → Intent Capture (Step 5); else Complexity Assessment (Step 6) → mode-appropriate start (Micro → PRODUCE; Lightweight → PLAN; Full → LC01 `COLLECT` > `ASSESS` > `PLAN`) |
| `plan.yaml` exists, `status: draft` | Resume PLAN — present plan summary, ask for approval Gate |
| `plan.yaml.workflow.active == reqs` | Start REQS — test-driven requirements (Hard guardrail: PRODUCE blocked until REQS exist) |
| `plan.yaml.workflow.active == design` | Start DESIGN (record `design` in `workflow.skipped` if not needed, then advance) |
| `plan.yaml.workflow.active == preview` | Start PREVIEW (should already be in `workflow.skipped` for CLI/API/data/embedded domains) |
| `plan.yaml.workflow.active == tests` | Start TESTS `--strategy` |
| `plan.yaml.workflow.active == produce`, none in-progress | Start PRODUCE on first planned TASK |
| `plan.yaml.workflow.active == produce`, tasks `in-progress` | Resume PRODUCE on current task |
| `plan.yaml.workflow.active == review` | Start REVIEW |
| `plan.yaml.workflow.active == fix` | Start FIX |
| `plan.yaml.workflow.active == deliver` | Start DELIVER |
| `plan.yaml.status == completed`, no compound | Start LC03: COMPOUND |
| Compound done | Propose next sprint → LC01 |
| Sprint stale (> `lifecycle.stale_sprint_sessions` sessions without progress) | Step 3 stale detection |

**Post-activity protocol:** after each activity completes, the orchestrator updates `.gse/plan.yaml` per the Sprint Plan Maintenance protocol (workflow transition, coherence evaluation, alerts by mode). See the orchestrator document for the full protocol.

**Implementation-only preflight extensions** (present in `gse-one/src/activities/go.md` but not in `gse-one-spec.md §14.3`): the running implementation adds two non-spec steps to the preflight sequence. They are orchestration concerns, not methodology requirements.

- **Step 2.6 — Dashboard Refresh** — after the preflight passes, regenerate `docs/dashboard.html` via `python3 "$(cat ~/.gse-one)/tools/dashboard.py"` so the current session starts from a fresh view. Silent unless it is the first generation (deferred pedagogy per HUG Step 5.5 — Dashboard Initialization).
- **Step 2.8 — Coach Workflow Overview (post-recovery)** — invoke the coach sub-agent with `moment: /gse:go after recovery check` per the Coach Invocation contract (`gse-one/src/agents/coach.md`) and design §5.17 to surface axes 2-8 (workflow overview) at the start of a resumed session. May return zero proposals (silent) or one Inform note.

Progression is defined as any TASK status change (`planned` → `in-progress`, `in-progress` → `review`, etc.) OR any `workflow.active` transition in `plan.yaml`. A session where neither happens counts as a session without progress, incrementing `sessions_without_progress` in `status.yaml` (writer: `/gse:go` Step 4 — Stale Sprint Detection and `/gse:resume` Step 6 — Finalize, per v0.52.0).

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

### 5.15 `/gse:deliver` — Deploy & Recovery Extensions

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

**Test-Specific Guardrails (spec §9.3.1).** `/gse:deliver` Step 1.5 enforces three guardrails before any merge:

**Guardrail 1 — Unexecuted tests (Hard).** Reads `test_evidence.status` on each TASK that implements a must-priority REQ (per §12.3 Backlog schema). If any status is in `{absent, fail, skipped}`, delivery is blocked and a Gate is presented with four options: (1) Run tests now inline via `/gse:tests --run` (recommended default), (2) Deliver partial (only passing REQs, requires Gate confirmation), (3) Reclassify TASK as spike/deferred (requires DEC-), (4) Discuss. Aligns the delivery gate with the canonical test run (spec §6.3 — Test Execution and Evidence) so the `test_evidence` field actually feeds enforcement. Complements the Activity Execution Fidelity Invariant §14.3 — which forces `/gse:produce` to execute the canonical test run in the first place; this guardrail catches the residual cases where evidence is nevertheless absent at delivery time.

**Guardrail 2 — Unexecuted test strategy (Hard).** Cross-checks `docs/sprints/sprint-{NN}/test-strategy.md` against `docs/sprints/sprint-{NN}/test-reports/` to detect declared test levels that have no `TCP-` campaign covering them. A level is *declared* when the strategy's H2 section (`## Unit Tests`, `## Integration Tests`, `## E2E Tests`, `## Policy Tests`) contains at least one `### TST-NNN` entry; it is *covered* when at least one TCP- campaign executed at least one TST- at that level (via the authoritative TST `level:` frontmatter field). If any declared level has no coverage, delivery is blocked and a Gate is presented with four options: (1) Run the missing level now via `/gse:tests --run --level <level>` (recommended default), (2) Deliver partial with the uncovered level rolled to next sprint (requires DEC-), (3) Reclassify the level as deferred for this sprint (requires DEC-), (4) Discuss. Catches the "pyramid gap" failure mode: a sprint that declares E2E tests in strategy but never actually runs any.

**Guardrail 3 — Stale test evidence (Soft).** Warns when `test_evidence.timestamp` predates the latest feature-branch commit (detected via `git log`). Non-blocking — the user may proceed with a note in DEC- or re-run tests at their discretion.

### 5.16 State Schemas

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

# (Sprint complexity budget lives in .gse/plan.yaml.budget — retired from status.yaml in v0.52.0)

# P16 pushback detection
consecutive_acceptances: 2
pushback_dismissed: 0

last_activity: /gse:produce
last_activity_timestamp: "2026-04-11T09:15:00Z"

# Stale sprint detection (complexity/session-based, not calendar-based)
sessions_without_progress: 0

# Review findings counter (used by hooks)
review_findings_open: 0

# /gse:audit history (appended by /gse:audit Step 6; capped at 20 entries)
audit_history:
  - timestamp: "2026-04-10T11:20:00Z"
    trigger: manual
    findings_total: 3
    findings_applied: 2
    findings_deferred: 1
    report_ref: docs/sprints/sprint-03/audit-2026-04-10T1120.md
```

**Sprint Freeze — Design Mechanics (spec §3.1 / lifecycle guardrail 3):**

The spec-level *Sprint Freeze* guardrail materializes as follows:

- **Conceptual trigger:** *the sprint plan status is completed* → **Concrete realization:** `.gse/plan.yaml` contains `status: completed`
- **Conceptual state:** *the number of the sprint in progress* → **Concrete realization:** `.gse/status.yaml` → `current_sprint: N`

**Writeable window:** a sprint is writeable by activities only while `.gse/plan.yaml` exists with `status: active`. When `/gse:deliver` Step 9 sets `status: completed`, the sprint becomes frozen for write operations.

**Activities that MUST consult `.gse/plan.yaml.status` before any write to `.gse/backlog.yaml` or transition of a TASK:**

- `/gse:task` (creates a new TASK)
- `/gse:produce` (transitions TASK `planned` → `in-progress` → `review`)
- `/gse:review` (transitions TASK `review` → `reviewed` if no HIGH/MEDIUM findings, else `review` → `fixing`)
- `/gse:fix` (transitions TASK `fixing` → `done`)

**Activities exempt from the Sprint Freeze preflight** (three categories — *closed-sprint consumers* operate on a sprint that is already frozen, e.g. post-delivery capitalization; *non-mutating activities* do not transition TASK state; *transition performers* are the activity that effects the freeze transition itself, and consulting a guard they are about to set would be self-defeating):

- `/gse:compound`, `/gse:integrate` — closed-sprint consumers (operate after deliver in LC03).
- `/gse:pause`, `/gse:resume`, `/gse:go`, `/gse:status`, `/gse:health`, `/gse:backlog`, `/gse:learn`, `/gse:hug`, `/gse:collect`, `/gse:assess`, `/gse:deploy` — non-mutating activities (do not transition TASK state; `/gse:deploy` writes `deploy.json` but not `backlog.yaml`).
- `/gse:plan --strategic` — sprint-opening activity; resets `plan.yaml.status` to `active` for the successor sprint.
- `/gse:deliver` — **transition performer**: Step 9.2 is the line that sets `plan.yaml.status: completed` (the freeze trigger itself). A preflight check at the start of deliver would be either pointless (status still `active`) or self-blocking (status already `completed`). Deliver is therefore exempt by necessity, not by scope.

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

**Git Identity Verification — Design Mechanics (spec P12.6 Git Identity Gate):**

The *Git Identity Verification* invariant declared in the spec materializes as a preflight check in activities that create commits programmatically.

**Detection logic:**
1. Run `git --version` to confirm git is installed. If exit code is non-zero (typically 127), abort the activity with: *"git is not installed on this system. GSE-One requires git — please install it first."* No Gate is shown.
2. Query identity at both scopes:
   - Global: `git config --global user.name`, `git config --global user.email`.
   - Local: `git config --local user.name`, `git config --local user.email` (only meaningful inside a git repo; outside, these return non-zero — treat as "absent").
3. If both name AND email are set at EITHER scope (global OR local) → identity OK, proceed with the commit.
4. If any of the four required values is missing → trigger the Git Identity Gate.

**Gate options → concrete actions:**

| Option | Shell command(s) | Prompt to user |
|--------|------------------|----------------|
| 1. Set global identity | `git config --global user.name "<name>"` + `git config --global user.email "<email>"` | Ask for name, then email (one at a time for beginners). Validate email format (`@` + dotted domain). |
| 2. Set local identity  | `git config --local user.name "<name>"` + `git config --local user.email "<email>"` | Same prompts as option 1. |
| 3. Quick placeholder   | `git config --local user.name "GSE User"` + `git config --local user.email "user@local"` | No prompt. After execution, print a reminder: *"Placeholder identity set locally for this project. If you plan to share or push this repo, run `/gse:hug --update` or update manually with `git config --global user.name/email`."* |
| 4. I'll set it myself  | (none) | Agent prints a copy-paste block with the two `git config --global ...` commands and waits for user confirmation ("done" / "ok"). On confirmation, the agent re-runs detection. If identity still missing, the agent re-presents the Gate. |
| 5. Discuss             | (none) | Agent explains the scope difference (global = all your projects; local = this project only; placeholder = disposable for throwaway work), the fact that commits on pushed branches are publicly visible, then re-presents options 1-4. |

**Email validation rule (options 1 and 2):** the agent accepts the email if it contains exactly one `@`, with a non-empty local part before `@` and a domain part after `@` that contains at least one `.` with non-empty labels on both sides of that dot. On validation failure, the agent re-prompts with: *"That doesn't look like a valid email address. Could you enter it again? (e.g., you@example.com)"*. No external validation (no DNS lookup).

**Placeholder reminder (option 3):** the reminder fires once, immediately after the placeholder is set. It is NOT repeated on subsequent activities — we rely on the user's awareness. This reflects the "cheap escape hatch for quick tests" intent of option 3; making it noisy would defeat its purpose.

**Activities that MUST invoke the preflight:**
- `/gse:hug` Step 4 — foundational commit
- `/gse:go` Step 2.7 — auto-fix commit when baseline is missing

Additional activities that SHOULD invoke the preflight in future releases (tracked as AMÉL follow-ups):
- `/gse:pause` — auto-commits of uncommitted work
- `/gse:deliver` — merge commits on `main`
- `/gse:task`, `/gse:produce`, `/gse:fix` — feature branch commits

**Implementation pattern:** the preflight is NOT extracted into a separate shared file. Each concerned activity SKILL.md inlines the detection + Gate sequence in its Step 4 / Step 2.7 / Step 0 block. Rationale: inlining avoids indirection when the agent reads a skill and removes dependency on loading additional context. The orchestrator documents the canonical invariant (single source of truth for the Gate shape and options).

**Exempt activities:** read-only and planning activities that do not create commits (`/gse:status`, `/gse:health`, `/gse:backlog`, `/gse:learn`, `/gse:resume`, `/gse:collect`, `/gse:assess`, `/gse:plan`, `/gse:reqs`, `/gse:design`, `/gse:preview`, `/gse:tests`, `/gse:review`, `/gse:compound`, `/gse:integrate`, `/gse:deploy`).

**Root-Cause Discipline — Design Mechanics (spec P16 "Root-Cause Discipline before patching"):**

The discipline materializes as a 4-step sub-protocol applied inside any fix flow. The orchestrator owns the invariant; `/gse:fix` Step 3 is the canonical in-lifecycle implementation; ad-hoc bug reports outside the lifecycle trigger the same protocol via the orchestrator.

**Step-by-step mechanics:**

| Step | Agent action | Blocking conditions |
|------|--------------|---------------------|
| **1. Read** | Open the relevant source file(s) via the Read tool in the current turn. Agent records which files were read. | A file must have been read in the current turn (not in a previous turn, not cached from context compaction) before it can be patched. |
| **2. Symptom** | Extract observable fact from the report. If report is vague, prompt the user for ONE concrete piece of evidence (console error, screenshot, specific interaction). | Empty/vague symptoms are not acceptable — the agent cannot proceed to step 3 without a specific observable. |
| **3. Hypothesis + Evidence** | Write in chat: hypothesis, proposed test, P15 confidence tag. Run the test (execute a command, inspect a file, run a unit test, ask the user to perform a concrete action). | If evidence contradicts → loop back to step 3 with a new hypothesis. If evidence confirms → proceed to step 4. Do NOT skip to step 4 without a confirming test result. |
| **4. Patch** | Apply the fix. Commit trailer MUST include `Root cause:` and `Evidence:` lines. | Commit is refused if these trailer lines are absent (can be enforced by a future pre-commit hook — for now, relies on the activity writing the commit message). |

**Counter persistence:**

| Field | File | Lifecycle |
|-------|------|-----------|
| `fix_attempts_on_current_symptom` | `.gse/status.yaml` | Persists across `/gse:pause` / `/gse:resume`. Reset on user confirmation of resolution, explicit symptom change, or sprint promotion (`/gse:plan --strategic` sets it back to 0 at the same time as sprint counter advance). |

**Increment logic:** after a patch is applied (step 4), the agent asks the user to re-verify the symptom (or automatically re-runs the evidence test if available). If the symptom persists, the counter increments. If resolved, the counter resets to 0.

**Threshold logic (read `profile.yaml → dimensions.it_expertise`):**

| Expertise | Threshold | Escalation action |
|-----------|-----------|-------------------|
| `beginner` | 2 | Freeze patching; spawn devil-advocate in focused-review mode (below). |
| `intermediate` | 3 | Same. |
| `expert` | 4 | Same. |

**Devil-advocate focused-review input format (on escalation):**

```yaml
mode: focused-review
symptom: "<precise observable>"
hypotheses_tried:
  - hypothesis: "<text>"
    evidence: "<result that contradicted>"
    confidence: Moderate
  - hypothesis: "<text>"
    evidence: "<result>"
    confidence: High
patches_applied:
  - file: "src/foo.js"
    summary: "<what was changed>"
    commit: "<hash>"
files_under_suspicion:
  - "src/foo.js"
  - "src/bar.js"
  - "index.html"
```

The devil-advocate runs its standard checklist (hallucination hunt, assumption challenge, complaisance detection, temporal validity, etc.) **focused on the symptom** and returns findings. The agent displays the findings and MUST address at least one finding (fix it, explicitly dismiss with a DEC-, or request user input) before any further patch on this symptom is authorized.

**Ad-hoc bug reports outside the lifecycle:**

The orchestrator detects user messages matching bug-report patterns ("doesn't work", "broken", "not working", "expected X but got Y", screenshots of errors, pasted console output) **outside of `/gse:fix`** (e.g., during PRODUCE, after DELIVER, or in idle state). On detection, the orchestrator applies the Root-Cause Discipline protocol inline, just as `/gse:fix` Step 3 would — same 4 steps, same counter, same escalation. The counter is a single transversal field (`fix_attempts_on_current_symptom` in `status.yaml`), not scoped per activity.

**Activities concerned:**
- `/gse:fix` (canonical, in-lifecycle) — applied in Step 3
- Any activity where a user reports a symptom (PRODUCE, post-DELIVER idle, etc.) — orchestrator-driven

**Exempt activities:** read-only and planning activities (`/gse:status`, `/gse:health`, `/gse:backlog`, `/gse:learn`, `/gse:resume`, `/gse:collect`, `/gse:assess`, `/gse:plan`, `/gse:reqs`, `/gse:design`, `/gse:preview`, `/gse:tests`, `/gse:compound`, `/gse:integrate`).

**Failure modes:**
- User refuses to provide a concrete observable at step 2 → agent proceeds with a *best-effort* symptom description but flags the uncertainty in the hypothesis confidence tag (max Moderate).
- Evidence test requires a user action (e.g., "open the console and tell me what you see") → agent waits; no counter increment until the user responds and a patch is attempted.
- Devil-advocate returns no findings (the focused review confirms the code is sound) → the escalation is logged as a DEC-, the counter is reset, and the agent suggests looking at external causes (environment, cache, network, permissions) with the user.

**Scope Reconciliation & Inform-Tier Summary — Design Mechanics (spec P6 Scope Reconciliation + P16 Inform-Tier Decisions Summary):**

Two complementary closure mechanisms for creator activities. The first (Scope Reconciliation) detects *what* was delivered outside the plan; the second (Inform-Tier Summary) detects *how* the delivered work was shaped (micro-decisions). Both fire at the end of creator activities.

**1. Scope Reconciliation — deterministic git-diff-based detection:**

*Applies to:* `/gse:produce`, `/gse:task` (activities that produce code or executable artefacts).

**a. Record activity start (at the start of the activity):**

```bash
git rev-parse HEAD
```

Save the result to `.gse/status.yaml → activity_start_sha`. Done right after the git setup step (feature branch / worktree created) so the diff captures only the activity's contribution.

**b. Compute deltas (at activity closure, before Finalize):**

```bash
git diff --name-status {activity_start_sha}..HEAD
git log {activity_start_sha}..HEAD --pretty=format:"%H%n%B%n---"
```

The first command gives the list of changed files (status: A/M/D/R). The second gives each commit's body, from which the agent parses the `Traces:` trailer line (already mandated by the produce/task commit format).

**c. Load planned scope:** read `docs/sprints/sprint-{NN}/reqs.md` (list of REQ-NNN) and `docs/sprints/sprint-{NN}/design.md` (list of DEC-NNN) to build `planned_ids = {REQ-001, REQ-002, DES-001, ...}`.

**d. Categorize each delta:**

| Condition | Category |
|-----------|----------|
| File added, no commit touching it has `Traces:` listing any `planned_id` | `ADDED out of scope` |
| File modified, commits touching it introduce `Traces:` IDs outside `planned_ids` | `MODIFIED beyond plan` |
| REQ or DEC in `planned_ids` with zero commits referencing it | `OMITTED` |
| Otherwise | `aligned` (no output) |

**e. Present the Gate if any non-`aligned` delta exists.**

**f. Execute the chosen option:**

- **Option 1 (Accept as deliberate):** append a single grouped DEC-NNN to `docs/sprints/sprint-{NN}/decisions.md`:
  ```markdown
  ### DEC-{next_id} — Out-of-scope additions during {activity} (TASK-{ID})
  
  During implementation of TASK-{ID}, the following items were delivered beyond the approved plan:
  - `{path/to/file1}` — {one-line rationale}
  - `{path/to/file2}` — {one-line rationale}
  
  Grouped rationale: {thematic summary — e.g. "user convenience additions that emerged during implementation and were judged individually low-risk"}
  Reconciled at: {timestamp}
  Traces: {associated REQ-NNN if any}
  ```
  For OMITTED items: move their derived TASK to backlog pool with `status: planned`, `sprint: null`.

- **Option 2 (Revert out-of-scope):** for each ADDED file, revert the originating commit(s). Verify the worktree still builds.

- **Option 3 (Amend):** append a **lightweight** REQ-NNN / DEC-NNN to the relevant sprint artefact — **no elicitation Gate, no approval cycle**. Format example:
  ```markdown
  ### REQ-{next_id} — {short title} [amended during {activity}]
  
  Acceptance criterion: {one line}
  Rationale: emerged during {activity}; reconciled at {timestamp}.
  ```

- **Option 4 (Discuss):** per-delta mixed decisions — iterate through each delta with its own 1/2/3/discuss choice.

**g. Clear `activity_start_sha`** to empty string after the reconciliation completes.

**2. Inform-Tier Summary — agent-maintained decision list:**

*Applies to:* `/gse:design`, `/gse:preview`, `/gse:produce`, `/gse:task`.

**a. During the activity:** the agent internally tracks Inform-tier decisions as it makes them. This is a conversation-scope list (not persisted to disk during the activity); it's assembled from the agent's own Inform-tier actions per P7.

Typical examples: *"chose `crypto.randomUUID()` over the uuid package"*, *"folder `src/components/` over `src/ui/`"*, *"HashRouter over BrowserRouter"*, *"integer cents over float euros for money"*.

**b. At activity closure:** present the list. If empty, display the standard empty-state message (*"No inform-tier decisions made this activity — all choices were Gated."*).

**c. On "Accept all":** append an `## Inform-tier Decisions` section to the activity's artefact:

| Activity | Destination |
|----------|-------------|
| `/gse:design` | `docs/sprints/sprint-{NN}/design.md` |
| `/gse:preview` | `docs/sprints/sprint-{NN}/preview.md` |
| `/gse:produce` | In the produce report (commit message body) AND as a section in `docs/sprints/sprint-{NN}/produce-{TASK-ID}.md` if such artefact exists |
| `/gse:task` | In the ad-hoc task commit message body |

**d. On "Promote":** for each selected decision, walk through a standard Gate (Question / Context / Options with consequence horizons per P8 / Discuss). If the user picks an alternative, the agent rolls back the inform-tier choice and applies the new one. The resulting DEC-NNN is added to `decisions.md`.

**Ordering at activity closure:**

Scope Reconciliation runs FIRST (material deltas), Inform-Tier Summary SECOND (design micro-choices). Both run before the activity's Finalize step (status.yaml update, dashboard regen).

**Exempt activities** (neither mechanism applies): `/gse:status`, `/gse:health`, `/gse:backlog`, `/gse:learn`, `/gse:resume`, `/gse:collect`, `/gse:assess`, `/gse:plan`, `/gse:reqs`, `/gse:tests`, `/gse:review`, `/gse:fix`, `/gse:deliver`, `/gse:compound`, `/gse:integrate`, `/gse:deploy`, `/gse:hug`, `/gse:go`, `/gse:pause`.

**Failure modes:**
- `activity_start_sha` missing or invalid (interrupted session, Micro mode, `git.strategy: none`) → skip Scope Reconciliation with a one-line Inform note ("Scope Reconciliation skipped: no git baseline recorded"). Proceed with Inform-Tier Summary normally.
- Commits without `Traces:` trailer (user commited manually, or legacy commits) → agent can still enumerate files but cannot match them to planned IDs. Treats the files as unlabeled and asks the user to clarify in a one-shot prompt.
- Plan artefacts missing (`reqs.md` or `design.md` absent — Lightweight mode, or early sprint) → skip Scope Reconciliation; Inform-Tier Summary still applies.

**Intent Capture — Design Mechanics (spec §3 Step 5 Intent Capture, P6 INT- prefix):**

The *Intent Capture* flow formalizes the greenfield onboarding step that precedes `/gse:collect`. It replaces the pre-v0.28 "Intent-first mode" (which was beginner-only and did not produce a formal artefact).

**Trigger detection (in `/gse:go` Step 7):**

1. Run the project file scan (same exclusion rules as `/gse:go` Step 1: `.cursor`, `.claude`, `.gse`, `.git`, `.vscode`, `.idea`, `.fleet`, `node_modules`, `__pycache__`, `.venv`, `target`, `dist`, `build`).
2. Count **source files** = non-excluded files that are not pure documentation (`*.md`, `*.txt`, `LICENSE`, `README`). Greenfield = `source_files_count == 0`.
3. Check for existing intent artefact: `os.path.isfile("docs/intent.md")` AND its frontmatter `id` starts with `INT-`. If present, skip Intent Capture (intent already captured; use existing).
4. If greenfield AND no intent artefact → enter Intent Capture.

**Artefact file (canonical template at `gse-one/src/templates/intent.md`):**

```markdown
---
id: INT-001
artefact_type: intent
title: "{project_name} — Project Intent"
sprint: 0
status: approved
created: {YYYY-MM-DD}
author: pair
---

# {project_name} — Project Intent

## Description (verbatim user statement)

> {exact user statement, quoted literally — no paraphrasing at this step}

## Reformulated understanding

{agent's reformulation in plain language, validated by the user in the elicitation loop}

## Users

- {single user / small shared group / public / specific role — e.g., "single user, no accounts"}

## Boundaries (explicit out-of-scope)

- {thing 1 — e.g., "no multi-device sync"}
- {thing 2 — e.g., "no server component"}
- ...

## Open questions

_Optional section. Lists ambiguities to resolve in downstream activities, each tagged with its natural home._

- **OQ-001** — single user or multi-user? (`resolves_in: PLAN`, `impact: scope-shaping`, `status: pending`)
- **OQ-002** — which categories at start? (`resolves_in: REQS`, `impact: behavioral`, `status: pending`)
```

**Field semantics:**

| Field | Rule |
|-------|------|
| `id` | `INT-001` on first capture. If the user pivots the project later (new intent), the existing artefact is renamed to `docs/archive/intent-v01.md` (preserving its original `id: INT-001`), and a new `docs/intent.md` is created with `id: INT-002`. The old `INT-001` is kept read-only for historical traceability. |
| `status` | `draft` during elicitation, `approved` once the user has confirmed the reformulated understanding. |
| `sprint` | Always `0` — intent precedes any sprint. |

**Elicitation loop (agent behavior during Step 5):**

1. Ask the intent question in the user's chosen language (from HUG profile). For beginners: one open-ended question. For intermediate/expert: may batch with follow-ups on users, boundaries, domain.
2. Capture the user's **first verbatim response** — this becomes the *Description* section, quoted literally. Do NOT edit or paraphrase.
3. Reformulate in plain language and present as bullet list. Ask for confirmation. Iterate until the user confirms.
4. For **Users** and **Boundaries**: if not explicit in the user's statement, ask brief follow-ups. Don't assume.
5. For **Open questions**: the agent lists its own remaining ambiguities. The user may add or dismiss.
6. Write `docs/intent.md` atomically (all sections at once) when the user approves.

**Integration with downstream activities:**

- `/gse:collect` (internal mode) now starts with **Step 0: Verify intent exists**. If greenfield and no `docs/intent.md`, the agent inlines Intent Capture (re-runs `/gse:go` Step 7 inline) before the inventory step.
- `/gse:assess` reads `docs/intent.md` and parses the *Open questions* section. Questions tagged `natural home: ASSESS` are surfaced as explicit gaps to resolve.
- `/gse:plan --strategic` uses the backlog items seeded during Intent Capture (which carry `traces.derives_from: [INT-001]`).
- `/gse:reqs` reads the intent artefact to cross-check that all user-stated goals are covered by at least one REQ. Requirements get `traces.derives_from: [INT-001, ...]`.

**Pivot / re-capture command:** out of scope for v0.28 — will be added later as `/gse:intent --pivot` or similar. For now, if the user wants to replace the intent, they manually archive `docs/intent.md` and re-run `/gse:go` on a greenfield-looking project (or use `/gse:hug --update` to reset the first-project flag).

**Exempt / skip conditions:**
- Existing project (non-greenfield) → no Intent Capture; inferred implicit from existing artefacts.
- Adopted project (`/gse:go --adopt`) → no Intent Capture; the adoption flow has its own analysis (see spec §14.2 — Adopting GSE-One on an Existing Project).
- User explicit skip ("I know the process", "no need") → no `intent.md` written, Inform note logged.
- Existing `docs/intent.md` present → skip Intent Capture, use the existing artefact.

**Failure modes (Intent Capture):**
- User refuses to describe intent → `/gse:go` proceeds to Step 6 (Complexity Assessment) without an intent artefact. A one-line Inform note is displayed: *"Intent Capture declined — I'll infer from your first sprint work. You can create `docs/intent.md` manually at any time."*
- User describes intent but declines to validate the reformulation → agent writes the artefact with `status: draft` and proceeds. The draft can be promoted to `approved` by running `/gse:go` again.

**Open Questions Resolution — Design Mechanics (spec P6 Open Questions + activity-entry scan):**

The *Open Questions* mechanism is the operational backbone that makes the `resolves_in` tag useful across the lifecycle.

**Artefact location:** open questions live in a dedicated `## Open Questions` markdown section at the end of the artefact that raises them. Typical origin artefacts:
- `docs/intent.md` — questions raised during Intent Capture (greenfield projects)
- `docs/sprints/sprint-{NN}/assess.md` — questions raised by gap analysis
- `docs/sprints/sprint-{NN}/reqs.md` — questions discovered during requirements elicitation
- `docs/sprints/sprint-{NN}/design.md` — questions deferred to later DESIGN decisions

**Format (markdown, human-readable, lightly parseable):**

Each entry is a bullet with sub-fields on indented lines:

```markdown
## Open Questions

- **OQ-001** — single user or multi-user?
  - resolves_in: PLAN
  - impact: scope-shaping
  - status: pending
  - raised_at: INT-001

- **OQ-002** — which categories at start?
  - resolves_in: REQS
  - impact: behavioral
  - status: pending
  - raised_at: INT-001
```

Once resolved, the entry is updated in place (status flipped, resolution fields populated):

```markdown
- **OQ-001** — single user or multi-user?
  - resolves_in: PLAN
  - impact: scope-shaping
  - status: resolved
  - raised_at: INT-001
  - resolved_at: "2026-04-19T14:32:00Z"
  - resolved_in: PLAN
  - answer: "single user, no accounts"
  - answered_by: user
  - confidence: Verified
  - traces: [DEC-005]
```

**Activity-entry scan implementation:**

At Step 0 of `/gse:assess`, `/gse:plan`, `/gse:reqs`, and `/gse:design`, the agent:

1. **Enumerate sources** — list all artefacts that may carry `## Open Questions` sections:
   - Always: `docs/intent.md`
   - If `.gse/status.yaml → current_sprint` ≥ 1: `docs/sprints/sprint-{NN}/*.md` for the current sprint
2. **Parse each section** — for each source file, scan for the `## Open Questions` heading and parse the bullet entries. Extract `id`, `resolves_in`, `impact`, `status`.
3. **Filter** — keep only entries with `status: pending` AND `resolves_in == <current_activity>`.
4. **Short-circuit** — if the filtered list is empty, skip Step 0 entirely and proceed to Step 1.
5. **Enter Open Questions Gate** — otherwise, present the questions according to the user's `decision_involvement` mode (see below).

**Gate behavior by `decision_involvement`:**

| Mode | Behavior |
|------|----------|
| `autonomous` | The agent generates proposed answers using (a) the intent artefact, (b) the project profile (domain, team context), (c) GSE convention defaults (e.g., browser-local storage for solo single-user web apps). For low-impact questions (`impact: behavioral` or `cosmetic`), the answers are applied silently and reported as Inform-tier. For high-impact questions (`impact: scope-shaping` or `architectural`), a Gate is raised per question for explicit user validation. |
| `collaborative` (default) | Per-question or per-theme Gate. Agent proposes answer + rationale + consequence horizons (P8). User validates, modifies, or rejects. `answered_by: user` after confirmation, `answered_by: agent` if user accepts verbatim (recorded as meta-decision). Theme batching (P9) activates when ≥ 3 questions — the agent groups them by detected theme (e.g., *users & data / domain model / UX & output*) to reduce cognitive load. |
| `supervised` | Each question is a neutral full Gate — the agent does not pre-answer. It presents the question, lists candidate options if relevant, and waits for the user's answer. `answered_by: user`. This mode is strictly more demanding — use it for high-stakes projects or first-time learners of the methodology. |

**Recording resolutions (all modes):**

For each resolved question, the agent:

1. Updates the origin artefact's `## Open Questions` entry in place (sets `status: resolved`, fills `resolved_at`, `resolved_in`, `answer`, `answered_by`, `confidence`, `traces`).
2. If the resolution is substantial (scope-shaping OR architectural OR otherwise judged non-trivial), creates a `DEC-NNN` entry in `docs/sprints/sprint-{NN}/decisions.md` with `traces.derives_from: [OQ-NNN]` and a short rationale.
3. If the resolution has `impact: scope-shaping` AND the current sprint plan exists (`.gse/plan.yaml`), propagates the sizing delta: update affected TASK entries in `backlog.yaml`, and if the total exceeds the sprint budget, triggers a `/gse:plan --tactical` Gate.

**Mode mapping to spec P7 tiers:**

| Mode | Low-impact question | High-impact question |
|------|--------------------|---------------------|
| `autonomous` | Auto (Inform-tier logged) | Gate (escalated) |
| `collaborative` | Inform or Gate (per agent judgment, default Gate) | Gate |
| `supervised` | Gate | Gate |

**Provenance and cross-activity flow:**

- A question raised in `INT-001` with `resolves_in: PLAN` will be resolved at the first `/gse:plan --strategic` call — not before, not after.
- A question raised in `docs/sprints/sprint-02/assess.md` with `resolves_in: DESIGN` will wait until `/gse:design` of the same sprint.
- If an activity is skipped in the current sprint's workflow (e.g., `/gse:preview` skipped for a CLI project), questions targeting that activity roll forward to the next lifecycle boundary where they make sense, or are escalated as a warning at DELIVER.

**Failure modes:**

- Malformed `## Open Questions` section (missing fields, invalid `resolves_in` values) → agent reports a parse warning, skips the malformed entry, continues with the rest. The user is asked to fix the file if the malformed entry is ambiguous.
- A question has `resolves_in: PLAN` but no `/gse:plan` is ever called (Micro mode) → the question remains `pending` until `/gse:compound` or `/gse:deliver`, which surface pending OQs as a reminder in the release notes.
- A question is resolved outside the agent (user edits the file manually) → the next activity-entry scan reads the updated status and respects it.

**Scope-resolve as Step 0 of `/gse:plan`:** the transversal activity-entry scan IS the scope-resolve mechanism. `/gse:plan --strategic` Step 0 scans for `resolves_in: PLAN` questions; if any have `impact: scope-shaping`, the Gate explicitly frames them as "scope-shaping questions — resolve before sprint selection". No separate `/gse:scope` skill is introduced.

**Config Application Transparency — Design Mechanics (spec P7 Config Application Transparency):**

The discipline surfaces every materialization of a `config.yaml` field with user-visible consequences as a one-line Inform message. No Gate, no new state — just a disciplined label at the moment of action.

**Standard format:**

```
Config applied: <field_path> = <value> (<origin> — to change: /gse:hug --update or edit .gse/config.yaml)
```

Where:
- `<field_path>` is the full dotted path (e.g., `git.strategy`, `testing.coverage.minimum`).
- `<value>` is the current applied value.
- `<origin>` is either *methodology default* or *user choice*, determined at display time by comparing the current value to the canonical default in `gse-one/src/templates/config.yaml`.

**Beginner adaptation (per P9):**

For `it_expertise: beginner`, the field path is translated to plain language and the technical "to change" command is replaced with a soft hint:

```
Config applied: I'm using separate workspaces for each task (default — say "I'd prefer a simpler setup" if you want to change)
```

**Origin classification algorithm:**

```python
# pseudo
default_value = read_template_field("git.strategy")      # e.g., "worktree"
current_value = read_config_field("git.strategy")         # e.g., "worktree" or "branch-only"
origin = "methodology default" if current_value == default_value else "user choice"
```

No persistent state is needed — the classification is computed fresh at each materialization.

**Fields covered in v0.30:**

| Activity | Field | Materialization point |
|----------|-------|----------------------|
| `/gse:produce` | `git.strategy` | Step 2 (Git Setup) — creates feature branch and optionally worktree |
| `/gse:task` | `git.strategy` | Step 4 (Git Setup) — same as produce |

**Extension pattern for future fields:**

When a new field with user-visible consequences is added (e.g., `testing.coverage.minimum` enforced at `/gse:tests`, or `git.tag_on_deliver` at `/gse:deliver`), the concerned activity's spec adds an Inform line using the standard format at the relevant step. No change to the orchestrator or spec P7 (the rule is already general). Each activity's SKILL.md documents which fields it materializes in a dedicated note.

**Scope of "user-visible consequences":**

Not every config field triggers the Inform line — only those that cause a concrete action the user might notice:
- Creates files or directories (e.g., worktree directories)
- Modifies git state (branches, tags)
- Enforces a hard threshold (coverage minimum)
- Changes delivery behavior (tag, cleanup)

Fields that only affect internal agent behavior (e.g., `interaction.verbosity`, `decisions.tier_bias`) do NOT trigger the Inform — they are transparent by design.

**Failure modes:**

- Template file not found (cannot compute origin) → skip the origin classification, emit the note without it: *"Config applied: `<field>` = `<value>` (to change: /gse:hug --update or edit .gse/config.yaml)"*
- Config field missing from config.yaml (should not happen — HUG always fills defaults) → agent emits a warning and falls back to the methodology default value before proceeding.

**Methodology Feedback — Design Mechanics (spec §3 COMPOUND Axe 2 + P14 methodology self-improvement):**

The methodology-feedback flow operates entirely inside `/gse:compound` Axe 2 and `/gse:integrate` Axe 2. No new skill, no new artefact type, no new profile flag.

**Source material (scanned during COMPOUND Axe 2):**

| Source | What to look for |
|--------|------------------|
| `docs/sprints/sprint-{NN}/review.md` | Findings tagged `[METHOD-FEEDBACK]` (process-level issues, not product-level) |
| `docs/sprints/sprint-{NN}/decisions.md` | DEC- entries with attribute `type: methodology-deviation` (the agent deviated from the methodology and logged why) |
| `.gse/status.yaml → activity_history[*].notes` | Free-text notes attached to activity completions |
| Conversation context | Friction points, user explicit complaints, or recurring questions the agent encountered during the sprint (agent subjective memory) |

**Convention for logging during the sprint:** the agent adds a `[METHOD-FEEDBACK]` tag or `type: methodology-deviation` attribute whenever it observes a process-level friction, deviation, or improvement opportunity. The tag is **optional** — the agent is not required to log every friction. It is a signal that compound Axe 2 can consume. For v0.31, the tag convention is documented; its broader adoption in `/gse:review` and `/gse:fix` can follow in future releases if the source coverage proves insufficient.

**Closure Gate at end of Axe 2 (3 options):**

After synthesizing the observations into themes, the agent presents:

```
I've consolidated N methodology observations from this sprint, grouped into M themes.
How should I route them?

1. Export as a local feedback document only
   → docs/sprints/sprint-{NN}/methodology-feedback.md
   You can share or submit it manually (email, chat, issue tracker).

2. Propose GitHub tickets (quality-filtered, theme-grouped, deduplicated)
   → I'll walk you through each proposed issue for validation before
     submission to the GSE-One plugin repository via /gse:integrate Axe 2.

3. Both — export AND propose tickets.

4. Discuss — I'll show a one-line-per-observation summary first.
```

**Output A — local export file:**

Written at `docs/sprints/sprint-{NN}/methodology-feedback.md` when option 1 or 3 is chosen. Structure:

```markdown
---
artefact_type: methodology-feedback
title: "Sprint {NN} — Methodology Feedback"
sprint: {NN}
created: "{YYYY-MM-DD}"
status: exported
---

# Sprint {NN} — Methodology Feedback

## Summary

{1-3 sentences giving the overall experience of this sprint with the methodology}

## Observations grouped by theme

### Theme 1: {name}

**Observation:** {specific, with context — file, step, quote, or artefact ref}

**Source:** {list of artefact references — RVW-NNN, DEC-NNN, activity in activity_history, …}

**User quote** (if relevant): *"{verbatim}"*

**Proposed improvement:** {actionable suggestion}

### Theme 2: ...
```

**Output B — ticket proposals (Gate path):**

For each theme that passes the quality filter, the agent presents a per-theme Gate:

```
**Proposed ticket 1 of N:**

Title: {~60 chars, imperative or descriptive}
Label: enhancement | bug | documentation
Body:
  Context: {what the user was trying to do}
  Observation: {what went wrong or was awkward, with source refs}
  Proposed change: {actionable suggestion}
  Sources: {list of RVW/DEC/activity refs from the sprint}
Dedup check: {"No open issue matching keywords" | "Potential match found: #NNN"}

Options:
1. Approve — I'll create this issue via /gse:integrate Axe 2.
2. Edit — adjust title/body/label before creating.
3. Skip — exclude this ticket.
4. Discuss.
```

**Quality filter rules (hard constraints applied before proposing):**

| Rule | Check |
|------|-------|
| Concrete | The observation must cite at least one specific example (file path, timestamp, user quote, or artefact ID). Vague complaints ("it felt confusing") are dropped or requested for specification. |
| Theme-grouped | Multiple observations belonging to the same theme (e.g., "scope-lock ergonomy") are merged into a single ticket. The agent is explicit about which observations were grouped. |
| Deduplicated | Before proposing, the agent runs `gh issue list --repo <upstream> --state open --search "<theme keywords>"` and flags matches. If `gh` is unavailable, the agent proceeds with a "dedup unverified" marker and leaves the decision to the user. |
| Cap | No more than `config.yaml → compound.max_proposed_issues_per_sprint` (default: **3**) tickets proposed per sprint. If more themes qualify, the agent prioritizes by impact (HIGH > MEDIUM > LOW severity from source findings) and consolidates the rest into the local export only. |
| User-validated | Each proposal goes through a per-ticket Gate. No silent creation. |

**Dedup algorithm:**

```
# pseudo
for each proposed_theme:
    keywords = extract_keywords(proposed_theme.title)
    try:
        existing = shell("gh issue list --repo <upstream> --state open --search '{keywords}' --json number,title")
        if existing:
            proposed_theme.dedup_note = f"Potential match: {existing}"
        else:
            proposed_theme.dedup_note = "No open issue matching keywords"
    except ShellError:
        proposed_theme.dedup_note = "dedup unverified (gh unavailable)"
```

**Link with `/gse:integrate` Axe 2:**

Compound prepares the tickets as a draft set (stored transiently in `.gse/compound-tickets-draft.yaml` for handoff). `/gse:integrate` Axe 2 reads this file and executes the user-approved `gh issue create` calls. No change to integrate's skeleton — just the input quality is now higher.

**Upstream repository resolution (Axe 2):** the target repository for `gh issue create` is resolved in order: (1) `config.yaml → github.upstream_repo` if non-empty (user override — private forks, corporate trackers), (2) plugin manifest — `plugin.json → repository` on Claude/Cursor, `opencode.json → gse.repository` on opencode (canonical default shipped with the plugin), (3) if neither resolves, `/gse:compound` Axe 2 hides the ticket-proposal options and only offers the local export. The final Gate before `gh issue create` must state explicitly that GitHub issues are public (privacy acknowledgment — cf. P4 consequence visibility).

**Configuration:**

New field in `config.yaml`:

```yaml
compound:
  max_proposed_issues_per_sprint: 3    # Hard cap. Raise only if sprint generates genuinely independent themes.
```

**Skipping behavior:**

- If no observations are collected (rare — typically happens on a very smooth sprint), the Gate is skipped silently and Axe 2 concludes with "No methodology observations worth escalating this sprint."
- If the user has opted out of upstream feedback entirely (e.g., `github.enabled: false`), only option 1 (local export) is offered; options 2 and 3 are hidden.

**Failure modes:**

- `plugin.json` has no `repository` field → options 2/3 are disabled; only local export is offered. Inform note displayed.
- `gh` command not installed or not authenticated → options 2/3 can still be proposed, but ticket creation in `/gse:integrate` will fail at runtime. The agent warns the user before proposing.

**Shared State — Design Mechanics (spec §3 `/gse:design` + design template section):**

Prevents the silent-duplication failure mode: a state that is logically single but implemented as N independent instances across components (e.g., a month filter that must be consistent across 3 pages but lives as 3 independent `st.selectbox` widgets — observed in training feedback).

**Artefact location:** a mandatory `## Shared State` section in `docs/sprints/sprint-{NN}/design.md`, between `## Data Model` and `## Technology Choices`. The section is populated during `/gse:design` Step 2.5.

**Row fields:**

| Field | Content |
|-------|---------|
| `Name` | Conceptual state name (`selected_month`, not `SelectedMonthProvider.state`). |
| `Scope` | List of components/pages/modules that read or write the state. |
| `Mechanism` | Framework-appropriate storage + synchronization (session state, URL param, global store, context, event bus, cookie, DB, etc.). |
| `Rationale` | One sentence explaining why the state must be shared (not duplicated). |
| `Traces` | REQ IDs that motivate the sharing. |

**Mandatory disclaimer for empty case:** when no shared state applies (CLI tools, pure libraries, strictly independent components), the section contains the literal sentence *"No shared state identified — components are independent."*. An empty section is not permitted — it would be indistinguishable from an oversight.

**Activation heuristic (in `/gse:design` Step 2.5):** after Step 2 (Component Decomposition), the agent walks through each component pair and asks *"Do they read or write any state that must stay consistent between them?"* If yes → row in the table. If no → move on. At the end, if the table is empty, the disclaimer is written.

**Domain adaptation (P9):**

- Web / mobile projects — typically 1-5 entries (selections, user identity, theme, navigation).
- CLI / library / scientific — often zero, disclaimer line is legitimate.
- API / backend — usually a few (request context, session, connection pool).

**Failure modes:**

- Agent overlooks a shared state piece that should have been formalized → the omission will surface in `/gse:review` (multiple components handling the same logical state independently) or in user testing. The next sprint's design should add the missing entry.
- Agent inflates the list with trivial state (local component state, ephemeral UI state) → the Rationale field acts as a filter: if it's hard to write a one-sentence reason for sharing, the state probably shouldn't be in this table.

**Preview Variants — Design Mechanics (spec §3 `/gse:preview` + Step 1.5 Variant Selection):**

`/gse:preview` officially supports two variants, selected at activity start:

| Variant | When appropriate | Output | Runnable? |
|---------|-----------------|--------|-----------|
| **static description** | All domains, default for API / CLI / library / scientific / data / arch previews | Wireframes, API examples, ASCII diagrams in `docs/sprints/sprint-{NN}/preview.md`. Throwaway. | No — just a description. |
| **scaffold-as-preview** | Web / mobile projects with modern framework (Vite, Next.js, Streamlit, React Native, etc.). Recommended when the scaffold cost is recovered at `/gse:produce`. | Minimal runnable project at the project root (or a sub-directory). Placeholder code marked with `PREVIEW:` comments. The scaffold becomes the starting base for `/gse:produce`. | Yes — `npm run build` / `python -m <tool>` exit 0 is the validation evidence. |

**Variant selection (Step 1.5 Gate):**

```
Question: How should the preview be produced?

1. Static description (lightweight, throwaway, any domain)
2. Scaffold-as-preview (runnable minimal project, becomes PRODUCE base)
3. Discuss
```

Default recommendation based on `config.yaml → project.domain`:

| Domain | Recommended | Rationale |
|--------|-------------|-----------|
| `web` | scaffold | modern JS/TS frameworks have fast scaffolds; cost recovered at PRODUCE |
| `mobile` | scaffold | RN/Flutter scaffolds deliver the component shell; PRODUCE fills the logic |
| `api` | static | API contracts are better shown as request/response examples |
| `cli` | static | CLI design is about command structure + output format — text is sufficient |
| `library` | static | interface design is best shown as signatures + usage examples |
| `scientific`, `data` | static | notebooks/scripts don't need a UI scaffold; mocked data tables suffice |

**Placeholder comment convention (scaffold-as-preview only):**

Code that is known to be placeholder and must be replaced at PRODUCE is marked with `PREVIEW:` comments, idiomatic per language:

| Language family | Syntax | Example |
|-----------------|--------|---------|
| JS, TS, C, C++, Go, Rust, Java, Kotlin, Swift | `//` | `// PREVIEW: mock data — replaced by real store in TASK-005` |
| Python, Ruby, shell, R, YAML | `#` | `# PREVIEW: hardcoded today's date — real parser added in TASK-007` |
| HTML, XML | `<!-- -->` | `<!-- PREVIEW: placeholder text — copy provided by TASK-003 -->` |
| CSS, SCSS | `/* */` | `/* PREVIEW: rough layout — final design in TASK-008 */` |

**Rules for `PREVIEW:` markers:**

- The marker MUST include a descriptor explaining what will replace it (not just `PREVIEW:`).
- Ideally, the descriptor cites the TASK ID that will replace it.
- The agent grep-scans for `PREVIEW:` at PRODUCE start (see below) to remind the user what remains.

**Integration with `/gse:produce`:**

When the current sprint used `scaffold-as-preview` (detectable by the presence of `## Scaffold` or similar section in `preview.md` + `PREVIEW:` comments in the codebase), `/gse:produce` Step 1 (Select Task) includes an **Inform-tier** scan:

```bash
grep -rn "PREVIEW:" --include="*.py" --include="*.ts" --include="*.js" --include="*.html" --include="*.css" [...] .
```

The scan produces a one-shot reminder list of placeholder sites still awaiting replacement. Not a guardrail — just a visibility cue. The user decides when/how to replace them during PRODUCE work.

**Variant scope (which preview types apply):**

Only **UI** and **feature walkthrough** previews are candidates for scaffold-as-preview. The other types (API contracts, architecture diagrams, data models, import comparisons) remain static — they describe concepts that don't benefit from a runnable scaffold.

**Persistence:**

The chosen variant is recorded in the preview artefact's frontmatter:

```yaml
---
...
preview_variant: static | scaffold
scaffold_path: ""  # populated only if variant: scaffold, e.g., "./" or "frontend/"
---
```

**Failure modes:**

- Agent picks `scaffold` for a domain where it's inappropriate (e.g., library) → DEC-NNN documenting the deviation, user can reverse.
- Scaffolder invocation fails (network / proxy / sandbox blocks the package registry) → the **connectivity preflight** detects the failure before running the heavy scaffold command; the agent presents a 4-option Gate (*Retry / Run locally, then resume / Fallback to static / Discuss*). The preflight is an ecosystem-appropriate reachability probe whose exact command is chosen by the coding agent based on the detected ecosystem. Rationale: avoids blind retries in corporate / training / sandboxed environments. See `activities/preview.md` Step 1.5 → option 2.
- Scaffold build fails (post-invocation) → the PREVIEW variant cannot be validated; agent asks the user whether to debug the scaffold (continues PREVIEW) or revert to static.
- User forgets to replace all `PREVIEW:` markers before DELIVER → the DELIVER review flags them via the same grep; explicit DEC- required to ship code with remaining placeholders.

**Checkpoint schema (spec §12.5):**
```yaml
timestamp: 2026-04-11T16:30:00
user: alice
last_task: TASK-038
note: "Working on auth module, 2 tests remain"

status_snapshot:
  current_phase: LC02
  current_sprint: 3
  last_activity: /gse:produce
  last_activity_timestamp: 2026-04-11T16:28:00
  health_score: 7.5

backlog_sprint_snapshot:
  tasks:
    TASK-038:
      status: in-progress
      complexity: 3
      branch: gse/sprint-03/feat/auth

git_state:
  current_branch: gse/sprint-03/feat/auth
  worktrees:
    - path: .worktrees/sprint-03-feat-auth
      branch: gse/sprint-03/feat/auth
      task: TASK-038
      last_commit: abc123
      clean: false
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

### 5.17 Additional Skill Extensions

**P16 pushback — signal tracking:**
Two counters stored at the root level of `status.yaml`:
- `consecutive_acceptances` — primary trigger; reaches the threshold (beginner=3, intermediate=5, expert=8) to activate the pushback checkpoint.
- `pushback_dismissed` — count of "Everything looks good" dismissals; governs the per-sprint suppression rule (suppress further pushback when `pushback_dismissed >= 2`).
These two signals were previously accompanied by four additional booleans (`never_discusses`, `terse_responses`, `never_modifies`, `never_questions`) — retired in v0.52.0 as pure aspiration (no writer ever landed; the primary counter proved sufficient in practice).

**Documentation as first-class artefact:**
When `/gse:produce` handles a TASK with `artefact_type: doc`:
- Auto-generate API docs from code docstrings if available
- Generate in the worktree branch `gse/sprint-NN/docs/<name>`
- Review alongside code artefacts

**Dependency audit:**
When `/gse:tests` runs, if `testing.dependency_audit: true`:
```bash
pip-audit  # or npm audit, depending on detected framework
```
Report findings in health alerts as `⚠ DEPS:` items.

**Framework drift detection:**
At start of `/gse:tests --run` or `/gse:produce`:
- Compare current framework (from package manifest) with `config.yaml → testing.framework`
- If different → Inform: "Framework changed from X to Y. Update config?"

**Coach agent — Design Mechanics (spec P14 + `agents/coach.md`):**

The coach is a dedicated specialized sub-agent responsible for **observing the AI+user collaboration** along 8 axes — pedagogy (P14) plus seven workflow-monitoring axes. Modeled after the other advocates (architect, security-auditor, ux-advocate, devil-advocate): separate agent file, fresh context on invocation, narrow but extensible mandate.

**Why a single unified agent (and not orchestrator-inline nor two separate agents):**
- Keeps the orchestrator lean — no inline pedagogical or workflow-monitoring algorithm
- Fresh context = objective evaluation across axes; the agent holds the full observational picture
- Prevents duplication: both pedagogy and workflow observation read from overlapping signal sources (profile, status history, activity transitions, P16 counters) — a single agent reads once
- Extensible: the `agents/coach.md` file contains a *"Coaching recipes"* section (tagged per axis) that both the user (manual edit) and the agent (auto-update via `/gse:compound` Axe 3) can maintain
- Individual axes toggleable via `config.yaml → coach.axes.<axis>` — users disable what's irrelevant

**The 8 axes:**

| # | Axis | Category | Purpose |
|---|------|----------|---------|
| 1 | Pedagogy | Pedagogy | Explicit `learning_goals` + inferred competency gaps → 5-option P14 preambles, LRN- notes |
| 2 | Profile calibration | Workflow | Drift between declared profile (HUG) and observed behavior → proposes `/gse:hug --update` |
| 3 | Sprint velocity | Workflow | Pace vs complexity budget; stall detection (`sessions_without_progress`) |
| 4 | Workflow health | Workflow | Uncompleted transitions, activity skips, broken flow sequences |
| 5 | Quality trends | Workflow | Trend in test pass-rate, review findings, design debt across recent sprints |
| 6 | Engagement pattern | Workflow | P16 `consecutive_acceptances` near threshold; `pushback_dismissed` abuse |
| 7 | Process deviation | Workflow | Sanctioned activities bypassed (e.g., produce without preview, fix without review) |
| 8 | Sustainability | Workflow | Session length / cadence drift from profile; fatigue signals |

**Invocation contract:**

Invoked by the orchestrator with a `moment` tag. Each axis is activated by specific moments:

| Moment tag                                                                                 | Axes activated                                                                              | Source activity                                  |
|--------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|--------------------------------------------------|
| `activity_start` (cross-cutting — dispatched centrally by orchestrator, not per-activity)  | 1 (pedagogy) — only if `learning_goals` non-empty + cap not exhausted                       | any lifecycle activity (orchestrator-delegated)  |
| `/gse:go` after recovery check                                                             | 2-8 (workflow overview)                                                                     | `/gse:go`                                        |
| `/gse:pause`                                                                               | 2-8 (end-of-session check)                                                                  | `/gse:pause`                                     |
| `/gse:compound` Axe 2 feed                                                                 | 2-8 (feeds methodology capitalization — all 7 workflow axes)                                | `/gse:compound` Axis 2 Step 2.7                  |
| `/gse:compound` Axe 3 feed                                                                 | 1, 2 (pedagogy + profile calibration — feeds competency update + learning_goals evolution)  | `/gse:compound` Axis 3 Step 3                    |
| Sprint promotion (`/gse:plan --strategic`)                                                 | 3, 4, 5, 8 (retrospective cross-sprint analysis)                                            | `/gse:plan --strategic`                          |
| `mid_sprint_stall` (when `sessions_without_progress ≥ 2`)                                  | 3 (sprint velocity), 4 (workflow health)                                                    | `/gse:go` (auto-detected)                        |
| `gate_sequence_end` (after P16 counter transitions)                                        | 6 (engagement pattern)                                                                      | any Gate emitting activity                       |
| `activity_skip_event` (an activity is skipped or bypassed)                                 | 7 (process deviation)                                                                       | orchestrator-driven                              |
| `session_boundary` (end of session, resume, long gap)                                      | 8 (sustainability)                                                                          | `/gse:pause`, `/gse:resume`                      |
| Profile drift threshold reached (signal in `status.yaml → profile_drift_signals{}`)        | 2 (profile_calibration, targeted suggestion)                                                | orchestrator-driven (status.yaml signal)         |
| Inferred pedagogical gap detected (if `proactive_gap_detection: true`)                     | 1 (pedagogy, targeted preamble)                                                             | orchestrator-driven (status.yaml signal)         |

**Inputs passed to the coach:**
- `moment` tag + activity name (when applicable)
- `profile.yaml` (all dimensions)
- `docs/learning/LRN-*` (list + metadata) — pedagogy axis
- `status.yaml` snapshot (health dimensions, P16 counters, `learning_preambles[]`, `detected_gaps[]`, `profile_drift_signals`, `workflow_observations[]`, `activity_history[]`, `sessions_without_progress`)
- `.gse/plan.yaml` (current sprint state, completed/pending activities)
- Relevant fragment of `.gse/backlog.yaml` when velocity/quality axes are active

**Outputs (returned to orchestrator — zero or more blocks):**

```yaml
# Pedagogy axis outputs (axis 1)
- coach: skip | propose
  axis: pedagogy
  # if skip:
  reason: "already covered (LRN-002)" | "previously declined" | "cap reached" | "no overlap" | ...
  # if propose:
  topic: "{precise formulation, 1 sentence}"
  trigger: explicit-goal | inferred-gap | gate-preamble | compound-review
  severity: low | medium | high          # used by the orchestrator to prioritize when multiple proposals compete
  preamble:
    core_concept: "{1-2 sentences}"
    example: "{concrete 3-10 line example}"
    pitfall: "{common mistake + fix hint}"
  suggested_depth: quick | deep

# Workflow axes outputs (axes 2-8)
- coach: advise
  axis: profile_calibration | sprint_velocity | workflow_health | quality_trends | engagement_pattern | process_deviation | sustainability
  severity: low | medium | high          # used by the orchestrator to prioritize advice (HIGH surfaced first)
  observation: "{1-2 sentences of what the coach has noticed}"
  evidence: ["{concrete signal 1}", "{concrete signal 2}"]
  suggestion: "{actionable next step — may cite an existing command like /gse:hug --update}"
```

On `coach: propose` (pedagogy), the orchestrator presents the 5-option P14 Gate. On `coach: advise` (workflow), the orchestrator emits a one-line Inform note — **workflow-axis outputs are always Inform-tier** per spec §P14 — Knowledge Transfer (Coaching), they never block. The `severity` field (`low | medium | high`) prioritizes ordering when multiple blocks compete for attention, but never escalates to a Gate. A `severity: gate` escalation path was considered in earlier design iterations but is not implemented — if a specific future signal justifies blocking, it will require a dedicated spec update. Every invocation respects `coach.max_advice_per_check` (default 3 blocks returned across all workflow axes).

**Persistence model:**

| Field | Location | Axis | Lifecycle |
|-------|----------|------|-----------|
| `learning_preambles[]` | `.gse/status.yaml` | Pedagogy | Per-project, survives pauses/resumes |
| `detected_gaps[]` | `.gse/status.yaml` | Pedagogy (inferred) | Per-project, reviewed at each `/gse:compound` |
| Learning notes | `docs/learning/LRN-*.md` | Pedagogy | Per-project, durable artefacts with traces |
| `profile_drift_signals{}` | `.gse/status.yaml` | Profile calibration | Per-project, persistent — feeds `/gse:hug --update` proposals |
| `workflow_observations[]` | `.gse/status.yaml` | sprint_velocity, workflow_health, quality_trends, engagement_pattern, process_deviation, sustainability | **Persistent** — cross-sprint ledger for trending. Axes like `quality_trends`, `sprint_velocity`, `sustainability` depend on history across ≥ 3 sprints. Individual observations may be summarized (not purged) at `/gse:compound`. |
| Coaching recipes | `gse-one/plugin/agents/coach.md` Recipes section | All axes (tagged `for: pedagogy | workflow | both`) | **Edit destination:** the user-local copy in `.claude/agents/coach.md` / `.cursor/agents/coach.md` (per-project) OR the shipped template (shared defaults) |

**Coaching recipes — dual maintenance:**

1. **User-edit path:** user manually edits the project-local `coach.md` copy to add project-specific observation strategies (e.g., "prefer code examples in TypeScript" for the pedagogy axis, "treat >2h sessions as fatigue signal" for sustainability).
2. **Agent auto-update path:** during `/gse:compound` Axe 3, if the coach observes that a specific presentation or observation strategy worked well (or poorly), it proposes a new recipe or update to the user via Gate. Approved updates are written to the same project-local file. Recipes are tagged `for: pedagogy | workflow | both` so curation remains scoped.

**Anti-spam architecture:**

- Sprint cap (`coach.max_preambles_per_sprint`) — hard budget for pedagogy preambles per sprint
- Per-invocation cap (`coach.max_advice_per_check`) — hard cap on workflow `advise` blocks returned per invocation (default 3)
- Per-topic permanent suppress (pedagogy: `not-interested` response)
- Per-topic activity-scope suppress (pedagogy: `not-now` response)
- LRN deduplication (pedagogy: if LRN exists on the topic, don't re-propose unless user requests refresh)
- Drift-signal debouncing (profile calibration: require N consistent observations before proposing `/gse:hug --update`, to avoid over-reacting to a single off-day)
- Empty-goals skip: pedagogy axis never invoked if `learning_goals` is empty AND `proactive_gap_detection: false`
- Per-axis disable: any axis with `config.yaml → coach.axes.<axis>: false` is never invoked

**Failure modes:**

- Coach sub-agent fails to return → orchestrator proceeds without preamble/advice, logs an Inform note
- `learning_goals` malformed → coach skips pedagogy axis with "invalid profile input" reason; orchestrator surfaces a warning; other axes continue
- Multiple pedagogy topics match → coach picks the most contextually relevant (matching the activity's current work); sprint cap enforced
- Workflow axis has insufficient signal (new project, empty history) → coach returns no block for that axis rather than speculating

**Policy tests — Design Mechanics (spec §6 Policy column):**

Policy tests enforce **structural rules** on the codebase via static analysis. They are a first-class test level in the pyramid (5% baseline, adjustable 10-15% for strict architecture projects), distinct from the Other column which contains dynamic-constraint checks.

**Categories of policy tests:**

| Category | Rule examples |
|----------|---------------|
| Architecture layering | `src/domain/** must not import src/ui/**`; `no circular imports`; `public API lives only in src/api/` |
| License compliance | `no GPL-licensed dependency`; `all deps must have license metadata` |
| Naming conventions | `all public functions start with lowercase`; `test files match pattern test_*.py` |
| File / module constraints | `no file > 500 lines`; `no function > 50 lines`; `no module with > 20 imports` |
| Dependency rules | `no deprecated packages`; `dev deps not imported in src/`; `version pins match policy` |
| Docstring / documentation | `all public functions must have a docstring`; `all public classes must have an example` |

**Tooling per language (suggestions, not prescriptive):**

| Language | Tools |
|----------|-------|
| Python | `pytest-archon` (architecture), `grimp` (import graph), `pip-licenses` (licenses), `ruff` (conventions) |
| TypeScript / JavaScript | `ts-arch` / `dependency-cruiser` (architecture), `license-checker` (licenses), `eslint` with custom rules |
| Java | `ArchUnit` (architecture), `license-maven-plugin` (licenses) |
| Go | `go-arch-lint` (architecture), `go-licenses` |
| Rust | `cargo-deny` (licenses, deps, advisories), custom macros for architecture |
| Language-agnostic | Custom grep / AST scanners in shell or Python as CI scripts |

**Integration in `/gse:tests`:**

At strategy definition time (Step 1 of `/gse:tests --strategy`), the agent scans:

- `docs/sprints/sprint-{NN}/design.md` — specifically the *Architecture Overview*, *Component Diagram*, and *Shared State* sections. If layered architecture is documented (e.g., "domain layer / storage layer / UI layer") → propose a policy test enforcing the layering.
- `docs/sprints/sprint-{NN}/decisions.md` — DEC- entries with architectural rules (e.g., "DEC-005: framework-free domain module") → propose a policy test enforcing the rule.
- `config.yaml → project.domain` — apply the baseline Policy percentage from the pyramid.

Proposals are presented as Inform-tier suggestions with concrete tool recommendations for the project's language. The user accepts, adjusts, or declines. Each accepted policy test gets its own TST-NNN artefact with `level: policy` in its frontmatter.

**Execution characteristics:**

Policy tests must be:
- **Fast** — full run in seconds (static scan, no runtime)
- **Deterministic** — pass/fail is a function of code state, not environment
- **Actionable on failure** — the message names the violating file + the rule + the fix hint

Run at the same points as other test levels (pre-commit hook, CI pipeline, `/gse:tests --run`). Failures block `/gse:produce` / `/gse:deliver` per the existing test-pass-rate guardrails.

**Why a first-class level and not a subset of Other:**

- **Other** contains *dynamic-constraint* checks attached to behavioral tests (e.g., an E2E test that also measures page load time). It is a modifier on behavioral tests.
- **Policy** is *purely structural* — no runtime, no behavior involved. It guards the codebase's shape. Confusing the two leads to under-budgeting and invisible architecture erosion.

Making Policy a first-class pyramid column forces its explicit allocation during strategy planning, which matches observed practice in mature codebases (see learner05 training feedback: *"Policy tests are surprisingly cheap and powerful — a ~60-line AST scan permanently enforces architecture decisions"*).

---

**Complexity budget ranges:**
Use the spec §8.1 range table. Agent selects within range based on context, presents as Inform. One point captures **coupled effort + complexity for the AI + user pair** (spec P10 / §8.1) with an indicative temporal anchor of 1 pt ≈ 1 pair-session hour. For maintenance work (refactoring, tests, docs, renaming, bug-fixing), apply the **Cost Assessment Grid for Maintenance Work** from spec Appendix B: four criteria (fan-out, review burden, rework risk, coupling) → 0 pt / 1 pt / 2-5 pt per item. The pre-v0.34 "zero-cost items" blanket rule is deprecated — agents must size maintenance activities case-by-case.

**Team matching algorithm:**
User detection in priority order:
1. `.gse/current-user` file → use content
2. `GSE_USER` env var → use value
3. `git config user.name` → use value
4. Ask user (Inform)
Match case-insensitive, spaces→hyphens against `.gse/profiles/`.

**Minimum viable project size:**
In lightweight mode detection: add note that for truly one-off tasks, don't use GSE-One.

**Concurrent access:**
- Each team member works in own worktree → no file conflicts during production
- `backlog.yaml` conflicts handled by git merge; agent detects on pull, proposes resolution (Gate)
- `decisions.md` is append-only → no conflicts
- Checkpoints are per-user → no conflicts

### 5.18 `/gse:deploy` — Application Deployment Activity

This section documents the design of the `/gse:deploy` activity (the Hetzner Cloud + Coolify v4 deployment command introduced at the spec level). The activity deploys the current project to a Hetzner Cloud server via Coolify v4, adapting to the user's starting situation (solo with zero infrastructure, partial pre-configured, training on shared server). The detailed phase-by-phase workflow lives in `gse-one/src/activities/deploy.md`; this section captures the design decisions that cross-cut the skill, the tools, and the state schema.

**Abstraction principle for `/gse:deploy` and future infrastructure-touching skills.** GSE-One prefers **concrete, deterministic instructions** over goal-level abstractions. The plugin is self-contained: every shell command, every API call, every UI step is embedded verbatim in the skill or the Python tools. This choice prioritizes:
- **Reproducibility** — critical for training scenarios (20 learners must get identical results) and CI testing
- **Auditability** — consistent with the "Governed by Humans" motto: a reader of `deploy.md` or `deploy.py` can predict exactly what will execute
- **Self-containment** — the plugin functions without runtime dependencies on external MCP servers or LLM-generated guidance
- **Testability** — deterministic inputs/outputs enable future CI validation

The maintenance cost (occasional upstream drift in Coolify API, DNS registrar UIs, hcloud CLI install paths) is absorbed by a documented contribution workflow (README → Deployment → Maintaining upstream compatibility). This is the explicit trade-off: accept bounded maintenance work in exchange for determinism.

**Onboarding orientation (Step -1).** `/gse:deploy` starts with a pre-flight orientation that triggers only for first-time users (detected by absence of `.gse/deploy.json` AND absence of any deploy-related env vars: `HETZNER_API_TOKEN`, `SERVER_IP`, `COOLIFY_URL`, `COOLIFY_API_TOKEN`, `DEPLOY_DOMAIN`, `DEPLOY_USER`). The orientation displays a 4-option menu identifying the user's role: **Solo** (deploying own project to own server), **Instructor** (preparing a shared training server), **Learner** (using an instructor-provided `.env.training`), or **Skip** (experienced user). Based on the answer, the skill gives a role-appropriate briefing (estimated duration, cost, next actions) and persists the role via `deploy.py record-role`. For Learner role, two preconditions are verified (`.env` copied from `.env.training`, `DEPLOY_USER` set) before proceeding. The `--silent` flag bypasses Step -1 entirely (for scripting, CI, or experienced users who don't need orientation). The role persists in `deploy.json → user_role` and can be used by future invocations to adapt communication tone — though v1 only records; no behavioral branching beyond Step -1.

**Subdomain derivation.** `/gse:deploy` derives the public subdomain for a deployed application as follows:

- **Solo mode** (no `DEPLOY_USER` in `.env`): `{project-name}.{DEPLOY_DOMAIN}`
- **Training mode** (`DEPLOY_USER` set): `{DEPLOY_USER}-{project-name}.{DEPLOY_DOMAIN}`

Both `project-name` (derived from the current directory) and `DEPLOY_USER` are sanitized identically: lowercase; any character outside `[a-z0-9-]` replaced with `-`; consecutive hyphens collapsed; leading/trailing hyphens trimmed; truncated to 30 characters per component. If sanitization yields an empty string, the activity aborts with a clear error.

**Rationale.** This pattern serves two goals simultaneously:
1. **Single wildcard DNS suffices.** Only one record (`*.{DEPLOY_DOMAIN}` → server IP) is needed. In training, the instructor does not need to create a wildcard per learner.
2. **Multi-application per learner.** A training participant can deploy multiple distinct projects in the same course (e.g., `alice-blog.training.example.com`, `alice-todo.training.example.com`) without collision, each tracked as a separate entry in `.gse/deploy.json → applications[]`.

The alternative `<project>.<user>.<domain>` pattern was rejected: it requires per-user wildcard records (`*.alice.domain.com`, `*.bob.domain.com`, ...) or an unsupported double-wildcard (`*.*.domain.com`), both incompatible with training mode at scale.

**FQDN length constraint.** The total FQDN must remain ≤ 253 characters and each DNS label ≤ 63 characters (RFC 1035). The sanitization cap of 30 chars per component keeps all valid combinations within these limits.

**State schema (`.gse/deploy.json`).** The infrastructure state file is versioned (`version: "1.0"`). Top-level blocks: server-level phases (`phases_completed`), the operator's `user_role` (solo | instructor | learner | skip — set by Step -1 Orientation via `record-role`), server / Coolify / domain metadata, `cdn { provider, enabled, bot_protection }` (optional Cloudflare metadata set by `record-cdn` during Phase 5 Step 7), and an array `applications[]` — one entry per deployed application.

Each application entry carries the fields needed to manage its lifecycle: identification (`name`, `project_name`, `deploy_user`, `subdomain`, `url`), source (`github_repo`, `branch`), runtime shape (`type`, `port`, `resources.{memory_limit, cpu_limit}`), Coolify handles (`coolify.{project_uuid, environment_uuid, app_uuid}`), and timestamps/status (`created_at`, `last_deploy_at`, `status`). Fields intentionally excluded from v1.0 and deferred to later design increments: `replicas[]` (scaling), `previous_deploy` (rollback snapshot), `env_vars` (per-app secrets).

**Coolify hierarchy mapping.** Coolify organizes resources as Project → Environment → Application. `/gse:deploy` maps this as:
- **Solo mode:** a single shared Coolify project named `gse`, one environment `production`, N applications.
- **Training mode:** one Coolify project per learner named `gse-{DEPLOY_USER}` (e.g. `gse-alice`), one environment `production`, N applications.

This mapping makes training cleanup trivial: deleting the per-user project in Coolify removes all of that user's applications in one operation. The `--destroy` flag leverages this by iterating over all `gse-*` projects before tearing down the server.

**Dockerfile templates.** `/gse:deploy` ships with four specialized Dockerfile templates in `plugin/templates/` and one shared `.dockerignore`. Each template includes `ARG SOURCE_COMMIT=unknown` (Docker cache-bust, cf. `references/hetzner-infrastructure.md` §7) and a `HEALTHCHECK` instruction.

| Template | Base image | Default port | Healthcheck path | Default CMD |
|---|---|:-:|---|---|
| `Dockerfile.streamlit` | `python:3.13-slim` + uv | 8501 | `/_stcore/health` | `streamlit run app.py` |
| `Dockerfile.python`    | `python:3.13-slim` + uv | 8000 | `/` | `python main.py` (edit for framework) |
| `Dockerfile.node`      | `node:20-slim`          | 3000 | `/` | `npm start` |
| `Dockerfile.static`    | `nginx:alpine`          | 80   | `/` | `nginx -g 'daemon off;'` |

The `config.yaml → deploy.app_type` key (`auto | streamlit | python | node | static | custom`) selects the template: `auto` triggers detection based on project files; `custom` bypasses template generation and expects the user to provide their own Dockerfile. The skill's Phase 6 Step 3 documents the detection and selection logic.

**Deploy operator role.** `/gse:deploy` adopts the `deploy-operator` specialized agent (defined in `src/agents/deploy-operator.md`) for the full duration of the activity. This agent encapsulates the safety, idempotence, and communication principles that govern every deployment step: no credentials in chat output or state file, mandatory confirmation before costly or destructive operations, idempotence via `phases_completed` tracking, step-numbered progress display, and the list of anti-patterns (never `--no-verify`, never commit `.env`, never disable UFW to debug, etc.). The skill loads this agent in its Prerequisites section. Invocation scope: only during `/gse:deploy` (not a background agent).

**Execution tools.** `/gse:deploy` delegates complex deterministic operations to two Python tools under `plugin/tools/`:

- `coolify_client.py` — a standard-library HTTP client for Coolify API v1 (projects, environments, applications, deploy triggers). Exposes `CoolifyClient` with typed methods and retries on 5xx errors.
- `deploy.py` — an orchestrator exposing CLI subcommands used by the skill: `init-state`, `state`, `detect`, `subdomain`, `env-{get,set,delete}`, `record-{phase,server,coolify,domain,role,cdn}`, `wait-dns`, `preflight`, `deploy-app`, `app-status`, `destroy`, `training-{init,reap}`. Grouped by purpose: state lifecycle (init-state / state / detect), naming (subdomain), env editing (env-*), phase persistence (record-phase / record-server / record-coolify / record-domain), orientation and CDN metadata (record-role / record-cdn), preflight gates (wait-dns, preflight), app lifecycle (deploy-app / app-status / destroy), and training-mode lifecycle (training-init / training-reap).

**Skill/tool boundary:** the skill narrates the workflow, handles user interaction (prompts, Gate decisions, cost displays), and performs shell-based operations (ssh, apt, hcloud). The tool handles Coolify API calls, state mutation, subdomain sanitization, situation detection, and the end-to-end deploy flow (Phase 6). Each phase 1–5 calls `record-phase` at its end to guarantee idempotence. Phase 6 is consolidated into a single `deploy-app` call.

The tools require only Python 3.9+ standard library (no external dependencies). They are hand-maintained (not regenerated from `src/`) and live permanently in `plugin/tools/`. Their presence is enforced by `python3 gse_generate.py --verify`.

**Note on Coolify API versioning.** `coolify_client.py` is pinned to **Coolify v4, API `v1`** (last verified 2026-04-20). If Coolify introduces a breaking change, the client will fail visibly with an unexpected response shape or `404` on pinned endpoints. Users who hit a version-compatibility issue are encouraged to **submit a PR** at the upstream repository (https://github.com/nicolasguelfi/gensem): the fix is usually a local modification to `coolify_client.py` (new field name, new endpoint, etc.). See the README "Deployment → Coolify compatibility" section for the contribution workflow.

**Preflight (Phase 6 Step 2).** `deploy.py preflight` returns a structured JSON with the detected project type, the default port, the resolved project directory, and a list of typed checks. Universal checks cover git state (repo, commits, remote, working tree cleanliness, `github.com` remote hint) and Dockerfile quality (`ARG SOURCE_COMMIT` cache-bust). Type-specific checks cover entry points (Streamlit / Python / Node), Streamlit Traefik config (`enableCORS=false`, `enableXsrfProtection=false` in `.streamlit/config.toml`), Node `start` script + Next.js build hint, and static `index.html` presence. Each check has `name`, `ok`, `level` (`info | warning | error`), `message`, and `fix_hint`. The overall status rolls up to `errors | warnings | ok` — the skill aborts on errors, Gate-decides on warnings, and proceeds silently on ok. The detected type propagates to Step 3 (Dockerfile template selection) and Step 4 (`deploy-app`), avoiding any re-detection in the skill.

**Training tools.** Two `deploy.py` subcommands support the instructor workflow in training mode:

- **`training-init`** — called by `/gse:deploy --training-init`. Reads the instructor's completed `.env` and emits a redacted `.env.training` file containing only what learners need (`COOLIFY_URL`, `COOLIFY_API_TOKEN`, `DEPLOY_DOMAIN`, a `DEPLOY_USER` placeholder) plus an embedded security warning about token sharing. Instructor-only secrets (`HETZNER_API_TOKEN`, `SERVER_IP`, SSH keys) are never included.
- **`training-reap`** — called by `/gse:deploy --training-reap`. Deletes Coolify projects named `gse-<learner>` (per-learner) or all `gse-*` (end-of-course), via the Coolify API. Requires `--confirm` matching the scope (either the learner name or the literal `all`). Supports `--dry-run`. Synchronizes `.gse/deploy.json → applications[]` by removing entries whose `deploy_user` matches the reaped scope. The `gse` solo project (instructor's own) is never touched.

These tools close the loop on the training-mode design promise: an instructor can prepare, distribute, and clean up a shared training server with three commands (full `/gse:deploy` once, then `--training-init` to distribute, then `--training-reap --all` at course end).

**Destroy semantics.** `/gse:deploy --destroy` is a best-effort, retry-safe operation:

- In `--dry-run` mode, enumerates the applications, Coolify projects, server, and firewall that would be deleted, with an estimated monthly cost saving (from a hardcoded price table in `deploy.py`, kept in sync with `references/hetzner-infrastructure.md`).
- Without `--dry-run`, requires `--confirm <server-name>` that must exactly match the server name recorded in state.
- Attempts deletions in order: Coolify applications → Coolify `gse` / `gse-*` projects → Hetzner server → Hetzner firewall.
- On any error, records it and continues (best-effort). Returns `status: "partial"` with the error list.
- **Critically: the state file is reset ONLY if all deletions succeeded.** On partial failure, state is preserved so the user can retry — this avoids silent data-loss (server still billed but no longer tracked).

The skill orchestrates a three-step ceremony (dry-run impact preview → Gate 1 generic confirmation → Gate 2 server-name retype) and surfaces post-destroy warnings about external resources (DNS records at registrar, Cloudflare zones, Let's Encrypt certs, SSH keys) that the destroy operation does not — and cannot — clean up.

**Testing.** The plugin ships with two levels of validation:

- **Unit tests** (`gse-one/tests/test_deploy.py`, ~44 tests) covering deterministic functions: `sanitize_component`, `build_subdomain`, `_detect_type`, `preflight` aggregation, `.env` parsing, state I/O, cost hints. Uses the `unittest` stdlib module — no external test dependency. Run: `python3 -m unittest discover tests` or integrated via `python3 gse_generate.py --verify` (which runs verify + tests atomically).
- **Manual E2E checklist** (`gse-one/TESTING.md`) covering Coolify / Hetzner / SSH flows that require live infrastructure: solo full flow, partial-skip detection, training mode (instructor + N learners), destroy with dry-run, edge cases (FQDN overflow, Coolify down, DNS timeout).

CI is not yet set up — listed as future work in `TESTING.md`. The test foundation is intentionally minimal to keep the contribution cost low while catching the most impactful regressions (subdomain sanitization, type detection, state schema drift, env file parsing).

### 5.19 `/gse:audit` — Project methodology audit

The audit activity implements spec §15 Methodology Audit. This section details the architecture for contributors.

#### Artefact inventory

| File | Role | Nature |
|------|------|--------|
| `src/activities/audit.md` | Activity workflow (6 Steps) | Source (edited; transformed into `plugin/skills/audit/SKILL.md` + `plugin/commands/gse-audit.md` + opencode variants by `gse_generate.py`) |
| `src/templates/sprint/audit.md` | Report template populated at Step 3 | Source (copied verbatim by `gse_generate.py`) |
| `plugin/tools/project-audit.py` | Deterministic audit engine (direct-edit tool per CLAUDE.md §Tool architecture, `# @gse-tool project-audit <version>` header) | Plugin direct file — NOT regenerated by `gse_generate.py` |
| `src/agents/project-reviewer.md` (Phase 2, deferred) | Semantic sub-agent (Reviewer archetype) invoked at Step 2 | Source (will be added when Phase 2 ships) |

#### Deterministic layer — `project-audit.py`

Design pattern mirrors `plugin/tools/dashboard.py`:
- CLI entry point with argparse (`--json`, `--severity-filter`, `--help`)
- Project root discovery via `.gse/` directory walk
- Minimal YAML parser (2-level nesting, flat dict with dotted keys) — **recopied** from dashboard.py rather than imported (decoupling per CLAUDE.md §Tool architecture — tools are autonomous)
- `@dataclass Finding` for finding serialization
- Check functions return `List[Finding]`
- Exit codes graded by severity (0 / 1 / 2 / 3) for CI integration

Each check is a pure function `check_<name>(id_counter) -> List[Finding]`. The `id_counter` is a mutable single-element list used as a counter box (ensures AUD-NNN allocation is monotonic across checks). IDs are allocation-time, not persistent across audits — stable within a single report, not between reports.

Phase 1 ships 15 checks covering: dashboard-freshness, test-evidence, file-structure, format (REQ H3, RVW brackets, health nested), workflow coherence, git-state, sprint-freeze, intent, backlog-traces, coach-observations, open-questions. See `plugin/tools/project-audit.py` for the canonical list and implementation.

#### Finding JSON schema

```json
{
  "audit_version": "0.1.0",
  "timestamp": "2026-04-22T14:30:00+00:00",
  "project_root": "/path/to/project",
  "phase": "Phase 1 deterministic (checks 1-15)",
  "findings": [
    {
      "id": "AUD-001",
      "severity": "HIGH",
      "category": "dashboard-freshness",
      "title": "...",
      "detail": "...",
      "evidence": "...",
      "recommendation": "...",
      "auto_fixable": true,
      "fix_command": "python3 \"$(cat ~/.gse-one)/tools/dashboard.py\""
    }
  ]
}
```

The activity file (`audit.md`) parses this JSON at Step 1 (deterministic output) and interleaves with Phase 2 semantic findings at Step 2 (when implemented). The template (`src/templates/sprint/audit.md`) formats the consolidated list at Step 3.

#### Integration with existing mechanisms

- **Dashboard (`plugin/tools/dashboard.py`)** — no direct integration in Phase 1. The dashboard reads `.gse/` state files; the audit reads the same state files and checks coherence. Both are independent consumers of the canonical formats (see §3.4 Dashboard parser format contracts). Phase 3 may add an "audit status" card to the dashboard.
- **Coach agent (`src/agents/coach.md`)** — bidirectional touch point. Coach writes to `status.yaml → workflow_observations` (during activities); audit check 14 (`check_coach_observations`) reads this same field to detect "coach enabled but silent" drift. Audit also appends its own entries to `workflow_observations` at Step 5 (`{axis: audit, ...}`). No double-counting because entries are tagged with `axis: audit` vs coach's own axis tags.
- **Dashboard contract (§3.4)** — `project-audit.py` parses the same canonical formats documented there. The audit adds CHECKS on these formats (e.g., "is the REQ format canonical?") that the dashboard doesn't enforce.

#### Phase 2 design sketch — semantic layer

When Phase 2 ships:

1. **New agent file** `src/agents/project-reviewer.md` (archetype: Reviewer — see CLAUDE.md §Agent archetypes). Perspective: `project-methodology`. Checklist covers P9 Adaptive Communication jargon detection, P14 Knowledge Transfer delivery verification, REQ/DESIGN coherence analysis, P16 Root-Cause Discipline application.
2. **Invocation at Step 2 of `/gse:audit`**: the orchestrator spawns a sub-agent with fresh context, passes current sprint artefacts + recent `activity_history` + `workflow_observations` + active profile + last N user messages. The reviewer returns `AUD-NNN` findings interleaved with Step 1 deterministic findings (shared ID counter or separate namespace — decision deferred to Phase 2 sub-proposition).
3. **Report section activation** — the "Semantic findings (Phase 2 — deferred)" section in the template (`src/templates/sprint/audit.md`) is populated instead of shown empty.

#### Phase 3 design sketch — auto-trigger

When Phase 3 ships:

1. **New invariant** `Methodology Audit Auto-Trigger Invariant` added to `src/agents/gse-orchestrator.md` Process Discipline section.
2. **Detection:** hybrid keyword + coach correlation:
   - **Keyword filter (cheap):** pattern match against user messages (`tu n'as pas`, `tu as oublié`, `pourquoi tu`, `en fait tu fais rien`, French+English variants). Similar pattern to the existing Ad-hoc Bug Report Detection (spec §P16).
   - **Coach confirmation (reuse):** coach's `engagement_pattern` axis or `process_deviation` axis must also signal frustration/deviation. Both signals must align to avoid false positives.
3. **Counter in `status.yaml`:** new field `methodology_drift_signals: {keyword_hits: int, coach_alerts: int, last_seen: iso8601}` (schema documented in §5.16 State Schemas after Phase 3 lands).
4. **Threshold:** at ≥ 2 correlated signals within the current session, the orchestrator emits Inform + Gate *"Run audit now / Defer / Discuss"*. Never auto-applies corrections.

#### Pre-release scope

Phase 1 ships the deterministic layer + manual invocation only. Phase 2 (semantic) and Phase 3 (auto-trigger) are deferred; their design sketches above serve as implementation pointers for future sub-propositions. Nothing in the current implementation blocks the phased additions.

---

## 6. Methodology Deployment: Cross-Platform Parity

The GSE-One methodology is loaded as the agent's permanent identity on all three supported platforms (Claude Code, Cursor, opencode) through a per-platform delivery mechanism, ensuring identical behavior regardless of the tool used.

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

### 6.3 opencode: AGENTS.md Embedding

opencode loads the methodology from `AGENTS.md` at the worktree root (or `~/.config/opencode/AGENTS.md` in plugin mode). GSE-One delivers the orchestrator body wrapped between surgical merge markers so the installer can update methodology content without disturbing user content:

```markdown
<!-- GSE-ONE START -->
...orchestrator body (identical to Claude/Cursor)...
<!-- GSE-ONE END -->
```

The installer:
1. Creates `AGENTS.md` if absent
2. If present, replaces only the block between `GSE-ONE START` and `GSE-ONE END` markers
3. Leaves any user content outside the markers untouched

Hooks on opencode are delivered as a **native TypeScript plugin** (`plugins/gse-guardrails.ts`) transpiled from `hooks/hooks.claude.json` at generation time — the same guardrail logic, expressed in opencode's `tool.execute.before/after` hook API.

Specialized agents ship under `opencode/agents/` with `mode: subagent` frontmatter and the `tools:` list translated from string form to opencode's object form. Skills and commands are generated under `opencode/skills/<name>/SKILL.md` and `opencode/commands/gse-<name>.md` respectively.

### 6.4 Generation and Parity

All three platform outputs are generated from the same source: `src/agents/gse-orchestrator.md`. The generator:

1. Extracts the body (everything after the YAML frontmatter `---...---`)
2. Wraps the body with **agent frontmatter** for Claude Code (`name`, `description` fields) → `agents/gse-orchestrator.md`
3. Wraps the same body with **.mdc frontmatter** for Cursor (`description`, `alwaysApply` fields) → `rules/gse-orchestrator.mdc`
4. Embeds the same body between `<!-- GSE-ONE START -->` / `<!-- GSE-ONE END -->` markers for opencode → `opencode/AGENTS.md`
5. Verifies body parity at generation time — if the three generated bodies differ, the generator reports `DIVERGENT!`

This ensures that Claude Code, Cursor, and opencode users experience the exact same methodology, decision logic, and orchestration behavior.

### 6.5 Installer Differentiation

Although the `plugin/` source directory contains `agents/gse-orchestrator.md`, `rules/gse-orchestrator.mdc`, and `opencode/AGENTS.md` side by side, the installer (`install.py`) ensures each platform only receives the appropriate file:

- **Claude Code:** Receives `agents/gse-orchestrator.md` (loaded via `settings.json → "agent"`). The `.mdc` file and the `opencode/` subtree are ignored by Claude.
- **Cursor:** Receives `rules/gse-orchestrator.mdc` (loaded via `alwaysApply: true`). The installer **excludes** `agents/gse-orchestrator.md` from Cursor installations to prevent double-loading the orchestrator.
- **opencode:** Receives `opencode/AGENTS.md` at the worktree root (or `~/.config/opencode/` in plugin mode). The installer merges surgically between `<!-- GSE-ONE START/END -->` markers, leaving any user content outside the markers untouched.

All three platforms still receive the 10 specialized agents (`code-reviewer.md`, `architect.md`, etc.) for sub-agent delegation during REVIEW and other activities. On Claude Code and Cursor they live in `agents/`; on opencode they live in `opencode/agents/` with `mode: subagent` frontmatter.

---

## 7. Hooks Design

GSE-One implements **3 system hooks** (spec P13 — Event-Driven Behaviors) — deterministic, rigid checks where the risk of the AI forgetting is too high. The hook tier assigned to each check (Soft / Hard / Emergency) derives from the **P11 guardrail taxonomy** defined in spec §P11 — Guardrails: Soft warns without blocking, Hard blocks until documented rationale, Emergency halts until explicit risk acknowledgment. All hook commands use cross-platform Python (`python3 -c`). The commands are defined as shared constants in the generator and emitted in platform-specific JSON wrappers.

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

| Aspect | Claude Code | Cursor | opencode |
|--------|------------|--------|----------|
| Delivery mechanism | `hooks/hooks.claude.json` (JSON) | `hooks/hooks.cursor.json` (JSON) | `opencode/plugins/gse-guardrails.ts` (native TS plugin) |
| Event names | PascalCase (`PreToolUse`) | camelCase (`preToolUse`) | camelCase (`tool.execute.before/after`) |
| `type` field | Required (`"type": "command"`) | Omitted (implicit) | N/A (TS function) |
| `version` field | Absent | Required (`"version": 1`) | N/A |
| Hook commands | Identical (cross-platform Python) | Identical (cross-platform Python) | Transpiled to TypeScript at generation |

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

`.gse/plan.yaml` is a **living document** maintained by the orchestrator, not a static artefact. Its authoritative schema is defined in `plugin/templates/plan.yaml`. The activity `plan.md` references this template for initialization; the template is the single source of truth for the YAML structure.

**Creation** — Written by `/gse:plan --strategic` at sprint start. `workflow.expected` is initialized from the project mode:

| Mode | workflow.expected |
|------|-------------------|
| Full | `[collect, assess, plan, reqs, design, preview, tests, produce, review, deliver]` (preview is in baseline per spec §14; moved to `workflow.skipped` at PLAN-time when `project.domain ∉ {web, mobile}`) |
| Lightweight | `[plan, reqs, produce, deliver]` |
| Micro | no `plan.yaml` — orchestrator falls back to file-existence checks |

**Maintenance** — After every activity transition, the orchestrator executes the **Sprint Plan Maintenance** protocol (defined in `gse-orchestrator.md`):
1. Move current activity from `workflow.active` to `workflow.completed` (with `completed_at` + notes).
2. **Post-REVIEW mutation (conditional FIX insertion):** If the activity just completed is `review`: if `review.md` contains at least one finding with severity HIGH or MEDIUM → insert `fix` at the head of `workflow.pending`. If no such finding exists → do not insert `fix`; if `fix` was previously in `workflow.expected`, move it to `workflow.skipped` with `reason: "no review findings"`.
3. Pop the next item from `workflow.pending` → `workflow.active`; record conditional skips in `workflow.skipped` with reason.
4. Evaluate non-blocking coherence: `budget_pressure` (>80% consumed with tasks remaining), `significant_scope_drift` (>50% tasks changed), `velocity_risk` (produce phase only).
5. React by mode: Full → Inform; Lightweight → one-line Inform; Micro → silent.
6. Update `status.yaml` cursor fields (`last_activity`, `last_activity_timestamp`, `current_phase`). Phase transitions are deterministic: LC00→LC01 on first `/gse:hug` or `/gse:go` closure; LC01→LC02 on first LC02 activity closure in the sprint (reqs/design/preview/tests/produce/review/fix/deliver); LC02→LC03 on `/gse:deliver` closure when `plan.yaml.status == completed` (both conditions set by deliver Step 9.2). See `plugin/agents/gse-orchestrator.md` Sprint Plan Maintenance Step 4 for the canonical rule. Activities do not write cursor fields directly (v0.53.0 protocol).

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
| 1 | `src/agents/gse-orchestrator.md` (body) | `plugin/agents/gse-orchestrator.md` + `plugin/rules/gse-orchestrator.mdc` + `plugin/opencode/AGENTS.md` (wrapped in markers) | Body identical across 3 outputs, frontmatter/wrapper differs |
| 2 | `src/activities/*.md` (24) | `plugin/skills/<name>/SKILL.md` + `plugin/commands/gse-<name>.md` + `plugin/opencode/skills/<name>/SKILL.md` + `plugin/opencode/commands/gse-<name>.md` | Shared body; opencode skills inject `name:` frontmatter |
| 3 | `src/agents/*.md` (10 specialized) | `plugin/agents/<name>.md` + `plugin/opencode/agents/<name>.md` (with `mode: subagent`) | Shared body; opencode agents translate `tools:` to object form |
| 4 | `src/templates/*` (29) | `plugin/templates/*` | Shared across platforms via `~/.gse-one` registry |
| 5 | `src/references/*.md` | `plugin/references/*.md` | Shared — consulted by agents at runtime |
| 6 | Constants | `plugin/.claude-plugin/plugin.json` + `plugin/.cursor-plugin/plugin.json` + `plugin/opencode/opencode.json` | Three manifests |
| 7 | Shared shell commands | `plugin/hooks/hooks.claude.json` + `plugin/hooks/hooks.cursor.json` + `plugin/opencode/plugins/gse-guardrails.ts` (transpiled TS) | Same logic, three formats |
| 8 | — | `plugin/settings.json` | Claude-only |

The generator's `--verify` flag asserts (a) `plugin/` structure completeness — every expected skill, agent, manifest, hook file is present per §12; (b) body parity between the three orchestrator outputs (`plugin/agents/`, `plugin/rules/gse-orchestrator.mdc`, `plugin/opencode/AGENTS.md`) — fatal on divergence; (c) presence of critical patterns in `gse-guardrails.ts` (transpiled hooks). In addition, `--verify` runs a *warning-level* external-docs consistency check on hand-maintained prose (`README.md`, `install.py`, `gse-one/README.md`) against the source-of-truth registries (`SPECIALIZED_AGENTS`, `ACTIVITY_NAMES`, `src/templates/`, `src/principles/`). External-docs mismatches are non-blocking by design — the authoritative numeric-drift audit lives in `gse-one/audit.py` (invoked via `/gse-audit` or `python3 gse-one/audit.py --fail-on warning`).

---

## 12. File Inventory

| Category | Shared | Claude-only | Cursor-only | opencode-only | Source |
|----------|--------|-------------|-------------|---------------|--------|
| Skills | 24 | — | — | 24 (regenerated with `name:` injection) | 24 activities |
| Commands | — | — | 24 | 24 | 24 activities (reused) |
| Agents | 11 (incl. orchestrator) | — | — | 10 specialized (excl. orchestrator) | 11 agents |
| Templates | 30 | — | — | — | 30 templates |
| Manifest | — | 1 | 1 | 1 (`opencode.json`) | constants |
| Rules | — | — | 1 (.mdc) | — | from orchestrator |
| Hooks | — | 1 | 1 | 1 (`gse-guardrails.ts`) | shared constants |
| Settings | — | 1 | — | — | — |
| AGENTS.md | — | — | — | 1 (from orchestrator) | from orchestrator |
| **Total** | **63** | **3** | **26** | **59** | **63 sources** |

Grand total: **151 files**. Generator: ~900 lines.

---

## 13. Implementation Priorities

> **Note — §13 is historical (v0.16 – v0.30.x roadmap).** The four phases below document the original Claude+Cursor build roadmap, preserved for historical context. **Numeric counts in the phases below (principle counts, agent counts, phase-item counts) reflect the methodology state at the time of writing and are NOT updated to the current state** — see §11.1 "Generation Steps" for the authoritative generator step table, §12 "File Inventory" for the current file inventory, and spec §2 "Core Principles" for the current 16-principle list (P1-P16). opencode support was added as a separate follow-up effort (v0.31+) covering: generator outputs for `opencode/skills/`, `opencode/commands/`, `opencode/agents/` (with `mode: subagent`), `opencode/AGENTS.md` (marker-wrapped orchestrator), `opencode/opencode.json`, and `opencode/plugins/gse-guardrails.ts` (hooks transpiled from `hooks.claude.json`).

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
15. Add all 10 specialized agents + Cursor orchestrator always-on rule (`.mdc`)
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

| # | Question | Impact | Status | Recommendation / Resolution |
|---|----------|--------|--------|------------------------------|
| 1 | Should GSE-One principles be in `settings.json` agent key or separate skills? | Context efficiency | **RESOLVED** | Principles are embedded in the orchestrator agent body (`agents/gse-orchestrator.md`), which also generates the Cursor `.mdc` rule and the opencode `AGENTS.md` block. `settings.json` contains only the agent reference. |
| 2 | Cursor marketplace or npm or both? | Reach | **OPEN** | Recommended: both. Status: Claude plugin marketplace entry exists (`gse-one/marketplace/.claude-plugin/marketplace.json`). Cursor marketplace submission and npm package publishing both remain TODO. |
| 3 | How to handle `.gse/` version upgrades? | UX | **OPEN** | Recommended: `gse_version` field + migration logic in skills. Status: field declared in `status.yaml` template, writer activated in `/gse:hug` Step 4 (v0.59.0) — reads the active plugin manifest's `version` field; reader activated in `dashboard.py` (v0.59.0) — displays "init with GSE-One v{X.Y.Z}" in the dashboard header. Migration logic (skill-level detection + transforms when `gse_version < current_VERSION`) is not yet implemented — deferred until the first breaking schema change after public release. |
| 4 | How to handle git conflicts during deliver? | User experience | **OPEN** | Recommended: Gate decision with 3 options — resolve manually, use theirs, use ours. Status: `/gse:deliver` Step 3 does a merge but has no documented conflict-resolution Gate. Conflicts currently abort the activity with a raw git error. |
| 5 | Should worktrees be created eagerly (at plan time) or lazily (at produce time)? | Resource usage | **RESOLVED** | **Lazily.** `/gse:plan` Step 6 assigns branch names only; `/gse:produce` creates the worktree at task start. Confirmed in plan.md ("Branches are NOT created yet — only named"). |
| 6 | How deep should git hygiene check go? | Scope | **RESOLVED** | Branch-level checks enforced by `guardrail-enforcer`; dependency vulnerability audit runs at `/gse:go` Step 1.6 — "Dependency vulnerability check" (defined in spec §14.3 Step 1.6 — "Dependency vulnerability check"). |
| 7 | Should `.gse/` itself live on main or on each branch? | State consistency | **RESOLVED** | **Main only.** `.gse/` is a single shared directory at repo root; worktrees inherit it via filesystem (not duplicated per-branch). |
| 8 | How to handle contextual tip frequency? Too many tips = annoying, too few = useless. | User experience | **RESOLVED** | Coach agent enforces `max_preambles_per_sprint: 3` (pedagogy axis) and `max_advice_per_check: 3` (workflow axes). User can disable per axis (`config.yaml → coach.axes.<name>: false`) or the whole subsystem (`coach.enabled: false`). "Track and adapt" via recipes auto-updated at `/gse:compound` Axe 3. |
| 9 | Should external source shallow clones be cached or re-cloned each time? | Performance | **OPEN** | Recommended: cache in `.gse/cache/` with TTL, clean on `/gse:deliver`. Status: `/gse:collect` currently performs a shallow clone into a temp directory (throwaway). No persistent cache implemented. |
| 10 | How to handle state recovery when user manually breaks `.gse/` or deletes branches? | Robustness | **RESOLVED** | Best-effort reconstruction implemented via spec §12.7 Resilience section + `/gse:go` Step 2 recovery check + pause/resume checkpoint handling with `session_paused` and `pause_checkpoint` fields. |
