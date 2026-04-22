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
        self.assertTrue(r["ok"])
        self.assertEqual(r["subdomain"], "my-blog.example.com")
        self.assertEqual(r["deploy_user"], "")

    def test_training_mode(self):
        r = deploy.build_subdomain(
            "/tmp/todo-app", "alice", "training.example.com"
        )
        self.assertTrue(r["ok"])
        self.assertEqual(
            r["subdomain"], "todo-app-alice.training.example.com"
        )
        self.assertEqual(r["deploy_user"], "alice")

    def test_project_sanitization(self):
        r = deploy.build_subdomain("/tmp/My_Cool_App", None, "example.com")
        self.assertTrue(r["ok"])
        self.assertEqual(r["project_name"], "my-cool-app")

    def test_user_sanitization(self):
        r = deploy.build_subdomain("/tmp/app", "Alice", "example.com")
        self.assertTrue(r["ok"])
        self.assertEqual(r["deploy_user"], "alice")

    def test_empty_project_fails(self):
        r = deploy.build_subdomain("/tmp/@@@", None, "example.com")
        self.assertFalse(r["ok"])
        self.assertIn("error", r)

    def test_empty_user_with_value_fails(self):
        r = deploy.build_subdomain("/tmp/app", "@@@", "example.com")
        self.assertFalse(r["ok"])

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
        self.assertIn("8.49", h)

    def test_known_case_insensitive(self):
        self.assertIn("4.49", deploy._cost_hint("CAX11"))

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


if __name__ == "__main__":
    unittest.main()
