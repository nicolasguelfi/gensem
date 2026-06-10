#!/usr/bin/env python3
"""Unit tests for plugin/tools/counters.py (v0.66.0 — backlog M2+AI3).

Covers the deterministic integrity-counter helper: whitelist enforcement,
comment-preserving line writes, counters_last_write stamping, and the
`health` staleness backstop.

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

import counters  # noqa: E402

SAMPLE = """\
current_sprint: 1
consecutive_acceptances: 0             # primary counter — triggers pushback at threshold
pushback_dismissed: 0                  # times user chose "Everything looks good"
fix_attempts_on_current_symptom: 2     # triggers devil-advocate escalation at threshold
counters_last_write: ""                # ISO 8601 — last integrity-counter write by counters.py
activity_history:
  - activity: /gse:produce
    completed_at: "2026-06-01T10:00:00Z"
    sprint: 1
  - activity: /gse:review
    completed_at: "2026-06-02T10:00:00Z"
    sprint: 1
review_findings_open: 0
"""


class _ChdirMixin(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.dir, ignore_errors=True))
        self._prev_cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(lambda: os.chdir(self._prev_cwd))

    def write_status(self, content: str = SAMPLE):
        Path(".gse").mkdir(exist_ok=True)
        Path(".gse/status.yaml").write_text(content, encoding="utf-8")


class GetCounterTests(_ChdirMixin):
    def test_get_reads_value(self):
        self.write_status()
        r = counters.get_counter("fix_attempts_on_current_symptom")
        self.assertEqual(r, {
            "status": "ok",
            "name": "fix_attempts_on_current_symptom",
            "value": 2,
        })

    def test_unknown_counter_rejected(self):
        self.write_status()
        r = counters.get_counter("sessions_without_progress")
        self.assertEqual(r["status"], "error")
        self.assertIn("unknown counter", r["error"])

    def test_missing_file_is_error(self):
        r = counters.get_counter("consecutive_acceptances")
        self.assertEqual(r["status"], "error")

    def test_missing_field_is_error(self):
        self.write_status("current_sprint: 1\n")
        r = counters.get_counter("consecutive_acceptances")
        self.assertEqual(r["status"], "error")
        self.assertIn("not found", r["error"])


class IncrResetTests(_ChdirMixin):
    def test_incr_increments_and_stamps(self):
        self.write_status()
        r = counters.incr_counter("consecutive_acceptances")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["value"], 1)
        text = Path(".gse/status.yaml").read_text(encoding="utf-8")
        self.assertIn("consecutive_acceptances: 1", text)
        # Comment on the counter line preserved
        self.assertIn("# primary counter — triggers pushback", text)
        # counters_last_write stamped (no longer the empty default)
        self.assertNotIn('counters_last_write: ""', text)

    def test_incr_twice(self):
        self.write_status()
        counters.incr_counter("pushback_dismissed")
        r = counters.incr_counter("pushback_dismissed")
        self.assertEqual(r["value"], 2)

    def test_reset_to_zero(self):
        self.write_status()
        r = counters.reset_counter("fix_attempts_on_current_symptom")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["value"], 0)
        text = Path(".gse/status.yaml").read_text(encoding="utf-8")
        self.assertIn("fix_attempts_on_current_symptom: 0", text)

    def test_other_fields_untouched(self):
        self.write_status()
        counters.incr_counter("consecutive_acceptances")
        text = Path(".gse/status.yaml").read_text(encoding="utf-8")
        self.assertIn("current_sprint: 1", text)
        self.assertIn("review_findings_open: 0", text)
        self.assertIn('completed_at: "2026-06-01T10:00:00Z"', text)

    def test_missing_last_write_field_appended(self):
        # Pre-v0.66 status.yaml without counters_last_write
        self.write_status(
            "consecutive_acceptances: 0\nactivity_history: []\n"
        )
        r = counters.incr_counter("consecutive_acceptances")
        self.assertEqual(r["status"], "ok")
        text = Path(".gse/status.yaml").read_text(encoding="utf-8")
        self.assertIn("counters_last_write:", text)

    def test_set_unknown_counter_rejected(self):
        self.write_status()
        r = counters.set_counter("review_findings_open", 9)
        self.assertEqual(r["status"], "error")


class HealthBackstopTests(_ChdirMixin):
    def test_never_written_counts_all_transitions(self):
        self.write_status()  # empty last_write, 2 history entries
        r = counters.counters_health()
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["transitions_since_last_write"], 2)
        self.assertFalse(r["stale"])
        self.assertIsNone(r["last_write"])

    def test_fresh_write_resets_transitions(self):
        self.write_status()
        counters.incr_counter("consecutive_acceptances")  # stamps now
        r = counters.counters_health()
        self.assertEqual(r["transitions_since_last_write"], 0)
        self.assertFalse(r["stale"])

    def test_stale_at_threshold(self):
        entries = "\n".join(
            f'  - activity: /gse:produce\n    completed_at: "2026-06-0{i}T10:00:00Z"'
            for i in range(1, 6)
        )
        self.write_status(
            "consecutive_acceptances: 0\n"
            "pushback_dismissed: 0\n"
            "fix_attempts_on_current_symptom: 0\n"
            'counters_last_write: "2026-05-01T00:00:00Z"\n'
            f"activity_history:\n{entries}\n"
            "review_findings_open: 0\n"
        )
        r = counters.counters_health()
        self.assertEqual(r["transitions_since_last_write"], 5)
        self.assertTrue(r["stale"])

    def test_missing_file_is_error(self):
        r = counters.counters_health()
        self.assertEqual(r["status"], "error")


class CounterCliTests(_ChdirMixin):
    TOOL = ROOT / "plugin" / "tools" / "counters.py"

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(self.TOOL), *args],
            capture_output=True, text=True,
        )

    def test_cli_incr_ok_exit_zero(self):
        self.write_status()
        proc = self._run("incr", "consecutive_acceptances")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["value"], 1)

    def test_cli_unknown_counter_exit_two(self):
        self.write_status()
        proc = self._run("incr", "bogus")
        self.assertEqual(proc.returncode, 2)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "error")

    def test_cli_health(self):
        self.write_status()
        proc = self._run("health")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertIn("stale", out)


if __name__ == "__main__":
    unittest.main()
