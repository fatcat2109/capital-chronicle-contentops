"""Live read-only research local preflight simulation contract for ContentOps 0174UR.

Deterministic local-only preflight simulation contract. No live/API/provider/network/
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

TASK_LABEL = "TASK_CONTENTOPS_0174UR_LOCAL_PREFLIGHT_SIMULATION_OF_LIVE_READ_ADAPTERS_V0"
MATRIX_VERSION = "0174UR_LOCAL_PREFLIGHT_SIMULATION_OF_LIVE_READ_ADAPTERS_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "1a308bcb4151e754cd49bedf90d29c9ee73c17ab"
DOC_REL_DIR = Path("docs") / "automation" / "0174UR"
PACKET_FILENAME = "live_read_only_research_local_preflight_simulation_contract_packet.json"
RUNBOOK_FILENAME = "live_read_only_research_local_preflight_simulation_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "live_read_only_research_local_preflight_simulation_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174US_READ_ONLY_CREDENTIALS_SLOT_CHECK_VALIDATION_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class LocalPreflightSimulatedAdapterProfile:
    platform_id: str
    adapter_mode: str
    endpoint_family: str
    endpoint_allowlist_status: str
    request_budget_max: int
    timeout_seconds_max: int
    credential_policy: str
    credential_values_accessed: bool = False
    env_read: bool = False
    network_performed: bool = False
    platform_api_called: bool = False
    provider_api_called: bool = False
    browser_session_used: bool = False
    raw_response_stored: bool = False
    secret_output_allowed: bool = False
    response_body_storage_allowed: bool = False
    public_post_allowed: bool = False
    live_write_allowed: bool = False


@dataclass(frozen=True)
class LocalPreflightSimulationScenario:
    scenario_id: str
    scenario_name: str
    simulated_response_classification: str
    response_shape_classification: str
    failure_or_timeout_classification: str
    abort_policy_result: str
    redaction_result: str
    evidence_artifact_hash_required: bool
    raw_response_logged: bool = False
    raw_response_body: str = "absent"


@dataclass(frozen=True)
class LocalPreflightSimulationDecision:
    decision_id: str
    platform_id: str
    scenario_id: str
    validation_status: str
    validation_strength: str
    precheck_status: str
    endpoint_allowlist_status: str
    request_budget_status: str
    credential_policy_status: str
    redaction_policy_status: str
    raw_response_policy_status: str
    stop_condition_status: str
    kill_switch_status: str
    operator_approval_status: str
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
class LocalPreflightSimulationPacket:
    packet_id: str
    packet_hash: str
    packet_hash_algorithm: str
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    platform_count: int
    scenario_count: int
    decision_count: int
    simulated_adapter_profiles: tuple[LocalPreflightSimulatedAdapterProfile, ...]
    simulation_scenarios: tuple[LocalPreflightSimulationScenario, ...]
    simulation_decisions: tuple[LocalPreflightSimulationDecision, ...]
    endpoint_family_summary: dict[str, str]
    request_budget_summary: dict[str, int]
    timeout_policy_summary: dict[str, int]
    credential_slot_policy_summary: dict[str, str]
    redaction_policy_summary: dict[str, str]
    simulated_response_classification_summary: dict[str, str]
    failure_or_abort_summary: dict[str, str]
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


def build_adapter_profiles() -> tuple[LocalPreflightSimulatedAdapterProfile, ...]:
    profiles = []
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
        p = LocalPreflightSimulatedAdapterProfile(
            platform_id=platform_id,
            adapter_mode="simulated_only",
            endpoint_family=endpoint_family,
            endpoint_allowlist_status="symbolic" if not is_manual else "manual_no_api",
            request_budget_max=budget,
            timeout_seconds_max=30 if not is_manual else 0,
            credential_policy="key_names_only" if not is_manual else "manual_no_credential",
        )
        profiles.append(p)
    return tuple(profiles)


def build_scenarios() -> tuple[LocalPreflightSimulationScenario, ...]:
    return (
        LocalPreflightSimulationScenario(
            scenario_id="happy_path_symbolic_preflight_still_blocked",
            scenario_name="Happy path simulation (preflight verifies but remains blocked due to live gates)",
            simulated_response_classification="success_classification",
            response_shape_classification="valid_symbolic_shape",
            failure_or_timeout_classification="none",
            abort_policy_result="completed_dry_run_simulation",
            redaction_result="redaction_proof_verified",
            evidence_artifact_hash_required=True,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="endpoint_allowlist_missing",
            scenario_name="Allowlist missing preflight block",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="allowlist_missing_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="request_budget_exceeded",
            scenario_name="Preflight request budget exhaustion check",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="budget_exhausted_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="timeout_triggered",
            scenario_name="Network or response timeout simulation",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="timeout_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="credential_slot_missing",
            scenario_name="No credential key name registered check",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="credential_missing_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="redaction_proof_missing",
            scenario_name="Simulated failure when redaction engine is absent",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="redaction_proof_missing_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="raw_response_attempt_blocked",
            scenario_name="Prohibit raw response logging assertion check",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="raw_response_attempt_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="secret_output_attempt_blocked",
            scenario_name="Prohibit secret payload keys serialization check",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="secret_output_attempt_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="kill_switch_open_blocked",
            scenario_name="Halt execution when kill switch is open",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="kill_switch_open_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="operator_approval_missing",
            scenario_name="Halt when operator signature is absent",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="operator_approval_missing_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
        LocalPreflightSimulationScenario(
            scenario_id="platform_specific_proof_missing",
            scenario_name="Simulated failure for missing platform evidence proofs",
            simulated_response_classification="blocked_classification",
            response_shape_classification="none",
            failure_or_timeout_classification="platform_proof_missing_error",
            abort_policy_result="abort_and_clean_temporary_session",
            redaction_result="none",
            evidence_artifact_hash_required=False,
        ),
    )


def compile_simulation_decision(
    platform_id: str,
    scenario_id: str,
    runbook_packet: runbook.LiveReadOnlyResearchRunbookApprovalGateDryRunPacket | None = None,
) -> LocalPreflightSimulationDecision:
    if platform_id not in PLATFORM_IDS:
        raise ValueError(f"invalid_platform_id: {platform_id}")

    rq = runbook_packet or runbook.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    rq_dec = next((d for d in rq.runbook_gate_decisions if d.platform_id == platform_id), None)
    scenarios = build_scenarios()
    sc = next((s for s in scenarios if s.scenario_id == scenario_id), None)

    if not rq_dec or not sc:
        raise ValueError(f"missing_runbook_precedent_for_platform: {platform_id} {scenario_id}")

    is_manual = platform_id == "substack_newsletter"

    blocked_reasons = list(rq_dec.blocked_reasons)
    missing_proofs = list(rq_dec.missing_proofs)

    # Preflight validation status
    if is_manual:
        validation_status = "manual_only"
        validation_strength = "manual_policy_only"
    else:
        validation_status = "blocked" if (rq_dec.runbook_gate_status == "blocked" or sc.scenario_id != "happy_path_symbolic_preflight_still_blocked") else "not_ready"
        validation_strength = rq_dec.runbook_gate_strength

    # Scenario specific overrides
    if sc.scenario_id == "endpoint_allowlist_missing":
        blocked_reasons.append("endpoint_allowlist_missing")
        missing_proofs.append("endpoint_allowlist_missing")
    elif sc.scenario_id == "request_budget_exceeded":
        blocked_reasons.append("request_budget_exceeds_limit")
        missing_proofs.append("request_budget_exceeds_limit")
    elif sc.scenario_id == "timeout_triggered":
        blocked_reasons.append("timeout_triggered")
        missing_proofs.append("timeout_triggered")
    elif sc.scenario_id == "credential_slot_missing":
        blocked_reasons.append("credential_values_exposed")
        missing_proofs.append("credential_values_exposed")
    elif sc.scenario_id == "redaction_proof_missing":
        blocked_reasons.append("redaction_policy_missing")
        missing_proofs.append("redaction_policy_missing")
    elif sc.scenario_id == "raw_response_attempt_blocked":
        blocked_reasons.append("raw_response_logging_allowed")
        missing_proofs.append("raw_response_logging_allowed")
    elif sc.scenario_id == "secret_output_attempt_blocked":
        blocked_reasons.append("secret_output_allowed")
        missing_proofs.append("secret_output_allowed")
    elif sc.scenario_id == "kill_switch_open_blocked":
        blocked_reasons.append("kill_switch_policy_unresolved")
        missing_proofs.append("kill_switch_policy_unresolved")
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
        "precheck_status": rq_dec.precheck_status,
        "endpoint_allowlist_status": rq_dec.endpoint_allowlist_status,
        "request_budget_status": rq_dec.request_budget_status,
        "credential_policy_status": rq_dec.credential_policy_status,
        "redaction_policy_status": rq_dec.redaction_policy_status,
        "raw_response_policy_status": rq_dec.raw_response_policy_status,
        "stop_condition_status": rq_dec.stop_condition_status,
        "kill_switch_status": rq_dec.kill_switch_status,
        "operator_approval_status": rq_dec.operator_approval_status,
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
        "evidence_refs": rq_dec.evidence_refs,
    }

    h_basis = {str(k): _asdict(v) for k, v in draft.items()}
    h = sha256(json.dumps(h_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    return LocalPreflightSimulationDecision(
        decision_id=f"simulation_decision_{platform_id}_{scenario_id[:12]}_" + h[:8],
        decision_hash=h,
        **draft
    )


def build_u9_audit_entries(
    decisions: tuple[LocalPreflightSimulationDecision, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UR"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, dec in enumerate(decisions, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UR",
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


def build_supervised_live_read_only_research_local_preflight_simulation_packet(
    runbook_packet: runbook.LiveReadOnlyResearchRunbookApprovalGateDryRunPacket | None = None
) -> LocalPreflightSimulationPacket:
    rq = runbook_packet or runbook.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    ap = approval.build_supervised_live_read_only_research_approval_packet_schema_packet()

    adapter_profiles = build_adapter_profiles()
    scenarios = build_scenarios()

    decisions = []
    for pid in PLATFORM_IDS:
        for sc in scenarios:
            decisions.append(compile_simulation_decision(pid, sc.scenario_id, rq))
    decisions = tuple(decisions)

    endpoint_family_summary = {p.platform_id: p.endpoint_family for p in adapter_profiles}
    request_budget_summary = {p.platform_id: p.request_budget_max for p in adapter_profiles}
    timeout_policy_summary = {p.platform_id: p.timeout_seconds_max for p in adapter_profiles}
    credential_slot_policy_summary = {p.platform_id: p.credential_policy for p in adapter_profiles}
    redaction_policy_summary = {t.platform_id: t.redaction_policy_ref for t in ep.templates}

    simulated_response_classification_summary = {s.scenario_id: s.simulated_response_classification for s in scenarios}
    failure_or_abort_summary = {s.scenario_id: s.failure_or_timeout_classification for s in scenarios}
    platform_gate_summary = {p.platform_id: "blocked" if p.platform_id != "substack_newsletter" else "manual_only" for p in adapter_profiles}

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
    }

    draft = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "platform_count": len(PLATFORM_IDS),
        "scenario_count": len(scenarios),
        "decision_count": len(decisions),
        "simulated_adapter_profiles": adapter_profiles,
        "simulation_scenarios": scenarios,
        "simulation_decisions": decisions,
        "endpoint_family_summary": endpoint_family_summary,
        "request_budget_summary": request_budget_summary,
        "timeout_policy_summary": timeout_policy_summary,
        "credential_slot_policy_summary": credential_slot_policy_summary,
        "redaction_policy_summary": redaction_policy_summary,
        "simulated_response_classification_summary": simulated_response_classification_summary,
        "failure_or_abort_summary": failure_or_abort_summary,
        "platform_gate_summary": platform_gate_summary,
        "blocked_reasons": global_blocked_reasons,
        "missing_proofs": global_missing_proofs,
        "safety_flags": safety_flags,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "next_required_gate": NEXT_REQUIRED_GATE,
    }

    packet_hash = _digest(draft)
    return LocalPreflightSimulationPacket(
        packet_id="live_read_only_research_local_preflight_simulation_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def render_runbook(packet: LocalPreflightSimulationPacket) -> str:
    lines = [
        "# Live Read-Only Research Local Preflight Simulation Contract V0",
        "",
        "## Critical Safety Warning",
        "> [!CAUTION]",
        "> **NOT LIVE, NOT APPROVED, NOT PUBLIC-POSTABLE.**",
        "> This module compiles preflight dry-run simulation matrices for local-only validation checks.",
        "> No live reads, API calls, environment/credential reads, browser sessions, scheduler behavior, or posting are authorized.",
        "",
        f"- **Task Label**: `{packet.task_label}`",
        f"- **Source Baseline Commit**: `{packet.source_baseline_commit}`",
        f"- **Matrix/Packet ID**: `{packet.packet_id}`",
        f"- **Packet Hash**: `{packet.packet_hash}`",
        f"- **Next Required Gate**: `{packet.next_required_gate}`",
        "",
        "## 1. Simulated Adapter Profiles Matrix",
        "",
        "| Platform ID | Adapter Mode | Endpoint Family | Allowlist Status | Request Budget Max | Timeout Max | Credential Policy |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in packet.simulated_adapter_profiles:
        lines.append(
            f"| `{p.platform_id}` | `{p.adapter_mode}` | `{p.endpoint_family}` | `{p.endpoint_allowlist_status}` | `{p.request_budget_max}` | `{p.timeout_seconds_max}` | `{p.credential_policy}` |"
        )

    lines.extend([
        "",
        "## 2. Preflight Simulation Scenarios Checklist",
        "",
        "| Scenario ID | Classification | Failure/Timeout Class | Abort Result | Redaction Result |",
        "|---|---|---|---|---|",
    ])
    for s in packet.simulation_scenarios:
        lines.append(
            f"| `{s.scenario_id}` | `{s.simulated_response_classification}` | `{s.failure_or_timeout_classification}` | `{s.abort_policy_result}` | `{s.redaction_result}` |"
        )

    lines.extend([
        "",
        "## 3. Required Preflight Checklists",
        "",
        "### Credential & Secret Redaction Check",
        "- [ ] Ensure env configuration keys are validated for format and length.",
        "- [ ] Ensure zero credentials values are ever logged or printed.",
        "- [ ] Ensure all raw response bodies are strictly redacted and omitted from log entries.",
        "",
        "### Endpoint Allowlist & Timeout Rules",
        "- [ ] Confirm symbolic allowlist registry is matching endpoint pattern.",
        "- [ ] Confirm timeout policy is strictly bounded (max 30 seconds).",
        "",
        "### Request Budget Rules",
        "- [ ] Verify that request budget does not exceed limit (maximum 1 request).",
        "",
        "## 4. Platform-Specific Simulation Blockers Summary",
        "",
    ])
    # Platform profiles loop
    for p in packet.simulated_adapter_profiles:
        lines.append(f"### Platform `{p.platform_id}`")
        lines.append(f"- **Simulated Endpoint Family**: `{p.endpoint_family}`")
        lines.append(f"- **Credential Policy**: `{p.credential_policy}`")
        lines.append("")

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UR")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_supervised_live_read_only_research_local_preflight_simulation_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "LocalPreflightSimulatedAdapterProfile",
    "LocalPreflightSimulationScenario",
    "LocalPreflightSimulationDecision",
    "LocalPreflightSimulationPacket",
    "build_adapter_profiles",
    "build_scenarios",
    "compile_simulation_decision",
    "build_supervised_live_read_only_research_local_preflight_simulation_packet",
    "render_runbook",
    "write_artifacts",
]
