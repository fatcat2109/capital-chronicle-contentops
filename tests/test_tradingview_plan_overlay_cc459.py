"""Real captured axes/images; fixture targets are geometric test inputs, never public claims."""
from copy import deepcopy
import json
from pathlib import Path, PureWindowsPath

from PIL import Image
import pytest

from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops import tradingview_plan_overlay_v1 as overlay

ROOT = Path(__file__).parents[1] / "docs/publisher/CC-459"


def captured(market, variant=0):
    proof = json.loads((ROOT / "six-market-scale-proof.json").read_text(encoding="utf-8"))
    packet = proof["markets"][market]
    asset = deepcopy(packet["variants"][variant])
    asset["path"] = str(ROOT / "media" / market / PureWindowsPath(asset["path"]).name)
    snap = asset["tradingview_snapshot"]
    snap["path"] = str(ROOT / "media" / market / PureWindowsPath(snap["path"]).name)
    return packet, asset


@pytest.mark.parametrize("market", sorted(tv.SYMBOLS))
@pytest.mark.parametrize("variant", [0,1])
def test_six_real_captures_match_visible_axes_and_all_overlay_pixels(market, variant):
    proof, asset = captured(market, variant)
    assert proof["status"] == "VERIFIED" and proof["grid_anchor_count"] >= 6
    assert proof["max_grid_error_px"] <= 2 and proof["max_level_error_px"] <= 2
    assert asset["tradingview_snapshot"]["tv_symbol"] == tv.SYMBOLS[market]
    tv.validate_snapshot_asset(asset)
    overlay.validate(asset)
    assert all(m["error_px"] <= 2 for m in asset["plan_overlay"]["markers"])
    assert asset["plan_overlay"]["source"]["source_content_hash"]


@pytest.mark.parametrize("scalar", [False, True])
def test_a_supplied_target_is_never_drawn(tmp_path,scalar):
    # CC-583 / decision 82: "A target is never drawn"; the zone and invalidation stay exactly as drawn.
    _, asset = captured("EURUSD")
    source = deepcopy(asset["plan_overlay"]["source"])
    scale = asset["tradingview_snapshot"]["chart_geometry"]
    # An explicitly synthetic in-view target tests the renderer, not a market forecast.
    source["key"] = "controlled-target-test"
    target=scale["grid_checks"][5]["price"]
    source["levels"]["target"] = target if scalar else [target]
    plain = tv.snapshot_asset("EURUSD", "Controlled geometry test", asset["tradingview_snapshot"], tmp_path)
    marked = overlay.apply(plain,source)
    overlay.validate(marked,source)
    assert [m["label"] for m in marked["plan_overlay"]["markers"]] == [m["label"] for m in asset["plan_overlay"]["markers"]]
    assert marked["plan_overlay"]["target_drawn"] is False and "target" not in marked["plan_overlay"]["source"]["levels"]
    with Image.open(marked["path"]) as im:
        ox,oy = marked["tradingview_snapshot"]["framing"]["original_box"][:2]
        y = round(overlay._price_y(scale,target)+oy)
        assert im.getpixel((scale["pane_box"][0]+60+ox,y)) != (31,83,160)


def test_a_level_beyond_the_visible_range_has_a_priced_edge_marker():
    _, asset = captured("US500")
    edge = next(m for m in asset["plan_overlay"]["markers"] if m["edge"])
    assert edge["label"] == "Invalidation" and edge["price"] is not None and edge["edge"] == "above view"


def test_the_line_and_its_label_use_the_same_exported_tick_rounding(tmp_path):
    _, asset = captured("EURUSD")
    source = deepcopy(asset["plan_overlay"]["source"])
    source["levels"].update(zone_low=1.122456,tick_size=.0001)
    plain = tv.snapshot_asset("EURUSD","Controlled rounding test",asset["tradingview_snapshot"],tmp_path)
    marked = overlay.apply(plain,source)
    low = next(m for m in marked["plan_overlay"]["markers"] if m["label"] == "Entry low")
    scale = asset["tradingview_snapshot"]["chart_geometry"]
    offset = marked["tradingview_snapshot"]["framing"]["original_box"][1]
    assert low["expected_y"] == pytest.approx(overlay._price_y(scale,1.1225)+offset)
    overlay.validate(marked,source)


def test_changed_source_levels_are_refused():
    _, asset = captured("EURUSD")
    source = deepcopy(asset["plan_overlay"]["source"])
    source["levels"]["zone_low"] = 123
    with pytest.raises(ValueError,match="SOURCE_OR_SCALE_CHANGED"):
        overlay.validate(asset,source)


def test_header_or_logo_pixel_change_is_refused(tmp_path):
    _, asset = captured("EURUSD")
    path = tmp_path / "changed.png"
    with Image.open(asset["path"]) as im:
        im = im.convert("RGB")
        im.putpixel((10,10),(255,0,0))
        im.save(path)
    asset["path"] = str(path)
    with pytest.raises(ValueError,match="PROTECTED_ATTRIBUTION_CHANGED"):
        overlay.validate(asset)


def test_unusable_scale_falls_back_to_the_plain_snapshot(tmp_path, monkeypatch):
    from live_contentops import plan_status_posts_v1 as posts
    _, asset = captured("EURUSD")
    snap = deepcopy(asset["tradingview_snapshot"])
    snap.pop("chart_geometry")
    monkeypatch.setattr(tv, "plan_snapshot", lambda *a,**kw: tv.snapshot_asset("EURUSD","Plain chart",snap,tmp_path))
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    row = deepcopy(asset["plan_overlay"]["source"])
    selected, credit = posts._post_image(row,tmp_path)
    assert credit and not selected.get("plan_overlay")
    tv.validate_snapshot_asset(selected)
    assert "PRICE_SCALE_NOT_CAPTURED" in (tmp_path / "outcomes.jsonl").read_text()
