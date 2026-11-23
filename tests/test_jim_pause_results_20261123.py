"""Jim's pause (23 Nov 04:50Z to 25 Nov 16:00Z): a result inside it is not posted; one outside it still is."""
from datetime import datetime, timedelta, timezone
import sys

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import secret_store_v1
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_call_cards_cc399 import rows, write
from test_plan_copy_cc682 import GOLD_PLAN_ID, PAGE_LINK, gold_export  # noqa: F401
from test_plan_status_posts_cc306 import event, main_root  # noqa: F401


def replay(gold_export, tmp_path, main_root, monkeypatch):
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    monkeypatch.setattr(pages, "confirmed_publication", lambda *args: {
        "plan_id": GOLD_PLAN_ID, "registration_hash": gold_export["registration_hash"],
        "canonical_url": PAGE_LINK, "summary": {"macro": "Fed path via real yields."}})
    store = ContentOpsDurableStore(tmp_path / "replay.sqlite3")
    events = []

    def queue(plan, state, at):
        events.append(event(GOLD_PLAN_ID, state, at))
        now = posts._utc(at) + timedelta(seconds=1)
        folder = write(tmp_path / "export", [plan], events, generated_at_utc=now.isoformat())
        return posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)

    setup = queue(gold_export, "WAITING", gold_export["registered_at_utc"])
    store.set_outbox_status(setup["queued"][0]["key"], "PUBLISHED")
    filled_at, resolved_at = "2026-11-19T09:44:07.552000Z", "2026-11-19T21:24:24.796000Z"
    queue({**gold_export, "status": "FILLED"}, "FILLED", filled_at)
    outcome_id = "outcome_7af1f8a0dfef1cef3779361d8f333c0b"
    score = {"asset_id": "XAUUSD", "plan_id": GOLD_PLAN_ID, "outcome_id": outcome_id, "result": "HIT",
             "score_basis": "BROKER_TAKE_PROFIT", "triggered_at_utc": filled_at, "resolved_at_utc": resolved_at}
    outcome = {"state": "SCORED", "result": "HIT", "outcome_id": outcome_id, "result_r": 1.5569006129583767, "score": score}
    return store, queue({**gold_export, "status": "CLOSED", "outcome": outcome}, "CLOSED", resolved_at)


def test_a_result_inside_the_pause_is_skipped_and_never_queued(gold_export, tmp_path, main_root, monkeypatch):
    monkeypatch.setattr(cards, "JIM_PAUSE_START", datetime(2026, 11, 19, 21, 0, tzinfo=timezone.utc))
    monkeypatch.setattr(cards, "JIM_PAUSE_END", datetime(2026, 11, 20, 0, 0, tzinfo=timezone.utc))
    store, run = replay(gold_export, tmp_path, main_root, monkeypatch)
    assert run["status"] == "OK", run
    assert not [r for r in run["queued"] if r["kind"] == "result"]
    details = run.get("not_posted") or []
    assert "JIM_PAUSE_RESULT_SHOWN_IN_SCORECARD" in {s.get("cause") for s in details if isinstance(s, dict)}
    assert not [r for r in rows(store) if r["kind"] == "result"]


def test_a_result_outside_the_pause_is_still_posted(gold_export, tmp_path, main_root, monkeypatch):
    store, run = replay(gold_export, tmp_path, main_root, monkeypatch)
    assert [r["kind"] for r in run["queued"]] == ["result"]


@pytest.mark.parametrize(("at", "inside"), [("2026-11-23T04:49:59Z", False), ("2026-11-23T04:50:00Z", True),
                                            ("2026-11-25T15:59:59Z", True), ("2026-11-25T16:00:00Z", False)])
def test_the_window_is_jims_exact_times(at, inside):
    assert (cards.JIM_PAUSE_START <= posts._utc(at) < cards.JIM_PAUSE_END) is inside


def test_the_live_window_runs_until_the_restore_record(tmp_path, monkeypatch):
    """Jim, 23 Nov 09:22Z: the pause lasts until the relaunch, whenever the restore runs."""
    import json as _json
    record = tmp_path / "restored.json"
    monkeypatch.setattr(cards, "JIM_PAUSE_RECORD", record)
    start, end = cards.jim_pause_window(live=True)
    assert start == cards.JIM_PAUSE_START and end.year == 9999  # no record yet: still paused
    record.write_text(_json.dumps({"started_at_utc": "2026-11-30T03:00:00+00:00"}), encoding="utf-8")
    assert cards.jim_pause_window(live=True)[1] == datetime(2026, 11, 30, 3, 0, tzinfo=timezone.utc)
    record.write_text("{not json", encoding="utf-8")
    assert cards.jim_pause_window(live=True)[1] == cards.JIM_PAUSE_END  # unreadable: the fixed fallback
    assert cards.jim_pause_window() == (cards.JIM_PAUSE_START, cards.JIM_PAUSE_END)  # tests never read the live file
