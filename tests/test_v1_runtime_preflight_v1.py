from __future__ import annotations

import importlib

from live_contentops import v1_runtime_preflight_v1 as runtime


def test_current_v1_runtime_import_preflight_passes_without_public_write():
    receipt = runtime.run_v1_runtime_preflight()
    assert receipt["status"] == "PASS"
    assert receipt["codex_private_cache_runtime_used"] is False
    assert set(receipt["imports"]) == set(runtime.REQUIRED_IMPORTS)
    assert all(row["status"] == "PASS" for row in receipt["imports"].values())
    assert receipt["public_write_performed"] is False
    assert receipt["secrets_read"] is False


def test_missing_required_import_fails_closed(monkeypatch):
    real_import = importlib.import_module

    def controlled_import(name):
        if name == "duckdb":
            raise ModuleNotFoundError("controlled")
        return real_import(name)

    monkeypatch.setattr(runtime.importlib, "import_module", controlled_import)
    receipt = runtime.run_v1_runtime_preflight()
    assert receipt["status"] == "BLOCKED"
    assert "required_import_unavailable:duckdb" in receipt["blockers"]
    assert receipt["public_write_performed"] is False


def test_codex_private_cache_interpreter_is_rejected(monkeypatch):
    monkeypatch.setattr(
        runtime.sys,
        "executable",
        r"C:\Users\operator\.cache\codex-runtimes\private\python.exe",
    )
    receipt = runtime.run_v1_runtime_preflight()
    assert receipt["status"] == "BLOCKED"
    assert "codex_private_cache_runtime_forbidden" in receipt["blockers"]
