#!/usr/bin/env python3
"""Unit tests for gse-one/audit.py — regression guards against known false positives.

Each test corresponds to a false-positive class that was caught during real
audit sessions. The test asserts that the audit engine's patterns correctly
distinguish the positive case (real drift) from the false-positive case
(look-alike string that should NOT fire).

Run: python3 -m unittest discover tests
Or:  python3 gse_generate.py --verify   (runs verify + tests)

History:
- 2026-04-22 v0.48.9 P14 introduced CHANGELOG.md exclusion + regex prefix
  `(?:^|\\s)` + "specialized" negative lookahead. These tests guard against
  regression of those fixes.
- 2026-04-22 v0.50.0 initial test file creation.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

# Make gse-one/ importable so we can import audit.py
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import audit  # noqa: E402


# ---------------------------------------------------------------------------
# Replicas of the audit_numeric() regex patterns — kept in sync with audit.py.
# If the audit patterns change, update these replicas to match.
# ---------------------------------------------------------------------------

SPECIALIZED_PATTERN = re.compile(
    r"(?:^|\s)(\d+)\s+specialized\b"
    r"(?!\s+(?:templates?|files?|Dockerfiles?|rules?|settings?|categories?))",
    re.IGNORECASE,
)

COMMANDS_PATTERN = re.compile(
    r"(?:^|\s)(\d+)\s+commands?\b",
    re.IGNORECASE,
)

PRINCIPLES_PATTERN = re.compile(
    r"(?:^|\s)(\d+)\s+principles?\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Test class — false positive regression guards
# ---------------------------------------------------------------------------

class TestAuditNumericPatterns(unittest.TestCase):
    """Guard against P14 regressions: the regex patterns must not match
    look-alike strings that were known false positives before v0.48.9."""

    # ----- "commands" pattern -----

    def test_commands_matches_real_claim(self):
        """Positive case: '23 commands covering the full SDLC' must match."""
        m = COMMANDS_PATTERN.search("GSE-One provides 23 commands covering the full SDLC")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "23")

    def test_commands_does_not_match_section_number(self):
        """Regression guard: '### 3.10 Commands by Lifecycle Phase' must NOT
        match because the digit '10' follows a period, not whitespace. Before
        P14 this was a false positive causing 'gse-one-spec.md:1226 claims
        10 commands — actual is 23' which the user could not correct (it's a
        section header, not a claim)."""
        m = COMMANDS_PATTERN.search("### 3.10 Commands by Lifecycle Phase")
        self.assertIsNone(m, "Section number 3.10 leaked as claim of 10 commands")

    def test_commands_matches_at_start_of_line(self):
        """Positive case: start-of-line prefix is accepted."""
        m = COMMANDS_PATTERN.search("23 commands are defined")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "23")

    # ----- "principles" pattern -----

    def test_principles_matches_real_claim(self):
        """Positive case: '16 principles form the backbone' must match."""
        m = PRINCIPLES_PATTERN.search("The 16 principles form the methodological backbone")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "16")

    def test_principles_does_not_match_principle_id(self):
        """Regression guard: 'P10 principle rule 8' must NOT match because
        the digit '10' follows a letter 'P', not whitespace. Before P14 this
        was a false positive from CHANGELOG entries discussing individual
        principles by ID."""
        m = PRINCIPLES_PATTERN.search("The rule 8 of P10 principle was replaced")
        self.assertIsNone(m, "Principle ID P10 leaked as claim of 10 principles")

    # ----- "specialized" pattern -----

    def test_specialized_matches_real_claim(self):
        """Positive case: '10 specialized agents' must match."""
        m = SPECIALIZED_PATTERN.search("has 10 specialized agents in the roster")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "10")

    def test_specialized_matches_with_orchestrator_suffix(self):
        """Positive case: '10 specialized + orchestrator' form must match."""
        m = SPECIALIZED_PATTERN.search("has 10 specialized + orchestrator")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "10")

    def test_specialized_does_not_match_templates_context(self):
        """Regression guard: '4 specialized templates' must NOT match because
        it describes Dockerfile templates, not agents. Before P14 this was a
        false positive causing 'CHANGELOG.md claims 4 specialized — actual is
        10' on a line discussing Dockerfile specialization."""
        m = SPECIALIZED_PATTERN.search("replaced by 4 specialized templates")
        self.assertIsNone(m, "4 specialized templates leaked as agent count")

    def test_specialized_does_not_match_files_context(self):
        """Regression guard: negative lookahead must also filter 'specialized
        files', 'specialized Dockerfiles', etc."""
        for context in (
            "5 specialized files in the deploy module",
            "3 specialized Dockerfiles for Python/Node/static",
            "2 specialized rules for linting",
            "4 specialized categories of events",
        ):
            m = SPECIALIZED_PATTERN.search(context)
            self.assertIsNone(
                m, f"Negative lookahead leaked: {context!r}",
            )

    def test_specialized_does_not_match_digit_after_letter(self):
        """Regression guard: digit preceded by letter (like 'v10 specialized')
        should also NOT match. The `(?:^|\\s)` prefix handles this."""
        m = SPECIALIZED_PATTERN.search("v10 specialized")
        self.assertIsNone(m)


class TestAuditFileScanExclusions(unittest.TestCase):
    """Guard against P14 regression: CHANGELOG.md must be excluded from the
    numeric-claim file scan (it records historical states, not current ones)."""

    def test_changelog_excluded_from_files_to_scan(self):
        """Regression guard: audit_numeric() must not list CHANGELOG.md
        among its scanned files. Inspects the actual file_to_scan population
        logic by reading the source — if CHANGELOG is mentioned as scanned,
        the test fails."""
        # Read audit.py and verify CHANGELOG is explicitly excluded
        audit_src = (ROOT / "audit.py").read_text(encoding="utf-8")
        # Find the audit_numeric() function body
        self.assertIn(
            "CHANGELOG.md is intentionally excluded",
            audit_src,
            "audit_numeric() lost its exclusion comment for CHANGELOG.md",
        )
        # Extract the file list portion near the function start
        func_start = audit_src.index("def audit_numeric")
        func_end = audit_src.index("def ", func_start + 1)
        func_body = audit_src[func_start:func_end]
        # The canonical file list tuple must NOT contain CHANGELOG.md
        # (it's filtered out by design in v0.48.9).
        # Look for the tuple literal after `for name in (`
        import re as _re
        tuple_match = _re.search(
            r'for name in \(([^)]+)\)', func_body,
        )
        self.assertIsNotNone(
            tuple_match,
            "Could not locate the file-name tuple in audit_numeric()",
        )
        names = tuple_match.group(1)
        self.assertNotIn(
            "CHANGELOG.md", names,
            "CHANGELOG.md leaked back into the scan tuple",
        )


class TestAuditCategoriesPresent(unittest.TestCase):
    """Smoke test: audit.py declares the expected 12 deterministic categories.
    Guards against accidental removal of a category."""

    def test_categories_list_is_complete(self):
        expected = {
            "version", "file_integrity", "plugin_parity", "cross_refs",
            "numeric", "links", "git", "python", "templates", "todos",
            "test_coverage", "freshness",
        }
        actual = set(audit.CATEGORIES)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
