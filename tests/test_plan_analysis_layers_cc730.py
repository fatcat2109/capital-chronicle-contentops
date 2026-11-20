from copy import deepcopy
import json

import pytest

from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_reader_editorial_v1 as editorial


def frozen_layers():
    exported = {
        "macro": "Real yields rose after the data release.",
        "event_and_cause": "The inflation release lifted Treasury yields and put pressure on metals.",
        "fundamental": "Physical demand slowed in Asia.",
        "positioning_and_sentiment": "Long positions are crowded after a week of inflows.",
        "options_and_gamma": "Dealer gamma turns positive above the nearest strike.",
        "cross_asset_and_contagion": "A stronger dollar would transmit the move to emerging markets.",
        "technical": "Price failed to recover last week's range.",
    }
    return {
        "layers": [{"layer": name, "state": "USED", "text": text, "first_cause": None}
                   for name, text in exported.items()],
        "scenario_analysis": {
            "priced": "Gold already reflects some of the rise in yields.",
            "base_case": {"probability_pct": 57, "market_move": "Real yields stay firm."},
            "main_alternative": {"probability_pct": 31, "market_move": "A softer dollar eases pressure on metals."},
        },
    }


def test_ordered_export_has_nine_layers_and_preserves_both_explicit_chances():
    plan = frozen_layers()
    _, gaps = reader.plan_layer_candidates(plan)
    quotes = editorial.prepare_plan_layers(plan, contract=reader.NINE_LAYER_COPY)
    lines = reader.verified_analysis_lines(plan, quotes, contract=reader.NINE_LAYER_COPY)
    assert not gaps
    assert [line.split(":", 1)[0] for line in lines] == [label for _, label in reader.PLAN_LAYER_ORDER]
    assert lines[-1] == "Scenarios: Main (57%): Real yields stay firm. Alternative (31%): A softer dollar eases pressure on metals."
    del plan["scenario_analysis"]["main_alternative"]["probability_pct"]
    lines = reader.verified_analysis_lines(plan, quotes, contract=reader.NINE_LAYER_COPY)
    assert "Alternative: A softer dollar" in lines[-1]
    assert "43%" not in lines[-1]


def test_three_gaps_distinguish_absence_and_the_exporters_cause():
    plan = frozen_layers()
    plan["layers"] = [row for row in plan["layers"] if row["layer"] != "event_and_cause"]
    gamma = next(row for row in plan["layers"] if row["layer"] == "options_and_gamma")
    gamma.update(state="UNAVAILABLE", text=None, first_cause="GAMMA_SNAPSHOT_STALE")
    plan["analysis_layers"] = {"options_and_gamma": {"state": "USED", "text": "A prior gamma reading was positive."}}
    del plan["scenario_analysis"]["priced"]
    _, gaps = reader.plan_layer_candidates(plan)
    assert gaps == {"event_and_cause": "EXPORT_FIELD_ABSENT", "priced_in": "EXPORT_FIELD_ABSENT",
                    "options_gamma": "GAMMA_SNAPSHOT_STALE"}
    quotes = editorial.prepare_plan_layers(plan, contract=reader.NINE_LAYER_COPY)
    assert len(reader.verified_analysis_lines(plan, quotes, contract=reader.NINE_LAYER_COPY)) == 6


def test_antigravity_rewrites_only_verified_source_notation_and_falls_back_per_line(tmp_path):
    plan = frozen_layers()
    plan["time_exit_utc"] = "2026-11-21T20:00:00Z"
    plan["layers"][0]["text"] = "CC-730: Treasury yields rose 5 basis points while channel MIXED."
    plan["scenario_analysis"]["main_alternative"]["market_move"] = (
        "Gold could recover at 20:00Z after the jim_weekly_minimum_20261117 starter."
    )
    expected = "Treasury yields rose 5 basis points while signals are mixed."
    seen = []

    def draft(prompt, **kwargs):
        assert kwargs["callers"] == ("antigravity",)
        options = json.loads(prompt.split("\n", 1)[1])
        assert options["macro"][0] == {"quote": plan["layers"][0]["text"], "text": expected}
        seen.append(kwargs["job"])
        answer = {key: "0" for key in options}
        answer["macro"] = expected
        answer["main_alternative"] = "Gold could recover at 2:00 PM ET after the initial entry."
        return json.dumps(answer).encode(), {"status": "RETURNED"}

    quotes = editorial.prepare_plan_layers(plan, output_dir=tmp_path, call=draft, contract=reader.NINE_LAYER_COPY)
    assert seen == ["plan_layer_lines"]
    assert quotes["macro"] == expected
    assert quotes["main_alternative"] == "Gold could recover at Sat 21 Nov, 3:00 PM ET after the initial entry."
    assert editorial.prepare_plan_layers(plan, output_dir=tmp_path, call=draft, contract=reader.NINE_LAYER_COPY) == quotes
    assert len(seen) == 1
    receipt = json.loads(next(tmp_path.glob("*/light-call.json")).read_bytes())
    assert receipt["findings"] == {"main_alternative": "CC688_LAYER_NOT_QUOTED_FROM_PLAN:main_alternative"}
    tampered = {**quotes, "macro": expected.replace("rose 5", "fell 6")}
    with pytest.raises(ValueError, match="CC688_LAYER_NOT_QUOTED_FROM_PLAN:macro"):
        reader.verified_analysis_lines(deepcopy(plan), tampered, contract=reader.NINE_LAYER_COPY)
