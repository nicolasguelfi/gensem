#!/usr/bin/env python3
"""Unit tests for plugin/tools/deploy.py.

Covers deterministic functions (sanitization, detection, state, preflight,
env parsing). Coolify API, SSH, and hcloud are not tested here (require
live infrastructure). See TESTING.md for the manual E2E checklist.

Run: python3 -m unittest discover tests
Or:  python3 gse_generate.py --verify   (runs verify + tests)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Make plugin/tools/ importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugin" / "tools"))

import deploy  # noqa: E402


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------


class SanitizeComponentTests(unittest.TestCase):
    def test_lowercase(self):
        self.assertEqual(deploy.sanitize_component("Hello"), "hello")

    def test_replace_special_chars(self):
        self.assertEqual(
            deploy.sanitize_component("my_cool.app!"), "my-cool-app"
        )

    def test_collapse_hyphens(self):
        self.assertEqual(deploy.sanitize_component("a---b"), "a-b")

    def test_trim_leading_trailing_hyphens(self):
        self.assertEqual(deploy.sanitize_component("-abc-"), "abc")

    def test_truncate_to_30(self):
        s = deploy.sanitize_component("a" * 50)
        self.assertLessEqual(len(s), 30)

    def test_empty_input(self):
        self.assertEqual(deploy.sanitize_component(""), "")

    def test_only_special_chars(self):
        self.assertEqual(deploy.sanitize_component("@@@!!!"), "")

    def test_digits_preserved(self):
        self.assertEqual(deploy.sanitize_component("app123"), "app123")

    def test_custom_max_len(self):
        s = deploy.sanitize_component("abcdefghij", max_len=5)
        self.assertEqual(s, "abcde")


# ---------------------------------------------------------------------------
# Subdomain building
# ---------------------------------------------------------------------------


class BuildSubdomainTests(unittest.TestCase):
    def test_solo_mode(self):
        r = deploy.build_subdomain("/tmp/my-blog", None, "example.com")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["subdomain"], "my-blog.example.com")
        self.assertEqual(r["deploy_user"], "")

    def test_training_mode(self):
        r = deploy.build_subdomain(
            "/tmp/todo-app", "alice", "training.example.com"
        )
        self.assertEqual(r["status"], "ok")
        self.assertEqual(
            r["subdomain"], "todo-app-alice.training.example.com"
        )
        self.assertEqual(r["deploy_user"], "alice")

    def test_project_sanitization(self):
        r = deploy.build_subdomain("/tmp/My_Cool_App", None, "example.com")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["project_name"], "my-cool-app")

    def test_user_sanitization(self):
        r = deploy.build_subdomain("/tmp/app", "Alice", "example.com")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["deploy_user"], "alice")

    def test_empty_project_fails(self):
        r = deploy.build_subdomain("/tmp/@@@", None, "example.com")
        self.assertEqual(r["status"], "error")
        self.assertIn("error", r)

    def test_empty_user_with_value_fails(self):
        r = deploy.build_subdomain("/tmp/app", "@@@", "example.com")
        self.assertEqual(r["status"], "error")

    def test_url_format(self):
        r = deploy.build_subdomain("/tmp/app", None, "example.com")
        self.assertEqual(r["url"], "https://app.example.com")


# ---------------------------------------------------------------------------
# Type detection
# ---------------------------------------------------------------------------


class DetectTypeTests(unittest.TestCase):
    def _mkdir(self, files: dict) -> Path:
        d = Path(tempfile.mkdtemp())
        for name, content in files.items():
            p = d / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        self.addCleanup(lambda: shutil.rmtree(d))
        return d

    def test_streamlit_via_pyproject(self):
        d = self._mkdir(
            {"pyproject.toml": "[project]\ndependencies = ['streamlit>=1.30']"}
        )
        t, _ = deploy._detect_type(d)
        self.assertEqual(t, "streamlit")

    def test_streamlit_via_requirements(self):
        d = self._mkdir({"requirements.txt": "streamlit==1.30.0\nnumpy\n"})
        t, _ = deploy._detect_type(d)
        self.assertEqual(t, "streamlit")

    def test_python_no_streamlit_pyproject(self):
        d = self._mkdir(
            {"pyproject.toml": "[project]\ndependencies = ['flask']"}
        )
        t, _ = deploy._detect_type(d)
        self.assertEqual(t, "python")

    def test_python_no_streamlit_requirements(self):
        d = self._mkdir({"requirements.txt": "flask==3.0\n"})
        t, _ = deploy._detect_type(d)
        self.assertEqual(t, "python")

    def test_node(self):
        d = self._mkdir({"package.json": '{"name":"myapp"}'})
        t, _ = deploy._detect_type(d)
        self.assertEqual(t, "node")

    def test_static(self):
        d = self._mkdir({"index.html": "<html>hi</html>"})
        t, _ = deploy._detect_type(d)
        self.assertEqual(t, "static")

    def test_custom_fallback(self):
        d = self._mkdir({"README.md": "just a readme"})
        t, _ = deploy._detect_type(d)
        self.assertEqual(t, "custom")

    def test_streamlit_takes_precedence_over_package_json(self):
        # A mixed repo with both Python+streamlit and a package.json
        # should be detected as streamlit (more specific).
        d = self._mkdir(
            {
                "pyproject.toml": "[project]\ndependencies = ['streamlit']",
                "package.json": '{"name":"tooling"}',
            }
        )
        t, _ = deploy._detect_type(d)
        self.assertEqual(t, "streamlit")


# ---------------------------------------------------------------------------
# Preflight aggregation
# ---------------------------------------------------------------------------


class PreflightAggregationTests(unittest.TestCase):
    def _mkproject(self, files: dict, with_git: bool = True) -> Path:
        d = Path(tempfile.mkdtemp())
        for name, content in files.items():
            p = d / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        if with_git:
            subprocess.run(["git", "init", "-q"], cwd=d, check=True)
            subprocess.run(
                ["git", "-c", "user.name=test", "-c", "user.email=t@t",
                 "add", "-A"],
                cwd=d, check=True,
            )
            subprocess.run(
                ["git", "-c", "user.name=test", "-c", "user.email=t@t",
                 "commit", "-q", "-m", "init"],
                cwd=d, check=True,
            )
        self.addCleanup(lambda: shutil.rmtree(d))
        return d

    def test_static_ok_with_github_remote(self):
        d = self._mkproject({"index.html": "<html/>"})
        subprocess.run(
            ["git", "remote", "add", "origin",
             "https://github.com/test/repo.git"],
            cwd=d, check=True,
        )
        r = deploy.preflight(str(d))
        self.assertEqual(r["type"], "static")
        self.assertEqual(r["port"], 80)
        self.assertEqual(r["overall"], "ok")

    def test_errors_block_custom_without_dockerfile(self):
        d = self._mkproject({"README.md": "x"})
        r = deploy.preflight(str(d))
        self.assertEqual(r["type"], "custom")
        self.assertEqual(r["overall"], "errors")

    def test_warnings_on_missing_remote(self):
        d = self._mkproject({"index.html": "<html/>"})
        r = deploy.preflight(str(d))
        # No remote → warning ; should roll up to "warnings"
        self.assertEqual(r["overall"], "warnings")
        names = [c["name"] for c in r["checks"]]
        self.assertIn("git_remote", names)

    def test_streamlit_config_missing_warning(self):
        d = self._mkproject(
            {
                "pyproject.toml": "[project]\ndependencies=['streamlit']",
                "app.py": "import streamlit as st",
            }
        )
        r = deploy.preflight(str(d))
        self.assertEqual(r["type"], "streamlit")
        names = [c["name"] for c in r["checks"]]
        self.assertIn("streamlit_config_exists", names)

    def test_no_git_repo_is_error(self):
        d = self._mkproject({"index.html": "<html/>"}, with_git=False)
        r = deploy.preflight(str(d))
        self.assertEqual(r["overall"], "errors")


# ---------------------------------------------------------------------------
# .env parsing
# ---------------------------------------------------------------------------


class EnvFileTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self.env = self.dir / ".env"

    def test_empty_file(self):
        self.assertEqual(deploy.parse_env(self.env), {})

    def test_set_and_get(self):
        deploy.set_env("FOO", "bar", self.env)
        self.assertEqual(deploy.parse_env(self.env).get("FOO"), "bar")

    def test_set_replaces(self):
        deploy.set_env("FOO", "old", self.env)
        deploy.set_env("FOO", "new", self.env)
        self.assertEqual(deploy.parse_env(self.env).get("FOO"), "new")

    def test_preserve_comments_and_other_keys(self):
        self.env.write_text(
            "# Header comment\nFOO=old\n# Between\nBAR=keep\n"
        )
        deploy.set_env("FOO", "new", self.env)
        text = self.env.read_text()
        self.assertIn("# Header comment", text)
        self.assertIn("# Between", text)
        self.assertIn("FOO=new", text)
        self.assertIn("BAR=keep", text)

    def test_delete(self):
        self.env.write_text("A=1\nB=2\n")
        deploy.delete_env("A", self.env)
        text = self.env.read_text()
        self.assertNotIn("A=", text)
        self.assertIn("B=2", text)

    def test_delete_missing_is_noop(self):
        # Should not raise
        deploy.delete_env("NOPE", self.env)

    def test_quoted_values_stripped(self):
        self.env.write_text('QUOTED="with spaces"\n')
        self.assertEqual(
            deploy.parse_env(self.env).get("QUOTED"), "with spaces"
        )


# ---------------------------------------------------------------------------
# State I/O
# ---------------------------------------------------------------------------


class StateTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_empty_state_shape(self):
        s = deploy._empty_state()
        for key in ("version", "plugin", "phases_completed", "server",
                    "coolify", "domain", "cdn", "applications"):
            self.assertIn(key, s)
        self.assertEqual(s["version"], deploy.STATE_VERSION)
        self.assertEqual(s["applications"], [])

    def test_init_state_creates_file(self):
        deploy.init_state()
        self.assertTrue((self.dir / ".gse" / "deploy.json").exists())

    def test_load_save_roundtrip(self):
        deploy.init_state()
        s = deploy.load_state()
        s["applications"].append({"name": "test"})
        deploy.save_state(s)
        s2 = deploy.load_state()
        self.assertEqual(
            [a["name"] for a in s2["applications"]], ["test"]
        )

    def test_load_missing_returns_empty(self):
        # No .gse/ yet
        s = deploy.load_state()
        self.assertEqual(s["applications"], [])


# ---------------------------------------------------------------------------
# Cost hints
# ---------------------------------------------------------------------------


class CostHintTests(unittest.TestCase):
    def test_known_cax21(self):
        h = deploy._cost_hint("cax21")
        self.assertIn("10.99", h)

    def test_known_case_insensitive(self):
        self.assertIn("6.49", deploy._cost_hint("CAX11"))

    def test_unknown_type(self):
        self.assertIn("unknown", deploy._cost_hint("nonexistent"))

    def test_empty(self):
        self.assertIn("unknown", deploy._cost_hint(""))


class RecordRoleTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_user_role_in_empty_state(self):
        s = deploy._empty_state()
        self.assertIn("user_role", s)
        self.assertEqual(s["user_role"], "")

    def test_record_solo(self):
        r = deploy.record_role("solo")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["role"], "solo")
        self.assertEqual(deploy.load_state()["user_role"], "solo")

    def test_record_instructor(self):
        deploy.record_role("instructor")
        self.assertEqual(deploy.load_state()["user_role"], "instructor")

    def test_record_learner(self):
        deploy.record_role("learner")
        self.assertEqual(deploy.load_state()["user_role"], "learner")

    def test_invalid_role_rejected(self):
        r = deploy.record_role("guest")
        self.assertEqual(r["status"], "error")
        self.assertIn("invalid role", r["error"])


class RecordPhaseContractTests(unittest.TestCase):
    """v0.55.0 unified status-wrapped contract for record_phase."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_record_phase_happy_path(self):
        r = deploy.record_phase("setup")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["phase"], "setup")
        self.assertTrue(r["completed_at"])  # non-empty ISO timestamp
        self.assertTrue(deploy.load_state()["phases_completed"]["setup"])

    def test_record_phase_unknown_returns_error(self):
        r = deploy.record_phase("bogus-phase")
        self.assertEqual(r["status"], "error")
        self.assertIn("unknown phase", r["error"])


