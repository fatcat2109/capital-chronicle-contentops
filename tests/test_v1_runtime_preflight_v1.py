from __future__ import annotations

import importlib
from pathlib import Path

from live_contentops import v1_runtime_preflight_v1 as runtime


def test_canonical_v1_runtime_manifest_pins_direct_cdp_transport_dependency():
    requirements = Path("requirements-v1-runtime.txt").read_text(encoding="utf-8").splitlines()
    assert "websocket-client==1.8.0" in requirements


def test_current_v1_runtime_import_preflight_passes_without_public_write():
    receipt = runtime.run_v1_runtime_preflight()
    assert receipt["status"] == "PASS"
    assert receipt["codex_private_cache_runtime_used"] is False
    assert set(receipt["imports"]) == set(runtime.REQUIRED_IMPORTS)
    assert all(row["status"] == "PASS" for row in receipt["imports"].values())
    assert receipt["imports"]["websocket"]["status"] == "PASS"
    assert receipt["imports"]["playwright.async_api"]["status"] == "PASS"
    assert receipt["ingestion_dependency_closure"]["status"] == "PASS"
    assert receipt["ingestion_dependency_closure"]["direct_cdp_transport"] == (
        "websocket-client"
    )
    assert receipt["ingestion_dependency_closure"]["browser_navigation_performed"] is False
    assert receipt["ingestion_dependency_closure"]["capture_performed"] is False
    assert receipt["ingestion_dependency_closure"]["session_material_read"] is False
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


def test_missing_direct_cdp_websocket_dependency_fails_actual_ingestion_closure(monkeypatch):
    real_import = importlib.import_module

    def controlled_import(name):
        if name == "websocket":
            raise ModuleNotFoundError("controlled")
        return real_import(name)

    monkeypatch.setattr(runtime.importlib, "import_module", controlled_import)
    receipt = runtime.run_v1_runtime_preflight()

    assert receipt["status"] == "BLOCKED"
    assert "required_import_unavailable:websocket" in receipt["blockers"]
    assert receipt["ingestion_dependency_closure"]["status"] == (
        "NOT_RUN_REQUIRED_IMPORT_BLOCKED"
    )
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
