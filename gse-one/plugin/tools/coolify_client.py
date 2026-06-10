#!/usr/bin/env python3
# @gse-tool coolify_client 1.0
"""
Coolify API v1 HTTP client for GSE-One /gse:deploy.

Uses only Python standard library (urllib). Designed to be imported by
`deploy.py` and used as a Python library — not invoked directly as a CLI.

Coolify API reference: https://coolify.io/docs/api-reference
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CoolifyError(Exception):
    """Raised on any non-2xx response from the Coolify API."""

    def __init__(self, status: int, message: str, body: Optional[str] = None):
        self.status = status
        self.message = message
        self.body = body
        super().__init__(f"[{status}] {message}")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CoolifyProject:
    uuid: str
    name: str
    description: str = ""
    environments: list[dict] = field(default_factory=list)


@dataclass
class CoolifyEnvironment:
    uuid: str
    name: str
    project_uuid: str = ""


@dataclass
class CoolifyApplication:
    uuid: str
    name: str
    status: str = ""
    fqdn: str = ""
    git_repository: str = ""
    git_branch: str = ""
    ports_exposes: str = ""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class CoolifyClient:
    """Thin wrapper around the Coolify REST API.

    Pinned to Coolify v4 API v1 (last verified: 2026-04-20).

    If Coolify ships a breaking change (v2 API, renamed field, etc.), this
    client will fail visibly with a 404 or an unexpected response shape.
    When that happens, please open a PR at
    https://github.com/nicolasguelfi/gensem updating the relevant method and
    the "last verified" date above. See README.md → Deployment → Coolify
    compatibility for the workflow.
    """

    API_VERSION = "v1"
    DEFAULT_TIMEOUT = 30  # seconds per HTTP request
    MAX_RETRIES = 3  # retries on 5xx responses
    RETRY_DELAYS = [1.0, 2.0, 4.0]  # exponential backoff

    def __init__(self, base_url: str, token: str, timeout: Optional[int] = None):
        """Initialize the client.

        Args:
            base_url: Coolify dashboard URL (e.g. https://coolify.example.com)
            token: API token from Coolify Keys & Tokens
            timeout: Optional per-request timeout in seconds
        """
        if not base_url:
            raise ValueError("base_url is required")
        if not token:
            raise ValueError("token is required")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout or self.DEFAULT_TIMEOUT

    # -------------------------------------------------------------------
    # Low-level HTTP
    # -------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[dict] = None,
        query: Optional[dict] = None,
    ) -> Any:
        """Execute an authenticated HTTP request. Returns parsed JSON or None."""
        url = f"{self.base_url}/api/{self.API_VERSION}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        body_bytes = None
        if json_body is not None:
            body_bytes = json.dumps(json_body).encode("utf-8")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        if body_bytes is not None:
            headers["Content-Type"] = "application/json"

        last_exc: Optional[Exception] = None
        for attempt in range(self.MAX_RETRIES):
            req = urllib.request.Request(
                url, data=body_bytes, headers=headers, method=method
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    if not raw:
                        return None
                    try:
                        return json.loads(raw.decode("utf-8"))
                    except json.JSONDecodeError:
                        return raw.decode("utf-8")
            except urllib.error.HTTPError as e:
                body_text = ""
                try:
                    body_text = e.read().decode("utf-8", errors="replace")
                except Exception:  # noqa: BLE001
                    pass
                if 500 <= e.code < 600 and attempt < self.MAX_RETRIES - 1:
                    # Retry on 5xx
                    time.sleep(self.RETRY_DELAYS[attempt])
                    last_exc = e
                    continue
                raise CoolifyError(e.code, str(e.reason), body_text) from e
            except urllib.error.URLError as e:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAYS[attempt])
                    last_exc = e
                    continue
                raise CoolifyError(0, f"Connection error: {e.reason}") from e
        # If we exhausted retries, re-raise the last exception.
        if last_exc:
            raise CoolifyError(0, f"Exhausted retries: {last_exc}")
        raise CoolifyError(0, "Unknown error")

    # -------------------------------------------------------------------
    # Projects
    # -------------------------------------------------------------------

    def list_projects(self) -> list[CoolifyProject]:
        """Return all Coolify projects."""
        data = self._request("GET", "/projects")
        if not isinstance(data, list):
            return []
        return [self._to_project(d) for d in data]

    def get_project(self, uuid: str) -> CoolifyProject:
        """Return one project by UUID."""
        data = self._request("GET", f"/projects/{uuid}")
        return self._to_project(data)

    def find_project_by_name(self, name: str) -> Optional[CoolifyProject]:
        """Return the first project matching `name`, or None."""
        for p in self.list_projects():
            if p.name == name:
                return p
        return None

    def create_project(self, name: str, description: str = "") -> CoolifyProject:
        """Create a project and return it."""
        data = self._request(
            "POST", "/projects", json_body={"name": name, "description": description}
        )
        # Coolify returns {"uuid": "..."} typically; fetch the full object
        uuid = data.get("uuid") if isinstance(data, dict) else None
        if not uuid:
            raise CoolifyError(0, f"Project creation returned no uuid: {data}")
        return self.get_project(uuid)

    def delete_project(self, uuid: str) -> None:
        """Delete a project by UUID."""
        self._request("DELETE", f"/projects/{uuid}")

    def ensure_project(self, name: str, description: str = "") -> CoolifyProject:
        """Idempotent: return existing project by name, or create it."""
        existing = self.find_project_by_name(name)
        if existing:
            return existing
        return self.create_project(name, description)

    # -------------------------------------------------------------------
    # Environments
    # -------------------------------------------------------------------

    def list_environments(self, project_uuid: str) -> list[CoolifyEnvironment]:
        """Return the environments of a project."""
        proj = self.get_project(project_uuid)
        envs = []
        for e in proj.environments or []:
            envs.append(
                CoolifyEnvironment(
                    uuid=e.get("uuid", ""),
                    name=e.get("name", ""),
                    project_uuid=project_uuid,
                )
            )
        return envs

    def find_environment_by_name(
        self, project_uuid: str, name: str
    ) -> Optional[CoolifyEnvironment]:
        """Return the named environment of a project, or None."""
        for e in self.list_environments(project_uuid):
            if e.name == name:
                return e
        return None

    def create_environment(
        self, project_uuid: str, name: str
    ) -> CoolifyEnvironment:
        """Create an environment within a project and return it."""
        data = self._request(
            "POST",
            f"/projects/{project_uuid}/environments",
            json_body={"name": name},
        )
        uuid = data.get("uuid") if isinstance(data, dict) else None
        if not uuid:
            raise CoolifyError(
                0, f"Environment creation returned no uuid: {data}"
            )
        return CoolifyEnvironment(uuid=uuid, name=name, project_uuid=project_uuid)

    def ensure_environment(
        self, project_uuid: str, name: str
    ) -> CoolifyEnvironment:
        """Idempotent: return existing environment by name, or create it."""
        existing = self.find_environment_by_name(project_uuid, name)
        if existing:
            return existing
        return self.create_environment(project_uuid, name)

    # -------------------------------------------------------------------
    # Servers
    # -------------------------------------------------------------------

    def list_servers(self) -> list[dict]:
        """Return raw server records visible to the token (GET /servers).

        Used to auto-resolve `server_uuid` at application creation (recent
        Coolify versions require it; the private-github-app endpoint always
        does)."""
        data = self._request("GET", "/servers")
        return data if isinstance(data, list) else []

    # -------------------------------------------------------------------
    # Applications
    # -------------------------------------------------------------------

    def list_applications(self) -> list[CoolifyApplication]:
        """Return all applications visible to the token."""
        data = self._request("GET", "/applications")
        if not isinstance(data, list):
            return []
        return [self._to_application(d) for d in data]

    def get_application(self, uuid: str) -> CoolifyApplication:
        """Return one application by UUID."""
        data = self._request("GET", f"/applications/{uuid}")
        return self._to_application(data)

    def find_application_by_name(
        self, name: str
    ) -> Optional[CoolifyApplication]:
        """Return the first application matching `name`, or None."""
        for a in self.list_applications():
            if a.name == name:
                return a
        return None

    def create_application(
        self,
        project_uuid: str,
        environment_name: str,
        name: str,
        git_repository: str,
        git_branch: str,
        ports_exposes: str,
        fqdn: str,
        dockerfile_location: str = "./Dockerfile",
        build_pack: str = "dockerfile",
        server_uuid: Optional[str] = None,
    ) -> CoolifyApplication:
        """Create a public-repository application.

        `server_uuid` is optional for backward compatibility with older
        Coolify versions; recent versions require it (HTTP 422 mentioning
        `server_uuid` otherwise). For private repositories, use
        `create_private_github_app_application` instead.
        """
        payload = self._app_payload(
            project_uuid, environment_name, name, git_repository,
            git_branch, ports_exposes, fqdn, dockerfile_location,
            build_pack, server_uuid,
        )
        return self._post_application("/applications/public", payload, name)

    def create_private_github_app_application(
        self,
        project_uuid: str,
        environment_name: str,
        name: str,
        git_repository: str,
        git_branch: str,
        ports_exposes: str,
        fqdn: str,
        github_app_uuid: str,
        server_uuid: str,
        dockerfile_location: str = "./Dockerfile",
        build_pack: str = "dockerfile",
    ) -> CoolifyApplication:
        """Create an application from a private repository via a GitHub App.

        Requires a Coolify GitHub App source (`github_app_uuid`) installed
        on the repo owner's GitHub account, and an explicit `server_uuid` —
        both are mandatory on this endpoint. `git_repository` uses the
        `owner/repo` form.
        """
        payload = self._app_payload(
            project_uuid, environment_name, name, git_repository,
            git_branch, ports_exposes, fqdn, dockerfile_location,
            build_pack, server_uuid,
        )
        payload["github_app_uuid"] = github_app_uuid
        return self._post_application(
            "/applications/private-github-app", payload, name
        )

    @staticmethod
    def _app_payload(
        project_uuid: str,
        environment_name: str,
        name: str,
        git_repository: str,
        git_branch: str,
        ports_exposes: str,
        fqdn: str,
        dockerfile_location: str,
        build_pack: str,
        server_uuid: Optional[str],
    ) -> dict:
        """Shared payload for the application-creation endpoints."""
        payload = {
            "project_uuid": project_uuid,
            "environment_name": environment_name,
            "name": name,
            "git_repository": git_repository,
            "git_branch": git_branch,
            "build_pack": build_pack,
            "ports_exposes": ports_exposes,
            "domains": fqdn,
            "dockerfile_location": dockerfile_location,
        }
        if server_uuid:
            payload["server_uuid"] = server_uuid
        return payload

    def _post_application(
        self, endpoint: str, payload: dict, name: str
    ) -> CoolifyApplication:
        """POST an application-creation payload and normalize the response."""
        data = self._request("POST", endpoint, json_body=payload)
        uuid = data.get("uuid") if isinstance(data, dict) else None
        if not uuid:
            raise CoolifyError(
                0, f"Application creation returned no uuid: {data}"
            )
        app = self._to_application(data)
        if not app.name:
            app.name = name
        return app

    def update_application(self, uuid: str, **fields: Any) -> CoolifyApplication:
        """PATCH application fields and return the updated application."""
        self._request("PATCH", f"/applications/{uuid}", json_body=fields)
        return self.get_application(uuid)

    def delete_application(self, uuid: str) -> None:
        """Delete an application by UUID."""
        self._request("DELETE", f"/applications/{uuid}")

    # -------------------------------------------------------------------
    # Deploy / lifecycle
    # -------------------------------------------------------------------

    def start_app(self, uuid: str) -> dict:
        """Trigger a full rebuild (pull git, rebuild Docker, install deps)."""
        return self._request("POST", f"/applications/{uuid}/start") or {}

    def stop_app(self, uuid: str) -> dict:
        """Stop a running application by UUID."""
        return self._request("POST", f"/applications/{uuid}/stop") or {}

    def restart_app(self, uuid: str) -> dict:
        """Reuse existing container (no code update). Prefer start_app for updates."""
        return self._request("POST", f"/applications/{uuid}/restart") or {}

    def trigger_deploy(self, uuid: str, force: bool = False) -> dict:
        """GET /deploy?uuid=...&force=true — forces a rebuild even on the same commit."""
        query = {"uuid": uuid}
        if force:
            query["force"] = "true"
        return self._request("GET", "/deploy", query=query) or {}

    def get_deployment_status(self, uuid: str) -> dict:
        """Return the status payload of a deployment by UUID."""
        app = self.get_application(uuid)
        return {"uuid": uuid, "status": app.status, "fqdn": app.fqdn}

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _to_project(data: Any) -> CoolifyProject:
        if not isinstance(data, dict):
            return CoolifyProject(uuid="", name="")
        return CoolifyProject(
            uuid=data.get("uuid", ""),
            name=data.get("name", ""),
            description=data.get("description", "") or "",
            environments=data.get("environments", []) or [],
        )

    @staticmethod
    def _to_application(data: Any) -> CoolifyApplication:
        if not isinstance(data, dict):
            return CoolifyApplication(uuid="", name="")
        return CoolifyApplication(
            uuid=data.get("uuid", ""),
            name=data.get("name", ""),
            status=data.get("status", "") or "",
            fqdn=data.get("fqdn", "") or data.get("domains", "") or "",
            git_repository=data.get("git_repository", "") or "",
            git_branch=data.get("git_branch", "") or "",
            ports_exposes=str(data.get("ports_exposes", "") or ""),
        )


if __name__ == "__main__":  # pragma: no cover
    # This module is a library, not a CLI. Print a usage hint.
    import sys
    sys.stderr.write(
        "coolify_client is a library, not a CLI. Import CoolifyClient from "
        "deploy.py or your own scripts.\n"
    )
    sys.exit(1)
