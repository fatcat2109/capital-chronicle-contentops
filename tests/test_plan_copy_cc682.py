"""Replay the public 19 November gold plan through the minute publisher."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import sys
from types import SimpleNamespace

from PIL import Image
import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import publication_image_contract_v1 as images
from live_contentops import secret_store_v1
from live_contentops import tradingview_plan_overlay_v1 as overlay
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_call_cards_cc399 import rows, write
from test_plan_status_posts_cc306 import event, main_root  # noqa: F401


GOLD_PLAN_ID = "plan_a5749b44e7c886ca7220670f"
GOLD_RESULT_KEY = "plan-result-post-580a244ff31eb610ac567a5f53621814"
GOLD_CANCEL = "Cancel if spot price trades at or above 3,792 before entry"
# Decision 157 (Jim, 23 Nov 2026: "Keep targets off"): the result names no target price.
GOLD_ENDING = "Gold: hit its target. Result: +1.6R."
PAGE_LINK = "https://capitalchronicle.substack.com/p/gold-test"


@pytest.fixture
def gold_export():
    # The plan-status.public.json row behind the exact result key. Keep only
    # the public facts needed by the composer. The score exports no fill price.
    return {
        "asset_id": "XAUUSD", "plan_id": GOLD_PLAN_ID, "direction": "BEARISH", "status": "WAITING",
        "registration_hash": "589d566e1f5323ecb3898192ab6c5c646fee80f8d1872b3c58754bed28702982",
        "zone": {"minimum": 3722.0, "maximum": 3752.0},
        "invalidation_conditions": [{"field": "high", "operator": "GTE", "threshold": 3792.0}],
        "registered_at_utc": "2026-11-19T09:42:33.233165Z",
        "entry_deadline_utc": "2026-11-19T13:15:00Z", "expires_at_utc": "2026-11-19T13:15:00Z",
        "target_level": 3645.0,
        "public_instrument": {"kind": "FUT", "name": "Micro gold", "symbol": "MGC",
                              "contract_month": "2026-12"},
        "scenario_analysis": {"horizon_end_utc": "2026-11-20T20:00:00Z",
                              "driver": "Fed path via real yields."},
    }


@pytest.fixture
def replay_gold(gold_export, tmp_path, main_root, monkeypatch):
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    monkeypatch.setattr(pages, "confirmed_publication", lambda *args: {
        "plan_id": GOLD_PLAN_ID, "registration_hash": gold_export["registration_hash"],
        "canonical_url": PAGE_LINK, "summary": {"macro": "Fed path via real yields."},
    })
    store = ContentOpsDurableStore(tmp_path / "replay.sqlite3")
    events = []

    def queue(plan, state, at):
        events.append(event(GOLD_PLAN_ID, state, at))
        now = posts._utc(at) + timedelta(seconds=1)
        folder = write(tmp_path / "export", [plan], events, generated_at_utc=now.isoformat())
        run = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
        assert run["status"] == "OK", run
        key, = [row["key"] for row in run["queued"]]
        row = next(row for row in rows(store) if row["key"] == key)
        alerts.validate(row, store=store)
        return row

    setup = queue(gold_export, "WAITING", gold_export["registered_at_utc"])
    store.set_outbox_status(setup["key"], "PUBLISHED")
    original_bytes = store.get_outbox_message(setup["key"])["payload"]
    filled_at = "2026-11-19T09:44:07.552000Z"
    fill = queue({**gold_export, "status": "FILLED"}, "FILLED", filled_at)
    resolved_at = "2026-11-19T21:24:24.796000Z"
    outcome_id = "outcome_7af1f8a0dfef1cef3779361d8f333c0b"
    score = {"asset_id": "XAUUSD", "plan_id": GOLD_PLAN_ID, "outcome_id": outcome_id,
             "result": "HIT", "score_basis": "BROKER_TAKE_PROFIT",
             "triggered_at_utc": filled_at, "resolved_at_utc": resolved_at}
    outcome = {"state": "SCORED", "result": "HIT", "outcome_id": outcome_id,
               "result_r": 1.5569006129583767, "score": score}
    result = queue({**gold_export, "status": "CLOSED", "outcome": outcome}, "CLOSED", resolved_at)
    assert result["key"] == GOLD_RESULT_KEY
    assert store.get_outbox_message(setup["key"])["payload"] == original_bytes
    return setup, fill, result


def test_gold_plan_fill_and_result_render_for_each_destination(replay_gold):
    for row in replay_gold:
        assert row["level_contract"] == reader.CURRENT_LEVEL_CONTRACT
        copies = cards.destination_payloads(row, card_id="gold-chart", chart_credit=True, complete_levels=True)
        assert set(copies) == set(cards.destinations_for(row))
        for destination, copy in copies.items():
            assert "cancelled" not in copy["full_text"].lower(), destination
            assert GOLD_CANCEL in copy["full_text"], destination
            if row["kind"] in {"setup", "update"}:
                assert "Filled positions close by" in copy["full_text"], destination
            if row["kind"] == "result":
                assert copy["text"].startswith(GOLD_ENDING), destination
                assert "Macro: Fed path via real yields." in copy["full_text"]
                assert "Target level:" not in copy["full_text"]
                assert "3,645" not in copy["full_text"]


def test_phase_wording_preserves_the_close_rule_and_futures_stop(gold_export):
    raw = {**gold_export,
           "invalidation_conditions": [{"field": "close", "operator": "LT", "threshold": 3700}],
           "public_instrument": {**gold_export["public_instrument"], "zone_low": 3723.1, "zone_high": 3753.1,
                                 "invalidation_level": 3832.9, "tick_size": 0.1}}
    terms = reader.thread_terms(raw, level_contract=reader.CURRENT_LEVEL_CONTRACT)
    assert terms["invalidation"] == (
        "Cancel if spot price closes below 3,700 before entry. Wrong above 3,832.9 after entry on MGC"
    )
    legacy = reader.thread_terms(raw, level_contract=reader.LEVEL_CONTRACT)
    assert legacy["invalidation"] == "Spot plan cancelled on close below 3,700 before entry; MGC plan wrong above 3,832.9 after entry"


def test_new_plan_page_uses_the_condition_and_stored_pages_validate_with_their_original_copy(gold_export, tmp_path):
    run = {"source_plan": gold_export, "documents": {"desktop-manual-result.json": {}},
           "freeze": {"frozen_at_utc": "2026-11-19T09:40:54.826235Z", "immutable_hash": "controlled"}}
    selection = {"macro": [0]}

    def select_sources(*args, **kwargs):
        return json.dumps(selection).encode(), {"status": "RETURNED"}

    draft = editorial.draft_plan_page(gold_export, run, output_dir=tmp_path, call=select_sources)
    payload, _, _ = pages._assemble(gold_export, draft, run)
    assert draft["level_contract"] == reader.CURRENT_LEVEL_CONTRACT
    assert GOLD_CANCEL in payload["body_markdown"] and "cancelled" not in payload["body_markdown"].lower()
    assert payload["title"] == "Gold: bearish at 3,722–3,752"

    stored = editorial._page_from_selection(gold_export, run, editorial._plan_page_sources(gold_export, run),
                                            selection, level_contract=reader.LEVEL_CONTRACT)
    assert "Spot plan cancelled on high" in stored["introduction"]
    pages.validate_manuscript(gold_export, stored, run)


def test_actual_cancellation_can_say_cancelled(replay_gold):
    _, fill, _ = replay_gold
    cancelled = alerts.compose({**fill, "state": "CANCELLED"})
    assert cancelled["lead"] == "Gold: the plan was cancelled."
    assert GOLD_CANCEL in cancelled["text"]


def test_time_exit_uses_the_public_r_without_substituting_the_plan_target(replay_gold):
    _, _, result = replay_gold
    row = {**result, "score_basis": "BROKER_TIME_EXIT", "direction_correct": True}
    assert alerts.result_headline(row) == "Gold: closed at its time exit, on our side of the entry. Result: +1.6R."


@pytest.fixture
def gold_chart(tmp_path, monkeypatch):
    """Controlled canvas and price-axis registration for the saved gold levels."""
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "snapshot-outcomes.jsonl")
    path = tmp_path / "source-gold.png"
    with Image.new("RGB", (800, 450), "white") as image:
        image.putpixel((20, 20), (0, 0, 0))
        image.save(path)
    digest = sha256(path.read_bytes()).hexdigest()

    def snapshot(market, interval, folder):
        symbol = tv.SYMBOLS[market]
        return {"path": str(path), "sha256": digest, "capture_ratio": "16:9",
                "tv_symbol": symbol, "interval": interval, "interval_label": tv.INTERVAL_LABELS[interval],
                "chart_url": tv.chart_url(symbol, interval),
                "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                "chart_geometry": {"policy": overlay.POLICY, "source_sha256": digest,
                                   "mode": "linear", "slope": -2, "intercept": 7800,
                                   "pane_box": [12, 32, 734, 395]}}
    return snapshot


def test_publisher_draws_gold_plan_and_fill_levels_then_the_result(replay_gold, gold_chart, tmp_path):
    for row in replay_gold:
        asset, credited = posts._post_image(row, tmp_path / row["key"], snapshot=gold_chart, required_chart=True)
        assert credited
        overlay.validate(asset, row)
        tv.validate_snapshot_asset(asset, {"market_asset": "XAUUSD"})
        rendered = asset["plan_overlay"]
        assert rendered["target_drawn"] is False
        with Image.open(asset["path"]) as image:
            assert image.getpixel((20, 20)) == (0, 0, 0)  # protected header pixels
            if row["kind"] == "result":
                assert rendered["source"]["result_text"] == GOLD_ENDING
                assert GOLD_ENDING in asset["alt_text"]
                assert "phase_terms" not in rendered["source"]
                assert rendered["markers"] == []
                assert image.getpixel((40, 99)) != (255, 255, 255)  # result banner
            else:
                assert rendered["source"]["phase_terms"] == GOLD_CANCEL
                by_label = {m["label"]: m for m in rendered["markers"]}
                assert by_label["Entry low"]["y"] == 356 and by_label["Entry high"]["y"] == 296
                assert by_label["Cancel before entry"]["y"] == 216
                assert image.getpixel((50, 330)) != (255, 255, 255)  # shaded entry band
                assert image.getpixel((50, 216)) == (175, 40, 57)  # cancellation line


def test_a_result_keeps_its_annotation_when_the_price_axis_is_unavailable(replay_gold, gold_chart, tmp_path):
    _, _, result = replay_gold
    snap = gold_chart("XAUUSD", "60", tmp_path)
    del snap["chart_geometry"]
    plain = tv.snapshot_asset("XAUUSD", "Gold", snap, tmp_path)
    asset = overlay.apply(plain, result)
    overlay.validate(asset, result)
    assert asset["plan_overlay"]["source"]["result_text"] == GOLD_ENDING
    assert asset["sha256"] != plain["sha256"]


def test_mapped_futures_numbers_are_not_plotted_on_the_spot_axis(replay_gold, gold_chart, tmp_path):
    setup, _, _ = replay_gold
    raw = setup["source_plan"]
    mapped = {**raw, "public_instrument": {**raw["public_instrument"], "zone_low": 3723.1,
                                         "zone_high": 3753.1, "invalidation_level": 3832.9, "tick_size": 0.1}}
    row = {**setup, "source_plan": mapped, "levels": cards.card_plan(mapped)}
    snap = gold_chart("XAUUSD", "60", tmp_path)
    snap["price_scale_check"] = images.not_compared("XAUUSD", snap, "controlled fixture")
    plain = tv.snapshot_asset("XAUUSD", "Gold", snap, tmp_path)
    asset = overlay.apply(plain, row)
    overlay.validate(asset, row)
    source = asset["plan_overlay"]["source"]
    assert source["phase_terms"] == GOLD_CANCEL + ". Wrong above 3,832.9 after entry on MGC"
    assert {m["price"] for m in asset["plan_overlay"]["markers"]} == {3722, 3752, 3792}
    store = SimpleNamespace(get_outbox_message=lambda key: {"destination": posts.DESTINATION, "payload": json.dumps(row)})
    coordinator = SimpleNamespace(store=store, _clock=lambda: posts._utc("2026-11-21T00:00:00Z"))
    intent = {"plan_status_post": row["key"], "media_assets": [asset]}
    assert images.validate_write(coordinator, intent, "telegram")["markets"] == ["XAUUSD"]
    source["levels"]["zone_low"] = 3723.1
    with pytest.raises(ValueError, match="SOURCE_OR_SCALE_CHANGED"):
        overlay.validate(asset, row)


def test_wti_chart_quote_does_not_map_plan_levels_to_futures(gold_chart, tmp_path):
    raw = {"asset_id": "USOIL", "direction": "BEARISH", "plan_id": "controlled-wti",
           "zone": {"minimum": 79, "maximum": 80}, "expires_at_utc": "2026-11-21T13:15:00Z",
           "invalidation_conditions": [{"field": "close", "operator": "GTE", "threshold": 81}]}
    snap = gold_chart("USOIL", "60", tmp_path)
    snap["page_title"] = "CL1! 80"
    comparison_at, _ = images.comparison_clock("USOIL", images.utc(snap["captured_at_utc"]))
    snap = images.bind_scale("USOIL", snap, quote={"market": "USOIL", "instrument": "USOIL", "price": 80,
        "quoted_at_utc": comparison_at.isoformat(), "known_at_utc": snap["captured_at_utc"],
        "source_path": "controlled-wti.json", "source_sha256": "a" * 64, "price_basis": "chart_futures"})
    row = {"key": "controlled-wti", "kind": "setup", "symbol": "USOIL",
           "source_plan": raw, "levels": cards.card_plan(raw), "level_contract": reader.CURRENT_LEVEL_CONTRACT}
    asset = overlay.apply(tv.snapshot_asset("USOIL", "WTI", snap, tmp_path), row)
    overlay.validate(asset, row)
    assert asset["plan_overlay"]["markers"] == []
    assert asset["plan_overlay"]["source"]["phase_terms"] == "Cancel if price closes at or above 81 before entry"
