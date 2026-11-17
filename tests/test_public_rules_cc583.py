"""CC-583: the pinned scorecard and the plan chart keep decisions 117, 40 and 82.

F4: no "model calls" in public text, and the public wording filters refuse it.
F5: the scorecard prints only plan levels, on the instrument's tick; no fill-like price.
F1: the plan chart overlay never draws a target, and the quality checks read what it drew.
Fixture prices are test inputs, never public claims.
"""
from copy import deepcopy
import re

import pytest

from live_contentops import pinned_result_scorecard_v1 as scorecard
from live_contentops import tradingview_plan_overlay_v1 as overlay
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops import weekly_scored_calls_v1 as weekly
from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, PUBLIC_NOTICE, PublicOutputError, check_publication_copy, public_execution_copy_forbidden,
)
from test_pinned_result_scorecard_cc394 import NOW, call, export
from test_tradingview_plan_overlay_cc459 import captured
from test_weekly_scored_calls_cc379 import CUTOFF, export as weekly_export, scored as weekly_scored


# F4 (decision 117) -------------------------------------------------------------------------------

def test_f4_pinned_scorecard_says_conditional_calls_without_model():
    text = scorecard.project(export(call("win")), now=NOW)["text"]
    assert "Results describe resolved conditional calls." in text
    assert not re.search(r"\bmodel\b", text, re.I)


def test_f4_weekly_record_and_its_writer_guidance_drop_model_calls():
    record = weekly.project(weekly_export(), cutoff_utc=CUTOFF)
    empty = weekly_export()
    empty["status"].update(plans=[], scored_call_count=0)
    for text in (record["text"], weekly.project(empty, cutoff_utc=CUTOFF)["text"], weekly.WRITER_GUIDANCE):
        assert not re.search(r"model[\s-]+calls?", text, re.I)
    assert "Results refer to resolved conditional calls." in record["text"]


@pytest.mark.parametrize("phrase", ["resolved conditional model calls", "one model call", "the Model-Call record"])
def test_f4_public_wording_filter_refuses_model_call(phrase):
    body = f"Results describe {phrase}.\n\n{PUBLIC_NOTICE} {CONFLICTS_NOTICE}"
    assert public_execution_copy_forbidden(body)
    with pytest.raises(PublicOutputError, match="PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"):
        check_publication_copy({"body": body})


def test_f4_plan_page_and_image_filters_refuse_model_call():
    from live_contentops.image_quality_v1 import BANNED
    from live_contentops.plan_analysis_pages_v1 import public_filter
    with pytest.raises(ValueError, match="PLAN_ANALYSIS_PRIVATE_ACCOUNT_OR_SIZE_FORBIDDEN"):
        public_filter("These are resolved conditional model calls.")
    assert {"model call", "model calls"} <= set(BANNED)


# F5 (decision 40) --------------------------------------------------------------------------------

def plan(ident, *, asset="USOIL", low=85.75, high=86.05, tick=0.001, mapped=None, state="NOT_SCORED_UNTRIGGERED"):
    value = call(ident, "HIT", state=state)
    value.update(asset_id=asset, zone={"minimum": low, "maximum": high},
                 invalidation_conditions=[{"field": "close", "operator": "LT", "threshold": 84.1}])
    value["outcome"]["score"] and value["outcome"]["score"].update(asset_id=asset)
    if tick is not None:
        value["target_tick_size"] = tick
    value["public_instrument"] = {"name": "Micro WTI crude oil", "symbol": "MCL", "kind": "FUT",
                                  "contract_month": "2027-01", **(mapped or {})}
    return value


MCL_MAPPED = {"zone_low": 85.94735687146667, "zone_high": 85.94735687146667, "invalidation_level": 83.99,
              "direction": "BULLISH", "tick_size": 0.01,
              "entries": [{"kind": "LIMIT", "zone_low": 85.94735687146667, "zone_high": 85.94735687146667}]}


def test_f5_mapped_unrounded_equal_prices_are_replaced_by_the_plan_levels():
    # The audit's 14 Nov line: "entry zone 85.94735687146667–85.94735687146667".
    record = scorecard.project(export(plan("mcl", mapped=MCL_MAPPED)), now=NOW)
    assert "| entry zone 85.75–86.05 (plan levels) | EXPIRED (untriggered; not scored)" in record["text"]
    assert "85.947" not in record["text"] and "85.95" not in record["text"]


