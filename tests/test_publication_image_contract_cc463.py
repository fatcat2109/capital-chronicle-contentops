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

NOW = datetime(2026, 11, 12, 9, tzinfo=timezone.utc)


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
    check = contract.compare_scale("USOIL", snap, quote("USOIL", 85.681))
    assert check["level_offset"] == pytest.approx(.909)
    assert check["quote"]["price"] == 85.681 and check["chart_price"] == 86.59


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