class RecordServerContractTests(unittest.TestCase):
    """v0.55.0 unified status-wrapped contract for record_server."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_record_server_happy_path(self):
        r = deploy.record_server("srv-01", "1.2.3.4", 42, "cax21", "fsn1")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["server"]["name"], "srv-01")
        self.assertEqual(r["server"]["ipv4"], "1.2.3.4")
        self.assertEqual(deploy.load_state()["server"]["id"], 42)

    def test_record_server_missing_name_rejected(self):
        r = deploy.record_server("", "1.2.3.4", 42, "cax21", "fsn1")
        self.assertEqual(r["status"], "error")
        self.assertIn("name", r["error"])


class RecordCoolifyContractTests(unittest.TestCase):
    """v0.55.0 unified status-wrapped contract for record_coolify."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_record_coolify_happy_path(self):
        r = deploy.record_coolify("https://coolify.example.com", "4.0.0")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["coolify"]["url"], "https://coolify.example.com")
        self.assertEqual(r["coolify"]["version"], "4.0.0")

    def test_record_coolify_empty_url_rejected(self):
        r = deploy.record_coolify("", "4.0.0")
        self.assertEqual(r["status"], "error")
        self.assertIn("url", r["error"])


class RecordDomainContractTests(unittest.TestCase):
    """v0.55.0 unified status-wrapped contract for record_domain."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_record_domain_happy_path(self):
        r = deploy.record_domain("example.com", "ovh")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["domain"]["base"], "example.com")
        self.assertEqual(r["domain"]["registrar"], "ovh")

    def test_record_domain_empty_base_rejected(self):
        r = deploy.record_domain("", "ovh")
        self.assertEqual(r["status"], "error")
        self.assertIn("base", r["error"])


class RecordCdnContractTests(unittest.TestCase):
    """v0.55.0 unified status-wrapped contract for record_cdn."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_record_cdn_happy_path(self):
        r = deploy.record_cdn("cloudflare", True, bot_protection=True)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["cdn"]["provider"], "cloudflare")
        self.assertTrue(r["cdn"]["enabled"])
        self.assertTrue(r["cdn"]["bot_protection"])

    def test_record_cdn_enabled_without_provider_rejected(self):
        r = deploy.record_cdn("", True)
        self.assertEqual(r["status"], "error")
        self.assertIn("provider", r["error"])

    def test_record_cdn_disabled_allows_empty_provider(self):
        # Disabling the CDN is valid even without a provider (no bot protection either).
        r = deploy.record_cdn("", False)
        self.assertEqual(r["status"], "ok")
        self.assertFalse(r["cdn"]["enabled"])


