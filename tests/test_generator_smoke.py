import os
import shutil
import subprocess
import sys
from pathlib import Path


def _rmtree_force(path: Path) -> None:
    def _onerror(func, p, exc_info):
        try:
            os.chmod(p, 0o700)
        except Exception:
            pass
        func(p)

    if path.exists():
        shutil.rmtree(path, onerror=_onerror)


def _copy_repo_subset(tmp_path: Path) -> Path:
    """
    Create an isolated minimal repo copy for running the generator:
    - VERSION at repo root (required by gse_generate.py)
    - gse-one/ tree (contains src/ + generator)
    """
    here = Path(__file__).resolve()
    repo_root = here.parents[1]

    (tmp_path / "gse-one").mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo_root / "VERSION", tmp_path / "VERSION")
    shutil.copytree(repo_root / "gse-one", tmp_path / "gse-one", dirs_exist_ok=True)
    return tmp_path


def test_generator_clean_verify_creates_expected_outputs(tmp_path: Path):
    sandbox = _copy_repo_subset(tmp_path)
    gse_one_dir = sandbox / "gse-one"

    # On Windows, copied files may carry read-only attributes; ensure we can regenerate.
    _rmtree_force(gse_one_dir / "plugin")

    proc = subprocess.run(
        [sys.executable, "gse_generate.py", "--verify"],
        cwd=str(gse_one_dir),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, f"generator failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    plugin_dir = gse_one_dir / "plugin"
    assert plugin_dir.is_dir(), "plugin/ directory was not created"

    cursor_manifest = plugin_dir / ".cursor-plugin" / "plugin.json"
    claude_manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    assert cursor_manifest.exists() and cursor_manifest.stat().st_size > 0
    assert claude_manifest.exists() and claude_manifest.stat().st_size > 0

    # Representative files (non-brittle): at least one command, one skill, one template
    assert any((plugin_dir / "commands").glob("gse-*.md")), "no Cursor commands generated"
    assert any((plugin_dir / "skills").glob("*/SKILL.md")), "no Claude skills generated"
    assert any((plugin_dir / "templates").rglob("*")), "no templates generated"

