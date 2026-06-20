"""Supervised live readiness review index contract for ContentOps 0174UM.

Deterministic local-only readiness review index. No live/API/provider/network/env/
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
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UM_SUPERVISED_LIVE_READINESS_REVIEW_INDEX_V0"
MATRIX_VERSION = "0174UM_SUPERVISED_LIVE_READINESS_REVIEW_INDEX_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "0842fde2b1609783b4607cb561cce9cfb2d25044"
DOC_REL_DIR = Path("docs") / "automation" / "0174UM"
PACKET_FILENAME = "supervised_live_readiness_review_index_contract_packet.json"
RUNBOOK_FILENAME = "supervised_live_readiness_review_index_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "supervised_live_readiness_review_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UN_SUPERVISED_LIVE_READ_ONLY_RESEARCH_GATE_PRECHECK_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class PlatformReadinessEvidenceRow:
    row_id: str
    platform_id: str
    platform_role: str
    account_binding_row_refs: tuple[str, ...]
    credential_boundary_refs: tuple[str, ...]
    official_docs_refs: tuple[str, ...]
    permission_gate_refs: tuple[str, ...]
    rate_budget_gate_refs: tuple[str, ...]
    preflight_decision_refs: tuple[str, ...]
    account_binding_status: str
    credential_boundary_status: str
    official_docs_status: str
    permission_gate_status: str
    app_review_status: str
    rate_budget_status: str
    kill_switch_status: str
    preflight_status: str
    manual_export_status: str
    live_readiness_status: str
    live_readiness_strength: str
    missing_proofs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    next_required_evidence: str
    live_read_allowed: bool
    live_write_allowed: bool
    env_read_allowed: bool
    credential_hydrated: bool
    platform_api_called: bool
    public_post_allowed: bool
    readiness_cleared: bool
    scheduler_enabled: bool
    browser_session_used: bool
    row_hash: str
    row_hash_algorithm: str

    def __post_init__(self) -> None:
        if self.platform_id not in PLATFORM_IDS:
            raise ValueError(f"invalid_platform_id: {self.platform_id}")


@dataclass(frozen=True)
class SupervisedLiveReadinessReviewPacket:
    packet_id: str
    matrix_version: str
    generated_at_epoch: int
    source_baseline_commit: str
    readiness_rows: tuple[PlatformReadinessEvidenceRow, ...]
    rows_by_platform: dict[str, tuple[str, ...]]
    platform_count: int
    blocked_count: int
    manual_only_count: int
    symbolic_only_count: int
    needs_human_review_count: int
    future_live_review_candidate_count: int
    live_read_allowed_count: int
    live_write_allowed_count: int
    env_read_allowed_count: int
    credential_hydrated_count: int
    platform_api_called_count: int
    public_post_allowed_count: int
    readiness_cleared_count: int
    scheduler_enabled_count: int
    browser_session_used_count: int
    all_platforms_blocked_or_manual_or_review: bool
    global_readiness_status: str
    global_blocked_reasons: tuple[str, ...]
    global_missing_proofs: tuple[str, ...]
    u9_audit_entry_ids: tuple[str, ...]
    u9_audit_entry_families: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
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


def build_platform_readiness_row(
    platform_id: str,
    *,
    binding_packet: binding.AccountBindingRegistryPacket | None = None,
    boundary_packet: boundary.CredentialBoundaryPacket | None = None,
    docs_packet: docs.OfficialPlatformDocsEvidenceMatrixPacket | None = None,
    perm_packet: permission.PlatformPermissionScopeAppReviewGatePacket | None = None,
    rate_packet: rate_budget.RateBudgetKillSwitchPacket | None = None,
    preflight_packet: preflight.PreflightDryRunRequestBudgetPacket | None = None,
) -> PlatformReadinessEvidenceRow:
    # 1. Fetch packets if not provided
    b_packet = binding_packet or binding.build_platform_account_binding_registry_packet()
    bd_packet = boundary_packet or boundary.build_credential_boundary_packet()
    d_packet = docs_packet or docs.build_official_platform_docs_evidence_matrix_packet()
    p_packet = perm_packet or permission.build_platform_permission_scope_app_review_gate_packet()
    r_packet = rate_packet or rate_budget.build_rate_budget_kill_switch_packet()
    pf_packet = preflight_packet or preflight.build_preflight_dry_run_request_budget_packet()

    # 2. Find row/decision for this platform
    dec = next((d for d in pf_packet.decisions if d.platform_id == platform_id), None)
    if not dec:
        raise ValueError(f"no_preflight_decision_found_for_platform: {platform_id}")

    u_entry = universe.PLATFORMS_BY_ID.get(platform_id)
    if not u_entry:
        raise ValueError(f"no_universe_entry_found_for_platform: {platform_id}")

    p_bindings = [b for b in b_packet.bindings if b.platform_id == platform_id]
    account_binding_row_refs = tuple(b.binding_id for b in p_bindings)

    p_handles = [h for h in bd_packet.credential_handles if h.platform_id == platform_id]
    credential_boundary_refs = tuple(h.credential_handle_id for h in p_handles)

    p_docs = [r for r in d_packet.docs_rows if r.platform_id == platform_id]
    official_docs_refs = tuple(r.row_id for r in p_docs)

    p_perms = [p for p in p_packet.permission_gate_rows if p.platform_id == platform_id]
    permission_gate_refs = tuple(p.row_id for p in p_perms)

    p_rates = [r for r in r_packet.rows if r.platform_id == platform_id]
    rate_budget_gate_refs = tuple(r.row_id for r in p_rates)

    preflight_decision_refs = (dec.decision_id,)

    # 3. Pull status from preflight decision
    account_binding_status = dec.account_binding_status
    credential_boundary_status = dec.credential_boundary_status
    official_docs_status = dec.official_docs_status
    permission_gate_status = dec.permission_gate_status
    rate_budget_status = dec.rate_budget_gate_status
    kill_switch_status = dec.kill_switch_status
    preflight_status = dec.decision_status

    # manual export status
    if platform_id == "substack_newsletter":
        manual_export_status = "manual_export_only"
    elif u_entry.manual_export_supported:
        manual_export_status = "manual_export_supported"
    else:
        manual_export_status = "not_supported"

    # app review status
    if platform_id in ("substack_newsletter", "telegram_remote_operator", "telegram_channel_destination"):
        app_review_status = "not_applicable"
    else:
        perm_row = p_perms[0] if p_perms else None
        if perm_row and any("app_review" in r for r in perm_row.required_app_review_items):
            has_app_rev_block = any("app_review" in b or "audit" in b for b in dec.blocked_reasons)
            if has_app_rev_block:
                app_review_status = "needs_app_review_proof"
            else:
                app_review_status = "app_review_verified"
        else:
            app_review_status = "needs_human_review"

    # 4. Resolve live readiness status and strength
    if preflight_status == "blocked_preflight":
        live_readiness_status = "blocked"
        live_readiness_strength = "deterministic_block"
    elif platform_id == "substack_newsletter":
        live_readiness_status = "manual_only"
        live_readiness_strength = "manual_policy_only"
    elif preflight_status == "needs_human_review":
        live_readiness_status = "needs_human_review"
        live_readiness_strength = "missing_proof"
    elif preflight_status == "dry_run_symbolic_pass":
        live_readiness_status = "symbolic_only"
        live_readiness_strength = "symbolic_local_only"
    else:
        live_readiness_status = "blocked"
        live_readiness_strength = "deterministic_block"

    # 5. Missing proofs and blocked reasons
    blocked_reasons = list(dec.blocked_reasons)
    missing_proofs = list(dec.missing_proofs)

    # Enforce specific blockers
    if platform_id == "x":
        if "rate_limit_and_spend_gate_unresolved" not in blocked_reasons:
            blocked_reasons.append("rate_limit_and_spend_gate_unresolved")
        if "rate_limit_and_spend_gate_unresolved" not in missing_proofs:
            missing_proofs.append("rate_limit_and_spend_gate_unresolved")

    if platform_id == "telegram_remote_operator":
        if "no_arbitrary_dm_allowed" not in blocked_reasons:
            blocked_reasons.append("no_arbitrary_dm_allowed")
        if "operator_inbox_chat_proof_required" not in missing_proofs:
            missing_proofs.append("operator_inbox_chat_proof_required")

    if platform_id == "telegram_channel_destination":
        if "channel_permission_proof_required" not in missing_proofs:
            missing_proofs.append("channel_permission_proof_required")
        if "bot_admin_gate_closed" not in blocked_reasons:
            blocked_reasons.append("bot_admin_gate_closed")

    if platform_id == "substack_newsletter":
        if "manual_export_first_no_api" not in missing_proofs:
            missing_proofs.append("manual_export_first_no_api")

    if platform_id == "linkedin":
        if "linkedin_organization_page_binding_missing" not in missing_proofs:
            missing_proofs.append("linkedin_organization_page_binding_missing")

    if platform_id in ("threads", "instagram", "facebook_page"):
        if "meta_app_review_closed" not in blocked_reasons:
            blocked_reasons.append("meta_app_review_closed")
        if "meta_app_account_proof_required" not in missing_proofs:
            missing_proofs.append("meta_app_account_proof_required")

    if platform_id == "tiktok":
        if "tiktok_audit_closed" not in missing_proofs:
            missing_proofs.append("tiktok_audit_closed")
        if "creator_account_video_publish_proof_required" not in missing_proofs:
            missing_proofs.append("creator_account_video_publish_proof_required")

    if platform_id == "youtube":
        if "quota_upload_gate_closed" not in missing_proofs:
            missing_proofs.append("quota_upload_gate_closed")

    evidence_map = {
        "x": "OAuth 2.0 app review verification, spend gate clearance, and API credential boundary proof",
        "telegram_remote_operator": "Operator inbox chat verification proof and identity verification",
        "telegram_channel_destination": "Bot administrator permissions proof on the destination channel",
        "substack_newsletter": "None (grounded strictly as manual markdown export only)",
        "linkedin": "Member profile identity proof and organization page binding proof",
        "threads": "Meta App Review verification and account integration proof",
        "instagram": "Meta App Review verification, Business account verification, and media URL gate proof",
        "facebook_page": "Meta App Review verification and Page administrator role proof",
        "tiktok": "Developer App Audit approval and creator account publish proof",
        "youtube": "OAuth consent screen approval and upload quota allocation proof",
    }
    next_required_evidence = evidence_map.get(platform_id, "Needs human review of required integration proofs")

    draft = {
        "platform_id": platform_id,
        "platform_role": u_entry.platform_role,
        "account_binding_row_refs": account_binding_row_refs,
        "credential_boundary_refs": credential_boundary_refs,
        "official_docs_refs": official_docs_refs,
        "permission_gate_refs": permission_gate_refs,
        "rate_budget_gate_refs": rate_budget_gate_refs,
        "preflight_decision_refs": preflight_decision_refs,
        "account_binding_status": account_binding_status,
        "credential_boundary_status": credential_boundary_status,
        "official_docs_status": official_docs_status,
        "permission_gate_status": permission_gate_status,
        "app_review_status": app_review_status,
        "rate_budget_status": rate_budget_status,
        "kill_switch_status": kill_switch_status,
        "preflight_status": preflight_status,
        "manual_export_status": manual_export_status,
        "live_readiness_status": live_readiness_status,
        "live_readiness_strength": live_readiness_strength,
        "missing_proofs": tuple(dict.fromkeys(missing_proofs)),
        "blocked_reasons": tuple(dict.fromkeys(blocked_reasons)),
        "next_required_evidence": next_required_evidence,
        "live_read_allowed": False,
        "live_write_allowed": False,
        "env_read_allowed": False,
        "credential_hydrated": False,
        "platform_api_called": False,
        "public_post_allowed": False,
        "readiness_cleared": False,
        "scheduler_enabled": False,
        "browser_session_used": False,
    }

    h_basis = {str(k): _asdict(v) for k, v in draft.items()}
    h = sha256(json.dumps(h_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    return PlatformReadinessEvidenceRow(
        row_id=f"platform_readiness_row_{platform_id}",
        row_hash=h,
        row_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def build_u9_audit_entries(
    rows: tuple[PlatformReadinessEvidenceRow, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UM"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, row in enumerate(rows, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UM",
            source_model_version=MATRIX_VERSION,
            payload={
                "id": row.row_id,
                "platform_id": row.platform_id,
                "status": row.live_readiness_status,
                "source_payload_hash": row.row_hash,
                "evidence_refs": row.account_binding_row_refs + row.credential_boundary_refs + row.official_docs_refs,
                "blocked_reasons": row.blocked_reasons,
                "missing_proofs": row.missing_proofs,
                "safety_flags": {
                    "live_read_allowed": row.live_read_allowed,
                    "live_write_allowed": row.live_write_allowed,
                    "env_read_allowed": row.env_read_allowed,
                    "credential_hydrated": row.credential_hydrated,
                    "platform_api_called": row.platform_api_called,
                    "readiness_cleared": row.readiness_cleared,
                    "public_post_allowed": row.public_post_allowed,
                },
            },
            policy=policy,
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_supervised_live_readiness_review_packet(
    rows: tuple[PlatformReadinessEvidenceRow, ...] | None = None
) -> SupervisedLiveReadinessReviewPacket:
    b_packet = binding.build_platform_account_binding_registry_packet()
    bd_packet = boundary.build_credential_boundary_packet()
    d_packet = docs.build_official_platform_docs_evidence_matrix_packet()
    p_packet = permission.build_platform_permission_scope_app_review_gate_packet()
    r_packet = rate_budget.build_rate_budget_kill_switch_packet()
    pf_packet = preflight.build_preflight_dry_run_request_budget_packet()

    final_rows = rows
    if not final_rows:
        final_rows = tuple(
            build_platform_readiness_row(
                platform_id=pid,
                binding_packet=b_packet,
                boundary_packet=bd_packet,
                docs_packet=d_packet,
                perm_packet=p_packet,
                rate_packet=r_packet,
                preflight_packet=pf_packet,
            )
            for pid in PLATFORM_IDS
        )

    rows_by_platform = {r.platform_id: (r.row_id,) for r in final_rows}

    blocked_count = sum(1 for r in final_rows if r.live_readiness_status == "blocked")
    manual_only_count = sum(1 for r in final_rows if r.live_readiness_status == "manual_only")
    symbolic_only_count = sum(1 for r in final_rows if r.live_readiness_status == "symbolic_only")
    needs_human_review_count = sum(1 for r in final_rows if r.live_readiness_status == "needs_human_review")
    future_live_review_candidate_count = sum(1 for r in final_rows if r.live_readiness_status == "future_live_review_candidate")

    live_read_allowed_count = 0
    live_write_allowed_count = 0
    env_read_allowed_count = 0
    credential_hydrated_count = 0
    platform_api_called_count = 0
    public_post_allowed_count = 0
    readiness_cleared_count = 0
    scheduler_enabled_count = 0
    browser_session_used_count = 0

    all_platforms_blocked_or_manual_or_review = all(
        r.live_readiness_status in ("blocked", "manual_only", "needs_human_review", "symbolic_only")
        for r in final_rows
    )

    global_readiness_status = "not_ready"
    global_blocked_reasons = tuple(dict.fromkeys(reason for r in final_rows for reason in r.blocked_reasons))
    global_missing_proofs = tuple(dict.fromkeys(proof for r in final_rows for proof in r.missing_proofs))

    evidence_refs = tuple(dict.fromkeys(
        ref
        for r in final_rows
        for ref in (list(r.account_binding_row_refs) + list(r.credential_boundary_refs) + list(r.official_docs_refs))
    ))

    audit_entries = build_u9_audit_entries(final_rows)

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
        "readiness_rows": final_rows,
        "rows_by_platform": rows_by_platform,
        "platform_count": len(final_rows),
        "blocked_count": blocked_count,
        "manual_only_count": manual_only_count,
        "symbolic_only_count": symbolic_only_count,
        "needs_human_review_count": needs_human_review_count,
        "future_live_review_candidate_count": future_live_review_candidate_count,
        "live_read_allowed_count": live_read_allowed_count,
        "live_write_allowed_count": live_write_allowed_count,
        "env_read_allowed_count": env_read_allowed_count,
        "credential_hydrated_count": credential_hydrated_count,
        "platform_api_called_count": platform_api_called_count,
        "public_post_allowed_count": public_post_allowed_count,
        "readiness_cleared_count": readiness_cleared_count,
        "scheduler_enabled_count": scheduler_enabled_count,
        "browser_session_used_count": browser_session_used_count,
        "all_platforms_blocked_or_manual_or_review": all_platforms_blocked_or_manual_or_review,
        "global_readiness_status": global_readiness_status,
        "global_blocked_reasons": global_blocked_reasons,
        "global_missing_proofs": global_missing_proofs,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }

    packet_hash = _digest(draft)
    return SupervisedLiveReadinessReviewPacket(
        packet_id="supervised_live_readiness_review_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def render_runbook(packet: SupervisedLiveReadinessReviewPacket) -> str:
    lines = [
        "# Supervised Live Readiness Review Index V0",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- matrix_version: `{packet.matrix_version}`",
        f"- source_baseline_commit: `{packet.source_baseline_commit}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Platform Readiness Decisions Matrix",
        "",
        "| Platform ID | Status | Strength | Binding Status | Boundary Status | Docs Status | Preflight Status | Next Required Evidence |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in packet.readiness_rows:
        lines.append(
            f"| `{row.platform_id}` | `{row.live_readiness_status}` | `{row.live_readiness_strength}` | `{row.account_binding_status}` | `{row.credential_boundary_status}` | `{row.official_docs_status}` | `{row.preflight_status}` | {row.next_required_evidence} |"
        )
    lines.extend([
        "",
        "## Required Distinctions & Enforcements",
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
        "- U9 preflight audit entries compiled under family `supervised_live_readiness_review_future`.",
        "",
        "## Packet Summary",
        "",
        "```json",
        json.dumps({
            "platform_count": packet.platform_count,
            "blocked_count": packet.blocked_count,
            "manual_only_count": packet.manual_only_count,
            "needs_human_review_count": packet.needs_human_review_count,
            "live_read_allowed_count": packet.live_read_allowed_count,
            "live_write_allowed_count": packet.live_write_allowed_count,
            "global_readiness_status": packet.global_readiness_status,
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UM")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_supervised_live_readiness_review_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "PlatformReadinessEvidenceRow",
    "SupervisedLiveReadinessReviewPacket",
    "build_platform_readiness_row",
    "build_supervised_live_readiness_review_packet",
    "build_u9_audit_entries",
    "write_artifacts",
]
