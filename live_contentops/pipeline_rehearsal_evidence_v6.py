"""V6 pipeline rehearsal evidence packet and readback helpers.

Keeps live/dry-run pipeline rehearsal evidence deterministic, local, and safe to
commit. The packet records status/audit consistency without storing raw secrets.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_PIPELINE_LIVE_REHEARSAL_AND_EVIDENCE_READBACK_V0"
SCHEMA_VERSION = "1.0.0"
DEFAULT_EVIDENCE_DIR = Path("docs/automation/V6_PIPELINE_LIVE_REHEARSAL_AND_EVIDENCE_READBACK")
DEFAULT_EVIDENCE_PACKET_PATH = DEFAULT_EVIDENCE_DIR / "rehearsal_evidence_packet.json"
DEFAULT_READBACK_SUMMARY_PATH = DEFAULT_EVIDENCE_DIR / "rehearsal_readback_summary.md"
SECRET_MARKERS = ("api_key", "apikey", "token", "secret", "password", "cookie", "authorization", "bearer")


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def load_json_if_exists(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


def capture_repo_state() -> dict[str, Any]:
    def run_git(args: list[str]) -> str:
        try:
            return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return ""

    return {
        "repo_full_name": "fatcat2109/capital-chronicle-contentops",
        "branch": run_git(["branch", "--show-current"]),
        "head_sha": run_git(["rev-parse", "HEAD"]),
        "remote_master_sha": run_git(["ls-remote", "origin", "refs/heads/master"]).split("\t", 1)[0],
        "dirty_state_short": run_git(["status", "--short"]),
    }


def _safe_result_excerpt(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": result.get("run_id"),
        "pipeline_status": result.get("pipeline_status"),
        "article_packet_id": result.get("article_packet_id"),
        "platform_variant_packet_id": result.get("platform_variant_packet_id"),
        "variant_status": result.get("variant_status"),
        "dispatch_audit_path": result.get("dispatch_audit_path"),
        "dispatch_live": result.get("dispatch_live", False),
        "dispatch_rehearsal": result.get("dispatch_rehearsal", False),
        "dry_run": result.get("dry_run"),
        "public_write": result.get("public_write"),
        "live_platform_api_called": result.get("live_platform_api_called"),
        "credential_lookup_performed": result.get("credential_lookup_performed"),
        "dispatch_blocked": result.get("dispatch_blocked", False),
        "dispatch_blockers": result.get("dispatch_blockers", []),
        "dispatch_summary": result.get("dispatch_summary", {}),
        "quality_gate_result": result.get("quality_gate_result", {}),
        "approval_marker_envelope": result.get("approval_marker_envelope", {}),
        "headline_rehearsal_context": result.get("headline_rehearsal_context", {}),
        "timestamp": result.get("timestamp"),
        "timestamp_gmt7": result.get("timestamp_gmt7"),
    }


def _audit_excerpt(audit: dict[str, Any] | None) -> dict[str, Any]:
    if not audit:
        return {}
    return {
        "run_id": audit.get("run_id"),
        "pipeline_status": audit.get("pipeline_status"),
        "dispatch_live": audit.get("dispatch_live", False),
        "dispatch_rehearsal": audit.get("dispatch_rehearsal", False),
        "dry_run": audit.get("dry_run"),
        "public_write": audit.get("public_write"),
        "dispatch_blocked": audit.get("dispatch_blocked", False),
        "dispatch_summary": audit.get("dispatch_summary", {}),
        "dispatch_blockers": audit.get("dispatch_blockers", []),
        "timestamp": audit.get("timestamp"),
    }


def readback_checks(result: dict[str, Any], audit: dict[str, Any] | None) -> dict[str, Any]:
    result_summary = result.get("dispatch_summary", {})
    audit_summary = audit.get("dispatch_summary", {}) if audit else {}
    checks = {
        "audit_file_present": audit is not None,
        "run_id_matches": bool(audit) and audit.get("run_id") == result.get("run_id"),
        "pipeline_status_matches": bool(audit) and audit.get("pipeline_status") == result.get("pipeline_status"),
        "dispatch_summary_matches": bool(audit) and audit_summary == result_summary,
    }
    checks["readback_ready"] = all(checks.values()) if result.get("dispatch_live") or result.get("dispatch_blocked") or result.get("dispatch_rehearsal") else True
    return checks


def contains_secret_marker(data: Any) -> bool:
    serialized = json.dumps(data, sort_keys=True, default=str).lower()
    return any(marker in serialized for marker in SECRET_MARKERS)


def build_rehearsal_evidence_packet(
    result: dict[str, Any],
    *,
    command: list[str] | None = None,
    mode: str = "controlled_rehearsal",
    repo_state: dict[str, Any] | None = None,
    audit_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    should_bind_audit = bool(result.get("dispatch_live") or result.get("dispatch_blocked") or result.get("dispatch_rehearsal"))
    if audit_packet is None and should_bind_audit:
        audit_packet = load_json_if_exists(result.get("dispatch_audit_path"))
    elif not should_bind_audit:
        audit_packet = None
    core = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "packet_kind": "v6_pipeline_rehearsal_evidence_packet",
        "created_at": _utc_now(),
        "mode": mode,
        "command": command or [],
        "repo_state": repo_state or capture_repo_state(),
        "pipeline_result": _safe_result_excerpt(result),
        "dispatch_audit_excerpt": _audit_excerpt(audit_packet),
        "readback_checks": readback_checks(result, audit_packet),
        "safety": {
            "raw_sensitive_values_persisted": False,
            "raw_env_values_persisted": False,
            "browser_session_sensitive_value_persisted": False,
            "audit_excerpt_only": True,
        },
    }
    core["sensitive_marker_detected"] = contains_secret_marker(core)
    core["evidence_hash"] = stable_hash(core)
    core["evidence_packet_id"] = f"v6_pipeline_rehearsal_{core['evidence_hash'][:16]}"
    return core


def write_rehearsal_evidence(packet: dict[str, Any], output_path: str | Path = DEFAULT_EVIDENCE_PACKET_PATH) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readback_summary(packet, path.parent / "rehearsal_readback_summary.md")
    return path


def write_readback_summary(packet: dict[str, Any], output_path: str | Path = DEFAULT_READBACK_SUMMARY_PATH) -> Path:
    checks = packet.get("readback_checks", {})
    result = packet.get("pipeline_result", {})
    summary = result.get("dispatch_summary", {})
    lines = [
        "# V6 Pipeline Rehearsal Readback Summary",
        "",
        f"- Task: `{packet.get('task_label')}`",
        f"- Evidence packet: `{packet.get('evidence_packet_id')}`",
        f"- Evidence hash: `{packet.get('evidence_hash')}`",
        f"- Pipeline status: `{result.get('pipeline_status')}`",
        f"- Run ID: `{result.get('run_id')}`",
        f"- Audit present: `{checks.get('audit_file_present')}`",
        f"- Run ID matches audit: `{checks.get('run_id_matches')}`",
        f"- Status matches audit: `{checks.get('pipeline_status_matches')}`",
        f"- Dispatch summary matches audit: `{checks.get('dispatch_summary_matches')}`",
        f"- Successful platforms: `{summary.get('successful_platforms', [])}`",
        f"- Failed platforms: `{summary.get('failed_platforms', [])}`",
        f"- Blocked platforms: `{summary.get('blocked_platforms', [])}`",
        f"- Sensitive marker detected in committed packet: `{packet.get('sensitive_marker_detected')}`",
        "",
    ]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
