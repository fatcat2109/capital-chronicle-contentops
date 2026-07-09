"""Render CC Content Artifact Packet V0 into an internal ContentOps draft."""
from __future__ import annotations

from typing import Any

from .cc_artifact_packet_approval_v0 import (
    HANDOFF_COMMIT,
    build_approval_hash,
    compute_component_hashes,
)

INTERNAL_ONLY_STATEMENT = (
    "INTERNAL/MANUAL REVIEW ONLY, NOT PUBLIC-PUBLISHABLE BY INTAKE ALONE"
)


def render_internal_draft(packet: dict[str, Any]) -> dict[str, Any]:
    component_hashes = compute_component_hashes(packet)
    approval_hash = build_approval_hash(packet)

    return {
        "draft_kind": "cc_content_artifact_packet_internal_draft_v0",
        "packet_id": packet["packet_id"],
        "schema_version": packet["schema_version"],
        "generated_at_utc": packet["generated_at_utc"],
        "handoff_commit": HANDOFF_COMMIT,
        "sample_packet.main_repo_head": packet["main_repo_head"],
        "audit_snapshot_ref": packet["audit_snapshot_ref"],
        "manifest_id": packet.get("manifest_id"),
        "topic": packet["topic"],
        "headline_or_catalyst": packet["headline_or_catalyst"],
        "article_angle": packet["article_angle"],
        "duplicate_family": packet["topic"],
        "dqr_warning": f"DQR status is {packet['dqr_status']}; ContentOps cannot promote this intake to public publication.",
        "source_quality_warning": f"Source quality status: {packet['source_quality_status']}",
        "candidate_only_warning": "candidate_only=true; values remain candidate/non-authoritative unless a future approved packet says otherwise.",
        "publish_eligibility_warning": f"publish_eligibility={packet['publish_eligibility']}; public_auto is forbidden for this intake.",
        "source_trail": packet["source_trail"],
        "claim_ledger": packet["claim_ledger"],
        "numeric_anchors": packet["numeric_anchors"],
        "chart_specs": packet.get("chart_specs"),
        "media_asset_candidates": [],
        "coverage_gaps": packet["coverage_gaps"],
        "limitations": packet["limitations"],
        "forbidden_use_notes": packet["forbidden_use_notes"],
        "platform_suitability": packet["platform_suitability"],
        "contentops_instructions": packet["contentops_instructions"],
        "handling_instructions": [
            "Preserve DQR, source-quality, candidate-only, limitation, and forbidden-use caveats verbatim.",
            "Do not fetch, parse, verify, or enrich macro source truth inside ContentOps.",
            "Do not publish externally or create a dispatchable outbox entry from intake alone.",
            "Use Capital Chronicle database/exported packets as numeric/source authority.",
        ],
        "public_publishable_by_intake_alone": False,
        "explicit_publication_statement": INTERNAL_ONLY_STATEMENT,
        "approval_required_before_any_downstream_use": True,
        "component_hashes": component_hashes,
        "approval_hash": approval_hash,
        "safety_flags": {
            "public_dispatch_authorized": False,
            "platform_api_call_authorized": False,
            "network_call_authorized": False,
            "credential_or_session_read_authorized": False,
            "main_repo_write_authorized": False,
            "source_truth_verification_authorized_in_contentops": False,
        },
    }
