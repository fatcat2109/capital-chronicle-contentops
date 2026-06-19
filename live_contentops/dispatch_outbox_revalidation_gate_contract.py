"""Dispatch outbox revalidation gate contract, 0174UB.

Deterministic local-only pre-dispatch revalidation. No dispatch, no provider/API,
no network/env/credential/scheduler/scraping/DM behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import approval_ledger_revocation_expiration_contract as approval_vx
from live_contentops import platform_universe_registry_v2 as registry
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UB_DISPATCH_OUTBOX_REVALIDATION_GATE_CONTRACT_V0"
MODEL_VERSION = "0174UB_DISPATCH_OUTBOX_REVALIDATION_GATE_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "709e34a3634ea92e7b33018695f1ffae14c4418c"
DOC_REL_DIR = Path("docs") / "automation" / "0174UB"
PACKET_FILENAME = "dispatch_outbox_revalidation_gate_contract_packet.json"
RUNBOOK_FILENAME = "dispatch_outbox_revalidation_gate_contract.md"
HASH_ALGORITHM = "sha256"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174UC_MANUAL_PUBLISH_RECORD_AND_METRICS_LEDGER_CONTRACT_V0"

STATUS_BLOCKED = "blocked"
STATUS_LOCAL_REVALIDATED_FUTURE_GATE = "locally_revalidated_but_dispatch_future_gate"

KILL_REASON_CLASSES = (
    "operator_hold", "safety_policy_hold", "platform_policy_hold",
    "credential_scope_hold", "incident_hold", "not_disabled",
    "unknown_or_blocked",
)
RATE_LIMIT_STATES = (
    "not_evaluated_future_gate", "within_limit_placeholder",
    "blocked_over_limit", "unknown_or_blocked",
)
BUDGET_STATES = (
    "not_evaluated_future_gate", "within_budget_placeholder",
    "blocked_over_budget", "unknown_or_blocked",
)
RETRY_STATES = (
    "retry_allowed_placeholder", "blocked_retry_limit", "unknown_or_blocked",
)

BLOCK_PAYLOAD_HASH_MISMATCH = "payload_hash_mismatch"
BLOCK_UNKNOWN_PLATFORM = "unknown_platform_fail_closed"
BLOCK_UNKNOWN_PAYLOAD_CLASS = "unknown_payload_class_fail_closed"
BLOCK_INCOMPATIBLE_PAYLOAD_CLASS = "platform_payload_class_incompatible"
BLOCK_DESTINATION_MISMATCH = "destination_binding_mismatch"
BLOCK_CREDENTIAL_MISMATCH = "credential_handle_mismatch"
BLOCK_APPROVAL_ASSESSMENT_REQUIRED = "approval_validity_assessment_required"
BLOCK_APPROVAL_NOT_VALID = "approval_not_valid"
BLOCK_APPROVAL_REVOKED = "approval_revoked"
BLOCK_APPROVAL_EXPIRED = "approval_expired"
BLOCK_IDEMPOTENCY_KEY_MISSING = "idempotency_key_missing"
BLOCK_IDEMPOTENCY_REPLAY_UNSAFE = "idempotency_replay_unsafe"
BLOCK_KILL_SWITCH_ACTIVE = "kill_switch_active"
BLOCK_KILL_SWITCH_UNKNOWN = "kill_switch_unknown_reason_fail_closed"
BLOCK_POLICY_RATE = "policy_rate_limit_blocked"
BLOCK_POLICY_BUDGET = "policy_budget_blocked"
BLOCK_POLICY_RETRY = "policy_retry_limit_blocked"
BLOCK_POLICY_UNKNOWN = "policy_state_unknown_fail_closed"
BLOCK_AUDIT_CHAIN_INVALID = "audit_chain_invalid"
BLOCK_AUDIT_ENTRIES_NOT_REDACTED = "audit_entries_not_redacted"
BLOCK_FUTURE_SEND_GATE_REQUIRED = "future_send_gate_required"
BLOCK_NO_DISPATCH = "can_dispatch_false_by_contract"


@dataclass(frozen=True)
class DispatchRevalidationCandidate:
    candidate_id: str
    outbox_entry_id: str
    outbox_idempotency_key: str
    candidate_payload_hash: str
    platform_id: str
    payload_class_id: str
    destination_binding_id: str
    credential_handle_id: str
    approval_ledger_entry_id: str
    approval_payload_hash: str
    policy_version: str
    requested_dispatch_epoch: int
    retry_count: int
    previous_attempt_count: int
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class DispatchKillSwitchState:
    kill_switch_state_id: str
    global_dispatch_disabled: bool
    platform_dispatch_disabled: bool
    destination_dispatch_disabled: bool
    credential_handle_disabled: bool
    reason_class: str
    evaluated_at_epoch: int
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class DispatchPolicyGateState:
    policy_gate_state_id: str
    policy_version: str
    platform_id: str
    payload_class_id: str
    max_retry_count: int
    max_attempt_count: int
    rate_limit_bucket_id: str
    budget_bucket_id: str
    rate_limit_state: str
    budget_state: str
    retry_state: str
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class DispatchRevalidationResult:
    revalidation_result_id: str
    candidate_id: str
    outbox_entry_id: str
    payload_hash_match: bool
    platform_known: bool
    payload_class_known: bool
    platform_payload_class_compatible: bool
    destination_binding_match: bool
    credential_handle_match: bool
    approval_validity_assessment_id: str
    approval_still_valid: bool
    approval_not_revoked: bool
    approval_not_expired: bool
    idempotency_key_present: bool
    idempotency_replay_safe: bool
    kill_switch_clear: bool
    policy_gate_clear: bool
    audit_chain_valid: bool
    audit_entries_redacted: bool
    no_live_behavior: bool
    revalidation_status: str
    can_dispatch: bool
    dispatch_ready: bool
    public_postable: bool
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]


@dataclass(frozen=True)
class DispatchOutboxRevalidationGatePacket:
    packet_id: str
    candidates: tuple[DispatchRevalidationCandidate, ...]
    kill_switch_states: tuple[DispatchKillSwitchState, ...]
    policy_gate_states: tuple[DispatchPolicyGateState, ...]
    revalidation_results: tuple[DispatchRevalidationResult, ...]
    packet_hash: str
    packet_hash_algorithm: str
    all_results_no_dispatch: bool
    all_results_require_future_send_gate: bool
    audit_ledger_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    next_required_gate: str


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


def safety_flags() -> dict[str, bool]:
    return {
        "local_revalidation_only": True,
        "future_send_gate_required": True,
        "can_dispatch": False,
        "dispatch_ready": False,
        "public_postable": False,
        "live_dispatch_enabled": False,
        "approval_granted": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "provider_api_called": False,
        "llm_provider_called": False,
        "credential_hydrated": False,
        "env_read": False,
        "network_performed": False,
        "scheduler_enabled": False,
        "autonomous_posting_allowed": False,
        "scraping_performed": False,
        "dm_or_reply_automation_allowed": False,
        "current_truth_promoted": False,
        "dqr_cleared": False,
        "readiness_cleared": False,
        "ingestion_repo_mutated": False,
    }


def build_revalidation_candidate(outbox_entry: dict[str, Any], preview_metadata: dict[str, Any] | None = None, approval_metadata: dict[str, Any] | None = None) -> DispatchRevalidationCandidate:
    preview_metadata = preview_metadata or {}
    approval_metadata = approval_metadata or {}
    payload_hash = str(outbox_entry.get("candidate_payload_hash") or outbox_entry.get("payload_hash") or preview_metadata.get("payload_hash") or "")
    approval_hash = str(approval_metadata.get("approval_payload_hash") or approval_metadata.get("payload_hash") or outbox_entry.get("approval_payload_hash") or payload_hash)
    basis = {
        "outbox_entry_id": outbox_entry.get("outbox_entry_id", ""),
        "outbox_idempotency_key": outbox_entry.get("outbox_idempotency_key") or outbox_entry.get("idempotency_key", ""),
        "candidate_payload_hash": payload_hash,
        "platform_id": outbox_entry.get("platform_id") or outbox_entry.get("platform") or preview_metadata.get("platform_id", ""),
        "payload_class_id": outbox_entry.get("payload_class_id") or outbox_entry.get("platform_payload_class") or preview_metadata.get("payload_class_id", ""),
        "destination_binding_id": outbox_entry.get("destination_binding_id") or preview_metadata.get("destination_binding_id", ""),
        "credential_handle_id": outbox_entry.get("credential_handle_id") or preview_metadata.get("credential_handle_id", ""),
        "approval_ledger_entry_id": outbox_entry.get("approval_ledger_entry_id") or outbox_entry.get("source_approval_ledger_entry_id") or approval_metadata.get("approval_ledger_entry_id", ""),
        "approval_payload_hash": approval_hash,
        "policy_version": outbox_entry.get("policy_version") or outbox_entry.get("policy_snapshot_id", "policy:0174UB:local"),
        "requested_dispatch_epoch": int(outbox_entry.get("requested_dispatch_epoch", 0)),
        "retry_count": int(outbox_entry.get("retry_count", 0)),
        "previous_attempt_count": int(outbox_entry.get("previous_attempt_count", 0)),
        "evidence_refs": _unique(tuple(outbox_entry.get("evidence_refs", ())) + tuple(preview_metadata.get("evidence_refs", ())) + tuple(approval_metadata.get("evidence_refs", ()))),
        "blocked_reasons": _unique(outbox_entry.get("blocked_reasons", ())),
    }
    return DispatchRevalidationCandidate(
        candidate_id="dispatch_revalidation_candidate_" + _digest(basis)[:24],
        safety_flags=safety_flags(),
        **basis,
    )


def build_kill_switch_state(*, global_dispatch_disabled: bool = False, platform_dispatch_disabled: bool = False, destination_dispatch_disabled: bool = False, credential_handle_disabled: bool = False, reason_class: str = "not_disabled", evaluated_at_epoch: int = 0, evidence_refs: tuple[str, ...] = ()) -> DispatchKillSwitchState:
    blockers: list[str] = []
    if reason_class not in KILL_REASON_CLASSES or reason_class == "unknown_or_blocked":
        reason_class = "unknown_or_blocked"
        blockers.append(BLOCK_KILL_SWITCH_UNKNOWN)
    if any((global_dispatch_disabled, platform_dispatch_disabled, destination_dispatch_disabled, credential_handle_disabled)):
        blockers.append(BLOCK_KILL_SWITCH_ACTIVE)
    basis = {
        "global_dispatch_disabled": bool(global_dispatch_disabled),
        "platform_dispatch_disabled": bool(platform_dispatch_disabled),
        "destination_dispatch_disabled": bool(destination_dispatch_disabled),
        "credential_handle_disabled": bool(credential_handle_disabled),
        "reason_class": reason_class,
        "evaluated_at_epoch": int(evaluated_at_epoch),
        "evidence_refs": _unique(evidence_refs),
        "blocked_reasons": _unique(blockers),
    }
    return DispatchKillSwitchState(
        kill_switch_state_id="dispatch_kill_switch_state_" + _digest(basis)[:24],
        safety_flags=safety_flags(),
        **basis,
    )


def build_policy_gate_state(*, policy_version: str, platform_id: str, payload_class_id: str, max_retry_count: int = 3, max_attempt_count: int = 3, rate_limit_bucket_id: str = "rate:future", budget_bucket_id: str = "budget:future", rate_limit_state: str = "within_limit_placeholder", budget_state: str = "within_budget_placeholder", retry_state: str = "retry_allowed_placeholder", evidence_refs: tuple[str, ...] = ()) -> DispatchPolicyGateState:
    blockers: list[str] = []
    if rate_limit_state not in RATE_LIMIT_STATES or rate_limit_state == "unknown_or_blocked":
        rate_limit_state = "unknown_or_blocked"
        blockers.append(BLOCK_POLICY_UNKNOWN)
    elif rate_limit_state == "blocked_over_limit":
        blockers.append(BLOCK_POLICY_RATE)
    if budget_state not in BUDGET_STATES or budget_state == "unknown_or_blocked":
        budget_state = "unknown_or_blocked"
        blockers.append(BLOCK_POLICY_UNKNOWN)
    elif budget_state == "blocked_over_budget":
        blockers.append(BLOCK_POLICY_BUDGET)
    if retry_state not in RETRY_STATES or retry_state == "unknown_or_blocked":
        retry_state = "unknown_or_blocked"
        blockers.append(BLOCK_POLICY_UNKNOWN)
    elif retry_state == "blocked_retry_limit":
        blockers.append(BLOCK_POLICY_RETRY)
    basis = {
        "policy_version": policy_version,
        "platform_id": platform_id,
        "payload_class_id": payload_class_id,
        "max_retry_count": int(max_retry_count),
        "max_attempt_count": int(max_attempt_count),
        "rate_limit_bucket_id": rate_limit_bucket_id,
        "budget_bucket_id": budget_bucket_id,
        "rate_limit_state": rate_limit_state,
        "budget_state": budget_state,
        "retry_state": retry_state,
        "evidence_refs": _unique(evidence_refs),
        "blocked_reasons": _unique(blockers),
    }
    return DispatchPolicyGateState(
        policy_gate_state_id="dispatch_policy_gate_state_" + _digest(basis)[:24],
        safety_flags=safety_flags(),
        **basis,
    )


def _registry_checks(platform_id: str, payload_class_id: str) -> tuple[bool, bool, bool, tuple[str, ...]]:
    platform_known = platform_id in registry.PLATFORMS_BY_ID
    payload_known = payload_class_id in registry.PAYLOAD_CLASSES_BY_ID
    reasons: list[str] = []
    if not platform_known:
        reasons.append(BLOCK_UNKNOWN_PLATFORM)
    if not payload_known:
        reasons.append(BLOCK_UNKNOWN_PAYLOAD_CLASS)
    compatible = False
    if platform_known and payload_known:
        compatible = bool(registry.validate_payload_class_compatibility(platform_id, payload_class_id).get("compatible"))
        if not compatible:
            reasons.append(BLOCK_INCOMPATIBLE_PAYLOAD_CLASS)
    return platform_known, payload_known, compatible, _unique(reasons)


def _audit_checks(chain: audit.ImmutableLedgerChain | None) -> tuple[bool, bool, tuple[str, ...], tuple[str, ...]]:
    if chain is None:
        return False, False, (BLOCK_AUDIT_CHAIN_INVALID,), ()
    validation = audit.validate_ledger_chain(chain)
    chain_valid = bool(validation.hash_chain_valid and validation.append_only_valid and validation.monotonic_sequence_valid)
    redacted = bool(validation.redaction_policy_applied and validation.forbidden_data_absent and chain.all_entries_redacted)
    blockers = []
    if not chain_valid:
        blockers.append(BLOCK_AUDIT_CHAIN_INVALID)
    if not redacted:
        blockers.append(BLOCK_AUDIT_ENTRIES_NOT_REDACTED)
    return chain_valid, redacted, _unique(blockers), _unique(chain.evidence_refs)


def revalidate_dispatch_candidate(*, candidate: DispatchRevalidationCandidate, approval_assessment: approval_vx.ApprovalValidityAssessment | None, kill_switch_state: DispatchKillSwitchState, policy_gate_state: DispatchPolicyGateState, audit_chain: audit.ImmutableLedgerChain | None, idempotency_replay_safe: bool = True, evidence_refs: tuple[str, ...] = ()) -> DispatchRevalidationResult:
    blockers = [BLOCK_FUTURE_SEND_GATE_REQUIRED, BLOCK_NO_DISPATCH]
    payload_hash_match = candidate.candidate_payload_hash == candidate.approval_payload_hash
    if not payload_hash_match:
        blockers.append(BLOCK_PAYLOAD_HASH_MISMATCH)
    platform_known, payload_known, compatible, reg_blockers = _registry_checks(candidate.platform_id, candidate.payload_class_id)
    blockers.extend(reg_blockers)
    assessment_id = ""
    if approval_assessment is None:
        approval_still_valid = False
        not_revoked = False
        not_expired = False
        destination_match = False
        credential_match = False
        blockers.append(BLOCK_APPROVAL_ASSESSMENT_REQUIRED)
    else:
        assessment_id = approval_assessment.assessment_id
        approval_still_valid = bool(approval_assessment.approval_still_valid)
        not_revoked = bool(approval_assessment.not_revoked)
        not_expired = bool(approval_assessment.not_expired)
        destination_match = candidate.destination_binding_id == approval_assessment.candidate_destination_binding_id
        credential_match = candidate.credential_handle_id == approval_assessment.candidate_credential_handle_id
        if not approval_still_valid:
            blockers.append(BLOCK_APPROVAL_NOT_VALID)
        if not not_revoked:
            blockers.append(BLOCK_APPROVAL_REVOKED)
        if not not_expired:
            blockers.append(BLOCK_APPROVAL_EXPIRED)
        blockers.extend(approval_assessment.blocked_reasons)
    if not destination_match:
        blockers.append(BLOCK_DESTINATION_MISMATCH)
    if not credential_match:
        blockers.append(BLOCK_CREDENTIAL_MISMATCH)
    idempotency_key_present = bool(candidate.outbox_idempotency_key)
    if not idempotency_key_present:
        blockers.append(BLOCK_IDEMPOTENCY_KEY_MISSING)
    if not idempotency_replay_safe:
        blockers.append(BLOCK_IDEMPOTENCY_REPLAY_UNSAFE)
    kill_switch_clear = not kill_switch_state.blocked_reasons and kill_switch_state.reason_class == "not_disabled"
    blockers.extend(kill_switch_state.blocked_reasons)
    policy_gate_clear = not policy_gate_state.blocked_reasons
    blockers.extend(policy_gate_state.blocked_reasons)
    audit_chain_valid, audit_entries_redacted, audit_blockers, audit_refs = _audit_checks(audit_chain)
    blockers.extend(audit_blockers)
    non_hard_blockers = (
        BLOCK_FUTURE_SEND_GATE_REQUIRED,
        BLOCK_NO_DISPATCH,
        approval_vx.BLOCK_DISPATCH_REVALIDATION_REQUIRED,
        approval_vx.BLOCK_NO_DISPATCH_IN_0174UA,
    )
    hard_blockers = [b for b in _unique(blockers) if b not in non_hard_blockers]
    local_pass = not hard_blockers
    status = STATUS_LOCAL_REVALIDATED_FUTURE_GATE if local_pass else STATUS_BLOCKED
    basis = {
        "candidate_id": candidate.candidate_id,
        "outbox_entry_id": candidate.outbox_entry_id,
        "blocked_reasons": _unique(blockers),
        "revalidation_status": status,
    }
    return DispatchRevalidationResult(
        revalidation_result_id="dispatch_revalidation_result_" + _digest(basis)[:24],
        candidate_id=candidate.candidate_id,
        outbox_entry_id=candidate.outbox_entry_id,
        payload_hash_match=payload_hash_match,
        platform_known=platform_known,
        payload_class_known=payload_known,
        platform_payload_class_compatible=compatible,
        destination_binding_match=destination_match,
        credential_handle_match=credential_match,
        approval_validity_assessment_id=assessment_id,
        approval_still_valid=approval_still_valid,
        approval_not_revoked=not_revoked,
        approval_not_expired=not_expired,
        idempotency_key_present=idempotency_key_present,
        idempotency_replay_safe=bool(idempotency_replay_safe),
        kill_switch_clear=kill_switch_clear,
        policy_gate_clear=policy_gate_clear,
        audit_chain_valid=audit_chain_valid,
        audit_entries_redacted=audit_entries_redacted,
        no_live_behavior=True,
        revalidation_status=status,
        can_dispatch=False,
        dispatch_ready=False,
        public_postable=False,
        blocked_reasons=_unique(blockers),
        evidence_refs=_unique(tuple(candidate.evidence_refs) + tuple(evidence_refs) + tuple(kill_switch_state.evidence_refs) + tuple(policy_gate_state.evidence_refs) + audit_refs),
        safety_flags=safety_flags(),
    )


def _fixture_approval() -> tuple[approval_vx.ApprovalValidityWindow, approval_vx.ApprovalValidityAssessment]:
    payload_hash = _digest({"fixture": "0174UB payload"})
    approval = {
        "approval_ledger_entry_id": "approval_entry_fixture_0174UB",
        "payload_hash": payload_hash,
        "platform_id": "telegram_channel_destination",
        "payload_class_id": "telegram_channel_update",
        "destination_binding_id": "destination:telegram_channel:redacted",
        "credential_handle_id": "credential_handle:telegram:redacted",
        "approved_by_operator_ref": "operator:jim:redacted",
        "evidence_refs": ("docs/automation/0174UA/approval_ledger_revocation_expiration_contract_packet.json",),
    }
    window = approval_vx.build_validity_window(approval, approved_at_epoch=1000, max_valid_duration_seconds=3600)
    expiration = approval_vx.build_expiration_fact(window, evaluated_at_epoch=1200)
    assessment = approval_vx.assess_approval_validity(
        validity_window=window,
        candidate_payload_hash=payload_hash,
        candidate_platform_id="telegram_channel_destination",
        candidate_payload_class_id="telegram_channel_update",
        candidate_destination_binding_id="destination:telegram_channel:redacted",
        candidate_credential_handle_id="credential_handle:telegram:redacted",
        evaluated_at_epoch=1200,
        expiration_fact=expiration,
    )
    return window, assessment


def build_revalidation_gate_packet() -> DispatchOutboxRevalidationGatePacket:
    window, assessment = _fixture_approval()
    candidate = build_revalidation_candidate({
        "outbox_entry_id": "outbox_entry_fixture_0174UB",
        "outbox_idempotency_key": "idempotency:0174UB:redacted",
        "payload_hash": window.approval_payload_hash,
        "platform_id": window.platform_id,
        "payload_class_id": window.payload_class_id,
        "destination_binding_id": window.destination_binding_id,
        "credential_handle_id": window.credential_handle_id,
        "approval_ledger_entry_id": window.approval_ledger_entry_id,
        "approval_payload_hash": window.approval_payload_hash,
        "policy_version": "policy:0174UB:local",
        "requested_dispatch_epoch": 1200,
        "evidence_refs": ("docs/automation/0174EE/dispatch_outbox_idempotency_contract_packet.json",),
    })
    kill = build_kill_switch_state(evaluated_at_epoch=1200, evidence_refs=("docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",))
    policy = build_policy_gate_state(policy_version=candidate.policy_version, platform_id=candidate.platform_id, payload_class_id=candidate.payload_class_id, evidence_refs=("policy:0174UB:placeholder",))
    audit_entry = audit.build_redacted_ledger_entry(entry_sequence=1, previous_entry_hash=audit.GENESIS_HASH, entry_family="dispatch_outbox_fact", source_model="0174UB", source_model_version=MODEL_VERSION, payload=_asdict(candidate), created_at_epoch=1200)
    chain = audit.build_ledger_chain((audit_entry,), chain_id="dispatch_outbox_revalidation_chain_0174UB")
    result = revalidate_dispatch_candidate(candidate=candidate, approval_assessment=assessment, kill_switch_state=kill, policy_gate_state=policy, audit_chain=chain, evidence_refs=("docs/automation/0174U9/redacted_immutable_audit_ledger_v2_contract_packet.json",))
    draft = {
        "candidates": (candidate,),
        "kill_switch_states": (kill,),
        "policy_gate_states": (policy,),
        "revalidation_results": (result,),
        "all_results_no_dispatch": all(not r.can_dispatch and not r.dispatch_ready and not r.public_postable for r in (result,)),
        "all_results_require_future_send_gate": all(r.revalidation_status == STATUS_LOCAL_REVALIDATED_FUTURE_GATE and BLOCK_FUTURE_SEND_GATE_REQUIRED in r.blocked_reasons for r in (result,)),
        "audit_ledger_refs": (chain.chain_id, chain.last_entry_hash),
        "evidence_refs": _unique(tuple(candidate.evidence_refs) + tuple(result.evidence_refs)),
        "safety_flags": safety_flags(),
        "blocked_reasons": _unique(reason for r in (result,) for reason in r.blocked_reasons),
        "next_required_gate": NEXT_HEAVY_BATCH,
    }
    packet_hash = _digest(draft)
    return DispatchOutboxRevalidationGatePacket(
        packet_id="dispatch_outbox_revalidation_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft,
    )


def render_runbook(packet: DispatchOutboxRevalidationGatePacket) -> str:
    return "\n".join([
        "# 0174UB Dispatch Outbox Revalidation Gate Contract", "",
        f"- task_label: `{TASK_LABEL}`",
        f"- model_version: `{MODEL_VERSION}`",
        f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`", "",
        "## Contract rules", "",
        "- Exact payload hash, platform, payload class, destination, credential, approval validity, idempotency, kill switch, policy, and U9 audit chain are checked.",
        "- Unknown platform, payload class, kill switch reason, rate, budget, or retry state fails closed.",
        "- Revoked, expired, missing, or invalid approval blocks.",
        "- Even local pass remains future-send-gated with `can_dispatch=false`.", "",
        "## Safety", "",
        "- No dispatch, platform API, provider API, Telegram API, env/credential read, scheduler, scraping, DM/reply, UI, or ingestion mutation.", "",
        "## Next heavy batch", "", f"`{NEXT_HEAVY_BATCH}`", "",
        "## Packet summary", "", "```json", json.dumps({"packet_id": packet.packet_id, "packet_hash": packet.packet_hash, "all_results_no_dispatch": packet.all_results_no_dispatch, "all_results_require_future_send_gate": packet.all_results_require_future_send_gate, "blocked_reasons": packet.blocked_reasons}, indent=2, sort_keys=True), "```", "",
    ])


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UB")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_revalidation_gate_packet()
    (out / PACKET_FILENAME).write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(out / PACKET_FILENAME), "runbook_path": str(out / RUNBOOK_FILENAME)}
