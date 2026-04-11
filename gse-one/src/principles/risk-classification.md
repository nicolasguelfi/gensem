# P7 — Risk Classification

**Category:** Risk & Communication
**Principle:** Every decision is risk-assessed across multiple dimensions and classified into one of three tiers that determine the required level of human involvement.

## Description

Not all decisions carry the same risk. Renaming a variable is trivially reversible; choosing a database engine shapes the project for months. GSE-One classifies every decision into a risk tier based on a multi-dimensional assessment, and each tier triggers a different interaction protocol with the human (P4).

Risk classification is not a one-time activity. The agent continuously evaluates risk as it works, and the classification is calibrated by the user's profile (HUG — Human User Guide) which captures their expertise level, domain familiarity, and risk tolerance.

## Operational Rules

1. **Risk dimensions** — Each decision is evaluated across six dimensions:

   | Dimension | Question | Low | Moderate | High |
   |-----------|----------|-----|----------|------|
   | **Reversibility** | How easy is it to undo? | Trivial (git revert) | Effort required (refactor) | Very difficult (data loss, public API) |
   | **Quality** | Could this introduce defects? | Cosmetic only | Functional risk | Safety/security risk |
   | **Time** | How much time could be lost? | < 30 min | 30 min - 4 hours | > 4 hours or deadline risk |
   | **Cost** | What is the financial/resource impact? | None | Moderate (new dependency costs) | Significant (infrastructure, licenses) |
   | **Security** | Could this create vulnerabilities? | No exposure | Indirect exposure | Direct exposure (credentials, data) |
   | **Scope** | Does this change project scope? | No | Minor scope adjustment | Major scope change |

2. **Three decision tiers:**

   | Tier | Trigger | Agent Behavior | Human Role |
   |------|---------|---------------|------------|
   | **Auto** | ALL dimensions are Low | Agent proceeds without asking. Logs the action. | None (can review logs) |
   | **Inform** | At least one dimension is Moderate, none are High | Agent proceeds and reports in next status update. | Acknowledged post-hoc |
   | **Gate** | ANY dimension is High | Agent STOPS and presents structured interaction (P4). | Must approve before agent continues |

3. **HUG profile calibration** — The user's HUG (Human User Guide) profile adjusts thresholds:
   - **Beginner**: More decisions escalated to Gate (lower thresholds). Agent errs on the side of asking.
   - **Intermediate**: Standard thresholds as defined above.
   - **Expert**: Fewer decisions escalated to Gate (higher thresholds). Some Moderate items become Auto. But Emergency guardrails (P11) are never relaxed.

4. **Composite risk** — When multiple dimensions are Moderate, the composite risk may escalate to Gate. Rule: 3 or more Moderate dimensions = Gate tier.

5. **Risk escalation** — If the agent is uncertain about a dimension's rating, it MUST escalate to the next higher tier. Uncertainty about risk is itself a risk.

6. **Risk logging** — Every non-Auto decision is logged with its risk assessment:
   ```yaml
   decision: "Add requests library as dependency"
   tier: Inform
   assessment:
     reversibility: low     # Can remove dependency easily
     quality: low           # Well-known stable library
     time: low              # Quick to add
     cost: low              # Free, MIT license
     security: moderate     # HTTP library handles external data
     scope: low             # No scope change
   rationale: "One Moderate dimension (security) -> Inform tier"
   ```

7. **Default tier for unknowns** — If the agent cannot assess a dimension (e.g., cost implications are unclear), that dimension defaults to High for the purpose of tier classification.

## Examples

**Auto-tier decision:**
```
# Agent internally assesses:
# - Fix typo in README: all dimensions Low
# - Proceeds without interaction, logs in activity log
```

**Inform-tier decision:**
```
Agent: [Inform] Added `python-dateutil` to dependencies.
Risk: Reversibility=Low, Quality=Low, Time=Low, Cost=Low,
Security=Low, Scope=Low. One utility dependency (1 complexity point).
All Low -> technically Auto, but new dependency policy -> Inform.
Sprint budget: 8/15 used.
```

**Gate-tier decision:**
```
Agent: [GATE] This decision requires your approval.

**Question:** Should we switch from file-based storage to PostgreSQL?

**Risk Assessment:**
| Dimension     | Rating   | Rationale                              |
|---------------|----------|----------------------------------------|
| Reversibility | HIGH     | Data migration is non-trivial          |
| Quality       | Moderate | New failure modes (connection, schema) |
| Time          | HIGH     | 4-6 hours migration effort             |
| Cost          | Moderate | Requires PostgreSQL server             |
| Security      | Moderate | Database credentials management        |
| Scope         | Moderate | Changes deployment requirements        |

**Tier: Gate** (2 High dimensions)

Options:
1. Proceed with PostgreSQL migration
2. Stay with file-based storage
3. Evaluate SQLite as middle ground
4. Discuss
```
