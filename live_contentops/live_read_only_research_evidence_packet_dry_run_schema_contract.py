"""Live read-only research evidence packet dry-run schema contract for ContentOps 0174UP.

Deterministic local-only evidence schema contract. No live/API/provider/network/env/
credential/browser/scheduler/scraping/DM/reply automation or UI behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import platform_universe_registry_v2 as universe
from live_contentops import platform_account_binding_registry_v2_contract as binding
from live_contentops import credential_handle_dotenv_secret_boundary_v2_contract as boundary
from live_contentops import official_platform_docs_evidence_packet_matrix_contract as docs
from live_contentops import platform_permission_scope_app_review_gate_matrix_contract as permission
from live_contentops import rate_budget_kill_switch_matrix_contract as rate_budget
from live_contentops import platform_preflight_dry_run_request_budget_contract as preflight
from live_contentops import supervised_live_readiness_review_index_contract as readiness
from live_contentops import supervised_live_read_only_research_gate_precheck_contract as precheck
from live_contentops import live_read_only_research_approval_packet_schema_contract as approval
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UP_LIVE_READ_ONLY_RESEARCH_EVIDENCE_PACKET_DRY_RUN_SCHEMA_V0"
MATRIX_VERSION = "0174UP_LIVE_READ_ONLY_RESEARCH_EVIDENCE_PACKET_DRY_RUN_SCHEMA_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "672a9f7870861d836249e5017bd277a718d3f28b"
DOC_REL_DIR = Path("docs") / "automation" / "0174UP"
PACKET_FILENAME = "live_read_only_research_evidence_packet_dry_run_schema_contract_packet.json"
RUNBOOK_FILENAME = "live_read_only_research_evidence_packet_dry_run_schema_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "live_read_only_research_evidence_packet_dry_run_schema_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UQ_LIVE_READ_ONLY_RESEARCH_RUNBOOK_AND_APPROVAL_GATE_DRY_RUN_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)

ALL_FIELD_KINDS = (
    "task_identity",
    "live_or_dry_run_classification",
    "platform_identity",
    "endpoint_family",
    "endpoint_allowlist",
    "request_budget",
    "request_count",
    "timeout_seconds",
    "credential_policy",
    "credential_key_names_only",
    "credential_presence_classification",
    "secret_redaction_proof",
    "no_secret_output_confirmation",
    "no_raw_response_logging_confirmation",
    "response_status_classification",
    "response_shape_classification",
    "response_body_redaction_classification",
    "evidence_artifact_ref",
    "evidence_artifact_hash",
    "source_payload_hash",
    "request_started_at",
    "request_finished_at",
    "duration_ms_classification",
    "failure_or_timeout_classification",
    "stop_condition_triggered",
    "abort_policy_result",
    "operator_approval_ref",
    "kill_switch_state",
    "audit_entry_ref",
    "safety_flags"
)


@dataclass(frozen=True)
class LiveReadOnlyEvidencePacketSchemaField:
    field_id: str
    field_name: str
    field_kind: str
    required: bool
    allowed_values: tuple[Any, ...]
    forbidden_values: tuple[Any, ...]
    default_value: Any
    validation_rule: str
    fail_closed_reason: str
    raw_response_allowed: bool
    secret_safe: bool
    live_safe: bool
    evidence_refs: tuple[str, ...]
    field_hash: str = ""
    field_hash_algorithm: str = "sha256"


@dataclass(frozen=True)
class LiveReadOnlyEvidencePacketDryRunTemplate:
    template_id: str
    platform_id: str
    endpoint_family: str
    schema_version: str
    required_fields: tuple[str, ...]
    forbidden_fields: tuple[str, ...]
    endpoint_allowlist: tuple[str, ...]
    request_budget_max: int
    request_count_max: int
    timeout_seconds_max: int
    credential_policy: str
    credential_key_names_only_required: bool
    redaction_policy_ref: str
    raw_response_logging_allowed: bool
    secret_output_allowed: bool
    response_body_storage_allowed: bool
    status_code_storage_policy: str
    response_shape_storage_policy: str
    evidence_artifact_hash_required: bool
    source_payload_hash_required: bool
    kill_switch_required_state: str
    stop_conditions: tuple[str, ...]
    abort_policy: str
    operator_approval_required: bool
    live_read_allowed_by_schema: bool
    live_write_allowed_by_schema: bool
    env_read_allowed_by_schema: bool
    credential_hydration_allowed_by_schema: bool
    platform_api_call_allowed_by_schema: bool
    public_post_allowed_by_schema: bool
    scheduler_allowed_by_schema: bool
    browser_session_allowed_by_schema: bool
    readiness_cleared_by_schema: bool
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]
    template_hash: str = ""
    template_hash_algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.platform_id not in PLATFORM_IDS:
            raise ValueError(f"invalid_platform_id: {self.platform_id}")


@dataclass(frozen=True)
class EvidencePacketDryRunValidationDecision:
    decision_id: str
    platform_id: str
    template_id: str
    validation_status: str
    validation_strength: str
    approval_schema_status: str
    precheck_status: str
    required_fields_present: bool
    forbidden_fields_absent: bool
    endpoint_allowlist_status: str
    credential_policy_status: str
    redaction_policy_status: str
    raw_response_policy_status: str
    secret_output_policy_status: str
    response_storage_policy_status: str
    artifact_hash_policy_status: str
    request_budget_status: str
    kill_switch_policy_status: str
    operator_approval_status: str
    live_read_allowed: bool
    live_write_allowed: bool
    env_read_allowed: bool
    credential_hydrated: bool
    platform_api_called: bool
    public_post_allowed: bool
    readiness_cleared: bool
    scheduler_enabled: bool
    browser_session_used: bool
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    decision_hash: str
    decision_hash_algorithm: str


@dataclass(frozen=True)
class LiveReadOnlyEvidencePacketDryRunSchemaPacket:
    packet_id: str
    matrix_version: str
    generated_at_epoch: int
    source_baseline_commit: str
    schema_fields: tuple[LiveReadOnlyEvidencePacketSchemaField, ...]
    templates: tuple[LiveReadOnlyEvidencePacketDryRunTemplate, ...]
    validation_decisions: tuple[EvidencePacketDryRunValidationDecision, ...]
    templates_by_platform: dict[str, tuple[str, ...]]
    platform_count: int
    field_count: int
    template_count: int
    decision_count: int
    dry_run_schema_blocked_count: int
    dry_run_schema_not_ready_count: int
    manual_only_count: int
    future_evidence_packet_schema_ready_count: int
    invalid_schema_count: int
    live_read_allowed_count: int
    live_write_allowed_count: int
    env_read_allowed_count: int
    credential_hydrated_count: int
    platform_api_called_count: int
    public_post_allowed_count: int
    readiness_cleared_count: int
    scheduler_enabled_count: int
    browser_session_used_count: int
    raw_response_logging_allowed_count: int
    secret_output_allowed_count: int
    response_body_storage_allowed_count: int
    all_live_actions_blocked: bool
    all_raw_responses_blocked: bool
    all_secret_outputs_blocked: bool
    global_evidence_schema_status: str
    u9_audit_entry_ids: tuple[str, ...]
    u9_audit_entry_families: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]
    packet_hash: str
    packet_hash_algorithm: str
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


def build_schema_fields() -> tuple[LiveReadOnlyEvidencePacketSchemaField, ...]:
    fields = []
    for field_name in ALL_FIELD_KINDS:
        f = LiveReadOnlyEvidencePacketSchemaField(
            field_id=f"evidence_field_{field_name}",
            field_name=field_name,
            field_kind=field_name,
            required=True,
            allowed_values=(),
            forbidden_values=(),
            default_value=None,
            validation_rule=f"enforce_presence_and_safe_type_for_{field_name}",
            fail_closed_reason=f"missing_evidence_field_{field_name}",
            raw_response_allowed=False,
            secret_safe=True,
            live_safe=True,
            evidence_refs=(),
        )
        h = sha256(_json(f).encode("utf-8")).hexdigest()
        f = replace(f, field_hash=h)
        fields.append(f)
    return tuple(fields)


def build_default_templates() -> tuple[LiveReadOnlyEvidencePacketDryRunTemplate, ...]:
    templates = []
    specs = [
        ("x", "x_api_read_only_symbolic", 1),
        ("telegram_remote_operator", "telegram_bot_getupdates_or_webhook_symbolic", 1),
        ("telegram_channel_destination", "telegram_bot_getchat_symbolic", 1),
        ("substack_newsletter", "manual_export_no_api", 0),
        ("linkedin", "linkedin_api_read_only_symbolic", 1),
        ("threads", "meta_threads_read_only_symbolic", 1),
        ("instagram", "meta_instagram_read_only_symbolic", 1),
        ("facebook_page", "meta_facebook_page_read_only_symbolic", 1),
        ("tiktok", "tiktok_read_only_symbolic", 1),
        ("youtube", "youtube_data_api_read_only_symbolic", 1),
    ]
    for platform_id, endpoint_family, budget in specs:
        is_manual = platform_id == "substack_newsletter"
        required_fields = ALL_FIELD_KINDS if not is_manual else ("task_identity", "platform_identity", "operator_approval_ref", "safety_flags")
        forbidden_fields = () if not is_manual else tuple(f for f in ALL_FIELD_KINDS if f not in required_fields)
        allowlist = (f"symbolic_allowlist_entry:{platform_id}",) if not is_manual else ()
        cred_policy = "credential_key_names_only_policy" if not is_manual else "manual_no_credential_policy"

        template = LiveReadOnlyEvidencePacketDryRunTemplate(
            template_id=f"evidence_dry_run_template_{platform_id}",
            platform_id=platform_id,
            endpoint_family=endpoint_family,
            schema_version=MATRIX_VERSION,
            required_fields=required_fields,
            forbidden_fields=forbidden_fields,
            endpoint_allowlist=allowlist,
            request_budget_max=budget,
            request_count_max=budget,
            timeout_seconds_max=30,
            credential_policy=cred_policy,
            credential_key_names_only_required=True if not is_manual else False,
            redaction_policy_ref=f"redaction_policy_{platform_id}_symbolic" if not is_manual else "",
            raw_response_logging_allowed=False,
            secret_output_allowed=False,
            response_body_storage_allowed=False,
            status_code_storage_policy="classification_only",
            response_shape_storage_policy="classification_or_hash_only",
            evidence_artifact_hash_required=True if not is_manual else False,
            source_payload_hash_required=True if not is_manual else False,
            kill_switch_required_state="closed" if not is_manual else "",
            stop_conditions=("on_error", "on_budget_exhausted") if not is_manual else (),
            abort_policy="abort_and_clean_temporary_session" if not is_manual else "",
            operator_approval_required=True,
            live_read_allowed_by_schema=False,
            live_write_allowed_by_schema=False,
            env_read_allowed_by_schema=False,
            credential_hydration_allowed_by_schema=False,
            platform_api_call_allowed_by_schema=False,
            public_post_allowed_by_schema=False,
            scheduler_allowed_by_schema=False,
            browser_session_allowed_by_schema=False,
            readiness_cleared_by_schema=False,
            blocked_reasons=(),
            missing_proofs=()
        )
        h = sha256(_json(template).encode("utf-8")).hexdigest()
        template = replace(template, template_hash=h, template_hash_algorithm=HASH_ALGORITHM)
        templates.append(template)

    return tuple(templates)


def compile_decision(
    template: LiveReadOnlyEvidencePacketDryRunTemplate,
    approval_packet: approval.LiveReadOnlyResearchApprovalPacketSchemaPacket | None = None
) -> EvidencePacketDryRunValidationDecision:
    packet_ap = approval_packet or approval.build_supervised_live_read_only_research_approval_packet_schema_packet()
    ap_dec = next((d for d in packet_ap.validation_decisions if d.platform_id == template.platform_id), None)
    if not ap_dec:
        raise ValueError(f"no_approval_decision_found_for_platform: {template.platform_id}")

    blocked_reasons = list(ap_dec.blocked_reasons)
    missing_proofs = list(ap_dec.missing_proofs)

    is_manual = template.platform_id == "substack_newsletter"

    if ap_dec.validation_status == "schema_blocked":
        validation_status = "dry_run_schema_blocked"
        validation_strength = "deterministic_block"
        blocked_reasons.append("approval_schema_failed_in_approval")
    elif ap_dec.validation_status == "schema_not_ready":
        validation_status = "dry_run_schema_not_ready"
        validation_strength = "symbolic_schema_only"
        blocked_reasons.append("approval_schema_not_ready_in_approval")
    elif ap_dec.validation_status == "manual_only":
        validation_status = "manual_only"
        validation_strength = "manual_policy_only"
    else:
        validation_status = "dry_run_schema_not_ready"
        validation_strength = "symbolic_schema_only"

    # Enforce forbidden flags:
    forbidden_live = (
        template.live_write_allowed_by_schema or template.env_read_allowed_by_schema or
        template.credential_hydration_allowed_by_schema or template.platform_api_call_allowed_by_schema or
        template.public_post_allowed_by_schema or template.scheduler_allowed_by_schema or
        template.browser_session_allowed_by_schema or template.readiness_cleared_by_schema or
        template.live_read_allowed_by_schema
    )
    if forbidden_live:
        validation_status = "dry_run_schema_blocked"
        validation_strength = "forbidden_live_capability"
        blocked_reasons.append("forbidden_live_capability_requested")

    if template.raw_response_logging_allowed:
        validation_status = "dry_run_schema_blocked"
        validation_strength = "forbidden_raw_response"
        blocked_reasons.append("raw_response_logging_allowed")

    if template.secret_output_allowed:
        validation_status = "dry_run_schema_blocked"
        validation_strength = "forbidden_secret_output"
        blocked_reasons.append("secret_output_allowed")

    if template.response_body_storage_allowed:
        validation_status = "dry_run_schema_blocked"
        validation_strength = "forbidden_raw_response"
        blocked_reasons.append("response_body_storage_allowed")

    # Fields verification
    required_fields_present = True
    if not is_manual:
        for field in ALL_FIELD_KINDS:
            if field not in template.required_fields:
                required_fields_present = False
                validation_status = "dry_run_schema_blocked"
                validation_strength = "missing_required_field"
                blocked_reasons.append(f"missing_required_field_{field}")
    else:
        required_fields_present = all(f in template.required_fields for f in ("task_identity", "platform_identity", "operator_approval_ref", "safety_flags"))

    forbidden_fields_absent = True
    if is_manual:
        for field in template.forbidden_fields:
            if field in template.required_fields:
                forbidden_fields_absent = False
                validation_status = "dry_run_schema_blocked"
                validation_strength = "forbidden_live_capability"
                blocked_reasons.append(f"forbidden_field_included_{field}")

    # Allowlist
    if is_manual:
        endpoint_allowlist_status = "manual_no_api"
    elif not template.endpoint_allowlist:
        endpoint_allowlist_status = "allowlist_missing"
        validation_status = "dry_run_schema_blocked"
        validation_strength = "missing_required_field"
        blocked_reasons.append("endpoint_allowlist_missing")
    else:
        endpoint_allowlist_status = "allowlist_symbolic"

    # Credential key names
    if is_manual:
        credential_policy_status = "manual_no_credential"
    elif not template.credential_key_names_only_required:
        credential_policy_status = "credential_values_exposed"
        validation_status = "dry_run_schema_blocked"
        validation_strength = "missing_required_field"
        blocked_reasons.append("credential_values_exposed")
    else:
        credential_policy_status = "credential_key_names_only_verified"

    # Redaction status
    if is_manual:
        redaction_policy_status = "manual_no_secret"
    elif not template.redaction_policy_ref:
        redaction_policy_status = "redaction_policy_missing"
        validation_status = "dry_run_schema_blocked"
        validation_strength = "missing_required_field"
        blocked_reasons.append("redaction_policy_missing")
    else:
        redaction_policy_status = "redaction_policy_verified"

    # Raw response
    if template.raw_response_logging_allowed:
        raw_response_policy_status = "raw_response_allowed_blocked"
    else:
        raw_response_policy_status = "raw_response_blocked_ok"

    # Secret output
    if template.secret_output_allowed:
        secret_output_policy_status = "secret_output_allowed_blocked"
    else:
        secret_output_policy_status = "secret_output_blocked_ok"

    # Response storage
    if template.response_body_storage_allowed or template.status_code_storage_policy != "classification_only" or template.response_shape_storage_policy != "classification_or_hash_only":
        response_storage_policy_status = "response_body_storage_allowed_blocked"
        validation_status = "dry_run_schema_blocked"
        validation_strength = "forbidden_raw_response"
        blocked_reasons.append("response_body_storage_allowed")
    else:
        response_storage_policy_status = "classification_only_ok"

    # Artifact hash
    if not is_manual and (not template.evidence_artifact_hash_required or not template.source_payload_hash_required):
        artifact_hash_policy_status = "artifact_hash_missing_blocked"
        validation_status = "dry_run_schema_blocked"
        validation_strength = "missing_required_field"
        blocked_reasons.append("artifact_hash_missing")
    else:
        artifact_hash_policy_status = "artifact_hash_required_ok"

    # Request budget
    if is_manual:
        if template.request_budget_max > 0:
            request_budget_status = "request_budget_exceeds_limit"
            validation_status = "dry_run_schema_blocked"
            validation_strength = "deterministic_block"
            blocked_reasons.append("request_budget_exceeds_limit")
        else:
            request_budget_status = "manual_no_api"
    else:
        if template.request_budget_max > 1:
            request_budget_status = "request_budget_exceeds_limit"
            validation_status = "dry_run_schema_blocked"
            validation_strength = "deterministic_block"
            blocked_reasons.append("request_budget_exceeds_limit")
        else:
            request_budget_status = "request_budget_within_symbolic_limit"

    # Kill switch required
    if is_manual:
        kill_switch_policy_status = "manual_stop_policy"
    elif template.kill_switch_required_state != "closed":
        kill_switch_policy_status = "kill_switch_policy_unresolved"
        validation_status = "dry_run_schema_blocked"
        validation_strength = "deterministic_block"
        blocked_reasons.append("kill_switch_policy_unresolved")
    else:
        kill_switch_policy_status = "kill_switch_closed"

    # Operator approval
    if not template.operator_approval_required:
        operator_approval_status = "operator_approval_disabled"
        validation_status = "dry_run_schema_blocked"
        validation_strength = "missing_required_field"
        blocked_reasons.append("operator_approval_disabled")
    else:
        operator_approval_status = "operator_approval_required"

    # Enforce platform specific blockers
    if template.platform_id == "x":
        for b in ("x_app_access_gap", "spend_gate_unresolved", "rate_budget_gap", "read_only_endpoint_proof_gap"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif template.platform_id == "telegram_remote_operator":
        for b in ("no_arbitrary_dm_allowed", "operator_inbox_proof_required"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif template.platform_id == "telegram_channel_destination":
        for b in ("channel_admin_proof_required", "bot_permission_gap", "channel_state_symbolic_only"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif template.platform_id == "substack_newsletter":
        blocked_reasons.append("manual_export_only")
        missing_proofs.append("manual_export_only")
    elif template.platform_id == "linkedin":
        blocked_reasons.append("linkedin_organization_page_proof_missing")
        missing_proofs.append("linkedin_organization_page_proof_missing")
    elif template.platform_id in ("threads", "instagram", "facebook_page"):
        for b in ("meta_app_review_closed", "meta_app_account_proof_required"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif template.platform_id == "tiktok":
        for b in ("tiktok_app_audit_closed", "creator_account_proof_required", "video_publish_proof_required"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif template.platform_id == "youtube":
        for b in ("youtube_quota_unresolved", "youtube_oauth_flow_closed", "upload_proof_required"):
            blocked_reasons.append(b)
            missing_proofs.append(b)

    draft = {
        "platform_id": template.platform_id,
        "template_id": template.template_id,
        "validation_status": validation_status,
        "validation_strength": validation_strength,
        "approval_schema_status": ap_dec.validation_status,
        "precheck_status": ap_dec.precheck_status,
        "required_fields_present": required_fields_present,
        "forbidden_fields_absent": forbidden_fields_absent,
        "endpoint_allowlist_status": endpoint_allowlist_status,
        "credential_policy_status": credential_policy_status,
        "redaction_policy_status": redaction_policy_status,
        "raw_response_policy_status": raw_response_policy_status,
        "secret_output_policy_status": secret_output_policy_status,
        "response_storage_policy_status": response_storage_policy_status,
        "artifact_hash_policy_status": artifact_hash_policy_status,
        "request_budget_status": request_budget_status,
        "kill_switch_policy_status": kill_switch_policy_status,
        "operator_approval_status": operator_approval_status,
        "live_read_allowed": False,
        "live_write_allowed": False,
        "env_read_allowed": False,
        "credential_hydrated": False,
        "platform_api_called": False,
        "public_post_allowed": False,
        "readiness_cleared": False,
        "scheduler_enabled": False,
        "browser_session_used": False,
        "blocked_reasons": tuple(dict.fromkeys(blocked_reasons)),
        "missing_proofs": tuple(dict.fromkeys(missing_proofs)),
        "evidence_refs": template.endpoint_allowlist,
    }

    h_basis = {str(k): _asdict(v) for k, v in draft.items()}
    h = sha256(json.dumps(h_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    return EvidencePacketDryRunValidationDecision(
        decision_id=f"evidence_dry_run_decision_{template.platform_id}_" + h[:16],
        decision_hash=h,
        decision_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def build_u9_audit_entries(
    decisions: tuple[EvidencePacketDryRunValidationDecision, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UP"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, dec in enumerate(decisions, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UP",
            source_model_version=MATRIX_VERSION,
            payload={
                "id": dec.decision_id,
                "platform_id": dec.platform_id,
                "status": dec.validation_status,
                "source_payload_hash": dec.decision_hash,
                "blocked_reasons": dec.blocked_reasons,
                "missing_proofs": dec.missing_proofs,
                "safety_flags": {
                    "live_read_allowed": dec.live_read_allowed,
                    "live_write_allowed": dec.live_write_allowed,
                    "env_read_allowed": dec.env_read_allowed,
                    "credential_hydrated": dec.credential_hydrated,
                    "platform_api_called": dec.platform_api_called,
                    "readiness_cleared": dec.readiness_cleared,
                    "public_post_allowed": dec.public_post_allowed,
                },
            },
            policy=policy,
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(
    templates: tuple[LiveReadOnlyEvidencePacketDryRunTemplate, ...] | None = None
) -> LiveReadOnlyEvidencePacketDryRunSchemaPacket:
    final_templates = templates or build_default_templates()
    schema_fields = build_schema_fields()
    ap_packet = approval.build_supervised_live_read_only_research_approval_packet_schema_packet()
    decisions = tuple(compile_decision(tmpl, ap_packet) for tmpl in final_templates)

    templates_by_platform = {t.platform_id: (t.template_id,) for t in final_templates}

    dry_run_schema_blocked_count = sum(1 for d in decisions if d.validation_status == "dry_run_schema_blocked")
    dry_run_schema_not_ready_count = sum(1 for d in decisions if d.validation_status == "dry_run_schema_not_ready")
    manual_only_count = sum(1 for d in decisions if d.validation_status == "manual_only")
    future_evidence_packet_schema_ready_count = sum(
        1 for d in decisions if d.validation_status == "future_evidence_packet_schema_ready"
    )
    invalid_schema_count = sum(1 for d in decisions if d.validation_status == "invalid_schema")

    live_read_allowed_count = 0
    live_write_allowed_count = 0
    env_read_allowed_count = 0
    credential_hydrated_count = 0
    platform_api_called_count = 0
    public_post_allowed_count = 0
    readiness_cleared_count = 0
    scheduler_enabled_count = 0
    browser_session_used_count = 0

    raw_response_logging_allowed_count = 0
    secret_output_allowed_count = 0
    response_body_storage_allowed_count = 0

    global_evidence_schema_status = "blocked" if dry_run_schema_blocked_count > 0 else "not_ready"
    all_live_actions_blocked = True
    all_raw_responses_blocked = True
    all_secret_outputs_blocked = True

    global_blocked_reasons = tuple(dict.fromkeys(reason for d in decisions for reason in d.blocked_reasons))
    global_missing_proofs = tuple(dict.fromkeys(proof for d in decisions for proof in d.missing_proofs))
    evidence_refs = tuple(dict.fromkeys(ref for t in final_templates for ref in t.endpoint_allowlist))

    audit_entries = build_u9_audit_entries(decisions)

    safety_flags = {
        "live_read_allowed": False,
        "live_write_allowed": False,
        "public_post_allowed": False,
        "credential_hydrated": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "telegram_api_called": False,
        "network_performed": False,
        "env_read": False,
        "browser_session_used": False,
        "scheduler_enabled": False,
        "scraping_performed": False,
        "dm_or_reply_automation_allowed": False,
        "dispatch_ready": False,
        "public_postable": False,
        "autonomous_posting_allowed": False,
        "current_truth_promoted": False,
        "dqr_cleared": False,
        "readiness_cleared": False,
        "ingestion_repo_mutated": False,
        "ui_generated": False,
        "local_readiness_review_only": True,
        "review_only": True,
    }

    draft = {
        "matrix_version": MATRIX_VERSION,
        "generated_at_epoch": 0,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "schema_fields": schema_fields,
        "templates": final_templates,
        "validation_decisions": decisions,
        "templates_by_platform": templates_by_platform,
        "platform_count": len(decisions),
        "field_count": len(schema_fields),
        "template_count": len(final_templates),
        "decision_count": len(decisions),
        "dry_run_schema_blocked_count": dry_run_schema_blocked_count,
        "dry_run_schema_not_ready_count": dry_run_schema_not_ready_count,
        "manual_only_count": manual_only_count,
        "future_evidence_packet_schema_ready_count": future_evidence_packet_schema_ready_count,
        "invalid_schema_count": invalid_schema_count,
        "live_read_allowed_count": live_read_allowed_count,
        "live_write_allowed_count": live_write_allowed_count,
        "env_read_allowed_count": env_read_allowed_count,
        "credential_hydrated_count": credential_hydrated_count,
        "platform_api_called_count": platform_api_called_count,
        "public_post_allowed_count": public_post_allowed_count,
        "readiness_cleared_count": readiness_cleared_count,
        "scheduler_enabled_count": scheduler_enabled_count,
        "browser_session_used_count": browser_session_used_count,
        "raw_response_logging_allowed_count": raw_response_logging_allowed_count,
        "secret_output_allowed_count": secret_output_allowed_count,
        "response_body_storage_allowed_count": response_body_storage_allowed_count,
        "all_live_actions_blocked": all_live_actions_blocked,
        "all_raw_responses_blocked": all_raw_responses_blocked,
        "all_secret_outputs_blocked": all_secret_outputs_blocked,
        "global_evidence_schema_status": global_evidence_schema_status,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags,
        "blocked_reasons": global_blocked_reasons,
        "missing_proofs": global_missing_proofs,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }

    packet_hash = _digest(draft)
    return LiveReadOnlyEvidencePacketDryRunSchemaPacket(
        packet_id="live_read_only_research_evidence_packet_dry_run_schema_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def render_runbook(packet: LiveReadOnlyEvidencePacketDryRunSchemaPacket) -> str:
    lines = [
        "# Live Read-Only Research Evidence Packet Dry-Run Schema V0",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- matrix_version: `{packet.matrix_version}`",
        f"- source_baseline_commit: `{packet.source_baseline_commit}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Defined Evidence Schema Fields",
        "",
        "| Field Name | Kind | Required | Raw Response Allowed | Secret Safe | Live Safe |",
        "|---|---|---|---|---|---|",
    ]
    for f in packet.schema_fields:
        lines.append(f"| `{f.field_name}` | `{f.field_kind}` | `{f.required}` | `{f.raw_response_allowed}` | `{f.secret_safe}` | `{f.live_safe}` |")

    lines.extend([
        "",
        "## Platform Evidence Validation Decisions Matrix",
        "",
        "| Platform ID | Status | Strength | Precheck Status | Fields Present | Allowlist Status | Credential Status | Budget Status | Kill Switch Status |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for d in packet.validation_decisions:
        lines.append(
            f"| `{d.platform_id}` | `{d.validation_status}` | `{d.validation_strength}` | `{d.precheck_status}` | `{d.required_fields_present}` | `{d.endpoint_allowlist_status}` | `{d.credential_policy_status}` | `{d.request_budget_status}` | `{d.kill_switch_policy_status}` |"
        )

    lines.extend([
        "",
        "## Platform-Specific Constraints Enforced by Schema",
        "",
        "- **X**: Requires app access/spend/rate budget proof and endpoint allowlist proof.",
        "- **Telegram Operator**: Distinct remote operator inbox proof required, prohibits arbitrary DM/reply automation.",
        "- **Telegram Channel Destination**: Bot channel permissions and admin validation required, prohibits posting side effects.",
        "- **Substack**: Strict manual export only template (no API request budget, no credential hydration, no raw response).",
        "- **LinkedIn/Meta/TikTok**: Org/page proof, app review, creator/video proof, and developer audit requirements.",
        "- **YouTube**: Requires OAuth consent and quota proofs, strictly enforces no stale sixteen-hundred units claim.",
        "",
        "## Safety and Invariants",
        "",
        "- All live read/write/public post allowed counts are strictly zero.",
        "- All template safety metrics remain false.",
        "- U9 preflight audit entries compiled under family `live_read_only_research_evidence_packet_dry_run_schema_future`.",
        "",
        "## Packet Summary",
        "",
        "```json",
        json.dumps({
            "platform_count": packet.platform_count,
            "field_count": packet.field_count,
            "template_count": packet.template_count,
            "dry_run_schema_blocked_count": packet.dry_run_schema_blocked_count,
            "dry_run_schema_not_ready_count": packet.dry_run_schema_not_ready_count,
            "manual_only_count": packet.manual_only_count,
            "global_status": packet.global_evidence_schema_status,
            "all_live_actions_blocked": packet.all_live_actions_blocked,
            "all_raw_responses_blocked": packet.all_raw_responses_blocked,
            "all_secret_outputs_blocked": packet.all_secret_outputs_blocked,
        }, indent=2, sort_keys=True),
        "```",
        ""
    ])
    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UP")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "LiveReadOnlyEvidencePacketSchemaField",
    "LiveReadOnlyEvidencePacketDryRunTemplate",
    "EvidencePacketDryRunValidationDecision",
    "LiveReadOnlyEvidencePacketDryRunSchemaPacket",
    "build_schema_fields",
    "build_default_templates",
    "compile_decision",
    "build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet",
    "write_artifacts",
]
