"""CC-314 (Jim's decision 82): a plan-status post carries TradingView's own chart snapshot of its
market; if the snapshot fails, CC-290's fact card with the plan's numbers. Controlled: the fixture
is a real TradingView Download image (US500, 4h, 5 Nov 13:21 UTC); no browser, no network."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image

from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.plan_status_posts_v1 import (
    POST_DESTINATIONS, _x_length, plan_facts, prepare_post, publish_ready, queue_posts,
)
from test_plan_status_posts_cc306 import NOW, event, main_root, plan, write_export  # noqa: F401
from test_plan_status_publication_cc306 import fake_host
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode

FIXTURE = Path(__file__).parent / "fixtures" / "cc314" / "SPX500USD_2026-11-05_13-21-11.png"


@pytest.fixture
def outcomes(tmp_path, monkeypatch):
    path = tmp_path / "outcomes.jsonl"
    monkeypatch.setattr(tv, "OUTCOMES", path)
    return path


@pytest.fixture
def queued(tmp_path, main_root, outcomes):
    plans = [plan("plan_spx", "US500", "BULLISH", 7650, 7672.5, cancel=7740, invalid=7620,
                  deadline="2026-11-06T12:45:00Z")]
    plans[0]["target_level"] = 7790  # a target in the export never reaches the row, the card or the chart
    export = write_export(tmp_path / "plan-status-v1", plans, [event("plan_spx", "WAITING", "2026-11-05T12:20:00Z")])
    store, _, coordinator = _coordinator(tmp_path, runtime=FixtureTransport())
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    result = queue_posts(store, export, now=NOW, main_root=main_root, python=sys.executable)
    return store, coordinator, result["queued"][0]["key"], tmp_path / "posts"


def tradingview_worker(calls):
    """Stands in for the browser: TradingView's download as it arrives (its own file name)."""
    def worker(args):
        calls.append(args)
        target = Path(args["out_dir"]) / FIXTURE.name
        shutil.copyfile(FIXTURE, target)
        return {"path": str(target), "suggested_filename": FIXTURE.name, "legend": "4h",
                "page_title": "SPX500USD 7,705.6", "captured_at_utc": "2026-11-05T13:21:11+00:00", "seconds": 20.3}
    return worker


def snapshot_with(calls):
    worker = tradingview_worker(calls)
    return lambda market, interval, out_dir: tv.capture(market, interval, out_dir, worker=worker)


def test_the_package_holds_tradingviews_snapshot_of_the_right_symbol_and_timeframe(queued, outcomes):
    store, _, key, root = queued
    calls = []
    plan_ = prepare_post(store, key, root=root, host=fake_host, snapshot=snapshot_with(calls))
    context = json.loads((Path(plan_["output_dir"]) / "run_context_v1.json").read_bytes())
    asset = context["media"]["assets"][0]
    assert asset["card_kind"] == "TRADINGVIEW_SNAPSHOT" and asset["asset_id"] == plan_["status_post_card_id"]
    snap = asset["tradingview_snapshot"]
    # US500 is the site's reviewed CFD symbol; a 24.4-hour plan takes the 4-hour chart.
    assert calls[0]["url"] == "https://www.tradingview.com/chart/?symbol=OANDA:SPX500USD&interval=240"
    assert snap["tv_symbol"] == "OANDA:SPX500USD" and snap["interval_label"] == "4h"
    assert context["chart_credit"] is True
    for row in plan_["destinations"]:
        assert "Chart: TradingView" in row["payload"]
    assert json.loads(outcomes.read_text().splitlines()[0])["status"] == "CAPTURED"


def test_the_attribution_is_never_cropped_and_the_frame_is_16_by_9(queued):
    store, _, key, root = queued
    plan_ = prepare_post(store, key, root=root, host=fake_host, snapshot=snapshot_with([]))
    asset = json.loads((Path(plan_["output_dir"]) / "run_context_v1.json").read_bytes())["media"]["assets"][0]
    left, top, right, bottom = asset["tradingview_snapshot"]["framing"]["original_box"]
    with Image.open(asset["path"]) as framed, Image.open(FIXTURE) as original:
        assert abs(framed.width / framed.height - 16 / 9) < 0.005
        # Every pixel of TradingView's image, its "Created with TradingView.com" header and its
        # logo included, is in the post image unchanged.
        assert list(framed.convert("RGB").crop((left, top, right, bottom)).getdata()) == \
            list(original.convert("RGB").getdata())
    portrait = tv.frame(FIXTURE, Path(plan_["output_dir"]) / "ig.png", "4:5")
    assert abs(portrait["width"] / portrait["height"] - 4 / 5) < 0.005


def test_no_level_or_target_is_drawn_and_no_target_is_kept(queued):
    store, _, key, root = queued
    plan_ = prepare_post(store, key, root=root, host=fake_host, snapshot=snapshot_with([]))
    asset = json.loads((Path(plan_["output_dir"]) / "run_context_v1.json").read_bytes())["media"]["assets"][0]
    assert asset["tradingview_snapshot"]["target_drawn"] is False
    assert asset["tradingview_snapshot"]["levels_drawn"] == []
    row = json.loads(store.get_outbox_message(key)["payload"])
    assert set(row["levels"]) == {"direction", "zone_low", "zone_high", "invalidation_level", "valid_until_utc"}
    assert "7,790" not in json.dumps(plan_) and "7790" not in json.dumps(row)


