"""Builder L, 24 Nov 2026: the relaunch rehearsal (backlog/relaunch-rehearsal-20261124).

A card-format (format 4) result row carries no scored_call_count. When its TradingView capture failed, the
fallback fact card read that key, raised KeyError, and the result never posted: the promised 20 Nov USD/JPY
result (plan_4bcfb1182f0fff4f8254172c) stayed NOT_STARTED on every tick of the rehearsed relaunch.
No network, no browser, no capture: the capture is replaced by a named failure.

The same rehearsal found an announced BTCUSD plan (Telegram 231, 23 Nov 03:55Z) invalidated inside Jim's pause:
the pause rule held its ending back as "shown in the scorecard", but the scorecard lists only scored results and
unscored expiries, so the ending was shown nowhere. The rule now holds back only results the scorecard shows.
"""
from datetime import timedelta
import sys

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import secret_store_v1
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_call_cards_cc399 import write
from test_plan_copy_cc682 import GOLD_PLAN_ID, PAGE_LINK, gold_export  # noqa: F401
from test_plan_status_posts_cc306 import event, main_root  # noqa: F401


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


def _announced_then(gold_export, tmp_path, main_root, monkeypatch, *, status, outcome):
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    monkeypatch.setattr(pages, "confirmed_publication", lambda *args: {
        "plan_id": GOLD_PLAN_ID, "registration_hash": gold_export["registration_hash"],
        "canonical_url": PAGE_LINK, "summary": {"macro": "Fed path via real yields."}})
    registered = posts._utc(gold_export["registered_at_utc"])
    monkeypatch.setattr(cards, "JIM_PAUSE_START", registered + timedelta(minutes=30))
    monkeypatch.setattr(cards, "JIM_PAUSE_END", registered + timedelta(days=7))
    store = ContentOpsDurableStore(tmp_path / "replay.sqlite3")
    events = []

    def queue(plan, state, at, now):
        events.append(event(GOLD_PLAN_ID, state, at))
        folder = write(tmp_path / "export", [plan], events, generated_at_utc=now.isoformat())
        return posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)

    setup = queue(gold_export, "WAITING", gold_export["registered_at_utc"], registered + timedelta(seconds=1))
    store.set_outbox_status(setup["queued"][0]["key"], "PUBLISHED")
    ended = (registered + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    return queue({**gold_export, "status": status, "outcome": outcome}, status, ended,
                 registered + timedelta(days=8))  # the relaunch, after the pause


def test_an_announced_plan_invalidated_inside_the_pause_still_gets_its_ending(gold_export, tmp_path, main_root,
                                                                               monkeypatch):
    run = _announced_then(gold_export, tmp_path, main_root, monkeypatch, status="INVALIDATED",
                          outcome={"state": "NOT_SCORED_UNTRIGGERED", "first_cause": "UNTRIGGERED_PLAN_ENDED"})
    assert run["status"] == "OK", run
    assert [r["kind"] for r in run["queued"]] == ["result"]
    assert "JIM_PAUSE_RESULT_SHOWN_IN_SCORECARD" not in {s.get("cause") for s in run.get("not_posted") or []}


def test_a_scored_result_inside_the_pause_stays_in_the_scorecard_only(gold_export, tmp_path, main_root, monkeypatch):
    score = {"asset_id": "XAUUSD", "plan_id": GOLD_PLAN_ID, "outcome_id": "outcome_test", "result": "EXPIRED",
             "score_basis": "PRECOMMITTED_EXPIRY_OR_TIME_EXIT", "triggered_at_utc": gold_export["registered_at_utc"],
             "resolved_at_utc": (posts._utc(gold_export["registered_at_utc"]) + timedelta(hours=2)).isoformat()}
    run = _announced_then(gold_export, tmp_path, main_root, monkeypatch, status="CLOSED",
                          outcome={"state": "SCORED", "result": "EXPIRED", "outcome_id": "outcome_test",
                                   "result_r": -0.1, "score": score})
    assert run["status"] == "OK", run
    assert not [r for r in run["queued"] if r["kind"] == "result"]
    assert "JIM_PAUSE_RESULT_SHOWN_IN_SCORECARD" in {s.get("cause") for s in run.get("not_posted") or []}
