#!/usr/bin/env python3
# @gse-tool deploy 1.0
"""
GSE-One /gse:deploy orchestrator.

CLI subcommands invoked by the skill src/activities/deploy.md.

Uses only Python 3.9+ standard library. Imports coolify_client from the same
directory (plugin/tools/).

Usage: python3 deploy.py <subcommand> [args...]

See docs: gse-one-implementation-design.md §5.18 — Execution tools
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Import CoolifyClient from the same directory.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from coolify_client import CoolifyClient, CoolifyError  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATE_PATH = Path(".gse/deploy.json")
ENV_PATH = Path(".env")
STATE_VERSION = "1.0"
DNS_LABEL_MAX = 63
FQDN_MAX = 253
SUBDOMAIN_COMPONENT_MAX = 30

PHASE_NAMES = {"setup", "provision", "secure", "coolify", "dns"}

VALID_ROLES = {"solo", "instructor", "learner"}

DEFAULT_HEALTH_CHECK_PATHS = {
    "streamlit": "/_stcore/health",
    "python": "/",
    "node": "/",
    "static": "/",
    "custom": "/",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    """ISO 8601 timestamp with UTC timezone."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_out(data: Any) -> None:
    """Print JSON to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _err(msg: str, code: int = 1) -> None:
    """Print error to stderr and exit."""
    sys.stderr.write(f"error: {msg}\n")
    sys.exit(code)


# ---------------------------------------------------------------------------
# State management (.gse/deploy.json)
# ---------------------------------------------------------------------------


def _empty_state() -> dict:
    """Return a fresh empty deploy state with the current STATE_VERSION."""
    return {
        "version": STATE_VERSION,
        "plugin": "gse-one",
        "created_at": _now(),
        "last_updated_at": _now(),
        "user_role": "",
        "phases_completed": {
            "setup": "",
            "provision": "",
            "secure": "",
            "coolify": "",
            "dns": "",
        },
        "server": {
            "name": "",
            "id": None,
            "ipv4": "",
            "type": "cax21",
            "datacenter": "fsn1",
        },
        "coolify": {"url": "", "version": ""},
        "domain": {"base": "", "registrar": ""},
        "cdn": {"provider": "", "enabled": False, "bot_protection": False},
        "applications": [],
    }


def load_state() -> dict:
    """Load the deploy state from STATE_PATH, or return an empty state if absent.
    Corrupt JSON triggers _err() — this is a library exit path retained for now
    (JSON corruption is unrecoverable; the CLI wrapper cannot produce a better
    remedy than a fatal error with the file path)."""
    if not STATE_PATH.exists():
        return _empty_state()
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _err(f"corrupt state file {STATE_PATH}: {e}")


def save_state(state: dict) -> None:
    """Persist state to STATE_PATH with refreshed `last_updated_at` timestamp.
    Creates the .gse/ parent directory if needed."""
    state["last_updated_at"] = _now()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def init_state() -> dict:
    """Ensure .gse/deploy.json exists; return the existing state if present,
    otherwise create an empty one. Idempotent."""
    if STATE_PATH.exists():
        return load_state()
    state = _empty_state()
    save_state(state)
    return state


# ---------------------------------------------------------------------------
# .env file management (preserves comments/order)
# ---------------------------------------------------------------------------


def parse_env(path: Path = ENV_PATH) -> dict:
    """Parse .env into a dict. Missing file → empty dict."""
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        # Strip optional surrounding quotes
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        result[key.strip()] = value
    return result


def set_env(key: str, value: str, path: Path = ENV_PATH) -> None:
    """Set or replace a KEY=VALUE line in .env, preserving comments and order."""
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    replaced = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        line_key, _, _ = stripped.partition("=")
        if line_key.strip() == key:
            new_lines.append(f"{key}={value}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        new_lines.append(f"{key}={value}")

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def delete_env(key: str, path: Path = ENV_PATH) -> None:
    """Delete a KEY= line from .env. No-op if missing."""
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        line_key, _, _ = stripped.partition("=")
        if line_key.strip() == key:
            continue
        new_lines.append(line)
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Subdomain sanitization (see P1 / design §5.18)
# ---------------------------------------------------------------------------


def sanitize_component(name: str, max_len: int = SUBDOMAIN_COMPONENT_MAX) -> str:
    """Sanitize a single DNS label component per P1 rules."""
    if not name:
        return ""
    # lowercase, replace non-[a-z0-9-] with -, collapse, trim, truncate
    lower = name.lower()
    replaced = re.sub(r"[^a-z0-9-]", "-", lower)
    collapsed = re.sub(r"-+", "-", replaced)
    trimmed = collapsed.strip("-")
    return trimmed[:max_len].rstrip("-")


def build_subdomain(
    project_dir: str, deploy_user: Optional[str], domain: str
) -> dict:
    """Build the full subdomain per P1. Returns dict with components and FQDN."""
    project_name = sanitize_component(Path(project_dir).name)
    if not project_name:
        return {
            "ok": False,
            "error": "project name sanitizes to empty — pass --subdomain explicitly",
        }
    user = sanitize_component(deploy_user) if deploy_user else ""
    if deploy_user and not user:
        return {
            "ok": False,
            "error": "DEPLOY_USER sanitizes to empty — check the value",
        }

    if user:
        label = f"{project_name}-{user}"
    else:
        label = project_name

    if len(label) > DNS_LABEL_MAX:
        return {
            "ok": False,
            "error": (
                f"combined label too long ({len(label)} > {DNS_LABEL_MAX}): "
                f"{label}"
            ),
        }

    fqdn = f"{label}.{domain}"
    if len(fqdn) > FQDN_MAX:
        return {"ok": False, "error": f"FQDN too long ({len(fqdn)} > {FQDN_MAX})"}

    return {
        "ok": True,
        "project_name": project_name,
        "deploy_user": user,
        "label": label,
        "subdomain": fqdn,
        "url": f"https://{fqdn}",
    }


# ---------------------------------------------------------------------------
# Situation detection (Step 0)
# ---------------------------------------------------------------------------


def detect_situation() -> dict:
    """Inspect .env and state to determine starting phase and mode."""
    env = parse_env()
    state = load_state() if STATE_PATH.exists() else None
    phases_done = (
        state.get("phases_completed", {}) if state else {}
    )  # e.g. {"setup": "...", "provision": ""}

    has_token = bool(env.get("HETZNER_API_TOKEN"))
    has_server = bool(env.get("SERVER_IP"))
    has_ssh_user = bool(env.get("SSH_USER"))
    has_coolify = bool(env.get("COOLIFY_URL") and env.get("COOLIFY_API_TOKEN"))
    has_domain = bool(env.get("DEPLOY_DOMAIN"))
    has_user = bool(env.get("DEPLOY_USER"))

    # Infer starting phase
    if has_coolify and has_domain:
        starting_phase = 6
        mode = "training" if has_user else "app-only"
    elif has_server and has_ssh_user and not has_coolify:
        starting_phase = 3 if not phases_done.get("secure") else 4
        mode = "partial"
    elif has_token and not has_server:
        starting_phase = 2
        mode = "full"
    elif has_token:
        starting_phase = 2
        mode = "full"
    else:
        starting_phase = 1
        mode = "full"

    # Clamp upward: if a phase is already completed, skip to the next
    for idx, name in enumerate(
        ["setup", "provision", "secure", "coolify", "dns"], start=1
    ):
        if phases_done.get(name):
            starting_phase = max(starting_phase, idx + 1)

    return {
        "starting_phase": starting_phase,
        "mode": mode,
        "env_present": {
            "HETZNER_API_TOKEN": has_token,
            "SERVER_IP": has_server,
            "SSH_USER": has_ssh_user,
            "COOLIFY_URL": bool(env.get("COOLIFY_URL")),
            "COOLIFY_API_TOKEN": bool(env.get("COOLIFY_API_TOKEN")),
            "DEPLOY_DOMAIN": has_domain,
            "DEPLOY_USER": has_user,
        },
        "phases_completed": {k: bool(v) for k, v in phases_done.items()},
    }


# ---------------------------------------------------------------------------
# Phase recording
# ---------------------------------------------------------------------------


def record_phase(phase_name: str) -> dict:
    """Mark a Phase N as completed in state (called at the end of each server-level phase —
    setup / provision / secure / coolify / dns). Returns status-wrapped dict:
    {"status": "ok" | "error", "phase": str, "completed_at": ISO8601} (or "error": str on failure)."""
    if phase_name not in PHASE_NAMES:
        return {
            "status": "error",
            "error": f"unknown phase '{phase_name}' (expected one of: {sorted(PHASE_NAMES)})",
        }
    state = load_state()
    if "phases_completed" not in state:
        state["phases_completed"] = {}
    state["phases_completed"][phase_name] = _now()
    save_state(state)
    return {
        "status": "ok",
        "phase": phase_name,
        "completed_at": state["phases_completed"][phase_name],
    }


def record_server(
    name: str, ipv4: str, id_: Optional[int], type_: str, datacenter: str
) -> dict:
    """Persist the provisioned Hetzner server block in state (called at the end of Phase 2 —
    provision). Returns status-wrapped dict: {"status": "ok" | "error", "server": {...}}."""
    if not name or not ipv4:
        return {
            "status": "error",
            "error": "record_server requires both name and ipv4 (non-empty)",
        }
    state = load_state()
    state["server"] = {
        "name": name,
        "id": id_,
        "ipv4": ipv4,
        "type": type_,
        "datacenter": datacenter,
    }
    save_state(state)
    return {"status": "ok", "server": state["server"]}


def record_coolify(url: str, version: str = "") -> dict:
    """Persist the Coolify endpoint in state (called at the end of Phase 4 — coolify,
    i.e. after Coolify v4 is installed and reachable). Returns status-wrapped dict:
    {"status": "ok" | "error", "coolify": {"url": str, "version": str}}."""
    if not url:
        return {
            "status": "error",
            "error": "record_coolify requires a non-empty url",
        }
    state = load_state()
    state["coolify"] = {"url": url, "version": version}
    save_state(state)
    return {"status": "ok", "coolify": state["coolify"]}


def record_domain(base: str, registrar: str = "") -> dict:
    """Persist the deployment base domain + registrar in state (called at the end of Phase 5 —
    dns, i.e. after DNS wildcard + SSL are verified). Returns status-wrapped dict:
    {"status": "ok" | "error", "domain": {"base": str, "registrar": str}}."""
    if not base:
        return {
            "status": "error",
            "error": "record_domain requires a non-empty base domain",
        }
    state = load_state()
    state["domain"] = {"base": base, "registrar": registrar}
    save_state(state)
    return {"status": "ok", "domain": state["domain"]}


def record_role(role: str) -> dict:
    """Persist the user role in state (solo | instructor | learner).

    Called by the skill's Step -1 Orientation once the user selects a role option.
    The Step -1 "Skip" menu option is a meta-action (bypass orientation, no role
    persisted); it does not call record-role. See deploy.md Step -1 option (4).
    The role is purely informational in v1 — no behavioral branching beyond Step -1.
    Returns status-wrapped dict: {"status": "ok" | "error", "role": str}.
    """
    if role not in VALID_ROLES:
        return {
            "status": "error",
            "error": f"invalid role '{role}'. Must be one of: {sorted(VALID_ROLES)}",
        }
    if not STATE_PATH.exists():
        init_state()
    state = load_state()
    state["user_role"] = role
    save_state(state)
    return {"status": "ok", "role": role}


def record_cdn(provider: str, enabled: bool, bot_protection: bool = False) -> dict:
    """Persist the CDN configuration in state (called at the end of Phase 5 Step 7 —
    optional Cloudflare CDN setup). Returns status-wrapped dict:
    {"status": "ok" | "error", "cdn": {"provider": str, "enabled": bool, "bot_protection": bool}}."""
    if enabled and not provider:
        return {
            "status": "error",
            "error": "record_cdn requires a non-empty provider when enabled=True",
        }
    state = load_state()
    state["cdn"] = {
        "provider": provider,
        "enabled": bool(enabled),
        "bot_protection": bool(bot_protection),
    }
    save_state(state)
    return {"status": "ok", "cdn": state["cdn"]}


# ---------------------------------------------------------------------------
# DNS polling (Phase 5)
# ---------------------------------------------------------------------------


def wait_dns(
    domain: str, expected_ip: str, timeout_seconds: int = 600
) -> dict:
    """Poll `dig` until `domain` resolves to `expected_ip`, or timeout.

    Tries the default resolver first, falls back to `@8.8.8.8` (Google
    public DNS) to bypass local cache. Returns structured JSON.
    """
    deadline = time.time() + timeout_seconds
    last_result = ""
    last_resolver = ""
    attempts = 0
    while time.time() < deadline:
        attempts += 1
        for resolver_arg in ("", "@8.8.8.8"):
            cmd = ["dig", "+short"]
            if resolver_arg:
                cmd.append(resolver_arg)
            cmd.append(domain)
            try:
                r = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10
                )
                ips = [
                    line.strip()
                    for line in r.stdout.splitlines()
                    if line.strip() and not line.strip().startswith(";")
                ]
                last_result = ",".join(ips) if ips else "(no answer)"
                last_resolver = resolver_arg or "system"
                if expected_ip in ips:
                    return {
                        "status": "resolved",
                        "domain": domain,
                        "resolver": last_resolver,
                        "ips": ips,
                        "attempts": attempts,
                    }
            except subprocess.TimeoutExpired:
                last_result = "(dig timeout)"
            except FileNotFoundError:
                return {
                    "status": "error",
                    "error": "dig not found — install dnsutils (Linux) or bind (macOS)",
                }
        time.sleep(15)
    return {
        "status": "timeout",
        "domain": domain,
        "expected": expected_ip,
        "last_result": last_result,
        "last_resolver": last_resolver,
        "attempts": attempts,
        "hint": (
            "DNS not propagated yet. This can take 5-30 minutes. "
            "Verify records at your registrar, then re-run."
        ),
    }


# ---------------------------------------------------------------------------
# Health check polling
# ---------------------------------------------------------------------------


def poll_health(url: str, timeout_seconds: int = 120) -> dict:
    """Poll the URL until 2xx or timeout. Returns {status, http_code}."""
    deadline = time.time() + timeout_seconds
    last_code = 0
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                last_code = resp.status
                if 200 <= resp.status < 300:
                    return {"status": "healthy", "http_code": resp.status, "url": url}
        except urllib.error.HTTPError as e:
            last_code = e.code
        except urllib.error.URLError:
            last_code = 0
        time.sleep(10)
    return {
        "status": "timeout" if last_code == 0 else "unhealthy",
        "http_code": last_code,
        "url": url,
    }


# ---------------------------------------------------------------------------
# Deploy app (Phase 6 — consolidated)
# ---------------------------------------------------------------------------


def deploy_app(
    name: str,
    project_name: str,
    deploy_user: str,
    subdomain: str,
    github_repo: str,
    branch: str,
    type_: str,
    port: int,
    memory: str = "512m",
    cpu: str = "0.5",
    health_timeout: int = 120,
) -> dict:
    """End-to-end Phase 6: ensure Coolify project/env, create/reuse app, deploy,
    health check, update state.
    """
    env = parse_env()
    coolify_url = env.get("COOLIFY_URL")
    coolify_token = env.get("COOLIFY_API_TOKEN")
    if not coolify_url or not coolify_token:
        return {
            "status": "error",
            "error": "missing COOLIFY_URL or COOLIFY_API_TOKEN in .env",
        }

    client = CoolifyClient(coolify_url, coolify_token)

    # 1. Determine project name (per Coolify hierarchy mapping, design §5.18)
    coolify_project_name = f"gse-{deploy_user}" if deploy_user else "gse"

    try:
        # 2. Ensure project
        project = client.ensure_project(
            coolify_project_name, description="Managed by GSE-One"
        )
        # 3. Ensure environment
        env_obj = client.ensure_environment(project.uuid, "production")

        # 4. Check for existing application in state
        state = load_state()
        existing = _find_application(state, name)

        if existing and existing.get("coolify", {}).get("app_uuid"):
            app_uuid = existing["coolify"]["app_uuid"]
            # Redeploy path
            client.trigger_deploy(app_uuid, force=True)
            created = False
        else:
            # Create new application
            app = client.create_application(
                project_uuid=project.uuid,
                environment_name="production",
                name=name,
                git_repository=github_repo,
                git_branch=branch,
                ports_exposes=str(port),
                fqdn=f"https://{subdomain}",
            )
            app_uuid = app.uuid
            client.trigger_deploy(app_uuid, force=False)
            created = True

        # 5. Health check
        health_path = DEFAULT_HEALTH_CHECK_PATHS.get(type_, "/")
        health_url = f"https://{subdomain}{health_path}"
        health = poll_health(health_url, timeout_seconds=health_timeout)

        # 6. Update state
        now = _now()
        entry = {
            "name": name,
            "project_name": project_name,
            "deploy_user": deploy_user,
            "subdomain": subdomain,
            "url": f"https://{subdomain}",
            "github_repo": github_repo,
            "branch": branch,
            "type": type_,
            "port": port,
            "coolify": {
                "project_uuid": project.uuid,
                "environment_uuid": env_obj.uuid,
                "app_uuid": app_uuid,
            },
            "resources": {"memory_limit": memory, "cpu_limit": cpu},
            "created_at": (existing or {}).get("created_at") or now,
            "last_deploy_at": now,
            "status": health["status"],
        }
        _upsert_application(state, entry)
        save_state(state)

        return {
            "status": health["status"],
            "url": f"https://{subdomain}",
            "app_uuid": app_uuid,
            "created": created,
            "http_code": health.get("http_code"),
        }
    except CoolifyError as e:
        return {"status": "error", "error": str(e), "http_status": e.status}


def _find_application(state: dict, name: str) -> Optional[dict]:
    """Locate an application entry by name in state. Returns None if missing."""
    for entry in state.get("applications", []):
        if entry.get("name") == name:
            return entry
    return None


def _upsert_application(state: dict, entry: dict) -> None:
    """Insert or replace an application entry in state (in-place mutation; keyed by name)."""
    apps = state.setdefault("applications", [])
    for i, existing in enumerate(apps):
        if existing.get("name") == entry["name"]:
            apps[i] = entry
            return
    apps.append(entry)


# ---------------------------------------------------------------------------
# App status (live health check)
# ---------------------------------------------------------------------------


def app_status(name: str) -> dict:
    """Live health check of a recorded application by name. Performs a short poll_health()
    against the application URL and persists the observed status back into state. Returns
    {"status": str, "name": str, "url": str, "type": str, "http_code": int} (or
    {"status": "unknown", "error": str} if the application is not recorded)."""
    state = load_state()
    entry = _find_application(state, name)
    if not entry:
        return {"status": "unknown", "error": f"no application named '{name}' in state"}
    type_ = entry.get("type", "custom")
    health_path = DEFAULT_HEALTH_CHECK_PATHS.get(type_, "/")
    url = entry.get("url", "")
    if not url:
        return {"status": "unknown", "error": "no URL recorded"}
    health_url = f"{url}{health_path}"
    result = poll_health(health_url, timeout_seconds=30)
    # Persist the observed status
    entry["status"] = result["status"]
    save_state(state)
    return {
        "name": name,
        "url": url,
        "type": type_,
        "status": result["status"],
        "http_code": result.get("http_code"),
    }


# ---------------------------------------------------------------------------
# Destroy
# ---------------------------------------------------------------------------


_COST_PER_TYPE_EUR = {
    "cax11": 4.49, "cax21": 8.49, "cax31": 16.49, "cax41": 31.99,
    "cx22": 5.09, "cx32": 9.09, "cx42": 21.49, "cx52": 42.49,
    "ccx13": 12.49, "ccx23": 24.49, "ccx33": 48.49,
    "ccx43": 96.49, "ccx53": 191.99,
}


def _cost_hint(server_type: str) -> str:
    """Human-readable monthly cost for a given Hetzner server type."""
    cost = _COST_PER_TYPE_EUR.get((server_type or "").lower())
    if cost is None:
        return "unknown server type — check Hetzner console"
    return f"~{cost:.2f} EUR/month saved after destroy"


def destroy(confirm_name: str, dry_run: bool = False) -> dict:
    """Delete Coolify apps + gse-* projects + Hetzner server + firewall.

    With dry_run=True, enumerates resources and returns without touching.
    On partial failure, state is preserved so the user can retry.
    """
    state = load_state()
    server_name = state.get("server", {}).get("name", "")
    server_type = state.get("server", {}).get("type", "")
    if not server_name:
        return {"status": "error", "error": "no server recorded in state"}

    if not dry_run and confirm_name != server_name:
        return {
            "status": "error",
            "error": (
                f"confirmation mismatch: expected '{server_name}', got "
                f"'{confirm_name}'"
            ),
        }

    env = parse_env()
    coolify_url = env.get("COOLIFY_URL")
    coolify_token = env.get("COOLIFY_API_TOKEN")
    apps = state.get("applications", [])
    app_names = [a.get("name", "") for a in apps if a.get("name")]

    # Pre-flight: enumerate Coolify projects that would / will be deleted.
    projects_to_delete: list[str] = []
    client: Optional[CoolifyClient] = None
    coolify_enum_error: Optional[str] = None
    if coolify_url and coolify_token:
        try:
            client = CoolifyClient(coolify_url, coolify_token)
            projects_to_delete = [
                p.name
                for p in client.list_projects()
                if p.name == "gse" or p.name.startswith("gse-")
            ]
        except Exception as e:  # noqa: BLE001
            coolify_enum_error = f"Coolify enumeration failed: {e}"
            client = None

    if dry_run:
        result = {
            "status": "dry-run",
            "would_delete_applications": app_names,
            "would_delete_projects": projects_to_delete,
            "would_delete_server": server_name,
            "would_delete_firewall": f"gse-fw-{server_name}",
            "estimated_cost_savings": _cost_hint(server_type),
            "hint": f"re-run with --confirm {server_name} to actually destroy",
        }
        if coolify_enum_error:
            result["warning"] = coolify_enum_error
        return result

    deleted_apps: list[str] = []
    deleted_projects: list[str] = []
    errors: list[str] = []

    if coolify_enum_error:
        errors.append(coolify_enum_error)

    # 1. Delete Coolify apps + projects (best effort)
    if client is not None:
        for app_entry in apps:
            uuid = app_entry.get("coolify", {}).get("app_uuid")
            if uuid:
                try:
                    client.delete_application(uuid)
                    deleted_apps.append(app_entry.get("name", uuid))
                except CoolifyError as e:
                    errors.append(f"app {uuid}: {e}")
        for proj_name in projects_to_delete:
            try:
                proj = client.find_project_by_name(proj_name)
                if proj:
                    client.delete_project(proj.uuid)
                    deleted_projects.append(proj_name)
            except CoolifyError as e:
                errors.append(f"project {proj_name}: {e}")

    # 2. Delete Hetzner server and firewall via hcloud CLI
    hcloud_ok = True
    fw_name = f"gse-fw-{server_name}"
    for cmd, label in [
        (["hcloud", "server", "delete", server_name], "server"),
        (["hcloud", "firewall", "delete", fw_name], "firewall"),
    ]:
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        except subprocess.CalledProcessError as e:
            errors.append(
                f"hcloud {label} delete: {e.stderr.decode('utf-8', 'replace')}"
            )
            hcloud_ok = False
        except FileNotFoundError:
            errors.append("hcloud CLI not found")
            hcloud_ok = False
        except subprocess.TimeoutExpired:
            errors.append(f"hcloud {label} delete: timeout")
            hcloud_ok = False

    # 3. Reset state ONLY if all deletions succeeded.
    if not errors:
        save_state(_empty_state())
        status = "ok"
    else:
        status = "partial"

    return {
        "status": status,
        "deleted_applications": deleted_apps,
        "deleted_projects": deleted_projects,
        "deleted_server": server_name if hcloud_ok else None,
        "errors": errors,
        "state_preserved_for_retry": bool(errors),
        "cost_savings": _cost_hint(server_type) if status == "ok" else None,
    }


# ---------------------------------------------------------------------------
# Preflight (Phase 6 Step 2)
# ---------------------------------------------------------------------------


_DEFAULT_PORTS = {
    "streamlit": 8501,
    "python": 8000,
    "node": 3000,
    "static": 80,
    "custom": None,
}


def _detect_type(project_dir: Path) -> tuple[str, list[str]]:
    """Return (type, evidence_list)."""
    evidence: list[str] = []
    pyproject = project_dir / "pyproject.toml"
    requirements = project_dir / "requirements.txt"
    package_json = project_dir / "package.json"

    streamlit_found = False
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8", errors="ignore")
        if "streamlit" in text.lower():
            streamlit_found = True
            evidence.append("pyproject.toml contains 'streamlit'")
    if not streamlit_found and requirements.exists():
        text = requirements.read_text(encoding="utf-8", errors="ignore")
        if any(
            line.strip().lower().startswith("streamlit")
            for line in text.splitlines()
        ):
            streamlit_found = True
            evidence.append("requirements.txt contains 'streamlit'")
    if streamlit_found:
        return "streamlit", evidence

    if pyproject.exists():
        evidence.append("pyproject.toml present")
        return "python", evidence
    if requirements.exists():
        evidence.append("requirements.txt present")
        return "python", evidence
    if package_json.exists():
        evidence.append("package.json present")
        return "node", evidence

    if (project_dir / "index.html").exists():
        evidence.append("index.html present; no pyproject/package.json")
        return "static", evidence

    evidence.append("no detection signal matched")
    return "custom", evidence


def _check(
    name: str,
    ok: bool,
    level: str,
    message: str = "",
    fix_hint: str = "",
) -> dict:
    return {
        "name": name,
        "ok": ok,
        "level": level,
        "message": message,
        "fix_hint": fix_hint,
    }


def _git_info(project_dir: Path) -> dict:
    """Probe .git/ for repo presence, commit count, origin remote, and working-tree cleanliness.
    Best-effort — any subprocess failure yields defaults (repo=False)."""
    result = {
        "repo": False,
        "commits": 0,
        "remote": "",
        "clean": True,
        "modified": 0,
    }
    if not (project_dir / ".git").exists():
        return result
    result["repo"] = True
    try:
        r = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0:
            result["commits"] = int(r.stdout.strip() or "0")
    except Exception:  # noqa: BLE001
        pass
    try:
        r = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0:
            result["remote"] = r.stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0:
            modified = [line for line in r.stdout.splitlines() if line.strip()]
            result["modified"] = len(modified)
            result["clean"] = len(modified) == 0
    except Exception:  # noqa: BLE001
        pass
    return result


def _streamlit_config_checks(project_dir: Path) -> list[dict]:
    """Build preflight _check() entries for .streamlit/config.toml (CORS + XSRF must be
    disabled when running behind Traefik in Coolify)."""
    checks: list[dict] = []
    cfg = project_dir / ".streamlit" / "config.toml"
    if not cfg.exists():
        checks.append(
            _check(
                "streamlit_config_exists",
                False,
                "warning",
                ".streamlit/config.toml missing",
                "create .streamlit/config.toml with [server] headless=true, "
                "port=8501, enableCORS=false, enableXsrfProtection=false",
            )
        )
        return checks
    text = cfg.read_text(encoding="utf-8", errors="ignore").lower()
    compact = text.replace(" ", "")
    checks.append(
        _check(
            "streamlit_config_cors",
            "enablecors=false" in compact,
            "warning",
            "enableCORS must be false for Traefik reverse proxy",
            "add 'enableCORS = false' under [server] in "
            ".streamlit/config.toml",
        )
    )
    checks.append(
        _check(
            "streamlit_config_xsrf",
            "enablexsrfprotection=false" in compact,
            "warning",
            "enableXsrfProtection must be false for Traefik reverse proxy",
            "add 'enableXsrfProtection = false' under [server] in "
            ".streamlit/config.toml",
        )
    )
    return checks


def _entry_point_check(project_dir: Path, type_: str) -> dict:
    """Verify a recognised entry point file exists for the given app type (streamlit accepts
    app.py / main.py / book.py / streamlit_app.py; python accepts main.py / app.py; etc.)."""
    candidates = {
        "streamlit": ["app.py", "main.py", "book.py", "streamlit_app.py"],
        "python": ["main.py", "app.py", "__main__.py"],
    }
    level = {"streamlit": "error", "python": "warning"}.get(type_, "info")
    entries = candidates.get(type_, [])
    for e in entries:
        if (project_dir / e).exists():
            return _check(
                f"{type_}_entry_point",
                True,
                "info",
                f"entry point found: {e}",
            )
    return _check(
        f"{type_}_entry_point",
        False,
        level,
        f"no entry point found (looked for: {', '.join(entries)})",
        f"create one of {entries[0]!r}, or edit the generated Dockerfile "
        f"CMD to point to your entry",
    )


def _dockerfile_check(project_dir: Path) -> list[dict]:
    """Flag Dockerfiles missing ARG SOURCE_COMMIT=unknown (Docker cache-bust — required
    so that identical commits don't reuse stale layers when the repo changes externally)."""
    dockerfile = project_dir / "Dockerfile"
    if not dockerfile.exists():
        return []
    text = dockerfile.read_text(encoding="utf-8", errors="ignore")
    return [
        _check(
            "dockerfile_source_commit",
            "ARG SOURCE_COMMIT" in text,
            "warning",
            "Dockerfile missing ARG SOURCE_COMMIT=unknown (Docker cache-bust)",
            "add 'ARG SOURCE_COMMIT=unknown' before the dependency install "
            "layer — see references/hetzner-infrastructure.md §7",
        )
    ]


def preflight(project_dir: Optional[str] = None) -> dict:
    """Detect project type and run all Phase 6 preflight checks."""
    pd = Path(project_dir or ".").resolve()
    type_, evidence = _detect_type(pd)
    port = _DEFAULT_PORTS.get(type_)

    checks: list[dict] = []

    # Deployable content (type-aware)
    if type_ == "custom":
        has_df = (pd / "Dockerfile").exists()
        checks.append(
            _check(
                "deployable_content",
                has_df,
                "error",
                f"detected type: custom ({'; '.join(evidence)})",
                "provide a Dockerfile or set deploy.app_type to a known "
                "value (streamlit|python|node|static)",
            )
        )
    else:
        checks.append(
            _check(
                "deployable_content",
                True,
                "info",
                f"detected type: {type_} ({'; '.join(evidence)})",
            )
        )

    # Git checks
    g = _git_info(pd)
    checks.append(
        _check(
            "git_repo",
            g["repo"],
            "error" if not g["repo"] else "info",
            "git repository required" if not g["repo"] else "git repo found",
            "run 'git init'" if not g["repo"] else "",
        )
    )
    if g["repo"]:
        checks.append(
            _check(
                "git_commits",
                g["commits"] > 0,
                "error" if g["commits"] == 0 else "info",
                f"{g['commits']} commit(s)",
                "make an initial commit" if g["commits"] == 0 else "",
            )
        )
        checks.append(
            _check(
                "git_remote",
                bool(g["remote"]),
                "warning" if not g["remote"] else "info",
                g["remote"] or "no remote 'origin' set",
                "add a GitHub remote: git remote add origin <url>"
                if not g["remote"]
                else "",
            )
        )
        if g["remote"]:
            is_gh = "github.com" in g["remote"].lower()
            checks.append(
                _check(
                    "git_remote_github",
                    is_gh,
                    "warning" if not is_gh else "info",
                    (
                        "Coolify supports GitHub natively; other providers "
                        "need manual source config"
                    )
                    if not is_gh
                    else "remote is github.com",
                )
            )
        checks.append(
            _check(
                "git_clean",
                g["clean"],
                "warning",
                (
                    f"{g['modified']} modified file(s) — Coolify deploys "
                    "remote HEAD, not your local changes"
                )
                if not g["clean"]
                else "working tree clean",
                "commit and push before deploying" if not g["clean"] else "",
            )
        )

    # Type-specific checks
    if type_ == "streamlit":
        checks.append(_entry_point_check(pd, "streamlit"))
        checks.extend(_streamlit_config_checks(pd))
    elif type_ == "python":
        checks.append(_entry_point_check(pd, "python"))
    elif type_ == "node":
        pkg = pd / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
                has_start = "start" in (data.get("scripts") or {})
                checks.append(
                    _check(
                        "node_start_script",
                        has_start,
                        "warning",
                        "package.json scripts.start present"
                        if has_start
                        else "package.json has no 'start' script",
                        "add '\"start\": \"node your-entry.js\"' to scripts "
                        "or edit Dockerfile.node CMD",
                    )
                )
                deps = data.get("dependencies") or {}
                if "next" in deps:
                    checks.append(
                        _check(
                            "nextjs_build_hint",
                            True,
                            "info",
                            "Next.js detected — remember to uncomment "
                            "'RUN npm run build' in Dockerfile.node",
                        )
                    )
            except json.JSONDecodeError:
                checks.append(
                    _check(
                        "package_json_valid",
                        False,
                        "error",
                        "package.json is not valid JSON",
                        "fix the JSON syntax",
                    )
                )
    elif type_ == "static":
        idx = (pd / "index.html").exists()
        checks.append(
            _check(
                "static_index_html",
                idx,
                "error" if not idx else "info",
                "index.html present"
                if idx
                else "no index.html at project root",
                "create an index.html" if not idx else "",
            )
        )

    # Dockerfile-level checks (if one exists)
    checks.extend(_dockerfile_check(pd))

    # Aggregate
    has_errors = any(
        c["level"] == "error" and not c["ok"] for c in checks
    )
    has_warnings = any(
        c["level"] == "warning" and not c["ok"] for c in checks
    )
    overall = "errors" if has_errors else (
        "warnings" if has_warnings else "ok"
    )

    return {
        "type": type_,
        "port": port,
        "project_dir": str(pd),
        "overall": overall,
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Training helpers
# ---------------------------------------------------------------------------


def training_init(output_path: str = ".env.training") -> dict:
    """Generate a redacted .env.training for distribution to learners.

    Includes COOLIFY_URL / COOLIFY_API_TOKEN / DEPLOY_DOMAIN and a DEPLOY_USER
    placeholder. Excludes HETZNER_API_TOKEN, SERVER_IP, SSH_USER, SSH_KEY
    (instructor-only secrets).
    """
    env = parse_env()
    required = ["COOLIFY_URL", "COOLIFY_API_TOKEN", "DEPLOY_DOMAIN"]
    missing = [k for k in required if not env.get(k)]
    if missing:
        return {
            "status": "error",
            "error": f"missing required keys in .env: {missing}",
        }
    domain = env["DEPLOY_DOMAIN"]
    content = (
        "# GSE-One Deploy — Training Configuration\n"
        f"# Generated by /gse:deploy --training-init on {_now()}\n"
        "# Distribute to learners alongside /gse:deploy usage instructions.\n"
        "# NEVER commit .env to git (learners should keep this local).\n"
        "#\n"
        "# WARNING: COOLIFY_API_TOKEN grants full access to the Coolify\n"
        "# instance. If you don't trust participants, generate a dedicated\n"
        "# token in Coolify Keys & Tokens and replace it below. Revoke\n"
        "# after the course ends.\n"
        "\n"
        f"COOLIFY_URL={env['COOLIFY_URL']}\n"
        f"COOLIFY_API_TOKEN={env['COOLIFY_API_TOKEN']}\n"
        f"DEPLOY_DOMAIN={domain}\n"
        "\n"
        "# === SET YOUR LEARNER ID BELOW ===\n"
        f"# Your apps will be deployed at: {{project-name}}-{{DEPLOY_USER}}.{domain}\n"
        f"# Example: blog-alice.{domain}, todo-alice.{domain}\n"
        "# Only letters, digits, and hyphens. Max 20 characters recommended.\n"
        "DEPLOY_USER=learnerXX\n"
    )
    Path(output_path).write_text(content, encoding="utf-8")
    return {
        "status": "ok",
        "path": output_path,
        "domain": domain,
        "learners_can_deploy_at": f"{{project}}-{{DEPLOY_USER}}.{domain}",
    }


def training_reap(
    user: Optional[str],
    all_users: bool,
    dry_run: bool,
    confirm: Optional[str],
) -> dict:
    """Delete Coolify projects gse-<user> or all gse-* (course cleanup).

    Does NOT touch the `gse` solo project. Requires --confirm matching either
    the user name (for --user) or the literal "all" (for --all), unless
    --dry-run is set.
    """
    if not user and not all_users:
        return {
            "status": "error",
            "error": "specify --user <name> or --all",
        }
    if user and all_users:
        return {
            "status": "error",
            "error": "cannot combine --user and --all",
        }
    env = parse_env()
    coolify_url = env.get("COOLIFY_URL")
    coolify_token = env.get("COOLIFY_API_TOKEN")
    if not coolify_url or not coolify_token:
        return {
            "status": "error",
            "error": "missing COOLIFY_URL or COOLIFY_API_TOKEN in .env",
        }
    client = CoolifyClient(coolify_url, coolify_token)
    try:
        projects = client.list_projects()
    except CoolifyError as e:
        return {"status": "error", "error": str(e)}

    if all_users:
        targets = [p for p in projects if p.name.startswith("gse-")]
        expected_confirm = "all"
    else:
        targets = [p for p in projects if p.name == f"gse-{user}"]
        expected_confirm = user

    target_names = [p.name for p in targets]

    if dry_run or confirm != expected_confirm:
        return {
            "status": "dry-run",
            "would_delete_projects": target_names,
            "hint": (
                f"re-run with --confirm {expected_confirm} to actually delete"
                if not dry_run
                else "dry-run: nothing deleted"
            ),
        }

    deleted: list[str] = []
    errors: list[str] = []
    for p in targets:
        try:
            client.delete_project(p.uuid)
            deleted.append(p.name)
        except CoolifyError as e:
            errors.append(f"{p.name}: {e}")

    # Sync state: drop applications[] entries whose deploy_user matches
    state = load_state()
    apps = state.get("applications", [])
    if all_users:
        state["applications"] = [a for a in apps if not a.get("deploy_user")]
    else:
        state["applications"] = [
            a for a in apps if a.get("deploy_user") != user
        ]
    save_state(state)

    return {
        "status": "ok" if not errors else "partial",
        "deleted_projects": deleted,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Human-friendly state rendering
# ---------------------------------------------------------------------------


def _render_state_human(state: dict) -> str:
    """Format deploy state as a human-readable ASCII report (consumed by `state --human`)."""
    lines = []
    lines.append("GSE-One Deployment State")
    lines.append("=" * 56)
    lines.append("")
    lines.append("Phases completed:")
    for name, ts in state.get("phases_completed", {}).items():
        mark = "✓" if ts else "·"
        lines.append(f"  {mark} {name:<18} {ts or '(not completed)'}")
    lines.append("")
    server = state.get("server", {})
    if server.get("name"):
        lines.append(f"Server: {server['name']} ({server.get('type')}, {server.get('datacenter')})")
        lines.append(f"  IPv4: {server.get('ipv4')}")
    coolify = state.get("coolify", {})
    if coolify.get("url"):
        lines.append(f"Coolify: {coolify['url']}")
    domain = state.get("domain", {})
    if domain.get("base"):
        lines.append(f"Domain:  {domain['base']} ({domain.get('registrar', 'manual')})")
    lines.append("")
    apps = state.get("applications", [])
    if apps:
        lines.append(f"Applications ({len(apps)}):")
        lines.append(f"  {'#':<3} {'Name':<30} {'Status':<10} {'Type':<10} {'URL'}")
        for i, a in enumerate(apps, start=1):
            lines.append(
                f"  {i:<3} {a.get('name', '')[:30]:<30} "
                f"{a.get('status', '')[:10]:<10} "
                f"{a.get('type', '')[:10]:<10} "
                f"{a.get('url', '')}"
            )
    else:
        lines.append("Applications: (none)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------


def _cmd_init_state(args: argparse.Namespace) -> None:
    state = init_state()
    _json_out({"status": "ok", "path": str(STATE_PATH), "version": state["version"]})


def _cmd_state(args: argparse.Namespace) -> None:
    state = load_state()
    if args.human:
        print(_render_state_human(state))
    else:
        _json_out(state)


def _cmd_detect(args: argparse.Namespace) -> None:
    _json_out(detect_situation())


def _cmd_subdomain(args: argparse.Namespace) -> None:
    result = build_subdomain(args.project, args.user or None, args.domain)
    _json_out(result)
    if not result.get("ok"):
        sys.exit(2)


def _cmd_env_get(args: argparse.Namespace) -> None:
    env = parse_env()
    value = env.get(args.key)
    _json_out({"key": args.key, "value": value, "present": args.key in env})


def _cmd_env_set(args: argparse.Namespace) -> None:
    set_env(args.key, args.value)
    _json_out({"status": "ok", "key": args.key})


def _cmd_env_delete(args: argparse.Namespace) -> None:
    delete_env(args.key)
    _json_out({"status": "ok", "key": args.key})


def _cmd_record_phase(args: argparse.Namespace) -> None:
    result = record_phase(args.phase)
    _json_out(result)
    if result.get("status") != "ok":
        sys.exit(2)


def _cmd_record_server(args: argparse.Namespace) -> None:
    result = record_server(
        name=args.name,
        ipv4=args.ipv4,
        id_=args.id,
        type_=args.type,
        datacenter=args.datacenter,
    )
    _json_out(result)
    if result.get("status") != "ok":
        sys.exit(2)


def _cmd_record_coolify(args: argparse.Namespace) -> None:
    result = record_coolify(args.url, args.version or "")
    _json_out(result)
    if result.get("status") != "ok":
        sys.exit(2)


def _cmd_record_domain(args: argparse.Namespace) -> None:
    result = record_domain(args.base, args.registrar or "")
    _json_out(result)
    if result.get("status") != "ok":
        sys.exit(2)


def _cmd_record_role(args: argparse.Namespace) -> None:
    result = record_role(args.role)
    _json_out(result)
    if result.get("status") != "ok":
        sys.exit(2)


def _cmd_record_cdn(args: argparse.Namespace) -> None:
    result = record_cdn(
        provider=args.provider,
        enabled=args.enabled,
        bot_protection=args.bot_protection,
    )
    _json_out(result)
    if result.get("status") != "ok":
        sys.exit(2)


def _cmd_wait_dns(args: argparse.Namespace) -> None:
    result = wait_dns(
        domain=args.domain,
        expected_ip=args.expected_ip,
        timeout_seconds=args.timeout or 600,
    )
    _json_out(result)
    if result.get("status") != "resolved":
        sys.exit(4)


def _cmd_deploy_app(args: argparse.Namespace) -> None:
    result = deploy_app(
        name=args.name,
        project_name=args.project_name,
        deploy_user=args.deploy_user or "",
        subdomain=args.subdomain,
        github_repo=args.github_repo,
        branch=args.branch,
        type_=args.type,
        port=args.port,
        memory=args.memory or "512m",
        cpu=args.cpu or "0.5",
        health_timeout=args.health_timeout or 120,
    )
    _json_out(result)
    if result.get("status") not in ("healthy",):
        sys.exit(3)


def _cmd_app_status(args: argparse.Namespace) -> None:
    _json_out(app_status(args.name))


def _cmd_destroy(args: argparse.Namespace) -> None:
    if not args.dry_run and not args.confirm:
        _err("--confirm is required unless --dry-run is set")
    _json_out(destroy(args.confirm, dry_run=args.dry_run))


def _cmd_preflight(args: argparse.Namespace) -> None:
    result = preflight(args.path)
    _json_out(result)
    if result["overall"] == "errors":
        sys.exit(5)


def _cmd_training_init(args: argparse.Namespace) -> None:
    result = training_init(args.output or ".env.training")
    _json_out(result)
    if result.get("status") != "ok":
        sys.exit(2)


def _cmd_training_reap(args: argparse.Namespace) -> None:
    _json_out(
        training_reap(
            user=args.user,
            all_users=args.all,
            dry_run=args.dry_run,
            confirm=args.confirm,
        )
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deploy.py",
        description="GSE-One /gse:deploy orchestrator (see design §5.18)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-state", help="Create .gse/deploy.json if missing")

    p_state = sub.add_parser("state", help="Print state")
    p_state.add_argument("--human", action="store_true", help="Pretty-print")

    sub.add_parser("detect", help="Determine starting phase and mode")

    p_sub = sub.add_parser("subdomain", help="Compute sanitized subdomain")
    p_sub.add_argument("--project", required=True, help="Project directory path")
    p_sub.add_argument("--user", default="", help="DEPLOY_USER (training mode)")
    p_sub.add_argument("--domain", required=True, help="DEPLOY_DOMAIN")

    p_eg = sub.add_parser("env-get", help="Read .env key")
    p_eg.add_argument("key")

    p_es = sub.add_parser("env-set", help="Write .env key=value")
    p_es.add_argument("key")
    p_es.add_argument("value")

    p_ed = sub.add_parser("env-delete", help="Delete .env key")
    p_ed.add_argument("key")

    p_rp = sub.add_parser("record-phase", help="Mark a phase completed")
    p_rp.add_argument("phase", choices=sorted(PHASE_NAMES))

    p_rs = sub.add_parser("record-server", help="Update server block")
    p_rs.add_argument("--name", required=True)
    p_rs.add_argument("--ipv4", required=True)
    p_rs.add_argument("--id", type=int, default=None)
    p_rs.add_argument("--type", required=True)
    p_rs.add_argument("--datacenter", required=True)

    p_rc = sub.add_parser("record-coolify", help="Update coolify block")
    p_rc.add_argument("--url", required=True)
    p_rc.add_argument("--version", default="")

    p_rd = sub.add_parser("record-domain", help="Update domain block")
    p_rd.add_argument("--base", required=True)
    p_rd.add_argument("--registrar", default="")

    p_rrole = sub.add_parser(
        "record-role",
        help="Persist user role in state (solo | instructor | learner)",
    )
    p_rrole.add_argument("role", choices=sorted(VALID_ROLES))

    p_rcdn = sub.add_parser("record-cdn", help="Update cdn block")
    p_rcdn.add_argument("--provider", required=True, help="e.g. cloudflare | none")
    p_rcdn.add_argument("--enabled", action="store_true", help="CDN active")
    p_rcdn.add_argument(
        "--bot-protection",
        action="store_true",
        help="Bot Fight Mode / equivalent enabled",
    )

    p_wd = sub.add_parser(
        "wait-dns", help="Poll dig until domain resolves to expected IP"
    )
    p_wd.add_argument("--domain", required=True)
    p_wd.add_argument("--expected-ip", required=True)
    p_wd.add_argument(
        "--timeout", type=int, default=600, help="Timeout seconds (default 600)"
    )

    p_da = sub.add_parser("deploy-app", help="End-to-end Phase 6 deploy")
    p_da.add_argument("--name", required=True)
    p_da.add_argument("--project-name", required=True)
    p_da.add_argument("--deploy-user", default="")
    p_da.add_argument("--subdomain", required=True)
    p_da.add_argument("--github-repo", required=True)
    p_da.add_argument("--branch", required=True)
    p_da.add_argument(
        "--type",
        required=True,
        choices=["streamlit", "python", "node", "static", "custom"],
    )
    p_da.add_argument("--port", type=int, required=True)
    p_da.add_argument("--memory", default="512m")
    p_da.add_argument("--cpu", default="0.5")
    p_da.add_argument("--health-timeout", type=int, default=120)

    p_as = sub.add_parser("app-status", help="Live health check of a recorded app")
    p_as.add_argument("name")

    p_destroy = sub.add_parser(
        "destroy",
        help="Wipe Coolify apps + gse-* projects + Hetzner server. Requires --confirm unless --dry-run.",
    )
    p_destroy.add_argument(
        "--confirm",
        default="",
        help="Must match the server name from state (double-check safeguard). Required unless --dry-run.",
    )
    p_destroy.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be deleted and exit without touching anything.",
    )

    p_pf = sub.add_parser(
        "preflight",
        help="Run Phase 6 preflight: detect type + structured checks",
    )
    p_pf.add_argument(
        "--path", default=".", help="Project directory (default: cwd)"
    )

    p_ti = sub.add_parser(
        "training-init",
        help="Generate .env.training from instructor's .env (training mode)",
    )
    p_ti.add_argument(
        "--output",
        default=".env.training",
        help="Output path (default: .env.training)",
    )

    p_tr = sub.add_parser(
        "training-reap",
        help="Delete Coolify gse-<user> or all gse-* projects (course cleanup)",
    )
    p_tr.add_argument("--user", default=None, help="Delete only gse-<name>")
    p_tr.add_argument(
        "--all", action="store_true", help="Delete all gse-* projects"
    )
    p_tr.add_argument("--dry-run", action="store_true", help="List, don't delete")
    p_tr.add_argument(
        "--confirm",
        default=None,
        help="Required unless --dry-run: must match <name> or 'all'",
    )

    return parser


_COMMANDS = {
    "init-state": _cmd_init_state,
    "state": _cmd_state,
    "detect": _cmd_detect,
    "subdomain": _cmd_subdomain,
    "env-get": _cmd_env_get,
    "env-set": _cmd_env_set,
    "env-delete": _cmd_env_delete,
    "record-phase": _cmd_record_phase,
    "record-server": _cmd_record_server,
    "record-coolify": _cmd_record_coolify,
    "record-domain": _cmd_record_domain,
    "record-role": _cmd_record_role,
    "record-cdn": _cmd_record_cdn,
    "wait-dns": _cmd_wait_dns,
    "preflight": _cmd_preflight,
    "deploy-app": _cmd_deploy_app,
    "app-status": _cmd_app_status,
    "destroy": _cmd_destroy,
    "training-init": _cmd_training_init,
    "training-reap": _cmd_training_reap,
}


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    fn = _COMMANDS.get(args.command)
    if fn is None:
        parser.error(f"unknown command: {args.command}")
    fn(args)


if __name__ == "__main__":
    main()
