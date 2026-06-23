"""Platform scope and permission contracts for ContentOps destinations.

Deterministic local-only rows. No credential hydration, read-only probes, network,
provider calls, browser automation, or live-write enablement.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_ACCOUNT_BINDING_PERMISSION_SCOPE_VERIFIER_CORE_V0"
MODEL = "contentops.platform_scope_permission_contract"
MODEL_VERSION = "0175_ACCOUNT_BINDING_PERMISSION_SCOPE_CONTRACT_V0"

PLATFORM_IDS: tuple[str, ...] = (
    "x_profile",
    "telegram_remote_operator_inbox",
    "telegram_channel_destination",
    "substack_newsletter",
    "linkedin_member_profile",
    "linkedin_organization_page",
    "threads_profile",
    "instagram_professional_account",
    "facebook_page",
    "tiktok_account",
    "youtube_channel",
)


@dataclass(frozen=True)
class PlatformScopePermissionContract:
    platform_id: str
    credential_kind: str
    destination_kind: str
    public_destination_allowed_future: bool
    required_identity_proof: tuple[str, ...]
    required_destination_proof: tuple[str, ...]
    required_permission_proofs: tuple[str, ...]
    required_scope_names_symbolic: tuple[str, ...]
    live_read_only_probe_required_before_write: bool
    official_docs_required_before_live: bool
    app_review_required: bool
    paid_or_quota_gate_required: bool
    media_permission_required: bool
    later_stage_media_gated: bool
    forbidden_actions_now: tuple[str, ...]
    live_write_allowed_now: bool = False
    read_only_probe_allowed_in_this_task: bool = False
    credential_hydration_allowed_in_this_task: bool = False
    no_secret_output: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


_CONTRACTS: tuple[PlatformScopePermissionContract, ...] = (
    PlatformScopePermissionContract(
        platform_id="x_profile",
        credential_kind="oauth2_user_context_symbolic",
        destination_kind="profile",
        public_destination_allowed_future=True,
        required_identity_proof=("account_handle_redacted", "user_id_redacted", "operator_account_confirmation"),
        required_destination_proof=("x_profile_handle_matches_destination",),
        required_permission_proofs=("write_permission_symbolic", "developer_project_access", "api_tier_or_spend_gate"),
        required_scope_names_symbolic=("tweet.read", "users.read", "tweet.write", "offline.access"),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=True,
        paid_or_quota_gate_required=True,
        media_permission_required=False,
        later_stage_media_gated=False,
        forbidden_actions_now=("api_write", "public_publish", "scheduler", "reply_automation", "dm_automation", "engagement_automation"),
    ),
    PlatformScopePermissionContract(
        platform_id="telegram_remote_operator_inbox",
        credential_kind="telegram_bot_token_symbolic",
        destination_kind="operator_inbox",
        public_destination_allowed_future=False,
        required_identity_proof=("bot_identity_redacted", "operator_chat_binding_redacted"),
        required_destination_proof=("operator_review_channel_only", "not_public_publish_destination"),
        required_permission_proofs=("operator_review_delivery_permission_symbolic",),
        required_scope_names_symbolic=(),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=False,
        paid_or_quota_gate_required=False,
        media_permission_required=False,
        later_stage_media_gated=False,
        forbidden_actions_now=("public_publish", "arbitrary_dm", "group_spam", "scheduler", "reply_automation"),
    ),
    PlatformScopePermissionContract(
        platform_id="telegram_channel_destination",
        credential_kind="telegram_bot_token_symbolic",
        destination_kind="channel",
        public_destination_allowed_future=True,
        required_identity_proof=("bot_identity_redacted",),
        required_destination_proof=("channel_id_or_handle_redacted", "channel_membership_proof"),
        required_permission_proofs=("bot_admin", "can_write_channel_messages"),
        required_scope_names_symbolic=(),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=False,
        paid_or_quota_gate_required=False,
        media_permission_required=False,
        later_stage_media_gated=False,
        forbidden_actions_now=("api_write", "private_dm_route", "group_spam", "arbitrary_destination", "scheduler"),
    ),
    PlatformScopePermissionContract(
        platform_id="substack_newsletter",
        credential_kind="manual_publication_binding_symbolic",
        destination_kind="newsletter_publication",
        public_destination_allowed_future=True,
        required_identity_proof=("publication_owner_or_editor_redacted",),
        required_destination_proof=("publication_url_redacted", "manual_export_binding"),
        required_permission_proofs=("manual_publish_operator_proof",),
        required_scope_names_symbolic=(),
        live_read_only_probe_required_before_write=False,
        official_docs_required_before_live=True,
        app_review_required=False,
        paid_or_quota_gate_required=False,
        media_permission_required=False,
        later_stage_media_gated=False,
        forbidden_actions_now=("official_api_assumption", "api_write", "browser_session_automation", "scheduler"),
    ),
    PlatformScopePermissionContract(
        platform_id="linkedin_member_profile",
        credential_kind="linkedin_member_oauth_symbolic",
        destination_kind="member_profile",
        public_destination_allowed_future=True,
        required_identity_proof=("member_urn_redacted", "member_identity_redacted"),
        required_destination_proof=("member_profile_binding",),
        required_permission_proofs=("linkedin_product_access", "member_write_permission"),
        required_scope_names_symbolic=("w_member_social",),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=True,
        paid_or_quota_gate_required=False,
        media_permission_required=False,
        later_stage_media_gated=False,
        forbidden_actions_now=("api_write", "organization_page_write", "comment_automation", "like_automation", "scheduler"),
    ),
    PlatformScopePermissionContract(
        platform_id="linkedin_organization_page",
        credential_kind="linkedin_organization_oauth_symbolic",
        destination_kind="organization_page",
        public_destination_allowed_future=True,
        required_identity_proof=("member_identity_redacted",),
        required_destination_proof=("organization_urn_redacted", "organization_page_role"),
        required_permission_proofs=("member_page_admin_or_role", "organization_write_permission"),
        required_scope_names_symbolic=("w_organization_social",),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=True,
        paid_or_quota_gate_required=False,
        media_permission_required=False,
        later_stage_media_gated=False,
        forbidden_actions_now=("api_write", "member_profile_write", "comment_automation", "like_automation", "scheduler"),
    ),
    PlatformScopePermissionContract(
        platform_id="threads_profile",
        credential_kind="threads_meta_oauth_symbolic",
        destination_kind="profile",
        public_destination_allowed_future=True,
        required_identity_proof=("threads_profile_id_redacted",),
        required_destination_proof=("threads_profile_binding",),
        required_permission_proofs=("threads_app_access", "threads_publish_permission"),
        required_scope_names_symbolic=("threads_basic", "threads_content_publish"),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=True,
        paid_or_quota_gate_required=False,
        media_permission_required=True,
        later_stage_media_gated=True,
        forbidden_actions_now=("api_write", "reply_automation", "engagement_automation", "scheduler"),
    ),
    PlatformScopePermissionContract(
        platform_id="instagram_professional_account",
        credential_kind="meta_instagram_oauth_symbolic",
        destination_kind="professional_account",
        public_destination_allowed_future=True,
        required_identity_proof=("professional_or_business_or_creator_account_redacted",),
        required_destination_proof=("instagram_business_account_id_redacted", "page_or_account_linkage"),
        required_permission_proofs=("content_publish_permission", "media_container_permission"),
        required_scope_names_symbolic=("instagram_basic", "instagram_content_publish"),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=True,
        paid_or_quota_gate_required=False,
        media_permission_required=True,
        later_stage_media_gated=True,
        forbidden_actions_now=("api_write", "text_only_publish_assumption", "scheduler", "engagement_automation"),
    ),
    PlatformScopePermissionContract(
        platform_id="facebook_page",
        credential_kind="meta_page_oauth_symbolic",
        destination_kind="page",
        public_destination_allowed_future=True,
        required_identity_proof=("page_id_redacted",),
        required_destination_proof=("facebook_page_binding", "not_personal_profile", "not_group"),
        required_permission_proofs=("page_role_or_task", "page_token_symbolic"),
        required_scope_names_symbolic=("pages_manage_posts", "pages_read_engagement"),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=True,
        paid_or_quota_gate_required=False,
        media_permission_required=False,
        later_stage_media_gated=False,
        forbidden_actions_now=("api_write", "personal_profile_posting", "group_posting", "scheduler"),
    ),
    PlatformScopePermissionContract(
        platform_id="tiktok_account",
        credential_kind="tiktok_oauth_symbolic",
        destination_kind="account",
        public_destination_allowed_future=True,
        required_identity_proof=("creator_open_id_redacted", "creator_info_redacted"),
        required_destination_proof=("tiktok_account_binding",),
        required_permission_proofs=("app_product_access", "creator_info_permission", "visibility_permission", "upload_permission"),
        required_scope_names_symbolic=("user.info.basic", "video.publish", "video.upload"),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=True,
        paid_or_quota_gate_required=True,
        media_permission_required=True,
        later_stage_media_gated=True,
        forbidden_actions_now=("api_write", "video_upload", "scheduler", "engagement_automation"),
    ),
    PlatformScopePermissionContract(
        platform_id="youtube_channel",
        credential_kind="youtube_oauth_symbolic",
        destination_kind="channel",
        public_destination_allowed_future=True,
        required_identity_proof=("youtube_channel_id_redacted",),
        required_destination_proof=("channel_ownership_or_manager_binding",),
        required_permission_proofs=("youtube_upload_permission", "quota_audit", "privacy_status_safe_mode"),
        required_scope_names_symbolic=("youtube.upload",),
        live_read_only_probe_required_before_write=True,
        official_docs_required_before_live=True,
        app_review_required=True,
        paid_or_quota_gate_required=True,
        media_permission_required=True,
        later_stage_media_gated=True,
        forbidden_actions_now=("api_write", "video_upload", "public_default_publish", "scheduler"),
    ),
)


def build_platform_scope_permission_contracts() -> tuple[PlatformScopePermissionContract, ...]:
    """Return immutable per-platform scope/permission contracts."""
    return _CONTRACTS


def contracts_by_platform_id() -> dict[str, PlatformScopePermissionContract]:
    """Return contracts indexed by platform_id."""
    return {contract.platform_id: contract for contract in build_platform_scope_permission_contracts()}


def platform_scope_permission_contract_packet() -> dict[str, Any]:
    """Return JSON-serializable scope/permission contract packet."""
    rows = [contract.as_dict() for contract in build_platform_scope_permission_contracts()]
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "platform_count": len(rows),
        "platform_ids": list(PLATFORM_IDS),
        "all_platforms_covered": sorted(row["platform_id"] for row in rows) == sorted(PLATFORM_IDS),
        "live_write_allowed_now": False,
        "read_only_probe_allowed_in_this_task": False,
        "credential_hydration_allowed_in_this_task": False,
        "no_live_api_probe": True,
        "no_secret_output": True,
        "contracts": rows,
    }
