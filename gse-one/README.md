<h1 align="center">GSE-One</h1>
<h2 align="center">Built by AI.<br>Governed by Humans.</h2>

GSE-One is an AI engineering companion that brings structured software development lifecycle (SDLC) management to coding agents. It works as a plugin for **Claude Code**, **Cursor**, and **opencode**, guiding projects through requirements, design, testing, production, review, and knowledge transfer — with adaptive risk analysis and methodology guardrails.

<p align="center">
  <img src="../assets/images/logo-gse-geni-with-shield-landscape_4x_slogan.png" width="700" alt="GSE-One — Built by AI, Governed by Humans">
</p>

Mono-plugin architecture — cross-platform parity. See [CHANGELOG](../CHANGELOG.md) for version history.

## What is GSE-One?

GSE-One is designed for users of **any expertise level** — from beginners building their first project to experienced engineers managing complex applications. The agent adapts its language, decisions, and level of autonomy to your profile. 23 commands covering planning, requirements, design, production, quality, delivery, deployment, and capitalization.

**v0.14.0 highlights:**
- **Interactive QCM** — clickable options (AskUserQuestion / Cursor clarifying questions) instead of numbered text lists
- **Language-first onboarding** — multilingual language question before anything else, with system locale detection
- **Test-driven requirements** — every requirement includes testable acceptance criteria (Given/When/Then)
- **Lifecycle guardrails** — no coding without requirements and test strategy (REQS → DESIGN → PREVIEW → TESTS → PRODUCE)
- **Beginner output filter** — all jargon translated to plain language for non-IT users
- **Three project modes** — Micro (< 3 files), Lightweight (3-4), Full (≥ 5)
- **Spike mode** — complexity-boxed experiments that bypass REQS/TESTS guardrails
- **Cross-sprint regression scan** — full test suite comparison during REVIEW
- **Dependency vulnerability check** — audit at every session start
- **Sprint archival** — automatic backlog compaction and sprint directory archival during COMPOUND
- **Monorepo sub-domains** — per-directory test pyramid calibration
- **Resilience** — YAML validation, context overflow prevention, graceful degradation

## Quick Start

### 1. Install the plugin (see Installation below)

### 2. Type `/gse:go`

The agent detects your project state and proposes the next step:
- **New project?** The agent runs an onboarding interview (`/gse:hug`) to understand your expertise and goals
- **Existing project without GSE-One?** The agent proposes to adopt it non-destructively (scan, set baseline, initialize)
- **Already set up?** The agent picks up where you left off — whether that's planning, producing, reviewing, or delivering

### 3. Follow the agent's guidance

GSE-One orchestrates the full lifecycle: `COLLECT > ASSESS > PLAN > REQS > DESIGN > PREVIEW > TESTS > PRODUCE > REVIEW > FIX > DELIVER > COMPOUND`. You don't need to memorize the commands — the agent proposes the next activity at each step.

## Installation

### Quick Start (recommended)

Clone the repository and run the interactive installer:

```bash
git clone https://github.com/nicolasguelfi/gensem.git
cd gensem
python3 install.py
```

The installer detects your OS (macOS, Linux, Windows), available platforms (Claude Code, Cursor), and guides you through the installation interactively. It supports plugin mode (with scope selection) and non-plugin mode for both platforms.

For non-interactive installation, use CLI flags:

```bash
# Claude Code — plugin, project scope (recommended)
python3 install.py --platform claude --mode plugin --scope project

# Cursor — plugin, global
python3 install.py --platform cursor --mode plugin

# opencode — plugin (global, ~/.config/opencode/)
python3 install.py --platform opencode --mode plugin

# opencode — non-plugin (project .opencode/)
python3 install.py --platform opencode --mode no-plugin --project-dir /path/to/project

# Both Claude + Cursor
python3 install.py --platform both --mode plugin --scope user

# All three platforms at once
python3 install.py --platform all --mode plugin --scope user

# Uninstall
python3 install.py --uninstall --platform claude --mode plugin
```

For the fastest opencode onboarding (install + create project + start), see [INSTALL-OPENCODE.md](../INSTALL-OPENCODE.md) at the repo root.

Run `python3 install.py --help` for all options.

### Verify

