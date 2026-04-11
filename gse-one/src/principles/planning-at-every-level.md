# P5 — Planning at Every Level

**Category:** Foundations
**Principle:** Planning is a cross-cutting activity that can be invoked at any abstraction level, not a phase bound to a single point in the lifecycle.

## Description

Traditional waterfall thinking confines planning to the beginning of a project. In GSE-One, planning is pervasive: it happens at the project level, the sprint level, the task level, and even the implementation level. The agent plans before acting, re-plans when conditions change, and makes planning artefacts visible and traceable.

Planning is not overhead — it is the mechanism by which complexity is managed, risk is anticipated, and decisions are made deliberately rather than by accident. A 30-second plan for a simple task is still a plan.

## Operational Rules

1. **Planning levels** — The agent recognizes and operates at these planning levels:

   | Level | Scope | Artefact | Frequency |
   |-------|-------|----------|-----------|
   | **Project** | Overall goals, epics, milestones | `docs/project-plan.md` | Created at project start, revised per sprint |
   | **Sprint** | Sprint goals, selected backlog items | `docs/sprints/sprint-NN/plan.md` | Once per sprint start |
   | **Task** | Implementation approach for a single task | Inline in task artefact or commit message | Before each task |
   | **Micro** | Step-by-step approach within a task | Agent's reasoning (visible on request) | Continuous |

2. **Plan-before-act** — Before starting any task above the Auto risk tier (P7), the agent MUST articulate a plan:
   - **What** will be done
   - **Why** (which backlog item / requirement this serves)
   - **How** (approach, tools, dependencies)
   - **Risks** (what could go wrong, mitigation)
   - **Complexity cost** (P10 budget impact)

3. **Plan visibility** — Plans at the Project and Sprint levels are always artefacts (P3) with full frontmatter. Task-level plans are recorded in the task's artefact or as structured commit messages. Micro-level plans are internal to the agent but can be surfaced on request.

4. **Re-planning triggers** — The agent MUST propose re-planning when:
   - A task takes more than 2x the estimated effort
   - A new dependency is discovered
   - An assumption is invalidated
   - The complexity budget (P10) is at risk of being exceeded
   - The user changes priorities or requirements

5. **Plan acceptance** — Sprint and Project plans are Gate-tier decisions (P4, P7). The human must approve them before execution begins. Task-level plans are Inform-tier: the agent states the plan and proceeds unless the human objects.

6. **No plan survives contact** — Plans are living documents. The agent updates plans as reality unfolds, noting deviations and their causes. A plan that was changed 5 times is more valuable than a plan that was ignored.

7. **Planning debt** — If planning is skipped under time pressure, the agent records a planning debt item in the sprint backlog for the next sprint's retrospective.

## Examples

**Sprint-level planning:**
```
Agent: Sprint 03 Plan

Goal: Implement user authentication module

Tasks:
| ID       | Description                  | Estimate | Risk  |
|----------|------------------------------|----------|-------|
| TASK-025 | Define auth requirements     | 2 pts    | Auto  |
| TASK-026 | Design auth flow             | 3 pts    | Gate  |
| TASK-027 | Implement login endpoint     | 3 pts    | Inform|
| TASK-028 | Write auth integration tests | 2 pts    | Auto  |
| TASK-029 | Security review              | 2 pts    | Gate  |

Total: 12/15 complexity points
Dependencies: TASK-026 blocks TASK-027, TASK-028
Risks: OAuth provider API may change (mitigation: abstract behind interface)

Shall I proceed? (1) Approve plan (2) Adjust scope (3) Discuss
```

**Task-level plan (Inform tier):**
```
Agent: [Plan] TASK-027: Implementing login endpoint.
Approach: Flask route + bcrypt password hashing + JWT token generation.
Files: src/auth/login.py, tests/test_login.py
Complexity: 3 points (1 utility dep + 2 implementation).
Proceeding unless you object.
```

**Micro-level plan (on request):**
```
User: What's your plan for this function?
Agent: I'll implement get_user() in 3 steps:
1. Query the database by email (using existing db module)
2. Validate the result (handle None case)
3. Return a User dataclass (already defined in models.py)
No new dependencies needed.
```
