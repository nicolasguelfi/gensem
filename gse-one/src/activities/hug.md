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

### Step 0 — Language Detection (always first, always alone)

**Condition:** No language is set in `.gse/profile.yaml` or `.gse/config.yaml`.

If a language is already configured, skip to Step 1.

1. **Detect system locale** — Read `$LANG` or `$LC_ALL` to identify the system language (e.g., `fr_FR.UTF-8` → French).
2. **Build the option list** — Start with the detected locale language (marked "Recommended"), then add the standard list: English, Français, Español, Deutsch. **Deduplicate:** if the detected locale matches one of the four, move it to first position instead of duplicating.
3. **Ask in all listed languages** — The question itself is displayed in each language so the user can understand it regardless of their language:

   Example (interactive — detected locale = Japanese):
   ```
   AskUserQuestion([
     { question: "Which language would you like me to use? / どの言語を使いますか？ / Quelle langue souhaitez-vous ? / ¿Qué idioma prefiere? / Welche Sprache bevorzugen Sie?",
       header: "Language",
       multiSelect: false,
       options: [
         { label: "日本語 (Recommended)", description: "Detected from your system / システムから検出" },
         { label: "English", description: "English" },
         { label: "Français", description: "French" },
         { label: "Español", description: "Spanish" }
       ] }
   ])
   // "Other" is automatically available — user can type Deutsch, 中文, हिन्दी, etc.
   ```

   Example (text fallback — detected locale = French):
   ```
   🌍 Which language would you like me to use?
      Quelle langue souhaitez-vous utiliser ?
      ¿Qué idioma desea utilizar?
      Welche Sprache möchten Sie verwenden?

   1. Français (Recommended — detected from your system)
   2. English
   3. Español
   4. Deutsch
   5. Other — type your language
   ```

4. **Set artifact language** — After the user chooses the chat language, set `language.artifacts` to `en` (industry default). Inform the user: "I'll chat in [chosen language]. Files I produce (code, docs) will be in English by default — you can change this anytime." This covers the `artifacts` and `overrides` sub-fields of dimension #4, which are NOT re-asked during Step 2.
5. **Switch immediately** — From this point on, ALL communication is in the chosen language.

### Step 1 — Smart Inference

Before asking any questions, infer as much as possible from available signals:

| Dimension | Inference Source |
|-----------|-----------------|
| Project domain | Package manifest, README, directory structure |
| IT expertise | Vocabulary complexity in user messages (e.g., "deploy" vs "put online") |
| Team context | Git log — number of contributors, commit patterns |
| Scientific expertise | Presence of academic references, LaTeX files, data science libraries |

