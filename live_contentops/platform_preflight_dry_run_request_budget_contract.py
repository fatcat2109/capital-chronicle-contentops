"""Platform preflight and dry-run request budget contract for ContentOps 0174UL.

Deterministic local-only preflight decision contract. No live/API/provider/network/env/
credential/browser/scheduler/scraping/DM/reply automation or UI behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

from live_contentops import platform_universe_registry_v2 as universe
from live_contentops import platform_account_binding_registry_v2_contract as binding
from live_contentops import credential_handle_dotenv_secret_boundary_v2_contract as boundary
from live_contentops import official_platform_docs_evidence_packet_matrix_contract as docs
from live_contentops import platform_permission_scope_app_review_gate_matrix_contract as permission
from live_contentops import rate_budget_kill_switch_matrix_contract as rate_budget
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UL_PLATFORM_PREFLIGHT_AND_DRY_RUN_REQUEST_BUDGET_CONTRACT_V0"
MATRIX_VERSION = "0174UL_PLATFORM_PREFLIGHT_AND_DRY_RUN_REQUEST_BUDGET_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "a9470460c795831489c89000c397dd89305556f4"
DOC_REL_DIR = Path("docs") / "automation" / "0174UL"
PACKET_FILENAME = "platform_preflight_dry_run_request_budget_contract_packet.json"
RUNBOOK_FILENAME = "platform_preflight_dry_run_request_budget_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "preflight_dry_run_request_budget_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UM_SUPERVISED_LIVE_READINESS_REVIEW_INDEX_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class ProposedPlatformAction:
    action_id: str
    platform_id: str
    action_kind: str
    intended_destination_ref: str
    account_binding_ref: str
    credential_handle_ref: str
    payload_ref: str
    requested_request_budget: int
    requested_retry_count: int
    requested_timeout_seconds: int
    operator_approval_ref: str
    kill_switch_state: str
    live_read_requested: bool = False
    live_write_requested: bool = False
    env_read_requested: bool = False
    credential_hydration_requested: bool = False
    platform_api_call_requested: bool = False
    public_post_requested: bool = False
    scheduler_requested: bool = False
    browser_automation_requested: bool = False
    evidence_refs: tuple[str, ...] = ()
    action_hash: str = ""
    action_hash_algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.platform_id not in PLATFORM_IDS:
            raise ValueError(f"invalid_platform_id: {self.platform_id}")


@dataclass(frozen=True)
class PreflightDryRunDecision:
    decision_id: str
    action_id: str
    platform_id: str
    action_kind: str
    decision_status: str
    decision_strength: str
    account_binding_status: str
    credential_boundary_status: str
    official_docs_status: str
    permission_gate_status: str
    rate_budget_gate_status: str
    kill_switch_status: str
    request_budget_status: str
    retry_status: str
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
class PreflightDryRunRequestBudgetPacket:
    packet_id: str
    matrix_version: str
    generated_at_epoch: int
    source_baseline_commit: str
    proposed_actions: tuple[ProposedPlatformAction, ...]
    decisions: tuple[PreflightDryRunDecision, ...]
    decisions_by_platform: dict[str, tuple[str, ...]]
    action_count: int
    decision_count: int
    blocked_preflight_count: int
    dry_run_symbolic_pass_count: int
    manual_export_only_count: int
    needs_human_review_count: int
    invalid_action_count: int
    live_read_allowed_count: int
    live_write_allowed_count: int
    env_read_allowed_count: int
    credential_hydrated_count: int
    platform_api_called_count: int
    public_post_allowed_count: int
    readiness_cleared_count: int
    scheduler_enabled_count: int
    browser_session_used_count: int
    request_budget_exceeded_count: int
    auto_retry_forbidden_count: int
    kill_switch_blocked_count: int
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


def _unique(values: Any) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(v) for v in values if v))


def safety_flags() -> dict[str, bool]:
    false_flags = (
        "live_read_allowed", "live_write_allowed", "public_post_allowed",
        "credential_hydrated", "platform_api_called", "provider_api_called",
        "telegram_api_called", "network_performed", "env_read",
        "browser_session_used", "scheduler_enabled", "scraping_performed",
        "dm_or_reply_automation_allowed", "dispatch_ready", "public_postable",
        "autonomous_posting_allowed", "current_truth_promoted", "dqr_cleared",
        "readiness_cleared", "ingestion_repo_mutated", "ui_generated",
    )
    return {**{flag: False for flag in false_flags}, "local_symbolic_preflight_only": True, "review_only": True}


def _action_hash_basis(action: ProposedPlatformAction | dict[str, Any]) -> dict[str, Any]:
    data = _asdict(action)
    data.pop("action_hash", None)
    data.pop("action_hash_algorithm", None)
    return data


def _decision_hash_basis(decision: PreflightDryRunDecision | dict[str, Any]) -> dict[str, Any]:
    data = _asdict(decision)
    data.pop("decision_hash", None)
    data.pop("decision_hash_algorithm", None)
    return data


def _make_proposed_action(
    *,
    action_id: str,
    platform_id: str,
    action_kind: str,
    intended_destination_ref: str,
    account_binding_ref: str,
    credential_handle_ref: str,
    payload_ref: str,
    requested_request_budget: int,
    requested_retry_count: int,
    requested_timeout_seconds: int,
    operator_approval_ref: str,
    kill_switch_state: str,
    live_read_requested: bool = False,
    live_write_requested: bool = False,
    env_read_requested: bool = False,
    credential_hydration_requested: bool = False,
    platform_api_call_requested: bool = False,
    public_post_requested: bool = False,
    scheduler_requested: bool = False,
    browser_automation_requested: bool = False,
    evidence_refs: tuple[str, ...],
) -> ProposedPlatformAction:
    draft = ProposedPlatformAction(
        action_id=action_id,
        platform_id=platform_id,
        action_kind=action_kind,
        intended_destination_ref=intended_destination_ref,
        account_binding_ref=account_binding_ref,
        credential_handle_ref=credential_handle_ref,
        payload_ref=payload_ref,
        requested_request_budget=requested_request_budget,
        requested_retry_count=requested_retry_count,
        requested_timeout_seconds=requested_timeout_seconds,
        operator_approval_ref=operator_approval_ref,
        kill_switch_state=kill_switch_state,
        live_read_requested=live_read_requested,
        live_write_requested=live_write_requested,
        env_read_requested=env_read_requested,
        credential_hydration_requested=credential_hydration_requested,
        platform_api_call_requested=platform_api_call_requested,
        public_post_requested=public_post_requested,
        scheduler_requested=scheduler_requested,
        browser_automation_requested=browser_automation_requested,
        evidence_refs=evidence_refs,
        action_hash="",
        action_hash_algorithm=HASH_ALGORITHM,
    )
    h = _digest(_action_hash_basis(draft))
    return replace(draft, action_hash=h)


# Raw specs for default proposed actions mapping
_ACTION_SPECS = (
    ("x", "channel_post_candidate", "intended_destination:x_main", 1, 0, 10, "operator_approval:x_main_draft", "closed"),
    ("telegram_remote_operator", "remote_operator_message_candidate", "intended_destination:tg_operator", 1, 0, 10, "operator_approval:tg_operator_draft", "closed"),
    ("telegram_channel_destination", "channel_post_candidate", "intended_destination:tg_channel", 1, 0, 10, "operator_approval:tg_channel_draft", "closed"),
    ("substack_newsletter", "newsletter_manual_export", "intended_destination:substack_newsletter", 0, 0, 0, "operator_approval:substack_newsletter_draft", "closed"),
    ("linkedin", "channel_post_candidate", "intended_destination:linkedin_main", 1, 0, 10, "operator_approval:linkedin_main_draft", "closed"),
    ("threads", "channel_post_candidate", "intended_destination:threads_main", 1, 0, 10, "operator_approval:threads_main_draft", "closed"),
    ("instagram", "channel_post_candidate", "intended_destination:instagram_main", 1, 0, 10, "operator_approval:instagram_main_draft", "closed"),
    ("facebook_page", "channel_post_candidate", "intended_destination:facebook_page_main", 1, 0, 10, "operator_approval:facebook_page_main_draft", "closed"),
    ("tiktok", "media_upload_candidate", "intended_destination:tiktok_main", 1, 0, 10, "operator_approval:tiktok_main_draft", "closed"),
    ("youtube", "media_upload_candidate", "intended_destination:youtube_main", 1, 0, 10, "operator_approval:youtube_main_draft", "closed"),
)


def build_default_proposed_actions() -> tuple[ProposedPlatformAction, ...]:
    # Load upstream contract outputs to resolve reference IDs
    binding_packet = binding.build_platform_account_binding_registry_packet()
    bindings = binding_packet.bindings
    
    boundary_packet = boundary.build_credential_boundary_packet()
    handles = boundary_packet.credential_handles
    
    actions = []
    for pid, kind, dest, budget, retry, timeout, approval, ks in _ACTION_SPECS:
        b_ref = next((b.binding_id for b in bindings if b.platform_id == pid), "binding_missing")
        h_ref = next((h.credential_handle_id for h in handles if h.platform_id == pid), "handle_missing")
        
        evidence = (
            "docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",
            f"default_proposed_action_spec:{pid}"
        )
        actions.append(
            _make_proposed_action(
                action_id=f"default_proposed_action_{pid}",
                platform_id=pid,
                action_kind=kind,
                intended_destination_ref=dest,
                account_binding_ref=b_ref,
                credential_handle_ref=h_ref,
                payload_ref=f"payload_ref:{pid}",
                requested_request_budget=budget,
                requested_retry_count=retry,
                requested_timeout_seconds=timeout,
                operator_approval_ref=approval,
                kill_switch_state=ks,
                evidence_refs=evidence,
            )
        )
    return tuple(actions)


def build_preflight_dry_run_decision(
    action: ProposedPlatformAction
) -> PreflightDryRunDecision:
    pid = action.platform_id
    
    # Load all dependencies to verify
    binding_packet = binding.build_platform_account_binding_registry_packet()
    bindings = binding_packet.bindings
    
    boundary_packet = boundary.build_credential_boundary_packet()
    handles = boundary_packet.credential_handles
    
    docs_packet = docs.build_official_platform_docs_evidence_matrix_packet()
    doc_refs = docs_packet.docs_rows
    
    perm_packet = permission.build_platform_permission_scope_app_review_gate_packet()
    perm_rows = perm_packet.permission_gate_rows
    
    rate_packet = rate_budget.build_rate_budget_kill_switch_packet()
    rate_rows = rate_packet.rows
    
    # Initialize variables
    blockers = []
    missing_proofs = []
    
    # 1. Evaluate account binding status
    bind_row = next((b for b in bindings if b.binding_id == action.account_binding_ref), None)
    if bind_row:
        if bind_row.platform_id != pid:
            account_binding_status = "binding_mismatch"
            blockers.append("binding_mismatch")
        else:
            account_binding_status = "binding_found"
    else:
        account_binding_status = "binding_missing"
        blockers.append("binding_missing")
        missing_proofs.append("binding_proof_missing")
        
    # 2. Evaluate credential handle status
    handle_row = next((h for h in handles if h.credential_handle_id == action.credential_handle_ref), None)
    if handle_row:
        if handle_row.platform_id != pid:
            credential_boundary_status = "credential_hydration_forbidden"
            blockers.append("credential_handle_mismatch")
        else:
            credential_boundary_status = "credential_handle_known_symbolic"
            # Add handles blockers if present
            blockers.extend(handle_row.blocked_reasons)
    else:
        credential_boundary_status = "credential_missing_for_future_gate"
        blockers.append("credential_handle_missing")
        missing_proofs.append("credential_handle_missing")
        
    # 3. Evaluate official docs status
    doc_row = next((d for d in doc_refs if d.platform_id == pid), None)
    if doc_row:
        if doc_row.docs_evidence_strength in ("partial", "weak"):
            official_docs_status = "docs_evidence_partial"
        elif doc_row.docs_evidence_strength == "blocked":
            official_docs_status = "docs_evidence_missing"
            blockers.append("docs_evidence_missing")
            missing_proofs.append("docs_evidence_missing")
        else:
            official_docs_status = "docs_evidence_found"
    else:
        official_docs_status = "docs_evidence_missing"
        blockers.append("docs_evidence_missing")
        missing_proofs.append("docs_evidence_missing")
        
    # 4. Permission gate status check
    perm_row = next((p for p in perm_rows if p.platform_id == pid), None)
    if perm_row:
        permission_gate_status = perm_row.gate_status
        if permission_gate_status in ("blocked_missing_permission_scope_matrix", "blocked_missing_app_review_proof", "blocked_missing_account_role_proof", "blocked_manual_export_only", "needs_human_review", "symbolic_permission_matrix_ready"):
            if permission_gate_status == "symbolic_permission_matrix_ready":
                blockers.append("permission_gate_status_official_doc_supported")
            else:
                blockers.append(f"permission_gate_status_{permission_gate_status}")
            blockers.extend(perm_row.blocked_reasons)
            missing_proofs.extend(perm_row.blocked_reasons)
    else:
        permission_gate_status = "blocked_missing_permission_scope_matrix"
        blockers.append("permission_gate_missing")
        
    # 5. Rate budget gate status check
    rate_row = next((r for r in rate_rows if r.platform_id == pid), None)
    if rate_row:
        rate_budget_gate_status = rate_row.gate_status
        if rate_budget_gate_status in ("rate_budget_gate_blocked", "needs_human_review", "symbolic_rate_budget_ready"):
            if rate_budget_gate_status == "symbolic_rate_budget_ready":
                blockers.append("rate_budget_gate_status_symbolic_rate_budget_ready")
            else:
                blockers.append(f"rate_budget_gate_status_{rate_budget_gate_status}")
            blockers.extend(rate_row.blocked_reasons)
            missing_proofs.extend(rate_row.blocked_reasons)
    else:
        rate_budget_gate_status = "rate_budget_gate_blocked"
        blockers.append("rate_budget_gate_missing")

    # 6. Evaluate requested budget and limits
    # Retrieve limit from rate registry if present, else default
    max_budget = 0
    if rate_row:
        # Determine maximum allowed budget from platform specifications
        reqs_matching = [r for r in rate_budget.build_default_requirements() if r.platform_id == pid]
        if reqs_matching:
            max_budget = max(r.max_request_budget_allowed for r in reqs_matching)
            
    if pid == "substack_newsletter":
        request_budget_status = "request_budget_not_applicable_manual_export"
    elif action.requested_request_budget == 0:
        request_budget_status = "request_budget_zero"
    elif action.requested_request_budget > max_budget:
        request_budget_status = "request_budget_exceeds_limit"
        if max_budget > 0:
            blockers.append("request_budget_exceeds_limit")
    else:
        request_budget_status = "request_budget_within_symbolic_limit"
        
    # 7. Evaluate retry policy
    if action.requested_retry_count > 0:
        retry_status = "retry_forbidden"
        blockers.append("retry_forbidden")
    else:
        retry_status = "retry_zero"
        
    # 8. Evaluate kill switch status
    is_api = pid != "substack_newsletter"
    if not is_api:
        kill_switch_status = "manual_stop_policy"
    else:
        if action.kill_switch_state == "closed":
            kill_switch_status = "kill_switch_closed"
        elif action.kill_switch_state == "open":
            kill_switch_status = "kill_switch_open_blocks"
            blockers.append("kill_switch_open_blocks")
        else:
            kill_switch_status = "kill_switch_missing_blocks"
            blockers.append("kill_switch_missing_blocks")
            
    # 9. Evaluate safety check violations (Live requests block preflight)
    if (action.live_read_requested or action.live_write_requested or
        action.env_read_requested or action.credential_hydration_requested or
        action.platform_api_call_requested or action.public_post_requested or
        action.scheduler_requested or action.browser_automation_requested):
        
        decision_status = "blocked_preflight"
        decision_strength = "deterministic_block"
        
        # Add details of what was requested
        if action.live_read_requested: blockers.append("live_read_requested")
        if action.live_write_requested: blockers.append("live_write_requested")
        if action.env_read_requested: blockers.append("env_read_requested")
        if action.credential_hydration_requested: blockers.append("credential_hydration_requested")
        if action.platform_api_call_requested: blockers.append("platform_api_call_requested")
        if action.public_post_requested: blockers.append("public_post_requested")
        if action.scheduler_requested: blockers.append("scheduler_requested")
        if action.browser_automation_requested: blockers.append("browser_automation_requested")

    # 10. Platform-specific blockers check
    if pid == "telegram_remote_operator" and "no_arbitrary_dm_allowed" not in blockers:
        blockers.append("no_arbitrary_dm_allowed")
        missing_proofs.append("operator_inbox_chat_proof_required")
        
    # 11. Compile final decision status
    if "decision_status" not in locals():
        # Check if any blocker has been logged so far
        # We also treat permission/rate budget statuses as blockers
        has_blocked_gate = (
            permission_gate_status in ("blocked_missing_permission_scope_matrix", "blocked_missing_app_review_proof", "blocked_missing_account_role_proof", "blocked_manual_export_only") or
            rate_budget_gate_status == "rate_budget_gate_blocked" or
            "request_budget_exceeds_limit" in blockers or
            "retry_forbidden" in blockers or
            "kill_switch_open_blocks" in blockers or
            "kill_switch_missing_blocks" in blockers
        )
        
        if pid == "substack_newsletter":
            decision_status = "manual_export_only"
            decision_strength = "weak_manual_policy"
        elif has_blocked_gate:
            decision_status = "blocked_preflight"
            decision_strength = "deterministic_block"
        elif (permission_gate_status == "needs_human_review" or
              rate_budget_gate_status == "needs_human_review" or
              "rate_limit_and_spend_gate_unresolved" in blockers or
              pid in ("x", "telegram_remote_operator", "telegram_channel_destination", "linkedin", "threads", "instagram", "facebook_page", "tiktok", "youtube")):
            # All other default platforms have pending reviews
            decision_status = "needs_human_review"
            decision_strength = "missing_proof"
        else:
            decision_status = "dry_run_symbolic_pass"
            decision_strength = "symbolic_local_pass"
            
    evidence = (
        "docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",
        f"preflight_decision_evidence:{pid}"
    )
    
    draft = {
        "action_id": action.action_id,
        "platform_id": pid,
        "action_kind": action.action_kind,
        "decision_status": decision_status,
        "decision_strength": decision_strength,
        "account_binding_status": account_binding_status,
        "credential_boundary_status": credential_boundary_status,
        "official_docs_status": official_docs_status,
        "permission_gate_status": permission_gate_status,
        "rate_budget_gate_status": rate_budget_gate_status,
        "kill_switch_status": kill_switch_status,
        "request_budget_status": request_budget_status,
        "retry_status": retry_status,
        "live_read_allowed": False,
        "live_write_allowed": False,
        "env_read_allowed": False,
        "credential_hydrated": False,
        "platform_api_called": False,
        "public_post_allowed": False,
        "readiness_cleared": False,
        "scheduler_enabled": False,
        "browser_session_used": False,
        "blocked_reasons": tuple(dict.fromkeys(blockers)),
        "missing_proofs": tuple(dict.fromkeys(missing_proofs)),
        "evidence_refs": evidence,
    }
    
    h = _digest(draft)
    
    return PreflightDryRunDecision(
        decision_id=f"preflight_decision_{pid}_{h[:16]}",
        decision_hash=h,
        decision_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def build_u9_audit_entries(
    packet_or_decisions: PreflightDryRunRequestBudgetPacket | tuple[PreflightDryRunDecision, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    decisions = packet_or_decisions.decisions if hasattr(packet_or_decisions, "decisions") else packet_or_decisions
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UL"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, dec in enumerate(decisions, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UL",
            source_model_version=MATRIX_VERSION,
            payload={
                "id": dec.decision_id,
                "action_id": dec.action_id,
                "platform_id": dec.platform_id,
                "status": dec.decision_status,
                "source_payload_hash": dec.decision_hash,
                "evidence_refs": dec.evidence_refs,
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


def build_preflight_dry_run_request_budget_packet(
    actions: tuple[ProposedPlatformAction, ...] | None = None
) -> PreflightDryRunRequestBudgetPacket:
    proposed = actions or build_default_proposed_actions()
    decisions = tuple(build_preflight_dry_run_decision(a) for a in proposed)
    
    by_platform = {pid: tuple(d.decision_id for d in decisions if d.platform_id == pid) for pid in PLATFORM_IDS}
    
    evidence_refs = _unique(ref for d in decisions for ref in d.evidence_refs)
    blockers = _unique(reason for d in decisions for reason in d.blocked_reasons)
    missing_proofs = _unique(proof for d in decisions for proof in d.missing_proofs)
    
    audit_entries = build_u9_audit_entries(decisions)
    
    # Counts
    blocked_preflight = sum(1 for d in decisions if d.decision_status == "blocked_preflight")
    dry_run_pass = sum(1 for d in decisions if d.decision_status == "dry_run_symbolic_pass")
    manual_export = sum(1 for d in decisions if d.decision_status == "manual_export_only")
    needs_review = sum(1 for d in decisions if d.decision_status == "needs_human_review")
    invalid_action = sum(1 for d in decisions if d.decision_status == "invalid_action")
    
    budget_exceeded = sum(1 for d in decisions if d.request_budget_status == "request_budget_exceeds_limit")
    auto_retry = sum(1 for a in proposed if a.requested_retry_count > 0 or a.live_read_requested)  # retry related block count
    ks_blocked = sum(1 for d in decisions if d.kill_switch_status in ("kill_switch_open_blocks", "kill_switch_missing_blocks"))
    
    draft = {
        "matrix_version": MATRIX_VERSION,
        "generated_at_epoch": 0,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "proposed_actions": proposed,
        "decisions": decisions,
        "decisions_by_platform": by_platform,
        "action_count": len(proposed),
        "decision_count": len(decisions),
        "blocked_preflight_count": blocked_preflight,
        "dry_run_symbolic_pass_count": dry_run_pass,
        "manual_export_only_count": manual_export,
        "needs_human_review_count": needs_review,
        "invalid_action_count": invalid_action,
        "live_read_allowed_count": 0,
        "live_write_allowed_count": 0,
        "env_read_allowed_count": 0,
        "credential_hydrated_count": 0,
        "platform_api_called_count": 0,
        "public_post_allowed_count": 0,
        "readiness_cleared_count": 0,
        "scheduler_enabled_count": 0,
        "browser_session_used_count": 0,
        "request_budget_exceeded_count": budget_exceeded,
        "auto_retry_forbidden_count": auto_retry,
        "kill_switch_blocked_count": ks_blocked,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags(),
        "blocked_reasons": blockers,
        "missing_proofs": missing_proofs,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    
    packet_hash = _digest(draft)
    
    return PreflightDryRunRequestBudgetPacket(
        packet_id="preflight_dry_run_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def render_runbook(packet: PreflightDryRunRequestBudgetPacket) -> str:
    lines = [
        "# 0174UL Platform Preflight & Dry-Run Request Budget Contract V0",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- matrix_version: `{packet.matrix_version}`",
        f"- source_baseline_commit: `{packet.source_baseline_commit}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Platform Preflight Decisions Matrix",
        "",
        "| Platform ID | Action ID | Status | Strength | Binding | Boundary | Docs | Kill Switch | Blockers |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for dec in packet.decisions:
        blockers = ", ".join(dec.blocked_reasons[:3])
        lines.append(
            f"| `{dec.platform_id}` | `{dec.action_id}` | `{dec.decision_status}` | `{dec.decision_strength}` | `{dec.account_binding_status}` | `{dec.credential_boundary_status}` | `{dec.official_docs_status}` | `{dec.kill_switch_status}` | `{blockers}` |"
        )
        
    lines.extend([
        "",
        "## Required Distinctions & Caveats",
        "",
        "- **X**: Blocked on pay-per-use spend gate and developer portal app access matrix status.",
        "- **Telegram Bot (Remote Operator & Channel)**: Distinct Remote Operator inbox message checking actions are isolated from channel posting actions. Operators block arbitrary DM.",
        "- **Substack**: Grounded strictly as manual export only without API request budgets or live hooks.",
        "- **LinkedIn/Meta/TikTok**: Throttling, container limits, and App Review blockers mapped. LinkedIn organizational access controls page proof fails closed.",
        "- **YouTube**: Videos.insert media upload represented with quota cost 1 unit without the stale sixteen-hundred units claim.",
        "",
        "## Safety Enforcements",
        "",
        "- All live allowed flags remain strictly false.",
        "- Auto retry and retry counts > 0 are forbidden.",
        "- Kill switch open or missing blocks all API-capable platform actions.",
        "- U9 preflight audit entries compiled under family `preflight_dry_run_request_budget_future`.",
        "",
        "## Packet Summary",
        "",
        "```json",
        json.dumps({
            "action_count": packet.action_count,
            "blocked_preflight_count": packet.blocked_preflight_count,
            "dry_run_symbolic_pass_count": packet.dry_run_symbolic_pass_count,
            "manual_export_only_count": packet.manual_export_only_count,
            "needs_human_review_count": packet.needs_human_review_count,
            "auto_retry_forbidden_count": packet.auto_retry_forbidden_count,
            "kill_switch_blocked_count": packet.kill_switch_blocked_count,
            "live_read_allowed_count": packet.live_read_allowed_count,
            "live_write_allowed_count": packet.live_write_allowed_count,
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UL")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_preflight_dry_run_request_budget_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "ProposedPlatformAction",
    "PreflightDryRunDecision",
    "PreflightDryRunRequestBudgetPacket",
    "build_default_proposed_actions",
    "build_preflight_dry_run_decision",
    "build_u9_audit_entries",
    "build_preflight_dry_run_request_budget_packet",
    "write_artifacts",
]
