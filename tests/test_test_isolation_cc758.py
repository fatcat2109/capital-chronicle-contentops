"""Prove the pytest boundary fires before any real process or export access."""

import subprocess
import sys

import pytest

from isolated_python.sitecustomize import REPORT_ENV, TestIsolationError as IsolationError
from live_contentops.plan_status_posts_v1 import EXPORT_DIR


@pytest.mark.parametrize("command", [
    ["agy.exe", "--version"],
    [r"C:\fake path\codex.cmd", "exec"],
    [sys.executable, "plan_analysis_pages.py", "draft-due"],
])
def test_process_guard_fails_before_launch(command, tmp_path, monkeypatch):
    report = tmp_path / "expected-violation.txt"
    monkeypatch.setenv(REPORT_ENV, str(report))
    with pytest.raises(IsolationError, match="Stub"):
        subprocess.Popen(command)
    assert "Stub" in report.read_text(encoding="utf-8")


def test_live_export_guard_fails_before_read_but_fixture_with_same_name_is_readable(tmp_path, monkeypatch):
    monkeypatch.setenv(REPORT_ENV, str(tmp_path / "expected-violation.txt"))
    fixture = tmp_path / "plan-status-v1" / "plan-status.public.json"
    fixture.parent.mkdir()
    fixture.write_text("{}", encoding="utf-8")
    assert fixture.read_text(encoding="utf-8") == "{}"
    with pytest.raises(IsolationError, match="Supply a fixture export"):
        (EXPORT_DIR / "plan-status.public.json").read_bytes()


def test_python_child_reports_forbidden_io_to_its_pytest_parent(tmp_path, monkeypatch):
    report = tmp_path / "expected-violation.txt"
    monkeypatch.setenv(REPORT_ENV, str(report))
    export_file = str(EXPORT_DIR / "plan-status.public.json")
    code = f"from pathlib import Path; Path({export_file!r}).read_bytes()"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=5,
    )
    assert result.returncode != 0
    assert "TestIsolationError" in result.stderr
    assert "Supply a fixture export" in report.read_text(encoding="utf-8")
