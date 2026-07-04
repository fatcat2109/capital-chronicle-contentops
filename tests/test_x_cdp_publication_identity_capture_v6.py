"""Tests for no-API X browser/CDP identity capture helpers."""
from __future__ import annotations

from live_contentops import x_cdp_publication_identity_capture_v6 as capture


EXPECTED = "Testing a supervised publishing workflow - no signal."


def test_normalized_text_matches_dash_variants():
    observed = "Testing a supervised publishing workflow — no signal."
    assert capture.visible_text_matches(EXPECTED, observed) is True


def test_capture_current_post_detail_identity_success():
    got = capture.capture_current_x_post_detail_identity("https://x.com/CapitalChron/status/777", EXPECTED, EXPECTED)
    assert got["result_class"] == "X_POST_IDENTITY_CAPTURED"
    assert got["platform_publication_id"] == "777"


def test_capture_current_post_detail_blocks_non_status_url():
    got = capture.capture_current_x_post_detail_identity("https://x.com/home", EXPECTED, EXPECTED)
    assert got["result_class"] == "BLOCKED_NOT_X_STATUS_URL"
    assert got["public_url_captured"] is False


def test_capture_current_post_detail_blocks_text_mismatch():
    got = capture.capture_current_x_post_detail_identity("https://x.com/CapitalChron/status/777", "other post", EXPECTED)
    assert got["result_class"] == "BLOCKED_EXPECTED_TEXT_NOT_VISIBLE"


def test_reconcile_latest_timeline_confident_one_match():
    got = capture.reconcile_latest_x_timeline_post(["https://x.com/CapitalChron/status/1", "https://x.com/Other/status/2"], [EXPECTED, "other"], EXPECTED)
    assert got["result_class"] == "X_TIMELINE_RECONCILE_CONFIDENT"
    assert got["platform_publication_id"] == "1"


def test_reconcile_latest_timeline_blocks_ambiguous_match():
    got = capture.reconcile_latest_x_timeline_post(["https://x.com/CapitalChron/status/1", "https://x.com/CapitalChron/status/2"], [EXPECTED, EXPECTED], EXPECTED)
    assert got["result_class"] == "BLOCKED_AMBIGUOUS_TIMELINE_MATCH"
    assert got["match_count"] == 2
