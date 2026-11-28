"""CC-788 (Jim, 24 Nov 2026): the Nasdaq 100 (Exness USTEC) is the seventh core market.

Every public output treats it like the other six: its public name, the cash-index chart, index-point
precision, no target, the scenario voice, dated results, the chart or the fact-card fallback, notices once
and grouped numbers. Missing Nasdaq data shows as a missing row or an "unavailable" note, never a guess.
Controlled fixtures only; nothing here reads a live store or contacts a provider.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from live_contentops import article_scenarios_v1 as scenarios
from live_contentops import call_followups_v1 as followups
from live_contentops import cpi_reaction_page_v1 as cpi
from live_contentops import daily_trend_board_v1 as board
from live_contentops import event_reaction_source_v1 as reactions
from live_contentops import image_template_inputs_v1 as inputs
from live_contentops import image_templates_v1 as templates
from live_contentops import market_wrap_editorial_v1 as wrap_copy
from live_contentops import market_wrap_sources_v1 as wrap_sources
from live_contentops import pinned_result_scorecard_v1 as scorecard
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import public_instruments_v1 as instruments
from live_contentops import public_market_quote_v1 as quotes
from live_contentops import publication_image_contract_v1 as contract
from live_contentops import reader_article_contract_v1 as reader
from live_contentops import tradingview_idea_v1 as idea
from live_contentops import tradingview_plan_overlay_v1 as overlay
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops import x_reply_fact_policy_v1 as reply_policy
from live_contentops import x_reply_fact_sources_v1 as reply_sources
from test_daily_trend_board_cc537 import at, ready, register, seal, source  # noqa: F401  (ready is a fixture)

SIX = ("XAUUSD", "US500", "EURUSD", "USDJPY", "USOIL", "BTCUSD")
CORE = SIX + ("USTEC",)
NASDAQ_DAY = "2026-11-30"  # a Monday after CC-788's board start


# ------------------------------------------------------------------ one core-market list everywhere

@pytest.mark.parametrize("table", [
    posts.MARKETS, posts.TITLES, board.MARKETS, board.PRICE_PLACES, scorecard.PLAN_TICKS, inputs.MARKETS,
    idea.MARKETS, tv.SYMBOLS, tv.NAMES, contract.MAX_DIFFERENCE_PCT,
    wrap_sources.MARKETS, scenarios.MARKETS, reactions.MARKETS, instruments.INSTRUMENTS,
    instruments.MARKET_PATTERNS,
], ids=lambda t: type(t).__name__ + str(len(t)))
def test_every_core_market_table_holds_the_six_and_the_nasdaq_100(table):
    assert set(table) == set(CORE)


def test_public_names_never_the_broker_symbol():
    assert posts.TITLES["USTEC"] == "Nasdaq 100" and posts.MARKETS["USTEC"] == "the Nasdaq 100"
    assert {board.MARKETS["USTEC"], inputs.MARKETS["USTEC"], idea.MARKETS["USTEC"], cpi.LABELS["USTEC"],
            wrap_sources.MARKETS["USTEC"][0]} == {"Nasdaq 100"}
    assert wrap_copy.title_market("USTEC") == "Nasdaq 100 (NQ futures reference)"
    assert posts.BROKER_SYMBOL.sub(lambda m: posts.BROKER_NAMES[m[1]], "USTEC fell") == "the Nasdaq 100 fell"
    with pytest.raises(ValueError, match="PUBLIC_INSTRUMENT_NAME_FORBIDDEN:USTEC"):
        instruments.validate_payload({"public_instrument_policy": instruments.POLICY}, {"text": "USTEC fell."})


def test_cash_index_chart_and_index_point_precision_follow_the_sp_500():
    # The S&P 500 uses its cash index (SP:SPX); the Nasdaq 100 uses NASDAQ:NDX, never a CFD feed.
    assert tv.SYMBOLS["US500"] == "SP:SPX" and tv.SYMBOLS["USTEC"] == "NASDAQ:NDX"
    assert board.PRICE_PLACES["USTEC"] == board.PRICE_PLACES["US500"] == 2
    assert scorecard.PLAN_TICKS["USTEC"] == scorecard.PLAN_TICKS["US500"] == "0.01"
    assert reply_sources.PLACES["USTEC"] == 2
    assert templates.price(26846.564, "USTEC") == "26,847" and templates.price(6812.4, "US500") == "6,812"
    assert contract.MAX_DIFFERENCE_PCT["USTEC"] == contract.MAX_DIFFERENCE_PCT["US500"]


def test_the_nasdaq_cash_chart_compares_at_the_last_new_york_close_like_the_sp_500():
    # CC-778: a cash index has no bars overnight; both indices compare at the 16:00 ET close.
    night = datetime(2026, 12, 1, 3, 0, tzinfo=timezone.utc)
    session = datetime(2026, 12, 1, 16, 0, tzinfo=timezone.utc)
    assert contract.comparison_clock("USTEC", night) == contract.comparison_clock("US500", night)
    assert contract.comparison_clock("USTEC", night)[1] is True
    assert contract.comparison_clock("USTEC", session) == (session, False)
    assert followups.CASH_SESSIONS["USTEC"] == followups.CASH_SESSIONS["US500"]


def test_nasdaq_chart_levels_wait_for_their_real_capture_proof():
    # CC-459 verifies each market's axis on real guest captures; until NDX has its two, the chart goes out
    # without drawn levels rather than with unproven ones.
    assert "USTEC" not in overlay.VERIFIED_MARKETS
    asset = {"tradingview_snapshot": {}, "path": "unused.png"}
    assert overlay.apply(asset, {"symbol": "USTEC"}) is asset


def test_the_owner_candidate_of_a_nasdaq_plan_is_mains_ustec_candidate():
    owner = {"candidates": [{"candidate_id": "cand_macro_spx"}, {"candidate_id": "cand_macro_ustec"}]}
    run = {"documents": {"owner-native.json": owner}}
    candidate, filename, pointer = pages._owner_candidate({"asset_id": "USTEC"}, run)
    assert candidate == {"candidate_id": "cand_macro_ustec"} and pointer == "/candidates/1"


# ------------------------------------------------------------------ quotes and reply facts

def test_the_old_ndx_route_is_an_alias_and_its_frozen_observations_stay_valid():
    assert quotes.ALIASES["NDX"] == "USTEC" and "NDX" not in quotes.SYMBOLS
    assert quotes.SYMBOLS["USTEC"][1] == "USTEC" and "USTEC_FUTURES" not in quotes.SYMBOLS
    now = datetime(2026, 11, 30, 15, 0, tzinfo=timezone.utc)
    held_legacy = {"market": "NDX", "source_symbol": "^NDX", "value": 25012.5, "known_at_utc": now.isoformat(),
                   "observed_at_utc": now.isoformat()}
    held_local = {"market": "USTEC", "source_symbol": "USTEC", "value": 25012.5, "known_at_utc": now.isoformat(),
                  "observed_at_utc": now.isoformat()}
    assert quotes.validate(held_legacy, "USTEC", now=now) is held_legacy
    assert quotes.validate(held_local, "NDX", now=now) is held_local
    with pytest.raises(quotes.QuoteError, match="PUBLIC_QUOTE_SYMBOL_MISMATCH"):
        quotes.validate({**held_local, "market": "US500"}, "USTEC", now=now)


@pytest.mark.parametrize("text", ["USTEC slid", "NAS100 slid", "The Nasdaq 100 slid", "NQ=F slid"])
def test_reply_facts_find_the_nasdaq_100_by_any_of_its_names(text):
    assert reply_policy.markets(text) == {"NDX"}
    assert reply_sources.FACT_MARKETS["USTEC"] == "NDX" and reply_sources.LABELS["USTEC"] == ("NDX", "Nasdaq 100")


def test_a_reply_quote_prints_the_nasdaq_at_its_precision():
    observation = {"market": "USTEC", "observed_at_utc": "2026-11-30T15:00:00+00:00",
                   "known_at_utc": "2026-11-30T15:00:01+00:00", "value": 25012.4987, "unit": "points",
                   "day_change": -101.23456, "instrument_name": "Nasdaq 100 index proxy",
                   "source": "Held market data",
                   "display": reply_sources.DISPLAY, "observation_path": "x.json", "observation_sha256": "a" * 64}
    source = reply_sources._quote_source(observation)
    assert source["fact_binding"]["markets"] == ["NDX"]
    assert "25012.50 points" in source["excerpt"] and "-101.23 points" in source["excerpt"]


# ------------------------------------------------------------------ the daily trend board

def nasdaq_board(day=NASDAQ_DAY, *, drop=None, partial=False):
    value = deepcopy(source(day))
    value.pop("content_hash")
    if drop:
        value["markets"].pop(drop)
    if partial:
        value["markets"]["USTEC"]["yardstick"].pop("mean_close_50")
    return seal(value)


def test_board_of_the_seven_markets_prints_the_nasdaq_row_like_the_others():
    current = board.project(nasdaq_board(), now=at(NASDAQ_DAY))
    assert list(current["markets"]) == list(CORE)
    copy = board.compose(current)
    assert copy["summary"].endswith("; Bitcoin DOWN; Nasdaq 100 DOWN")
    nasdaq = copy["blocks"][-1]
    assert nasdaq.startswith("Nasdaq 100 DOWN. Mean closes: 20 sessions 106; 50 sessions 126.")
    assert "Follow a downtrend, 20 sessions (bearish): -0.2R mean on 48 cases, 2016-11-01 to 2026-11-12." in nasdaq
    assert board.fact_rows(current)[-1] == ("Nasdaq 100", "DOWN; 20-session mean 106; 50-session mean 126")


def test_a_board_without_a_nasdaq_row_says_unavailable_and_never_guesses():
    current = board.project(nasdaq_board(drop="USTEC"), now=at(NASDAQ_DAY))
    assert current["markets"]["USTEC"] == {"state": board.UNAVAILABLE, "means": {}, "rows": []}
    copy = board.compose(current)
    assert copy["summary"].endswith("; Nasdaq 100 unavailable")
    assert copy["blocks"][-1] == "Nasdaq 100 unavailable: no trend state or mean closes for this session."
    assert board.fact_rows(current)[-1] == ("Nasdaq 100", "Unavailable")
    # The previous board's Nasdaq state is never compared with an unavailable one.
    previous = board.project(nasdaq_board("2026-11-27"), now=at("2026-11-27"))
    assert "Nasdaq" not in board.compose(current, previous)["changes"]


def test_a_partial_nasdaq_row_stops_the_board_like_any_other_market():
    with pytest.raises(board.BoardSourceError) as caught:
        board.project(nasdaq_board(partial=True), now=at(NASDAQ_DAY))
    assert caught.value.details["missing_fields"] == ["/markets/USTEC/yardstick/mean_close_50"]


def test_boards_before_26_nov_keep_their_six_markets_and_bytes():
    current = board.project(nasdaq_board("2026-11-24"), now=at("2026-11-24"))
    assert list(current["markets"]) == list(SIX)
    assert "Nasdaq" not in json.dumps(board.compose(current))


def test_the_registered_board_fact_card_carries_the_nasdaq_row(ready):
    value = register(ready, nasdaq_board())
    asset, = value["media_assets"]
    assert asset["modality"] == "plan_fact_card"
    assert asset["data_card_packet"]["facts"][-1] == ["Nasdaq 100", "DOWN; 20-session mean 106; 50-session mean 126"]
    store, _ = ready
    board._deliver(store, value, False, False, None, at(NASDAQ_DAY))  # registers the links; sends nothing
    assert board.validate_media(store, {"work_item_id": value["links"][0]["link_id"],
                                        "media_assets": value["media_assets"]})["policy"] == board.POLICY
    for link in value["links"]:
        text = link["native_payload"]["full_text"]
        assert "Nasdaq 100 DOWN" in text and "USTEC" not in text and "target" not in text.lower()
        assert text.count(board.PUBLIC_NOTICE) <= 1


# ------------------------------------------------------------------ the TradingView idea pack

def test_a_nasdaq_plan_makes_an_idea_pack_on_the_cash_index_with_grouped_numbers():
    fixture = Path(__file__).parent / "fixtures" / "tradingview_idea_cc469_plans.json"
    btc = next(p for p in json.loads(fixture.read_text(encoding="utf-8"))["plans"] if p["symbol"] == "BTCUSD")
    plan = json.loads(json.dumps(btc).replace("BTCUSD", "USTEC").replace("Bitcoin", "Nasdaq 100"))
    pack = idea.idea_entry(plan)
    assert pack["status"] == "READY" and pack["check"] == "PASS" and idea.check_idea(pack) == "PASS"
    assert pack["title"].startswith("Nasdaq 100: bearish at 60,000–61,400, wrong above 68,450")
    assert pack["chart"]["symbol"] == "NASDAQ:NDX" and pack["chart"]["interval"] == "D"
    assert [d["label"] for d in pack["chart"]["draw"]] == ["Entry zone", "Invalidation"]
    assert "Base case (bear, " in pack["description"] and "Bull case (" in pack["description"]
    assert "target" not in pack["description"].casefold() and "60600.84" not in pack["description"]
    assert "open NASDAQ:NDX on the daily chart" in pack["how_to_post"]


# ------------------------------------------------------------------ the daily checks

def test_the_daily_checks_map_a_nasdaq_post_to_its_chart(tmp_path):
    from test_public_decision_checks_cc690 import checks, published
    audit = checks(tmp_path)
    plan_source = {"kind": "result", "plan_id": "plan_ndx", "symbol": "USTEC", "source_plan": {
        "macro": "Rates fell after the policy surprise."}}
    for platform, symbol in (("discord", "FX_IDC:EURUSD"), ("telegram", "NASDAQ:NDX")):
        published(audit, "ndx-result", platform, text="Macro: Rates fell after the policy surprise.",
                  source=plan_source, native={"media_asset_ids": ["chart"]},
                  intent={"media_assets": [{"asset_id": "chart", "tradingview_snapshot": {"tv_symbol": symbol}}]})
    output = audit.finish({}, {})
    charts = {(e["platform"], e["first_cause"]) for e in output["issues"] if e["decision"] == "82"}
    assert ("discord", "MARKET_TRADINGVIEW_SYMBOL_MISMATCH") in charts
    assert not {cause for platform, cause in charts if platform == "telegram"}
    assert not any(cause == "MARKET_TRADINGVIEW_SYMBOL_UNMAPPED" for _, cause in charts)


# ------------------------------------------------------------------ wraps, maps and articles

def map_record(*, nasdaq=True):
    rows = [{"market": m, "last": 25012.5 if m == "USTEC" else 158.2, "change_1d_pct": .5, "state_word": "Range",
             "view_line": "No view", "driver_line": "PPI Friday"} for m in (CORE if nasdaq else SIX)]
    if nasdaq == "unavailable":
        rows[-1] = {"market": "USTEC", "unavailable": True}
    return {"market_asset": "USDJPY", "morning_map": {"date_et": "Mon 30 Nov", "lead_line": "USD/JPY moved most.",
                                                      "lead_market": "USDJPY", "rows": rows}}


@pytest.mark.parametrize("nasdaq", [True, "unavailable", False])
def test_morning_map_tables_render_seven_rows_or_keep_six(tmp_path, nasdaq):
    from live_contentops import image_quality_v1 as quality
    data = inputs.for_morning_map(map_record(nasdaq=nasdaq))
    assert [r["market"] for r in data["map"]["rows"]] == list(CORE if nasdaq else SIX)
    for master in ("W", "T"):
        image, meta = templates.compile_image(data, master, image_number=2)
        names = [t["text"] for t in meta["texts"] if t["field"] == "map.market"]
        assert names[-1] == ("Nasdaq 100" if nasdaq else "Bitcoin")
        boxes = [t["box"] for t in meta["texts"]]
        assert not any(max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])
                       for i, a in enumerate(boxes) for b in boxes[i + 1:])
        assert all(t["box"][3] <= image.size[1] for t in meta["texts"])
        if nasdaq == "unavailable":
            assert [t["text"] for t in meta["texts"] if t["field"] == "map.unavailable"] == ["Unavailable"]
            assert "25,012" not in json.dumps(meta["texts"])
        assert meta["alt_text"].startswith("Seven markets" if nasdaq else "Six markets")
        asset = templates.render(data, master, tmp_path / str(nasdaq), image_number=2)
        check = quality.code_check(asset)
        assert check["passed"], check["causes"]


def test_a_map_never_marks_one_of_the_six_unavailable():
    record = map_record()
    record["morning_map"]["rows"][0] = {"market": "XAUUSD", "unavailable": True}
    assert inputs.for_morning_map(record) is None


def test_the_wrap_map_shows_a_missing_nasdaq_quote_as_unavailable():
    pack = {"morning_map_sources": {"rows": {m: {"last": 100 + i, "change_1d_pct": i / 10, "state_word": "Range"}
                                             for i, m in enumerate(SIX)}},
            "analysis": {"outlooks": {}, "layers": {}}}
    value = wrap_copy.morning_map(pack, datetime(2026, 11, 30).date())
    assert value["rows"][-1] == {"market": "USTEC", "unavailable": True}
    assert value["lead_market"] == "BTCUSD"
    pack["morning_map_sources"]["rows"].pop("XAUUSD")
    assert wrap_copy.morning_map(pack, datetime(2026, 11, 30).date()) is None


def test_the_daily_note_table_needs_the_nasdaq_row_from_26_nov():
    table = "| Market | Move |\n| --- | ---: |\n" + "\n".join(
        f"| {name} | +0.1% |" for name in ("Gold", "S&P 500", "EUR/USD", "USD/JPY", "WTI", "Bitcoin"))
    body = "We think rates lead.\n\n" + table + "\n\nSo what: watch yields."
    assert reader._daily_prose(body, "2026-11-25T12:00:00Z")[1] == []
    assert reader._daily_prose(body, "2026-11-26T12:00:00Z")[1] == ["DAILY_SIX_MARKET_TABLE_REQUIRED"]
    seven = body.replace("| Bitcoin | +0.1% |", "| Bitcoin | +0.1% |\n| Nasdaq 100 | Unavailable |")
    assert reader._daily_prose(seven, "2026-11-26T12:00:00Z")[1] == []


def test_a_nasdaq_article_names_a_futures_or_etf_instrument_like_the_six():
    article = {"public_instrument_policy": instruments.POLICY, "title": "Nasdaq 100 slips",
               "substack_body_markdown": "We think the Nasdaq 100 slips as yields climb."}
    with pytest.raises(ValueError, match="PUBLIC_FUTURES_OR_ETF_REQUIRED:USTEC"):
        instruments.validate_article(article)
    article["substack_body_markdown"] += " NQ futures and QQQ lead."
    instruments.validate_article(article)


def test_scenarios_carry_a_nasdaq_implication_when_main_gives_one_and_six_stay_valid():
    def scenario_set(markets):
        doc = {"document_id": "main", "publisher": "Capital Chronicle", "canonical_content_text": ""}
        out = []
        for role, name, chance in (("base_case", "Soft landing", "55%"), ("alternative", "Sticky prices", "45%")):
            moves = {m: f"{m} reacts to {name}" for m in markets}
            fields = {"probability": chance, "confirmation": f"{name} confirmed", "invalidation": f"{name} fails",
                      **{"market_moves." + m: v for m, v in moves.items()}}
            doc["canonical_content_text"] += " ".join(f"[{v}]" for v in fields.values()) + " "
            out.append({"name": name, "role": role, "probability": chance, "confirmation": fields["confirmation"],
                        "invalidation": fields["invalidation"], "market_moves": moves,
                        "source_bindings": {k: {"document_id": "main", "support_excerpt": f"[{v}]"}
                                            for k, v in fields.items()}})
        visible = "\n".join(f"{s['name']} {s['probability']} {scenarios.MODEL_LABEL} {s['confirmation']} "
                            f"{s['invalidation']} " + " ".join(s["market_moves"].values()) for s in out)
        article = {"scenario_analysis": out, "substack_body_markdown": "## Scenarios\n" + visible + "\n"
                   + scenarios.PUBLIC_NOTICE + " " + scenarios.CONFLICTS_NOTICE,
                   "social_scenarios": {"base_case": "Base case: 55% soft landing.",
                                        "alternative": "Alternative: 45% sticky prices."}}
        return article, [doc]
    for markets in (SIX, CORE):
        scenarios.validate_article_scenarios(*scenario_set(markets))
    with pytest.raises(ValueError, match="SCENARIO_SIX_MARKETS_REQUIRED"):
        scenarios.validate_article_scenarios(*scenario_set(SIX[:5]))


def test_the_event_reaction_page_shows_held_nasdaq_rows_and_never_infers_one():
    window = {"move_bps": 12.5, "endpoint_utc": "2026-11-06T13:31:00Z"}
    table = {"as_of_utc": "2026-11-07T00:00:00Z",
             "events": [{"event_id": "nfp-nov", "event_date": "2026-11-06"}],
             "rows": [{"family": "NFP", "symbol": "USTEC", "event_id": "nfp-nov", "released_at_utc": "2026-11-06T13:30:00Z",
                       "series_id": "mt5_demo_capture:USTEC", "windows": {h: dict(window) for h in reactions.HORIZONS}}]}
    projected = reactions.project(table, "NFP")
    assert "## Payrolls: Nasdaq 100" in projected["body_markdown"]
    assert "Capital Chronicle broker-price proxy for Nasdaq 100" in projected["body_markdown"]
    assert reactions.project({**table, "rows": []}, "NFP")["market_rows"] == 0
