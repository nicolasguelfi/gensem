---
description: "Establish or update user profile. Triggered when user context is unknown or /gse:hug is called."
---

# GSE-One HUG — User Profile

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Start or resume the user profile interview |
| `--update`         | Update an existing profile (re-ask only changed dimensions) |
| `--show`           | Display the current profile without modification |
| `--team`           | Enable team mode (per-user profiles) |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/profile.yaml` — existing profile (if any)
2. `.gse/config.yaml` — project configuration (if any)
3. `pyproject.toml` / `package.json` / `Cargo.toml` — project manifest for domain inference
4. Git log — for team context inference

## Workflow

### Step 1 — Smart Inference

Before asking any questions, infer as much as possible from available signals:

| Dimension | Inference Source |
|-----------|-----------------|
| Chat language | Language of the user's first message |
| Project domain | Package manifest, README, directory structure |
| IT expertise | Vocabulary complexity in user messages (e.g., "deploy" vs "put online") |
| Team context | Git log — number of contributors, commit patterns |
| Scientific expertise | Presence of academic references, LaTeX files, data science libraries |

Report inferences: "Based on what I can see, I'll assume: [inferred values]. I'll only ask about what I can't determine."

### Step 2 — Interview (Only Unresolved Dimensions)

The 11 HUG dimensions are:

| # | Dimension | Scale / Values | Purpose |
|---|-----------|---------------|---------|
| 1 | **IT expertise** | beginner / intermediate / advanced / expert | Calibrate technical depth of explanations |
| 2 | **Scientific expertise** | none / familiar / practitioner / researcher | Adjust formality and rigor expectations |
| 3 | **Abstraction capability** | concrete-first / balanced / abstract-first | Choose explanation style (examples vs theory) |
| 4 | **Language** | `chat`: ISO 639-1, `artifacts`: ISO 639-1, `overrides`: per-type | Set chat language, artifact language, and per-type overrides. Default: chat=detected, artifacts=en. Tell the user: "I'll communicate in [chat language]. Files will be produced in [artifacts language] by default. You can change this at any time, globally or per document." |
| 5 | **Preferred verbosity** | terse / normal / detailed | Control output length and ceremony level |
| 6 | **Domain background** | free text | Tailor domain-specific vocabulary and examples |
| 7 | **Decision involvement** | autonomous / collaborative / supervised | Control Gate frequency and agent autonomy |
| 8 | **Project domain** | web / api / cli / data / mobile / embedded / other | Calibrate default tech stack and test pyramid |
| 9 | **Team context** | solo / pair / small-team / large-team | Adjust collaboration ceremonies |
| 10 | **Learning goals** | free text (optional) | Activate proactive LEARN at relevant moments |
| 11 | **Contextual tips** | on / off | Enable/disable inline micro-explanations |
| 12 | **Emoji** | on / off | Enable/disable emoji in chat output (default: on) |

For dimensions that could not be inferred, ask questions in natural conversation style. Group related questions to minimize back-and-forth. Typically 4-5 questions suffice.

Example interview flow:
```
Agent: I see this is a Python web project (FastAPI) with a single contributor.
I'll assume: IT expertise = advanced, project domain = api, team context = solo.

A few quick questions to complete your profile:
1. What language do you prefer me to use? (I noticed you wrote in French)
2. Do you prefer short, focused answers or detailed explanations?
3. Should I make decisions autonomously, or check with you at each step?
4. Any specific topics you'd like to learn along the way?
```

### Step 3 — Team Mode

When `--team` is specified or multiple git contributors are detected:

1. **Detect git user** — Read `git config user.name` and `git config user.email`
2. **Check profiles directory** — Look for `.gse/profiles/{username}.yaml`
3. **Load or create** — If profile exists, load it. If not, run the interview for this user.
4. **Link** — Copy the active user's profile to `.gse/profile.yaml` (or create a symlink on systems that support it)
5. **Switch** — When git user changes between sessions, auto-switch the active profile by updating `.gse/profile.yaml`

Profile file structure:
```
.gse/
├── profile.yaml          # active profile (copy of profiles/nicolas.yaml)
└── profiles/
    ├── nicolas.yaml
    └── alex.yaml
```

### Step 4 — Git Initialization

Verify the project environment is ready:

1. **Git repo check** — If no `.git/` directory exists:
   - Ask: "This directory is not a git repository. Should I initialize one?"
   - If yes: run `git init`, create initial `.gitignore`
2. **Create `.gse/` directory** — If it does not exist:
   - Create `.gse/` with subdirectories: `profiles/`
   - Add to `.gitignore`: entries for `.gse/local/` (machine-specific state)
3. **Save profile** — Write the completed profile to `.gse/profile.yaml` (or `.gse/profiles/{username}.yaml` in team mode)

### Step 5 — Profile Persistence

Save the profile as YAML:

```yaml
# .gse/profile.yaml
version: 1
user:
  name: "Nicolas"
  git_email: "nicolas@example.com"
dimensions:
  it_expertise: advanced
  scientific_expertise: practitioner
  abstraction_capability: balanced
  mother_tongue: fr
  preferred_verbosity: normal
  domain_background: "Software engineering, AI-assisted development"
  decision_involvement: collaborative
  project_domain: api
  team_context: solo
  learning_goals: "Rust async patterns, property-based testing"
  contextual_tips: on
inferred:
  it_expertise: true
  project_domain: true
  team_context: true
  mother_tongue: true
created: 2026-01-15
updated: 2026-01-15
```

### Step 6 — Transition

After profile creation:
- If project has no `.gse/config.yaml`: propose `/gse:go` to start project setup
- If project already configured: confirm profile saved and return to previous activity
