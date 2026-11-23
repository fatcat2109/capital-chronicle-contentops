"""Pre-relaunch audit of the plan posts and the relaunch path (Jim, 23 Nov 2026: audit before going live again).

Each test names the defect the audit found on copies of the 19-23 Nov rows and of Main's export.
No production store, browser, model or network is used.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import scenario_voice_v1 as voice
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
from test_plan_copy_cc682 import gold_export, replay_gold  # noqa: F401
from test_plan_status_posts_cc306 import main_root  # noqa: F401

FIXTURE = Path(__file__).parents[1] / "docs/publisher/prerelaunch-audit-20261123/fixtures/btcusd-plan-20261123.json"
LIMITS = {"x": 280, "threads": 500}


# --- the relaunch path -------------------------------------------------------------------------------------

def test_a_dated_result_queued_at_the_relaunch_is_not_closed_by_its_old_ending(tmp_path):
    """Seen in the simulation: a result that ended before the pause went to Telegram and Discord, then its seven
    other destinations were closed in the same minute (PUBLISHING_OLDER_THAN_24_HOURS)."""
    from test_minute_consumer_cc515 import NOW, retained
    store = ContentOpsDurableStore(tmp_path / "owed.sqlite3")
    queued = (NOW - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    fresh = retained(store, "relaunch-result", kind="result", hours=24 * 7, status="PUBLISHING",
                     result_queued_at_utc=queued)
    assert cards.settle_pending(store, store.get_outbox_message(fresh["key"]), fresh, now=NOW) is None
    # The attempt itself still ends after 24 hours (CC-515), counted from when it was queued.
    stale = retained(store, "stuck-result", kind="result", hours=24 * 7, status="PUBLISHING",
                     result_queued_at_utc=(NOW - timedelta(hours=25)).isoformat())
    settled = cards.settle_pending(store, store.get_outbox_message(stale["key"]), stale, now=NOW)
    assert settled["status"] == "SETTLED" and settled["cause"] == "PUBLISHING_OLDER_THAN_24_HOURS"
    # A fill is not a result: an update older than 24 hours still settles at the relaunch.
    fill = retained(store, "pause-fill", kind="update", hours=30, status=posts.READY,
                    result_queued_at_utc=queued)
    assert cards.settle_pending(store, store.get_outbox_message(fill["key"]), fill, now=NOW)["status"] == "SETTLED"


def test_new_result_rows_record_when_they_were_queued(replay_gold):
    setup, fill, result = replay_gold
    queued = posts._utc(result["at_utc"]) + timedelta(seconds=1)
    assert result["result_queued_at_utc"] == queued.isoformat().replace("+00:00", "Z")
    assert "result_queued_at_utc" not in setup and "result_queued_at_utc" not in fill
    assert alerts.compose(result)["text"] == result["text"]


@pytest.mark.parametrize(("ended", "minutes_later", "record", "inside"), [
    ("2026-11-24T10:00:00Z", 5, "closed", True),       # ended inside the pause: never posted
    ("2026-11-29T23:58:00Z", 2, "closed", True),       # just before a 30 Nov restore: still inside
    ("2026-11-30T18:05:00Z", 2, "closed", False),      # after the restore: posted
    ("2026-11-23T04:40:00Z", 60 * 24 * 7, "closed", False),  # before the pause: posted, dated
    ("2026-11-30T18:05:00Z", 2, "missing", False),     # restore record missing, job running: fresh news posts
    ("2026-11-30T16:00:00Z", 125, "missing", True),    # record missing: an older ending stays off
    ("2026-11-24T10:00:00Z", 3, "missing", True),      # before the earliest resume: stays off
])
def test_pause_window_and_a_missing_restore_record(ended, minutes_later, record, inside):
    """Audit finding: with restored.json absent the window never closed, so every later result was skipped for good."""
    end = posts._utc("2026-11-30T18:00:00Z") if record == "closed" else cards.OPEN_PAUSE_END
    now = posts._utc(ended) + timedelta(minutes=minutes_later)
    assert cards.inside_jim_pause(ended, now, (cards.JIM_PAUSE_START, end)) is inside


def test_the_live_window_reads_the_restore_record_and_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr(cards, "JIM_PAUSE_RECORD", tmp_path / "restored.json")
    assert cards.jim_pause_window(live=True) == (cards.JIM_PAUSE_START, cards.OPEN_PAUSE_END)
    (tmp_path / "restored.json").write_text(json.dumps({"started_at_utc": "2026-11-30T18:00:00Z"}), encoding="utf-8")
    assert cards.jim_pause_window(live=True)[1] == posts._utc("2026-11-30T18:00:00Z")
    (tmp_path / "restored.json").write_text("{", encoding="utf-8")
    assert cards.jim_pause_window(live=True)[1] == cards.JIM_PAUSE_END


# --- the scenario voice of decision 158 on the 23 Nov plans ---------------------------------------------------

@pytest.fixture
def btc():
    return json.loads(FIXTURE.read_bytes())


@pytest.mark.parametrize(("span", "expected"), [
    ("BTCUSD is below 60977.64 at 2026-11-25T03:00Z.", "Bitcoin is below 60,977.64 at Tue 24 Nov, 10:00 PM ET."),
    ("The rejected break is a spring and trapped shorts fuel a squeeze through 61581.46 toward 62571.63.",
     "The rejected break is a spring and trapped traders betting on a fall fuel a squeeze through 61,581.46 toward 62,571.63."),
    ("Speculators hold fewer net long positions than usual.", "Speculators hold fewer net bets on a rise than usual."),
    ("The incident is not officially confirmed in the frozen files, so no shock premium is assumed.",
     "The incident is not officially confirmed, so no shock premium is assumed."),
    ("A completed D1 close above 66095.46, or the broker stop at 68450.00.", "A completed daily close above 66,095.46."),
    ("A completed M15 high at or above 3609.00.", "A completed 15-minute high at or above 3,609.00."),
    ("BTC trades as high-beta equity, 60-day US500 beta 1.35 and correlation 0.63.",
     "BTC trades as high-beta equity, 60-day S&P 500 beta 1.35 and correlation 0.63."),
])
def test_scenario_voice_quotes_read_for_people(btc, span, expected):
    assert reader._public_plan_quote(span, btc, scenario_voice=True) == expected


@pytest.mark.parametrize("span", [
    "68450.00 is above the 14 Nov high, above the lane's measured minimum 6,862.67, so ordinary noise does not reach it.",
    "Stop tightening fact.",
    "The stop sits 2.41 normal days from the reference.",
])
def test_scenario_voice_drops_desk_notes_and_fragments(btc, span):
    with pytest.raises(ValueError, match="SCENARIO_VOICE_(?:DESK_TERM|FRAGMENT)|LAYER|CC466"):
        reader._public_plan_quote(span, btc, scenario_voice=True)


def test_rows_without_the_scenario_voice_keep_their_quotes(btc):
    # Stored rows recompose from the same function: their wording must not move.
    assert reader._public_plan_quote("BTCUSD is below 60977.64 at 2026-11-25T03:00Z.", btc) == (
        "BTCUSD is below 60977.64 at Tue 24 Nov, 10:00 PM ET.")


def voice_row(raw, *, scenario=True):
    terms = reader.thread_terms(raw, level_contract=reader.CURRENT_LEVEL_CONTRACT)
    row = {"schema_version": posts.SCHEMA, "format": cards.FORMAT, "key": "plan-status-post-audit",
           "plan_id": raw["plan_id"], "kind": "setup", "state": "WAITING", "symbol": raw["asset_id"],
           "levels": cards.card_plan(raw), "instrument_title": terms["market"],
           "at_utc": raw["registered_at_utc"], "registered_at_utc": raw["registered_at_utc"],
           "entry_deadline_utc": terms["entry_deadline_utc"], "time_exit_utc": terms["time_exit_utc"],
           "source_plan": raw, "source_plan_registration": raw["registration_hash"],
           "state_alert_contract": alerts.CONTRACT, "state_alert_source_sha256": posts._sha(raw),
           "thread_contract": reader.THREAD_CONTRACT, "level_contract": reader.CURRENT_LEVEL_CONTRACT,
           "price_basis": terms["price_basis"], "target_policy": cards.NO_TARGET_POLICY,
           "analysis_copy_contract": reader.NINE_LAYER_COPY}
    if scenario:
        row["scenario_voice"] = voice.CONTRACT
    row["analysis_layer_quotes"] = reader.plan_layer_candidates(raw, scenario_voice=scenario)[0]
    row["analysis_layer_quotes"] = {k: v[0]["text"] for k, v in row["analysis_layer_quotes"].items()}
    row["analysis_layer_gaps"] = reader.plan_layer_candidates(raw, scenario_voice=scenario)[1]
    row.update(cards.compose(row))
    return row


def test_a_waiting_plan_reads_plainly_in_the_scenario_voice(btc):
    row = voice_row(btc)
    assert "Bitcoin: waiting for price to break through 60,250 (breakout)." in row["text"]
    assert "armed" not in row["text"] and "BTCUSD" not in row["text"] and "frozen" not in row["text"]
    assert row["text"].startswith("Scenarios: Base case (54%): Bitcoin is below 60,977.64")
    alerts.validate(row)
    # The legacy wording stays byte-identical for rows queued without the voice.
    assert "Bitcoin: armed, waiting for price breaks through 60,250 (breakout)." in voice_row(btc, scenario=False)["text"]


def test_short_routes_give_the_call_right_after_the_cases(btc):
    """X carried the zone and the cancel line in post 8 of 10 and Threads in its last part."""
    row = voice_row(btc)
    copies = cards.destination_payloads(row, card_id="chart", chart_credit=True, complete_levels=True)
    call = "We are bearish on Bitcoin if price breaks through 60,250 (breakout)."
    x = copies["x"]["posts"]
    assert x[0]["text"].startswith("Scenarios: Base case (54%)") and x[0]["media_asset_ids"] == ["chart"]
    assert any(call in part["text"] for part in x[:4])
    threads = [copies["threads"]["text"], *copies["threads"]["reply_texts"]]
    assert any(call in part for part in threads[:2])
    for destination, parts in (("x", [p["text"] for p in x]), ("threads", threads)):
        width = posts._x_length if destination == "x" else len
        full = "\n\n".join(parts)
        assert full.count(PUBLIC_NOTICE) == 1 and full.count(CONFLICTS_NOTICE) == 1, destination
        assert "Chart: TradingView" in parts[0], destination
        for part in parts:
            assert width(part) <= LIMITS[destination], destination
            assert "…" not in part
            assert part.rstrip()[-1] in ".)" or part.rstrip().endswith(("TradingView", "trading-rule-before")), part
        for line in row["text"].splitlines():
            if line and line not in (PUBLIC_NOTICE + " " + CONFLICTS_NOTICE,):
                assert line in full, (destination, line)


def test_every_destination_keeps_targets_off_and_one_notice(btc):
    row = voice_row(btc)
    copies = cards.destination_payloads(row, card_id="chart", chart_credit=True, complete_levels=True)
    target = cards.level(btc["target_level"], row["levels"])
    assert set(copies) == set(cards.destinations_for(row))
    for destination, copy in copies.items():
        full = copy["full_text"]
        assert target not in full and "Target level" not in full, destination
        assert full.count(PUBLIC_NOTICE) == 1, destination
        assert voice.validate_copy(full) == [] or destination == "x"


def test_linkedin_overflow_keeps_whole_sentences(btc):
    row = voice_row(btc)
    body, notices = posts._split(row["text"])
    layers = alerts.analysis_lines(row)
    long_layers = [*layers, *(f"Macro: A long sentence about rates number {i} that fills the post." * 3
                               for i in range(40))]
    long_body = "\n".join([*long_layers, *body.splitlines()[len(layers):]])
    parts = alerts.nine_layer_parts(long_layers, long_body, notices, destination="linkedin", limit=3000,
                                    reply_limit=3000, whole_lines=True)
    assert len(parts) == 1 and len(parts[0]) <= 3000 and "…" not in parts[0]
    assert parts[0].startswith("Scenarios: Base case") and parts[0].endswith(notices)
    assert "We are bearish on Bitcoin" in parts[0]
