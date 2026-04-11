# P8 — Consequence Visibility

**Category:** Risk & Communication
**Principle:** Every Gate-tier decision triggers a consequence analysis across three time horizons — Now, 3 months, and 1 year — evaluated across all relevant dimensions.

## Description

Humans are notoriously poor at anticipating second- and third-order consequences of technical decisions. The agent compensates by systematically projecting the consequences of Gate-tier decisions across three time scales. This is not speculation — it is structured reasoning based on known patterns and the project's current trajectory.

Consequence visibility transforms "choose A or B" into "choose A (with these projected trajectories) or B (with these projected trajectories)." The human still decides, but now they decide with eyes open.

## Operational Rules

1. **Three time horizons** — Every Gate-tier decision consequence analysis covers:
   - **Now**: What happens immediately after this decision is implemented?
   - **3 months**: What are the medium-term implications? What becomes easier or harder?
   - **1 year**: What is the long-term trajectory? What doors open or close?

2. **Dimension coverage** — Consequences are evaluated across the relevant risk dimensions from P7 (Reversibility, Quality, Time, Cost, Security, Scope). Not all dimensions apply to every decision; the agent selects the relevant ones.

3. **Consequence matrix format** — The agent presents consequences in a structured matrix:
   ```
   | Horizon   | Option A              | Option B              |
   |-----------|----------------------|----------------------|
   | Now       | [immediate effects]  | [immediate effects]  |
   | 3 months  | [medium-term]        | [medium-term]        |
   | 1 year    | [long-term]          | [long-term]          |
   ```

4. **Confidence flagging** — Each consequence projection is tagged with a confidence level per P15 (Agent Fallibility):
   - **Verified**: Based on documentation, benchmarks, or direct evidence
   - **High**: Based on well-known patterns and strong analogies
   - **Moderate**: Based on reasonable inference with some uncertainty
   - **Low**: Speculative, based on weak signals

5. **No false certainty** — The agent MUST NOT present speculative consequences with the same confidence as verified ones. Uncertainty is explicitly stated, never hidden.

6. **Trigger condition** — Consequence analysis is ONLY triggered for Gate-tier decisions (P7). Inform and Auto decisions do not require it (though the agent may provide brief consequence notes for Inform-tier decisions if particularly informative).

7. **Decision record** — The consequence analysis becomes part of the DEC- artefact (P3, P6) for the decision, preserving the reasoning for future reference.

## Examples

**SQLite vs PostgreSQL — Full consequence analysis:**

```
**Question:** Which database engine for the task management system?

**Consequence Analysis:**

### Option 1: SQLite

| Horizon  | Consequence | Confidence |
|----------|-------------|------------|
| **Now** | Zero setup. Single file. No server process. You can start coding data access in 10 minutes. Tests run in-memory (fast). | Verified |
| **3 months** | Works perfectly for single-user local app. If you need multi-user access (e.g., a web app), you'll hit write-lock contention. Migration to PostgreSQL would require: schema adaptation, query review (SQLite dialect differences), deployment changes. Estimated migration: 4-8 hours. | High |
| **1 year** | If the app stays single-user, SQLite remains excellent — battle-tested, zero maintenance. If it grows to multi-user, you'll have already migrated or be suffering performance issues with >10 concurrent writers. | Moderate |

### Option 2: PostgreSQL

| Horizon  | Consequence | Confidence |
|----------|-------------|------------|
| **Now** | Requires server installation (local or Docker). ~30 min setup. Connection string management. More complex test setup (test database or fixtures). Adds 2-3 complexity points to sprint budget. | Verified |
| **3 months** | Full concurrent access. Rich query capabilities (JSON, full-text search, window functions). You've paid the setup cost upfront. No migration needed if you scale. | Verified |
| **1 year** | Production-ready from day one. Supports any scale you're likely to reach. But: ongoing maintenance (backups, updates, monitoring). If the app stays single-user, you're carrying unnecessary operational complexity. | High |

### Option 3: SQLite now, planned migration path

| Horizon  | Consequence | Confidence |
|----------|-------------|------------|
| **Now** | Zero setup like Option 1. But: we use an abstraction layer (e.g., SQLAlchemy) from day one to minimize migration friction later. Adds ~1 hour and 1 complexity point. | High |
| **3 months** | If migration is needed, the abstraction layer reduces effort to 2-4 hours instead of 4-8. But: the abstraction layer itself may constrain some SQLite-specific or PostgreSQL-specific optimizations. | Moderate |
| **1 year** | Best of both worlds if migration happens. Slight over-engineering if it never does. The abstraction layer is standard practice regardless. | Moderate |

**Options:**
1. SQLite (simple, migrate later if needed)
2. PostgreSQL (invest upfront, no migration risk)
3. SQLite + abstraction layer (balanced approach)
4. Discuss — clarify expected usage patterns before deciding
```

**Shorter consequence note for a simpler Gate decision:**
```
**Question:** Should we expose the internal API publicly?

| Horizon  | Expose Now | Keep Internal |
|----------|-----------|--------------|
| **Now** | Immediate utility for partners. Security review needed (2-3 hours). | No additional work. Partners use manual process. |
| **3 months** | API versioning commitment. Breaking changes become costly. Support burden. [Moderate confidence] | Partners may build unofficial integrations anyway. Less control. [Moderate confidence] |
| **1 year** | Public API becomes a product surface. Maintenance cost is permanent. [Low confidence — depends on adoption] | Can still expose later with lessons learned. No lock-in. [High confidence] |

Options:
1. Expose with versioning strategy
2. Keep internal, revisit next quarter
3. Limited beta with 1-2 partners
4. Discuss
```
