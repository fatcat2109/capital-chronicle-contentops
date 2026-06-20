"""Live read-only research runbook and approval-gate dry-run contract for ContentOps 0174UQ.

Deterministic local-only gate and runbook compiler. No live/API/provider/network/env/
credential/browser/scheduler/scraping/DM/reply automation or UI behavior.
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

TASK_LABEL = "TASK_CONTENTOPS_0174UQ_LIVE_READ_ONLY_RESEARCH_RUNBOOK_AND_APPROVAL_GATE_DRY_RUN_V0"
MATRIX_VERSION = "0174UQ_LIVE_READ_ONLY_RESEARCH_RUNBOOK_APPROVAL_GATE_DRY_RUN_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "9656aa43fd7778e5002925f94888f0707398abf2"
DOC_REL_DIR = Path("docs") / "automation" / "0174UQ"
PACKET_FILENAME = "live_read_only_research_runbook_approval_gate_dry_run_contract_packet.json"
RUNBOOK_FILENAME = "live_read_only_research_runbook_approval_gate_dry_run_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "live_read_only_research_runbook_approval_gate_dry_run_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UR_LOCAL_PREFLIGHT_SIMULATION_OF_LIVE_READ_ADAPTERS_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class LiveReadOnlyResearchRunbookGateDecision:
    platform_id: str
    platform_role: str
    endpoint_family: str
    approval_schema_status: str
    evidence_schema_status: str
    precheck_status: str
    endpoint_allowlist_status: str
    request_budget_status: str
    credential_policy_status: str
    redaction_policy_status: str
    raw_response_policy_status: str
    stop_condition_status: str
    kill_switch_status: str
    operator_approval_status: str
    runbook_gate_status: str
    runbook_gate_strength: str
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
class LiveReadOnlyResearchRunbookApprovalGateDryRunPacket:
    packet_id: str
    packet_hash: str
    packet_hash_algorithm: str
    task_label: str
    source_baseline_commit: str
    generated_at_epoch: int
    platform_count: int
    runbook_gate_count: int
    approval_decision_count: int
    evidence_template_count: int
    runbook_gate_decisions: tuple[LiveReadOnlyResearchRunbookGateDecision, ...]
    platform_gate_summary: dict[str, str]
    operator_review_steps: tuple[str, ...]
    required_approval_fields: tuple[str, ...]
    required_evidence_fields: tuple[str, ...]
    endpoint_family_summary: dict[str, str]
    request_budget_summary: dict[str, int]
    credential_policy_summary: dict[str, str]
    redaction_policy_summary: dict[str, str]
    stop_condition_summary: dict[str, tuple[str, ...]]
    kill_switch_summary: dict[str, str]
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


def compile_runbook_decision(
    platform_id: str,
    approval_packet: approval.LiveReadOnlyResearchApprovalPacketSchemaPacket | None = None,
    evidence_packet: evidence.LiveReadOnlyEvidencePacketDryRunSchemaPacket | None = None,
) -> LiveReadOnlyResearchRunbookGateDecision:
    if platform_id not in PLATFORM_IDS:
        raise ValueError(f"invalid_platform_id: {platform_id}")

    ap = approval_packet or approval.build_supervised_live_read_only_research_approval_packet_schema_packet()
    ep = evidence_packet or evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()

    ap_dec = next((d for d in ap.validation_decisions if d.platform_id == platform_id), None)
    ep_dec = next((d for d in ep.validation_decisions if d.platform_id == platform_id), None)
    template = next((t for t in ep.templates if t.platform_id == platform_id), None)

    if not ap_dec or not ep_dec or not template:
        raise ValueError(f"missing_precedent_schema_elements_for_platform: {platform_id}")

    is_manual = platform_id == "substack_newsletter"

    blocked_reasons = list(ep_dec.blocked_reasons)
    missing_proofs = list(ep_dec.missing_proofs)

    # Standard runbook gate rules:
    approval_schema_status = ap_dec.validation_status
    evidence_schema_status = ep_dec.validation_status
    precheck_status = ap_dec.precheck_status

    if is_manual:
        runbook_gate_status = "manual_only"
        runbook_gate_strength = "manual_policy_only"
        endpoint_allowlist_status = "manual_no_api"
        request_budget_status = "manual_no_api"
        credential_policy_status = "manual_no_credential"
        redaction_policy_status = "manual_no_secret"
        raw_response_policy_status = "raw_response_blocked_ok"
        stop_condition_status = "manual_stop_policy"
        kill_switch_status = "manual_stop_policy"
        operator_approval_status = "operator_approval_required"
    else:
        runbook_gate_status = "blocked" if (ep_dec.validation_status == "dry_run_schema_blocked" or ap_dec.validation_status == "schema_blocked") else "not_ready"
        runbook_gate_strength = ep_dec.validation_strength
        endpoint_allowlist_status = ep_dec.endpoint_allowlist_status
        request_budget_status = ep_dec.request_budget_status
        credential_policy_status = ep_dec.credential_policy_status
        redaction_policy_status = ep_dec.redaction_policy_status
        raw_response_policy_status = ep_dec.raw_response_policy_status
        stop_condition_status = "stop_on_budget_or_error_verified"
        kill_switch_status = "kill_switch_closed_verified" if ep_dec.kill_switch_policy_status == "kill_switch_closed" else "kill_switch_unresolved"
        operator_approval_status = ep_dec.operator_approval_status

    # Meta validations matching constraints
    if not template.operator_approval_required:
        runbook_gate_status = "blocked"
        blocked_reasons.append("operator_approval_disabled")
    
    if not is_manual and not template.endpoint_allowlist:
        runbook_gate_status = "blocked"
        blocked_reasons.append("endpoint_allowlist_missing")

    if template.raw_response_logging_allowed:
        runbook_gate_status = "blocked"
        blocked_reasons.append("raw_response_logging_allowed")

    if template.secret_output_allowed:
        runbook_gate_status = "blocked"
        blocked_reasons.append("secret_output_allowed")

    if template.response_body_storage_allowed:
        runbook_gate_status = "blocked"
        blocked_reasons.append("response_body_storage_allowed")

    if not is_manual and template.request_budget_max > 1:
        runbook_gate_status = "blocked"
        blocked_reasons.append("request_budget_exceeds_limit")

    if not is_manual and template.kill_switch_required_state != "closed":
        runbook_gate_status = "blocked"
        blocked_reasons.append("kill_switch_policy_unresolved")

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
        "platform_role": template.endpoint_family,
        "endpoint_family": template.endpoint_family,
        "approval_schema_status": approval_schema_status,
        "evidence_schema_status": evidence_schema_status,
        "precheck_status": precheck_status,
        "endpoint_allowlist_status": endpoint_allowlist_status,
        "request_budget_status": request_budget_status,
        "credential_policy_status": credential_policy_status,
        "redaction_policy_status": redaction_policy_status,
        "raw_response_policy_status": raw_response_policy_status,
        "stop_condition_status": stop_condition_status,
        "kill_switch_status": kill_switch_status,
        "operator_approval_status": operator_approval_status,
        "runbook_gate_status": runbook_gate_status,
        "runbook_gate_strength": runbook_gate_strength,
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
        "evidence_refs": template.endpoint_allowlist,
    }

    h_basis = {str(k): _asdict(v) for k, v in draft.items()}
    h = sha256(json.dumps(h_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    return LiveReadOnlyResearchRunbookGateDecision(
        decision_hash=h,
        **draft
    )


def build_u9_audit_entries(
    decisions: tuple[LiveReadOnlyResearchRunbookGateDecision, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UQ"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, dec in enumerate(decisions, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UQ",
            source_model_version=MATRIX_VERSION,
            payload={
                "platform_id": dec.platform_id,
                "gate_status": dec.runbook_gate_status,
                "precheck_status": dec.precheck_status,
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


def build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet(
    approval_packet: approval.LiveReadOnlyResearchApprovalPacketSchemaPacket | None = None,
    evidence_packet: evidence.LiveReadOnlyEvidencePacketDryRunSchemaPacket | None = None,
) -> LiveReadOnlyResearchRunbookApprovalGateDryRunPacket:
    ap = approval_packet or approval.build_supervised_live_read_only_research_approval_packet_schema_packet()
    ep = evidence_packet or evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()

    decisions = tuple(compile_runbook_decision(pid, ap, ep) for pid in PLATFORM_IDS)

    platform_gate_summary = {d.platform_id: d.runbook_gate_status for d in decisions}

    operator_review_steps = (
        "1. Verify the targeted platform role and endpoint family.",
        "2. Confirm that the platform-specific endpoint is present in the allowlist registry.",
        "3. Assert that the request budget is symbolic and does not exceed limit (max 1 request).",
        "4. Verify that credential policy is strictly limited to key names, never raw secret values.",
        "5. Inspect the redaction proof and confirm that no raw response bodies are stored or logged.",
        "6. Confirm the kill switch status is closed and safety flags are fully locked.",
        "7. Ensure human operator approval ref is recorded and active before any future validation progression.",
    )

    required_approval_fields = approval.REQUIRED_16_FIELDS + approval.BOUNDARY_4_FIELDS
    required_evidence_fields = evidence.ALL_FIELD_KINDS

    endpoint_family_summary = {d.platform_id: d.endpoint_family for d in decisions}
    request_budget_summary = {t.platform_id: t.request_budget_max for t in ep.templates}
    credential_policy_summary = {t.platform_id: t.credential_policy for t in ep.templates}
    redaction_policy_summary = {t.platform_id: t.redaction_policy_ref for t in ep.templates}
    stop_condition_summary = {t.platform_id: t.stop_conditions for t in ep.templates}
    kill_switch_summary = {t.platform_id: t.kill_switch_required_state for t in ep.templates}

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
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "platform_count": len(decisions),
        "runbook_gate_count": len(decisions),
        "approval_decision_count": len(ap.validation_decisions),
        "evidence_template_count": len(ep.templates),
        "runbook_gate_decisions": decisions,
        "platform_gate_summary": platform_gate_summary,
        "operator_review_steps": operator_review_steps,
        "required_approval_fields": required_approval_fields,
        "required_evidence_fields": required_evidence_fields,
        "endpoint_family_summary": endpoint_family_summary,
        "request_budget_summary": request_budget_summary,
        "credential_policy_summary": credential_policy_summary,
        "redaction_policy_summary": redaction_policy_summary,
        "stop_condition_summary": stop_condition_summary,
        "kill_switch_summary": kill_switch_summary,
        "blocked_reasons": global_blocked_reasons,
        "missing_proofs": global_missing_proofs,
        "safety_flags": safety_flags,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "next_required_gate": NEXT_REQUIRED_GATE,
    }

    packet_hash = _digest(draft)
    return LiveReadOnlyResearchRunbookApprovalGateDryRunPacket(
        packet_id="live_read_only_research_runbook_approval_gate_dry_run_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def render_runbook(packet: LiveReadOnlyResearchRunbookApprovalGateDryRunPacket) -> str:
    lines = [
        "# Live Read-Only Research Runbook & Approval Gate Dry-Run V0",
        "",
        "## Critical Safety Warning",
        "> [!CAUTION]",
        "> **NOT LIVE, NOT APPROVED, NOT PUBLIC-POSTABLE.**",
        "> This module is a local-only dry-run contract mapping and validating future validation criteria.",
        "> No live reads, API calls, environment/credential reads, browser sessions, scheduler behavior, or posting are authorized.",
        "",
        f"- **Task Label**: `{packet.task_label}`",
        f"- **Source Baseline Commit**: `{packet.source_baseline_commit}`",
        f"- **Matrix/Packet ID**: `{packet.packet_id}`",
        f"- **Packet Hash**: `{packet.packet_hash}`",
        f"- **Next Required Gate**: `{packet.next_required_gate}`",
        "",
        "## 1. Runbook Validation Decisions Matrix",
        "",
        "| Platform ID | Gate Status | Precheck Status | Approval Status | Evidence Status | Allowlist Status | Budget Status | Kill Switch Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for d in packet.runbook_gate_decisions:
        lines.append(
            f"| `{d.platform_id}` | `{d.runbook_gate_status}` | `{d.precheck_status}` | `{d.approval_schema_status}` | `{d.evidence_schema_status}` | `{d.endpoint_allowlist_status}` | `{d.request_budget_status}` | `{d.kill_switch_status}` |"
        )

    lines.extend([
        "",
        "## 2. Operator Review Checklist",
        "",
    ])
    for step in packet.operator_review_steps:
        lines.append(f"- [ ] {step}")

    lines.extend([
        "",
        "## 3. Required Verification Checklists",
        "",
        "### Approval Gate Checklist",
    ])
    for field in packet.required_approval_fields:
        lines.append(f"- [ ] Verify approval validation field presence for kind `{field}`.")

    lines.extend([
        "",
        "### Evidence Packet Checklist",
    ])
    for field in packet.required_evidence_fields:
        lines.append(f"- [ ] Enforce evidence structure verification for kind `{field}`.")

    lines.extend([
        "",
        "### Redaction Proof & Security Checklist",
        "- [ ] Enforce that no raw response logging is enabled for all templates.",
        "- [ ] Enforce that all secret outputs are completely blocked.",
        "- [ ] Verify credential policy key names only (values strictly hidden).",
        "- [ ] Check that the stop condition triggered matches symbolics (`on_error`, `on_budget_exhausted`).",
        "- [ ] Verify the kill switch state remains closed.",
        "",
        "## 4. Platform Blockers & Gaps Summary",
        "",
    ])
    for d in packet.runbook_gate_decisions:
        lines.append(f"### Platform `{d.platform_id}`")
        lines.append(f"- **Role/Endpoint Family**: `{d.endpoint_family}`")
        if d.blocked_reasons:
            lines.append("- **Blocked Reasons**:")
            for r in d.blocked_reasons:
                lines.append(f"  - `{r}`")
        if d.missing_proofs:
            lines.append("- **Missing Proofs**:")
            for p in d.missing_proofs:
                lines.append(f"  - `{p}`")
        lines.append("")

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UQ")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "LiveReadOnlyResearchRunbookGateDecision",
    "LiveReadOnlyResearchRunbookApprovalGateDryRunPacket",
    "compile_runbook_decision",
    "build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet",
    "render_runbook",
    "write_artifacts",
]
