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
3. `.env` — credentials and configuration (if exists)
4. `.gse/profile.yaml` — user profile (apply P9 Adaptive Communication to all output)
5. `$(cat ~/.gse-one)/agents/deploy-operator.md` — adopt this role for the entire activity
6. `$(cat ~/.gse-one)/references/hetzner-infrastructure.md` — pricing, sizing, Coolify API (consulted on demand)
7. `$(cat ~/.gse-one)/references/ssh-operations.md` — SSH patterns and credential resolution (consulted on demand)

## Workflow

> **Workflow structure note.** `/gse:deploy` uses a two-level hierarchy reflecting its deployment lifecycle:
> - **Step -1 and Step 0** (Orientation, Situation Detection) — pre-flight checks before committing to a lifecycle.
> - **Phase 1 through Phase 6** (Setup → Provision → Secure → Install Coolify → Configure DNS → Deploy Application) — the main deployment lifecycle. Each Phase corresponds to an idempotent milestone tracked in `.gse/deploy.json` under `phases_completed.<phase_name>`; a completed Phase is automatically skipped on re-run.
> - **Step N inside a Phase** — sub-steps within a Phase (e.g., "Step 3 — Dockerfile template selection" inside Phase 6). This internal numbering resets for each Phase.
>
> This two-level hierarchy is specific to `/gse:deploy` — other GSE-One activities use a flat Step sequence. The distinction reflects the idempotent-milestone nature of deployment.

### Step -1 — Orientation (first-time users only)

**Skip this step if ANY of the following is true:**
- The `--silent` flag was passed
- `.gse/deploy.json` already exists
- Any of these env vars are set in `.env`: `HETZNER_API_TOKEN`, `SERVER_IP`, `COOLIFY_URL`, `COOLIFY_API_TOKEN`, `DEPLOY_DOMAIN`, `DEPLOY_USER`

Otherwise (first-time user), display:

