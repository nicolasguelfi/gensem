---
name: "gse-deploy"
description: "Deploy the current project to a Hetzner server via Coolify. Adapts to the user's situation: from zero infrastructure (solo) to a pre-configured shared server (training). Triggered by /gse:deploy."
---


# GSE-One Deploy — Hetzner Deployment

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args) | Deploy current project (detect situation, resume from last phase) |
| --status | Show deployment status (server, app URL, health) |
| --logs [--lines N] | Show the last N lines (default 100) of your deployed app's runtime logs — first thing to read when the app does not start or the health check fails |
| --destroy | Tear down server and all data (Gate, confirm twice) |
| --redeploy | Force rebuild and redeploy (skip infrastructure phases) |
| --registrar `<name>` | Show DNS instructions for a specific registrar (`namecheap`, `gandi`, `ovh`, `cloudflare`) without re-running earlier phases |
| --silent | Skip the Step -1 Orientation (for scripting/CI or experienced users) |
| --training-init | (Instructor) Generate `.env.training` for distribution to learners |
| --training-reap | (Instructor) Delete learner apps at end of course |
| --help | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/config.yaml` — deploy section (provider, server type, datacenter)
2. `.gse/deploy.json` — infrastructure state (if exists)
3. `.env` — credentials and configuration (if exists). **Do not read this file whole**: it holds API tokens (in training mode, the shared course token that can write to every learner app), and reading it puts their values in the model context. Use the presence map returned by `deploy.py detect` (Step 0 — Situation Detection) to know which keys are set, and `deploy.py env-get <KEY>` when a step needs one value; the shell checks below (`test -f`, `grep -E '^KEY='`) test presence without printing secrets. Never display, log, or commit a token value.
4. `.gse/profile.yaml` — user profile (apply P9 Adaptive Communication to all output)
5. `$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/agents/deploy-operator.md` — adopt this role for the entire activity
6. `$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/references/hetzner-infrastructure.md` — pricing, sizing, Coolify API (consulted on demand)
7. `$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/references/ssh-operations.md` — SSH patterns and credential resolution (consulted on demand)

## Workflow

> **Workflow structure note.** `/gse:deploy` uses a two-level hierarchy reflecting its deployment lifecycle:
> - **Step -1 and Step 0** (Orientation, Situation Detection) — pre-flight checks before committing to a lifecycle.
> - **Phase 1 through Phase 6** (Setup → Provision → Secure → Install Coolify → Configure DNS → Deploy Application) — the main deployment lifecycle. Each Phase corresponds to an idempotent milestone tracked in `.gse/deploy.json` under `phases_completed.<phase_name>`; a completed Phase is automatically skipped on re-run.
> - **Step N inside a Phase** — sub-steps within a Phase (e.g., "Step 3 — Dockerfile template selection" inside Phase 6). This internal numbering resets for each Phase.
>
> This two-level hierarchy is specific to `/gse:deploy` — other GSE-One activities use a flat Step sequence. The distinction reflects the idempotent-milestone nature of deployment.
>
> **Boundary note (per spec §1.4 — Design Philosophy).** DEPLOY is an opinionated operations module (Hetzner + Coolify + Docker), deliberately outside the technology-neutral methodological core — the stack is a supported choice, not a methodology requirement.

### Step -1 — Orientation (first-time users only)

**Skip this step if ANY of the following is true:**
- The `--silent` flag was passed
- `.gse/deploy.json` already exists
- Any of these env vars are set in `.env`: `HETZNER_API_TOKEN`, `SERVER_IP`, `COOLIFY_URL`, `COOLIFY_API_TOKEN`, `DEPLOY_DOMAIN`, `DEPLOY_USER`

Otherwise (first-time user), display:

> Welcome to `/gse:deploy`. This command provisions infrastructure and deploys your project. First, let me understand your situation:
>
>   (1) **Solo** — Deploy my own project to my own Hetzner server. (~1h first time, ~11 EUR/month ongoing for the default CAX21 server. You'll need a Hetzner account and optionally a domain.)
>
>   (2) **Instructor** — Prepare a shared server for a training session. (~1h setup, then distribute a `.env.training` file to learners. Reap at course end.)
>
>   (3) **Learner** — My instructor sent me a `.env.training` file to use. (~5 min. You only deploy your project, no server setup.)
>
>   (4) **Skip** — I know what I'm doing, proceed to detection.
>
> Which are you? [1/2/3/4]

Wait for the user's answer, then route:

**(1) Solo** — Persist role and brief:
```
python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-role solo
```
Say: *"You'll go through 6 phases: installing the hcloud CLI, creating a Hetzner server, hardening it, installing Coolify, configuring DNS/SSL, and deploying your project. I'll guide you at each step. Type 'ready' to begin."*
Wait for confirmation → proceed to Step 0.

**(2) Instructor** — Persist role and brief:
```
python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-role instructor
```
Say: *"I'll walk you through the full 6-phase setup (same as Solo mode), then help you generate a `.env.training` file with `--training-init` to distribute to your learners. Heads-up: the token in that file gives learners write access to ALL apps on the shared server — we'll use a course-dedicated token you revoke at the end. If a learner's app is damaged or deleted mid-course (the shared token makes that possible), recovery is built in: the learner just re-runs `/gse:deploy` — the app is recreated from their GitHub repo in ~5 minutes. At the end of the course, run `/gse:deploy --training-reap --all` to clean up all learner apps (then revoke the token). Ready to start the server setup?"*
Wait for confirmation → proceed to Step 0.

**(3) Learner** — Three precondition checks. Do NOT ask the learner — each one is deterministically verifiable in under a second; run the checks yourself and only surface the remediation message when a check fails (self-reported y/n answers are a classroom failure amplifier: a learner answers "yes" in good faith, is wrong, and fails 10 minutes later with a cryptic error):
1. Check `.env` exists: `test -f .env`
   - If missing: *"I can't find a `.env` file. Copy the `.env.training` file your instructor sent you into your project directory as `.env` (`cp .env.training .env`). Then re-run `/gse:deploy`."* → Exit.
2. Check `DEPLOY_USER` is set and is not the placeholder: `grep -E '^DEPLOY_USER=' .env` must match and must NOT be the `learnerXX` placeholder written by `--training-init`.
   - If unset/placeholder: *"Open `.env` in your editor, set `DEPLOY_USER=<your-learner-id>`, save, and re-run `/gse:deploy`."* → Exit.
3. Check the project has a GitHub remote: `git remote -v` shows an `origin` pointing at github.com (Coolify clones from GitHub — an unpushed project fails at deploy time). Optionally confirm the branch is pushed (`git status -sb` shows no `ahead` marker).
   - If no remote: *"Push it first: create a repo (`gh repo create` or the GitHub UI), then `git push -u origin <branch>`. A public repo is simplest for the course; for a private repo, follow the GitHub App guide (`cat "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/references/private-repo-github-app-setup.md"`, section B) BEFORE deploying. Then re-run `/gse:deploy`."* → Exit.

On success, state what was verified in one line — e.g. *"Checked: `.env` found with `DEPLOY_USER=alice`; GitHub remote `origin` present."* — so the learner sees the preflight passed.
4. Persist role:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-role learner
   ```
5. Say: *"I'll detect your instructor's shared server from the training config and deploy your project at `{project-name}-{DEPLOY_USER}.{DEPLOY_DOMAIN}`. Expected duration: ~5 minutes."*
6. Proceed to Step 0 (will detect app-only mode → Phase 6).

