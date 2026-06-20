"""Live read-only research credential slot check validation contract for ContentOps 0174US.

Deterministic local-only validation contract. No live/API/provider/network/
env/credential/browser/scheduler/scraping/DM/reply automation or UI behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import platform_universe_registry_v2 as universe
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit
from live_contentops import live_read_only_research_approval_packet_schema_contract as approval
from live_contentops import live_read_only_research_evidence_packet_dry_run_schema_contract as evidence
from live_contentops import live_read_only_research_runbook_approval_gate_dry_run_contract as runbook
from live_contentops import live_read_only_research_local_preflight_simulation_contract as simulation
from live_contentops import credential_handle_dotenv_secret_boundary_v2_contract as boundary
from live_contentops import platform_account_binding_registry_v2_contract as binding

TASK_LABEL = "TASK_CONTENTOPS_0174US_READ_ONLY_CREDENTIALS_SLOT_CHECK_VALIDATION_V0"
MATRIX_VERSION = "0174US_READ_ONLY_CREDENTIALS_SLOT_CHECK_VALIDATION_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "5ff00dbfa3f9fac25f7b1afb20e8fa8798143fa8"
DOC_REL_DIR = Path("docs") / "automation" / "0174US"
PACKET_FILENAME = "read_only_credential_slot_check_validation_contract_packet.json"
RUNBOOK_FILENAME = "read_only_credential_slot_check_validation_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "read_only_credential_slot_check_validation_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UT_READ_ONLY_CREDENTIALS_SLOT_INSPECTION_MOCK_AUDIT_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class ReadOnlyCredentialSlotSpec:
    platform_id: str
    platform_role: str
    endpoint_family: str
    slot_policy: str
    required_slot_names: tuple[str, ...]
    optional_slot_names: tuple[str, ...]
    slot_name_format_rules: tuple[str, ...]
    allowed_key_name_prefixes: tuple[str, ...]
    forbidden_key_name_patterns: tuple[str, ...]
    manual_only: bool
    credential_values_accessed: bool = False
    env_read: bool = False
    dotenv_loaded: bool = False
    secret_store_accessed: bool = False
    credential_hydrated: bool = False
    secret_value_serialized: bool = False
    secret_hash_displayed: bool = False
    token_prefix_displayed: bool = False
    token_suffix_displayed: bool = False
    redaction_required: bool = True
    redaction_policy_ref: str = "none"
    live_read_allowed: bool = False
    live_write_allowed: bool = False
    platform_api_called: bool = False
    provider_api_called: bool = False
    public_post_allowed: bool = False
    blocked_reasons: tuple[str, ...] = ()
    missing_proofs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReadOnlyCredentialSlotCheckScenario:
    scenario_id: str
    scenario_name: str
    slot_check_status: str
    slot_check_strength: str
    credential_presence_classification: str
    redaction_result: str
    failure_or_abort_classification: str
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]


@dataclass(frozen=True)
class ReadOnlyCredentialSlotValidationDecision:
    decision_id: str
    platform_id: str
    scenario_id: str
    validation_status: str
    validation_strength: str
    precheck_status: str
    slot_policy_status: str
    redaction_policy_status: str
    secret_output_status: str
    live_read_allowed: bool
    live_write_allowed: bool
    env_read_allowed: bool
    credential_hydrated: bool
    platform_api_called: bool
    provider_api_called: bool
    public_post_allowed: bool
    scheduler_enabled: bool
    browser_session_used: bool
    scraping_performed: bool
    dm_or_reply_automation_allowed: bool
    readiness_cleared: bool
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    decision_hash: str


@dataclass(frozen=True)
class ReadOnlyCredentialSlotCheckPacket:
    packet_id: str
    packet_hash: str
    packet_hash_algorithm: str
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    platform_count: int
    slot_spec_count: int
    scenario_count: int
    decision_count: int
    credential_slot_specs: tuple[ReadOnlyCredentialSlotSpec, ...]
    slot_check_scenarios: tuple[ReadOnlyCredentialSlotCheckScenario, ...]
    slot_validation_decisions: tuple[ReadOnlyCredentialSlotValidationDecision, ...]
    required_slot_summary: dict[str, tuple[str, ...]]
    optional_slot_summary: dict[str, tuple[str, ...]]
    slot_policy_summary: dict[str, str]
    credential_presence_summary: dict[str, str]
    redaction_policy_summary: dict[str, str]
    platform_gate_summary: dict[str, str]
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]
    safety_flags: dict[str, bool]
    u9_audit_entry_ids: tuple[str, ...]
    u9_audit_entry_families: tuple[str, ...]
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


def build_slot_specs() -> tuple[ReadOnlyCredentialSlotSpec, ...]:
    specs = []
    specs_data = [
        ("x", "research_operator", "x_api_read_only_symbolic", "key_names_only", ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"), (), ("UPPER_SNAKE_CASE",), ("X_",), ("*PASSWORD*", "*PASSWD*"), False),
        ("telegram_remote_operator", "remote_operator", "telegram_bot_getupdates_or_webhook_symbolic", "key_names_only", ("TELEGRAM_BOT_TOKEN", "TELEGRAM_OPERATOR_CHAT_ID"), (), ("UPPER_SNAKE_CASE",), ("TELEGRAM_",), ("*PASSWORD*", "*PASSWD*"), False),
        ("telegram_channel_destination", "channel_destination", "telegram_bot_getchat_symbolic", "key_names_only", ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID"), (), ("UPPER_SNAKE_CASE",), ("TELEGRAM_",), ("*PASSWORD*", "*PASSWD*"), False),
        ("substack_newsletter", "newsletter_destination", "manual_export_no_api", "manual_no_credential", (), (), (), (), (), True),
        ("linkedin", "organization_research", "linkedin_api_read_only_symbolic", "key_names_only", ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"), (), ("UPPER_SNAKE_CASE",), ("LINKEDIN_",), ("*PASSWORD*", "*PASSWD*"), False),
        ("threads", "meta_threads_research", "meta_threads_read_only_symbolic", "key_names_only", ("THREADS_ACCESS_TOKEN",), (), ("UPPER_SNAKE_CASE",), ("THREADS_",), ("*PASSWORD*", "*PASSWD*"), False),
        ("instagram", "meta_instagram_research", "meta_instagram_read_only_symbolic", "key_names_only", ("INSTAGRAM_ACCESS_TOKEN",), (), ("UPPER_SNAKE_CASE",), ("INSTAGRAM_",), ("*PASSWORD*", "*PASSWD*"), False),
        ("facebook_page", "meta_facebook_page_research", "meta_facebook_page_read_only_symbolic", "key_names_only", ("FACEBOOK_PAGE_ACCESS_TOKEN",), (), ("UPPER_SNAKE_CASE",), ("FACEBOOK_",), ("*PASSWORD*", "*PASSWD*"), False),
        ("tiktok", "tiktok_research", "tiktok_read_only_symbolic", "key_names_only", ("TIKTOK_CREATOR_ACCESS_TOKEN",), (), ("UPPER_SNAKE_CASE",), ("TIKTOK_",), ("*PASSWORD*", "*PASSWD*"), False),
        ("youtube", "youtube_research", "youtube_data_api_read_only_symbolic", "key_names_only", ("YOUTUBE_API_KEY", "YOUTUBE_OAUTH_CLIENT_ID"), (), ("UPPER_SNAKE_CASE",), ("YOUTUBE_",), ("*PASSWORD*", "*PASSWD*"), False),
    ]

    for p_id, role, family, policy, req, opt, rules, prefixes, forbidden, manual in specs_data:
        specs.append(
            ReadOnlyCredentialSlotSpec(
                platform_id=p_id,
                platform_role=role,
                endpoint_family=family,
                slot_policy=policy,
                required_slot_names=req,
                optional_slot_names=opt,
                slot_name_format_rules=rules,
                allowed_key_name_prefixes=prefixes,
                forbidden_key_name_patterns=forbidden,
                manual_only=manual,
                redaction_required=not manual,
                redaction_policy_ref="policy:0174U9" if not manual else "none",
            )
        )
    return tuple(specs)


def build_scenarios() -> tuple[ReadOnlyCredentialSlotCheckScenario, ...]:
    return (
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="declared_slots_schema_only",
            scenario_name="Declared credential slot schema check only (no credentials present)",
            slot_check_status="not_ready",
            slot_check_strength="schema_declared_only",
            credential_presence_classification="absent",
            redaction_result="pending_readiness",
            failure_or_abort_classification="none",
            blocked_reasons=("credential_slot_schema_only",),
            missing_proofs=("credential_slot_schema_only",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="required_slot_missing",
            scenario_name="Failure check when required slot name is missing from dotenv template",
            slot_check_status="blocked",
            slot_check_strength="missing_required_slot",
            credential_presence_classification="absent",
            redaction_result="none",
            failure_or_abort_classification="missing_required_slot_error",
            blocked_reasons=("required_slot_name_missing",),
            missing_proofs=("required_slot_name_missing",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="forbidden_slot_name_pattern",
            scenario_name="Failure check when slot name matches forbidden pattern",
            slot_check_status="blocked",
            slot_check_strength="invalid_slot_name",
            credential_presence_classification="absent",
            redaction_result="none",
            failure_or_abort_classification="forbidden_slot_pattern_error",
            blocked_reasons=("forbidden_slot_name_pattern",),
            missing_proofs=("forbidden_slot_name_pattern",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="credential_value_present_attempt_blocked",
            scenario_name="Assertion check when a real secret value load is attempted",
            slot_check_status="blocked",
            slot_check_strength="secret_value_present_blocked",
            credential_presence_classification="blocked",
            redaction_result="none",
            failure_or_abort_classification="credential_value_attempt_error",
            blocked_reasons=("credential_value_read_blocked",),
            missing_proofs=("credential_value_read_blocked",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="env_read_attempt_blocked",
            scenario_name="Assertion check that environment read fails closed",
            slot_check_status="blocked",
            slot_check_strength="env_read_blocked",
            credential_presence_classification="blocked",
            redaction_result="none",
            failure_or_abort_classification="env_read_attempt_error",
            blocked_reasons=("env_read_blocked",),
            missing_proofs=("env_read_blocked",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="dotenv_load_attempt_blocked",
            scenario_name="Assertion check that dotenv library parse is blocked",
            slot_check_status="blocked",
            slot_check_strength="dotenv_load_blocked",
            credential_presence_classification="blocked",
            redaction_result="none",
            failure_or_abort_classification="dotenv_load_attempt_error",
            blocked_reasons=("dotenv_load_blocked",),
            missing_proofs=("dotenv_load_blocked",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="secret_hash_display_attempt_blocked",
            scenario_name="Prohibit displaying hashed outputs of credential values",
            slot_check_status="blocked",
            slot_check_strength="hash_display_blocked",
            credential_presence_classification="blocked",
            redaction_result="none",
            failure_or_abort_classification="secret_hash_attempt_error",
            blocked_reasons=("secret_hash_display_blocked",),
            missing_proofs=("secret_hash_display_blocked",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="token_prefix_suffix_display_attempt_blocked",
            scenario_name="Prohibit displaying partial prefix/suffix token characters",
            slot_check_status="blocked",
            slot_check_strength="prefix_suffix_display_blocked",
            credential_presence_classification="blocked",
            redaction_result="none",
            failure_or_abort_classification="prefix_suffix_attempt_error",
            blocked_reasons=("prefix_suffix_display_blocked",),
            missing_proofs=("prefix_suffix_display_blocked",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="redaction_policy_missing",
            scenario_name="Failure check when redaction contract references are missing",
            slot_check_status="blocked",
            slot_check_strength="redaction_policy_missing",
            credential_presence_classification="absent",
            redaction_result="none",
            failure_or_abort_classification="redaction_policy_missing_error",
            blocked_reasons=("redaction_policy_missing",),
            missing_proofs=("redaction_policy_missing",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="operator_approval_missing",
            scenario_name="Failure check when operator approval signature is absent",
            slot_check_status="blocked",
            slot_check_strength="operator_approval_missing",
            credential_presence_classification="absent",
            redaction_result="none",
            failure_or_abort_classification="operator_approval_missing_error",
            blocked_reasons=("operator_approval_missing",),
            missing_proofs=("operator_approval_missing",),
        ),
        ReadOnlyCredentialSlotCheckScenario(
            scenario_id="platform_specific_proof_missing",
            scenario_name="Failure check when platform specific review proofs are missing",
            slot_check_status="blocked",
            slot_check_strength="proof_missing",
            credential_presence_classification="absent",
            redaction_result="none",
            failure_or_abort_classification="platform_proof_missing_error",
            blocked_reasons=("platform_proof_missing",),
            missing_proofs=("platform_proof_missing",),
        ),
    )


def compile_slot_decision(
    platform_id: str,
    scenario_id: str,
    sim_packet: simulation.LocalPreflightSimulationPacket | None = None,
) -> ReadOnlyCredentialSlotValidationDecision:
    if platform_id not in PLATFORM_IDS:
        raise ValueError(f"invalid_platform_id: {platform_id}")

    sim = sim_packet or simulation.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    sim_dec = next((d for d in sim.simulation_decisions if d.platform_id == platform_id and d.scenario_id == "happy_path_symbolic_preflight_still_blocked"), None)
    sc = next((s for s in build_scenarios() if s.scenario_id == scenario_id), None)

    if not sim_dec or not sc:
        raise ValueError(f"missing_precedent_data_for_platform: {platform_id} {scenario_id}")

    is_manual = platform_id == "substack_newsletter"

    blocked_reasons = list(sim_dec.blocked_reasons)
    missing_proofs = list(sim_dec.missing_proofs)

    # validation status
    if is_manual:
        validation_status = "manual_only"
        validation_strength = "manual_policy_only"
    else:
        validation_status = "blocked" if (sim_dec.validation_status == "blocked" or sc.scenario_id != "declared_slots_schema_only") else "not_ready"
        validation_strength = sim_dec.validation_strength

    # override scenario specific reasons
    if sc.scenario_id == "declared_slots_schema_only":
        if "credential_slot_schema_only" not in blocked_reasons:
            blocked_reasons.append("credential_slot_schema_only")
        if "credential_slot_schema_only" not in missing_proofs:
            missing_proofs.append("credential_slot_schema_only")
    elif sc.scenario_id == "required_slot_missing":
        blocked_reasons.append("required_slot_name_missing")
        missing_proofs.append("required_slot_name_missing")
    elif sc.scenario_id == "forbidden_slot_name_pattern":
        blocked_reasons.append("forbidden_slot_name_pattern")
        missing_proofs.append("forbidden_slot_name_pattern")
    elif sc.scenario_id == "credential_value_present_attempt_blocked":
        blocked_reasons.append("credential_value_read_blocked")
        missing_proofs.append("credential_value_read_blocked")
    elif sc.scenario_id == "env_read_attempt_blocked":
        blocked_reasons.append("env_read_blocked")
        missing_proofs.append("env_read_blocked")
    elif sc.scenario_id == "dotenv_load_attempt_blocked":
        blocked_reasons.append("dotenv_load_blocked")
        missing_proofs.append("dotenv_load_blocked")
    elif sc.scenario_id == "secret_hash_display_attempt_blocked":
        blocked_reasons.append("secret_hash_display_blocked")
        missing_proofs.append("secret_hash_display_blocked")
    elif sc.scenario_id == "token_prefix_suffix_display_attempt_blocked":
        blocked_reasons.append("prefix_suffix_display_blocked")
        missing_proofs.append("prefix_suffix_display_blocked")
    elif sc.scenario_id == "redaction_policy_missing":
        blocked_reasons.append("redaction_policy_missing")
        missing_proofs.append("redaction_policy_missing")
    elif sc.scenario_id == "operator_approval_missing":
        blocked_reasons.append("operator_approval_disabled")
        missing_proofs.append("operator_approval_disabled")

    # Platform specific requirements & blockers
    if platform_id == "x":
        for r in ("x_app_access_gap", "spend_gate_unresolved", "rate_budget_gap", "read_only_endpoint_proof_gap"):
            if r not in blocked_reasons:
                blocked_reasons.append(r)
            if r not in missing_proofs:
                missing_proofs.append(r)
    elif platform_id == "telegram_remote_operator":
        for r in ("no_arbitrary_dm_allowed", "operator_inbox_proof_required"):
            if r not in blocked_reasons:
                blocked_reasons.append(r)
            if r not in missing_proofs:
                missing_proofs.append(r)
    elif platform_id == "telegram_channel_destination":
        for r in ("channel_admin_proof_required", "bot_permission_gap", "channel_state_symbolic_only"):
            if r not in blocked_reasons:
                blocked_reasons.append(r)
            if r not in missing_proofs:
                missing_proofs.append(r)
    elif platform_id == "substack_newsletter":
        if "manual_export_only" not in blocked_reasons:
            blocked_reasons.append("manual_export_only")
        if "manual_export_only" not in missing_proofs:
            missing_proofs.append("manual_export_only")
    elif platform_id == "linkedin":
        for r in ("linkedin_organization_page_proof_missing",):
            if r not in blocked_reasons:
                blocked_reasons.append(r)
            if r not in missing_proofs:
                missing_proofs.append(r)
    elif platform_id in ("threads", "instagram", "facebook_page"):
        for r in ("meta_app_review_closed", "meta_app_account_proof_required"):
            if r not in blocked_reasons:
                blocked_reasons.append(r)
            if r not in missing_proofs:
                missing_proofs.append(r)
    elif platform_id == "tiktok":
        for r in ("tiktok_app_audit_closed", "creator_account_proof_required", "video_publish_proof_required"):
            if r not in blocked_reasons:
                blocked_reasons.append(r)
            if r not in missing_proofs:
                missing_proofs.append(r)
    elif platform_id == "youtube":
        for r in ("youtube_quota_unresolved", "youtube_oauth_flow_closed", "upload_proof_required"):
            if r not in blocked_reasons:
                blocked_reasons.append(r)
            if r not in missing_proofs:
                missing_proofs.append(r)

    draft = {
        "platform_id": platform_id,
        "scenario_id": scenario_id,
        "validation_status": validation_status,
        "validation_strength": validation_strength,
        "precheck_status": sim_dec.precheck_status,
        "slot_policy_status": "manual_no_credential" if is_manual else "key_names_only",
        "redaction_policy_status": sim_dec.redaction_policy_status,
        "secret_output_status": "prohibited",
        "live_read_allowed": False,
        "live_write_allowed": False,
        "env_read_allowed": False,
        "credential_hydrated": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "public_post_allowed": False,
        "scheduler_enabled": False,
        "browser_session_used": False,
        "scraping_performed": False,
        "dm_or_reply_automation_allowed": False,
        "readiness_cleared": False,
        "blocked_reasons": tuple(dict.fromkeys(blocked_reasons)),
        "missing_proofs": tuple(dict.fromkeys(missing_proofs)),
        "evidence_refs": sim_dec.evidence_refs,
    }

    h_basis = {str(k): _asdict(v) for k, v in draft.items()}
    h = sha256(json.dumps(h_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    return ReadOnlyCredentialSlotValidationDecision(
        decision_id=f"slot_decision_{platform_id}_{scenario_id[:12]}_" + h[:8],
        decision_hash=h,
        **draft
    )


def build_u9_audit_entries(
    decisions: tuple[ReadOnlyCredentialSlotValidationDecision, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174US"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, dec in enumerate(decisions, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174US",
            source_model_version=MATRIX_VERSION,
            payload={
                "id": dec.decision_id,
                "platform_id": dec.platform_id,
                "scenario_id": dec.scenario_id,
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


def build_supervised_read_only_credential_slot_check_packet(
    sim_packet: simulation.LocalPreflightSimulationPacket | None = None
) -> ReadOnlyCredentialSlotCheckPacket:
    sim = sim_packet or simulation.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    bp = boundary.build_credential_boundary_packet()
    ab = binding.build_platform_account_binding_registry_packet()

    slot_specs = build_slot_specs()
    scenarios = build_scenarios()

    decisions = []
    for pid in PLATFORM_IDS:
        for sc in scenarios:
            decisions.append(compile_slot_decision(pid, sc.scenario_id, sim))
    decisions = tuple(decisions)

    required_slot_summary = {s.platform_id: s.required_slot_names for s in slot_specs}
    optional_slot_summary = {s.platform_id: s.optional_slot_names for s in slot_specs}
    slot_policy_summary = {s.platform_id: s.slot_policy for s in slot_specs}
    credential_presence_summary = {s.scenario_id: s.credential_presence_classification for s in scenarios}
    redaction_policy_summary = {t.platform_id: t.redaction_policy_ref for t in ep.templates}
    platform_gate_summary = {s.platform_id: "blocked" if s.platform_id != "substack_newsletter" else "manual_only" for s in slot_specs}

    global_blocked_reasons = tuple(dict.fromkeys(r for d in decisions for r in d.blocked_reasons))
    global_missing_proofs = tuple(dict.fromkeys(p for d in decisions for p in d.missing_proofs))

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
        "all_credential_values_blocked": True,
        "all_env_reads_blocked": True,
        "all_dotenv_loads_blocked": True,
        "all_secret_outputs_blocked": True,
        "all_live_actions_blocked": True,
    }

    draft = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "platform_count": len(PLATFORM_IDS),
        "slot_spec_count": len(slot_specs),
        "scenario_count": len(scenarios),
        "decision_count": len(decisions),
        "credential_slot_specs": slot_specs,
        "slot_check_scenarios": scenarios,
        "slot_validation_decisions": decisions,
        "required_slot_summary": required_slot_summary,
        "optional_slot_summary": optional_slot_summary,
        "slot_policy_summary": slot_policy_summary,
        "credential_presence_summary": credential_presence_summary,
        "redaction_policy_summary": redaction_policy_summary,
        "platform_gate_summary": platform_gate_summary,
        "blocked_reasons": global_blocked_reasons,
        "missing_proofs": global_missing_proofs,
        "safety_flags": safety_flags,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "next_required_gate": NEXT_REQUIRED_GATE,
    }

    packet_hash = _digest(draft)
    return ReadOnlyCredentialSlotCheckPacket(
        packet_id="read_only_credential_slot_check_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def render_runbook(packet: ReadOnlyCredentialSlotCheckPacket) -> str:
    lines = [
        "# Read-Only Credentials Slot Check Validation Contract V0",
        "",
        "## Critical Security Warning",
        "> [!CAUTION]",
        "> **ZERO SECRET MATERIAL OR REAL VALUES ARE LOADED BY THIS SYSTEM.**",
        "> This contract operates purely on synthetic slot schema names and enforces strict key-name policies.",
        "> No dotenv load, env read, credential hydration, or secret display is permitted.",
        "",
        f"- **Task Label**: `{packet.task_label}`",
        f"- **Source Baseline Commit**: `{packet.source_baseline_commit}`",
        f"- **Matrix/Packet ID**: `{packet.packet_id}`",
        f"- **Packet Hash**: `{packet.packet_hash}`",
        f"- **Next Required Gate**: `{packet.next_required_gate}`",
        "",
        "## 1. Platform Credential Slot Spec Matrix",
        "",
        "| Platform ID | Platform Role | Endpoint Family | Slot Policy | Required Slot Names | Redaction Required |",
        "|---|---|---|---|---|---|",
    ]
    for s in packet.credential_slot_specs:
        req_slots = ", ".join(f"`{name}`" for name in s.required_slot_names) if s.required_slot_names else "*None (Manual)*"
        lines.append(
            f"| `{s.platform_id}` | `{s.platform_role}` | `{s.endpoint_family}` | `{s.slot_policy}` | {req_slots} | `{s.redaction_required}` |"
        )

    lines.extend([
        "",
        "## 2. Slot-Name-Only Policy Checklist",
        "- [ ] Ensure env configuration keys are validated for uppercase snake case structure.",
        "- [ ] Ensure zero credentials values are ever loaded to environment memory.",
        "- [ ] Ensure secret hash display attempts and token slice extracts fail closed.",
        "",
        "## 3. Forbidden Secret-Output Checklist",
        "- [ ] Enforce that no log lines, terminal print statements, or debug structures output credentials.",
        "- [ ] Confirm that raw API responses are excluded from ledger payload storage.",
        "",
        "## 4. Redaction Proof Checklist",
        "- [ ] Redact all user operator identities under standard `policy:0174U9` redaction format.",
        "- [ ] Enforce `redaction_required=True` policy for all API-like platforms.",
        "",
        "## 5. Scenario Simulation Matrix",
        "",
        "| Scenario ID | Status | Presence Class | Abort Class |",
        "|---|---|---|---|",
    ])
    for sc in packet.slot_check_scenarios:
        lines.append(
            f"| `{sc.scenario_id}` | `{sc.slot_check_status}` | `{sc.credential_presence_classification}` | `{sc.failure_or_abort_classification}` |"
        )

    lines.extend([
        "",
        "## 6. Missing Proofs / Blocked Reasons by Platform",
        "",
    ])
    for s in packet.credential_slot_specs:
        lines.append(f"### Platform `{s.platform_id}`")
        lines.append(f"- **Simulated Endpoint Family**: `{s.endpoint_family}`")
        lines.append(f"- **Gate Status**: `{packet.platform_gate_summary[s.platform_id]}`")
        lines.append("")

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174US")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_supervised_read_only_credential_slot_check_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "ReadOnlyCredentialSlotSpec",
    "ReadOnlyCredentialSlotCheckScenario",
    "ReadOnlyCredentialSlotValidationDecision",
    "ReadOnlyCredentialSlotCheckPacket",
    "build_slot_specs",
    "build_scenarios",
    "compile_slot_decision",
    "build_supervised_read_only_credential_slot_check_packet",
    "render_runbook",
    "write_artifacts",
]
