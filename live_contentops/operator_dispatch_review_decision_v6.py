"""V6 Operator Dispatch Review Decision from Preflight."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PREFLIGHT_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PREFLIGHT_FROM_ACTIVE_OUTBOX_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_DISPATCH_REVIEW_DECISION_FROM_PREFLIGHT_V0"
SCHEMA_VERSION = "6.0.0"

SECRET_MARKERS = ("token", "api_key", "password", "bearer", "cookie", "webhook_url", "private_key", "secret", "credential")
PUBLIC_READY_MARKERS = (
    "approved",
    "approval_status",
    "approved_canonical_article_available",
    "publication_ready",
    "allowed_for_publication",
    "publication_allowed",
    "public_postable",
    "dispatch_allowed",
    "platform_variant_generation_allowed",
    "outbox_creation_allowed",
    "public_url",
    "public_metrics",
    "canonical_public_url",
)
FAKE_CLAIMS_MARKERS = (
    "fake_url",
    "fake_metrics",
    "fake_comments",
    "fake_readiness",
    "fake_citation",
)
CITATION_CLAIMS_MARKERS = (
    "citations_verified",
    "generated_citations_allowed",
    "citations_verified_true",
    "generated_citations",
)
TRADING_ADVICE_PATTERNS = (
    r"\bbuy\b",
    r"\bsell\b",
    r"\bhold\b",
    r"\bposition\s+sizing\b",
    r"\bentry\b",
    r"\bexit\b",
    r"\btarget\b",
    r"\bguaranteed\s+prediction\b",
    r"\bsignal\s+service\b",
    r"\btrading\s+advice\b",
)
TRADING_ADVICE_RE = [re.compile(p, re.IGNORECASE) for p in TRADING_ADVICE_PATTERNS]


@dataclass(frozen=True)
class OperatorDispatchReviewDecisionPacket:
    schema_version: str
    task_label: str
    operator_dispatch_review_decision_packet_id: str
    operator_dispatch_decision_id: str
    operator_id: str
    created_at_manual: str
    local_dispatch_preflight_id: str
    local_dispatch_preflight_sha256: str
    local_active_outbox_manifest_id: str
    operator_active_outbox_review_decision_id: str
    active_outbox_eligibility_id: str
    outbox_package_staging_id: str
    payload_review_ledger_id: str
    approval_intent_id: str
    variant_preview_staging_id: str
    metadata_values_review_id: str
    metadata_values_id: str
    metadata_proposal_id: str
    source_pack_intake_id: str
    source_pack_id: str
    editorial_workflow_id: str
    canonical_slug: str
    canonical_title: str
    reviewed_active_outbox_entries: list[str]
    reviewed_active_outbox_entry_hashes: dict[str, str]
    reviewed_active_outbox_payload_files: list[str]
    reviewed_active_outbox_payload_file_hashes: dict[str, str]
    combined_payload_hash: str
    decision: str
    approval_phrase: str
    approval_scope: str
    dispatch_payload_preparation_approved: bool
    dispatch_review_decision_available: bool
    dispatch_payload_created: bool = False
    approval_for_dispatch: bool = False
    approval_for_publication: bool = False
    generated_citations_allowed: bool = False
    citations_verified: bool = False
    approved_canonical_article_available: bool = False
    publication_ready: bool = False
    dispatch_allowed: bool = False
    platform_variant_generation_allowed: bool = False
    outbox_creation_allowed: bool = False
    public_url: None = None
    public_metrics: None = None
    review_only: bool = True
    human_review_required: bool = True
    kill_switch_active: bool = True
    runtime_truth: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _has_secret_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SECRET_MARKERS)


def load_json_packet(path: Path, malformed_label: str) -> Any:
    try:
        val = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(val, dict):
            raise ValueError(malformed_label)
        return val
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def load_text_file(path: Path, malformed_label: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def _normalize_path(p: str | Path) -> str:
    return str(Path(p).resolve()).lower().replace("\\", "/")


def _check_public_and_live_fields(packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    false_fields = [
        "approved_canonical_article_available",
        "publication_ready",
        "dispatch_allowed",
        "platform_variant_generation_allowed",
        "outbox_creation_allowed",
    ]
    null_fields = ["public_url", "public_metrics"]
    for field_name in false_fields:
        if packet.get(field_name) is not False:
            blockers.append(f"{prefix}_{field_name}_not_false")
    for field_name in null_fields:
        if packet.get(field_name) is not None:
            blockers.append(f"{prefix}_{field_name}_not_null")
    return blockers


def _validate_preflight_packet(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != PREFLIGHT_TASK_LABEL:
        blockers.append("preflight_task_label_invalid")
    if packet.get("dispatch_preflight_available") is not True:
        blockers.append("preflight_not_available")
    if packet.get("eligible_for_operator_dispatch_review") is not True:
        blockers.append("preflight_not_eligible_for_operator_review")
    if packet.get("dispatch_payload_created") is not False:
        blockers.append("preflight_dispatch_payload_created_not_false")
    if packet.get("approval_for_dispatch") is not False:
        blockers.append("preflight_approval_for_dispatch_not_false")
    if packet.get("approval_for_publication") is not False:
        blockers.append("preflight_approval_for_publication_not_false")
    if packet.get("generated_citations_allowed") is not False:
        blockers.append("preflight_generated_citations_allowed_not_false")
    if packet.get("citations_verified") is not False:
        blockers.append("preflight_citations_verified_not_false")

    blockers.extend(_check_public_and_live_fields(packet, "preflight"))

    if packet.get("review_only") is not True:
        blockers.append("preflight_review_only_not_true")
    if packet.get("human_review_required") is not True:
        blockers.append("preflight_human_review_required_not_true")
    if packet.get("kill_switch_active") is not True:
        blockers.append("preflight_kill_switch_active_not_true")
    if packet.get("runtime_truth") is not False:
        blockers.append("preflight_runtime_truth_not_false")
    if packet.get("blockers"):
        blockers.append("preflight_has_blockers")

    # Required fields check
    required_keys = [
        "local_dispatch_preflight_id",
        "local_active_outbox_manifest_id",
        "local_active_outbox_manifest_sha256",
        "operator_active_outbox_review_decision_id",
        "active_outbox_eligibility_id",
        "outbox_package_staging_id",
        "payload_review_ledger_id",
        "approval_intent_id",
        "variant_preview_staging_id",
        "metadata_values_review_id",
        "metadata_values_id",
        "metadata_proposal_id",
        "source_pack_intake_id",
        "source_pack_id",
        "editorial_workflow_id",
        "canonical_slug",
        "canonical_title",
        "combined_payload_hash",
    ]
    for key in required_keys:
        if not packet.get(key):
            blockers.append(f"preflight_{key}_missing")

    # Checked file counts
    entries = packet.get("active_outbox_entries", [])
    if not isinstance(entries, list) or len(entries) != 2:
        blockers.append("preflight_active_outbox_entries_count_invalid")

    entry_hashes = packet.get("active_outbox_entry_hashes", {})
    if not isinstance(entry_hashes, dict) or len(entry_hashes) != 2:
        blockers.append("preflight_active_outbox_entry_hashes_count_invalid")

    payloads = packet.get("active_outbox_payload_files", [])
    if not isinstance(payloads, list) or len(payloads) != 2:
        blockers.append("preflight_active_outbox_payload_files_count_invalid")

    payload_hashes = packet.get("active_outbox_payload_file_hashes", {})
    if not isinstance(payload_hashes, dict) or len(payload_hashes) != 2:
        blockers.append("preflight_active_outbox_payload_file_hashes_count_invalid")

    return blockers


def _validate_decision_text(text: str) -> list[str]:
    blockers: list[str] = []
    if _has_secret_marker(text):
        blockers.append("decision_secret_marker_detected")

    lowered = text.lower()

    # Prohibited claims
    for marker in PUBLIC_READY_MARKERS:
        if marker in lowered:
            blockers.append(f"decision_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"decision_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"decision_citations_verified_or_generated_claim_detected_{marker}")

    # Trading/financial advice checks
    for rx in TRADING_ADVICE_RE:
        if rx.search(lowered):
            blockers.append("decision_financial_advice_or_signal_framing_detected")
            break

    # Webhook or dispatch tokens check
    live_send_markers = ["webhook_url", "channel_id", "bot_token", "dispatch_allowed: true", "publish: true"]
    for marker in live_send_markers:
        if marker in lowered:
            blockers.append("decision_live_send_instructions_detected")

    return blockers


def make_operator_dispatch_review_decision_packet(
    preflight_packet: Any,
    operator_decision_json: Any,
) -> OperatorDispatchReviewDecisionPacket:
    blockers: list[str] = []

    preflight_is_dict = isinstance(preflight_packet, dict)
    if not preflight_is_dict:
        blockers.append("malformed_local_dispatch_preflight_json")

    decision_is_dict = isinstance(operator_decision_json, dict)
    if not decision_is_dict:
        blockers.append("malformed_operator_dispatch_decision_json")

    # Scan inputs for secrets
    if preflight_is_dict and _has_secret_marker(json.dumps(preflight_packet)):
        blockers.append("preflight_secret_marker_detected")
    if decision_is_dict and _has_secret_marker(json.dumps(operator_decision_json)):
        blockers.append("decision_secret_marker_detected")

    local_dispatch_preflight_id = ""
    local_dispatch_preflight_sha256 = ""
    local_active_outbox_manifest_id = ""
    operator_active_outbox_review_decision_id = ""
    active_outbox_eligibility_id = ""
    outbox_package_staging_id = ""
    payload_review_ledger_id = ""
    approval_intent_id = ""
    variant_preview_staging_id = ""
    metadata_values_review_id = ""
    metadata_values_id = ""
    metadata_proposal_id = ""
    source_pack_intake_id = ""
    source_pack_id = ""
    editorial_workflow_id = ""
    canonical_slug = ""
    canonical_title = ""
    combined_payload_hash = ""
    reviewed_active_outbox_entries: list[str] = []
    reviewed_active_outbox_entry_hashes: dict[str, str] = {}
    reviewed_active_outbox_payload_files: list[str] = []
    reviewed_active_outbox_payload_file_hashes: dict[str, str] = {}
    decision = ""
    approval_phrase = ""
    approval_scope = ""
    operator_dispatch_decision_id = ""
    operator_id = ""
    created_at_manual = ""

    if preflight_is_dict and "preflight_secret_marker_detected" not in blockers:
        blockers.extend(_validate_preflight_packet(preflight_packet))
        
        local_dispatch_preflight_id = str(preflight_packet.get("local_dispatch_preflight_id") or "")
        local_active_outbox_manifest_id = str(preflight_packet.get("local_active_outbox_manifest_id") or "")
        operator_active_outbox_review_decision_id = str(preflight_packet.get("operator_active_outbox_review_decision_id") or "")
        active_outbox_eligibility_id = str(preflight_packet.get("active_outbox_eligibility_id") or "")
        outbox_package_staging_id = str(preflight_packet.get("outbox_package_staging_id") or "")
        payload_review_ledger_id = str(preflight_packet.get("payload_review_ledger_id") or "")
        approval_intent_id = str(preflight_packet.get("approval_intent_id") or "")
        variant_preview_staging_id = str(preflight_packet.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(preflight_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(preflight_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(preflight_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(preflight_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(preflight_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(preflight_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(preflight_packet.get("canonical_slug") or "")
        canonical_title = str(preflight_packet.get("canonical_title") or "")
        combined_payload_hash = str(preflight_packet.get("combined_payload_hash") or "")

    if decision_is_dict and "decision_secret_marker_detected" not in blockers:
        # Check required fields in operator decision JSON
        required_decision_keys = [
            "schema_version",
            "operator_dispatch_decision_id",
            "operator_id",
            "created_at_manual",
            "local_dispatch_preflight_id",
            "local_active_outbox_manifest_id",
            "combined_payload_hash",
            "reviewed_active_outbox_entries",
            "reviewed_active_outbox_payload_files",
            "decision",
            "approval_phrase",
            "approval_scope",
        ]
        for key in required_decision_keys:
            if not operator_decision_json.get(key):
                blockers.append(f"decision_{key}_missing")
        if "notes" not in operator_decision_json or not isinstance(operator_decision_json.get("notes"), str):
            blockers.append("decision_notes_missing_or_invalid")

        blockers.extend(_validate_decision_text(json.dumps(operator_decision_json)))

        operator_dispatch_decision_id = str(operator_decision_json.get("operator_dispatch_decision_id") or "")
        operator_id = str(operator_decision_json.get("operator_id") or "")
        created_at_manual = str(operator_decision_json.get("created_at_manual") or "")
        decision = str(operator_decision_json.get("decision") or "")
        approval_phrase = str(operator_decision_json.get("approval_phrase") or "")
        approval_scope = str(operator_decision_json.get("approval_scope") or "")

        # Check references match preflight packet
        if operator_decision_json.get("local_dispatch_preflight_id") != local_dispatch_preflight_id:
            blockers.append("decision_local_dispatch_preflight_id_mismatch")
        if operator_decision_json.get("local_active_outbox_manifest_id") != local_active_outbox_manifest_id:
            blockers.append("decision_local_active_outbox_manifest_id_mismatch")
        if operator_decision_json.get("combined_payload_hash") != combined_payload_hash:
            blockers.append("decision_combined_payload_hash_mismatch")

        # Normalize and compare reviewed active outbox entries
        raw_reviewed_entries = operator_decision_json.get("reviewed_active_outbox_entries", [])
        if not isinstance(raw_reviewed_entries, list):
            blockers.append("decision_reviewed_active_outbox_entries_not_list")
        else:
            entries_normalized = [_normalize_path(p) for p in raw_reviewed_entries]
            preflight_entries_normalized = []
            if preflight_is_dict:
                preflight_entries_normalized = [_normalize_path(p) for p in preflight_packet.get("active_outbox_entries", [])]

            if len(entries_normalized) != len(set(entries_normalized)):
                blockers.append("decision_reviewed_active_outbox_entries_duplicate_detected")
            if entries_normalized != preflight_entries_normalized:
                blockers.append("decision_reviewed_active_outbox_entries_mismatch")

            reviewed_active_outbox_entries = entries_normalized
            if preflight_is_dict:
                reviewed_active_outbox_entry_hashes = preflight_packet.get("active_outbox_entry_hashes", {})

        # Normalize and compare reviewed active outbox payload files
        raw_reviewed_payloads = operator_decision_json.get("reviewed_active_outbox_payload_files", [])
        if not isinstance(raw_reviewed_payloads, list):
            blockers.append("decision_reviewed_active_outbox_payload_files_not_list")
        else:
            payloads_normalized = [_normalize_path(p) for p in raw_reviewed_payloads]
            preflight_payloads_normalized = []
            if preflight_is_dict:
                preflight_payloads_normalized = [_normalize_path(p) for p in preflight_packet.get("active_outbox_payload_files", [])]

            if len(payloads_normalized) != len(set(payloads_normalized)):
                blockers.append("decision_reviewed_active_outbox_payload_files_duplicate_detected")
            if payloads_normalized != preflight_payloads_normalized:
                blockers.append("decision_reviewed_active_outbox_payload_files_mismatch")

            reviewed_active_outbox_payload_files = payloads_normalized
            if preflight_is_dict:
                reviewed_active_outbox_payload_file_hashes = preflight_packet.get("active_outbox_payload_file_hashes", {})

    dispatch_payload_preparation_approved = False
    if decision == "approve_dispatch_payload_preparation":
        if approval_phrase == "APPROVE_LOCAL_DISPATCH_PAYLOAD_PREPARATION_ONLY_NOT_SEND" and approval_scope == "dispatch_payload_preparation_only":
            dispatch_payload_preparation_approved = True
        else:
            blockers.append("decision_approval_phrase_or_scope_invalid_for_approve")
    elif decision in ["reject", "defer"]:
        blockers.append(f"decision_rejected_or_deferred_{decision}")
    else:
        if decision:
            blockers.append("decision_value_invalid")

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = (
        "preflight_secret_marker_detected" in blockers or
        "decision_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
        operator_dispatch_decision_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_dispatch_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_active_outbox_manifest_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_active_outbox_review_decision_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        active_outbox_eligibility_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        outbox_package_staging_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        payload_review_ledger_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        approval_intent_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        variant_preview_staging_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        metadata_values_review_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        metadata_values_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        metadata_proposal_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        source_pack_intake_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        source_pack_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        editorial_workflow_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_slug = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_title = "[REDACTED_SECRET_MARKER_DETECTED]"
        combined_payload_hash = ""
        reviewed_active_outbox_entries = []
        reviewed_active_outbox_entry_hashes = {}
        reviewed_active_outbox_payload_files = []
        reviewed_active_outbox_payload_file_hashes = {}
        local_dispatch_preflight_sha256 = ""
        dispatch_payload_preparation_approved = False

    elif preflight_is_dict and not has_secrets:
        local_dispatch_preflight_sha256 = hashlib.sha256(_canonical_json(preflight_packet).encode("utf-8")).hexdigest()

    # Deterministic packet ID
    intake_material = {
        "local_dispatch_preflight_id": local_dispatch_preflight_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
        "decision": decision,
    }
    operator_dispatch_review_decision_packet_id = f"operator_dispatch_review_decision_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("operator_dispatch_review_decision_blocked_pending_operator_repair")

    return OperatorDispatchReviewDecisionPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        operator_dispatch_review_decision_packet_id=operator_dispatch_review_decision_packet_id,
        operator_dispatch_decision_id=operator_dispatch_decision_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        local_dispatch_preflight_id=local_dispatch_preflight_id,
        local_dispatch_preflight_sha256=local_dispatch_preflight_sha256,
        local_active_outbox_manifest_id=local_active_outbox_manifest_id,
        operator_active_outbox_review_decision_id=operator_active_outbox_review_decision_id,
        active_outbox_eligibility_id=active_outbox_eligibility_id,
        outbox_package_staging_id=outbox_package_staging_id,
        payload_review_ledger_id=payload_review_ledger_id,
        approval_intent_id=approval_intent_id,
        variant_preview_staging_id=variant_preview_staging_id,
        metadata_values_review_id=metadata_values_review_id,
        metadata_values_id=metadata_values_id,
        metadata_proposal_id=metadata_proposal_id,
        source_pack_intake_id=source_pack_intake_id,
        source_pack_id=source_pack_id,
        editorial_workflow_id=editorial_workflow_id,
        canonical_slug=canonical_slug,
        canonical_title=canonical_title,
        reviewed_active_outbox_entries=reviewed_active_outbox_entries,
        reviewed_active_outbox_entry_hashes=reviewed_active_outbox_entry_hashes,
        reviewed_active_outbox_payload_files=reviewed_active_outbox_payload_files,
        reviewed_active_outbox_payload_file_hashes=reviewed_active_outbox_payload_file_hashes,
        combined_payload_hash=combined_payload_hash,
        decision=decision,
        approval_phrase=approval_phrase,
        approval_scope=approval_scope,
        dispatch_payload_preparation_approved=dispatch_payload_preparation_approved,
        dispatch_review_decision_available=available,
        approval_for_dispatch=dispatch_payload_preparation_approved,
        blockers=blockers,
        warnings=warnings,
    )


def write_operator_dispatch_review_decision_packet(
    packet: OperatorDispatchReviewDecisionPacket,
    output_dir: Path,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    packet_path = out_path / f"{packet.operator_dispatch_review_decision_packet_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 operator dispatch review decision contract")
    parser.add_argument("preflight_packet")
    parser.add_argument("operator_decision")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        preflight = load_json_packet(Path(args.preflight_packet), "malformed_local_dispatch_preflight_json")
        decision_json = load_json_packet(Path(args.operator_decision), "malformed_operator_dispatch_decision_json")
    except ValueError as exc:
        blocker = str(exc)
        packet = OperatorDispatchReviewDecisionPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            operator_dispatch_review_decision_packet_id="operator_dispatch_review_decision_blocked",
            operator_dispatch_decision_id="",
            operator_id="",
            created_at_manual="",
            local_dispatch_preflight_id="",
            local_dispatch_preflight_sha256="",
            local_active_outbox_manifest_id="",
            operator_active_outbox_review_decision_id="",
            active_outbox_eligibility_id="",
            outbox_package_staging_id="",
            payload_review_ledger_id="",
            approval_intent_id="",
            variant_preview_staging_id="",
            metadata_values_review_id="",
            metadata_values_id="",
            metadata_proposal_id="",
            source_pack_intake_id="",
            source_pack_id="",
            editorial_workflow_id="",
            canonical_slug="",
            canonical_title="",
            reviewed_active_outbox_entries=[],
            reviewed_active_outbox_entry_hashes={},
            reviewed_active_outbox_payload_files=[],
            reviewed_active_outbox_payload_file_hashes={},
            combined_payload_hash="",
            decision="",
            approval_phrase="",
            approval_scope="",
            dispatch_payload_preparation_approved=False,
            dispatch_review_decision_available=False,
            blockers=[blocker],
            warnings=["operator_dispatch_review_decision_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        packet_path = out_path / f"{packet.operator_dispatch_review_decision_packet_id}.json"
        packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    packet = make_operator_dispatch_review_decision_packet(preflight, decision_json)
    write_operator_dispatch_review_decision_packet(packet, Path(args.output_dir))

    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
