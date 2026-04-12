# GSE-One — Generic Software Engineering One

**Version:** see `VERSION` file  
**Date:** 2026-04-12  
**Status:** Conceptual framework — coding agent architecture, cross-platform parity, aligned hooks  
**Aliases:** `gse`, `gse-one`, `gseone`

> **Audience:** This document is the **technical specification** for GSE-One, intended for implementers and advanced users who want to understand the methodology in detail. If you are a **new user**, you don't need to read this — just type `/gse:go` and the agent will guide you through everything adaptively. A separate "Getting Started" guide will be available for beginners.

---

## Table of Contents

1. [Overview](#1-overview) — Coding agent architecture, platform mapping, GSE-One philosophy, key concepts, agent roles
2. [Core Principles](#2-core-principles) — Foundations (P1-P3, P5-P6) | Risk & Communication (P4, P7–P11) | Infrastructure (P12–P14) | AI Integrity (P15–P16)
3. [Activities (Commands)](#3-activities-commands) — 22 commands across 8 categories
4. [Collect — Artefact Inventory and External Source Discovery](#4-collect)
5. [Preview](#5-preview)
6. [Testing Strategy](#6-testing-strategy) — Test pyramid, environment, evidence, coverage
7. [Project Health Dashboard](#7-project-health-dashboard)
8. [Complexity Budget](#8-complexity-budget)
9. [Guardrails](#9-guardrails)
10. [Version Control Strategy](#10-version-control-strategy)
11. [Decision Journal](#11-decision-journal)
12. [Artefact Storage Conventions](#12-artefact-storage-conventions)
13. [Configuration & Customization](#13-configuration--customization)
14. [Standard Activity Groups (Lifecycle Phases)](#14-standard-activity-groups)
15. [Glossary](#15-glossary)
A. [Activity Summary (Quick Reference)](#appendix-a)
B. [Changelog](#appendix-b)

---

## 1. Overview

### 1.1 Coding Agents and Plugin Architecture

This section defines the foundational concepts of generative AI coding agents. Understanding these concepts is essential because GSE-One is not a standalone application — it is a set of artifacts consumed by a coding agent platform. The terminology used throughout this specification (agent, skill, hook, template) maps to concrete platform mechanisms described below.

Concepts are ordered from most composite to least composite.

#### Coding Agent

A **coding agent** is an autonomous system built on a large language model (LLM) that operates in an iterative reasoning loop to accomplish software engineering tasks:

```
Observe → Reason → Act → Observe → ...
```

At each iteration, the coding agent observes the current state (user prompt, file contents, prior tool outputs, conversation history), reasons about what to do next, and acts by invoking one or more tools. The loop continues until the task is complete or requires human input.

The coding agent's behavior is shaped by two layers of instructions:

- The **system prompt** — a platform-provided, generally non-modifiable set of instructions that defines the agent's core identity, safety constraints, and capabilities. It is the foundation layer, always present and not visible to the user.
- The **context** — the set of skills, rules, conversation history, and tool outputs loaded into the agent's working memory. The context is finite (bounded by the LLM's context window) and dynamically managed: the platform selectively injects artifacts based on inclusion rules and compacts older content when the window fills.

A coding agent can **spawn subagents** — child instances that run their own independent reasoning loops with isolated context. Subagents can execute in parallel, use different LLM models, and return their results to the parent. This enables task decomposition: the parent agent delegates specialized work to subagents while continuing its own reasoning.

#### Agent

An **agent** is a named role that shapes how the coding agent reasons about a specific concern. An agent defines evaluation criteria, vocabulary, priorities, and domain expertise. When loaded into the coding agent's context, the agent acts as a persona — the coding agent adopts that expert's perspective for the duration of the task.

Agents can serve different architectural functions:

- A **default agent** is loaded at session start and remains active throughout. It defines the methodology, principles, and conventions that the coding agent follows at all times. In GSE-One, this role is called the **orchestrator** — it coordinates activities, manages state, and decides which specialized agents to activate. Note: "orchestrator" is a GSE-One convention, not a formal platform concept.
- **Specialized agents** are loaded on demand by the default agent when their expertise is needed. They are injected into the context temporarily to preserve context budget.

#### Skill

A **skill** is a unit of knowledge and instructions that the coding agent can load into its context. A skill has three facets:

- **Content** — what the coding agent should know or do: steps, constraints, inputs, outputs, evaluation criteria, or persistent conventions.
- **Trigger** — how the skill is invoked. A skill can be triggered by a user **command** (typed as `/<name>` or `/<prefix>:<name>` in the prompt), by the agent autonomously (when it determines the skill is relevant), or by file patterns (when specific files are referenced). A single user prompt can trigger multiple skills; they are loaded into the context and processed by the coding agent.
- **Inclusion policy** — when and for how long the content is loaded:

| Inclusion policy | Loaded when | Duration | Typical use |
|-----------------|-------------|----------|-------------|
| **On-demand** | User types a command or agent decides | Duration of the activity | Activity-specific instructions |
| **Always-on** | Session start | Entire session | Methodology principles, naming conventions |
| **Contextual** | File pattern match or agent decision | While relevant | File-type-specific guidelines |

At this level of abstraction, a "rule" (a persistent convention) and a "command" (a user-invoked activity) are both skills — they differ in their trigger and inclusion policy. This distinction matters because coding agent platforms implement these through different mechanisms (see below).

#### Hook

A **hook** is a deterministic, non-AI command that executes outside the LLM reasoning loop. It is triggered by a platform event (before a tool call, after a tool call, at session start, etc.) and communicates via exit codes:

- **Exit 0** — success, the action proceeds
- **Exit 2** — block, the action is cancelled and the reason is sent to the coding agent as feedback

Hooks are reserved for constraints where the non-deterministic nature of AI is unacceptable — the risk of the LLM forgetting or adapting incorrectly is too high. A hook is code, not a prompt: it executes the same way every time.

#### Template

A **template** is a structured artifact skeleton — the expected form of a project deliverable (YAML schema, document outline, configuration defaults). Templates are passive: they are read by skills when creating artifacts. They carry no behavior, trigger, or inclusion policy.

#### Tool

A **tool** is a primitive action that the coding agent can perform on its environment: read a file, run a shell command, edit code, search the web. Tools are provided by the platform, not by the methodology. The coding agent selects which tools to invoke as part of its reasoning loop. Hooks intercept tool execution at the platform level.

#### 1.1.1 Abstract Execution Loop

A user prompt is a **composite input** to the coding agent. It may contain, in any combination: natural language instructions, one or more command triggers (`/gse:plan`, `/gse:review`), references to agents ("ask the security auditor to check this"), and constraints ("don't modify the database schema").

Processing occurs in two phases:

**Phase 1 — Context enrichment (platform, deterministic).** The platform extracts command triggers from the prompt and loads the content of the matching skills into the coding agent's context. If the prompt contains `/gse:plan` and `/gse:produce`, both skill contents are injected. Always-on skills and conditional skills (matched by file patterns or agent decision) are also loaded as applicable. This phase is mechanical — the platform does not reason.

**Phase 2 — Reasoning and execution (LLM, non-deterministic).** The coding agent receives the entire input: the original prompt, the loaded skills, and the pre-existing context (default agent, conversation history, persistent instructions). It reasons about the **totality** of this input and constructs its own execution plan:
- It decides the **order** in which to process the activities
- It decides whether to **decompose** into subtasks
- It decides which **specialized agents** to consult and when
- It decides whether to **delegate to subagents** for parallel execution
- It respects the **constraints** expressed in the prompt

**The coding agent is not a command interpreter.** It does not process commands left-to-right like a shell. It is a reasoning system that interprets the user's composite intent and creates its own execution strategy.

```
User prompt (composite input)
  │
  ├─ Phase 1 (platform, deterministic):
  │    Extract command triggers → Load matching skill(s) into context
  │    Load always-on skills and conditional skills as applicable
  │
  └─ Phase 2 (LLM, reasoning):
       Interpret the whole (prompt + skills + context)
         → Build execution plan
         → Reasoning loop:
              Sequence activities
              Invoke tool(s)
                → Hooks intercept (can block or warn)
              Load specialized agents if needed
              Delegate to subagent(s) if decomposition is useful
              Verify constraints at each step
         → Continue or respond to user
```

#### 1.1.2 Claude Code

**Architecture.** Claude Code is a CLI-based coding agent powered by the Claude LLM. It provides built-in tools (`Bash`, `Read`, `Write`, `Edit`, `Grep`, `Glob`, `Agent` for spawning subagents) and can be extended with MCP tools. The system prompt is platform-defined and not directly modifiable. Additional instructions can be appended via `--append-system-prompt`, but the primary extension mechanism is context injection (agents, skills, project instructions).

**Execution loop.** When a session starts:

1. The platform loads **settings** from multiple scopes (user, project, plugins) and merges them.
2. If a **default agent** is declared in settings (e.g., `{"agent": "gse-orchestrator"}`), its body is loaded as the agent's system prompt for the session.
3. **CLAUDE.md** files (project root, subdirectories, user-level) are loaded into the context as persistent instructions.
4. The user types a prompt that may include one or more commands (e.g., `/gse:plan`).
5. **Phase 1**: For each command that matches a skill trigger, the skill's content is injected into the context.
6. **Phase 2**: The reasoning loop begins. The coding agent reasons about the full input and executes:
   - **Before** each tool call, `PreToolUse` hooks fire. If any hook returns exit 2, the tool call is blocked and the feedback is sent to the coding agent.
   - The tool executes.
   - **After** each tool call, `PostToolUse` hooks fire (informational).
   - The coding agent can spawn **subagents** via the `Agent` tool — each runs in an isolated context, optionally on a different LLM model. Multiple subagents can run in parallel.
7. The loop continues until the task is complete.

```
Session start
  → Load settings (user + project + plugins)
  → Load default agent body (if declared)
  → Load CLAUDE.md files

User prompt (may include /command triggers)
  → Phase 1: Load matching skill(s) into context
  → Phase 2: Reasoning loop:
      Observe → Reason → Build/update execution plan
        → Select tool(s)
          → PreToolUse hooks (can block)
            → Tool executes
          → PostToolUse hooks (can warn)
        → [Optional: spawn subagent(s) with isolated context]
      → Observe results → Continue or respond
```

**Artifact delivery mechanisms.** Skills, agents, hooks, and templates can be delivered through several mechanisms:

| Mechanism | Scope | Provides | Shared via git? |
|-----------|-------|----------|:--------------:|
| **Plugin** (`.claude-plugin/plugin.json`) | All projects where installed | Skills (namespaced: `/prefix:name`), agents, hooks, templates, settings | Yes (via plugin repo) |
| **Project directory** (`.claude/`) | One project | Skills (`/name`), agents, hooks (`settings.json`), rules (`rules/*.md`) | Yes |
| **Project instructions** (`CLAUDE.md`) | One project or subdirectory | Always-on instructions (injected as context) | Yes |
| **Personal settings** (`.claude/settings.local.json`) | One project, one user | Hooks, permissions, local overrides | No (gitignored) |
| **User settings** (`~/.claude/settings.json`) | All projects, one user | Hooks, permissions, global preferences | No (local) |

A plugin and a project directory deliver the same types of artifacts. The plugin adds **namespacing** (prevents skill name conflicts), **versioning** (semantic version in manifest), and **distribution** (installable from a repository or marketplace). The project directory is simpler — suitable for project-specific conventions.

**Inclusion policy mapping:**

| Abstract policy | Claude Code mechanism |
|----------------|----------------------|
| **Always-on** | Default agent body (via `settings.json` → `"agent"`), `.claude/rules/*.md`, `CLAUDE.md` |
| **On-demand** | Skill file (`skills/<name>/SKILL.md`), invoked via `/<name>` or `/<prefix>:<name>` |
| **Contextual** | Specialized agent files (`agents/<name>.md`), loaded by the default agent during reasoning |

#### 1.1.3 Cursor

**Architecture.** Cursor is an IDE-based coding agent (Composer/Agent mode) powered by a configurable LLM. It provides built-in tools (terminal, file editor, codebase search, multi-file editing) and built-in subagents (`Explore`, `Bash`, `Browser`). Custom subagents can be defined in `.cursor/agents/`. Cursor does not have a single system prompt file — persistent instructions are delivered through the rules system (`.mdc` files).

**Execution loop.** When a session starts:

1. The platform scans for **rules**: `.mdc` files with `alwaysApply: true` are loaded immediately. Other rules are indexed by their description and glob patterns for conditional loading.
2. Plugin configurations are loaded (skills, agents, hooks).
3. The user types a prompt that may include one or more commands (e.g., `/gse:plan`).
4. **Phase 1**: If the prompt matches one or more skill triggers, their content is injected into the context. Conditional rules are loaded if relevant files are referenced.
5. **Phase 2**: The reasoning loop begins. The agent can also autonomously load skills based on relevance:
   - `preToolUse` hooks fire before tool calls (can block).
   - The tool executes.
   - `postToolUse` hooks fire after tool calls (can warn).
   - The agent can delegate to **subagents** — up to 8 can run in parallel, each with isolated context and optionally in isolated git worktrees.
6. The loop continues until the task is complete.

```
Session start
  → Load rules (alwaysApply: true)
  → Index conditional rules (by description + globs)
  → Load plugin configurations

User prompt (may include /command triggers)
  → Phase 1: Load matching skill(s) into context
              Load conditional rules if relevant files referenced
  → Phase 2: Reasoning loop:
      Observe → Reason → Build/update execution plan
        → Select tool(s)
          → preToolUse hooks (can block)
            → Tool executes
          → postToolUse hooks (can warn)
        → [Optional: delegate to subagent(s), up to 8 in parallel]
      → Observe results → Continue or respond
```

**Artifact delivery mechanisms:**

| Mechanism | Scope | Provides | Shared via git? |
|-----------|-------|----------|:--------------:|
| **Plugin** (`.cursor-plugin/plugin.json`) | All projects where installed | Skills, agents, rules (.mdc), hooks, MCP servers | Yes (via plugin repo) |
| **Project directory** (`.cursor/`) | One project | Skills (`skills/`), agents (`agents/`), rules (`rules/*.mdc`), hooks (`hooks.json`) | Yes |
| **Project instructions** (`AGENTS.md`) | One project | Always-on instructions (markdown alternative to rules) | Yes |
| **Legacy rules** (`.cursorrules`) | One project | Always-on instructions (single file, community convention) | Yes |
| **User plugins** (`~/.cursor/plugins/`) | All projects, one user | Global plugins | No (local) |

A plugin and a project directory deliver the same types of artifacts. The plugin adds **marketplace distribution** and can bundle **MCP servers**. The project directory is simpler and project-specific.

**Inclusion policy mapping:**

| Abstract policy | Cursor mechanism |
|----------------|-----------------|
| **Always-on** | `.mdc` file with `alwaysApply: true`, `.cursorrules`, `AGENTS.md` |
| **On-demand** | Skill file (`skills/<name>/SKILL.md`), invoked via `/<name>` or by agent decision |
| **Contextual** | `.mdc` file with `globs` patterns (auto-loaded when matching files are referenced), or `alwaysApply: false` (agent reads description and decides) |

#### 1.1.4 GSE-One: Mono-Plugin Architecture

GSE-One delivers its methodology as a **single plugin directory** (`plugin/`) that works on both Claude Code and Cursor. Shared artifacts (skills, agents, templates) are identical across platforms. Platform-specific artifacts coexist in the same directory — each platform loads only the files it recognizes and silently ignores the rest.

| Artifact | Files | Claude Code | Cursor |
|----------|-------|:-----------:|:------:|
| Skills (22) | `skills/<name>/SKILL.md` | Loaded | Loaded |
| Agents (9) | `agents/<name>.md` | Loaded | Loaded |
| Templates (15) | `templates/*` | Loaded | Loaded |
| Always-on skill (methodology) | `agents/gse-orchestrator.md` | Via `settings.json` → `"agent"` | Via `rules/000-gse-methodology.mdc` (identical body) |
| Hooks (3) | `hooks/hooks.claude.json` | Loaded | Ignored |
| Hooks (3) | `hooks/hooks.cursor.json` | Ignored | Loaded |
| Manifest | `.claude-plugin/plugin.json` | Loaded | Ignored |
| Manifest | `.cursor-plugin/plugin.json` | Ignored | Loaded |
| Settings | `settings.json` | Loaded | Ignored |

Note: "orchestrator" is a GSE-One convention. In Claude Code, it is the session's default agent. In Cursor, it is an always-on rule. Neither platform has a formal "orchestrator" concept.

### 1.2 GSE-One Overview

GSE-One (Generic Software Engineering One) is an AI engineering companion that guides users through the full software development lifecycle. It is implemented as a plugin for AI coding agents (Claude Code, Cursor, or any compatible agent-based IDE) and provides 22 commands covering planning, requirements, design, production, quality, delivery, and capitalization.

GSE-One is designed for users of **any expertise level** — from beginners building their first project to experienced engineers managing complex applications. The agent adapts its language, decisions, and level of autonomy to the user's profile, and progressively transfers knowledge so the user grows alongside the project.

The canonical command prefix is **`/gse:`**.

> **Note:** All artefact metadata (YAML frontmatter), git operations, and state management are handled automatically by the GSE-One agent. Users focus on intent and validation — the agent handles the mechanics.

### 1.3 Design Philosophy

GSE-One is built for a fundamental asymmetry: the **user has the intent** but the **agent has the technical depth**. The methodology bridges this gap through seven pillars:

1. **Risk-aware decision making** — Every decision is assessed across multiple dimensions (quality, cost, time, security, scope). Low-risk decisions are automated; high-risk decisions are presented with consequence horizons so users can evaluate trade-offs through concrete impact, not abstract technicality. (P7→P8→P11)

2. **Unified backlog** — All work items live in a single, ordered backlog. Items flow from pool (ideas) to sprint (committed) to delivered, with full traceability. The sprint plan is a filtered view of the backlog, not a separate document. GitHub Issues are synchronized when available. (Section 3.4, 12.3)

3. **Version control isolation** — Every task is developed in its own git worktree, branched from the sprint branch. The `main` branch is always stable. Merges are formal decisions with user validation. The user never needs to learn git commands — the agent handles branching, merging, and cleanup transparently. (P12)

4. **Adaptive knowledge transfer** — The agent acts as a tutor alongside its engineering role. It inserts contextual explanations during activities, proposes learning sessions at natural workflow transitions, and produces persistent learning notes grounded in the user's actual project. As the user learns, the agent progressively steps back. (P14)

5. **External source reuse** — Projects can bootstrap from existing code, whether from the user's other projects or from public repositories. The agent scans, evaluates compatibility, and imports with full provenance traceability. (Section 4)

6. **Methodology self-improvement** — During capitalization (end of sprint), the agent detects patterns where the methodology itself could be improved and proposes feedback to the GSE-One developers via issue creation on the plugin's repository. (COMPOUND Axe 2)

7. **AI integrity safeguards** — The agent is a generative AI with inherent limitations (hallucinations, complaisance, outdated knowledge). GSE-One protects the user from these failures through explicit confidence levels on every recommendation, verification gates for critical assertions, adversarial self-review (devil's advocate), source citation, and active encouragement of user pushback when passive acceptance is detected. (P15, P16)

### 1.4 Key Concepts

| Concept | Summary |
|---------|---------|
| **Sprint** | A complexity-budgeted iteration. All work is organized in sprints. A sprint ends when its complexity budget is consumed or all tasks are delivered — not by calendar. |
| **Backlog** | The single list of all work items (TASK). Unplanned items are in the pool; planned items are in a sprint. |
| **Artefact** | Any project deliverable: code, requirements, design, tests, documentation, learning notes. |
| **Decision tier** | Every decision is classified as Auto (agent decides), Inform (agent decides + explains), or Gate (user must validate). |
| **Guardrail** | Protection against high-consequence actions. Makes risk visible without blocking. |
| **Health score** | A 0–10 composite metric reflecting project quality across 8 dimensions. |
| **Worktree** | An isolated working directory per task — the user and agent can work on multiple tasks in parallel without interference. |
| **Learning note** | A persistent, reusable course note written by the agent in the user's language, grounded in the project context. |
| **Mono-repo** | GSE-One manages one repository at a time. Multi-component projects should use a mono-repo. |
| **Confidence level** | Every agent recommendation carries a confidence tag: Verified, High, Moderate, or Low. |
| **Devil's advocate** | During review, the agent challenges its own productions — hunting hallucinations, unverified claims, and missing alternatives. |

### 1.5 Agent Roles

An agent is a named role that shapes how the coding agent reasons about a specific concern (see the Agent concept defined earlier in this section). GSE-One defines 9 agents — one orchestrator and 8 specialized roles. Each specialized agent is invoked by the orchestrator during the activities that require its expertise:

| Agent | Role | Invoked during |
|-------|------|----------------|
| **gse-orchestrator** | Main identity. Manages lifecycle, state, decisions, and dispatches to specialized agents. | Always active |
| **requirements-analyst** | Ensures requirements are complete, testable, and traceable. | `/gse:reqs`, `/gse:review` |
| **architect** | Evaluates architecture decisions for quality, scalability, maintainability. | `/gse:design`, `/gse:review` |
| **test-strategist** | Ensures test coverage, strategy, and evidence quality. | `/gse:tests`, `/gse:review`, `/gse:produce` |
| **code-reviewer** | Reviews code for quality, security, maintainability. | `/gse:review` |
| **security-auditor** | Identifies security vulnerabilities and risks. | `/gse:design`, `/gse:review` |
| **ux-advocate** | Evaluates user experience and accessibility. | `/gse:preview`, `/gse:review` |
| **guardrail-enforcer** | Monitors and enforces guardrail compliance (P11). Cross-cutting, always active. | All activities |
| **devil-advocate** | Challenges the agent's own productions for AI integrity (P16). | `/gse:review` |

---

## 2. Core Principles

The 16 principles are organized into four categories:

| Category | Principles | Purpose |
|----------|-----------|---------|
| **Foundations** | P1, P2, P3, P5, P6 | What GSE-One believes — the invariant axioms |
| **Risk & Communication** | P4, P7, P8, P9, P10, P11 | How GSE-One interacts with the user and manages risk |
| **Infrastructure** | P12, P13, P14 | What GSE-One manages automatically behind the scenes |
| **AI Integrity** | P15, P16 | How GSE-One protects the user from the agent's own limitations |

**Foundations**

### P1 — Iterative & Incremental Lifecycle
Documents and artefacts correspond to increments. They must be modular at the file system level and easily traceable across iterations. Every artefact version is associated with a sprint.

Operationally, this is ensured by: sprint artefacts in `docs/sprints/sprint-NN/` (Section 12), git branches per sprint and per task (Section 9), and YAML frontmatter with sprint number on every artefact (Section 12.2).

### P2 — Agile Terminology
All terminology is inherited from the agile engineering methods domain (sprints, backlogs, user stories, etc.). See the Glossary (Section 15) for all defined terms.

### P3 — Artefacts Are Everything
Artefacts encompass all project files: code, requirements, design documents, tests, configuration, plans, decisions, learning notes, and any other deliverable. Every artefact is tracked via YAML frontmatter (Section 12.2) and assigned a unique ID (P6).

**Risk & Communication**

### P4 — Human-in-the-Loop by Default
GSE-One promotes human oversight for important or critical aspects of any artefact. The level of human involvement is calibrated by decision tier (see P7). For decisions that require user input, the agent uses the **structured interaction pattern**:

```
**Question:** <the agent's question>

**Context:** <why this decision matters in the current project>

**Options:**
1. <Option A>
   - Pros: ...
   - Cons: ...
   - Consequence horizon: Now → ... | 3 months → ... | 1 year → ...
2. <Option B>
   - Pros: ...
   - Cons: ...
   - Consequence horizon: Now → ... | 3 months → ... | 1 year → ...
3. <Option C> ...
N. Discuss — Open a discussion around this question

**Rule:** Every structured interaction pattern MUST end with a "Discuss" option as the last numbered choice. This ensures the user always has an escape hatch to request more context before deciding.

**Your choice:** [1/2/3/.../N]
```

**No implicit consent:** Silence or lack of response is NOT consent for Gate-tier decisions. If the user does not respond, the agent waits or works on other non-blocked tasks. The agent never assumes approval.

**Escalation when uncertain:** If the agent is uncertain about the risk tier of a decision, it MUST escalate to Gate tier. It is always safe to ask; it is never safe to assume.

### P5 — Planning at Every Level
Planning is a cross-cutting activity, not bound to a single lifecycle phase. It can be invoked at any abstraction level — from strategic sprint scoping down to micro-task ordering within a single activity. Whenever a decision about what to do next, in what order, and with what scope is needed, PLAN is the appropriate activity. See Section 14 (cross-cutting activities) for its position in the lifecycle.

**Four planning levels:**

| Level | Scope | Artefact | Approval tier |
|-------|-------|----------|---------------|
| **Project** | Multi-sprint roadmap, major goals | Project backlog | Gate |
| **Sprint** | What to deliver this sprint, complexity budget | Sprint plan (`docs/sprints/sprint-NN/plan.md`) | Gate |
| **Task** | How to implement a single TASK | Inline in activity (no separate file) | Inform |
| **Micro** | Step ordering within an activity | None (ephemeral) | Auto |

**Re-planning triggers:** The agent proposes re-planning when:
1. A task exceeds 2x its estimated complexity
2. A new dependency is discovered mid-sprint
3. An assumption underlying the plan is invalidated
4. The complexity budget is at risk (>80% consumed with tasks remaining)
5. The user changes priorities

**Planning debt:** If planning is skipped under pressure (e.g., user says "just do it"), the agent records a planning debt item in the sprint backlog. Planning debt is reviewed during the next `/gse:compound` retrospective.

### P6 — Traceability
Every artefact must be traceable to its origin and related artefacts. Requirements trace to tests, tests trace to code, design decisions trace to requirements. Traceability is maintained through lightweight metadata in artefact files (see Section 12.2).

**Artefact ID allocation:** Each artefact receives an ID composed of a type prefix and a sprint-scoped auto-incrementing number:

| Prefix | Type | Example |
|--------|------|---------|
| `REQ-` | Requirement | REQ-001 |
| `DES-` | Design decision | DES-003 |
| `TST-` | Test definition | TST-012 |
| `RVW-` | Review finding | RVW-005 |
| `DEC-` | Decision | DEC-008 |
| `TASK-` | Work item (backlog + sprint tasks — unified) | TASK-014 |
| `SRC-` | External source | SRC-001 |
| `LRN-` | Learning note | LRN-003 |

IDs are unique within the project (not recycled across sprints). TASK is the **unified work item ID** — there is no separate backlog ID. A TASK is either in the pool (unplanned) or assigned to a sprint.

Each TASK carries an `artefact_type` indicating what kind of deliverable it produces:

| artefact_type | Produces |
|---------------|----------|
| `code` | Source code, scripts |
| `requirement` | FR/NFR definitions, user stories |
| `design` | Architecture, interface contracts |
| `test` | Test definitions, test code |
| `doc` | Documentation, learning notes |
| `config` | Configuration, infrastructure |
| `import` | Imported/adapted external source |

**Trace link types:** Every artefact's `traces` field uses typed links to express the nature of each relationship:

| Link type | Meaning | Example |
|-----------|---------|---------|
| `derives_from` | "I come from..." | REQ derives from TASK, DES derives from REQ |
| `implements` | "I realize/validate..." | Code implements DES, test validates REQ |
| `decided_by` | "This choice is justified by..." | DES justified by DEC |
| `related_to` | "Related to..." | Catch-all for informational links |

```yaml
traces:
  derives_from: [REQ-007, REQ-008]
  decided_by: [DEC-003]
```

Only include the link types that apply — omit empty ones for brevity. The agent maintains **bidirectional consistency**: if artefact A says `implements: [REQ-007]`, then REQ-007 is implemented by A.

### P7, P8, P11 — Risk Analysis and Mitigation System

Principles P7, P8 and P11 form a coherent **risk analysis and mitigation chain**. Together they ensure that any action with significant consequences on the project — regardless of the dimension (application quality, cost, development time, security, maintainability) — is analyzed, presented transparently, and formally validated by the user with full traceability.

The chain operates in three stages:

```
P7 (Classify)  →  P8 (Analyze & Present)  →  P11 (Enforce & Trace)
   What kind         What are the              Ensure formal
   of decision?      consequences?             validation & logging
```

### P7 — Risk-Based Decision Classification
Every action the agent takes or proposes involves a decision. Before acting, the agent performs a **risk assessment** that evaluates each decision across multiple dimensions:

| Dimension | Examples |
|-----------|----------|
| **Reversibility** | Can this be undone? At what cost? |
| **Quality impact** | Does this affect code quality, test coverage, architecture? |
| **Time impact** | Does this add delay, create rework, or block other tasks? |
| **Cost impact** | Does this introduce new dependencies, services, or infrastructure costs? |
| **Security impact** | Does this create an attack surface, expose data, or weaken authentication? |
| **Scope impact** | Does this change what the sprint delivers? |

Based on this assessment, the decision is classified into one of three tiers:

| Tier | Risk Level | Agent Behavior |
|------|-----------|----------------|
| **Auto** | Low risk across all dimensions, trivially reversible | Agent decides, logs silently. User can review in decision log anytime. |
| **Inform** | Moderate risk on one or more dimensions, reversible with effort | Agent decides, explains why in one line. User can override. |
| **Gate** | High risk on any dimension, irreversible or costly to reverse | Full risk analysis presented (P8). Agent waits for formal user validation. Traced in decision journal. |

**Composite risk rule:** When 3 or more dimensions are assessed as Moderate, the decision escalates to Gate tier — even if no single dimension is High. Multiple moderate risks compound into a high overall risk.

**Default for unknowns:** If the agent cannot assess a dimension (insufficient information, unfamiliar domain), that dimension defaults to High for the purpose of tier classification. It is always safe to over-protect; it is never safe to assume low risk.

The classification threshold is calibrated by the user profile (HUG). A senior engineer receives more Auto/Inform decisions; a first-time user receives more Gate decisions. The user can also explicitly configure their preferred thresholds and force-gate specific categories (see Section 13).

### P8 — Consequence Visibility (Risk Analysis Presentation)
Every Gate-tier decision triggers a **risk analysis** whose results are presented to the user through the structured interaction pattern (P4). The analysis includes a **consequence horizon** — a projection of each option's impact at three time scales:

- **Now:** immediate effect on the current sprint
- **3 months:** medium-term impact on maintainability, scalability, cost
- **1 year:** long-term implications on architecture, technical debt, team capacity

The consequence horizon is evaluated across all relevant dimensions (quality, cost, time, security, scope). This allows users without technical depth to evaluate trade-offs through their **concrete, temporal impact** rather than through abstract technical complexity.

**Example:**

```
**Option 1:** Use SQLite
  - Quality:  adequate for current needs
  - Cost:     free, zero infrastructure
  - Time:     immediate, no setup
  - Security: file-based, no network exposure
  - Now → works perfectly
  - 3 months → if >100 concurrent users, migration required (~2 sprints of rework)
  - 1 year → hard ceiling on write throughput, becomes a blocker

**Option 2:** Use PostgreSQL
  - Quality:  production-grade, full SQL support
  - Cost:     ~$15/month managed service
  - Time:     2 hours setup
  - Security: network-exposed, requires credential management
  - Now → more setup work
  - 3 months → scales without changes
  - 1 year → still appropriate
```

**Confidence on projections:** Each consequence projection is tagged with a confidence level per P15. A projection based on verified benchmarks is Verified; a projection extrapolated from general knowledge is Moderate. This prevents the user from treating speculative consequences as established facts.

**No false certainty:** The agent MUST NOT present speculative consequence projections with the same tone as verified ones. If a 3-month projection is uncertain, it must say so: "3 months → if >100 concurrent users, migration required (~2 sprints of rework) [Moderate confidence — depends on actual user growth]".

### P9 — Adaptive Communication
All technical concepts are explained using analogies calibrated to the user's domain knowledge and mental model (as captured by HUG). The agent does not simplify — it **translates** into the user's existing conceptual framework.

Examples:
- For a teacher: "A git branch is like a photocopy of your essay — you can scribble on the copy without touching the original"
- For a scientist: "A worktree is like a parallel experiment — isolated conditions, same lab, merge results when proven"
- For a business person: "A branch is like a draft proposal — work on it independently, present it for approval, then merge into the official version"

**Language levels:** Communication uses the user's `language.chat` setting; produced artefacts use `language.artifacts` (default: `en`). Per-type overrides are available (e.g., requirements in French, code in English). See the Language dimension in the HUG profile.

**Domain-specific expertise:** The agent observes expertise signals during activities and silently records per-domain expertise in the user profile (`expertise_domains`). When a domain entry exists, the agent uses it instead of the global `it_expertise` for communication depth and decision tier calibration in that domain. The agent never announces classification changes — it adapts silently.

**Output formatting:** Chat output uses **bold** for decisions and key terms, *italic* for file paths and references, bullet lists over tables (portability), code blocks for commands and YAML. Emoji usage is controlled by the `emoji` HUG dimension (default: on, at most one per message, never inside technical content).

### P10 — Complexity Budget
A sprint that accumulates too many features, dependencies, or architectural changes becomes unmanageable — tests are skipped, reviews are superficial, and defects slip through. Users rarely perceive this risk because each addition feels small in isolation, but complexity compounds.

To prevent this, each sprint has a **complexity budget** — a finite number of points representing the maximum amount of new complexity the sprint can absorb. Every planned task consumes points based on what it introduces (a new dependency costs 1–2 points, an architectural change costs 3–5). The agent tracks the running total and makes it visible throughout the sprint (see Section 8).

**Role in the methodology:**
- During **PLAN**, the agent evaluates whether planned tasks fit within the budget. If the total exceeds the budget, a Hard guardrail triggers and the agent proposes either deferring lower-priority tasks to the next sprint or splitting the sprint into two smaller ones.
- During **PRODUCE**, if ad-hoc additions push the sprint over budget, the agent warns before proceeding.
- During **HEALTH**, the budget consumption ratio is one of the 8 health sub-scores — a sprint at 90% budget is a risk signal.

The budget size is calibrated by project size and team context (via HUG). A solo beginner gets a smaller budget (fewer moving parts to manage); an expert team gets a larger one.

### P11 — Guardrails (Risk Mitigation and Traceability)
Guardrails are the enforcement mechanism of the P7→P8→P11 risk analysis chain. They ensure that high-consequence actions are formally validated by the user and traced in the decision journal. Guardrails do not block — they make cost visible and require proportional acknowledgment. See Section 9 for levels (Soft, Hard, Emergency), calibration by expertise, and git-specific guardrails.

**Infrastructure**

### P12 — Version Control Isolation
Every production task is performed in an isolated git environment. The `main` branch is always stable and deployable. Work is done on feature branches, each in its own git worktree. Merges are planned activities with Gate-tier validation.

**Core rules:**
1. **`main` is sacred** — no direct commits. All changes arrive via reviewed, approved merges.
2. **One branch per task** — each planned task gets its own branch, named predictably.
3. **Worktree isolation** — each branch is checked out in its own directory, so work on multiple tasks doesn't interfere.
4. **Merge is a decision** — every merge is a Gate-tier decision. The way the agent presents the merge options is adapted to the user's expertise (P9): a beginner sees a plain-language choice between "clean summary" vs. "full history"; an expert sees the technical options (squash, merge, rebase) with consequence horizons.
5. **Clean up after merge** — merged branches and worktrees are deleted to prevent sprawl.

See Section 10 for the full branching model.

### P13 — Event-Driven Behaviors (Hooks)
GSE-One uses two categories of automated behaviors: **system hooks** (deterministic, rigid, executed by the platform before/after tool calls) and **agent behaviors** (adaptive, context-aware, executed by the orchestrator agent during activities).

#### System hooks

System hooks are reserved for actions where deterministic enforcement is critical — the risk of the AI forgetting or adapting incorrectly is too high. They are implemented as `PreToolUse`/`PostToolUse` commands in Claude Code and Cursor:

| Hook | Trigger | Action | Level | Principle Enforced |
|------|---------|--------|-------|--------------------|
| **Protect main** | `git commit` on `main` branch | Block the commit, send feedback to agent | Hard (exit 2) | P12 (version control) |
| **Block force-push** | `git push --force` | Block the push, send feedback to agent | Emergency (exit 2) | P12 (version control) |
| **Review findings on push** | `git push` | Warn if `review_findings_open > 0` in `status.yaml` | Informational (exit 0) | P11 (guardrails), P6 (traceability) |

**Hook failure handling:** If a hook command fails (e.g., `status.yaml` not found), the failure is non-blocking — the user's work is not interrupted.

System hooks are configurable via `.gse/config.yaml` → `hooks` section (see Section 13).

#### Agent behaviors

The following behaviors are executed by the orchestrator agent during activities. They are adaptive (calibrated to user expertise) and context-aware (the agent decides when they apply):

| Behavior | When | Action | Principle Enforced |
|----------|------|--------|--------------------|
| **Auto-commit on pause** | `/gse:pause` or session end | Checkpoint commit with WIP status | P1 (incremental), P12 (version control) |
| **Frontmatter validation** | Artefact save during any activity | Verify YAML frontmatter completeness (type, sprint, status, traces) | P3 (artefacts), P6 (traceability) |
| **Health check** | Before `/gse:deliver`, during `/gse:review` | Warn if health score < 5, check complexity budget | P10 (complexity), P6 (traceability) |
| **Sprint boundary** | Sprint start/end | Generate sprint artefact templates, archive previous sprint | P1 (iterative), P5 (planning) |
| **Dependency tracking** | New package detected during `/gse:produce` | Log complexity cost, check budget, update ledger | P10 (complexity budget) |
| **Risk escalation** | High-risk condition detected during any activity | Interrupt current flow, trigger Gate interaction | P7 (risk classification) |

### P14 — Knowledge Transfer (Tutoring)
GSE-One acts as a **tutor** alongside its engineering companion role. Knowledge transfer operates in two complementary modes:

#### Contextual mode (subtle, within activities)
During any activity, the agent detects **learning opportunities** — moments where a concept the user doesn't fully grasp is directly relevant to what they are doing. When this happens, the agent inserts a brief, non-intrusive explanation calibrated to the user's level (P9).

Contextual teaching is:
- **Brief** — 2–3 sentences maximum, never a lecture
- **Relevant** — only triggered when the concept matters for the current task
- **Positioned after the action** — the user sees the result first, then understands why
- **Progressive** — the agent tracks which concepts have been explained and doesn't repeat them
- **Optional** — the user can disable contextual tips via HUG or config

Examples:
- During `/gse:review`, when a security finding is detected: "This is called an SQL injection — it happens when user input is inserted directly into a database query without sanitization. In your project, this matters because..."
- During `/gse:deliver`, at merge time: "You just did a 'squash merge' — it combined your 12 changes into one clean entry. This is useful because if you ever need to undo this feature, it's a single step."
- During `/gse:plan`, when the user adds too many tasks: "In agile practice, a sprint that exceeds its capacity almost always delivers less than a focused one. Here's why..."

#### Proactive mode (agent-initiated learning proposals)
The agent periodically proposes short learning sessions when it detects a **competency gap** that would benefit the project. This happens at natural transition points in the workflow — never in the middle of production.

**Triggers for proactive proposals:**
- **End of a sprint** (during LC03 — Capitalization): "During this sprint, you encountered 3 security-related decisions. Would you like a 5-minute overview of common web security patterns?"
- **Before a complex activity** (during PLAN): "The next task involves designing an API. I noticed you haven't worked with REST conventions before. Want a quick introduction before we start?"
- **After a repeated mistake** (during REVIEW/FIX): "This is the second sprint where test coverage findings come up. Would you like to explore testing strategies so we can prevent these earlier?"
- **HUG-expressed learning goals**: If the user listed learning objectives in their profile, the agent watches for natural moments to address them.

Proactive proposals use the structured interaction pattern (P4):

```
**Learning opportunity:** <topic>

**Context:** <why this matters for your project right now>

**Options:**
1. Yes, quick overview (5 min) — key concepts + how they apply to your project
2. Yes, deeper session (15 min) — concepts + examples + practice exercise
3. Not now — remind me next sprint
4. Not interested — don't propose this topic again
5. Discuss — tell me more before I decide

**Your choice:** [1/2/3/4/5]
```

The agent respects the user's pace — it never proposes more than one learning session per activity phase, and "not now" is always honored without judgment.

#### Learning notes (persistent artefacts)

Every learning session — whether contextual or explicit — produces a **learning note** saved in `docs/learning/`. These notes are the user's personal course material, written in the user's language and at their level, grounded in their actual project context.

**Format:**

```markdown
---
gse:
  type: learning-note
  topic: git-branching
  sprint: 3
  mode: deep                        # contextual | quick | deep
  trigger: proactive                # reactive | proactive | contextual
  related_activity: /gse:deliver
  traces:
    derives_from: [DEC-012, TASK-007]  # artefacts that motivated this lesson
  created: 2026-04-10
---

# Git Branching — How Your Project Uses Branches

## Key Concepts
...

## How This Applies to Your Project
...

## Practice Exercise (if deep session)
...

## Quick Reference Card
...
```

**Key design choices:**
- Notes are written **in the user's language** (from HUG profile), not in English by default
- Notes reference **the user's actual project** — not abstract examples. "Your `gse/sprint-03/feat/user-auth` branch" instead of "a typical feature branch"
- Notes include a **quick reference card** at the end — a condensed cheat sheet the user can glance at later without re-reading the full note
- Contextual micro-explanations (2–3 sentences during activities) are **aggregated** into a single note per topic at the end of the sprint, rather than producing one file per tip
- Notes are **cumulative** — if the user revisits a topic in a later sprint, the existing note is enriched rather than duplicated

**Consultation:**
- `/gse:learn --notes` — list all learning notes by topic
- `/gse:learn --notes git` — show the note on git
- `/gse:learn --notes --recent` — notes from the current sprint
- During any activity, the agent can reference: "See your note on testing strategies (`docs/learning/testing-strategies.md`) for a refresher"

#### Knowledge tracking

The agent maintains a lightweight **competency map** in the HUG profile (`.gse/profile.yaml`) that tracks:
- Concepts explained (contextual mode) — with date, so it doesn't repeat
- Learning sessions completed (proactive mode) — with topic, depth, and note path
- Learning goals expressed by the user — with progress status
- Competency gaps detected — with project relevance
- Notes produced — index of all learning notes with topics

This map is used to calibrate both the contextual tips and the proactive proposals, and to progressively adjust the user's effective expertise level over time. As the user learns, the agent naturally shifts from Gate-tier to Inform-tier decisions, from verbose to concise explanations, and from frequent to rare guardrails — the tutoring works itself out of a job.

#### Progressive expertise by domain

In addition to the global `it_expertise` captured at HUG, the profile includes an `expertise_domains` section (initially empty) that the agent populates by observation during activities. Example after a few sprints:

```yaml
expertise_domains:
  frontend: advanced       # user corrected CSS issues spontaneously
  database: beginner       # user struggled with SQL joins
  security: advanced       # user identified a vulnerability before the agent
```

When a domain entry exists, the agent uses it instead of the global `it_expertise` for communication and decision tier calibration in that domain. This is never asked at HUG — it emerges from use.

**AI Integrity**

### P15 — Agent Fallibility (Self-Awareness)

GSE-One is powered by a generative AI (LLM) that has inherent limitations: it can hallucinate facts, invent non-existent libraries, misunderstand requirements, and produce plausible-sounding but incorrect recommendations. The methodology must **protect the user from the agent's own failures**, not just from the user's mistakes.

#### Confidence levels

Every production, recommendation, or assertion by the agent carries an explicit **confidence level**:

| Level | Meaning | Agent behavior |
|-------|---------|----------------|
| **Verified** | The agent has factually verified the assertion (code executed, test passed, library installed, API confirmed) | Proceeds normally. No caveat. |
| **High confidence** | The agent draws on well-established knowledge but has not verified in the project's specific context | Proceeds. Adds: "Not verified in your specific context." |
| **Moderate confidence** | The agent reconstructs from patterns — possible approximation, outdated knowledge | Signals explicitly: "I believe X, but I recommend verifying Y before proceeding." |
| **Low confidence** | The agent is unsure, reasoning from vague patterns, or the domain is unfamiliar | Alerts: "I am not confident about this recommendation. Here is what I suggest you verify independently: [specific checkpoints]." |

The agent must **never present moderate or low confidence content with the same tone as verified content**. The confidence level must be visible in the output, not hidden.

#### Verification gates

Certain categories of assertion require **proof, not just statement**:

| Assertion type | Required verification |
|---------------|----------------------|
| "This library does X" | `pip install` / `npm install` succeeds; version confirmed; actual API matches claim |
| "This code works" | Tests executed, results shown |
| "This API accepts Y" | Test request or official documentation cited with URL |
| "This pattern is recommended" | Verifiable source cited (official docs, RFC, OWASP, published reference) |
| "There is no vulnerability" | Security scan executed, not just asserted |
| "This is compatible with Z" | Dependency resolution checked, version constraints verified |

When the agent **cannot verify**, it must mark the assertion as **unverified** and the health dashboard counts unverified assertions as a risk signal.

#### Source citation

When the agent teaches (P14) or recommends a practice, it cites its sources when possible:
- "The Repository pattern is described by Martin Fowler (Patterns of Enterprise Application Architecture)..."
- "According to the official FastAPI documentation (fastapi.tiangolo.com/tutorial/security)..."
- "I cannot find an authoritative source for this recommendation — it is based on my general understanding. Please verify independently."

This allows the user to **check independently** and reduces the false authority that fluent AI-generated prose creates.

### P16 — Adversarial Self-Review and User Pushback

The risk analysis chain (P7→P8→P11) assumes the agent is a reliable evaluator. P16 corrects this assumption by adding two counter-measures.

#### Devil's Advocate (agent self-challenge)

During `/gse:review`, the agent activates a **devil's advocate perspective** on its own productions. This is not a quality review — it is an integrity review that specifically targets AI failure modes:

1. **Challenge assumptions** — "The design assumes X. What if X is false? What evidence supports X?"
2. **Hunt hallucinations** — "Does this library/API/pattern actually exist? Verify with a concrete check."
3. **Question complaisance** — "The user validated Y, but is Y truly the best choice? What alternatives were NOT presented?"
4. **Test edge cases** — "This code works for the normal case. What happens with empty input, null values, very large data, malicious input?"
5. **Check temporal validity** — "This recommendation may be based on outdated knowledge. Has the ecosystem changed since the agent's training data?"

The devil's advocate findings are reported as a separate section in the review, tagged `[AI-INTEGRITY]`:

```
RVW-012 [AI-INTEGRITY] [MEDIUM] — Unverified library recommendation
  The agent recommended `fastapi-magic-auth` for authentication.
  Verification: this library does not exist on PyPI.
  Fix: replace with `fastapi-users` (verified, 2.3k stars, actively maintained).
```

#### User Pushback Encouragement

The agent monitors the user's engagement pattern. If it detects signs of **passive acceptance** (the user validates everything without pushback), it triggers a proactive challenge:

**Passive acceptance signals (observable within the conversation):**
- The user chooses the agent's recommended option in N+ consecutive Gate decisions
- The user never selects "Discuss" in any interaction
- The user never asks "why?", "what about...?", or proposes alternatives
- The user responds with single-word confirmations ("ok", "yes", "1") to complex decisions
- The user never modifies a plan, design, or test strategy proposed by the agent

**Agent response (after detecting passive acceptance):**

```
**Critical checkpoint:** You have validated the last N decisions without 
modification. This may be perfectly fine — but I want to make sure I'm not 
leading you in a direction that doesn't serve your project.

Here are the 3 most impactful choices we've made recently:
1. [DEC-012] PostgreSQL over SQLite — are you comfortable with the 
   ongoing cost and setup complexity?
2. [DEC-015] REST architecture — did you consider that your use case 
   (real-time updates) might benefit from WebSockets or GraphQL?
3. [DEC-018] No integration tests this sprint — is this a conscious 
   trade-off or did it slip through?

**Options:**
1. Everything looks good, continue as-is
2. I'd like to revisit one of these decisions
3. I'm feeling overwhelmed — let's slow down and review together
4. Discuss
```

The pushback mechanism is calibrated:
- **Beginner**: triggers after 3 consecutive acceptances (more protective)
- **Intermediate**: triggers after 5 consecutive acceptances
- **Expert**: triggers after 8 consecutive acceptances (less intrusive)
- If the user selects "Everything looks good" twice in a row, the agent respects this and does not trigger again for the rest of the sprint.

---

## 3. Activities (Commands)

> **Terminology:** An activity is a user-facing action invoked via a `/gse:*` command. Each activity is delivered to the coding agent as a skill — a technical artifact with content, trigger, and inclusion policy. See the Coding Agents and Plugin Architecture section of this document for the formal definitions and platform mapping.

### 3.1 Orchestration & Session

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:go` | **Orchestrate** | Detect current project state (including git branch and worktree state), propose the next logical activity group (LC00–LC03), and orchestrate it with validation gates between activities. **`--adopt`**: onboard an existing project (scan, infer sprint state, initialize `.gse/`, offer to annotate existing artefacts). Auto-detected when `.gse/` is absent but the project has existing code. |
| `/gse:status` | **Status** | Show lifecycle status: current sprint, active phase, artefact inventory, pending reviews, health score, **active branches and worktrees** |
| `/gse:health` | **Health** | Display the project health dashboard: coverage, debt, complexity, risks, **git hygiene** (see Section 7) |
| `/gse:pause` | **Pause** | Auto-commit all uncommitted work in active worktrees, save session checkpoint (context, sprint state, pending tasks, review findings, decision log snapshot, **worktree map**) |
| `/gse:resume` | **Resume** | Reload checkpoint, verify worktree integrity, brief the user on where work stopped, propose next actions |
| `/gse:task` | **Ad-hoc Task** | Execute a task outside the standard lifecycle in a dedicated branch/worktree. The task is added to the backlog (`artefact_type` inferred from description, `sprint` set to current). It consumes complexity budget. It is reviewed during the next `/gse:review` unless trivial (complexity ≤ 1). It is delivered with the rest of the sprint. |

### 3.2 Onboarding

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:hug` | **User Profile** | Establish or update the full engineering context profile (see Section 3.2.1). Also verifies that the project is a git repository and initializes `.gse/` if needed |

#### 3.2.1 HUG Profile Dimensions

The HUG activity captures and maintains the following profile dimensions:

| Dimension | Purpose | Examples |
|-----------|---------|----------|
| **IT expertise** | Calibrate technical depth of explanations | Beginner / Intermediate / Advanced / Expert |
| **Scientific expertise** | Calibrate analytical rigor and formalism | None / Familiar / Proficient / Researcher |
| **Abstraction capability** | Calibrate level of conceptual vs. concrete communication | Prefers examples / Balanced / Prefers abstractions |
| **Language** | Adapt interaction and production languages | `chat: fr`, `artifacts: en`, `overrides: {requirement: fr}`. Default: chat=detected, artifacts=en. Changeable at any time globally or per document. |
| **Preferred verbosity** | Control response length | Concise / Standard / Verbose |
| **Domain background** | Source of analogies for adaptive communication (P9) | Teaching / Business / Science / Engineering / Design |
| **Decision involvement** | Calibrate decision tier thresholds (P7) | Hands-off (more Auto) / Balanced / Hands-on (more Gate) |
| **Project domain** | Adapt engineering recommendations | Web / Embedded / Scientific / CLI / Library / Mobile |
| **Team context** | Adapt collaboration recommendations | Solo / Small team / Large team |
| **Learning goals** | Drive proactive learning proposals (P14) | "I want to understand testing" / "Learn git basics" / None |
| **Contextual tips** | Enable/disable in-activity micro-explanations (P14) | Enabled / Disabled |
| **Emoji** | Enable/disable emoji in chat output | On (default) / Off |

**Smart interview:** The agent infers as many dimensions as possible from context before asking:
- **Language:** detected from the user's first message
- **Project domain:** detected from package manifest, file extensions
- **IT expertise:** estimated from vocabulary and question complexity
- **Team context:** detected from git log (multiple committers?)

Only dimensions that cannot be reliably inferred are asked explicitly. For a typical solo project, the interview should have 4-5 questions, not 11.

### 3.3 Learning

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:learn` | **Learn** | Start an explicit learning session on a topic. **Reactive:** the user asks (`/gse:learn git branching`). **Proactive:** the agent proposes a session at a natural workflow transition when it detects a competency gap relevant to the project. Sessions are adapted to the user's level (P9) and tracked in the competency map (P14). |

`/gse:learn` supports three modes:

| Mode | Trigger | Duration | Example |
|------|---------|----------|---------|
| **Quick** | User or agent proposal | ~5 min | Key concepts + how they apply to the current project |
| **Deep** | User request | ~15 min | Concepts + examples + a small practice exercise in the project context |
| **Roadmap** | `/gse:learn --roadmap` | ~2 min | Show the competency map: what the user has learned, what gaps remain, what the agent recommends next |

### 3.4 Backlog

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:backlog` | **Backlog** | View and manage the unified work item list. Items are either in the **pool** (unplanned) or assigned to a **sprint**. Syncs with GitHub Issues when enabled. See Section 12.3 |

`/gse:backlog` sub-commands:

| Sub-command | Usage |
|-------------|-------|
| `/gse:backlog` | Show full backlog (pool + current sprint) |
| `/gse:backlog add <description>` | Add a new item to the pool |
| `/gse:backlog sprint` | Show current sprint items only |
| `/gse:backlog pool` | Show unplanned items only |
| `/gse:backlog --type code` | Filter by artefact type (code/test/requirement/design/doc/config/import) |
| `/gse:backlog sync` | Synchronize with GitHub Issues |

The agent also creates backlog items **automatically** during other activities (REVIEW findings, COLLECT imports, PLAN deferrals) — `/gse:backlog` is for explicit user interaction.

### 3.5 Discovery & Planning

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:collect` | **Collect** | Inventory and classify artefacts from **internal** (current project) and **external** (other local projects, GitHub repos) sources. Import open GitHub Issues into the backlog. See Section 4 |
| `/gse:assess` | **Assess** | Evaluate artefact current status with respect to project goals, identify gaps and risks. For external sources, evaluate compatibility and integration cost |
| `/gse:plan` | **Plan** | Select items from the backlog pool and promote them to the current sprint. Create new items if needed. **At strategic level:** creates the sprint branch. **At tactical level:** assigns branch names to each task. The sprint plan is a **filtered view** of the backlog. |

### 3.6 Engineering

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:reqs` | **Requirements** | Define product functions and qualities (FR & NFR) including user stories for validation testing |
| `/gse:design` | **Design** | Define architecture decisions, component decomposition, interface contracts, and technical choices. Produces design artefacts traced to requirements. All significant choices are logged to the decision journal |
| `/gse:preview` | **Preview** | Simulate and show what the planned artefacts will look like before building them — wireframes, API contracts, component diagrams, user story walkthroughs (see Section 5) |
| `/gse:tests` | **Tests** | Define test strategy, write tests, set up test environment, execute test campaigns, and produce test evidence. Covers verification (unit, integration) and validation (acceptance, E2E, visual). Adapts the test pyramid to the project domain. Installs required tools (test frameworks, browsers, coverage tools). Produces test campaign reports with screenshots and optional video. See Section 6 |
| `/gse:produce` | **Produce** | **Create feature branch + worktree** for the task, then execute the production plan in the isolated worktree. All code, tests, and docs are committed to the feature branch. Tests are executed after production and results are attached as evidence. |
| `/gse:deliver` | **Deliver** | **Merge** reviewed feature branches into the sprint branch, merge sprint branch into `main`, tag release, generate changelog. **Optionally deploy:** if `git.post_tag_hook` is configured, execute the deployment command after tagging. If deployment fails, propose rollback (Gate). Clean up branches and worktrees (see Section 10.3) |

### 3.7 Quality

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:review` | **Review** | Review operates on the **branch diff** (`git diff sprint-branch...feature-branch`), not just file state. Complete review of all artefact types in the current sprint. Includes **devil's advocate** perspective on the agent's own productions (P16): hunts hallucinations, challenges assumptions, verifies libraries/APIs exist. Updates health score |
| `/gse:fix` | **Fix** | Create a fix branch from the reviewed branch, apply fixes in an isolated worktree, with traceability to review items |

### 3.8 Capitalization

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:compound` | **Compound** | Capitalize learnings across 3 axes: **Axe 1** (project — patterns, errors, best practices → `compound.md`), **Axe 2** (methodology — what worked/didn't in GSE-One itself → propose issue on GSE-One repo, filtered: only actionable feedback observed in 2+ sprints or confirmed by user), **Axe 3** (competencies — feed P14 learning notes) |
| `/gse:integrate` | **Integrate** | Route capitalized solutions: Axe 1 → project config/rules, Axe 2 → issue on `your-org/gse-one` repo (if user accepts), Axe 3 → `docs/learning/` + competency map |

---

## 4. Collect — Artefact Inventory and External Source Discovery

The `/gse:collect` activity inventories available material for the project. It operates in two modes that can be combined.

### 4.1 Internal Mode (default)

Scans the current project and produces an inventory of all existing artefacts:

- Source files, tests, documentation, configuration
- Sprint artefacts in `docs/sprints/`
- Learning notes in `docs/learning/`
- Git state: branches, worktrees, tags
- Dependencies (package manifests)

Output: an artefact inventory saved to `.gse/inventory.yaml`, classified by type, status (draft/reviewed/approved/implemented), and completeness. This file is used by `/gse:assess` as input for gap analysis.

### 4.2 External Mode

Activated when the user provides a path or URL:

```
/gse:collect ~/my-other-project/src/auth/
/gse:collect https://github.com/user/repo
/gse:collect ~/project-A ~/project-B https://github.com/user/template
```

The agent scans the external sources and for each discovered element produces a **reusability assessment**:

| Field | Description |
|-------|-------------|
| **Source** | Path or URL of the element |
| **Type** | Code module / Component / Test suite / Documentation / Configuration / Template |
| **Description** | What it does (auto-detected or from README/docstrings) |
| **Reusability** | Reusable as-is / Adaptable / Reference only / Incompatible |
| **Dependencies** | What the element requires (libraries, frameworks, services) |
| **Compatibility** | Does it match the current project's stack, language, architecture? |
| **Integration cost** | Estimated complexity points (P10) to integrate into the project |
| **License** | License of the source (for external repos) — flagged if restrictive |

For GitHub sources, the agent uses the GitHub API or clones a shallow copy to analyze the repository structure, README, and relevant source files without downloading the entire history.

### 4.3 Reusability Evaluation (Gate Decision)

After scanning, the agent presents the findings as a **Gate decision** (P7):

```
**Question:** Which external elements do you want to include in your project?

**Context:** I scanned 3 sources and found 8 potentially reusable elements.

**Options per element:**
  ✓ ~/project-A/src/auth/       — Auth module (Flask, JWT)
    Reusability: adaptable (your project uses FastAPI, needs adapter)
    Integration cost: ~3 complexity points
    Dependencies: PyJWT, bcrypt (compatible)
    [Include] [Skip] [Discuss]

  ✓ ~/project-A/tests/test_auth/ — Auth test suite
    Reusability: adaptable (follows same module)
    Integration cost: ~1 point
    [Include] [Skip] [Discuss]

  ✗ github.com/user/repo/src/db/  — Database layer (MongoDB)
    Reusability: incompatible (your project targets PostgreSQL)
    [Skip] [Discuss]

  ✓ github.com/user/template/     — Project template (FastAPI)
    Reusability: as-is (matches your stack)
    Integration cost: ~2 points
    License: MIT ✓
    [Include] [Skip] [Discuss]
```

### 4.4 Source Registry

All evaluated sources — whether retained or skipped — are recorded in `.gse/sources.yaml` for traceability:

```yaml
# .gse/sources.yaml
sources:
  - id: SRC-001
    origin: ~/my-other-project/src/auth/
    type: local
    evaluated: 2026-04-10
    sprint: 3
    elements:
      - path: auth_module.py
        reusability: adaptable
        status: included              # included | skipped | deferred
        integration_task: TASK-004    # link to plan
        target: src/auth/             # where it was placed in the project
      - path: tests/test_auth.py
        reusability: adaptable
        status: included
        integration_task: TASK-005
        target: tests/test_auth/

  - id: SRC-002
    origin: https://github.com/user/repo
    type: github
    evaluated: 2026-04-10
    sprint: 3
    license: MIT
    elements:
      - path: src/db/
        reusability: incompatible
        status: skipped
        reason: "Project uses PostgreSQL, source uses MongoDB"
```

### 4.5 Integration into the Lifecycle

| Phase | How external sources are used |
|-------|------------------------------|
| **COLLECT** | Scan, evaluate, register sources. User selects what to include. |
| **ASSESS** | Gap analysis considers both internal artefacts and retained external sources. |
| **PLAN** | Each retained external element becomes an import/adapt task in the sprint plan, with estimated complexity cost and dependencies. |
| **PRODUCE** | Import tasks are executed in their own feature branch/worktree. The agent copies, adapts, and integrates the external element. |
| **REVIEW** | Imported elements are reviewed like any other artefact — the diff shows exactly what was added/modified. |

### 4.6 Provenance Traceability

Every artefact that originates from an external source carries a `gse.source` field in its frontmatter:

```yaml
---
gse:
  type: code
  sprint: 3
  source: SRC-001                     # reference to .gse/sources.yaml
  source_origin: ~/my-other-project/src/auth/auth_module.py
  adaptation: "Replaced Flask with FastAPI, updated JWT config"
  traces:
    implements: [REQ-003]
    derives_from: [DES-007]
  status: implemented
  created: 2026-04-10
---
```

This ensures that at any point in the project's life, someone can answer: "Where did this code come from? What was changed? Why?"

### 4.7 Assess — Gap Analysis

The `/gse:assess` activity evaluates the project's current state against its goals:

1. **Input:** Artefact inventory from COLLECT + project goals from config or user
2. **Analysis:**
   - For each project goal: which artefacts exist? Which are missing?
   - For each existing artefact: what is its status (draft/reviewed/approved)?
   - For external sources: what is the compatibility and integration cost?
3. **Output:** A gap analysis report identifying each gap with a `GAP-NN` identifier:
   - ✓ Covered goals (artefacts exist and are complete)
   - ◐ Partial goals (artefacts exist but incomplete or unreviewed)
   - ✗ Uncovered goals (no artefacts) → `GAP-01`, `GAP-02`, ...
   - ⚠ Risk areas (high-complexity gaps, security-sensitive gaps)

   GAP identifiers are transient analysis results (not persistent artefacts like REQ- or TASK-). They are used to reference specific gaps in sprint planning and decision discussions.

4. **Feeds PLAN:** The gap analysis directly informs planning — uncovered goals (GAP-NN items) become candidate TASK items in the backlog pool.

---

## 5. Preview

The `/gse:preview` activity shows what a planned artefact will look like before production:

| Artefact type | Preview format |
|---------------|---------------|
| UI feature | Wireframe description, screen-by-screen walkthrough |
| API | Example request/response pairs, endpoint summary |
| Architecture | Component diagram (text/mermaid), dependency map |
| Data model | Entity list, relationship description |
| Feature | User story walkthrough: "As a user, I click X, I see Y" |
| Imported element | Side-by-side: original source vs. planned adaptation |

Preview is lightweight — it is not a prototype. Its purpose is to close the gap between "I described what I want" and "I can see what I'll get" before any code is written.

---

## 6. Testing Strategy

The `/gse:tests` activity manages the full testing lifecycle: strategy definition, environment setup, test writing, campaign execution, evidence collection, and coverage analysis. It adapts to the project domain and the user's expertise level.

### 6.1 Test Strategy Framework

#### Test types

| Type | Purpose | Traces to |
|------|---------|-----------|
| **Unit** | Verify individual functions/modules in isolation | DES (design), code |
| **Integration** | Verify that modules work together correctly | DES (interfaces), REQ |
| **E2E (End-to-End)** | Simulate complete user workflows through the application | REQ (user stories) |
| **Visual** | Verify UI rendering via screenshot comparison | REQ (UI requirements) |
| **Acceptance** | Validate that a requirement is met (from the user's perspective) | REQ (acceptance criteria) |
| **Regression** | Ensure that previously fixed bugs don't reappear | RVW (past review findings) |

#### Test pyramid (calibrated by project domain)

The agent proposes a test distribution adapted to the project type (from `config.yaml → project.domain`):

| Domain | Unit | Integration | E2E / Visual | Acceptance |
|--------|------|-------------|-------------|------------|
| **Web frontend** | 20% | 20% | 40% | 20% |
| **API backend** | 50% | 30% | 5% | 15% |
| **CLI tool** | 60% | 20% | 10% | 10% |
| **Scientific** | 40% | 20% | 0% | 40% |
| **Library** | 70% | 20% | 0% | 10% |
| **Mobile** | 25% | 20% | 35% | 20% |

The pyramid is a **starting point** — the agent adjusts based on actual project needs and presents deviations as Inform-tier decisions.

#### Risk-based prioritization

Not all code needs equal test coverage. The agent prioritizes testing based on risk:

| Factor | More tests | Fewer tests |
|--------|-----------|-------------|
| Module touched by a review finding (RVW) | High priority | — |
| Module with a Gate-tier decision (DEC) | Regression test mandatory | — |
| Module imported from external source (SRC) | Compatibility tests mandatory | — |
| Security-sensitive code (auth, crypto, input) | Comprehensive coverage | — |
| Simple configuration / static content | — | Minimal tests |

### 6.2 Test Environment Management

The agent manages the complete test toolchain:

#### Auto-detection and installation

When `/gse:tests` is first called, the agent:

1. **Detects** the project's language and framework from package manifests
2. **Proposes** the test framework (Gate decision for beginners, Inform for experts):
   - Python → pytest + coverage.py
   - JavaScript/TypeScript → vitest or jest + c8
   - Go → built-in `go test` + cover
   - etc.
3. **Installs** the framework as a dev dependency
4. **Configures** the test runner (config file, directories, scripts)

#### Visual testing setup (web projects)

When `project.domain` is `web` or `mobile`, the agent proposes visual testing (Gate):

```
**Question:** Your project has a web interface. Would you like to enable 
visual testing (screenshots and simulated user interactions)?

**Context:** Visual tests let me verify that your app looks correct 
by taking screenshots and comparing them. I can also record videos 
of user workflows as evidence.

**Options:**
1. Yes, full visual testing (screenshots + video on failure)
   - Installs: Playwright + Chromium (~200MB)
   - Benefit: automated proof that the UI works
2. Yes, screenshots only (no video)
   - Installs: Playwright + Chromium (~200MB)
   - Lighter but still provides visual evidence
3. No, text-based tests only
   - No additional install
   - Faster, but no visual proof
4. Discuss
```

If accepted, the agent:
1. Installs the visual testing tool: `npx playwright install --with-deps chromium`
2. Creates the test directory structure: `tests/e2e/`, `tests/visual/`
3. Creates a base configuration file
4. Adds a TASK in the backlog for writing the first visual test

**Framework drift detection:** Each time `/gse:tests --run` or `/gse:produce` executes, the agent compares the current framework (from package manifest) with the configured framework in `config.yaml → testing.framework`. If they differ: "The project's test framework has changed from jest to vitest. Would you like me to update the test configuration?" (Inform). If accepted, the agent re-runs setup and flags existing tests that may need migration.

### 6.3 Test Execution and Evidence

#### During `/gse:produce`

After producing code for a TASK, the agent automatically:

1. **Runs the test suite** in the worktree:
   ```bash
   cd .worktrees/sprint-03-feat-auth/
   uv run pytest --cov --cov-report=json  # or equivalent
   ```

2. **Captures evidence**:
   - Test results (pass/fail per test)
   - Code coverage report
   - Screenshots (if visual testing enabled)
   - Video recording on failure (if enabled)

3. **Saves evidence** to `tests/evidence/sprint-NN/TASK-NNN/`:
   ```
   tests/evidence/sprint-03/TASK-038/
   ├── results.json              # Test results (machine-readable)
   ├── coverage.json             # Coverage data
   ├── login-page.png            # Screenshot: login page rendered
   ├── login-error.png           # Screenshot: error state
   ├── login-success.png         # Screenshot: after successful login
   ├── login-flow.mp4            # Video: full login E2E test (if enabled)
   └── report.md                 # Human-readable campaign report
   ```

4. **Analyzes screenshots** (multimodal LLM capability):
   - Checks for visual defects: misaligned elements, truncated text, missing images
   - Compares with reference screenshots (visual regression)
   - Detects accessibility issues: insufficient contrast, tiny text
   - Reports findings as `[VISUAL]` tagged items

**Important: Agent visual analysis is best-effort.** The agent's multimodal analysis can detect obvious visual defects (missing images, broken layouts, text overflow) but is NOT a replacement for specialized tools. For reliable results:
- **Accessibility:** Use dedicated tools (Axe, Lighthouse) — the agent can install and run them as part of the test campaign
- **Visual regression:** Use pixel-diff tools (Playwright's built-in comparator, Percy, BackstopJS) — the agent can configure them
- **The agent's role** is to orchestrate these tools, interpret their output, and present findings — not to replace them
- Agent's own visual assessments are tagged with confidence level (P15): tool-based findings → **Verified**, agent's own analysis → **Moderate confidence**

#### Test campaign report

Each test execution produces a traceable **campaign report**:

```markdown
---
gse:
  type: test-campaign
  sprint: 3
  branch: gse/sprint-03/feat/auth
  traces:
    implements: [REQ-007]
    derives_from: [TASK-038]
  created: 2026-04-10
---

# Test Campaign — Sprint 3 / TASK-038

## Summary
- Executed: 24 tests (12 unit, 8 integration, 4 E2E)
- Passed: 22 (91.7%)
- Failed: 2
- Duration: 45 seconds
- Code coverage: 78%

## Failures
| ID | Test | Expected | Got | Linked to |
|----|------|----------|-----|-----------|
| TST-002 | Login with invalid email | HTTP 400 | HTTP 500 | REQ-007 |
| TST-004 | Visual: login button mobile | Button visible | Button overlaps footer | REQ-007 |

## Evidence
- [Login page](tests/evidence/sprint-03/TASK-038/login-page.png)
- [Error state](tests/evidence/sprint-03/TASK-038/login-error.png)
- [Failure video](tests/evidence/sprint-03/TASK-038/login-flow.mp4)

## Coverage
| Module | Coverage | Δ from previous |
|--------|----------|----------------|
| src/auth/ | 92% | +12% |
| src/api/ | 64% | new |
```

Campaign reports are saved in `docs/sprints/sprint-NN/test-reports/` and traced in the backlog.

### 6.4 Coverage Model

The health dashboard tracks three coverage dimensions:

| Dimension | Measures | Target |
|-----------|---------|--------|
| **Code coverage** | % of code lines/branches exercised by tests | Configurable (default 60%) |
| **Requirements coverage** | % of REQ with at least one linked test | 100% for `must` priority, 80% for `should` |
| **Risk coverage** | % of high-risk modules (security, Gate decisions, imports) with dedicated tests | 100% |

When coverage drops below the configured minimum, a **Hard guardrail** triggers:
"Code coverage is 45% (minimum: 60%). Add tests before proceeding to DELIVER."

### 6.5 Adaptation to User Expertise

| Level | Agent's testing behavior |
|-------|------------------------|
| **Beginner** | The agent writes all tests, executes them, and shows visual results. "8 tests pass, 2 fail — here are the screenshots." No jargon. The user sees evidence, not code. |
| **Intermediate** | The agent proposes the test strategy, writes the tests, explains what each test verifies in plain language. The user can modify tests. Technical terms introduced progressively (P14). |
| **Advanced** | The agent discusses strategy (TDD vs test-after), proposes the test pyramid, co-writes tests with the user. Coverage targets are negotiated. |
| **Expert** | Full collaboration. The agent proposes advanced techniques (property-based testing, mutation testing, contract testing). The user drives, the agent assists. |

---

## 7. Project Health Dashboard

The health dashboard (`/gse:health`) provides a single-screen view of project quality, designed for users who cannot evaluate technical quality directly.

### 7.1 Health Score

A composite score from 0 to 10, computed from 8 sub-dimensions:

```
Project Health: 6.7/10

  Requirements coverage:  ████████░░  12/15 have tests         (8/10)
  Test pass rate:          █████████░  94% passing              (9/10)
  Design debt:             ███░░░░░░░  3 known shortcuts        (3/10)
  Review findings:         ████████░░  2 open, 8 resolved       (8/10)
  Complexity budget:       ██████░░░░  62% consumed             (6/10)
  Traceability:            █████████░  91% of artefacts linked  (9/10)
  Git hygiene:             █████░░░░░  3 branches, 1 stale      (5/10)
  AI integrity:            ██████░░░░  2 unverified assertions   (6/10)
```

**Dimension computation:** Each dimension is scored 0-10 using these formulas:

| Dimension | Formula |
|-----------|---------|
| requirements_coverage | (traced requirements / total requirements) × 10 |
| test_pass_rate | (passing tests / total tests) × 10 |
| design_debt | 10 − (HIGH findings × 2.0 + MEDIUM × 1.0 + LOW × 0.5), floor 0 |
| review_findings | 10 − (open HIGH × 1.5 + MEDIUM × 0.8 + LOW × 0.3), floor 0 |
| complexity_budget | (remaining budget / total budget) × 10 |
| traceability | (fully traced tasks / total tasks) × 10 |
| git_hygiene | weighted score from 6 sub-factors (see Section 7.4) |
| ai_integrity | weighted: unverified assertions 40%, hallucinations 30%, user engagement 30% |

The overall score is the mean of all enabled dimensions. Dimensions listed in `health.disabled_dimensions` are excluded. Alert threshold: any dimension below 7/10 triggers a risk alert.

### 7.2 Risk Alerts

Actionable warnings surfaced from the health score:

```
  ⚠ RISK: REQ-007 (user authentication) has no tests
  ⚠ RISK: Design shortcut DS-002 (hardcoded config) — planned fix: sprint 4
  ⚠ DEBT: 2 dependencies have known vulnerabilities (npm audit)
  ⚠ GIT:  2 worktrees have uncommitted changes
  ⚠ GIT:  Branch gse/sprint-02/feat/old-feature not touched in >2 sprints
  ✓ OK:   All sprint-3 deliverables have been reviewed
  ✓ GIT:  main is clean and tagged (v0.2.1)
  ✓ GIT:  No merge conflicts detected
  ⚠ AI:   2 library recommendations not yet verified (TASK-038, TASK-041)
  ⚠ AI:   User has accepted 6 consecutive decisions without discussion
  ✓ AI:   Devil's advocate found 0 hallucinations in last review
```

### 7.3 Trend

```
  Sprint 1: 5.8  →  Sprint 2: 6.5  →  Sprint 3: 6.9  ↑ improving
```

### 7.4 Git Hygiene Sub-Score

The git hygiene score (0–10) is computed from:

| Factor | Good (high score) | Bad (low score) |
|--------|------------------|-----------------|
| Active branches | < 5 | > 10 |
| Stale branches (not touched in >2 sprints) | 0 | > 3 |
| Uncommitted changes across worktrees | 0 | > 0 |
| Merge conflicts detected | 0 | > 0 |
| Main branch status | Clean, tagged | Dirty, untagged |
| Feature branches without review | 0 | > 2 |

---

## 8. Complexity Budget

### 8.1 Concept

Every sprint has a complexity budget — a finite capacity for new complexity. Each addition to the project has a cost:

| Action | Cost Range | Guidance |
|--------|-----------|----------|
| New utility dependency (lodash, dayjs) | 1 point | Small, well-known, no config |
| New framework dependency (ORM, auth lib) | 2–3 points | Requires config, learning curve |
| New external service integration | 2–4 points | API keys, error handling, latency |
| New UI component | 1–2 points | 1 if standard, 2 if complex/interactive |
| New security surface | 2–3 points | Auth, crypto, user input handling |
| New API endpoint | 1 point | Surface area increase |
| Database schema change | 1–2 points | Migration, backward compatibility |
| New abstraction layer | 2 points | Indirection cost, must justify itself |
| New design pattern introduction | 1–2 points | Team must understand and maintain |
| Configuration system (env vars, config files) | 1 point | One more thing to manage |
| Multi-threading / async introduction | 3 points | Concurrency bugs, reasoning difficulty |
| Architectural pattern change | 3–5 points | 3 for local, 5 for system-wide |
| Custom DSL or metaprogramming | 3–5 points | High maintenance, hard to debug |
| New language/framework | 4–6 points | Build system, tooling, team learning |

The agent selects within the range based on project context and presents the estimate as an Inform-tier decision. **The budget is a directional tool, not a precise constraint** — its purpose is to make scope creep visible and trigger a conversation when the sprint is overloaded.

The budget per sprint is calibrated by project size and team context (via HUG). Default budgets by sprint type:
- **Foundation sprint** (early project): 15 points — more room for structural decisions
- **Feature sprint** (mid-project): 12 points — most complexity is already in place
- **Stabilization sprint** (late project): 8 points — focus on simplification, not addition

**Complexity debt:** If a sprint exceeds its budget, the overrun is recorded as complexity debt. The next sprint's budget is reduced by the overrun amount unless the team explicitly decides to absorb it (Gate decision).

**Simplification credit:** Removing complexity earns negative points. Removing an unused dependency (−1 pt), eliminating a dead abstraction layer (−2 pt), or consolidating two config systems into one (−1 pt) frees budget. The agent actively looks for simplification opportunities.

**Zero-cost items:** The following do NOT consume complexity budget:
- Renaming, reformatting, documentation
- Bug fixes that don't change architecture
- Tests (testing reduces risk, not adds complexity)
- Removing code or dependencies

### 8.2 Visualization

The agent shows the complexity budget whenever planning or adding features:

```
Sprint 3 complexity budget: ████████░░ 8/10 used

Adding "social login" would cost ~3 points:
  - New dependency (OAuth library): +1
  - New external service (Google/GitHub OAuth): +1
  - New security surface (token management): +1

  Remaining after this addition: -1 (over budget)

  Options:
  1. Defer social login to sprint 4 (recommended — keeps sprint healthy)
  2. Remove a lower-priority item to make room (agent suggests which)
  3. Accept over-budget (increases defect risk, review will flag it)
  4. Discuss
```

---

## 9. Guardrails

### 9.1 Purpose

Guardrails are the enforcement mechanism of the risk analysis system (P7→P8→P11). They serve two goals:

1. **Formal validation** — ensure that actions with significant consequences on any project dimension (quality, cost, time, security, scope) are explicitly approved by the user before execution.
2. **Traceability** — every guarded decision is logged in the decision journal with the full risk analysis, the user's choice, and the rationale, so it can be audited and revisited.

Guardrails do not block — they make cost visible and require proportional acknowledgment. The stronger the guardrail, the more explicit the acknowledgment must be.

### 9.2 Levels

| Level | Trigger | Agent Behavior |
|-------|---------|----------------|
| **Soft** | User skips a recommended step | "Skipping tests for this feature. I'll mark it as untested and flag it in health. Proceed?" |
| **Hard** | User makes an unrealistic scope decision | "Adding 12 features to a 1-week sprint will result in none being properly tested. I recommend picking 3. Here's how I'd prioritize: ..." |
| **Emergency** | User's choice creates a security or data risk | "Deploying without fixing the authentication finding exposes user data. I strongly recommend fixing it first. To proceed anyway, please confirm explicitly." |

### 9.3 Git-Specific Guardrails

| Guardrail | Trigger | Level |
|-----------|---------|-------|
| Working on main | User or agent tries to edit code directly on `main` | **Hard** — propose creating a feature branch |
| Uncommitted changes | Agent tries to switch branch with uncommitted work | **Hard** — commit or stash first |
| Unreviewed merge | `/gse:deliver` called before `/gse:review` | **Hard** — review first |
| Merge conflict | Conflict detected during merge | **Gate** — present conflict, explain options, wait for user choice |
| Force push | Any force push attempt | **Emergency** — explain data loss risk |
| Branch sprawl | More than 5 active branches | **Soft** — suggest cleanup |
| Stale branches | Branch not touched in >2 sprints | **Soft** — suggest deletion or archival |

### 9.4 Calibration

Guardrail sensitivity is calibrated by the HUG profile:

| User expertise | Soft | Hard | Emergency |
|---------------|------|------|-----------|
| Beginner | Triggers often | Triggers on moderate risk | Always triggers |
| Intermediate | Triggers selectively | Triggers on high risk | Always triggers |
| Expert | Rarely triggers | Triggers on very high risk | Always triggers |

Emergency guardrails always trigger regardless of expertise — they represent genuine danger, not preference.

---

## 10. Version Control Strategy

### 10.1 Branch Model

```
main                                         # Always stable, deployable
├── gse/sprint-03                           # Sprint branch (created by PLAN)
│   ├── gse/sprint-03/feat/user-auth        # Feature branch (created by PRODUCE)
│   ├── gse/sprint-03/feat/dashboard        # Another feature branch
│   ├── gse/sprint-03/fix/rvw-005           # Fix branch (created by FIX)
│   └── gse/sprint-03/docs/api-reference    # Documentation branch
└── gse/sprint-04                           # Next sprint (future)
```

**Branch naming convention:** `gse/sprint-NN/type/short-description`

| Type prefix | Usage |
|-------------|-------|
| `feat/` | New feature or enhancement |
| `fix/` | Fix from review finding (references RVW-NNN) |
| `refactor/` | Structural improvement, no behavior change |
| `docs/` | Documentation artefact |
| `test/` | Test-only changes |

### 10.2 Worktree Isolation

Each active branch is checked out in its own git worktree — a separate directory on disk linked to the same repository:

```
<project-root>/                          # main branch (always clean)
├── .gse/
│   └── ...
├── .worktrees/                          # Worktree directories (gitignored)
│   ├── sprint-03-feat-user-auth/        # Full working copy for user-auth
│   ├── sprint-03-feat-dashboard/        # Full working copy for dashboard
│   └── sprint-03-fix-rvw-005/           # Full working copy for fix
└── src/, tests/, docs/, ...             # Main branch files
```

**Why worktrees, not just branches:**
- Each task has its own directory — no `git stash` or `git switch` needed
- User can review one task while the agent works on another
- Failed experiments are discarded by deleting the worktree — no trace on `main`
- Merge conflicts are detectable before they happen (compare worktree diffs)
- Beginners never need to understand `git checkout` — the agent handles isolation transparently

**Small project escape hatch:** For very small projects (single file, solo developer), the user can set `git.strategy: branch-only` or `git.strategy: none` in config to disable worktrees or branching entirely (see Section 13).

### 10.3 Lifecycle Integration

| Activity | Git Actions |
|----------|------------|
| **PLAN (strategic)** | Create sprint branch `gse/sprint-NN` from `main`. Assign branch names to each planned task. |
| **PLAN (tactical)** | Assign branch names to newly planned tasks. No branch creation yet. |
| **PRODUCE** | Create feature branch from sprint branch + create worktree in `.worktrees/`. All work happens in the worktree. Commit with conventional messages: `gse(sprint-NN/activity): description`. |
| **REVIEW** | Review operates on the branch diff: `git diff gse/sprint-NN...gse/sprint-NN/feat/X`. Shows exactly what changed. |
| **FIX** | Create fix branch `gse/sprint-NN/fix/rvw-NNN` from the reviewed feature branch. Fix in isolated worktree. |
| **DELIVER** | **Gate decision:** merge strategy (squash/merge/rebase). Merge feature branches → sprint branch → `main`. Tag `main` with semantic version. Delete merged branches and worktrees. |
| **PAUSE** | Auto-commit all uncommitted work in all active worktrees. Save worktree map in checkpoint. |
| **RESUME** | Verify all worktrees exist and are intact. Report any external changes. |
| **STATUS** | Show branch tree, worktree state (active/paused/ready-to-merge), uncommitted changes. |
| **HEALTH** | Compute git hygiene sub-score: branch count, stale branches, conflicts, uncommitted changes. |
| **COLLECT** | Inventory branches and worktrees alongside artefact files. |
| **TASK** | Create ad-hoc branch `gse/sprint-NN/task/description` + worktree. |

### 10.4 Merge Strategy (Gate Decision)

Every merge is a Gate-tier decision. The presentation is **adapted to the user's expertise** (P9 — Adaptive Communication):

#### For a beginner user

The agent hides technical git terminology and presents the choice in plain language:

```
**Question:** Your "user authentication" feature is ready to be integrated.
  How do you want its history to appear in the project?

**Context:** This feature involved 12 individual saves (commits) and 
  modified 8 files. There are no conflicts with the rest of the project.

**Options:**
1. Clean summary (recommended) — combine all 12 saves into one single entry.
   Your project history will show: "Added user authentication" as one item.
   - Pros: simple to read, easy to undo the whole feature if needed later
   - Cons: you lose the step-by-step development trail
2. Full history — keep all 12 individual saves visible.
   - Pros: you can see every step of how the feature was built
   - Cons: the project history becomes longer and harder to scan
3. Let me decide — use the default from the project configuration
4. Discuss — explain more about what this means

**Your choice:** [1/2/3/4]
```

The agent chooses the appropriate git command (squash, merge, rebase) based on the user's plain-language answer, without exposing the technical mechanism.

#### For an advanced/expert user

The agent presents the technical options directly:

```
**Question:** Merge strategy for `gse/sprint-03/feat/user-auth`?

**Context:** 12 commits, 8 files changed, no conflicts with sprint branch.

**Options:**
1. Squash — single commit on sprint branch
   - Pros: clean history, atomic revert
   - Cons: loses granular commit history
   - Consequence horizon: Now → clean | 3mo → easy bisect | 1yr → fine
2. Merge commit — preserve all commits with merge node
   - Pros: full history, shows development process
   - Cons: noisier log
3. Rebase — linear replay on sprint branch
   - Pros: linear history, no merge commit
   - Cons: rewrites hashes (risky if shared)
4. Discuss

**Your choice:** [1/2/3/4]
```

#### For an intermediate user

The agent uses a hybrid: plain-language descriptions with technical terms in parentheses, so the user progressively learns the vocabulary:

```
**Options:**
1. Clean summary (squash merge) — combine all saves into one entry
2. Full history (merge commit) — keep all individual saves visible
3. Linear replay (rebase) — replay saves on top of current state
4. Discuss
```

### 10.5 Commit Message Convention

All commits follow the convention:

```
gse(<scope>): <description>

<optional body>

Sprint: <N>
Traces: <artefact IDs>
```

**Examples:**
```
gse(sprint-03/feat): implement user authentication flow

Sprint: 3
Traces: REQ-007, DES-003

gse(sprint-03/fix): resolve XSS vulnerability in login form

Sprint: 3
Traces: RVW-005, SEC-002

gse(sprint-03/docs): add API reference for auth endpoints

Sprint: 3
Traces: DES-003
```

### 10.6 Safety and Recovery

Before any destructive git operation (merge, branch delete, worktree remove, tag delete), the agent creates a **safety reference**:

```bash
# Before merging:
git tag gse-backup/sprint-03-pre-merge-feat-auth $(git rev-parse gse/sprint-03)

# Before deleting a branch:
git tag gse-backup/sprint-03-feat-auth-deleted $(git rev-parse gse/sprint-03/feat/auth)
```

Safety tags are prefixed `gse-backup/` and retained for 30 days (configurable via `git.backup_retention_days`).

**Recovery procedures:**
- **Branch recovery:** `git checkout -b gse/sprint-03/feat/auth gse-backup/sprint-03-feat-auth-deleted`
- **Merge reversal:** `git checkout gse/sprint-03 && git reset --hard gse-backup/sprint-03-pre-merge-feat-auth`
- **State file recovery:** `.gse/` files are git-tracked — `git checkout HEAD~1 -- .gse/backlog.yaml` restores the previous version

**Cleanup:** Old backup tags are cleaned up during `/gse:deliver` (delete tags older than `backup_retention_days`).

**Project backup:** GSE-One relies on git as the safety net. To protect against local disk failure, the agent proposes pushing to a remote during `/gse:deliver` if no remote is configured: "Your project has no remote. Push to GitHub/GitLab to protect your work?" (Inform tier).

```yaml
# In config.yaml → git:
  backup_before_destructive: true     # create safety tags (default: true)
  backup_retention_days: 30           # how long to keep backup tags
```

---

## 11. Decision Journal

### 11.1 Purpose

The agent automatically maintains a decision journal (`.gse/decisions.md`) that records every Inform-tier and Gate-tier decision. This prevents "why did we do this?" amnesia and enables informed revisiting of past choices.

### 11.2 Format

```markdown
## DEC-005 — Database engine: PostgreSQL
- **Sprint:** 2
- **Date:** 2026-04-10
- **Tier:** Gate
- **Branch:** gse/sprint-02/feat/data-layer
- **Options considered:** SQLite, PostgreSQL, MongoDB
- **Chosen:** PostgreSQL
- **Why:** User expects >500 concurrent users within 6 months.
  SQLite would require a costly migration later.
- **Consequence horizon:**
  - Now: more setup, managed service cost (~$15/month)
  - 3 months: scales without changes
  - 1 year: still appropriate
- **Reversibility:** High cost (data migration + ORM changes, ~2 sprints)
- **Review trigger:** Revisit if user count stays <50 after 6 months
```

### 11.3 Auto Decisions

Auto-tier decisions are logged in a compact format in `.gse/decisions-auto.log`:

```
2026-04-10 DEC-A042 Auto: chose ESLint flat config over legacy .eslintrc (standard for new projects)
2026-04-10 DEC-A043 Auto: named component UserProfileCard (follows existing naming convention)
```

This log is not shown to the user by default but is available via `/gse:status --decisions`.

---

## 12. Artefact Storage Conventions

### 12.1 Project Layout

```
<project-root>/
├── .gse/
│   ├── config.yaml                  # GSE-One configuration & customization
│   ├── profile.yaml                 # HUG user profile (solo) or symlink to profiles/
│   ├── profiles/                    # Per-user profiles (team mode)
│   ├── status.yaml                  # Current lifecycle state, health, complexity budget
│   ├── backlog.yaml                 # Unified work items (TASK) with git state
│   ├── sources.yaml                 # External source registry
│   ├── inventory.yaml               # Artefact inventory (COLLECT output)
│   ├── decisions.md                 # Decision journal (Inform + Gate tiers)
│   ├── decisions-auto.log           # Auto-tier decision log (compact)
│   └── checkpoints/                 # Pause/resume snapshots
│       └── checkpoint-YYYY-MM-DD-HHMM.yaml
│
├── .worktrees/                      # Git worktree directories (gitignored)
│   └── sprint-NN-type-description/  # One directory per active task
│
├── docs/
│   ├── sprints/
│   │   └── sprint-NN/
│   │       ├── plan.md              # Sprint plan
│   │       ├── reqs.md              # Requirements (FR & NFR)
│   │       ├── design.md            # Design decisions & architecture
│   │       ├── tests.md             # Test definitions & traceability
│   │       ├── review.md            # Review findings
│   │       ├── compound.md          # Capitalized learnings
│   │       └── release.md           # Release/delivery notes
│   └── learning/                    # Learning notes (P14)
│       ├── git-branching.md         # Personal course note on git branching
│       ├── testing-strategies.md    # Personal course note on testing
│       └── ...                      # One file per topic, enriched over time
│
├── src/                             # Source code artefacts
├── tests/                           # Test artefacts
│   └── evidence/                    # Test evidence (screenshots, videos, reports)
│       └── sprint-NN/
│           └── TASK-NNN/
│               ├── *.png            # Screenshots
│               ├── *.mp4            # Videos (optional)
│               └── report.md        # Campaign report
└── ...                              # Other project files
```

### 12.2 Artefact Metadata

Each structured artefact (markdown) includes a YAML frontmatter for traceability:

```yaml
---
gse:
  type: requirement | design | test | review | plan | compound | decision | learning-note | code | test-campaign
  sprint: 3
  branch: gse/sprint-03/feat/user-auth
  traces:                                 # typed trace links (P6)
    derives_from: [REQ-001]
    implements: [DES-002]
    decided_by: [DEC-005]
  status: draft | reviewed | approved | implemented
  complexity_cost: 2                    # optional — points consumed
  source: SRC-001                       # optional — external source reference
  source_origin: ~/project/auth.py      # optional — original file path or URL
  adaptation: "Replaced Flask..."       # optional — what was changed from original
  created: 2026-04-10
  updated: 2026-04-10
---
```

### 12.3 Unified Backlog

`.gse/backlog.yaml` is the **single source of truth** for all work items. Each TASK carries its own git state — there is no separate worktree tracking file.

```yaml
# .gse/backlog.yaml
items:
  # Sprint task — in progress
  - id: TASK-038
    title: "Implement user authentication"
    artefact_type: code
    sprint: 3
    priority: must
    complexity: 3
    traces:
      implements: [REQ-007]
      derives_from: [DES-003]
    acceptance_criteria: "User can login via GitHub OAuth"
    status: in-progress              # open | planned | in-progress | review | fixing | done | delivered | deferred
    origin: plan                     # plan | review | collect | user | import
    origin_ref: null
    git:
      branch: gse/sprint-03/feat/auth
      branch_status: active          # null | planned | active | merged | deleted
      worktree: .worktrees/sprint-03-feat-auth
      worktree_status: active        # null | active | removed
      commits: 12
      last_commit: 2026-04-10T14:30
      uncommitted_changes: 0
    github_issue: 42                 # null if GitHub not enabled
    test_campaign: null              # optional — path to test campaign report
    test_pass_rate: null             # optional — % passing (set after test run)
    code_coverage: null              # optional — % coverage (set after test run)
    created: 2026-04-08
    updated: 2026-04-10

  # Pool item — not yet assigned to a sprint
  - id: TASK-042
    title: "Add dark mode support"
    artefact_type: code
    sprint: null                     # null = pool (unplanned)
    priority: could
    complexity: null                 # estimated during PLAN when promoted
    traces:
      derives_from: []
      implements: []
    status: open
    origin: user
    git:
      branch: null
      branch_status: null
      worktree: null
      worktree_status: null
    github_issue: 46
    created: 2026-04-10
    updated: 2026-04-10
```

**Key design principles:**
- **One ID, one item, one place** — no dual tracking between plan and backlog
- **Git state is per-TASK** — branch and worktree info lives with the task, not in a separate file
- **Sprint plan = filtered view** — `docs/sprints/sprint-NN/plan.md` is generated from the backlog, not a primary data store
- **Merge queue = derived view** — items where `status == done AND git.branch_status == active`

**Status lifecycle:**

| TASK status | git.branch_status | git.worktree_status | Triggered by |
|-------------|-------------------|---------------------|--------------|
| `open` | `null` | `null` | Created (pool or backlog add) |
| `planned` | `planned` | `null` | PLAN (promoted to sprint, branch name assigned) |
| `in-progress` | `active` | `active` | PRODUCE (branch + worktree created) |
| `review` | `active` | `active` | REVIEW (under review) |
| `fixing` | `active` | `active` | FIX (fix branch in progress) |
| `done` | `active` | `active` | FIX complete — ready to merge |
| `delivered` | `deleted` | `removed` | DELIVER (merged, cleaned up) |
| `deferred` | `null` or `deleted` | `null` or `removed` | Deferred to future sprint |

### 12.4 Status State File

`.gse/status.yaml` tracks the project's dynamic state:

```yaml
gse_version: "0.7.0"
current_sprint: 3
current_phase: LC02                  # LC00 | LC01 | LC02 | LC03
plan_status: approved                # pending | approved | none

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
  last_computed: 2026-04-10

complexity:
  budget: 10
  consumed: 6.5
  remaining: 3.5

# P16 pushback detection
consecutive_acceptances: 2             # counter for passive acceptance detection
never_discusses: false                 # user never selects Discuss
terse_responses: 0                     # single-word confirmations counter
never_modifies: false                  # user never modifies proposals
never_questions: false                 # user never asks why

last_activity: /gse:produce
last_activity_date: 2026-04-10

# Stale sprint detection (complexity/session-based, not calendar-based)
sessions_without_progress: 0           # incremented each /gse:go or /gse:resume with no TASK status change

# Review findings counter (used by hooks)
review_findings_open: 0
```

### 12.5 Checkpoint Format

Checkpoints (saved by `/gse:pause`, loaded by `/gse:resume`):

```yaml
# .gse/checkpoints/checkpoint-2026-04-10-1630.yaml
timestamp: 2026-04-10T16:30:00
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
    - branch: gse/sprint-03/feat/dashboard
      last_commit: def456
notes: "Working on auth module, tests passing, 2 tests remain"
```

### 12.6 State Loading Priority

When resuming a session, the agent loads state in priority order to stay within context limits:

| Priority | File | Always loaded | Typical size |
|----------|------|--------------|-------------|
| 1 | `status.yaml` | Yes | ~20 lines |
| 2 | `profile.yaml` | Yes | ~30 lines |
| 3 | `config.yaml` | Yes | ~40 lines |
| 4 | `backlog.yaml` (current sprint only) | Yes | Variable |
| 5 | `backlog.yaml` (pool) | On demand | Only when user asks |
| 6 | `decisions.md` (last 5) | On demand | Only recent decisions |
| 7 | `sources.yaml` | On demand | Only during COLLECT |
| 8 | `decisions-auto.log` | Never auto-loaded | Only via `/gse:status --decisions` |

**Total essential context:** ~100-200 lines. The agent must NEVER load all state files at once.

---

## 13. Configuration & Customization

### 13.1 Project Configuration

Users can customize GSE-One behavior via `.gse/config.yaml`:

```yaml
# .gse/config.yaml
project:
  name: "My Project"
  domain: "web"                        # web | embedded | scientific | cli | library | mobile

lifecycle:
  mode: full                           # full | lightweight
  stale_sprint_sessions: 3              # sessions without progress before stale detection (/gse:go)
  phases:
    LC02:
      deliver: true
      design: true
      preview: true
      # Custom activity ordering for LC02 (uncomment to override default):
      # order: [reqs, design, preview, tests, plan, produce, review, fix, deliver]

interaction:
  verbosity: standard                   # concise | standard | verbose
  language:
    chat: auto                          # auto (from HUG) | en | fr | de | ...
    artifacts: en                       # default language for produced files

decisions:
  tier_bias: balanced                  # hands-off | balanced | hands-on
  always_gate:
    - security
    - data-model
    - external-dependency
    - merge-strategy                   # merges are always Gate

guardrails:
  sensitivity: auto                    # auto (from HUG) | relaxed | standard | strict

complexity:
  budget_per_sprint: 10                # directional tool, not precise constraint

health:
  disabled_dimensions: []              # list of dimensions to exclude (non-code projects)
  # e.g., [test_pass_rate, design_debt] for documentation projects

hooks:
  protect_main: true                   # block direct commits to main branch (Hard guardrail)
  block_force_push: true               # block git push --force (Emergency guardrail)
  review_findings_on_push: true        # warn if open review findings before push

git:
  strategy: worktree                   # worktree | branch-only | none
  worktree_dir: .worktrees             # relative to project root
  branch_prefix: gse                   # prefix for all GSE-One branches
  merge_strategy_default: squash       # squash | merge | rebase (default proposal for Gate)
  protect_main: true                   # Hard guardrail on direct main commits
  auto_commit_on_pause: true           # Auto-commit uncommitted work on /gse:pause
  commit_convention: gse               # gse | conventional | free
  tag_on_deliver: true                 # Tag main with semantic version on deliver
  cleanup_on_deliver: true             # Delete merged branches and worktrees after deliver
  pre_merge_check: ""                  # optional — e.g., "npm test"
  post_tag_hook: ""                    # optional — e.g., "python scripts/deploy.py staging"
  rollback_on_deploy_failure: true     # auto-propose rollback if post_tag_hook fails
  backup_before_destructive: true      # create safety tags before merge/delete (Section 10.6)
  backup_retention_days: 30            # how long to keep backup tags

github:
  enabled: false                       # auto-detected when git remote exists
  repo: ""                             # auto-detected from git remote
  sync_mode: manual                    # manual | on-activity | real-time
  auto_close_on_deliver: true          # close linked issues when TASK is delivered
  # Methodology feedback (COMPOUND Axe 2) targets the GSE-One plugin repo,
  # read from plugin.json → repository. Not configured here.

testing:
  framework: auto                      # auto-detect | pytest | jest | vitest | go-test | ...
  strategy: auto                       # auto | tdd | test-after
  pyramid: auto                        # auto (from project.domain) | custom
  dependency_audit: true               # run dependency audit during /gse:tests
  audit_tool: auto                     # auto-detect | npm-audit | pip-audit | ...
  visual:
    enabled: false                     # auto-suggested for web/mobile projects
    tool: playwright                   # playwright | cypress | puppeteer
    browsers: [chromium]               # chromium | firefox | webkit
    video: false                       # record video of E2E tests
    video_on_failure_only: true        # save video only when test fails
  coverage:
    tool: auto                         # auto-detect | coverage.py | istanbul | c8
    minimum: 60                        # % minimum code coverage (Hard guardrail)
  environment:
    db_test: auto                      # auto | sqlite-memory | docker-postgres | none
    mocks: auto                        # auto-detect mock needs
```

**Documentation as first-class artefact:** Documentation tasks (`artefact_type: doc`) follow the same lifecycle as code — planned, produced in a worktree branch (`gse/sprint-NN/docs/<name>`), reviewed, and delivered. The agent can auto-generate API documentation from code (e.g., docstrings → reference docs) during `/gse:produce` when the TASK has `artefact_type: doc`.

> **Mono-repo assumption:** GSE-One manages a single repository at a time. For multi-component projects, a mono-repo is recommended. If you use multiple repos, run GSE-One independently in each repo.

### 13.2 Lightweight Mode

For micro-projects (single file, 1-hour task, quick script), the full lifecycle is overkill. GSE-One supports a **lightweight mode** that reduces overhead while preserving traceability:

```yaml
lifecycle:
  mode: lightweight                    # full | lightweight
```

**Auto-detection:** If `.gse/` does not exist and the project has < 5 files, the agent proposes lightweight mode automatically (Inform tier — user can override to full).

| Aspect | Full mode | Lightweight mode |
|--------|-----------|-----------------|
| Lifecycle | LC01 → LC02 → LC03 | PLAN → PRODUCE → DELIVER |
| Git strategy | worktree (sprint + feature branches) | branch-only (single feature branch, no sprint branch) |
| Sprint artefacts | Full set (plan, reqs, design, tests, review, compound) | Plan only (inline, no separate file) |
| Health dashboard | 8 dimensions | 3 of 8 (test_pass_rate, review_findings, git_hygiene — minimum for any project) |
| Complexity budget | Tracked | Not tracked |
| Decision tiers | Full P7 assessment | Simplified (Auto + Gate only, no Inform) |

The user can switch from lightweight to full mode at any time via `/gse:go` — the agent will scaffold the missing `.gse/` structure.

**Minimum viable project size:** GSE-One is designed for projects that evolve over multiple sessions. For truly one-off tasks (a single script, a quick fix, a configuration change), using GSE-One adds more overhead than value. In such cases, work without GSE-One and consider adopting it later if the project grows.

### 13.3 Team Usage

For projects with multiple developers, GSE-One adapts its state management:

**Per-user profiles:** In a team, each developer has their own HUG profile:

```
.gse/
├── profiles/
│   ├── alice.yaml               # Alice's expertise, language, learning goals
│   └── bob.yaml                 # Bob's expertise, language, learning goals
├── profile.yaml                 # Fallback for solo mode (symlink to active user)
└── ...
```

**User detection (in priority order):**
1. If `.gse/current-user` file exists → use its content
2. If `GSE_USER` environment variable is set → use its value
3. If `git config user.name` returns a value → use it
4. If none → ask the user (Inform: "Who are you?")

**Matching:** Username is matched against filenames in `.gse/profiles/` (case-insensitive, spaces replaced by hyphens). If no match → propose creating a new profile.

**Role assignment in plans:** Sprint tasks can be assigned to team members:

```yaml
- id: TASK-003
  title: Implement user authentication
  assignee: alice                # optional — team member responsible
  reviewer: bob                  # optional — team member who will review
```

**Shared vs. personal:** Configuration, decisions, and sprint artefacts are **shared** (committed). Checkpoints are **personal** (gitignored).

**Concurrent access:** When multiple team members work on the same project:
- Each member works in their own worktree/branch — no file-level conflicts during production
- `.gse/backlog.yaml` may be modified concurrently. Git merge handles this at commit level. If a conflict occurs, the agent detects it on next pull and proposes resolution (Gate: keep mine / keep theirs / merge manually)
- `.gse/decisions.md` is append-only — concurrent additions don't conflict
- Each member's checkpoint is in their own profile — no conflict

### 13.4 Non-Code Projects

GSE-One can be used for documentation, research, or configuration projects by disabling irrelevant dimensions:

```yaml
# .gse/config.yaml for a documentation project
project:
  domain: "documentation"

lifecycle:
  phases:
    LC02:
      tests: false
      preview: true
      design: false

health:
  disabled_dimensions:
    - test_pass_rate
    - design_debt
```

The health dashboard adapts: disabled dimensions are excluded from the score computation (the score is computed from the remaining active dimensions).

---

## 14. Standard Activity Groups (Lifecycle Phases)

> **Key principle:** PLAN is not locked to a single phase. It appears explicitly in LC01 and LC02 but can be invoked **at any moment within any phase** when planning decisions are needed — at any abstraction level from strategic to micro-task.

| Phase | Name | Typical Flow | Notes |
|-------|------|--------------|-------|
| **LC00** | Onboarding | `HUG` | Run once, update as needed. Initializes `.gse/` and verifies git. |
| **LC01** | Discovery & Planning | `GO > COLLECT > ASSESS > PLAN` | PLAN creates sprint branch. COLLECT can scan external sources. |
| **LC02** | Development Sprint | `REQS > DESIGN > PREVIEW > TESTS > PLAN > PRODUCE > REVIEW > FIX > DELIVER` | PRODUCE creates feature branches + worktrees. REVIEW uses branch diffs. DELIVER merges and tags. |
| **LC03** | Capitalization | `COMPOUND > INTEGRATE` | Post-sprint learning loop. Runs on `main` after delivery. Natural moment for proactive LEARN proposals. |

### Cross-Cutting Activities

Available at any time, outside of phase sequencing:

| Activity | Command |
|----------|---------|
| Planning (any level) | `/gse:plan` |
| Backlog management | `/gse:backlog` |
| Learning (reactive + proactive) | `/gse:learn` |
| Health dashboard | `/gse:health` |
| Project status | `/gse:status` |
| Session pause | `/gse:pause` |
| Session resume | `/gse:resume` |
| Ad-hoc task | `/gse:task` |

### Lifecycle Flow

```
LC00 (once)
  │  verify git, init .gse/, create .gitignore for .worktrees/
  v
┌─── LC01: Discovery & Planning ──────────────────────────┐
│    GO > COLLECT > ASSESS > PLAN                         │
│    PLAN creates sprint branch: gse/sprint-NN           │
│         ↑ PLAN callable at any point                    │
└──────────────────────────────────────┬──────────────────┘
                                       │
                                       v
┌─── LC02: Development Sprint ────────────────────────────┐
│    REQS > DESIGN > PREVIEW > TESTS > PLAN >             │
│    PRODUCE > REVIEW > FIX > DELIVER                     │
│                                                          │
│    PRODUCE: branch + worktree per task                   │
│    REVIEW: diff-based on feature branch                  │
│    FIX: fix branch from reviewed branch                  │
│    DELIVER: merge → sprint → main, tag, cleanup          │
│                                                          │
│         ↑ PLAN callable at any point                    │
│         ↑ HEALTH viewable at any point                  │
│         ↑ Guardrails active throughout                  │
│         ↑ Git guardrails protect main                   │
└──────────────────────────────────────┬──────────────────┘
                                       │
                                       v
┌─── LC03: Capitalization ────────────────────────────────┐
│    COMPOUND > INTEGRATE                                 │
│    (runs on main, after delivery)                       │
└──────────────────────────────────────┬──────────────────┘
                                       │
                                       v
                              next sprint → LC01

Cross-cutting (available at any point):
  PLAN, LEARN, HEALTH, STATUS, PAUSE, RESUME, TASK
```

### 14.1 Sprint 1 vs Sprint N+1

The `/gse:go` orchestrator adapts its flow depending on project maturity:

| Aspect | Sprint 1 (new project) | Sprint N+1 (continuing) |
|--------|----------------------|------------------------|
| **COLLECT** | Internal finds nothing (or very little). Agent suggests external source scan. | Internal finds existing artefacts, previous sprint results. |
| **ASSESS** | Starts from project goals only. No baseline to compare against. | Compares against previous sprint health, reviews, and delivery. |
| **PLAN** | Creates sprint branch from `main`. No previous velocity data. Agent asks more Gate questions about scope. | Uses previous sprint velocity to calibrate budget. Detects unfinished tasks from previous sprint. |
| **HUG** | Full interview (all 11 dimensions). | Asks only if profile needs updating ("Anything changed since last time?"). |
| **LEARN** | Frequent proactive proposals — the user encounters many new concepts. | Targeted — only for competency gaps detected in the previous sprint. |

### 14.2 Adopting GSE-One on an Existing Project

When `/gse:go` detects that `.gse/` does not exist but the project already has code, tests, or documentation, it enters **adopt mode** (also available via `/gse:go --adopt`):

1. **Scan** — Run `/gse:collect` (internal) to inventory all existing artefacts.
2. **Infer state** — Examine git history to estimate: how many sprints of work exist? What was the last stable release? Are there lingering branches?
3. **Initialize** — Create `.gse/` with reasonable defaults inferred from the scan (project domain from dependencies, git strategy from existing branch pattern).
4. **Propose annotation** — Offer to add YAML frontmatter to existing artefacts (Gate decision — the user may not want to modify existing files).
5. **Set baseline** — Record current state as "sprint 0" — the starting point for the first GSE-managed sprint.
6. **Proceed** — Transition to normal LC01 flow for sprint 1.

The adopt flow is designed to be **non-destructive**: it never modifies existing files without explicit user approval, and it can be interrupted and resumed.

### 14.3 Orchestrator Decision Logic (`/gse:go`)

When invoked, `/gse:go` follows this decision tree:

**Step 1 — Detect project state:**

| Condition | Action |
|-----------|--------|
| `.gse/` does not exist + project has files | Enter **adopt mode** (14.2) |
| `.gse/` does not exist + project is empty | Enter **HUG** (LC00) |
| `.gse/` exists | Read `status.yaml` → proceed to Step 2 |

**Step 2 — Recovery check:**

If `.gse/` exists, scan for unsaved work from a previous session that ended without `/gse:pause`:
- Check all active worktrees and the main directory for uncommitted changes
- If found: present a Gate decision — recover (auto-commit), review the diff first, discard, or skip
- If nothing found: proceed silently

**Step 3 — Determine next action:**

| Current state | Next action |
|--------------|-------------|
| No sprint exists AND `it_expertise: beginner` AND new project | Enter **intent-first mode** (Step 6) |
| No sprint exists | Start LC01 (GO > COLLECT > ASSESS > PLAN) |
| Sprint exists, plan not approved | Resume PLAN |
| Sprint exists, tasks in-progress | Resume PRODUCE on current task |
| Sprint exists, tasks done, not reviewed | Start REVIEW |
| Sprint exists, review done, fixes pending | Start FIX |
| Sprint exists, all tasks delivered | Start LC03 (COMPOUND > INTEGRATE) |
| Sprint exists, compound done | Propose next sprint → LC01 |
| Sprint stale (> `lifecycle.stale_sprint_sessions` sessions without progress) | Stale detection (Step 4) |

**Step 4 — Stale sprint detection:**

```
**Question:** Sprint N has had X sessions without progress. What would you like to do?

> A "session" is an invocation of `/gse:go` or `/gse:resume`. A "progression" is any TASK moving from one status to the next (open→planned, planned→in-progress, in-progress→done, etc.). The counter resets when any TASK progresses.

**Options:**
1. Resume — pick up where we left off
2. Partial delivery — deliver completed tasks, defer the rest to backlog pool
3. Discard — abandon the sprint, move all tasks back to pool, delete branches
4. Discuss
```

**Step 5 — Failure handling:**

If an activity fails (test failure, merge conflict, tool error):
1. Save current state to checkpoint
2. Report the error with the agent's assessment of the cause
3. Propose options (Gate): retry, skip (if skippable), pause, discuss
4. Never silently continue after a failure

**Step 6 — Intent-first mode (beginner + new project):**

When `it_expertise: beginner` and no sprint exists yet, the orchestrator enters a conversational mode before the formal lifecycle:
1. Elicit intent in plain language: *"Describe what you'd like to build or achieve."*
2. Reformulate and validate: *"If I understand correctly, you want: [list]. Correct?"*
3. Translate to initial backlog items (no jargon)
4. Transition to LC01, presenting each activity in plain language (e.g., COLLECT → *"Let me look at what we have to work with"*)
5. The user can exit intent-first mode at any time by saying *"I know the process"* — the agent switches to normal orchestration and updates the profile

```yaml
# In config.yaml → lifecycle:
  stale_sprint_sessions: 3            # sessions without progress before stale detection
```

---

## 15. Glossary

| Term | Definition |
|------|------------|
| **GSE-One** | Generic Software Engineering One — the methodology and plugin name |
| **Artefact** | Any project file: code, requirements, test, design document, plan, decision, configuration |
| **Sprint** | A complexity-budgeted iteration producing one or more artefact increments. Ends when budget is consumed or tasks delivered, not by calendar |
| **FR** | Functional Requirement |
| **NFR** | Non-Functional Requirement |
| **SDLC** | Software Development Life Cycle |
| **Simplification credit** | Negative complexity points earned by removing unused dependencies, dead abstractions, or consolidating configurations |
| **HUG** | Human User Grounding — the user profiling and context-setting activity |
| **Traceability** | The ability to link any artefact to its origin artefacts and dependents |
| **Validation gate** | A human-in-the-loop checkpoint between activities where the user confirms readiness to proceed |
| **Decision tier** | Classification of a decision by reversibility and impact: Auto, Inform, or Gate |
| **Consequence horizon** | Projection of an option's impact at three time scales: now, 3 months, 1 year |
| **Complexity budget** | Finite capacity for new complexity within a sprint, measured in points |
| **Composite risk** | When 3 or more risk dimensions are Moderate, the decision escalates to Gate tier — multiple moderate risks compound |
| **Guardrail** | Agent-initiated protection against high-cost decisions, calibrated by user expertise |
| **Health score** | Composite metric (0–10) reflecting project quality across 8 dimensions |
| **Preview** | Lightweight simulation of a planned artefact before production begins |
| **Decision journal** | Persistent log of all non-trivial decisions with rationale and consequence analysis |
| **Sprint branch** | Git branch `gse/sprint-NN` that collects all feature branches for a sprint |
| **Feature branch** | Git branch `gse/sprint-NN/type/name` where a single task is developed |
| **Worktree** | Isolated working directory linked to a branch, allowing parallel work without branch switching |
| **Merge strategy** | How commits from a feature branch are integrated: squash, merge commit, or rebase |
| **Hook** | Event-driven behavior triggered automatically (e.g., auto-commit on pause, guardrail check on push) |
| **Hook suppression** | Temporarily disabling a hook with documented rationale — an Inform-tier decision logged in sprint activity |
| **Inventory** | The `.gse/inventory.yaml` file produced by `/gse:collect` — classifies all project artefacts by type, status, and completeness |
| **Learning note** | Persistent, reusable course note produced by `/gse:learn`, written in the user's language and grounded in the project context |
| **Competency map** | Lightweight tracking of concepts learned, sessions completed, and detected skill gaps, stored in the HUG profile |
| **External source** | A local project or remote repository (e.g., GitHub) scanned by `/gse:collect` for reusable elements |
| **Source registry** | Persistent log (`.gse/sources.yaml`) of all external sources evaluated, with reusability assessments and provenance links |
| **Provenance** | Traceability link from an imported artefact back to its original external source |
| **Lightweight mode** | Reduced lifecycle for micro-projects: PLAN → PRODUCE → DELIVER, no worktrees, minimal health tracking |
| **Adopt mode** | `/gse:go --adopt` — onboarding flow for existing projects, scans and initializes without destroying existing state |
| **Backlog** | Unified, ordered list of all work items (TASK). Items are either in the pool (unplanned) or assigned to a sprint. Syncs with GitHub Issues when enabled |
| **Planning debt** | Tracked item when planning is skipped under pressure — reviewed during next `/gse:compound` retrospective |
| **Pool** | Subset of the backlog containing unplanned items (`sprint: null`) — candidates for future sprints |
| **Artefact type** | Classification of what a TASK produces: code, requirement, design, test, doc, config, or import |
| **Mono-repo** | GSE-One assumes a single repository per project. Recommended for multi-component projects |
| **Confidence level** | Tag on every agent assertion: Verified (factually checked), High (established knowledge, not project-verified), Moderate (reconstructed from patterns), Low (uncertain) |
| **Verification gate** | Proof requirement for critical assertions — code must be executed, libraries must be installed, APIs must be confirmed |
| **Devil's advocate** | Adversarial self-review perspective activated during `/gse:review` — hunts hallucinations, challenges assumptions, checks temporal validity |
| **User pushback** | Mechanism that detects passive acceptance and proactively challenges the user to engage critically with decisions |
| **AI integrity** | Health sub-dimension measuring unverified assertions, hallucination findings, and user engagement level |
| **Test pyramid** | Distribution of test types (unit/integration/E2E/visual/acceptance) calibrated by project domain |
| **Test campaign** | A single execution of the test suite, producing a traceable report with results, coverage, and evidence |
| **Test evidence** | Screenshots, videos, and logs captured during test execution — visual proof that the application works |
| **Visual testing** | Automated screenshot capture and analysis during E2E tests, leveraging multimodal AI for defect detection |
| **Code coverage** | Percentage of code exercised by tests — tracked as a health sub-dimension |

---

## Appendix A — Activity Summary (Quick Reference)

```
ORCHESTRATION       /gse:go        /gse:status     /gse:health
SESSION             /gse:pause     /gse:resume
ONBOARDING          /gse:hug
LEARNING            /gse:learn     (reactive + proactive, cross-cutting)
BACKLOG             /gse:backlog   (unified work items, cross-cutting)
DISCOVERY           /gse:collect   /gse:assess
PLANNING            /gse:plan      (cross-cutting, any level, any time)
ENGINEERING         /gse:reqs      /gse:design     /gse:preview
                    /gse:tests     /gse:produce    /gse:deliver
QUALITY             /gse:review    /gse:fix
CAPITALIZATION      /gse:compound  /gse:integrate
AD-HOC              /gse:task
```

**Total: 22 commands** | Canonical prefix: `/gse:`

---

## Appendix B — Changelog

> **Note:** Versions 0.1.0 through 0.7.0 were developed during an intensive design session. The dates reflect the actual drafting period. Future versions will follow standard release cadence.

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-04-10 | Initial definition |
| 0.2.0 | 2026-04-10 | Added: DESIGN, DELIVER, traceability, storage conventions, configuration, expanded HUG, PLAN as cross-cutting, GO semantics, lifecycle flow |
| 0.3.0 | 2026-04-10 | Added: Decision tiers (P7), consequence horizons (P8), adaptive communication (P9), complexity budget (P10), guardrails (P11), health dashboard, decision journal, preview activity, HUG profile dimensions, guardrail calibration, cross-cutting activities table, quick reference appendix |
| 0.3.1 | 2026-04-10 | Renamed: canonical prefix to `/gse:`, storage dir to `.gse/`, metadata key to `gse:` |
| 0.4.0 | 2026-04-10 | Added: P12 (Version Control Isolation), P13 (Hooks), full git branching model with worktrees, merge strategy as Gate decision, git-specific guardrails, git hygiene in health dashboard, worktree state tracking, commit convention, branch naming convention, artefact ID allocation scheme. Moved Preview to own section. Added `gse.branch` to artefact metadata. Integrated git actions into all relevant activities. |
| 0.5.0 | 2026-04-10 | Renamed to GSE-One, `/gse:` prefix. P7+P8+P11 unified as risk analysis chain. P10 rewritten. P12 merge adapted to user expertise. P14 (Knowledge Transfer) + `/gse:learn`. Learning notes in `docs/learning/`. Extended `/gse:collect` with external sources. Provenance traceability. 20 commands. |
| 0.6.0 | 2026-04-10 | Major consolidation (see v0.6 changelog for details). |
| 0.9.0 | 2026-04-12 | **Conceptual framework.** Added §1.1 (Coding Agents and Plugin Architecture): abstract concepts (coding agent, agent, skill with inclusion policies, hook, template, tool), system prompt, subagents. Platform-specific sections for Claude Code and Cursor (execution loops, artifact delivery mechanisms, inclusion policy mapping). §1.1.3 GSE-One mono-plugin architecture mapping. **P13**: reclassified hooks — 7 hooks → 3 system hooks (protect main, block force-push, review findings on push) + 6 agent behaviors. Hooks rewritten as cross-platform Python commands with correct exit codes (exit 2 for blocking, stderr for feedback). **Config §13.1**: hooks section aligned (3 keys). **Cross-platform**: all documentation, templates, and examples neutralized for macOS/Linux/Windows. Added §1.5 Agent Roles to spec. |
| 0.8.0 | 2026-04-11 | **Implementation alignment pass.** TIME→COMPLEXITY: replaced `stale_sprint_days` with `stale_sprint_sessions` (Sections 13.1, 14.3), Sprint redefined as complexity-budgeted (not time-boxed) in Key Concepts and Glossary. **P4**: added "no implicit consent" and "escalation when uncertain" rules. **P5**: added 4-level planning taxonomy, 5 re-planning triggers, planning debt concept. **P6**: replaced flat `traces: []` with 4 typed trace links (`derives_from`, `implements`, `decided_by`, `related_to`) + bidirectional consistency rule — cascaded to all YAML examples (Sections 4.6, 6.3, 12.2, 12.3). **P7**: added composite risk rule (3+ Moderate = Gate), unknowns-default-to-High rule. **P8**: added confidence flagging on consequence projections, "no false certainty" rule. **P10/Section 8**: expanded complexity cost table (8→14 items), added sprint type budgets (15/12/8), complexity debt, simplification credit, zero-cost items. **P13**: expanded hooks (4→7 types), added hook suppression and failure handling. **Section 4**: added `inventory.yaml` as COLLECT output, "Reference only" as 4th reusability option. **Section 4.7**: added GAP-NN identifiers for assess gaps. **Section 7**: added computation formulas for all 8 health dimensions, alert threshold (< 7/10), replaced "12 days" with ">2 sprints". **Section 12.4**: added P16 tracking fields (never_discusses, terse_responses, never_modifies, never_questions), sessions_without_progress, review_findings_open. **Section 15**: added 5 glossary terms (composite risk, hook suppression, inventory, planning debt, simplification credit). |
| 0.7.0 | 2026-04-11 | **41-issue fix pass.** CRITICAL: fixed health dim count (7→8 everywhere), removed infeasible timing detection in P16. HIGH: added /gse:go decision logic (14.3) with stale sprint detection, safety/recovery mechanism (10.6) with backup tags, visual testing best-effort caveat (6.3), status.yaml schema (12.4), checkpoint schema (12.5), state loading priority (12.6), assess methodology (4.7), doc-as-first-class artefact, audience note for beginners. MEDIUM: 13.1 config section, P11 dedup, complexity ranges, team matching algorithm, concurrent access, tech stack drift detection, hooks config, health config, dependency audit, min project size note, ad-hoc task lifecycle. LOW: category headers, TOC fixes, artefact spelling, Discuss standardization, changelog note. | **Overview** rewritten (7 pillars + Key Concepts). **Unified backlog** (`/gse:backlog`, TASK as single ID, git state per-TASK). **AI Integrity** (P15 confidence levels/verification gates/source citation, P16 devil's advocate/user pushback). **Testing Strategy** (Section 6): test pyramid by domain, environment auto-setup, visual testing with screenshots/video, test campaign reports as traced artefacts, coverage model (code + requirements + risk), expertise-adapted testing behavior. **Health** expanded to 8 dimensions (+AI integrity). `testing` config section. `tests/evidence/` in project layout. `test-campaign` artefact type. TOC, principle grouping (4 categories, 16 principles). Adopt mode, lightweight mode, team profiles, non-code config, mono-repo, GitHub sync, COMPOUND 3 axes. 15 sections, 22 commands, 8 health dimensions. |
