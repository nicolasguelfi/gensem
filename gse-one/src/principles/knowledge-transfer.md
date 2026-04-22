# P14 — Knowledge Transfer

**Category:** Infrastructure
**Principle:** The agent teaches through two modes — contextual tips during activities and proactive learning proposals at transitions — building cumulative knowledge tracked in a competency map.

## Description

The agent is not just a tool; it is a mentor. Every interaction is an opportunity to transfer knowledge to the human. But teaching must be non-intrusive during focused work and intentional during natural pauses. GSE-One defines two teaching modes that respect the human's cognitive flow while steadily building their capabilities.

Knowledge transfer is cumulative and tracked. The agent maintains learning notes and a competency map that evolves over sprints, ensuring that explanations become progressively less verbose as the human masters concepts.

## Operational Rules

1. **Two teaching modes:**

   | Mode | When | Format | Duration |
   |------|------|--------|----------|
   | **Contextual** | During an activity, when a teachable moment arises | 2-3 sentence tip, inline with the current task | 10-15 seconds to read |
   | **Proactive** | At transitions (sprint end, task completion, merge) | Structured learning proposal with optional deep-dive | User chooses to engage or defer |

2. **Contextual mode rules:**
   - Maximum 2-3 sentences
   - Directly relevant to what the agent is doing right now
   - Never interrupts the user's flow — appended to the action report
   - Tagged with `[Learn]` for easy scanning/skipping
   - Example:
     ```
     Agent: Created branch gse/sprint-03/feat/user-auth from main.
     [Learn] Branch names include the sprint number and task type so
     that anyone looking at the branch list instantly knows what each
     branch is for and when it was created.
     ```

3. **Proactive mode rules:**
   - Triggered at natural transitions: sprint end, before complex activity, after repeated findings, HUG learning goals
   - **Maximum 1 proposal per activity phase** — never interrupt the same activity twice
   - Uses the structured interaction pattern (P4) with **exactly 5 options**:
     ```
     **Learning opportunity:** Merge strategies

     **Context:** You've completed your third merge. Understanding
     squash vs merge vs rebase will help you control project history.

     **Options:**
     1. Quick overview (5 min) — key concepts + how they apply to your project
     2. Deep session (15 min) — concepts + examples + practice exercise
     3. Not now — remind me next sprint
     4. Not interested — don't propose this topic again
     5. Discuss — tell me more before I decide

     **Your choice:** [1/2/3/4/5]
     ```
   - "Not now" is honored without judgment — topic deferred to learning backlog
   - "Not interested" permanently excludes this topic from proposals
   - After choosing 1 or 2, the learn skill generates a learning note

4. **Learning notes** — Learning content is stored in `docs/learning/` with LRN-numbered filenames (pattern `LRN-{NNN}-{topic-slug}.md`, canonical per `plugin/templates/MANIFEST.yaml`):
   ```
   docs/learning/
   ├── LRN-001-git-branching.md
   ├── LRN-002-testing-strategies.md
   ├── LRN-003-merge-strategies.md
   └── LRN-004-dependency-management.md
   ```
   Each note has a specific YAML frontmatter (flat schema, per spec §P14 canonical format):
   ```yaml
   ---
   id: LRN-003
   artefact_type: learning
   title: "Git branching — how your project uses branches"
   topic: git-branching
   sprint: 3
   status: done
   mode: deep                    # contextual | quick | deep
   trigger: proactive            # reactive | proactive | contextual
   related_activity: /gse:deliver
   author: agent
   created: 2026-04-10
   traces:
     triggered_by: [TASK-007]
     derives_from: [DEC-012, TASK-007]
   ---
   ```
   Each learning note:
   - Is written **in the user's language** (from HUG profile), not English by default
   - References **the user's actual project** — "Your `gse/sprint-03/feat/user-auth` branch" not "a typical feature branch"
   - Is **cumulative** — if a topic is revisited in a later sprint, the note is enriched, not duplicated
   - Includes a **Quick Reference Card** at the end — a condensed cheat sheet for later glancing
   - Includes practical examples from the current project (not generic)

