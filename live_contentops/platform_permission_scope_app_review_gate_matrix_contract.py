"""Platform permission scope and app review gate matrix contract for ContentOps 0174UJ.

Deterministic local-only docs grounding matrix. No live/API/provider/network/env/
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
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UJ_PLATFORM_PERMISSION_SCOPE_AND_APP_REVIEW_GATE_MATRIX_V0"
MATRIX_VERSION = "0174UJ_PLATFORM_PERMISSION_SCOPE_AND_APP_REVIEW_GATE_MATRIX_V1"
SOURCE_BASELINE_COMMIT = "af770408b50734d1efd11aa526c1102c92a6903a"
DOC_REL_DIR = Path("docs") / "automation" / "0174UJ"
PACKET_FILENAME = "platform_permission_scope_app_review_gate_matrix_contract_packet.json"
RUNBOOK_FILENAME = "platform_permission_scope_app_review_gate_matrix_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "permission_scope_gate_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UK_RATE_BUDGET_AND_KILL_SWITCH_MATRIX_V0"

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
class PermissionScopeRequirement:
    requirement_id: str
    platform_id: str
    requirement_kind: str
    requirement_name: str
    official_doc_ref_id: str
    official_doc_url: str
    official_domain: str
    permission_status: str
    app_review_required: bool
    account_role_proof_required: bool
    credential_required_future: bool
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


@dataclass(frozen=True)
class PlatformPermissionGateRow:
    row_id: str
    platform_id: str
    platform_role: str
    account_binding_refs: tuple[str, ...]
    credential_handle_refs: tuple[str, ...]
    official_docs_refs: tuple[str, ...]
    permission_requirements: tuple[str, ...]
    required_oauth_scopes: tuple[str, ...]
    required_bot_permissions: tuple[str, ...]
    required_admin_roles: tuple[str, ...]
    required_app_review_items: tuple[str, ...]
    required_account_type_proofs: tuple[str, ...]
    manual_export_constraints: tuple[str, ...]
    gate_status: str
    gate_strength: str
    live_read_allowed: bool
    live_write_allowed: bool
    env_read: bool
    credential_hydrated: bool
    platform_api_called: bool
    readiness_cleared: bool
    public_post_allowed: bool
    evidence_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    row_hash: str


@dataclass(frozen=True)
class PlatformPermissionScopeAppReviewGatePacket:
    packet_id: str
    matrix_version: str
    generated_at_epoch: int
    permission_gate_rows: tuple[PlatformPermissionGateRow, ...]
    rows_by_platform: dict[str, tuple[str, ...]]
    permission_requirement_count: int
    app_review_required_platforms: tuple[str, ...]
    account_role_proof_required_platforms: tuple[str, ...]
    manual_export_only_platforms: tuple[str, ...]
    blocked_platforms: tuple[str, ...]
    symbolic_permission_matrix_ready_count: int
    live_read_allowed_count: int
    live_write_allowed_count: int
    env_read_count: int
    credential_hydrated_count: int
    platform_api_called_count: int
    readiness_cleared_count: int
    public_post_allowed_count: int
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
    )
    return {**{flag: False for flag in false_flags}, "local_symbolic_permissions_only": True, "review_only": True}


def _requirement_hash_basis(req: PermissionScopeRequirement | dict[str, Any]) -> dict[str, Any]:
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
    permission_status: str,
    app_review_required: bool,
    account_role_proof_required: bool,
    credential_required_future: bool,
    evidence_refs: tuple[str, ...],
    blocked_reasons: tuple[str, ...],
) -> PermissionScopeRequirement:
    draft = PermissionScopeRequirement(
        requirement_id=requirement_id,
        platform_id=platform_id,
        requirement_kind=requirement_kind,
        requirement_name=requirement_name,
        official_doc_ref_id=official_doc_ref_id,
        official_doc_url=official_doc_url,
        official_domain=official_domain,
        permission_status=permission_status,
        app_review_required=app_review_required,
        account_role_proof_required=account_role_proof_required,
        credential_required_future=credential_required_future,
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


# Raw specifications for default requirements
_REQ_SPECS = (
    ("req_x_oauth", "x", "oauth_scope", "X OAuth 2.0 Scopes (tweet.read, tweet.write, users.read, offline.access)", "doc_evidence_ref_x_v2", "https://developer.x.com/en/docs/authentication/oauth-2-0/authorization-code-flow-with-pkce", "developer.x.com", "official_doc_supported", True, False, True, ("rate_limit_and_spend_gate_unresolved",)),
    ("req_x_app_access", "x", "app_review_permission", "Developer Portal App Access Verification", "doc_evidence_ref_x_limits", "https://developer.x.com/", "developer.x.com", "needs_human_review", True, False, True, ("x_api_gate_closed",)),
    ("req_tg_op_send", "telegram_remote_operator", "bot_permission", "Telegram Bot sendMessage to Operator", "doc_evidence_ref_telegram_operator_intro", "https://core.telegram.org/bots/api", "core.telegram.org", "official_doc_supported", False, True, True, ("operator_inbox_chat_proof_required",)),
    ("req_tg_op_proof", "telegram_remote_operator", "human_review_gate", "Operator Identity Proof Verification", "doc_evidence_ref_telegram_operator_intro", "https://core.telegram.org/bots/api", "core.telegram.org", "needs_human_review", False, True, False, ("not_public_destination",)),
    ("req_tg_ch_send", "telegram_channel_destination", "bot_permission", "Telegram Bot sendMessage/sendPhoto to Channel", "doc_evidence_ref_telegram_channel_send", "https://core.telegram.org/bots/api", "core.telegram.org", "official_doc_supported", False, True, True, ("channel_permission_proof_required",)),
    ("req_tg_ch_admin", "telegram_channel_destination", "channel_admin_permission", "Telegram Bot Administrator Role on Destination Channel", "doc_evidence_ref_telegram_channel_send", "https://core.telegram.org/bots/api", "core.telegram.org", "official_doc_supported", False, True, True, ("bot_admin_gate_closed",)),
    ("req_substack_manual", "substack_newsletter", "manual_export_policy", "Substack Manual Copy-Paste Markdown Export Only", "doc_evidence_ref_substack_help", "https://support.substack.com/", "support.substack.com", "manual_export_no_api", False, False, False, ("manual_export_first_no_api",)),
    ("req_li_member", "linkedin", "oauth_scope", "LinkedIn w_member_social Scope for Personal Profile", "doc_evidence_ref_linkedin_share", "https://learn.microsoft.com/linkedin/consumer/integrations/self-serve/share-on-linkedin", "learn.microsoft.com", "official_doc_supported", True, False, True, ("linkedin_member_profile_proof_required",)),
    ("req_li_org_admin", "linkedin", "page_admin_role", "LinkedIn w_organization_social and Page Administrator Proof", "doc_evidence_ref_linkedin_share", "https://learn.microsoft.com/linkedin/shared/references/v2/organizational-access-control", "learn.microsoft.com", "blocked", True, True, True, ("linkedin_organization_page_binding_missing", "organization_page_proof_required")),
    ("req_threads_scopes", "threads", "oauth_scope", "Threads API Publishing Scopes (threads_basic, threads_content_publish)", "doc_evidence_ref_threads_overview", "https://developers.facebook.com/docs/threads/", "developers.facebook.com", "official_doc_supported", True, False, True, ("meta_app_review_closed",)),
    ("req_threads_review", "threads", "app_review_permission", "Meta App Review Verification for Threads Integration", "doc_evidence_ref_threads_overview", "https://developers.facebook.com/docs/threads/", "developers.facebook.com", "needs_human_review", True, False, True, ("meta_app_account_proof_required",)),
    ("req_insta_scopes", "instagram", "oauth_scope", "Instagram API Content Publish Scopes (instagram_basic, instagram_content_publish, pages_show_list)", "doc_evidence_ref_instagram_publish", "https://developers.facebook.com/docs/", "developers.facebook.com", "official_doc_supported", True, True, True, ("instagram_content_publish_gate_closed",)),
    ("req_insta_type", "instagram", "account_type_requirement", "Instagram Professional/Business/Creator Account Verification", "doc_evidence_ref_instagram_publish", "https://developers.facebook.com/docs/", "developers.facebook.com", "needs_human_review", True, True, True, ("instagram_business_creator_proof_required", "media_url_gate_closed")),
    ("req_fb_scopes", "facebook_page", "oauth_scope", "Facebook Page Posting Scopes (pages_read_engagement, pages_manage_posts, pages_show_list)", "doc_evidence_ref_facebook_page_publish", "https://developers.facebook.com/docs/", "developers.facebook.com", "official_doc_supported", True, True, True, ("pages_manage_posts_gate_closed",)),
    ("req_fb_admin", "facebook_page", "page_admin_role", "Facebook Page Administrator Role", "doc_evidence_ref_facebook_page_publish", "https://developers.facebook.com/docs/", "developers.facebook.com", "needs_human_review", True, True, True, ("facebook_page_role_proof_required", "app_review_gate_closed")),
    ("req_tiktok_scopes", "tiktok", "oauth_scope", "TikTok Content Posting Scopes (user.info.basic, video.upload, video.publish)", "doc_evidence_ref_tiktok_posting", "https://developers.tiktok.com/doc/content-posting-api-get-started/", "developers.tiktok.com", "official_doc_supported", True, True, True, ("later_video_gate_closed",)),
    ("req_tiktok_audit", "tiktok", "app_review_permission", "TikTok Developer App Audit and Review", "doc_evidence_ref_tiktok_posting", "https://developers.tiktok.com/doc/content-posting-api-get-started/", "developers.tiktok.com", "blocked", True, True, True, ("creator_account_video_publish_proof_required", "tiktok_audit_closed")),
    ("req_yt_scopes", "youtube", "oauth_scope", "YouTube Data API v3 upload and readonly (youtube.upload, youtube.readonly)", "doc_evidence_ref_youtube_insert", "https://developers.google.com/youtube/v3/docs/videos/insert", "developers.google.com", "official_doc_supported", True, True, True, ("quota_upload_gate_closed",)),
    ("req_yt_consent", "youtube", "app_review_permission", "Google App OAuth Consent Screen and Verification", "doc_evidence_ref_youtube_insert", "https://developers.google.com/youtube/v3/docs/videos/insert", "developers.google.com", "needs_human_review", True, True, True, ("youtube_oauth_channel_proof_required", "later_video_gate_closed")),
)


def build_default_requirements() -> tuple[PermissionScopeRequirement, ...]:
    reqs = []
    for rid, pid, kind, name, doc_ref, url, domain, status, app_rev, role_proof, cred_req, blockers in _REQ_SPECS:
        evidence = (
            "docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",
            f"evidence_requirement_spec:{pid}:{rid}"
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
                permission_status=status,
                app_review_required=app_rev,
                account_role_proof_required=role_proof,
                credential_required_future=cred_req,
                evidence_refs=evidence,
                blocked_reasons=tuple(blockers),
            )
        )
    return tuple(reqs)


def _row_hash_basis(row: PlatformPermissionGateRow | dict[str, Any]) -> dict[str, Any]:
    data = _asdict(row)
    data.pop("row_hash", None)
    return data


def _make_row(
    *,
    row_id: str,
    platform_id: str,
    platform_role: str,
    account_binding_refs: tuple[str, ...],
    credential_handle_refs: tuple[str, ...],
    official_docs_refs: tuple[str, ...],
    permission_requirements: tuple[str, ...],
    required_oauth_scopes: tuple[str, ...],
    required_bot_permissions: tuple[str, ...],
    required_admin_roles: tuple[str, ...],
    required_app_review_items: tuple[str, ...],
    required_account_type_proofs: tuple[str, ...],
    manual_export_constraints: tuple[str, ...],
    gate_status: str,
    gate_strength: str,
    evidence_refs: tuple[str, ...],
    blocked_reasons: tuple[str, ...],
) -> PlatformPermissionGateRow:
    draft = PlatformPermissionGateRow(
        row_id=row_id,
        platform_id=platform_id,
        platform_role=platform_role,
        account_binding_refs=account_binding_refs,
        credential_handle_refs=credential_handle_refs,
        official_docs_refs=official_docs_refs,
        permission_requirements=permission_requirements,
        required_oauth_scopes=required_oauth_scopes,
        required_bot_permissions=required_bot_permissions,
        required_admin_roles=required_admin_roles,
        required_app_review_items=required_app_review_items,
        required_account_type_proofs=required_account_type_proofs,
        manual_export_constraints=manual_export_constraints,
        gate_status=gate_status,
        gate_strength=gate_strength,
        live_read_allowed=False,
        live_write_allowed=False,
        env_read=False,
        credential_hydrated=False,
        platform_api_called=False,
        readiness_cleared=False,
        public_post_allowed=False,
        evidence_refs=evidence_refs,
        blocked_reasons=blocked_reasons,
        row_hash="",
    )
    h = _digest(_row_hash_basis(draft))
    return replace(draft, row_hash=h)


def build_default_rows(
    requirements: tuple[PermissionScopeRequirement, ...] | None = None
) -> tuple[PlatformPermissionGateRow, ...]:
    reqs = requirements or build_default_requirements()
    
    # Retrieve dependencies from prior registries to align IDs
    binding_packet = binding.build_platform_account_binding_registry_packet()
    bindings = binding_packet.bindings
    
    boundary_packet = boundary.build_credential_boundary_packet()
    handles = boundary_packet.credential_handles
    
    docs_packet = docs.build_official_platform_docs_evidence_matrix_packet()
    doc_refs = docs_packet.docs_rows
    
    rows = []
    for plat in universe.PLATFORMS:
        pid = plat.platform_id
        
        # Link references
        plat_bindings = tuple(b.binding_id for b in bindings if b.platform_id == pid)
        plat_handles = tuple(h.credential_handle_id for h in handles if h.platform_id == pid)
        plat_docs = tuple(d.row_id for d in doc_refs if d.platform_id == pid)
        
        # Filter requirements
        plat_reqs = tuple(r for r in reqs if r.platform_id == pid)
        plat_req_ids = tuple(r.requirement_id for r in plat_reqs)
        
        # Aggregate scopes and sub-items
        oauth_scopes = tuple(r.requirement_name for r in plat_reqs if r.requirement_kind == "oauth_scope")
        bot_perms = tuple(r.requirement_name for r in plat_reqs if r.requirement_kind == "bot_permission")
        admin_roles = tuple(
            r.requirement_name for r in plat_reqs if r.requirement_kind in ("channel_admin_permission", "page_admin_role")
        )
        app_reviews = tuple(r.requirement_name for r in plat_reqs if r.requirement_kind == "app_review_permission")
        account_proofs = tuple(r.requirement_name for r in plat_reqs if r.requirement_kind == "account_type_requirement")
        manual_exports = tuple(r.requirement_name for r in plat_reqs if r.requirement_kind == "manual_export_policy")
        
        # Compute status and strength
        has_blocked = any(r.permission_status == "blocked" for r in plat_reqs)
        has_needs_review = any(r.permission_status == "needs_human_review" for r in plat_reqs)
        has_manual = any(r.permission_status == "manual_export_no_api" for r in plat_reqs)
        
        if pid == "substack_newsletter" or has_manual:
            gate_status = "blocked_manual_export_only"
            gate_strength = "weak_manual_policy"
        elif has_blocked:
            gate_status = "blocked_missing_permission_scope_matrix"
            gate_strength = "blocked"
        elif has_needs_review:
            gate_status = "needs_human_review"
            gate_strength = "partial_official_docs"
        else:
            gate_status = "symbolic_permission_matrix_ready"
            gate_strength = "strong_official_docs"
            
        evidence = (
            "docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",
            f"permission_gate_row_spec:{pid}"
        )
        
        # Blocker Reasons
        blockers = []
        for r in plat_reqs:
            blockers.extend(r.blocked_reasons)
        if pid == "x":
            blockers.append("rate_limit_and_spend_gate_unresolved")
        if not blockers:
            blockers.append("permission_gate_matrix_not_finalized")
        
        rows.append(
            _make_row(
                row_id=f"platform_permission_gate_row_{pid}",
                platform_id=pid,
                platform_role=plat.platform_role,
                account_binding_refs=plat_bindings,
                credential_handle_refs=plat_handles,
                official_docs_refs=plat_docs,
                permission_requirements=plat_req_ids,
                required_oauth_scopes=oauth_scopes,
                required_bot_permissions=bot_perms,
                required_admin_roles=admin_roles,
                required_app_review_items=app_reviews,
                required_account_type_proofs=account_proofs,
                manual_export_constraints=manual_exports,
                gate_status=gate_status,
                gate_strength=gate_strength,
                evidence_refs=evidence,
                blocked_reasons=tuple(dict.fromkeys(blockers)),
            )
        )
    return tuple(rows)


def build_u9_audit_entries(
    packet_or_rows: PlatformPermissionScopeAppReviewGatePacket | tuple[PlatformPermissionGateRow, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    rows = packet_or_rows.permission_gate_rows if hasattr(packet_or_rows, "permission_gate_rows") else packet_or_rows
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UJ"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, row in enumerate(rows, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UJ",
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
                },
            },
            policy=policy,
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_platform_permission_scope_app_review_gate_packet(
    requirements: tuple[PermissionScopeRequirement, ...] | None = None,
    rows: tuple[PlatformPermissionGateRow, ...] | None = None
) -> PlatformPermissionScopeAppReviewGatePacket:
    plat_reqs = requirements or build_default_requirements()
    plat_rows = rows or build_default_rows(plat_reqs)
    
    rows_by_platform = {pid: tuple(r.row_id for r in plat_rows if r.platform_id == pid) for pid in PLATFORM_IDS}
    
    app_review_platforms = _unique(r.platform_id for r in plat_reqs if r.app_review_required)
    account_role_platforms = _unique(r.platform_id for r in plat_reqs if r.account_role_proof_required)
    manual_export_platforms = _unique(r.platform_id for r in plat_reqs if r.permission_status == "manual_export_no_api")
    blocked_platforms = _unique(r.platform_id for r in plat_reqs if r.permission_status == "blocked")
    
    symbolic_ready_count = sum(1 for r in plat_rows if r.gate_status == "symbolic_permission_matrix_ready")
    
    evidence_refs = _unique(ref for r in plat_rows for ref in r.evidence_refs)
    blockers = _unique(reason for r in plat_rows for reason in r.blocked_reasons)
    
    audit_entries = build_u9_audit_entries(plat_rows)
    
    draft = {
        "matrix_version": MATRIX_VERSION,
        "generated_at_epoch": 0,
        "permission_gate_rows": plat_rows,
        "rows_by_platform": rows_by_platform,
        "permission_requirement_count": len(plat_reqs),
        "app_review_required_platforms": app_review_platforms,
        "account_role_proof_required_platforms": account_role_platforms,
        "manual_export_only_platforms": manual_export_platforms,
        "blocked_platforms": blocked_platforms,
        "symbolic_permission_matrix_ready_count": symbolic_ready_count,
        "live_read_allowed_count": 0,
        "live_write_allowed_count": 0,
        "env_read_count": 0,
        "credential_hydrated_count": 0,
        "platform_api_called_count": 0,
        "readiness_cleared_count": 0,
        "public_post_allowed_count": 0,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags(),
        "blocked_reasons": blockers,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    
    # Calculate deterministic packet hash
    packet_hash = _digest(draft)
    
    return PlatformPermissionScopeAppReviewGatePacket(
        packet_id="platform_permission_scope_app_review_gate_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def matrix_checksum() -> str:
    return build_platform_permission_scope_app_review_gate_packet().packet_hash


def render_runbook(packet: PlatformPermissionScopeAppReviewGatePacket) -> str:
    lines = [
        "# 0174UJ Platform Permission Scope & App Review Gate Matrix V0",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- matrix_version: `{packet.matrix_version}`",
        f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Permission & Gate Status Matrix",
        "",
        "| Platform ID | Role | Gate Status | Strength | Scopes/Permissions | Blockers |",
        "|---|---|---|---|---|---|",
    ]
    for row in packet.permission_gate_rows:
        scopes = ", ".join(row.required_oauth_scopes + row.required_bot_permissions + row.required_admin_roles)
        blockers = ", ".join(row.blocked_reasons[:3])
        lines.append(f"| `{row.platform_id}` | `{row.platform_role}` | `{row.gate_status}` | `{row.gate_strength}` | `{scopes}` | `{blockers}` |")
        
    lines.extend([
        "",
        "## Required Distinctions & Caveats",
        "",
        "- **Telegram Remote Operator**: Separated operator inbox message sendMessage Bot permission requirements with human reviewed chat_id validation blocker.",
        "- **Telegram Channel Destination**: sendMessage/sendPhoto bot administrator permissions with active admin check blocker.",
        "- **Substack**: Grounded as manual export only without OAuth scopes or API endpoints.",
        "- **LinkedIn**: Member profile shares scopes separated from page admin permissions, with page admin proof failing closed.",
        "- **Meta Platforms**: Threads, Instagram, and Facebook Page separate scopes and meta app review/creator blockers.",
        "",
        "## Safety Enforcements",
        "",
        "- All live read/write/public post flags remain false.",
        "- No credentials or active tokens are loaded.",
        "- U9 audit entry family: `permission_scope_gate_future`.",
        "- Unofficial domain references fail closed on construction.",
        "",
        "## Packet Summary",
        "",
        "```json",
        json.dumps({
            "requirement_count": packet.permission_requirement_count,
            "blocked_platforms": packet.blocked_platforms,
            "manual_export_only_platforms": packet.manual_export_only_platforms,
            "app_review_required_platforms": packet.app_review_required_platforms,
            "account_role_proof_required_platforms": packet.account_role_proof_required_platforms,
            "symbolic_permission_matrix_ready_count": packet.symbolic_permission_matrix_ready_count,
            "live_read_allowed_count": packet.live_read_allowed_count,
            "live_write_allowed_count": packet.live_write_allowed_count,
            "credential_hydrated_count": packet.credential_hydrated_count,
            "platform_api_called_count": packet.platform_api_called_count,
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UJ")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_platform_permission_scope_app_review_gate_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "PermissionScopeRequirement",
    "PlatformPermissionGateRow",
    "PlatformPermissionScopeAppReviewGatePacket",
    "build_default_requirements",
    "build_default_rows",
    "build_u9_audit_entries",
    "build_platform_permission_scope_app_review_gate_packet",
    "matrix_checksum",
    "write_artifacts",
]
