# GSE-One — Generic Software Engineering One

**Aliases:** `gse`, `gse-one`, `gseone`

> **Audience:** This document is the **technical specification** for GSE-One, intended for implementers and advanced users who want to understand the methodology in detail. If you are a **new user**, you don't need to read this — just type `/gse:go` and the agent will guide you through everything adaptively.

---

## 0. Getting Started

### 0.1 Prerequisites

GSE-One assumes the following baseline knowledge. You don't need to be an expert — basic familiarity is sufficient:

- **Terminal / CLI** — You can open a terminal, navigate directories, and run commands
- **Git basics** — You understand commits, branches, and push/pull (GSE-One handles the advanced parts for you)
- **Text files** — You can read and edit Markdown and YAML files (GSE-One generates most of them)
- **Agile concepts** (optional) — Knowing what a sprint, backlog, or user story is helps but is not required — GSE-One explains these progressively

**No programming language knowledge is required.** GSE-One adapts to your project's language and your expertise level.

### 0.2 Quickstart — Your First 20 Minutes

Here is what a typical first session looks like. You type one command; the agent handles the rest:

```
You:   /gse:go

Agent: I don't see a project set up yet. Let me get to know you first.
       What language do you prefer for our conversations?

You:   French

Agent: [... 4-5 profiling questions: your role, experience, what you want to build ...]

You:   I want to build a personal expense tracker as a web app. I'm a beginner.

Agent: Great! Here's what I'll do:
       1. I'll organize the work into a first cycle (sprint)
       2. I'll write down what the app should do and ask you to confirm
       3. I'll build it step by step, checking my work as I go
       4. I'll deliver the result when everything is verified

       Ready to start? I'll begin by planning the work.

You:   Yes

Agent: [Plans sprint → Writes requirements → Asks for confirmation →
        Designs architecture → Creates tests → Produces code →
        Reviews own work → Fixes issues → Delivers]
```

**Key commands you'll use:**
- `/gse:go` — Start or continue (the agent figures out what to do next)
- `/gse:status` — See where you are
- `/gse:health` — Check project quality dashboard
- `/gse:pause` — Save and stop (you can resume later with `/gse:go`)

Everything else is handled by the agent based on your profile and project state. Advanced users can invoke any of the 23 commands directly (see Section 3).

---

## Table of Contents

