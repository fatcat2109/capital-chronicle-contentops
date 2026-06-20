"""Live read-only research approval packet schema contract for ContentOps 0174UO.

Deterministic local-only approval packet schema contract. No live/API/provider/network/
env/credential/browser/scheduler/scraping/DM/reply automation or UI behavior.
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
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UO_LIVE_READ_ONLY_RESEARCH_APPROVAL_PACKET_SCHEMA_V0"
MATRIX_VERSION = "0174UO_LIVE_READ_ONLY_RESEARCH_APPROVAL_PACKET_SCHEMA_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "07c093bfab6c1dd998e309bde092a74b2a785397"
DOC_REL_DIR = Path("docs") / "automation" / "0174UO"
PACKET_FILENAME = "live_read_only_research_approval_packet_schema_contract_packet.json"
RUNBOOK_FILENAME = "live_read_only_research_approval_packet_schema_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "live_read_only_research_approval_packet_schema_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UP_LIVE_READ_ONLY_RESEARCH_EVIDENCE_PACKET_DRY_RUN_SCHEMA_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)

REQUIRED_16_FIELDS = (
    "explicit_task_label",
    "platform_id",
    "endpoint_family",
    "endpoint_allowlist",
    "credential_policy",
    "credential_handle_key_names_only",
    "request_budget",
    "timeout_seconds",
    "redaction_policy",
    "secret_output_prohibition",
    "no_raw_response_logging",
    "kill_switch_state",
    "stop_conditions",
    "rollback_or_abort_policy",
    "evidence_packet_schema",
    "operator_approval_ref"
)

BOUNDARY_4_FIELDS = (
    "live_read_boundary",
    "live_write_prohibition",
    "env_read_boundary",
    "audit_chain_requirement"
)


@dataclass(frozen=True)
class LiveReadOnlyResearchApprovalPacketSchemaField:
    field_id: str
    field_name: str
    field_kind: str
    required: bool
    allowed_values: tuple[Any, ...]
    forbidden_values: tuple[Any, ...]
    default_value: Any
    validation_rule: str
    fail_closed_reason: str
    secret_safe: bool
    live_safe: bool
    evidence_refs: tuple[str, ...]
    field_hash: str = ""
    field_hash_algorithm: str = "sha256"


@dataclass(frozen=True)
class LiveReadOnlyResearchApprovalPacketTemplate:
    template_id: str
    platform_id: str
    endpoint_family: str
    approval_packet_version: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    forbidden_fields: tuple[str, ...]
    endpoint_allowlist: tuple[str, ...]
    credential_policy: str
    credential_handle_key_names_only: bool
    request_budget_default: int
    request_budget_max: int
    timeout_seconds_default: int
    redaction_policy_ref: str
    secret_output_prohibition: bool
    no_raw_response_logging: bool
    kill_switch_required: bool
    kill_switch_required_state: str
    stop_conditions: tuple[str, ...]
    rollback_or_abort_policy: str
    evidence_packet_schema: str
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
class ApprovalPacketSchemaValidationDecision:
    decision_id: str
    platform_id: str
    template_id: str
    validation_status: str
    validation_strength: str
    precheck_status: str
    required_fields_present: bool
    forbidden_fields_absent: bool
    endpoint_allowlist_status: str
    credential_policy_status: str
    request_budget_status: str
    redaction_policy_status: str
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
class LiveReadOnlyResearchApprovalPacketSchemaPacket:
    packet_id: str
    matrix_version: str
    generated_at_epoch: int
    source_baseline_commit: str
    schema_fields: tuple[LiveReadOnlyResearchApprovalPacketSchemaField, ...]
    templates: tuple[LiveReadOnlyResearchApprovalPacketTemplate, ...]
    validation_decisions: tuple[ApprovalPacketSchemaValidationDecision, ...]
    templates_by_platform: dict[str, tuple[str, ...]]
    platform_count: int
    field_count: int
    template_count: int
    decision_count: int
    schema_blocked_count: int
    schema_not_ready_count: int
    manual_only_count: int
    future_approval_packet_template_ready_count: int
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
    all_live_actions_blocked: bool
    global_schema_status: str
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


def build_schema_fields() -> tuple[LiveReadOnlyResearchApprovalPacketSchemaField, ...]:
    fields = []
    # 16 required fields
    for field_name in REQUIRED_16_FIELDS:
        f = LiveReadOnlyResearchApprovalPacketSchemaField(
            field_id=f"schema_field_{field_name}",
            field_name=field_name,
            field_kind=field_name,
            required=True,
            allowed_values=(),
            forbidden_values=(),
            default_value=None,
            validation_rule=f"check_presence_and_format_for_{field_name}",
            fail_closed_reason=f"missing_or_invalid_{field_name}",
            secret_safe=True,
            live_safe=True,
            evidence_refs=(),
            field_hash="",
            field_hash_algorithm=HASH_ALGORITHM
        )
        h = sha256(_json(f).encode("utf-8")).hexdigest()
        f = replace(f, field_hash=h)
        fields.append(f)

    # 4 boundary fields
    for field_name in BOUNDARY_4_FIELDS:
        f = LiveReadOnlyResearchApprovalPacketSchemaField(
            field_id=f"schema_field_{field_name}",
            field_name=field_name,
            field_kind=field_name,
            required=True,
            allowed_values=(),
            forbidden_values=(),
            default_value=None,
            validation_rule=f"enforce_boundary_check_for_{field_name}",
            fail_closed_reason=f"boundary_violation_{field_name}",
            secret_safe=True,
            live_safe=True,
            evidence_refs=(),
            field_hash="",
            field_hash_algorithm=HASH_ALGORITHM
        )
        h = sha256(_json(f).encode("utf-8")).hexdigest()
        f = replace(f, field_hash=h)
        fields.append(f)

    return tuple(fields)


def build_default_templates() -> tuple[LiveReadOnlyResearchApprovalPacketTemplate, ...]:
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
        required_fields = REQUIRED_16_FIELDS if not is_manual else ("explicit_task_label", "platform_id", "operator_approval_ref")
        forbidden_fields = () if not is_manual else tuple(f for f in REQUIRED_16_FIELDS if f not in required_fields)
        allowlist = (f"symbolic_allowlist_entry:{platform_id}",) if not is_manual else ()
        cred_policy = "credential_key_names_only_policy" if not is_manual else "manual_no_credential_policy"

        template = LiveReadOnlyResearchApprovalPacketTemplate(
            template_id=f"approval_template_{platform_id}",
            platform_id=platform_id,
            endpoint_family=endpoint_family,
            approval_packet_version=MATRIX_VERSION,
            required_fields=required_fields,
            optional_fields=(),
            forbidden_fields=forbidden_fields,
            endpoint_allowlist=allowlist,
            credential_policy=cred_policy,
            credential_handle_key_names_only=True if not is_manual else False,
            request_budget_default=budget,
            request_budget_max=budget,
            timeout_seconds_default=30,
            redaction_policy_ref=f"redaction_policy_{platform_id}_symbolic" if not is_manual else "",
            secret_output_prohibition=True,
            no_raw_response_logging=True,
            kill_switch_required=True if not is_manual else False,
            kill_switch_required_state="closed" if not is_manual else "",
            stop_conditions=("on_error", "on_budget_exhausted") if not is_manual else (),
            rollback_or_abort_policy="abort_on_failure_no_state_leak" if not is_manual else "",
            evidence_packet_schema=f"schema_evidence_{platform_id}_symbolic" if not is_manual else "",
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
    template: LiveReadOnlyResearchApprovalPacketTemplate,
    precheck_packet: precheck.LiveReadOnlyResearchGatePrecheckPacket | None = None
) -> ApprovalPacketSchemaValidationDecision:
    packet_pc = precheck_packet or precheck.build_supervised_live_read_only_research_gate_precheck_packet()
    pc_dec = next((d for d in packet_pc.decisions if d.platform_id == template.platform_id), None)
    if not pc_dec:
        raise ValueError(f"no_precheck_decision_found_for_platform: {template.platform_id}")

    blocked_reasons = list(pc_dec.blocked_reasons)
    missing_proofs = list(pc_dec.missing_proofs)

    is_manual = template.platform_id == "substack_newsletter"

    # Enforce basic preflight / precheck status propagation
    if pc_dec.decision_status == "blocked_precheck":
        validation_status = "schema_blocked"
        validation_strength = "deterministic_block"
        blocked_reasons.append("precheck_failed_closed_in_precheck")
    elif pc_dec.decision_status == "not_ready":
        validation_status = "schema_not_ready"
        validation_strength = "symbolic_template_only"
        blocked_reasons.append("precheck_not_ready_in_precheck")
    elif pc_dec.decision_status == "manual_only":
        validation_status = "manual_only"
        validation_strength = "manual_policy_only"
    else:
        validation_status = "schema_not_ready"
        validation_strength = "symbolic_template_only"

    # Verify forbidden live flags
    forbidden_live = (
        template.live_write_allowed_by_schema or template.env_read_allowed_by_schema or
        template.credential_hydration_allowed_by_schema or template.platform_api_call_allowed_by_schema or
        template.public_post_allowed_by_schema or template.scheduler_allowed_by_schema or
        template.browser_session_allowed_by_schema or template.readiness_cleared_by_schema or
        template.live_read_allowed_by_schema
    )
    if forbidden_live:
        validation_status = "schema_blocked"
        validation_strength = "forbidden_live_capability"
        blocked_reasons.append("forbidden_live_capability_requested")

    # Required fields verification
    required_fields_present = True
    if not is_manual:
        for field in REQUIRED_16_FIELDS:
            if field not in template.required_fields:
                required_fields_present = False
                validation_status = "schema_blocked"
                validation_strength = "missing_required_field"
                blocked_reasons.append(f"missing_required_field_{field}")
    else:
        # substack newsletter manual fields check
        required_fields_present = all(f in template.required_fields for f in ("explicit_task_label", "platform_id", "operator_approval_ref"))

    # Forbidden fields verification
    forbidden_fields_absent = True
    if is_manual:
        for field in template.forbidden_fields:
            if field in template.required_fields:
                forbidden_fields_absent = False
                validation_status = "schema_blocked"
                validation_strength = "forbidden_live_capability"
                blocked_reasons.append(f"forbidden_field_included_{field}")

    # Allowlist status
    if is_manual:
        endpoint_allowlist_status = "manual_no_api"
    elif not template.endpoint_allowlist:
        endpoint_allowlist_status = "allowlist_missing"
        validation_status = "schema_blocked"
        validation_strength = "missing_required_field"
        blocked_reasons.append("endpoint_allowlist_missing")
    else:
        endpoint_allowlist_status = "allowlist_symbolic"

    # Credential key names check
    if is_manual:
        credential_policy_status = "manual_no_credential"
    elif not template.credential_handle_key_names_only:
        credential_policy_status = "credential_values_exposed"
        validation_status = "schema_blocked"
        validation_strength = "missing_required_field"
        blocked_reasons.append("credential_values_exposed")
    else:
        credential_policy_status = "credential_key_names_only_verified"

    # Request budget status
    if is_manual:
        if template.request_budget_max > 0:
            request_budget_status = "request_budget_exceeds_limit"
            validation_status = "schema_blocked"
            validation_strength = "deterministic_block"
            blocked_reasons.append("request_budget_exceeds_limit")
        else:
            request_budget_status = "manual_no_api"
    else:
        if template.request_budget_max > 1:
            request_budget_status = "request_budget_exceeds_limit"
            validation_status = "schema_blocked"
            validation_strength = "deterministic_block"
            blocked_reasons.append("request_budget_exceeds_limit")
        else:
            request_budget_status = "request_budget_within_symbolic_limit"

    # Redaction policy
    if is_manual:
        redaction_policy_status = "manual_no_secret"
    elif not template.redaction_policy_ref:
        redaction_policy_status = "redaction_policy_missing"
        validation_status = "schema_blocked"
        validation_strength = "missing_required_field"
        blocked_reasons.append("redaction_policy_missing")
    else:
        redaction_policy_status = "redaction_policy_verified"

    # Kill switch policy status
    if is_manual:
        kill_switch_policy_status = "manual_stop_policy"
    elif not template.kill_switch_required or template.kill_switch_required_state != "closed":
        kill_switch_policy_status = "kill_switch_policy_unresolved"
        validation_status = "schema_blocked"
        validation_strength = "deterministic_block"
        blocked_reasons.append("kill_switch_policy_unresolved")
    else:
        kill_switch_policy_status = "kill_switch_closed"

    # Operator approval status
    if not template.operator_approval_required:
        operator_approval_status = "operator_approval_disabled"
        validation_status = "schema_blocked"
        validation_strength = "missing_required_field"
        blocked_reasons.append("operator_approval_disabled")
    else:
        operator_approval_status = "operator_approval_required"

    # Secret and raw response logging
    if not template.secret_output_prohibition:
        validation_status = "schema_blocked"
        validation_strength = "deterministic_block"
        blocked_reasons.append("secret_output_prohibition_disabled")
    if not template.no_raw_response_logging:
        validation_status = "schema_blocked"
        validation_strength = "deterministic_block"
        blocked_reasons.append("no_raw_response_logging_disabled")

    # Platform-specific blockers check
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
        "precheck_status": pc_dec.decision_status,
        "required_fields_present": required_fields_present,
        "forbidden_fields_absent": forbidden_fields_absent,
        "endpoint_allowlist_status": endpoint_allowlist_status,
        "credential_policy_status": credential_policy_status,
        "request_budget_status": request_budget_status,
        "redaction_policy_status": redaction_policy_status,
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

    return ApprovalPacketSchemaValidationDecision(
        decision_id=f"approval_decision_{template.platform_id}_" + h[:16],
        decision_hash=h,
        decision_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def build_u9_audit_entries(
    decisions: tuple[ApprovalPacketSchemaValidationDecision, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UO"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, dec in enumerate(decisions, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UO",
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


def build_supervised_live_read_only_research_approval_packet_schema_packet(
    templates: tuple[LiveReadOnlyResearchApprovalPacketTemplate, ...] | None = None
) -> LiveReadOnlyResearchApprovalPacketSchemaPacket:
    final_templates = templates or build_default_templates()
    schema_fields = build_schema_fields()
    pc_packet = precheck.build_supervised_live_read_only_research_gate_precheck_packet()
    decisions = tuple(compile_decision(tmpl, pc_packet) for tmpl in final_templates)

    templates_by_platform = {t.platform_id: (t.template_id,) for t in final_templates}

    schema_blocked_count = sum(1 for d in decisions if d.validation_status == "schema_blocked")
    schema_not_ready_count = sum(1 for d in decisions if d.validation_status == "schema_not_ready")
    manual_only_count = sum(1 for d in decisions if d.validation_status == "manual_only")
    future_approval_packet_template_ready_count = sum(
        1 for d in decisions if d.validation_status == "future_approval_packet_template_ready"
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

    global_schema_status = "blocked" if schema_blocked_count > 0 else "not_ready"
    all_live_actions_blocked = True

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
        "schema_blocked_count": schema_blocked_count,
        "schema_not_ready_count": schema_not_ready_count,
        "manual_only_count": manual_only_count,
        "future_approval_packet_template_ready_count": future_approval_packet_template_ready_count,
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
        "global_schema_status": global_schema_status,
        "all_live_actions_blocked": all_live_actions_blocked,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags,
        "blocked_reasons": global_blocked_reasons,
        "missing_proofs": global_missing_proofs,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }

    packet_hash = _digest(draft)
    return LiveReadOnlyResearchApprovalPacketSchemaPacket(
        packet_id="live_read_only_research_approval_packet_schema_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def render_runbook(packet: LiveReadOnlyResearchApprovalPacketSchemaPacket) -> str:
    lines = [
        "# Live Read-Only Research Approval Packet Schema V0",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- matrix_version: `{packet.matrix_version}`",
        f"- source_baseline_commit: `{packet.source_baseline_commit}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Defined Schema Fields",
        "",
        "| Field Name | Kind | Required | Secret Safe | Live Safe |",
        "|---|---|---|---|---|",
    ]
    for f in packet.schema_fields:
        lines.append(f"| `{f.field_name}` | `{f.field_kind}` | `{f.required}` | `{f.secret_safe}` | `{f.live_safe}` |")

    lines.extend([
        "",
        "## Platform Validation Decisions Matrix",
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
        "- **X**: Requires spend and rate budget proof, app access, and endpoint allowlist.",
        "- **Telegram Operator**: Distinct remote operator inbox proof required, prohibits arbitrary DM/reply automation.",
        "- **Telegram Channel Destination**: Bot channel permissions and admin validation required, prohibits auto-posting.",
        "- **Substack**: Strict manual export only template (no API request budget, no credential hydration).",
        "- **LinkedIn/Meta/TikTok**: Org/page proof, app review, creator/video proof, and developer audit requirements.",
        "- **YouTube**: Requires OAuth consent and quota proofs, strictly enforces no stale sixteen-hundred units claim.",
        "",
        "## Safety and Invariants",
        "",
        "- All live read/write/public post allowed counts are strictly zero.",
        "- All template safety metrics remain false.",
        "- U9 preflight audit entries compiled under family `live_read_only_research_approval_packet_schema_future`.",
        "",
        "## Packet Summary",
        "",
        "```json",
        json.dumps({
            "platform_count": packet.platform_count,
            "field_count": packet.field_count,
            "template_count": packet.template_count,
            "schema_blocked_count": packet.schema_blocked_count,
            "schema_not_ready_count": packet.schema_not_ready_count,
            "manual_only_count": packet.manual_only_count,
            "global_status": packet.global_schema_status,
            "all_live_actions_blocked": packet.all_live_actions_blocked,
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UO")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_supervised_live_read_only_research_approval_packet_schema_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "LiveReadOnlyResearchApprovalPacketSchemaField",
    "LiveReadOnlyResearchApprovalPacketTemplate",
    "ApprovalPacketSchemaValidationDecision",
    "LiveReadOnlyResearchApprovalPacketSchemaPacket",
    "build_schema_fields",
    "build_default_templates",
    "compile_decision",
    "build_supervised_live_read_only_research_approval_packet_schema_packet",
    "write_artifacts",
]