**(4) Skip** — Meta-action (not a role value): no `record-role` call; no `user_role` persisted in `deploy.json`. Proceed directly to Step 0. The 3 role values stored in `user_role` are `solo` / `instructor` / `learner` only — see design §5.18 State schema for the enum.

---

### Step 0 — Situation Detection

Invoke the deploy tool:

```
python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" detect
```

This returns a JSON object with `starting_phase`, `mode` (`full | partial | app-only | training`), the presence map of `.env` variables, and the `phases_completed` map. Use the returned `starting_phase` to skip already-completed phases (idempotence is handled by the tool, not by this skill).

**`.env` variables (all optional) — for reference:**

| Variable | Purpose | Level |
|----------|---------|-------|
| `HETZNER_API_TOKEN` | Hetzner Cloud API access | Infrastructure |
| `SERVER_IP` | Pre-existing server IP address | Server |
| `SSH_USER` | SSH username (default: deploy) | Server |
| `SSH_KEY` | Path to SSH private key | Server |
| `COOLIFY_URL` | Coolify dashboard URL | Coolify |
| `COOLIFY_API_TOKEN` | Coolify API access | Coolify |
| `DEPLOY_DOMAIN` | Base domain for subdomains | Domain |
| `DEPLOY_USER` | User identity for subdomain prefix (training mode) | Identity |

The detection logic (which variables map to which starting phase) is documented in `gse-one-implementation-design.md` §5.18 — /gse:deploy — Application Deployment Activity ("Situation detection" table) and authoritatively applied by the `detect` subcommand. Trust its output — do not re-derive the mapping from the table above.

**Display the detected situation to the user:**
- Full mode: *"No deployment configuration found. I'll guide you through the complete setup."*
- Partial: *"I found a server at {IP}. Starting from there."*
- App-only: *"Deployment infrastructure is ready ({COOLIFY_URL}). I'll deploy your application."*
- Training: *"Training mode detected. I'll deploy your project on the shared server. The full URL will be shown after Phase 6 (typically `{project-name}-{DEPLOY_USER}.{DEPLOY_DOMAIN}`)."*

---

### Phase 1 — Setup (skip if `HETZNER_API_TOKEN` in `.env`)

**Purpose:** Install CLI tools, obtain credentials, save configuration.

1. **Check hcloud CLI**
   - Run `hcloud version`
   - If not found, install:
     - macOS: `brew install hcloud`
     - Linux: download from https://github.com/hetznercloud/cli/releases
     - Windows: `winget install hetznercloud.cli` or direct download
   - Verify: `hcloud version`

2. **Obtain Hetzner API token**
   - Guide the user step by step:
     *"Go to https://console.hetzner.cloud → select or create a project → Security → API Tokens → Generate API Token (Read & Write). Copy the token — it is shown only once."*
   - **Never display the token back in chat**

3. **Domain name**
   - Ask: *"What domain will you use for deployment? (e.g., my-project.com)"*
   - The domain may be decided later (typical for an instructor whose DNS is not ready yet): then skip it here — `detect` works without `DEPLOY_DOMAIN`, and Phase 5 — Configure DNS asks for it before configuring DNS.

4. **Save credentials**
   - **Secrets never go on a command line** (a command-line argument is visible to every local user in the process list and stays in the agent transcript). Preferred: ask the user to run, in their own terminal, `python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set HETZNER_API_TOKEN --stdin` and paste the token at the hidden prompt — the token then never enters the chat. If the user pasted it in the chat instead, pipe it through the shell builtin `printf` (builtins do not appear in the process list):
     ```
     printf '%s\n' '<token>' | python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set HETZNER_API_TOKEN --stdin
     python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set DEPLOY_DOMAIN <domain>   # skip if no domain yet (Step 3)
     ```
   - Check `.gitignore` contains `.env` — if not, add it and warn the user
   - If no `.gitignore` exists: Gate decision to create one

5. **Verify hcloud access**
   - Run `hcloud server list` to confirm the token works
   - If it fails: ask user to verify the token

6. **Persist completion**
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" init-state
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-phase setup
   ```

---

### Phase 2 — Provision (skip if `SERVER_IP` in `.env` or `deploy.json` has `phases_completed.provision`)

**Purpose:** Create a Hetzner server with firewall.

1. **Read configuration**
   - Server type: `config.yaml → deploy.server_type` (default: `cax21`)
   - Datacenter: `config.yaml → deploy.datacenter` (default: `fsn1`)
   - Server name: `gse-<project-name>` (sanitized, lowercase, hyphens only). An instructor may pick a course name instead (e.g. `gse-<course>`); keep the `gse-` prefix — `--destroy` derives the firewall name `gse-fw-<name>` from it.

2. **Check for existing server**
   - `hcloud server list -o columns=name,ipv4`
   - If a server with this name exists: skip provision, record IP

3. **Gate decision: server creation**
   - Read the **live** price first (the reference tables go stale — Hetzner changes prices): `hcloud server-type describe <type> -o json` → `prices[]` entry whose `location` is the datacenter → `price_monthly.net` (EUR excl. VAT; add ~0.50 EUR for the primary IPv4).
   - Display cost and configuration:
     *"Creating a Hetzner server:*
     *- Type: CAX21 (4 vCPU ARM, 8 GB RAM, 80 GB SSD)*
     *- Location: Falkenstein (fsn1)*
     *- Monthly cost: {live price} EUR excl. VAT (+ ~0.50 EUR primary IPv4)*
     *Proceed?"*
   - Wait for explicit user confirmation

4. **Generate SSH key** (if `~/.ssh/gse-deploy` does not exist)
   - `ssh-keygen -t ed25519 -f ~/.ssh/gse-deploy -N ""`
   - Upload: `hcloud ssh-key create --name gse-deploy --public-key-from-file ~/.ssh/gse-deploy.pub`
   - Any other key path and Hetzner key name work (e.g. an instructor's course-dedicated key kept next to the course files instead of `~/.ssh`): `SSH_KEY` in `.env` (Step 8) records the path — substitute it for `~/.ssh/gse-deploy` in every `ssh -i` below, **double-quoted** if the path contains spaces (see `plugin/references/ssh-operations.md` — Paths with spaces).

5. **Create firewall** (before the server, so the server is never exposed without it)
   - `hcloud firewall create --name gse-fw-<name>` (instructors sharing one Hetzner project across courses: add `--label` pairs, e.g. `--label role=training`, here and in Step 6, to find and clean the course resources later)
   - Add inbound rules, each for IPv4 and IPv6 (`--source-ips 0.0.0.0/0 --source-ips ::/0`): TCP 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (Coolify setup, temporary), and ICMP (ping). Give each rule a description `<protocol>-<port>` (`icmp` for ICMP) so it can be deleted later (Phase 5 Step 5 — Close temporary port 8000). Example: `hcloud firewall add-rule gse-fw-<name> --direction in --protocol tcp --port 22 --source-ips 0.0.0.0/0 --source-ips ::/0 --description tcp-22`
   - Coolify also publishes ports 6001/6002 (dashboard live updates and web terminal). Leaving them closed is fine for the API-driven `/gse:deploy` flow (the dashboard may show a realtime warning).

6. **Create server**
   - `hcloud server create --name <name> --type <type> --location <datacenter> --image ubuntu-24.04 --ssh-key gse-deploy --firewall gse-fw-<name>` (+ the same optional `--label` pairs)
   - Record id, IPv4 and IPv6: `hcloud server describe <name> -o json` → `id`, `public_net.ipv4.ip`, `public_net.ipv6.ip` (an IPv6 /64 network — the server's address is `<network>::1`, used for optional AAAA records in Phase 5 — Configure DNS)

7. **Verify SSH access**
   - `ssh -i ~/.ssh/gse-deploy -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 root@<IP> "echo ok"`
   - Retry up to 3 times with 15s wait between attempts (per `plugin/references/ssh-operations.md` — the canonical SSH pattern source)

8. **Persist completion**
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-server \
     --name <name> --ipv4 <IP> --ipv6 <IPv6 network> --id <id> --type <type> --datacenter <dc>
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set SERVER_IP <IP>
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set SSH_USER root
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set SSH_KEY ~/.ssh/gse-deploy
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-phase provision
   ```

