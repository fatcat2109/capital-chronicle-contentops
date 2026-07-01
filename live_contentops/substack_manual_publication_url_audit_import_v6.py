"""V6 Substack manual publication URL/audit import packet builder."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_PUBLICATION_URL_AUDIT_IMPORT_LANE_V0"
SAMPLE_SCOPE = "sample_fixture_only"
HASH_ALGORITHM = "sha256_json_v6"
PUBLICATION_PLATFORM = "substack"
PUBLICATION_STATUS = "manually_published_outside_contentops"
URL_VERIFICATION_STATUS = "operator_supplied_not_network_verified"
AUDIT_STATUS = "manual_url_imported_pending_operator_review"

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


class SubstackManualPublicationUrlAuditImportError(ValueError):
    """Raised when a manual publication URL audit packet is unsafe or invalid."""


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
                raise SubstackManualPublicationUrlAuditImportError("forbidden_secret_or_session_material")


def _require_str(packet: Mapping[str, Any], key: str) -> str:
    value = packet.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SubstackManualPublicationUrlAuditImportError(f"missing_required_string:{key}")
    return value


def _require_false(packet: Mapping[str, Any], key: str) -> None:
    if packet.get(key) is not False:
        raise SubstackManualPublicationUrlAuditImportError(f"required_false:{key}")


def _require_true(packet: Mapping[str, Any], key: str) -> None:
    if packet.get(key) is not True:
        raise SubstackManualPublicationUrlAuditImportError(f"required_true:{key}")


def _normalize_https_url(url: str) -> str:
    normalized = url.strip()
    if any(char in normalized for char in ("\n", "\r", "\t")):
        raise SubstackManualPublicationUrlAuditImportError("operator_url_contains_control_whitespace")
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SubstackManualPublicationUrlAuditImportError("operator_url_must_be_https")
    return normalized


def build_substack_manual_publication_url_audit_import_packet(
    operator_handoff_packet: Mapping[str, Any],
    *,
    operator_supplied_publication_url: str,
    operator_supplied_publication_timestamp: str,
    operator_supplied_publication_platform: str = PUBLICATION_PLATFORM,
    operator_supplied_publication_status: str = PUBLICATION_STATUS,
    operator_supplied_url_verification_status: str = URL_VERIFICATION_STATUS,
) -> dict[str, Any]:
    """Build a deterministic audit packet without network or browser access."""
    _assert_safe(operator_handoff_packet)
    _require_true(operator_handoff_packet, "manual_copy_only")
    for key in (
        "live_publish_allowed",
        "live_publish_performed",
        "substack_api_used",
        "provider_call_made",
        "network_call_made",
        "credential_read_made",
        "env_value_read_made",
        "browser_session_used",
        "enabled_publish_send_dispatch_approve_controls",
    ):
        _require_false(operator_handoff_packet, key)
    if operator_handoff_packet.get("sample_scope") != SAMPLE_SCOPE:
        raise SubstackManualPublicationUrlAuditImportError("binding_mismatch:sample_scope")
    if operator_supplied_publication_platform != PUBLICATION_PLATFORM:
        raise SubstackManualPublicationUrlAuditImportError("publication_platform_must_be_substack")
    if operator_supplied_publication_status != PUBLICATION_STATUS:
        raise SubstackManualPublicationUrlAuditImportError("publication_status_must_be_manual_outside_contentops")
    if operator_supplied_url_verification_status != URL_VERIFICATION_STATUS:
        raise SubstackManualPublicationUrlAuditImportError("url_verification_status_must_be_operator_supplied")
    if not operator_supplied_publication_timestamp.strip():
        raise SubstackManualPublicationUrlAuditImportError("missing_publication_timestamp")

    normalized_url = _normalize_https_url(operator_supplied_publication_url)
    operator_handoff_packet_id = _require_str(operator_handoff_packet, "operator_handoff_packet_id")
    operator_handoff_hash = _require_str(operator_handoff_packet, "operator_handoff_hash")
    source_export_packet_id = _require_str(operator_handoff_packet, "source_export_packet_id")
    source_export_payload_hash = _require_str(operator_handoff_packet, "source_export_payload_hash")
    approval_export_evidence_packet_id = _require_str(operator_handoff_packet, "approval_export_evidence_packet_id")
    approval_export_evidence_hash = _require_str(operator_handoff_packet, "approval_export_evidence_hash")
    source_article_packet_id = _require_str(operator_handoff_packet, "source_article_packet_id")
    source_article_hash = _require_str(operator_handoff_packet, "source_article_hash")
    exact_payload_hash = _require_str(operator_handoff_packet, "exact_payload_hash")
    url_hash = _stable_hash(normalized_url)

    evidence_cards = [
        {"card_id": "operator_handoff_packet", "card_type": "operator_handoff_packet", "display_status": "bound", "source_id": operator_handoff_packet_id, "hash": operator_handoff_hash},
        {"card_id": "manual_export_payload", "card_type": "manual_export_payload", "display_status": "bound", "source_id": source_export_packet_id, "hash": source_export_payload_hash},
        {"card_id": "approval_export_evidence_packet", "card_type": "approval_export_evidence_packet", "display_status": "bound", "source_id": approval_export_evidence_packet_id, "hash": approval_export_evidence_hash},
        {"card_id": "canonical_article_source", "card_type": "canonical_article_source", "display_status": "bound", "source_id": source_article_packet_id, "hash": source_article_hash},
        {"card_id": "operator_supplied_publication_url", "card_type": "operator_supplied_publication_url", "display_status": URL_VERIFICATION_STATUS, "source_id": "operator_supplied_publication_url", "hash": url_hash},
    ]
    core = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "sample_scope": SAMPLE_SCOPE,
        "hash_algorithm": HASH_ALGORITHM,
        "publication_audit_status": AUDIT_STATUS,
        "operator_handoff_packet_id": operator_handoff_packet_id,
        "operator_handoff_hash": operator_handoff_hash,
        "source_export_packet_id": source_export_packet_id,
        "source_export_payload_hash": source_export_payload_hash,
        "approval_export_evidence_packet_id": approval_export_evidence_packet_id,
        "approval_export_evidence_hash": approval_export_evidence_hash,
        "source_article_packet_id": source_article_packet_id,
        "source_article_hash": source_article_hash,
        "exact_payload_hash": exact_payload_hash,
        "operator_supplied_publication_url": normalized_url,
        "operator_supplied_publication_url_hash": url_hash,
        "operator_supplied_publication_timestamp": operator_supplied_publication_timestamp.strip(),
        "operator_supplied_publication_platform": operator_supplied_publication_platform,
        "operator_supplied_publication_status": operator_supplied_publication_status,
        "operator_supplied_url_verification_status": operator_supplied_url_verification_status,
        "url_network_verified": False,
        "substack_api_used": False,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read_made": False,
        "env_value_read_made": False,
        "browser_session_used": False,
        "live_publish_performed_by_contentops": False,
        "manual_publication_claim_operator_supplied": True,
        "enabled_publish_send_dispatch_approve_controls": False,
        "blocked_controls": ["approve", "send", "publish", "dispatch", "schedule"],
        "evidence_cards": evidence_cards,
        "operator_review_status": "pending_review",
        "warnings": ["sample_fixture_only", "operator_supplied_url_not_network_verified", "no_url_fetch_no_scrape", "manual_publication_claim_not_contentops_publish"],
        "recommended_next_task": "TASK_CONTENTOPS_V6_SUBSTACK_PUBLICATION_AUDIT_REVIEW_OR_METRICS_SUMMARY_V0",
    }
    audit_hash = _stable_hash(core)
    packet = {"publication_url_audit_packet_id": f"substack_manual_publication_url_audit_{audit_hash[:16]}", "publication_url_audit_hash": audit_hash, **core}
    _assert_safe(packet)
    return packet


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build V6 Substack manual publication URL audit import packet.")
    parser.add_argument("--handoff-input", required=True, type=Path)
    parser.add_argument("--publication-url", required=True)
    parser.add_argument("--publication-timestamp", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packet = build_substack_manual_publication_url_audit_import_packet(
        load_json(args.handoff_input),
        operator_supplied_publication_url=args.publication_url,
        operator_supplied_publication_timestamp=args.publication_timestamp,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