def test_f5_plan_levels_are_rounded_to_the_instrument_tick():
    record = scorecard.project(export(plan("gold", asset="XAUUSD", low=4085.1955, high=4090.2049, tick=0.01)), now=NOW)
    assert "entry zone 4,085.2–4,090.2 (plan levels)" in record["text"]
    assert "4,085.1955" not in record["text"] and "4090.2049" not in record["text"]


def test_f5_a_plan_without_an_exported_tick_uses_its_market_tick():
    record = scorecard.project(export(plan("gold", asset="XAUUSD", low=4033.406, high=4085.1955, tick=None)), now=NOW)
    assert "entry zone 4,033.406–4,085.196 (plan levels)" in record["text"]


@pytest.mark.parametrize("low, high", [(86.0, 86.0), (86.0001, 86.0004)])
def test_f5_a_one_price_zone_prints_no_price(low, high):
    record = scorecard.project(export(plan("point", low=low, high=high)), now=NOW)
    line = record["rows"][0]["line"]
    assert "entry zone" not in line and "86" not in line
    assert line.endswith("| original direction was bullish | EXPIRED (untriggered; not scored)")
    assert line in record["text"]


def test_f5_a_plan_without_levels_prints_no_price():
    # Main's export contract requires a zone; a held row without one is covered below.
    assert scorecard.plan_levels("USOIL", {"zone_low": None, "zone_high": None}, {}) is None


def test_f5_held_lines_from_before_the_change_are_rendered_again_or_lose_their_price():
    old = {"plan_id": "gone", "outcome_id": None, "score_hash": None, "at_utc": "2026-11-10T08:40:00Z",
           "result": "EXPIRED", "scored": False, "corrects_outcome_id": None, "scored_at_utc": None,
           "direction_at_window_end": None,
           "line": "2026-11-10 ET | Micro gold (MGC futures, Dec 2026) | original direction was bearish | "
                   "entry zone 3,954.3964602861997–3,954.3964602861997 | EXPIRED (untriggered; not scored)"}
    held = {**old, "plan_id": "mcl", "outcome_id": "outcome-mcl", "result": "STOPPED", "scored": True,
            "scored_at_utc": "2026-11-10T08:50:00Z",
            "line": "2026-11-10 ET | Micro WTI crude oil (MCL futures, Jan 2027) | original direction was bullish | "
                    "entry zone 85.94735687146667–85.94735687146667 | STOPPED"}
    record = scorecard.project(export(plan("mcl", mapped=MCL_MAPPED)), now=NOW, retained_rows=[old, held])
    lines = {r["plan_id"]: r["line"] for r in record["rows"]}
    assert lines["gone"] == ("2026-11-10 ET | Micro gold (MGC futures, Dec 2026) | original direction was bearish"
                             " | EXPIRED (untriggered; not scored)")
    assert lines["mcl"].endswith("| original direction was bullish | entry zone 85.75–86.05 (plan levels) | STOPPED")
    assert "3,954.39" not in record["text"] and "85.947" not in record["text"]
    assert record["counts"]["STOPPED"] == 1 and record["counts"]["total"] == 2


def _weekly_line(zone, *, tick=None):
    data = weekly_export()
    plan = weekly_scored("gold", "STOPPED", "2026-11-10T14:00:00Z")
    if zone is None:
        plan.pop("zone")
    else:
        plan["zone"] = {"minimum": zone[0], "maximum": zone[1]}
    if tick is not None:
        plan["target_tick_size"] = tick
    data["status"].update(plans=[plan], scored_call_count=1)
    record = weekly.project(data, cutoff_utc=CUTOFF)
    return record["rows"][0]["line"], record["text"]


def test_f5_weekly_record_prints_plan_levels_on_the_plan_tick():
    line, text = _weekly_line(("4085.1955", "4090.2049"), tick=0.01)
    assert line == "- Tue 10 Nov ET: Gold; original direction was bearish; entry zone 4,085.2–4,090.2; stopped."
    assert "4,085.1955" not in text and "4,090.2049" not in text
    line, _ = _weekly_line(("4033.406", "4085.1955"))  # No exported tick: the market's tick.
    assert "entry zone 4,033.406–4,085.196;" in line


@pytest.mark.parametrize("zone", [None, ("4070", "4070"), ("4070.0001", "4070.0004")])
def test_f5_weekly_record_prints_no_price_without_plan_levels_or_for_one_price(zone):
    line, text = _weekly_line(zone)
    assert line == "- Tue 10 Nov ET: Gold; original direction was bearish; stopped."
    assert line in text and "4,070" not in text