> Welcome to `/gse:deploy`. This command provisions infrastructure and deploys your project. First, let me understand your situation:
>
>   (1) **Solo** — Deploy my own project to my own Hetzner server. (~1h first time, ~8.49 EUR/month ongoing. You'll need a Hetzner account and optionally a domain.)
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
python3 "$(cat ~/.gse-one)/tools/deploy.py" record-role solo
```
Say: *"You'll go through 6 phases: installing the hcloud CLI, creating a Hetzner server, hardening it, installing Coolify, configuring DNS/SSL, and deploying your project. I'll guide you at each step. Type 'ready' to begin."*
Wait for confirmation → proceed to Step 0.

**(2) Instructor** — Persist role and brief:
```
python3 "$(cat ~/.gse-one)/tools/deploy.py" record-role instructor
```
Say: *"I'll walk you through the full 6-phase setup (same as Solo mode), then help you generate a `.env.training` file with `--training-init` to distribute to your learners. At the end of the course, run `/gse:deploy --training-reap --all` to clean up all learner apps. Ready to start the server setup?"*
Wait for confirmation → proceed to Step 0.

**(3) Learner** — Two precondition checks:
1. Ask: *"Have you copied the `.env.training` file your instructor sent you into your project directory as `.env`? (y/n)"*
   - If no: *"Please do that first (`cp .env.training .env` in your project). Then re-run `/gse:deploy`."* → Exit.
2. Ask: *"Have you set `DEPLOY_USER` to your learner ID in the `.env` file? (y/n)"*
   - If no: *"Open `.env` in your editor, set `DEPLOY_USER=<your-learner-id>`, save, and re-run `/gse:deploy`."* → Exit.
3. Persist role:
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-role learner
   ```
4. Say: *"I'll detect your instructor's shared server from the training config and deploy your project at `{project-name}-{DEPLOY_USER}.{DEPLOY_DOMAIN}`. Expected duration: ~5 minutes."*
5. Proceed to Step 0 (will detect app-only mode → Phase 6).

**(4) Skip** — Meta-action (not a role value): no `record-role` call; no `user_role` persisted in `deploy.json`. Proceed directly to Step 0. The 3 role values stored in `user_role` are `solo` / `instructor` / `learner` only — see design §5.18 State schema for the enum.

---

### Step 0 — Situation Detection

Invoke the deploy tool:

```
python3 "$(cat ~/.gse-one)/tools/deploy.py" detect
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

The detection logic (which variables map to which starting phase) is documented in `gse-one-implementation-design.md` §5.18 and authoritatively applied by the `detect` subcommand. Trust its output — do not re-derive the mapping from the table above.

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
   - Ask the user to paste the token
   - **Never display the token back in chat**

3. **Domain name**
   - Ask: *"What domain will you use for deployment? (e.g., my-project.com)"*

4. **Save credentials**
   - Persist the token and domain via the deploy tool:
     ```
     python3 "$(cat ~/.gse-one)/tools/deploy.py" env-set HETZNER_API_TOKEN <token>
     python3 "$(cat ~/.gse-one)/tools/deploy.py" env-set DEPLOY_DOMAIN <domain>
     ```
   - Check `.gitignore` contains `.env` — if not, add it and warn the user
   - If no `.gitignore` exists: Gate decision to create one

5. **Verify hcloud access**
   - Run `hcloud server list` to confirm the token works
   - If it fails: ask user to verify the token

6. **Persist completion**
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" init-state
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-phase setup
   ```

---

### Phase 2 — Provision (skip if `SERVER_IP` in `.env` or `deploy.json` has `phases_completed.provision`)

**Purpose:** Create a Hetzner server with firewall.

1. **Read configuration**
   - Server type: `config.yaml → deploy.server_type` (default: `cax21`)
   - Datacenter: `config.yaml → deploy.datacenter` (default: `fsn1`)
   - Server name: `gse-<project-name>` (sanitized, lowercase, hyphens only)

2. **Check for existing server**
   - `hcloud server list -o columns=name,ipv4`
   - If a server with this name exists: skip provision, record IP

3. **Gate decision: server creation**
   - Display cost and configuration:
     *"Creating a Hetzner server:*
     *- Type: CAX21 (4 vCPU ARM, 8 GB RAM, 80 GB SSD)*
     *- Location: Falkenstein (fsn1)*
     *- Monthly cost: ~8.49 EUR*
     *Proceed?"*
   - Wait for explicit user confirmation

4. **Generate SSH key** (if `~/.ssh/gse-deploy` does not exist)
   - `ssh-keygen -t ed25519 -f ~/.ssh/gse-deploy -N ""`
   - Upload: `hcloud ssh-key create --name gse-deploy --public-key-from-file ~/.ssh/gse-deploy.pub`

5. **Create server**
   - `hcloud server create --name <name> --type <type> --location <datacenter> --image ubuntu-24.04 --ssh-key gse-deploy`
   - Record IP address from output

6. **Create firewall**
   - `hcloud firewall create --name gse-fw-<name>`
   - Add rules: allow TCP 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (Coolify setup, temporary)
   - Apply to server: `hcloud firewall apply-to-resource gse-fw-<name> --type server --server <name>`

7. **Verify SSH access**
   - `ssh -i ~/.ssh/gse-deploy -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 root@<IP> "echo ok"`
   - Retry up to 3 times with 10s wait between attempts

8. **Persist completion**
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-server \
     --name <name> --ipv4 <IP> --id <id> --type <type> --datacenter <dc>
   python3 "$(cat ~/.gse-one)/tools/deploy.py" env-set SERVER_IP <IP>
   python3 "$(cat ~/.gse-one)/tools/deploy.py" env-set SSH_USER root
   python3 "$(cat ~/.gse-one)/tools/deploy.py" env-set SSH_KEY ~/.ssh/gse-deploy
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-phase provision
   ```

---

### Phase 3 — Secure (skip if `deploy.json` has `phases_completed.secure`)

**Purpose:** Harden the server — non-root user, SSH hardening, firewall, intrusion detection.

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
   - Edit `/etc/ssh/sshd_config`:
     - `PermitRootLogin no`
     - `PasswordAuthentication no`
     - `PubkeyAuthentication yes`
   - `ssh deploy@<IP> "sudo systemctl restart sshd"`

4. **Install UFW firewall**
   - ```
     ssh deploy@<IP> "sudo apt-get update -qq && sudo apt-get install -y -qq ufw && \
       sudo ufw default deny incoming && sudo ufw default allow outgoing && \
       sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && \
       sudo ufw allow 443/tcp && sudo ufw allow 8000/tcp && \
       sudo ufw --force enable"
     ```

5. **Install ufw-docker** (prevents Docker from bypassing UFW rules)
   - By default, Docker publishes containers to `0.0.0.0` and inserts iptables rules that bypass UFW. Without `ufw-docker`, a container exposing port `5432` to the host would be reachable from the internet even if UFW denies port `5432`. This is a real production risk.
   - ```
     ssh deploy@<IP> "sudo wget -O /usr/local/bin/ufw-docker \
       https://github.com/chaifeng/ufw-docker/raw/master/ufw-docker && \
       sudo chmod +x /usr/local/bin/ufw-docker && \
       sudo ufw-docker install && \
       sudo systemctl restart ufw"
     ```
   - Verify: `ssh deploy@<IP> "sudo ufw-docker status"` (should report rules are active).

6. **Install fail2ban**
   - ```
     ssh deploy@<IP> "sudo apt-get install -y -qq fail2ban && \
       sudo systemctl enable fail2ban && sudo systemctl start fail2ban"
     ```

7. **Automatic security updates**
   - ```
     ssh deploy@<IP> "sudo apt-get install -y -qq unattended-upgrades && \
       sudo dpkg-reconfigure -plow unattended-upgrades"
     ```

8. **Persist completion**
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" env-set SSH_USER deploy
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-phase secure
   ```

---

### Phase 4 — Install Coolify (skip if `COOLIFY_URL` in `.env` or `deploy.json` has `phases_completed.coolify`)

**Purpose:** Install Coolify v4 (self-hosted PaaS with Traefik reverse proxy).

1. **Install Coolify**
   - `ssh deploy@<IP> "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash"`

2. **Wait for readiness**
   - Poll `http://<IP>:8000` every 15 seconds, timeout 5 minutes
   - Show progress: *"Waiting for Coolify to start..."*

3. **Guide browser setup (detailed)**
   Walk the user through the Coolify onboarding. Tell them verbatim:

   > Coolify is ready. Open `http://<IP>:8000` in your browser.
   >
   > **3a. Create your admin account:**
   > - Fill in: *Email*, *Name*, *Password* (min 8 chars), *Confirm password*
   > - Click **Register**. You are now logged in.
   >
   > **3b. Initial setup wizard:**
   > - Coolify displays a *"Welcome"* screen. Click **Let's go!** or **Skip** through optional settings (root user email, instance name — you can change these later in Settings).
   >
   > **3c. Create an API token:**
   > - In the left sidebar, click your profile icon (bottom left) → **Keys & Tokens** → **API Tokens** tab.
   > - Click **Create New Token**.
   > - Name it: `gse-one`
   > - Permissions: check **Read**, **Write**, and **Deploy** (or the "Full Access" preset if available).
   > - Click **Continue**. The token is displayed **only once** — copy it now.
   >
   > **3d. Paste the token here.**

   Then persist:
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" env-set COOLIFY_URL http://<IP>:8000
   python3 "$(cat ~/.gse-one)/tools/deploy.py" env-set COOLIFY_API_TOKEN <token>
   ```

   **If the UI has changed** (Coolify iterates fast), adapt the step numbering to what the user describes. The invariants are: create account → find "API tokens" or equivalent → create token with full-access permissions → copy once. If a step path differs significantly, please consider submitting a PR to update this section (see README → Deployment → Maintaining upstream compatibility).

4. **Verify containers**
   - `ssh deploy@<IP> "sudo docker ps --format 'table {{.Names}}\t{{.Status}}'"` 
   - Check: coolify, traefik, postgres containers running

5. **Persist completion**
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-coolify --url http://<IP>:8000
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-phase coolify
   ```

---

### Phase 5 — Configure DNS (skip if `deploy.json` has `phases_completed.dns`)

**Purpose:** Point the domain to the server and enable SSL.

1. **Guide DNS configuration**
   - Tell the user (verbatim):
     > Add these DNS records at your domain registrar:
     > | Type | Name | Value        | TTL |
     > |------|------|--------------|-----|
     > | A    | `@`  | `<server-IP>` | 300 |
     > | A    | `*`  | `<server-IP>` | 300 |
     >
     > The wildcard `*` enables all subdomains (`project-a.domain.com`, `project-b.domain.com`, ...) to point to this server automatically — essential for the multi-app pattern.
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
   python3 "$(cat ~/.gse-one)/tools/deploy.py" wait-dns \
     --domain <domain> --expected-ip <server-IP> --timeout 600
   ```
   The tool polls `dig` (system resolver + `@8.8.8.8` fallback every 15s). On `resolved`, proceed. On `timeout`, it returns a hint — display it to the user and exit the skill without marking the phase complete (so the user can re-run `/gse:deploy` once propagation completes).

3. **Configure Coolify dashboard domain**
   Use the Coolify API to set the dashboard FQDN to `coolify.<domain>`:
   ```
   curl -X PATCH "http://<IP>:8000/api/v1/settings/general" \
     -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"instance_fqdn":"https://coolify.<domain>"}'
   ```
   Then update the env:
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" env-set COOLIFY_URL https://coolify.<domain>
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
   - `ssh deploy@<IP> "sudo ufw delete allow 8000/tcp"`
   - `hcloud firewall delete-rule gse-fw-<name> --direction in --protocol tcp --port 8000`

6. **Persist domain completion**
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-domain --base <domain> --registrar <namecheap|gandi|ovh|cloudflare|manual>
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-phase dns
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
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-cdn --provider none
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
   python3 "$(cat ~/.gse-one)/tools/deploy.py" record-cdn --provider cloudflare --enabled --bot-protection
   ```

   **If Cloudflare UI has changed** (Cloudflare redesigns periodically): adapt wording to what the user sees. Invariants: DNS with proxy orange cloud on apps + grey cloud on `coolify`; SSL Full (strict); Bot Fight Mode + AI Scrapers Block. If navigation diverges significantly, please submit a PR (see README → Deployment → Maintaining upstream compatibility).

