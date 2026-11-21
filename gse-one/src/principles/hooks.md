# P13 — Hooks

**Category:** Infrastructure
**Principle:** Event-driven behaviors automate recurring project hygiene tasks — auto-commit on pause, guardrail enforcement on push, frontmatter validation, and health warnings.

## Description

Hooks are automatic behaviors triggered by project events. They remove the cognitive burden of remembering routine tasks — the system handles them. Hooks are the operational glue that keeps principles P1-P12 working in practice without requiring constant manual attention.

Hooks are not optional conveniences; they are the enforcement mechanism for the project's discipline. A principle without enforcement is a suggestion. Hooks turn principles into practice.

## Operational Rules

1. **Two categories of automated behaviors** (per spec §P13 — Event-Driven Behaviors):
   - **System hooks** — deterministic, rigid checks executed by the platform before/after tool calls. Guaranteed by code: the agent cannot forget or reinterpret them.
   - **Agent behaviors** — adaptive, context-aware behaviors executed by the orchestrator agent during activities. Enforced by agent discipline, not by code.

   The distinction matters: system hooks are reserved for actions where the risk of the AI forgetting is too high; everything else stays adaptive so it can be calibrated to context and user expertise.

2. **System hooks** (3, generated from `_guardrail_commands()` in `gse_generate.py` — single source of truth, emitted per platform at generation time):

   | Hook | Trigger | Action | Level | Principle Enforced |
   |------|---------|--------|-------|--------------------|
   | **Protect main** | `git commit` on `main` branch (any form, incl. chained `&& git commit` and `git -C . commit`) | Block the commit, send feedback to agent. Sanctioned exceptions: a **record-only commit** (every file under `.gse/`, `docs/sprints/`, `docs/archive/`, `docs/learning/`, or one of `docs/intent.md`, `docs/dashboard.html`, `docs/health-history.yaml`, `.gitignore` — GSE-One's own bookkeeping: profile and intent before the first sprint, delivery bookkeeping after the main merge; the hook checks the staged files, what a `git add` in the same command would stage, and tracked changes for `commit -a`; an empty set stays blocked); `hooks.protect_main: false`, `git.strategy: none` (Micro mode), repository-initialization commit | **Hard** (exit 2) | P12 (version control) |
   | **Block force-push** | any force push: `-f` / `--force` / `--force-with-lease`, flag in any position | Block the push, send feedback to agent | **Emergency** (exit 2) | P12 (version control) |
   | **Review findings on push** | `git push` (any form) | Warn if `review_findings_open > 0` in `status.yaml` | Soft (warn-only, exit 0) | P11 (guardrails), P6 (traceability) |

   Committing or pushing to `main` is a **Hard** guardrail (blocked until documented rationale); **Emergency** is reserved for force-push. Push-time diligence beyond these three checks — branch naming convention (`gse/sprint-NN/type/description`), secret patterns in staged files (`.env`, `credentials.*`, API keys) — is agent discipline under P11/P12, not enforced by a deterministic hook.

3. **Agent behaviors** (7, executed by the orchestrator during activities — adaptive and expertise-calibrated per P9):

   | Behavior | When | Action | Principle Enforced |
   |----------|------|--------|--------------------|
   | **Auto-commit on pause** | `/gse:pause` or session end | Checkpoint commit with WIP status | P1 (incremental), P12 (version control) |
   | **Frontmatter validation** | Artefact save during any activity | Verify YAML frontmatter completeness (type, sprint, status, traces) | P3 (artefacts), P6 (traceability) |
   | **Health check** | Before `/gse:deliver`, during `/gse:review` | Warn if health score < 5, check complexity budget | P10 (complexity), P6 (traceability) |
   | **Sprint boundary** | Sprint start/end | Generate sprint artefact templates, archive previous sprint | P1 (iterative), P5 (planning) |
   | **Dependency tracking** | New package detected during `/gse:produce` | Log complexity cost, check budget, update ledger | P10 (complexity budget) |
   | **Risk escalation** | High-risk condition detected during any activity | Interrupt current flow, trigger Gate interaction | P7 (risk classification) |
   | **Process discipline** | Every transition between lifecycle phases | The next lifecycle step is always the default action; shortcuts are never proposed proactively | P1 (iterative), P2 (agile) |

4. **Auto-commit on pause** (agent behavior, detail):
   - Trigger: User says "pause", "stop", "break", "I'll be back", or session times out
   - Action:
     ```
     git add -A
     git commit -m "WIP: checkpoint before pause

     Sprint: [current sprint]
     Active tasks: [list of in-progress tasks]
     Status: paused, safe to resume
     "
     ```
   - The WIP commit is on the current task branch, never on `main`
   - On resume, the agent reports the checkpoint and current state

5. **Frontmatter validation** (agent behavior, detail):
   - Trigger: Saving any `.md` file in `docs/` or creating a new artefact
   - Required fields: `id`, `artefact_type`, `title`, `sprint`, `status`, `created`, `author`
   - On missing field: Soft guardrail warning with auto-fix suggestion
   - The agent can auto-fix missing fields if the information is inferrable (e.g., `sprint` from current sprint, `created` from today's date)

6. **Health check** (agent behavior, detail):
   - Trigger: Before `/gse:deliver`, during `/gse:review` (per the agent-behaviors table above)
   - Checks:
     - Complexity budget consumption (warn at >80%)
     - Trace link consistency (any broken bidirectional links?)
     - Orphan files (any new files without frontmatter or manifest entry?)
     - Test coverage (any modified source files without corresponding test changes?)
   - Output format:
     ```
     [HEALTH] Commit check:
     - Complexity: 10/12 pts (83%) — approaching budget limit
     - Trace links: consistent
     - Orphan files: 1 found (scripts/deploy.sh)
     - Test coverage: src/auth.py modified but tests/test_auth.py unchanged
     ```

7. **Hook configuration** — System hooks are configurable via `.gse/config.yaml` → `hooks` section (per spec §P13; see the authoritative template in `plugin/templates/config.yaml`):
   ```yaml
   hooks:
     protect_main: true                   # block direct commits to main branch (Hard guardrail)
     block_force_push: true               # block git push --force (Emergency guardrail)
     review_findings_on_push: true        # warn if open review findings before push
   ```
   Agent behaviors are calibrated through their owning activities and the user profile — they have no dedicated toggle file.

8. **Hook suppression** — Individual hooks can be temporarily suppressed with documented rationale. Suppression is an Inform-tier decision logged in the sprint activity:
   ```
   Agent: [Inform] Suppressing frontmatter validation for imported files
   (IMP-003..IMP-007) — will add frontmatter in TASK-045.
   ```

9. **Hook failures** — If a hook fails (e.g., cannot validate frontmatter due to malformed YAML), the agent reports the failure without blocking the user's work. Hook failures are logged and added to the next sprint's backlog as maintenance tasks.

## Examples

**Auto-commit on pause:**
```
User: I need to take a break.
Agent: Creating checkpoint commit on branch gse/sprint-03/feat/user-auth.

Committed: WIP checkpoint
- Modified: src/auth/login.py (in progress)
- Modified: tests/test_login.py (2 tests added)
- Sprint 03, TASK-027 in progress

You can resume anytime. I'll brief you on the current state.
```

**Health check (before deliver):**
```
Agent: [HEALTH] Pre-deliver check for TASK-027:

  Complexity:   9/12 pts (75%)
  Trace links:  1 issue — TST-030 references REQ-012 but REQ-012
                doesn't list TST-030 in tested_by
  Orphan files: none
  Test coverage: OK

Fix trace link issue? (1) Auto-fix (2) Skip for now (3) Discuss
```
