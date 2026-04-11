# P13 — Hooks

**Category:** Infrastructure
**Principle:** Event-driven behaviors automate recurring project hygiene tasks — auto-commit on pause, guardrail enforcement on push, frontmatter validation, and health warnings.

## Description

Hooks are automatic behaviors triggered by project events. They remove the cognitive burden of remembering routine tasks — the system handles them. Hooks are the operational glue that keeps principles P1-P12 working in practice without requiring constant manual attention.

Hooks are not optional conveniences; they are the enforcement mechanism for the project's discipline. A principle without enforcement is a suggestion. Hooks turn principles into practice.

## Operational Rules

1. **Hook types and triggers:**

   | Hook | Trigger Event | Action | Principle Enforced |
   |------|--------------|--------|-------------------|
   | **Auto-commit on pause** | User pauses work or session ends | Create checkpoint commit with WIP status | P1 (incremental), P12 (version control) |
   | **Guardrail on push** | `git push` command | Validate branch naming, check for secrets, verify merge checklist | P11 (guardrails), P12 (version control) |
   | **Frontmatter validation** | File save / pre-commit | Verify YAML frontmatter completeness (id, type, sprint, status) | P3 (artefacts), P6 (traceability) |
   | **Health warning on commit** | `git commit` command | Check complexity budget, trace link consistency, orphan files | P10 (complexity), P6 (traceability) |
   | **Sprint boundary** | Sprint start/end | Generate sprint review template, archive sprint artefacts | P1 (iterative), P5 (planning) |
   | **Dependency addition** | New package added | Log complexity cost, check budget, update ledger | P10 (complexity budget) |
   | **Risk escalation** | High-risk condition detected | Interrupt current flow, trigger Gate interaction | P7 (risk classification) |

2. **Auto-commit on pause:**
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

3. **Guardrail on push:**
   - Trigger: Any `git push` command
   - Checks performed:
     - Branch name follows convention `gse/sprint-NN/type/description`
     - No `.env`, `.secrets`, `credentials.*`, or API key patterns in staged files
     - If pushing to `main`: Emergency guardrail (P11)
     - If force push: Emergency guardrail (P11)
   - On violation: Push is blocked, violation explained, remediation suggested

4. **Frontmatter validation:**
   - Trigger: Saving any `.md` file in `docs/` or creating a new artefact
   - Required fields: `id`, `artefact_type`, `title`, `sprint`, `status`, `created`, `author`
   - On missing field: Soft guardrail warning with auto-fix suggestion
   - The agent can auto-fix missing fields if the information is inferrable (e.g., `sprint` from current sprint, `created` from today's date)

5. **Health warning on commit:**
   - Trigger: Every `git commit`
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

6. **Hook configuration** — Hooks are configured in `config/hooks.yaml`:
   ```yaml
   hooks:
     auto_commit_on_pause:
       enabled: true
       include_untracked: true
     guardrail_on_push:
       enabled: true
       secret_patterns:
         - "*.env"
         - "credentials.*"
         - "**/*secret*"
     frontmatter_validation:
       enabled: true
       auto_fix: true
       required_fields: [id, artefact_type, title, sprint, status]
     health_warning:
       enabled: true
       complexity_warn_threshold: 0.8
       check_trace_links: true
       check_orphan_files: true
   ```

7. **Hook suppression** — Individual hooks can be temporarily suppressed with documented rationale. Suppression is an Inform-tier decision logged in the sprint activity:
   ```
   Agent: [Inform] Suppressing frontmatter validation for imported files
   (IMP-003..IMP-007) — will add frontmatter in TASK-045.
   ```

8. **Hook failures** — If a hook fails (e.g., cannot validate frontmatter due to malformed YAML), the agent reports the failure without blocking the user's work. Hook failures are logged and added to the next sprint's backlog as maintenance tasks.

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

**Health warning on commit:**
```
Agent: [HEALTH] Pre-commit check for TASK-027:

  Complexity:   9/12 pts (75%)
  Trace links:  1 issue — TST-030 references REQ-012 but REQ-012
                doesn't list TST-030 in tested_by
  Orphan files: none
  Test coverage: OK

Fix trace link issue? (1) Auto-fix (2) Skip for now (3) Discuss
```
