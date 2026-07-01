"""V6 Next Article Draft Authorization and Readiness Packet Builder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INTAKE_PACKET_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION/next_article_source_pack_intake_validation_packet.json"

TASK_LABEL = "TASK_CONTENTOPS_V6_NEXT_ARTICLE_SOURCE_PACK_TO_DRAFT_AUTHORIZATION_AND_LOCAL_DRAFT_READINESS_HEAVY_BATCH_V0"
FORBIDDEN_WORDING = (
    "buy", "sell", "hold", "price target", "position sizing",
    "guaranteed prediction", "signal-service", "trading instruction",
    "trade signal", "buy signal", "sell signal", "hold recommendation",
    "guaranteed return", "prediction guarantee",
)


def _stable_hash(payload: dict[str, Any]) -> str:
    # Remove packet ID fields to hash deterministically
    p = {k: v for k, v in payload.items() if k not in ("draft_authorization_packet_id", "draft_readiness_packet_id")}
    return hashlib.sha256(json.dumps(p, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_intake_packet() -> dict[str, Any]:
    return json.loads(INTAKE_PACKET_PATH.read_text(encoding="utf-8"))


def _assert_safe_text(value: str) -> None:
    lowered = value.lower()
    for term in FORBIDDEN_WORDING:
        if term in lowered:
            raise ValueError(f"Packet contains forbidden wording or financial advice: {term}")


def build_next_article_draft_authorization_packet(
    intake_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic draft authorization and readiness packet."""
    intake = intake_packet or _load_intake_packet()

    # Input validations
    if intake.get("missing_check_ids"):
        raise ValueError("Input source-pack has missing checklist items")
    if intake.get("network_verified_url_count", 0) > 0:
        raise ValueError("Input source-pack has network verified URLs")
    if intake.get("api_verified_source_count", 0) > 0:
        raise ValueError("Input source-pack has API verified sources")
    if intake.get("ready_for_auto_publish") is True:
        raise ValueError("Input source-pack is auto-publish ready")
    if intake.get("ready_for_dispatch") is True:
        raise ValueError("Input source-pack is dispatch ready")
    if intake.get("live_action_allowed") is True:
        raise ValueError("Input source-pack live action is allowed")

    # Assert safe text on key content fields
    headline = intake["article_working_headline"]
    _assert_safe_text(headline)

    for entry in intake.get("source_entries", []):
        _assert_safe_text(entry.get("source_title", ""))
        _assert_safe_text(entry.get("operator_supplied_summary", ""))

    # Prepare authorization and readiness packet
    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "next_article_draft_authorization_and_readiness_v0",
        "task_label": TASK_LABEL,
        "source_pack_intake_packet_id": intake["source_pack_intake_packet_id"],
        "source_pack_intake_packet_hash": intake["exact_payload_hash"],
        "source_pack_review_packet_id": intake["source_pack_review_packet_id"],
        "source_pack_review_packet_hash": intake["source_pack_review_packet_hash"],
        "source_next_article_brief_packet_id": intake["source_next_article_brief_packet_id"],
        "source_next_article_brief_packet_hash": intake["source_next_article_brief_packet_hash"],
        "article_working_headline": headline,
        "selected_backlog_candidate_id": "backlog_candidate_cash_flow_quality_explainer",
        
        "authorization_record_status": "operator_drafting_authorization_recorded",
        "authorization_scope": "local_canonical_draft_preparation_only",
        "operator_authorization_required": True,
        "operator_authorization_recorded": True,
        "operator_authorization_source": "fixture_operator_supplied_local_record",
        
        "local_draft_readiness_status": "ready_for_local_canonical_draft_workflow",
        "source_pack_collection_status": intake["source_pack_collection_status"],
        "checklist_coverage_status": intake["checklist_coverage_status"],
        "covered_check_ids": intake["covered_check_ids"],
        "missing_check_ids": intake["missing_check_ids"],
        "source_entry_count": intake["source_entry_count"],
        "network_verified_url_count": 0,
        "api_verified_source_count": 0,
        
        "ready_for_local_canonical_draft_workflow": True,
        "ready_for_llm_drafting": False,
        "ready_for_provider_drafting": False,
        "canonical_draft_created": False,
        "article_body_created": False,
        "ready_for_auto_publish": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        
        "separate_drafting_task_required": True,
        "separate_llm_scope_required": True,
        "separate_publish_authorization_required": True,
        "human_review_required_before_draft_generation": True,
        
        "llm_provider_call_made": False,
        "provider_call_made": False,
        "platform_api_used": False,
        "network_call_made": False,
        "public_url_fetch_made": False,
        "env_value_read_made": False,
        "credential_read_made": False,
        "browser_session_used": False,
        "live_publish_performed_by_contentops": False,
        "enabled_publish_send_dispatch_approve_controls": False,
        
        "forbidden_financial_advice_or_signal_wording_present": False,
        "scanned_for_terms": [
            "buy", "sell", "hold", "price target", "position sizing",
            "guaranteed prediction", "signal-service", "trading instruction"
        ],
    }

    h = _stable_hash(packet)
    packet["exact_payload_hash"] = h
    packet["draft_authorization_packet_id"] = f"next_article_draft_authorization_{h[:16]}"
    packet["draft_readiness_packet_id"] = f"next_article_draft_readiness_{h[:16]}"
    
    return packet


if __name__ == "__main__":
    print(json.dumps(build_next_article_draft_authorization_packet(), indent=2, sort_keys=True))
