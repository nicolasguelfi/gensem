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


if __name__ == "__main__":
    unittest.main()