---

### Phase 6 — Deploy Application

**Purpose:** Deploy the current project as a Coolify application.

1. **Determine subdomain**
   Invoke the deploy tool:
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" subdomain \
     --project "$PWD" \
     --user "$(python3 "$(cat ~/.gse-one)/tools/deploy.py" env-get DEPLOY_USER | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"value\") or \"\")')" \
     --domain "$(python3 "$(cat ~/.gse-one)/tools/deploy.py" env-get DEPLOY_DOMAIN | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"value\"])')"
   ```
   The tool applies the full P1 rule (sanitization, training vs solo pattern, RFC 1035 length checks). If it returns `{"ok": false, ...}`, abort and report the error to the user. On success, it returns `{project_name, deploy_user, label, subdomain, url}`.

2. **Preflight checks** — delegate to the tool for deterministic, typed checks:
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" preflight
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
     - `streamlit` → `$(cat ~/.gse-one)/templates/Dockerfile.streamlit`
     - `python`    → `$(cat ~/.gse-one)/templates/Dockerfile.python`
     - `node`      → `$(cat ~/.gse-one)/templates/Dockerfile.node`
     - `static`    → `$(cat ~/.gse-one)/templates/Dockerfile.static`
   - Copy the selected template to `./Dockerfile` in the project, and copy `$(cat ~/.gse-one)/templates/.dockerignore` to `./.dockerignore` if absent.
   - Show the generated Dockerfile to the user for approval (Inform tier), highlighting any CMD/ENTRYPOINT line the user may need to customize (notably for Python: FastAPI/Flask/script comment block; for Node: optional `RUN npm run build`).
   - Commit both files if the user approves.

4. **Deploy the application (Coolify project → environment → app → build → health check → state)**

   This step consolidates what were previously five sub-steps (create project, create app, trigger build, health check, update state). The tool does all of it in one call:

   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" deploy-app \
     --name "<label-from-subdomain-step>" \
     --project-name "<pre-sanitization-dir-name>" \
     --deploy-user "<DEPLOY_USER or empty>" \
     --subdomain "<fqdn-from-subdomain-step>" \
     --github-repo "<user/repo>" \
     --branch "<current-branch>" \
     --type "<streamlit|python|node|static|custom>" \
     --port <N>
   ```

   **What the tool does:**
   - Ensures a Coolify project (`gse-{DEPLOY_USER}` in training, `gse` in solo) exists.
   - Ensures a `production` environment exists within that project.
   - Looks up `applications[]` in `.gse/deploy.json` by name. If a matching entry with `coolify.app_uuid` exists → triggers a redeploy (`GET /api/v1/deploy?uuid=...&force=true`). Otherwise, creates the app via `POST /api/v1/applications/public` and triggers the initial deploy.
   - Polls the health endpoint (`/_stcore/health` for Streamlit, `/` for others) for `config.yaml → deploy.health_check_timeout` seconds (default 120).
   - Records the application entry in `.gse/deploy.json → applications[]` with all fields (identification, source, runtime, Coolify UUIDs, resources, timestamps, status).

   **Return JSON:** `{"status": "healthy|unhealthy|timeout|error", "url": "...", "app_uuid": "...", "created": true|false, "http_code": N}`.

5. **Report**
   - If `status == "healthy"`: *"Your project is live at: https://{subdomain}"*
   - If `status` is `unhealthy` or `timeout`: report failure, suggest checking the Coolify dashboard at `{COOLIFY_URL}`.
   - If `status == "error"`: show the Coolify error message and suggest corrective action.
   - Solo mode: append *"Server: {IP} ({server-type}), monthly cost: ~8.49 EUR"*.
   - Training mode: append *"Deployed on shared training server."*

---

### --status Option

When invoked with `--status`:

1. Invoke:
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" state --human
   ```
   This prints the full state (phases, server, Coolify, domain, applications table).

2. For each application listed, run a live health check:
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" app-status <app-name>
   ```
   and display the current status to the user.

3. If no `.gse/deploy.json` exists (the tool will return an empty state): *"No deployment found. Run `/gse:deploy` to deploy."*

### --destroy Option

When invoked with `--destroy`:

1. **Dry-run first** — always surface the impact before the Gates:
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" destroy --dry-run
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
   python3 "$(cat ~/.gse-one)/tools/deploy.py" destroy --confirm <typed-name>
   ```

5. **Handle the result:**
   - If `status == "ok"`: all deletions succeeded. State file is cleared. Continue to step 6.
   - If `status == "partial"`: some deletions failed (see `errors` array). **State is preserved** for retry — the user can re-run `/gse:deploy --destroy` later once the issue is resolved. Surface the `errors` list verbatim so the user can diagnose (e.g., hcloud token expired, network issue, Coolify down). **Skip step 6** (keep `.env` intact for retry).

6. **Clean up `.env` variables** (only on `status == "ok"`):
   ```
   for key in SERVER_IP SSH_USER SSH_KEY COOLIFY_URL COOLIFY_API_TOKEN; do
     python3 "$(cat ~/.gse-one)/tools/deploy.py" env-delete "$key"
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
2. Skip directly to Phase 6 (subdomain computation + `deploy-app` + report). The `deploy-app` subcommand auto-detects the existing application entry by name and triggers a forced rebuild via `GET /api/v1/deploy?uuid=...&force=true`.
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
   python3 "$(cat ~/.gse-one)/tools/deploy.py" training-init [--output .env.training]
   ```
3. The tool generates `.env.training` containing `COOLIFY_URL`, `COOLIFY_API_TOKEN`, `DEPLOY_DOMAIN`, and a `DEPLOY_USER=learnerXX` placeholder. It **excludes** `HETZNER_API_TOKEN`, `SERVER_IP`, SSH keys. A security warning is embedded as a comment.
4. Display the output path to the instructor and remind them:
   *"Distribute .env.training to your learners. They copy it to their project as .env and set DEPLOY_USER. Consider generating a dedicated Coolify token for the course; revoke it when the course ends."*

### --training-reap Option (Instructor-only)

When invoked with `--training-reap`:

1. Prompt for scope (Gate):
   *"Reap which? (1) a single learner, (2) all gse-* projects, (3) cancel"*
2. If option 1: ask for the learner name, then run a dry-run first:
   ```
   python3 "$(cat ~/.gse-one)/tools/deploy.py" training-reap --user <name> --dry-run
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
> - **Solo user** → Run `/gse:deploy` (no args). First run walks you through 6 phases (setup, provision, secure, Coolify, DNS, deploy). Expect ~1h first time, ~8.49 EUR/month ongoing.
>
> - **Instructor** → Run `/gse:deploy` once to set up a shared server. Then `/gse:deploy --training-init` to generate `.env.training` for distribution to learners. At course end, `/gse:deploy --training-reap --all`.
>
> - **Learner** → Copy the `.env.training` file your instructor sent into your project as `.env`, set `DEPLOY_USER=<your-id>`, then run `/gse:deploy`. Takes ~5 minutes.
>
> All commands support `--status` (inspect state), `--redeploy` (force rebuild), `--destroy` (tear down, double Gate), `--silent` (skip orientation for scripting).

Then display the full Options table.

If `config.yaml → deploy.app_type` is set to a specific value (not `auto`), also mention which Dockerfile template would be used (e.g., *"Current app_type: `python` → will use Dockerfile.python"*).
