"""Bounded, local-only operator controls for the canonical V1 Daily App.

This module deliberately exposes no caller-selected path or process identifier.  It owns
the small fixed log allowlist used by the loopback UI and the fail-closed shutdown
preflight shared by the HTTP control and the standalone PowerShell fallback.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from live_contentops.daily_app_ui_read_model_v1 import (
    DailyAppReadModelError,
    build_daily_app_snapshot,
    update_daily_app_mode,
)
from live_contentops.durable_operational_store_v1 import OperatingModeConflictError

SHUTDOWN_ENDPOINT = "/api/daily-app/control/shutdown-all-background"
LOGS_ENDPOINT = "/api/daily-app/background-logs"
HOURLY_AUDIT_ENDPOINT = "/api/daily-app/hourly-audit/latest"
MAX_LOG_LINES = 400
MAX_LOG_BYTES = 128 * 1024


class OperatorControlError(RuntimeError):
    """A bounded control could not be completed safely."""


@dataclass(frozen=True)
class LogSpec:
    stream: str
    relative_path: str
    label: str


LOG_ALLOWLIST = {
    spec.stream: spec
    for spec in (
        LogSpec("supervisor_stdout", "one_click_launcher/daily_app.supervisor.stdout.log", "Supervisor stdout"),
        LogSpec("supervisor_stderr", "one_click_launcher/daily_app.supervisor.stderr.log", "Supervisor stderr"),
        LogSpec("v5_ui", "one_click_launcher/v5_ui_server.log", "V5 UI server"),
        LogSpec("launcher", "one_click_launcher/launcher.log", "One-click launcher"),
        LogSpec("operator_shutdown", "one_click_launcher/operator_shutdown.log", "Operator shutdown"),
        LogSpec("hourly_audit", "hourly_audit/audit_history.jsonl", "Hourly runtime audit"),
    )
}

_REDACTION_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret|password|cookie|webhook)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+\-/=]{8,}"),
    re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{12,}\b"),
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def redact_log_text(text: str) -> str:
    """Defensively remove common credential forms from already-bounded log text."""
    clean = text
    for pattern in _REDACTION_PATTERNS:
        clean = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED]", clean)
    return clean


def _runtime_root_for_store(store_path: str | Path) -> Path:
    path = Path(store_path).resolve(strict=True)
    return path.parent


def available_log_streams() -> list[dict[str, str]]:
    return [{"stream": item.stream, "label": item.label} for item in LOG_ALLOWLIST.values()]


def read_allowlisted_log(store_path: str | Path, *, stream: str, lines: int = 160) -> dict[str, Any]:
    """Read a fixed runtime log tail; arbitrary paths and traversal are impossible."""
    if stream not in LOG_ALLOWLIST:
        raise OperatorControlError("LOG_STREAM_NOT_ALLOWLISTED")
    if isinstance(lines, bool) or not isinstance(lines, int) or not 1 <= lines <= MAX_LOG_LINES:
        raise OperatorControlError("LOG_LINE_LIMIT_INVALID")
    root = _runtime_root_for_store(store_path)
    spec = LOG_ALLOWLIST[stream]
    path = (root / spec.relative_path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:  # defensive invariant; specs are constants
        raise OperatorControlError("LOG_ALLOWLIST_PATH_INVALID") from exc
    # Older accepted launch procedures used a SHA-addressed supervisor stderr name.
    # Keep this fallback bounded to an exact 40-hex filename grammar and this one stream.
    if stream == "supervisor_stderr" and not path.is_file():
        sha_name = re.compile(r"daily_app\.supervisor\.[0-9a-f]{40}\.stderr\.log", re.IGNORECASE)
        candidates = [
            candidate for candidate in path.parent.glob("daily_app.supervisor.*.stderr.log")
            if candidate.is_file() and sha_name.fullmatch(candidate.name)
        ]
        if candidates:
            path = max(candidates, key=lambda candidate: candidate.stat().st_mtime_ns).resolve()
    if not path.is_file():
        return {
            "schema_version": "contentops.background_log_tail.v1",
            "stream": stream,
            "label": spec.label,
            "status": "LOG_NOT_YET_AVAILABLE",
            "line_count": 0,
            "truncated": False,
            "latest_timestamp_utc": None,
            "content": "",
        }
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > MAX_LOG_BYTES:
                handle.seek(-MAX_LOG_BYTES, 2)
            raw = handle.read(MAX_LOG_BYTES)
        decoded = raw.decode("utf-8", errors="replace")
    except OSError as exc:
        raise OperatorControlError("LOG_READ_FAILED") from exc
    selected = decoded.splitlines()[-lines:]
    content = redact_log_text("\n".join(selected))
    return {
        "schema_version": "contentops.background_log_tail.v1",
        "stream": stream,
        "label": spec.label,
        "status": "AVAILABLE",
        "line_count": len(selected),
        "truncated": size > len(raw) or len(decoded.splitlines()) > lines,
        "latest_timestamp_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        "content": content,
    }


def read_latest_hourly_audit(store_path: str | Path) -> dict[str, Any]:
    path = _runtime_root_for_store(store_path) / "hourly_audit" / "latest.json"
    if not path.is_file():
        return {
            "schema_version": "contentops.hourly_runtime_audit.latest_pointer.v1",
            "status": "AUDIT_NOT_YET_AVAILABLE",
            "classification": "UNKNOWN",
            "generated_at_utc": None,
        }
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise OperatorControlError("LATEST_AUDIT_UNREADABLE") from exc
    if not isinstance(value, Mapping):
        raise OperatorControlError("LATEST_AUDIT_INVALID")
    # The audit writer owns this fixed nonsecret schema.  Never return arbitrary siblings.
    return dict(value)


def _shutdown_blockers(snapshot: Mapping[str, Any]) -> list[str]:
    runtime = snapshot.get("runtime") if isinstance(snapshot.get("runtime"), Mapping) else {}
    today = snapshot.get("today") if isinstance(snapshot.get("today"), Mapping) else {}
    published = snapshot.get("published") if isinstance(snapshot.get("published"), Mapping) else {}
    trigger = runtime.get("operator_cycle_trigger") if isinstance(runtime.get("operator_cycle_trigger"), Mapping) else {}
    blockers: list[str] = []
    if runtime.get("active_editorial_cycle_window_id"):
        blockers.append("ACTIVE_EDITORIAL_CYCLE")
    if str(trigger.get("state") or "").upper() == "PENDING":
        blockers.append("OPERATOR_TRIGGER_PENDING")
    if int(published.get("unknown_write_count") or 0) > 0:
        blockers.append("UNKNOWN_WRITE_PRESENT")
    if int(published.get("pending_readback_count") or 0) > 0:
        blockers.append("PENDING_READBACK_PRESENT")
    if int(today.get("pending_lifecycle_recovery_count") or 0) > 0:
        blockers.append("PENDING_LIFECYCLE_RECOVERY_PRESENT")
    return blockers


def prepare_safe_shutdown(
    store_path: str | Path,
    *,
    expected_state_version: int | None = None,
) -> dict[str, Any]:
    """Fail closed on active/ambiguous work, then establish KILL_SWITCH by CAS."""
    snapshot = build_daily_app_snapshot(store_path)
    controls = snapshot["controls"]
    actual_version = int(controls["state_version"])
    if expected_state_version is not None and int(expected_state_version) != actual_version:
        raise OperatorControlError("SHUTDOWN_CONTROL_STATE_CONFLICT")
    blockers = _shutdown_blockers(snapshot)
    if blockers:
        raise OperatorControlError("SHUTDOWN_BLOCKED:" + ",".join(blockers))
    if controls["current_mode"] != "KILL_SWITCH":
        try:
            control = update_daily_app_mode(
                store_path,
                expected_state_version=actual_version,
                operating_mode="KILL_SWITCH",
            )
        except OperatingModeConflictError as exc:
            raise OperatorControlError("SHUTDOWN_KILL_SWITCH_CAS_CONFLICT") from exc
        actual_version = int(control["state_version"])
    return {
        "schema_version": "contentops.safe_background_shutdown_preflight.v1",
        "status": "SAFE_TO_STOP_PROVEN_BACKGROUND_PROCESSES",
        "kill_switch_active": True,
        "state_version": actual_version,
        "active_or_ambiguous_work": False,
        "checked_at_utc": utc_now_iso(),
    }


def spawn_shutdown_fallback(*, repo_root: Path, store_path: Path) -> int:
    """Launch only the fixed repository shutdown script with no browser-controlled args."""
    script = (repo_root / "scripts" / "Stop-ContentOpsBackground.ps1").resolve(strict=True)
    log_path = _runtime_root_for_store(store_path) / "one_click_launcher" / "operator_shutdown.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as output:
        process = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            cwd=str(repo_root),
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0),
            close_fds=True,
        )
    return int(process.pid)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ContentOps V1 bounded operator control helper")
    sub = parser.add_subparsers(dest="command", required=True)
    preflight = sub.add_parser("shutdown-preflight")
    preflight.add_argument("--store", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = prepare_safe_shutdown(args.store)
    except (OperatorControlError, DailyAppReadModelError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