# ---------------------------------------------------------------------------
# Application source routing + server_uuid resolution (v0.64.0 — U4)
# ---------------------------------------------------------------------------


class _FakeCoolifyClient:
    """Duck-typed stand-in for CoolifyClient (only list_servers is used)."""

    def __init__(self, servers=None, error=False):
        self._servers = servers or []
        self._error = error

    def list_servers(self):
        if self._error:
            raise deploy.CoolifyError(500, "boom")
        return self._servers


class SelectAppSourceTests(unittest.TestCase):
    def test_public_when_no_github_app_uuid(self):
        self.assertEqual(deploy._select_app_source({}), ("public", None))

    def test_private_when_github_app_uuid_set(self):
        env = {"COOLIFY_GITHUB_APP_UUID": "abc123"}
        self.assertEqual(
            deploy._select_app_source(env), ("private-github-app", "abc123")
        )

    def test_blank_uuid_falls_back_to_public(self):
        env = {"COOLIFY_GITHUB_APP_UUID": "   "}
        self.assertEqual(deploy._select_app_source(env), ("public", None))


class ResolveServerUuidTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(lambda: os.chdir(self._prev_cwd))

    def test_env_value_takes_precedence(self):
        # Even a broken API must not be consulted when .env has the value.
        r = deploy._resolve_server_uuid(
            _FakeCoolifyClient(error=True), {"SERVER_UUID": "srv-1"},
            required=True,
        )
        self.assertEqual(r, {"status": "ok", "server_uuid": "srv-1"})

    def test_sole_server_resolved_and_persisted(self):
        client = _FakeCoolifyClient(servers=[{"uuid": "srv-9", "name": "m"}])
        r = deploy._resolve_server_uuid(client, {}, required=True)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["server_uuid"], "srv-9")
        self.assertEqual(deploy.parse_env().get("SERVER_UUID"), "srv-9")

    def test_multiple_servers_required_is_error(self):
        client = _FakeCoolifyClient(
            servers=[{"uuid": "a", "name": "s1"}, {"uuid": "b", "name": "s2"}]
        )
        r = deploy._resolve_server_uuid(client, {}, required=True)
        self.assertEqual(r["status"], "error")
        self.assertIn("SERVER_UUID", r["error"])
        self.assertIn("s1=a", r["error"])

    def test_multiple_servers_optional_returns_none(self):
        client = _FakeCoolifyClient(servers=[{"uuid": "a"}, {"uuid": "b"}])
        r = deploy._resolve_server_uuid(client, {}, required=False)
        self.assertEqual(r, {"status": "ok", "server_uuid": None})

    def test_api_error_optional_returns_none(self):
        r = deploy._resolve_server_uuid(
            _FakeCoolifyClient(error=True), {}, required=False
        )
        self.assertEqual(r, {"status": "ok", "server_uuid": None})

    def test_api_error_required_is_error(self):
        r = deploy._resolve_server_uuid(
            _FakeCoolifyClient(error=True), {}, required=True
        )
        self.assertEqual(r["status"], "error")