Type `/gse:go` in Claude Code, `/gse-go` in Cursor or opencode. The agent should respond and detect your project state.

### Marketplace (when available)

Not yet operational. After approval:
```bash
# Claude Code
claude plugin install gse-one

# Cursor — search "gse-one" in /add-plugin

# opencode — no marketplace; install.py handles deployment
```

## Commands (23)

| Category | Commands | What they do |
|----------|----------|-------------|
| **Orchestration** | `/gse:go` | Detect project state, propose next activity. Entry point. |
| | `/gse:status` | Show sprint state, artefact inventory, health, git state |
| | `/gse:health` | Display the 8-dimension health dashboard (0-10 scale) |
| **Session** | `/gse:pause` | Auto-commit work, save session checkpoint |
| | `/gse:resume` | Reload checkpoint, verify worktrees, propose next action |
| **Onboarding** | `/gse:hug` | Establish your profile (expertise, language, goals) |
| **Learning** | `/gse:learn` | Start a learning session on any SE topic |
| **Backlog** | `/gse:backlog` | View and manage the unified work item list |
| **Discovery** | `/gse:collect` | Inventory project artefacts + scan external sources |
| | `/gse:assess` | Gap analysis: what's covered, what's missing |
| **Planning** | `/gse:plan` | Select backlog items for sprint, assign branches |
| **Engineering** | `/gse:reqs` | Define test-driven requirements with acceptance criteria |
| | `/gse:design` | Architecture decisions, component decomposition |
| | `/gse:preview` | Simulate planned artefacts before building |
| | `/gse:tests` | Test strategy, environment setup, execution, evidence |
| | `/gse:produce` | Execute production in isolated worktree |
| | `/gse:deliver` | Merge, tag release, cleanup branches |
| **Deployment** | `/gse:deploy` | Deploy to Hetzner server via Coolify (solo or training mode) |
| **Quality** | `/gse:review` | Review branch diff + devil's advocate (AI integrity) |
| | `/gse:fix` | Apply fixes from review in isolated branch |
| **Capitalization** | `/gse:compound` | Capitalize learnings across 3 axes |
| | `/gse:integrate` | Route solutions to project/methodology/learning |
| **Ad-hoc** | `/gse:task` | Execute a task outside the standard lifecycle |

## Architecture

```
gse-one/
├── src/                        # Shared source of truth
│   ├── principles/             # 16 core principles (P1-P16)
│   ├── activities/             # 23 activity definitions
│   ├── agents/                 # 11 agents (10 specialized + orchestrator)
│   └── templates/              # 29 artefact & config templates
├── plugin/                     # Single deployable directory (3 platforms)
│   ├── .claude-plugin/         # Claude Code manifest
│   ├── .cursor-plugin/         # Cursor manifest
│   ├── skills/                 # 23 skills (shared, with name: field)
│   ├── commands/               # 23 /gse-<name>.md (Cursor)
│   ├── agents/                 # 11 agents (shared)
│   ├── templates/              # 29 templates (shared)
│   ├── tools/                  # Python tools (dashboard, etc.)
│   ├── rules/                  # 1 .mdc (Cursor-only, ignored by Claude/opencode)
│   ├── hooks/                  # 2 hooks files (Claude + Cursor)
│   ├── settings.json           # Claude-only
│   └── opencode/               # opencode subtree (skills, commands, agents,
│                               #   plugins/gse-guardrails.ts, AGENTS.md, opencode.json)
├── marketplace/                # Marketplace metadata
└── gse_generate.py             # Generator: src/ → plugin/ (incl. opencode/)
```

## Core Principles (16)

| Category | Principles |
|----------|-----------|
| **Foundations** | P1 Iterative, P2 Agile, P3 Artefacts, P5 Planning, P6 Traceability |
| **Risk & Communication** | P4 Human-in-loop, P7 Risk Classification, P8 Consequence Visibility, P9 Adaptive Comm, P10 Complexity Budget, P11 Guardrails |
| **Infrastructure** | P12 Version Control, P13 Hooks, P14 Knowledge Transfer |
| **AI Integrity** | P15 Agent Fallibility, P16 Adversarial Review |

## License

Business Source License 1.1 — see [LICENSE](LICENSE) for details.
