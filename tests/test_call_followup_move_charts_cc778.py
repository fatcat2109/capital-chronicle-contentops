"""CC-778: the prepared CC-603 follow-ups capture their own move chart, then post at most two a day.

No live services: the snapshot worker is a fake that returns a retained TradingView download, as the other
snapshot tests do, and the coordinator is the existing test coordinator.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil

import pytest

from live_contentops import call_followups_v1 as f
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import tradingview_plan_overlay_v1 as overlay
from live_contentops import tradingview_snapshot_v1 as tv
from test_call_followups_cc603 import ready  # noqa: F401  (the existing fixture: corrections read back, record)
from test_plan_status_publication_cc306 import fake_host

NOW = datetime(2026, 11, 14, 2, tzinfo=timezone.utc)
START = NOW - timedelta(hours=2)
FIXTURES = Path(__file__).parents[1] / "docs/publisher/CC-603"
TERMS = {"market": "Gold", "condition": "price trades into 3,950–3,960", "direction": "bearish",
         "horizon": "14 Nov 03:00 ET", "invalidation": "price moves above 4,000"}
OUTSIDE_PAUSE = (datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 2, tzinfo=timezone.utc))

# The nine CC603_PREPARED follow-ups in the live store (read read-only on 24 Nov 2026):
# key suffix, market, call published, move resolved, the follow-up's destinations.
NINE = [
    ("2659ec1c", "EURUSD", "2026-11-11T03:27:10.699521+00:00", "2026-11-11T13:30:00+00:00",
     ["facebook_page", "instagram_business", "substack_notes", "telegram"]),
    ("f49e1e04", "XAUUSD", "2026-11-11T06:34:13.611454+00:00", "2026-11-11T16:45:00+00:00",
     ["facebook_page", "instagram_business", "telegram", "threads"]),
    ("6cb9230a", "USDJPY", "2026-11-11T06:34:37.544714+00:00", "2026-11-11T13:45:00+00:00",
     ["facebook_page", "instagram_business", "telegram", "threads"]),
    ("35a55222", "USOIL", "2026-11-09T09:13:56.142951+00:00", "2026-11-09T11:30:00+00:00",
     ["discord", "telegram", "threads"]),
    ("af988bdf", "EURUSD", "2026-11-09T09:18:15.384073+00:00", "2026-11-09T20:30:00+00:00",
     ["discord", "telegram", "threads"]),
    ("9b071613", "US500", "2026-11-10T03:17:06.207616+00:00", "2026-11-10T06:30:00+00:00",
     ["discord", "telegram", "threads"]),
    ("bb2dc2d3", "USOIL", "2026-11-10T03:17:37.024348+00:00", "2026-11-10T06:45:00+00:00",
     ["discord", "telegram", "threads"]),
    ("f260f6f4", "EURUSD", "2026-11-11T06:35:01.183861+00:00", "2026-11-11T13:15:00+00:00",
     ["facebook_page", "instagram_business", "telegram", "threads"]),
    ("813c70c1", "XAUUSD", "2026-11-11T16:26:16.601628+00:00", "2026-11-11T19:30:00+00:00", ["telegram"]),
]


def _utc(value):
    return datetime.fromisoformat(value)


def nine_row(suffix, symbol, published, resolved, destinations):
    return {"key": "cc603-followup-" + suffix, "kind": "call_followup", "symbol": symbol,
            "cc603_destinations": destinations,
            "candidate": {"published_at_utc": published, "zone_low": 1, "zone_high": 2, "direction": "bearish",
                          "invalidation": {"field": "high", "level": 3, "side": "above"}},
            "price_check": {"resolved_at_utc": resolved}}


@pytest.mark.parametrize("item", NINE, ids=[n[0] for n in NINE])
def test_each_prepared_followup_gets_a_capture_request_for_its_market_and_window(item):
    row = nine_row(*item)
    request = f.move_chart_request(row)
    published, resolved = _utc(item[2]), _utc(item[3])
    window = request["visible_range"]
    assert request["tv_symbol"] == tv.SYMBOLS[item[1]] and request["interval"] == "15"
    # held_chart's own check: visible_from <= published < resolved <= visible_to; the window ends on the move.
    assert _utc(window["show_from_utc"]) <= published < resolved <= _utc(request["visible_to_utc"])
    assert _utc(request["visible_to_utc"]) == resolved
    assert _utc(window["last_bar_open_utc"]) == resolved - timedelta(minutes=15)
    assert _utc(window["from_utc"]) <= _utc(window["show_from_utc"]) - timedelta(hours=1)
    assert _utc(request["visible_to_utc"]) - _utc(window["from_utc"]) >= timedelta(hours=12)
    assert set(request["levels"]) == {"zone_low", "zone_high", "invalidation_level", "direction"}
    assert ("4:5" in request["ratios"]) == ("instagram_business" in item[4])
    # SP:SPX has no bars at 01:30 ET: that call waits with its cause instead of showing an empty chart.
    assert (request.get("refusal") == "CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:SP:SPX") == (item[1] == "US500")


def gold_candidate():
    quote = posts.conditional_call_text(TERMS)
    return {"call_id": "cc778-stored-call", "plan_id": "cc778-plan", "symbol": "XAUUSD", "source_kind": "AS_WRITTEN",
            "short_id": "a0380280", "terms": TERMS, "quote": quote, "original_text": quote,
            "original_url": "https://t.me/CapitalChronicle/169", "published_at_utc": START.isoformat(),
            "valid_until_utc": (START + timedelta(hours=6)).isoformat(), "zone_low": 3950, "zone_high": 3960,
            "reference_price": 3970, "resolution_level": 3900, "direction": "bearish",
            "invalidation": {"field": "high", "level": 4000, "side": "above"},
            "destinations": ["telegram", "discord", "x", "substack_notes"]}


def gold_bars():
    bars = []
    for i in range(1, 7):
        at = int((START + timedelta(minutes=15 * i)).timestamp())
        if i < 6:
            bars.append({"open_epoch": at, "open": 3965 - i, "high": 3966 - i, "low": 3955 - i, "close": 3958 - i,
                         "source_sha256": "held-source"})
        else:
            bars.append({"open_epoch": at, "open": 3952, "high": 3953, "low": 3895, "close": 3898,
                         "source_sha256": "held-source"})
    return bars


class FakeWorker:
    """Returns the retained gold download as TradingView's own file, with the window it was asked for."""

    def __init__(self, *, close="3,898.00", observed=None, error=None):
        self.calls, self.close, self.observed, self.error = [], close, observed, error

    def __call__(self, args):
        self.calls.append(args)
        if self.error:
            raise tv.SnapshotError(self.error)
        out = Path(args["out_dir"])
        name = "XAUUSD_2026-11-30_10-00-00.png"
        shutil.copyfile(FIXTURES / "media/gold-original.png", out / name)
        window = args["visible_range"]
        return {"path": str(out / name), "suggested_filename": name, "legend": "Gold Spot 15m ICE",
                "page_title": "XAUUSD 4,101.20", "capture_ratio": "16:9", "geometry_probe": [{"fixture": True}],
                "axis_path": str(out / name), "captured_at_utc": NOW.isoformat(), "seconds": 21.0,
                "visible_range_observed": self.observed or {"from": window["from"], "to": window["to"]},
                "visible_last_close": self.close, "live_values_hidden": True}


