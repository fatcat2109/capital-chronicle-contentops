"""Approval ledger revocation + expiration contract, 0174UA.

Deterministic local-only approval validity facts. No dispatch, no provider/API,
no network/env/credential/scheduler/scraping/DM behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UA_APPROVAL_LEDGER_REVOCATION_EXPIRATION_CONTRACT_V0"
MODEL_VERSION = "0174UA_APPROVAL_LEDGER_REVOCATION_EXPIRATION_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "dbf1030c64874f96032acd781ac3d7b430dac52c"
DOC_REL_DIR = Path("docs") / "automation" / "0174UA"
PACKET_FILENAME = "approval_ledger_revocation_expiration_contract_packet.json"
RUNBOOK_FILENAME = "approval_ledger_revocation_expiration_contract.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174UB_DISPATCH_OUTBOX_REVALIDATION_GATE_CONTRACT_V0"
HASH_ALGORITHM = "sha256"

REVOCATION_REASON_CLASSES = (
    "operator_revoked", "payload_superseded", "destination_changed",
    "credential_scope_changed", "safety_policy_changed",
    "source_context_changed", "manual_hold", "unknown_or_blocked",
)
EXPIRATION_REASON_CLASSES = (
    "time_window_expired", "missing_validity_window", "invalid_time_order",
    "not_expired_yet", "unknown_or_blocked",
)

BLOCK_MISSING_VALIDITY_WINDOW = "missing_validity_window"
BLOCK_INVALID_TIME_ORDER = "invalid_time_order"
BLOCK_PAYLOAD_HASH_MISMATCH = "payload_hash_mismatch"
BLOCK_PLATFORM_SCOPE_MISMATCH = "platform_scope_mismatch"
BLOCK_PAYLOAD_CLASS_SCOPE_MISMATCH = "payload_class_scope_mismatch"
BLOCK_DESTINATION_SCOPE_MISMATCH = "destination_binding_scope_mismatch"
BLOCK_CREDENTIAL_SCOPE_MISMATCH = "credential_handle_scope_mismatch"
BLOCK_APPROVAL_REVOKED = "approval_revoked"
BLOCK_APPROVAL_EXPIRED = "approval_expired"
BLOCK_UNKNOWN_REVOCATION_REASON = "unknown_revocation_reason_fail_closed"
BLOCK_DISPATCH_REVALIDATION_REQUIRED = "dispatch_revalidation_required_future_0174UB"
BLOCK_NO_DISPATCH_IN_0174UA = "can_dispatch_false_by_contract"


@dataclass(frozen=True)
class ApprovalValidityWindow:
    validity_window_id: str
    approval_ledger_entry_id: str
    approval_payload_hash: str
    platform_id: str
    payload_class_id: str
    destination_binding_id: str
    credential_handle_id: str
    approved_by_operator_ref: str
    approved_at_epoch: int
    expires_at_epoch: int
    max_valid_duration_seconds: int
    payload_hash_required: bool
    destination_scope_required: bool
    credential_scope_required: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ApprovalRevocationFact:
    revocation_fact_id: str
    approval_ledger_entry_id: str
    revoked_payload_hash: str
    revoked_by_operator_ref: str
    revoked_at_epoch: int
    revocation_reason_class: str
    revocation_reason_detail_hash: str
    revocation_evidence_refs: tuple[str, ...]
    immutable_append_only: bool
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ApprovalExpirationFact:
    expiration_fact_id: str
    approval_ledger_entry_id: str
    approval_payload_hash: str
    evaluated_at_epoch: int
    expires_at_epoch: int
    is_expired: bool
    expiration_reason_class: str
    immutable_append_only: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ApprovalValidityAssessment:
    assessment_id: str
    approval_ledger_entry_id: str
    approval_payload_hash: str
    candidate_payload_hash: str
    candidate_platform_id: str
    candidate_payload_class_id: str
    candidate_destination_binding_id: str
    candidate_credential_handle_id: str
    evaluated_at_epoch: int
    payload_hash_match: bool
    platform_scope_match: bool
    payload_class_scope_match: bool
    destination_scope_match: bool
    credential_scope_match: bool
    not_revoked: bool
    not_expired: bool
    approval_still_valid: bool
    can_dispatch: bool
    dispatch_revalidation_required: bool
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]


@dataclass(frozen=True)
class ApprovalRevocationExpirationLedgerPacket:
    packet_id: str
    validity_windows: tuple[ApprovalValidityWindow, ...]
    revocation_facts: tuple[ApprovalRevocationFact, ...]
    expiration_facts: tuple[ApprovalExpirationFact, ...]
    validity_assessments: tuple[ApprovalValidityAssessment, ...]
    packet_hash: str
    packet_hash_algorithm: str
    append_only: bool
    all_facts_redacted: bool
    no_dispatch: bool
    no_live_behavior: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


def _asdict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return [_asdict(v) for v in value]
    if isinstance(value, list):
        return [_asdict(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _asdict(v) for k, v in value.items()}
    return value


def _json(value: Any) -> str:
    return json.dumps(_asdict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _digest(value: Any) -> str:
    return sha256(_json(value).encode("utf-8")).hexdigest()


def _unique(values: Any) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(v) for v in values if v))


def safety_flags(*, revoked: bool = False, expiration_evaluated: bool = False) -> dict[str, bool]:
    return {
        "immutable_append_only": True,
        "approval_granted": False,
        "approval_revoked_fact_recorded": bool(revoked),
        "approval_expiration_evaluated": bool(expiration_evaluated),
        "can_dispatch": False,
        "dispatch_ready": False,
        "live_dispatch_enabled": False,
        "public_postable": False,
        "current_truth_promoted": False,
        "dqr_cleared": False,
        "readiness_cleared": False,
        "llm_provider_called": False,
        "provider_api_called": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "credential_hydrated": False,
        "env_read": False,
        "network_performed": False,
        "scheduler_enabled": False,
        "autonomous_posting_allowed": False,
        "scraping_performed": False,
        "dm_or_reply_automation_allowed": False,
        "ingestion_repo_mutated": False,
    }


def build_validity_window(approval_fact: dict[str, Any], *, approved_at_epoch: int | None = None, max_valid_duration_seconds: int = 3600) -> ApprovalValidityWindow:
    approved_at = int(approved_at_epoch if approved_at_epoch is not None else approval_fact.get("approved_at_epoch", approval_fact.get("created_at_epoch", 0)))
    duration = int(max_valid_duration_seconds)
    expires_at = approved_at + duration
    reasons = []
    if duration <= 0 or expires_at <= approved_at:
        reasons.append(BLOCK_INVALID_TIME_ORDER)
    basis = {
        "approval_ledger_entry_id": approval_fact.get("approval_ledger_entry_id") or approval_fact.get("ledger_recording_fact_id") or approval_fact.get("ledger_entry_id"),
        "approval_payload_hash": approval_fact.get("approval_payload_hash") or approval_fact.get("payload_hash"),
        "platform_id": approval_fact.get("platform_id") or approval_fact.get("platform"),
        "payload_class_id": approval_fact.get("payload_class_id", "unknown_payload_class"),
        "destination_binding_id": approval_fact.get("destination_binding_id"),
        "credential_handle_id": approval_fact.get("credential_handle_id", "credential_handle_redacted"),
        "approved_by_operator_ref": approval_fact.get("approved_by_operator_ref") or approval_fact.get("operator_identity_ref", "operator:unknown_redacted"),
        "approved_at_epoch": approved_at,
        "expires_at_epoch": expires_at,
        "max_valid_duration_seconds": duration,
        "payload_hash_required": True,
        "destination_scope_required": True,
        "credential_scope_required": True,
        "evidence_refs": _unique(approval_fact.get("evidence_refs", ())),
        "blocked_reasons": tuple(reasons),
    }
    window_id = "validity_window_" + _digest(basis)[:24]
    return ApprovalValidityWindow(validity_window_id=window_id, safety_flags=safety_flags(), **basis)


def build_revocation_fact(*, approval_ledger_entry_id: str, revoked_payload_hash: str, revoked_by_operator_ref: str, revoked_at_epoch: int, revocation_reason_class: str, revocation_reason_detail: str = "", revocation_evidence_refs: tuple[str, ...] = ()) -> ApprovalRevocationFact:
    reasons = []
    if revocation_reason_class not in REVOCATION_REASON_CLASSES or revocation_reason_class == "unknown_or_blocked":
        revocation_reason_class = "unknown_or_blocked"
        reasons.append(BLOCK_UNKNOWN_REVOCATION_REASON)
    detail_hash = _digest({"revocation_reason_detail": str(revocation_reason_detail)})
    basis = {
        "approval_ledger_entry_id": approval_ledger_entry_id,
        "revoked_payload_hash": revoked_payload_hash,
        "revoked_by_operator_ref": revoked_by_operator_ref,
        "revoked_at_epoch": int(revoked_at_epoch),
        "revocation_reason_class": revocation_reason_class,
        "revocation_reason_detail_hash": detail_hash,
        "revocation_evidence_refs": _unique(revocation_evidence_refs),
        "immutable_append_only": True,
        "blocked_reasons": tuple(reasons),
    }
    return ApprovalRevocationFact("revocation_fact_" + _digest(basis)[:24], safety_flags=safety_flags(revoked=True), **basis)


def build_expiration_fact(validity_window: ApprovalValidityWindow | None, *, approval_ledger_entry_id: str = "", approval_payload_hash: str = "", evaluated_at_epoch: int = 0) -> ApprovalExpirationFact:
    reasons: list[str] = []
    if validity_window is None:
        reason = "missing_validity_window"
        reasons.append(BLOCK_MISSING_VALIDITY_WINDOW)
        expires_at = 0
        expired = True
        entry_id = approval_ledger_entry_id
        payload_hash = approval_payload_hash
        evidence = ()
    else:
        entry_id = validity_window.approval_ledger_entry_id
        payload_hash = validity_window.approval_payload_hash
        expires_at = int(validity_window.expires_at_epoch)
        evidence = validity_window.evidence_refs
        if validity_window.expires_at_epoch <= validity_window.approved_at_epoch:
            reason = "invalid_time_order"
            reasons.append(BLOCK_INVALID_TIME_ORDER)
            expired = True
        elif int(evaluated_at_epoch) > expires_at:
            reason = "time_window_expired"
            reasons.append(BLOCK_APPROVAL_EXPIRED)
            expired = True
        else:
            reason = "not_expired_yet"
            expired = False
    basis = {
        "approval_ledger_entry_id": entry_id,
        "approval_payload_hash": payload_hash,
        "evaluated_at_epoch": int(evaluated_at_epoch),
        "expires_at_epoch": expires_at,
        "is_expired": expired,
        "expiration_reason_class": reason,
        "immutable_append_only": True,
        "evidence_refs": _unique(evidence),
        "blocked_reasons": tuple(reasons),
    }
    return ApprovalExpirationFact("expiration_fact_" + _digest(basis)[:24], safety_flags=safety_flags(expiration_evaluated=True), **basis)


def assess_approval_validity(*, validity_window: ApprovalValidityWindow | None, candidate_payload_hash: str, candidate_platform_id: str, candidate_payload_class_id: str, candidate_destination_binding_id: str, candidate_credential_handle_id: str, evaluated_at_epoch: int, revocation_facts: tuple[ApprovalRevocationFact, ...] = (), expiration_fact: ApprovalExpirationFact | None = None, evidence_refs: tuple[str, ...] = ()) -> ApprovalValidityAssessment:
    blockers = [BLOCK_DISPATCH_REVALIDATION_REQUIRED, BLOCK_NO_DISPATCH_IN_0174UA]
    if validity_window is None:
        expiration_fact = expiration_fact or build_expiration_fact(None, evaluated_at_epoch=evaluated_at_epoch)
        blockers.append(BLOCK_MISSING_VALIDITY_WINDOW)
        window = ApprovalValidityWindow("missing", "", "", "", "", "", "", "", 0, 0, 0, True, True, True, (), safety_flags(), (BLOCK_MISSING_VALIDITY_WINDOW,))
    else:
        window = validity_window
        if window.expires_at_epoch <= window.approved_at_epoch:
            blockers.append(BLOCK_INVALID_TIME_ORDER)
        expiration_fact = expiration_fact or build_expiration_fact(window, evaluated_at_epoch=evaluated_at_epoch)
    payload_hash_match = candidate_payload_hash == window.approval_payload_hash
    platform_scope_match = candidate_platform_id == window.platform_id
    payload_class_scope_match = candidate_payload_class_id == window.payload_class_id
    destination_scope_match = candidate_destination_binding_id == window.destination_binding_id
    credential_scope_match = candidate_credential_handle_id == window.credential_handle_id
    if not payload_hash_match:
        blockers.append(BLOCK_PAYLOAD_HASH_MISMATCH)
    if not platform_scope_match:
        blockers.append(BLOCK_PLATFORM_SCOPE_MISMATCH)
    if not payload_class_scope_match:
        blockers.append(BLOCK_PAYLOAD_CLASS_SCOPE_MISMATCH)
    if not destination_scope_match:
        blockers.append(BLOCK_DESTINATION_SCOPE_MISMATCH)
    if not credential_scope_match:
        blockers.append(BLOCK_CREDENTIAL_SCOPE_MISMATCH)
    matched_revocations = [r for r in revocation_facts if r.approval_ledger_entry_id == window.approval_ledger_entry_id and (not r.revoked_payload_hash or r.revoked_payload_hash == window.approval_payload_hash)]
    for revocation in matched_revocations:
        blockers.extend(revocation.blocked_reasons)
    not_revoked = not matched_revocations
    if not not_revoked:
        blockers.append(BLOCK_APPROVAL_REVOKED)
    not_expired = not expiration_fact.is_expired and not expiration_fact.blocked_reasons
    if not not_expired:
        blockers.extend(expiration_fact.blocked_reasons or (BLOCK_APPROVAL_EXPIRED,))
    approval_still_valid = all((validity_window is not None, payload_hash_match, platform_scope_match, payload_class_scope_match, destination_scope_match, credential_scope_match, not_revoked, not_expired))
    basis = {
        "approval_ledger_entry_id": window.approval_ledger_entry_id,
        "approval_payload_hash": window.approval_payload_hash,
        "candidate_payload_hash": candidate_payload_hash,
        "candidate_platform_id": candidate_platform_id,
        "candidate_payload_class_id": candidate_payload_class_id,
        "candidate_destination_binding_id": candidate_destination_binding_id,
        "candidate_credential_handle_id": candidate_credential_handle_id,
        "evaluated_at_epoch": int(evaluated_at_epoch),
        "blocked_reasons": _unique(blockers),
    }
    return ApprovalValidityAssessment(
        assessment_id="approval_validity_assessment_" + _digest(basis)[:24],
        approval_ledger_entry_id=window.approval_ledger_entry_id,
        approval_payload_hash=window.approval_payload_hash,
        candidate_payload_hash=candidate_payload_hash,
        candidate_platform_id=candidate_platform_id,
        candidate_payload_class_id=candidate_payload_class_id,
        candidate_destination_binding_id=candidate_destination_binding_id,
        candidate_credential_handle_id=candidate_credential_handle_id,
        evaluated_at_epoch=int(evaluated_at_epoch),
        payload_hash_match=payload_hash_match,
        platform_scope_match=platform_scope_match,
        payload_class_scope_match=payload_class_scope_match,
        destination_scope_match=destination_scope_match,
        credential_scope_match=credential_scope_match,
        not_revoked=not_revoked,
        not_expired=not_expired,
        approval_still_valid=approval_still_valid,
        can_dispatch=False,
        dispatch_revalidation_required=True,
        blocked_reasons=_unique(blockers),
        evidence_refs=_unique(tuple(window.evidence_refs) + tuple(evidence_refs) + tuple(expiration_fact.evidence_refs)),
        safety_flags=safety_flags(),
    )


def build_u9_audit_entries(facts: tuple[Any, ...]) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    entries = []
    prev = audit.GENESIS_HASH
    for seq, fact in enumerate(facts, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family="approval_ledger_fact",
            source_model="0174UA",
            source_model_version=MODEL_VERSION,
            payload=_asdict(fact),
            created_at_epoch=getattr(fact, "revoked_at_epoch", getattr(fact, "evaluated_at_epoch", 0)),
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_ledger_packet() -> ApprovalRevocationExpirationLedgerPacket:
    approval = {
        "approval_ledger_entry_id": "approval_entry_fixture_0174UA",
        "payload_hash": _digest({"fixture": "payload"}),
        "platform_id": "telegram_channel_destination",
        "payload_class_id": "telegram_channel_update",
        "destination_binding_id": "destination:telegram_channel:redacted",
        "credential_handle_id": "credential_handle:telegram:redacted",
        "approved_by_operator_ref": "operator:jim:redacted",
        "evidence_refs": ("docs/automation/0174ED/approval_ledger_payload_hash_contract_packet.json", "docs/automation/0174U9/redacted_immutable_audit_ledger_v2_contract_packet.json"),
    }
    window = build_validity_window(approval, approved_at_epoch=1000, max_valid_duration_seconds=3600)
    revocation = build_revocation_fact(
        approval_ledger_entry_id=window.approval_ledger_entry_id,
        revoked_payload_hash=window.approval_payload_hash,
        revoked_by_operator_ref="operator:jim:redacted",
        revoked_at_epoch=1200,
        revocation_reason_class="manual_hold",
        revocation_reason_detail="raw detail must never appear in packet",
        revocation_evidence_refs=("fixture:manual_hold",),
    )
    expired = build_expiration_fact(window, evaluated_at_epoch=5000)
    not_expired = build_expiration_fact(window, evaluated_at_epoch=1100)
    valid_assessment = assess_approval_validity(
        validity_window=window,
        candidate_payload_hash=window.approval_payload_hash,
        candidate_platform_id=window.platform_id,
        candidate_payload_class_id=window.payload_class_id,
        candidate_destination_binding_id=window.destination_binding_id,
        candidate_credential_handle_id=window.credential_handle_id,
        evaluated_at_epoch=1100,
        expiration_fact=not_expired,
    )
    revoked_assessment = assess_approval_validity(
        validity_window=window,
        candidate_payload_hash=window.approval_payload_hash,
        candidate_platform_id=window.platform_id,
        candidate_payload_class_id=window.payload_class_id,
        candidate_destination_binding_id=window.destination_binding_id,
        candidate_credential_handle_id=window.credential_handle_id,
        evaluated_at_epoch=1300,
        revocation_facts=(revocation,),
        expiration_fact=not_expired,
    )
    facts = (window, revocation, expired, not_expired, valid_assessment, revoked_assessment)
    evidence = _unique(ref for fact in facts for ref in getattr(fact, "evidence_refs", getattr(fact, "revocation_evidence_refs", ())))
    blockers = _unique(reason for fact in facts for reason in getattr(fact, "blocked_reasons", ()))
    draft = {
        "validity_windows": [window],
        "revocation_facts": [revocation],
        "expiration_facts": [expired, not_expired],
        "validity_assessments": [valid_assessment, revoked_assessment],
        "append_only": True,
        "all_facts_redacted": True,
        "no_dispatch": True,
        "no_live_behavior": True,
        "evidence_refs": evidence,
        "safety_flags": safety_flags(),
        "blocked_reasons": blockers,
    }
    packet_hash = _digest(draft)
    return ApprovalRevocationExpirationLedgerPacket(
        packet_id="approval_revocation_expiration_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft,
    )


def render_runbook(packet: ApprovalRevocationExpirationLedgerPacket) -> str:
    data = _asdict(packet)
    return "\n".join([
        "# 0174UA Approval Ledger Revocation + Expiration Contract", "",
        f"- task_label: `{TASK_LABEL}`",
        f"- model_version: `{MODEL_VERSION}`",
        f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`", "",
        "## Rules", "",
        "- Exact payload hash mismatch blocks.",
        "- Platform, payload-class, destination, and credential scope mismatch block.",
        "- Revocation facts block.",
        "- Expired or invalid validity windows block.",
        "- Missing validity window blocks.",
        "- Unknown revocation reason fails closed.",
        "- `can_dispatch=false` always; 0174UB revalidation remains required.", "",
        "## Redaction and append-only", "",
        "- Revocation detail is represented only as SHA-256 hash.",
        "- Facts are append-only; mutation/update/delete are not modeled.",
        "- U9 audit ledger can record facts under `approval_ledger_fact`.", "",
        "## Safety", "",
        "- No live dispatch, provider/API/network/env/credential/scheduler/scraping/DM behavior.",
        "- No UI/dashboard work.",
        "- No ingestion repo mutation.", "",
        "## Next heavy batch", "", f"`{NEXT_HEAVY_BATCH}`", "",
        "## Packet summary", "", "```json", json.dumps({"packet_id": data["packet_id"], "packet_hash": data["packet_hash"], "no_dispatch": data["no_dispatch"], "blocked_reasons": data["blocked_reasons"]}, indent=2, sort_keys=True), "```", "",
    ])


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UA")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_ledger_packet()
    (out / PACKET_FILENAME).write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(out / PACKET_FILENAME), "runbook_path": str(out / RUNBOOK_FILENAME)}
