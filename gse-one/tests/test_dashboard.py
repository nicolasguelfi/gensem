#!/usr/bin/env python3
"""Unit tests for plugin/tools/dashboard.py (v0.81.0).

Regression guard for the pre-first-sprint baseline state: just after /gse:hug a
project has no active sprint. The canonical encoding is `current_sprint: 0`
(see src/templates/status.yaml + go.md Adopt Step 5 — Set baseline), but a
hand-authored or migrated status.yaml may carry an explicit `current_sprint:
null`. dashboard.py must coerce null -> 0 and render, NOT crash on the
f"sprint-{n:02d}" format (the v0.80.0 TypeError, reported from a Codex sandbox
run, which corrupted status.yaml with an invented `current_phase: initialization`).

Run: python3 -m unittest discover tests
Or:  python3 gse_generate.py --verify   (runs verify + tests)
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "plugin" / "tools" / "dashboard.py"


def _run_dashboard(project_dir):
    """Run dashboard.py with cwd=project_dir, offline, to a temp output file.
    Returns (returncode, stdout, stderr, output_exists, error_marker_exists)."""
    out = Path(project_dir) / "out.html"
    proc = subprocess.run(
        [sys.executable, str(DASHBOARD), "--no-cdn", "--output", str(out)],
        cwd=str(project_dir), capture_output=True, text=True,
    )
    error_marker = Path(project_dir) / ".gse" / ".dashboard-error.yaml"
    return (proc.returncode, proc.stdout, proc.stderr,
            out.exists() and out.stat().st_size > 0, error_marker.exists())


def _make_project(tmp, status_body):
    gse = Path(tmp) / ".gse"
    gse.mkdir(parents=True)
    (gse / "status.yaml").write_text(status_body, encoding="utf-8")
    return tmp


class TestDashboardPreSprintBaseline(unittest.TestCase):

    def test_null_current_sprint_does_not_crash(self):
        """current_sprint: null (pre-sprint baseline) must render, not TypeError."""
        with tempfile.TemporaryDirectory() as tmp:
            _make_project(tmp, 'gse_version: "0.81.0"\n'
                               'current_sprint: null\n'
                               'current_phase: null\n'
                               'last_activity: hug\n')
            rc, out, err, produced, error_marker = _run_dashboard(tmp)
            self.assertEqual(rc, 0, f"dashboard exited {rc}; stderr:\n{err}")
            self.assertNotIn("Traceback", err)
            self.assertTrue(produced, "dashboard HTML was not produced")
            self.assertFalse(error_marker,
                             ".dashboard-error.yaml written — the null state was "
                             "treated as a failure instead of the pre-sprint baseline")

    def test_zero_current_sprint_renders(self):
        """current_sprint: 0 (canonical baseline) renders cleanly."""
        with tempfile.TemporaryDirectory() as tmp:
            _make_project(tmp, 'gse_version: "0.81.0"\n'
                               'current_sprint: 0\n'
                               'current_phase: LC01\n'
                               'last_activity: hug\n')
            rc, out, err, produced, error_marker = _run_dashboard(tmp)
            self.assertEqual(rc, 0, f"dashboard exited {rc}; stderr:\n{err}")
            self.assertTrue(produced)
            self.assertFalse(error_marker)

    def test_active_sprint_still_renders(self):
        """A normal active sprint (current_sprint: 3) is unaffected by the fix."""
        with tempfile.TemporaryDirectory() as tmp:
            _make_project(tmp, 'gse_version: "0.81.0"\n'
                               'current_sprint: 3\n'
                               'current_phase: LC02\n'
                               'last_activity: produce\n')
            rc, out, err, produced, error_marker = _run_dashboard(tmp)
            self.assertEqual(rc, 0, f"dashboard exited {rc}; stderr:\n{err}")
            self.assertTrue(produced)
            self.assertFalse(error_marker)


class TestParseYamlInlineComments(unittest.TestCase):
    """Regression (v0.90.1): `key: value   # comment` must yield `value`.

    Seen in a classroom rehearsal: config.yaml lines such as
    `protect_main: true   # block direct commits` were read as the string
    "true   # block direct commits", so booleans and numbers were not coerced.
    """

    @classmethod
    def setUpClass(cls):
        import importlib.util
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("gse_dashboard", DASHBOARD)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def _parse(self, text):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x.yaml"
            f.write_text(text, encoding="utf-8")
            return self.mod.parse_yaml_simple(f)

    def test_trailing_comments_are_dropped(self):
        r = self._parse(
            "git:\n"
            "  protect_main: true          # block direct commits\n"
            "  max_points: 10 # budget\n"
            "mode: lightweight  # comment\n"
            "section:   # parent with a comment\n"
            "  child: ok\n"
        )
        self.assertIs(r["git.protect_main"], True)
        self.assertEqual(r["git.max_points"], 10)
        self.assertEqual(r["mode"], "lightweight")
        self.assertEqual(r["section.child"], "ok")

    def test_hash_inside_quotes_or_words_is_kept(self):
        r = self._parse('title: "Sprint #1 # not a comment"\nref: issue#42\n')
        self.assertEqual(r["title"], "Sprint #1 # not a comment")
        self.assertEqual(r["ref"], "issue#42")


if __name__ == "__main__":
    unittest.main()