@pytest.fixture
def fixture_scale(monkeypatch, tmp_path):
    snap = json.loads((FIXTURES / "original-gold-chart.json").read_bytes())
    monkeypatch.setattr(overlay, "geometry", lambda result: snap["chart_geometry"])
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")


def queued(store, record):
    c = gold_candidate()
    checked = f.check_path(c, gold_bars())
    assert checked["eligible"] and checked["resolved_at_utc"] == (START + timedelta(minutes=105)).isoformat()
    return f.queue_followup(store, c, checked, record, now=NOW)["key"]


def test_fake_capture_binds_the_window_and_levels_then_releases_the_followup(ready, tmp_path, fixture_scale,
                                                                            monkeypatch):
    store, transport, coordinator, record = ready
    fixture_publish = transport.publish

    def publish_with_public_url(**kwargs):  # as the CC-603 consumer test: the fixture's Discord receipt has no URL
        receipt = fixture_publish(**kwargs)
        if kwargs["destination"] == "discord":
            receipt["public_url"] = "https://discord.com/channels/1/2/3"
        return receipt
    monkeypatch.setattr(transport, "publish", publish_with_public_url)
    key = queued(store, record)
    root, worker = tmp_path / "followups", FakeWorker()
    options = dict(now=NOW, root=root, coordinator_for=lambda *a: coordinator, host=fake_host,
                   bars_reader=lambda *a: gold_bars(), pause_window=OUTSIDE_PAUSE, move_chart_worker=worker)
    first = f.run_due(store, {"status": {"plans": []}}, **options)
    capture = next(p for p in first["posts"] if p.get("key") == key)
    assert capture["status"] == "MEDIA_CAPTURED" and not transport.publish_calls
    asked = worker.calls[0]
    assert asked["url"] == tv.chart_url("FX_IDC:XAUUSD", "15")
    assert asked["visible_range"]["last_bar_open"] == int((START + timedelta(minutes=90)).timestamp())
    binding = json.loads((root / key / "reviewed_chart.json").read_bytes())
    assert _utc(binding["visible_from_utc"]) <= START < START + timedelta(minutes=105) == _utc(binding["visible_to_utc"])
    asset = binding["asset"]
    assert asset["tradingview_snapshot"]["price_scale_check"]["comparison_basis"] == "VISIBLE_WINDOW_CLOSE"
    assert asset["tradingview_snapshot"]["price_scale_check"]["difference_pct"] == 0
    labels = [m["label"] for m in asset["plan_overlay"]["markers"]]
    assert sorted(labels) == ["Entry high", "Entry low", "Invalidation"] and not overlay.target_drawn(asset)
    assert binding["review"]["levels_drawn"] == labels and "from before our original view" in asset["caption"]
    row = posts._row_payload(store, key)
    assert f.held_chart(store, row, root=root)["asset_id"] == asset["asset_id"]
    # The bound chart releases the follow-up in the next minute run, with its dated CC-603 copy unchanged.
    f.run_due(store, {"status": {"plans": []}}, **options)
    assert sorted(transport.publish_calls) == sorted(row["cc603_destinations"]) and len(worker.calls) == 1
    intents = [json.loads(r["payload"]) for r in store.list_outbox_messages(work_item_id=key)
               if r["destination"] in row["cc603_destinations"]]
    assert all(r["native_payload"]["media_asset_ids"] == [asset["asset_id"]] for r in intents)
    assert all("13 Nov 2026 19:00 ET" in r["native_payload"]["full_text"] for r in intents)
    f.run_due(store, {"status": {"plans": []}}, **options)
    assert store.get_outbox_message(key)["status"] == "PUBLISHED"