---

### Phase 3 — Secure (skip if `deploy.json` has `phases_completed.secure`)

**Purpose:** Harden the server — non-root user, SSH hardening, firewall, intrusion detection.

> **Command-chain note.** Each step below is one `&&` chain: if any command fails, the rest is skipped *and the ssh exit status is non-zero*. Always check that status and the command output; on failure stop, show the error to the user, and do not mark the phase complete.

1. **Create deploy user**
   - ```
     ssh root@<IP> "adduser --disabled-password --gecos '' deploy && \
       usermod -aG sudo deploy && \
       echo 'deploy ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/deploy"
     ```
   - Copy SSH key:
     ```
     ssh root@<IP> "mkdir -p /home/deploy/.ssh && \
       cp /root/.ssh/authorized_keys /home/deploy/.ssh/ && \
       chown -R deploy:deploy /home/deploy/.ssh && \
       chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys"
     ```

2. **Verify deploy user SSH**
   - `ssh -i ~/.ssh/gse-deploy -o ConnectTimeout=10 deploy@<IP> "sudo echo ok"`
   - **CRITICAL: do not proceed if this fails** — root access will be disabled next

3. **Harden SSH**
   - **Root login stays possible from Coolify's Docker networks only, by key only.** Coolify (Phase 4 — Install Coolify) manages its own host over SSH as `root`, from a Docker network (`10.x` / `172.16–31.x`) — a global `PermitRootLogin no` makes the host unreachable for Coolify and its Traefik proxy never starts (apps become undeployable). So: root login is refused from the internet, and allowed with an SSH key (never a password) from local Docker networks only.
   - Settings go in a drop-in file read **first** (`00-` prefix — sshd keeps the first value it reads, so it wins over e.g. a cloud-init `PasswordAuthentication yes`), and the Docker-network exception is a `Match` block appended at the **end** of `sshd_config` (a `Match` block runs until the end of the file):
     ```
     ssh deploy@<IP> "printf '%s\n' 'PermitRootLogin no' 'PasswordAuthentication no' \
         'KbdInteractiveAuthentication no' 'PubkeyAuthentication yes' \
         | sudo tee /etc/ssh/sshd_config.d/00-gse-hardening.conf >/dev/null && \
       (grep -q '^Match Address 10.0.0.0/8' /etc/ssh/sshd_config || \
         printf '\n%s\n%s\n' 'Match Address 10.0.0.0/8,172.16.0.0/12,fd00::/8,127.0.0.1,::1' \
           '    PermitRootLogin prohibit-password' | sudo tee -a /etc/ssh/sshd_config >/dev/null) && \
       sudo sshd -t && sudo systemctl restart ssh"
     ```
     On Ubuntu 22.04+/Debian the systemd unit is `ssh` (`systemctl restart sshd` fails with "Unit sshd.service not found" and leaves the hardening unapplied).
   - Verify (both must hold):
     - `ssh deploy@<IP> "sudo sshd -T | grep -Ei '^(permitrootlogin|passwordauthentication) '"` → `permitrootlogin no`, `passwordauthentication no`
     - `ssh deploy@<IP> "sudo sshd -T -C user=root,host=localhost,addr=10.0.0.2 | grep -i '^permitrootlogin'"` → `permitrootlogin prohibit-password`

4. **Install UFW firewall**
   - ```
     ssh deploy@<IP> "sudo apt-get update -qq && \
       sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ufw && \
       sudo ufw default deny incoming && sudo ufw default allow outgoing && \
       sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && \
       sudo ufw allow 443/tcp && sudo ufw allow 8000/tcp && \
       sudo ufw --force enable"
     ```
   - Docker is not installed yet: the `ufw-docker` protection (Docker would otherwise bypass these rules) is installed right after Coolify, in Phase 4 Step 3 — Install ufw-docker.

5. **Install fail2ban** (before Coolify, with Docker networks ignored)
   - Coolify's own SSH connections come from Docker addresses; if one is ever refused (e.g. hardening mistake), fail2ban would ban Coolify itself and turn the error into a misleading "Connection refused". The jail therefore ignores local Docker networks:
     ```
     ssh deploy@<IP> "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq fail2ban && \
       printf '%s\n' '[DEFAULT]' 'ignoreip = 127.0.0.1/8 ::1 10.0.0.0/8 172.16.0.0/12 fd00::/8' \
         '' '[sshd]' 'enabled = true' 'maxretry = 3' 'bantime = 1h' \
         | sudo tee /etc/fail2ban/jail.local >/dev/null && \
       sudo systemctl enable fail2ban && sudo systemctl restart fail2ban"
     ```
   - Verify: `ssh deploy@<IP> "sudo fail2ban-client status sshd"` (jail active). If a Docker address was banned before this fix: `sudo fail2ban-client unban <address>`.

6. **Automatic security updates** (non-interactive — `dpkg-reconfigure` would wait for a keyboard answer over a non-tty SSH session)
   - ```
     ssh deploy@<IP> "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq unattended-upgrades && \
       printf '%s\n' 'APT::Periodic::Update-Package-Lists \"1\";' 'APT::Periodic::Unattended-Upgrade \"1\";' \
         | sudo tee /etc/apt/apt.conf.d/20auto-upgrades >/dev/null"
     ```

7. **Persist completion**
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set SSH_USER deploy
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-phase secure
   ```

---

### Phase 4 — Install Coolify (skip if `COOLIFY_URL` in `.env` or `deploy.json` has `phases_completed.coolify`)

**Purpose:** Install Coolify v4 (self-hosted PaaS with Traefik reverse proxy).

1. **Install Coolify**
   - `ssh deploy@<IP> "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash"` (also installs Docker)
   - Optional (instructor, unattended install): the Coolify installer can pre-create the admin account from the environment variables `ROOT_USERNAME`, `ROOT_USER_EMAIL`, `ROOT_USER_PASSWORD`, so the public registration page of Step 4 is never exposed. The password is then briefly visible in the server's process list — change it in the dashboard afterwards. Default path: the browser registration of Step 4.

2. **Wait for readiness**
   - Poll `http://<IP>:8000` every 15 seconds, timeout 5 minutes
   - Show progress: *"Waiting for Coolify to start..."*

