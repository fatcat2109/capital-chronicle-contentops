"""Rate budget and kill-switch matrix contract for ContentOps 0174UK.

Deterministic local-only docs/limits grounding matrix. No live/API/provider/network/env/
credential/browser/scheduler/scraping/DM behavior.
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
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UK_RATE_BUDGET_AND_KILL_SWITCH_MATRIX_V0"
MATRIX_VERSION = "0174UK_RATE_BUDGET_AND_KILL_SWITCH_MATRIX_V1"
SOURCE_BASELINE_COMMIT = "a3d4b82f74fe78a296b24f0a013ab3e8ad85fd4b"
DOC_REL_DIR = Path("docs") / "automation" / "0174UK"
PACKET_FILENAME = "rate_budget_kill_switch_matrix_contract_packet.json"
RUNBOOK_FILENAME = "rate_budget_kill_switch_matrix_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "rate_budget_kill_switch_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UL_PLATFORM_PREFLIGHT_AND_DRY_RUN_REQUEST_BUDGET_CONTRACT_V0"

ALLOWED_DOMAINS = {
    "developer.x.com",
    "docs.x.com",
    "core.telegram.org",
    "support.substack.com",
    "learn.microsoft.com",
    "developers.facebook.com",
    "developers.tiktok.com",
    "developers.google.com",
}

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class RateBudgetRequirement:
    requirement_id: str
    platform_id: str
    requirement_kind: str
    requirement_name: str
    official_doc_ref_id: str
    official_doc_url: str
    official_domain: str
    claim_support_status: str
    exact_numeric_claim: bool
    exact_numeric_claim_has_direct_doc_proof: bool
    budget_or_quota_value_summary: str
    request_budget_default: int
    max_request_budget_allowed: int
    retry_allowed: bool
    auto_retry_allowed: bool
    kill_switch_required: bool
    kill_switch_default_state: str
    timeout_seconds_default: int
    failure_mode: str
    live_read_allowed: bool
    live_write_allowed: bool
    env_read: bool
    credential_hydrated: bool
    platform_api_called: bool
    evidence_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    safety_flags: dict[str, bool]
    requirement_hash: str
    requirement_hash_algorithm: str

    def __post_init__(self) -> None:
        # strict validation on construction: unofficial domains fail closed
        parsed = urlparse(self.official_doc_url)
        host = parsed.netloc.split(":")[0] if parsed.netloc else ""
        if host not in ALLOWED_DOMAINS:
            raise ValueError(f"unofficial_domain_not_allowed: {host}")
        if self.official_domain != host:
            raise ValueError(f"domain_mismatch: {self.official_domain} vs {host}")
        
        # Enforce all safety check counts are strictly False/0
        if (self.live_read_allowed or self.live_write_allowed or 
            self.env_read or self.credential_hydrated or self.platform_api_called):
            raise ValueError("live_credential_api_not_permitted")

        # Enforce zero auto retry
        if self.auto_retry_allowed:
            raise ValueError("auto_retry_not_permitted")


@dataclass(frozen=True)
class PlatformRateBudgetKillSwitchRow:
    row_id: str
    platform_id: str
    platform_role: str
    docs_refs: tuple[str, ...]
    permission_gate_refs: tuple[str, ...]
    rate_budget_requirements: tuple[str, ...]
    endpoint_rate_limit_summary: str
    daily_quota_summary: str
    spend_budget_summary: str
    request_budget_policy_summary: str
    retry_policy_summary: str
    kill_switch_policy_summary: str
    timeout_failure_policy_summary: str
    exact_numeric_claims_present: tuple[str, ...]
    unsupported_numeric_claims: tuple[str, ...]
    row_claim_support_status: str
    gate_status: str
    gate_strength: str
    live_read_allowed: bool
    live_write_allowed: bool
    env_read: bool
    credential_hydrated: bool
    platform_api_called: bool
    readiness_cleared: bool
    public_post_allowed: bool
    retry_allowed: bool
    auto_retry_allowed: bool
    kill_switch_required: bool
    kill_switch_default_state: str
    evidence_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    row_hash: str


@dataclass(frozen=True)
class RateBudgetKillSwitchPacket:
    packet_id: str
    matrix_version: str
    generated_at_epoch: int
    rows: tuple[PlatformRateBudgetKillSwitchRow, ...]
    rows_by_platform: dict[str, tuple[str, ...]]
    requirement_count: int
    platforms_requiring_kill_switch: tuple[str, ...]
    platforms_with_exact_numeric_claims: tuple[str, ...]
    platforms_with_unsupported_numeric_claims: tuple[str, ...]
    manual_export_only_platforms: tuple[str, ...]
    blocked_platforms: tuple[str, ...]
    symbolic_rate_budget_ready_count: int
    live_read_allowed_count: int
    live_write_allowed_count: int
    env_read_count: int
    credential_hydrated_count: int
    platform_api_called_count: int
    readiness_cleared_count: int
    public_post_allowed_count: int
    retry_allowed_count: int
    auto_retry_allowed_count: int
    u9_audit_entry_ids: tuple[str, ...]
    u9_audit_entry_families: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
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
        "retry_allowed", "auto_retry_allowed",
    )
    return {**{flag: False for flag in false_flags}, "local_symbolic_rate_budget_only": True, "review_only": True}


def _requirement_hash_basis(req: RateBudgetRequirement | dict[str, Any]) -> dict[str, Any]:
    data = _asdict(req)
    data.pop("requirement_hash", None)
    data.pop("requirement_hash_algorithm", None)
    return data


def _make_requirement(
    *,
    requirement_id: str,
    platform_id: str,
    requirement_kind: str,
    requirement_name: str,
    official_doc_ref_id: str,
    official_doc_url: str,
    official_domain: str,
    claim_support_status: str,
    exact_numeric_claim: bool,
    exact_numeric_claim_has_direct_doc_proof: bool,
    budget_or_quota_value_summary: str,
    request_budget_default: int,
    max_request_budget_allowed: int,
    retry_allowed: bool,
    auto_retry_allowed: bool,
    kill_switch_required: bool,
    kill_switch_default_state: str,
    timeout_seconds_default: int,
    failure_mode: str,
    evidence_refs: tuple[str, ...],
    blocked_reasons: tuple[str, ...],
) -> RateBudgetRequirement:
    draft = RateBudgetRequirement(
        requirement_id=requirement_id,
        platform_id=platform_id,
        requirement_kind=requirement_kind,
        requirement_name=requirement_name,
        official_doc_ref_id=official_doc_ref_id,
        official_doc_url=official_doc_url,
        official_domain=official_domain,
        claim_support_status=claim_support_status,
        exact_numeric_claim=exact_numeric_claim,
        exact_numeric_claim_has_direct_doc_proof=exact_numeric_claim_has_direct_doc_proof,
        budget_or_quota_value_summary=budget_or_quota_value_summary,
        request_budget_default=request_budget_default,
        max_request_budget_allowed=max_request_budget_allowed,
        retry_allowed=retry_allowed,
        auto_retry_allowed=auto_retry_allowed,
        kill_switch_required=kill_switch_required,
        kill_switch_default_state=kill_switch_default_state,
        timeout_seconds_default=timeout_seconds_default,
        failure_mode=failure_mode,
        live_read_allowed=False,
        live_write_allowed=False,
        env_read=False,
        credential_hydrated=False,
        platform_api_called=False,
        evidence_refs=evidence_refs,
        blocked_reasons=blocked_reasons,
        safety_flags=safety_flags(),
        requirement_hash="",
        requirement_hash_algorithm=HASH_ALGORITHM,
    )
    h = _digest(_requirement_hash_basis(draft))
    return replace(draft, requirement_hash=h)


# Default specifications grounding matrix mapping
_REQ_SPECS = (
    ("req_x_rate_limit", "x", "endpoint_rate_limit", "X Endpoint-Specific Rate Limits and Spend Gate", "doc_evidence_ref_x_limits", "https://developer.x.com/", "developer.x.com", "partially_supported_by_cited_doc", False, False, "Pay-per-use credit-based pricing, endpoint-specific 15-minute rate limit windows", 0, 0, False, False, True, "enabled", 10, "fail_closed_unapproved_budget", ("rate_limit_and_spend_gate_unresolved",)),
    ("req_tg_op_limit", "telegram_remote_operator", "request_budget_policy", "Telegram Remote Operator sendMessage Limit", "doc_evidence_ref_telegram_operator_intro", "https://core.telegram.org/bots/api", "core.telegram.org", "partially_supported_by_cited_doc", False, False, "One-request budget model for supervised remote operator inbox", 0, 1, False, False, True, "enabled", 10, "needs_human_review", ("operator_inbox_chat_proof_required", "no_arbitrary_dm_allowed")),
    ("req_tg_ch_limit", "telegram_channel_destination", "request_budget_policy", "Telegram Channel sendMessage/sendPhoto Limits", "doc_evidence_ref_telegram_channel_send", "https://core.telegram.org/bots/api", "core.telegram.org", "partially_supported_by_cited_doc", False, False, "One-request budget model for channel post sending", 0, 1, False, False, True, "enabled", 10, "needs_human_review", ("channel_permission_proof_required",)),
    ("req_substack_manual", "substack_newsletter", "manual_export_no_api", "Substack Manual Copy-Paste Markdown Export Only", "doc_evidence_ref_substack_help", "https://support.substack.com/", "support.substack.com", "manual_export_no_api", False, False, "No API request budget, manual copy-paste markdown only", 0, 0, False, False, False, "manual_stop_policy", 0, "fail_closed_manual_export_only", ("manual_export_first_no_api",)),
    ("req_linkedin_limit", "linkedin", "endpoint_rate_limit", "LinkedIn Throttling and App Access Constraints", "doc_evidence_ref_linkedin_share", "https://learn.microsoft.com/linkedin/consumer/integrations/self-serve/share-on-linkedin", "learn.microsoft.com", "partially_supported_by_cited_doc", False, False, "Member profile w_member_social rate limits and organization control access page gates", 0, 0, False, False, True, "enabled", 10, "needs_human_review", ("linkedin_organization_page_binding_missing", "rate_budget_unverified")),
    ("req_threads_limit", "threads", "endpoint_rate_limit", "Threads API Publishing Rate Limits", "doc_evidence_ref_threads_overview", "https://developers.facebook.com/docs/threads/", "developers.facebook.com", "partially_supported_by_cited_doc", False, False, "Threads API publishing rate limits and Meta App Review rate ceilings", 0, 0, False, False, True, "enabled", 10, "needs_human_review", ("meta_app_review_closed", "rate_budget_unverified")),
    ("req_instagram_limit", "instagram", "endpoint_rate_limit", "Instagram Graph API Publishing Rate Limits", "doc_evidence_ref_instagram_publish", "https://developers.facebook.com/docs/", "developers.facebook.com", "partially_supported_by_cited_doc", False, False, "Instagram content publishing container rates and creator/business account limits", 0, 0, False, False, True, "enabled", 10, "needs_human_review", ("instagram_content_publish_gate_closed", "rate_budget_unverified")),
    ("req_fb_limit", "facebook_page", "endpoint_rate_limit", "Facebook Graph API Page Posting Rate Limits", "doc_evidence_ref_facebook_page_publish", "https://developers.facebook.com/docs/", "developers.facebook.com", "partially_supported_by_cited_doc", False, False, "Facebook Page posting scopes rate limitations and App Review thresholds", 0, 0, False, False, True, "enabled", 10, "needs_human_review", ("pages_manage_posts_gate_closed", "rate_budget_unverified")),
    ("req_tiktok_limit", "tiktok", "endpoint_rate_limit", "TikTok Content Posting API Quotas", "doc_evidence_ref_tiktok_posting", "https://developers.tiktok.com/doc/content-posting-api-get-started/", "developers.tiktok.com", "partially_supported_by_cited_doc", False, False, "TikTok Content Posting API video upload and post publish constraints", 0, 0, False, False, True, "enabled", 10, "needs_human_review", ("tiktok_audit_closed", "rate_budget_unverified")),
    ("req_yt_upload_quota", "youtube", "media_upload_quota", "YouTube videos.insert Quota Limits Wording", "doc_evidence_ref_youtube_insert", "https://developers.google.com/youtube/v3/docs/videos/insert", "developers.google.com", "supported_by_cited_doc", True, True, "videos.insert supports media upload, 100 calls per day daily limit, cost 1 unit in Video Uploads bucket, 256GB max size", 0, 1, False, False, True, "enabled", 10, "fail_closed_unapproved_budget", ("quota_upload_gate_closed",)),
)


def build_default_requirements() -> tuple[RateBudgetRequirement, ...]:
    reqs = []
    for rid, pid, kind, name, doc_ref, url, domain, status, exact_num, has_proof, summary, req_def, max_req, ret, autoret, ks, ks_state, to, fail, blockers in _REQ_SPECS:
        evidence = (
            "docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",
            f"evidence_rate_budget_spec:{pid}:{rid}"
        )
        reqs.append(
            _make_requirement(
                requirement_id=rid,
                platform_id=pid,
                requirement_kind=kind,
                requirement_name=name,
                official_doc_ref_id=doc_ref,
                official_doc_url=url,
                official_domain=domain,
                claim_support_status=status,
                exact_numeric_claim=exact_num,
                exact_numeric_claim_has_direct_doc_proof=has_proof,
                budget_or_quota_value_summary=summary,
                request_budget_default=req_def,
                max_request_budget_allowed=max_req,
                retry_allowed=ret,
                auto_retry_allowed=autoret,
                kill_switch_required=ks,
                kill_switch_default_state=ks_state,
                timeout_seconds_default=to,
                failure_mode=fail,
                evidence_refs=evidence,
                blocked_reasons=tuple(blockers),
            )
        )
    return tuple(reqs)


def _row_hash_basis(row: PlatformRateBudgetKillSwitchRow | dict[str, Any]) -> dict[str, Any]:
    data = _asdict(row)
    data.pop("row_hash", None)
    return data


def _make_row(
    *,
    row_id: str,
    platform_id: str,
    platform_role: str,
    docs_refs: tuple[str, ...],
    permission_gate_refs: tuple[str, ...],
    rate_budget_requirements: tuple[str, ...],
    endpoint_rate_limit_summary: str,
    daily_quota_summary: str,
    spend_budget_summary: str,
    request_budget_policy_summary: str,
    retry_policy_summary: str,
    kill_switch_policy_summary: str,
    timeout_failure_policy_summary: str,
    exact_numeric_claims_present: tuple[str, ...],
    unsupported_numeric_claims: tuple[str, ...],
    row_claim_support_status: str,
    gate_status: str,
    gate_strength: str,
    retry_allowed: bool,
    auto_retry_allowed: bool,
    kill_switch_required: bool,
    kill_switch_default_state: str,
    evidence_refs: tuple[str, ...],
    blocked_reasons: tuple[str, ...],
) -> PlatformRateBudgetKillSwitchRow:
    draft = PlatformRateBudgetKillSwitchRow(
        row_id=row_id,
        platform_id=platform_id,
        platform_role=platform_role,
        docs_refs=docs_refs,
        permission_gate_refs=permission_gate_refs,
        rate_budget_requirements=rate_budget_requirements,
        endpoint_rate_limit_summary=endpoint_rate_limit_summary,
        daily_quota_summary=daily_quota_summary,
        spend_budget_summary=spend_budget_summary,
        request_budget_policy_summary=request_budget_policy_summary,
        retry_policy_summary=retry_policy_summary,
        kill_switch_policy_summary=kill_switch_policy_summary,
        timeout_failure_policy_summary=timeout_failure_policy_summary,
        exact_numeric_claims_present=exact_numeric_claims_present,
        unsupported_numeric_claims=unsupported_numeric_claims,
        row_claim_support_status=row_claim_support_status,
        gate_status=gate_status,
        gate_strength=gate_strength,
        live_read_allowed=False,
        live_write_allowed=False,
        env_read=False,
        credential_hydrated=False,
        platform_api_called=False,
        readiness_cleared=False,
        public_post_allowed=False,
        retry_allowed=retry_allowed,
        auto_retry_allowed=auto_retry_allowed,
        kill_switch_required=kill_switch_required,
        kill_switch_default_state=kill_switch_default_state,
        evidence_refs=evidence_refs,
        blocked_reasons=blocked_reasons,
        row_hash="",
    )
    h = _digest(_row_hash_basis(draft))
    return replace(draft, row_hash=h)


def build_default_rows(
    requirements: tuple[RateBudgetRequirement, ...] | None = None
) -> tuple[PlatformRateBudgetKillSwitchRow, ...]:
    reqs = requirements or build_default_requirements()
    
    # Retrieve dependency registry packets to align IDs
    docs_packet = docs.build_official_platform_docs_evidence_matrix_packet()
    doc_refs = docs_packet.docs_rows
    
    perm_packet = permission.build_platform_permission_scope_app_review_gate_packet()
    perm_rows = perm_packet.permission_gate_rows
    
    rows = []
    for plat in universe.PLATFORMS:
        pid = plat.platform_id
        
        # Link references
        plat_docs = tuple(d.row_id for d in doc_refs if d.platform_id == pid)
        plat_perms = tuple(p.row_id for p in perm_rows if p.platform_id == pid)
        
        # Filter requirements
        plat_reqs = tuple(r for r in reqs if r.platform_id == pid)
        plat_req_ids = tuple(r.requirement_id for r in plat_reqs)
        
        # Aggregate properties
        exact_numeric = tuple(r.requirement_id for r in plat_reqs if r.exact_numeric_claim)
        unsupported_numeric = tuple(
            r.requirement_id for r in plat_reqs 
            if r.exact_numeric_claim and not r.exact_numeric_claim_has_direct_doc_proof
        )
        
        rate_limits = [r.budget_or_quota_value_summary for r in plat_reqs if r.requirement_kind == "endpoint_rate_limit"]
        daily_quotas = [r.budget_or_quota_value_summary for r in plat_reqs if r.requirement_kind in ("daily_quota", "media_upload_quota")]
        spend_budgets = [r.budget_or_quota_value_summary for r in plat_reqs if r.requirement_kind == "pay_per_use_budget"]
        request_policies = [r.budget_or_quota_value_summary for r in plat_reqs if r.requirement_kind in ("request_budget_policy", "manual_export_no_api")]
        retries = [f"retry={r.retry_allowed}, autoretry={r.auto_retry_allowed}" for r in plat_reqs]
        kill_switches = [f"required={r.kill_switch_required}, default={r.kill_switch_default_state}" for r in plat_reqs]
        timeouts = [f"timeout={r.timeout_seconds_default}s, fail={r.failure_mode}" for r in plat_reqs]
        
        # Set support status
        if unsupported_numeric:
            row_claim_status = "unsupported_by_cited_doc"
        elif any(r.claim_support_status == "not_verified_current_docs" for r in plat_reqs):
            row_claim_status = "not_verified_current_docs"
        elif any(r.claim_support_status == "partially_supported_by_cited_doc" for r in plat_reqs):
            row_claim_status = "partially_supported_by_cited_doc"
        elif any(r.claim_support_status == "manual_export_no_api" for r in plat_reqs):
            row_claim_status = "manual_export_no_api"
        else:
            row_claim_status = "supported_by_cited_doc"

        # Gate status and strength
        has_blocked = any(r.claim_support_status == "unsupported_by_cited_doc" for r in plat_reqs)
        has_manual = any(r.claim_support_status == "manual_export_no_api" for r in plat_reqs)
        has_needs_review = any(r.claim_support_status == "not_verified_current_docs" for r in plat_reqs) or bool(unsupported_numeric)
        
        if pid == "substack_newsletter" or has_manual:
            gate_status = "manual_export_no_api"
            gate_strength = "weak_manual_policy"
        elif has_blocked or bool(unsupported_numeric):
            gate_status = "rate_budget_gate_blocked"
            gate_strength = "blocked"
        elif has_needs_review or any(r.claim_support_status == "partially_supported_by_cited_doc" for r in plat_reqs):
            gate_status = "needs_human_review"
            gate_strength = "partial_official_docs"
        else:
            gate_status = "symbolic_rate_budget_ready"
            gate_strength = "strong_official_docs"
            
        # Check defaults for retry and kill switches
        row_retry = any(r.retry_allowed for r in plat_reqs)
        row_autoret = any(r.auto_retry_allowed for r in plat_reqs)
        row_ks_req = any(r.kill_switch_required for r in plat_reqs)
        row_ks_state = plat_reqs[0].kill_switch_default_state if plat_reqs else "disabled"
        
        evidence = (
            "docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",
            f"rate_budget_gate_row_spec:{pid}"
        )
        
        blockers = []
        for r in plat_reqs:
            blockers.extend(r.blocked_reasons)
        if pid == "x":
            blockers.append("rate_limit_and_spend_gate_unresolved")
        if bool(unsupported_numeric):
            blockers.append("unsupported_numeric_claims_present")
        if not blockers:
            blockers.append("rate_budget_matrix_not_finalized")
            
        rows.append(
            _make_row(
                row_id=f"platform_rate_budget_gate_row_{pid}",
                platform_id=pid,
                platform_role=plat.platform_role,
                docs_refs=plat_docs,
                permission_gate_refs=plat_perms,
                rate_budget_requirements=plat_req_ids,
                endpoint_rate_limit_summary=", ".join(rate_limits) or "N/A",
                daily_quota_summary=", ".join(daily_quotas) or "N/A",
                spend_budget_summary=", ".join(spend_budgets) or "N/A",
                request_budget_policy_summary=", ".join(request_policies) or "N/A",
                retry_policy_summary=", ".join(retries) or "N/A",
                kill_switch_policy_summary=", ".join(kill_switches) or "N/A",
                timeout_failure_policy_summary=", ".join(timeouts) or "N/A",
                exact_numeric_claims_present=exact_numeric,
                unsupported_numeric_claims=unsupported_numeric,
                row_claim_support_status=row_claim_status,
                gate_status=gate_status,
                gate_strength=gate_strength,
                retry_allowed=row_retry,
                auto_retry_allowed=row_autoret,
                kill_switch_required=row_ks_req,
                kill_switch_default_state=row_ks_state,
                evidence_refs=evidence,
                blocked_reasons=tuple(dict.fromkeys(blockers)),
            )
        )
    return tuple(rows)


def build_u9_audit_entries(
    packet_or_rows: RateBudgetKillSwitchPacket | tuple[PlatformRateBudgetKillSwitchRow, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    rows = packet_or_rows.rows if hasattr(packet_or_rows, "rows") else packet_or_rows
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UK"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, row in enumerate(rows, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UK",
            source_model_version=MATRIX_VERSION,
            payload={
                "id": row.row_id,
                "platform_id": row.platform_id,
                "status": row.gate_status,
                "source_payload_hash": row.row_hash,
                "evidence_refs": row.evidence_refs,
                "blocked_reasons": row.blocked_reasons,
                "safety_flags": {
                    "live_read_allowed": row.live_read_allowed,
                    "live_write_allowed": row.live_write_allowed,
                    "env_read": row.env_read,
                    "credential_hydrated": row.credential_hydrated,
                    "platform_api_called": row.platform_api_called,
                    "readiness_cleared": row.readiness_cleared,
                    "public_post_allowed": row.public_post_allowed,
                    "retry_allowed": row.retry_allowed,
                    "auto_retry_allowed": row.auto_retry_allowed,
                },
            },
            policy=policy,
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_rate_budget_kill_switch_packet(
    requirements: tuple[RateBudgetRequirement, ...] | None = None,
    rows: tuple[PlatformRateBudgetKillSwitchRow, ...] | None = None
) -> RateBudgetKillSwitchPacket:
    plat_reqs = requirements or build_default_requirements()
    plat_rows = rows or build_default_rows(plat_reqs)
    
    rows_by_platform = {pid: tuple(r.row_id for r in plat_rows if r.platform_id == pid) for pid in PLATFORM_IDS}
    
    ks_platforms = _unique(r.platform_id for r in plat_reqs if r.kill_switch_required)
    exact_num_platforms = _unique(r.platform_id for r in plat_reqs if r.exact_numeric_claim)
    unsupported_num_platforms = _unique(
        r.platform_id for r in plat_reqs 
        if r.exact_numeric_claim and not r.exact_numeric_claim_has_direct_doc_proof
    )
    manual_platforms = _unique(r.platform_id for r in plat_reqs if r.claim_support_status == "manual_export_no_api")
    blocked_platforms = _unique(r.platform_id for r in plat_rows if r.gate_status == "rate_budget_gate_blocked")
    
    symbolic_ready_count = sum(1 for r in plat_rows if r.gate_status == "symbolic_rate_budget_ready")
    
    evidence_refs = _unique(ref for r in plat_rows for ref in r.evidence_refs)
    blockers = _unique(reason for r in plat_rows for reason in r.blocked_reasons)
    
    audit_entries = build_u9_audit_entries(plat_rows)
    
    draft = {
        "matrix_version": MATRIX_VERSION,
        "generated_at_epoch": 0,
        "rows": plat_rows,
        "rows_by_platform": rows_by_platform,
        "requirement_count": len(plat_reqs),
        "platforms_requiring_kill_switch": ks_platforms,
        "platforms_with_exact_numeric_claims": exact_num_platforms,
        "platforms_with_unsupported_numeric_claims": unsupported_num_platforms,
        "manual_export_only_platforms": manual_platforms,
        "blocked_platforms": blocked_platforms,
        "symbolic_rate_budget_ready_count": symbolic_ready_count,
        "live_read_allowed_count": 0,
        "live_write_allowed_count": 0,
        "env_read_count": 0,
        "credential_hydrated_count": 0,
        "platform_api_called_count": 0,
        "readiness_cleared_count": 0,
        "public_post_allowed_count": 0,
        "retry_allowed_count": 0,
        "auto_retry_allowed_count": 0,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags(),
        "blocked_reasons": blockers,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    
    packet_hash = _digest(draft)
    
    return RateBudgetKillSwitchPacket(
        packet_id="rate_budget_kill_switch_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def matrix_checksum() -> str:
    return build_rate_budget_kill_switch_packet().packet_hash


def render_runbook(packet: RateBudgetKillSwitchPacket) -> str:
    lines = [
        "# 0174UK Rate Budget & Kill Switch Matrix V0",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- matrix_version: `{packet.matrix_version}`",
        f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Rate Limit, Quota & Kill Switch Matrix",
        "",
        "| Platform ID | Role | Gate Status | Strength | Kill Switch Required | Retry Allowed | Auto-Retry | Blockers |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in packet.rows:
        blockers = ", ".join(row.blocked_reasons[:3])
        lines.append(
            f"| `{row.platform_id}` | `{row.platform_role}` | `{row.gate_status}` | `{row.gate_strength}` | `{row.kill_switch_required}` | `{row.retry_allowed}` | `{row.auto_retry_allowed}` | `{blockers}` |"
        )
        
    lines.extend([
        "",
        "## Required Distinctions & Caveats",
        "",
        "- **X**: Credit-budget pay-per-use caveat and endpoint-specific 15-minute rate limit windows.",
        "- **Telegram Bot (Remote Operator & Channel)**: Restricted message limits with one-request budget models. Operator separate from Channel posting. Zero arbitrary DM access.",
        "- **Substack**: Grounded strictly as manual copy-paste markdown export without API request budgets.",
        "- **LinkedIn/Meta/TikTok**: Throttling, container publication limitations, and Meta app review rate caps. All are blocked or pending review.",
        "- **YouTube**: Direct doc-grounded videos.insert quota limit (100 calls/day, 1 unit cost) without any stale quota claims.",
        "",
        "## Safety Enforcements",
        "",
        "- All live read/write/posting and env/credential access flags are strictly false.",
        "- `auto_retry_allowed` is false for all platforms.",
        "- `kill_switch_required` is true for all API-capable platforms.",
        "- U9 audit entry family: `rate_budget_kill_switch_future`.",
        "- Unofficial domain references fail closed on construction.",
        "",
        "## Packet Summary",
        "",
        "```json",
        json.dumps({
            "requirement_count": packet.requirement_count,
            "blocked_platforms": packet.blocked_platforms,
            "manual_export_only_platforms": packet.manual_export_only_platforms,
            "platforms_requiring_kill_switch": packet.platforms_requiring_kill_switch,
            "platforms_with_exact_numeric_claims": packet.platforms_with_exact_numeric_claims,
            "platforms_with_unsupported_numeric_claims": packet.platforms_with_unsupported_numeric_claims,
            "live_read_allowed_count": packet.live_read_allowed_count,
            "live_write_allowed_count": packet.live_write_allowed_count,
            "auto_retry_allowed_count": packet.auto_retry_allowed_count,
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UK")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_rate_budget_kill_switch_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "RateBudgetRequirement",
    "PlatformRateBudgetKillSwitchRow",
    "RateBudgetKillSwitchPacket",
    "build_default_requirements",
    "build_default_rows",
    "build_u9_audit_entries",
    "build_rate_budget_kill_switch_packet",
    "matrix_checksum",
    "write_artifacts",
]
