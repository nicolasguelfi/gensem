# Hetzner Infrastructure Reference

This reference provides Hetzner Cloud data consulted by `/gse:deploy` and any
future deployment-related skill. Read this before making sizing decisions or
advising users on server configuration.

## 1. Hetzner Cloud Server Types (EUR/month excl. VAT)

> Last verified: 2026-04-22

### CAX Series — ARM (Ampere Altra) — Best value

| Type   | vCPU | RAM    | SSD     | Traffic | Price/mo | Indicative capacity |
|--------|------|--------|---------|---------|----------|---------------------|
| CAX11  | 2    | 4 GB   | 40 GB   | 20 TB   | ~4.49 €  | 3–5 small apps      |
| CAX21  | 4    | 8 GB   | 80 GB   | 20 TB   | ~8.49 €  | 8–15 small apps     |
| CAX31  | 8    | 16 GB  | 160 GB  | 20 TB   | ~16.49 € | 15–30 small apps    |
| CAX41  | 16   | 32 GB  | 320 GB  | 20 TB   | ~31.99 € | 30–60 small apps    |

### CX Series — x86 Shared (Intel/AMD)

| Type  | vCPU | RAM    | SSD     | Price/mo  |
|-------|------|--------|---------|-----------|
| CX22  | 2    | 4 GB   | 40 GB   | ~5.09 €   |
| CX32  | 4    | 8 GB   | 80 GB   | ~9.09 €   |
| CX42  | 8    | 16 GB  | 160 GB  | ~21.49 €  |
| CX52  | 16   | 32 GB  | 320 GB  | ~42.49 €  |

### CCX Series — Dedicated vCPU (guaranteed performance)

| Type   | vCPU (ded) | RAM     | SSD     | Price/mo   |
|--------|-----------|---------|---------|------------|
| CCX13  | 2         | 8 GB    | 80 GB   | ~12.49 €   |
| CCX23  | 4         | 16 GB   | 160 GB  | ~24.49 €   |
| CCX33  | 8         | 32 GB   | 240 GB  | ~48.49 €   |
| CCX43  | 16        | 64 GB   | 360 GB  | ~96.49 €   |
| CCX53  | 32        | 128 GB  | 600 GB  | ~191.99 €  |

### Recommendation by use case

| Use case                 | Server  | Why                                  |
|--------------------------|---------|--------------------------------------|
| Personal, testing        | CAX11   | Cheapest, enough for 3-5 light apps  |
| Small group, training    | CAX31   | Best value for 15-30 projects        |
| Class with 30+ students  | CAX41   | Many concurrent sessions             |
| Production with SLA      | CCX33   | Dedicated CPU, no noisy neighbor     |
| High load                | CCX43+  | 60+ projects, hundreds of users      |

## 2. Hetzner Load Balancers

> Last verified: 2026-04-22

| LB   | Services | Targets | SSL Certs | Connections | Traffic | Price/mo |
|------|----------|---------|-----------|-------------|---------|----------|
| LB11 | 5        | 25      | 10        | 10,000      | 1 TB    | ~6 €     |
| LB21 | 15       | 75      | 25        | 20,000      | 2 TB    | ~40 €    |
| LB31 | 30       | 150     | 50        | 40,000      | 3 TB    | ~91 €    |

**For apps that use persistent WebSocket connections** (Streamlit, live chat,
realtime dashboards): sticky sessions MUST be enabled (cookie-based) on the
load balancer. Without sticky sessions, a user's requests may be routed to
different servers mid-session, breaking the long-lived connection.

## 3. Other Hetzner Pricing

> Last verified: 2026-04-22

| Resource              | Price                 |
|-----------------------|-----------------------|
| IPv4 (primary)        | Included (0.50 €/mo)  |
| Floating IPv4         | 3 €/mo                |
| Floating IPv6         | 1 €/mo                |
| Block Storage         | 0.057 €/GB/mo         |
| Snapshots             | 0.012 €/GB/mo         |
| Backups               | +20% of server price  |
| Extra traffic (>20TB) | 1 €/TB                |
| Cloud Firewall        | Free                  |
| Private Networks      | Free                  |

## 4. Datacenters

> Last verified: 2026-04-22

| Location       | ID   | Region     | Latency EU | Latency US | ARM available |
|----------------|------|------------|------------|------------|---------------|
| Falkenstein    | fsn1 | Germany    | ~10-20 ms  | ~100 ms    | Yes           |
| Nuremberg      | nbg1 | Germany    | ~10-20 ms  | ~100 ms    | Yes           |
| Helsinki       | hel1 | Finland    | ~30-40 ms  | ~120 ms    | Yes           |
| Ashburn        | ash  | USA (VA)   | ~80 ms     | ~10 ms     | No            |
| Hillsboro      | hil  | USA (OR)   | ~120 ms    | ~20 ms     | No            |

Default recommendation: **fsn1** for EU users, **ash** for US users.

## 5. Application Resource Profiles

> Last verified: 2026-04-22

Approximate resource consumption by application type. Use these figures to
estimate server capacity and recommend sizing.