def test_a_failed_snapshot_still_posts_with_the_plans_numbers(queued, outcomes):
    store, _, key, root = queued

    def broken(market, interval, out_dir):
        raise tv.SnapshotError("TRADINGVIEW_SNAPSHOT_TIMEOUT")
    plan_ = prepare_post(store, key, root=root, host=fake_host, snapshot=broken)
    asset = json.loads((Path(plan_["output_dir"]) / "run_context_v1.json").read_bytes())["media"]["assets"][0]
    assert asset["card_kind"] == "PLAN_FACT_CARD" and Path(asset["path"]).is_file()
    facts = dict(asset["data_card_packet"]["facts"])
    assert facts["Entry zone"] == "7,650–7,672.5" and facts["Invalidation"] == "Below 7,620"
    assert facts["Status"] == "New plan" and facts["As of"] == "Thu 5 Nov, 12:20 UTC"
    assert "7,790" not in json.dumps(asset) and "7,740" not in json.dumps(asset)
    for row in plan_["destinations"]:
        assert "Chart: TradingView" not in row["payload"]
    assert tv.failure_count(outcomes) == 1


def test_one_snapshot_per_post_a_resumed_post_reuses_its_image(queued):
    store, _, key, root = queued
    calls = []
    first = prepare_post(store, key, root=root, host=fake_host, snapshot=snapshot_with(calls))
    again = prepare_post(store, key, root=root, host=fake_host, destinations=("x",), snapshot=snapshot_with(calls))
    assert len(calls) == 1 and first["status_post_card_id"] == again["status_post_card_id"]
    x = again["destinations"][0]["payload"]
    assert "Chart: TradingView" in x


def test_x_keeps_the_credit_with_the_link_inside_its_limit(queued):
    from live_contentops.plan_status_posts_v1 import destination_payloads
    store, _, key, _ = queued
    row = json.loads(store.get_outbox_message(key)["payload"])
    x = destination_payloads(row, card_id="c", chart_credit=True)["x"]
    assert all(_x_length(p["text"]) <= 280 for p in x["posts"])
    assert "Chart: TradingView" in x["posts"][0]["text"] and x["posts"][0]["media_asset_ids"] == ["c"]


def test_a_busy_tick_falls_back_once_its_snapshot_budget_is_spent(queued, outcomes):
    store, _, key, root = queued
    calls = []
    plan_ = prepare_post(store, key, root=root, host=fake_host, snapshot=snapshot_with(calls),
                         snapshot_allowed=lambda: False)
    assert calls == []
    asset = json.loads((Path(plan_["output_dir"]) / "run_context_v1.json").read_bytes())["media"]["assets"][0]
    assert asset["card_kind"] == "PLAN_FACT_CARD"
    assert json.loads(outcomes.read_text().splitlines()[0])["status"] == "SKIPPED_RUN_TIME_BUDGET"


def test_capture_refuses_another_symbol_or_an_unconfirmed_timeframe(tmp_path):
    def worker_for(name, legend):
        def worker(args):
            target = Path(args["out_dir"]) / name
            shutil.copyfile(FIXTURE, target)
            return {"path": str(target), "suggested_filename": name, "legend": legend}
        return worker
    with pytest.raises(tv.SnapshotError, match="NOT_THIS_SYMBOL"):
        tv.capture("XAUUSD", "240", tmp_path / "a", worker=worker_for(FIXTURE.name, "4h"))
    with pytest.raises(tv.SnapshotError, match="INTERVAL_NOT_CONFIRMED"):
        tv.capture("US500", "60", tmp_path / "b", worker=worker_for(FIXTURE.name, "4h"))


@pytest.mark.parametrize("hours,interval", [(6, "60"), (24, "60"), (25, "240"), (24 * 7, "240"), (24 * 8, "D")])
def test_the_timeframe_follows_the_plans_validity(hours, interval):
    from datetime import datetime, timedelta, timezone
    start = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)
    assert tv.interval_for((start + timedelta(hours=hours)).isoformat(), start.isoformat()) == interval


def test_the_symbols_are_the_sites_reviewed_map():
    if not tv.REVIEWED_MAP.is_file():
        pytest.skip("the site's reviewed map is not on this machine")
    reviewed = tv.reviewed_symbols()
    assert {m: reviewed.get(m) for m in tv.SYMBOLS} == tv.SYMBOLS


def test_the_plan_facts_never_carry_a_target():
    row = {"state": "TRIGGERED", "at_utc": "2026-11-05T12:20:00Z",
           "levels": {"direction": "bearish", "zone_low": 61.2, "zone_high": 61.8, "invalidation_level": 62.4,
                      "target": 59.0}}
    assert plan_facts(row) == [("Entry zone", "61.2–61.8"), ("Invalidation", "Above 62.4"),
                               ("Status", "Plan now active"), ("As of", "Thu 5 Nov, 12:20 UTC")]


def test_a_daily_chart_is_confirmed_by_tradingviews_d_label(tmp_path):
    def worker(args):
        target = Path(args["out_dir"]) / "USDJPY_2026-11-05_13-28-16.png"
        shutil.copyfile(FIXTURE, target)
        return {"path": str(target), "suggested_filename": target.name, "legend": "D"}
    snap = tv.capture("USDJPY", "D", tmp_path / "d", worker=worker)
    assert snap["tv_symbol"] == "FX:USDJPY" and snap["interval"] == "D"
