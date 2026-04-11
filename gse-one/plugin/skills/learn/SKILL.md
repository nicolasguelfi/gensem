---
description: "Start or continue a learning session. Triggered when user asks to learn, understand, or be taught. Also triggered proactively at workflow transitions."
---

# GSE-One Learn — Knowledge Transfer

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| `<topic>`          | Start a learning session on the specified topic |
| `--notes`          | List all learning notes |
| `--notes <topic>`  | Show the learning note for a specific topic |
| `--notes --recent` | Show the 5 most recent learning notes |
| `--roadmap`        | Show personalized learning roadmap based on competency map |
| `--quick`          | Force quick mode (5 min) |
| `--deep`           | Force deep mode (15 min) |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/profile.yaml` — user profile (especially `learning_goals`, `it_expertise`, `abstraction_capability`, `preferred_verbosity`)
2. `.gse/competency_map.yaml` — topics already explained (if it exists)
3. `docs/learning/` — existing learning notes (if any)

## Workflow

### Mode Selection

Three learning modes are available:

| Mode | Duration | Depth | When to Use |
|------|----------|-------|-------------|
| **Quick** | ~5 min | Core concept + 1 example | Default for reactive requests, good for filling a specific gap |
| **Deep** | ~15 min | Theory + examples + exercises + connections | When user says "explain in detail", "I want to understand deeply" |
| **Roadmap** | ~2 min | Map of known/unknown topics + suggested path | When user says "what should I learn", "where are my gaps" |

Mode is determined by: explicit flag > user phrasing > default (quick).

### Reactive Workflow (User-Initiated)

Triggered when the user explicitly asks to learn something.

#### Step 1 — Check Existing Note

Search `docs/learning/` for an existing note on the topic:
- If found and recent (created or updated in the current or previous sprint): offer to show it or go deeper
- If found and stale (not updated in > 3 sprints): offer to refresh it
- If not found: proceed to generate

#### Step 2 — Determine Mode

- `--quick` or `--deep` flag → use that mode
- User said "explain", "what is", "quick overview" → quick mode
- User said "teach me", "deep dive", "I want to understand" → deep mode
- User said "what should I learn", "roadmap" → roadmap mode

#### Step 3 — Generate Calibrated Content

Content is calibrated using the user profile:

| Profile Dimension | Content Adaptation |
|------------------|--------------------|
| `it_expertise` | Technical depth, assumed prerequisites |
| `abstraction_capability` | Examples-first (concrete) vs theory-first (abstract) |
| `preferred_verbosity` | Length and detail level |
| `mother_tongue` | Language of explanation |

**Quick mode structure:**
1. One-sentence definition
2. Why it matters (in the context of the current project)
3. One concrete example (from the project if possible)
4. One common pitfall
5. Link to deeper resources

**Deep mode structure:**
1. Concept overview and motivation
2. Core theory (with diagrams if applicable)
3. Worked example from the current project
4. Second example showing edge case
5. Practice exercise
6. Connections to related concepts
7. Common pitfalls and misconceptions
8. Further reading

**Roadmap mode structure:**
1. Competency map visualization (known/partial/unknown)
2. Suggested learning path ordered by relevance to current sprint
3. Estimated time investment per topic
4. Dependencies between topics

#### Step 4 — Save Learning Note

Create a learning note artefact:

```yaml
---
id: LRN-{NNN}
artefact_type: learning
title: "{Topic}"
sprint: {current_sprint}
status: done
created: {date}
author: agent
mode: quick | deep
traces:
  triggered_by: [TASK-{NNN}]  # if learning was triggered during a task
---
```

Save to `docs/learning/LRN-{NNN}-{topic-slug}.md`.

#### Step 5 — Update Competency Map

Update `.gse/competency_map.yaml`:

```yaml
topics:
  git-rebase:
    level: explained  # not-seen | mentioned | explained | practiced
    last_session: 2026-01-15
    mode: deep
    note: LRN-003
  dependency-injection:
    level: mentioned
    last_session: 2026-01-10
    mode: quick
    note: LRN-001
```

### Proactive Workflow (Agent-Initiated)

Triggered automatically at workflow transitions when GSE-One detects a learning opportunity.

#### When to Trigger

- Before a phase that requires knowledge the user may not have
- After a task that introduced a new concept
- When the user makes an error that suggests a knowledge gap

#### Structured Interaction Pattern

Present exactly 5 options — never force learning on the user:

```
Agent: We're about to define API contracts. I notice "REST design patterns"
isn't in your competency map. Would you like to:

1. Quick overview (5 min) — core REST principles for this project
2. Deep dive (15 min) — REST design patterns with exercises
3. Not now — remind me next sprint
4. Not interested — don't propose this topic again
5. Discuss — tell me more before I decide
```

#### Guardrails

- **Max 1 proposal per phase** — Never interrupt the same activity twice
- **Respect user pace** — If user chose "Not now" for a topic, do not re-propose in the same sprint
- **Contextual relevance** — Only propose topics directly relevant to the current or next task

### Contextual Tips (Inline Micro-Explanations)

When `contextual_tips: on` in user profile:

After any action that involves a technical concept:

1. Check `competency_map.yaml` — has this concept been explained?
2. If not explained: insert 2-3 sentences of context after the action output
3. Mark as `mentioned` in competency map (not `explained` — that requires a full session)

Example:
```
Agent: Created branch `gse/sprint-01/feat/user-auth` from `main`.

> Tip: Branch naming follows the convention `gse/sprint-NN/type/name`.
> The `feat/` prefix indicates a feature branch. Other prefixes include
> `fix/` for bug fixes and `refactor/` for restructuring.
```
