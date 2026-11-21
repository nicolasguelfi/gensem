# Instructor-path deploy rehearsal — friction treatment (v0.91.0)

Date: 2026-11-21. Source: a real instructor-path rehearsal of `/gse:deploy`
(Hetzner CAX31, Ubuntu 24.04 ARM, Coolify v4.7.6) following
`gse-one/src/activities/deploy.md` Phases 1–4 to the letter. 19 frictions
(F1–F19) were logged by the rehearsal, plus F20 added by the maintainer, and
F21–F26 found while running Phase 5 — Configure DNS and a learner-path
rehearsal (`DEPLOY_USER=rehearsal`, a public starter repository) on the same server.

Each friction was re-checked against the current sources and, where relevant,
upstream documentation (Coolify docs via Context7, the `ufw-docker` script at
its pinned commit, the Hetzner price page) before any change.

## Verdicts and resolutions

| Id | Sev | Verdict | Resolution |
|---|:-:|---|---|
| F1 | H | CONFIRMED (`ufw-docker` dies "Docker executable not found") | `ufw-docker` moved from Phase 3 to Phase 4 Step 3 — Install ufw-docker (after the Coolify installer brings Docker). Command-chain note added: a failed `&&` chain stops the phase. |
| F2 | H | CONFIRMED (ufw-docker filters the forward path) | Phase 4 Step 3 adds `ufw route allow` for container ports 80/tcp, 443/tcp, 443/udp, 8080/tcp (Coolify dashboard behind host 8000). Phase 5 Step 5 — Close temporary port 8000 also deletes the 8080 route rule. |
| F3 | H | CONFIRMED (Coolify docs: localhost server needs `PermitRootLogin prohibit-password`) | Phase 3 Step 3 — Harden SSH: global settings in `sshd_config.d/00-gse-hardening.conf` (first value wins), plus an end-of-file `Match Address <Docker networks>` → `PermitRootLogin prohibit-password`; two `sshd -T` checks. Security checklist updated. |
| F4 | H | CONFIRMED | Phase 3 Step 5 — Install fail2ban writes `jail.local` (`ignoreip` = loopback + Docker networks, `maxretry=3`, `bantime=1h`), still before Coolify. |
| F5 | M | CONFIRMED (Coolify API docs: `POST /servers/{uuid}/validate`) | New `deploy.py validate-server` + `CoolifyClient.validate_server/get_server/get_version`; new Phase 4 Step 5 — Validate the Coolify host server; container list fixed (`coolify-db`, `coolify-redis`, `coolify-proxy`). |
| F6 | M | CONFIRMED (Coolify docs: self-hosted API disabled by default) | Phase 4 Step 4c — Enable the API; `validate-server` maps a 403 on `GET /version` to that remedy. |
| F7 | M | NEEDS_REFINEMENT | Documented only the supported installer variables (`ROOT_USERNAME` / `ROOT_USER_EMAIL` / `ROOT_USER_PASSWORD`) as an optional instructor path; the `artisan tinker` token hack is not prescribed (internal API, fragile). |
| F8 | M | CONFIRMED (logs need `read:sensitive`) | Token wording: `root`, or read + write + deploy + read:sensitive — Phase 4 Step 4d, `--training-init` token step, `.env.training` header comment, `--logs` 403 remedy, Hetzner reference §7. |
| F9 | M | CONFIRMED (Ubuntu 24.04 unit is `ssh`) | `systemctl restart ssh` after `sshd -t`. |
| F10 | M | CONFIRMED | `DEBIAN_FRONTEND=noninteractive` on every apt-get; `dpkg-reconfigure` replaced by writing `20auto-upgrades`. |
| F11 | M | CONFIRMED | `deploy.py env-set KEY --stdin` (hidden prompt on a terminal, first line on a pipe); activity stores tokens via the user's own terminal or a `printf` builtin pipe. |
| F12 | L | NEEDS_REFINEMENT | Defaults kept; Phase 2 Step 4 and the SSH reference state that any key path works via `SSH_KEY` (quoted if it contains spaces). |
| F13 | L | NEEDS_REFINEMENT | Firewall now created before the server and attached with `--firewall`; optional `--label` pairs for instructors; `gse-` prefix kept (destroy derives `gse-fw-<name>`). |
| F14 | L | CONFIRMED | `record-server --ipv6` (state `server.ipv6`); Phase 4 passes `record-coolify --version`; optional AAAA records in Phase 5 Step 1. |
| F15 | L | CONFIRMED | CAX/CX prices re-verified; Phase 2 Gate reads the live `hcloud server-type describe` price; `deploy.py` cost hints and corpus "~8.49" mentions updated. |
| F16 | L | CONFIRMED | `ufw-docker` pinned to commit `020a8699f955…` with SHA-256 `643e56b0…35ab0` check (hash re-computed, matches the rehearsal). |
| F17 | L | CONFIRMED | Phase 1 Step 3 — Domain name may be skipped; Phase 5 Step 1 asks for it when absent. |
| F18 | L | CONFIRMED (no change needed) | One-line note in Phase 2 Step 5: ports 6001/6002 may stay closed for the API-driven flow. |
| F19 | L | FALSE_POSITIVE (harmless) | `record-role` creating the state before `init-state` is by design (`init-state` is idempotent); no change. |
| F20 | L | NEEDS_REFINEMENT | No GSE-One tool builds a `UserKnownHostsFile=` option (grep of tools, installer, activities). The SSH reference now quotes `-i "$SSH_KEY_PATH"` and documents the inner quoting `-o "UserKnownHostsFile=\"$KNOWN_HOSTS\""`. |
| F21 | H | CONFIRMED (Coolify 4.7.6 routes: only `/settings/email`; `PATCH /settings/general` answers 404) | Phase 5 Step 3 — Configure Coolify dashboard domain sets `InstanceSettings.fqdn` via `artisan tinker` then `Server::find(0)->setupDynamicProxyConfiguration()` (what the UI Save does); UI fallback documented. Verified: Let's Encrypt certificate issued in ~15 s. Hetzner reference row removed. |
| F22 | M | CONFIRMED (`hcloud firewall delete-rule` matches every field) | Rules carrying a description are not found without `--description`. Phase 2 now names each rule `<protocol>-<port>`; Phase 5 Step 5 — Close temporary port 8000 passes `--description tcp-8000` and checks the remaining rules. |
| F23 | H | CONFIRMED (Coolify 4.7.6 422: `git_repository` must be a URL; `dockerfile_location` must start with `/`) | `CoolifyClient.create_application` expands an `owner/repo` slug to `https://github.com/owner/repo`; default `dockerfile_location` is `/Dockerfile`. Every learner deploy would have failed in class. `deploy-app` errors now include `details` (Coolify's field-level reason). |
| F24 | M | CONFIRMED (app created, then the deploy trigger failed before state was saved) | `deploy-app` adopts a same-name application found in the user's own project environment and redeploys it instead of creating a duplicate. |
| F25 | H | CONFIRMED (Coolify 4.7.6 `GET /deploy` answers 405 "This endpoint has changed to a POST request") | `trigger_deploy` uses POST (GET fallback on 405 for older instances); reference, agent, activity and cheatsheet updated. |
| F26 | H | CONFIRMED (Coolify 400 "Project has resources"; application deletion is a queued job) | `training-reap` deletes each application of the learner project, then retries the project deletion for up to 90 s; result lists `deleted_applications`. |
| F27 | L | NO CHANGE | Preflight warns about the untracked `.gse/` that `record-role` itself creates in a fresh clone; in a real learner project `.gse/` is committed. |

Learner-path result after the fixes: deploy healthy in 45 s (Let's Encrypt certificate for the app name),
`deploy.py logs` shows the nginx access log (internet scanners appear within seconds of the certificate
being issued — useful debrief material), `training-reap --user rehearsal` removes app and project in 1.5 s.

## Tests

`gse-one/tests/test_deploy.py` gains mocked (no network) tests for
`env-set --stdin`, `record-server --ipv6`, `validate-server` (happy path,
API-disabled 403, unreachable timeout, older `settings.is_reachable` shape)
and the `CoolifyClient` validate POST / 405→GET fallback / plain-text version.
