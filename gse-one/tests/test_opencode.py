"""OpenCode installer selection and generated runtime regression tests."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("gse_installer", ROOT / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
SOURCE = ROOT / "gse-one/plugin/opencode"


class TestOpenCodeInstaller(unittest.TestCase):
    def test_version_selection(self):
        for version, adapter in [("1.17.18", "plugins/gse-guardrails.ts"),
                                 ("1.18.29", "plugins/gse-guardrails.ts"),
                                 ("2.0.32", "compat/gse-guardrails-v2.ts"),
                                 ("opencode v2.0.32-beta.1", "compat/gse-guardrails-v2.ts")]:
            with self.subTest(version=version), patch.object(installer.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, version)):
                self.assertEqual(installer._opencode_guardrails_source(SOURCE), SOURCE / adapter)

    def test_missing_unrecognized_or_failed_cli_warns_and_preserves_v1(self):
        for result in [subprocess.CompletedProcess([], 0, "unknown"), subprocess.CompletedProcess([], 1, "2.0.32")]:
            with patch.object(installer.subprocess, "run", return_value=result), patch.object(installer, "warn") as warning:
                self.assertEqual(installer._opencode_guardrails_source(SOURCE), SOURCE / "plugins/gse-guardrails.ts")
                warning.assert_called_once()
        for error in [FileNotFoundError(), subprocess.TimeoutExpired("opencode", 10)]:
            with patch.object(installer.subprocess, "run", side_effect=error), patch.object(installer, "warn") as warning:
                self.assertEqual(installer._opencode_guardrails_source(SOURCE), SOURCE / "plugins/gse-guardrails.ts")
                warning.assert_called_once()

    def test_unknown_future_major_is_not_silently_supported(self):
        with patch.object(installer.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "3.0.0")):
            with patch.object(installer, "err") as error:
                self.assertIsNone(installer._opencode_guardrails_source(SOURCE))
                error.assert_called_once()

    def test_missing_adapter_fails_before_copying_files(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(installer, "_opencode_guardrails_source", return_value=Path(tmp) / "missing.ts"), patch.object(installer, "err") as error:
            target = Path(tmp) / "target"
            self.assertIsNone(installer._opencode_copy_tree(SOURCE, target))
            self.assertFalse(target.exists())
            error.assert_called_once()

    def test_selection_failure_is_reported_by_both_install_modes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(installer, "_check_duplicate_install", return_value=True), patch.object(installer, "_opencode_guardrails_source", return_value=None), patch.object(installer.tracker, "add") as track:
            self.assertFalse(installer.install_opencode_plugin({"opencode_dir": Path(tmp) / "global"}))
            self.assertFalse(installer.install_opencode_no_plugin(Path(tmp) / "project"))
            self.assertEqual(track.call_count, 2)
            self.assertTrue(all(call.args[-2] == "FAIL" for call in track.call_args_list))
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_upgrade_downgrade_and_uninstall_preserve_user_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "plugins").mkdir()
            custom = target / "plugins/custom.ts"
            custom.write_text("// User-owned plugin\n")
            for version, adapter in [("1.17.18", "plugins/gse-guardrails.ts"), ("2.0.32", "compat/gse-guardrails-v2.ts"), ("1.17.18", "plugins/gse-guardrails.ts")]:
                with patch.object(installer.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, version)):
                    counts = installer._opencode_copy_tree(SOURCE, target)
                self.assertEqual(counts["plugins"], 1)
                self.assertEqual((target / "plugins/gse-guardrails.ts").read_bytes(), (SOURCE / adapter).read_bytes())
                self.assertEqual(sorted(p.name for p in (target / "plugins").iterdir()), ["custom.ts", "gse-guardrails.ts"])
                self.assertFalse((target / "compat").exists())
            installer._opencode_remove_content(target)
            self.assertEqual(list((target / "plugins").iterdir()), [custom])
            self.assertEqual(custom.read_text(), "// User-owned plugin\n")


class TestOpenCodeRuntime(unittest.TestCase):
    @unittest.skipUnless(shutil.which("bun"), "Bun is required for OpenCode runtime tests; CI installs it")
    def test_generated_adapters(self):
        result = subprocess.run(["bun", "test", "tests/opencode.test.ts"], cwd=ROOT / "gse-one", capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
