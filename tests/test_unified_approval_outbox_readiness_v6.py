"""Tests for V6 local approval-decision to outbox readiness reconciliation."""

from live_contentops.unified_approval_outbox_readiness_v6 import (
    reconcile_operator_decisions_to_local_outbox_readiness,
)


def test_reconcile_operator_decisions_keeps_outbox_non_executable() -> None:
    payloads = [
        {"platform_id": "substack", "platform": "Substack", "variant_key": "substack_canonical_preview", "payload_hash": "hash-approve", "dispatch_gate": "manual_review_only"},
        {"platform_id": "x", "platform": "X", "variant_key": "x_manual_preview", "payload_hash": "hash-hold", "dispatch_gate": "manual_review_only"},
        {"platform_id": "instagram", "platform": "Instagram", "variant_key": "instagram_caption_preview", "payload_hash": "hash-reject", "dispatch_gate": "blocked_deferred"},
        {"platform_id": "discord", "platform": "Discord", "variant_key": "discord_drop_preview", "payload_hash": "hash-live-scope", "dispatch_gate": "blocked_live_scope_required"},
        {"platform_id": "linkedin", "platform": "LinkedIn", "variant_key": "linkedin_professional_preview", "payload_hash": "hash-no-decision", "dispatch_gate": "manual_review_only"},
    ]
    decisions = [
        {"payload_hash": "hash-approve", "decision": "approve", "decision_packet_id": "d1", "decision_packet_hash": "p1"},
        {"payload_hash": "hash-hold", "decision": "hold", "decision_packet_id": "d2", "decision_packet_hash": "p2"},
        {"payload_hash": "hash-reject", "decision": "reject", "decision_packet_id": "d3", "decision_packet_hash": "p3"},
    ]

    report = reconcile_operator_decisions_to_local_outbox_readiness(payloads, decisions)

    assert report["counts"] == {
        "approved_manual_ready": 1,
        "held_for_revision": 1,
        "rejected_blocked": 1,
        "blocked_no_decision": 1,
        "blocked_live_scope_required": 1,
        "total": 5,
        "dispatchable": 0,
    }
    assert {row["platform_id"]: row["readiness_state"] for row in report["readiness_rows"]} == {
        "substack": "approved_manual_ready",
        "x": "held_for_revision",
        "instagram": "rejected_blocked",
        "discord": "blocked_live_scope_required",
        "linkedin": "blocked_no_decision",
    }
    for row in report["readiness_rows"]:
        assert row["outbox_entry_created"] is False
        assert row["outbox_dispatchable"] is False
        assert row["dispatch_allowed_now"] is False
        assert row["live_write_allowed_now"] is False
        assert row["scheduler_or_retry_wired"] is False
        assert row["public_url_fetch_made"] is False
        assert row["provider_or_api_call_made"] is False
        assert row["browser_or_cdp_used"] is False
        assert row["approval_ledger_live_write_made"] is False
