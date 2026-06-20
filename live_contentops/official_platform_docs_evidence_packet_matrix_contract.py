"""Official platform docs evidence packet matrix contract for ContentOps 0174UI.

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
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UI_OFFICIAL_PLATFORM_DOCS_EVIDENCE_PACKET_MATRIX_V0"
MATRIX_VERSION = "0174UI_OFFICIAL_PLATFORM_DOCS_EVIDENCE_PACKET_MATRIX_V1"
SOURCE_BASELINE_COMMIT = "dc997aa68df523539dd6f4df6b77d792d3961e14"
DOC_REL_DIR = Path("docs") / "automation" / "0174UI"
PACKET_FILENAME = "official_platform_docs_evidence_packet_matrix_contract_packet.json"
RUNBOOK_FILENAME = "official_platform_docs_evidence_packet_matrix_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "platform_docs_evidence_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UJ_PLATFORM_PERMISSION_SCOPE_AND_APP_REVIEW_GATE_MATRIX_V0"

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
class DocRelevance:
    auth_model: bool = False
    endpoint_family: bool = False
    payload_constraints: bool = False
    media_constraints: bool = False
    permission_scope: bool = False
    rate_limit_or_quota: bool = False
    app_review_or_access_level: bool = False
    manual_export_no_api: bool = False


@dataclass(frozen=True)
class OfficialDocsEvidenceRef:
    evidence_ref_id: str
    platform_id: str
    official_doc_title: str
    official_doc_url: str
    official_domain: str
    doc_accessed_at_epoch: int
    doc_relevance: DocRelevance
    cited_claim_summary: str
    caveats: str
    evidence_status: str  # official_doc_cited, official_doc_missing, manual_export_no_api, needs_human_review, blocked_unofficial_only
    evidence_hash: str
    evidence_hash_algorithm: str

    def __post_init__(self) -> None:
        # Strict validation on construction: unofficial domains fail closed
        parsed = urlparse(self.official_doc_url)
        host = parsed.netloc.split(":")[0] if parsed.netloc else ""
        if host not in ALLOWED_DOMAINS:
            raise ValueError(f"unofficial_domain_not_allowed: {host}")
        if self.official_domain != host:
            raise ValueError(f"domain_mismatch: {self.official_domain} vs {host}")
        if self.evidence_status not in {
            "official_doc_cited", "official_doc_missing", "manual_export_no_api",
            "needs_human_review", "blocked_unofficial_only"
        }:
            raise ValueError(f"invalid_evidence_status: {self.evidence_status}")


@dataclass(frozen=True)
class PlatformDocsEvidenceRow:
    row_id: str
    platform_id: str
    platform_role: str
    doc_refs: tuple[str, ...]
    auth_model_summary: str
    endpoint_family_summary: str
    payload_constraint_summary: str
    media_constraint_summary: str
    permission_scope_summary: str
    rate_quota_spend_summary: str
    app_review_access_summary: str
    docs_status: str  # docs_grounded, partial_docs_grounded, manual_export_no_api, blocked_missing_official_docs, needs_human_review
    live_read_allowed: bool
    live_write_allowed: bool
    platform_api_called: bool
    credential_required_future: bool
    credential_hydrated: bool
    env_read: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    row_hash: str


@dataclass(frozen=True)
class OfficialPlatformDocsEvidenceMatrixPacket:
    packet_id: str
    matrix_version: str
    generated_at_epoch: int
    docs_rows: tuple[PlatformDocsEvidenceRow, ...]
    rows_by_platform: dict[str, tuple[str, ...]]
    official_doc_ref_count: int
    official_domain_count: int
    docs_grounded_platform_count: int
    manual_export_no_api_platforms: tuple[str, ...]
    blocked_missing_docs_platforms: tuple[str, ...]
    live_read_allowed_count: int
    live_write_allowed_count: int
    platform_api_called_count: int
    env_read_count: int
    credential_hydrated_count: int
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
    return {**{flag: False for flag in false_flags}, "local_docs_matrix_only": True, "review_only": True}


def build_default_evidence_refs() -> tuple[OfficialDocsEvidenceRef, ...]:
    # Statically defined real official platform documentation references
    specs = [
        (
            "doc_evidence_ref_x_v2",
            "x",
            "X API - Getting Started",
            "https://developer.x.com/en/docs/x-api/getting-started/about-x-api",
            "developer.x.com",
            1781913600,
            DocRelevance(auth_model=True, endpoint_family=True, payload_constraints=True, rate_limit_or_quota=True, app_review_or_access_level=True),
            "OAuth 2.0 Authorization Code Flow with PKCE is standard. Write permissions require Free, Basic, or Pro tiers.",
            "Free tier is write-only with low rate limits (17 tweets/24h). Higher limits require paid Basic/Pro plans. V2 endpoints are primary.",
            "official_doc_cited",
        ),
        (
            "doc_evidence_ref_telegram_operator_intro",
            "telegram_remote_operator",
            "Telegram Bot API - Introduction",
            "https://core.telegram.org/bots/api#introduction",
            "core.telegram.org",
            1781913600,
            DocRelevance(auth_model=True, endpoint_family=True, permission_scope=True),
            "Telegram Bot token is passed in the request path. Access is bot-based and chat-scoped via chat_id.",
            "Bots cannot message arbitrary users without prior contact. Operates as incoming inbox only via getUpdates/Webhooks.",
            "official_doc_cited",
        ),
        (
            "doc_evidence_ref_telegram_channel_send",
            "telegram_channel_destination",
            "Telegram Bot API - sendMessage",
            "https://core.telegram.org/bots/api#sendmessage",
            "core.telegram.org",
            1781913600,
            DocRelevance(auth_model=True, endpoint_family=True, payload_constraints=True, permission_scope=True),
            "sendMessage requires a chat_id (e.g. @channelusername) and text content. Max length is 4096 characters.",
            "The bot must be added to the channel as an administrator with the 'Post Messages' permission.",
            "official_doc_cited",
        ),
        (
            "doc_evidence_ref_substack_help",
            "substack_newsletter",
            "Substack Help Center - Publication Management",
            "https://support.substack.com/hc/en-us",
            "support.substack.com",
            1781913600,
            DocRelevance(manual_export_no_api=True),
            "Substack does not offer an official, public API for programmatic post creation or publishing.",
            "ContentOps must rely on manual markdown export or drafts, as automated browser sessions are prohibited.",
            "manual_export_no_api",
        ),
        (
            "doc_evidence_ref_linkedin_share",
            "linkedin",
            "LinkedIn Share on LinkedIn API",
            "https://learn.microsoft.com/linkedin/consumer/integrations/self-serve/share-on-linkedin",
            "learn.microsoft.com",
            1781913600,
            DocRelevance(auth_model=True, endpoint_family=True, permission_scope=True, app_review_or_access_level=True),
            "Posting on behalf of members uses the ugcPosts or shares API. Requires w_member_social scope.",
            "Requires OAuth 2.0 authorization. App must be approved via the LinkedIn Developer Portal. Members cannot post to pages without page permissions.",
            "official_doc_cited",
        ),
        (
            "doc_evidence_ref_threads_overview",
            "threads",
            "Threads API - Overview",
            "https://developers.facebook.com/docs/threads/overview",
            "developers.facebook.com",
            1781913600,
            DocRelevance(auth_model=True, endpoint_family=True, permission_scope=True, app_review_or_access_level=True),
            "Threads API supports publishing threads, text, images, and videos. Requires threads_basic and threads_content_publish scopes.",
            "Requires Meta App Review for live API access. Accounts are subject to rate limiting of 250 posts per 24 hours per user.",
            "official_doc_cited",
        ),
        (
            "doc_evidence_ref_instagram_publish",
            "instagram",
            "Instagram Content Publishing API",
            "https://developers.facebook.com/docs/instagram-api/guides/content-publishing",
            "developers.facebook.com",
            1781913600,
            DocRelevance(auth_model=True, endpoint_family=True, payload_constraints=True, media_constraints=True, permission_scope=True, app_review_or_access_level=True),
            "Instagram Graph API supports publishing media (images, videos, carousels) for Instagram Business or Creator accounts.",
            "Requires Meta App Review and instagram_content_publish scope. Media must be hosted on a public URL accessible by Facebook servers during container creation.",
            "official_doc_cited",
        ),
        (
            "doc_evidence_ref_facebook_page_publish",
            "facebook_page",
            "Facebook Pages API - Publishing",
            "https://developers.facebook.com/docs/pages/publishing",
            "developers.facebook.com",
            1781913600,
            DocRelevance(auth_model=True, endpoint_family=True, permission_scope=True, app_review_or_access_level=True),
            "Programmatic posting to a Facebook Page requires a Page Access Token and the pages_manage_posts permission.",
            "Requires Meta App Review to get advanced access for pages_manage_posts scope, and the posting user must have a sufficient Page role.",
            "official_doc_cited",
        ),
        (
            "doc_evidence_ref_tiktok_posting",
            "tiktok",
            "TikTok Content Posting API Overview",
            "https://developers.tiktok.com/doc/content-posting-api-get-started",
            "developers.tiktok.com",
            1781913600,
            DocRelevance(auth_model=True, endpoint_family=True, payload_constraints=True, media_constraints=True, permission_scope=True, app_review_or_access_level=True),
            "TikTok Content Posting API allows developers to publish videos directly to user accounts. Requires video.upload and video.publish scopes.",
            "Requires developer app review and user authorization. Video files must be compliant with TikTok specs and accessible via a public URL or direct upload chunking.",
            "official_doc_cited",
        ),
        (
            "doc_evidence_ref_youtube_insert",
            "youtube",
            "YouTube Data API - Videos: insert",
            "https://developers.google.com/youtube/v3/docs/videos/insert",
            "developers.google.com",
            1781913600,
            DocRelevance(auth_model=True, endpoint_family=True, media_constraints=True, permission_scope=True, rate_limit_or_quota=True),
            "Uploads videos to YouTube using videos.insert. Requires OAuth 2.0 with youtube.upload scope.",
            "Video uploads consume a significant amount of the daily API quota (1600 units per upload out of 10,000 default units).",
            "official_doc_cited",
        )
    ]
    refs = []
    for ref_id, platform, title, url, domain, accessed, relevance, claim, caveats, status in specs:
        # Compute evidence_hash for deterministic packaging
        material = {
            "evidence_ref_id": ref_id,
            "platform_id": platform,
            "official_doc_title": title,
            "official_doc_url": url,
            "official_domain": domain,
            "doc_accessed_at_epoch": accessed,
            "doc_relevance": _asdict(relevance),
            "cited_claim_summary": claim,
            "caveats": caveats,
            "evidence_status": status,
        }
        refs.append(
            OfficialDocsEvidenceRef(
                evidence_ref_id=ref_id,
                platform_id=platform,
                official_doc_title=title,
                official_doc_url=url,
                official_domain=domain,
                doc_accessed_at_epoch=accessed,
                doc_relevance=relevance,
                cited_claim_summary=claim,
                caveats=caveats,
                evidence_status=status,
                evidence_hash=_digest(material),
                evidence_hash_algorithm=HASH_ALGORITHM,
            )
        )
    return tuple(refs)


def build_default_docs_rows(refs: tuple[OfficialDocsEvidenceRef, ...] | None = None) -> tuple[PlatformDocsEvidenceRow, ...]:
    actual_refs = build_default_evidence_refs() if refs is None else refs
    by_platform: dict[str, list[OfficialDocsEvidenceRef]] = {pid: [] for pid in PLATFORM_IDS}
    for r in actual_refs:
        if r.platform_id in by_platform:
            by_platform[r.platform_id].append(r)

    rows = []
    for platform_id in PLATFORM_IDS:
        plat_refs = by_platform[platform_id]
        doc_refs = tuple(r.evidence_ref_id for r in plat_refs)

        # Base properties matching universe configuration roles
        role = universe.PLATFORMS_BY_ID[platform_id].platform_role
        
        # Determine status and summary details based on the platform and its references
        if platform_id == "substack_newsletter":
            docs_status = "manual_export_no_api"
            auth_model_summary = "None (Manual Markdown Export)"
            endpoint_family_summary = "None (No API Supported)"
            payload_constraint_summary = "Markdown publication formatting constraints"
            media_constraint_summary = "Assets manually embedded"
            permission_scope_summary = "No OAuth scopes"
            rate_quota_spend_summary = "Manual copy/paste workflow"
            app_review_access_summary = "No Meta/LinkedIn/TikTok Developer App review"
            credential_required = False
            blocked_reasons = ("no_substack_public_publish_api_gate", "session_automation_blocked", "manual_export_first_no_api")
        else:
            # Most API platforms require app review or scopes
            credential_required = True
            if not plat_refs:
                docs_status = "blocked_missing_official_docs"
                auth_model_summary = "Missing official documentation"
                endpoint_family_summary = "Missing official documentation"
                payload_constraint_summary = "Missing official documentation"
                media_constraint_summary = "Missing official documentation"
                permission_scope_summary = "Missing official documentation"
                rate_quota_spend_summary = "Missing official documentation"
                app_review_access_summary = "Missing official documentation"
                blocked_reasons = ("missing_official_docs", "fails_closed_missing_docs")
            else:
                # Map specific summaries
                if platform_id == "x":
                    docs_status = "partial_docs_grounded"
                    auth_model_summary = "OAuth 2.0 Authorization Code Flow with PKCE"
                    endpoint_family_summary = "v2/tweets POST/GET"
                    payload_constraint_summary = "Short post (280 chars) or thread payload structure"
                    media_constraint_summary = "Image (JPEG, PNG), GIF, or Video up to 512MB"
                    permission_scope_summary = "tweet.read, tweet.write, users.read, offline.access"
                    rate_quota_spend_summary = "17 tweets per 24 hours on Free tier; paywall spend tier caveats"
                    app_review_access_summary = "Developer portal app creation and user authorization"
                    blocked_reasons = ("x_api_gate_closed", "credential_gate_closed", "rate_limit_and_spend_gate_unresolved")
                elif platform_id == "telegram_remote_operator":
                    docs_status = "docs_grounded"
                    auth_model_summary = "Bot Token API Authentication"
                    endpoint_family_summary = "getMe, getUpdates, Webhooks, sendMessage"
                    payload_constraint_summary = "Review challenge message payload"
                    media_constraint_summary = "None (Text operators)"
                    permission_scope_summary = "sendMessage:operator_inbox"
                    rate_quota_spend_summary = "No commercial spend quota; standard Bot API rate limits"
                    app_review_access_summary = "Inbox presence only; operator chat_id binding verification"
                    blocked_reasons = ("operator_inbox_chat_proof_required", "telegram_api_gate_closed")
                elif platform_id == "telegram_channel_destination":
                    docs_status = "docs_grounded"
                    auth_model_summary = "Bot Token API Authentication"
                    endpoint_family_summary = "sendMessage, sendPhoto"
                    payload_constraint_summary = "Channel update message (4096 chars limit)"
                    media_constraint_summary = "Direct photo upload or public image URL"
                    permission_scope_summary = "sendMessage:channel, administrator:can_post_messages"
                    rate_quota_spend_summary = "Standard Bot API limits (30 messages/second max)"
                    app_review_access_summary = "Requires Bot to be added to channel with Administrator roles"
                    blocked_reasons = ("channel_permission_proof_required", "telegram_api_gate_closed", "bot_admin_gate_closed")
                elif platform_id == "linkedin":
                    docs_status = "partial_docs_grounded"
                    auth_model_summary = "OAuth 2.0 Authorization Code Flow"
                    endpoint_family_summary = "ugcPosts, shares API"
                    payload_constraint_summary = "Professional post text constraints"
                    media_constraint_summary = "Links, images, and video assets"
                    permission_scope_summary = "openid, profile, w_member_social, organization_admin_symbolic"
                    rate_quota_spend_summary = "Standard member rate limits"
                    app_review_access_summary = "Member profile posting vs organization page admin permission constraints"
                    blocked_reasons = ("linkedin_member_profile_proof_required", "linkedin_oauth_gate_closed", "permission_review_closed")
                elif platform_id == "threads":
                    docs_status = "partial_docs_grounded"
                    auth_model_summary = "OAuth 2.0 Meta App Authorization"
                    endpoint_family_summary = "Threads API publishing endpoint"
                    payload_constraint_summary = "Short post (500 chars limit)"
                    media_constraint_summary = "Images, videos up to spec"
                    permission_scope_summary = "threads_basic, threads_content_publish"
                    rate_quota_spend_summary = "250 posts per 24 hours per user"
                    app_review_access_summary = "Meta App Review required for live API context"
                    blocked_reasons = ("meta_app_account_proof_required", "meta_app_review_closed")
                elif platform_id == "instagram":
                    docs_status = "partial_docs_grounded"
                    auth_model_summary = "Instagram Graph API via Facebook Login"
                    endpoint_family_summary = "media containers and media publish endpoints"
                    payload_constraint_summary = "Caption up to 2200 chars, max 30 hashtags"
                    media_constraint_summary = "Hosted publicly accessible URL required for Facebook server intake"
                    permission_scope_summary = "instagram_basic, instagram_content_publish, pages_show_list"
                    rate_quota_spend_summary = "Container creation limit (25 per 24h rolling)"
                    app_review_access_summary = "Meta App Review and Business Verification required"
                    blocked_reasons = ("instagram_business_creator_proof_required", "instagram_content_publish_gate_closed", "media_url_gate_closed")
                elif platform_id == "facebook_page":
                    docs_status = "partial_docs_grounded"
                    auth_model_summary = "Page Access Token via OAuth 2.0"
                    endpoint_family_summary = "Pages API feed endpoint"
                    payload_constraint_summary = "Page feed text and links"
                    media_constraint_summary = "Images and video formats"
                    permission_scope_summary = "pages_read_engagement, pages_manage_posts, pages_show_list"
                    rate_quota_spend_summary = "Facebook Page rate limit system"
                    app_review_access_summary = "Meta App Review Advanced Access and Page admin role verification"
                    blocked_reasons = ("facebook_page_role_proof_required", "app_review_gate_closed")
                elif platform_id == "tiktok":
                    docs_status = "partial_docs_grounded"
                    auth_model_summary = "OAuth 2.0 Three-Legged Authorization"
                    endpoint_family_summary = "Content Posting API upload endpoints"
                    payload_constraint_summary = "Video title, description, and privacy settings"
                    media_constraint_summary = "MP4/WebM compliance, aspect ratio constraints"
                    permission_scope_summary = "user.info.basic, video.publish, video.upload"
                    rate_quota_spend_summary = "TikTok Posting quota limitations"
                    app_review_access_summary = "Developer app audit and TikTok video upload permissions review"
                    blocked_reasons = ("creator_account_video_publish_proof_required", "video_future_gate_closed", "tiktok_audit_closed")
                elif platform_id == "youtube":
                    docs_status = "partial_docs_grounded"
                    auth_model_summary = "Google OAuth 2.0 with client id"
                    endpoint_family_summary = "YouTube Data API v3 videos.insert"
                    payload_constraint_summary = "Video title, description, tags, playlist constraints"
                    media_constraint_summary = "Video containers (MOV, MP4, AVI, etc.)"
                    permission_scope_summary = "youtube.readonly, youtube.upload"
                    rate_quota_spend_summary = "Daily API upload quota consumes 1600 units out of 10000 units"
                    app_review_access_summary = "Google OAuth Consent Screen review and verification"
                    blocked_reasons = ("youtube_oauth_channel_proof_required", "quota_upload_gate_closed", "later_video_gate_closed")

        material = {
            "row_id": f"docs_evidence_row_{platform_id}",
            "platform_id": platform_id,
            "platform_role": role,
            "doc_refs": doc_refs,
            "auth_model_summary": auth_model_summary,
            "endpoint_family_summary": endpoint_family_summary,
            "payload_constraint_summary": payload_constraint_summary,
            "media_constraint_summary": media_constraint_summary,
            "permission_scope_summary": permission_scope_summary,
            "rate_quota_spend_summary": rate_quota_spend_summary,
            "app_review_access_summary": app_review_access_summary,
            "docs_status": docs_status,
            "live_read_allowed": False,
            "live_write_allowed": False,
            "platform_api_called": False,
            "credential_required_future": credential_required,
            "credential_hydrated": False,
            "env_read": False,
            "evidence_refs": doc_refs + ("docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",),
        }

        rows.append(
            PlatformDocsEvidenceRow(
                row_id=material["row_id"],
                platform_id=platform_id,
                platform_role=role,
                doc_refs=doc_refs,
                auth_model_summary=auth_model_summary,
                endpoint_family_summary=endpoint_family_summary,
                payload_constraint_summary=payload_constraint_summary,
                media_constraint_summary=media_constraint_summary,
                permission_scope_summary=permission_scope_summary,
                rate_quota_spend_summary=rate_quota_spend_summary,
                app_review_access_summary=app_review_access_summary,
                docs_status=docs_status,
                live_read_allowed=False,
                live_write_allowed=False,
                platform_api_called=False,
                credential_required_future=credential_required,
                credential_hydrated=False,
                env_read=False,
                evidence_refs=material["evidence_refs"],
                safety_flags=safety_flags(),
                blocked_reasons=blocked_reasons,
                row_hash=_digest(material)
            )
        )
    return tuple(rows)


def build_u9_audit_entries(packet_or_rows: OfficialPlatformDocsEvidenceMatrixPacket | tuple[PlatformDocsEvidenceRow, ...]) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    rows = packet_or_rows.docs_rows if hasattr(packet_or_rows, "docs_rows") else packet_or_rows
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UI"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, row in enumerate(rows, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UI",
            source_model_version=MATRIX_VERSION,
            payload={
                "id": row.row_id,
                "platform_id": row.platform_id,
                "status": row.docs_status,
                "source_payload_hash": row.row_hash,
                "evidence_refs": row.evidence_refs,
                "blocked_reasons": row.blocked_reasons,
                "safety_flags": row.safety_flags,
            },
            policy=policy,
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_official_platform_docs_evidence_matrix_packet(
    rows: tuple[PlatformDocsEvidenceRow, ...] | None = None,
    refs: tuple[OfficialDocsEvidenceRef, ...] | None = None,
) -> OfficialPlatformDocsEvidenceMatrixPacket:
    actual_refs = build_default_evidence_refs() if refs is None else refs
    actual_rows = build_default_docs_rows(actual_refs) if rows is None else rows
    
    rows_by_platform = {r.platform_id: (r.row_id,) for r in actual_rows}
    
    # Analyze domain metrics
    unique_domains = _unique(ref.official_domain for ref in actual_refs)
    
    # Status categorizations
    grounded_count = sum(1 for r in actual_rows if r.docs_status == "docs_grounded")
    manual_export_platforms = _unique(r.platform_id for r in actual_rows if r.docs_status == "manual_export_no_api")
    blocked_platforms = _unique(r.platform_id for r in actual_rows if r.docs_status == "blocked_missing_official_docs")
    
    # Safety verification (must be zeroed)
    live_read_count = sum(1 for r in actual_rows if r.live_read_allowed)
    live_write_count = sum(1 for r in actual_rows if r.live_write_allowed)
    api_called_count = sum(1 for r in actual_rows if r.platform_api_called)
    env_read_count = sum(1 for r in actual_rows if r.env_read)
    hydrated_count = sum(1 for r in actual_rows if r.credential_hydrated)
    
    # U9 audit ledger generation
    audit_entries = build_u9_audit_entries(actual_rows)
    
    evidence_refs = _unique(ref for r in actual_rows for ref in r.evidence_refs)
    blockers = _unique(reason for r in actual_rows for reason in r.blocked_reasons)
    
    draft = {
        "matrix_version": MATRIX_VERSION,
        "generated_at_epoch": 0,
        "docs_rows": actual_rows,
        "rows_by_platform": rows_by_platform,
        "official_doc_ref_count": len(actual_refs),
        "official_domain_count": len(unique_domains),
        "docs_grounded_platform_count": grounded_count,
        "manual_export_no_api_platforms": manual_export_platforms,
        "blocked_missing_docs_platforms": blocked_platforms,
        "live_read_allowed_count": live_read_count,
        "live_write_allowed_count": live_write_count,
        "platform_api_called_count": api_called_count,
        "env_read_count": env_read_count,
        "credential_hydrated_count": hydrated_count,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags(),
        "blocked_reasons": blockers,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    packet_hash = _digest(draft)
    return OfficialPlatformDocsEvidenceMatrixPacket(
        packet_id="official_platform_docs_evidence_matrix_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def matrix_checksum() -> str:
    return build_official_platform_docs_evidence_matrix_packet().packet_hash


def render_runbook(packet: OfficialPlatformDocsEvidenceMatrixPacket) -> str:
    lines = [
        "# 0174UI Official Platform Docs Evidence Matrix Contract",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- matrix_version: `{packet.matrix_version}`",
        f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Docs Evidence Grounding Matrix",
        "",
        "| Platform ID | Priority Tier | Role | Docs Status | Auth Summary | Endpoint Family | Key Caveats |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in packet.docs_rows:
        plat_universe = universe.PLATFORMS_BY_ID[row.platform_id]
        lines.append(
            f"| `{row.platform_id}` | `{plat_universe.priority_tier}` | `{row.platform_role}` | `{row.docs_status}` | "
            f"{row.auth_model_summary} | {row.endpoint_family_summary} | {row.rate_quota_spend_summary} |"
        )
    lines.extend([
        "",
        "## Required Distinctions & Caveats",
        "",
        "- **X / Twitter**: Paywalled API tiers. Free tier is write-only and highly rate-limited (17 tweets/24h).",
        "- **Telegram**: Bots are chat-scoped and require chat_id values. Bot cannot message arbitrary users.",
        "- **Substack**: Grounded as `manual_export_no_api` (no official programmatic publish API exists).",
        "- **LinkedIn**: Member profile shares (`w_member_social`) separate from organization page administration.",
        "- **Meta (Threads, Instagram, Facebook)**: Standard Meta OAuth and App Review apply. Media URL visibility is required.",
        "- **TikTok & YouTube**: High quota constraints (e.g. videos.insert consumes 1600 units) and video uploads metadata only.",
        "",
        "## Safety Enforcements",
        "",
        "- All live read/write/API actions remain false.",
        "- No credentials or environment secrets are loaded.",
        "- Inputting an unofficial domain fails closed.",
        "- U9 Audit family: `platform_docs_evidence_future`.",
        "",
        "## Packet Summary Metrics",
        "",
        "```json",
        json.dumps({
            "rows_count": len(packet.docs_rows),
            "grounded_count": packet.docs_grounded_platform_count,
            "manual_export_no_api_platforms": packet.manual_export_no_api_platforms,
            "blocked_missing_docs_platforms": packet.blocked_missing_docs_platforms,
            "live_read_allowed_count": packet.live_read_allowed_count,
            "live_write_allowed_count": packet.live_write_allowed_count,
            "platform_api_called_count": packet.platform_api_called_count,
            "env_read_count": packet.env_read_count,
            "credential_hydrated_count": packet.credential_hydrated_count,
            "official_doc_ref_count": packet.official_doc_ref_count,
            "official_domain_count": packet.official_domain_count,
        }, indent=2, sort_keys=True),
        "```",
        "",
    ])
    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UI")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_official_platform_docs_evidence_matrix_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "DocRelevance",
    "OfficialDocsEvidenceRef",
    "PlatformDocsEvidenceRow",
    "OfficialPlatformDocsEvidenceMatrixPacket",
    "build_default_evidence_refs",
    "build_default_docs_rows",
    "build_official_platform_docs_evidence_matrix_packet",
    "build_u9_audit_entries",
    "matrix_checksum",
    "write_artifacts",
]