def test_f5_weekly_unscored_expiry_uses_the_same_rule():
    data = weekly_export()
    data["status"]["plans"].append({"plan_id": "legacy-expiry", "asset_id": "EURUSD", "direction": "BULLISH",
        "status": "EXPIRED", "zone": {"minimum": 1.123456, "maximum": 1.12389}, "invalidation_conditions": [],
        "expires_at_utc": "2026-11-12T14:00:00Z", "outcome": {"state": "NOT_SCORED_UNTRIGGERED"}})
    data["transitions"]["transitions"].append({"plan_id": "legacy-expiry", "status": "EXPIRED",
                                                "at_utc": "2026-11-12T14:00:00Z"})
    record = weekly.project(data, cutoff_utc=CUTOFF)
    line = next(r["line"] for r in record["rows"] if r["plan_id"] == "legacy-expiry")
    assert line == ("- Thu 12 Nov ET: EUR/USD; original direction was bullish; entry zone 1.12346–1.12389; "
                    "expired without entry; not scored.")


# F1 (decision 82) --------------------------------------------------------------------------------

def test_f1_source_binding_carries_no_target():
    row = {"key": "k", "symbol": "XAUUSD", "source_content_hash": "h",
           "levels": {"zone_low": 3954, "zone_high": 3964, "invalidation_level": 3972.6,
                      "target": [3876], "target_level": 3876, "direction": "bearish"}}
    levels = overlay.source_binding(row)["levels"]
    assert "target" not in levels and "target_level" not in levels
    assert levels == {"zone_low": 3954, "zone_high": 3964, "invalidation_level": 3972.6, "direction": "bearish"}


def test_f1_overlay_draws_no_target_and_records_what_it_drew(tmp_path):
    _, asset = captured("EURUSD")
    source = deepcopy(asset["plan_overlay"]["source"])
    scale = asset["tradingview_snapshot"]["chart_geometry"]
    plain = tv.snapshot_asset("EURUSD", "Controlled geometry test", asset["tradingview_snapshot"], tmp_path)
    without = overlay.apply(deepcopy(plain), source)
    source["levels"]["target_level"] = scale["grid_checks"][5]["price"]
    with_target = overlay.apply(plain, source)
    labels = [m["label"] for m in with_target["plan_overlay"]["markers"]]
    assert "Target" not in labels and sorted(labels) == ["Entry high", "Entry low", "Invalidation"]
    assert with_target["plan_overlay"]["target_drawn"] is False
    # The zone and the invalidation are drawn exactly as without a target.
    assert with_target["plan_overlay"]["markers"] == without["plan_overlay"]["markers"]
    assert with_target["sha256"] == without["sha256"]
    overlay.validate(with_target, source)


def _drew_a_target(asset):
    marked = deepcopy(asset)
    marker = deepcopy(marked["plan_overlay"]["markers"][0])
    marker.update(label="Target", price=3876)
    marked["plan_overlay"]["markers"].append(marker)
    return marked


def test_f1_overlay_and_snapshot_checks_refuse_an_image_whose_overlay_drew_a_target():
    _, asset = captured("EURUSD")
    tv.validate_snapshot_asset(asset)  # The real target-free capture passes.
    marked = _drew_a_target(asset)
    assert marked["tradingview_snapshot"]["target_drawn"] is False  # The raw record cannot see it.
    with pytest.raises(ValueError, match="TRADINGVIEW_OVERLAY_TARGET_DRAWN"):
        overlay.validate(marked)
    with pytest.raises(ValueError, match="TRADINGVIEW_OVERLAY_TARGET_DRAWN"):
        tv.validate_snapshot_asset(marked)
    flagged = deepcopy(asset)
    flagged["plan_overlay"]["target_drawn"] = True
    with pytest.raises(ValueError, match="TRADINGVIEW_OVERLAY_TARGET_DRAWN"):
        tv.validate_snapshot_asset(flagged)


def test_f1_article_quality_check_refuses_an_image_whose_overlay_drew_a_target():
    from live_contentops.article_publication_quality_v1 import ImagePolicyError, validate_snapshot_asset
    _, asset = captured("EURUSD")
    for marked in (_drew_a_target(asset), {**deepcopy(asset), "plan_overlay": {**asset["plan_overlay"], "target_drawn": True}}):
        with pytest.raises(ImagePolicyError, match="TRADINGVIEW_OVERLAY_TARGET_DRAWN"):
            validate_snapshot_asset(marked, market="EURUSD")
