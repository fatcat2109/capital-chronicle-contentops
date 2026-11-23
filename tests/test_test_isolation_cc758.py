"""Prove the pytest boundary fires before any real process or export access."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from isolated_python.sitecustomize import MAIN_EXPORT, REPORT_ENV, TestIsolationError as IsolationError


@pytest.mark.parametrize("command", [
    ["agy.exe", "--version"],
    [r"C:\fake path\codex.cmd", "exec"],
    [sys.executable, "plan_analysis_pages.py", "draft-due"],
])
def test_process_guard_fails_before_launch(command):
    with pytest.raises(IsolationError, match="Stub"):
        subprocess.Popen(command)


def test_live_export_guard_fails_before_read_but_fixture_with_same_name_is_readable(tmp_path):
    fixture = tmp_path / "plan-status-v1" / "plan-status.public.json"
    fixture.parent.mkdir()
    fixture.write_text("{}", encoding="utf-8")
    assert fixture.read_text(encoding="utf-8") == "{}"
    with pytest.raises(IsolationError, match="Supply a fixture export"):
        Path(MAIN_EXPORT + "/plan-status.public.json").read_bytes()


def test_python_child_reports_forbidden_io_to_its_pytest_parent(tmp_path):
    report = tmp_path / "expected-violation.txt"
    code = "from pathlib import Path; Path(" + repr(MAIN_EXPORT + "/plan-status.public.json") + ").read_bytes()"
    result = subprocess.run(
        [sys.executable, "-c", code], env={**os.environ, REPORT_ENV: str(report)},
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode != 0
    assert "TestIsolationError" in result.stderr
    assert "Supply a fixture export" in report.read_text(encoding="utf-8")
