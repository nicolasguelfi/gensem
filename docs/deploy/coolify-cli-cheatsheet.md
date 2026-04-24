# Coolify CLI Cheatsheet — via `curl` + `jq`

**Audience:** GSE-One trainers and learners who need to inspect or manipulate Coolify state from the command line without clicking through the UI.

**Why `curl` + `jq` and not a dedicated CLI?** Coolify does not ship an official CLI tool. Its REST API at `$COOLIFY_URL/api/v1/*` is the canonical programmatic surface. `curl` + `jq` covers 100% of common ops, adds zero dependency, and shows the reader the exact HTTP request being made (transparent, auditable).

**Hetzner side.** For Hetzner-level operations (servers, firewalls, SSH keys), use the official `hcloud` CLI — GSE-One already uses it in Phase 2 of `/gse:deploy`. This cheatsheet covers only the Coolify side.

---

## Prerequisites

All recipes below assume the following env vars are set. They are written into `.env` by `/gse:deploy` Phase 1 and Phase 4:

- `COOLIFY_URL` — the Coolify dashboard URL (e.g., `https://coolify.example.org`).
- `COOLIFY_API_TOKEN` — a Coolify API token with Read+Write+Deploy scopes.

Load them into your shell session:

```bash
set -a && source .env && set +a
```

(`set -a` + `source` + `set +a` is a portable pattern that exports all variables defined by the `.env` file into the current shell. Works in bash, zsh, Git Bash on Windows.)

`jq` is optional but highly recommended for JSON parsing. macOS: `brew install jq`. Debian/Ubuntu: `apt install jq`. Windows: `winget install jqlang.jq` or use Git Bash with recent jq bundled.

---

## Recipe 1 — List all projects

```bash
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/projects" \
  | jq '.[] | {uuid, name, description, created_at}'
```

Returns one JSON block per project with its UUID, name, description, and creation timestamp. Scan the list for duplicates (same `name`), orphans (empty projects after failed deploys), or outdated naming.

---

## Recipe 2 — List all applications (across all projects)

```bash
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/applications" \
  | jq '.[] | {uuid, name, status, fqdn, git_repository, git_branch}'
```

Shows every deployed app with its Coolify UUID, current status (`running`, `exited`, `degraded`, etc.), the public FQDN, and the Git source.

---

## Recipe 3 — Find duplicate projects by name

Duplicates are a common artefact of concurrent `deploy-app` invocations (see `src/activities/deploy.md` Phase 6 Step 4 concurrency note). To detect them:

```bash
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/projects" \
  | jq 'group_by(.name) | map(select(length > 1)) | .[][] | {uuid, name, created_at}'
```

Returns entries **only** for names that appear 2+ times. Empty output → no duplicates.

For a specific name (e.g., `gse-learner-03`):

```bash
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/projects" \
  | jq '.[] | select(.name == "gse-learner-03") | {uuid, name, created_at}'
```

---

## Recipe 4 — Delete a project by UUID

```bash
curl -s -X DELETE -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/projects/<PROJECT-UUID>"
```

No output body on success. Coolify refuses to delete a project that still contains applications — delete its applications first (Recipe 5) or rely on Coolify's cascade behaviour if enabled.

**Safety pattern for cleaning up empty duplicate projects:** always `jq`-filter on `.created_at` to keep the oldest and delete only the newer duplicate(s). The oldest is more likely to be the one the tool first registered in its state file.

---

## Recipe 5 — Delete an application by UUID

```bash
curl -s -X DELETE -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/applications/<APP-UUID>"
```

Prefer Recipe 2 first to get the UUID, then delete. Useful to clean up a failed deploy without nuking the whole project.

---

## Recipe 6 — Force a rebuild/redeploy of an existing application

```bash
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/deploy?uuid=<APP-UUID>&force=true"
```

This is the canonical redeploy path used internally by `deploy.py` (see `deploy-operator.md` anti-pattern on `/restart`). It rebuilds the image (bypassing Docker cache if the `Dockerfile` uses `ARG SOURCE_COMMIT`) and redeploys. Returns a JSON with a `deployment_uuid` you can tail for logs.

---

## Recipe 7 — Inspect server info

```bash
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/servers" \
  | jq '.[] | {uuid, name, ip, status}'
```

Shows all servers registered in Coolify. For a single-server GSE-One setup, you'll see one entry — typically `localhost` if Coolify is self-managing the host it runs on.

---

## Recipe 8 — Get app status + health (JSON)

```bash
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/applications/<APP-UUID>" \
  | jq '{name, status, fqdn, git_branch, build_pack, last_online_at}'
```

Use this when the `/gse:deploy --status` output is stale or you want the ground-truth Coolify view.

---

## Pattern — Cleanup empty duplicate projects (full recipe)

Combining Recipes 3 + 4, here is a copy-paste cleanup for the specific case encountered in training when a learner ran parallel `deploy-app` calls:

```bash
# 1. Identify duplicates for a specific project name
NAME="gse-learner-03"

curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/projects" \
  | jq --arg n "$NAME" '.[] | select(.name == $n) | .uuid' -r

# 2. Copy the UUIDs from the output and delete them one by one
curl -s -X DELETE -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/projects/<UUID-1>"

curl -s -X DELETE -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/projects/<UUID-2>"

# 3. Verify the list is now clean
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "$COOLIFY_URL/api/v1/projects" \
  | jq --arg n "$NAME" '.[] | select(.name == $n)'
# empty output → clean
```

**Do not script the DELETE in a pipeline** (e.g., `jq '...' | xargs curl ...`). Coolify rate-limits and a batch DELETE that fires all UUIDs at once has caused intermittent 500s in practice. Delete one at a time, verify each 200 OK.

---

## When to graduate to a proper `coolify-*` subcommand in `deploy.py`

If the same curl pattern is used ≥3 times across different incidents (cleanup, force-redeploy, app-status-dump), that's the signal to promote it into a first-class `deploy.py coolify-<verb>` subcommand in `gse-one/plugin/tools/deploy.py`. Until then, this cheatsheet is the authoritative documentation.

Ideas for future subcommands (tracked, not yet implemented):

- `deploy.py coolify-list-projects` / `coolify-list-apps`
- `deploy.py coolify-dedup --name <project-name>` (with `--dry-run` and interactive confirmation)
- `deploy.py coolify-force-deploy <app-name>`
- `deploy.py coolify-clean-empty-projects` (removes all projects with zero applications, respects `--dry-run`)

Contributors welcome — see `gensem/CLAUDE.md` for the build pipeline rules.
