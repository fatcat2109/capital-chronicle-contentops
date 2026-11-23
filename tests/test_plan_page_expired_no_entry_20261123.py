"""Pre-relaunch (23 Nov 2026): an untriggered plan that Main ended without a market cancel reads
'expired, no entry' on its page, as the scorecard and Main's export now show it.

Seen: Bitcoin plan_caf370e4's page said "cancelled"; Main exported it CANCELLED at 21 Nov 00:00:44Z
(the result post's outcome_source_plan holds that record) and now exports EXPIRED at 23 Nov 00:00Z,
untriggered, with no cancel transition.
"""
import pytest

from live_contentops import plan_analysis_pages_v1 as pages, plan_reader_copy_v1 as reader
from live_contentops import plan_status_posts_v1 as posts
from test_plan_analysis_pages_cc432 import source  # noqa: F401
from test_plan_page_current_cc584 import frozen_gold_reasoning, gold_18_nov  # noqa: F401

UNTRIGGERED = {"state": "NOT_SCORED_UNTRIGGERED", "first_cause": "UNTRIGGERED_PLAN_ENDED"}
BTC = {  # the exported registration, as the stored result post and today's export hold it
    "plan_id": "plan_caf370e4bd6053e0a4cdfef8", "asset_id": "BTCUSD", "direction": "BEARISH",
    "registration_hash": "23d10ed01335f6bbe098e3d6f59ecd4ecb87d48527a586e224a9facf587ab489",
    "registered_at_utc": "2026-11-20T23:04:34.309572Z", "entry_deadline_utc": "2026-11-27T21:00:00Z",
    "expires_at_utc": "2026-11-27T21:00:00Z", "zone": {"minimum": 56000, "maximum": 56500},
    "invalidation_conditions": [{"field": "close", "operator": "GT", "threshold": 61940.88}],
}


def test_the_bitcoin_record_of_21_nov_reads_expired_no_entry():
    current = {**BTC, "status": "CANCELLED", "status_at_utc": "2026-11-21T00:00:44.078717Z",
               "cancel_kind": None, "first_blocking_cause": None, "last_price": 58834.45, "outcome": UNTRIGGERED}
    final = pages.ended_plan_status(BTC, current, now=posts._utc("2026-11-21T13:28:42Z"))
    assert final == {"status": "EXPIRED", "status_at_utc": "2026-11-21T00:00:44.078717Z", "no_entry": True,
                     "export_status": "CANCELLED", "ended_before_entry_deadline": True}


def test_todays_export_of_the_same_plan_reads_expired_no_entry():
    current = {**BTC, "status": "EXPIRED", "status_at_utc": "2026-11-23T00:00:00Z", "cancel_kind": None,
               "first_cause": "OCO_DIFFERENT_FROZEN_PLAN", "outcome": UNTRIGGERED}
    final = pages.ended_plan_status(BTC, current, now=posts._utc("2026-11-23T12:00:00Z"))
    assert final == {"status": "EXPIRED", "status_at_utc": "2026-11-23T00:00:00Z", "no_entry": True,
                     "ended_before_entry_deadline": True}


@pytest.mark.parametrize("change,status", [
    ({"cancel_kind": "RUNAWAY_BEFORE_PULLBACK"}, "CANCELLED"),  # a market cancel keeps its word
    ({"outcome": {"state": "PENDING"}}, "CANCELLED"),            # triggered, then stopped by the order path
    ({"outcome": None}, "CANCELLED"),                            # no outcome on the record: unchanged
    ({"status": "INVALIDATED"}, "INVALIDATED"),                  # the plan's own cancel level
    ({"status": "VIEW_CHANGED"}, "VIEW_CHANGED"),
])
def test_other_ends_keep_mains_word(change, status):
    current = {**BTC, "status": "CANCELLED", "status_at_utc": "2026-11-21T00:00:44Z", "outcome": UNTRIGGERED,
               **change}
    final = pages.ended_plan_status(BTC, current, now=posts._utc("2026-11-21T13:28:42Z"))
    assert final["status"] == status and "no_entry" not in final


def _render(raw, manuscript, final, tmp_path, monkeypatch, run):
    monkeypatch.setattr(pages, "load_run", lambda *a, **k: run)
    monkeypatch.setattr(pages, "_card", lambda *a: None)
    monkeypatch.setattr(pages, "_closed_plan_chart", lambda *a: None)
    return pages.render(raw, manuscript, output_dir=tmp_path / "page", final_status=final)


def _manuscript(raw, run):
    from live_contentops import plan_reader_editorial_v1 as editorial
    from test_plan_thread_consistency_cc549 import authored
    source = reader.source_packet(raw, run, thread=True, level_contract=reader.LEVEL_CONTRACT)
    return editorial.bind_manuscript(authored(source), source, raw)


def test_the_page_says_expired_no_entry_where_it_said_cancelled(gold_18_nov, frozen_gold_reasoning, tmp_path,
                                                                monkeypatch):
    raw = {**gold_18_nov, "status": "WAITING", "run_id": "retained-gold", "analysis_result_hash": "retained"}
    run = frozen_gold_reasoning
    run["source_plan"] = raw
    current = {**raw, "status": "CANCELLED", "status_at_utc": "2026-11-18T07:43:00Z", "outcome": UNTRIGGERED}
    now = posts._utc("2026-11-18T07:45:00Z")
    monkeypatch.setattr(posts, "current_public_plan", lambda *a, **k: current)
    final = pages.ended_plan_status(raw, current, now=now)
    packet = _render(raw, _manuscript(raw, run), final, tmp_path, monkeypatch, run)
    title, body = packet["native_payload"]["title"], packet["native_payload"]["body_markdown"]
    assert title.endswith("(plan expired, no entry)")
    assert "Status: expired, no entry (updated Wed 18 Nov, 2:43 AM ET)." in body
    assert "Status: cancelled" not in body
    # The daily CC-584 check reads 'status: <word>' from FINAL_STATES; the line still carries it.
    assert "status: " + pages.FINAL_STATES[final["status"]] in body.casefold()
    assert pages.require_current_page(packet, now=now) == current


def test_a_page_stored_before_the_change_keeps_its_bytes(gold_18_nov, frozen_gold_reasoning, tmp_path, monkeypatch):
    raw = {**gold_18_nov, "status": "WAITING", "run_id": "retained-gold", "analysis_result_hash": "retained"}
    run = frozen_gold_reasoning
    run["source_plan"] = raw
    stored = {"status": "CANCELLED", "status_at_utc": "2026-11-18T07:43:00Z", "ended_before_entry_deadline": True}
    packet = _render(raw, _manuscript(raw, run), stored, tmp_path, monkeypatch, run)
    assert packet["native_payload"]["title"].endswith("(plan cancelled)")
    assert "Status: cancelled (updated Wed 18 Nov, 2:43 AM ET)." in packet["native_payload"]["body_markdown"]