@pytest.mark.parametrize("worker,cause", [
    (FakeWorker(error="TRADINGVIEW_CHART_API_ABSENT"), "TRADINGVIEW_CHART_API_ABSENT"),
    (FakeWorker(observed={"from": 0, "to": 10 ** 10}), tv.HISTORICAL_RANGE_UNCONFIRMED),
    (FakeWorker(close="4,200.00"), "TRADINGVIEW_PRICE_SCALE_MISMATCH"),
])
def test_a_failed_capture_keeps_the_followup_waiting_with_its_cause(ready, tmp_path, fixture_scale, worker, cause):
    store, transport, coordinator, record = ready
    key = queued(store, record)
    root = tmp_path / "followups"
    options = dict(root=root, coordinator_for=lambda *a: coordinator, host=fake_host,
                   bars_reader=lambda *a: gold_bars(), pause_window=OUTSIDE_PAUSE, move_chart_worker=worker)
    for minute in range(3):
        result = f.run_due(store, {"status": {"plans": []}}, now=NOW + timedelta(minutes=minute), **options)
        entry = next(p for p in result["posts"] if p.get("key") == key)
        assert entry["status"] == "MEDIA_PENDING" and cause in entry["cause"]
    # Two attempts make a round; the third minute waits for the retry time. Nothing posted text only.
    assert len(worker.calls) == 2 and not transport.publish_calls
    assert not (root / key / "reviewed_chart.json").exists()
    state = json.loads((root / key / "move_chart_capture_v1.json").read_bytes())
    assert state["status"] == "FAILED" and len(state["attempt_causes"]) == 2 and cause in state["first_cause"]
    later = NOW + f.CAPTURE_RETRY_AFTER + timedelta(minutes=1)
    f.run_due(store, {"status": {"plans": []}}, now=later, **options)
    assert len(worker.calls) == 3 and store.get_outbox_message(key)["status"] == "CC603_PREPARED"


