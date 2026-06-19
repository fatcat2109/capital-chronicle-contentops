"""Platform universe registry v2 for ContentOps 0174U1.

Deterministic local-only registry for platform families and payload classes.
No live dispatch, network, provider, credential, env, scheduler, scraping, or DM behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0174U1_PLATFORM_UNIVERSE_REGISTRY_V2_AND_PRIMARY_PAYLOAD_CLASSES_CONTRACT_V0"
MODEL = "contentops.platform_universe_registry_v2"
MODEL_VERSION = "0174U1_PLATFORM_UNIVERSE_REGISTRY_V2_V1"
SOURCE_BASELINE_COMMIT = "ae424c27c69338aa189edaf23f8240151cbff6ac"
DOC_REL_DIR = Path("docs") / "automation" / "0174U1"
PACKET_FILENAME = "platform_universe_registry_v2_packet.json"
RUNBOOK_FILENAME = "platform_universe_registry_v2.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174U2_PRIMARY_PLATFORM_PAYLOAD_PREVIEW_CONTRACTS_V0"

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


@dataclass(frozen=True)
class PlatformRegistryEntry:
    platform_id: str
    platform_family: str
    platform_role: str
    priority_tier: str
    build_phase: str
    default_publish_mode: str
    live_gate_required: bool
    credential_gate_required: bool
    api_gate_required: bool
    manual_export_supported: bool
    preview_supported: bool
    payload_classes_supported: tuple[str, ...]
    hard_limits: dict[str, Any]
    soft_guidelines: tuple[str, ...]
    safety_flags: dict[str, bool]
    evidence_refs: tuple[str, ...]
    official_docs_refs: tuple[str, ...]
    current_capability: str
    future_capability: str
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class PayloadClassEntry:
    payload_class_id: str
    platform_family: str
    content_lane_support: tuple[str, ...]
    body_shape: str
    media_shape: str
    title_supported: bool
    subtitle_supported: bool
    thread_supported: bool
    markdown_export_supported: bool
    manual_export_supported: bool
    live_gate_required: bool
    approval_required: bool
    payload_hash_required: bool
    source_citation_required_when_claimed: bool
    no_signal_required: bool
    no_advice_required: bool
    dispatch_ready_default: bool
    public_postable_default: bool
    evidence_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]


class UnsupportedPlatformError(ValueError):
    """Raised when platform lookup fails closed."""


class UnsupportedPayloadClassError(ValueError):
    """Raised when payload class lookup fails closed."""


def _safety_flags(*, remote_review_only: bool = False, future_supervised: bool = True) -> dict[str, bool]:
    flags = dict(NO_LIVE_DEFAULTS)
    flags["manual_export_or_preview_only"] = not remote_review_only
    flags["future_supervised_dispatch_possible"] = future_supervised
    return flags


def _platform_entries() -> tuple[PlatformRegistryEntry, ...]:
    common_evidence = (
        "docs/automation/0174U0/heavy_strategy_recon_report.md",
        "docs/CAPITAL_CHRONICLE_CONTENTOPS_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AFTER_0174AO.md",
        "docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",
    )
    return (
        PlatformRegistryEntry("x", "x", "primary_distribution", "primary_now", "preview_now", "preview_only", True, True, True, False, True, ("x_short_post", "x_thread"), {"text": "short_form_or_thread_preview"}, ("fast_public_narrative", "preserve_citations_when_claimed"), _safety_flags(), common_evidence, ("https://developer.x.com/",), "preview_contract_only", "future_supervised_live_gate_after_platform_policy_and_budget_gate", ("x_api_gate_closed", "credential_gate_closed")),
        PlatformRegistryEntry("telegram_remote_operator", "telegram_remote_operator", "remote_operator_review", "primary_now", "contract_now", "remote_review_only", True, True, True, False, True, ("telegram_operator_review_message",), {"destination": "operator_review_not_public_channel"}, ("review_control_only", "must_not_publish"), _safety_flags(remote_review_only=True, future_supervised=False), common_evidence, ("https://core.telegram.org/bots/api",), "local_review_contract_only", "future_read_only_or_review_gate_only", ("not_publish_destination", "telegram_api_gate_closed")),
        PlatformRegistryEntry("telegram_channel_destination", "telegram_channel_destination", "controlled_channel_distribution", "primary_now", "preview_now", "preview_only", True, True, True, False, True, ("telegram_channel_update",), {"method_future": "sendMessage_or_sendPhoto_after_gate"}, ("controlled_channel_distribution", "hash_exact_payload"), _safety_flags(), common_evidence, ("https://core.telegram.org/bots/api",), "channel_payload_preview_only", "future_supervised_send_after_gate", ("telegram_api_gate_closed", "bot_admin_gate_closed")),
        PlatformRegistryEntry("substack_newsletter", "substack_newsletter", "owned_long_form", "primary_now", "manual_export_now", "manual_export_only", True, True, True, True, True, ("substack_newsletter_issue", "substack_longform_post"), {"export": "markdown_manual_export"}, ("owned_audience", "citation_footer", "seo_metadata"), _safety_flags(), common_evidence, ("https://support.substack.com/",), "manual_markdown_export_only", "future_manual_publish_record_without_session_automation", ("no_substack_public_publish_api_gate", "session_automation_blocked")),
        PlatformRegistryEntry("linkedin", "linkedin", "professional_credibility", "secondary_next", "preview_now", "preview_only", True, True, True, False, True, ("linkedin_professional_post",), {"tone": "professional_credibility"}, ("founder_voice", "institutional_credibility"), _safety_flags(), common_evidence, ("https://learn.microsoft.com/linkedin/",), "professional_preview_only", "future_supervised_posts_api_after_review", ("linkedin_oauth_gate_closed", "permission_review_closed")),
        PlatformRegistryEntry("threads", "threads", "expansion_distribution", "expansion_later", "preview_now", "preview_only", True, True, True, False, True, ("threads_short_post",), {"shape": "short_conversation_preview"}, ("lightweight_conversation",), _safety_flags(), common_evidence, ("https://developers.facebook.com/docs/threads/",), "expansion_preview_only", "future_meta_threads_gate", ("meta_app_review_closed",)),
        PlatformRegistryEntry("instagram", "instagram", "expansion_distribution", "expansion_later", "preview_now", "preview_only", True, True, True, True, True, ("instagram_caption_asset_packet", "instagram_carousel_script"), {"requires": "asset_packet_or_carousel_script"}, ("visual_education", "rights_status_required"), _safety_flags(), common_evidence, ("https://developers.facebook.com/docs/",), "asset_packet_preview_only", "future_content_publishing_api_gate", ("instagram_content_publish_gate_closed", "media_url_gate_closed")),
        PlatformRegistryEntry("facebook_page", "facebook_page", "expansion_distribution", "expansion_later", "preview_now", "preview_only", True, True, True, False, True, ("facebook_page_post",), {"destination": "page_post_preview"}, ("meta_page_distribution",), _safety_flags(), common_evidence, ("https://developers.facebook.com/docs/",), "page_post_preview_only", "future_page_publish_after_review", ("pages_manage_posts_gate_closed",)),
        PlatformRegistryEntry("tiktok", "tiktok", "later_video_distribution", "video_later", "video_future_gate", "preview_only", True, True, True, True, True, ("video_script_metadata_packet", "tiktok_video_metadata_packet"), {"media": "video_metadata_only"}, ("rights_checklist_required",), _safety_flags(), common_evidence, ("https://developers.tiktok.com/doc/content-posting-api-get-started/",), "video_metadata_packet_only", "future_video_posting_api_after_audit", ("video_future_gate_closed", "tiktok_audit_closed")),
        PlatformRegistryEntry("youtube", "youtube", "later_video_distribution", "video_later", "video_future_gate", "preview_only", True, True, True, True, True, ("video_script_metadata_packet", "youtube_video_metadata_packet"), {"media": "video_metadata_only"}, ("rights_checklist_required", "quota_awareness"), _safety_flags(), common_evidence, ("https://developers.google.com/youtube/v3/docs/videos/insert",), "video_metadata_packet_only", "future_upload_after_oauth_quota_gate", ("video_future_gate_closed", "youtube_oauth_gate_closed")),
    )


def _payload_entries() -> tuple[PayloadClassEntry, ...]:
    lanes = ("pre_alpha_process", "grounded_news_context", "future_artifact_backed")
    payload_specs = (
        ("x_short_post", "x", "short_text", "optional_link_or_media", False, False, False, False, False),
        ("x_thread", "x", "ordered_short_text_parts", "optional_link_or_media", False, False, True, False, False),
        ("telegram_channel_update", "telegram_channel_destination", "message_text", "optional_image_or_link", False, False, False, False, False),
        ("telegram_operator_review_message", "telegram_remote_operator", "review_challenge_message", "none", False, False, False, False, False),
        ("substack_newsletter_issue", "substack_newsletter", "newsletter_markdown", "optional_assets", True, True, False, True, True),
        ("substack_longform_post", "substack_newsletter", "longform_markdown", "optional_assets", True, True, False, True, True),
        ("linkedin_professional_post", "linkedin", "professional_post_text", "optional_link_or_media", False, False, False, False, False),
        ("threads_short_post", "threads", "short_text", "optional_link_or_media", False, False, True, False, False),
        ("instagram_caption_asset_packet", "instagram", "caption_plus_asset_manifest", "asset_packet", False, False, False, False, True),
        ("instagram_carousel_script", "instagram", "carousel_slide_script", "carousel_assets", True, False, False, False, True),
        ("facebook_page_post", "facebook_page", "page_post_text", "optional_link_or_media", False, False, False, False, False),
        ("video_script_metadata_packet", "tiktok", "video_script_metadata", "video_rights_metadata", True, True, False, False, True),
        ("youtube_video_metadata_packet", "youtube", "youtube_metadata", "video_rights_metadata", True, True, False, False, True),
        ("tiktok_video_metadata_packet", "tiktok", "tiktok_metadata", "video_rights_metadata", True, True, False, False, True),
    )
    return tuple(
        PayloadClassEntry(
            payload_id,
            platform,
            lanes,
            body_shape,
            media_shape,
            title_supported,
            subtitle_supported,
            thread_supported,
            markdown_export_supported,
            manual_export_supported,
            True,
            True,
            True,
            True,
            True,
            True,
            False,
            False,
            ("docs/automation/0174U0/heavy_strategy_recon_report.md",),
            ("live_gate_closed", "approval_required", "dispatch_revalidation_not_built"),
        )
        for payload_id, platform, body_shape, media_shape, title_supported, subtitle_supported,
        thread_supported, markdown_export_supported, manual_export_supported in payload_specs
    )


PLATFORMS: tuple[PlatformRegistryEntry, ...] = _platform_entries()
PAYLOAD_CLASSES: tuple[PayloadClassEntry, ...] = _payload_entries()
PLATFORMS_BY_ID = {entry.platform_id: entry for entry in PLATFORMS}
PAYLOAD_CLASSES_BY_ID = {entry.payload_class_id: entry for entry in PAYLOAD_CLASSES}


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _checksum(data: dict[str, Any]) -> str:
    return sha256(_json(data).encode("utf-8")).hexdigest()


def lookup_platform(platform_id: str) -> PlatformRegistryEntry:
    try:
        return PLATFORMS_BY_ID[platform_id]
    except KeyError as exc:
        raise UnsupportedPlatformError(f"unsupported_platform:{platform_id}") from exc


def lookup_payload_class(payload_class_id: str) -> PayloadClassEntry:
    try:
        return PAYLOAD_CLASSES_BY_ID[payload_class_id]
    except KeyError as exc:
        raise UnsupportedPayloadClassError(f"unsupported_payload_class:{payload_class_id}") from exc


def list_primary_triangle() -> tuple[str, ...]:
    return ("x", "telegram_channel_destination", "substack_newsletter")


def list_expansion_platforms() -> tuple[str, ...]:
    return ("threads", "instagram", "facebook_page")


def validate_payload_class_compatibility(platform_id: str, payload_class_id: str) -> dict[str, Any]:
    platform = lookup_platform(platform_id)
    payload = lookup_payload_class(payload_class_id)
    compatible = payload.platform_family == platform.platform_family and payload_class_id in platform.payload_classes_supported
    return {
        "platform_id": platform_id,
        "payload_class_id": payload_class_id,
        "compatible": compatible,
        "reason": "compatible" if compatible else "payload_class_not_supported_by_platform",
    }


def confirm_no_live_safety_flags() -> dict[str, Any]:
    checked_false = tuple(NO_LIVE_DEFAULTS)
    platform_results = {
        platform.platform_id: all(platform.safety_flags.get(flag) is False for flag in checked_false)
        for platform in PLATFORMS
    }
    payload_results = {
        payload.payload_class_id: (
            payload.dispatch_ready_default is False and payload.public_postable_default is False
        )
        for payload in PAYLOAD_CLASSES
    }
    return {
        "platform_flags_false": platform_results,
        "payload_defaults_false": payload_results,
        "all_clear": all(platform_results.values()) and all(payload_results.values()),
    }


def build_registry_packet() -> dict[str, Any]:
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "platform_entries": [asdict(entry) for entry in PLATFORMS],
        "payload_class_entries": [asdict(entry) for entry in PAYLOAD_CLASSES],
        "primary_triangle": list(list_primary_triangle()),
        "expansion_platforms": list(list_expansion_platforms()),
        "no_live_defaults": dict(NO_LIVE_DEFAULTS),
        "no_live_confirmation": confirm_no_live_safety_flags(),
        "next_heavy_batch_recommendation": NEXT_HEAVY_BATCH,
        "artifact_scope": "docs/automation/0174U1_only",
    }
    packet["registry_checksum"] = _checksum(packet)
    return packet


def registry_checksum() -> str:
    return build_registry_packet()["registry_checksum"]


def _assert_safe_output(repo_root: str | Path, output_dir: str | Path | None) -> Path:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174U1")
    return out


def render_runbook(packet: dict[str, Any]) -> str:
    lines = [
        "# 0174U1 Platform Universe Registry V2",
        "",
        f"- task_label: `{packet['task_label']}`",
        f"- model_version: `{packet['model_version']}`",
        f"- source_baseline_commit: `{packet['source_baseline_commit']}`",
        f"- registry_checksum: `{packet['registry_checksum']}`",
        f"- next_heavy_batch_recommendation: `{packet['next_heavy_batch_recommendation']}`",
        "",
        "## Platform tiers",
    ]
    for platform in packet["platform_entries"]:
        lines.append(
            f"- `{platform['platform_id']}`: `{platform['priority_tier']}` / "
            f"`{platform['platform_role']}` / `{platform['default_publish_mode']}`"
        )
    lines.extend(["", "## Payload classes"])
    for payload in packet["payload_class_entries"]:
        lines.append(
            f"- `{payload['payload_class_id']}` -> `{payload['platform_family']}`; "
            "dispatch_ready_default=`false`; public_postable_default=`false`"
        )
    lines.extend([
        "",
        "## No-live defaults",
        "",
        "All platform/API/provider/credential/env/scheduler/autonomous/scraping/DM flags default false.",
        "Official docs refs are string metadata only; this module performs no network behavior.",
        "",
        "## Scope confirmations",
        "",
        "- No UI/dashboard work.",
        "- No ingestion repo mutation.",
        "- No live/API/credential/provider/scheduler/scraping/DM behavior.",
        "- Artifact writer is locked to `docs/automation/0174U1`.",
    ])
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet = build_registry_packet()
    (out / PACKET_FILENAME).write_text(_json(packet), encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return packet


__all__ = [
    "PlatformRegistryEntry",
    "PayloadClassEntry",
    "UnsupportedPlatformError",
    "UnsupportedPayloadClassError",
    "PLATFORMS",
    "PAYLOAD_CLASSES",
    "build_registry_packet",
    "registry_checksum",
    "lookup_platform",
    "lookup_payload_class",
    "list_primary_triangle",
    "list_expansion_platforms",
    "validate_payload_class_compatibility",
    "confirm_no_live_safety_flags",
    "write_artifacts",
]
