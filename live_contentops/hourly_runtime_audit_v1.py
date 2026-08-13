"""Independent, read-only hourly audit for the canonical ContentOps V1 runtime.

The audit performs loopback/process/CDP/store readback only.  It never invokes a model,
browser automation, provider, publisher, restart, reconciliation, or control mutation.
Its only writes are compact audit artifacts under the fixed runtime audit directory.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from live_contentops.daily_app_launcher_v1 import collect_port_inventory, is_canonical_daily_app_command_line
from live_contentops.daily_app_ui_read_model_v1 import DailyAppReadModelError, build_daily_app_snapshot
from live_contentops.operator_control_plane_v1 import OperatorControlError, read_allowlisted_log

SCHEMA_VERSION = "contentops.hourly_runtime_audit.v1"
TASK_NAME = "CapitalChronicle_ContentOps_V1_Hourly_Audit"
DEFAULT_API_PORT = 5174
MAX_HISTORY_RECORDS = 24 * 14
RETENTION_DAYS = 14
_SHA_LOG = re.compile(r"^daily_app\.supervisor\.([0-9a-f]{40})\.stderr\.log$", re.IGNORECASE)
_BENIGN_STDERR_PATTERNS = (
    re.compile(r"\[DEP0169\].*DeprecationWarning:.*url\.parse\(\)", re.IGNORECASE),
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_seconds(value: Any, now: datetime) -> float | None:
    parsed = _parse_time(value)
    return round(max(0.0, (now - parsed).total_seconds()), 3) if parsed else None


def _get_json(url: str, *, timeout: float = 4.0) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return dict(value) if isinstance(value, Mapping) else None


def _git_sha(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(repo_root), capture_output=True,
            text=True, timeout=10, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip().lower()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def _runtime_source_sha(runtime_root: Path) -> tuple[str | None, str]:
    identity = runtime_root / "one_click_launcher" / "runtime_identity_v1.json"
    try:
        value = json.loads(identity.read_text(encoding="utf-8"))
        sha = str(value.get("source_sha") or "").lower() if isinstance(value, Mapping) else ""
        if re.fullmatch(r"[0-9a-f]{40}", sha):
            return sha, "RUNTIME_IDENTITY_ARTIFACT"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        pass
    log_root = runtime_root / "one_click_launcher"
    candidates: list[tuple[int, str]] = []
    try:
        for path in log_root.glob("daily_app.supervisor.*.stderr.log"):
            match = _SHA_LOG.fullmatch(path.name)
            if match and path.is_file():
                candidates.append((path.stat().st_mtime_ns, match.group(1).lower()))
    except OSError:
        return None, "RUNTIME_SOURCE_UNAVAILABLE"
    if candidates:
        return max(candidates)[1], "BOUNDED_SHA_LOG_IDENTITY"
    return None, "RUNTIME_SOURCE_UNAVAILABLE"


def _cdp_status(port: int) -> dict[str, Any]:
    value = _get_json(f"http://127.0.0.1:{port}/json/version", timeout=2.0)
    browser = str((value or {}).get("Browser") or "")
    return {
        "port": port,
        "state": "READY" if value else "UNAVAILABLE",
        "browser_family": browser.split("/", 1)[0] if browser else None,
        "protocol_version": (value or {}).get("Protocol-Version"),
    }


def _scheduled_task_state() -> dict[str, Any]:
    command = (
        "$t=Get-ScheduledTask -TaskName '" + TASK_NAME + "' -ErrorAction Stop;"
        "$i=Get-ScheduledTaskInfo -TaskName '" + TASK_NAME + "' -ErrorAction Stop;"
        "$a=$t.Actions | Select-Object -First 1;"
        "[ordered]@{state=[string]$t.State;next_run_time=$i.NextRunTime.ToUniversalTime().ToString('o');"
        "last_run_time=$i.LastRunTime.ToUniversalTime().ToString('o');last_result=$i.LastTaskResult;"
        "action_execute=[string]$a.Execute;action_arguments=[string]$a.Arguments;"
        "working_directory=[string]$a.WorkingDirectory}|ConvertTo-Json -Compress"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=15, check=True,
        )
        value = json.loads(result.stdout.strip())
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {"installed": False, "state": "NOT_INSTALLED_OR_UNAVAILABLE", "next_run_utc": None}
    return {
        "installed": True,
        "state": value.get("state"),
        "next_run_utc": value.get("next_run_time"),
        "last_run_utc": value.get("last_run_time"),
        "last_result": value.get("last_result"),
        "action_execute": value.get("action_execute"),
        "action_arguments": value.get("action_arguments"),
        "working_directory": value.get("working_directory"),
    }


def _recent_stderr_signal(store_path: Path) -> dict[str, Any]:
    try:
        tail = read_allowlisted_log(store_path, stream="supervisor_stderr", lines=200)
    except OperatorControlError:
        return {
            "status": "UNAVAILABLE", "error_lines": 0, "warning_lines": 0,
            "informational_noise_lines": 0,
        }
    lines = str(tail.get("content") or "").splitlines()
    informational = [
        line for line in lines if any(pattern.search(line) for pattern in _BENIGN_STDERR_PATTERNS)
    ]
    actionable = [line for line in lines if line not in informational]
    errors = sum(
        1 for line in actionable
        if re.search(
            r"(?i)(?:\b(?:error|exception|traceback|critical)\b|\b[A-Za-z_][A-Za-z0-9_]*Error\b)",
            line,
        )
    )
    warnings = sum(1 for line in actionable if re.search(r"(?i)\bwarn(?:ing)?\b", line))
    return {
        "status": tail.get("status"),
        "sampled_lines": len(lines),
        "error_lines": errors,
        "warning_lines": warnings,
        "informational_noise_lines": len(informational),
        "informational_noise_classes": ["NODE_DEP0169_URL_PARSE_DEPRECATION"] if informational else [],
        "truncated": bool(tail.get("truncated")),
    }


def _headline_runtime_signal(now: datetime) -> dict[str, Any]:
    from live_contentops.headline_data_root_v1 import (
        canonical_headline_data_root,
        canonical_headline_sidecar_glob,
    )
    from live_contentops.newsroom_assignment_scheduler_v1 import (
        load_rolling_x_headline_sidecars,
    )

    data_root = canonical_headline_data_root()
    try:
        intake = load_rolling_x_headline_sidecars(
            cutoff_utc=now, sidecar_glob=canonical_headline_sidecar_glob(), window_hours=24.0
        )
        headlines = intake.get("headlines") or []
        newest = max(
            (str(row.get("source_timestamp_utc") or "") for row in headlines),
            default=None,
        )
        counts = intake.get("counts") if isinstance(intake.get("counts"), Mapping) else {}
        return {
            "canonical_data_root": str(data_root),
            "canonical_sidecar_glob": canonical_headline_sidecar_glob(),
            "data_root_exists": data_root.is_dir(),
            "source_file_count": int(counts.get("source_files") or 0),
            "source_row_count": int(counts.get("source_rows") or 0),
            "rolling_24h_unique_count": len(headlines),
            "newest_source_event_utc": newest,
            "canonical_input_hash": intake.get("canonical_input_hash"),
            "status": "READY",
        }
    except Exception as exc:
        return {
            "canonical_data_root": str(data_root),
            "canonical_sidecar_glob": canonical_headline_sidecar_glob(),
            "data_root_exists": data_root.is_dir(),
            "source_file_count": 0,
            "source_row_count": 0,
            "rolling_24h_unique_count": None,
            "newest_source_event_utc": None,
            "canonical_input_hash": None,
            "status": "UNAVAILABLE:" + type(exc).__name__,
        }


def _classify(report: Mapping[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    action_required = False
    runtime = report["runtime"]
    safety = report["safety"]
    if runtime["supervisor_count"] > 1:
        return "ACTION_REQUIRED", ["DUPLICATE_CANONICAL_SUPERVISOR"]
    if safety["unknown_write_count"] or safety["pending_readback_count"] or safety["pending_lifecycle_recovery_count"]:
        return "ACTION_REQUIRED", ["WRITE_OR_READBACK_AMBIGUITY_PRESENT"]
    critical_auth_states = {
        "REAUTH_REQUIRED", "AUTH_INVALID", "IDENTITY_MISMATCH", "PERMISSION_MISSING",
    }
    for row in report["destinations"]:
        platform = str(row.get("platform_id") or "")
        readiness = str(row.get("readiness") or "")
        if platform == "linkedin" and readiness in {
            *critical_auth_states, "EXCLUDED_PENDING_OFFICIAL_API_MIGRATION",
        }:
            reasons.append("LINKEDIN_EXCLUDED_PENDING_OFFICIAL_API_MIGRATION")
        elif readiness in critical_auth_states:
            reasons.append(f"DESTINATION_AUTH_REQUIRED:{platform or 'unknown'}")
            action_required = True
    if runtime["supervisor_count"] != 1 or runtime["api_health"] != "LOOPBACK_API_HEALTHY":
        reasons.append("CANONICAL_RUNTIME_UNAVAILABLE")
        action_required = True
    if runtime["source_sha_match"] is not True:
        reasons.append("RUNTIME_SOURCE_SHA_UNPROVEN_OR_MISMATCH")
        action_required = True
    if runtime["controller_health"] != "HEALTHY":
        reasons.append("CONTROLLER_NOT_HEALTHY")
        action_required = True
    heartbeat_age = runtime.get("heartbeat_age_seconds")
    if heartbeat_age is None or heartbeat_age > 180:
        reasons.append("HEARTBEAT_STALE_OR_UNAVAILABLE")
        action_required = True
    headline_age = runtime.get("headline_ingest_age_seconds")
    if (
        runtime.get("headline_lane_state") == "PAUSED_KILL_SWITCH"
        and runtime.get("operating_mode") == "KILL_SWITCH"
    ):
        reasons.append("HEADLINE_INGESTION_PAUSED_BY_KILL_SWITCH")
    elif runtime.get("headline_lane_state") != "RUNNING" or headline_age is None or headline_age > 900:
        reasons.append("HEADLINE_INGESTION_DEGRADED_OR_STALE")
        action_required = True
    if report["browsers"]["chrome_9222"]["state"] != "READY":
        reasons.append("CHROME_9222_UNAVAILABLE")
        action_required = True
    if report["browsers"]["edge_9223"]["state"] != "READY":
        reasons.append("EDGE_9223_UNAVAILABLE")
        action_required = True
    if report["stderr_signal"]["error_lines"]:
        reasons.append("RECENT_SUPERVISOR_STDERR_ERROR_SIGNAL")
        action_required = True
    elif report["stderr_signal"].get("warning_lines"):
        reasons.append("RECENT_SUPERVISOR_STDERR_WARNING_SIGNAL")
    if reasons:
        return ("ACTION_REQUIRED" if action_required else "DEGRADED"), reasons
    return "PASS", ["ALL_REQUIRED_READ_ONLY_CHECKS_PASS"]


def build_hourly_audit(
    *, store_path: str | Path, repo_root: str | Path, api_port: int = DEFAULT_API_PORT,
    now: datetime | None = None,
) -> dict[str, Any]:
    generated = (now or _utc_now()).astimezone(timezone.utc)
    store = Path(store_path).resolve(strict=True)
    root = Path(repo_root).resolve(strict=True)
    runtime_root = store.parent
    health = _get_json(f"http://127.0.0.1:{api_port}/api/health") or {}
    api_snapshot = _get_json(f"http://127.0.0.1:{api_port}/api/daily-app/snapshot")
    try:
        snapshot = api_snapshot or build_daily_app_snapshot(store, now=generated)
        snapshot_source = "LOOPBACK_API" if api_snapshot else "QUERY_ONLY_STORE_FALLBACK"
    except DailyAppReadModelError as exc:
        snapshot = {}
        snapshot_source = "UNAVAILABLE:" + str(exc)
    inventory = collect_port_inventory(api_port)
    canonical = [
        row for row in inventory.supervisor_processes
        if is_canonical_daily_app_command_line(str(row.get("cmd") or ""), str(store))
    ]
    expected_sha = _git_sha(root)
    current_sha, sha_source = _runtime_source_sha(runtime_root)
    runtime = snapshot.get("runtime") if isinstance(snapshot.get("runtime"), Mapping) else {}
    published = snapshot.get("published") if isinstance(snapshot.get("published"), Mapping) else {}
    today = snapshot.get("today") if isinstance(snapshot.get("today"), Mapping) else {}
    current_cycle = today.get("current_cycle") if isinstance(today.get("current_cycle"), Mapping) else {}
    headline = runtime.get("headline_ingestion") if isinstance(runtime.get("headline_ingestion"), Mapping) else {}
    destinations = (snapshot.get("platforms") or {}).get("destinations", []) if isinstance(snapshot.get("platforms"), Mapping) else []
    headline_runtime = _headline_runtime_signal(generated)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _iso(generated),
        "classification": "UNKNOWN",
        "classification_reasons": [],
        "read_only": True,
        "runtime": {
            "api_health": health.get("status", "UNAVAILABLE"),
            "snapshot_source": snapshot_source,
            "supervisor_count": len(canonical),
            "store_identity": store.name,
            "expected_source_sha": expected_sha,
            "current_runtime_source_sha": current_sha,
            "runtime_source_sha_evidence": sha_source,
            "source_sha_match": bool(expected_sha and current_sha and expected_sha == current_sha),
            "controller_health": runtime.get("controller_health", "UNAVAILABLE"),
            "heartbeat_at_utc": runtime.get("latest_heartbeat_at_utc"),
            "heartbeat_age_seconds": _age_seconds(runtime.get("latest_heartbeat_at_utc"), generated),
            "operating_mode": runtime.get("operating_mode", "UNAVAILABLE"),
            "kill_switch_active": bool(runtime.get("kill_switch_active")),
            "active_cycle_id": runtime.get("active_editorial_cycle_window_id"),
            "active_cycle_age_seconds": _age_seconds(current_cycle.get("updated_at_utc"), generated) if runtime.get("active_editorial_cycle_window_id") else None,
            "headline_lane_state": headline.get("lane_state", "UNAVAILABLE"),
            "last_headline_ingest_utc": headline.get("last_ingest_utc"),
            "headline_ingest_age_seconds": _age_seconds(headline.get("last_ingest_utc"), generated),
        },
        "browsers": {"chrome_9222": _cdp_status(9222), "edge_9223": _cdp_status(9223)},
        "destinations": [
            {
                "platform_id": row.get("platform_id"),
                "readiness": row.get("readiness"),
                "identity_match": row.get("identity_match"),
                "write_eligible": row.get("write_eligible"),
            }
            for row in destinations if isinstance(row, Mapping)
        ],
        "safety": {
            "unknown_write_count": int(published.get("unknown_write_count") or 0),
            "pending_readback_count": int(published.get("pending_readback_count") or 0),
            "pending_lifecycle_recovery_count": int(today.get("pending_lifecycle_recovery_count") or 0),
        },
        "stderr_signal": _recent_stderr_signal(store),
        "headline_operational_data": headline_runtime,
        "scheduled_task": _scheduled_task_state(),
        "side_effects": "AUDIT_ARTIFACT_WRITES_ONLY",
    }
    classification, reasons = _classify(report)
    report["classification"] = classification
    report["classification_reasons"] = reasons
    return report


def write_audit_artifacts(report: Mapping[str, Any], *, runtime_root: str | Path) -> dict[str, str]:
    root = Path(runtime_root).resolve() / "hourly_audit"
    root.mkdir(parents=True, exist_ok=True)
    latest = root / "latest.json"
    history = root / "audit_history.jsonl"
    serialized = json.dumps(dict(report), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    fd, temporary_name = tempfile.mkstemp(prefix="latest.", suffix=".tmp", dir=str(root))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized + "\n")
        os.replace(temporary_name, latest)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    cutoff = _utc_now() - timedelta(days=RETENTION_DAYS)
    retained: list[str] = []
    if history.is_file():
        try:
            for line in history.read_text(encoding="utf-8").splitlines()[-MAX_HISTORY_RECORDS:]:
                try:
                    item = json.loads(line)
                    when = _parse_time(item.get("generated_at_utc")) if isinstance(item, Mapping) else None
                    if when is not None and when >= cutoff:
                        retained.append(json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
                except json.JSONDecodeError:
                    continue
        except OSError:
            retained = []
    retained.append(serialized)
    history.write_text("\n".join(retained[-MAX_HISTORY_RECORDS:]) + "\n", encoding="utf-8")
    return {"latest": str(latest), "history": str(history)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the independent ContentOps V1 hourly audit")
    parser.add_argument("--store", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--api-port", type=int, default=DEFAULT_API_PORT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        report = build_hourly_audit(store_path=args.store, repo_root=args.repo_root, api_port=args.api_port)
        artifacts = write_audit_artifacts(report, runtime_root=Path(args.store).resolve().parent)
    except Exception as exc:  # fail visible; never attempt repair/restart
        print(json.dumps({"classification": "ACTION_REQUIRED", "error": type(exc).__name__}, sort_keys=True))
        return 2
    print(json.dumps({"classification": report["classification"], "artifacts": artifacts}, sort_keys=True))
    return 0 if report["classification"] in {"PASS", "DEGRADED", "ACTION_REQUIRED"} else 2


if __name__ == "__main__":
    sys.exit(main())
