from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_direct_file_cli_bootstraps_repository_package_from_arbitrary_cwd(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "run_v1_simple_gemini_newsroom.py"

    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "ModuleNotFoundError" not in completed.stderr
    assert "Run one zero-write V1 simple Gemini newsroom opportunity." in completed.stdout