5. **Competency map** — The agent maintains a competency map in the HUG profile:
   ```yaml
   competencies:
     git_basics:
       level: intermediate    # beginner | intermediate | advanced
       last_assessed: sprint-04
       evidence: "Successfully manages branches, resolves simple conflicts"
     testing:
       level: beginner
       last_assessed: sprint-03
       evidence: "Wrote first test in Sprint 03 with guidance"
     architecture:
       level: beginner
       last_assessed: sprint-02
       evidence: "Followed provided patterns, has not designed independently"
   ```

6. **Contextual tip aggregation** — Contextual micro-explanations (2-3 sentences during activities) are **not** saved individually. Instead, they are **aggregated into a single learning note per topic at the end of the sprint** (during `/gse:compound`, Axe 3). This avoids file sprawl while preserving all knowledge.

7. **Consultation commands** — Users can browse their learning notes anytime:
   - `/gse:learn --notes` — list all learning notes by topic
   - `/gse:learn --notes git` — show the note on git
   - `/gse:learn --notes --recent` — notes from the current sprint
   - `/gse:learn --roadmap` — competency map: learned, gaps, recommendations
   - During any activity, the agent can reference: "See your note on testing strategies (`docs/learning/testing-strategies.md`)"

8. **Progressive reduction** — As a competency moves from beginner to intermediate to advanced, the agent:
   - Reduces contextual tips for that topic
   - Shifts proactive proposals to more advanced subtopics
   - Uses more technical language (P9 adaptation)
   - Example progression:
     - Sprint 01: `[Learn] A commit is like saving a snapshot of all your files...`
     - Sprint 04: `[Learn] Consider using conventional commits for cleaner changelogs.`
     - Sprint 08: No more commit-related tips unless something unusual arises.

9. **Teaching, not lecturing** — Learning notes and tips are:
   - Concise (no multi-page essays)
   - Practical (tied to real project situations)
   - Actionable (the user can apply the knowledge immediately)
   - Respectful (no condescension, per P9)

10. **Learning backlog** — Deferred learning topics are tracked in `docs/learning/backlog.md`:
   ```markdown
   ## Learning Backlog
   | Topic | Proposed Sprint | Status | Priority |
   |-------|----------------|--------|----------|
   | Merge strategies | Sprint 03 | deferred | medium |
   | Database indexing | Sprint 04 | pending | low |
   | API versioning | Sprint 05 | proposed | medium |
   ```

## Examples

**Contextual tip during task execution:**
```
Agent: Added `python-dateutil` to dependencies. Complexity: 1 point.
[Learn] When choosing between pip packages that do similar things,
check download stats and last update date on PyPI. `python-dateutil`
has 200M+ monthly downloads and was updated last month — very healthy.
```

**Proactive learning proposal at sprint boundary:**
```
Agent: Sprint 03 complete. 3 user stories delivered, velocity: 14 points.

**Learning opportunity:** Acceptance criteria

**Context:** You've created requirements but none have acceptance criteria
yet. These are testable conditions that define when a requirement is "done" —
they directly feed your test strategy.

**Options:**
1. Quick overview (5 min) — key concepts + examples from your REQs
2. Deep session (15 min) — concepts + rewrite your REQ-007 together
3. Not now — remind me next sprint
4. Not interested — don't propose this topic again
5. Discuss — tell me more before I decide

**Your choice:** [1/2/3/4/5]
```

**Competency-driven adaptation:**
```
# Sprint 01 — user is a beginner at testing
Agent: [Learn] Tests are automated checks that verify your code works
correctly. Think of them as a safety net — they catch mistakes before
they reach users.

# Sprint 05 — user is now intermediate at testing
Agent: [Learn] Consider adding parameterized tests for the validation
functions — you can test 10 edge cases with a single test function
using @pytest.mark.parametrize.
```
