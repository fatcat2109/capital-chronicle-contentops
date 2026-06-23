"""Primary payload classes contract for ContentOps.

Deterministic local-only specifications for platform payload classes.
All rows default to not public postable, not dispatchable, and not live write allowed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_PLATFORM_UNIVERSE_REGISTRY_V2_PRIMARY_PAYLOAD_CLASSES_CORE_V0"
MODEL = "contentops.primary_payload_classes_contract"
MODEL_VERSION = "0174U1_PRIMARY_PAYLOAD_CLASSES_CONTRACT_V1"


@dataclass(frozen=True)
class PayloadClassEntry:
    payload_class_id: str
    platform_id: str
    payload_family: str
    default_current_status: str
    text_fields: tuple[str, ...]
    media_fields: tuple[str, ...]
    media_required: bool
    supports_threading: bool
    supports_link_preview: bool
    character_limit_class: str
    citation_required_policy: str
    limitation_required_policy: str
    no_financial_advice_required: bool  # Must be True
    no_signal_language_required: bool  # Must be True
    source_requirement_policy: str
    approval_hash_input_fields: tuple[str, ...]
    dispatch_transform_allowed_after_approval: bool  # Must be False
    public_postable_now: bool  # Must be False
    dispatchable_now: bool  # Must be False
    live_write_allowed_now: bool  # Must be False
    manual_export_allowed: bool
    browser_assisted_lab_allowed: bool
    future_live_gate_required: bool
    blocked_reasons: tuple[str, ...]
    forbidden_current_actions: tuple[str, ...]


class UnsupportedPayloadClassError(ValueError):
    """Raised when payload class lookup fails closed."""


def build_primary_payload_classes() -> tuple[PayloadClassEntry, ...]:
    """Build specifications for all primary payload classes."""
    return (
        PayloadClassEntry(
            payload_class_id="x_short_post",
            platform_id="x_profile",
            payload_family="x",
            default_current_status="preview_only",
            text_fields=("body_text",),
            media_fields=("media_attachments",),
            media_required=False,
            supports_threading=False,
            supports_link_preview=True,
            character_limit_class="short_post_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("body_text", "media_attachments"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
        PayloadClassEntry(
            payload_class_id="x_thread",
            platform_id="x_profile",
            payload_family="x",
            default_current_status="preview_only",
            text_fields=("body_text_parts",),
            media_fields=("media_attachments_parts",),
            media_required=False,
            supports_threading=True,
            supports_link_preview=True,
            character_limit_class="short_post_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("body_text_parts", "media_attachments_parts"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
        PayloadClassEntry(
            payload_class_id="telegram_operator_review_message",
            platform_id="telegram_remote_operator_inbox",
            payload_family="telegram",
            default_current_status="local_only",
            text_fields=("challenge_text", "approval_note"),
            media_fields=(),
            media_required=False,
            supports_threading=False,
            supports_link_preview=False,
            character_limit_class="telegram_review_limit",
            citation_required_policy="none",
            limitation_required_policy="none",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="none",
            approval_hash_input_fields=("challenge_text",),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=False,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false", "not_public_dest"),
            forbidden_current_actions=("live_dispatch", "public_post"),
        ),
        PayloadClassEntry(
            payload_class_id="telegram_channel_update",
            platform_id="telegram_channel_destination",
            payload_family="telegram",
            default_current_status="preview_only",
            text_fields=("message_text",),
            media_fields=("media_attachments",),
            media_required=False,
            supports_threading=False,
            supports_link_preview=True,
            character_limit_class="telegram_channel_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("message_text", "media_attachments"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
        PayloadClassEntry(
            payload_class_id="substack_newsletter_issue",
            platform_id="substack_newsletter",
            payload_family="substack",
            default_current_status="manual_export_only",
            text_fields=("body_markdown", "seo_title", "seo_description"),
            media_fields=("image_attachments",),
            media_required=False,
            supports_threading=False,
            supports_link_preview=True,
            character_limit_class="long_form_limit",
            citation_required_policy="strict",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("body_markdown", "seo_title", "seo_description"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=True,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false", "no_substack_publish_api"),
            forbidden_current_actions=("live_dispatch", "api_post"),
        ),
        PayloadClassEntry(
            payload_class_id="substack_manual_export_package",
            platform_id="substack_newsletter",
            payload_family="substack",
            default_current_status="manual_export_only",
            text_fields=("body_markdown",),
            media_fields=("image_attachments",),
            media_required=False,
            supports_threading=False,
            supports_link_preview=True,
            character_limit_class="long_form_limit",
            citation_required_policy="strict",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("body_markdown",),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=True,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false", "no_substack_publish_api"),
            forbidden_current_actions=("live_dispatch", "api_post"),
        ),
        PayloadClassEntry(
            payload_class_id="linkedin_member_post",
            platform_id="linkedin_member_profile",
            payload_family="linkedin",
            default_current_status="preview_only",
            text_fields=("post_text",),
            media_fields=("media_attachments",),
            media_required=False,
            supports_threading=False,
            supports_link_preview=True,
            character_limit_class="linkedin_post_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("post_text", "media_attachments"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
        PayloadClassEntry(
            payload_class_id="linkedin_organization_post",
            platform_id="linkedin_organization_page",
            payload_family="linkedin",
            default_current_status="preview_only",
            text_fields=("post_text",),
            media_fields=("media_attachments",),
            media_required=False,
            supports_threading=False,
            supports_link_preview=True,
            character_limit_class="linkedin_post_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("post_text", "media_attachments"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
        PayloadClassEntry(
            payload_class_id="threads_text_post",
            platform_id="threads_profile",
            payload_family="threads",
            default_current_status="preview_only",
            text_fields=("post_text",),
            media_fields=("media_attachments",),
            media_required=False,
            supports_threading=False,
            supports_link_preview=True,
            character_limit_class="threads_post_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("post_text", "media_attachments"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
        PayloadClassEntry(
            payload_class_id="instagram_caption_media_package",
            platform_id="instagram_professional_account",
            payload_family="instagram",
            default_current_status="preview_only",
            text_fields=("caption_text",),
            media_fields=("image_or_video_attachments",),
            media_required=True,
            supports_threading=False,
            supports_link_preview=False,
            character_limit_class="instagram_post_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("caption_text", "image_or_video_attachments"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
        PayloadClassEntry(
            payload_class_id="facebook_page_text_link_post",
            platform_id="facebook_page",
            payload_family="facebook",
            default_current_status="preview_only",
            text_fields=("post_text", "link_url"),
            media_fields=("media_attachments",),
            media_required=False,
            supports_threading=False,
            supports_link_preview=True,
            character_limit_class="facebook_post_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("post_text", "link_url", "media_attachments"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
        PayloadClassEntry(
            payload_class_id="tiktok_video_metadata_packet",
            platform_id="tiktok_account",
            payload_family="tiktok",
            default_current_status="preview_only",
            text_fields=("title", "description"),
            media_fields=("video_attachment",),
            media_required=True,
            supports_threading=False,
            supports_link_preview=False,
            character_limit_class="tiktok_post_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("title", "description", "video_attachment"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
        PayloadClassEntry(
            payload_class_id="youtube_video_metadata_packet",
            platform_id="youtube_channel",
            payload_family="youtube",
            default_current_status="preview_only",
            text_fields=("title", "description"),
            media_fields=("video_attachment",),
            media_required=True,
            supports_threading=False,
            supports_link_preview=False,
            character_limit_class="youtube_post_limit",
            citation_required_policy="strict_when_claimed",
            limitation_required_policy="strict",
            no_financial_advice_required=True,
            no_signal_language_required=True,
            source_requirement_policy="citation_preservation",
            approval_hash_input_fields=("title", "description", "video_attachment"),
            dispatch_transform_allowed_after_approval=False,
            public_postable_now=False,
            dispatchable_now=False,
            live_write_allowed_now=False,
            manual_export_allowed=True,
            browser_assisted_lab_allowed=False,
            future_live_gate_required=True,
            blocked_reasons=("live_write_allowed_now_false",),
            forbidden_current_actions=("live_dispatch", "autonomous_publish"),
        ),
    )


PAYLOAD_CLASSES: tuple[PayloadClassEntry, ...] = build_primary_payload_classes()
PAYLOAD_CLASSES_BY_ID: dict[str, PayloadClassEntry] = {p.payload_class_id: p for p in PAYLOAD_CLASSES}


def lookup_payload_class(payload_class_id: str) -> PayloadClassEntry:
    """Look up a payload class specification by ID."""
    try:
        return PAYLOAD_CLASSES_BY_ID[payload_class_id]
    except KeyError as exc:
        raise UnsupportedPayloadClassError(f"unsupported_payload_class:{payload_class_id}") from exc


def payload_classes_by_platform_id() -> dict[str, list[PayloadClassEntry]]:
    """Return map of payload classes list indexed by platform_id."""
    res: dict[str, list[PayloadClassEntry]] = {}
    for p in PAYLOAD_CLASSES:
        res.setdefault(p.platform_id, []).append(p)
    return res


def primary_payload_classes_packet() -> dict[str, Any]:
    """Generate the primary payload classes JSON-serializable packet."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "payload_class_entries": [asdict(entry) for entry in PAYLOAD_CLASSES],
    }
    return packet
