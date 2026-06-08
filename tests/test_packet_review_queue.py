import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from live_contentops import editorial_packet_export as export
from live_contentops import packet_review_queue as queue


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def packets():
    data = load_fixture("review_queue_input.json")
    return [export.build_export_packet(r) for r in data["packets"]]


@pytest.fixture
def review_queue(packets):
    return queue.build_queue(packets)


def test_queue_item_has_all_required_fields(review_queue):
    required = [
        "queue_item_id",
        "export_packet_id",
        "source_fixture_id",
        "content_type",
        "target_platforms",
        "created_at",
        "queue_status",
        "audit_status",
        "blocker_count",
        "warning_count",
        "review_required",
        "manual_decision_required",
        "approval_granted",
        "publish_ready",
        "provider_call_allowed",
        "search_call_allowed",
        "platform_action_allowed",
        "no_public_post_reason",
        "operator_review",
    ]
    for item in review_queue:
        for key in required:
            assert key in item, f"missing field: {key}"


def test_queue_item_safety_flags(review_queue):
    for item in review_queue:
        assert item["review_required"] is True
        assert item["manual_decision_required"] is True
        assert item["approval_granted"] is False
        assert item["publish_ready"] is False
        assert item["provider_call_allowed"] is False
        assert item["search_call_allowed"] is False
        assert item["platform_action_allowed"] is False
        assert item["queue_status"] in queue.QUEUE_STATUSES


def test_operator_review_placeholders_grant_no_authority(review_queue):
    for item in review_queue:
        review = item["operator_review"]
        assert review["reviewer_id"] is None
        assert review["selected_preview_id"] is None
        assert review["decision"] == "PENDING_MANUAL_REVIEW"
        assert review["operator_notes"] == ""
        assert review["reviewed_at"] is None
        assert review["approval_status"] == "NOT_APPROVED"
        assert review["publish_status"] == "NOT_PUBLIC_POSTABLE"


def test_all_items_not_public_postable(review_queue):
    for item in review_queue:
        assert item["no_public_post_reason"] is not None
        assert item["no_public_post_reason"] != ""


def test_summary_is_deterministic(packets):
    s1 = queue.summarize_queue(queue.build_queue(packets))
    s2 = queue.summarize_queue(queue.build_queue(packets))
    assert json.dumps(s1, sort_keys=True) == json.dumps(s2, sort_keys=True)


def test_publish_ready_count_always_zero(review_queue):
    summary = queue.summarize_queue(review_queue)
    assert summary["publish_ready_count"] == 0
    assert summary["all_fixture_outputs_not_public_postable"] is True
    assert summary["live_actions_disabled"] is True
    assert summary["advisory_only"] is True
