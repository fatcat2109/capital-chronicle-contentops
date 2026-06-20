"""Supervised live read-only research gate precheck contract for ContentOps 0174UN.

Deterministic local-only research gate precheck. No live/API/provider/network/env/
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
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UN_SUPERVISED_LIVE_READ_ONLY_RESEARCH_GATE_PRECHECK_V0"
MATRIX_VERSION = "0174UN_SUPERVISED_LIVE_READ_ONLY_RESEARCH_GATE_PRECHECK_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "65c2ba47f4d48530b7b320ff0f47fd0047bd228a"
DOC_REL_DIR = Path("docs") / "automation" / "0174UN"
PACKET_FILENAME = "supervised_live_read_only_research_gate_precheck_contract_packet.json"
RUNBOOK_FILENAME = "supervised_live_read_only_research_gate_precheck_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "supervised_live_read_only_research_gate_precheck_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UO_LIVE_READ_ONLY_RESEARCH_APPROVAL_PACKET_SCHEMA_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class ProposedLiveReadOnlyResearchGate:
    gate_id: str
    platform_id: str
    research_kind: str
    endpoint_family: str
    endpoint_allowlist: tuple[str, ...]
    account_binding_ref: str
    credential_handle_ref: str
    requested_request_budget: int
    requested_timeout_seconds: int
    operator_approval_required: bool
    operator_approval_ref: str
    redaction_required: bool
    kill_switch_required: bool
    kill_switch_state: str
    stop_conditions: tuple[str, ...]
    live_read_requested: bool = False
    live_write_requested: bool = False
    env_read_requested: bool = False
    credential_hydration_requested: bool = False
    platform_api_call_requested: bool = False
    public_post_requested: bool = False
    scheduler_requested: bool = False
    browser_automation_requested: bool = False
    evidence_refs: tuple[str, ...] = ()
    gate_hash: str = ""
    gate_hash_algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.platform_id not in PLATFORM_IDS:
            raise ValueError(f"invalid_platform_id: {self.platform_id}")
        kinds = (
            "official_doc_refresh", "account_state_read", "post_status_read",
            "metrics_read", "channel_state_read", "inbox_state_read",
            "app_review_status_read", "quota_state_read", "manual_export_state_review"
        )
        if self.research_kind not in kinds:
            raise ValueError(f"invalid_research_kind: {self.research_kind}")


@dataclass(frozen=True)
class LiveReadOnlyResearchGatePrecheckDecision:
    decision_id: str
    gate_id: str
    platform_id: str
    research_kind: str
    decision_status: str
    decision_strength: str
    readiness_review_status: str
    account_binding_status: str
    credential_boundary_status: str
    official_docs_status: str
    permission_gate_status: str
    rate_budget_status: str
    preflight_status: str
    endpoint_allowlist_status: str
    credential_policy_status: str
    request_budget_status: str
    redaction_status: str
    kill_switch_status: str
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
    required_future_approval_packet_fields: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    decision_hash: str
    decision_hash_algorithm: str


@dataclass(frozen=True)
class LiveReadOnlyResearchGatePrecheckPacket:
    packet_id: str
    matrix_version: str
    generated_at_epoch: int
    source_baseline_commit: str
    proposed_gates: tuple[ProposedLiveReadOnlyResearchGate, ...]
    decisions: tuple[LiveReadOnlyResearchGatePrecheckDecision, ...]
    decisions_by_platform: dict[str, tuple[str, ...]]
    platform_count: int
    gate_count: int
    decision_count: int
    blocked_precheck_count: int
    not_ready_count: int
    manual_only_count: int
    future_supervised_live_read_candidate_count: int
    invalid_gate_count: int
    live_read_allowed_count: int
    live_write_allowed_count: int
    env_read_allowed_count: int
    credential_hydrated_count: int
    platform_api_called_count: int
    public_post_allowed_count: int
    readiness_cleared_count: int
    scheduler_enabled_count: int
    browser_session_used_count: int
    global_live_read_only_precheck_status: str
    all_live_actions_blocked: bool
    u9_audit_entry_ids: tuple[str, ...]
    u9_audit_entry_families: tuple[str, ...]
    evidence_refs: tuple[str, ... ]
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


def build_default_proposed_gates() -> tuple[ProposedLiveReadOnlyResearchGate, ...]:
    gates = []
    specs = [
        ("x", "account_state_read", "x_api_read_only_symbolic", 1),
        ("telegram_remote_operator", "inbox_state_read", "telegram_bot_getupdates_or_webhook_symbolic", 1),
        ("telegram_channel_destination", "channel_state_read", "telegram_bot_getchat_symbolic", 1),
        ("substack_newsletter", "manual_export_state_review", "manual_export_no_api", 0),
        ("linkedin", "account_state_read", "linkedin_api_read_only_symbolic", 1),
        ("threads", "account_state_read", "meta_threads_read_only_symbolic", 1),
        ("instagram", "account_state_read", "meta_instagram_read_only_symbolic", 1),
        ("facebook_page", "account_state_read", "meta_facebook_page_read_only_symbolic", 1),
        ("tiktok", "account_state_read", "tiktok_read_only_symbolic", 1),
        ("youtube", "quota_state_read", "youtube_data_api_read_only_symbolic", 1),
    ]
    for platform_id, kind, endpoint_family, budget in specs:
        allowlist = (f"symbolic_allowlist_entry:{platform_id}",) if platform_id != "substack_newsletter" else ()
        gate = ProposedLiveReadOnlyResearchGate(
            gate_id=f"proposed_live_read_only_gate_{platform_id}",
            platform_id=platform_id,
            research_kind=kind,
            endpoint_family=endpoint_family,
            endpoint_allowlist=allowlist,
            account_binding_ref=f"platform_account_binding_{platform_id}_symbolic",
            credential_handle_ref=f"symbolic_credential_handle:{platform_id}",
            requested_request_budget=budget,
            requested_timeout_seconds=30,
            operator_approval_required=True,
            operator_approval_ref="operator_approval_pending",
            redaction_required=True,
            kill_switch_required=True,
            kill_switch_state="closed",
            stop_conditions=("on_error", "on_budget_exhausted"),
            live_read_requested=False,
            live_write_requested=False,
            env_read_requested=False,
            credential_hydration_requested=False,
            platform_api_call_requested=False,
            public_post_requested=False,
            scheduler_requested=False,
            browser_automation_requested=False,
            evidence_refs=(),
        )
        h = sha256(_json(gate).encode("utf-8")).hexdigest()
        gate = replace(gate, gate_hash=h, gate_hash_algorithm=HASH_ALGORITHM)
        gates.append(gate)
    return tuple(gates)


def compile_decision(
    gate: ProposedLiveReadOnlyResearchGate,
    um_packet: readiness.SupervisedLiveReadinessReviewPacket | None = None
) -> LiveReadOnlyResearchGatePrecheckDecision:
    packet_um = um_packet or readiness.build_supervised_live_readiness_review_packet()
    um_row = next((r for r in packet_um.readiness_rows if r.platform_id == gate.platform_id), None)
    if not um_row:
        raise ValueError(f"no_readiness_row_found_for_platform: {gate.platform_id}")

    blocked_reasons: list[str] = []
    missing_proofs: list[str] = []

    # 1. 0174UM row check
    if um_row.live_readiness_status == "blocked":
        blocked_reasons.append("platform_readiness_blocked_in_um")
        decision_status = "blocked_precheck"
    elif um_row.live_readiness_status == "needs_human_review":
        blocked_reasons.append("platform_readiness_requires_human_review_in_um")
        decision_status = "not_ready"
    elif um_row.live_readiness_status == "manual_only":
        decision_status = "manual_only"
    else:
        decision_status = "future_supervised_live_read_candidate"

    # 2. Kill switch
    if gate.platform_id == "substack_newsletter":
        kill_switch_status = "manual_stop_policy"
    elif gate.kill_switch_state == "closed":
        kill_switch_status = "kill_switch_closed"
    elif gate.kill_switch_state == "open":
        kill_switch_status = "kill_switch_open_blocks"
        blocked_reasons.append("kill_switch_gate_open_or_missing")
        decision_status = "blocked_precheck"
    else:
        kill_switch_status = "kill_switch_missing_blocks"
        blocked_reasons.append("kill_switch_gate_open_or_missing")
        decision_status = "blocked_precheck"

    # 3. Endpoint allowlist
    if gate.platform_id == "substack_newsletter":
        endpoint_allowlist_status = "manual_no_api"
    elif not gate.endpoint_allowlist:
        endpoint_allowlist_status = "allowlist_missing"
        blocked_reasons.append("endpoint_allowlist_missing")
        decision_status = "blocked_precheck"
    else:
        endpoint_allowlist_status = "allowlist_symbolic"

    # 4. Request budget
    if gate.platform_id == "substack_newsletter":
        if gate.requested_request_budget > 0:
            request_budget_status = "request_budget_exceeds_limit"
            blocked_reasons.append("request_budget_limit_exceeded")
            decision_status = "blocked_precheck"
        else:
            request_budget_status = "manual_no_api"
    else:
        if gate.requested_request_budget > 1:
            request_budget_status = "request_budget_exceeds_limit"
            blocked_reasons.append("request_budget_limit_exceeded")
            decision_status = "blocked_precheck"
        elif gate.requested_request_budget == 0:
            request_budget_status = "request_budget_zero"
        else:
            request_budget_status = "request_budget_within_symbolic_limit"

    # 5. Redaction status
    if gate.platform_id == "substack_newsletter":
        redaction_status = "manual_no_secret"
    elif not gate.redaction_required:
        redaction_status = "redaction_required_missing_proof"
        blocked_reasons.append("redaction_proof_missing")
        if decision_status != "blocked_precheck":
            decision_status = "not_ready"
    elif not gate.evidence_refs:
        redaction_status = "redaction_required_missing_proof"
        missing_proofs.append("redaction_proof_missing")
        if decision_status != "blocked_precheck":
            decision_status = "not_ready"
    else:
        redaction_status = "redaction_policy_present"

    # 6. Credential boundary check
    if gate.platform_id == "substack_newsletter":
        credential_policy_status = "manual_no_credential"
    elif "symbolic" in gate.credential_handle_ref:
        credential_policy_status = "credential_handle_symbolic_only"
        blocked_reasons.append("credential_boundary_unverified")
        if decision_status != "blocked_precheck":
            decision_status = "not_ready"
    else:
        credential_policy_status = "credential_required_future"

    # 7. Live action requested check
    live_requests = (
        gate.live_read_requested or gate.live_write_requested or gate.env_read_requested or
        gate.credential_hydration_requested or gate.platform_api_call_requested or
        gate.public_post_requested or gate.scheduler_requested or gate.browser_automation_requested
    )
    if live_requests:
        blocked_reasons.append("live_actions_forbidden_in_current_task")
        decision_status = "blocked_precheck"

    # Platform specific blockers
    if gate.platform_id == "x":
        for b in ("x_app_access_gap", "spend_gate_unresolved", "rate_budget_gap", "read_only_endpoint_proof_gap"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif gate.platform_id == "telegram_remote_operator":
        for b in ("no_arbitrary_dm_allowed", "operator_inbox_proof_required"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif gate.platform_id == "telegram_channel_destination":
        for b in ("channel_admin_proof_required", "bot_permission_gap", "channel_state_symbolic_only"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif gate.platform_id == "substack_newsletter":
        blocked_reasons.append("manual_export_only")
        missing_proofs.append("manual_export_only")
    elif gate.platform_id == "linkedin":
        blocked_reasons.append("linkedin_organization_page_proof_missing")
        missing_proofs.append("linkedin_organization_page_proof_missing")
    elif gate.platform_id in ("threads", "instagram", "facebook_page"):
        for b in ("meta_app_review_closed", "meta_app_account_proof_required"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif gate.platform_id == "tiktok":
        for b in ("tiktok_app_audit_closed", "creator_account_proof_required", "video_publish_proof_required"):
            blocked_reasons.append(b)
            missing_proofs.append(b)
    elif gate.platform_id == "youtube":
        for b in ("youtube_quota_unresolved", "youtube_oauth_flow_closed", "upload_proof_required"):
            blocked_reasons.append(b)
            missing_proofs.append(b)

    # Clean decision status & strength mapping
    if decision_status == "blocked_precheck":
        if "live_actions_forbidden_in_current_task" in blocked_reasons or "platform_readiness_blocked_in_um" in blocked_reasons:
            decision_strength = "deterministic_block"
        elif "endpoint_allowlist_missing" in blocked_reasons:
            decision_strength = "missing_endpoint_allowlist"
        else:
            decision_strength = "deterministic_block"
    elif decision_status == "not_ready":
        if "redaction_proof_missing" in blocked_reasons or "redaction_proof_missing" in missing_proofs:
            decision_strength = "missing_redaction_proof"
        elif "credential_boundary_unverified" in blocked_reasons:
            decision_strength = "missing_credential_policy"
        else:
            decision_strength = "missing_operator_approval"
    elif decision_status == "manual_only":
        decision_strength = "manual_policy_only"
    else:
        decision_strength = "symbolic_future_candidate"

    future_fields = (
        "explicit_task_label", "platform_id", "endpoint_family", "endpoint_allowlist",
        "credential_policy", "credential_handle_key_names_only", "request_budget",
        "timeout_seconds", "redaction_policy", "secret_output_prohibition",
        "no_raw_response_logging", "kill_switch_state", "stop_conditions",
        "rollback_or_abort_policy", "evidence_packet_schema", "operator_approval_ref"
    ) if gate.platform_id != "substack_newsletter" else ()

    draft = {
        "gate_id": gate.gate_id,
        "platform_id": gate.platform_id,
        "research_kind": gate.research_kind,
        "decision_status": decision_status,
        "decision_strength": decision_strength,
        "readiness_review_status": um_row.live_readiness_status,
        "account_binding_status": um_row.account_binding_status,
        "credential_boundary_status": um_row.credential_boundary_status,
        "official_docs_status": um_row.official_docs_status,
        "permission_gate_status": um_row.permission_gate_status,
        "rate_budget_status": um_row.rate_budget_status,
        "preflight_status": um_row.preflight_status,
        "endpoint_allowlist_status": endpoint_allowlist_status,
        "credential_policy_status": credential_policy_status,
        "request_budget_status": request_budget_status,
        "redaction_status": redaction_status,
        "kill_switch_status": kill_switch_status,
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
        "required_future_approval_packet_fields": future_fields,
        "evidence_refs": gate.evidence_refs,
    }

    h_basis = {str(k): _asdict(v) for k, v in draft.items()}
    h = sha256(json.dumps(h_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    return LiveReadOnlyResearchGatePrecheckDecision(
        decision_id=f"live_read_only_decision_{gate.platform_id}_" + h[:16],
        decision_hash=h,
        decision_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def build_u9_audit_entries(
    decisions: tuple[LiveReadOnlyResearchGatePrecheckDecision, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UN"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, dec in enumerate(decisions, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UN",
            source_model_version=MATRIX_VERSION,
            payload={
                "id": dec.decision_id,
                "platform_id": dec.platform_id,
                "research_kind": dec.research_kind,
                "status": dec.decision_status,
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


def build_supervised_live_read_only_research_gate_precheck_packet(
    gates: tuple[ProposedLiveReadOnlyResearchGate, ...] | None = None
) -> LiveReadOnlyResearchGatePrecheckPacket:
    final_gates = gates or build_default_proposed_gates()
    um_packet = readiness.build_supervised_live_readiness_review_packet()
    decisions = tuple(compile_decision(gate, um_packet) for gate in final_gates)

    decisions_by_platform = {d.platform_id: (d.decision_id,) for d in decisions}

    blocked_precheck_count = sum(1 for d in decisions if d.decision_status == "blocked_precheck")
    not_ready_count = sum(1 for d in decisions if d.decision_status == "not_ready")
    manual_only_count = sum(1 for d in decisions if d.decision_status == "manual_only")
    future_supervised_live_read_candidate_count = sum(
        1 for d in decisions if d.decision_status == "future_supervised_live_read_candidate"
    )
    invalid_gate_count = sum(1 for d in decisions if d.decision_status == "invalid_gate")

    # All allowed flags are strictly False/0
    live_read_allowed_count = 0
    live_write_allowed_count = 0
    env_read_allowed_count = 0
    credential_hydrated_count = 0
    platform_api_called_count = 0
    public_post_allowed_count = 0
    readiness_cleared_count = 0
    scheduler_enabled_count = 0
    browser_session_used_count = 0

    global_live_read_only_precheck_status = "blocked" if blocked_precheck_count > 0 else "not_ready"
    all_live_actions_blocked = True

    global_blocked_reasons = tuple(dict.fromkeys(reason for d in decisions for reason in d.blocked_reasons))
    global_missing_proofs = tuple(dict.fromkeys(proof for d in decisions for proof in d.missing_proofs))
    evidence_refs = tuple(dict.fromkeys(ref for d in decisions for ref in d.evidence_refs))

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
        "proposed_gates": final_gates,
        "decisions": decisions,
        "decisions_by_platform": decisions_by_platform,
        "platform_count": len(decisions),
        "gate_count": len(final_gates),
        "decision_count": len(decisions),
        "blocked_precheck_count": blocked_precheck_count,
        "not_ready_count": not_ready_count,
        "manual_only_count": manual_only_count,
        "future_supervised_live_read_candidate_count": future_supervised_live_read_candidate_count,
        "invalid_gate_count": invalid_gate_count,
        "live_read_allowed_count": live_read_allowed_count,
        "live_write_allowed_count": live_write_allowed_count,
        "env_read_allowed_count": env_read_allowed_count,
        "credential_hydrated_count": credential_hydrated_count,
        "platform_api_called_count": platform_api_called_count,
        "public_post_allowed_count": public_post_allowed_count,
        "readiness_cleared_count": readiness_cleared_count,
        "scheduler_enabled_count": scheduler_enabled_count,
        "browser_session_used_count": browser_session_used_count,
        "global_live_read_only_precheck_status": global_live_read_only_precheck_status,
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
    return LiveReadOnlyResearchGatePrecheckPacket(
        packet_id="live_read_only_research_gate_precheck_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def render_runbook(packet: LiveReadOnlyResearchGatePrecheckPacket) -> str:
    lines = [
        "# Supervised Live Read-Only Research Gate Precheck V0",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- matrix_version: `{packet.matrix_version}`",
        f"- source_baseline_commit: `{packet.source_baseline_commit}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Platform Research Precheck Decisions Matrix",
        "",
        "| Platform ID | Status | Strength | 0174UM Status | Allowlist Status | Credential Status | Budget Status | Kill Switch Status | Redaction Status |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for d in packet.decisions:
        lines.append(
            f"| `{d.platform_id}` | `{d.decision_status}` | `{d.decision_strength}` | `{d.readiness_review_status}` | `{d.endpoint_allowlist_status}` | `{d.credential_policy_status}` | `{d.request_budget_status}` | `{d.kill_switch_status}` | `{d.redaction_status}` |"
        )
    lines.extend([
        "",
        "## Platform-Specific Blockers & Gaps",
        "",
        "- **X**: Blocked on pay-per-use spend gate, developer portal app access, and rate budget verification.",
        "- **Telegram Bot (Remote Operator & Channel)**: Operators are distinct operator inbox checking gates. Channel bot administrator permission checks are isolated.",
        "- **Substack**: Strictly marked manual export only without active API readiness.",
        "- **LinkedIn/Meta/TikTok**: Throttling, org/page boundaries, app review, and creator/business account checks mapped.",
        "- **YouTube**: video upload quota cost is 1 unit (no stale sixteen-hundred units claim), upload gate remains closed.",
        "",
        "## Safety and Invariants",
        "",
        "- All live read/write/public post allowed counts are strictly zero.",
        "- All readiness row safety metrics remain false.",
        "- U9 preflight audit entries compiled under family `supervised_live_read_only_research_gate_precheck_future`.",
        "",
        "## Packet Summary",
        "",
        "```json",
        json.dumps({
            "platform_count": packet.platform_count,
            "blocked_precheck_count": packet.blocked_precheck_count,
            "not_ready_count": packet.not_ready_count,
            "manual_only_count": packet.manual_only_count,
            "global_status": packet.global_live_read_only_precheck_status,
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UN")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_supervised_live_read_only_research_gate_precheck_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "ProposedLiveReadOnlyResearchGate",
    "LiveReadOnlyResearchGatePrecheckDecision",
    "LiveReadOnlyResearchGatePrecheckPacket",
    "build_default_proposed_gates",
    "compile_decision",
    "build_supervised_live_read_only_research_gate_precheck_packet",
    "write_artifacts",
]