class TrainingInitOptionalKeysTests(unittest.TestCase):
    BASE = (
        "COOLIFY_URL=https://coolify.example.com\n"
        "COOLIFY_API_TOKEN=tok\n"
        "DEPLOY_DOMAIN=example.com\n"
    )

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(lambda: os.chdir(self._prev_cwd))

    def test_handout_without_optional_keys(self):
        Path(".env").write_text(self.BASE, encoding="utf-8")
        r = deploy.training_init(".env.training")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["optional_keys"], [])
        text = Path(".env.training").read_text(encoding="utf-8")
        self.assertNotIn("SERVER_UUID", text)
        self.assertNotIn("COOLIFY_GITHUB_APP_UUID", text)

    def test_handout_includes_optional_keys_when_present(self):
        Path(".env").write_text(
            self.BASE + "SERVER_UUID=srv-1\nCOOLIFY_GITHUB_APP_UUID=gh-2\n",
            encoding="utf-8",
        )
        r = deploy.training_init(".env.training")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(
            sorted(r["optional_keys"]),
            ["COOLIFY_GITHUB_APP_UUID", "SERVER_UUID"],
        )
        text = Path(".env.training").read_text(encoding="utf-8")
        self.assertIn("SERVER_UUID=srv-1", text)
        self.assertIn("COOLIFY_GITHUB_APP_UUID=gh-2", text)
        # Hetzner/SSH secrets must stay instructor-only.
        self.assertNotIn("HETZNER_API_TOKEN", text)


# ---------------------------------------------------------------------------
# Runtime logs of the user's own app (v0.91.0 — /gse:deploy --logs)
# ---------------------------------------------------------------------------

import contextlib  # noqa: E402
import io  # noqa: E402
import urllib.error  # noqa: E402
from unittest import mock  # noqa: E402

import coolify_client  # noqa: E402

SECRET = "tok-SECRET-1234567890"


class _FakeLogsClient:
    """Duck-typed CoolifyClient for app_logs(); records every call."""

    instances: list = []

    def __init__(self, base_url, token, timeout=None):
        self.calls = []
        self.projects = {}       # name -> uuid
        self.env_apps = {}       # project uuid -> [CoolifyApplication]
        self.logs = {}           # app uuid -> text
        self.error = None        # CoolifyError raised by get_application_logs
        _FakeLogsClient.instances.append(self)
        cfg = _FakeLogsClient.config
        self.projects.update(cfg.get("projects", {}))
        self.env_apps.update(cfg.get("env_apps", {}))
        self.logs.update(cfg.get("logs", {}))
        self.error = cfg.get("error")

    def find_project_by_name(self, name):
        self.calls.append(("find_project_by_name", name))
        uuid = self.projects.get(name)
        return coolify_client.CoolifyProject(uuid=uuid, name=name) if uuid else None

    def list_environment_applications(self, project_uuid, env_name):
        self.calls.append(("list_environment_applications", project_uuid, env_name))
        return self.env_apps.get(project_uuid, [])

    def list_applications(self):  # must never be used by app_logs
        raise AssertionError("app_logs must not enumerate all applications")

    def get_application_logs(self, uuid, lines=100):
        self.calls.append(("get_application_logs", uuid, lines))
        if self.error:
            raise self.error
        return self.logs.get(uuid, "")


class AppLogsTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.root))
        self.dir = self.root / "reading-tracker"
        self.dir.mkdir()
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(lambda: os.chdir(self._prev_cwd))
        _FakeLogsClient.instances = []
        _FakeLogsClient.config = {}
        patcher = mock.patch.object(deploy, "CoolifyClient", _FakeLogsClient)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _env(self, user="alice"):
        text = (
            "COOLIFY_URL=https://coolify.example.com\n"
            f"COOLIFY_API_TOKEN={SECRET}\n"
            "DEPLOY_DOMAIN=example.com\n"
        )
        if user:
            text += f"DEPLOY_USER={user}\n"
        Path(".env").write_text(text, encoding="utf-8")

    def _state(self, apps):
        state = deploy._empty_state()
        state["applications"] = apps
        deploy.save_state(state)

    @staticmethod
    def _entry(name, user, uuid):
        return {
            "name": name, "deploy_user": user,
            "url": f"https://{name}.example.com",
            "coolify": {"app_uuid": uuid},
        }

    def _client(self):
        return _FakeLogsClient.instances[-1]

    def test_training_resolves_own_app_from_state(self):
        self._env("alice")
        self._state([
            self._entry("reading-tracker-bob", "bob", "u-bob"),
            self._entry("reading-tracker-alice", "alice", "u-alice"),
        ])
        _FakeLogsClient.config = {"logs": {"u-alice": "line1\nline2\n"}}
        r = deploy.app_logs(lines=50)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["name"], "reading-tracker-alice")
        self.assertEqual(r["logs"], "line1\nline2\n")
        self.assertIn(("get_application_logs", "u-alice", 50), self._client().calls)
        # Bob's app is never touched.
        self.assertFalse(any("u-bob" in str(c) for c in self._client().calls))

    def test_training_refuses_other_learner_name(self):
        self._env("alice")
        self._state([self._entry("reading-tracker-bob", "bob", "u-bob")])
        r = deploy.app_logs(name="reading-tracker-bob")
        self.assertEqual(r["status"], "error")
        self.assertIn("only read apps", r["error"])
        self.assertEqual(self._client().calls, [])

    def test_training_ignores_other_users_state_entries(self):
        # Only bob's app is in state: alice must not get it, and the API
        # fallback looks only inside gse-alice.
        self._env("alice")
        self._state([self._entry("reading-tracker-bob", "bob", "u-bob")])
        _FakeLogsClient.config = {"projects": {"gse-bob": "p-bob"}}
        r = deploy.app_logs()
        self.assertEqual(r["status"], "not_deployed")
        self.assertIn("gse-alice", r["error"])
        self.assertEqual(
            self._client().calls, [("find_project_by_name", "gse-alice")]
        )

    def test_training_fallback_to_own_coolify_project(self):
        self._env("alice")
        _FakeLogsClient.config = {
            "projects": {"gse-alice": "p-alice"},
            "env_apps": {"p-alice": [
                coolify_client.CoolifyApplication(
                    uuid="u-alice", name="reading-tracker-alice")
            ]},
            "logs": {"u-alice": "started\n"},
        }
        r = deploy.app_logs()
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["app_uuid"], "u-alice")
        self.assertIn(
            ("list_environment_applications", "p-alice", "production"),
            self._client().calls,
        )

    def test_solo_resolution(self):
        self._env(user=None)
        self._state([
            self._entry("reading-tracker", "", "u-solo"),
            self._entry("reading-tracker-bob", "bob", "u-bob"),
        ])
        _FakeLogsClient.config = {"logs": {"u-solo": "ok\n"}}
        r = deploy.app_logs()
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["app_uuid"], "u-solo")

    def test_not_deployed_when_app_absent(self):
        self._env("alice")
        _FakeLogsClient.config = {
            "projects": {"gse-alice": "p-alice"}, "env_apps": {"p-alice": []},
        }
        r = deploy.app_logs()
        self.assertEqual(r["status"], "not_deployed")
        self.assertIn("reading-tracker-alice", r["error"])

    def test_404_no_running_container(self):
        self._env("alice")
        self._state([self._entry("reading-tracker-alice", "alice", "u-alice")])
        _FakeLogsClient.config = {"error": deploy.CoolifyError(
            404, "Not Found", '{"message":"No running container found."}')}
        r = deploy.app_logs()
        self.assertEqual(r["status"], "not_running")
        self.assertEqual(r["http_status"], 404)

    def test_404_application_not_found(self):
        self._env("alice")
        self._state([self._entry("reading-tracker-alice", "alice", "u-alice")])
        _FakeLogsClient.config = {"error": deploy.CoolifyError(
            404, "Not Found", '{"message":"Application not found."}')}
        r = deploy.app_logs()
        self.assertEqual(r["status"], "not_found")
        self.assertIn("/gse:deploy", r["error"])

    def test_401_token_rejected(self):
        self._env("alice")
        self._state([self._entry("reading-tracker-alice", "alice", "u-alice")])
        _FakeLogsClient.config = {
            "error": deploy.CoolifyError(401, "Unauthorized", SECRET)}
        r = deploy.app_logs()
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["http_status"], 401)
        self.assertIn("instructor", r["error"])
        self.assertNotIn(SECRET, json.dumps(r))

    def test_403_missing_read_sensitive(self):
        self._env(user=None)
        self._state([self._entry("reading-tracker", "", "u-solo")])
        _FakeLogsClient.config = {
            "error": deploy.CoolifyError(403, "Forbidden")}
        r = deploy.app_logs()
        self.assertEqual(r["http_status"], 403)
        self.assertIn("read:sensitive", r["error"])

    def test_lines_bounds(self):
        self._env("alice")
        for bad in (0, -5, deploy.MAX_LOG_LINES + 1):
            self.assertEqual(deploy.app_logs(lines=bad)["status"], "error")

    def test_missing_credentials(self):
        Path(".env").write_text("DEPLOY_USER=alice\n", encoding="utf-8")
        r = deploy.app_logs()
        self.assertEqual(r["status"], "error")
        self.assertIn("COOLIFY_API_TOKEN", r["error"])

    def test_token_redacted_from_log_text(self):
        self._env("alice")
        self._state([self._entry("reading-tracker-alice", "alice", "u-alice")])
        _FakeLogsClient.config = {
            "logs": {"u-alice": f"env dump: TOKEN={SECRET}\n"}}
        r = deploy.app_logs()
        self.assertNotIn(SECRET, r["logs"])
        self.assertIn("***", r["logs"])

    def test_cli_never_prints_token(self):
        self._env("alice")
        self._state([self._entry("reading-tracker-alice", "alice", "u-alice")])
        _FakeLogsClient.config = {"logs": {"u-alice": f"a\n{SECRET}\nb\n"}}
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            deploy.main(["logs", "--lines", "20"])
        self.assertIn("Last 20 log lines of reading-tracker-alice", out.getvalue())
        self.assertNotIn(SECRET, out.getvalue() + err.getvalue())
        self.assertIn(("get_application_logs", "u-alice", 20), self._client().calls)

    def test_cli_error_exit_code_and_no_token(self):
        self._env("alice")
        self._state([self._entry("reading-tracker-alice", "alice", "u-alice")])
        _FakeLogsClient.config = {
            "error": deploy.CoolifyError(401, "Unauthorized", SECRET)}
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                deploy.main(["logs", "--json"])
        self.assertEqual(cm.exception.code, 6)
        self.assertNotIn(SECRET, out.getvalue() + err.getvalue())
        self.assertEqual(json.loads(out.getvalue())["http_status"], 401)