3. **Install ufw-docker** (prevents Docker from bypassing UFW rules — requires Docker, hence after Step 1)
   - By default, Docker publishes containers to `0.0.0.0` and inserts iptables rules that bypass UFW. Without `ufw-docker`, a container exposing port `5432` to the host would be reachable from the internet even if UFW denies port `5432`. This is a real production risk.
   - Once `ufw-docker` is active, traffic to containers is filtered in the *forwarded* path: `ufw allow` (Phase 3 Step 4 — Install UFW firewall) no longer suffices, each published container port needs a `ufw route allow` rule. The rule names the port **inside** the container: Traefik listens on 80/443, the Coolify dashboard on 8080 (published as host port 8000). Without these rules, 80/443/8000 all time out from the internet.
   - The script is pinned to a reviewed commit and checked by SHA-256 (it runs as root — never fetch a moving branch):
     ```
     ssh deploy@<IP> "sudo wget -qO /usr/local/bin/ufw-docker \
         https://raw.githubusercontent.com/chaifeng/ufw-docker/020a8699f95592561f254d8d4ad1bb40d401dfc7/ufw-docker && \
       echo '643e56b080567c567b4aa28650196849b2a2da5dd0473fd3e5216b0886035ab0  /usr/local/bin/ufw-docker' | sudo sha256sum -c - && \
       sudo chmod +x /usr/local/bin/ufw-docker && \
       sudo ufw-docker install && \
       sudo ufw route allow proto tcp from any to any port 80 && \
       sudo ufw route allow proto tcp from any to any port 443 && \
       sudo ufw route allow proto udp from any to any port 443 && \
       sudo ufw route allow proto tcp from any to any port 8080 && \
       sudo systemctl restart ufw"
     ```
     If `sha256sum -c` fails, stop: the pinned file changed — do not run it (maintainers update the commit + hash after review).
   - Verify: `ssh deploy@<IP> "sudo ufw-docker status"` (rules active) and, from the local machine, `http://<IP>:8000` answers again (Step 2 poll, one attempt).

4. **Guide browser setup (detailed)**
   Walk the user through the Coolify onboarding. Tell them verbatim:

   > Coolify is ready. Open `http://<IP>:8000` in your browser — do it now: until an admin account exists, anyone reaching this page can create it.
   >
   > **4a. Create your admin account:**
   > - Fill in: *Email*, *Name*, *Password* (min 8 chars), *Confirm password*
   > - Click **Register**. You are now logged in.
   >
   > **4b. Initial setup wizard:**
   > - Coolify displays a *"Welcome"* screen. Click **Let's go!** or **Skip** through optional settings (root user email, instance name — you can change these later in Settings). If it asks which server to use, choose **This Machine** (localhost).
   >
   > **4c. Enable the API** (self-hosted Coolify ships with the API disabled — every API call fails until it is enabled):
   > - **Settings** → **Advanced** → set **API Access** to enabled → **Save**.
   >
   > **4d. Create an API token:**
   > - In the left sidebar, click your profile icon (bottom left) → **Keys & Tokens** → **API Tokens** tab.
   > - Click **Create New Token**.
   > - Name it: `gse-one`
   > - Permissions: check **root** (full access — simplest). Otherwise check at least **read**, **write**, **deploy** and **read:sensitive**: `read:sensitive` is required to read runtime logs (`/gse:deploy --logs` answers 403 without it — including for learners when this token is distributed by `--training-init`), and `write` + `deploy` to validate the server (Step 5).
   > - Click **Continue**. The token is displayed **only once** — copy it now.
   >
   > **4e. Store the token** — in your own terminal (hidden prompt, the token never enters the chat): `python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set COOLIFY_API_TOKEN --stdin`

   Then persist the URL (and, only if the user pasted the token in the chat instead of 4e, store it via the builtin `printf` pipe — never as a command-line argument):
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set COOLIFY_URL http://<IP>:8000
   printf '%s\n' '<token>' | python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set COOLIFY_API_TOKEN --stdin   # fallback only
   ```

   **If the UI has changed** (Coolify iterates fast), adapt the step numbering to what the user describes. The invariants are: create account → enable API access → find "API tokens" or equivalent → create token with full-access (or read + write + deploy + read:sensitive) permissions → copy once. If a step path differs significantly, please consider submitting a PR to update this section (see README → Deployment → Maintaining upstream compatibility).

5. **Validate the Coolify host server** (starts the Traefik proxy)
   - Coolify starts its reverse proxy (`coolify-proxy`, Traefik) only once its own host server ("localhost") is validated — until then no app can be served. Invoke:
     ```
     python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" validate-server
     ```
     The tool checks the API (`GET /version`), resolves and persists `SERVER_UUID`, sends `POST /api/v1/servers/{uuid}/validate` (Coolify 4.7+ — older versions used GET; the tool falls back), and polls until the server is reachable (default 180 s). It returns `{status, server_uuid, coolify_version, ...}`; the token is never printed.
   - `status == "error"` with `http_status` 403 → API access not enabled (Step 4c) or token without `write`/`deploy`; 401 → token rejected (redo Step 4d/4e).
   - `status == "timeout"` → Coolify cannot SSH into its host as root: re-check Phase 3 Step 3 — Harden SSH (the `sshd -T -C …addr=10.0.0.2` check must print `prohibit-password`) and Phase 3 Step 5 — Install fail2ban (`sudo fail2ban-client status sshd` must not list a Docker address), then re-run `validate-server`.

6. **Verify containers**
   - `ssh deploy@<IP> "sudo docker ps --format 'table {{.Names}}\t{{.Status}}'"` 
   - Check running: `coolify`, `coolify-db` (PostgreSQL), `coolify-redis`, `coolify-proxy` (Traefik — present only after Step 5)

7. **Persist completion**
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-coolify --url http://<IP>:8000 --version <coolify_version from Step 5>
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-phase coolify
   ```

---

### Phase 5 — Configure DNS (skip if `deploy.json` has `phases_completed.dns`)

**Purpose:** Point the domain to the server and enable SSL.

