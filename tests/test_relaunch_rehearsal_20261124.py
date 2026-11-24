"""Builder L, 24 Nov 2026: the relaunch rehearsal (backlog/relaunch-rehearsal-20261124).

A card-format (format 4) result row carries no scored_call_count. When its TradingView capture failed, the
fallback fact card read that key, raised KeyError, and the result never posted: the promised 20 Nov USD/JPY
result (plan_4bcfb1182f0fff4f8254172c) stayed NOT_STARTED on every tick of the rehearsed relaunch.
No network, no browser, no capture: the capture is replaced by a named failure.
"""
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import tradingview_snapshot_v1 as tv


def card_result_row():
    return {"key": "plan-result-post-test", "kind": "result", "format": 4, "symbol": "USDJPY", "state": "RESULT",
            "plan_id": "plan_test", "at_utc": "2026-11-23T03:00:16.836000Z", "result": "EXPIRED", "scored": True,
            "instrument_title": "USD/JPY",
            "text": "USD/JPY, plan of 20–22 Nov: closed at its time exit.\n\n"
                    + posts.PUBLIC_NOTICE + " " + posts.CONFLICTS_NOTICE,
            "levels": {"zone_low": 158.87, "zone_high": 159.03, "invalidation_level": 159.6, "direction": "bearish"}}


def test_card_result_facts_need_no_scored_call_count():
    facts = dict(posts.plan_facts(card_result_row()))
    assert facts["Result"] == "expired" and "Scored calls" not in facts
    assert facts["Entry zone"] == "158.87–159.03" and facts["Invalidation"] == "Above 159.6"
    assert facts["Status"] == "Scored"


def test_format_three_result_keeps_its_scored_call_count():
    facts = dict(posts.plan_facts({**card_result_row(), "format": 3, "scored_call_count": 41}))
    assert facts["Scored calls"] == "41"


def test_failed_capture_on_a_card_result_carries_the_fact_card(tmp_path, monkeypatch):
    def unavailable(row, folder, **kwargs):
        raise tv.SnapshotUnavailable("TRADINGVIEW_SNAPSHOT_WORKER_FAILED:test")
    monkeypatch.setattr(tv, "plan_snapshot", unavailable)
    monkeypatch.setattr("live_contentops.image_template_inputs_v1.for_plan_post", lambda row: None)
    asset, charted = posts._post_image(card_result_row(), tmp_path, plan_post=True, required_chart=True)
    assert charted is False and asset["plan_chart_fallback"]["cause"] == "TRADINGVIEW_SNAPSHOT_WORKER_FAILED:test"
    facts = dict(asset["data_card_packet"]["facts"])
    assert facts["Result"] == "expired" and "target" not in str(asset).lower()
