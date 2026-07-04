"""Audit-backed distribution record to feedback backlog bridge v6.

Local-only deterministic bridge for Jim's north-star loop:
publication audit/outcome evidence -> operator feedback -> backlog -> next brief.
No network, API, webhook, provider, browser, CDP, scraping, env, credential,
cookie, storage, session, token, header, live write, retry, schedule, comment,
DM, or reaction action is performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from live_contentops.dispatch_outcome_identity_link_v6 import make_dispatch_outcome_identity_link
from live_contentops.feedback_backlog_next_article_brief_v6 import build_feedback_backlog_next_article_brief_packet
from live_contentops.operator_feedback_backlog_summary_v6 import build_operator_feedback_backlog_summary_packet
from live_contentops.operator_supplied_feedback_intake_v6 import (
    SAMPLE_FEEDBACK_ITEMS,
    build_operator_supplied_feedback_intake_packet,
)
from live_contentops.platform_publication_identity_registry_v6 import make_registry_record

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "automation" / "V6_AUDIT_BACKED_FEEDBACK_BACKLOG"
TASK_LABEL = "TASK_CONTENTOPS_V6_AUDIT_BACKED_DISTRIBUTION_RECORD_TO_FEEDBACK_BACKLOG_V0"

SAFETY_FLAGS = {
    "network_call_made": False,
    "provider_call_made": False,
    "llm_provider_call_made": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "browser_session_used": False,
    "browser_or_cdp_action_performed": False,
    "public_url_fetch_made": False,
    "platform_api_used": False,
    "webhook_request_made": False,
    "scraping_performed": False,
    "comment_or_reply_performed": False,
    "dm_or_private_message_performed": False,
    "reaction_performed": False,
    "scheduler_enabled": False,
    "retry_enabled": False,
    "live_publish_performed_by_contentops": False,
}

SECRET_KEY_MARKERS = (
    "cookie",
    "token",
    "secret",
    "authorization",
    "password",
    "session",
    "localstorage",
    "sessionstorage",
    "credential_value",
    "raw_header",
    "webhook_url",
)
ALLOWED_STATUS_KEYS = {
    *SAFETY_FLAGS,
    "api_request_performed",
    "browser_or_cdp_action_performed",
    "browser_session_started",
    "browser_session_used",
    "comment_or_reply_performed",
    "cookie_read_performed",
    "credential_read_made",
    "credential_value_read",
    "dm_or_private_message_performed",
    "env_value_read_made",
    "llm_provider_call_made",
    "no_paid_api_used",
    "provider_call_made",
    "raw_secret_output",
    "session_storage_read_performed",
    "token_or_header_read_performed",
    "webhook_request_made",
    "webhook_request_performed",
}
FORBIDDEN_WORDING = (
    "financial advice",
    "trade signal",
    "buy signal",
    "sell signal",
    "hold recommendation",
    "price target",
    "position sizing",
    "guaranteed return",
    "prediction guarantee",
)
PRIVATE_SOURCE_KINDS = {"dm", "direct_message", "private_message", "private_chat"}


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _has_secret_like_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if key_lower not in ALLOWED_STATUS_KEYS and any(marker in key_lower for marker in SECRET_KEY_MARKERS):
                return True
            if _has_secret_like_key(child):
                return True
    if isinstance(value, list):
        return any(_has_secret_like_key(child) for child in value)
    return False


def _has_forbidden_wording(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_has_forbidden_wording(child) for child in value.values())
    if isinstance(value, list):
        return any(_has_forbidden_wording(child) for child in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(term in lowered for term in FORBIDDEN_WORDING)
    return False


def _has_private_message_source(feedback_items: list[dict[str, Any]]) -> bool:
    return any(str(item.get("source_kind", "")).lower() in PRIVATE_SOURCE_KINDS for item in feedback_items)


def _redacted_notes(notes: list[dict[str, Any]], unsafe: bool) -> list[dict[str, Any]]:
    if not unsafe:
        return notes
    return [{"redacted_due_to_unsafe_input": True} for _ in notes]


def make_sample_identity_link() -> dict[str, Any]:
    """Create a safe synthetic identity link for local packet generation."""
    record = make_registry_record(
        platform="x",
        payload_hash="sha256:auditbackedfeedbackbridge001",
        public_url="https://x.com/CapitalChron/status/1800000000000000000",
        approval_id="approval_audit_feedback_001",
        outbox_entry_id="outbox_audit_feedback_001",
        dispatch_attempt_id="dispatch_audit_feedback_001",
        account_binding_ref="acct_x_capital_chronicle",
        destination_binding_ref="dest_x_main",
        created_at_utc="2026-07-03T00:00:00+00:00",
    )
    return make_dispatch_outcome_identity_link(record)


def build_audit_backed_feedback_backlog_packet(
    identity_link: dict[str, Any] | None = None,
    audit_record_ref: str | None = "audit_record_redacted_ref_001",
    feedback_items: list[dict[str, Any]] | None = None,
    metrics_notes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build local audit-backed feedback/backlog/next-brief packet."""
    link = identity_link or make_sample_identity_link()
    items = SAMPLE_FEEDBACK_ITEMS if feedback_items is None else feedback_items
    notes = metrics_notes or []
    blockers: list[str] = []

    audit_backed = bool(audit_record_ref) or link.get("ready_for_publication_audit_record") is True
    if not audit_backed:
        blockers.append("audit_backing_missing")
    if not items:
        blockers.append("feedback_items_missing")
    if _has_secret_like_key({"feedback_items": items, "metrics_notes": notes, "identity_link": link}):
        blockers.append("secret_like_input_key_blocked")
    if _has_forbidden_wording({"feedback_items": items, "metrics_notes": notes}):
        blockers.append("forbidden_financial_advice_or_signal_wording")
    if _has_private_message_source(items):
        blockers.append("private_message_feedback_source_blocked")

    unsafe = any(
        blocker in {
            "secret_like_input_key_blocked",
            "forbidden_financial_advice_or_signal_wording",
            "private_message_feedback_source_blocked",
        }
        for blocker in blockers
    )
    if unsafe:
        status = "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    elif "audit_backing_missing" in blockers:
        status = "BLOCKED_MISSING_AUDIT_BACKING"
    elif "feedback_items_missing" in blockers:
        status = "REVIEW_MISSING_FEEDBACK_ITEMS"
    else:
        status = "READY_FOR_OPERATOR_BACKLOG_REVIEW"

    if items and not unsafe:
        intake = build_operator_supplied_feedback_intake_packet(items)
        backlog = build_operator_feedback_backlog_summary_packet(intake)
        brief = build_feedback_backlog_next_article_brief_packet(backlog) if backlog["candidate_count"] else None
    else:
        intake = None
        backlog = None
        brief = None

    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "audit_backed_feedback_backlog_packet_v0",
        "task_label": TASK_LABEL,
        "bridge_status": status,
        "distribution_record_id": f"distribution_feedback_record_{_stable_hash(link)[:16]}",
        "source_identity_link_hash": _stable_hash(link),
        "source_audit_record_ref": audit_record_ref,
        "audit_backed_publication_context": {
            "registry_record_id": link.get("registry_record_id"),
            "platform": link.get("platform"),
            "public_url": link.get("public_url"),
            "platform_publication_id": link.get("platform_publication_id"),
            "approval_id": link.get("approval_id"),
            "outbox_entry_id": link.get("outbox_entry_id"),
            "dispatch_attempt_id": link.get("dispatch_attempt_id"),
            "publication_audit_ready": link.get("ready_for_publication_audit_record") is True,
            "explicit_audit_record_ref_present": bool(audit_record_ref),
        },
        "operator_feedback_intake_packet_id": intake.get("feedback_intake_packet_id") if intake else None,
        "feedback_backlog_summary_packet_id": backlog.get("backlog_summary_packet_id") if backlog else None,
        "next_article_brief_packet_id": brief.get("next_article_brief_packet_id") if brief else None,
        "feedback_items": intake.get("feedback_items", []) if intake else [],
        "backlog_candidates": backlog.get("backlog_candidates", []) if backlog else [],
        "selected_next_article_brief": brief.get("brief_candidate") if brief else None,
        "metrics_notes": _redacted_notes(notes, unsafe),
        "community_signal_status": "operator_supplied_only_no_scrape_no_bot",
        "final_product_loop_position": "audit_to_feedback_to_next_idea",
        "blocked_controls": ["approve", "dispatch", "publish", "schedule", "send", "scrape", "reply", "dm", "react"],
        "safety_flags": SAFETY_FLAGS,
        "non_readiness_claims": {
            "live_readiness_claimed": False,
            "api_readiness_claimed": False,
            "llm_summary_claimed": False,
            "public_url_verification_claimed": False,
            "dispatch_readiness_claimed": False,
            "canonical_draft_readiness_claimed": False,
            "community_scrape_claimed": False,
            "bot_or_slash_command_claimed": False,
        },
        "blockers": blockers,
    }
    packet["exact_payload_hash"] = _stable_hash(packet)
    validate_audit_backed_feedback_backlog_packet(packet)
    return packet


