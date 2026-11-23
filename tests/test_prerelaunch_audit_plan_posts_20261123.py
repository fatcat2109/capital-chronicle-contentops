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
     "The rejected break is a spring and trapped bets on a fall fuel a squeeze through 61,581.46 toward 62,571.63."),
    ("Speculators hold fewer net long positions than usual.", "Speculators hold fewer net bets on a rise than usual."),
    ("The incident is not officially confirmed in the frozen files, so no shock premium is assumed.",
     "The incident is not officially confirmed, so no shock premium is assumed."),
    ("A completed D1 close above 66095.46, or the broker stop at 68450.00.", "A completed daily close above 66,095.46."),
    ("A completed M15 high at or above 3609.00.", "A completed 15-minute high at or above 3,609.00."),
    # Builder C, 23 Nov: on a page "shorts" were the desk's trades; "traders positioned for losses" inverted it.
    ("The desk's own recent shorts in this market have paid.", "The desk's own recent bets on a fall in this market have paid."),
    ("BTC trades as high-beta equity, 60-day US500 beta 1.35 and correlation 0.63.",
     "BTC trades as high-beta equity, 60-day S&P 500 beta 1.35 and correlation 0.63."),
])
def test_scenario_voice_quotes_read_for_people(btc, span, expected):
    assert reader._public_plan_quote(span, btc, scenario_voice=True) == expected


@pytest.mark.parametrize("span", [
    "68450.00 is above the 14 Nov high, above the lane's measured minimum 6,862.67, so ordinary noise does not reach it.",
    "The stop sits 2.41 normal days from the reference.",
])
def test_scenario_voice_drops_desk_notes_and_fragments(btc, span):
    with pytest.raises(ValueError, match="SCENARIO_VOICE_DESK_TERM|LAYER|CC466"):
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


def test_case_lines_never_open_on_a_clause_whose_subject_was_dropped(btc):
    """Builder C, 23 Nov: "BTC carries that through a 1.31 beta" came from the second clause of a driver."""
    plan = {**btc, "scenario_analysis": {**btc["scenario_analysis"],
            "mechanism": "deleveraging priced per block cc442:0a549244c48a9832c461; BTC carries that through a 1.31 beta.",
            "driver": "Rate expectations rose after the jobs report. Crypto funds saw outflows for a third week."}}
    cases = reader.scenario_case_copy(plan)
    lines = [line for case in cases for line in (case["heading"], *case["support"])]
    assert not any("carries that" in line for line in lines)
    # The 23 Nov plan's stop note ends in a list label; its first clause is a desk note, so no "undo" line is cut from it.
    original = [line for case in reader.scenario_case_copy(btc) for line in (case["heading"], *case["support"])]
    assert not any("Stop tightening" in line or "stop sits" in line for line in original)
    assert ("Base case driver: Rate expectations rose after the jobs report. "
            "Crypto funds saw outflows for a third week.") in lines


def test_reader_fields_accept_the_scenario_voice_labels():
    """Decision 158: the validator takes "Base case"/"Bull case" beside the earlier "Main"/"Alternative"."""
    text = ("Base case (54%): Bitcoin stays below 60,977 at the exit. "
            "Bull case (46%): Bitcoin holds 60,283 and turns higher.")
    source = {"thread_contract": reader.THREAD_CONTRACT, "sources": [{"id": "s1", "layer": "scenarios", "text": text}],
              "scenario_analysis": {"base_case": {"probability_pct": 54}, "main_alternative": {"probability_pct": 46}}}

    def fields(main, alt):
        return {"hook": {"text": "Bitcoin waits below 60,977.", "source_ids": ["s1"]}, "points": [],
                "scenario_main": {"text": main, "source_ids": ["s1"]},
                "scenario_alt": {"text": alt, "source_ids": ["s1"]}}

    reader.validate_fields(fields("Base case (54%): Bitcoin stays below 60,977 at the exit.",
                                  "Bull case (46%): Bitcoin holds 60,283 and turns higher."), source)
    reader.validate_fields(fields("Main (54%): Bitcoin stays below 60,977 at the exit.",
                                  "Alternative (46%): Bitcoin holds 60,283 and turns higher."), source)
    with pytest.raises(ValueError, match="CC466_SCENARIO_ODDS_CHANGED"):
        reader.validate_fields(fields("Base case (54%): Bitcoin stays below 60,977 at the exit.",
                                      "Bull case (54%): Bitcoin holds 60,283 and turns higher."), source)
    with pytest.raises(ValueError, match="CC466_MAIN_ODDS_REQUIRED"):
        reader.validate_fields(fields("Bitcoin stays below 60,977 at the exit.",
                                      "Bull case (46%): Bitcoin holds 60,283 and turns higher."), source)


