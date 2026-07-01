"""V6 Substack publication audit review / manual metrics summary packet builder."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_SUBSTACK_PUBLICATION_AUDIT_REVIEW_OR_METRICS_SUMMARY_V0"
SAMPLE_SCOPE = "sample_fixture_only"
HASH_ALGORITHM = "sha256_json_v6"
METRICS_SOURCE = "operator_supplied_manual_entry"
AUDIT_STATUS = "manual_url_import_reviewed_pending_metrics_confirmation"
METRICS_STATUS = "manual_metrics_fixture_only_pending_operator_confirmation"

FORBIDDEN_SECRET_PATTERNS = (
    r"https://discord(?:app)?\.com/api/webhooks/",
    r"sk-[A-Za-z0-9]",
    r"xox[baprs]-",
    r"ghp_[A-Za-z0-9]",
    r"bearer\s+[A-Za-z0-9._-]{12,}",
    r"cookie\s*[:=]",
    r"localstorage\s*[:=]",
    r"sessionstorage\s*[:=]",
    r"browser session data\s*[:=]",
)


class SubstackPublicationAuditReviewMetricsSummaryError(ValueError):
    """Raised when a manual publication metrics summary packet is unsafe or invalid."""


def _stable_hash(payload: Mapping[str, Any] | str) -> str:
    body = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [s for item in value.values() for s in _walk_strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in _walk_strings(item)]
    return []


def _assert_safe(packet: Mapping[str, Any]) -> None:
    for text in _walk_strings(packet):
        for pattern in FORBIDDEN_SECRET_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                raise SubstackPublicationAuditReviewMetricsSummaryError("forbidden_secret_or_session_material")


def _require_str(packet: Mapping[str, Any], key: str) -> str:
    value = packet.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SubstackPublicationAuditReviewMetricsSummaryError(f"missing_required_string:{key}")
    return value


def _require_false(packet: Mapping[str, Any], key: str) -> None:
    if packet.get(key) is not False:
        raise SubstackPublicationAuditReviewMetricsSummaryError(f"required_false:{key}")


def _require_true(packet: Mapping[str, Any], key: str) -> None:
    if packet.get(key) is not True:
        raise SubstackPublicationAuditReviewMetricsSummaryError(f"required_true:{key}")


def build_substack_publication_audit_review_metrics_summary_packet(
    url_audit_packet: Mapping[str, Any],
    *,
    operator_supplied_views: int | None = None,
    operator_supplied_opens: int | None = None,
    operator_supplied_likes: int | None = None,
    operator_supplied_comments: int | None = None,
    operator_supplied_shares: int | None = None,
    operator_supplied_restacks: int | None = None,
    operator_supplied_subscribers_delta: int | None = None,
    operator_supplied_notes: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic audit review and metrics summary packet."""
    _assert_safe(url_audit_packet)
    _require_true(url_audit_packet, "manual_publication_claim_operator_supplied")
    for key in (
        "url_network_verified",
        "substack_api_used",
        "provider_call_made",
        "network_call_made",
        "credential_read_made",
        "env_value_read_made",
        "browser_session_used",
        "enabled_publish_send_dispatch_approve_controls",
    ):
        _require_false(url_audit_packet, key)
    if url_audit_packet.get("sample_scope") != SAMPLE_SCOPE:
        raise SubstackPublicationAuditReviewMetricsSummaryError("binding_mismatch:sample_scope")

    publication_url_audit_packet_id = _require_str(url_audit_packet, "publication_url_audit_packet_id")
    publication_url_audit_hash = _require_str(url_audit_packet, "publication_url_audit_hash")
    operator_handoff_packet_id = _require_str(url_audit_packet, "operator_handoff_packet_id")
    operator_handoff_hash = _require_str(url_audit_packet, "operator_handoff_hash")
    source_export_packet_id = _require_str(url_audit_packet, "source_export_packet_id")
    source_export_payload_hash = _require_str(url_audit_packet, "source_export_payload_hash")
    approval_export_evidence_packet_id = _require_str(url_audit_packet, "approval_export_evidence_packet_id")
    approval_export_evidence_hash = _require_str(url_audit_packet, "approval_export_evidence_hash")
    source_article_packet_id = _require_str(url_audit_packet, "source_article_packet_id")
    source_article_hash = _require_str(url_audit_packet, "source_article_hash")
    exact_payload_hash = _require_str(url_audit_packet, "exact_payload_hash")
    operator_supplied_publication_url = _require_str(url_audit_packet, "operator_supplied_publication_url")
    operator_supplied_publication_url_hash = _require_str(url_audit_packet, "operator_supplied_publication_url_hash")
    operator_supplied_publication_timestamp = _require_str(url_audit_packet, "operator_supplied_publication_timestamp")

    evidence_cards = [
        {"card_id": "publication_url_audit_packet", "card_type": "publication_url_audit_packet", "display_status": "bound", "source_id": publication_url_audit_packet_id, "hash": publication_url_audit_hash},
        {"card_id": "operator_handoff_packet", "card_type": "operator_handoff_packet", "display_status": "bound", "source_id": operator_handoff_packet_id, "hash": operator_handoff_hash},
        {"card_id": "manual_export_payload", "card_type": "manual_export_payload", "display_status": "bound", "source_id": source_export_packet_id, "hash": source_export_payload_hash},
        {"card_id": "approval_export_evidence_packet", "card_type": "approval_export_evidence_packet", "display_status": "bound", "source_id": approval_export_evidence_packet_id, "hash": approval_export_evidence_hash},
        {"card_id": "canonical_article_source", "card_type": "canonical_article_source", "display_status": "bound", "source_id": source_article_packet_id, "hash": source_article_hash},
        {"card_id": "operator_supplied_publication_url", "card_type": "operator_supplied_publication_url", "display_status": "verified", "source_id": "operator_supplied_publication_url", "hash": operator_supplied_publication_url_hash},
    ]

    metrics = {
        "views": operator_supplied_views,
        "opens": operator_supplied_opens,
        "likes": operator_supplied_likes,
        "comments": operator_supplied_comments,
        "shares": operator_supplied_shares,
        "restacks": operator_supplied_restacks,
        "subscribers_delta": operator_supplied_subscribers_delta,
        "notes": operator_supplied_notes.strip() if operator_supplied_notes else None,
    }

    core = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "sample_scope": SAMPLE_SCOPE,
        "hash_algorithm": HASH_ALGORITHM,
        "publication_audit_status": AUDIT_STATUS,
        "metrics_summary_status": METRICS_STATUS,
        "publication_url_audit_packet_id": publication_url_audit_packet_id,
        "publication_url_audit_hash": publication_url_audit_hash,
        "operator_handoff_packet_id": operator_handoff_packet_id,
        "operator_handoff_hash": operator_handoff_hash,
        "source_export_packet_id": source_export_packet_id,
        "source_export_payload_hash": source_export_payload_hash,
        "approval_export_evidence_packet_id": approval_export_evidence_packet_id,
        "approval_export_evidence_hash": approval_export_evidence_hash,
        "source_article_packet_id": source_article_packet_id,
        "source_article_hash": source_article_hash,
        "exact_payload_hash": exact_payload_hash,
        "operator_supplied_publication_url": operator_supplied_publication_url,
        "operator_supplied_publication_url_hash": operator_supplied_publication_url_hash,
        "operator_supplied_publication_timestamp": operator_supplied_publication_timestamp,
        "metrics_source": METRICS_SOURCE,
        "metrics_network_verified": False,
        "metrics_provider_api_used": False,
        "url_network_verified": False,
        "substack_api_used": False,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read_made": False,
        "env_value_read_made": False,
        "browser_session_used": False,
        "live_publish_performed_by_contentops": False,
        "manual_publication_claim_operator_supplied": True,
        "manual_metrics_claim_operator_supplied": True,
        "enabled_publish_send_dispatch_approve_controls": False,
        "blocked_controls": ["approve", "send", "publish", "dispatch", "schedule"],
        "evidence_cards": evidence_cards,
        "manual_metrics": metrics,
        "operator_review_status": "pending_review",
        "warnings": [
            "sample_fixture_only",
            "operator_supplied_metrics_not_network_verified",
            "no_metrics_api_used",
            "manual_metrics_claim_not_contentops_metrics",
        ],
        "recommended_next_task": "TASK_CONTENTOPS_V6_SUBSTACK_PUBLICATION_METRICS_CONFIRMATION_OR_LANE_COMPLETE_V0",
    }
    review_hash = _stable_hash(core)
    packet = {
        "publication_audit_review_packet_id": f"substack_publication_audit_review_{review_hash[:16]}",
        "publication_audit_review_hash": review_hash,
        **core,
    }
    _assert_safe(packet)
    return packet


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build V6 Substack publication audit review metrics summary packet.")
    parser.add_argument("--url-audit-input", required=True, type=Path)
    parser.add_argument("--views", type=int, default=1240)
    parser.add_argument("--opens", type=int, default=820)
    parser.add_argument("--likes", type=int, default=45)
    parser.add_argument("--comments", type=int, default=8)
    parser.add_argument("--shares", type=int, default=12)
    parser.add_argument("--restacks", type=int, default=3)
    parser.add_argument("--subscribers-delta", type=int, default=15)
    parser.add_argument("--notes", default="Fixture metrics for evaluation purposes only.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    packet = build_substack_publication_audit_review_metrics_summary_packet(
        load_json(args.url_audit_input),
        operator_supplied_views=args.views,
        operator_supplied_opens=args.opens,
        operator_supplied_likes=args.likes,
        operator_supplied_comments=args.comments,
        operator_supplied_shares=args.shares,
        operator_supplied_restacks=args.restacks,
        operator_supplied_subscribers_delta=args.subscribers_delta,
        operator_supplied_notes=args.notes,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
