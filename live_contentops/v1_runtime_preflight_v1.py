"""Fail-closed V1 native Desktop runtime preflight.

The runtime is a durable ContentOps dependency, not a Codex cache dependency.  This
module performs imports and bounded, read-only transport/database checks only.  It
never installs packages, reads secrets, or performs a public write.
"""
from __future__ import annotations

import importlib
import os
import socket
import sys
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "contentops.v1_runtime_preflight.v1"
REQUIRED_IMPORTS = (
    "live_contentops",
    "playwright",
    "playwright.sync_api",
    "PIL",
    "duckdb",
)
CANONICAL_EDGE_CDP_PORT = 9223


def _cache_runtime(value: str) -> bool:
    normalized = value.replace("/", "\\").casefold()
    return "\\.cache\\codex-runtimes\\" in normalized


def run_v1_runtime_preflight(
    *,
    require_edge_attach: bool = False,
    edge_cdp_port: int = CANONICAL_EDGE_CDP_PORT,
    capital_chronicle_duckdb_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return a sanitized preflight receipt; all optional probes are read-only."""
    imports: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    for module_name in REQUIRED_IMPORTS:
        try:
            module = importlib.import_module(module_name)
            imports[module_name] = {
                "status": "PASS",
                "version": str(getattr(module, "__version__", "not_exposed")),
            }
        except Exception as exc:
            imports[module_name] = {
                "status": "FAIL",
                "error_class": type(exc).__name__,
            }
            blockers.append(f"required_import_unavailable:{module_name}")

    executable = str(Path(sys.executable).resolve())
    if _cache_runtime(executable):
        blockers.append("codex_private_cache_runtime_forbidden")

    edge = {
        "required": bool(require_edge_attach),
        "cdp_port": int(edge_cdp_port),
        "status": "NOT_REQUESTED",
        "read_only": True,
    }
    if require_edge_attach:
        if int(edge_cdp_port) != CANONICAL_EDGE_CDP_PORT:
            edge["status"] = "FAIL_NONCANONICAL_CDP_PORT"
            blockers.append("canonical_edge_cdp_9223_required")
        else:
            try:
                with socket.create_connection(("127.0.0.1", edge_cdp_port), timeout=2):
                    pass
                edge["status"] = "PASS_TCP_ATTACHABLE"
            except OSError as exc:
                edge.update({"status": "FAIL_UNAVAILABLE", "error_class": type(exc).__name__})
                blockers.append("canonical_edge_cdp_9223_unavailable")

    duckdb_probe: dict[str, Any] = {
        "required": capital_chronicle_duckdb_path is not None,
        "status": "NOT_REQUESTED",
        "access_mode": "READ_ONLY",
    }
    if capital_chronicle_duckdb_path is not None and imports.get("duckdb", {}).get("status") == "PASS":
        target = Path(capital_chronicle_duckdb_path).resolve()
        stores = sorted(target.glob("*.duckdb")) if target.is_dir() else [target]
        duckdb_probe["path"] = str(target)
        duckdb_probe["store_count"] = len(stores)
        if not stores or any(not store.is_file() for store in stores):
            duckdb_probe["status"] = "FAIL_MISSING"
            blockers.append("capital_chronicle_duckdb_missing")
        else:
            try:
                import duckdb

                for store in stores:
                    connection = duckdb.connect(str(store), read_only=True)
                    try:
                        connection.execute("SELECT 1").fetchone()
                    finally:
                        connection.close()
                duckdb_probe["status"] = "PASS_READ_ONLY"
            except Exception as exc:
                duckdb_probe.update({"status": "FAIL", "error_class": type(exc).__name__})
                blockers.append("capital_chronicle_duckdb_read_only_attach_failed")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not blockers else "BLOCKED",
        "python_executable": executable,
        "python_version": sys.version.split()[0],
        "contentops_owned_runtime_expected": True,
        "codex_private_cache_runtime_used": _cache_runtime(executable),
        "imports": imports,
        "edge_attach": edge,
        "capital_chronicle_duckdb": duckdb_probe,
        "blockers": blockers,
        "public_write_performed": False,
        "secrets_read": False,
    }


def require_v1_runtime_preflight(**kwargs: Any) -> dict[str, Any]:
    receipt = run_v1_runtime_preflight(**kwargs)
    if receipt["status"] != "PASS":
        raise RuntimeError("V1_RUNTIME_PREFLIGHT_BLOCKED:" + ",".join(receipt["blockers"]))
    return receipt


if __name__ == "__main__":
    import json

    print(json.dumps(run_v1_runtime_preflight(), indent=2, sort_keys=True))
