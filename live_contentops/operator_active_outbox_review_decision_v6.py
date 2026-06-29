"""V6 Operator Active Outbox Review Decision from Eligibility Gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ELIGIBILITY_TASK_LABEL = "TASK_CONTENTOPS_V6_ACTIVE_OUTBOX_ELIGIBILITY_GATE_FROM_LOCAL_PACKAGE_STAGING_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_ACTIVE_OUTBOX_REVIEW_DECISION_FROM_ELIGIBILITY_GATE_V0"
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
class OperatorActiveOutboxReviewDecisionPacket:
    schema_version: str
    task_label: str
    operator_active_outbox_review_decision_id: str
    operator_review_decision_id: str
    operator_id: str
    created_at_manual: str
    active_outbox_eligibility_id: str
    active_outbox_eligibility_sha256: str
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
    reviewed_staged_payload_files: list[str]
    reviewed_staged_payload_file_hashes: dict[str, str]
    combined_payload_hash: str
    decision: str
    approval_phrase: str
    approval_scope: str
    active_outbox_creation_approved: bool
    active_outbox_creation_decision_available: bool
    active_outbox_entry_created: bool = False
    approval_for_dispatch: bool = False
    approval_for_outbox_creation: bool = False
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


def _validate_eligibility_packet(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != ELIGIBILITY_TASK_LABEL:
        blockers.append("eligibility_task_label_invalid")
    if packet.get("active_outbox_eligibility_available") is not True:
        blockers.append("eligibility_not_available")
    if packet.get("eligible_for_operator_outbox_review") is not True:
        blockers.append("eligibility_not_eligible_for_operator_review")
    if packet.get("active_outbox_entry_created") is not False:
        blockers.append("eligibility_active_outbox_entry_created_not_false")
    if packet.get("approval_for_dispatch") is not False:
        blockers.append("eligibility_approval_for_dispatch_not_false")
    if packet.get("approval_for_outbox_creation") is not False:
        blockers.append("eligibility_approval_for_outbox_creation_not_false")
    if packet.get("approval_for_publication") is not False:
        blockers.append("eligibility_approval_for_publication_not_false")
    if packet.get("generated_citations_allowed") is not False:
        blockers.append("eligibility_generated_citations_allowed_not_false")
    if packet.get("citations_verified") is not False:
        blockers.append("eligibility_citations_verified_not_false")

    blockers.extend(_check_public_and_live_fields(packet, "eligibility"))

    if packet.get("review_only") is not True:
        blockers.append("eligibility_review_only_not_true")
    if packet.get("human_review_required") is not True:
        blockers.append("eligibility_human_review_required_not_true")
    if packet.get("kill_switch_active") is not True:
        blockers.append("eligibility_kill_switch_active_not_true")
    if packet.get("runtime_truth") is not False:
        blockers.append("eligibility_runtime_truth_not_false")
    if packet.get("blockers"):
        blockers.append("eligibility_has_blockers")

    # Required fields check
    required_keys = [
        "active_outbox_eligibility_id",
        "outbox_package_staging_id",
        "outbox_package_staging_sha256",
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
        "package_dir",
        "combined_payload_hash",
    ]
    for key in required_keys:
        if not packet.get(key):
            blockers.append(f"eligibility_{key}_missing")

    # Checked file count
    files = packet.get("eligible_staged_payload_files", [])
    if not isinstance(files, list) or len(files) != 2:
        blockers.append("eligibility_staged_payload_files_count_invalid")

    hashes = packet.get("eligible_staged_payload_file_hashes", {})
    if not isinstance(hashes, dict) or len(hashes) != 2:
        blockers.append("eligibility_staged_payload_file_hashes_count_invalid")

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


def make_operator_active_outbox_review_decision_packet(
    eligibility_packet: Any,
    operator_decision_json: Any,
) -> OperatorActiveOutboxReviewDecisionPacket:
    blockers: list[str] = []

    eligibility_is_dict = isinstance(eligibility_packet, dict)
    if not eligibility_is_dict:
        blockers.append("malformed_active_outbox_eligibility_json")

    decision_is_dict = isinstance(operator_decision_json, dict)
    if not decision_is_dict:
        blockers.append("malformed_operator_review_decision_json")

    # Scan inputs for secrets
    if eligibility_is_dict and _has_secret_marker(json.dumps(eligibility_packet)):
        blockers.append("eligibility_secret_marker_detected")
    if decision_is_dict and _has_secret_marker(json.dumps(operator_decision_json)):
        blockers.append("decision_secret_marker_detected")

    active_outbox_eligibility_id = ""
    active_outbox_eligibility_sha256 = ""
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
    package_dir = ""
    combined_payload_hash = ""
    reviewed_staged_payload_files: list[str] = []
    reviewed_staged_payload_file_hashes: dict[str, str] = {}
    decision = ""
    approval_phrase = ""
    approval_scope = ""
    operator_review_decision_id = ""
    operator_id = ""
    created_at_manual = ""

    if eligibility_is_dict and "eligibility_secret_marker_detected" not in blockers:
        blockers.extend(_validate_eligibility_packet(eligibility_packet))
        
        active_outbox_eligibility_id = str(eligibility_packet.get("active_outbox_eligibility_id") or "")
        outbox_package_staging_id = str(eligibility_packet.get("outbox_package_staging_id") or "")
        payload_review_ledger_id = str(eligibility_packet.get("payload_review_ledger_id") or "")
        approval_intent_id = str(eligibility_packet.get("approval_intent_id") or "")
        variant_preview_staging_id = str(eligibility_packet.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(eligibility_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(eligibility_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(eligibility_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(eligibility_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(eligibility_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(eligibility_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(eligibility_packet.get("canonical_slug") or "")
        canonical_title = str(eligibility_packet.get("canonical_title") or "")
        package_dir = str(eligibility_packet.get("package_dir") or "")
        combined_payload_hash = str(eligibility_packet.get("combined_payload_hash") or "")

    if decision_is_dict and "decision_secret_marker_detected" not in blockers:
        # Check required fields in operator decision JSON
        required_decision_keys = [
            "schema_version",
            "operator_review_decision_id",
            "operator_id",
            "created_at_manual",
            "active_outbox_eligibility_id",
            "outbox_package_staging_id",
            "combined_payload_hash",
            "reviewed_staged_payload_files",
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

        operator_review_decision_id = str(operator_decision_json.get("operator_review_decision_id") or "")
        operator_id = str(operator_decision_json.get("operator_id") or "")
        created_at_manual = str(operator_decision_json.get("created_at_manual") or "")
        decision = str(operator_decision_json.get("decision") or "")
        approval_phrase = str(operator_decision_json.get("approval_phrase") or "")
        approval_scope = str(operator_decision_json.get("approval_scope") or "")

        # Check references match eligibility packet
        if operator_decision_json.get("active_outbox_eligibility_id") != active_outbox_eligibility_id:
            blockers.append("decision_active_outbox_eligibility_id_mismatch")
        if operator_decision_json.get("outbox_package_staging_id") != outbox_package_staging_id:
            blockers.append("decision_outbox_package_staging_id_mismatch")
        if operator_decision_json.get("combined_payload_hash") != combined_payload_hash:
            blockers.append("decision_combined_payload_hash_mismatch")

        # Normalize and compare reviewed staged payload files
        raw_reviewed_files = operator_decision_json.get("reviewed_staged_payload_files", [])
        if not isinstance(raw_reviewed_files, list):
            blockers.append("decision_reviewed_staged_payload_files_not_list")
        else:
            reviewed_normalized = [_normalize_path(p) for p in raw_reviewed_files]
            eligibility_normalized = []
            if eligibility_is_dict:
                eligibility_normalized = [_normalize_path(p) for p in eligibility_packet.get("eligible_staged_payload_files", [])]

            if len(reviewed_normalized) != len(set(reviewed_normalized)):
                blockers.append("decision_reviewed_staged_payload_files_duplicate_detected")
            if reviewed_normalized != eligibility_normalized:
                blockers.append("decision_reviewed_staged_payload_files_mismatch")

            reviewed_staged_payload_files = reviewed_normalized
            if eligibility_is_dict:
                # Copy file hashes from eligibility
                reviewed_staged_payload_file_hashes = eligibility_packet.get("eligible_staged_payload_file_hashes", {})

    active_outbox_creation_approved = False
    if decision == "approve_active_outbox_creation":
        if approval_phrase == "APPROVE_LOCAL_ACTIVE_OUTBOX_CREATION_ONLY_NOT_DISPATCH" and approval_scope == "active_outbox_creation_only":
            active_outbox_creation_approved = True
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
        "eligibility_secret_marker_detected" in blockers or
        "decision_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
        operator_review_decision_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
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
        reviewed_staged_payload_files = []
        reviewed_staged_payload_file_hashes = {}
        active_outbox_eligibility_sha256 = ""
        active_outbox_creation_approved = False

    elif eligibility_is_dict and not has_secrets:
        active_outbox_eligibility_sha256 = hashlib.sha256(_canonical_json(eligibility_packet).encode("utf-8")).hexdigest()

    # Deterministic active outbox review decision packet ID
    intake_material = {
        "active_outbox_eligibility_id": active_outbox_eligibility_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
        "decision": decision,
    }
    operator_active_outbox_review_decision_id = f"operator_active_outbox_review_decision_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("operator_active_outbox_review_decision_blocked_pending_operator_repair")

    return OperatorActiveOutboxReviewDecisionPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        operator_active_outbox_review_decision_id=operator_active_outbox_review_decision_id,
        operator_review_decision_id=operator_review_decision_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        active_outbox_eligibility_id=active_outbox_eligibility_id,
        active_outbox_eligibility_sha256=active_outbox_eligibility_sha256,
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
        reviewed_staged_payload_files=reviewed_staged_payload_files,
        reviewed_staged_payload_file_hashes=reviewed_staged_payload_file_hashes,
        combined_payload_hash=combined_payload_hash,
        decision=decision,
        approval_phrase=approval_phrase,
        approval_scope=approval_scope,
        active_outbox_creation_approved=active_outbox_creation_approved,
        active_outbox_creation_decision_available=available,
        approval_for_outbox_creation=active_outbox_creation_approved,
        blockers=blockers,
        warnings=warnings,
    )


def write_operator_active_outbox_review_decision_packet(
    packet: OperatorActiveOutboxReviewDecisionPacket,
    output_dir: Path,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    packet_path = out_path / f"{packet.operator_active_outbox_review_decision_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 operator active outbox review decision contract")
    parser.add_argument("eligibility_packet")
    parser.add_argument("operator_decision")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        eligibility = load_json_packet(Path(args.eligibility_packet), "malformed_active_outbox_eligibility_json")
        decision_json = load_json_packet(Path(args.operator_decision), "malformed_operator_review_decision_json")
    except ValueError as exc:
        blocker = str(exc)
        packet = OperatorActiveOutboxReviewDecisionPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            operator_active_outbox_review_decision_id="operator_active_outbox_review_decision_blocked",
            operator_review_decision_id="",
            operator_id="",
            created_at_manual="",
            active_outbox_eligibility_id="",
            active_outbox_eligibility_sha256="",
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
            reviewed_staged_payload_files=[],
            reviewed_staged_payload_file_hashes={},
            combined_payload_hash="",
            decision="",
            approval_phrase="",
            approval_scope="",
            active_outbox_creation_approved=False,
            active_outbox_creation_decision_available=False,
            blockers=[blocker],
            warnings=["operator_active_outbox_review_decision_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        packet_path = out_path / f"{packet.operator_active_outbox_review_decision_id}.json"
        packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    packet = make_operator_active_outbox_review_decision_packet(eligibility, decision_json)
    write_operator_active_outbox_review_decision_packet(packet, Path(args.output_dir))

    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
