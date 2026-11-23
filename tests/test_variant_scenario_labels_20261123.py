"""Decision 158 in the social-variant prompt: Base case, Bull case and Bear case lines with odds and causes.

plan_reader_copy_v1.validate_fields accepts these labels beside the earlier Main/Alternative ones
(Builder B, live at 29a9cd82); variants stored with Main/Alternative keep their bytes.
"""
import json

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_analysis_pages_cc432 import source  # noqa: F401


@pytest.mark.parametrize("direction,scenario,label", [
    ("BEARISH", {"base_case": {"market_move": "lower", "probability_pct": 55},
                 "main_alternative": {"market_move": "higher", "probability_pct": 45}}, "Bull case"),
    ("BULLISH", {"base_case": {"market_move": "higher", "probability_pct": 60},
                 "main_alternative": {"market_move": "lower", "probability_pct": 40}}, "Bear case"),
    ("BULLISH", {"base_case": {"market_move": "higher", "probability_pct": 60},
                 "bear_case": {"market_move": "lower", "probability_pct": 40}}, "Bear case"),
    ("BEARISH", {"base_case": {"market_move": "lower", "probability_pct": 55}},
     "Bull case or Bear case (the side it argues)"),
])
def test_the_alternative_label_follows_the_plans_own_scenarios(direction, scenario, label):
    assert editorial.variant_alternative_label({"direction": direction, "scenario_analysis": scenario}) == label


def test_variant_prompt_asks_for_base_and_bull_cases_and_the_labelled_variant_validates(source, tmp_path):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from test_plan_analysis_distribution_cc435 import confirm
    root, folder, plan, manuscript = source
    result = {"native_synthesis": {"candidates": [{"candidate_id": "cand_macro_eurusd",
              "rationale": "Dollar strength supports the view. Probability: 55% lower at the exit."}]}}
    plan.update(direction="BEARISH", analysis_result_hash=sha256_of(result),
                scenario_analysis={"base_case": {"probability_pct": None},
                                   "main_alternative": {"market_move": "the euro recovers on softer US data.",
                                                        "probability_pct": None}})
    for name in ("owner-native.json", "desktop-manual-result.json"):
        (folder / name).write_text(json.dumps(result), encoding="utf-8")
    freeze = json.loads((folder / "final-decision-freeze.json").read_bytes())
    freeze["qualitative_result_hash"] = plan["analysis_result_hash"]
    (folder / "final-decision-freeze.json").write_text(json.dumps(freeze), encoding="utf-8")
    run = pages.load_run(plan, run_root=root)
    current = reader.source_packet(plan, run, original_probabilities=True)
    rationale = "Dollar strength supports the view. Probability: 55% lower at the exit."
    manuscript["sections"] = {key: {"paragraphs": [{"text": rationale,
        "refs": [{"file": "owner-native.json", "pointer": "/native_synthesis/candidates/0/rationale"}],
        "rights": "CAPITAL_CHRONICLE_ORIGINAL_ANALYSIS", "source_name": "Capital Chronicle"}],
        "summary": "Dollar strength supports the view."} for key, _ in pages.SECTIONS}
    store = ContentOpsDurableStore(tmp_path / "labels.sqlite3")
    packet = pages.register_page(store, pages.render(plan, manuscript, run_root=root, output_dir=tmp_path / "page"))
    confirm(store, packet["page_id"], packet["plan"]["plan_hash"], "substack", "123",
            "https://capitalchronicle.substack.com/p/scenario-labels")
    row = {"kind": "setup", "symbol": "EURUSD", "instrument_title": "EUR/USD", "source_plan": plan,
           "source_plan_registration": plan["registration_hash"], "levels": {"zone_low": 1.12, "zone_high": 1.13,
           "invalidation_level": 1.15, "direction": "bearish", "valid_until_utc": "2026-11-13T13:15:00Z"}}
    sid = current["original_probability_binding"]["source_id"]

    def field(text):
        return {"text": text, "source_ids": [sid]}

    fields = {"hook": field("Dollar strength supports the view."),
              "points": [{"layer": "macro", **field("The dollar supports the view.")}],
              "scenario_main": field("Base case (55%): the euro is lower at the exit on dollar strength."),
              "scenario_alt": None, "alt_text": field("The chart shows the original plan.")}
    prompts = []

    def call(prompt, **kwargs):
        prompts.append(prompt)
        return {"status": "RETURNED", "output": fields}

    prepared = editorial.prepare_variants(packet, row, output_dir=tmp_path / "variants", call=call)
    assert prepared["status"] == "PREPARED", prepared
    prompt = prompts[0]
    assert "scenario_main must start Base case (odds%): and say what drives it." in prompt
    assert "scenario_alt must start Bull case (odds%): and say what drives it." in prompt
    assert "Main must start Main" not in prompt and '"Main (50%)' not in prompt
    assert prepared["reader_fields"]["scenario_main"]["text"].startswith("Base case (55%): ")
