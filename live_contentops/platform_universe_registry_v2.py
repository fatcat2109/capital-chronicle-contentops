"""Platform universe registry v2 for ContentOps.

Deterministic local-only registry for platform families.
No live dispatch, network, provider, credential, env, scheduler, scraping, or DM behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_PLATFORM_UNIVERSE_REGISTRY_V2_PRIMARY_PAYLOAD_CLASSES_CORE_V0"
MODEL = "contentops.platform_universe_registry_v2"
MODEL_VERSION = "0174U1_PLATFORM_UNIVERSE_REGISTRY_V2_V2"

SECRET_PATTERNS = [
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b"),  # Telegram bot token
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),  # JWT token
]


@dataclass(frozen=True)
class PlatformUniverseRegistryEntry:
    platform_id: str
    display_name: str
    platform_family: str
    platform_role: str
    strategy_tier: str  # primary | secondary | expansion | later
    destination_kind: str
    default_current_mode: str
    allowed_current_modes: tuple[str, ...]
    future_modes: tuple[str, ...]
    primary_payload_class_ids: tuple[str, ...]
    manual_export_supported: bool
    browser_assisted_lab_supported: bool
    api_available_future: bool
    api_write_available_future: bool
    live_write_allowed_now: bool  # Must be False
    dispatchable_now: bool  # Must be False
    public_postable_now: bool  # Must be False
    credential_required_for_live: bool
    account_binding_required_for_live: bool
    approval_payload_hash_required: bool
    approval_ledger_required: bool
    outbox_required: bool
    idempotency_required: bool
    kill_switch_required: bool
    redacted_audit_required: bool
    manual_fallback_required: bool
    official_docs_required_before_live: bool
    re_ground_required_before_live: bool
    live_gate_status: str
    blocked_reasons: tuple[str, ...]
    forbidden_current_actions: tuple[str, ...]
    no_autonomous_reply_dm_scheduler_scraping: bool  # Must be True


class UnsupportedPlatformError(ValueError):
    """Raised when platform lookup fails closed."""


def build_platform_universe_registry_v2() -> tuple[PlatformUniverseRegistryEntry, ...]:
    """Build the list of platform registry rows."""
    return (
        PlatformUniverseRegistryEntry(
            platform_id="x_profile",
            display_name="X Profile",
            platform_family="x",
            platform_role="primary_distribution",
            strategy_tier="primary",
            destination_kind="profile",
            default_current_mode="preview_only",
            allowed_current_modes=("preview_only",),
            future_modes=("supervised_api_write",),
            primary_payload_class_ids=("x_short_post", "x_thread"),
            manual_export_supported=False,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=True,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "credential_gate_closed", "api_write_gate_closed"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="telegram_remote_operator_inbox",
            display_name="Telegram Remote Operator Inbox",
            platform_family="telegram",
            platform_role="remote_operator_review",
            strategy_tier="primary",
            destination_kind="operator_inbox",
            default_current_mode="local_only",
            allowed_current_modes=("local_only",),
            future_modes=("supervised_inbox_check",),
            primary_payload_class_ids=("telegram_operator_review_message",),
            manual_export_supported=False,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=False,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "not_publish_destination"),
            forbidden_current_actions=("public_post", "auto_reply", "direct_message", "scheduler_post"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="telegram_channel_destination",
            display_name="Telegram Channel Destination",
            platform_family="telegram",
            platform_role="controlled_channel_distribution",
            strategy_tier="primary",
            destination_kind="channel",
            default_current_mode="preview_only",
            allowed_current_modes=("preview_only",),
            future_modes=("supervised_api_write",),
            primary_payload_class_ids=("telegram_channel_update",),
            manual_export_supported=False,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=True,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "telegram_api_gate_closed"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="substack_newsletter",
            display_name="Substack Newsletter",
            platform_family="substack",
            platform_role="owned_long_form",
            strategy_tier="primary",
            destination_kind="newsletter",
            default_current_mode="manual_export_only",
            allowed_current_modes=("manual_export_only",),
            future_modes=("browser_assisted_lab",),
            primary_payload_class_ids=("substack_newsletter_issue", "substack_manual_export_package"),
            manual_export_supported=True,
            browser_assisted_lab_supported=True,
            api_available_future=False,
            api_write_available_future=False,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "session_automation_blocked", "no_substack_public_publish_api"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="linkedin_member_profile",
            display_name="LinkedIn Member Profile",
            platform_family="linkedin",
            platform_role="professional_credibility",
            strategy_tier="secondary",
            destination_kind="member_profile",
            default_current_mode="preview_only",
            allowed_current_modes=("preview_only",),
            future_modes=("supervised_api_write",),
            primary_payload_class_ids=("linkedin_member_post",),
            manual_export_supported=False,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=True,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "linkedin_oauth_gate_closed"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="linkedin_organization_page",
            display_name="LinkedIn Organization Page",
            platform_family="linkedin",
            platform_role="professional_credibility",
            strategy_tier="secondary",
            destination_kind="organization_page",
            default_current_mode="preview_only",
            allowed_current_modes=("preview_only",),
            future_modes=("supervised_api_write",),
            primary_payload_class_ids=("linkedin_organization_post",),
            manual_export_supported=False,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=True,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "linkedin_org_urn_missing"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="threads_profile",
            display_name="Threads Profile",
            platform_family="threads",
            platform_role="expansion_distribution",
            strategy_tier="expansion",
            destination_kind="profile",
            default_current_mode="preview_only",
            allowed_current_modes=("preview_only",),
            future_modes=("supervised_api_write",),
            primary_payload_class_ids=("threads_text_post",),
            manual_export_supported=False,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=True,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "meta_app_review_pending"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="instagram_professional_account",
            display_name="Instagram Professional Account",
            platform_family="instagram",
            platform_role="expansion_distribution",
            strategy_tier="expansion",
            destination_kind="professional_account",
            default_current_mode="preview_only",
            allowed_current_modes=("preview_only",),
            future_modes=("supervised_api_write",),
            primary_payload_class_ids=("instagram_caption_media_package",),
            manual_export_supported=True,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=True,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "instagram_content_publish_gate_closed"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="facebook_page",
            display_name="Facebook Page",
            platform_family="facebook",
            platform_role="expansion_distribution",
            strategy_tier="expansion",
            destination_kind="page",
            default_current_mode="preview_only",
            allowed_current_modes=("preview_only",),
            future_modes=("supervised_api_write",),
            primary_payload_class_ids=("facebook_page_text_link_post",),
            manual_export_supported=False,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=True,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "facebook_page_access_token_missing"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="tiktok_account",
            display_name="TikTok Account",
            platform_family="tiktok",
            platform_role="later_video_distribution",
            strategy_tier="later",
            destination_kind="account",
            default_current_mode="preview_only",
            allowed_current_modes=("preview_only",),
            future_modes=("supervised_api_write",),
            primary_payload_class_ids=("tiktok_video_metadata_packet",),
            manual_export_supported=True,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=True,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "tiktok_audit_pending"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
        PlatformUniverseRegistryEntry(
            platform_id="youtube_channel",
            display_name="YouTube Channel",
            platform_family="youtube",
            platform_role="later_video_distribution",
            strategy_tier="later",
            destination_kind="channel",
            default_current_mode="preview_only",
            allowed_current_modes=("preview_only",),
            future_modes=("supervised_api_write",),
            primary_payload_class_ids=("youtube_video_metadata_packet",),
            manual_export_supported=True,
            browser_assisted_lab_supported=False,
            api_available_future=True,
            api_write_available_future=True,
            live_write_allowed_now=False,
            dispatchable_now=False,
            public_postable_now=False,
            credential_required_for_live=True,
            account_binding_required_for_live=True,
            approval_payload_hash_required=True,
            approval_ledger_required=True,
            outbox_required=True,
            idempotency_required=True,
            kill_switch_required=True,
            redacted_audit_required=True,
            manual_fallback_required=True,
            official_docs_required_before_live=True,
            re_ground_required_before_live=True,
            live_gate_status="disabled",
            blocked_reasons=("platform_live_write_not_allowed", "youtube_oauth_pending"),
            forbidden_current_actions=("api_post", "scheduler_post", "auto_reply", "direct_message"),
            no_autonomous_reply_dm_scheduler_scraping=True,
        ),
    )


PLATFORMS: tuple[PlatformUniverseRegistryEntry, ...] = build_platform_universe_registry_v2()
PLATFORMS_BY_ID: dict[str, PlatformUniverseRegistryEntry] = {p.platform_id: p for p in PLATFORMS}


def registry_by_platform_id() -> dict[str, PlatformUniverseRegistryEntry]:
    """Return map of platform entries indexed by platform_id."""
    return PLATFORMS_BY_ID


def lookup_platform(platform_id: str) -> PlatformUniverseRegistryEntry:
    """Look up a platform by ID, raising UnsupportedPlatformError if not found."""
    try:
        return PLATFORMS_BY_ID[platform_id]
    except KeyError as exc:
        raise UnsupportedPlatformError(f"unsupported_platform:{platform_id}") from exc


def assert_no_live_write_allowed(registry_data: dict[str, Any]) -> None:
    """Assert that none of the platforms allow live write, dispatch, or posting now."""
    rows = registry_data.get("rows", [])
    if not rows:
        # Fallback to direct check on registry_data if not formatted as a packet
        rows = registry_data.get("platform_entries", [])
    for row in rows:
        if row.get("live_write_allowed_now") is not False:
            raise AssertionError(f"live_write_allowed_now must be False for platform {row.get('platform_id')}")
        if row.get("dispatchable_now") is not False:
            raise AssertionError(f"dispatchable_now must be False for platform {row.get('platform_id')}")
        if row.get("public_postable_now") is not False:
            raise AssertionError(f"public_postable_now must be False for platform {row.get('platform_id')}")


def assert_no_secret_shaped_material(data: Any) -> None:
    """Recursively verify that no string in data contains secret-shaped material."""
    if isinstance(data, str):
        for pattern in SECRET_PATTERNS:
            if pattern.search(data):
                raise AssertionError("Secret-shaped string detected in registry output.")
    elif isinstance(data, dict):
        for v in data.values():
            assert_no_secret_shaped_material(v)
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            assert_no_secret_shaped_material(item)


def platform_universe_registry_v2_packet() -> dict[str, Any]:
    """Generate the platform universe registry v2 JSON-serializable packet."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "platform_entries": [asdict(entry) for entry in PLATFORMS],
    }
    assert_no_live_write_allowed(packet)
    assert_no_secret_shaped_material(packet)
    return packet