PROMISED = "plan_4bcfb1182f0fff4f8254172c"


@pytest.mark.parametrize(("plan_id", "resolved_at", "posts_it"), [
    (PROMISED, "2026-11-23T03:00:13Z", True),   # the real close, before the pause
    (PROMISED, "2026-11-24T12:00:00Z", True),   # scored with a clock inside the pause: still promised
    ("plan_a5749b44e7c886ca7220670f", "2026-11-24T12:00:00Z", False),  # any other plan: the scorecard shows it
])
def test_a_result_promised_by_a_published_correction_posts_a_week_later(
        gold_export, tmp_path, main_root, monkeypatch, plan_id, resolved_at, posts_it):
    """Ops Product, 23 Nov: Telegram 232 promised the 20 Nov USD/JPY result "in its own post"."""
    import sys
    from live_contentops import plan_analysis_pages_v1 as pages
    from live_contentops import secret_store_v1
    from test_plan_call_cards_cc399 import rows, write
    from test_plan_status_posts_cc306 import event
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    monkeypatch.setattr(pages, "confirmed_publication", lambda *args: None)
    store = ContentOpsDurableStore(tmp_path / "promised.sqlite3")
    plan = {**gold_export, "plan_id": plan_id}
    events = [event(plan_id, "WAITING", plan["registered_at_utc"])]

    def queue(raw, now):
        folder = write(tmp_path / "export", [raw], events, generated_at_utc=now.isoformat())
        run = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
        assert run["status"] == "OK", run
        return run

    setup_run = queue(plan, posts._utc(plan["registered_at_utc"]) + timedelta(seconds=1))
    setup_key, = [row["key"] for row in setup_run["queued"]]
    store.set_outbox_status(setup_key, "PUBLISHED")
    events.append(event(plan_id, "FILLED", "2026-11-19T09:44:07Z"))
    events.append(event(plan_id, "CLOSED", resolved_at))
    outcome_id = "outcome_promised_" + plan_id[-6:]
    score = {"asset_id": "XAUUSD", "plan_id": plan_id, "outcome_id": outcome_id, "result": "EXPIRED",
             "score_basis": "TIME_EXIT", "triggered_at_utc": "2026-11-19T09:44:07Z", "resolved_at_utc": resolved_at}
    closed = {**plan, "status": "CLOSED", "outcome": {"state": "SCORED", "result": "EXPIRED", "outcome_id": outcome_id,
                                                      "result_r": -0.3, "score": score}}
    week_later = posts._utc("2026-11-30T18:00:00Z")
    run = queue(closed, week_later)
    results = [row for row in rows(store) if row["kind"] == "result"]
    if not posts_it:
        assert results == []
        assert any(item["cause"] == "JIM_PAUSE_RESULT_SHOWN_IN_SCORECARD" for item in run["not_posted"])
        return
    result, = results
    dates = cards.plan_dates(plan["registered_at_utc"], resolved_at)
    assert result["text"].startswith(f"Gold, plan of {dates}: closed at its time exit")
    alerts.validate(result, store=store)
    # Queued a week after its ending, it still reaches every destination, once.
    held = store.get_outbox_message(result["key"])
    assert cards.settle_pending(store, held, result, now=week_later + timedelta(minutes=1)) is None
    assert queue(closed, week_later + timedelta(minutes=1))["queued"] == []
