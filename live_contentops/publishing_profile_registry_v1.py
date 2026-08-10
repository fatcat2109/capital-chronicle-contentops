"""Canonical Microsoft Edge publishing-profile registry and runtime doctor.

This module is the only browser-profile authority for live ContentOps writes.
It intentionally inspects only Windows process metadata and CDP version metadata;
it never reads browser storage, cookies, headers, tokens, or page content.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .live_entrypoint_registry_v1 import (
    BROWSER_PROFILE_EXECUTION_QUARANTINED,
    quarantine,
)


REGISTRY_VERSION = "contentops.publishing_profile_registry.v1"
CANONICAL_PROFILE_ID = "contentops-social-main"
CANONICAL_PROFILE_ROOT = Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main")
CANONICAL_BROWSER_FAMILY = "microsoft_edge"
CANONICAL_PUBLISHING_CDP_PORT = 9223
CANONICAL_CDP_PORTS = (CANONICAL_PUBLISHING_CDP_PORT,)
PROFILE_ENV_KEY = "CONTENTOPS_OPERATOR_BROWSER_PROFILE_ROOT"
CDP_PORT_ENV_KEY = "CONTENTOPS_OPERATOR_BROWSER_CDP_PORT"
BROWSER_BINARY_ENV_KEY = "CONTENTOPS_OPERATOR_BROWSER_BINARY"

_EDGE_EXECUTABLE_MARKERS = ("msedge", "microsoft\\edge", "microsoft/edge")
_CHROME_MARKERS = ("chrome", "chromium")
_ANTIGRAVITY_MARKERS = (".gemini\\antigravity-browser-profile", ".gemini/antigravity-browser-profile")
_BUILT_IN_PROFILE_MARKERS = ("\\user data\\default", "\\user data\\profile ", "\\edge\\user data\\")
_PORT_RE = re.compile(r"--remote-debugging-port(?:=|\s+)(\d+)", re.IGNORECASE)
_PROFILE_RE = re.compile(r"--user-data-dir(?:=|\s+)(\"[^\"]+\"|'[^']+'|.*?)(?=\s+--|$)", re.IGNORECASE)


class PublishingProfileError(RuntimeError):
    """Raised when a live writer is not attached to the canonical Edge profile."""


def _normalise_path(value: str | Path) -> str:
    return str(value).strip().strip('"').replace("/", "\\").rstrip("\\").lower()


def _is_edge_executable(value: str | Path | None) -> bool:
    lowered = str(value or "").replace("/", "\\").lower()
    return any(marker in lowered for marker in _EDGE_EXECUTABLE_MARKERS)


def _extract_profile_root(command_line: str | None) -> str | None:
    if not command_line:
        return None
    match = _PROFILE_RE.search(command_line)
    return match.group(1).strip().strip('"\'') if match else None


def _extract_ports(command_line: str | None) -> tuple[int, ...]:
    if not command_line:
        return ()
    values: list[int] = []
    for item in _PORT_RE.findall(command_line):
        try:
            values.append(int(item))
        except ValueError:
            continue
    return tuple(dict.fromkeys(values))


def _profile_class(profile_root: str | Path | None) -> str:
    value = _normalise_path(profile_root or "")
    if value == _normalise_path(CANONICAL_PROFILE_ROOT):
        return "canonical_contentops_profile"
    if any(marker in value for marker in _ANTIGRAVITY_MARKERS):
        return "antigravity_profile_blocked"
    if any(marker in value for marker in _BUILT_IN_PROFILE_MARKERS):
        return "builtin_browser_profile_blocked"
    return "unknown_profile_blocked"


def canonical_profile_registry() -> dict[str, Any]:
    """Return the safe, machine-readable publishing authority declaration."""
    return {
        "schema_version": REGISTRY_VERSION,
        "profile_id": CANONICAL_PROFILE_ID,
        "browser_family": CANONICAL_BROWSER_FAMILY,
        "profile_root": str(CANONICAL_PROFILE_ROOT),
        "allowed_cdp_ports": list(CANONICAL_CDP_PORTS),
        "publishing_cdp_port": CANONICAL_PUBLISHING_CDP_PORT,
        "ingestion_only_cdp_port": 9222,
        "ingestion_port_publishing_allowed": False,
        "chrome_publishing_allowed": False,
        "temporary_profile_publishing_allowed": False,
        "builtin_edge_profile_publishing_allowed": False,
        "browser_storage_read_allowed": False,
        "profile_root_persistable_in_git": False,
    }


def resolve_cdp_port(env: Mapping[str, str] | None = None) -> int:
    source = os.environ if env is None else env
    raw = str(source.get(CDP_PORT_ENV_KEY, CANONICAL_PUBLISHING_CDP_PORT)).strip()
    if not raw.isdigit() or int(raw) not in CANONICAL_CDP_PORTS:
        raise PublishingProfileError("publishing_cdp_port_must_be_9223")
    return int(raw)


def resolve_profile_root(env: Mapping[str, str] | None = None) -> Path:
    source = os.environ if env is None else env
    configured = source.get(PROFILE_ENV_KEY)
    root = Path(configured).expanduser() if configured else CANONICAL_PROFILE_ROOT
    if _normalise_path(root) != _normalise_path(CANONICAL_PROFILE_ROOT):
        raise PublishingProfileError("publishing_profile_root_must_match_canonical_contentops_profile")
    return CANONICAL_PROFILE_ROOT


def find_edge_binary(env: Mapping[str, str] | None = None) -> str | None:
    """Locate Edge without ever falling back to Chrome or Chromium."""
    source = os.environ if env is None else env
    configured = source.get(BROWSER_BINARY_ENV_KEY)
    if configured:
        return configured if _is_edge_executable(configured) and Path(configured).exists() else None
    candidates = (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "msedge.exe",
        "msedge",
    )
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
        if Path(candidate).exists():
            return candidate
    return None


def build_edge_command(
    browser_binary: str,
    *,
    profile_root: Path = CANONICAL_PROFILE_ROOT,
    cdp_port: int,
    urls: Sequence[str],
) -> list[str]:
    if not _is_edge_executable(browser_binary):
        raise PublishingProfileError("publishing_browser_must_be_microsoft_edge")
    if _normalise_path(profile_root) != _normalise_path(CANONICAL_PROFILE_ROOT):
        raise PublishingProfileError("publishing_profile_root_must_match_canonical_contentops_profile")
    if cdp_port not in CANONICAL_CDP_PORTS:
        raise PublishingProfileError("publishing_cdp_port_must_be_9223")
    return [
        browser_binary,
        f"--user-data-dir={CANONICAL_PROFILE_ROOT}",
        f"--remote-debugging-port={cdp_port}",
        "--no-first-run",
        "--disable-default-apps",
        "--new-window",
        *[str(url) for url in urls if str(url).strip()],
    ]


def _windows_browser_processes() -> list[dict[str, Any]]:
    """Read process metadata only; callers must never persist raw command lines."""
    command = (
        "$rows = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(msedge|chrome|chromium)(\\.exe)?$' } | "
        "Select-Object ProcessId,Name,CommandLine; "
        "if ($rows) { $rows | ConvertTo-Json -Compress }"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            return []
        decoded = json.loads(completed.stdout)
    except Exception:
        return []
    rows = decoded if isinstance(decoded, list) else [decoded]
    return [row for row in rows if isinstance(row, dict)]


def _classify_process(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    command_line = str(row.get("CommandLine") or "")
    name = str(row.get("Name") or "")
    profile = _extract_profile_root(command_line)
    profile_status = _profile_class(profile)
    process_is_edge = _is_edge_executable(name) or _is_edge_executable(command_line.split(" ", 1)[0])
    browser_class = CANONICAL_BROWSER_FAMILY if process_is_edge else "chrome_or_chromium"
    rows: list[dict[str, Any]] = []
    for port in _extract_ports(command_line):
        rows.append(
            {
                "pid": int(row.get("ProcessId") or 0),
                "cdp_port": port,
                "browser_class": browser_class,
                "profile_class": profile_status,
                "canonical_write_authority": bool(
                    process_is_edge and profile_status == "canonical_contentops_profile" and port in CANONICAL_CDP_PORTS
                ),
            }
        )
    return rows


def sanitized_cdp_process_rows(processes: Iterable[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    source = list(processes) if processes is not None else _windows_browser_processes()
    rows: list[dict[str, Any]] = []
    for process in source:
        rows.extend(_classify_process(process))
    return sorted(rows, key=lambda item: (int(item["cdp_port"]), int(item["pid"])))


def probe_cdp_version(cdp_port: int, timeout_seconds: float = 3.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json/version", timeout=timeout_seconds) as response:
            payload = json.load(response)
    except Exception:
        return {"cdp_alive": False, "browser_family": None, "websocket_available": False}
    browser = str(payload.get("Browser") or "")
    return {
        "cdp_alive": bool(browser and payload.get("webSocketDebuggerUrl")),
        "browser_family": CANONICAL_BROWSER_FAMILY if browser.startswith("Edg/") else "non_edge_browser",
        "websocket_available": bool(payload.get("webSocketDebuggerUrl")),
    }


def browser_doctor(
    *,
    env: Mapping[str, str] | None = None,
    processes: Iterable[Mapping[str, Any]] | None = None,
    probe: bool = True,
) -> dict[str, Any]:
    """Return a safe preflight report for the two allowed publishing CDP ports."""
    registry = canonical_profile_registry()
    rows = sanitized_cdp_process_rows(processes)
    port_reports: list[dict[str, Any]] = []
    preferred = resolve_cdp_port(env)
    for port in CANONICAL_CDP_PORTS:
        owners = [row for row in rows if row["cdp_port"] == port]
        canonical_owner = next((row for row in owners if row["canonical_write_authority"]), None)
        status = "free" if not owners else ("canonical_edge_owner" if canonical_owner else "blocked_by_noncanonical_owner")
        port_reports.append(
            {
                "cdp_port": port,
                "status": status,
                "owner_count": len(owners),
                "canonical_edge_owner": bool(canonical_owner),
                "owner_classes": [f"{row['browser_class']}:{row['profile_class']}" for row in owners],
                "cdp_probe": probe_cdp_version(port) if probe else {"cdp_alive": False, "browser_family": None, "websocket_available": False},
            }
        )
    attachable = next((row["cdp_port"] for row in port_reports if row["canonical_edge_owner"] and row["cdp_probe"]["cdp_alive"] and row["cdp_probe"]["browser_family"] == CANONICAL_BROWSER_FAMILY), None)
    free_ports = [row["cdp_port"] for row in port_reports if row["status"] == "free"]
    chosen = attachable or (preferred if preferred in free_ports else (free_ports[0] if free_ports else None))
    status = "READY_TO_ATTACH" if attachable else ("READY_TO_LAUNCH" if chosen else "BLOCKED_NO_CANONICAL_CDP_PORT")
    return {
        "schema_version": REGISTRY_VERSION,
        "status": status,
        "recommended_cdp_port": chosen,
        "edge_binary_found": bool(find_edge_binary(env)),
        "profile_root_exists": CANONICAL_PROFILE_ROOT.exists(),
        "ports": port_reports,
        "registry": registry,
        "safety": {
            "raw_command_line_persisted": False,
            "cookies_read": False,
            "local_storage_read": False,
            "session_storage_read": False,
            "tokens_read": False,
        },
    }


def open_or_attach_canonical_edge(
    *,
    urls: Sequence[str],
    env: Mapping[str, str] | None = None,
    wait_seconds: float = 12.0,
) -> dict[str, Any]:
    """Reject direct browser execution outside the canonical production orchestrator."""
    quarantine(
        "contentops.direct_browser_profile_execution.v1",
        BROWSER_PROFILE_EXECUTION_QUARANTINED,
        "Direct canonical-profile launch/attach is quarantined; use ContentOpsProductionOrchestrator.",
    )
    doctor = browser_doctor(env=env)
    port = doctor.get("recommended_cdp_port")
    if not doctor["profile_root_exists"]:
        return {**doctor, "status": "BLOCKED_CANONICAL_PROFILE_ROOT_MISSING", "launched": False}
    if doctor["status"] == "READY_TO_ATTACH":
        return {**doctor, "status": "ATTACHED_CANONICAL_EDGE", "cdp_port": port, "launched": False}
    if doctor["status"] != "READY_TO_LAUNCH" or not isinstance(port, int):
        return {**doctor, "launched": False}
    binary = find_edge_binary(env)
    if not binary:
        return {**doctor, "status": "BLOCKED_MICROSOFT_EDGE_BINARY_NOT_FOUND", "launched": False}
    try:
        command = build_edge_command(binary, cdp_port=port, urls=urls)
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        return {**doctor, "status": "BLOCKED_CANONICAL_EDGE_LAUNCH_FAILED", "error_class": type(exc).__name__, "launched": False}
    deadline = time.monotonic() + max(wait_seconds, 1.0)
    final = doctor
    while time.monotonic() < deadline:
        time.sleep(0.5)
        final = browser_doctor(env=env)
        if final["status"] == "READY_TO_ATTACH" and final.get("recommended_cdp_port") == port:
            return {**final, "status": "LAUNCHED_CANONICAL_EDGE", "cdp_port": port, "launched": True}
    return {**final, "status": "BLOCKED_CANONICAL_EDGE_CDP_NOT_READY", "cdp_port": port, "launched": True}


def ensure_canonical_edge_publishing_runtime(
    *,
    authority_context: Mapping[str, Any],
    urls: Sequence[str] = ("https://substack.com/",),
    env: Mapping[str, str] | None = None,
    wait_seconds: float = 12.0,
) -> dict[str, Any]:
    """Launch/attach Edge only for the canonical production-orchestrator operation.

    Direct browser/profile CLIs remain quarantined.  The narrow authority context is nonsecret,
    exact, and deliberately unavailable as a default so importing this module cannot silently
    create a second browser-launch authority.
    """
    expected = {
        "entrypoint_id": "contentops.production_orchestrator.v1",
        "operation": "ensure_canonical_edge_publishing_runtime",
        "profile_id": CANONICAL_PROFILE_ID,
        "cdp_port": CANONICAL_PUBLISHING_CDP_PORT,
    }
    if dict(authority_context or {}) != expected:
        raise PublishingProfileError("canonical_production_orchestrator_authority_required")
    doctor = browser_doctor(env=env)
    port = doctor.get("recommended_cdp_port")
    if port not in (None, CANONICAL_PUBLISHING_CDP_PORT):
        return {**doctor, "status": "BLOCKED_NONCANONICAL_PUBLISHING_PORT", "launched": False}
    if not doctor["profile_root_exists"]:
        return {**doctor, "status": "BLOCKED_CANONICAL_PROFILE_ROOT_MISSING", "launched": False}
    if doctor["status"] == "READY_TO_ATTACH":
        return {
            **doctor,
            "status": "ATTACHED_CANONICAL_EDGE",
            "cdp_port": CANONICAL_PUBLISHING_CDP_PORT,
            "launched": False,
        }
    if doctor["status"] != "READY_TO_LAUNCH":
        return {**doctor, "launched": False}
    binary = find_edge_binary(env)
    if not binary:
        return {**doctor, "status": "BLOCKED_MICROSOFT_EDGE_BINARY_NOT_FOUND", "launched": False}
    try:
        command = build_edge_command(
            binary,
            cdp_port=CANONICAL_PUBLISHING_CDP_PORT,
            urls=urls,
        )
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        return {
            **doctor,
            "status": "BLOCKED_CANONICAL_EDGE_LAUNCH_FAILED",
            "error_class": type(exc).__name__,
            "launched": False,
        }
    deadline = time.monotonic() + max(wait_seconds, 1.0)
    final = doctor
    while time.monotonic() < deadline:
        time.sleep(0.5)
        final = browser_doctor(env=env)
        if final["status"] == "READY_TO_ATTACH":
            return {
                **final,
                "status": "LAUNCHED_CANONICAL_EDGE",
                "cdp_port": CANONICAL_PUBLISHING_CDP_PORT,
                "launched": True,
            }
    return {
        **final,
        "status": "BLOCKED_CANONICAL_EDGE_CDP_NOT_READY",
        "cdp_port": CANONICAL_PUBLISHING_CDP_PORT,
        "launched": True,
    }


def assert_canonical_edge_cdp(cdp_port: int) -> dict[str, Any]:
    report = browser_doctor()
    matching = next((row for row in report["ports"] if row["cdp_port"] == cdp_port), None)
    if not matching or not matching["canonical_edge_owner"]:
        raise PublishingProfileError("canonical_edge_profile_not_owner_of_requested_cdp_port")
    probe = matching["cdp_probe"]
    if not probe["cdp_alive"] or probe["browser_family"] != CANONICAL_BROWSER_FAMILY:
        raise PublishingProfileError("canonical_edge_cdp_probe_failed")
    return {"cdp_port": cdp_port, "profile_id": CANONICAL_PROFILE_ID, "browser_family": CANONICAL_BROWSER_FAMILY}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ContentOps canonical Edge publishing-profile doctor")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    open_parser = sub.add_parser("open")
    open_parser.add_argument("--url", action="append", default=["https://substack.com/"])
    args = parser.parse_args(argv)
    if args.command == "open":
        quarantine(
            "contentops.direct_browser_profile_execution.v1",
            BROWSER_PROFILE_EXECUTION_QUARANTINED,
            "Direct canonical-profile CLI execution is quarantined; use ContentOpsProductionOrchestrator.",
        )
    result = browser_doctor()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if str(result.get("status", "")).startswith(("READY", "ATTACHED", "LAUNCHED")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
