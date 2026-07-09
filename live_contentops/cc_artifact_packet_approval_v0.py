"""Approval hashing for CC Content Artifact Packet V0 intake.

This module is intentionally local-only. It hashes packet components that the
operator must review, and it does not fetch sources, inspect credentials, or
touch the Capital Chronicle database repository.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

HANDOFF_COMMIT = "74ccf071ac8558d54e6a3c9d7d2a05ecbf42a2f2"

COMPONENT_FIELDS = (
    "source_trail",
    "claim_ledger",
    "numeric_anchors",
    "forbidden_use_notes",
    "limitations",
    "coverage_gaps",
    "platform_suitability",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_json_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def compute_component_hashes(packet: dict[str, Any]) -> dict[str, str]:
    return {field: canonical_json_hash(packet.get(field)) for field in COMPONENT_FIELDS}


def build_approval_hash(packet: dict[str, Any]) -> str:
    component_hashes = compute_component_hashes(packet)
    approval_material = {
        "packet_id": packet.get("packet_id"),
        "schema_version": packet.get("schema_version"),
        "generated_at_utc": packet.get("generated_at_utc"),
        "handoff_commit": HANDOFF_COMMIT,
        "sample_packet.main_repo_head": packet.get("main_repo_head"),
        "dqr_status": packet.get("dqr_status"),
        "source_quality_status": packet.get("source_quality_status"),
        "candidate_only": packet.get("candidate_only"),
        "publish_eligibility": packet.get("publish_eligibility"),
        "duplicate_family": packet.get("topic"),
        "source_trail_hash": component_hashes["source_trail"],
        "claim_ledger_hash": component_hashes["claim_ledger"],
        "numeric_anchors_hash": component_hashes["numeric_anchors"],
        "forbidden_use_notes_hash": component_hashes["forbidden_use_notes"],
        "limitations_hash": component_hashes["limitations"],
        "coverage_gaps_hash": component_hashes["coverage_gaps"],
        "platform_suitability_hash": component_hashes["platform_suitability"],
    }
    return canonical_json_hash(approval_material)
