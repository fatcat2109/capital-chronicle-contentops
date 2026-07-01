"""Manual distribution evidence registry v6.

Pure local read-model for accepted manual distribution evidence lanes.
No network, env, credential, browser, provider, or live platform action is performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

PLATFORM_PACKET_PATHS = {
    "substack": {
        "platform_label": "Substack",
        "export": "docs/automation/V6_SUBSTACK_MANUAL_EXPORT_ARTICLE_STUDIO/sample_substack_manual_export_article_studio_packet.json",
        "approval": "docs/automation/V6_SUBSTACK_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_substack_manual_approval_export_evidence_packet.json",
        "handoff": "docs/automation/V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF/sample_substack_manual_export_operator_handoff_packet.json",
        "url": "docs/automation/V6_SUBSTACK_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_substack_manual_publication_url_audit_import_packet.json",
        "metrics": "docs/automation/V6_SUBSTACK_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY/sample_substack_publication_audit_review_metrics_summary_packet.json",
    },
    "linkedin": {
        "platform_label": "LinkedIn",
        "export": "docs/automation/V6_LINKEDIN_MANUAL_EXPORT/sample_linkedin_manual_export_packet.json",
        "approval": "docs/automation/V6_LINKEDIN_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_linkedin_manual_approval_export_evidence_packet.json",
        "handoff": "docs/automation/V6_LINKEDIN_MANUAL_OPERATOR_HANDOFF/sample_linkedin_manual_operator_handoff_packet.json",
        "url": "docs/automation/V6_LINKEDIN_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_linkedin_manual_publication_url_audit_import_packet.json",
        "metrics": "docs/automation/V6_LINKEDIN_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY/sample_linkedin_publication_audit_review_metrics_summary_packet.json",
    },
    "x": {
        "platform_label": "X",
        "export": "docs/automation/V6_X_MANUAL_EXPORT/sample_x_manual_export_packet.json",
        "approval": "docs/automation/V6_X_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_x_manual_approval_export_evidence_packet.json",
        "handoff": "docs/automation/V6_X_MANUAL_OPERATOR_HANDOFF/sample_x_manual_operator_handoff_packet.json",
        "url": "docs/automation/V6_X_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_x_manual_publication_url_audit_import_packet.json",
        "metrics": "docs/automation/V6_X_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY/sample_x_publication_audit_review_metrics_summary_packet.json",
    },
}

PACKET_ID_FIELDS = {
    "export": "export_packet_id",
    "approval": "approval_export_evidence_packet_id",
    "handoff": "operator_handoff_packet_id",
    "url": "publication_url_audit_packet_id",
    "metrics": "publication_audit_review_packet_id",
}

HASH_FIELDS = {
    "export": ("export_hash", "exact_payload_hash"),
    "approval": ("approval_export_evidence_hash", "exact_payload_hash"),
    "handoff": ("operator_handoff_hash", "exact_payload_hash"),
    "url": ("publication_url_audit_hash", "exact_payload_hash"),
    "metrics": ("publication_audit_review_hash", "exact_payload_hash"),
}


def _load_packet(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _first_present(packet: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = packet.get(field)
        if value:
            return str(value)
    raise KeyError(fields)


def _registry_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_manual_distribution_evidence_registry() -> dict[str, Any]:
    platforms: list[dict[str, Any]] = []
    for platform, config in PLATFORM_PACKET_PATHS.items():
        source_packets: dict[str, Any] = {}
        loaded: list[dict[str, Any]] = []
        for role in ("export", "approval", "handoff", "url", "metrics"):
            packet = _load_packet(config[role])
            loaded.append(packet)
            source_packets[role] = {
                "packet_id": str(packet.get(PACKET_ID_FIELDS[role], "")),
                "hash": _first_present(packet, HASH_FIELDS[role]),
                "source_path": config[role],
            }
        blocked_controls = sorted({control for packet in loaded for control in packet.get("blocked_controls", [])})
        platforms.append({
            "platform": platform,
            "platform_label": config["platform_label"],
            "lane_status": "fixture_manual_operator_supplied",
            "canonical_ui_label": f"{config['platform_label']} manual publication evidence",
            "source_packets": source_packets,
            "manual_operator_supplied": True,
            "metric_provenance": "operator_supplied_manual_entry_not_network_verified",
            "url_provenance": "operator_supplied_not_network_verified",
            "blocked_controls": blocked_controls,
            "safety_flags": {
                "api_used": False,
                "network_call_made": False,
                "url_network_verified": False,
                "metrics_network_verified": False,
                "env_value_read_made": False,
                "credential_read_made": False,
                "browser_session_used": False,
                "live_publish_performed_by_contentops": False,
                "enabled_publish_send_dispatch_approve_controls": False,
            },
        })
    registry = {
        "schema_version": "6.0.0",
        "registry_kind": "manual_distribution_evidence_registry_v0",
        "registry_status": "fixture_manual_operator_supplied_only",
        "platforms": platforms,
        "safety_summary": "No platform API, env, credential, browser session, public URL fetch/scrape, live post, reply, DM, like, repost, quote, schedule, approve, send, publish, or dispatch action.",
    }
    registry["registry_hash"] = _registry_hash(registry)
    registry["registry_packet_id"] = f"manual_distribution_evidence_registry_{registry['registry_hash'][:16]}"
    return registry
