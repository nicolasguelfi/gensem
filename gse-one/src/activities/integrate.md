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
5. Upstream repository URL for methodology issues (Axe 2). **Resolution order:** (1) `config.yaml → github.upstream_repo` if set (user override — private forks, corporate trackers), (2) plugin manifest (`plugin.json → repository` on Claude/Cursor; `opencode.json → gse.repository` on opencode), (3) skip Axe 2 with an Inform note.

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

Route methodology feedback to the GSE-One repository. This step consumes the ticket draft prepared by `/gse:compound` Axe 2.

1. **Read the draft** — look for `.gse/compound-tickets-draft.yaml` prepared by the most recent `/gse:compound` Axe 2 run. Each entry was already validated by the user during COMPOUND's per-ticket Gate (approve / edit / skip) with quality filters applied (concrete, theme-grouped, deduplicated, capped).
   - **If the file is absent** (user chose option 1 "local export only" in COMPOUND, or COMPOUND was skipped): skip this step with an Inform note: *"No GitHub ticket proposals to process — Axe 2 handoff file absent."*
   - **If the file is present**: proceed.

2. **Final confirmation Gate (public submission — privacy acknowledgment).** List the approved tickets one last time (title + label + one-line body preview) and state explicitly that submission will create **public issues** on the resolved repository. Ask: *"Submit {N} methodology issues to the upstream repository ({repo_url})? Note: issues are public and visible to anyone with access to the repo."*
   - Options: *Submit all* / *Review individually again* / *Cancel* / *Discuss*.

3. **On submission**, for each approved ticket (using the repository resolved per Prerequisite 5):
   ```
   gh issue create \
     --repo {resolved_upstream_repo} \
     --title "{title}" \
     --body "{body}" \
     --label "{label}"
   ```
   Capture the returned issue URL.

4. **Record created issue URLs** in `docs/sprints/sprint-{NN}/compound.md` under a "Submitted Issues" section. Cross-link: each source observation in the sprint artefacts gets a pointer to the created issue URL for bidirectional traceability.

5. **Clean up** — after successful submission, delete `.gse/compound-tickets-draft.yaml` (the handoff is consumed). If submission partially failed (e.g., rate limit), keep the draft with remaining entries for a retry.

6. **Skipped / cancelled proposals** — not re-proposed unless the same theme is observed again in a future sprint. Recorded in `compound.md` as "Deferred" with the source observation references.

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
