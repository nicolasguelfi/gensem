---
description: "Route capitalized solutions to their targets. Triggered by /gse:integrate after compound."
---

# GSE-One Integrate — Integration

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Route all capitalized solutions from the latest compound |
| `--axis project`   | Integrate project solutions only (Axe 1) |
| `--axis methodology` | Integrate methodology solutions only (Axe 2) |
| `--axis competencies` | Integrate competency solutions only (Axe 3) |
| `--dry-run`        | Show integration plan without executing |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint and lifecycle state
2. `.gse/config.yaml` — project configuration
3. `.gse/profile.yaml` — user profile, competency map
4. `docs/sprints/sprint-{NN}/compound.md` — capitalization output (source of solutions)
5. `gse-one/plugin.json` — repository URL for methodology issues (Axe 2)

## Workflow

### Step 1 — Axe 1: Project Integration

Route project-level learnings into operational configuration:

1. **Patterns** — If patterns were identified, consider:
   - Adding them as coding conventions in project config (`.gse/config.yaml` or project linter rules)
   - Creating template snippets in project templates
   - Updating project documentation

2. **Lessons learned** — If prevention strategies were defined:
   - Add as review checklist items in `.gse/config.yaml` under `review.custom_checks`
   - Update `.gse/config.yaml` constraints or guardrails

3. **Technical debt** — If debt items were flagged:
   - Create backlog entries in `.gse/backlog.yaml` (pool, not assigned to a sprint)
   - Set appropriate priority based on impact assessment

4. Report changes made to project configuration files.

### Step 2 — Axe 2: Methodology Integration

Route methodology feedback to the GSE-One repository:

1. Read methodology proposals from `compound.md`
2. For each proposal, present to user (Gate):
   - Title: "{proposal title}"
   - Description: "{what was observed and what should change}"
   - Label: `enhancement` or `bug` (depending on nature)
   - "Shall I create this issue on the GSE-One repository?"

3. If user accepts:
   ```
   gh issue create \
     --repo {repository_from_plugin.json} \
     --title "{proposal title}" \
     --body "{detailed description with sprint context}" \
     --label "enhancement"
   ```

4. Record created issue URLs in `docs/sprints/sprint-{NN}/compound.md` under a "Submitted Issues" section.

5. If user declines a proposal:
   - Record as "Deferred" in `compound.md`
   - Do not re-propose unless observed again in a future sprint

### Step 3 — Axe 3: Competency Integration

Route competency learnings into persistent storage:

1. **Learning notes** — Write or append to `docs/learning/` directory:
   - One file per topic area (e.g., `docs/learning/python-patterns.md`, `docs/learning/testing-strategies.md`)
   - Each note includes: date, sprint context, concept, practical example

2. **Competency map** — Update `profile.yaml` competency section:
   - Adjust skill levels based on sprint evidence
   - Add new skills discovered during the sprint
   - Update `last_practiced` timestamps

3. **Learning suggestions** — If proactive LEARN proposals were generated in compound:
   - Persist accepted proposals as learning goals in `profile.yaml`
   - Declined proposals are not persisted

### Step 4 — Finalize

1. Update `status.yaml`:
   - `last_activity: integrate`
   - `last_activity_timestamp: {now}`
2. Report integration summary:
   - Project config changes: {count}
   - Issues created: {count} (with URLs)
   - Learning notes updated: {count}
   - Competency map changes: {count}
3. Sprint cycle is now complete. Propose:
   - Start next sprint: `/gse:go` (will detect and propose LC01 for sprint S{NN+1})
   - Or pause: `/gse:pause` to save state and resume later