def validate_audit_backed_feedback_backlog_packet(packet: dict[str, Any]) -> None:
    """Validate the local-only bridge packet."""
    if _has_secret_like_key(packet):
        raise ValueError("secret_like_packet_key_blocked")
    flags = packet.get("safety_flags", {})
    for key, expected in SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            raise ValueError(f"{key}_must_be_false")
    if packet["bridge_status"] == "READY_FOR_OPERATOR_BACKLOG_REVIEW" and packet.get("blockers"):
        raise ValueError("ready_packet_cannot_have_blockers")
    if packet["bridge_status"] == "READY_FOR_OPERATOR_BACKLOG_REVIEW" and not packet.get("selected_next_article_brief"):
        raise ValueError("ready_packet_requires_next_article_brief")


def write_default_packet() -> dict[str, Any]:
    """Write deterministic evidence packet and implementation report."""
    packet = build_audit_backed_feedback_backlog_packet()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "audit_backed_feedback_backlog_packet.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8"
    )
    report = f"""# V6 Audit-Backed Feedback Backlog Implementation Report

## Status

`{packet['bridge_status']}`

## Purpose

This packet closes the local final-product loop segment:

```text
audit-backed distribution record -> operator feedback -> backlog -> next brief
```

## Safety Boundary

No network, API, webhook, provider, browser, CDP, scraping, env, credential,
cookie, storage, session, token, header, live write, retry, schedule, comment,
DM, or reaction action is performed.

## Packet

- `distribution_record_id`: `{packet['distribution_record_id']}`
- `feedback items`: {len(packet['feedback_items'])}
- `backlog candidates`: {len(packet['backlog_candidates'])}
- `next brief`: `{packet['next_article_brief_packet_id']}`

## Next Task

```text
TASK_CONTENTOPS_V6_CAMPAIGN_OBJECT_AND_FINAL_LOOP_INTEGRATION_V0
```
"""
    (OUT_DIR / "implementation_report.md").write_text(report, encoding="utf-8")
    return packet


if __name__ == "__main__":
    print(json.dumps(write_default_packet(), indent=2, sort_keys=True))