### System overhead (incompressible)

| Component          | RAM         |
|--------------------|-------------|
| OS + Docker        | ~500 MB     |
| Coolify + Postgres | ~600 MB     |
| Traefik            | ~100 MB     |
| **Total**          | **~1.2 GB** |

### Per-application profiles

| Profile         | Typical apps                        | RAM idle | RAM per user | Users per 1 GB |
|-----------------|-------------------------------------|----------|--------------|----------------|
| **Documentation** | Static sites, docs, landing pages  | ~100 MB  | +30 MB       | 15–25          |
| **Web app**       | SPA, dashboards, interactive UI    | ~250 MB  | +80 MB       | 5–8            |
| **Data / API**    | REST APIs, DB-backed services      | ~250 MB  | +80 MB       | 5–8            |
| **AI / Multimedia** | ML models, image generation      | ~500 MB  | +150 MB      | 2–3            |

### Capacity formula

```
Available RAM     = Server RAM - 1.2 GB (overhead)
Max apps (idle)   = Available RAM / Profile RAM idle
Max concurrent    = (Available RAM - N × Profile RAM idle) / Profile RAM per user
```

### Example: CAX31 (16 GB)

```
Available: 16 - 1.2 = 14.8 GB
Web apps (idle): 14.8 GB / 250 MB = ~60 (theoretical max)
Practical limit: ~20-30 web apps with moderate concurrent usage
```

## 6. State file

Deployment state lives in `.gse/deploy.json` at the project root. Its schema
is documented in `gse-one-implementation-design.md` §5.18 (State schema).
Credentials (tokens, SSH keys) never live in the state file; they live in
`.env` which MUST be gitignored.

## 7. Coolify API Endpoints Reference

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List applications | GET | `/api/v1/applications` |
| Get application | GET | `/api/v1/applications/{uuid}` |
| Create application | POST | `/api/v1/applications` |
| Update application | PATCH | `/api/v1/applications/{uuid}` |
| Delete application | DELETE | `/api/v1/applications/{uuid}` |
| Rebuild (full) | POST | `/api/v1/applications/{uuid}/start` |
| Restart (quick) | POST | `/api/v1/applications/{uuid}/restart` |
| Stop | POST | `/api/v1/applications/{uuid}/stop` |
| Get env vars | GET | `/api/v1/applications/{uuid}/envs` |
| Set env var | POST | `/api/v1/applications/{uuid}/envs` |
| Deploy (webhook) | GET | `/api/v1/deploy?uuid={uuid}` |
| List projects | GET | `/api/v1/projects` |
| Create project | POST | `/api/v1/projects` |
| Delete project | DELETE | `/api/v1/projects/{uuid}` |

**CRITICAL**: `/start` = full rebuild (pull git, rebuild Docker, install deps).
`/restart` = reuse existing container (no code update). Always use `/start`
for code updates. To force a rebuild on the same commit:
`GET /api/v1/deploy?uuid={uuid}&force=true`.

### Docker cache-bust (universal best practice)

Every Dockerfile built by Coolify SHOULD include an `ARG SOURCE_COMMIT=unknown`
declaration **before** the dependency install layer. Coolify passes
`SOURCE_COMMIT` automatically with the git commit hash. Without this ARG,
Docker caches the dependency install layer aggressively and may skip
reinstalling packages when a new commit only changes application code but
also requires a refreshed dependency tree.

**Symptom if missing**: deployed app runs with stale dependencies, even though
the image rebuilds; the lock file may have changed but the cached layer is
reused.

**Rule**: when generating a Dockerfile for a new project, always include
`ARG SOURCE_COMMIT=unknown` as the first ARG after the base image.

## 8. GitHub Actions Integration

Coolify can redeploy applications via webhook on git push. Two patterns:

1. **Auto-deploy in Coolify**: in the application settings, enable "Auto Deploy"
   and copy the webhook URL. In GitHub, add this URL as a webhook on push events.
   No GitHub Actions workflow needed. Simplest setup.

2. **Workflow-based**: a GitHub Actions workflow polls for a condition (e.g.,
   package published on PyPI or npm) before calling the Coolify deploy API.
   Uses `COOLIFY_API_TOKEN` as a GitHub secret. Better control but more setup.

For the default `/gse:deploy` flow, pattern 1 is sufficient. Pattern 2 belongs
to projects with external release dependencies.

## 9. Security Checklist

- [ ] Non-root user with SSH key (`deploy`)
- [ ] Root login disabled in `/etc/ssh/sshd_config`
- [ ] Password authentication disabled
- [ ] UFW active with ports 22, 80, 443 open only
- [ ] `ufw-docker` installed (prevents Docker from bypassing UFW rules)
- [ ] fail2ban active (sshd jail: 3 attempts → 1h ban)
- [ ] Unattended security upgrades enabled
- [ ] Coolify dashboard behind HTTPS (port 8000 closed after domain setup)
- [ ] No credentials in `.gse/deploy.json` or git
- [ ] `.env` gitignored
