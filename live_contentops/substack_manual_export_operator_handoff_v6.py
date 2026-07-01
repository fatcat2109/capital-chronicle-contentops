"""V6 Substack manual export operator handoff packet builder."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF_PACKET_V0"
SAMPLE_SCOPE = "sample_fixture_only"
HASH_ALGORITHM = "sha256_json_v6"
FORBIDDEN_SECRET_PATTERNS = (
    r"https://discord(?:app)?\.com/api/webhooks/",
    r"sk-[A-Za-z0-9]",
    r"xox[baprs]-",
    r"ghp_[A-Za-z0-9]",
    r"bearer\s+[A-Za-z0-9._-]{12,}",
    r"cookie\s*[:=]",
    r"localstorage\s*[:=]",
    r"sessionstorage\s*[:=]",
)


class SubstackManualExportOperatorHandoffError(ValueError):
    """Raised when a handoff packet cannot be safely built."""


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


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
                raise SubstackManualExportOperatorHandoffError("forbidden_secret_or_session_material")


def _require_str(packet: Mapping[str, Any], key: str) -> str:
    value = packet.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SubstackManualExportOperatorHandoffError(f"missing_required_string:{key}")
    return value


def _require_mapping(packet: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = packet.get(key)
    if not isinstance(value, Mapping):
        raise SubstackManualExportOperatorHandoffError(f"missing_required_mapping:{key}")
    return value


def _require_false(packet: Mapping[str, Any], key: str) -> None:
    if packet.get(key) is not False:
        raise SubstackManualExportOperatorHandoffError(f"required_false:{key}")


def _require_equal(left: Any, right: Any, label: str) -> None:
    if left != right:
        raise SubstackManualExportOperatorHandoffError(f"binding_mismatch:{label}")


def build_substack_manual_export_operator_handoff_packet(export_packet: Mapping[str, Any], approval_export_evidence_packet: Mapping[str, Any]) -> dict[str, Any]:
    _assert_safe(export_packet)
    _assert_safe(approval_export_evidence_packet)
    manual_copy_payload = _require_mapping(export_packet, "manual_copy_payload")
    export_packet_id = _require_str(export_packet, "export_packet_id")
    export_payload_hash = _require_str(export_packet, "exact_payload_hash")
    source_article_packet_id = _require_str(export_packet, "source_article_packet_id")
    source_article_hash = _require_str(export_packet, "source_canonical_hash")
    approval_evidence_packet_id = _require_str(approval_export_evidence_packet, "approval_export_evidence_packet_id")
    approval_evidence_hash = _require_str(approval_export_evidence_packet, "approval_export_evidence_hash")

    _require_equal(approval_export_evidence_packet.get("source_export_packet_id"), export_packet_id, "export_packet_id")
    _require_equal(approval_export_evidence_packet.get("exact_payload_hash"), export_payload_hash, "exact_payload_hash")
    _require_equal(approval_export_evidence_packet.get("source_article_packet_id"), source_article_packet_id, "source_article_packet_id")
    _require_equal(approval_export_evidence_packet.get("source_canonical_hash"), source_article_hash, "source_article_hash")
    _require_equal(export_packet.get("sample_scope"), SAMPLE_SCOPE, "export_sample_scope")
    _require_equal(approval_export_evidence_packet.get("sample_scope"), SAMPLE_SCOPE, "evidence_sample_scope")
    _require_equal(approval_export_evidence_packet.get("approval_status"), "pending", "approval_status")

    for packet in (export_packet, approval_export_evidence_packet):
        for key in ("live_publish_allowed", "live_publish_performed", "provider_call_made", "network_call_made", "browser_session_used"):
            _require_false(packet, key)
    for key in ("substack_api_used", "credential_read_made", "env_value_read_made", "enabled_publish_send_dispatch_approve_controls"):
        _require_false(approval_export_evidence_packet, key)

    manual_copy_checklist = [
        {"check_id": "confirm_article_source", "label": "Confirm canonical article source packet and hash", "status": "pending_review", "required": True},
        {"check_id": "confirm_export_payload", "label": "Confirm Substack manual export payload hash before copy", "status": "pending_review", "required": True},
        {"check_id": "confirm_approval_evidence", "label": "Confirm approval/export evidence packet remains pending", "status": "pending_review", "required": True},
        {"check_id": "confirm_manual_copy_only", "label": "Confirm manual copy only; no Substack API, publish, send, dispatch, or scheduler", "status": "pending_review", "required": True},
    ]
    operator_instructions = [
        "Open canonical V5 Manual Export, Approval Queue, and Evidence Vault views only.",
        "Compare article, export, approval/export evidence, and handoff hashes before manual copy.",
        "If separate human approval is granted outside this packet, manually copy the payload into Substack outside ContentOps.",
        "Do not use Substack API, live publish, dispatch, scheduler, provider calls, env values, credentials, browser sessions, cookies, localStorage, or tokens.",
    ]
    evidence_cards = [
        {"card_id": "canonical_article_source", "card_type": "canonical_article_source", "display_status": "bound", "source_id": source_article_packet_id, "hash": source_article_hash},
        {"card_id": "manual_export_payload", "card_type": "manual_export_payload", "display_status": "bound", "source_id": export_packet_id, "hash": export_payload_hash},
        {"card_id": "approval_export_evidence_packet", "card_type": "approval_export_evidence_packet", "display_status": "bound", "source_id": approval_evidence_packet_id, "hash": approval_evidence_hash},
        {"card_id": "manual_copy_checklist", "card_type": "manual_copy_checklist", "display_status": "pending_review", "source_id": "operator_handoff_checklist", "hash": _stable_hash({"manual_copy_checklist": manual_copy_checklist})},
        {"card_id": "blocked_live_publish_state", "card_type": "blocked_live_publish_state", "display_status": "blocked", "source_id": "live_publish_allowed=false", "hash": _stable_hash({"live_publish_allowed": False, "live_publish_performed": False, "substack_api_used": False})},
    ]
    core = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "source_article_packet_id": source_article_packet_id,
        "source_article_hash": source_article_hash,
        "source_export_packet_id": export_packet_id,
        "source_export_payload_hash": export_payload_hash,
        "approval_export_evidence_packet_id": approval_evidence_packet_id,
        "approval_export_evidence_hash": approval_evidence_hash,
        "article_title": _require_str(export_packet, "article_title"),
        "manual_copy_payload": manual_copy_payload,
        "exact_payload_hash": _stable_hash({"manual_copy_payload": manual_copy_payload, "operator_instructions": operator_instructions}),
        "hash_algorithm": HASH_ALGORITHM,
        "approval_status": "pending",
        "operator_handoff_status": "ready_for_manual_review",
        "manual_copy_only": True,
        "live_publish_allowed": False,
        "live_publish_performed": False,
        "substack_api_used": False,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read_made": False,
        "env_value_read_made": False,
        "browser_session_used": False,
        "sample_scope": SAMPLE_SCOPE,
        "manual_copy_checklist": manual_copy_checklist,
        "operator_instructions": operator_instructions,
        "evidence_cards": evidence_cards,
        "blockers": ["operator_approval_pending", "live_publish_disabled", "manual_copy_only", "substack_api_disabled"],
        "blocked_controls": ["approve", "send", "publish", "dispatch", "schedule"],
        "enabled_publish_send_dispatch_approve_controls": False,
        "warnings": ["sample_fixture_only", "manual_copy_only_no_substack_api", "live_publish_disabled", "operator_handoff_pending_review"],
        "recommended_next_task": "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF_BROWSER_QA_OR_RELEASE_REVIEW_V0",
    }
    packet_hash = _stable_hash(core)
    core["evidence_cards"] = [*evidence_cards, {"card_id": "operator_handoff_packet", "card_type": "operator_handoff_packet", "display_status": "ready_for_manual_review", "source_id": "operator_handoff", "hash": packet_hash}]
    packet_hash = _stable_hash(core)
    packet = {"operator_handoff_packet_id": f"substack_manual_export_operator_handoff_{packet_hash[:16]}", "operator_handoff_hash": packet_hash, **core}
    _assert_safe(packet)
    return packet


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build V6 Substack manual export operator handoff packet.")
    parser.add_argument("--export-input", required=True, type=Path)
    parser.add_argument("--evidence-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packet = build_substack_manual_export_operator_handoff_packet(load_json(args.export_input), load_json(args.evidence_input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
