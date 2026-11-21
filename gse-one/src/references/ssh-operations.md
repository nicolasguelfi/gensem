# SSH Operations Reference

This reference centralizes SSH connection patterns used by `/gse:deploy`
(and any future skill that interacts with the Hetzner server).

## Credential resolution

Always read credentials in this order (matches what `deploy.py` actually honors — project-local files only):

1. `.env` in project root (the only credential source `deploy.py` reads)
2. `.gse/deploy.json` → `server.ipv4`, `server.name` (non-secret server metadata)
3. Prompt the user as a last resort

The canonical SSH key path is `~/.ssh/gse-deploy`. The SSH key name registered
in Hetzner is `gse-deploy`. Any other path works (e.g. a course-dedicated key
kept outside `~/.ssh`): `SSH_KEY` in `.env` records it.

## Paths with spaces

Always double-quote key and known-hosts paths (`-i "$SSH_KEY_PATH"`). For
`-o` options whose value is a path, quoting the whole argument is not enough:
ssh splits the option value on whitespace (`UserKnownHostsFile` accepts several
files), so a path with spaces must be quoted **inside** the value:

```bash
ssh -i "$SSH_KEY_PATH" -o "UserKnownHostsFile=\"$KNOWN_HOSTS\"" deploy@$SERVER_IP "command"
```

## Connection patterns

### Standard SSH command (as root, during initial provisioning)

```bash
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 root@$SERVER_IP "command"
```

### Standard SSH command (as deploy user, after secure phase)

```bash
ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 deploy@$SERVER_IP "command"
```

### Multi-line SSH script

```bash
ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 deploy@$SERVER_IP << 'REMOTE'
command1
command2
command3
REMOTE
```

### Which user to use per phase

| Phase              | User             | Reason |
|--------------------|------------------|--------|
| provision (created)| `root`           | Only root exists at this point |
| secure (hardening) | `root` → `deploy`| Switch to deploy at the end of the phase. Root stays allowed by key from Docker networks only (Coolify manages its host as root) |
| coolify            | `deploy`         | Coolify installer runs with sudo (Phase 4 — install Coolify v4) |
| dns                | `deploy`         | Post-hardening, sudo available (Phase 5 — DNS wildcard + SSL + port 8000 close) |
| All maintenance ops| `deploy`         | Standard operations |

## Server IP resolution

Read IP from `.gse/deploy.json`:

```
server.ipv4
```

## Health check after SSH operations

After any operation that changes the server state:

```bash
# Verify server is reachable
ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 deploy@$SERVER_IP "echo OK && uptime"
```

## Coolify-specific SSH patterns

### Check Coolify container status

```bash
ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 deploy@$SERVER_IP \
  "sudo docker ps --format '{{.Names}}\t{{.Status}}'"
```

### View container logs

```bash
ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 deploy@$SERVER_IP \
  "sudo docker logs --tail 20 CONTAINER_NAME 2>&1"
```

### Check resource usage

```bash
ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 deploy@$SERVER_IP \
  "free -h && echo '---' && df -h / && echo '---' && sudo docker stats --no-stream"
```

## Constants

| Constant          | Default value         | Description |
|-------------------|-----------------------|-------------|
| SSH key path      | `~/.ssh/gse-deploy`   | Default key location (can be overridden via `SSH_KEY` in `.env`) |
| SSH key name      | `gse-deploy`          | Name registered in Hetzner |
| SSH user          | `deploy`              | Non-root user created by the secure phase |
| Server type       | `cax21`               | Default ARM server (can be overridden via `config.yaml → deploy.server_type`) |
| Location          | `fsn1`                | Falkenstein datacenter (can be overridden via `config.yaml → deploy.datacenter`) |
| Coolify port      | `8000`                | Dashboard port (container port 8080 behind `ufw-docker`), open only during initial setup |

## Timeouts and retries

- Always use `-o ConnectTimeout=10` to avoid hanging on unreachable servers
- After provisioning, retry SSH up to 3 times with 15s interval (server boot)
- Never use `-o StrictHostKeyChecking=no` beyond the initial `accept-new` —
  it silently accepts man-in-the-middle attacks