1. **Guide DNS configuration**
   - If `DEPLOY_DOMAIN` is not set yet (the domain was skipped in Phase 1 Step 3 — Domain name), ask for it now and persist it: `python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set DEPLOY_DOMAIN <domain>`.
   - Tell the user (verbatim):
     > Add these DNS records at your domain registrar:
     > | Type | Name | Value        | TTL |
     > |------|------|--------------|-----|
     > | A    | `@`  | `<server-IP>` | 300 |
     > | A    | `*`  | `<server-IP>` | 300 |
     >
     > The wildcard `*` enables all subdomains (`project-a.domain.com`, `project-b.domain.com`, ...) to point to this server automatically — essential for the multi-app pattern.
     >
     > Optional IPv6: add the same two names as `AAAA` records pointing to `<server-IPv6>` (the `server.ipv6` network recorded in Phase 2, with `::1` as host part — e.g. `2001:db8:1:2::1`).
   - Ask the user which registrar they use; if one of the four below, display the registrar-specific subsection. Otherwise, provide the generic records and invite them to follow their registrar's documentation (you can also run `/gse:deploy --registrar <name>` later to re-display the steps).

   #### 1a. Namecheap
   1. Log in at https://www.namecheap.com → **Domain List** (top menu).
   2. Next to your domain, click **Manage**.
   3. Open the **Advanced DNS** tab.
   4. Under **Host Records**, click **Add New Record**:
      - Type: `A Record`, Host: `@`, Value: `<server-IP>`, TTL: `Automatic`.
   5. Click **Add New Record** again:
      - Type: `A Record`, Host: `*`, Value: `<server-IP>`, TTL: `Automatic`.
   6. Click the green check next to each to save. Changes propagate in 5–30 minutes.

   #### 1b. Gandi
   1. Log in at https://admin.gandi.net → **Domaines** (or **Domains**).
   2. Click your domain → **DNS Records** (or **Enregistrements DNS**).
   3. Click **Add record**. Type `A`, Name `@`, TTL `300`, Value `<server-IP>`. Save.
   4. Click **Add record** again. Type `A`, Name `*`, TTL `300`, Value `<server-IP>`. Save.

   #### 1c. OVH
   1. Log in at https://www.ovh.com/manager/ → **Web Cloud** → **Domains** (or **Noms de domaine**).
   2. Click your domain → **DNS Zone** (or **Zone DNS**).
   3. Click **Add an entry**:
      - Type: `A`, Sub-domain: (leave empty for `@`), Target: `<server-IP>`, TTL: `300`.
   4. Click **Add an entry** again:
      - Type: `A`, Sub-domain: `*`, Target: `<server-IP>`, TTL: `300`.

   #### 1d. Cloudflare (DNS-only for now, CDN opt-in later)
   1. Log in at https://dash.cloudflare.com → click your domain.
   2. Open the **DNS** → **Records** page.
   3. Click **Add record**:
      - Type: `A`, Name: `@`, IPv4 address: `<server-IP>`, Proxy status: **DNS only** (grey cloud), TTL: `Auto`.
   4. Click **Add record** again:
      - Type: `A`, Name: `*`, IPv4 address: `<server-IP>`, Proxy status: **DNS only** (grey cloud), TTL: `Auto`.
   5. **Important:** keep the proxy OFF at this stage. Let's Encrypt needs direct DNS resolution to issue the certificate. After SSL is active and Coolify dashboard works, the next step (CDN proposal) offers to enable proxy + CDN.

2. **Verify DNS propagation**
   Invoke the tool with a timeout of 10 minutes:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" wait-dns \
     --domain <domain> --expected-ip <server-IP> --timeout 600
   ```
   The tool polls `dig` (system resolver + `@8.8.8.8` fallback every 15s). On `resolved`, proceed. On `timeout`, it returns a hint — display it to the user and exit the skill without marking the phase complete (so the user can re-run `/gse:deploy` once propagation completes).

3. **Configure Coolify dashboard domain**
   The Coolify API has no endpoint for the instance domain (only `/settings/email` — verified on Coolify 4.7.6). Set the dashboard FQDN to `coolify.<domain>` inside the Coolify container, then regenerate the proxy routing (the same two calls the UI's Settings → Save makes):
   ```
   ssh deploy@<IP> 'sudo docker exec coolify php artisan tinker --execute="\$s = \App\Models\InstanceSettings::get(); \$s->fqdn = \"https://coolify.<domain>\"; \$s->save(); \App\Models\Server::find(0)->setupDynamicProxyConfiguration(); echo \$s->fqdn;"'
   ```
   The command echoes the new URL. Fallback if it fails: the user opens `http://<IP>:8000` → **Settings** → **Instance's Domain** = `https://coolify.<domain>` → **Save**.
   Then update the env:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-set COOLIFY_URL https://coolify.<domain>
   ```

4. **Verify SSL (Let's Encrypt via Traefik)**
   Coolify+Traefik requests a Let's Encrypt certificate automatically on first HTTPS request. Poll until it succeeds (max 2 minutes):
   ```
   for i in $(seq 1 8); do
     if curl -sI "https://coolify.<domain>" 2>/dev/null | grep -q "HTTP.*200\|HTTP.*301\|HTTP.*302"; then
       echo "SSL OK"; break
     fi
     sleep 15
   done
   ```
   If SSL fails, check DNS propagation first (`dig coolify.<domain>` must return `<server-IP>`).

5. **Close temporary port 8000**
   - `ssh deploy@<IP> "sudo ufw delete allow 8000/tcp && sudo ufw route delete allow proto tcp from any to any port 8080"` (the route rule is the `ufw-docker` path to the dashboard container — Phase 4 Step 3 — Install ufw-docker)
   - `hcloud firewall delete-rule gse-fw-<name> --direction in --protocol tcp --port 8000 --source-ips 0.0.0.0/0 --source-ips ::/0 --description tcp-8000`
   - `delete-rule` matches every field of the rule, description included: it must repeat the `--description` given at creation (Phase 2), otherwise hcloud answers "rule not found". Check with `hcloud firewall describe gse-fw-<name>` that only 22, 80, 443 and ICMP remain.

6. **Persist domain completion**
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-domain --base <domain> --registrar <namecheap|gandi|ovh|cloudflare|manual>
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-phase dns
   ```

7. **Propose Cloudflare CDN + DDoS + WAF (recommended for production)**

   Ask the user (Inform tier):
   > Your domain is live. Would you like to add Cloudflare CDN & DDoS protection? (free plan, ~10 minutes, no downtime)
   >
   > Benefits:
   > - Free CDN (faster page loads worldwide)
   > - DDoS protection (layer 3/4/7)
   > - Bot & AI-scraper detection/blocking
   > - Web Application Firewall (WAF)
   > - Rate limiting per IP
   > - Analytics & threat dashboard
   >
   > Without it, the server has only: Hetzner network-level DDoS (L3/L4), UFW firewall, fail2ban (SSH only).

   **If the user declines:** record `--provider none` and exit this step:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-cdn --provider none
   ```

   **If the user accepts:** walk them through:

   7a. Create a free Cloudflare account at https://dash.cloudflare.com (skip if they have one).

   7b. Click **Add a site** → enter the domain → **Free plan**.

   7c. Cloudflare displays nameservers (e.g., `nina.ns.cloudflare.com`, `rob.ns.cloudflare.com`). **Copy both.**

   7d. Change nameservers at the original registrar:
   - **Namecheap:** Domain List → Manage → **Nameservers** → select **Custom DNS** → paste Cloudflare NS1 and NS2 → save.
   - **Gandi:** Domain → **Nameservers** → **Change** → paste NS1 and NS2 → save.
   - **OVH:** Domain → **DNS servers** (or **Serveurs DNS**) → **Modify** → paste NS1 and NS2 → save.
   - (Cloudflare-as-registrar: already handled automatically.)

   7e. Wait for nameserver activation (minutes to 24h; Cloudflare sends an email when active). During this window, the site may be briefly unreachable — warn the user.

   7f. Once active, in Cloudflare **DNS** → **Records**:
   - Change A `@` → **Proxy status: Proxied** (orange cloud).
   - Change A `*` → **Proxy status: Proxied** (orange cloud).
   - Add A `coolify` → `<server-IP>` → **Proxy status: DNS only** (grey cloud, because the admin panel uses WebSockets that Cloudflare proxy can break).

   7g. In **SSL/TLS**:
   - Mode: **Full (strict)** (the server already has a valid Let's Encrypt cert).
   - **Always Use HTTPS:** ON.
   - **Minimum TLS Version:** 1.2.

   7h. In **Security** → **Bots**:
   - **Bot Fight Mode:** ON.
   - **AI Scrapers and Crawlers:** Block.

   7i. In **Security** → **Settings**:
   - **Security Level:** Medium.
   - **Challenge Passage:** 30 minutes.

   7j. Record the CDN state:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" record-cdn --provider cloudflare --enabled --bot-protection
   ```

   **If Cloudflare UI has changed** (Cloudflare redesigns periodically): adapt wording to what the user sees. Invariants: DNS with proxy orange cloud on apps + grey cloud on `coolify`; SSL Full (strict); Bot Fight Mode + AI Scrapers Block. If navigation diverges significantly, please submit a PR (see README → Deployment → Maintaining upstream compatibility).

