"""Platform universe registry v2 for ContentOps.

Deterministic local-only registry for platform families.
No live dispatch, network, provider, credential, env, scheduler, scraping, or DM behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Any

from live_contentops.primary_payload_classes_contract import PAYLOAD_CLASSES_BY_ID

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


def registry_by_platform_id() -> dict[str, PlatformRegistryEntryWrapper]:
    """Return map of platform entries indexed by platform_id."""
    return PLATFORMS_BY_ID



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


# --- Compatibility Shim for downstream modules (e.g. primary_platform_payload_preview_contracts) ---

from live_contentops.primary_payload_classes_contract import (
    PayloadClassEntry,
    UnsupportedPayloadClassError,
    build_primary_payload_classes,
)

PAYLOAD_CLASSES: tuple[PayloadClassEntry, ...] = build_primary_payload_classes()
PAYLOAD_CLASSES_BY_ID = {p.payload_class_id: p for p in PAYLOAD_CLASSES}

NO_LIVE_DEFAULTS: dict[str, bool] = {
    "live_dispatch_enabled": False,
    "platform_api_called": False,
    "provider_api_called": False,
    "credential_hydrated": False,
    "env_read": False,
    "scheduler_enabled": False,
    "autonomous_posting_allowed": False,
    "scraping_performed": False,
    "dm_or_reply_automation_allowed": False,
    "dispatch_ready": False,
    "public_postable": False,
}

class PlatformRegistryEntryWrapper:
    def __init__(self, entry: Any, requested_id: str | None = None):
        if isinstance(entry, PlatformRegistryEntryWrapper):
            entry = entry._entry
        object.__setattr__(self, "_entry", entry)
        object.__setattr__(self, "_requested_id", requested_id)
    @property
    def __dataclass_fields__(self):
        return self._entry.__dataclass_fields__

    def __getattr__(self, name):
        if name == "platform_id" and self._requested_id is not None:
            return self._requested_id
        elif name == "platform_family":
            return self._entry.platform_family
        elif name == "priority_tier":
            return self._entry.strategy_tier
        elif name == "default_publish_mode":
            return self._entry.default_current_mode
        elif name == "payload_classes_supported":
            ids = self._entry.primary_payload_class_ids
            mapped = []
            for x in ids:
                if x == "telegram_operator_review_inbox_message":
                    mapped.append("telegram_operator_review_message")
                    mapped.append("telegram_operator_review_inbox_message")
                elif x == "substack_manual_export_package":
                    mapped.append("substack_longform_post")
                    mapped.append("substack_manual_export_package")
                elif x == "linkedin_member_post":
                    mapped.append("linkedin_professional_post")
                    mapped.append("linkedin_member_post")
                elif x == "threads_text_post":
                    mapped.append("threads_short_post")
                    mapped.append("threads_text_post")
                elif x == "instagram_caption_media_package":
                    mapped.append("instagram_caption_asset_packet")
                    mapped.append("instagram_carousel_script")
                    mapped.append("instagram_caption_media_package")
                elif x == "facebook_page_text_link_post":
                    mapped.append("facebook_page_post")
                    mapped.append("facebook_page_text_link_post")
                else:
                    mapped.append(x)
            return tuple(mapped)
        elif name == "manual_export_supported":
            return self._entry.manual_export_supported
        elif name == "preview_supported":
            return True
        elif name == "soft_guidelines":
            pid = self._entry.platform_id
            if pid == "x_profile" or pid == "x":
                return ("fast_public_narrative", "preserve_citations_when_claimed")
            elif pid == "telegram_remote_operator_inbox" or pid == "telegram_remote_operator":
                return ("review_control_only", "must_not_publish")
            elif pid == "telegram_channel_destination":
                return ("controlled_channel_distribution", "hash_exact_payload")
            elif pid == "substack_newsletter":
                return ("owned_audience", "citation_footer", "seo_metadata")
            elif pid == "linkedin_member_profile" or pid == "linkedin":
                return ("founder_voice", "institutional_credibility")
            elif pid == "threads_profile" or pid == "threads":
                return ("lightweight_conversation",)
            elif pid == "instagram_professional_account" or pid == "instagram":
                return ("visual_brand_attachment", "carousel_or_grid_shape")
            elif pid == "facebook_page_text_link_post" or pid == "facebook_page":
                return ("local_community_page_context",)
            return ()
        elif name == "evidence_refs":
            return ()
        elif name == "blocked_reasons":
            # Map new blocked reasons to old ones for legacy validations in contract modules
            pid = self._entry.platform_id
            if pid == "substack_newsletter":
                return ("no_substack_public_publish_api_gate", "session_automation_blocked")
            elif pid == "telegram_remote_operator_inbox" or pid == "telegram_remote_operator":
                return ("not_publish_destination", "telegram_api_gate_closed")
            elif pid == "telegram_channel_destination":
                return ("telegram_api_gate_closed", "bot_admin_gate_closed")
            elif pid == "x_profile" or pid == "x":
                return ("x_api_gate_closed", "credential_gate_closed")
            elif pid == "linkedin_member_profile" or pid == "linkedin":
                return ("linkedin_oauth_gate_closed", "permission_review_closed")
            elif pid == "threads_profile" or pid == "threads":
                return ("meta_app_review_closed",)
            return self._entry.blocked_reasons
        elif name == "safety_flags":
            return {k: False for k in NO_LIVE_DEFAULTS}
        return getattr(self._entry, name)

    def __setattr__(self, name, value):
        setattr(self._entry, name, value)

class PayloadClassEntryWrapper:
    def __init__(self, entry: PayloadClassEntry, requested_id: str | None = None):
        object.__setattr__(self, "_entry", entry)
        object.__setattr__(self, "_requested_id", requested_id)
    @property
    def __dataclass_fields__(self):
        return self._entry.__dataclass_fields__

    def __getattr__(self, name):
        if name == "payload_class_id" and self._requested_id is not None:
            return self._requested_id
        elif name == "platform_family":
            return self._entry.payload_family
        elif name == "media_shape":
            cid = self._entry.payload_class_id
            if cid in ("instagram_caption_asset_packet", "instagram_caption_media_package"):
                return "asset_packet"
            elif cid == "instagram_carousel_script":
                return "carousel_assets"
            elif cid in ("tiktok_video_metadata_packet", "youtube_video_metadata_packet"):
                return "video_rights_metadata"
            elif cid in ("substack_newsletter_issue", "substack_longform_post", "substack_manual_export_package"):
                return "optional_assets"
            elif cid == "telegram_channel_update":
                return "optional_image_or_link"
            elif cid in ("telegram_operator_review_message", "telegram_operator_review_inbox_message"):
                return "none"
            elif cid in ("x_short_post", "x_thread", "linkedin_professional_post", "linkedin_member_post", "threads_short_post", "threads_text_post", "facebook_page_post", "facebook_page_text_link_post"):
                return "optional_link_or_media"
            return "optional_image" if self._entry.media_fields else "none"
        elif name == "no_signal_required":
            return self._entry.no_financial_advice_required
        elif name == "no_advice_required":
            return self._entry.no_financial_advice_required
        elif name == "source_citation_required_when_claimed":
            return self._entry.citation_required_policy == "required_when_claims_exist"
        elif name == "approval_required":
            return True
        elif name == "manual_export_supported":
            return self._entry.manual_export_allowed
        elif name == "evidence_refs":
            return ()
        elif name == "blocked_reasons":
            return ("live_gate_closed", "approval_required", "dispatch_revalidation_not_built")
        return getattr(self._entry, name)

    def __setattr__(self, name, value):
        setattr(self._entry, name, value)

PlatformRegistryEntry = PlatformRegistryEntryWrapper

LEGACY_PLATFORM_MAP = {
    "x": "x_profile",
    "telegram_remote_operator": "telegram_remote_operator_inbox",
    "telegram_channel_destination": "telegram_channel_destination",
    "substack_newsletter": "substack_newsletter",
    "linkedin": "linkedin_member_profile",
    "threads": "threads_profile",
    "instagram": "instagram_professional_account",
    "facebook_page": "facebook_page",
    "tiktok": "tiktok_account",
    "youtube": "youtube_channel",
}

_v2_platforms = build_platform_universe_registry_v2()
_v2_platforms_by_id = {p.platform_id: p for p in _v2_platforms}

PLATFORMS: tuple[PlatformRegistryEntryWrapper, ...] = tuple(
    PlatformRegistryEntryWrapper(_v2_platforms_by_id[v2_id], requested_id=legacy_id)
    for legacy_id, v2_id in LEGACY_PLATFORM_MAP.items()
    if v2_id in _v2_platforms_by_id
)

PLATFORMS_BY_ID: dict[str, PlatformRegistryEntryWrapper] = {}
for p in _v2_platforms:
    PLATFORMS_BY_ID[p.platform_id] = PlatformRegistryEntryWrapper(p, requested_id=p.platform_id)

for legacy_id, v2_id in LEGACY_PLATFORM_MAP.items():
    if v2_id in _v2_platforms_by_id:
        PLATFORMS_BY_ID[legacy_id] = PlatformRegistryEntryWrapper(_v2_platforms_by_id[v2_id], requested_id=legacy_id)

def lookup_platform(platform_id: str) -> PlatformRegistryEntryWrapper:
    """Look up a platform by ID, raising UnsupportedPlatformError if not found."""
    mapped_id = LEGACY_PLATFORM_MAP.get(platform_id, platform_id)
    try:
        return PlatformRegistryEntryWrapper(PLATFORMS_BY_ID[mapped_id], requested_id=platform_id)
    except KeyError as exc:
        raise UnsupportedPlatformError(f"unsupported_platform:{platform_id}") from exc


def lookup_payload_class(payload_class_id: str) -> PayloadClassEntryWrapper:
    from live_contentops.primary_payload_classes_contract import lookup_payload_class as raw_lookup
    # Map legacy payload class name if needed
    mapped_id = payload_class_id
    if payload_class_id == "telegram_operator_review_inbox_message":
        mapped_id = "telegram_operator_review_message"
    elif payload_class_id == "substack_longform_post":
        mapped_id = "substack_manual_export_package"
    elif payload_class_id == "linkedin_professional_post":
        mapped_id = "linkedin_member_post"
    elif payload_class_id == "threads_short_post":
        mapped_id = "threads_text_post"
    elif payload_class_id in ("instagram_caption_asset_packet", "instagram_carousel_script"):
        mapped_id = "instagram_caption_media_package"
    elif payload_class_id == "facebook_page_post":
        mapped_id = "facebook_page_text_link_post"

    return PayloadClassEntryWrapper(raw_lookup(mapped_id), requested_id=payload_class_id)

def validate_payload_class_compatibility(platform_id: str, payload_class_id: str) -> dict[str, Any]:
    platform = lookup_platform(platform_id)
    payload = lookup_payload_class(payload_class_id)
    compatible = payload.payload_family == platform.platform_family and payload_class_id in platform.payload_classes_supported
    return {
        "platform_id": platform_id,
        "payload_class_id": payload_class_id,
        "compatible": compatible,
        "reason": "compatible" if compatible else "payload_class_not_supported_by_platform",
    }

def registry_checksum() -> str:
    from hashlib import sha256
    import json
    packet = platform_universe_registry_v2_packet()
    return sha256(json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()



