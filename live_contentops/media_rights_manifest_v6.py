"""V6 local-only media rights manifest builder."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from live_contentops.internal_visual_card_packet import (
    SAFETY_FLAGS as CARD_SAFETY_FLAGS,
    build_internal_visual_card,
    has_secret_like_key,
    stable_hash,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "automation" / "V6_MEDIA_SYSTEM"
MANIFEST_PATH = OUT_DIR / "sample_media_manifest.json"
REPORT_PATH = OUT_DIR / "implementation_report.md"
TASK_LABEL = "TASK_CONTENTOPS_V6_MEDIA_RIGHTS_AND_INTERNAL_VISUAL_CARD_SYSTEM_V0"

SUPPORTED_MEDIA = {
    "internal_visual_card",
    "article_quote_card",
    "data_sufficiency_card",
    "source_trust_card",
    "forecast_readiness_blocked_card",
    "rights_checked_external_image",
    "hero_image_candidate",
    "thumbnail_candidate",
}
EXTERNAL_MEDIA_TYPES = {"rights_checked_external_image"}
RIGHTS_STATUSES = {"owned", "licensed", "public_domain", "creative_commons", "operator_supplied_rights_checked"}
SAFETY_FLAGS = {
    **CARD_SAFETY_FLAGS,
    "download_performed": False,
    "media_file_written": False,
    "rights_url_verified": False,
    "live_write_allowed_now": False,
}


def build_media_item(
    *,
    media_id: str,
    media_type: str,
    alt_text: str,
    origin: str,
    rights_status: str | None = None,
    attribution: str | None = None,
    source_label: str | None = None,
    card_packet: dict[str, Any] | None = None,
    platform_optional: bool = True,
) -> dict[str, Any]:
    item = {
        "media_id": media_id,
        "media_type": media_type,
        "alt_text": alt_text,
        "origin": origin,
        "rights_status": rights_status,
        "attribution": attribution,
        "source_label": source_label,
        "platform_optional": platform_optional,
        "card_packet": card_packet,
        "fetch_or_download_claimed": False,
    }
    blockers: list[str] = []
    if media_type not in SUPPORTED_MEDIA:
        blockers.append("unsupported_media_type")
    if not alt_text:
        blockers.append("alt_text_missing")
    if media_type in EXTERNAL_MEDIA_TYPES:
        if rights_status not in RIGHTS_STATUSES:
            blockers.append("external_media_rights_status_missing_or_invalid")
        if not attribution:
            blockers.append("external_media_attribution_missing")
        if not source_label:
            blockers.append("external_media_source_label_missing")
    if card_packet and card_packet.get("status") != "READY_FOR_MEDIA_MANIFEST_REVIEW":
        blockers.append("card_packet_not_ready")
    if has_secret_like_key(item):
        blockers.append("secret_like_key_blocked")
    item["blockers"] = blockers
    item["status"] = "BLOCKED_MEDIA_REVIEW_REQUIRED" if blockers else "READY_FOR_MEDIA_MANIFEST_REVIEW"
    item["media_hash"] = stable_hash({k: v for k, v in item.items() if k != "media_hash"})
    return item


def build_media_manifest(
    *,
    campaign_id: str = "campaign_redacted_001",
    selected_platforms: list[str] | None = None,
    media_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    platforms = selected_platforms or ["substack", "discord", "x", "linkedin"]
    items = media_items if media_items is not None else sample_media_items()
    blockers = [f"{item['media_id']}:{blocker}" for item in items for blocker in item.get("blockers", [])]
    if has_secret_like_key({"media_items": items}):
        blockers.append("secret_like_key_blocked")
    manifest = {
        "schema_version": "6.0.0",
        "packet_kind": "media_rights_manifest_v0",
        "task_label": TASK_LABEL,
        "campaign_id": campaign_id,
        "selected_platforms": platforms,
        "media_required_for_platforms": [],
        "media_optional_for_platforms": platforms,
        "media_items": items,
        "status": "BLOCKED_MEDIA_REVIEW_REQUIRED" if blockers else "READY_FOR_OPERATOR_MEDIA_REVIEW",
        "blockers": blockers,
        "safety_flags": SAFETY_FLAGS,
        "non_readiness_claims": {
            "rendered_images_claimed": False,
            "external_downloads_claimed": False,
            "public_url_verification_claimed": False,
            "provider_generation_claimed": False,
        },
        "blocked_controls": ["download", "fetch", "generate_image", "publish", "dispatch", "schedule", "scrape"],
    }
    manifest["media_manifest_hash"] = stable_hash([item["media_hash"] for item in items])
    manifest["exact_payload_hash"] = stable_hash(manifest)
    if not blockers:
        validate_media_manifest(manifest)
    return manifest


def validate_media_manifest(manifest: dict[str, Any]) -> None:
    for key, expected in SAFETY_FLAGS.items():
        if manifest.get("safety_flags", {}).get(key) is not expected:
            raise ValueError(f"{key}_must_be_false")
    for item in manifest.get("media_items", []):
        if not item.get("alt_text"):
            raise ValueError("alt_text_required")
        if item.get("media_type") in EXTERNAL_MEDIA_TYPES:
            if item.get("rights_status") not in RIGHTS_STATUSES:
                raise ValueError("external_media_rights_status_required")
            if not item.get("attribution") or not item.get("source_label"):
                raise ValueError("external_media_attribution_and_source_required")
        if item.get("fetch_or_download_claimed") is not False:
            raise ValueError("fetch_or_download_claim_blocked")
    expected_hash = stable_hash([item["media_hash"] for item in manifest.get("media_items", [])])
    if manifest.get("media_manifest_hash") != expected_hash:
        raise ValueError("media_hash_mismatch")
    if has_secret_like_key(manifest):
        raise ValueError("secret_like_key_blocked")


def sample_media_items() -> list[dict[str, Any]]:
    quote_card = build_internal_visual_card(
        card_id="card_quote_001",
        card_type="article_quote_card",
        title="Quote Card - Policy Watch",
        body="Key excerpt prepared for internal editorial review.",
        alt_text="Text card showing a reviewed article quote for operator approval.",
        source_refs=["canonical_article_redacted_001"],
    )
    return [
        build_media_item(
            media_id="media_internal_quote_card_001",
            media_type="article_quote_card",
            alt_text=quote_card["alt_text"],
            origin="internal_spec_only",
            rights_status="owned",
            attribution="Capital Chronicle internal visual system",
            source_label="canonical_article_redacted_001",
            card_packet=quote_card,
        ),
        build_media_item(
            media_id="media_external_hero_candidate_001",
            media_type="rights_checked_external_image",
            alt_text="Rights-checked external hero image candidate for operator review.",
            origin="external_metadata_only_no_fetch",
            rights_status="operator_supplied_rights_checked",
            attribution="operator_supplied_attribution_pending_final_copy",
            source_label="operator_supplied_source_label",
        ),
    ]


def write_sample_media_manifest() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_media_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(f"""# V6 Media System Implementation Report

## Status

`{manifest['status']}`

## Purpose

This local-only media system records rights-checked external media metadata and
internal visual-card specs for campaign/article review.

## Safety Boundary

No network, API, webhook, provider, image-provider, browser, CDP, scraping, env,
credential, cookie, storage, session, token, header, download, live write, retry,
schedule, comment, DM, or reaction action is performed.

## Packet

- `campaign_id`: `{manifest['campaign_id']}`
- `media_items`: {len(manifest['media_items'])}
- `status`: `{manifest['status']}`
- `media_manifest_hash`: `{manifest['media_manifest_hash']}`
- `exact_payload_hash`: `{manifest['exact_payload_hash']}`

## Next Task

```text
TASK_CONTENTOPS_V6_COMMUNITY_SIGNAL_INTAKE_AND_FEEDBACK_SUMMARY_V0
```
""", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(write_sample_media_manifest(), indent=2, sort_keys=True))
