"""Manual distribution registry source-path audit v6.

Deterministic local verification for registry source packet bindings.
No network, env, credential, browser, provider, or live platform action is performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from live_contentops.manual_distribution_evidence_registry_v6 import (
    HASH_FIELDS,
    PACKET_ID_FIELDS,
    ROOT,
    build_manual_distribution_evidence_registry,
)

PACKET_ROLES = ("export", "approval", "handoff", "url", "metrics")
SAFETY_FLAGS = {
    "network_call_made": False,
    "provider_call_made": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "browser_session_used": False,
    "public_url_fetch_made": False,
    "live_publish_performed_by_contentops": False,
}


def _is_url_like(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or lowered.startswith(("http:", "https:", "www."))


def _first_present_with_field(packet: dict[str, Any], fields: tuple[str, ...]) -> tuple[str, str]:
    for field in fields:
        value = packet.get(field)
        if value:
            return field, str(value)
    return fields[0], ""


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_manual_distribution_registry_source_path_audit(
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic local source-path audit for registry bindings."""
    registry = registry or build_manual_distribution_evidence_registry()
    platforms: list[dict[str, Any]] = []

    for platform in registry["platforms"]:
        role_checks: dict[str, Any] = {}
        for role in PACKET_ROLES:
            binding = platform["source_packets"][role]
            source_path = str(binding["source_path"])
            full_path = ROOT / source_path
            path_exists = full_path.is_file()
            within_docs_automation = source_path.startswith("docs/automation/") and ".." not in Path(source_path).parts
            path_url_like = _is_url_like(source_path)
            source_packet = json.loads(full_path.read_text(encoding="utf-8")) if path_exists else {}
            expected_packet_id_field = PACKET_ID_FIELDS[role]
            expected_hash_field, observed_hash = _first_present_with_field(source_packet, HASH_FIELDS[role])
            observed_packet_id = str(source_packet.get(expected_packet_id_field, ""))

            role_checks[role] = {
                "source_path": source_path,
                "path_exists": path_exists,
                "path_within_docs_automation": within_docs_automation,
                "path_url_like": path_url_like,
                "packet_id_field": expected_packet_id_field,
                "registry_packet_id": str(binding["packet_id"]),
                "observed_packet_id": observed_packet_id,
                "packet_id_matches": str(binding["packet_id"]) == observed_packet_id,
                "hash_field": expected_hash_field,
                "registry_hash": str(binding["hash"]),
                "observed_hash": observed_hash,
                "hash_matches": str(binding["hash"]) == observed_hash,
            }

        platforms.append({
            "platform": platform["platform"],
            "platform_label": platform["platform_label"],
            "roles": role_checks,
        })

    role_records = [role for platform in platforms for role in platform["roles"].values()]
    audit = {
        "schema_version": "6.0.0",
        "audit_kind": "manual_distribution_registry_source_path_audit_v0",
        "registry_packet_id": registry["registry_packet_id"],
        "registry_hash": registry["registry_hash"],
        "source_path_audit_status": "passed",
        "platforms": platforms,
        "all_paths_exist": all(record["path_exists"] for record in role_records),
        "all_packet_ids_match": all(record["packet_id_matches"] for record in role_records),
        "all_hashes_match": all(record["hash_matches"] for record in role_records),
        "all_paths_within_docs_automation": all(record["path_within_docs_automation"] for record in role_records),
        "no_url_like_source_paths": all(not record["path_url_like"] for record in role_records),
        **SAFETY_FLAGS,
    }
    audit["source_path_audit_status"] = "passed" if all([
        audit["all_paths_exist"],
        audit["all_packet_ids_match"],
        audit["all_hashes_match"],
        audit["all_paths_within_docs_automation"],
        audit["no_url_like_source_paths"],
    ]) else "failed"
    audit["exact_payload_hash"] = _stable_hash(audit)
    audit["audit_packet_id"] = f"manual_distribution_registry_source_path_audit_{audit['exact_payload_hash'][:16]}"
    return audit
