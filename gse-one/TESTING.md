# GSE-One Testing

Two levels of validation:

1. **Automated unit tests** — fast, deterministic, runnable locally
2. **Manual E2E checklist** — requires live Hetzner + Coolify infrastructure

Rationale: the Python tools (`plugin/tools/deploy.py` + `coolify_client.py`) have a
deterministic core (state, sanitization, detection, preflight, env parsing) that can
be unit-tested without infrastructure, and an infrastructure-dependent surface
(Coolify API, SSH, hcloud, DNS, Let's Encrypt) that can only be validated end-to-end.

Known coverage gap (tracked): 8 deploy.py public functions are infrastructure-bound
(`detect_situation`, `wait_dns`, `poll_health`, `deploy_app`, `app_status`, `destroy`,
`training_init`, `training_reap`) and currently covered only by the manual E2E
checklist below — the audit engine's `test_coverage` check reports them. Mocked unit
tests are a welcome future contribution.

---

## Unit tests

Located in `gse-one/tests/` — five files:

- `test_deploy.py` — deploy tool deterministic core (detailed below)
- `test_audit.py` — audit engine regression guards (false-positive classes, catalog chain, checkpoint round-trip coherence)
- `test_hooks.py` — generated guardrail hooks executed against synthetic stdin JSON
- `test_counters.py` — P15/P16 integrity-counter helper (whitelist, comment-preserving writes, health backstop)
- `test_checkpoint` coverage note: checkpoint schema coherence is enforced through the audit engine (`audit.py` templates category) per CLAUDE.md Meta-3 — no dedicated test file.

`test_deploy.py` covers:

- `sanitize_component()` — 9 edge cases (empty, special chars, hyphen collapse, trim, truncate)
- `build_subdomain()` — solo mode, training mode, sanitization, FQDN construction
- `_detect_type()` — 5 types with various file signals
- `preflight()` — rollup logic (errors/warnings/ok), Streamlit config detection
- `parse_env()` / `set_env()` / `delete_env()` — comment preservation, round-trip
- `load_state()` / `save_state()` / `_empty_state()` — JSON round-trip, schema shape
- `_cost_hint()` — lookup table with case-insensitivity

**Dependencies:** Python 3.9+ standard library only (`unittest`, no pytest).

### Run directly

```bash
cd gse-one
python3 -m unittest discover tests -v
```

### Run via the generator

```bash
cd gse-one
python3 gse_generate.py --verify
```

`--verify` runs the plugin regeneration checks first (frontmatter, parity, file
counts), then executes unit tests. Any failing test fails the whole verify.

### Add a test when contributing

1. Open `gse-one/tests/test_deploy.py`
2. Either add a `test_*` method to an existing `TestClassName` class, or add a
   new `class FeatureTests(unittest.TestCase):` at the end
3. Use `tempfile.mkdtemp()` + `shutil.rmtree` (via `addCleanup`) for isolation
4. Run locally; all tests must pass
5. Include the test in your PR

---

## Manual E2E checklist

Run this checklist when modifying: `destroy`, `deploy_app`, `training_init`,
`training_reap`, any SSH/hcloud/Coolify flow, or registrar instructions.

### Prerequisites

- A Hetzner API token (disposable project recommended — a dedicated test project
  is safer than your production project)
- A domain or subdomain you control (cheap `.org` / `.app` / `.dev` works)
- ~1 hour for a full solo flow, ~2 hours to validate solo + training

### Solo mode — full flow (Phases 1–6)

- [ ] `/gse:deploy` from an empty Streamlit project → walks through Phase 1
      (hcloud install, token paste, domain)
- [ ] Phase 2: server created (`cax21`, `fsn1`), firewall applied, SSH works as
      `root`
- [ ] Phase 3: `deploy` user created, SSH hardened (root disabled), UFW active,
      `ufw-docker` installed, fail2ban running, unattended-upgrades set
- [ ] Phase 4: Coolify installed, admin account created, API token obtained
      (pasted back in chat), containers `coolify`, `coolify-proxy`, `coolify-db`
      running
- [ ] Phase 5: DNS records configured (verify for at least one registrar),
      `wait-dns` resolves, SSL active on `coolify.<domain>`, port 8000 closed.
      Decline Cloudflare CDN proposal.
- [ ] Phase 6: preflight passes (or warnings accepted), Dockerfile generated
      (`Dockerfile.streamlit` for Streamlit), Coolify project `gse` created,
      environment `production` created, application created, deploy triggered,
      URL responds 200 with Streamlit content
- [ ] `/gse:deploy --status` lists the app as healthy
- [ ] `/gse:deploy --redeploy` triggers a rebuild, URL still works, `app_uuid`
      unchanged in state
- [ ] `/gse:deploy --destroy --dry-run` shows impact (apps, projects, server,
      firewall, cost savings) without touching anything
- [ ] `/gse:deploy --destroy` with Gate 1 + Gate 2 retype → everything deleted,
      state cleared, server gone from Hetzner console, `.env` cleaned up

### Solo mode — partial skip (existing infra)

- [ ] With only `SERVER_IP` + `SSH_USER` pre-set in `.env`: skill skips to
      Phase 3 or 4 depending on `phases_completed`
- [ ] With `COOLIFY_URL` + `COOLIFY_API_TOKEN` + `DEPLOY_DOMAIN` pre-set:
      skill skips directly to Phase 6 (app-only mode)

### Training mode — instructor + 2 learners

**Instructor:**

- [ ] Full solo flow completed (Phases 1–5 once on a shared server)
- [ ] `/gse:deploy --training-init` → `.env.training` generated. Inspect the
      file: contains `COOLIFY_URL`, `COOLIFY_API_TOKEN`, `DEPLOY_DOMAIN`, and
      `DEPLOY_USER=learnerXX` placeholder. Does **NOT** contain
      `HETZNER_API_TOKEN`, `SERVER_IP`, SSH keys. Security warning in header.

**Learner Alice:**

- [ ] Copies `.env.training` to `.env` in a new Streamlit project
- [ ] Sets `DEPLOY_USER=alice`
- [ ] `/gse:deploy` → detects training mode, skips to Phase 6
- [ ] Deployed at `alice-<project>.<domain>`
- [ ] Creates a second Streamlit project, repeats → `alice-<project2>.<domain>`
- [ ] Both URLs live simultaneously

**Learner Bob (different project type):**

- [ ] Same flow but with a Node.js project → `bob-<node-project>.<domain>`
- [ ] `Dockerfile.node` generated correctly

**Instructor again:**

- [ ] `/gse:deploy --status` lists all apps across `gse-alice` and `gse-bob`
      Coolify projects
- [ ] `/gse:deploy --training-reap --user alice --dry-run` → lists `gse-alice`
      project only (not `gse-bob`, not `gse`)
- [ ] `--training-reap --user alice --confirm alice` deletes `gse-alice`
      project + all its apps, preserves `gse-bob` and `gse`
- [ ] `--training-reap --all --dry-run` → lists remaining `gse-*` (`gse-bob`)
- [ ] `--training-reap --all --confirm all` deletes `gse-bob`, **preserves
      `gse`** (solo project)

### Edge cases

- [ ] Empty project name (`/tmp/@@@`): skill aborts with clear message from
      `build_subdomain`
- [ ] FQDN > 253 chars: `build_subdomain` returns `ok: false` with error
- [ ] Coolify down during deploy: `deploy-app` returns status `error`, state
      NOT polluted with partial entry
- [ ] hcloud offline during destroy: returns `status: partial`, state
      preserved, user can retry
- [ ] DNS not propagated after 10 min: `wait-dns` returns `timeout` with hint
      to verify registrar; phase `dns` not marked complete
- [ ] Re-run `/gse:deploy` after a partial destroy: detection picks up correctly
      from `phases_completed`

---

## Recovery checklist (manual)

Session/state recovery scenarios — these exercise LLM-driven activity behavior and
file-system state, so they are manual by nature (like the E2E deploy checklist).
Run them when touching pause/resume, state schemas, or the deliver tag strategy.

### R1 — Kill mid-PRODUCE, then `/gse:go`

1. Start `/gse:produce` on a TASK in a sandbox project; kill the session (close the
   terminal) after the first file edits, before the activity closes.
2. Reopen and run `/gse:go`.
3. **Expected:** go detects the in-flight state; the scope reconciliation uses
   `status.yaml → activity_start_sha` (`git diff --name-status <sha>..HEAD`) to list
   what was already touched; `plan.yaml → workflow.pending` still contains the
   interrupted activity; no state file is corrupted.

### R2 — Corrupt `status.yaml`, then the §12.7 recovery ladder

1. In a sandbox project, truncate `.gse/status.yaml` mid-line (invalid YAML).
2. Run any activity (e.g., `/gse:status`).
3. **Expected:** the agent applies the spec §12.7 Resilience recovery ladder in
   order: (1) `git checkout -- .gse/status.yaml` if a committed version exists;
   (2) else restore the fields covered by the latest checkpoint in
   `.gse/checkpoints/`; (3) else recreate from the template and re-populate from
   session context. The error and the recovery path used are reported; a corrupt
   file is never left in place.

### R3 — Revert a delivery via backup tags

1. Complete a `/gse:deliver` in a sandbox project (this creates the backup tags,
   including the pre-main-merge class introduced in v0.63.0).
2. List tags (`git tag -l 'gse-backup/*'`), pick the pre-merge tag, and follow the
   deliver.md reversion path (`git reset --hard <tag>` on the integration branch /
   revert of the merge commit on main as documented).
3. **Expected:** the working tree returns to the pre-delivery state; `.gse/` state
   files match the reverted code state; the cleanup step (deliver Step 8 — Cleanup
   Backup Tags) only removes tags after user confirmation.

## CI (future work)

Not yet set up. Candidates:

- **GitHub Actions** triggered on PR: `python3 -m unittest discover tests`
- **Matrix:** Python 3.9, 3.10, 3.11, 3.12, 3.13
- **Platforms:** macOS, Linux (Windows WSL covers Linux)
- **Optional:** a staging Coolify instance + disposable Hetzner project for
  weekly integration tests against the manual checklist

Contributions welcome — see README → Deployment → Maintaining upstream
compatibility for the PR workflow.