0. [Getting Started](#0-getting-started) — Prerequisites, Quickstart (your first 20 minutes)
1. [Overview](#1-overview) — Coding agent architecture, agile foundations, platform mapping, GSE-One philosophy, key concepts, agent roles
2. [Core Principles](#2-core-principles) — Foundations (P1-P3, P5-P6) | Risk & Communication (P4, P7–P11) | Infrastructure (P12–P14) | AI Integrity (P15–P16)
3. [Activities (Commands)](#3-activities-commands) — 23 commands across 9 categories
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
B. [Maintainer Guide](#appendix-b)

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

GSE-One delivers its methodology as a **single plugin directory** (`plugin/`) that works on Claude Code, Cursor, and opencode. Shared artifacts (skills, agents, templates) are identical across platforms. Platform-specific artifacts coexist in the same directory — each platform loads only the files it recognizes and silently ignores the rest.

| Artifact | Files | Claude Code | Cursor | opencode |
|----------|-------|:-----------:|:------:|:--------:|
| Skills (23) | `skills/<name>/SKILL.md` | Loaded | Loaded | Via `opencode/skills/` |
| Specialized agents (8) | `agents/<name>.md` | Loaded | Loaded | Via `opencode/agents/` (`mode: subagent`) |
| Orchestrator (identity) | `agents/gse-orchestrator.md` | Via `settings.json` → `"agent"` | Not installed | Not installed |
| Orchestrator (identity) | `rules/gse-orchestrator.mdc` | Ignored | `alwaysApply: true` | Ignored |
| Orchestrator (identity) | `opencode/AGENTS.md` | Ignored | Ignored | Loaded (always-on, worktree root) |
| Commands (23) | `commands/gse-<name>.md` | Ignored | Loaded | Via `opencode/commands/` |
| Templates (15) | `templates/*` | Loaded | Loaded | Shared via registry tools |
| Hooks (3) | `hooks/hooks.claude.json` | Loaded | Ignored | Ignored |
| Hooks (3) | `hooks/hooks.cursor.json` | Ignored | Loaded | Ignored |
| Hooks (3) | `opencode/plugins/gse-guardrails.ts` | Ignored | Ignored | Native TS plugin |
| Manifest | `.claude-plugin/plugin.json` | Loaded | Ignored | Ignored |
| Manifest | `.cursor-plugin/plugin.json` | Ignored | Loaded | Ignored |
| Config | `opencode/opencode.json` | Ignored | Ignored | Deep-merged by installer |
| Settings | `settings.json` | Loaded | Ignored | Ignored |

Note: "orchestrator" is a GSE-One convention. The orchestrator body is identical on all three platforms — only the delivery mechanism differs. On Claude Code, it is the session's default agent (`agents/gse-orchestrator.md` referenced by `settings.json`). On Cursor, it is an always-on rule (`rules/gse-orchestrator.mdc`). On opencode, it is the `AGENTS.md` body at the worktree root (or `~/.config/opencode/AGENTS.md` in plugin mode), wrapped between `<!-- GSE-ONE START -->` / `<!-- GSE-ONE END -->` markers so the installer can merge/replace surgically without disturbing user content. The installer excludes `gse-orchestrator.md` from Cursor's and opencode's `agents/` directories to avoid double-loading.

### 1.2 Agile Software Engineering Foundations

This section defines the agile engineering principles that underpin GSE-One. Understanding these foundations is essential because GSE-One is not a generic tool — it is an opinionated methodology that adapts agile practices for the solo developer + AI agent context.

#### Why agile?

Traditional software development (waterfall) follows a sequential process: gather all requirements → design everything → build everything → test everything → deliver. Each phase completes before the next begins. This fails in practice because requirements change, designs have flaws only visible during implementation, and late testing discovers issues that are expensive to fix.

Agile methodologies solve this by working in **short iterations** (sprints) where each cycle delivers a working increment of the product. Feedback is gathered early and often, and the plan adapts to what is learned. The Agile Manifesto (2001) summarizes this as four values:

1. **Individuals and interactions** over processes and tools
2. **Working software** over comprehensive documentation
3. **Customer collaboration** over contract negotiation
4. **Responding to change** over following a plan

#### Core agile concepts

| Concept | Standard Definition |
|---|---|
| **Sprint** | A short iteration (typically 1-4 weeks) producing a working increment |
| **Product Backlog** | The ordered list of everything the product needs |
| **Sprint Backlog** | The subset of backlog items selected for a sprint |
| **User Story** | A requirement expressed as "As a [role], I want [goal], so that [benefit]" |
| **Acceptance Criteria** | Conditions that must be met for a story to be considered done |
| **Increment** | The sum of all completed work, integrated with prior increments |
| **Definition of Done** | The checklist an artefact must satisfy to be considered complete |
| **Retrospective** | A sprint-end reflection on process improvement |
| **Velocity** | The amount of work completed per sprint |

#### How GSE-One adapts agile for solo AI-assisted development

GSE-One inherits agile principles but adapts them for a context that standard agile (Scrum, XP, SAFe) does not address: a single developer working with an AI agent, not a team of humans.

| Agile standard | GSE-One adaptation | Why |
|---|---|---|
| Sprint = time-boxed (2 weeks) | Sprint = **complexity-boxed** (budget of points, no fixed duration) | A solo dev + AI has no fixed cadence; sessions vary in length |
| Product Owner (human role) | The **user** is the product owner | No organizational role separation needed |
| Scrum Master (human facilitator) | The **AI agent** is the facilitator | The agent guides the process, enforces guardrails, proposes next steps |
| Daily Standup (team sync) | **Recovery check** at each `/gse:go` | No team to sync; the agent checks for unsaved work instead |
| Sprint Review (stakeholder demo) | `/gse:review` with **devil's advocate** | The agent reviews its own work and challenges its own assumptions (P16) |
| Sprint Retrospective (process improvement) | `/gse:compound` (3 axes: project, methodology, competencies) | Deeper than a retrospective — includes knowledge transfer and methodology feedback |
| User Stories | **Test-driven requirements** (REQ- with Given/When/Then acceptance criteria) | Acceptance criteria = validation test specifications, ensuring every requirement is testable |
| Definition of Done (manual checklist) | **Lifecycle guardrails** (REQS → TESTS → PRODUCE → REVIEW, automatically enforced) | No manual checklist — the agent blocks progression if prerequisites are missing |
| Velocity (story points per sprint) | **Complexity points** consumed per sprint | Same concept, measured in complexity cost rather than abstract story points |
| Pair Programming (XP) | **Human + AI agent** collaboration | The agent is the permanent pair partner, adapting its level of autonomy to the user's preference |

#### What GSE-One adds beyond standard agile

| GSE-One original | Purpose | Not found in standard agile |
|---|---|---|
| **AI integrity** (P15, P16) | Protect the user from hallucinations, complaisance, and outdated knowledge | Agile assumes human practitioners don't hallucinate |
| **Adaptive communication** (P9) | Translate jargon to the user's level; beginner output filter | Agile assumes shared vocabulary among team members |
| **Consequence horizons** (P8) | Evaluate decisions at 3 time scales (Now, 3 months, 1 year) | Agile focuses on the current sprint, not multi-horizon impact |
| **Complexity budget** (P10) | Finite budget per sprint preventing scope creep via measurable cost | Agile uses velocity as a trailing indicator, not a forward constraint |
| **Progressive knowledge transfer** (P14) | Agent teaches the user during work, with mastery tracking | Agile expects pre-existing expertise or external training |
| **Spike mode** | Complexity-boxed experiments bypassing REQS/TESTS guardrails | XP has spikes, but without formal guardrail bypass or complexity caps |
| **Three project modes** (Micro/Lightweight/Full) | Scale ceremony to project complexity (assessed from structural signals, not file count) | Agile methodologies are typically one-size (Scrum) or customizable but heavy (SAFe) |

### 1.3 GSE-One Overview

GSE-One (Generic Software Engineering One) is an AI engineering companion that guides users through the full software development lifecycle. It is implemented as a plugin for AI coding agents (Claude Code, Cursor, or any compatible agent-based IDE) and provides 23 commands covering planning, requirements, design, production, quality, delivery, deployment, and capitalization.

GSE-One is designed for users of **any expertise level** — from beginners building their first project to experienced engineers managing complex applications. The agent adapts its language, decisions, and level of autonomy to the user's profile, and progressively transfers knowledge so the user grows alongside the project.

The canonical command prefix is **`/gse:`**.

> **Note:** All artefact metadata (YAML frontmatter), git operations, and state management are handled automatically by the GSE-One agent. Users focus on intent and validation — the agent handles the mechanics.

### 1.4 Design Philosophy

GSE-One is built for a fundamental asymmetry: the **user has the intent** but the **agent has the technical depth**. The methodology bridges this gap through seven pillars:

1. **Risk-aware decision making** — Every decision is assessed across multiple dimensions (quality, cost, time, security, scope). Low-risk decisions are automated; high-risk decisions are presented with consequence horizons so users can evaluate trade-offs through concrete impact, not abstract technicality. (P7→P8→P11)

2. **Unified backlog** — All work items live in a single, ordered backlog. Items flow from pool (ideas) to sprint (committed) to delivered, with full traceability. The sprint plan (`.gse/plan.yaml`) is a living, filtered view of the backlog that the orchestrator maintains throughout the sprint. It tracks workflow state, budget consumption, and coherence — never a static document. GitHub Issues are synchronized when available. (Section 3.4, 12.3)

3. **Version control isolation** — Every task is developed in its own git worktree, branched from the sprint branch. The `main` branch is always stable. Merges are formal decisions with user validation. The user never needs to learn git commands — the agent handles branching, merging, and cleanup transparently. (P12)

4. **Adaptive knowledge transfer** — The agent acts as a tutor alongside its engineering role. It inserts contextual explanations during activities, proposes learning sessions at natural workflow transitions, and produces persistent learning notes grounded in the user's actual project. As the user learns, the agent progressively steps back. (P14)

5. **External source reuse** — Projects can bootstrap from existing code, whether from the user's other projects or from public repositories. The agent scans, evaluates compatibility, and imports with full provenance traceability. (Section 4)

6. **Methodology self-improvement** — During capitalization (end of sprint), the agent consolidates methodology observations accumulated during the sprint (from review findings tagged `[METHOD-FEEDBACK]`, decisions marked as `type: methodology-deviation`, `status.yaml → activity_history` notes, and conversation context) and offers them back to the user through a **3-option Gate** at the end of COMPOUND Axe 2: *(1) Export as a local feedback document only* — producing a shareable sprint-scoped methodology-feedback artefact the user can send through any channel; *(2) Propose GitHub tickets* — curated, theme-grouped, deduplicated against existing issues, capped by `compound.max_proposed_issues_per_sprint` (default 3), each validated individually by the user before upstream submission via `/gse:integrate` Axe 2; *(3) Both* — export AND propose tickets. **Quality rules** (applied to the ticket path): every proposal must (a) cite at least one concrete example from the sprint (file, timestamp, user quote, or artefact ID), (b) be theme-grouped (one ticket per theme, never per micro-friction), (c) deduplicated against open issues in the upstream repo when `gh` is available (fallback: flag "dedup unverified" if unavailable), (d) respect the per-sprint cap, (e) presented to the user as a per-ticket Gate for validation. Rationale: the methodology evolves best through **curated, high-signal feedback** — not through ticket spam. Users who prefer a lighter channel (email, chat, manual issue) get the local export without any GitHub interaction.

7. **AI integrity safeguards** — The agent is a generative AI with inherent limitations (hallucinations, complaisance, outdated knowledge). GSE-One protects the user from these failures through explicit confidence levels on every recommendation, verification gates for critical assertions, adversarial self-review (devil's advocate), source citation, and active encouragement of user pushback when passive acceptance is detected. (P15, P16)

### 1.5 Key Concepts

| Concept | Summary |
|---------|---------|
| **Sprint** | A complexity-budgeted iteration. All work is organized in sprints. A sprint ends when its complexity budget is consumed or all tasks are delivered — not by calendar. |
| **Backlog** | The single list of all work items (TASK). Unplanned items are in the pool; planned items are in a sprint. |
| **Artefact** | Any project deliverable: code, requirements, design, tests, documentation, learning notes. |
| **Decision tier** | Every decision is classified as Auto (agent decides), Inform (agent decides + explains), or Gate (user must validate). |
| **Guardrail** | Protection against high-consequence actions. Three levels: Soft (warn), Hard (block until override), Emergency (halt until risk acknowledgment). |
| **Health score** | A 0–10 composite metric reflecting project quality across 8 dimensions. |
| **Worktree** | An isolated working directory per task — the user and agent can work on multiple tasks in parallel without interference. |
| **Learning note** | A persistent, reusable course note written by the agent in the user's language, grounded in the project context. |
| **Mono-repo** | GSE-One manages one repository at a time. Multi-component projects should use a mono-repo. |
| **Confidence level** | Every agent recommendation carries a confidence tag: Verified, High, Moderate, or Low. |
| **Devil's advocate** | During review, the agent challenges its own productions — hunting hallucinations, unverified claims, and missing alternatives. |
| **Verification** | A test that confirms the code is built correctly — "build the thing right". Traces to DES- (design decisions, interfaces, data contracts). Typical levels: unit, integration. |
| **Validation** | A test that confirms the code does what the user asked for — "build the right thing". Traces to REQ- (acceptance criteria). Typical levels: acceptance, E2E, visual. |

### 1.6 Agent Roles

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

**Interactive mode (preferred when available):** When the hosting environment provides an interactive question tool (e.g., `AskUserQuestion` in Claude Code, clarifying questions in Cursor), the agent SHOULD use it instead of the text-based numbered list. This provides a better UX with clickable options, checkboxes for multi-select, and skip buttons. The structured content (Question, Context, Options, Discuss) remains the same — only the presentation changes from text to interactive widget. When the interactive tool is unavailable or the number of options exceeds its limits, fall back to the text format above.

**No implicit consent:** Silence or lack of response is NOT consent for Gate-tier decisions. If the user does not respond, the agent waits or works on other non-blocked tasks. The agent never assumes approval.

**Escalation when uncertain:** If the agent is uncertain about the risk tier of a decision, it MUST escalate to Gate tier. It is always safe to ask; it is never safe to assume.

### P5 — Planning at Every Level
Planning is a cross-cutting activity, not bound to a single lifecycle phase. It can be invoked at any abstraction level — from strategic sprint scoping down to micro-task ordering within a single activity. Whenever a decision about what to do next, in what order, and with what scope is needed, PLAN is the appropriate activity. See Section 14 (cross-cutting activities) for its position in the lifecycle.

**Four planning levels:**

| Level | Scope | Artefact | Approval tier |
|-------|-------|----------|---------------|
| **Project** | Multi-sprint roadmap, major goals | Project backlog | Gate |
| **Sprint** | What to deliver this sprint, complexity budget, workflow tracking | `.gse/plan.yaml` (living) → `docs/sprints/sprint-NN/plan-summary.md` (archive at delivery) | Gate (creation), Auto (updates) |
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
| `TCP-` | Test campaign report (execution event) | TCP-007 |
| `RVW-` | Review finding | RVW-005 |
| `DEC-` | Decision | DEC-008 |
| `TASK-` | Work item (backlog + sprint tasks — unified) | TASK-014 |
| `INT-` | Project intent | INT-001 |
| `OQ-` | Open question (pending resolution) | OQ-003 |
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
| `spike` | Exploratory experiment — throwaway code to answer a technical question. **Complexity-boxed** (max 3 points). **Non-deliverable** — cannot be merged to main. Must produce a DEC- artefact documenting the question, approach, and answer. Bypasses REQS and TESTS guardrails. If the spike yields reusable code, a normal TASK must be created to implement it properly with REQS/TESTS. For beginners: Gate confirmation required ("This is an experiment — the code won't be kept. Are you sure?"). |

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

**Open Questions — structured traceability of pending ambiguities:** any artefact (intent, requirements, design, etc.) may contain an `## Open Questions` section listing ambiguities that cannot be resolved immediately. Each question carries structured fields to enable automatic routing and resolution downstream:

| Field | Values | Meaning |
|-------|--------|---------|
| `id` | `OQ-NNN` | Unique within the project (see table above). |
| `question` | free text | The question in plain language. |
| `resolves_in` | `ASSESS` \| `PLAN` \| `REQS` \| `DESIGN` | The lifecycle activity where this question is logically resolved. Set by the agent (or user override). The activity-entry scan reads this field to know which questions it must address. |
| `impact` | `scope-shaping` \| `behavioral` \| `architectural` \| `cosmetic` | Sizing/priority tag. `scope-shaping` changes the size of ≥ 1 task and is what triggers a scope-resolve preflight at PLAN entry. `behavioral` affects REQS acceptance criteria. `architectural` affects DESIGN decisions. `cosmetic` is low-priority (UI, docs, naming). |
| `status` | `pending` \| `resolved` | Lifecycle status. Transitions from `pending` to `resolved` when the responsible activity processes it. |
| `raised_at` | artefact ID | The artefact that originally raised the question (e.g., `INT-001`, `ASS-002`). Preserves provenance. |
| `resolved_at` | ISO-8601 timestamp | Set when the question is resolved. |
| `resolved_in` | activity name | The activity that actually resolved the question (may differ from `resolves_in` if the user chose to resolve earlier or later). |
| `answer` | free text | The resolution answer. |
| `answered_by` | `user` \| `agent` | Who produced the answer (respecting the `decision_involvement` mode). |
| `confidence` | P15 tag | `Verified` / `High` / `Moderate` / `Low`. |
| `traces` | list of IDs | Links to DEC-NNN or other artefacts produced as a consequence of the resolution. |

**Activity-entry scan (transversal rule):** at the very first step of each of the four lifecycle activities `/gse:assess`, `/gse:plan`, `/gse:reqs`, `/gse:design`, the agent scans the project's intent artefact and all active-sprint artefacts for open questions with `status: pending` AND `resolves_in: <current activity>`. If ≥ 1 match, the agent enters the **Open Questions Gate** before executing the activity's main work. The Gate behavior depends on the user's `decision_involvement` (HUG profile):

- **`autonomous`** — the agent proposes answers based on intent + project profile + GSE conventions and records them as Inform-tier with `answered_by: agent`. A Gate is raised only for questions tagged `impact: scope-shaping` or `impact: architectural` (high-impact cases that warrant explicit user approval).
- **`collaborative`** (default) — per-question or per-theme Gate: the agent proposes an answer with rationale + consequence horizons (P8), user validates or modifies. `answered_by: user` after confirmation.
- **`supervised`** — each question is a neutral Gate (no pre-answer), user provides the answer directly.

In all three modes, each resolution is **recorded in structured form** in the origin artefact's `## Open Questions` section (status flipped to `resolved`, all downstream fields populated). Substantial resolutions also produce a `DEC-NNN` in `decisions.md` with `traces.derives_from: [OQ-NNN]`. Resolutions with `impact: scope-shaping` propagate to `backlog.yaml` (task sizing update) and may trigger a `/gse:plan --tactical` if the current sprint plan is affected.

**Scope Reconciliation — creator-activity closure check:** at the end of every creator activity that produces code or executable artefacts (`/gse:produce`, `/gse:task`), the agent MUST present a **Scope Reconciliation** comparing what was planned (from the approved requirements and design of the current sprint) to what was actually delivered. The delivered set is derived **deterministically from the version-control history** between the activity's starting commit (recorded when the activity began) and its ending commit, cross-referenced with the per-commit `Traces:` trailer. Deltas are categorized as `ADDED out of scope` (delivered but not traceable to a planned REQ or DEC), `OMITTED` (planned but not delivered), or `MODIFIED beyond plan` (existing artefact changed in a way that introduces new user-visible behavior not in the plan). If any non-empty delta exists, the activity blocks at a Gate with four options: *(1) Accept as deliberate* (the agent records all ADDED items together as **a single grouped DEC-NNN** summarizing the additions by theme, preserving traceability; OMITTED items move to the backlog pool for a future sprint), *(2) Revert out-of-scope* (each ADDED item is undone), *(3) Amend requirements/design* (the agent appends a **lightweight REQ-NNN or DEC-NNN** to the current sprint's artefact to recognize the emergent scope, without re-running the full elicitation ceremony), *(4) Discuss* (per-delta mixed decisions). If deltas are empty, the Gate is skipped silently. **Exempt modes:** Micro mode (no formal plan) and `git.strategy: none` (no commit history to diff) skip this check entirely. Rationale: code delivered outside the approved scope bypasses human governance and erodes the "Built by AI, Governed by Humans" contract.

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

**Config Application Transparency (Inform-tier discipline):** whenever an activity **materializes** a project configuration choice — that is, performs a concrete action whose shape is determined by a `config.yaml` field with user-visible consequences (e.g., `git.strategy` creates worktrees/branches, `testing.coverage.minimum` sets a test gate, `git.tag_on_deliver` tags a release, etc.) — the agent MUST emit a **one-line Inform note** at the moment of materialization. The note names the field, its applied value, its origin (methodology default vs. user choice), and the path to change it. Rationale: the methodology defines many defaults that users have not explicitly validated, and silent application can lead to surprise (e.g., unexpected directory creation via worktrees). A single visible line at the moment of action respects the Inform tier — no interruption, but the user sees what is happening and can intervene. **Origin classification:** the agent compares the current config value to the methodology default (defined in the config.yaml template). Equal → *methodology default*. Different → *user choice* (via HUG update or manual edit). **Format:** *"Config applied: `<field>` = `<value>` (<origin> — to change: `/gse:hug --update` or edit `.gse/config.yaml`)"*. Adapted to P9 for beginners (plain-language translation of field names). **Scope for v0.30:** the rule is documented as a general discipline and implemented for `git.strategy` (the field first observed to cause surprise in training feedback). Additional fields are added as activities are updated — each activity lists the config fields it materializes in its spec.

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

**System dialog anticipation:** When the agent is about to trigger an action that will produce a system permission dialog (e.g., git init confirmation, file access request, terminal command approval), it MUST prepare the user before executing. For beginner users: explain what the dialog means and which button to click. For advanced users: no anticipation needed. This prevents beginners from being blocked by unexpected technical dialogs.

**Question cadence:** The number of questions asked simultaneously is proportional to IT expertise. Beginner: 1 question at a time. Intermediate: 2-3 grouped by theme. Advanced/Expert: all in one block. This applies across all skills.

**Beginner output filter:** When `it_expertise: beginner`, the agent applies a translation table to ALL chat output. Internal artefacts keep technical names — only chat is filtered. The user never needs to type `/gse:` commands; the agent proposes actions in plain language.

| Internal term | Beginner-visible term |
|---|---|
| `config.yaml` | "your project settings" |
| `backlog.yaml` | "your task list" |
| `status.yaml` | "the project progress tracker" |
| `profile.yaml` | "your preferences" |
| `.gse/` | "the project folder" |
| `TASK-001`, `TASK-002`... | "Step 1", "Step 2"... |
| `REQ-001`, `DES-001`... | hide IDs, use descriptive names |
| `sprint N` | "work cycle N" |
| `LC01`, `LC02`, `LC03` | hide — describe the activity instead |
| `/gse:collect` | "I'll look at what we have" |
| `/gse:assess` | "I'll figure out what's missing" |
| `/gse:plan` | "I'll organize the work" |
| `/gse:reqs` | "I'll write down what the app should do and ask you to confirm" |
| `/gse:design` | "I'll decide how to structure the app" |
| `/gse:tests --strategy` | "I'll describe how we'll verify each feature works" |
| `/gse:produce` | "I'll build it" |
| `/gse:review` | "I'll check my work" |
| `/gse:fix` | "I'll fix what was found during review" |
| `/gse:deliver` | "I'll finalize the result" |
| `/gse:compound` | "I'll review what we learned" |
| `reqs.md` | "the description of what the app should do" |
| `test-strategy.md` | "the verification plan" |
| `design.md` | "the app structure decisions" |
| `acceptance criteria` | "how we'll know each feature is done" |
| `Gate decision` | "I need your decision" |
| `complexity budget` | "the amount of new things we can add" |
| `worktree` | "a separate workspace" |
| `merge` | "combine changes" |

**Output formatting:** Chat output uses **bold** for decisions and key terms, *italic* for file paths and references, bullet lists over tables (portability), code blocks for commands and YAML. Emoji usage is controlled by the `emoji` HUG dimension (default: on, at most one per message, never inside technical content).

### P10 — Complexity Budget
A sprint that accumulates too many features, dependencies, or architectural changes becomes unmanageable — tests are skipped, reviews are superficial, and defects slip through. Users rarely perceive this risk because each addition feels small in isolation, but complexity compounds.

To prevent this, each sprint has a **complexity budget** — a finite number of points representing the maximum amount of work the sprint can absorb.

**Definition of a complexity point.** One point measures **coupled effort and complexity for the AI + user pair** — the three tightly-linked factors a unit of work adds to the project: (1) code complexity added (maintenance risk, coupling), (2) AI generation effort (production + iteration), (3) human review effort (reading, validation, decisions). Because these factors are entangled in practice — complex code takes longer to generate AND requires more review AND raises future maintenance — a single scalar captures them adequately.

**Temporal anchor (indicative).** As a ballpark calibration: **1 point ≈ 1 pair-session hour** — one focused hour of AI generation + user review. A 10-point sprint therefore ≈ 1-3 working days of AI + user sessions. Solo human equivalent (without AI): 1 point ≈ 0.5-1 working day (speedup ratio typically 10×, varying 5-20× by domain: 15-20× on CRUD-standard work, 5-10× on unfamiliar-domain learning, 3-5× on algorithmic or research problems). The anchor is **indicative, not prescriptive** — spec §2 "Sprint = complexity-boxed, no fixed duration" is preserved. The ballpark helps users sense the size of their commitments; it is not a deadline.

Every planned task consumes points based on what it introduces (a new dependency costs 1–2 points, an architectural change costs 3–5). The agent tracks the running total and makes it visible throughout the sprint (see Section 8).

**Role in the methodology:**
- During **PLAN**, the agent evaluates whether planned tasks fit within the budget. If the total exceeds the budget, a Gate decision is presented (not Hard — complexity estimates are imprecise by nature): continue with overrun, reduce scope, defer to next sprint, or discuss. The budget is a directional tool, not a rigid constraint.
- During **PRODUCE**, if ad-hoc additions push the sprint over budget, the agent warns (Soft at 80%, Gate at 100%) before proceeding.
- During **HEALTH**, the budget consumption ratio is one of the 8 health sub-scores — a sprint at 90% budget is a risk signal.

The budget size is calibrated by project size and team context (via HUG). A solo beginner gets a smaller budget (fewer moving parts to manage); an expert team gets a larger one.

### P11 — Guardrails (Risk Mitigation and Traceability)
Guardrails are the enforcement mechanism of the P7→P8→P11 risk analysis chain. They ensure that high-consequence actions are formally validated by the user and traced in the decision journal. Guardrails make cost visible and require proportional acknowledgment: Soft guardrails warn without blocking; Hard guardrails block until the user provides a documented rationale for overriding; Emergency guardrails halt operations until explicit acknowledgment of risk. See Section 9 for levels, calibration by expertise, and git-specific guardrails.

**Infrastructure**

### P12 — Version Control Isolation
Every production task is performed in an isolated git environment. The `main` branch is always stable and deployable. Work is done on feature branches, each in its own git worktree. Merges are planned activities with Gate-tier validation.

**Core rules:**
0. **Foundational commit** — a newly initialized repository MUST have at least one commit on `main` before any branching operation. Without this, `main` is not a valid branch reference and `git checkout -b ... main` fails. This commit is created during HUG (Step 4) as part of git initialization. **Precondition:** a valid git identity (user name + email) must exist, either globally or scoped to the current repository, before any commit attempt — otherwise the commit fails. When the identity is missing, the **Git Identity Verification** invariant (see rule 6 below) MUST resolve it through a Gate before the foundational commit is attempted.
1. **`main` is sacred** — no direct commits after the foundational commit. All subsequent changes arrive via reviewed, approved merges.
2. **One branch per task** — each planned task gets its own branch, named predictably.
3. **Worktree isolation** — each branch is checked out in its own directory, so work on multiple tasks doesn't interfere.
4. **Merge is a decision** — every merge is a Gate-tier decision. The way the agent presents the merge options is adapted to the user's expertise (P9): a beginner sees a plain-language choice between "clean summary" vs. "full history"; an expert sees the technical options (squash, merge, rebase) with consequence horizons.
5. **Clean up after merge** — merged branches and worktrees are deleted to prevent sprawl.

6. **Git Identity Verification (Hard, all modes)** — Any activity about to create a commit programmatically (foundational commit during HUG, auto-fix commit during `/gse:go` baseline verification, auto-commit on `/gse:pause`, merge commit during `/gse:deliver`, feature commits during `/gse:task`/`/gse:produce`/`/gse:fix`, etc.) MUST verify that a git identity is configured. Verification queries identity at both global and local scope; if neither is set (both name AND email), the activity blocks and presents the **Git Identity Gate** with five options: *(1) Set global identity* (default, recommended — applies to all projects on this machine, agent asks for name + email), *(2) Set local identity* (this project only, preserves the user's global setup), *(3) Quick placeholder* (local-only throwaway identity for quick tests — the agent sets a neutral *"GSE User"* / *"user@local"* pair and reminds the user to replace it before sharing the repo), *(4) I'll set it myself* (agent provides the exact shell commands and waits for user confirmation), *(5) Discuss*. The Gate is adapted to the user's expertise per P9 — beginners see plain-language equivalents ("your signature", "just for this folder", "a disposable signature"). When the agent collects an email at options 1 or 2, it performs basic format validation (presence of `@` and a dotted domain) and re-prompts on failure. Once the identity is resolved, the originating activity resumes. **Failure mode:** if `git` itself is not installed, the activity aborts gracefully with an install-git message — no Gate is shown.

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
| **Process discipline** | Every transition between lifecycle phases | The next step in the GSE lifecycle is always the default action. Shortcuts or alternatives are never proposed proactively — only if the user asks or a Gate exposes them. | P1 (iterative), P2 (agile) |

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

**Passive acceptance counter:** The agent maintains a `consecutive_acceptances` counter in `.gse/status.yaml` (persisted across context window resets). This counter is **incremented** by +1 for each of the following events:
- The user chooses the agent's recommended option in a **Gate decision** (the primary signal)
- The user confirms a reformulation, plan, design, or requirement set with a single-word response ("yes", "ok", "1") **without modification or question**

The counter is **reset to 0** when:
- The user selects "Discuss" in any interaction
- The user asks "why?", "what about...?", or proposes an alternative
- The user modifies any proposed artefact (plan, design, requirements, test strategy)
- The user rejects an option or selects a non-recommended option
- The pushback checkpoint is triggered and the user responds

**What does NOT increment the counter:**
- Inform-tier acknowledgments (the user was not asked to decide)
- Auto-tier decisions (the user was not involved)
- Simple navigation confirmations ("should I continue?" → "yes") that are not Gate decisions

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

#### Root-Cause Discipline before patching

When applying a fix to a reported defect — either during `/gse:fix` processing a review finding, or in response to a user-reported bug arriving during any other activity (PRODUCE, post-DELIVER, etc.) — the agent MUST follow a 4-step protocol before modifying any file. The protocol protects against *unsystematic debugging*: applying speculative patches in rapid succession without first identifying the actual root cause.

**The 4 steps (mandatory, in order):**

1. **Read** — the source files relevant to the reported defect MUST have been opened in the current turn. A patch on code the agent has not just read is forbidden.
2. **Symptom** — the agent states the defect in specific, observable terms ("the toggle button's background color does not change when clicked", not "the toggle does not work"). If the report is vague, the agent requests one concrete observable fact (console error line, screenshot, specific user interaction sequence) before proceeding.
3. **Hypothesis + Evidence test** — the agent writes in the chat: (a) the hypothesized root cause, (b) a test that would validate or invalidate the hypothesis, (c) a confidence tag per P15 (Verified / High / Moderate / Low). The agent then runs the evidence test. If the result contradicts the hypothesis, the agent returns to this step with a new hypothesis. No patch is attempted yet.
4. **Patch** — only after the evidence test confirms the hypothesis, the agent applies the fix. The commit trailer includes the root-cause summary and the confirming evidence.

**Failed-patch counter and devil-advocate escalation:**

The agent maintains a `fix_attempts_on_current_symptom` counter in `.gse/status.yaml`. The counter is **incremented** by +1 each time a patch fails to resolve the symptom (the user reports the same symptom again, or the evidence test still fails after the patch). The counter is **reset to 0** when:
- The user explicitly confirms resolution ("it works now", "fixed", user moves on to a different topic),
- The symptom explicitly changes (a different observable defect is reported),
- A new sprint starts (`/gse:plan --strategic` promotes the next sprint).

**Escalation thresholds** (calibrated by expertise):

| Expertise | Threshold | On reaching threshold |
|-----------|-----------|----------------------|
| **Beginner** | 2 | Agent STOPS patching and spawns the devil-advocate for a focused static review of the relevant code. |
| **Intermediate** | 3 | Same escalation. |
| **Expert** | 4 | Same escalation. |

On escalation, the devil-advocate receives as input: the precise symptom description, the chain of hypotheses already tried, the patches already applied, and the list of source files under suspicion. It returns findings per its standard format. The agent MUST resolve at least one finding before attempting any further patch on this symptom.

**Rationale:** premature patching adds noise, introduces new bugs, and often fails to address causes external to the code being patched (CORS issues, module-resolution failures, environment mismatches, cache staleness). The read-first and hypothesis-first rules force the agent to anchor in reality; the counter prevents the agent from spiraling into trial-and-error loops that erode user trust.

#### Inform-Tier Decisions Summary

At the end of every creator activity (`/gse:design`, `/gse:preview`, `/gse:produce`, `/gse:task`), the agent MUST close with a short list of **Inform-tier decisions** it made during the activity (per P7 risk classification). These are choices the agent made autonomously because they were individually low-stakes — library micro-choice, folder naming, utility-vs-framework, import style, convention-over-configuration defaults — none of which warranted an interruptive Gate on their own. Listing them at closure gives the user a retrospective override window:

1. **Accept all as-is** (default) — the decisions are appended as an `## Inform-tier Decisions` section in the activity's artefact (or in the commit message for `/gse:task`) for traceability.
2. **Promote one or more to Gate** — the selected decision is elevated to a DEC-NNN and the agent walks through it with the standard Gate format (Question / Context / Options with consequence horizons / Discuss).
3. **Discuss** — explore any of the decisions before accepting or promoting.

If the agent made no Inform-tier decisions during the activity (rare — all choices were Gated), it says so explicitly: *"No inform-tier decisions made this activity — all choices were Gated."*

**Rationale:** inform-tier decisions are individually small but collectively shape the codebase. Making them visible at activity closure is cheaper than surfacing each one at the time it was made, and keeps the human in the loop without decision fatigue. Complements **Scope Reconciliation** (P6 creator-closure check): that one detects *what* was delivered outside the plan; this one detects *how* the delivered work was shaped (design micro-choices).

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
| `/gse:task` | **Ad-hoc Task** | Execute a task outside the standard lifecycle in a dedicated branch/worktree. The task is added to the backlog (the type of artefact is inferred from the description, and the task is attached to the current sprint). It consumes complexity budget. It is reviewed during the next `/gse:review` unless trivial (complexity ≤ 1). It is delivered with the rest of the sprint. **Sprint Freeze guardrail (Hard, all modes except Micro) — see lifecycle guardrails below.** **`--spike`**: create a **spike** — an exploratory experiment to answer a technical question. Spikes are complexity-boxed (max 3 points), non-deliverable (branch deleted after completion), and bypass REQS/TESTS guardrails. Must produce a DEC- artefact documenting the question, approach, and answer. If reusable code emerges, a normal TASK must be created to implement it properly. For beginners: Gate confirmation ("This is an experiment — the code won't be kept. Are you sure?"). |

### 3.2 Onboarding

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:hug` | **User Profile** | Establish or update the full engineering context profile (see Section 3.2.1). Also verifies that the project is a git repository (initializes with foundational commit if needed) and creates `.gse/` |

#### 3.2.1 HUG Profile Dimensions

The HUG activity captures and maintains the following profile dimensions:

| Dimension | Purpose | Examples |
|-----------|---------|----------|
| **IT expertise** | Calibrate technical depth of explanations | Beginner / Intermediate / Advanced / Expert |
| **Scientific expertise** | Calibrate analytical rigor and formalism | none / familiar / practitioner / researcher |
| **Abstraction capability** | Calibrate level of conceptual vs. concrete communication | concrete-first / balanced / abstract-first |
| **Language** | Adapt interaction and production languages | `chat: fr`, `artifacts: en`, `overrides: {requirement: fr}`. Default: chat=detected, artifacts=en. Changeable at any time globally or per document. |
| **Preferred verbosity** | Control response length | terse / normal / detailed |
| **Domain background** | Source of analogies for adaptive communication (P9) | Teaching / Business / Science / Engineering / Design |
| **Decision involvement** | Calibrate decision tier thresholds (P7) | autonomous (more Auto) / collaborative / supervised (more Gate) |
| **Project domain** | Adapt engineering recommendations | Web / Embedded / Scientific / CLI / Library / Mobile |
| **Team context** | Adapt collaboration recommendations | Solo / Small team / Large team |
| **Learning goals** | Drive proactive learning proposals (P14) | "I want to understand testing" / "Learn git basics" / None |
| **Contextual tips** | Enable/disable in-activity micro-explanations (P14) | Enabled / Disabled |
| **Emoji** | Enable/disable emoji in chat output | On (default) / Off |
| **User name** | Display name in dashboard and artefacts (optional) | Free text / Skip (defaults to git user name or "Unknown") |

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
| `/gse:plan` | **Plan** | Select items from the backlog pool and promote them to the current sprint. Create new items if needed. **At strategic level:** creates `.gse/plan.yaml` with workflow, budget, and sprint branch. **At tactical level:** adjusts scope and reorders tasks within the active plan. The plan is a **living, filtered view** of the backlog maintained by the orchestrator. |

### 3.6 Engineering

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:reqs` | **Requirements** | Define product functions and qualities (FR & NFR). Begins with conversational elicitation (Step 0) to capture user intent in natural language before formalization. Includes user stories with testable acceptance criteria for validation testing. Ends with a quality assurance checklist (ISO 25010 inspired) verifying NFR completeness and measurability |
| `/gse:design` | **Design** | Define architecture decisions, component decomposition, interface contracts, **shared state identification** (state that must be consistent across components/pages — mandatory section with an explicit disclaimer if none), and technical choices. Produces design artefacts traced to requirements. All significant choices are logged to the decision journal |
| `/gse:preview` | **Preview** | Simulate and show what the planned artefacts will look like before building them. Two variants are officially supported and chosen at activity start via a Gate: **(a) static description** (default, any domain) — wireframes, API contracts, component diagrams, user story walkthroughs written into the preview artefact, throwaway; **(b) scaffold-as-preview** (recommended for web/mobile) — minimal runnable project (framework scaffold) that becomes the base for the following `/gse:produce`, with placeholder code marked by `PREVIEW:` comments (idiomatic per language: `//`, `#`, `<!-- -->`) for later replacement. The variant choice is adapted to the project domain (web/mobile → scaffold recommended; api/cli/library/scientific → static recommended). **Sprint-level skip:** PREVIEW is legitimately skipped when the current sprint contains no user-visible or demonstrable task (foundation sprints doing infrastructure only) — recorded in `plan.yaml → workflow.skipped`, no deviation. Preview-ahead (previewing future-sprint tasks from the current sprint) is explicitly NOT supported — PREVIEW is just-in-time. See Section 5. |
| `/gse:tests` | **Tests** | Define test strategy, write tests, set up test environment, execute test campaigns, and produce test evidence. Covers verification (unit, integration), validation (acceptance, E2E, visual), **policy** (static structural enforcement: architecture layering, license compliance, conventions — see Section 6), and dynamic constraints (accessibility, performance, compatibility). Adapts the test pyramid to the project domain. Installs required tools (test frameworks, browsers, coverage tools). Produces test campaign reports with screenshots and optional video. See Section 6 |
| `/gse:produce` | **Produce** | **Create feature branch + worktree** for the task, then execute the production plan in the isolated worktree. All code, tests, and docs are committed to the feature branch. Tests are executed after production and results are attached as evidence. |
| `/gse:deliver` | **Deliver** | **Merge** reviewed feature branches into the sprint branch, merge sprint branch into `main`, tag release, generate changelog. **Optionally deploy:** if `git.post_tag_hook` is configured, execute the deployment command after tagging. If deployment fails, propose rollback (Gate). Clean up branches and worktrees (see Section 10.3) |

### 3.7 Quality

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:review` | **Review** | Review operates on the **branch diff** (`git diff sprint-branch...feature-branch`), not just file state. Complete review of all artefact types in the current sprint. Includes **devil's advocate** perspective on the agent's own productions (P16): hunts hallucinations, challenges assumptions, verifies libraries/APIs exist. Updates health score |
| `/gse:fix` | **Fix** | Create a fix branch from the reviewed branch, apply fixes in an isolated worktree, with traceability to review items |

### 3.8 Deployment

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:deploy` | **Deploy** | Deploy the current project to a Hetzner server via Coolify. Adapts to the user's situation: from zero infrastructure (solo) to a pre-configured shared server (training). Handles provisioning, server hardening, Coolify installation, DNS/SSL, and application deployment in a single guided flow. Options: `--status` (show deployment state), `--redeploy` (rebuild), `--destroy` (tear down server, Gate). |

### 3.9 Capitalization

| Command | Activity | Description |
|---------|----------|-------------|
| `/gse:compound` | **Compound** | Capitalize learnings across 3 axes: **Axe 1** (project — patterns, errors, best practices → `compound.md`), **Axe 2** (methodology — what worked/didn't in GSE-One itself → closes with a 3-option Gate: *(1) export as a local feedback document only, (2) propose GitHub tickets for upstream submission, (3) both*; quality filter capped at `compound.max_proposed_issues_per_sprint` issues per sprint, theme-grouped, deduplicated against existing issues, each validated by the user before submission), **Axe 3** (competencies — feed P14 learning notes) |
| `/gse:integrate` | **Integrate** | Route capitalized solutions: Axe 1 → project config/rules, Axe 2 → issue on `your-org/gse-one` repo (if user accepts), Axe 3 → `docs/learning/` + competency map |

### 3.10 Commands by Lifecycle Phase

For orientation, here is when each command is typically used in the lifecycle:

| Phase | Commands | Purpose |
|-------|----------|---------|
| **LC00 — Onboarding** | `/gse:hug` | User profiling and project initialization |
| **LC01 — Discovery & Planning** | `/gse:go`, `/gse:collect`, `/gse:assess`, `/gse:plan` | Understand context, identify gaps, plan the sprint |
| **LC02 — Development** | `/gse:reqs`, `/gse:design`, `/gse:preview`, `/gse:tests`, `/gse:produce` | Specify, design, test, and build |
| **LC02 — Quality & Delivery** | `/gse:review`, `/gse:fix`, `/gse:deliver` | Verify, fix, and ship |
| **LC03 — Capitalization** | `/gse:compound`, `/gse:integrate` | Learn from the sprint, route improvements |
| **Cross-cutting** | `/gse:status`, `/gse:health`, `/gse:backlog`, `/gse:task`, `/gse:learn`, `/gse:pause`, `/gse:resume`, `/gse:deploy` | Available at any time regardless of phase |

> **Note:** `/gse:go` detects the current project state and proposes the next command automatically. Users don't need to memorize this sequence — the orchestrator handles it (see Section 14).

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

| Type | Kind | Purpose | Traces to |
|------|------|---------|-----------|
| **Unit** | verification | Check individual functions/modules in isolation | DES (design), code |
| **Integration** | verification | Check that modules work together correctly | DES (interfaces), REQ |
| **E2E (End-to-End)** | validation | Simulate complete user workflows through the application | REQ (user stories) |
| **Visual** | validation | Check UI rendering via screenshot comparison | REQ (UI requirements) |
| **Acceptance** | validation | Confirm that a requirement is met from the user's perspective | REQ (acceptance criteria) |
| **Regression** | both | Ensure that previously fixed bugs don't reappear (verification or validation depending on what regressed) | RVW (past review findings) |

The **Kind** column labels each type against the methodological distinction (see glossary §1.5): **verification** = "build the thing right" (vs DES-), **validation** = "build the right thing" (vs REQ-). Regression is `both` because a regressed bug may concern either side.

**Cross-sprint regression detection:** During `/gse:review`, the agent executes the **full test suite** (not just tests for the current TASK) and compares pass/fail counts with the previous sprint's test report (`docs/sprints/sprint-{NN-1}/test-reports/`). Tests that passed in the previous sprint but now fail are flagged as `[REGRESSION]` findings with severity HIGH. This provides automatic cross-sprint regression detection without additional infrastructure — it leverages the accumulated test suite.

#### Requirements elicitation and quality assurance

The `/gse:reqs` activity includes two mechanisms that feed into the test strategy:

**Conversational elicitation (Step 0):** Before formalizing requirements, the agent engages the user in a free-form conversation to capture intent in natural language. The user describes what the system should do and how it should behave (speed, reliability, ease of use). The agent identifies both functional needs and implicit quality expectations, reformulates them as themes, and validates with the user. This ensures quality requirements are surfaced early — not as an afterthought during NFR definition.

**Quality assurance checklist (Step 7, ISO 25010 inspired):** After drafting requirements, the agent verifies NFR completeness against 7 quality dimensions: Performance, Security, Reliability, Usability, Maintainability, Accessibility, Compatibility. For each NFR, 2-3 checklist items are verified (target metric defined? measurement method specified? conditions defined?). Gaps are classified by priority: HIGH (security, reliability, performance) trigger Soft guardrails; MEDIUM and LOW are informational. The output is a **quality coverage matrix** persisted in `reqs.md`.

**Impact on test strategy:** When quality gaps are identified, the test strategy must include corresponding tests to close them. Each gap-closing test carries a `quality_gap: true` trace field to distinguish it from standard validation tests. These are not a new pyramid level — they are constraints on existing levels informed by the quality checklist.

#### Test pyramid (calibrated by project domain)

The agent proposes a test distribution adapted to the project type (from `config.yaml → project.domain`):

| Domain | Unit | Integration | E2E / Visual | Acceptance | Policy | Other |
|--------|------|-------------|--------------|------------|--------|-------|
| **Web frontend** | 20% | 20% | 30% | 20% | 5% | 5% (a11y, perf) |
| **API backend** | 45% | 25% | 5% | 10% | 5% | 10% (load, security) |
| **CLI tool** | 55% | 20% | 5% | 10% | 5% | 5% (compat) |
| **Data pipeline** | 35% | 30% | 0% | 20% | 5% | 10% (data quality) |
| **Mobile** | 20% | 20% | 30% | 15% | 5% | 10% (device compat) |
| **Library / SDK** | 65% | 20% | 0% | 5% | 5% | 5% (compat, docs) |
| **Embedded** | 45% | 25% | 0% | 10% | 5% | 15% (hardware sim) |
| **Scientific** | 35% | 20% | 0% | 30% | 5% | 10% (data quality) |

The **Policy** column — added in v0.35 — groups tests that **enforce structural rules** on the codebase (architecture, licenses, conventions) rather than verify behavior. A policy test scans the static state of the code (imports, dependencies, naming, file size) and produces a deterministic pass/fail that fails CI when a rule is violated. Examples: *"src/domain/** must not import src/ui/**"*, *"no GPL-licensed dependency"*, *"all public functions must have a docstring"*, *"no file > 500 lines"*. Policy tests run fast (static analysis, no runtime) and guard the codebase's **shape**, not its behaviour. The 5% baseline is indicative — projects with strict layered architecture, regulated licensing, or strong convention enforcement may raise it to 10-15%.

The **Other** column groups **dynamic-constraint** tests attached to existing levels: accessibility (attached to E2E), performance / load (attached to integration or E2E), compatibility (attached to E2E across targets), hardware simulation (attached to integration), data quality (attached to integration). Distinction from Policy: Other verifies behavioral constraints under dynamic execution; Policy verifies structural rules via static scan.

The pyramid is a **starting point** — the agent adjusts based on actual project needs and presents deviations as Inform-tier decisions.

**Monorepo sub-domains:** When `config.yaml → project.sub_domains` is defined, the test pyramid is calibrated **per sub-domain**. For example, a project with `frontend/` (web) and `backend/` (api) uses the web pyramid for frontend tests and the api pyramid for backend tests. The top-level `project.domain` is the fallback for files outside any sub-domain path.

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

#### Canonical test run

A **canonical test run** is the single procedure executed identically whether invoked from `/gse:produce` (automatic post-production run) or `/gse:tests --run` (explicit run). Both entry points MUST produce the same artefacts and the same user-visible output — any divergence is a bug in the methodology, not a feature. Each activity adds only its own pre/post-conditions; the seven steps below are immutable.

1. **Execute the test suite** in the appropriate directory (task worktree under PRODUCE, project root or selected worktree under TESTS). Coverage is enabled whenever the framework supports it.
   ```bash
   cd .worktrees/sprint-03-feat-auth/
   uv run pytest --cov --cov-report=json  # or equivalent
   ```
2. **Capture evidence**: pass/fail per test, execution time, stdout/stderr, stack traces, coverage data, screenshots and videos (when visual testing is enabled).
3. **Save raw evidence** to `tests/evidence/sprint-NN/TASK-NNN/`:
   ```
   tests/evidence/sprint-03/TASK-038/
   ├── results.json              # Test results (machine-readable)
   ├── coverage.json             # Coverage data
   ├── login-page.png            # Screenshot
   ├── login-flow.mp4            # Video (if enabled)
   ```
4. **Allocate a TCP-NNN and create the campaign report** at `docs/sprints/sprint-NN/test-reports/campaign-{YYYY-MM-DD}-{TASK-ID}.md` using the `test-campaign.md` template. The report carries the frontmatter defined in §12.2 (prefix `TCP-`, type `test-campaign`) and traces to the TASK and the covered REQs.
5. **Write `test_evidence` on each covered TASK** in `backlog.yaml` with the structured block: `status`, `campaign_ref`, `timestamp`, `pass_rate`, `code_coverage`, `summary` (see §12.3 backlog schema).
6. **Display the inline summary** in chat (see "Inline summary" below). This step is not optional — it makes the test-driven approach visible at every run.
7. **Update health and dashboard**: recompute `health.dimensions.test_pass_rate` in `status.yaml` using the formula in §7.1, then run `dashboard.py` to refresh `docs/dashboard.html`.

#### Inline summary (mandatory at step 6)

The summary adapts to `profile.yaml → user.it_expertise`.

**For beginner users:** Map test names to feature descriptions derived from REQS acceptance criteria. Use ✅/❌ indicators. When tests fail and are then fixed, show the correction explicitly (`✅ corrigé ← était en échec`). The user sees that every feature is verified and that problems are caught and fixed — without any jargon or file names.

**For intermediate/expert users:** Show a technical summary (file-level pass/fail counts, duration, build/lint status, coverage delta when relevant).

**Failure → fix → verify cycle:** When tests fail mid-run and the user accepts the auto-fix, display the failure summary first, then the corrected summary — so the cycle is transparent.

#### Screenshot analysis (visual runs only)

When visual testing is enabled, after step 3 the agent performs a **multimodal analysis** of captured screenshots:
- Misaligned elements, truncated text, missing images
- Comparison against reference screenshots (visual regression)
- Accessibility issues: insufficient contrast, tiny text
- Findings are tagged `[VISUAL]` and attached to the campaign report

**Best-effort caveat:** The agent's multimodal analysis can detect obvious visual defects but is NOT a replacement for specialized tools. For reliable results:
- **Accessibility:** Use dedicated tools (Axe, Lighthouse) — the agent installs and runs them as part of the campaign
- **Visual regression:** Use pixel-diff tools (Playwright comparator, Percy, BackstopJS) — the agent configures them
- **The agent's role** is to orchestrate, interpret, and present — not to replace these tools
- Tool-based findings → confidence **Verified**; agent's own analysis → **Moderate** (P15)

#### Activity-specific invocations

Each entry point invokes the canonical run with its own pre/post-conditions:

| Activity | When called | Pre-conditions specific to this activity | Post-conditions specific to this activity |
|----------|-------------|------------------------------------------|-------------------------------------------|
| `/gse:produce` (auto) | After code is produced for a TASK | Gate on `--skip-tests` (logs DEC-); auto-generates tests if absent (per expertise); failure triggers Fix/Skip/Discuss Gate | Task `test_evidence.status` feeds the review guardrail |
| `/gse:tests --run` | Explicit run | Tests must already exist (no generation) | Campaign report is the primary output |
| `/gse:tests --run TST-NNN` | Explicit single-test run | TST-NNN must be defined | Scoped campaign (only the one test) |
| `/gse:tests --run --level unit` | Explicit scoped run | Level must exist in test strategy | Scoped campaign (only the level) |
| `/gse:tests --visual` | Visual-only run | Visual testing must be configured | Screenshot analysis is mandatory |

#### Test campaign report

Each test execution produces a traceable **campaign report**:

```markdown
---
gse:
  id: TCP-007
  type: test-campaign
  sprint: 3
  branch: gse/sprint-03/feat/auth
  traces:
    implements: [REQ-007]
    derives_from: [TASK-038]
  created: 2026-04-10
---

# Test Campaign TCP-007 — Sprint 3 / TASK-038

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

Campaign reports are saved in `docs/sprints/sprint-NN/test-reports/` and traced in the backlog via `test_evidence.campaign_ref` on each covered TASK.

### 6.4 Coverage Model

The health dashboard tracks three coverage dimensions:

| Dimension | Measures | Target |
|-----------|---------|--------|
| **Code coverage** | % of code lines/branches exercised by tests | Configurable (default 60%) |
| **Requirements coverage** | % of REQ with at least one linked test | 100% for `must` priority, 80% for `should` |
| **Risk coverage** | % of high-risk modules (security, Gate decisions, imports) with dedicated tests | 100% |

When coverage drops below the configured minimum, a **Hard guardrail** triggers:
"Code coverage is 45% (minimum: 60%). Add tests before proceeding to DELIVER."

### 6.5 Test Review Layering

Reviewing tests happens at **three distinct moments**, each targeting a different class of defect. Only the implementation review is systematic; the two pre-production reviews are agile-by-default and fire only when project risk warrants them.

| Tier | Question answered | When it runs | Activated automatically when | Always available via |
|------|-------------------|--------------|------------------------------|---------------------|
| **Strategy review** (tag `[STRATEGY]`) | Is the test approach calibrated correctly? (pyramid, risk coverage, quality-gap coverage, CI integration plan) | At the end of `/gse:tests --strategy`, before the strategy file is finalised | `project.domain` is security-sensitive (auth/crypto/payments) OR `complexity_budget > 15` | `/gse:tests --review-strategy` |
| **TST specs review** (tag `[TST-SPEC]`) | Does each TST- spec encode the right scenario? (exact conditions, boundaries, quality-gap tests) | At the end of `/gse:tests` Step 3 (Write Tests), before production starts | ≥ 1 TST- carries `quality_gap: true` OR the total TST- count ≥ 20 | `/gse:tests --review-specs` |
| **Implementation review** (tag `[IMPL]`) | Are the written tests meaningful? (assertions, fixtures, edge cases, no tautological tests, regression scan) | During `/gse:review`, after production | Always (systematic step 2e) | `/gse:review --perspective tests` |

**Rationale:** The three tiers split "test the right thing" (STRATEGY, TST-SPEC — upstream of code) from "test it correctly" (IMPL — after code). Running the upstream tiers only conditionally keeps light sprints agile while high-risk or high-volume sprints get the full checkpoint dispositif. The `--deep-review` shortcut on `/gse:tests` activates STRATEGY + TST-SPEC together when the user wants the full treatment regardless of triggers.

**Findings** from all three tiers land in the standard review report (`docs/sprints/sprint-NN/review.md`) with the matching tag, so the user sees one consolidated list. Pre-production findings use the same RVW-NNN ID space and the same severity scale (HIGH / MEDIUM / LOW) as post-production findings.

**Guardrail effect:** A STRATEGY or TST-SPEC finding with severity HIGH blocks `/gse:produce` (Hard guardrail) until resolved — the user fixes the strategy or the TST- spec before writing code against it. MEDIUM / LOW findings warn but do not block.

### 6.6 Adaptation to User Expertise

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

Every sprint has a complexity budget — a finite capacity for new work. One **complexity point** measures **coupled effort and complexity for the AI + user pair** (see P10 for the full definition): code complexity added + AI generation effort + human review effort, treated as a single scalar because these three factors are entangled in practice.

**Temporal anchor (indicative).** 1 point ≈ 1 pair-session hour (AI generation + user review + decision). A 10-point sprint ≈ 1-3 working days of AI+user sessions. Solo human (without AI) equivalent: 1 point ≈ 0.5-1 working day, speedup ratio typically 10× (range 5-20× depending on domain — CRUD-standard ~15-20×, algorithmic / research problems ~3-5×). This anchor is **indicative, not prescriptive** — spec §2 *"Sprint = complexity-boxed, no fixed duration"* is preserved. The ballpark helps users sense the size of their commitments; it is not a deadline.

Each addition to the project has a cost:

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

**Maintenance work — case-by-case assessment (replaces the previous "zero-cost items" blanket rule):** refactoring, test writing, documentation, renaming, bug-fixing, and other maintenance activities have **highly variable pair effort**. Some are trivial (a typo fix, a single docstring) and genuinely cost zero points. Others consume real pair-session hours (rewriting documentation for a whole subsystem, refactoring a public API across 50 call sites, building a comprehensive test harness). Treating them all as zero-cost underestimates sprint load and misleads budgeting.

The agent therefore assesses each maintenance task case-by-case using the **Cost Assessment Grid for Maintenance Work** (see Appendix B) with four criteria: fan-out, review burden, rework risk, coupling introduction. The grid yields 0 pt, 1 pt, or 2-5 pt depending on how many criteria are non-trivial. Removing code or dependencies remains a **simplification credit** (negative points) regardless of scale — removal reduces future pair effort.

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

Guardrails make cost visible and require proportional acknowledgment. Soft guardrails warn without blocking. Hard guardrails block until the user provides a documented rationale. Emergency guardrails halt until explicit risk acknowledgment. The stronger the guardrail, the more explicit the acknowledgment must be.

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
main                                              # Always stable, deployable
├── gse/sprint-03/integration                     # Sprint integration branch (created by PLAN)
│   ├── gse/sprint-03/feat/user-auth              # Feature branch (created by PRODUCE)
│   ├── gse/sprint-03/feat/dashboard              # Another feature branch
│   ├── gse/sprint-03/fix/rvw-005                 # Fix branch (created by FIX)
│   └── gse/sprint-03/docs/api-reference          # Documentation branch
└── gse/sprint-04/integration                     # Next sprint (future)
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
| **PLAN (strategic)** | Create sprint integration branch `gse/sprint-NN/integration` from `main`. Assign branch names to each planned task. |
| **PLAN (tactical)** | Assign branch names to newly planned tasks. No branch creation yet. |
| **PRODUCE** | Create feature branch from sprint integration branch + create worktree in `.worktrees/`. All work happens in the worktree. Commit with conventional messages: `gse(sprint-NN/activity): description`. |
| **REVIEW** | Review operates on the branch diff: `git diff gse/sprint-NN/integration...gse/sprint-NN/feat/X`. Shows exactly what changed. |
| **FIX** | Create fix branch `gse/sprint-NN/fix/rvw-NNN` from the reviewed feature branch. Fix in isolated worktree. |
| **DELIVER** | **Gate decision:** merge strategy (squash/merge/rebase). Merge feature branches → sprint integration → `main`. Tag `main` with semantic version. Delete merged branches and worktrees. |
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
git tag gse-backup/sprint-03-pre-merge-feat-auth $(git rev-parse gse/sprint-03/integration)

# Before deleting a branch:
git tag gse-backup/sprint-03-feat-auth-deleted $(git rev-parse gse/sprint-03/feat/auth)
```

Safety tags are prefixed `gse-backup/` and retained for 30 days (configurable via `git.backup_retention_days`).

**Recovery procedures:**
- **Branch recovery:** `git checkout -b gse/sprint-03/feat/auth gse-backup/sprint-03-feat-auth-deleted`
- **Merge reversal:** `git checkout gse/sprint-03/integration && git reset --hard gse-backup/sprint-03-pre-merge-feat-auth`
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
│   ├── plan.yaml                    # Living sprint plan (workflow, budget, coherence)
│   ├── backlog.yaml                 # Unified work items (TASK) with git state
│   ├── sources.yaml                 # External source registry
│   ├── inventory.yaml               # Artefact inventory (COLLECT output)
│   ├── decisions.md                 # Decision journal (Inform + Gate tiers)
│   ├── decisions-auto.log           # Auto-tier decision log (compact)
│   ├── dashboard.py                 # Dashboard generator script (copied from plugin)
│   ├── backlog-archive.yaml         # Delivered TASKs from past sprints (not auto-loaded)
│   └── checkpoints/                 # Pause/resume snapshots
│       └── checkpoint-YYYY-MM-DD-HHMM.yaml
│
├── .worktrees/                      # Git worktree directories (gitignored)
│   └── sprint-NN-type-description/  # One directory per active task
│
├── docs/
│   ├── sprints/
│   │   └── sprint-NN/
│   │       ├── plan-summary.md      # Sprint plan archive (generated by DELIVER from .gse/plan.yaml)
│   │       ├── reqs.md              # Requirements (FR & NFR)
│   │       ├── design.md            # Design decisions & architecture
│   │       ├── test-strategy.md      # Test strategy (pyramid, coverage targets, verification + validation)
│   │       ├── test-reports/        # Test campaign reports and evidence
│   │       ├── review.md            # Review findings
│   │       ├── compound.md          # Capitalized learnings
│   │       └── release.md           # Release/delivery notes
│   ├── dashboard.html               # Project health dashboard (generated, auto-refresh)
│   ├── archive/                     # Archived sprints (older than current - 2)
│   └── learning/                    # Learning notes (P14)
│       ├── git-branching.md         # Personal course note on git branching
│       ├── testing-strategies.md    # Personal course note on testing
│       └── ...                      # One file per topic, enriched over time
│
├── src/                             # Source code artefacts
├── tests/                           # Test source files (unit, integration, e2e)
└── ...                              # Other project files
```

### 12.2 Artefact Metadata

Each structured artefact (markdown) includes a YAML frontmatter for traceability:

```yaml
---
gse:
  type: requirement | design | test | review | plan-summary | compound | decision | learning-note | code | test-campaign
  sprint: 3
  branch: gse/sprint-03/feat/user-auth
  traces:                                 # typed trace links (P6)
    derives_from: [REQ-001]               # this artefact was created because of...
    implements: [DES-002]                 # this artefact satisfies...
    tested_by: [TST-001]                 # this artefact is verified by...
    decided_by: [DEC-005]                # this artefact was shaped by decision...
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
    test_evidence:                   # single structured field (see §6.3 Test Execution and Evidence)
      status: pass                   # absent | pass | fail | skipped
      campaign_ref: docs/sprints/sprint-03/test-reports/campaign-2026-04-10-TASK-038.md
      timestamp: 2026-04-10T14:30:00Z
      pass_rate: 91.7                # % of tests passing (0-100)
      code_coverage: 78              # % line coverage (0-100), null if not measured
      summary: "24 tests, 22 passed, 2 failed"
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
- **Sprint plan = living filtered view** — `.gse/plan.yaml` is maintained by the orchestrator throughout the sprint, tracking workflow state, budget, and coherence. At delivery, a snapshot is archived to `docs/sprints/sprint-NN/plan-summary.md`. `plan.yaml` uses its own YAML schema (not Markdown frontmatter)
- **Merge queue = derived view** — items where `status == done AND git.branch_status == active`

**Archival (multi-sprint scalability):**

To keep `backlog.yaml` within context limits (~200 lines), delivered TASKs are archived during COMPOUND:
- TASKs with `status: delivered` are moved from `backlog.yaml` to `backlog-archive.yaml` (same YAML format, not auto-loaded)
- Sprint artefact directories older than 2 sprints are moved: `docs/sprints/sprint-{NN}/` → `docs/archive/sprint-{NN}/`
- Archived data remains accessible via `/gse:status --history`

```
.gse/
├── backlog.yaml              # active TASKs (pool + current/recent sprints)
├── backlog-archive.yaml      # delivered TASKs from past sprints (not auto-loaded)
docs/
├── sprints/                   # last 2 sprints (active)
├── archive/                   # older sprints (accessible on demand)
```

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
# plan approval/state is now tracked in .gse/plan.yaml (field: status)

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

# P16 pushback detection — see spec P16 for increment/reset rules
# Incremented: Gate decision accepted without modification, single-word confirmation of artefact
# Reset to 0: user selects Discuss, asks why, modifies proposal, rejects option, or checkpoint triggers
consecutive_acceptances: 2             # primary counter — triggers pushback at threshold (beginner=3, intermediate=5, expert=8)
pushback_dismissed: 0                  # times user chose "Everything looks good" — if >=2, suppress for rest of sprint

# P16 root-cause discipline — see spec P16 "Root-Cause Discipline before patching" for rules
# Incremented: patch applied but symptom persists (user reports again, or evidence test still fails)
# Reset to 0: user confirms resolution, symptom explicitly changes, or new sprint starts
fix_attempts_on_current_symptom: 0     # triggers devil-advocate escalation at threshold (beginner=2, intermediate=3, expert=4)

# P6 scope reconciliation — recorded at start of creator activities (produce, task)
# Used at closure to compute `git diff --name-status <sha>..HEAD` and detect scope drift
# Cleared at activity closure; empty when not in a creator activity
activity_start_sha: ""                 # HEAD SHA at the start of the current creator activity

last_activity: /gse:produce
last_activity_date: 2026-04-10

# Per-activity completion history — authoritative source for plan.yaml workflow.completed timestamps
# Appended by the orchestrator at each activity transition. Scoped to the current sprint;
# reset by /gse:plan --strategic when promoting a new sprint.
activity_history:
  - activity: collect
    completed_at: "2026-04-08T09:15:00Z"
    sprint: 3
    notes: "12 files scanned"
  - activity: assess
    completed_at: "2026-04-08T09:30:00Z"
    sprint: 3
    notes: "2 gaps identified"
  - activity: plan
    completed_at: "2026-04-08T10:00:00Z"
    sprint: 3

# Stale sprint detection (complexity/session-based, not calendar-based)
sessions_without_progress: 0           # incremented each /gse:go or /gse:resume with no TASK status change

# Review findings counter (used by hooks)
review_findings_open: 0
```

### 12.4.1 Required Fields in `.gse/` Files

The following fields are **mandatory** — tools and the dashboard depend on them. The agent MUST verify their presence and non-emptiness after writing any `.gse/` file.

**`config.yaml` — required fields:**

| Field | Type | Purpose |
|-------|------|---------|
| `project.name` | string (non-empty) | Project display name — used by dashboard title |
| `project.domain` | string | Project domain — used by dashboard and PREVIEW logic |
| `git.strategy` | `worktree` \| `branch-only` \| `none` | Git branching strategy |

**`status.yaml` — required fields:**

| Field | Type | Purpose |
|-------|------|---------|
| `gse_version` | string | GSE-One version — used by dashboard |
| `current_sprint` | integer ≥ 0 | Current sprint number |
| `current_phase` | `LC00` \| `LC01` \| `LC02` \| `LC03` | Current lifecycle phase — used by dashboard |
| `activity_history` | list of `{ activity, completed_at, sprint, notes }` | Per-activity completion log for the current sprint — authoritative source for `plan.yaml.workflow.completed` timestamps |
| `consecutive_acceptances` | integer ≥ 0 | P16 pushback counter |
| `fix_attempts_on_current_symptom` | integer ≥ 0 | P16 root-cause discipline counter — triggers devil-advocate escalation at threshold |

**Validation rule:** After creating or updating `config.yaml` or `status.yaml`, the agent SHOULD verify that all required fields are present and non-empty. If the dashboard tool (`dashboard.py`) is available, regenerate the dashboard and verify the output does not contain placeholder values ("Unknown Project", empty phase).

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

### 12.7 Resilience

GSE-One state files are human-readable YAML and Markdown by design. This enables resilience against agent failures:

1. **YAML validation** — After writing any `.gse/*.yaml` file, the agent verifies that the YAML is parseable. If the file is corrupt (invalid YAML), the agent restores from the latest checkpoint in `.gse/checkpoints/` and reports the error. A corrupt state file must never be left in place.

2. **Context overflow prevention** — When `backlog.yaml` exceeds ~200 lines (typically around sprint 5), the agent compacts it by moving TASKs with `status: delivered` to `backlog-archive.yaml`. When sprint artefact directories accumulate past 5 sprints, the agent proposes archiving completed sprints: `docs/sprints/sprint-{NN}/` → `docs/archive/sprint-{NN}/`. This keeps the active state within context window limits.

3. **Graceful degradation** — If the AI agent is unavailable (context overflow, service outage, model error), the user can continue by reading the state files directly:
   - `status.yaml` → current sprint, phase, last activity
   - `backlog.yaml` → task list and statuses
   - `docs/sprints/sprint-{NN}/` → plan, requirements, design, test strategy, review findings
   - `.gse/checkpoints/` → recovery snapshots

   All file formats are documented in Sections 12.1–12.5. No proprietary encoding is used.

### 12.8 Project Dashboard

GSE-One generates a self-contained HTML dashboard at `docs/dashboard.html` that provides a real-time view of both methodology health and project health.

**Generation:** The dashboard is generated by `tools/dashboard.py` (Python script, no external dependencies except optional Chart.js via CDN), located in the plugin directory. It parses all `.gse/*.yaml` files and `docs/sprints/` artefacts. Tools are resolved at runtime via the `~/.gse-one` registry file (written by `install.py`), which contains the absolute path to the plugin directory.

**Tool resolution:** `install.py` writes `~/.gse-one` (a single line: the absolute plugin path). Skills execute tools via: `python3 "$(cat ~/.gse-one)/tools/dashboard.py"`. This ensures tools are never copied or improvised by the AI agent — they run directly from their source.

**Lifecycle integration:**

| Moment | Action |
|---|---|
| HUG (Step 5.5) | Validate `~/.gse-one` registry, generate initial `docs/dashboard.html`, inform user |
| GO (Step 2.6) | Validate registry, regenerate at session start (silent) |
| PRODUCE (Step 5) | Regenerate after each TASK completion |
| REVIEW (Step 6) | Regenerate + inform user (health scores changed) |
| DELIVER (Step 9) | Regenerate with delivery status |
| COMPOUND (Step 5) | Regenerate + inform user (sprint history updated) |

**Content:** Project state (sprint, phase, kanban), health radar (8 dimensions), REQS→TESTS traceability, quality metrics (findings, regressions), lifecycle checklist, git state.

**Usage:**
```bash
python3 "$(cat ~/.gse-one)/tools/dashboard.py"              # generate once (CDN mode)
python3 "$(cat ~/.gse-one)/tools/dashboard.py" --watch      # live updates on file changes
python3 "$(cat ~/.gse-one)/tools/dashboard.py" --no-cdn     # offline mode
python3 "$(cat ~/.gse-one)/tools/dashboard.py" --if-stale   # regen only if state is newer (used by hooks)
```

**Automatic regeneration policy:** the dashboard is kept in sync with project state without manual intervention. Every time sprint state (sprint plan, backlog, status, profile) or a sprint artefact (requirements, design, test strategy, review, release notes, compound notes, decisions, etc.) is modified, the dashboard regenerates. This is enforced by a cross-platform tool-invocation hook that fires on every editor write, with an internal debounce (configurable, default 5 seconds) so bursts of writes trigger at most one regeneration per debounce window. Activities that mark major milestones (`/gse:hug`, `/gse:go`, `/gse:produce`, `/gse:review`, `/gse:deliver`, `/gse:compound`) additionally trigger an explicit regeneration at the end of their workflow, guaranteeing a fresh dashboard at every checkpoint even if the hook is unavailable. **Failure visibility:** if a regeneration attempt fails, the failure is recorded and surfaced as a visible red warning banner at the top of the dashboard on the next successful regeneration — users never discover staleness silently.

**Output:** `docs/dashboard.html` — committed to git, viewable in any browser, servable via GitHub Pages. Auto-refreshes every 30 seconds. Manual refresh button included.

---

## 13. Configuration & Customization

### 13.1 Project Configuration

Users can customize GSE-One behavior via `.gse/config.yaml`:

```yaml
# .gse/config.yaml
project:
  name: "My Project"
  domain: "web"                        # web | embedded | scientific | cli | library | mobile
  # Optional: sub-domains for monorepos (calibrates test pyramid per sub-project)
  # sub_domains:
  #   - path: frontend/
  #     domain: web
  #   - path: backend/
  #     domain: api
  #   - path: services/auth/
  #     domain: api

lifecycle:
  mode: full                           # full | lightweight | micro
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

deploy:
  provider: hetzner                    # only supported provider
  server_type: cax21                   # cax21 | cax31 | cax41
  datacenter: fsn1                     # fsn1 | nbg1 | hel1
  app_type: auto                       # auto | python | streamlit | static
  health_check_timeout: 120            # seconds
```

**Documentation as first-class artefact:** Documentation tasks (`artefact_type: doc`) follow the same lifecycle as code — planned, produced in a worktree branch (`gse/sprint-NN/docs/<name>`), reviewed, and delivered. The agent can auto-generate API documentation from code (e.g., docstrings → reference docs) during `/gse:produce` when the TASK has `artefact_type: doc`.

> **Mono-repo assumption:** GSE-One manages a single repository at a time. For multi-component projects, a mono-repo is recommended. If you use multiple repos, run GSE-One independently in each repo.

### 13.2 Lightweight Mode

For micro-projects (single file, 1-hour task, quick script), the full lifecycle is overkill. GSE-One supports a **lightweight mode** that reduces overhead while preserving traceability:

```yaml
lifecycle:
  mode: micro | lightweight | full     # auto-detected, user can override
```

**Auto-detection:** The orchestrator scans structural signals (package manifests, persistence, entry points, multi-component structure, CI/CD, git maturity, test presence) and recommends a mode based on project complexity — not file count. The recommendation is presented as a Gate decision — the user confirms or overrides. See Section 14.3 Step 6 for the full assessment protocol.

Complexity-to-mode mapping:
- **Micro** — No manifest, no git history, ≤ 2 source files. Scripts, one-off tasks.
- **Lightweight** — Simple project: few dependencies, single component, no persistence, no CI.
- **Full** — Complex project: persistence, multi-component, CI/CD, >10 dependencies, or >10 entry points.

Upgrading from Micro → Lightweight → Full is possible at any time via `/gse:go` — the agent scaffolds the missing structure.

| Aspect | Full mode | Lightweight mode | Micro mode |
|--------|-----------|-----------------|------------|
| Selection | Complex project (persistence, multi-component, CI, many deps) | Simple project (few deps, single component, no persistence) | Trivial project (script, one-off, experiment) |
| Lifecycle | LC01 → LC02 → LC03 | PLAN → REQS → PRODUCE → DELIVER | PRODUCE → DELIVER |
| `.gse/` state | 4 files (config, profile, status, backlog) + plan.yaml | 4 files + plan.yaml | 1 file only (`status.yaml` with inline profile + task list) |
| Git strategy | worktree (sprint + feature branches) | branch-only (single feature branch, no sprint branch) | direct commit (no branch creation) |
| Sprint artefacts | Full set (plan-summary, reqs, design, tests, review, compound) | reqs.md only | None |
| Health dashboard | 8 dimensions | 3 of 8 (test_pass_rate, review_findings, git_hygiene) | None |
| Complexity budget | Tracked | Not tracked | Not tracked |
| Decision tiers | Full P7 assessment | Simplified (Auto + Gate only, no Inform) | Gate only (security/destructive actions) |
| REQS guardrail | Hard (mandatory) | Hard (mandatory, reduced ceremony) | Not enforced |
| TESTS guardrail | Hard (formal strategy required) | Soft (auto-generated strategy, Inform) | Not enforced |
| REQS ceremony | Full: elicitation + REQs + quality checklist + coverage analysis | Reduced: elicitation + REQs (no quality checklist, no coverage analysis) | None |
| DESIGN / PREVIEW | Yes (conditional) | No | No |
| REVIEW / COMPOUND | Yes | No | No |

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
| **LC02** | Development Sprint | `REQS > DESIGN > PREVIEW > TESTS > PRODUCE > REVIEW > [FIX] > DELIVER` | PRODUCE creates feature branches + worktrees. REVIEW uses branch diffs. `[FIX]` is conditionally inserted by the orchestrator after REVIEW only if findings with severity HIGH or MEDIUM exist — otherwise omitted. DELIVER merges, tags, and archives `.gse/plan.yaml` to `plan-summary.md`. |
| **LC03** | Capitalization | `COMPOUND > INTEGRATE` | Post-sprint learning loop. Runs on `main` after delivery. Natural moment for proactive LEARN proposals. |

> **Note on PLAN:** PLAN is **not** part of the LC02 sequence. It is cross-cutting (P5). The orchestrator maintains `.gse/plan.yaml` as a living document throughout all phases, monitoring coherence non-blockingly at each activity transition (budget pressure, scope drift, velocity risk — all Inform-tier). The user can invoke `/gse:plan --tactical` at any time to explicitly re-plan.

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
  │  foundational commit on main (required for branching)
  v
┌─── LC01: Discovery & Planning ──────────────────────────┐
│    GO > COLLECT > ASSESS > PLAN                         │
│    PLAN creates branch: gse/sprint-NN/integration      │
│         ↑ PLAN callable at any point                    │
└──────────────────────────────────────┬──────────────────┘
                                       │
                                       v
┌─── LC02: Development Sprint ────────────────────────────┐
│    REQS > DESIGN > PREVIEW > TESTS >                     │
│    PRODUCE > REVIEW > [FIX] > DELIVER                   │
│                                                          │
│    plan.yaml updated at each transition (non-blocking)   │
│    PRODUCE: branch + worktree per task                   │
│    REVIEW: diff-based on feature branch                  │
│    [FIX]: conditional — inserted if HIGH/MEDIUM findings │
│    DELIVER: merge → sprint → main, tag, cleanup,         │
│             archive plan.yaml → plan-summary.md          │
│                                                          │
│         ↑ PLAN callable at any point (/gse:plan)        │
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

### 14.0.1 Activity Ceremony by Expertise Level

Activities MUST be executed as **separate, identifiable steps** regardless of the user's expertise level. The agent adapts **communication** (P9) and **artefact formality**, not **lifecycle structure**. Fusing or skipping activities without explicit specification is a methodology violation.

The following table defines the minimum ceremony per expertise level for Full mode:

| Activity | Beginner | Intermediate | Advanced/Expert |
|----------|----------|--------------|-----------------|
| **COLLECT** | Agent runs silently, reports findings in plain language | Agent reports summary | Agent reports summary |
| **ASSESS** | Agent explains gaps in plain language, one at a time | Grouped summary | Grouped summary |
| **PLAN** | Agent proposes plan in plain language, Gate approval | Plan summary, Gate | Plan summary, Gate |
| **REQS** | Conversational elicitation (Step 0) → formal reqs (hidden IDs) → quality checklist | Full REQS flow, IDs visible | Full REQS flow |
| **DESIGN** | Agent explains structure in plain language, Gate | Design artefact, Gate | Design artefact, Gate |
| **PREVIEW** | Visual artefact (HTML mockup or wireframe), Gate | Visual artefact, Gate | Optional (agent proposes, user can skip) |
| **TESTS** | Strategy explained in plain language, no jargon | Strategy artefact | Strategy artefact |
| **PRODUCE** | Agent builds, explains key choices contextually (P14) | Agent builds, Inform on choices | Agent builds, Auto on low-risk |
| **REVIEW** | Guided walkthrough (step-by-step with user) | Summary + findings | Summary + findings |
| **DELIVER** | Agent explains merge in plain language, Gate | Gate on merge strategy | Gate on merge strategy |

**Non-fusion rule:** The agent MUST NOT merge two activities into a single conversational turn (e.g., combining DESIGN and PREVIEW into one message, or running TESTS strategy inside PRODUCE). Each activity produces its own output and, where applicable, its own artefact. The user must be able to identify which activity is being performed.

**Exceptions:**
- **Micro mode** and **Lightweight mode** have reduced lifecycles (see Section 13.2) — the table above applies to Full mode only.
- **COLLECT + ASSESS** may be presented as a single "analysis" step for beginners if the project is empty (nothing to collect), but both must run internally.
- If a user explicitly requests acceleration ("just build it"), the agent records a **planning debt** item (P5) and may proceed, but must not silently drop activities.

### 14.1 Sprint 1 vs Sprint N+1

The `/gse:go` orchestrator adapts its flow depending on project maturity:

| Aspect | Sprint 1 (new project) | Sprint N+1 (continuing) |
|--------|----------------------|------------------------|
| **COLLECT** | Internal finds nothing (or very little). Agent suggests external source scan. | Internal finds existing artefacts, previous sprint results. |
| **ASSESS** | Starts from project goals only. No baseline to compare against. | Compares against previous sprint health, reviews, and delivery. |
| **PLAN** | Creates sprint branch from `main`. No previous velocity data. Agent asks more Gate questions about scope. | Uses previous sprint velocity to calibrate budget. Detects unfinished tasks from previous sprint. |
| **HUG** | Full interview (all 13 dimensions). | Asks only if profile needs updating ("Anything changed since last time?"). |
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
| `.gse/` does not exist + project is empty | **Automatically execute** `/gse:hug` inline (LC00). No diagnostic output, no status table. User sees the language question as the very first interaction. |
| `.gse/` exists | Read `status.yaml` → proceed to Step 1.5 (recovery) → Step 2 |

**"Project files"** excludes tool/IDE dirs: `.cursor/`, `.claude/`, `.gse/`, `.git/`, `.vscode/`, `.idea/`, `.fleet/`, `node_modules/`, `__pycache__/`, `.venv/`, `target/`, `dist/`, `build/`.

**Step 1.5 — Recovery check:**

If `.gse/` exists, scan for unsaved work from a previous session that ended without `/gse:pause`:
1. Check all active worktrees listed in `config.yaml → git.worktree_dir` and the main directory for uncommitted changes
2. If found: present a Gate decision — **Recover** (auto-commit checkpoint) / **Review first** (show diff) / **Discard** (confirm twice) / **Skip** (leave uncommitted). For beginners: "I found unsaved work from a previous session. Should I save it before we continue?"
3. If nothing found: proceed to Step 1.6

**Step 1.6 — Dependency vulnerability check:**

If `config.yaml → dependency_audit: true` (default for projects with package manifests):
1. Run the appropriate audit command (`npm audit` / `pip-audit` / `cargo audit` / equivalent)
2. If **critical** vulnerabilities found → Soft guardrail: warn and suggest update
3. If no vulnerabilities or low-severity only → proceed silently to Step 2

This runs at **every session start**, not just during `/gse:tests`, to catch vulnerabilities disclosed between sprints.

**Step 1.7 — Git baseline verification:**

If `config.yaml → git.strategy` is `worktree` or `branch-only`:
1. Verify `main` has at least one commit: `git rev-parse --verify main`
2. If this fails → **Hard guardrail**: auto-fix by committing `.gitignore` (or creating it if missing): `git add .gitignore && git commit -m "chore: initialize repository"`. For beginners: "I need to save a first checkpoint in version control before we can organize the work properly."
3. If `main` exists → proceed to Step 2

This is a **safety net** for cases where HUG Step 4 was interrupted or the foundational commit was not created. Without a commit on `main`, all branching operations (sprint branch, feature branches) will fail.

**Step 2 — Determine next action:**

The orchestrator reads `.gse/plan.yaml` when available. If `plan.yaml` exists with `status: active`, the orchestrator uses `workflow.active` to determine the next activity. This is more robust than checking for the existence of individual artefact files. If `plan.yaml` is absent (Micro mode or pre-v0.20 projects), the orchestrator falls back to file-existence checks.

Evaluate states **in order** — the first matching row wins.

| Current state | Next action |
|--------------|-------------|
| No sprint + project is **greenfield** (no source files after standard exclusions) AND no `INT-001` intent artefact exists | Enter **Intent Capture** (Step 5). After intent captured and the `intent` artefact is written → proceed to **complexity assessment** (Step 6) to determine mode. Applies to all expertise levels; tone and cadence are adapted via P9. |
| No sprint (after intent-first if applicable) | **Complexity assessment** (Step 6): scan structural signals (dependencies, persistence, entry points, multi-component, CI/CD, git maturity, tests), recommend mode (Gate). Based on chosen mode: Micro → PRODUCE, Lightweight → PLAN, Full → LC01 (`COLLECT` > `ASSESS` > `PLAN`). |
| `plan.yaml` exists, `status: draft` | Resume `PLAN` |
| `plan.yaml.workflow.active == reqs` | Start `REQS` — begins with **conversational elicitation** (Step 0) to capture user intent in natural language, then **test-driven requirements** with testable acceptance criteria (Given/When/Then) and open technical questions, then **quality assurance checklist** (Step 7, ISO 25010 inspired) verifying NFR completeness. **Hard guardrail: PRODUCE MUST NOT start until REQS exist.** |
| `plan.yaml.workflow.active == design` | Start `DESIGN`. If tasks do not involve architecture decisions, move `design` to `workflow.skipped` and advance to PREVIEW or TESTS. |
| `plan.yaml.workflow.active == preview` | Start `PREVIEW` — show mockup/prototype for user validation before coding. For CLI/API/data/embedded: `preview` should already be in `workflow.skipped`. |
| `plan.yaml.workflow.active == tests` | Start `TESTS --strategy` — define test pyramid: verification tests (from DESIGN) + validation tests (from REQS acceptance criteria). |
| `plan.yaml.workflow.active == produce`, none in-progress | Start `PRODUCE` on first planned TASK |
| `plan.yaml.workflow.active == produce`, tasks `in-progress` | Resume `PRODUCE` on current task |
| `plan.yaml.workflow.active == review` | Start `REVIEW` (requires test evidence — will block if tests were skipped) |
| `plan.yaml.workflow.active == fix` | Start `FIX` |
| `plan.yaml.workflow.active == deliver` | Start `DELIVER` (requires REQ→TST coverage for must-priority requirements) |
| Sprint plan status is *completed* and `/gse:compound` has not run | Start LC03 (`COMPOUND` > `INTEGRATE`) |
| Sprint plan status is *completed* and `/gse:compound` + `/gse:integrate` are done | Propose next sprint → LC01. The number of the sprint in progress only advances when `/gse:plan --strategic` promotes the successor sprint. Until then, the current sprint remains the delivered one, frozen (see *Sprint Freeze* guardrail). |
| Sprint stale (> `lifecycle.stale_sprint_sessions` sessions without progress) | Stale detection (Step 3) |

**Lifecycle guardrails (mode-differentiated):**
1. **No PRODUCE without REQS (Full and Lightweight)** — No TASK can move to `in-progress` unless at least one REQ- artefact with testable acceptance criteria is traced to it. In Full mode, the quality assurance checklist (Step 7) must also have been run. REQS is test-driven: acceptance criteria ARE the future validation test specs. **Exception:** Micro mode and `artefact_type: spike`.
2. **No PRODUCE without test strategy (Full only)** — The test approach (verification from DESIGN + validation from REQS acceptance criteria) must be defined before coding starts. Test strategy comes AFTER DESIGN and PREVIEW. In Lightweight mode, a minimal test strategy is auto-generated at PRODUCE time (Soft guardrail — Inform tier). **Exception:** Micro mode and `artefact_type: spike`.
3. **Sprint Freeze (Hard, all modes except Micro)** — Once a sprint has been delivered, its plan transitions to the *completed* state. From that point on, the sprint is **frozen** to ensure sprint closure immutability: no new task may be added to it and no existing task within it may be transitioned forward (e.g., from *planned* to *in-progress*, or from *in-progress* to *review*). Activities that would otherwise write to a frozen sprint (`/gse:task`, `/gse:produce`, `/gse:fix`, `/gse:review`) MUST present a Gate with exactly three options: *(1) Start next sprint now* — the agent promotes the next sprint via the standard opening sequence (`/gse:plan --strategic` in Lightweight mode; `/gse:collect` > `/gse:assess` > `/gse:plan --strategic` in Full mode), then executes the intended activity in the newly opened sprint; *(2) Cancel* — abort the current activity with no state change; *(3) Discuss*. Option 1 is the default. **No "amend closed sprint" escape hatch is offered** — the sanctioned way to capture complementary work is to open a successor sprint (e.g., titled *"Sprint N+1 — Complementary tasks"*). **Exempt activities** (operate legitimately on frozen sprints): `/gse:compound`, `/gse:integrate`, `/gse:pause`, `/gse:resume`, `/gse:go`, `/gse:status`, `/gse:health`, `/gse:backlog`, `/gse:learn`, `/gse:hug`, `/gse:collect`, `/gse:assess`, `/gse:plan --strategic`, `/gse:deploy`, `/gse:deliver`.

**Decision tier override:**
4. **Supervised mode** — When `decision_involvement: supervised`, ALL technical choices during PRODUCE are escalated to **Gate-tier** decisions. The agent presents options and waits for user confirmation.

**Step 3 — Stale sprint detection:**

```
**Question:** Sprint N has had X sessions without progress. What would you like to do?

> A "session" is an invocation of `/gse:go` or `/gse:resume`. A "progression" is any TASK moving from one status to the next (open→planned, planned→in-progress, in-progress→review, review→fixing, fixing→done, done→delivered, etc.). The counter resets when any TASK progresses.

**Options:**
1. Resume — pick up where we left off
2. Partial delivery — deliver completed tasks, defer the rest to backlog pool
3. Discard — abandon the sprint, move all tasks back to pool, delete branches
4. Discuss
```

**Step 4 — Failure handling:**

If an activity fails (test failure, merge conflict, tool error):
1. Save current state to checkpoint
2. Report the error with the agent's assessment of the cause
3. Propose options (Gate): retry, skip (if skippable), pause, discuss
4. Never silently continue after a failure

**Step 5 — Intent Capture (greenfield projects, all expertise levels):**

When the project is **greenfield** (no source files after standard exclusions) and **no intent artefact exists yet** (no `INT-001` in the project), the orchestrator enters a conversational capture mode before the formal lifecycle. Applies to **all expertise levels** — the trigger is project state, not user profile. Cadence and tone are adapted via P9 (one question at a time for beginners; grouped elicitation for experts).

1. **Elicit intent** in plain language: *"Describe what you'd like to build or achieve."* Let the user express freely — no technical framing.
2. **Reformulate and validate**: *"If I understand correctly, you want: [list]. Correct?"* Iterate until the user confirms.
3. **Write the intent artefact** `INT-001` to the canonical location `docs/intent.md`. The artefact includes YAML frontmatter (`id: INT-001`, `artefact_type: intent`, `sprint: 0`, `status: approved`) and four mandatory sections: *Description (verbatim user statement)*, *Reformulated understanding*, *Users*, *Boundaries* (explicit out-of-scope items). An optional fifth section *Open questions* lists ambiguities to resolve in downstream activities. Each question is a structured entry with the fields defined in P6 (`id: OQ-NNN`, `question`, `resolves_in: ASSESS | PLAN | REQS | DESIGN`, `impact: scope-shaping | behavioral | architectural | cosmetic`, `status: pending`, `raised_at: INT-001`). These questions are auto-detected at the entry of their target activity via the activity-entry scan (see P6 "Activity-entry scan"). The intent artefact is committed to git and becomes the traceability root — downstream REQ, TASK, and gap artefacts may carry `traces.derives_from: [INT-001]`.
4. **Translate to initial backlog items** (no jargon): the agent converts the validated intent into concrete TASK goals in `backlog.yaml`. Each seeded TASK carries `traces.derives_from: [INT-001]` preserving the intent → backlog provenance.
5. After intent is captured and backlog items created, proceed to **Step 6 (Complexity Assessment)** to determine the appropriate mode. The mode determines the lifecycle path (Micro → PRODUCE, Lightweight → PLAN, Full → COLLECT). Present each activity in plain language for beginners; direct technical terms for intermediate/expert.
6. **Exit condition:** the user can skip Intent Capture at any time by saying *"I know the process"* / *"no need, let's proceed"* / equivalent. If skipped, no `intent.md` is written and the agent proceeds directly to Step 6. An Inform note is logged noting intent was declined.
7. **Pivot / re-capture:** if at a later date the user wants to replace or evolve the intent (project pivot, scope reset), the existing `INT-001` is archived to `docs/archive/intent-vNN.md` and a new `INT-002` is created with the updated content. Downstream artefacts pointing to the old `INT-001` are not rewritten — the archive preserves the historical trace.

```yaml
# In config.yaml → lifecycle:
  stale_sprint_sessions: 3            # sessions without progress before stale detection
```

---

## 15. Glossary

### Essential Concepts (Start Here)

If you are new to GSE-One, these 20 concepts form the minimum vocabulary to get started. All are defined in the full glossary below:

| # | Concept | One-line summary |
|---|---------|-----------------|
| 1 | **Sprint** | A time-boxed work cycle with a complexity budget |
| 2 | **Backlog** | The list of all work items (TASKs), planned or not |
| 3 | **TASK** | A single work item in the backlog, tracked from creation to delivery |
| 4 | **Artefact** | Any project file — code, requirements, design, tests, config |
| 5 | **REQ (Requirement)** | A user story describing what the system should do, with testable acceptance criteria |
| 6 | **Acceptance criteria** | Measurable conditions (Given/When/Then) that define when a requirement is met |
| 7 | **TST (Test)** | A test derived from a requirement or design decision |
| 8 | **DES (Design decision)** | An architectural choice documented with rationale |
| 9 | **Traceability** | Links between artefacts: requirement → design → test → code |
| 10 | **Guardrail** | Automatic protection that blocks risky actions (e.g., coding without requirements) |
| 11 | **Gate decision** | A high-impact decision that requires your explicit approval |
| 12 | **Health score** | A 0–10 quality metric across 8 dimensions (tests, coverage, debt...) |
| 13 | **Lifecycle phases** | LC00 (onboarding) → LC01 (discovery) → LC02 (development) → LC03 (capitalization) |
| 14 | **Worktree** | An isolated workspace for developing one task without affecting others |
| 15 | **Feature branch** | A git branch where a single task is developed |
| 16 | **Review** | Multi-perspective quality check of completed work, including AI self-review |
| 17 | **Complexity budget** | A point-based limit on the total work a sprint can absorb. One point measures **coupled effort + complexity for the AI + user pair** (code complexity added + AI generation + human review). Indicative temporal anchor: 1 pt ≈ 1 pair-session hour; 10-pt sprint ≈ 1-3 working days |
| 18 | **Confidence level** | How certain the agent is about a claim: Verified, High, Moderate, or Low |
| 19 | **HUG** | The profiling activity that teaches the agent who you are and how to work with you |
| 20 | **Spike** | A time-boxed experiment to answer a technical question — code is thrown away |

### Full Glossary

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
| **Complexity budget** | Finite capacity for work within a sprint, measured in complexity points. A point captures **coupled effort + complexity for the AI + user pair**: code complexity added, AI generation effort, human review effort (treated as a single scalar because entangled in practice). Indicative temporal anchor: 1 pt ≈ 1 pair-session hour (solo human ~0.5-1 day; speedup ratio 5-20× depending on domain) |
| **Composite risk** | When 3 or more risk dimensions are Moderate, the decision escalates to Gate tier — multiple moderate risks compound |
| **Guardrail** | Agent-initiated protection against high-cost decisions, calibrated by user expertise |
| **Health score** | Composite metric (0–10) reflecting project quality across 8 dimensions |
| **Preview** | Lightweight simulation of a planned artefact before production begins |
| **Decision journal** | Persistent log of all non-trivial decisions with rationale and consequence analysis |
| **Sprint integration branch** | Git branch `gse/sprint-NN/integration` that collects all feature branches for a sprint |
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
| **Lightweight mode** | Reduced lifecycle for simple projects: PLAN → REQS → PRODUCE → DELIVER. Branch-only git, 3 health dimensions, reduced REQS ceremony (no quality checklist), auto-generated test strategy. Selected by complexity assessment, not file count |
| **Adopt mode** | `/gse:go --adopt` — onboarding flow for existing projects, scans and initializes without destroying existing state |
| **Backlog** | Unified, ordered list of all work items (TASK). Items are either in the pool (unplanned) or assigned to a sprint. Syncs with GitHub Issues when enabled |
| **Planning debt** | Tracked item when planning is skipped under pressure — reviewed during next `/gse:compound` retrospective |
| **Coolify** | Self-hosted PaaS (Platform as a Service) used by `/gse:deploy` for application deployment on Hetzner servers. Includes Traefik reverse proxy and Let's Encrypt SSL. |
| **Deploy state** | The `.gse/deploy.json` file tracking infrastructure phases, server details, Coolify configuration, and application deployment status |
| **Pool** | Subset of the backlog containing unplanned items (`sprint: null`) — candidates for future sprints |
| **Artefact type** | Classification of what a TASK produces: code, requirement, design, test, doc, config, or import |
| **Mono-repo** | GSE-One assumes a single repository per project. Recommended for multi-component projects |
| **Confidence level** | Tag on every agent assertion: Verified (factually checked), High (established knowledge, not project-verified), Moderate (reconstructed from patterns), Low (uncertain) |
| **Verification gate** | Proof requirement for critical assertions — code must be executed, libraries must be installed, APIs must be confirmed |
| **Devil's advocate** | Adversarial self-review perspective activated during `/gse:review` — hunts hallucinations, challenges assumptions, checks temporal validity |
| **User pushback** | Mechanism that detects passive acceptance and proactively challenges the user to engage critically with decisions |
| **AI integrity** | Health sub-dimension measuring unverified assertions, hallucination findings, and user engagement level |
| **Test pyramid** | Distribution of test types (unit/integration/E2E/visual/acceptance) calibrated by project domain |
| **Test campaign** | A single execution of the test suite, producing a traceable report (prefix `TCP-`, type `test-campaign`) with results, coverage, and evidence references. Each campaign carries its own ID so it can be cited independently of its file path and counted on the dashboard. |
| **Test evidence** | Two related meanings: (a) the raw artefacts produced by a test run — screenshots, videos, logs, coverage reports stored under `tests/evidence/sprint-NN/TASK-NNN/`; (b) the structured `test_evidence` field on each TASK in `backlog.yaml` that records execution status, campaign reference, pass rate, code coverage, and summary. Guardrails and reviews read the TASK field; humans consult the raw artefacts. |
| **Visual testing** | Automated screenshot capture and analysis during E2E tests, leveraging multimodal AI for defect detection |
| **Code coverage** | Percentage of code exercised by tests — tracked as a health sub-dimension |
| **Spike** | Exploratory experiment created via `/gse:task --spike`. Complexity-boxed (max 3 points), non-deliverable (branch deleted after completion), bypasses REQS/TESTS guardrails. Must produce a DEC- artefact documenting question, approach, and answer. If reusable code emerges, a normal TASK is created |
| **Acceptance criteria** | Measurable conditions attached to a requirement, expressed in Given/When/Then (BDD) format. These criteria ARE the specification for validation tests — each criterion generates at least one TST- artefact |
| **Lifecycle phases (LC00–LC03)** | The four phases of a GSE-One project cycle: LC00 (onboarding — `/gse:hug`), LC01 (discovery & planning — `COLLECT` > `ASSESS` > `PLAN`), LC02 (development — `REQS` > `DESIGN` > `PREVIEW` > `TESTS` > `PRODUCE` > `REVIEW` > `[FIX]` > `DELIVER` — where `[FIX]` is conditionally inserted if REVIEW produces HIGH/MEDIUM findings), LC03 (capitalization — `COMPOUND` > `INTEGRATE`) |
| **Intent Capture** | Conversational capture flow triggered when a project is **greenfield** (no source files after standard exclusions) and no intent artefact exists. Applies to all expertise levels — tone and cadence adapted via P9. Produces `INT-001` at the canonical path `docs/intent.md` (four mandatory sections: Description verbatim, Reformulated understanding, Users, Boundaries; optional Open questions). Serves as the traceability root for downstream REQ, TASK, and gap artefacts via `traces.derives_from: [INT-001]`. Replaced the pre-v0.28 "Intent-first mode" (which was beginner-only and did not produce a formal artefact) |
| **Intent artefact (`INT-`)** | Project-level artefact capturing the user's plain-language intent for what they want to build or achieve. Unique per project (one `INT-001` by default). On project pivot, the current artefact is archived to `docs/archive/intent-vNN.md` and a new `INT-002` is created. Referenced by downstream artefacts via `traces.derives_from: [INT-NNN]` |
| **Open Question (`OQ-`)** | A structured entry representing an ambiguity raised in an artefact that cannot be resolved immediately. Each entry carries `id`, `question`, `resolves_in` (the lifecycle activity where it will be addressed), `impact` (scope-shaping / behavioral / architectural / cosmetic), `status` (pending / resolved), provenance (`raised_at`), and, once resolved, resolution metadata (`resolved_at`, `resolved_in`, `answer`, `answered_by`, `confidence`, `traces`). See P6 for the full schema. Consumed automatically by the **activity-entry scan**: each of `/gse:assess`, `/gse:plan`, `/gse:reqs`, `/gse:design` scans for pending OQs with `resolves_in: <self>` at Step 0 and resolves them per the user's `decision_involvement` mode (autonomous / collaborative / supervised). |
| **Activity-entry scan** | Transversal rule (spec P6) executed at the first step of `/gse:assess`, `/gse:plan`, `/gse:reqs`, `/gse:design`. The agent walks the project's intent artefact and all active-sprint artefacts for pending Open Questions (`OQ-`) whose `resolves_in` matches the current activity. If ≥ 1 match, the activity enters the **Open Questions Gate** before proceeding. Gate behavior is calibrated by the user's `decision_involvement` profile field: `autonomous` (agent pre-answers, Gate only for high-impact questions), `collaborative` (Gate with agent-proposed answer + rationale), `supervised` (neutral Gate, no pre-answer). |
| **Supervised mode** | When `decision_involvement: supervised` in the profile, ALL technical choices during PRODUCE are escalated to Gate-tier decisions — the agent presents options and waits for confirmation |
| **Micro mode** | Minimal lifecycle for trivial projects (scripts, one-off tasks): `PRODUCE` > `DELIVER`, direct commit, 1 state file, no REQS/TESTS guardrails, no health tracking. Selected by complexity assessment, not file count |
| **Complexity assessment** | Structural analysis performed by the orchestrator during `/gse:go` to recommend a project mode (Micro/Lightweight/Full). Scans 7 structural complexity signals: (1) dependencies (direct dep count from manifests), (2) persistence (ORM, SQL, DB config), (3) entry points (routes, CLI commands), (4) multi-component (multiple manifests, monorepo), (5) existing tests (test directories/files), (6) CI/CD (workflow files, Docker), (7) git maturity (commits, branches, contributors). Source file count is not a complexity signal — it is used only as a trivialiy pre-filter for Micro mode detection. Presented as a Gate decision — the user confirms or overrides |
| **Stale sprint** | A sprint where no TASK has progressed for more than `lifecycle.stale_sprint_sessions` sessions (default: 3). Triggers a Gate decision: resume, partial delivery, discard, or discuss |
| **Design debt** | Health sub-dimension measuring accumulated design-level issues. Computed from review findings with the architect perspective: 10 − (HIGH × 2.0 + MEDIUM × 1.0 + LOW × 0.5), floor 0 |
| **Regression test** | A test verifying that previously passing functionality still works after new changes. During `/gse:review`, the full test suite is compared against the previous sprint's results — newly failing tests are flagged `[REGRESSION]` with severity HIGH |
| **Quality gap** | A missing or incomplete detail in a non-functional requirement, identified by the ISO 25010-inspired quality checklist (Step 7 of `/gse:reqs`). Gaps are classified as HIGH, MEDIUM, or LOW priority and may generate corresponding tests in the test strategy |
| **Dependency audit** | Automated vulnerability scan of project dependencies (e.g., `npm audit`, `pip-audit`), run at every session start. Critical vulnerabilities trigger a Soft guardrail |
| **Quality coverage matrix** | Summary table in `reqs.md` showing which quality dimensions (Performance, Security, Reliability, Usability, Maintainability, Accessibility, Compatibility) are covered by requirements and where gaps exist |
| **plan.yaml** | The living sprint plan stored in `.gse/plan.yaml`. Contains sprint goal, selected tasks, workflow tracking (`expected`/`completed`/`active`/`pending`/`skipped`), budget, non-blocking coherence monitoring, and risks. Maintained by the orchestrator at every activity transition. Archived to `docs/sprints/sprint-{NN}/plan-summary.md` at delivery |
| **plan-summary.md** | Read-only archive of `.gse/plan.yaml` generated by DELIVER at end of sprint. Used for human reference, COMPOUND process-deviation analysis, and sprint history. Never read by the orchestrator for decision-making |

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
DEPLOYMENT          /gse:deploy
QUALITY             /gse:review    /gse:fix
CAPITALIZATION      /gse:compound  /gse:integrate
AD-HOC              /gse:task
```

**Total: 23 commands** | Canonical prefix: `/gse:`

---

## Appendix B — Cost Assessment Grid for Maintenance Work

Used by `/gse:plan` and `/gse:task` to size maintenance activities (refactoring, tests, documentation, renaming, bug-fixing, and other upkeep work). Replaces the pre-v0.34 "zero-cost items" blanket rule that classified all such work as free — in practice, large-scope maintenance consumes real pair effort and must be budgeted.

### Four criteria the agent evaluates

| Criterion | Question the agent asks |
|-----------|-------------------------|
| **Fan-out** | How many files / modules / test files are touched by this work? |
| **Review burden** | How much time will the user spend reading the change to validate it? |
| **Rework risk** | How likely is this to need multiple iterations (the first attempt misses edge cases)? |
| **Coupling** | Does this introduce new connections between modules, or expose new surfaces? |

Each criterion is assessed as **trivial** or **non-trivial** based on project context (a small project's "whole codebase refactor" may still be trivial; a large project's "rename one public API" may be substantial).

### Scale

| Verdict | Point cost | Examples |
|---------|-----------|----------|
| All four criteria trivial | **0 pt** | Rename a local variable; fix a typo in a comment; write one docstring; add a blank line for readability; format a single file |
| Exactly one criterion non-trivial | **1 pt** | Add 10 unit tests for an existing function; refactor a single module (no public API change); update the README for one feature; rename an internal helper used in 3-5 places |
| Two or more criteria non-trivial, OR structural impact | **2-5 pt** | Rewrite documentation for a whole subsystem (2 pt); refactor a public API across 30+ call sites (3 pt); build an integration test harness for a new subsystem (3 pt); restructure error handling across all modules (4-5 pt) |

### Usage

- **At planning time (`/gse:plan`):** the agent sizes each backlog item using this grid if the item is maintenance-flavored.
- **At task-creation time (`/gse:task`):** the agent applies the grid to estimate the complexity of ad-hoc tasks.
- **At review time (`/gse:review`):** if actual pair effort diverged significantly from the estimate, the gap is surfaced as a learning for next sprint's calibration.
- **User override:** the agent presents its estimate with a brief justification. The user may override via a Gate if the assessment feels off.

### Simplification credit (unchanged)

Removing code or dependencies still earns **negative points** (1-2 pt credit) regardless of scale — removal reduces future pair effort and frees sprint budget. See P10 "Simplification credit" and spec §8.1.

---

## Appendix C — Maintainer Guide

This section helps anyone maintaining, extending, or debugging GSE-One understand the architecture and avoid cascading inconsistencies.

### File hierarchy and propagation rules

```
gse-one-spec.md                    ← Authoritative source of truth
  ↓ (principles extracted to)
src/principles/*.md                ← Detailed principle rules (P1-P16)
  ↓ (summarized into)
src/agents/gse-orchestrator.md     ← Agent context (routing + global rules)
  ↓ (activities implemented as)
src/activities/*.md                ← Skill files (execution details)
  ↓ (generated into)
plugin/                            ← Deployable plugin (Claude Code + Cursor)
```

### Discipline: what goes where

| Content type | Location | Rationale |
|---|---|---|
| **Routing decisions** (which activity next) | Orchestrator | Loaded in every session |
| **Global rules** (beginner filter, project layout, recovery) | Orchestrator | Applied across all skills |
| **Principle summaries** (1-3 lines per P) | Orchestrator | Agent needs them for risk/communication decisions |
| **Execution details** (how to run an activity, pre-checks) | Skill files | Loaded on-demand when the activity is invoked |
| **Detailed rules** (full rule sets, examples, edge cases) | Principle files | Reference documentation |
| **Canonical definitions** (enums, formats, lifecycle phases) | Spec | Single source of truth |

### Modification checklist

When changing any concept, verify alignment across all layers:

1. **Spec** (`gse-one-spec.md`) — update the canonical definition
2. **Principle file** (`src/principles/*.md`) — update detailed rules if applicable
3. **Orchestrator** (`src/agents/gse-orchestrator.md`) — update summary if it affects routing or global behavior
4. **Skill files** (`src/activities/*.md`) — update execution details if applicable
5. **Guardrails** (`src/principles/guardrails.md`) — update if severity levels change
6. **Regenerate** — run `python gse_generate.py --clean --verify` to rebuild the plugin
7. **Cross-audit** — verify no contradictions between spec, orchestrator, and skills

### Common cascade patterns

| If you change... | Also check... |
|---|---|
| An enum (e.g., verbosity scale) | Spec table, HUG skill, profile YAML example, orchestrator |
| A lifecycle phase ordering | Orchestrator decision tree, go.md decision tree, spec Section 14.3 |
| A guardrail severity level | guardrails.md, orchestrator lifecycle guardrails, go.md, affected skill |
| A principle rule number | Principle file, spec, any skill that references "(P{N})" |
| The project layout | Orchestrator Project Layout, spec Section 12.1, affected skills |
| A TASK artefact_type | Spec Section 4, task.md, produce.md, guardrails.md |
