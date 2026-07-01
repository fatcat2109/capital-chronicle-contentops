"""Manual distribution registry audit index v6.

Local readiness index binding the registry packet and source-path audit packet.
This is operator-review-only readiness, not live/API/platform readiness.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from live_contentops.manual_distribution_evidence_registry_v6 import build_manual_distribution_evidence_registry
from live_contentops.manual_distribution_evidence_registry_source_path_audit_v6 import (
    build_manual_distribution_registry_source_path_audit,
)

SAFETY_FLAGS = {
    "network_call_made": False,
    "provider_call_made": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "browser_session_used": False,
    "public_url_fetch_made": False,
    "live_publish_performed_by_contentops": False,
    "enabled_publish_send_dispatch_approve_controls": False,
}

BLOCKERS = [
    "live/provider/platform execution disabled",
    "platform API/auth/dispatch readiness is out of scope",
    "approve/send/publish/dispatch/schedule controls remain blocked",
]

CAVEATS = [
    "fixture/operator-supplied/manual only",
    "public URL reachability is not verified",
    "platform-side state is not proven",
    "operator review is required before any external manual action",
]


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _all_registry_safety_false(registry: dict[str, Any]) -> bool:
    for platform in registry["platforms"]:
        flags = platform["safety_flags"]
        if any(flags.values()):
            return False
    return True


def build_manual_distribution_registry_audit_index() -> dict[str, Any]:
    """Build deterministic operator-review-only audit readiness index."""
    registry = build_manual_distribution_evidence_registry()
    source_path_audit = build_manual_distribution_registry_source_path_audit(registry)
    readiness_inputs = [
        bool(registry.get("registry_packet_id")),
        registry.get("registry_status") == "fixture_manual_operator_supplied_only",
        source_path_audit["source_path_audit_status"] == "passed",
        source_path_audit["all_paths_exist"],
        source_path_audit["all_packet_ids_match"],
        source_path_audit["all_hashes_match"],
        source_path_audit["all_paths_within_docs_automation"],
        source_path_audit["no_url_like_source_paths"],
        _all_registry_safety_false(registry),
        not any(SAFETY_FLAGS.values()),
    ]
    readiness_status = "ready_for_manual_operator_review_only" if all(readiness_inputs) else "blocked_for_manual_operator_review"
    audit_index = {
        "schema_version": "6.0.0",
        "audit_index_kind": "manual_distribution_registry_audit_index_v0",
        "registry_packet_id": registry["registry_packet_id"],
        "registry_hash": registry["registry_hash"],
        "source_path_audit_packet_id": source_path_audit["audit_packet_id"],
        "source_path_audit_hash": source_path_audit["exact_payload_hash"],
        "platforms_included": [platform["platform_label"] for platform in registry["platforms"]],
        "registry_status": registry["registry_status"],
        "source_path_audit_status": source_path_audit["source_path_audit_status"],
        "all_paths_exist": source_path_audit["all_paths_exist"],
        "all_packet_ids_match": source_path_audit["all_packet_ids_match"],
        "all_hashes_match": source_path_audit["all_hashes_match"],
        "all_paths_within_docs_automation": source_path_audit["all_paths_within_docs_automation"],
        "no_url_like_source_paths": source_path_audit["no_url_like_source_paths"],
        "registry_readiness_status": readiness_status,
        "blockers": BLOCKERS,
        "caveats": CAVEATS,
        "next_manual_operator_action": "review committed registry and audit packets locally; do not dispatch or perform live platform actions from ContentOps",
        "non_readiness_claims": {
            "live_readiness_claimed": False,
            "api_readiness_claimed": False,
            "public_url_verification_claimed": False,
            "platform_auth_readiness_claimed": False,
            "dispatch_readiness_claimed": False,
        },
        **SAFETY_FLAGS,
    }
    audit_index["exact_payload_hash"] = _stable_hash(audit_index)
    audit_index["audit_index_packet_id"] = f"manual_distribution_registry_audit_index_{audit_index['exact_payload_hash'][:16]}"
    return audit_index
