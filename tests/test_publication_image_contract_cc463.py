"""Decision 124 at the real coordinator and existing image register; no network."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image
import pytest

from live_contentops import publication_image_contract_v1 as contract
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.published_images_v1 import PublishedImages, day_of
from test_article_publication_quality_cc333 import publication
from test_tradingview_snapshot_cc314 import FIXTURE

NOW = datetime(2026, 11, 12, 16, tzinfo=timezone.utc)


def quote(market="US500", price=7549.51):
    return {"market": market, "instrument": market, "price": price,
        "quoted_at_utc": NOW.isoformat(), "known_at_utc": NOW.isoformat(),
        "source_path": "controlled-main-capture.json", "source_sha256": "a" * 64,
        "price_basis": "plan_feed"}


def snapshot():
    return {"path": str(FIXTURE), "sha256": sha256(FIXTURE.read_bytes()).hexdigest(),
        "tv_symbol": tv.SYMBOLS["US500"], "interval": "240", "interval_label": "4h",
        "chart_url": tv.chart_url(tv.SYMBOLS["US500"], "240"),
        "page_title": "SPX 7,549.51", "captured_at_utc": NOW.isoformat(), "capture_ratio": "16:9"}


def chart(tmp_path):
    taken = contract.bind_scale("US500", snapshot(), quote=quote())
    return {**tv.snapshot_asset("US500", "S&P 500", taken, tmp_path),
            "article_inclusion": True, "canonical_article_media": True}


def message_with(tmp_path, assets, **article_fields):
    store, runtime, coordinator, message, *_ = publication(tmp_path)
    coordinator._clock = lambda: NOW
    intent = json.loads(message["payload"])
    path = Path(intent["output_dir"]) / "run_context_v1.json"
    context = json.loads(path.read_bytes())
    context["article"].update(market_asset="US500", lead_image_asset_id=assets[0]["asset_id"] if assets else None,
                              **article_fields)
    context["media"]["assets"] = assets
    path.write_text(json.dumps(context), encoding="utf-8")
    return store, runtime, coordinator, message


def test_coordinator_records_wrong_type_as_definite_no_write_before_any_destination_probe(tmp_path):
    path = tmp_path / "drawn.png"
    Image.new("RGB", (800, 450), "red").save(path)
    asset = {"asset_id": "drawn", "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(),
             "modality": "source_bound_data_card"}
    store, runtime, coordinator, message = message_with(tmp_path / "run", [asset])
    coordinator._readiness = lambda *a: pytest.fail("wrong image reached a destination probe")
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DEFINITE_NO_WRITE"
    assert result["reason_code"] == "TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE"
    assert runtime.publish_calls == []
    assert store.get_platform_dispatch(result["dispatch_id"])["status"] == "DEFINITE_NO_WRITE"
    assert store.get_outbox_message(message["message_id"])["status"] == "DEFINITE_NO_WRITE"
    again = coordinator._dispatch_message(message, canonical_url=None)
    assert again["status"] == "DEFINITE_NO_WRITE" and runtime.publish_calls == []


def test_coordinator_refuses_an_off_scale_chart(tmp_path):
    asset = chart(tmp_path)
    asset["tradingview_snapshot"]["page_title"] = "SPX 8,549.51"
    _, runtime, coordinator, message = message_with(tmp_path / "run", [asset])
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DEFINITE_NO_WRITE"
    assert result["reason_code"] == "TRADINGVIEW_PRICE_SCALE_MISMATCH"
    assert result["image_contract_details"]["difference_pct"] > contract.MAX_DIFFERENCE_PCT["US500"]
    assert runtime.publish_calls == []


def test_a_valid_chart_reaches_the_real_consumer_and_records_its_type(tmp_path):
    asset = chart(tmp_path)
    _, runtime, coordinator, message = message_with(tmp_path / "run", [asset])
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DISPATCH_CONFIRMED"
    assert runtime.publish_calls == ["substack"]
    from live_contentops.article_publication_quality_v1 import image_register
    record = image_register(coordinator).records()[-1]
    assert record["state"] == "PUBLISHED"
    assert record["images"][0]["image_type"] == "TRADINGVIEW_MARKET_CHART"
    assert record["images"][0]["price_scale_check"]["difference_pct"] == 0


@pytest.mark.parametrize("market", sorted(tv.SYMBOLS))
def test_every_market_has_an_explicit_scale_threshold_and_refuses_excess(market):
    snap = {**snapshot(), "tv_symbol": tv.SYMBOLS[market], "page_title": "TICKER 100"}
    own = quote(market, 100)
    assert contract.compare_scale(market, snap, own)["maximum_difference_pct"] == contract.MAX_DIFFERENCE_PCT[market]
    snap["page_title"] = "TICKER 103"
    with pytest.raises(contract.ImageContractError, match="PRICE_SCALE_MISMATCH"):
        contract.compare_scale(market, snap, own)


def test_stale_or_wrong_instrument_quotes_do_not_certify_the_chart():
    own = quote()
    own["quoted_at_utc"] = (NOW - timedelta(seconds=121)).isoformat()
    with pytest.raises(contract.ImageContractError, match="QUOTE_STALE"):
        contract.compare_scale("US500", snapshot(), own)
    own = {**quote(), "instrument": "MES"}
    with pytest.raises(contract.ImageContractError, match="INSTRUMENT_MISMATCH"):
        contract.compare_scale("US500", snapshot(), own)


def test_wti_conversion_is_additive_and_keeps_both_original_prices():
    snap = {**snapshot(), "tv_symbol": tv.SYMBOLS["USOIL"], "page_title": "CL1! 86.59"}
    check = contract.compare_scale("USOIL", snap, quote("USOIL", 86.481))
    assert check["level_offset"] == pytest.approx(.109)
    assert check["quote"]["price"] == 86.481 and check["chart_price"] == 86.59


def test_daily_counts_count_observed_types_once_and_ignore_reservations(tmp_path):
    register = PublishedImages(tmp_path / "published_images_v1.jsonl")
    asset = chart(tmp_path)
    register.reserve(piece_id="one", assets=[asset], lead_asset_id=asset["asset_id"], now=NOW)
    assert register.daily_image_counts(day_of(NOW))["counts_by_type"] == {}
    register.settle("one", state="PUBLISHED", now=NOW, published_at_utc=NOW.isoformat())
    register.settle("one", state="PUBLISHED", now=NOW, published_at_utc=NOW.isoformat())
    report = register.daily_image_counts(day_of(NOW))
    assert report["counts_by_type"] == {"TRADINGVIEW_MARKET_CHART": 1}
    assert len(report["observed_posts"]) == 1


def test_a_wide_capture_cannot_be_padded_into_an_instagram_image(tmp_path):
    with pytest.raises(tv.SnapshotError, match="NATIVE_4X5"):
        tv.frame(FIXTURE, tmp_path / "wide-as-portrait.png", "4:5")
    source = tmp_path / "portrait.png"
    Image.new("RGB", (1080, 1350), "navy").save(source)
    framed = tv.frame(source, tmp_path / "portrait-copy.png", "4:5")
    assert framed["mode"] == "NATIVE_VIEWPORT"
    assert framed["original_box"] == [0, 0, 1080, 1350]


def test_macro_post_refuses_the_old_default_bar_chart(tmp_path):
    asset = chart(tmp_path)
    _, runtime, coordinator, message = message_with(tmp_path / "run", [asset], release_analysis=True)
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DEFINITE_NO_WRITE"
    assert result["reason_code"] == "MACRO_SOURCE_GRAPH_REQUIRED"
    assert runtime.publish_calls == []


def controlled_capture(market, interval, folder, *, ratio="16:9"):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    taken = snapshot()
    if ratio == "4:5":
        path = folder / "controlled-portrait.png"
        Image.new("RGB", (1080, 1350), "navy").save(path)
        taken.update(path=str(path), sha256=sha256(path.read_bytes()).hexdigest(), capture_ratio=ratio)
    return contract.bind_scale(market, taken, quote=quote(market))


def test_article_uses_shared_wide_and_native_portrait_captures_and_the_transport_selects_them(tmp_path, monkeypatch):
    from live_contentops.tradingview_snapshot_v1 import prepare_contract_article
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
    from test_post_image_policy_v1 import packet
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    source = {**packet()["article"], "market_asset": "US500"}
    article, assets = prepare_contract_article(source, [], output_dir=tmp_path, snapshot=controlled_capture)
    assert len(assets) == 2
    assert assets[0]["tradingview_snapshot"]["capture_ratio"] == "16:9"
    assert assets[1]["tradingview_snapshot"]["capture_ratio"] == "4:5"
    context = {"article": article, "selection": {}, "media": {"assets": assets}}
    (tmp_path / "run_context_v1.json").write_text(json.dumps(context), encoding="utf-8")
    for dest, chosen in [("telegram", assets[0]), ("instagram_business", assets[1])]:
        intent = {"work_item_id": "one", "output_dir": str(tmp_path), "destination_plan": {"destination": dest},
            "native_payload": {"text": "Bounded test.", "media_asset_ids": article["native_destination_media"][dest]}}
        data = _durable_intent_inputs(intent)
        assert data["local_media"] == chosen["path"]
        assert data["media_assets"] == [chosen]


def test_two_article_capture_failures_do_not_create_a_drawn_substitute_and_keep_the_daily_cap(tmp_path, monkeypatch):
    from live_contentops.tradingview_snapshot_v1 import prepare_contract_article
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import post_image_view
    from live_contentops.post_visuals_v1 import require_publication_image
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    calls = []
    def unavailable(*args, **kwargs):
        calls.append(1)
        raise tv.SnapshotError("CONTROLLED_CHART_UNAVAILABLE")
    article, assets = prepare_contract_article({"title": "S&P 500", "market_asset": "US500"}, [],
        output_dir=tmp_path, snapshot=unavailable)
    assert assets == [] and len(calls) == 2
    assert contract.bounded_text_fallback(article, tmp_path)["first_cause"] == "CONTROLLED_CHART_UNAVAILABLE"
    view = post_image_view({"article": article, "media_assets": []}, output_dir=tmp_path / "view")
    assert view["media_assets"] == [] and view["post_image_policy"]["default_asset_id"] is None
    require_publication_image("telegram", {"article": article, "output_dir": tmp_path, "media_assets": []})
    with pytest.raises(ValueError, match="IMAGE_REQUIRED"):
        require_publication_image("instagram_business", {"article": article, "output_dir": tmp_path})
    register = PublishedImages(tmp_path / "images.jsonl")
    for i in range(2):
        register.reserve(piece_id=str(i), assets=[], lead_asset_id=None, now=NOW,
            market="US500", image_contract=contract.POLICY, text_fallback={"policy": contract.POLICY})
    with pytest.raises(ValueError, match="DAILY_ARTICLE_CAP_REACHED"):
        register.reserve(piece_id="three", assets=[], lead_asset_id=None, now=NOW,
            text_fallback={"policy": contract.POLICY})


def test_main_quote_reader_uses_a_hash_verified_saved_tick_and_does_not_export_account_fields(tmp_path):
    import os
    folder = tmp_path / "t2-runs/run/request"
    folder.mkdir(parents=True)
    body = {"schema": "CapitalChroniclePrimaryDemoAccountCaptureV1", "known_at_utc": NOW.isoformat(),
            "account": {"login": "PRIVATE_TEST_VALUE"}, "ticks": {
                "US500": {"bid": 7549.5, "ask": 7549.52, "time": NOW.timestamp()}}}
    digest = sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    path = folder / "capture.json"
    path.write_text(json.dumps({**body, "content_hash": digest}), encoding="utf-8")
    os.utime(path, (NOW.timestamp(), NOW.timestamp()))
    observed = contract.saved_main_quote("US500", NOW, root=tmp_path)
    assert observed["price"] == pytest.approx(7549.51)
    assert observed["source_sha256"] == sha256(path.read_bytes()).hexdigest()
    assert "PRIVATE_TEST_VALUE" not in json.dumps(observed)
    body["ticks"]["US500"]["bid"] = 9999
    path.write_text(json.dumps({**body, "content_hash": digest}), encoding="utf-8")
    os.utime(path, (NOW.timestamp(), NOW.timestamp()))
    with pytest.raises(ValueError, match="CONTEMPORANEOUS_MAIN_QUOTE_UNAVAILABLE"):
        contract.saved_main_quote("US500", NOW, root=tmp_path)


def test_wti_overlay_translates_the_supplied_levels_and_prints_the_difference(tmp_path):
    from live_contentops import tradingview_plan_overlay_v1 as overlay
    from test_tradingview_plan_overlay_cc459 import captured
    _, asset = captured("USOIL")
    snap = deepcopy(asset["tradingview_snapshot"])
    snap.update(page_title="CL1! 86.59", captured_at_utc=NOW.isoformat())
    snap = contract.bind_scale("USOIL", snap, quote=quote("USOIL", 86.481))
    original = deepcopy(asset["plan_overlay"]["source"])
    original["levels"].update(zone_low=85, zone_high=85.1, invalidation_level=84.5, target_level=87)
    original["levels"].pop("target", None)
    plain = tv.snapshot_asset("USOIL", "WTI", snap, tmp_path)
    marked = overlay.apply(plain, original)
    assert "0.109 USD/bbl at capture" in marked["plan_overlay"]["basis_label"]
    low = next(m for m in marked["plan_overlay"]["markers"] if m["label"] == "Entry low")
    target = next(m for m in marked["plan_overlay"]["markers"] if m["label"] == "Target")
    assert low["price"] == pytest.approx(85.109)
    assert target["price"] == pytest.approx(87.109)
    assert original["levels"]["zone_low"] == 85
    overlay.validate(marked, original)


def test_instagram_rejects_the_wide_image_even_when_its_prices_pass(tmp_path):
    asset = chart(tmp_path)
    _, _, coordinator, message = message_with(tmp_path / "run", [asset])
    intent = json.loads(message["payload"])
    intent["destination_plan"]["destination"] = "instagram_business"
    intent["native_payload"] = {"text": "Exact copy", "media_asset_ids": [asset["asset_id"]]}
    with pytest.raises(contract.ImageContractError, match="NATIVE_4X5"):
        contract.validate_write(coordinator, intent, "instagram_business")


def test_macro_accepts_a_bound_economic_series_download(tmp_path):
    snap = snapshot()
    snap.update(tv_symbol="FRED:CPIAUCSL", chart_url=tv.chart_url("FRED:CPIAUCSL", "240"),
                page_title="CPIAUCSL 330")
    asset = {**tv.snapshot_asset("FRED:CPIAUCSL", "Consumer prices", snap, tmp_path),
             "article_inclusion": True, "canonical_article_media": True}
    _, _, coordinator, message = message_with(tmp_path / "run", [asset], macro_data_post=True)
    result = contract.validate_write(coordinator, json.loads(message["payload"]), "substack")
    assert result["first_image_type"] == "TRADINGVIEW_ECONOMIC_CHART"


def test_closed_cash_index_compares_the_last_close_not_a_moving_overnight_quote():
    captured = datetime(2026, 11, 12, 2, tzinfo=timezone.utc)
    at, closed = contract.comparison_clock("US500", captured)
    assert closed and at == datetime(2026, 11, 11, 21, tzinfo=timezone.utc)
    frozen = {**snapshot(), "captured_at_utc": captured.isoformat()}
    close_quote = {**quote(), "quoted_at_utc": at.isoformat(), "known_at_utc": at.isoformat()}
    result = contract.compare_scale("US500", frozen, close_quote)
    assert result["difference_pct"] == 0 and result["comparison_basis"] == "LAST_CLOSE"
    live_quote = {**quote(price=7800), "quoted_at_utc": captured.isoformat(), "known_at_utc": captured.isoformat()}
    with pytest.raises(contract.ImageContractError, match="QUOTE_STALE"):
        contract.compare_scale("US500", frozen, live_quote)


@pytest.mark.parametrize("market", sorted(set(tv.SYMBOLS) - {"BTCUSD"}))
def test_weekend_charts_use_the_last_close_with_dst_correct_et_clock(market):
    captured = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)
    at, closed = contract.comparison_clock(market, captured)
    assert closed
    assert at == datetime(2026, 11, 13, 21 if market == "US500" else 22, tzinfo=timezone.utc)
    summer = datetime(2026, 7, 18, 12, tzinfo=timezone.utc)
    at, closed = contract.comparison_clock(market, summer)
    assert closed and at.hour == (20 if market == "US500" else 21)
    assert contract.comparison_clock("BTCUSD", captured) == (captured, False)
