"""Next article source pack intake and validation packet builder v6.

Deterministically validates the operator-supplied source-pack entries against
the next article brief source-pack review checklist.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from live_contentops.operator_supplied_feedback_intake_v6 import SAFETY_FLAGS

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PACKET = ROOT / "docs/automation/V6_NEXT_ARTICLE_BRIEF_SOURCE_PACK_AND_REVIEW/next_article_brief_source_pack_review_packet.json"

TASK_LABEL = "TASK_CONTENTOPS_V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION_V0"
FORBIDDEN_WORDING = (
    "buy", "sell", "hold", "price target", "position sizing",
    "guaranteed prediction", "signal-service", "trading instruction",
    "trade signal", "buy signal", "sell signal", "hold recommendation",
    "guaranteed return", "prediction guarantee",
)


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_review_packet() -> dict[str, Any]:
    return json.loads(REVIEW_PACKET.read_text(encoding="utf-8"))


def _assert_safe_text(value: str) -> None:
    lowered = value.lower()
    for term in FORBIDDEN_WORDING:
        if term in lowered:
            raise ValueError(f"Packet contains forbidden wording or financial advice: {term}")


def build_next_article_source_pack_intake_validation_packet(
    review_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic next article source pack intake and validation packet."""
    review = review_packet or _load_review_packet()
    
    # Assert safety in the input headline
    headline = review["article_working_headline"]
    _assert_safe_text(headline)

    source_entries = [
        {
            "source_entry_id": "source_entry_primary_source_001",
            "source_type": "primary_source",
            "source_title": "SEC Cash Flow Statement Guidance Reference",
            "operator_supplied_summary": "Guidelines on cash conversion cycle definitions and revenue quality metrics.",
            "source_url_text_optional": "https://www.sec.gov/files/accounts-receivable-quality-explainer",
            "source_url_hash_optional": "f3b392a832dd39bc4e",
            "local_evidence_path_optional": "docs/automation/evidence/sec_guidance_ref.txt",
            "source_url_network_verified": False,
            "source_api_used": False,
            "source_scraped": False,
            "operator_supplied_only": True,
            "required_for_check_id": "primary_source_references_required",
            "validation_status": "pending_operator_review",
        },
        {
            "source_entry_id": "source_entry_outline_001",
            "source_type": "outline_note",
            "source_title": "Cash flow quality outline Draft V1",
            "operator_supplied_summary": "Draft outline structured around plain-English concepts avoiding advisory/signal claims.",
            "source_url_text_optional": None,
            "source_url_hash_optional": None,
            "local_evidence_path_optional": "docs/automation/evidence/outline_v1.txt",
            "source_url_network_verified": False,
            "source_api_used": False,
            "source_scraped": False,
            "operator_supplied_only": True,
            "required_for_check_id": "article_outline_evidence_required",
            "validation_status": "pending_operator_review",
        },
        {
            "source_entry_id": "source_entry_definitions_001",
            "source_type": "definition_note",
            "source_title": "Definitions list: cash conversion & dividend coverage",
            "operator_supplied_summary": "Educational definitions explaining formula parameters without advice.",
            "source_url_text_optional": None,
            "source_url_hash_optional": None,
            "local_evidence_path_optional": "docs/automation/evidence/definitions.json",
            "source_url_network_verified": False,
            "source_api_used": False,
            "source_scraped": False,
            "operator_supplied_only": True,
            "required_for_check_id": "definitions_caveats_required",
            "validation_status": "pending_operator_review",
        },
        {
            "source_entry_id": "source_entry_non_advisory_001",
            "source_type": "operator_note",
            "source_title": "Compliance review guidelines for non-advisory copy",
            "operator_supplied_summary": "Audit checkpoint checklist ensuring no advisory or target-price phrasing is generated.",
            "source_url_text_optional": None,
            "source_url_hash_optional": None,
            "local_evidence_path_optional": "docs/automation/evidence/compliance_checklist.txt",
            "source_url_network_verified": False,
            "source_api_used": False,
            "source_scraped": False,
            "operator_supplied_only": True,
            "required_for_check_id": "non_advisory_language_review_required",
            "validation_status": "pending_operator_review",
        },
        {
            "source_entry_id": "source_entry_auth_001",
            "source_type": "operator_note",
            "source_title": "Operator V6 Drafting Sign-Off",
            "operator_supplied_summary": "Manual auth sign-off confirming that drafting is approved locally but locked pending formal drafting loop.",
            "source_url_text_optional": None,
            "source_url_hash_optional": None,
            "local_evidence_path_optional": "docs/automation/evidence/sign_off_drafting.txt",
            "source_url_network_verified": False,
            "source_api_used": False,
            "source_scraped": False,
            "operator_supplied_only": True,
            "required_for_check_id": "final_operator_authorization_required",
            "validation_status": "pending_operator_review",
        },
    ]

    for entry in source_entries:
        _assert_safe_text(entry["source_title"])
        _assert_safe_text(entry["operator_supplied_summary"])

    required_check_ids = [item["check_id"] for item in review["source_pack_checklist"]]
    covered_check_ids = sorted(list(set([entry["required_for_check_id"] for entry in source_entries if entry["required_for_check_id"] in required_check_ids])))
    missing_check_ids = sorted([cid for cid in required_check_ids if cid not in covered_check_ids])

    source_entry_count = len(source_entries)
    source_url_count = sum(1 for entry in source_entries if entry.get("source_url_text_optional"))

    if len(missing_check_ids) == 0:
        source_pack_collection_status = "operator_supplied_complete_pending_review"
        checklist_coverage_status = "complete_coverage"
    else:
        source_pack_collection_status = "operator_supplied_incomplete"
        checklist_coverage_status = "incomplete_coverage"

    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "next_article_source_pack_intake_validation_v0",
        "task_label": TASK_LABEL,
        "source_pack_review_packet_id": review["source_pack_review_packet_id"],
        "source_pack_review_packet_hash": review["exact_payload_hash"],
        "source_next_article_brief_packet_id": review["source_next_article_brief_packet_id"],
        "source_next_article_brief_packet_hash": review["source_next_article_brief_packet_hash"],
        "article_working_headline": headline,
        "intake_status": "operator_source_pack_supplied_for_review",
        "validation_status": "local_metadata_validation_pending_operator_review",
        "source_pack_collection_status": source_pack_collection_status,
        "checklist_coverage_status": checklist_coverage_status,
        "covered_check_ids": covered_check_ids,
        "missing_check_ids": missing_check_ids,
        "source_entry_count": source_entry_count,
        "source_url_count": source_url_count,
        "network_verified_url_count": 0,
        "api_verified_source_count": 0,
        "ready_for_llm_drafting": False,
        "ready_for_canonical_draft": False,
        "ready_for_auto_publish": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "source_entries": source_entries,
        **SAFETY_FLAGS,
        "enabled_publish_send_dispatch_approve_controls": False,
    }

    packet["exact_payload_hash"] = _stable_hash(packet)
    packet["source_pack_intake_packet_id"] = f"next_article_source_pack_intake_{packet['exact_payload_hash'][:16]}"
    packet["source_pack_validation_packet_id"] = f"next_article_source_pack_validation_{packet['exact_payload_hash'][:16]}"
    return packet


if __name__ == "__main__":
    print(json.dumps(build_next_article_source_pack_intake_validation_packet(), indent=2, sort_keys=True))
