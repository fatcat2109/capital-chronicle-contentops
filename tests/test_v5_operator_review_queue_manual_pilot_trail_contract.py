"""Unit tests for V5 operator review queue manual pilot trail contract."""
from hashlib import sha256
import json

from live_contentops.v5_operator_review_queue_manual_pilot_trail_contract import (
    build_v5_operator_review_queue_manual_pilot_trail_packet,
    TASK_LABEL,
    CONTRACT_VERSION,
    SOURCE_MANUAL_EXPORT_PACKET_HASH,
)


def test_packet_builds_deterministically():
    p1 = build_v5_operator_review_queue_manual_pilot_trail_packet()
    p2 = build_v5_operator_review_queue_manual_pilot_trail_packet()
    assert p1.packet_hash == p2.packet_hash
    assert p1.queue_id == p2.queue_id
    assert p1.task_label == TASK_LABEL
    assert p1.contract_version == CONTRACT_VERSION


def test_source_manual_export_hash_referenced():
    p = build_v5_operator_review_queue_manual_pilot_trail_packet()
    assert p.source_manual_export_packet_hash == SOURCE_MANUAL_EXPORT_PACKET_HASH
    assert p.source_manual_export_packet_hash == "277fb7d44b247efc6021f038e362256f746cc039"


def test_review_items_are_safe_and_local():
    p = build_v5_operator_review_queue_manual_pilot_trail_packet()
    assert len(p.review_items) == 4
    platforms = {item.item_id: item for item in p.review_items}
    assert "item_x_manual_post_draft_review" in platforms
    assert "item_telegram_channel_manual_message_review" in platforms
    assert "item_substack_manual_newsletter_export_review" in platforms
    assert "item_linkedin_manual_post_review" in platforms

    for item in p.review_items:
        assert item.local_only is True
        assert item.manual_review_required is True
        assert item.no_api is True
        assert item.no_credentials is True
        assert item.no_scheduler is True
        assert item.not_dispatch_ready is True
        assert item.not_public_postable is True
        assert item.operator_action_outside_contentops_required is True


def test_trail_entries_are_descriptive():
    p = build_v5_operator_review_queue_manual_pilot_trail_packet()
    assert len(p.local_review_trail_entries) == 5
    types = [entry.entry_type for entry in p.local_review_trail_entries]
    assert "created_local_review_item" in types
    assert "checklist_pending" in types
    assert "manual_publish_url_empty" in types
    assert "metrics_empty" in types
    assert "live_dispatch_disabled" in types


def test_disabled_future_gates_are_locked():
    p = build_v5_operator_review_queue_manual_pilot_trail_packet()
    s = p.disabled_live_action_state
    assert s.live_dispatch_enabled is False
    assert s.publish_enabled is False
    assert s.send_enabled is False
    assert s.schedule_enabled is False
    assert s.connect_account_enabled is False
    assert s.verify_credentials_enabled is False
    assert s.sync_platform_enabled is False
    assert s.reason == "manual_export_pilot_verification_only_no_live_affordance"


def test_placeholders_remain_empty():
    p = build_v5_operator_review_queue_manual_pilot_trail_packet()
    for ph in p.manual_publish_placeholders:
        assert ph.status == "empty_not_recorded"
        assert ph.value == ""
