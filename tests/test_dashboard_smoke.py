import subprocess
import sys
from pathlib import Path


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_dashboard_generates_html(tmp_path: Path):
    # Minimal project structure expected by dashboard.py
    root = tmp_path / "proj"
    gse_dir = root / ".gse"
    docs_dir = root / "docs" / "sprints" / "sprint-00"
    gse_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    _write_text(
        gse_dir / "config.yaml",
        "project:\n  name: test-proj\ngit:\n  enabled: false\n",
    )
    _write_text(
        gse_dir / "status.yaml",
        "current_sprint: 0\ncurrent_phase: LC01\nlast_activity: tests\n",
    )
    _write_text(
        gse_dir / "profile.yaml",
        "dimensions:\n  it_expertise: intermediate\n  decision_involvement: normal\nuser:\n  name: tester\n",
    )
    _write_text(gse_dir / "backlog.yaml", "backlog:\n  tasks: []\n")
    _write_text(
        gse_dir / "plan.yaml",
        "status: active\ncurrent_sprint: 0\nworkflow:\n  active: tests\n  pending: []\n  completed: []\n  skipped: []\n",
    )

    out_html = root / "docs" / "dashboard.html"

    script = (
        Path(__file__).resolve().parents[1]
        / "gse-one"
        / "plugin"
        / "tools"
        / "dashboard.py"
    )

    proc = subprocess.run(
        [sys.executable, str(script), "--no-cdn", "--output", str(out_html)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, f"dashboard failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert out_html.exists() and out_html.stat().st_size > 0, "dashboard.html not generated"

