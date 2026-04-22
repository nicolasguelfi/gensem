# SSH Operations Reference

This reference centralizes SSH connection patterns used by `/gse:deploy`
(and any future skill that interacts with the Hetzner server).

## Credential resolution

Always read credentials in this order:

1. `.env` in project root (preferred)
2. `.env` in parent directory
3. Environment variables (`COOLIFY_URL`, `COOLIFY_API_TOKEN`,
   `HETZNER_API_TOKEN`, `SSH_KEY`, `SSH_USER`, `SERVER_IP`)
4. `.gse/deploy.json` → `server.ipv4`, `server.name`
5. Prompt the user as a last resort

The canonical SSH key path is `~/.ssh/gse-deploy`. The SSH key name registered
in Hetzner is `gse-deploy`.

## Connection patterns

### Standard SSH command (as root, during initial provisioning)

```bash
ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 root@$SERVER_IP "command"
```

### Standard SSH command (as deploy user, after secure phase)

```bash
ssh -i $SSH_KEY_PATH -o ConnectTimeout=10 deploy@$SERVER_IP "command"
```

### Multi-line SSH script

```bash
ssh -i $SSH_KEY_PATH -o ConnectTimeout=10 deploy@$SERVER_IP << 'REMOTE'
command1
command2
command3
REMOTE
```

### Which user to use per phase

| Phase              | User             | Reason |
|--------------------|------------------|--------|
| provision (created)| `root`           | Only root exists at this point |
| secure (hardening) | `root` → `deploy`| Switch to deploy at the end of the phase |
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
ssh -i $SSH_KEY_PATH -o ConnectTimeout=10 deploy@$SERVER_IP "echo OK && uptime"
```

## Coolify-specific SSH patterns

### Check Coolify container status

```bash
ssh -i $SSH_KEY_PATH -o ConnectTimeout=10 deploy@$SERVER_IP \
  "sudo docker ps --format '{{.Names}}\t{{.Status}}'"
```

### View container logs

```bash
ssh -i $SSH_KEY_PATH -o ConnectTimeout=10 deploy@$SERVER_IP \
  "sudo docker logs --tail 20 CONTAINER_NAME 2>&1"
```

### Check resource usage

```bash
ssh -i $SSH_KEY_PATH -o ConnectTimeout=10 deploy@$SERVER_IP \
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
| Coolify port      | `8000`                | Dashboard port, open only during initial setup |

## Timeouts and retries

- Always use `-o ConnectTimeout=10` to avoid hanging on unreachable servers
- After provisioning, retry SSH up to 3 times with 15s interval (server boot)
- Never use `-o StrictHostKeyChecking=no` beyond the initial `accept-new` —
  it silently accepts man-in-the-middle attacks