---

### Phase 6 — Deploy Application

**Purpose:** Deploy the current project as a Coolify application.

1. **Determine subdomain**
   Invoke the deploy tool:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" subdomain \
     --project "$PWD" \
     --user "$(python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-get DEPLOY_USER | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"value\") or \"\")')" \
     --domain "$(python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-get DEPLOY_DOMAIN | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"value\"])')"
   ```
   The tool applies the full P1 rule (sanitization, training vs solo pattern, RFC 1035 length checks). If it returns `{"status": "error", ...}`, abort and report the error to the user. On success (`"status": "ok"`), it returns `{project_name, deploy_user, label, subdomain, url}`.

2. **Preflight checks** — delegate to the tool for deterministic, typed checks:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" preflight
   ```
   The tool detects the project type (`streamlit | python | node | static | custom`), derives the default port, and runs a structured list of checks: git state (repo, commits, remote, github.com hint, working tree), entry points per type (Streamlit/Python/Node), Streamlit reverse-proxy config (`enableCORS=false`, `enableXsrfProtection=false`), Node `start` script + Next.js build hint, static `index.html`, and `Dockerfile` `ARG SOURCE_COMMIT`. It returns JSON with `type`, `port`, `overall` (`ok | warnings | errors`), and the full `checks` list.

   Handle the result:
   - **`overall == "errors"`** → abort the skill. Display each failed check (`name`, `message`, `fix_hint`). Ask the user to resolve and re-run `/gse:deploy`.
   - **`overall == "warnings"`** → list the warnings (Inform tier). Present a Gate: *"Proceed despite these warnings?"* (Typical: uncommitted changes, missing Streamlit CORS config, remote not on github.com, missing `ARG SOURCE_COMMIT`.) On accept → continue. On decline → exit, suggest the fixes.
   - **`overall == "ok"`** → proceed silently.

   Capture the returned `type` and `port` — used in Step 3 (Dockerfile template selection) and Step 4 (`deploy-app --type --port`).

3. **Generate Dockerfile and .dockerignore** (if not present in project root)
   - Use the `type` returned by the preflight tool in Step 2 (do **not** re-detect — the tool is authoritative). If `config.yaml → deploy.app_type` is set to an explicit value (not `auto`), that value **overrides** the detected type.
   - Map the type to a template:
     - `streamlit` → `$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/templates/Dockerfile.streamlit`
     - `python`    → `$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/templates/Dockerfile.python`
     - `node`      → `$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/templates/Dockerfile.node`
     - `static`    → `$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/templates/Dockerfile.static`
   - Copy the selected template to `./Dockerfile` in the project, and copy `$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/templates/.dockerignore` to `./.dockerignore` if absent.
   - Show the generated Dockerfile to the user for approval (Inform tier), highlighting any CMD/ENTRYPOINT line the user may need to customize (notably for Python: FastAPI/Flask/script comment block; for Node: optional `RUN npm run build`).
   - Commit both files if the user approves.

4. **Deploy the application (Coolify project → environment → app → build → health check → state)**

   This step consolidates what were previously five sub-steps (create project, create app, trigger build, health check, update state). The tool does all of it in one call:

   **Concurrency note — run `deploy-app` calls sequentially, never in parallel.** When a user deploys multiple apps under the same `DEPLOY_USER` (e.g., a WEB and an API app for the same learner), each call invokes `ensure_project` on the shared Coolify project `gse-{DEPLOY_USER}`. The Coolify API exposes no atomic get-or-create for projects, so two concurrent `deploy-app` invocations can both observe "project does not exist" and both issue a `POST /projects` — producing two identically-named duplicate projects, both empty if subsequent app creation fails (e.g., the 422-private-repo branch documented below). Always instruct the user to wait for the first `deploy-app` to return (health check resolved, URL announced) before launching the next. If duplicates already exist, point the user to `docs/deploy/coolify-cli-cheatsheet.md` for the curl-based cleanup recipe.

   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" deploy-app \
     --name "<label-from-subdomain-step>" \
     --project-name "<pre-sanitization-dir-name>" \
     --deploy-user "<DEPLOY_USER or empty>" \
     --subdomain "<fqdn-from-subdomain-step>" \
     --github-repo "<user/repo>" \
     --branch "<current-branch>" \
     --type "<streamlit|python|node|static|custom>" \
     --port <N> \
     --health-timeout <config.yaml → deploy.health_check_timeout, default 120>
   ```

   **What the tool does:**
   - Ensures a Coolify project (`gse-{DEPLOY_USER}` in training, `gse` in solo) exists.
   - Ensures a `production` environment exists within that project.
   - Looks up `applications[]` in `.gse/deploy.json` by name. If a matching entry with `coolify.app_uuid` exists → triggers a redeploy (`POST /api/v1/deploy?uuid=...&force=true`). Otherwise, creates the app via `POST /api/v1/applications/public` — or `POST /api/v1/applications/private-github-app` when `COOLIFY_GITHUB_APP_UUID` is set in `.env` — resolving and sending `server_uuid` (from `.env SERVER_UUID`, else the sole server returned by `GET /api/v1/servers`, persisted back to `.env`), then triggers the initial deploy.
   - Polls the health endpoint (`/_stcore/health` for Streamlit, `/` for others) for `--health-timeout` seconds (the skill passes `config.yaml → deploy.health_check_timeout`, default 120 — the tool itself never reads config.yaml).
   - Records the application entry in `.gse/deploy.json → applications[]` with all fields (identification, source, runtime, Coolify UUIDs, resources, timestamps, status).

   **Return JSON:** `{"status": "healthy|unhealthy|timeout|error", "url": "...", "app_uuid": "...", "created": true|false, "http_code": N}`. On `error`, the result also carries `details`: Coolify's own reason (for a 422, the rejected fields and why) — show it to the user before any remedy. The tool sends a public repo as its full `https://github.com/<user/repo>` URL and the Dockerfile as `/Dockerfile`, the forms Coolify 4.7 validates.

   **Error branch — Coolify 422 on private GitHub repo.** If the tool returns `{"status": "error", "http_status": 422, ...}` and the user's repo is private (check via `gh repo view <user/repo> --json isPrivate` or ask the user), Coolify cannot clone via its public-repo endpoint. Do NOT suggest making the repo public — that is a privacy regression, not a fix. Instead, display this guidance verbatim (adapt tone to the detected `user_role`):
   > *"Your repo is private, so Coolify needs an authenticated source to clone it. In a training context, your trainer has typically pre-configured a Coolify 'GitHub App' source for this. Ask your trainer for two values: (a) the **GitHub App install link** (of the form `https://github.com/apps/<app-slug>/installations/new`) and (b) the **Coolify Source UUID** (a short alphanumeric string). Once you have both: (1) click the install link and install the App on your GitHub account, selecting only the repo you want to deploy; (2) run `deploy.py env-set COOLIFY_GITHUB_APP_UUID <uuid>`; (3) re-run this `deploy-app` command. Full procedure: `cat "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/references/private-repo-github-app-setup.md"` (section B)."*
   >
   > *Solo users (no trainer) can create their own Coolify GitHub App source via Coolify UI → Sources → GitHub App, then follow the same install + env-set flow. See the App-owner section (A) of `cat "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/references/private-repo-github-app-setup.md"` — in solo mode you are your own App owner.*

   **Note — since v0.64.0, `deploy.py` auto-routes to the Coolify `/applications/private-github-app` endpoint when `COOLIFY_GITHUB_APP_UUID` is set.** After `env-set`, re-running `deploy-app` completes end-to-end (the tool also resolves and sends the required `server_uuid`). If the retry still fails, verify the GitHub App is actually installed on the user's GitHub account with access to the repo (see `cat "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/references/private-repo-github-app-setup.md"`, section B troubleshooting).

5. **Report**
   - If `status == "healthy"`: *"Your project is live at: https://{subdomain}"*
   - If `status` is `unhealthy` or `timeout`: report failure and offer to read the app's runtime logs right away (`/gse:deploy --logs` — see the --logs Option section below); in solo mode, the Coolify dashboard at `{COOLIFY_URL}` also shows the build log.
   - If `status == "error"`: show the Coolify error message and suggest corrective action.
   - Solo mode: append *"Server: {IP} ({server-type}), monthly cost: ~{price shown at the Phase 2 Gate} EUR"*.
   - Training mode: append *"Deployed on shared training server."*

6. **Verify deployed version matches repo HEAD (Inform-tier, pedagogical)**

   Healthy ≠ correct version. A successful Coolify deploy can still serve a stale build (caching, rollback after failed redeploy, partial deploy). Compare what is **live** against what the local repo declared:

   1. Read the local source of truth: `git rev-parse --short HEAD` and, if a release tag was emitted by `/gse:deliver`, the latest `v*` tag on `main`.
   2. Probe the live app for its version. Try in order:
      - `curl -fsS https://{subdomain}/version` (if the project exposes a `/version` endpoint)
      - `curl -fsS https://{subdomain}/_stcore/health` and inspect any embedded version string
      - Fetch the HTML root and grep for a version marker (footer, meta tag, JS bundle hash)
   3. Display the result:

      ```
      DEPLOYED VERSION CHECK
        Repo HEAD: {short_sha} (tag: {v*-or-untagged})
        Live app:  {detected_string-or-"unknown"}
        Match:     {OK | MISMATCH | UNKNOWN}
      ```

   4. Interpretation guidance:
      - **OK** → deployment confirmed end-to-end. Proceed.
      - **MISMATCH** → suggest one of: (a) `/gse:deploy --redeploy` to force a fresh build, (b) inspect Coolify deployment logs for a silent rollback (e.g., healthcheck failure → previous container restored — observed in real sessions), (c) hard-refresh in browser (cache).
      - **UNKNOWN** → no version surface in the app. Suggest adding a minimal `/version` endpoint or a footer string as a future improvement. Do not block — many projects do not expose this, and the check then carries no signal.

   This step is **purely Inform** — it does not modify state, does not call other activities, and does not block on a MISMATCH. Rationale: in observed sessions, users assumed a healthy deploy meant the new code was live, only to discover at runtime that the previous version was still being served. A 30-second cross-check at the end of `/gse:deploy` closes that gap without adding methodological weight.

---

### --status Option

When invoked with `--status`:

1. Invoke:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" state --human
   ```
   This prints the full state (phases, server, Coolify, domain, applications table).

2. For each application listed, run a live health check:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" app-status <app-name>
   ```
   and display the current status to the user.

3. If no `.gse/deploy.json` exists (the tool will return an empty state): *"No deployment found. Run `/gse:deploy` to deploy."*

### --logs Option

> **Structure note (Meta-2).** Like `--status`, `--logs` is a disjoint read-only mode: it runs instead of the Step -1 → Phase 6 lifecycle, changes no state, and needs no Gate.

**What logs are (explain this to beginners the first time).** While your app runs on the server, everything it prints — startup messages, `print()`/`console.log` output, error messages and stack traces — is recorded by the server. These records are the app's *runtime logs*. When the deployed app does not start, shows an error page, or fails the health check, the logs almost always contain the actual error (a missing module, a wrong port, a crash at startup). Reading them is the first debugging step — and in training mode it is the only way to see them, since learners have no Coolify dashboard account.

When to propose it: after Phase 6 reports `unhealthy` or `timeout`, when the user says the live app "does not work", or when `--status` shows an unhealthy app.

When invoked with `--logs` (optionally `--lines N`, default 100):

1. Invoke:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" logs --lines <N>
   ```
   The tool reads `COOLIFY_URL` / `COOLIFY_API_TOKEN` / `DEPLOY_USER` itself (never read `.env` here) and resolves the app of **this project for this user**: first from `.gse/deploy.json → applications[]` (entries owned by the current `DEPLOY_USER`, or without user in solo mode), else by looking only inside the user's own Coolify project (`gse-{DEPLOY_USER}` in training, `gse` in solo). It never reads another learner's app. If several of the user's apps are recorded, it asks for `--name <app-name>`. It prints the last N lines on stdout; the API token is never printed (it is even masked if it appears in the log text).
2. Display the log lines to the user, then help interpret them (P9 Adaptive Communication): point at the first error or stack trace, explain it in plain words, and propose a fix (e.g., wrong port in the Dockerfile, missing dependency in `requirements.txt` / `package.json`, missing environment variable). After a fix is committed and pushed, propose `/gse:deploy --redeploy`.
3. On failure the tool exits non-zero with a one-line message on stderr — relay it:
   - `not_deployed` / `not_found` → the app does not exist (yet or anymore): propose `/gse:deploy`.
   - `not_running` → no container is running (still building, build failed, or crashed): wait a minute and retry; if it persists, `/gse:deploy --redeploy` then `--logs` right after. A build failure produces no runtime logs — in solo mode, the build log is in the Coolify dashboard; in training mode, ask the instructor.
   - `error` with 401 (token rejected) or 403 (token lacks Coolify's `read:sensitive` permission) → training: ask the instructor for a valid token; solo: create a new token in Coolify (Keys & Tokens) with `root` or `read:sensitive` (Phase 4 Step 4 — Guide browser setup) and store it with `deploy.py env-set COOLIFY_API_TOKEN --stdin` (hidden prompt, in the user's own terminal).

### --destroy Option

When invoked with `--destroy`:

1. **Dry-run first** — always surface the impact before the Gates:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" destroy --dry-run
   ```
   Display the result to the user:
   > **Impact of /gse:deploy --destroy:**
   > - Applications to delete: {count} ({comma-separated list})
   > - Coolify projects to delete: {count} ({comma-separated list})
   > - Hetzner server to delete: {server-name}
   > - Firewall to delete: {firewall-name}
   > - Estimated cost savings: {cost-hint}

2. **Gate 1** — first confirmation (generic):
   > *"This is a destructive operation that cannot be undone. It will stop billing for the Hetzner server but will NOT touch DNS records at your registrar (you may want to remove them manually afterwards). Proceed?"*

   Wait for explicit user confirmation (yes/no). If no: exit without change.

3. **Gate 2** — retype the server name:
   > *"To confirm, type the server name exactly: {server-name}"*

   Wait for the user to type the literal name. If mismatch: abort with *"Name mismatch. Destroy cancelled."*

4. **Execute destroy** with the typed name as confirmation:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" destroy --confirm <typed-name>
   ```

5. **Handle the result:**
   - If `status == "ok"`: all deletions succeeded. State file is cleared. Continue to step 6.
   - If `status == "partial"`: some deletions failed (see `errors` array). **State is preserved** for retry — the user can re-run `/gse:deploy --destroy` later once the issue is resolved. Surface the `errors` list verbatim so the user can diagnose (e.g., hcloud token expired, network issue, Coolify down). **Skip step 6** (keep `.env` intact for retry).

6. **Clean up `.env` variables** (only on `status == "ok"`):
   ```
   for key in SERVER_IP SERVER_UUID SSH_USER SSH_KEY COOLIFY_URL COOLIFY_API_TOKEN COOLIFY_GITHUB_APP_UUID; do
     python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" env-delete "$key"
   done
   ```

7. **Post-destroy report + warnings** (only on `status == "ok"`):
   > Deployment configuration cleared. {cost_savings}.
   >
   > Remaining external resources to consider:
   > - **DNS records** at your registrar (`A @` and `A *`) still point to a dead IP — remove or repurpose them.
   > - **Cloudflare CDN** (if you set it up): consider removing the zone or reverting nameservers to the registrar's defaults.
   > - **Let's Encrypt certificates** were automatically revoked when Coolify shut down — no action needed.
   > - **Hetzner SSH key** (`gse-deploy`) is still registered in your Hetzner project if you want to reuse it.

### --redeploy Option

When invoked with `--redeploy`:

1. Verify that `deploy.json → phases_completed.dns` is set (infrastructure is ready). If not, abort with *"Infrastructure not ready. Run /gse:deploy first to complete Phases 1-5."*
2. Skip directly to Phase 6 (subdomain computation + `deploy-app` + report). The `deploy-app` subcommand auto-detects the existing application entry by name and triggers a forced rebuild via `POST /api/v1/deploy?uuid=...&force=true`.
3. Return the same JSON contract as a normal deploy: `{status, url, app_uuid, created: false, http_code}`.

### --registrar Option

When invoked with `--registrar <name>` (where `<name>` is `namecheap`, `gandi`, `ovh`, or `cloudflare`):

1. Read `.gse/deploy.json → server.ipv4`. If missing: *"No server IP recorded. Run /gse:deploy to provision first."*
2. Display **only** the corresponding registrar subsection from Phase 5 Step 1 (1a/1b/1c/1d) with the server IP substituted.
3. Remind the user they can run `/gse:deploy` (no args) afterwards to continue from the detected phase.

Useful when the user skipped the full flow, already has infrastructure, and just needs the registrar-specific DNS instructions.

### --training-init Option (Instructor-only)

When invoked with `--training-init`:

1. Verify `phases_completed.dns` is set (the instructor has completed Phases 1-5). If not, abort with *"Training-init requires completed infrastructure. Finish /gse:deploy first."*
2. Invoke:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" training-init [--output .env.training]
   ```
3. The tool generates `.env.training` containing `COOLIFY_URL`, `COOLIFY_API_TOKEN`, `DEPLOY_DOMAIN`, and a `DEPLOY_USER=learnerXX` placeholder — plus `SERVER_UUID` and `COOLIFY_GITHUB_APP_UUID` when present in the instructor's `.env` (so the single handout also covers recent Coolify versions and learners with private repos; remind the instructor to set both before generating if the cohort needs them). It **excludes** `HETZNER_API_TOKEN`, `SERVER_IP`, SSH keys. A security warning is embedded as a comment.
4. **Mandatory token step — before distributing anything:** instruct the instructor to generate a **dedicated Coolify API token for the course** (Coolify UI → Keys & Tokens) and re-run `--training-init` with it in `.env` if the current token is their personal one. The course token must carry `root`, or at least `read`, `write`, `deploy` **and `read:sensitive`** — without `read:sensitive`, every learner's `/gse:deploy --logs` fails with 403. Store it with `deploy.py env-set COOLIFY_API_TOKEN --stdin`. State the risk explicitly: *"The token embedded in `.env.training` gives every learner WRITE access to ALL applications on the shared Coolify server — any learner can modify or delete other learners' apps (or yours). Use a course-dedicated token, and revoke it in the Coolify UI as soon as the course ends (`--training-reap` cleans the apps, not the token)."*
5. Display the output path to the instructor and remind them:
   *"Distribute .env.training to your learners. They copy it to their project as .env and set DEPLOY_USER."*
   *"Mid-course incident recipe: if a learner's app is damaged or deleted (the shared token allows it), the learner just re-runs `/gse:deploy` — the app is recreated from their GitHub repo in ~5 minutes. No instructor intervention needed."*
   *"Pre-course tip: have learners install GSE-One with a pinned version — `GSE_VERSION=vX.Y.Z curl … | sh` — so the whole cohort runs the same version AND you avoid the unauthenticated GitHub API rate limit (~60 requests/hour/IP) when 20 learners install behind one classroom NAT (see README → Troubleshooting → GitHub API rate limit)."*

### --training-reap Option (Instructor-only)

When invoked with `--training-reap`:

1. Prompt for scope (Gate):
   *"Reap which? (1) a single learner, (2) all gse-* projects, (3) cancel"*
2. If option 1: ask for the learner name, then run a dry-run first:
   ```
   python3 "$([ -s .gse/registry ] && cat .gse/registry || cat ~/.gse-one)/tools/deploy.py" training-reap --user <name> --dry-run
   ```
   Display the list of projects that would be deleted. If the instructor confirms (Gate), re-invoke with `--confirm <name>` to actually delete.
3. If option 2: run `training-reap --all --dry-run`, display the list, confirm (Gate), then `--all --confirm all`.
4. The tool deletes the selected Coolify projects via API and syncs `.gse/deploy.json → applications[]` by removing entries whose `deploy_user` matches.
5. Report the number of projects deleted and any errors (e.g., partial failures).

The `gse` solo project (instructor's own apps) is **never** touched by `--training-reap`.

### --help Option

When invoked with `--help`:

Display a role-first narrative, then the Options table:

> **Who are you?**
>
> - **Solo user** → Run `/gse:deploy` (no args). First run walks you through 6 phases (setup, provision, secure, Coolify, DNS, deploy). Expect ~1h first time, ~11 EUR/month ongoing (default CAX21 server).
>
> - **Instructor** → Run `/gse:deploy` once to set up a shared server. Then `/gse:deploy --training-init` to generate `.env.training` for distribution to learners. At course end, `/gse:deploy --training-reap --all`.
>
> - **Learner** → Copy the `.env.training` file your instructor sent into your project as `.env`, set `DEPLOY_USER=<your-id>`, then run `/gse:deploy`. Takes ~5 minutes.
>
> All commands support `--status` (inspect state), `--logs` (read your app's runtime logs), `--redeploy` (force rebuild), `--destroy` (tear down, double Gate), `--silent` (skip orientation for scripting).

Then display the full Options table.

If `config.yaml → deploy.app_type` is set to a specific value (not `auto`), also mention which Dockerfile template would be used (e.g., *"Current app_type: `python` → will use Dockerfile.python"*).
