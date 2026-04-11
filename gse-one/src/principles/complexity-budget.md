# P10 — Complexity Budget

**Category:** Risk & Communication
**Principle:** Each sprint has a finite complexity budget; every decision that adds complexity is costed, tracked, and checked against the budget.

## Description

Complexity is the primary enemy of maintainable software. It accumulates invisibly — one dependency here, one abstraction layer there — until the project becomes incomprehensible. GSE-One makes complexity visible and finite by assigning each sprint a complexity budget measured in points.

Every decision that adds complexity has a known cost. The agent tracks consumption against the budget and raises warnings when the budget is at risk. This creates a natural pressure toward simplicity: if a sprint has 15 points and a framework dependency costs 3, the team must consciously choose to spend those points.

## Operational Rules

1. **Complexity cost table** — Standard costs for common complexity-adding decisions:

   | Decision | Cost | Rationale |
   |----------|------|-----------|
   | Utility dependency (e.g., `python-dateutil`) | 1 pt | Small, stable, well-known |
   | Framework dependency (e.g., Flask, FastAPI) | 2-3 pt | Shapes architecture, learning curve |
   | External service integration (e.g., Stripe, AWS S3) | 2-4 pt | Network dependency, auth, error handling |
   | New UI component | 1-2 pt | 1 if standard, 2 if complex/interactive |
   | New security surface | 2-3 pt | Auth, crypto, user input handling |
   | New API endpoint | 1 pt | Surface area increase |
   | Database schema change | 1-2 pt | Migration, backward compatibility |
   | New abstraction layer | 2 pt | Indirection cost, must justify itself |
   | New design pattern introduction | 1-2 pt | Team must understand and maintain |
   | Configuration system (e.g., env vars, config files) | 1 pt | One more thing to manage |
   | Multi-threading / async introduction | 3 pt | Concurrency bugs, reasoning difficulty |
   | Architectural pattern change | 3-5 pt | 3 for local, 5 for system-wide |
   | Custom DSL or metaprogramming | 3-5 pt | High maintenance, hard to debug |
   | New language/framework | 4-6 pt | Build system, tooling, team learning |

2. **Sprint complexity budget** — Default budgets by sprint type:
   - **Foundation sprint** (early project): 15 points — more room for structural decisions
   - **Feature sprint** (mid-project): 12 points — most complexity is already in place
   - **Stabilization sprint** (late project): 8 points — focus on simplification, not addition
   - Budgets are adjustable in the sprint plan (P5) with human approval (P4)

3. **PLAN phase budget check** — During sprint planning, the agent estimates total complexity cost and compares to budget:
   ```
   Sprint 04 complexity estimate:
   - Flask dependency: 3 pts
   - SQLAlchemy ORM: 3 pts
   - 2 API endpoints: 2 pts
   - Config system: 1 pt
   Total: 9/12 pts — within budget, 3 pts reserve
   ```

4. **PRODUCE phase warnings** — During implementation, if a decision would push consumption beyond 80% of budget, the agent warns:
   ```
   Agent: [Complexity Warning] Adding Redis caching (3 pts) would bring
   sprint total to 14/12 pts, exceeding budget by 2 pts.
   Options:
   1. Proceed anyway (accept budget overrun)
   2. Defer Redis to next sprint
   3. Remove a lower-priority complexity item to make room
   4. Discuss
   ```

5. **HEALTH tracking** — The agent maintains a running complexity ledger in `docs/sprints/sprint-NN/complexity.md`:
   ```markdown
   ## Sprint 04 Complexity Ledger
   Budget: 12 points

   | Decision | Cost | Running Total | Approved By |
   |----------|------|---------------|-------------|
   | Flask    | 3    | 3/12          | Sprint plan |
   | SQLAlchemy | 3  | 6/12          | Sprint plan |
   | /login endpoint | 1 | 7/12      | Auto        |
   | /register endpoint | 1 | 8/12   | Auto        |
   | pytest-cov | 1  | 9/12          | Inform      |
   ```

6. **Complexity debt** — If a sprint exceeds its budget, the overrun is recorded as complexity debt. The next sprint's budget is reduced by the overrun amount unless the team explicitly decides to absorb it.

7. **Simplification credit** — Removing complexity earns negative points. Removing an unused dependency (-1 pt), eliminating a dead abstraction layer (-2 pt), or consolidating two config systems into one (-1 pt) frees budget. The agent actively looks for simplification opportunities.

8. **Zero-cost items** — The following do NOT consume complexity budget:
   - Renaming, reformatting, documentation
   - Bug fixes that don't change architecture
   - Tests (testing reduces risk, not adds complexity)
   - Removing code/dependencies

## Examples

**Budget overrun scenario:**
```
Agent: Sprint 05 complexity budget is 12 points.
Current consumption: 10/12 points.

You're asking me to add WebSocket support for real-time notifications.
Estimated cost: 3-4 points (new protocol, connection management, error handling).

This would put us at 13-14/12 points.

Options:
1. Add WebSocket support, accept 1-2 point overrun (next sprint budget reduced)
2. Use polling instead (1 point — simpler, slight delay)
3. Defer real-time to Sprint 06 (no cost now)
4. Discuss — evaluate whether real-time is a requirement or a nice-to-have
```

**Simplification credit:**
```
Agent: [Simplification] Removed `moment.js` dependency — replaced with
native Date methods for our 2 use cases. Complexity credit: -1 point.
Sprint budget: 7/12 -> 6/12. Nice.
```
