"""Ops Product interim, 20 Nov 2026: a new plan's first post quotes the analyst's own scenario text."""
import sys

from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_scenario_lines_v1 as scenario_lines
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from test_plan_call_cards_cc399 import controlled_tradingview, write, rows  # noqa: F401
from test_plan_status_posts_cc306 import main_root, event  # noqa: F401
from test_plan_state_alerts_cc543 import replay  # noqa: F401

# USD/JPY, registered 20 Nov 2026 08:14Z: the export's own fields, as Main wrote them.
USDJPY = {"plan_id": "plan_usdjpy_fixture", "asset_id": "USDJPY", "scenario_analysis": {
    "mechanism": "risk-off repatriation, BoJ hike expectations and MoF warnings near 160 force carry longs out "
                 "below the 17 Nov low 158.868",
    "driver": "risk-off against the rate gap, channel MIXED.",
    "priced": "Fed hike 100%; BoJ 58% held (19 Nov), higher per an unconfirmed digest.",
    "positioning": "carry longs added 11-19 Nov; their stops sit under 158.87.",
    "confirmations": "an M15 close below 158.90.",
    "base_case": {"market_move": "USDJPY is below 159.114 at 2026-11-23T06:00Z, and a break of the 158.87-159.03 "
                                 "shelf runs toward lower levels.", "probability_pct": 55.0},
    "main_alternative": {"market_move": "USDJPY holds the 159 handle on carry demand and returns toward 159.6 after "
                                        "Waller.", "probability_pct": 45.0}}}

# Gold, registered 20 Nov 2026 05:33Z: every field carries an internal token, so nothing is shown.
GOLD = {"plan_id": "plan_gold_fixture", "asset_id": "XAUUSD", "scenario_analysis": {
    "mechanism": "causal_reasoning cand_macro_gold.",
    "driver": "real yields, channel CLEAR; dollar channel MIXED.",
    "priced": "a 100% December Fed hike, US real 10Y 2.88% (2026-11-19), a 15% fall since 9 Nov; 76% market odds "
              "for a 3,500 touch.",
    "positioning": "COT not observed; the prior gold short closed and the XAUUSD:SHORT slot reads UNKNOWN.",
    "base_case": {"market_move": "GOLD trades below 3523.277 at 20:00Z as real-yield liquidation keeps lower highs "
                                 "under 3556; jim_weekly_minimum_20261117 starter.", "probability_pct": 54.0},
    "main_alternative": {"market_move": "gold rebounds toward 3580-3610 into the weekend as forced selling ends.",
                         "probability_pct": 46.0}}}


def test_usdjpy_lines_quote_the_analyst_with_et_times_and_odds():
    lines = scenario_lines.analysis_lines(USDJPY)
    assert lines == [
        "Macro: Risk-off repatriation, BoJ hike expectations and MoF warnings near 160 force carry longs out below "
        "the 17 Nov low 158.868.",
        "Positioning: Carry longs added 11-19 Nov; their stops sit under 158.87.",
        "Main (55%): USDJPY is below 159.114 at Mon 23 Nov, 1:00 AM ET, and a break of the 158.87-159.03 shelf "
        "runs toward lower levels.",
        "Alternative (45%): USDJPY holds the 159 handle on carry demand and returns toward 159.6 after Waller.",
    ]


def test_internal_tokens_utc_clocks_and_market_odds_are_left_out():
    assert scenario_lines.analysis_lines(GOLD) == []
    # An alternative is never shown without its main case.
    only_alt = {"scenario_analysis": {"main_alternative": GOLD["scenario_analysis"]["main_alternative"],
                                      "base_case": GOLD["scenario_analysis"]["base_case"]}}
    assert scenario_lines.analysis_lines(only_alt) == []
    assert scenario_lines.analysis_lines({"scenario_analysis": None}) == []
    assert scenario_lines.analysis_lines({}) == []


def test_bullish_words_and_first_person_are_left_out():
    raw = {"scenario_analysis": {"mechanism": "we are bearish because real yields rise.",
                                 "positioning": "I think longs are trapped above 3832.",
                                 "priced": "December fully priced; gold is 9.2% under its 50-session mean."}}
    assert scenario_lines.analysis_lines(raw) == [
        "Priced in: December fully priced; gold is 9.2% under its 50-session mean."]


def test_queued_interim_alert_keeps_its_bytes_and_new_alerts_drop_interim_contract(replay, main_root, monkeypatch):
    store, folder, raw, now = replay
    macro = "Real yields rise as the hike is priced."
    interim_lines = ["Macro: " + macro, "Main (60%): Gold trades lower into the exit."]
    raw["analysis_layers"] = {"macro": {"state": "USED", "text": macro, "first_cause": None}}
    write(folder, [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
          generated_at_utc=now.isoformat())
    monkeypatch.setattr(scenario_lines, "EFFECTIVE", now)
    monkeypatch.setattr(scenario_lines, "analysis_lines", lambda plan: interim_lines)
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    assert queued["status"] == "OK", queued
    current, = rows(store)
    assert current["analysis_copy_contract"] == "CC730_V1"
    assert "analysis_lines_contract" not in current
    assert current["text"].startswith(interim_lines[0] + "\n")
    assert current["text"].count(interim_lines[0]) == 1
    assert interim_lines[1] not in current["text"]
    alerts.validate(current, store=store)

    interim = {key: value for key, value in current.items() if not key.startswith("analysis_")}
    interim["analysis_lines_contract"] = scenario_lines.CONTRACT
    frozen = alerts.compose({key: value for key, value in interim.items() if key != "analysis_lines_contract"})["text"]
    interim["text"] = frozen.replace("\nRegistered ", "\n" + "\n".join(interim_lines) + "\nRegistered ", 1)
    assert interim["text"] != frozen
    alerts.validate(interim, store=store)
    interim["detail_lines"] = alerts.compose(interim)["detail_lines"]
    payloads = cards.destination_payloads(interim, card_id="card-fixture", complete_levels=True)
    assert payloads and all(p["text"] for p in payloads.values())