class _FakeResponse:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class CoolifyClientLogsTests(unittest.TestCase):
    def test_get_application_logs_url_and_lines(self):
        seen = {}

        def fake_urlopen(req, timeout=None):
            seen["url"] = req.full_url
            seen["method"] = req.get_method()
            seen["auth"] = req.get_header("Authorization")
            return _FakeResponse({"logs": "hello\nworld"})

        client = coolify_client.CoolifyClient("https://c.example.com/", SECRET)
        with mock.patch.object(
            coolify_client.urllib.request, "urlopen", fake_urlopen
        ):
            text = client.get_application_logs("app-1", 42)
        self.assertEqual(text, "hello\nworld")
        self.assertEqual(seen["method"], "GET")
        self.assertEqual(
            seen["url"], "https://c.example.com/api/v1/applications/app-1/logs?lines=42"
        )
        self.assertEqual(seen["auth"], f"Bearer {SECRET}")

    def test_get_application_logs_401_raises_without_token(self):
        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 401, "Unauthorized", {}, io.BytesIO(b"{}")
            )

        client = coolify_client.CoolifyClient("https://c.example.com", SECRET)
        with mock.patch.object(
            coolify_client.urllib.request, "urlopen", fake_urlopen
        ):
            with self.assertRaises(coolify_client.CoolifyError) as cm:
                client.get_application_logs("app-1")
        self.assertEqual(cm.exception.status, 401)
        self.assertNotIn(SECRET, str(cm.exception))

    def test_list_environment_applications(self):
        seen = {}

        def fake_urlopen(req, timeout=None):
            seen["url"] = req.full_url
            return _FakeResponse({"name": "production", "applications": [
                {"uuid": "u1", "name": "reading-tracker-alice"}]})

        client = coolify_client.CoolifyClient("https://c.example.com", SECRET)
        with mock.patch.object(
            coolify_client.urllib.request, "urlopen", fake_urlopen
        ):
            apps = client.list_environment_applications("p1", "production")
        self.assertEqual(seen["url"], "https://c.example.com/api/v1/projects/p1/production")
        self.assertEqual([(a.uuid, a.name) for a in apps], [("u1", "reading-tracker-alice")])



# ---------------------------------------------------------------------------
# Instructor-path rehearsal fixes (v0.91.0 — F11 secrets on argv, F14 IPv6,
# F5/F6 Coolify host validation + API-disabled detection)
# ---------------------------------------------------------------------------