def test_an_interrupted_attempt_is_named_before_the_next(ready, tmp_path, fixture_scale):
    store, _, coordinator, record = ready
    key = queued(store, record)
    row = posts._row_payload(store, key)
    folder = tmp_path / "followups" / key
    folder.mkdir(parents=True)
    state = {"key": key, "ratio": "16:9", "request_sha256": f._hash(f.move_chart_request(row)), "attempts": 1,
             "round_attempts": 1, "attempt_causes": [], "status": "PENDING", "started_at_utc": NOW.isoformat()}
    (folder / "move_chart_capture_v1.json").write_text(json.dumps(state), encoding="utf-8")
    taken = f.capture_move_chart(row, root=tmp_path / "followups", now=NOW, worker=FakeWorker(),
                                 bars_reader=lambda *a: gold_bars())
    assert taken["status"] == "CAPTURED"
    saved = json.loads((folder / "move_chart_capture_v1.json").read_bytes())
    assert saved["attempt_causes"] == [tv.CAPTURE_INTERRUPTED, "CAPTURED"]


def test_a_closed_cash_market_waits_with_its_cause_and_spends_no_capture(tmp_path):
    row = nine_row(*NINE[5])
    worker = FakeWorker()
    taken = f.capture_move_chart(row, root=tmp_path, now=NOW, worker=worker)
    assert taken["status"] == "MEDIA_PENDING" and not taken["attempted"] and not worker.calls
    assert taken["cause"] == "CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:SP:SPX"


def prepared(store, suffix, published):
    key = "cc603-followup-" + suffix
    row = {"schema_version": posts.SCHEMA, "key": key, "kind": "call_followup", "symbol": "XAUUSD",
           "title": "Gold: our earlier view and what followed", "candidate": {"published_at_utc": published.isoformat()}}
    store.create_work_item(story_id=key, work_item_id=key, title=row["title"], target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=key, work_item_id=key, destination=posts.DESTINATION,
                                  payload=json.dumps(row), status="CC603_PREPARED")
    return key


def start(store, key):
    identity = key + "-telegram"
    store.register_outbox_message(message_id=identity, work_item_id=key, destination="telegram", payload="{}")
    store.register_platform_dispatch(dispatch_id="dispatch_" + identity, message_id=identity, platform="telegram",
                                     status="DISPATCH_CONFIRMED", public_object_id="1",
                                     public_object_url="https://t.me/CapitalChronicle/1")


def started_at(store, key):
    return posts._utc(store.get_dispatches_for_work_item(key)[0]["dispatched_at"])


def test_pacing_holds_two_a_day_oldest_call_first(ready):
    store = ready[0]
    called = datetime(2026, 11, 9, tzinfo=timezone.utc)
    newest = prepared(store, "c", called + timedelta(days=2))
    oldest = prepared(store, "a", called)
    middle = prepared(store, "b", called + timedelta(days=1))
    keys = [newest, oldest, middle]
    order, held = f.backfill_order(store, keys, now=datetime.now(timezone.utc), pause_window=OUTSIDE_PAUSE)
    assert order == [oldest, middle, newest] and not held
    start(store, oldest)
    now = started_at(store, oldest) + timedelta(minutes=5)
    order, held = f.backfill_order(store, keys, now=now, pause_window=OUTSIDE_PAUSE)
    assert order == [oldest, middle, newest] and not held  # the one in progress finishes first
    start(store, middle)
    order, held = f.backfill_order(store, keys, now=now, pause_window=OUTSIDE_PAUSE)
    assert order == [oldest, middle]
    assert held == [{"key": newest, "status": "BACKFILL_PACED", "cause": "CC778_BACKFILL_TWO_A_DAY",
                     "next_due_utc": (started_at(store, oldest) + f.BACKFILL_DAY).isoformat()}]
    # A day after the first start, one more may begin.
    order, held = f.backfill_order(store, keys, now=started_at(store, oldest) + f.BACKFILL_DAY + timedelta(seconds=1),
                                   pause_window=OUTSIDE_PAUSE)
    assert order == [oldest, middle, newest] and not held


