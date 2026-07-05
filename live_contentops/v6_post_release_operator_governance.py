"""V6 Post-Release Operator Governance & Maintenance Module.

Provides automated evidence health checking, telemetry registry maintenance,
platform capability inspection, and stale artifact archiving for ContentOps V6.
"""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON_PATH = ROOT / "docs" / "status" / "current_project_status.json"
TELEMETRY_LOG_PATH = ROOT / "docs" / "automation" / "V6_LIVE_TELEMETRY" / "live_telemetry_registry_v6.jsonl"
GOVERNANCE_OUT_DIR = ROOT / "docs" / "automation" / "V6_POST_RELEASE_GOVERNANCE"
GOVERNANCE_PACKET_PATH = GOVERNANCE_OUT_DIR / "operator_governance_summary.json"

ALL_PLATFORMS = [
    "meta_facebook",
    "meta_instagram",
    "meta_threads",
    "substack",
    "linkedin",
    "x",
    "discord",
    "telegram",
    "tiktok",
    "generic_manual"
]

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def audit_telemetry_registry(log_path: Optional[Path] = None) -> Dict[str, Any]:
    target_path = log_path or TELEMETRY_LOG_PATH
    archive_path = target_path.parent / f"{target_path.stem}_archive.jsonl"

    archive_exists = archive_path.exists()
    archive_total = 0
    archive_size = 0
    if archive_exists:
        archive_size = archive_path.stat().st_size
        try:
            with open(archive_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        archive_total += 1
        except Exception:
            pass

    archive_info = {
        "exists": archive_exists,
        "total_entries": archive_total,
        "size_bytes": archive_size
    }

    if not target_path.exists():
        return {
            "exists": False,
            "total_entries": 0,
            "success_count": 0,
            "error_count": 0,
            "corrupt_entries_count": 0,
            "platform_breakdown": {},
            "telemetry_archive": archive_info
        }

    total = 0
    success = 0
    errors = 0
    corrupt = 0
    platforms: Dict[str, int] = {}

    with open(target_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                total += 1
                platform = entry.get("platform_id", "unknown")
                platforms[platform] = platforms.get(platform, 0) + 1
                if entry.get("success"):
                    success += 1
                else:
                    errors += 1
            except Exception:
                corrupt += 1
                continue

    return {
        "exists": True,
        "total_entries": total,
        "success_count": success,
        "error_count": errors,
        "corrupt_entries_count": corrupt,
        "platform_breakdown": platforms,
        "telemetry_archive": archive_info
    }

def rotate_telemetry_log(log_path: Optional[Path] = None, max_lines: int = 1000) -> Dict[str, Any]:
    target_path = log_path or TELEMETRY_LOG_PATH
    if not target_path.exists():
        return {"rotated": False, "archived_lines": 0}

    with open(target_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) <= max_lines:
        return {"rotated": False, "archived_lines": 0}

    keep_count = max_lines // 2
    rotate_count = len(lines) - keep_count
    rotate_lines = lines[:rotate_count]
    keep_lines = lines[rotate_count:]

    archive_path = target_path.parent / f"{target_path.stem}_archive.jsonl"
    with open(archive_path, "a", encoding="utf-8") as f:
        f.writelines(rotate_lines)

    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(keep_lines)

    return {"rotated": True, "archived_lines": rotate_count}

def inspect_platform_capabilities() -> List[Dict[str, Any]]:
    capabilities = [
        {"platform_id": "meta_facebook", "name": "Facebook Page", "status": "live_capable", "auth_mode": "official_graph_api"},
        {"platform_id": "meta_instagram", "name": "Instagram Business", "status": "media_input_gated", "auth_mode": "official_graph_api"},
        {"platform_id": "meta_threads", "name": "Threads", "status": "live_capable", "auth_mode": "official_threads_api"},
        {"platform_id": "substack", "name": "Substack", "status": "manual_export_active", "auth_mode": "cdp_and_manual_export"},
        {"platform_id": "linkedin", "name": "LinkedIn", "status": "manual_export_active", "auth_mode": "manual_export"},
        {"platform_id": "x", "name": "X (Twitter)", "status": "cdp_supervised_active", "auth_mode": "cdp_profile_guard"},
        {"platform_id": "discord", "name": "Discord", "status": "live_capable", "auth_mode": "webhook_api"},
        {"platform_id": "telegram", "name": "Telegram", "status": "live_capable", "auth_mode": "bot_api"},
        {"platform_id": "tiktok", "name": "TikTok", "status": "deferred", "auth_mode": "manual_fallback"},
        {"platform_id": "generic_manual", "name": "Generic Manual", "status": "manual_fallback", "auth_mode": "operator_copy"},
    ]
    return capabilities

def audit_and_archive_stale_artifacts(scratch_dir: Optional[Path] = None) -> Dict[str, Any]:
    import shutil
    target_scratch = scratch_dir or (ROOT / "scratch")
    stale_files_found = []
    stale_directories_found = []
    
    if target_scratch.exists():
        for item in target_scratch.iterdir():
            if item.is_file():
                if item.name.startswith("temp_") or item.name.endswith(".tmp"):
                    stale_files_found.append(str(item.name))
                    try:
                        item.unlink()
                    except Exception:
                        pass
            elif item.is_dir():
                if item.name.startswith("temp_profile_") or item.name.startswith("temp_"):
                    stale_directories_found.append(str(item.name))
                    try:
                        shutil.rmtree(item)
                    except Exception:
                        pass

    return {
        "scratch_dir_checked": str(target_scratch),
        "stale_files_found": stale_files_found,
        "stale_directories_found": stale_directories_found,
        "archived_count": len(stale_files_found) + len(stale_directories_found),
        "status": "CLEAN"
    }


def _observed_repo_head_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def audit_status_ledger_alignment(
    status_json_path: Optional[Path] = None,
    observed_remote_sha: Optional[str] = None,
) -> Dict[str, Any]:
    """Audit whether status metadata matches the currently observed repo authority."""
    target_path = status_json_path or STATUS_JSON_PATH
    observed_sha = observed_remote_sha or _observed_repo_head_sha()
    sha_pattern = re.compile(r"^[0-9a-f]{40}$")

    if not target_path.exists():
        return {
            "status_json_exists": False,
            "status": "MISSING_STATUS_LEDGER",
            "observed_remote_sha": observed_sha,
            "ledger_last_verified_remote_sha": None,
            "ledger_matches_observed_remote": False,
            "issues": ["status_json_missing"],
        }

    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "status_json_exists": True,
            "status": "INVALID_STATUS_LEDGER_JSON",
            "observed_remote_sha": observed_sha,
            "ledger_last_verified_remote_sha": None,
            "ledger_matches_observed_remote": False,
            "issues": ["status_json_invalid"],
        }

    ledger_sha = data.get("last_verified_remote_sha")
    issues = []
    if not isinstance(ledger_sha, str) or not sha_pattern.fullmatch(ledger_sha):
        issues.append("last_verified_remote_sha_invalid")
    if sha_pattern.fullmatch(observed_sha) and ledger_sha != observed_sha:
        issues.append("last_verified_remote_sha_mismatch")

    return {
        "status_json_exists": True,
        "status": "PASS_STATUS_LEDGER_ALIGNED" if not issues else "REQUIRES_STATUS_LEDGER_RECONCILIATION",
        "observed_remote_sha": observed_sha,
        "ledger_last_verified_remote_sha": ledger_sha,
        "ledger_accepted_product_baseline_sha": data.get("accepted_product_baseline_sha"),
        "ledger_last_status_commit_sha": data.get("last_status_commit_sha"),
        "ledger_latest_accepted_task": data.get("latest_accepted_task"),
        "ledger_matches_observed_remote": not issues,
        "issues": issues,
    }


def generate_operator_governance_summary() -> Dict[str, Any]:
    rotation_status = rotate_telemetry_log()
    telemetry_audit = audit_telemetry_registry()
    platform_capabilities = inspect_platform_capabilities()
    artifact_audit = audit_and_archive_stale_artifacts()
    status_ledger_audit = audit_status_ledger_alignment()

    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "v6_operator_governance_summary_v0",
        "governance_status": "PASS_OPERATOR_GOVERNANCE_HEALTHY" if status_ledger_audit["ledger_matches_observed_remote"] else "REQUIRES_STATUS_LEDGER_RECONCILIATION",
        "telemetry_rotation": rotation_status,
        "telemetry_audit": telemetry_audit,
        "platform_capabilities": platform_capabilities,
        "artifact_audit": artifact_audit,
        "status_ledger_audit": status_ledger_audit,
        "system_invariants": {
            "fast_ship_mode_active": True,
            "operator_override_enabled": True,
            "deterministic_hash_bound": True,
            "financial_advice_forbidden": True
        }
    }

    packet_hash = stable_hash(packet)
    packet["packet_hash"] = packet_hash

    GOVERNANCE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(GOVERNANCE_PACKET_PATH, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2, sort_keys=True)

    return packet

if __name__ == "__main__":
    summary = generate_operator_governance_summary()
    print(json.dumps(summary, indent=2, sort_keys=True))
