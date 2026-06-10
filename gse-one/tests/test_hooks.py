#!/usr/bin/env python3
"""Smoke tests for the generated guardrail hooks (plugin/hooks/hooks.claude.json).

Added after the v0.62 hooks audit: the pre-v0.63 hooks read a CLAUDE_TOOL_INPUT
environment variable that does not exist in the Claude Code hook contract (input
arrives as JSON on stdin), so every guard silently no-opped (fail-open) since
creation — with zero tests to notice. These tests execute the REAL generated
commands with synthetic stdin JSON and assert the exit-code contract:
exit 2 = block (stderr fed back to the model), exit 0 = allow.

Run: python3 -m unittest tests.test_hooks
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # gse-one/
HOOKS_JSON = ROOT / "plugin" / "hooks" / "hooks.claude.json"


def _load_commands():
    data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    pre = data["hooks"]["PreToolUse"][0]["hooks"]
    post_bash = data["hooks"]["PostToolUse"][0]["hooks"]
    return {
        "protect_main": pre[0]["command"],
        "block_force": pre[1]["command"],
        "review_findings": post_bash[0]["command"],
    }


def _run_hook(command: str, bash_command: str, cwd: Path) -> subprocess.CompletedProcess:
    """Run a generated hook command with the documented stdin JSON transport."""
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": bash_command},
    })
    return subprocess.run(
        command, shell=True, input=payload, capture_output=True,
        text=True, cwd=str(cwd),
    )


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=str(cwd), check=True,
        capture_output=True, text=True,
        env={**os.environ,
             "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


class TestForcePushHook(unittest.TestCase):
    """Emergency guardrail: any force push form is blocked (exit 2)."""

    @classmethod
    def setUpClass(cls):
        cls.cmd = _load_commands()["block_force"]
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_blocks_force_forms(self):
        for form in (
            "git push --force",
            "git push -f",
            "git push origin main --force",
            "git push --force-with-lease",
            "cd sub && git push -f origin main",
        ):
            res = _run_hook(self.cmd, form, self.dir)
            self.assertEqual(res.returncode, 2, f"{form!r}: {res.stderr}")
            self.assertIn("EMERGENCY GUARDRAIL", res.stderr)

    def test_allows_benign(self):
        for form in ("git push", "git push origin main", "ls -f", "echo --force"):
            res = _run_hook(self.cmd, form, self.dir)
            self.assertEqual(res.returncode, 0, f"{form!r}: {res.stderr}")

    def test_toggle_disables(self):
        gse = self.dir / ".gse"
        gse.mkdir(exist_ok=True)
        (gse / "config.yaml").write_text("hooks:\n  block_force_push: false\n")
        try:
            res = _run_hook(self.cmd, "git push --force", self.dir)
            self.assertEqual(res.returncode, 0, res.stderr)
        finally:
            (gse / "config.yaml").unlink()

    def test_empty_stdin_fails_open(self):
        res = subprocess.run(self.cmd, shell=True, input="",
                             capture_output=True, text=True, cwd=str(self.dir))
        self.assertEqual(res.returncode, 0, res.stderr)


class TestProtectMainHook(unittest.TestCase):
    """Hard guardrail: git commit on main is blocked, with sanctioned exceptions."""

    def setUp(self):
        self.cmd = _load_commands()["protect_main"]
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        _git(self.dir, "init", "-b", "main")

    def tearDown(self):
        self.tmp.cleanup()

    def _first_commit(self):
        (self.dir / "f").write_text("x")
        _git(self.dir, "add", "f")
        _git(self.dir, "commit", "-m", "init")

    def test_blocks_commit_on_main(self):
        self._first_commit()
        for form in ("git commit -m x", "git add -A && git commit -m x",
                     "git -C . commit -m x"):
            res = _run_hook(self.cmd, form, self.dir)
            self.assertEqual(res.returncode, 2, f"{form!r}: {res.stderr}")
            self.assertIn("GUARDRAIL", res.stderr)

    def test_allows_initialization_commit(self):
        # No HEAD yet — the foundational / Step 1.7 auto-fix commit is allowed.
        res = _run_hook(self.cmd, "git commit -m 'chore: initialize repository'", self.dir)
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_allows_on_feature_branch(self):
        self._first_commit()
        _git(self.dir, "checkout", "-b", "feat/x")
        res = _run_hook(self.cmd, "git commit -m x", self.dir)
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_toggle_and_strategy_none_disable(self):
        self._first_commit()
        gse = self.dir / ".gse"
        gse.mkdir()
        for body in ("hooks:\n  protect_main: false\n",
                     "git:\n  strategy: none\n"):
            (gse / "config.yaml").write_text(body)
            res = _run_hook(self.cmd, "git commit -m x", self.dir)
            self.assertEqual(res.returncode, 0, f"{body!r}: {res.stderr}")

    def test_allows_non_commit(self):
        self._first_commit()
        res = _run_hook(self.cmd, "git log --oneline", self.dir)
        self.assertEqual(res.returncode, 0, res.stderr)


class TestReviewFindingsHook(unittest.TestCase):
    """Informational hook: warn (exit 0) when open review findings exist."""

    def setUp(self):
        self.cmd = _load_commands()["review_findings"]
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / ".gse").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_warns_on_open_findings(self):
        (self.dir / ".gse" / "status.yaml").write_text("review_findings_open: 3\n")
        res = _run_hook(self.cmd, "git push origin main", self.dir)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("WARNING: 3 open review findings", res.stdout)

    def test_silent_when_clean_or_disabled(self):
        (self.dir / ".gse" / "status.yaml").write_text("review_findings_open: 0\n")
        res = _run_hook(self.cmd, "git push", self.dir)
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("WARNING", res.stdout)

        (self.dir / ".gse" / "status.yaml").write_text("review_findings_open: 3\n")
        (self.dir / ".gse" / "config.yaml").write_text(
            "hooks:\n  review_findings_on_push: false\n")
        res = _run_hook(self.cmd, "git push", self.dir)
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("WARNING", res.stdout)


if __name__ == "__main__":
    unittest.main()
