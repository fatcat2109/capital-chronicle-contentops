from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path

import pytest

from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import scenario_voice_v1 as voice
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


def scenario_plan():
    return {
        "direction": "BEARISH",
        "layers": {
            "macro": "Real yields rose after the release.",
            "fundamental": "Physical demand slowed.",
            "positioning_and_sentiment": "Positioning remains crowded.",
            "priced_in": "The rate path is partly priced in.",
        },
        "scenario_analysis": {
            "mechanism": "Higher real yields raise the opportunity cost of holding gold.",
            "invalidation_text": "A close above the broken shelf would reverse the case.",
            "base_case": {"probability_pct": 58, "market_move": "Gold extends the breakdown."},
            "main_alternative": {"market_move": "Gold rebounds through the shelf.",
                                 "invalidation": "Renewed selling below the range would end the rebound."},
        },
    }


def test_direction_maps_main_alternative_to_bull_case_without_complement():
    plan = scenario_plan()
    cases = reader.scenario_case_copy(plan)
    assert cases[0]["heading"] == "Base case (58%): Gold extends the breakdown."
    assert cases[1]["heading"] == "Bull case: Gold rebounds through the shelf."
    assert "Higher real yields" in cases[0]["support"][0]
    assert "Renewed selling" in cases[1]["support"][0]
    lines = str(cases)
    assert "42%" not in lines
    assert "Bear case" not in lines


def test_named_branches_keep_their_own_chances_and_take_precedence():
    plan = scenario_plan()
    plan["scenario_analysis"].update(
        bull_case={"probability_pct": 12.5, "market_move": "A weaker dollar supports a rebound."},
        bear_case={"probability_pct": 9, "market_move": "Gold drops if yields rise again."},
    )
    cases = reader.scenario_case_copy(plan)
    assert [case["heading"].split(":", 1)[0] for case in cases] == [
        "Base case (58%)", "Bull case (12.5%)", "Bear case (9%)",
    ]


def test_target_is_hard_and_position_words_are_flagged():
    assert not voice.validate_copy("Short-term positioning is crowded. Gold could move toward 3,900 if yields fall.")
    assert not voice.validate_copy("The Fed kept its inflation target of 2%.")
    with pytest.raises(ValueError, match="TARGET_FORBIDDEN"):
        voice.validate_copy("Base case (58%): Gold weakens. Target level: 3,900.")
    assert voice.validate_copy("Long positions buy the breakout and sell the dip.") == ["SCENARIO_VOICE_POSITION_WORDS"]
    assert voice.validate_copy("Positioning remains long.") == []


def test_thin_export_is_an_editorial_finding_and_remains_usable():
    assert voice.validate_copy("Macro: Real yields rose.", plan=True) == [
        "SCENARIO_VOICE_CASES", "SCENARIO_VOICE_FORCE_WEIGHT",
    ]


def test_minute_queue_and_three_platforms_use_the_new_voice(tmp_path, monkeypatch):
    fixture = Path(__file__).parents[1] / "docs/publisher/CC-543/fixtures/gold-plan-20261112.json"
    raw = json.loads(fixture.read_bytes())
    now = posts._utc(raw["registered_at_utc"]) + timedelta(minutes=1)
    store = ContentOpsDurableStore(tmp_path / "plan-posts.sqlite3")
    monkeypatch.setattr(cards, "NO_TARGET_EFFECTIVE", now)
    source = scenario_plan()
    # Current Main emits base and main_alternative. Named branches are checked above.
    source["scenario_analysis"]["main_alternative"].pop("invalidation")
    raw.update(source)
    raw["target"] = 3900
    status = {"schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0", "content_hash": "a" * 64,
              "generated_at_utc": now.isoformat(), "plans": [raw]}
    transitions = {"schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
                   "generated_at_utc": now.isoformat(), "status_content_hash": status["content_hash"],
                   "transitions": [{"plan_id": raw["plan_id"], "status": "WAITING", "reason_code": "WAITING",
                                    "at_utc": raw["registered_at_utc"]}]}
    monkeypatch.setattr(posts, "read_export", lambda *_args, **_kwargs: {
        "status": status, "transitions": transitions,
    })
    result = posts.queue_posts(store, tmp_path, now=now)
    assert result["status"] == "OK", result
    outbox, = store.list_outbox_messages(destination=posts.DESTINATION)
    row = json.loads(outbox["payload"])
    assert row["scenario_voice"] == voice.CONTRACT
    assert row["scenario_voice_findings"] == []
    assert row["text"].startswith("Scenarios: Base case (58%)")
    assert "3,954" in row["text"] and "3,972.6" in row["text"]
    alerts.validate(row, store=store)
    copies = cards.destination_payloads(row, card_id="chart", chart_credit=True)
    for destination in ("telegram", "discord", "threads"):
        text = copies[destination]["full_text"]
        assert "Base case (58%)" in text and "Bull case" in text
        assert "Macro:" in text and "Fundamentals:" in text and "Priced in:" in text
        assert "3900" not in text and "3,900" not in text
        assert voice.validate_copy(text, plan=True) == []
    changed = deepcopy(row)
    changed["text"] += "\nTarget level: 3,900."
    with pytest.raises(ValueError, match="PLAN_ALERT_SOURCE_COPY_CHANGED"):
        alerts.validate(changed, store=store)