class _ChdirTmp(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(lambda: os.chdir(self._prev_cwd))


class _PipeStdin(io.StringIO):
    def isatty(self):
        return False


class EnvSetStdinTests(_ChdirTmp):
    def _run(self, argv, stdin_text=""):
        out = io.StringIO()
        with mock.patch.object(sys, "stdin", _PipeStdin(stdin_text)), \
                contextlib.redirect_stdout(out):
            deploy.main(argv)
        return out.getvalue()

    def test_stdin_value_written_and_never_echoed(self):
        out = self._run(["env-set", "COOLIFY_API_TOKEN", "--stdin"], SECRET + "\n")
        self.assertEqual(deploy.parse_env().get("COOLIFY_API_TOKEN"), SECRET)
        self.assertNotIn(SECRET, out)
        self.assertEqual(json.loads(out), {"status": "ok", "key": "COOLIFY_API_TOKEN"})

    def test_positional_value_still_supported(self):
        self._run(["env-set", "DEPLOY_DOMAIN", "example.com"])
        self.assertEqual(deploy.parse_env().get("DEPLOY_DOMAIN"), "example.com")

    def test_empty_stdin_rejected(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            self._run(["env-set", "HETZNER_API_TOKEN", "--stdin"], "\n")
        self.assertNotIn("HETZNER_API_TOKEN", deploy.parse_env())

    def test_value_and_stdin_together_rejected(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            self._run(["env-set", "K", "v", "--stdin"], "w\n")

    def test_missing_value_rejected(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            self._run(["env-set", "K"])


class RecordServerIpv6Tests(_ChdirTmp):
    def test_ipv6_recorded(self):
        r = deploy.record_server(
            "srv", "1.2.3.4", 7, "cax31", "fsn1", ipv6="2001:db8::/64"
        )
        self.assertEqual(r["server"]["ipv6"], "2001:db8::/64")
        self.assertEqual(deploy.load_state()["server"]["ipv6"], "2001:db8::/64")

    def test_ipv6_defaults_empty_and_in_empty_state(self):
        self.assertEqual(deploy._empty_state()["server"]["ipv6"], "")
        r = deploy.record_server("srv", "1.2.3.4", None, "cax21", "fsn1")
        self.assertEqual(r["server"]["ipv6"], "")

    def test_cli_flag(self):
        with contextlib.redirect_stdout(io.StringIO()):
            deploy.main([
                "record-server", "--name", "s", "--ipv4", "1.2.3.4",
                "--type", "cax21", "--datacenter", "fsn1",
                "--ipv6", "2001:db8::/64",
            ])
        self.assertEqual(deploy.load_state()["server"]["ipv6"], "2001:db8::/64")


class _FakeValidateClient:
    config: dict = {}

    def __init__(self, base_url, token, timeout=None):
        self.cfg = _FakeValidateClient.config
        self.calls = []
        _FakeValidateClient.last = self

    def get_version(self):
        if self.cfg.get("version_error"):
            raise self.cfg["version_error"]
        return "4.7.6"

    def list_servers(self):
        return self.cfg.get("servers", [{"uuid": "srv-1", "name": "localhost"}])

    def validate_server(self, uuid, install=False):
        self.calls.append(("validate", uuid, install))
        if self.cfg.get("validate_error"):
            raise self.cfg["validate_error"]
        return {"message": "Validation started."}

    def get_server(self, uuid):
        self.calls.append(("get_server", uuid))
        seq = self.cfg.setdefault("reachable_seq", [True])
        return {"uuid": uuid, "is_reachable": seq.pop(0) if seq else False}


class ValidateServerTests(_ChdirTmp):
    def setUp(self):
        super().setUp()
        Path(".env").write_text(
            f"COOLIFY_URL=http://203.0.113.10:8000\nCOOLIFY_API_TOKEN={SECRET}\n"
        )
        _FakeValidateClient.config = {}
        for target, value in (
            ("CoolifyClient", _FakeValidateClient),
        ):
            patcher = mock.patch.object(deploy, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        sleeper = mock.patch.object(deploy.time, "sleep", lambda s: None)
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def test_happy_path_validates_and_persists_server_uuid(self):
        _FakeValidateClient.config = {"reachable_seq": [False, True]}
        r = deploy.validate_server(timeout_seconds=60, poll_interval=0)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["coolify_version"], "4.7.6")
        self.assertEqual(r["server_uuid"], "srv-1")
        self.assertEqual(deploy.parse_env().get("SERVER_UUID"), "srv-1")
        self.assertIn(("validate", "srv-1", False), _FakeValidateClient.last.calls)
        self.assertNotIn(SECRET, json.dumps(r))

    def test_api_disabled_403_explained(self):
        _FakeValidateClient.config = {
            "version_error": deploy.CoolifyError(403, "Forbidden")
        }
        r = deploy.validate_server(timeout_seconds=0)
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["http_status"], 403)
        self.assertIn("API access", r["error"])

    def test_unreachable_times_out_with_ssh_hint(self):
        _FakeValidateClient.config = {"reachable_seq": []}
        r = deploy.validate_server(timeout_seconds=0, poll_interval=0)
        self.assertEqual(r["status"], "timeout")
        self.assertIn("prohibit-password", r["error"])
        self.assertIn("fail2ban", r["error"])

    def test_settings_is_reachable_older_shape(self):
        self.assertTrue(deploy._server_reachable({"settings": {"is_reachable": True}}))
        self.assertFalse(deploy._server_reachable({"settings": {"is_reachable": False}}))

    def test_missing_env_is_error(self):
        Path(".env").write_text("")
        r = deploy.validate_server(timeout_seconds=0)
        self.assertEqual(r["status"], "error")


class CoolifyClientValidateTests(unittest.TestCase):
    def test_validate_posts_install_flag(self):
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append((req.get_method(), req.full_url, req.data))
            return _FakeResponse({"message": "Validation started."})

        client = coolify_client.CoolifyClient("http://c.example.com:8000", SECRET)
        with mock.patch.object(coolify_client.urllib.request, "urlopen", fake_urlopen):
            client.validate_server("srv-1")
        self.assertEqual(seen[0][0], "POST")
        self.assertEqual(seen[0][1], "http://c.example.com:8000/api/v1/servers/srv-1/validate")
        self.assertEqual(json.loads(seen[0][2]), {"install": False})

    def test_validate_falls_back_to_get_on_405(self):
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append(req.get_method())
            if req.get_method() == "POST":
                raise urllib.error.HTTPError(
                    req.full_url, 405, "Method Not Allowed", {}, io.BytesIO(b"{}")
                )
            return _FakeResponse({"message": "ok"})

        client = coolify_client.CoolifyClient("http://c.example.com:8000", SECRET)
        with mock.patch.object(coolify_client.urllib.request, "urlopen", fake_urlopen):
            client.validate_server("srv-1")
        self.assertEqual(seen, ["POST", "GET"])

    def test_get_version_plain_text(self):
        class _Raw(_FakeResponse):
            def __init__(self):
                self._raw = b"4.7.6"

        client = coolify_client.CoolifyClient("http://c.example.com:8000", SECRET)
        with mock.patch.object(
            coolify_client.urllib.request, "urlopen", lambda req, timeout=None: _Raw()
        ):
            self.assertEqual(client.get_version(), "4.7.6")


class CoolifyPayloadFormTests(unittest.TestCase):
    """Coolify 4.7 validation forms (rehearsal F23): public repo URL,
    Dockerfile path starting with '/', readable 422 details."""

    def setUp(self):
        import coolify_client
        self.cc = coolify_client

    def test_slug_expanded_to_github_https_url(self):
        f = self.cc.public_repository_url
        self.assertEqual(f("user/repo"), "https://github.com/user/repo")
        self.assertEqual(f(" user/repo.git "), "https://github.com/user/repo")

    def test_urls_and_ssh_forms_unchanged(self):
        f = self.cc.public_repository_url
        for v in ("https://github.com/u/r", "git@github.com:u/r.git", "ssh://git@h/u/r"):
            self.assertEqual(f(v), v)

    def test_public_app_payload_uses_url_and_absolute_dockerfile(self):
        sent = {}
        client = self.cc.CoolifyClient("https://c.example", "t")

        def fake_post(endpoint, payload, name):
            sent.update(payload, endpoint=endpoint)
            return None
        client._post_application = fake_post
        client.create_application("p", "production", "app", "user/repo",
                                  "main", "3000", "https://a.example", server_uuid="s")
        self.assertEqual(sent["endpoint"], "/applications/public")
        self.assertEqual(sent["git_repository"], "https://github.com/user/repo")
        self.assertEqual(sent["dockerfile_location"], "/Dockerfile")

    def test_error_details_lists_rejected_fields(self):
        body = json.dumps({"message": "Validation failed.", "errors": {
            "git_repository": ["must start with https://"],
            "dockerfile_location": ["format is invalid."]}})
        d = self.cc.error_details(body)
        self.assertIn("git_repository: must start with https://", d)
        self.assertIn("dockerfile_location: format is invalid.", d)

    def test_error_details_fallbacks(self):
        self.assertIsNone(self.cc.error_details(None))
        self.assertEqual(self.cc.error_details('{"message": "Not found."}'), "Not found.")
        self.assertEqual(self.cc.error_details("plain text"), "plain text")


class DeployAppAdoptsOrphanTests(unittest.TestCase):
    """A same-name app already in the user's own environment but missing from
    local state (previous run failed before saving) is redeployed, not
    duplicated (rehearsal F24)."""

    def _run(self, env_apps):
        from types import SimpleNamespace as NS
        from unittest import mock
        calls = {"create": 0, "deploy": []}

        class Fake:
            def __init__(self, *a, **k):
                pass
            def ensure_project(self, *a, **k):
                return NS(uuid="proj")
            def ensure_environment(self, *a, **k):
                return NS(uuid="env", name="production")
            def list_environment_applications(self, project_uuid, env_name):
                return [NS(name=n, uuid=u) for n, u in env_apps]
            def trigger_deploy(self, uuid, force=False):
                calls["deploy"].append((uuid, force))
            def create_application(self, **k):
                calls["create"] += 1
                return NS(uuid="new")
            def list_servers(self):
                return [NS(uuid="srv")]

        saved = {}
        with mock.patch.object(deploy, "CoolifyClient", Fake), \
             mock.patch.object(deploy, "parse_env", return_value={
                 "COOLIFY_URL": "https://c", "COOLIFY_API_TOKEN": "t",
                 "SERVER_UUID": "srv"}), \
             mock.patch.object(deploy, "load_state", return_value={"applications": []}), \
             mock.patch.object(deploy, "save_state", side_effect=lambda st: saved.update(st)), \
             mock.patch.object(deploy, "poll_health", return_value={"status": "healthy", "http_code": 200}):
            res = deploy.deploy_app(
                name="app-alice", project_name="app", deploy_user="alice",
                subdomain="app-alice.example.org", github_repo="u/r",
                branch="main", type_="static", port=80)
        return res, calls

    def test_orphan_is_adopted_and_redeployed(self):
        res, calls = self._run([("other", "x"), ("app-alice", "orphan")])
        self.assertEqual(res["status"], "healthy")
        self.assertEqual(res["app_uuid"], "orphan")
        self.assertFalse(res["created"])
        self.assertEqual(calls["create"], 0)
        self.assertEqual(calls["deploy"], [("orphan", True)])

    def test_no_orphan_creates(self):
        res, calls = self._run([("other", "x")])
        self.assertTrue(res["created"])
        self.assertEqual(calls["create"], 1)


class TrainingReapEmptiesProjectTests(unittest.TestCase):
    """Coolify refuses to delete a non-empty project and deletes apps
    asynchronously: reap deletes the apps, then retries the project
    (rehearsal F26)."""

    def test_apps_deleted_then_project_retried(self):
        from types import SimpleNamespace as NS
        from unittest import mock
        log = []

        class Fake:
            def __init__(self, *a, **k):
                self.tries = 0
            def list_projects(self):
                return [NS(name="gse-alice", uuid="p1"), NS(name="gse", uuid="solo")]
            def list_environments(self, uuid):
                return [NS(name="production", uuid="e1")]
            def list_environment_applications(self, uuid, env):
                return [NS(name="app-alice", uuid="a1")]
            def delete_application(self, uuid):
                log.append(("app", uuid))
            def delete_project(self, uuid):
                self.tries += 1
                if self.tries < 3:
                    raise deploy.CoolifyError(400, "Bad Request",
                        '{"message": "Project has resources, so it cannot be deleted."}')
                log.append(("project", uuid))

        with mock.patch.object(deploy, "CoolifyClient", Fake), \
             mock.patch.object(deploy, "parse_env", return_value={
                 "COOLIFY_URL": "https://c", "COOLIFY_API_TOKEN": "t"}), \
             mock.patch.object(deploy, "load_state", return_value={"applications": []}), \
             mock.patch.object(deploy, "save_state"), \
             mock.patch.object(deploy.time, "sleep"):
            res = deploy.training_reap(user="alice", all_users=False,
                                       dry_run=False, confirm="alice")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["deleted_projects"], ["gse-alice"])
        self.assertEqual(res["deleted_applications"], ["gse-alice/app-alice"])
        self.assertEqual(log, [("app", "a1"), ("project", "p1")])

    def test_non_400_error_reported_with_reason(self):
        from types import SimpleNamespace as NS
        from unittest import mock

        class Fake:
            def __init__(self, *a, **k):
                pass
            def list_projects(self):
                return [NS(name="gse-bob", uuid="p2")]
            def list_environments(self, uuid):
                return []
            def delete_project(self, uuid):
                raise deploy.CoolifyError(403, "Forbidden", '{"message": "Missing permission."}')

        with mock.patch.object(deploy, "CoolifyClient", Fake), \
             mock.patch.object(deploy, "parse_env", return_value={
                 "COOLIFY_URL": "https://c", "COOLIFY_API_TOKEN": "t"}), \
             mock.patch.object(deploy, "load_state", return_value={"applications": []}), \
             mock.patch.object(deploy, "save_state"):
            res = deploy.training_reap(user="bob", all_users=False,
                                       dry_run=False, confirm="bob")
        self.assertEqual(res["status"], "partial")
        self.assertIn("Missing permission.", res["errors"][0])


if __name__ == "__main__":
    unittest.main()