Report inferences (in the user's chosen language): "Based on what I can see, I'll assume: [inferred values]. I'll only ask about what I can't determine."

### Step 2 — Interview (Only Unresolved Dimensions)

The 13 HUG dimensions are:

| # | Dimension | Scale / Values | Purpose |
|---|-----------|---------------|---------|
| 1 | **IT expertise** | beginner / intermediate / advanced / expert | Calibrate technical depth of explanations |
| 2 | **Scientific expertise** | none / familiar / practitioner / researcher | Adjust formality and rigor expectations |
| 3 | **Abstraction capability** | concrete-first / balanced / abstract-first | Choose explanation style (examples vs theory) |
| 4 | **Language** | `chat`: ISO 639-1, `artifacts`: ISO 639-1, `overrides`: per-type | Set chat language, artifact language, and per-type overrides. Default: chat=detected, artifacts=en. Tell the user: "I'll communicate in [chat language]. Files will be produced in [artifacts language] by default. You can change this at any time, globally or per document." |
| 5 | **Preferred verbosity** | terse / normal / detailed | Control output length and ceremony level |
| 6 | **Domain background** | free text | Tailor domain-specific vocabulary and examples |
| 7 | **Decision involvement** | autonomous / collaborative / supervised | Control Gate frequency and agent autonomy |
| 8 | **Project domain** | web / api / cli / data / mobile / embedded / library / scientific / other | Calibrate default tech stack and test pyramid |
| 9 | **Team context** | solo / pair / small-team / large-team | Adjust collaboration ceremonies |
| 10 | **Learning goals** | list of short goal strings (optional) | Activate proactive LEARN at relevant moments |
| 11 | **Contextual tips** | on / off | Enable/disable inline micro-explanations |
| 12 | **Emoji** | on / off | Enable/disable emoji in chat output (default: on) |
| 13 | **User name** | free text (optional) | Display name in dashboard and artefacts. For beginners: "What name should I use for you in the project? (You can skip this.)" Store in `profile.yaml` under `user.name`. If skipped, defaults to git user name or "Unknown". |

#### Question cadence (adaptive)

The number of questions asked at once is proportional to the user's IT expertise. The **first question after Step 0** is ALWAYS the IT expertise level (asked alone) — it determines the cadence for all remaining questions.

| IT Expertise | Cadence | Rationale |
|---|---|---|
| **Beginner** | **1 question at a time** — wait for response before asking the next | Avoid cognitive overload; let the user absorb each concept |
| **Intermediate** | **2-3 questions grouped** by related theme | Comfortable enough to handle a small batch |
| **Advanced / Expert** | **All remaining questions in one block** | Efficient; no hand-holding needed |

**Interview sequence:**
1. **IT expertise** (always alone, always first after Step 0) — this is the cadence key
2. **Remaining dimensions** — asked at the cadence determined by Step 2.1

**Interactive mode (preferred):** When the environment provides an interactive question tool (e.g., `AskUserQuestion` in Claude Code, clarifying questions in Cursor), use it to present profile questions as clickable choices instead of numbered text lists. Use `multiSelect: true` for dimensions where multiple values apply. Map "Discuss" to the automatic "Other" escape hatch. When interactive tools are unavailable or dimensions require free text (e.g., learning goals, domain background), fall back to conversational text.

Example — beginner flow (1 question at a time):
```
[Step 0] → Language selected: Français
[Step 1] → Inferences reported in French
[Step 2.1] → "Comment décririez-vous votre expérience avec les outils informatiques ?"
             → Réponse : débutant → cadence = 1 par 1
[Step 2.2] → "Préférez-vous des réponses courtes ou des explications détaillées ?"
             → Réponse
[Step 2.3] → "Souhaitez-vous que je prenne les décisions seul, ou que je vous consulte ?"
             → Réponse
[Step 2.4] → ... (1 question à la fois jusqu'à complétion)
```

Example — expert flow (all at once):
```
[Step 0] → Skipped (language detected from first message)
[Step 1] → Inferences: IT=expert (from vocabulary), domain=api, team=solo
[Step 2]  → All remaining questions in one block:
            AskUserQuestion([
              { question: "Verbosity?", ... },
              { question: "Decision involvement?", ... },
              { question: "Learning goals?", ... }
            ])
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

Verify the project environment is ready. **This step is blocking** — do NOT mention `/gse:go` or any next steps until git initialization is fully resolved (accepted or declined).

1. **Git repo check** — If no `.git/` directory exists:
   - **For beginner users (per P9 — Adaptive Communication):** Explain what git is before asking, and warn about the system dialog that will appear:
     ```
     Agent: Before we continue, I need to set up version control for your project.
     
     Version control (git) is like an "infinite undo" — it keeps a complete 
     history of every change you make, so you can always go back to a previous 
     version if something goes wrong.
     
     If you agree, I'll initialize it now. A confirmation dialog will appear 
     in the editor — click "Run" to confirm (or "Skip" to cancel).
     
     Should I set it up?
     ```
   - **For intermediate/advanced users:** Ask concisely: "No git repo detected here. Should I run `git init`?"
   - **Wait for response** — Do NOT proceed or mention next steps until the user responds.
   - If yes: run `git init`, create initial `.gitignore`, **apply the Git Identity Verification preflight** (see below), then create a **foundational commit** on `main`:
     ```bash
     git init
     # create .gitignore with project-appropriate entries
     # [Git Identity Verification preflight — see below]
     git add .gitignore
     git commit -m "chore: initialize repository"
     ```
     This foundational commit is **mandatory** — without it, `main` is not a valid branch reference and all subsequent branching operations (P12) will fail. If a system permission dialog appears, the user has already been told what to do.

     **Git Identity Verification preflight (Hard guardrail, spec P12.6):** Before running `git commit`, verify that a git identity is configured.
     1. **Check git installation** — Run `git --version`. If exit code is non-zero (git not installed), abort with: *"git is not installed on this system. GSE-One requires git — please install it first."* No Gate is shown.
     2. **Query identity at both scopes:**
        - `git config --global user.name` and `git config --global user.email`
        - `git config --local user.name` and `git config --local user.email`
     3. **If both name AND email are set at either scope (global OR local)** → identity is OK, proceed to the commit.
     4. **If any value is missing** → present the **Git Identity Gate**:

        > **Question:** I need a git identity to save commits — none is set on this machine, globally or for this project. How should I proceed?
        >
        > **Options:**
        > 1. **Set global identity** (recommended) — I'll configure git with your name and email, so all your projects on this machine can commit. I'll ask for your name and email.
        > 2. **Set local identity (this project only)** — I'll configure git for this project only. Your global setup is unchanged. I'll ask for your name and email.
        > 3. **Quick placeholder (local, for a quick test)** — I'll set `GSE User` / `user@local` for this project only. Good for throwaway experiments; change later with options 1 or 2.
        > 4. **I'll set it myself** — Here are the commands to run in your terminal:
        >    ```
        >    git config --global user.name "Your Name"
        >    git config --global user.email "you@example.com"
        >    ```
        >    Let me know when you're done — I'll re-check and continue.
        > 5. **Discuss** — Explain the scope difference and security considerations.

        **Beginner translations** (per P9 Adaptive Communication): option 1 → "set up your signature for all your projects"; option 2 → "just for this folder"; option 3 → "a disposable signature for this quick test"; option 4 → "I'll give you two commands to type yourself".

     5. **On option 1 or 2:** ask for the user's name, then ask for the email (one at a time for beginners, grouped for intermediate/expert). **Validate the email** (must contain exactly one `@` with a non-empty local part and a dotted domain with non-empty labels on both sides of the dot — e.g. `you@example.com`). On invalid email, re-prompt: *"That doesn't look like a valid email address. Could you enter it again? (e.g., you@example.com)"*. Once valid, run:
        - Option 1: `git config --global user.name "<name>"` and `git config --global user.email "<email>"`
        - Option 2: `git config --local user.name "<name>"` and `git config --local user.email "<email>"`
        Re-verify identity, then proceed to the commit.
     6. **On option 3:** run `git config --local user.name "GSE User"` and `git config --local user.email "user@local"`. Immediately print a single reminder: *"Placeholder identity set locally for this project. If you plan to share this repo or push to a remote, replace it via `/gse:hug --update` or directly with `git config --global user.name` / `user.email`."* Do not repeat the reminder on subsequent activities. Proceed to the commit.
     7. **On option 4:** print the two `git config --global ...` commands as a copy-paste block, wait for user confirmation ("done" / "ok" / "c'est fait"), then re-run the identity detection. If still missing, re-present the Gate (options 1-5).
     8. **On option 5:** explain (scope difference between global/local, visibility of commits on pushed branches, throwaway nature of option 3), then re-present options 1-4.
   - If no: acknowledge and continue without git. Note that some GSE features (branching, version control guardrails) will be unavailable.
2. **Create `.gse/` directory** — If it does not exist:
   - Create `.gse/` with subdirectories: `profiles/`, `checkpoints/`
   - Copy `config.yaml` from the template (`$(cat ~/.gse-one)/templates/config.yaml`) with default values. Leave `lifecycle.mode` empty — `/gse:go` will fill it after Complexity Assessment (spec §14.3 — Orchestrator Decision Logic, Step 6 — Complexity Assessment).
   - Add to `.gitignore`: entries for `.gse/local/` (machine-specific state)
3. **Save profile** — Write the completed profile to `.gse/profile.yaml` (or `.gse/profiles/{username}.yaml` in team mode)

### Step 4.5 — Update Mode (`--update`)

When called with `--update`, the profile already exists. Only re-ask dimensions the user wants to change:

1. **Load current profile** — Read `.gse/profile.yaml` and display current values as a summary.
2. **Ask what to change** — Present all dimensions with their current values. The user selects which ones to modify.
3. **Re-interview selected dimensions** — Run Step 2 interview only for the selected dimensions.
4. **Detect behavioral impact** — Compare old and new values. If any of the following dimensions changed, notify the user of the consequences:

   | Changed dimension | Impact | Notification |
   |---|---|---|
   | `it_expertise` | Vocabulary, question cadence, artefact approval, knowledge transfer | "I'll adjust how I explain things and how many questions I ask at once." |
   | `language.chat` | All chat output language | "From now on, I'll communicate in [new language]." |
   | `decision_involvement` | Gate frequency, supervised mode override | "I'll [ask more / ask less] before making technical choices." |
   | `preferred_verbosity` | Output length and detail level | "I'll make my responses [shorter / more detailed]." |
   | `contextual_tips` | Inline micro-explanations | "I'll [start / stop] adding learning tips during activities." |

5. **Save and apply immediately** — Update `profile.yaml` with the new values and set `updated` timestamp. The changes take effect on the very next skill invocation — no restart needed.

### Step 5 — Profile Persistence

Save the profile as YAML:

```yaml
# .gse/profile.yaml
version: 1
created: 2026-01-15
updated: 2026-01-15
user:
  name: "Nicolas"
  git_email: "nicolas@example.com"
dimensions:
  it_expertise: advanced
  scientific_expertise: practitioner
  abstraction_capability: balanced
  language:
    chat: fr
    artifacts: en
    overrides: {}
  preferred_verbosity: normal
  domain_background: "Software engineering, AI-assisted development"
  decision_involvement: collaborative
  project_domain: api
  team_context: solo
  learning_goals:
    - "Rust async patterns"
    - "property-based testing"
  contextual_tips: true
  emoji: true
inferred:
  it_expertise: true
  project_domain: true
  team_context: true
  language.chat: true
```

### Step 5.5 — Dashboard Initialization

After `.gse/` is created and profile saved:

1. **Validate tool access** — Run: `cat ~/.gse-one` to verify the plugin registry exists. If the file is missing, warn the user: "GSE-One registry not found. Run `python3 install.py` again to fix."
2. **Generate the first dashboard** — Run: `python3 "$(cat ~/.gse-one)/tools/dashboard.py"`
3. **Verify** — Check that `docs/dashboard.html` was created and is not empty.
4. Inform the user:
   - **For beginner users:** "J'ai créé un tableau de bord pour suivre l'avancement de ton projet. Tu peux l'ouvrir dans ton navigateur à tout moment : `docs/dashboard.html`. Il se met à jour à chaque étape."
   - **For intermediate/advanced users:** "Dashboard generated at `docs/dashboard.html`. Regenerated after each activity. Run `python3 \"$(cat ~/.gse-one)/tools/dashboard.py\" --watch` for live updates."

### Step 6 — Transition

**Only after Steps 4-5.5 are fully completed** (git initialization resolved, profile saved, dashboard created):
- If project has no `.gse/config.yaml`: propose `/gse:go` to start project setup.
  - **For beginner users:** Explain what `/gse:go` does before suggesting it: "Now that your profile is saved, the next step is to set up your project. Type `/gse:go` — it will help you define what you want to build and create a first work plan."
  - **For intermediate/advanced users:** "Profile saved. Run `/gse:go` to set up project state (config.yaml, first sprint)."
- If project already configured: confirm profile saved and return to previous activity