def test_pause_and_the_first_hour_after_restore_hold_every_backfill_post():
    begin = datetime(2026, 11, 23, 4, 50, tzinfo=timezone.utc)
    restored = datetime(2026, 11, 30, 2, tzinfo=timezone.utc)
    window = (begin, restored)
    open_window = (begin, datetime.max.replace(tzinfo=timezone.utc))
    assert f.backfill_hold(begin - timedelta(minutes=1), window) is None
    assert f.backfill_hold(begin, window) == "CC778_BACKFILL_PAUSED"
    assert f.backfill_hold(datetime(2026, 12, 9, tzinfo=timezone.utc), open_window) == "CC778_BACKFILL_PAUSED"
    assert f.backfill_hold(restored, window) == "CC778_BACKFILL_FIRST_HOUR_AFTER_RESTORE"
    assert f.backfill_hold(restored + timedelta(minutes=59), window) == "CC778_BACKFILL_FIRST_HOUR_AFTER_RESTORE"
    assert f.backfill_hold(restored + timedelta(hours=1), window) is None


def test_run_due_posts_and_captures_nothing_inside_the_pause(ready, tmp_path, fixture_scale):
    store, transport, coordinator, record = ready
    key = queued(store, record)
    worker = FakeWorker()
    paused = (NOW - timedelta(hours=1), NOW + timedelta(days=3))
    for now in (NOW, paused[1] + timedelta(minutes=30)):
        result = f.run_due(store, {"status": {"plans": []}}, now=now, root=tmp_path / "followups",
                           coordinator_for=lambda *a: coordinator, host=fake_host, bars_reader=lambda *a: gold_bars(),
                           pause_window=paused, move_chart_worker=worker)
        assert [p["status"] for p in result["posts"] if p.get("key") == key] == ["BACKFILL_HELD"]
    assert not worker.calls and not transport.publish_calls


def test_two_started_followups_pace_the_next_through_the_minute_run(ready, tmp_path, fixture_scale):
    store, transport, coordinator, record = ready
    key = queued(store, record)
    for suffix, day in (("x1", 9), ("x2", 10)):
        done = prepared(store, suffix, datetime(2026, 11, day, tzinfo=timezone.utc))
        start(store, done)
        store.set_outbox_status(done, "PUBLISHED")
    worker = FakeWorker()
    result = f.run_due(store, {"status": {"plans": []}}, now=NOW, root=tmp_path / "followups",
                       coordinator_for=lambda *a: coordinator, host=fake_host, bars_reader=lambda *a: gold_bars(),
                       pause_window=OUTSIDE_PAUSE, move_chart_worker=worker)
    assert [p["status"] for p in result["posts"] if p.get("key") == key] == ["BACKFILL_PACED"]
    assert not worker.calls and not transport.publish_calls


def test_an_instagram_followup_tries_its_native_portrait_before_posting(ready, tmp_path, fixture_scale):
    store, transport, coordinator, record = ready
    c = {**gold_candidate(), "destinations": ["telegram", "instagram_business"]}
    key = f.queue_followup(store, c, f.check_path(c, gold_bars()), record, now=NOW)["key"]
    root, worker = tmp_path / "followups", FakeWorker()
    options = dict(root=root, coordinator_for=lambda *a: coordinator, host=fake_host,
                   bars_reader=lambda *a: gold_bars(), pause_window=OUTSIDE_PAUSE, move_chart_worker=worker)
    statuses = []
    for minute in range(3):
        result = f.run_due(store, {"status": {"plans": []}}, now=NOW + timedelta(minutes=minute), **options)
        statuses += [p["status"] for p in result["posts"] if p.get("key") == key]
    # The 16:9 chart binds; the retained download is not a native 4:5 chart, so both portrait attempts fail.
    assert statuses == ["MEDIA_CAPTURED", "PORTRAIT_MEDIA_PENDING", "PORTRAIT_MEDIA_PENDING"]
    portrait = json.loads((root / key / "move_chart_capture_4x5_v1.json").read_bytes())
    assert portrait["status"] == "FAILED" and portrait["first_cause"] == "INSTAGRAM_NATIVE_4X5_CHART_REQUIRED"
    assert not transport.publish_calls and not (root / key / "reviewed_portrait.json").exists()
    # A failed portrait never holds the other destinations: the bound 16:9 chart posts next.
    f.run_due(store, {"status": {"plans": []}}, now=NOW + timedelta(minutes=3), **options)
    assert "telegram" in transport.publish_calls and len(worker.calls) == 3
