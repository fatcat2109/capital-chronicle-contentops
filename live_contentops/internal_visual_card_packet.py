"""V6 local-only internal visual card packet builder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "automation" / "V6_MEDIA_SYSTEM"
CARDS_PATH = OUT_DIR / "sample_internal_visual_cards.json"

TASK_LABEL = "TASK_CONTENTOPS_V6_MEDIA_RIGHTS_AND_INTERNAL_VISUAL_CARD_SYSTEM_V0"
SECRET_KEY_PARTS = ("secret", "token", "cookie", "session", "password", "credential", "authorization", "api_key", "header", "env")
CARD_TYPES = {
    "article_quote_card",
    "data_sufficiency_card",
    "source_trust_card",
    "forecast_readiness_blocked_card",
    "hero_image_candidate",
    "thumbnail_candidate",
}
SAFETY_FLAGS = {
    "rendered_image_created": False,
    "image_provider_call_made": False,
    "provider_call_made": False,
    "network_call_made": False,
    "browser_or_cdp_action_performed": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "public_url_fetch_made": False,
    "scraping_performed": False,
}


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def has_secret_like_key(value: Any) -> bool:
    allowed_keys = set(SAFETY_FLAGS) | {"safety_flags", "non_readiness_claims"}
    return any(
        key.lower() not in allowed_keys and any(part in key.lower() for part in SECRET_KEY_PARTS)
        for key, _ in _walk(value)
    )


def _has_unbacked_number(card: dict[str, Any]) -> bool:
    text = json.dumps({"title": card.get("title"), "body": card.get("body"), "claims": card.get("claims", [])}, sort_keys=True)
    has_digit = any(ch.isdigit() for ch in text)
    return has_digit and not card.get("source_refs")


def build_internal_visual_card(
    *,
    card_id: str,
    card_type: str,
    title: str,
    body: str,
    alt_text: str,
    source_refs: list[str] | None = None,
    claims: list[str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic internal visual-card spec; it does not render an image."""
    blockers: list[str] = []
    refs = source_refs or []
    card = {
        "schema_version": "6.0.0",
        "packet_kind": "internal_visual_card_v0",
        "task_label": TASK_LABEL,
        "card_id": card_id,
        "card_type": card_type,
        "title": title,
        "body": body,
        "alt_text": alt_text,
        "source_refs": refs,
        "claims": claims or [],
        "render_status": "not_rendered_spec_only",
        "safety_flags": SAFETY_FLAGS,
    }
    if card_type not in CARD_TYPES:
        blockers.append("unsupported_card_type")
    if not alt_text:
        blockers.append("alt_text_missing")
    if has_secret_like_key(card):
        blockers.append("secret_like_key_blocked")
    if _has_unbacked_number(card):
        blockers.append("unbacked_number_or_metric_blocked")
    card["blockers"] = blockers
    card["status"] = "BLOCKED_CARD_REVIEW_REQUIRED" if blockers else "READY_FOR_MEDIA_MANIFEST_REVIEW"
    card["card_hash"] = stable_hash({k: v for k, v in card.items() if k != "card_hash"})
    if not blockers:
        validate_internal_visual_card(card)
    return card


def validate_internal_visual_card(card: dict[str, Any]) -> None:
    if not card.get("alt_text"):
        raise ValueError("alt_text_required")
    if has_secret_like_key(card):
        raise ValueError("secret_like_key_blocked")
    if _has_unbacked_number(card):
        raise ValueError("unbacked_number_or_metric_blocked")
    if card.get("card_type") not in CARD_TYPES:
        raise ValueError("unsupported_card_type")
    for key, expected in SAFETY_FLAGS.items():
        if card.get("safety_flags", {}).get(key) is not expected:
            raise ValueError(f"{key}_must_be_false")
    if card.get("render_status") != "not_rendered_spec_only":
        raise ValueError("rendered_image_claim_blocked")


def sample_internal_visual_cards() -> list[dict[str, Any]]:
    return [
        build_internal_visual_card(
            card_id="card_quote_001",
            card_type="article_quote_card",
            title="Quote Card - Policy Watch",
            body="Key excerpt prepared for internal editorial review.",
            alt_text="Text card showing a reviewed article quote for operator approval.",
            source_refs=["canonical_article_redacted_001"],
            claims=["excerpt_reviewed_for_context"],
        ),
        build_internal_visual_card(
            card_id="card_sufficiency_001",
            card_type="data_sufficiency_card",
            title="Data Sufficiency",
            body="Evidence is sufficient for commentary, not for a forecast.",
            alt_text="Internal card stating evidence is sufficient for commentary but not forecasting.",
            source_refs=["source_pack_review_redacted_001"],
        ),
        build_internal_visual_card(
            card_id="card_forecast_blocked_001",
            card_type="forecast_readiness_blocked_card",
            title="Forecast Blocked",
            body="Forecast language remains blocked until a future approved evidence gate.",
            alt_text="Warning-style internal card indicating forecast readiness is blocked.",
            source_refs=["draft_inspector_redacted_001"],
        ),
    ]


def write_sample_internal_visual_cards() -> list[dict[str, Any]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cards = sample_internal_visual_cards()
    CARDS_PATH.write_text(json.dumps(cards, indent=2, sort_keys=True), encoding="utf-8")
    return cards


if __name__ == "__main__":
    print(json.dumps(write_sample_internal_visual_cards(), indent=2, sort_keys=True))
