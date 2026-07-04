"""V6 local-only multi-platform campaign object builder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "automation" / "V6_CAMPAIGN_OBJECT"
SAMPLE_PATH = OUT_DIR / "sample_campaign.json"
REPORT_PATH = OUT_DIR / "implementation_report.md"
TASK_LABEL = "TASK_CONTENTOPS_V6_CAMPAIGN_OBJECT_AND_FINAL_LOOP_INTEGRATION_V0"

SECRET_KEY_PARTS = ("secret", "token", "cookie", "session", "password", "credential", "authorization", "api_key", "header")
ALLOWED_STATUS_KEYS = {"credential_read_made", "no_secret_material_present", "credential_handle_status"}
FORBIDDEN_WORDING = ("buy signal", "sell signal", "price target", "entry point", "exit point", "guaranteed prediction", "trading recommendation")
SAFETY_FLAGS = {
    "dispatch_attempted": False,
    "network_call_made": False,
    "webhook_request_made": False,
    "platform_api_used": False,
    "provider_call_made": False,
    "browser_or_cdp_action_performed": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "public_url_fetch_made": False,
    "scraping_performed": False,
    "scheduler_enabled": False,
    "retry_enabled": False,
    "comment_dm_or_reaction_performed": False,
    "live_write_allowed_now": False,
}


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _has_secret_like_key(value: Any) -> bool:
    for key, _ in _walk(value):
        lowered = key.lower()
        if lowered not in ALLOWED_STATUS_KEYS and any(part in lowered for part in SECRET_KEY_PARTS):
            return True
    return False


def _has_forbidden_wording(value: Any) -> bool:
    return any(term in json.dumps(value, sort_keys=True).lower() for term in FORBIDDEN_WORDING)


def _sample_outbox_entries() -> list[dict[str, Any]]:
    return [
        {"outbox_entry_id": "outbox_substack_manual_001", "platform": "substack", "platform_state": "manual", "payload_hash_locked": True, "dispatchable": False},
        {"outbox_entry_id": "outbox_discord_drop_001", "platform": "discord", "platform_state": "ready", "payload_hash_locked": True, "dispatchable": False},
        {"outbox_entry_id": "outbox_x_manual_001", "platform": "x", "platform_state": "manual", "payload_hash_locked": True, "dispatchable": False},
        {"outbox_entry_id": "outbox_linkedin_deferred_001", "platform": "linkedin", "platform_state": "deferred", "payload_hash_locked": True, "dispatchable": False},
    ]


def build_campaign(
    *,
    canonical_article_id: str | None = "canonical_article_redacted_001",
    selected_platforms: list[str] | None = None,
    discord_drop_ids: list[str] | None = None,
    variant_set_id: str = "variant_set_redacted_001",
    approval_packet_id: str = "approval_preview_28f5ef142e404225",
    outbox_entries: list[dict[str, Any]] | None = None,
    dispatch_results: list[dict[str, Any]] | None = None,
    metrics_records: list[dict[str, Any]] | None = None,
    feedback_summary: dict[str, Any] | None = None,
    approval_mode: str = "bundle_review",
) -> dict[str, Any]:
    """Build a deterministic local campaign packet without live actions."""
    platforms = selected_platforms or ["substack", "discord", "x", "linkedin"]
    drops = discord_drop_ids if discord_drop_ids is not None else ["discord_drop_redacted_001"]
    outbox = outbox_entries if outbox_entries is not None else _sample_outbox_entries()
    dispatch = dispatch_results if dispatch_results is not None else [
        {"platform": entry["platform"], "status": "not_dispatched_local_only", "public_url_verified": False}
        for entry in outbox
    ]
    metrics = metrics_records if metrics_records is not None else [{"record_id": "metrics_redacted_001", "source": "operator_supplied_redacted", "scraped": False}]
    feedback = feedback_summary or {
        "feedback_backlog_summary_packet_id": "feedback_backlog_summary_redacted_001",
        "next_article_brief_packet_id": "next_article_brief_redacted_001",
        "community_signal_status": "operator_supplied_only_no_scrape_no_bot",
    }

    blockers: list[str] = []
    if not canonical_article_id:
        blockers.append("canonical_article_missing")
    if "discord" in platforms and not drops:
        blockers.append("discord_drop_missing")
    if approval_mode not in {"per_payload_review", "bundle_review"}:
        blockers.append("approval_mode_invalid")
    if approval_mode == "bundle_review" and not all(entry.get("payload_hash_locked") is True for entry in outbox):
        blockers.append("exact_hash_locks_missing_for_bundle_review")
    unsafe_input = {"outbox_entries": outbox, "dispatch_results": dispatch, "metrics_records": metrics, "feedback_summary": feedback}
    if _has_secret_like_key(unsafe_input):
        blockers.append("secret_like_input_key_blocked")
        metrics = [{"record_id": "metrics_redacted_blocked", "source": "redacted_secret_like_input", "scraped": False}]
        feedback = {"community_signal_status": "blocked_secret_like_input_redacted"}
    if _has_forbidden_wording({"outbox_entries": outbox, "dispatch_results": dispatch, "metrics_records": metrics, "feedback_summary": feedback}):
        blockers.append("forbidden_financial_advice_or_signal_wording")

    unsafe = any(b in blockers for b in {"secret_like_input_key_blocked", "forbidden_financial_advice_or_signal_wording"})
    has_manual_or_deferred = any(entry.get("platform_state") in {"manual", "deferred"} for entry in outbox)
    if unsafe:
        status = "BLOCKED_UNSAFE_OR_SECRET_LIKE_INPUT"
    elif "canonical_article_missing" in blockers:
        status = "BLOCKED_MISSING_CANONICAL_ARTICLE"
    elif "exact_hash_locks_missing_for_bundle_review" in blockers:
        status = "BLOCKED_MISSING_EXACT_HASH_LOCKS"
    elif blockers or has_manual_or_deferred:
        status = "REVIEW_WITH_MANUAL_OR_DEFERRED_PLATFORMS"
    else:
        status = "READY_FOR_OPERATOR_CAMPAIGN_REVIEW"

    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "campaign_object_v0",
        "task_label": TASK_LABEL,
        "campaign_id": "pending",
        "canonical_article_id": canonical_article_id,
        "selected_platforms": platforms,
        "discord_drop_ids": drops,
        "variant_set_id": variant_set_id,
        "approval_packet_id": approval_packet_id,
        "approval_mode": approval_mode,
        "outbox_entries": outbox,
        "dispatch_results": dispatch,
        "metrics_records": metrics,
        "feedback_summary": feedback,
        "status": status,
        "blockers": blockers,
        "platform_state_counts": {state: sum(1 for entry in outbox if entry.get("platform_state") == state) for state in ("ready", "manual", "deferred")},
        "final_product_loop_position": "idea_to_campaign_to_audit_to_feedback_to_next_idea",
        "blocked_controls": ["approve", "dispatch", "publish", "schedule", "send", "scrape", "reply", "dm", "react"],
        "safety_flags": SAFETY_FLAGS,
        "non_readiness_claims": {
            "live_readiness_claimed": False,
            "dispatch_readiness_claimed": False,
            "api_readiness_claimed": False,
            "public_url_verification_claimed": False,
            "community_scrape_claimed": False,
            "bot_or_slash_command_claimed": False,
        },
    }
    exact_hash = _stable_hash({k: v for k, v in packet.items() if k != "campaign_id"})
    packet["campaign_id"] = f"campaign_{exact_hash[:16]}"
    packet["exact_payload_hash"] = _stable_hash(packet)
    if not blockers:
        validate_campaign(packet)
    return packet


def validate_campaign(campaign: dict[str, Any]) -> None:
    """Validate campaign safety and acceptance rules."""
    if _has_secret_like_key(campaign):
        raise ValueError("secret_like_campaign_key_blocked")
    if "discord" in campaign.get("selected_platforms", []) and not campaign.get("discord_drop_ids"):
        raise ValueError("discord_drop_missing")
    if campaign.get("approval_mode") == "bundle_review" and not all(entry.get("payload_hash_locked") is True for entry in campaign.get("outbox_entries", [])):
        raise ValueError("bundle_review_requires_exact_hash_locks")
    for key, expected in SAFETY_FLAGS.items():
        if campaign.get("safety_flags", {}).get(key) is not expected:
            raise ValueError(f"{key}_must_be_false")
    if campaign["status"] == "READY_FOR_OPERATOR_CAMPAIGN_REVIEW" and campaign.get("blockers"):
        raise ValueError("ready_campaign_cannot_have_blockers")


def write_sample_campaign() -> dict[str, Any]:
    """Write deterministic campaign sample and report."""
    packet = build_campaign()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_PATH.write_text(json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(f"""# V6 Campaign Object Implementation Report

## Status

`{packet['status']}`

## Purpose

This local-only campaign object groups canonical article, Discord drop, platform
variants, approval packet, dry-run outbox entries, dispatch/audit placeholders,
manual metrics, and audit-backed feedback summary.

## Safety Boundary

No network, API, webhook, provider, browser, CDP, scraping, env, credential,
cookie, storage, session, token, header, live write, retry, schedule, comment,
DM, or reaction action is performed.

## Packet

- `campaign_id`: `{packet['campaign_id']}`
- `selected_platforms`: {', '.join(packet['selected_platforms'])}
- `discord_drop_ids`: {len(packet['discord_drop_ids'])}
- `status`: `{packet['status']}`
- `exact_payload_hash`: `{packet['exact_payload_hash']}`

## Next Task

```text
TASK_CONTENTOPS_V6_MEDIA_RIGHTS_AND_INTERNAL_VISUAL_CARD_SYSTEM_V0
```
""", encoding="utf-8")
    return packet


if __name__ == "__main__":
    print(json.dumps(write_sample_campaign(), indent=2, sort_keys=True))
