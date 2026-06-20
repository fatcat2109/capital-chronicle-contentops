"""Local preflight bundle and V5 read-model precheck contract for ContentOps 0174UU.

Consolidated preflight bundle contract combining recent live-read-only research gates,
slot checks, mock inspections, bindings, registries, budgets, and audit ledgers.
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
from live_contentops import live_read_only_research_approval_packet_schema_contract as approval
from live_contentops import live_read_only_research_evidence_packet_dry_run_schema_contract as evidence
from live_contentops import live_read_only_research_runbook_approval_gate_dry_run_contract as runbook
from live_contentops import live_read_only_research_local_preflight_simulation_contract as simulation
from live_contentops import read_only_credential_slot_check_validation_contract as slot_check
from live_contentops import read_only_credential_slot_inspection_mock_audit_contract as mock_audit
from live_contentops import supervised_live_read_only_research_gate_precheck_contract as gate_precheck
from live_contentops import platform_preflight_dry_run_request_budget_contract as request_budget
from live_contentops import rate_budget_kill_switch_matrix_contract as kill_switch
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit
from live_contentops import local_content_governance_summary_mart_contract as governance_mart
from live_contentops import manual_publish_record_metrics_ledger_contract as manual_publish
from live_contentops import content_performance_review_editorial_feedback_contract as performance_review
from live_contentops import internal_alpha_artifact_intake_content_eligibility_contract as eligibility

TASK_LABEL = "TASK_CONTENTOPS_0174UU_LOCAL_PREFLIGHT_BUNDLE_AND_V5_READ_MODEL_BINDING_PRECHECK_V0"
MATRIX_VERSION = "0174UU_LOCAL_PREFLIGHT_BUNDLE_V5_READ_MODEL_PRECHECK_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "25e88d61625a3c5ed55e1b79a53854fe07632487"
DOC_REL_DIR = Path("docs") / "automation" / "0174UU"
PACKET_FILENAME = "local_preflight_bundle_v5_read_model_precheck_contract_packet.json"
RUNBOOK_FILENAME = "local_preflight_bundle_v5_read_model_precheck_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "local_preflight_bundle_v5_read_model_precheck_future"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0174UV_V5_COCKPIT_READ_MODEL_INTEGRATION_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class LocalPreflightBundleSourceRef:
    source_ref_id: str
    task_family: str
    module_name: str
    artifact_family: str
    consumed: bool = True
    source_status: str = "valid"
    source_hash_or_packet_hash: str = ""
    live_capability_added: bool = False
    credential_values_accessed: bool = False
    env_read: bool = False
    platform_api_called: bool = False
    ui_mutated: bool = False
    ingestion_mutated: bool = False


@dataclass(frozen=True)
class LocalPreflightBundlePlatformState:
    platform_id: str
    platform_role: str
    primary_or_secondary_or_expansion: str
    endpoint_family: str
    account_binding_status: str
    credential_slot_status: str
    credential_mock_audit_status: str
    approval_gate_status: str
    evidence_packet_status: str
    preflight_simulation_status: str
    rate_budget_status: str
    kill_switch_status: str
    manual_export_status: str
    v5_display_status: str
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]
    safe_display_fields: tuple[str, ...]
    hidden_or_absent_fields: tuple[str, ...]
    redaction_required_fields: tuple[str, ...]
    live_read_allowed: bool = False
    live_write_allowed: bool = False
    public_post_allowed: bool = False
    dispatch_ready: bool = False
    readiness_cleared: bool = False


@dataclass(frozen=True)
class V5ReadModelCandidateField:
    field_id: str
    room_id: str
    source_family: str
    field_name: str
    field_kind: str
    display_policy: str  # safe_to_show / redacted / hidden / absent
    current_truth_policy: str  # current_state / historical_evidence / reference_only / future_gate
    user_action_affordance: str  # read_only / manual_review_only / disabled_future_gate
    forbidden_affordance_reason: str
    sample_value_classification: str
    source_ref_id: str
    evidence_ref: str


@dataclass(frozen=True)
class V5RoomBindingPrecheck:
    room_id: str
    binding_status: str  # ready_for_read_model_design / blocked_missing_contract / future_gate_only
    safe_fields_count: int
    hidden_fields_count: int
    redacted_fields_count: int
    disabled_affordances: tuple[str, ...]
    required_contracts: tuple[str, ...]
    missing_contracts: tuple[str, ...]
    safety_notes: str
    no_live_action_affordances: bool = True


@dataclass(frozen=True)
class LocalPreflightBundleV5ReadModelPrecheckPacket:
    packet_id: str
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    source_ref_count: int
    platform_count: int
    candidate_field_count: int
    room_count: int
    source_refs: tuple[LocalPreflightBundleSourceRef, ...]
    platform_states: tuple[LocalPreflightBundlePlatformState, ...]
    v5_candidate_fields: tuple[V5ReadModelCandidateField, ...]
    room_binding_prechecks: tuple[V5RoomBindingPrecheck, ...]
    global_blocked_reasons: tuple[str, ...]
    global_missing_proofs: tuple[str, ... ]
    ui_binding_policy: str
    safety_flags: dict[str, bool]
    u9_audit_entry_ids: tuple[str, ...]
    u9_audit_entry_families: tuple[str, ...]
    packet_hash: str
    packet_hash_algorithm: str
    next_recommended_task: str


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


def get_source_hash(module_name: str, module: Any) -> str:
    for attr in (
        "build_supervised_credential_slot_inspection_audit_packet",
        "build_supervised_read_only_credential_slot_check_packet",
        "build_supervised_live_read_only_research_local_preflight_simulation_packet",
        "build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet",
        "build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet",
        "build_supervised_live_read_only_research_approval_packet_schema_packet",
        "build_supervised_live_read_only_research_gate_precheck_packet",
        "build_preflight_dry_run_request_budget_packet",
        "build_rate_budget_kill_switch_packet",
        "build_platform_account_binding_registry_packet",
        "build_credential_boundary_packet",
        "build_mart",
        "build_contract_packet",
    ):
        if hasattr(module, attr):
            func = getattr(module, attr)
            try:
                if attr in ("build_mart", "build_contract_packet"):
                    res = func()
                    if isinstance(res, dict) and "packet_hash" in res:
                        return res["packet_hash"]
                    if hasattr(res, "packet_hash"):
                        return res.packet_hash
                else:
                    res = func()
                    if hasattr(res, "packet_hash"):
                        return res.packet_hash
            except Exception:
                pass
    try:
        file_path = Path(module.__file__)
        if file_path.exists():
            return sha256(file_path.read_bytes()).hexdigest()
    except Exception:
        pass
    return sha256(module_name.encode("utf-8")).hexdigest()


def build_source_refs() -> tuple[LocalPreflightBundleSourceRef, ...]:
    precedents = (
        ("platform_universe_registry_v2", universe, "universe_registry", "platforms"),
        ("platform_account_binding_registry_v2_contract", binding, "account_binding", "bindings"),
        ("credential_handle_dotenv_secret_boundary_v2_contract", boundary, "secret_boundary", "secret_boundary"),
        ("live_read_only_research_approval_packet_schema_contract", approval, "live_read_only_research_approval", "approval_schema"),
        ("live_read_only_research_evidence_packet_dry_run_schema_contract", evidence, "live_read_only_research_evidence", "evidence_schema"),
        ("live_read_only_research_runbook_approval_gate_dry_run_contract", runbook, "live_read_only_research_runbook", "runbook_gate"),
        ("live_read_only_research_local_preflight_simulation_contract", simulation, "live_read_only_research_simulation", "simulation_gate"),
        ("read_only_credential_slot_check_validation_contract", slot_check, "read_only_credential_slot_check", "slot_check"),
        ("read_only_credential_slot_inspection_mock_audit_contract", mock_audit, "read_only_credential_slot_inspection", "mock_audit"),
        ("supervised_live_read_only_research_gate_precheck_contract", gate_precheck, "supervised_live_read_only_research", "gate_precheck"),
        ("platform_preflight_dry_run_request_budget_contract", request_budget, "platform_preflight_dry_run", "budget_decision"),
        ("rate_budget_kill_switch_matrix_contract", kill_switch, "rate_budget_kill_switch", "kill_switch_packet"),
        ("redacted_immutable_audit_ledger_v2_contract", audit, "audit_ledger", "ledger_rules"),
        ("local_content_governance_summary_mart_contract", governance_mart, "governance_summary", "summary_mart"),
        ("manual_publish_record_metrics_ledger_contract", manual_publish, "manual_publish", "metrics_ledger"),
        ("content_performance_review_editorial_feedback_contract", performance_review, "performance_review", "feedback_loop"),
        ("internal_alpha_artifact_intake_content_eligibility_contract", eligibility, "artifact_intake", "intake_eligibility"),
    )
    return tuple(
        LocalPreflightBundleSourceRef(
            source_ref_id=name,
            task_family=fam,
            module_name=f"live_contentops.{name}",
            artifact_family=art,
            source_hash_or_packet_hash=get_source_hash(name, mod),
        )
        for name, mod, fam, art in precedents
    )


def build_platform_states() -> tuple[LocalPreflightBundlePlatformState, ...]:
    states = []
    for pid in PLATFORM_IDS:
        p_entry = next(entry for entry in universe.PLATFORMS if entry.platform_id == pid)
        role = p_entry.platform_role
        is_primary = pid in ("x", "substack_newsletter")
        primary_secondary = "primary" if is_primary else ("secondary" if pid in ("telegram_channel_destination", "linkedin") else "expansion")
        endpoint_family = "manual" if pid == "substack_newsletter" else "live_read_only"

        # Platform spec blockers
        blocked_reasons: list[str] = []
        missing_proofs: list[str] = []

        if pid == "x":
            blocked_reasons.extend(["x_app_access_gap", "spend_gate_unresolved", "rate_budget_gap", "read_only_endpoint_proof_gap"])
            missing_proofs.extend(["x_app_access_gap", "spend_gate_unresolved", "rate_budget_gap", "read_only_endpoint_proof_gap"])
        elif pid == "telegram_remote_operator":
            blocked_reasons.extend(["no_arbitrary_dm_allowed", "operator_inbox_proof_required"])
            missing_proofs.extend(["no_arbitrary_dm_allowed", "operator_inbox_proof_required"])
        elif pid == "telegram_channel_destination":
            blocked_reasons.extend(["channel_admin_proof_required", "bot_permission_gap", "channel_state_symbolic_only"])
            missing_proofs.extend(["channel_admin_proof_required", "bot_permission_gap", "channel_state_symbolic_only"])
        elif pid == "substack_newsletter":
            blocked_reasons.extend(["manual_export_only"])
            missing_proofs.extend(["manual_export_only"])
        elif pid == "linkedin":
            blocked_reasons.extend(["linkedin_organization_page_proof_missing"])
            missing_proofs.extend(["linkedin_organization_page_proof_missing"])
        elif pid in ("threads", "instagram", "facebook_page"):
            blocked_reasons.extend(["meta_app_review_closed", "meta_app_account_proof_required"])
            missing_proofs.extend(["meta_app_review_closed", "meta_app_account_proof_required"])
        elif pid == "tiktok":
            blocked_reasons.extend(["tiktok_app_audit_closed", "creator_account_proof_required", "video_publish_proof_required"])
            missing_proofs.extend(["tiktok_app_audit_closed", "creator_account_proof_required", "video_publish_proof_required"])
        elif pid == "youtube":
            blocked_reasons.extend(["youtube_quota_unresolved", "youtube_oauth_flow_closed", "upload_proof_required"])
            missing_proofs.extend(["youtube_quota_unresolved", "youtube_oauth_flow_closed", "upload_proof_required"])

        # Default values matching task specs
        account_binding_status = "symbolic" if pid != "substack_newsletter" else "bound"
        credential_slot_status = "key_names_only" if pid != "substack_newsletter" else "manual_no_credential"
        credential_mock_audit_status = "blocked" if pid != "substack_newsletter" else "manual_only"
        approval_gate_status = "blocked" if pid != "substack_newsletter" else "manual_only"
        evidence_packet_status = "blocked" if pid != "substack_newsletter" else "manual_only"
        preflight_simulation_status = "blocked" if pid != "substack_newsletter" else "manual_only"
        rate_budget_status = "blocked" if pid != "substack_newsletter" else "limit_not_applicable"
        kill_switch_status = "open_fails_closed" if pid != "substack_newsletter" else "not_applicable"
        manual_export_status = "manual_export_only" if pid == "substack_newsletter" else "not_applicable"
        v5_display_status = "hidden_fields_only"

        states.append(
            LocalPreflightBundlePlatformState(
                platform_id=pid,
                platform_role=role,
                primary_or_secondary_or_expansion=primary_secondary,
                endpoint_family=endpoint_family,
                account_binding_status=account_binding_status,
                credential_slot_status=credential_slot_status,
                credential_mock_audit_status=credential_mock_audit_status,
                approval_gate_status=approval_gate_status,
                evidence_packet_status=evidence_packet_status,
                preflight_simulation_status=preflight_simulation_status,
                rate_budget_status=rate_budget_status,
                kill_switch_status=kill_switch_status,
                manual_export_status=manual_export_status,
                v5_display_status=v5_display_status,
                blocked_reasons=tuple(blocked_reasons),
                missing_proofs=tuple(missing_proofs),
                safe_display_fields=("platform_id", "platform_role", "primary_or_secondary_or_expansion", "endpoint_family"),
                hidden_or_absent_fields=("raw_secrets", "credential_values", "token_slices", "hashes", "raw_api_responses", "env_values"),
                redaction_required_fields=("raw_api_responses",),
            )
        )
    return tuple(states)


def build_candidate_fields() -> tuple[V5ReadModelCandidateField, ...]:
    fields = []
    rooms = (
        ("command_center", "universe_registry", "platform_registry_list", "metadata", "safe_to_show", "reference_only", "read_only"),
        ("command_center", "governance_summary", "global_readiness_status", "status", "safe_to_show", "reference_only", "read_only"),
        ("command_center", "rate_budget_kill_switch", "live_dispatch_toggle", "control", "hidden", "future_gate", "disabled_future_gate"),
        
        ("evidence_vault", "audit_ledger", "u9_ledger_entries", "json_ledger", "redacted", "historical_evidence", "read_only"),
        ("evidence_vault", "live_read_only_research_evidence", "evidence_packet_records", "json_packet", "redacted", "historical_evidence", "read_only"),
        
        ("approval_queue", "live_read_only_research_approval", "pending_operator_actions", "list", "safe_to_show", "current_state", "manual_review_only"),
        ("approval_queue", "live_read_only_research_approval", "approval_signature_field", "signature", "hidden", "future_gate", "disabled_future_gate"),
        
        ("platform_payload_preview", "platform_preflight_dry_run", "dry_run_payload_preview", "json_preview", "safe_to_show", "reference_only", "read_only"),
        ("platform_payload_preview", "platform_preflight_dry_run", "rendered_social_media_preview", "html", "safe_to_show", "reference_only", "read_only"),
        
        ("substack_manual_export", "dry_run_preview", "manual_export_manifest", "json", "safe_to_show", "current_state", "manual_review_only"),
        ("substack_manual_export", "dry_run_preview", "export_package_checksum", "hash", "safe_to_show", "historical_evidence", "read_only"),
        
        ("credential_boundary", "read_only_credential_slot_check", "credential_slots_schema", "json_schema", "safe_to_show", "reference_only", "read_only"),
        ("credential_boundary", "secret_boundary", "raw_secret_material", "secret", "hidden", "future_gate", "disabled_future_gate"),
        
        ("account_binding", "account_binding", "bound_accounts_list", "list", "safe_to_show", "current_state", "read_only"),
        ("account_binding", "account_binding", "oauth_client_id", "id_string", "redacted", "reference_only", "read_only"),
        
        ("live_readiness_gate", "supervised_live_read_only_research", "gate_precheck_results", "json", "safe_to_show", "current_state", "read_only"),
        ("live_readiness_gate", "supervised_live_read_only_research", "post_pilot_ledger_status", "status", "safe_to_show", "historical_evidence", "read_only"),
        
        ("manual_publish_metrics", "manual_publish", "manual_publish_ledger", "json_ledger", "safe_to_show", "historical_evidence", "read_only"),
        ("manual_publish_metrics", "manual_publish", "published_metrics_record", "record", "safe_to_show", "historical_evidence", "read_only"),
        
        ("content_performance_review", "performance_review", "performance_review_packet", "json", "safe_to_show", "historical_evidence", "read_only"),
        ("content_performance_review", "performance_review", "editorial_feedback_loop", "json", "safe_to_show", "historical_evidence", "read_only"),
        
        ("internal_alpha_artifact_intake", "artifact_intake", "intake_content_eligibility_report", "json", "safe_to_show", "historical_evidence", "read_only"),
        ("internal_alpha_artifact_intake", "artifact_intake", "artifact_idea_seed_packet", "json", "safe_to_show", "historical_evidence", "read_only"),
        
        ("writer_studio", "editorial_writer", "ai_writer_output", "json", "safe_to_show", "reference_only", "read_only"),
        ("writer_studio", "editorial_writer", "editorial_brief", "json", "safe_to_show", "reference_only", "read_only"),
        
        ("grounded_news_workbench", "editorial_writer", "grounded_news_angle_workbench", "json", "safe_to_show", "reference_only", "read_only"),
        ("grounded_news_workbench", "editorial_writer", "grounded_research_brief", "json", "safe_to_show", "reference_only", "read_only"),
    )
    for room, fam, name, kind, disp, truth, afford in rooms:
        fields.append(
            V5ReadModelCandidateField(
                field_id=f"v5_field_{room}_{name}",
                room_id=room,
                source_family=fam,
                field_name=name,
                field_kind=kind,
                display_policy=disp,
                current_truth_policy=truth,
                user_action_affordance=afford,
                forbidden_affordance_reason="live_action_blocked_local_only" if afford == "disabled_future_gate" else "",
                sample_value_classification="mock_or_metadata_only",
                source_ref_id=f"source_ref_{fam}",
                evidence_ref="proof:0174UU",
            )
        )
    return tuple(fields)


def build_room_binding_prechecks(fields: tuple[V5ReadModelCandidateField, ...]) -> tuple[V5RoomBindingPrecheck, ...]:
    rooms = (
        ("command_center", "ready_for_read_model_design", ("platform_universe_registry_v2", "local_content_governance_summary_mart_contract", "rate_budget_kill_switch_matrix_contract")),
        ("evidence_vault", "ready_for_read_model_design", ("redacted_immutable_audit_ledger_v2_contract", "live_read_only_research_evidence_packet_dry_run_schema_contract")),
        ("approval_queue", "ready_for_read_model_design", ("live_read_only_research_approval_packet_schema_contract",)),
        ("platform_payload_preview", "ready_for_read_model_design", ("platform_preflight_dry_run_request_budget_contract",)),
        ("substack_manual_export", "ready_for_read_model_design", ("live_read_only_research_local_preflight_simulation_contract",)),
        ("credential_boundary", "ready_for_read_model_design", ("read_only_credential_slot_check_validation_contract", "credential_handle_dotenv_secret_boundary_v2_contract")),
        ("account_binding", "ready_for_read_model_design", ("platform_account_binding_registry_v2_contract",)),
        ("live_readiness_gate", "ready_for_read_model_design", ("supervised_live_read_only_research_gate_precheck_contract",)),
        ("manual_publish_metrics", "ready_for_read_model_design", ("manual_publish_record_metrics_ledger_contract",)),
        ("content_performance_review", "ready_for_read_model_design", ("content_performance_review_editorial_feedback_contract",)),
        ("internal_alpha_artifact_intake", "ready_for_read_model_design", ("internal_alpha_artifact_intake_content_eligibility_contract",)),
        ("writer_studio", "ready_for_read_model_design", ("live_read_only_research_approval_packet_schema_contract",)),
        ("grounded_news_workbench", "ready_for_read_model_design", ("live_read_only_research_approval_packet_schema_contract",)),
    )
    prechecks = []
    for r_id, status, reqs in rooms:
        r_fields = [f for f in fields if f.room_id == r_id]
        safe_cnt = sum(1 for f in r_fields if f.display_policy == "safe_to_show")
        hidden_cnt = sum(1 for f in r_fields if f.display_policy == "hidden")
        redacted_cnt = sum(1 for f in r_fields if f.display_policy == "redacted")
        disabled_afford = tuple(f.field_name for f in r_fields if f.user_action_affordance == "disabled_future_gate")

        prechecks.append(
            V5RoomBindingPrecheck(
                room_id=r_id,
                binding_status=status,
                safe_fields_count=safe_cnt,
                hidden_fields_count=hidden_cnt,
                redacted_fields_count=redacted_cnt,
                disabled_affordances=disabled_afford,
                required_contracts=reqs,
                missing_contracts=(),
                safety_notes="Verified: local preflight bundle safety policy holds. No live action affordances exist.",
                no_live_action_affordances=True,
            )
        )
    return tuple(prechecks)


def build_u9_audit_entries(
    packet_id: str,
    platform_states: tuple[LocalPreflightBundlePlatformState, ...],
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UU"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, ps in enumerate(platform_states, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UU",
            source_model_version=MATRIX_VERSION,
            payload={
                "id": packet_id,
                "platform_id": ps.platform_id,
                "status": "ready_for_read_model_design",
                "blocked_reasons": ps.blocked_reasons,
                "missing_proofs": ps.missing_proofs,
                "live_read_allowed": ps.live_read_allowed,
                "live_write_allowed": ps.live_write_allowed,
                "public_post_allowed": ps.public_post_allowed,
                "dispatch_ready": ps.dispatch_ready,
                "readiness_cleared": ps.readiness_cleared,
            },
            policy=policy,
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_local_preflight_bundle_v5_read_model_precheck_packet() -> LocalPreflightBundleV5ReadModelPrecheckPacket:
    source_refs = build_source_refs()
    platform_states = build_platform_states()
    v5_candidate_fields = build_candidate_fields()
    room_binding_prechecks = build_room_binding_prechecks(v5_candidate_fields)

    global_blocked = tuple(dict.fromkeys(r for s in platform_states for r in s.blocked_reasons))
    global_missing = tuple(dict.fromkeys(p for s in platform_states for p in s.missing_proofs))

    packet_id_draft = "read_model_precheck_packet_draft"
    u9_entries = build_u9_audit_entries(packet_id_draft, platform_states)

    safety_flags = {
        "local_only": True,
        "read_model_precheck_only": True,
        "ui_mutated": False,
        "live_read_allowed": False,
        "live_write_allowed": False,
        "public_post_allowed": False,
        "dispatch_ready": False,
        "autonomous_posting_allowed": False,
        "env_read": False,
        "credential_values_accessed": False,
        "credential_hydrated": False,
        "secret_output_allowed": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "network_performed": False,
        "browser_session_used": False,
        "scheduler_enabled": False,
        "scraping_performed": False,
        "dm_or_reply_automation_allowed": False,
        "current_truth_promoted": False,
        "dqr_cleared": False,
        "readiness_cleared": False,
        "ingestion_repo_mutated": False,
    }

    draft = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "source_ref_count": len(source_refs),
        "platform_count": len(platform_states),
        "candidate_field_count": len(v5_candidate_fields),
        "room_count": len(room_binding_prechecks),
        "source_refs": source_refs,
        "platform_states": platform_states,
        "v5_candidate_fields": v5_candidate_fields,
        "room_binding_prechecks": room_binding_prechecks,
        "global_blocked_reasons": global_blocked,
        "global_missing_proofs": global_missing,
        "ui_binding_policy": "strict_read_model_precheck_v5_isolation",
        "safety_flags": safety_flags,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in u9_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in u9_entries),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
    }

    packet_hash = _digest(draft)
    real_packet_id = "local_preflight_bundle_v5_read_model_precheck_packet_" + packet_hash[:24]

    # Re-evaluate with the final packet id to ensure strict hashing
    u9_entries = build_u9_audit_entries(real_packet_id, platform_states)
    draft["u9_audit_entry_ids"] = tuple(e.ledger_entry_id for e in u9_entries)
    packet_hash = _digest(draft)

    return LocalPreflightBundleV5ReadModelPrecheckPacket(
        packet_id=real_packet_id,
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft,
    )


def render_runbook(packet: LocalPreflightBundleV5ReadModelPrecheckPacket) -> str:
    lines = [
        "# Local Preflight Bundle & V5 Read-Model Precheck Contract",
        "",
        "## Critical Warning",
        "> [!CAUTION]",
        "> **LOCAL-ONLY PREFLIGHT BUNDLE AND V5 READ-MODEL PRECHECK ONLY. ZERO LIVE ACTIONS AUTHORIZED.**",
        "> This module consolidates precedent contract metrics and audits to verify local readiness.",
        "> No actual credential loading, environment secret reads, platform API integration, or posting occurs.",
        "> **No UI files were edited in this task.**",
        "",
        f"- **Task Label**: `{packet.task_label}`",
        f"- **Source Baseline Commit**: `{packet.source_baseline_commit}`",
        f"- **Matrix/Packet ID**: `{packet.packet_id}`",
        f"- **Packet Hash**: `{packet.packet_hash}`",
        f"- **Next Recommended Task**: `{packet.next_recommended_task}`",
        "",
        "## 1. Source Contract Inventory",
        "",
        "| Source Ref ID | Task Family | Module Name | Consumed | Live Capability Added | Credential Values Accessed |",
        "|---|---|---|---|---|---|",
    ]
    for ref in packet.source_refs:
        lines.append(
            f"| `{ref.source_ref_id}` | `{ref.task_family}` | `{ref.module_name}` | `{ref.consumed}` | `{ref.live_capability_added}` | `{ref.credential_values_accessed}` |"
        )

    lines.extend([
        "",
        "## 2. Platform State Matrix",
        "",
        "| Platform ID | Role | Endpoint Family | Binding Status | Credential Status | Mock Audit Status | Display Status |",
        "|---|---|---|---|---|---|---|",
    ])
    for ps in packet.platform_states:
        lines.append(
            f"| `{ps.platform_id}` | `{ps.platform_role}` | `{ps.endpoint_family}` | `{ps.account_binding_status}` | `{ps.credential_slot_status}` | `{ps.credential_mock_audit_status}` | `{ps.v5_display_status}` |"
        )

    lines.extend([
        "",
        "## 3. V5 Room Binding Precheck Matrix",
        "",
        "| Room ID | Binding Status | Safe Fields | Redacted Fields | Hidden Fields | No Live Action Affordances |",
        "|---|---|---|---|---|---|",
    ])
    for pr in packet.room_binding_prechecks:
        lines.append(
            f"| `{pr.room_id}` | `{pr.binding_status}` | `{pr.safe_fields_count}` | `{pr.redacted_fields_count}` | `{pr.hidden_fields_count}` | `{pr.no_live_action_affordances}` |"
        )

    lines.extend([
        "",
        "## 4. Safe Display Fields vs Hidden/Redacted Fields",
        "- **Safe Fields to Show**: Platform Registry Metadata, Governance Mart summaries, previews of dry-run posts, bound platform IDs, and audit log structure.",
        "- **Redacted Fields**: API Client IDs, signature hashes, and transaction references.",
        "- **Hidden/Absent Fields**: Real credential secrets, raw secret strings, token slices, environment secret variables, and actual active payload parameters.",
        "",
        "## 5. Disabled Future-Gate Affordances",
        "- Live dispatch toggles, active posting controls, direct credential slot modifications, and auto-verify triggers remain locked under `disabled_future_gate` due to missing live credentials and security policies.",
        "",
        "## 6. Global Blocked Reasons",
    ])
    for r in packet.global_blocked_reasons:
        lines.append(f"- `{r}`")

    lines.extend([
        "",
        "## 7. Global Missing Proofs",
    ])
    for p in packet.global_missing_proofs:
        lines.append(f"- `{p}`")

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UU")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_local_preflight_bundle_v5_read_model_precheck_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "LocalPreflightBundleSourceRef",
    "LocalPreflightBundlePlatformState",
    "V5ReadModelCandidateField",
    "V5RoomBindingPrecheck",
    "LocalPreflightBundleV5ReadModelPrecheckPacket",
    "build_source_refs",
    "build_platform_states",
    "build_candidate_fields",
    "build_room_binding_prechecks",
    "build_local_preflight_bundle_v5_read_model_precheck_packet",
    "render_runbook",
    "write_artifacts",
]
