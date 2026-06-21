"""Redacted immutable audit ledger v2 contract, 0174U9.

Deterministic local evidence ledger. No provider/API/network/env/credential,
no approval, no dispatch, no public readiness, no DQR/readiness/current-truth
promotion.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0174U9_REDACTED_IMMUTABLE_AUDIT_LEDGER_V2_CONTRACT_V0"
MODEL_VERSION = "0174U9_REDACTED_IMMUTABLE_AUDIT_LEDGER_V2_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "573d407ba32ecd2f1af47542d85d997b712c0eb5"
DOC_REL_DIR = Path("docs") / "automation" / "0174U9"
PACKET_FILENAME = "redacted_immutable_audit_ledger_v2_contract_packet.json"
RUNBOOK_FILENAME = "redacted_immutable_audit_ledger_v2_contract.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174UA_APPROVAL_LEDGER_REVOCATION_EXPIRATION_CONTRACT_V0"
HASH_ALGORITHM = "sha256"
GENESIS_HASH = "0" * 64
LEDGER_VERSION = MODEL_VERSION

ENTRY_FAMILIES = (
    "raw_operator_input", "content_idea", "local_intent", "editorial_brief",
    "ai_writer_output", "draft_variant", "platform_payload_preview",
    "substack_manual_export", "multi_platform_dry_run",
    "ingestion_context_candidate", "headline_context_packet",
    "internal_alpha_artifact_intake", "content_eligibility_assessment",
    "artifact_idea_seed", "approval_ledger_fact", "dispatch_outbox_fact",
    "manual_publish_record_future_gate", "metrics_record_future_gate",
    "content_performance_review", "editorial_feedback_signal",
    "editorial_feedback_loop", "content_performance_validation",
    "local_governance_summary_mart", "platform_governance_summary",
    "evidence_governance_summary", "governance_blocker_summary",
    "platform_automation_readiness", "platform_automation_blocker",
    "platform_account_binding_future", "credential_boundary_future",
    "platform_docs_evidence_future", "permission_scope_gate_future",
    "rate_budget_kill_switch_future", "platform_preflight_future",
    "preflight_dry_run_request_budget_future",
    "supervised_live_readiness_review_future",
    "supervised_live_read_only_research_gate_precheck_future",
    "live_read_only_research_approval_packet_schema_future",
    "live_read_only_research_evidence_packet_dry_run_schema_future",
    "live_read_only_research_runbook_approval_gate_dry_run_future",
    "live_read_only_research_local_preflight_simulation_future",
    "read_only_credential_slot_check_validation_future",
    "read_only_credential_slot_inspection_mock_audit_future",
    "local_preflight_bundle_v5_read_model_precheck_future",
    "v5_operator_review_queue_manual_pilot_trail_future",
    "v5_manual_pilot_trail_reconciliation_future",
    "v5_manual_pilot_trail_reconciliation_audit_future",
    "v5_local_operator_runbook_index_future",
    "lane_c_artifact_intake_validation_future",
    "lane_c_artifact_connector_index_future",
    "lane_c_artifact_ingestion_foundation_future",
    "lane_c_artifact_to_editorial_brief_review_packet_future",
    "lane_c_editorial_brief_to_draft_review_only_packet_future",
    "lane_c_draft_review_to_approval_packet_gate_future",
    "lane_c_approval_packet_to_platform_preview_precheck_future",
    "platform_preview_dry_payload_shape_registry_future",
    "platform_preview_dry_render_packet_future",
    "platform_preview_dry_render_to_review_bundle_future",
    "platform_review_bundle_operator_decision_gate_future",
    "operator_decision_gate_to_manual_export_precheck_future",
    "manual_export_precheck_to_export_packet_stub_future",
    "export_packet_stub_to_operator_audit_summary_future",
    "operator_audit_summary_to_manual_publish_record_precheck_future",
    "manual_publish_record_precheck_to_record_stub_future",
    "unknown_or_blocked",
)

FORCED_FALSE_FLAGS = (
    "public_postable", "approval_granted", "dispatch_ready",
    "current_truth_promoted", "dqr_cleared", "readiness_cleared",
    "ingestion_repo_mutated",
)

SAFETY_FALSE_FLAGS = FORCED_FALSE_FLAGS + (
    "live_dispatch_enabled", "llm_provider_called", "provider_api_called",
    "platform_api_called", "telegram_api_called", "credential_hydrated",
    "env_read", "network_performed", "scheduler_enabled",
    "autonomous_posting_allowed", "scraping_performed",
    "dm_or_reply_automation_allowed", "ingestion_repo_mutated",
)

SENSITIVE_KEY_TERMS = (
    "secret", "token", "password", "passwd", "api_key", "apikey",
    "client_secret", "credential", "authorization", "cookie", "env_value",
    "dotenv", "raw_text", "operator_email", "operator_identity",
)

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
TOKEN_RE = re.compile(r"(?i)(bearer\s+[A-Za-z0-9._-]{8,}|(?:token|secret|api_key|client_secret|password)\s*[:=]\s*\S+|ghp_[A-Za-z0-9]{20,}|xoxb-[A-Za-z0-9-]{10,}|\bey[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,})")
ENV_PATH_RE = re.compile(r"(?i)([A-Z]:\\[^\s]*\.(?:env|pem|key)|/[^\s]*\.(?:env|pem|key)|\.env(?:\.[A-Za-z0-9_-]+)?)")
SECRET_URL_RE = re.compile(r"(?i)https?://[^\s'\"]*(?:token|secret|api_key|key|password|bearer|code)=([^\s&'\"]+)")


@dataclass(frozen=True)
class RedactionPolicy:
    policy_id: str
    policy_version: str
    redact_raw_text: bool
    redact_operator_identity: bool
    redact_credentials: bool
    redact_env_paths: bool
    redact_tokens: bool
    redact_emails: bool
    redact_phone_numbers: bool
    redact_urls_if_secret_like: bool
    preserve_hashes: bool
    preserve_evidence_refs: bool
    preserve_model_versions: bool
    preserve_blocked_reasons: bool
    preserve_safety_flags: bool
    policy_hash: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class RedactedAuditLedgerEntry:
    ledger_entry_id: str
    ledger_version: str
    entry_sequence: int
    previous_entry_hash: str
    entry_hash: str
    entry_hash_algorithm: str
    entry_family: str
    source_model: str
    source_model_version: str
    source_object_id: str
    source_object_hash: str
    source_payload_hash: str
    redacted_summary: dict[str, Any]
    redacted_fields: tuple[str, ...]
    retained_evidence_refs: tuple[str, ...]
    blocked_reason_refs: tuple[str, ...]
    safety_state_snapshot: dict[str, bool]
    created_at_epoch: int
    operator_identity_ref: str
    human_review_required: bool
    public_postable: bool
    approval_granted: bool
    dispatch_ready: bool
    current_truth_promoted: bool
    dqr_cleared: bool
    readiness_cleared: bool
    immutable_append_only: bool
    evidence_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ImmutableLedgerChain:
    chain_id: str
    ledger_version: str
    entry_count: int
    first_entry_hash: str
    last_entry_hash: str
    chain_hash: str
    chain_hash_algorithm: str
    entries: tuple[RedactedAuditLedgerEntry, ...]
    append_only: bool
    monotonic_sequence: bool
    all_previous_hashes_match: bool
    all_entries_redacted: bool
    no_public_postable_entries: bool
    no_dispatch_ready_entries: bool
    no_approval_granted_entries: bool
    no_current_truth_promoted_entries: bool
    no_dqr_cleared_entries: bool
    no_readiness_cleared_entries: bool
    evidence_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    safety_flags: dict[str, bool]


@dataclass(frozen=True)
class LedgerValidationResult:
    validation_id: str
    source_chain_id: str
    entry_count: int
    hash_chain_valid: bool
    append_only_valid: bool
    monotonic_sequence_valid: bool
    redaction_policy_applied: bool
    forbidden_data_absent: bool
    no_secret_material: bool
    no_public_postable: bool
    no_dispatch_ready: bool
    no_approval_granted: bool
    no_current_truth_promotion: bool
    no_dqr_clearance: bool
    no_readiness_clearance: bool
    no_provider_or_platform_behavior: bool
    validation_status: str
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _digest(data: Any) -> str:
    return sha256(_json(data).encode("utf-8")).hexdigest()


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


def safety_flags() -> dict[str, bool]:
    flags = {flag: False for flag in SAFETY_FALSE_FLAGS}
    flags.update({
        "immutable_append_only": True,
        "redaction_policy_applied": True,
        "no_secret_material": True,
    })
    return flags


def build_redaction_policy(evidence_refs: tuple[str, ...] = ("policy:0174U9",)) -> RedactionPolicy:
    base = {
        "policy_id": "redaction_policy_0174U9_v2",
        "policy_version": MODEL_VERSION,
        "redact_raw_text": True,
        "redact_operator_identity": True,
        "redact_credentials": True,
        "redact_env_paths": True,
        "redact_tokens": True,
        "redact_emails": True,
        "redact_phone_numbers": True,
        "redact_urls_if_secret_like": True,
        "preserve_hashes": True,
        "preserve_evidence_refs": True,
        "preserve_model_versions": True,
        "preserve_blocked_reasons": True,
        "preserve_safety_flags": True,
        "evidence_refs": evidence_refs,
    }
    return RedactionPolicy(policy_hash=_digest(base), **base)


def _normalize_family(family: str) -> str:
    return family if family in ENTRY_FAMILIES else "unknown_or_blocked"


def _source_id(payload: dict[str, Any], fallback: str) -> str:
    for key in (
        "raw_input_id", "idea_id", "intent_id", "brief_id", "writer_output_id",
        "draft_id", "bundle_id", "dry_run_id", "candidate_id",
        "headline_context_packet_id", "artifact_intake_id", "assessment_id",
        "artifact_idea_seed_id", "ledger_entry_id", "outbox_entry_id",
        "record_id", "id",
    ):
        if payload.get(key):
            return str(payload[key])
    return fallback


def _detect_forbidden_text(text: str) -> tuple[bool, str]:
    redacted = text
    found = False
    for name, pat in (
        ("email", EMAIL_RE), ("phone", PHONE_RE), ("token", TOKEN_RE),
        ("env_path", ENV_PATH_RE), ("secret_url", SECRET_URL_RE),
    ):
        new = pat.sub(f"[REDACTED_{name.upper()}]", redacted)
        found = found or new != redacted
        redacted = new
    return found, redacted


def _redact_value(key: str, value: Any, fields: set[str]) -> Any:
    low = key.lower()
    if any(term in low for term in SENSITIVE_KEY_TERMS):
        fields.add(key)
        return "[REDACTED]"
    if isinstance(value, str):
        found, redacted = _detect_forbidden_text(value)
        if found:
            fields.add(key)
        if len(redacted) > 180:
            fields.add(key + ":truncated")
            redacted = redacted[:180] + "…"
        return redacted
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, list):
        return [_redact_value(key, v, fields) for v in value[:8]]
    if isinstance(value, tuple):
        return [_redact_value(key, v, fields) for v in list(value)[:8]]
    if isinstance(value, dict):
        return {str(k): _redact_value(str(k), v, fields) for k, v in list(value.items())[:12]}
    return str(value)


def redact_payload_summary(payload: Any, policy: RedactionPolicy) -> tuple[dict[str, Any], tuple[str, ...]]:
    data = _asdict(payload)
    if not isinstance(data, dict):
        data = {"value": data}
    fields: set[str] = set()
    preserved = {
        "source_object_id": _source_id(data, "unknown_source_object"),
        "model_version": data.get("model_version") or data.get("source_model_version") or data.get("ledger_version"),
        "evidence_refs": list(data.get("evidence_refs") or data.get("retained_evidence_refs") or []),
        "blocked_reasons": list(data.get("blocked_reasons") or data.get("blocked_reason_refs") or []),
        "safety_flags": dict(data.get("safety_flags") or data.get("safety_state_snapshot") or {}),
    }
    display_keys = [
        "content_lane", "source_requirement_status", "claim_risk_class",
        "review_status", "validation_status", "eligibility_class", "artifact_family",
        "candidate_class", "topic_hint", "context_summary", "status", "fact_kind",
        "payload_hash", "source_payload_hash", "artifact_hash", "dry_run_hash",
    ]
    summary = {"preserved": preserved, "redacted": {}}
    for key in display_keys:
        if key in data:
            summary["redacted"][key] = _redact_value(key, data[key], fields)
    summary_hash = _digest({"payload": data, "policy": policy.policy_hash})
    summary["source_payload_digest"] = summary_hash
    return summary, tuple(sorted(fields))


def scan_for_forbidden_material(obj: Any) -> tuple[str, ...]:
    hits: list[str] = []
    allowed_sensitive_keys = {"credential_hydrated", "no_secret_material", "operator_identity_ref"}
    hash_or_id_terms = ("hash", "digest", "id")

    def walk(value: Any, key: str = "value") -> None:
        low_key = key.lower()
        if isinstance(value, dict):
            for k, v in value.items():
                low = str(k).lower()
                if any(term in low for term in SENSITIVE_KEY_TERMS) and low not in allowed_sensitive_keys:
                    hits.append(f"forbidden_key:{low}")
                walk(v, str(k))
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item, key)
        elif isinstance(value, str):
            skip_phone = any(term in low_key for term in hash_or_id_terms)
            checks = (("email", EMAIL_RE), ("token", TOKEN_RE), ("env_path", ENV_PATH_RE), ("secret_url", SECRET_URL_RE))
            for name, pat in checks:
                if pat.search(value):
                    hits.append(f"forbidden_{name}:{key}")
            if not skip_phone and PHONE_RE.search(value):
                hits.append(f"forbidden_phone:{key}")
    walk(obj)
    return tuple(sorted(set(hits)))


def _entry_hash_basis(entry: RedactedAuditLedgerEntry | dict[str, Any]) -> dict[str, Any]:
    data = _asdict(entry)
    data.pop("ledger_entry_id", None)
    data.pop("entry_hash", None)
    return data


def compute_entry_hash(entry: RedactedAuditLedgerEntry | dict[str, Any]) -> str:
    return _digest(_entry_hash_basis(entry))


def build_redacted_ledger_entry(*, entry_sequence: int, previous_entry_hash: str, entry_family: str, source_model: str, source_model_version: str, payload: Any, created_at_epoch: int = 0, operator_identity_ref: str = "operator:manual_review_redacted", evidence_refs: tuple[str, ...] = (), blocked_reasons: tuple[str, ...] = (), policy: RedactionPolicy | None = None) -> RedactedAuditLedgerEntry:
    policy = policy or build_redaction_policy()
    data = _asdict(payload)
    if not isinstance(data, dict):
        data = {"value": data}
    family = _normalize_family(entry_family)
    extra_blockers = [] if family != "unknown_or_blocked" else ["unknown_source_family_fail_closed"]
    source_object_id = _source_id(data, f"source_{entry_sequence}")
    source_object_hash = _digest({"source_model": source_model, "payload": data})
    source_payload_hash = str(data.get("payload_hash") or data.get("source_payload_hash") or data.get("artifact_hash") or data.get("dry_run_hash") or source_object_hash)
    summary, redacted_fields = redact_payload_summary(data, policy)
    source_evidence = tuple(data.get("evidence_refs") or evidence_refs or (f"source:{source_object_id}",))
    source_blockers = tuple(data.get("blocked_reasons") or blocked_reasons or ()) + tuple(extra_blockers)
    flags = safety_flags()
    flags.update({k: bool(v) for k, v in dict(data.get("safety_flags") or {}).items() if k not in FORCED_FALSE_FLAGS})
    for flag in FORCED_FALSE_FLAGS:
        flags[flag] = False
    draft = RedactedAuditLedgerEntry(
        ledger_entry_id="pending", ledger_version=LEDGER_VERSION,
        entry_sequence=int(entry_sequence), previous_entry_hash=previous_entry_hash,
        entry_hash="", entry_hash_algorithm=HASH_ALGORITHM, entry_family=family,
        source_model=source_model, source_model_version=source_model_version,
        source_object_id=source_object_id, source_object_hash=source_object_hash,
        source_payload_hash=source_payload_hash, redacted_summary=summary,
        redacted_fields=redacted_fields, retained_evidence_refs=source_evidence,
        blocked_reason_refs=tuple(dict.fromkeys(source_blockers)),
        safety_state_snapshot=flags, created_at_epoch=int(created_at_epoch),
        operator_identity_ref="redacted_operator_identity" if policy.redact_operator_identity else operator_identity_ref,
        human_review_required=True, public_postable=False, approval_granted=False,
        dispatch_ready=False, current_truth_promoted=False, dqr_cleared=False,
        readiness_cleared=False, immutable_append_only=True,
        evidence_refs=source_evidence, blocked_reasons=tuple(dict.fromkeys(source_blockers)),
    )
    entry_hash = compute_entry_hash(draft)
    return replace(draft, ledger_entry_id="ledger_entry_" + entry_hash[:24], entry_hash=entry_hash)


def build_entry_from_source(payload: Any, entry_sequence: int, previous_entry_hash: str, entry_family: str, source_model: str, source_model_version: str, **kwargs: Any) -> RedactedAuditLedgerEntry:
    return build_redacted_ledger_entry(entry_sequence=entry_sequence, previous_entry_hash=previous_entry_hash, entry_family=entry_family, source_model=source_model, source_model_version=source_model_version, payload=payload, **kwargs)


def _chain_linkage(entries: tuple[RedactedAuditLedgerEntry, ...]) -> bool:
    prev = GENESIS_HASH
    for entry in entries:
        if entry.previous_entry_hash != prev:
            return False
        if compute_entry_hash(entry) != entry.entry_hash:
            return False
        prev = entry.entry_hash
    return True


def _monotonic(entries: tuple[RedactedAuditLedgerEntry, ...]) -> bool:
    return [e.entry_sequence for e in entries] == list(range(1, len(entries) + 1))


def _all_redacted(entries: tuple[RedactedAuditLedgerEntry, ...]) -> bool:
    return not scan_for_forbidden_material([e.redacted_summary for e in entries])


def build_ledger_chain(entries: tuple[RedactedAuditLedgerEntry, ...], *, chain_id: str | None = None) -> ImmutableLedgerChain:
    evidence = tuple(dict.fromkeys(ref for e in entries for ref in e.evidence_refs))
    blockers = tuple(dict.fromkeys(reason for e in entries for reason in e.blocked_reasons))
    no_public = not any(e.public_postable for e in entries)
    no_dispatch = not any(e.dispatch_ready for e in entries)
    no_approval = not any(e.approval_granted for e in entries)
    no_truth = not any(e.current_truth_promoted for e in entries)
    no_dqr = not any(e.dqr_cleared for e in entries)
    no_ready = not any(e.readiness_cleared for e in entries)
    monotonic = _monotonic(entries)
    linkage = _chain_linkage(entries)
    redacted = _all_redacted(entries)
    basis = {"ledger_version": LEDGER_VERSION, "entry_hashes": [e.entry_hash for e in entries], "entry_count": len(entries)}
    chain_hash = _digest(basis)
    flags = safety_flags()
    return ImmutableLedgerChain(
        chain_id=chain_id or "ledger_chain_" + chain_hash[:24], ledger_version=LEDGER_VERSION,
        entry_count=len(entries), first_entry_hash=entries[0].entry_hash if entries else "",
        last_entry_hash=entries[-1].entry_hash if entries else "", chain_hash=chain_hash,
        chain_hash_algorithm=HASH_ALGORITHM, entries=entries, append_only=True,
        monotonic_sequence=monotonic, all_previous_hashes_match=linkage,
        all_entries_redacted=redacted, no_public_postable_entries=no_public,
        no_dispatch_ready_entries=no_dispatch, no_approval_granted_entries=no_approval,
        no_current_truth_promoted_entries=no_truth, no_dqr_cleared_entries=no_dqr,
        no_readiness_cleared_entries=no_ready, evidence_refs=evidence,
        blocked_reasons=blockers, safety_flags=flags,
    )


def validate_ledger_chain(chain: ImmutableLedgerChain) -> LedgerValidationResult:
    entries = chain.entries
    forbidden_hits = scan_for_forbidden_material(_asdict(chain))
    blockers: list[str] = []
    checks = {
        "hash_chain_valid": _chain_linkage(entries) and chain.all_previous_hashes_match,
        "append_only_valid": chain.append_only and all(e.immutable_append_only for e in entries),
        "monotonic_sequence_valid": _monotonic(entries) and chain.monotonic_sequence,
        "redaction_policy_applied": all(e.safety_state_snapshot.get("redaction_policy_applied") is True for e in entries),
        "forbidden_data_absent": not forbidden_hits,
        "no_secret_material": not forbidden_hits and all(e.safety_state_snapshot.get("no_secret_material") is True for e in entries),
        "no_public_postable": not any(e.public_postable for e in entries),
        "no_dispatch_ready": not any(e.dispatch_ready for e in entries),
        "no_approval_granted": not any(e.approval_granted for e in entries),
        "no_current_truth_promotion": not any(e.current_truth_promoted for e in entries),
        "no_dqr_clearance": not any(e.dqr_cleared for e in entries),
        "no_readiness_clearance": not any(e.readiness_cleared for e in entries),
        "no_provider_or_platform_behavior": not any(e.safety_state_snapshot.get(k) for e in entries for k in ("provider_api_called", "platform_api_called", "telegram_api_called", "network_performed", "env_read", "credential_hydrated", "scheduler_enabled", "scraping_performed", "dm_or_reply_automation_allowed")),
    }
    for name, passed in checks.items():
        if not passed:
            blockers.append(name + "_failed")
    blockers.extend(forbidden_hits)
    validation_id = "ledger_validation_" + _digest({"chain": chain.chain_id, "checks": checks, "blockers": blockers})[:24]
    return LedgerValidationResult(validation_id, chain.chain_id, len(entries), checks["hash_chain_valid"], checks["append_only_valid"], checks["monotonic_sequence_valid"], checks["redaction_policy_applied"], checks["forbidden_data_absent"], checks["no_secret_material"], checks["no_public_postable"], checks["no_dispatch_ready"], checks["no_approval_granted"], checks["no_current_truth_promotion"], checks["no_dqr_clearance"], checks["no_readiness_clearance"], checks["no_provider_or_platform_behavior"], "pass" if not blockers else "blocked", tuple(sorted(set(blockers))), chain.evidence_refs)


def build_contract_packet() -> dict[str, Any]:
    policy = build_redaction_policy()
    sources = [
        ("raw_operator_input", "U4", "0174U4", {"raw_input_id": "u4_raw_fixture", "raw_text": "draft from operator@example.com token=abc123456789 SECRET_KEY=C:\\tmp\\.env", "evidence_refs": ["fixture:u4_raw"]}),
        ("content_idea", "U4", "0174U4", {"idea_id": "u4_idea_fixture", "content_lane": "grounded_news_context", "evidence_refs": ["fixture:u4_idea"], "public_postable": False}),
        ("local_intent", "U4", "0174U4", {"intent_id": "u4_intent_fixture", "intent_class": "create_content_from_idea", "evidence_refs": ["fixture:u4_intent"]}),
        ("editorial_brief", "U5", "0174U5", {"brief_id": "u5_brief_fixture", "claim_risk_class": "source_context_claim", "evidence_refs": ["fixture:u5_brief"]}),
        ("ai_writer_output", "U5", "0174U5", {"writer_output_id": "u5_writer_fixture", "review_status": "review_only", "evidence_refs": ["fixture:u5_writer"]}),
        ("draft_variant", "U5", "0174U5", {"draft_id": "u5_draft_fixture", "platform": "x", "evidence_refs": ["fixture:u5_draft"]}),
        ("platform_payload_preview", "U6", "0174U6", {"preview_id": "u6_preview_fixture", "payload_hash": _digest("preview"), "evidence_refs": ["fixture:u6_preview"]}),
        ("substack_manual_export", "U6", "0174U6", {"export_package_id": "u6_substack_fixture", "source_payload_hash": _digest("substack"), "evidence_refs": ["fixture:u6_substack"]}),
        ("multi_platform_dry_run", "U6", "0174U6", {"dry_run_id": "u6_dry_run_fixture", "dry_run_hash": _digest("dry_run"), "evidence_refs": ["fixture:u6_dry_run"]}),
        ("ingestion_context_candidate", "U7", "0174U7", {"candidate_id": "u7_candidate_fixture", "candidate_class": "headline_surface", "evidence_refs": ["fixture:u7_candidate"], "may_create_current_truth": False}),
        ("headline_context_packet", "U7", "0174U7", {"headline_context_packet_id": "u7_headline_fixture", "content_lane": "grounded_news_context", "evidence_refs": ["fixture:u7_headline"]}),
        ("internal_alpha_artifact_intake", "U8", "0174U8", {"artifact_intake_id": "u8_intake_fixture", "artifact_family": "internal_alpha_report", "artifact_hash": _digest("artifact"), "evidence_refs": ["fixture:u8_intake"]}),
        ("content_eligibility_assessment", "U8", "0174U8", {"assessment_id": "u8_assessment_fixture", "eligibility_class": "eligible_for_content_idea_only", "evidence_refs": ["fixture:u8_assessment"], "dqr_cleared": False, "readiness_cleared": False}),
        ("artifact_idea_seed", "U8", "0174U8", {"artifact_idea_seed_id": "u8_seed_fixture", "topic_hint": "internal alpha artifact review", "evidence_refs": ["fixture:u8_seed"]}),
        ("approval_ledger_fact", "0174ED", "0174ED", {"ledger_entry_id": "ed_approval_fact_fixture", "payload_hash": _digest("approval"), "fact_kind": "approval", "approval_granted": False, "evidence_refs": ["fixture:0174ED"]}),
        ("dispatch_outbox_fact", "0174EE", "0174EE", {"outbox_entry_id": "ee_outbox_fact_fixture", "idempotency_key": _digest("outbox"), "dispatch_ready": False, "evidence_refs": ["fixture:0174EE"]}),
        ("manual_publish_record_future_gate", "future", "0174U9", {"record_id": "future_manual_publish_gate", "status": "future_gate_required", "evidence_refs": ["fixture:future_manual_publish"]}),
        ("metrics_record_future_gate", "future", "0174U9", {"record_id": "future_metrics_gate", "status": "future_gate_required", "evidence_refs": ["fixture:future_metrics"]}),
        ("not_real_family", "unknown", "0174U9", {"id": "unknown_fixture", "blocked_reasons": ["unknown_source_family_fail_closed"], "evidence_refs": ["fixture:unknown"]}),
    ]
    entries: list[RedactedAuditLedgerEntry] = []
    prev = GENESIS_HASH
    for seq, (family, model, version, payload) in enumerate(sources, start=1):
        entry = build_redacted_ledger_entry(entry_sequence=seq, previous_entry_hash=prev, entry_family=family, source_model=model, source_model_version=version, payload=payload, policy=policy)
        entries.append(entry)
        prev = entry.entry_hash
    chain = build_ledger_chain(tuple(entries))
    validation = validate_ledger_chain(chain)
    packet = {
        "task_label": TASK_LABEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "redaction_policy": _asdict(policy),
        "ledger_chain": _asdict(chain),
        "validation_result": _asdict(validation),
        "safety_false_flags": list(SAFETY_FALSE_FLAGS),
        "entry_families": list(ENTRY_FAMILIES),
        "ledger_scope": "docs/automation/0174U9_only",
        "next_heavy_batch_recommendation": NEXT_HEAVY_BATCH,
    }
    packet["contract_checksum"] = _digest(packet)
    return packet


def render_runbook(packet: dict[str, Any]) -> str:
    chain = packet["ledger_chain"]
    validation = packet["validation_result"]
    return "\n".join([
        "# 0174U9 Redacted Immutable Audit Ledger V2 Contract", "",
        f"- task_label: `{packet['task_label']}`",
        f"- model_version: `{packet['model_version']}`",
        f"- source_baseline_commit: `{packet['source_baseline_commit']}`",
        f"- contract_checksum: `{packet['contract_checksum']}`",
        f"- chain_id: `{chain['chain_id']}`",
        f"- entry_count: `{chain['entry_count']}`",
        f"- validation_status: `{validation['validation_status']}`", "",
        "## Contract Summary", "",
        "- Redacted evidence ledger only.",
        "- Hash-chained by SHA-256 over retained fields plus previous entry hash.",
        "- Append-only semantics; mutation/update/delete are not modeled.",
        "- Raw text, identity, credential, token, email, phone, env-like, and secret-like URL material redacted.",
        "- Hashes, evidence refs, model versions, blocked reasons, and safety flags preserved.", "",
        "## Hard Blocks", "",
        "- `public_postable=false`", "- `approval_granted=false`", "- `dispatch_ready=false`",
        "- `current_truth_promoted=false`", "- `dqr_cleared=false`", "- `readiness_cleared=false`",
        "- No provider/API/network/env/credential/scheduler/scraping/DM behavior.", "",
        "## Next heavy batch", "", f"`{packet['next_heavy_batch_recommendation']}`", "",
    ])


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174U9")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    (out / PACKET_FILENAME).write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return packet
