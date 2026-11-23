"""The installed minute consumer uses Main's board through the real coordinator.

All stores, source dates and transport observations here are controlled fixtures.
They do not establish any live publication day.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops import daily_trend_board_v1 as board
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
from test_publication_coordinator_v1 import FixtureTransport, _set_mode


class BoardTransport(FixtureTransport):
    def publish(self, *, destination, intent, authorization_context):
        result = super().publish(destination=destination, intent=intent, authorization_context=authorization_context)
        result.update(id=sha256(intent["work_item_id"].encode()).hexdigest()[:16],
                      public_url="https://example.test/" + destination + "/" + intent["work_item_id"])
        return result


def at(day="2026-11-16"):
    return datetime.combine(date.fromisoformat(day) + timedelta(days=1), datetime.min.time(), timezone.utc) + timedelta(hours=2)


def source(day="2026-11-16"):
    markets = {}
    for index, symbol in enumerate(board.MARKETS):
        markets[symbol] = {"yardstick": {"state": "AVAILABLE", "yardstick": "DOWN",
            "last_completed_bar_utc": day + "T00:00:00Z", "mean_close_20": 100 + index,
            "mean_close_50": 120 + index}, "rows_whose_condition_holds_now": [
            {"behaviour": "SHORT_WHILE_DOWN_20", "side": "SHORT",
             "this_side": [42 + index, 0.31, -0.195, -1.1, 0.09, -0.51, "LOST"],
             "both_sides_together": [999, 9.999, 0, 0, 0, "PAID"],
             "sample_period": {"start": "2016-11-01", "end": "2026-11-12"}}]}
    return seal({"schema": "CapitalChronicleDeskBoardPublicV1", "as_of_utc": at(day).isoformat(),
        "yardstick_rule": "UP when 20-session and 60-session changes are positive and price is above its 20-session and 50-session mean; DOWN when all four are negative; otherwise MIXED.",
        "measured_table": {"state": "AVAILABLE", "table_content_hash": "a" * 64}, "markets": markets})


def seal(value):
    value.pop("content_hash", None)
    value["content_hash"] = sha256_of(value)
    return value


def no_snapshot(*args, **kwargs):
    raise tv.SnapshotError("CONTROLLED_SNAPSHOT_UNAVAILABLE")


@pytest.fixture
def ready(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    reference = {"identity": "cc536-measured-odds-1", "plan_hash": "b" * 64,
                 "canonical_url": "https://capitalchronicle.substack.com/p/method-and-limits", "table_hash": "c" * 64}
    from live_contentops import measured_odds_series_v1 as series
    monkeypatch.setattr(series, "confirmed_method_page", lambda s: deepcopy(reference))
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "snapshot-outcomes.jsonl")
    return store, tmp_path / "posts"


def register(ready, value=None):
    store, root = ready
    value = value or source()
    return board.register(store, value, source_path=root / "producer.json", output_root=root,
                          now=at(value["markets"]["XAUUSD"]["yardstick"]["last_completed_bar_utc"][:10]),
                          snapshot=no_snapshot)


def clock(monkeypatch, now):
    class Fixed(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)
    monkeypatch.setattr(pages, "datetime", Fixed)


def delivery(runtime, now):
    def send(store, value, *, command="resume", **kwargs):
        coordinator = Coordinator(store=store, transport_runtime=runtime,
            readiness_provider=lambda d: {"readiness_state": "READY_AUTHENTICATED"}, clock=lambda: now)
        coordinator.allow_prior_confirmed_distribution = True
        coordinator.recovery_scope = {"work_item_id": value["link_id"], "plan": value["plan"], "exact_work_item_only": True}
        if command == "readback":
            ids = coordinator._ids(value["link_id"], value["plan"]["plan_hash"], value["destination"])
            return coordinator.readback_existing_dispatch(ids["dispatch_id"])
        return coordinator.publish_plan(value["link_id"], value["plan"])
    return send


def write(tmp_path, value):
    path = tmp_path / "producer-board.json"
    path.write_bytes(canonical_bytes(value))
    return path


def test_six_markets_all_source_rows_and_real_mean_tuple_index_feed_public_copy(ready):
    value = source()
    value["markets"]["XAUUSD"]["named_triggers"] = [{"level": 888888, "sentence": "private trigger"}]
    value["markets"]["XAUUSD"]["account"] = 279805139
    seal(value)
    stored = register(ready, value)
    copies = [link["native_payload"] for link in stored["links"]]
    note = next(p for p in copies if p["destination"] == "substack_notes")["text"]
    assert all(name in note for name in board.MARKETS.values())
    assert "-0.195R mean on 42 cases, 2016-11-01 to 2026-11-12" in note
    assert "20 sessions 100; 50 sessions 120" in note
    assert all(str(private) not in note for private in ("888888", "279805139", "private trigger", "9.999", "0.31"))
    assert stored["counts_as_article"] is False
    for payload in copies:
        if payload["destination"] == "discord":
            assert len(payload["text"]) <= 1900
        if payload["destination"] == "x":
            assert all(len(post["text"]) <= 280 for post in payload["posts"])
            assert payload["posts"][0]["media_asset_ids"]
    assert "Method and limits" in note and board.PUBLIC_NOTICE in note


@pytest.mark.parametrize("mutation,path", [
    ("mean", "/markets/XAUUSD/yardstick/mean_close_20"),
    ("period", "/markets/XAUUSD/rows_whose_condition_holds_now/0/sample_period"),
    ("row", "/markets/XAUUSD/rows_whose_condition_holds_now/0/this_side"),
])
def test_absent_producer_field_posts_nothing_and_never_requests_media(ready, tmp_path, monkeypatch, mutation, path):
    value = source()
    if mutation == "mean":
        value["markets"]["XAUUSD"]["yardstick"].pop("mean_close_20")
    elif mutation == "period":
        value["markets"]["XAUUSD"]["rows_whose_condition_holds_now"][0].pop("sample_period")
    else:
        value["markets"]["XAUUSD"]["rows_whose_condition_holds_now"][0]["this_side"] = None
    path_to_board = write(tmp_path, seal(value))
    monkeypatch.setattr(board, "prepare_media", lambda *a, **k: pytest.fail("source refusal must precede media"))
    store, root = ready
    result = board.run_due(store, board_path=path_to_board, output_root=root, now=at())
    assert result["cause"] == "BOARD_PUBLIC_FIELDS_ABSENT" and path in result["missing_fields"]
    assert store.list_outbox_messages(destination=board.DESTINATION) == []


@pytest.mark.parametrize("change,cause", [
    ("hash", "BOARD_CONTENT_HASH_CHANGED"), ("future", "BOARD_FROM_FUTURE"),
    ("file_age", "BOARD_OLDER_THAN_ONE_TRADING_DAY"),
    ("bar_age", "BOARD_MARKET_DATA_OLDER_THAN_ONE_TRADING_DAY"),
    ("mismatch", "BOARD_MARKET_SESSIONS_DIFFER"),
    ("period_future", "BOARD_SAMPLE_ENDS_AFTER_SESSION"),
])
def test_source_clocks_and_hash_prevent_wrong_or_refreshed_stale_public_numbers(change, cause):
    value = source()
    if change == "hash":
        value["markets"]["XAUUSD"]["yardstick"]["mean_close_20"] = 999
    elif change == "future":
        value["as_of_utc"] = (at() + timedelta(seconds=1)).isoformat()
    elif change == "file_age":
        value["as_of_utc"] = "2026-11-12T02:00:00Z"
    elif change == "bar_age":
        for row in value["markets"].values():
            row["yardstick"]["last_completed_bar_utc"] = "2026-11-12T00:00:00Z"
    elif change == "mismatch":
        value["markets"]["US500"]["yardstick"]["last_completed_bar_utc"] = "2026-11-13T00:00:00Z"
    else:
        value["markets"]["US500"]["rows_whose_condition_holds_now"][0]["sample_period"]["end"] = "2026-11-17"
    if change != "hash":
        seal(value)
    with pytest.raises(board.BoardSourceError, match=cause):
        board.project(value, now=at() + timedelta(hours=12) if change == "period_future" else at())


@pytest.mark.parametrize("instant,expected", [
    ("2026-11-02T21:30:00Z", "2026-10-30"), ("2026-10-30T21:30:00Z", "2026-10-30"),
    ("2026-11-14T12:00:00Z", "2026-11-13"), ("2026-11-16T15:00:00Z", "2026-11-13"),
    ("2026-11-16T22:00:00Z", "2026-11-16"),
])
def test_new_york_close_dst_and_weekend_choose_the_public_session(instant, expected):
    assert board.latest_close(instant) == expected


def test_the_changed_market_is_the_headline_and_a_gap_is_never_called_yesterday():
    previous = board.project(source("2026-11-13"), now=at("2026-11-13"))
    value = source()
    value["markets"]["EURUSD"]["yardstick"]["yardstick"] = "UP"
    current = board.project(seal(value), now=at())
    copy = board.compose(current, previous)
    assert copy["headline"] == "EUR/USD turns UP" and copy["lead_market"] == "EURUSD"
    assert "EUR/USD DOWN to UP" in copy["changes"]
    previous["day_et"] = "2026-11-12"
    assert "not available" in board.compose(current, previous)["changes"]


def test_repeated_or_corrected_same_day_source_keeps_the_issued_bytes_and_chart(ready):
    first = register(ready)
    second = source()
    second["markets"]["XAUUSD"]["yardstick"]["mean_close_20"] = 999
    repeated = register(ready, seal(second))
    assert repeated == first
    assert len(ready[0].list_outbox_messages(destination=board.DESTINATION)) == 1
    asset, = first["media_assets"]
    assert asset["snapshot_failure"]["attempts"] == 2
    assert asset["data_card_packet"]["facts"][0][1] == "DOWN; 20-session mean 100; 50-session mean 120"


def test_weekend_bitcoin_uses_its_own_date_in_the_delivered_board(ready, tmp_path, monkeypatch):
    store, root = ready
    runtime = BoardTransport()
    now = datetime(2026, 11, 23, 2, 18, tzinfo=timezone.utc)
    value = source("2026-11-20")
    value["as_of_utc"] = now.isoformat()
    bitcoin = value["markets"]["BTCUSD"]
    bitcoin["yardstick"]["last_completed_bar_utc"] = "2026-11-22T00:00:00Z"
    bitcoin["rows_whose_condition_holds_now"][0]["sample_period"]["end"] = "2026-11-21"
    clock(monkeypatch, now)
    result = board.run_due(store, board_path=write(tmp_path, seal(value)), output_root=root, now=now,
                           snapshot=no_snapshot, deliver=delivery(runtime, now))

    assert result["day_et"] == "2026-11-20"
    assert result["state"] == "BOARD_COORDINATOR_RETURNED", result
    assert all(outcome["readback"]["confirmed"] for outcome in result["outcomes"])
    issued = json.loads(store.get_outbox_message(result["board_id"])["payload"])
    assert issued["current"]["markets"]["BTCUSD"]["session_date_et"] == "2026-11-22"
    for link in issued["links"]:
        text = link["native_payload"]["full_text"]
        assert "20 Nov 2026 close, ET (Bitcoin through 22 Nov 2026, ET)" in text
        assert "https://capitalchronicle.substack.com/p/method-and-limits" in text


def test_each_day_reaches_the_real_coordinator_once_and_three_fixture_days_require_all_readbacks(ready, tmp_path, monkeypatch):
    store, root = ready
    runtime = BoardTransport()
    for day in ("2026-11-12", "2026-11-13", "2026-11-16"):
        now = at(day)
        value = source(day)
        for row in value["markets"].values():
            row["rows_whose_condition_holds_now"][0]["sample_period"]["end"] = "2026-11-11"
        clock(monkeypatch, now)
        path = write(tmp_path, seal(value))
        result = board.run_due(store, board_path=path, output_root=root, now=now,
                               snapshot=no_snapshot, deliver=delivery(runtime, now))
        assert result["state"] == "BOARD_COORDINATOR_RETURNED", result
        assert all(o["readback"]["confirmed"] for o in result["outcomes"]), result
        before = list(runtime.publish_calls)
        repeated = board.run_due(store, board_path=path, output_root=root, now=now,
                                 snapshot=no_snapshot, deliver=delivery(runtime, now))
        assert repeated["state"] == "BOARD_REUSED" and runtime.publish_calls == before
    result = board.acceptance(store)
    assert result["passed"] and result["observed_consecutive_trading_days"] == 3
    assert set(runtime.publish_calls) == {"x", "discord", "substack_notes"}
    assert len(runtime.readback_calls) >= len(runtime.publish_calls)
    # Every transport intent is the source-matching, frozen, illustrated copy.
    for row in store.list_outbox_messages(destination=board.DESTINATION):
        for link in json.loads(row["payload"])["links"]:
            ids = Coordinator._ids(link["link_id"], link["plan"]["plan_hash"], link["destination"])
            intent = json.loads(store.get_outbox_message(ids["message_id"])["payload"])
            assert intent["native_payload"] == link["native_payload"]
            assert intent["media_assets"] == link["media_assets"]
            assert "published_content_export" not in intent


def test_lost_response_recovers_exact_dispatch_after_source_disappears_without_reposting(ready, tmp_path, monkeypatch):
    store, root = ready
    clock(monkeypatch, at())
    path = write(tmp_path, source())
    runtime = FixtureTransport(raise_after_write=True, ambiguous=True)
    first = board.run_due(store, board_path=path, output_root=root, now=at(),
                          snapshot=no_snapshot, deliver=delivery(runtime, at()))
    assert first["state"] == "BOARD_COORDINATOR_RETURNED"
    assert runtime.publish_calls and not board.acceptance(store)["passed"]
    first_calls = list(runtime.publish_calls)
    path.unlink()
    second = board.run_due(store, board_path=path, output_root=root, now=at(), deliver=delivery(runtime, at()))
    assert second["state"] == "BOARD_REUSED"
    assert runtime.publish_calls == first_calls
    assert runtime.readback_calls


def test_source_tampering_is_refused_by_the_existing_coordinator_before_transport(ready):
    store, _ = ready
    value = register(ready)
    board._deliver(store, value, False, False, None, at())
    Path(value["frozen_path"]).write_text("{}", encoding="utf-8")
    runtime = FixtureTransport()
    coordinator = Coordinator(store=store, transport_runtime=runtime)
    link = value["links"][0]
    with pytest.raises(ValueError, match="BOARD_FROZEN_SOURCE_CHANGED"):
        coordinator.publish_plan(link["link_id"], link["plan"])
    assert runtime.publish_calls == []


def test_late_unsent_day_does_not_starve_the_next_day_and_never_backdates(ready, tmp_path, monkeypatch):
    store, root = ready
    register(ready, source("2026-11-13"))
    path = write(tmp_path, source())
    clock(monkeypatch, at())
    runtime = FixtureTransport()
    result = board.run_due(store, board_path=path, output_root=root, now=at(),
                           snapshot=no_snapshot, deliver=delivery(runtime, at()))
    assert any(o["outcome"].get("state") == "BOARD_PUBLIC_DAY_EXPIRED" for o in result["outcomes"])
    assert any(o["readback"]["confirmed"] for o in result["outcomes"] if "2026-11-16" in o["link_id"])
    assert not board.acceptance(store)["passed"]


def test_minute_entry_consumes_board_even_when_plan_export_is_stale(ready, tmp_path, monkeypatch, capsys):
    from scripts import plan_status_posts as entry
    from live_contentops import plan_status_posts_v1 as posts
    from live_contentops import heavy_news_quotes_v1, x_reply_bot_v1, x_reply_tabs_v1
    from live_contentops import event_timestamp_v1, event_pack_v1, audience_collection_v1, model_invocation_usage_v1
    from live_contentops import call_followups_v1, plan_reader_editorial_v1, substack_daily_note_v1
    store, root = ready
    path = write(tmp_path, source())
    clock(monkeypatch, at())
    actual = board.run_due
    calls = []
    def consume(s, **kwargs):
        calls.append(kwargs)
        return actual(s, board_path=path, output_root=root, now=at(), publish=False, snapshot=no_snapshot)
    monkeypatch.setattr(board, "run_due", consume)
    monkeypatch.setattr(posts, "queue_posts", lambda *a, **k: {"status": "EXPORT_STALE"})
    monkeypatch.setattr(posts, "read_export", lambda *a, **k: (_ for _ in ()).throw(ValueError("EXPORT_STALE")))
    for module, names in (
        (heavy_news_quotes_v1, ["refresh_due"]), (x_reply_bot_v1, ["refresh_due", "observe_due"]),
        (x_reply_tabs_v1, ["refresh_due"]), (event_timestamp_v1, ["maintain_timestamps"]),
        (event_pack_v1, ["run_due_packs"]), (audience_collection_v1, ["run_collection"]),
        (model_invocation_usage_v1, ["import_native_invocations"]), (call_followups_v1, ["minute_due"]),
        (plan_reader_editorial_v1, ["run_due"]), (substack_daily_note_v1, ["run_due"]),
    ):
        for name in names:
            monkeypatch.setattr(module, name, lambda *a, **k: {"status": "NO_DUE_WORK"})
    assert entry.main(["--publish", "--store", str(store.db_path)]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["daily_trend_board"]["state"] == "BOARD_PREPARED"
    assert calls[0]["automatic_neo"] is True
    assert len(store.list_outbox_messages(destination=board.DESTINATION)) == 1
