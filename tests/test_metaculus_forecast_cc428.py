from copy import deepcopy
import gzip
import json
import socket

import pytest

from live_contentops.metaculus_forecast_v1 import (
    ENDPOINT, compile_round, digest, event_forecasts, normalize_posts, plan_forecasts,
)
from scripts.run_metaculus_dry_run import main


NOW = "2026-11-11T10:00:00Z"
CONTRACT = {"instrument": "BTCUSD:EXAMPLE_RESOLVER", "measure": "TERMINAL_PRICE",
    "unit": "USD", "horizon_start_utc": "2026-11-10T00:00:00Z",
    "horizon_end_utc": "2026-11-12T00:00:00Z", "resolution_source": "FIXTURE_PUBLIC_PRICE_RESOLVER",
    "conditioning": {}, "predicate": {"operator": ">=", "threshold": 85000}}


def question():
    return {"post_id": 500, "question_id": 901, "title": "Fixture Bitcoin threshold question",
        "type": "binary", "open_at_utc": "2026-11-10T10:00:00Z", "close_at_utc": "2026-11-11T11:00:00Z",
        "desk_topics": ["BTCUSD"], "contract": deepcopy(CONTRACT)}


def forecast():
    return {"forecast_id": "fixture-main-btc", "assets": ["BTCUSD"], "format": "binary",
        "probability_yes": 0.63, "available_at_utc": "2026-11-11T09:00:00Z",
        "contract": deepcopy(CONTRACT), "public_model_estimate": True,
        "public_explanation": "Capital Chronicle's uncalibrated model estimates a 63% chance for this exact threshold and deadline.",
        "source": {"path": "fixture-main-public.json", "sha256": "a" * 64, "pointer": "/probability"}}


def run(q=None, f=None, *, replay=False):
    return compile_round({"round_id": "fixture-round", "questions": [q or question()]},
        [{"forecasts": [f or forecast()]}], as_of_utc=NOW, replay=replay)


def test_exact_main_number_is_used_in_atomic_request_with_distinct_ids():
    result = run()
    request = result["prepared_requests"][0]
    assert request["url"] == ENDPOINT
    assert request["json"]["forecasts"] == [{"question": 901, "probability_yes": 0.63}]
    comment = request["json"]["comments"][0]
    assert comment["on_post"] == 500 and comment["included_forecast"] and comment["is_private"]
    assert "63%" in comment["text"] and "not financial advice" in comment["text"]
    assert result["submission_count"] == result["network_call_count"] == 0
    assert result["external_score"] is result["external_rank"] is None


@pytest.mark.parametrize("key,value", [
    ("instrument", "BTCUSD:ANOTHER_EXCHANGE"), ("unit", "EUR"),
    ("horizon_end_utc", "2026-11-13T00:00:00Z"), ("horizon_start_utc", "2026-11-11T00:00:00Z"),
    ("measure", "TOUCH_PRICE"), ("resolution_source", "ANOTHER_RESOLVER"),
    ("conditioning", {"after_entry": True}), ("predicate", {"operator": ">", "threshold": 85000}),
])
def test_nearby_proposition_never_reuses_probability(key, value):
    q = question(); q["contract"][key] = value
    result = run(q=q)
    assert not result["prepared_requests"]
    assert result["answers"][0]["first_cause"] == "NO_EXACT_MAIN_TARGET_INSTRUMENT_HORIZON_RESOLVER"
    assert result["answers"][0]["candidate_forecast_ids"] == ["fixture-main-btc"]


def test_closed_round_replay_does_not_backdate_an_input_version():
    q = question(); q["close_at_utc"] = "2026-11-11T08:00:00Z"
    result = run(q=q, replay=True)
    assert result["first_causes"] == {"MAIN_VERSION_AVAILABLE_AFTER_FORECAST_DEADLINE": 1}
    f = forecast(); f["available_at_utc"] = "2026-11-11T07:00:00Z"
    assert run(q=q, f=f, replay=True)["answers"][0]["state"] == "MATCHED_REPLAY"
    assert run(q=q, f=f)["first_causes"] == {"QUESTION_NOT_OPEN": 1}


def test_incomplete_or_hidden_metadata_and_post_id_do_not_become_question_id():
    q = question(); q["question_id"] = None
    assert run(q=q)["first_causes"] == {"PLATFORM_QUESTION_ID_UNAVAILABLE": 1}
    q["contract"] = None
    assert run(q=q)["first_causes"] == {"PLATFORM_FULL_RESOLUTION_CONTRACT_UNAVAILABLE": 1}


def test_numeric_source_cdf_is_carried_exactly_and_never_fitted_from_point_estimate():
    q = question(); q.update(type="numeric", scaling={"range_min": 0, "range_max": 100, "zero_point": None})
    f = forecast(); f.update(format="continuous", scaling=deepcopy(q["scaling"]),
                             continuous_cdf=[i / 200 for i in range(201)])
    assert run(q=q, f=f)["prepared_requests"][0]["json"]["forecasts"][0]["continuous_cdf"] == f["continuous_cdf"]
    assert run(q=q)["first_causes"] == {"MAIN_DISTRIBUTION_DOES_NOT_MATCH_QUESTION_TYPE": 1}
    f["continuous_cdf"][100] = 0.1
    assert run(q=q, f=f)["first_causes"] == {"MAIN_CDF_INVALID": 1}
    f["scaling"]["range_min"] = -1
    assert run(q=q, f=f)["first_causes"] == {"NUMERIC_SCALE_MISMATCH_OR_UNAVAILABLE": 1}


def test_option_probabilities_preserve_the_complete_source_set():
    q = question(); q.update(type="multiple_choice", options=["a", "b"])
    f = forecast(); f.update(format="multiple_choice", probability_yes_per_category={"a": 0.6, "b": 0.4})
    assert run(q=q, f=f)["matched_count"] == 1
    del f["probability_yes_per_category"]["b"]
    assert run(q=q, f=f)["first_causes"] == {"MAIN_OPTION_DISTRIBUTION_INVALID": 1}


def test_conflicting_source_versions_and_duplicate_questions_are_not_resubmissions():
    f = forecast(); other = {**f, "probability_yes": 0.7}
    args = {"round_input": {"round_id": "fixture", "questions": [question()]},
        "inventories": [{"forecasts": [f, other]}], "as_of_utc": NOW, "replay": False}
    assert compile_round(**args)["first_causes"] == {"AMBIGUOUS_EXACT_MAIN_FORECAST": 1}
    args["round_input"]["questions"].append(question())
    with pytest.raises(ValueError, match="DUPLICATE_PLATFORM_QUESTION"):
        compile_round(**args)


@pytest.mark.parametrize("text,cause", [
    ("Account login 279779602", "MAIN_EXPLANATION_CONTAINS_PRIVATE_OR_RESTRICTED_CONTENT"),
    ("See https://capital-chronicle-preview.pages.dev/", "PREVIEW_HOST_LINK_FORBIDDEN"),
    ("The deadline is 12:00 GMT+7.", "PUBLIC_TIMEZONE_ET_REQUIRED"),
])
def test_prepared_public_comment_uses_existing_public_guards(text, cause):
    f = forecast(); f["public_explanation"] = text
    assert run(f=f)["first_causes"] == {cause: 1}


def test_named_public_rights_restriction_keeps_numbers_in_internal_matching():
    f = forecast(); f.update(public_model_estimate=False, public_restriction="PUBLIC_REDISTRIBUTION_NOT_LICENSED")
    result = run(f=f)
    assert result["first_causes"] == {"PUBLIC_REDISTRIBUTION_NOT_LICENSED": 1}
    assert result["inventory"][0]["forecasts"][0]["probability_yes"] == 0.63


def test_api_group_children_are_not_collapsed_to_post_or_filled_from_hidden_values():
    rows = normalize_posts([{"id": 50, "group_of_questions": {"questions": [
        {"id": 700, "type": "numeric", "scaling": None}, {"id": 701, "type": "numeric"}]}}])
    assert [r["question_id"] for r in rows] == [700, 701]
    assert {r["post_id"] for r in rows} == {50}
    assert rows[0]["scaling"] is rows[0]["resolution_criteria"] is None


def public_plan(path):
    doc = {"schema": "CapitalChroniclePlanStatusV1", "generated_at_utc": NOW, "plans": [{
        "asset_id": "BTCUSD", "plan_id": "fixture-btc", "registered_at_utc": "2026-11-01T00:00:00Z",
        "forecast_probabilities": {"probability_up_pct": 46, "probability_touch_pct": 48,
            "probability_target_before_stop_pct": 38, "probability_basis": "UNCALIBRATED_HYBRID_JUDGMENT",
            "reference_price": 73539.18, "horizon_end_utc": "2026-12-02T02:07:07Z"},
        "private_sentinel": "MUST_NOT_LEAK"}]}
    doc["content_hash"] = digest(doc)
    raw = json.dumps(doc).encode()
    path.write_bytes(gzip.compress(raw) if str(path).endswith(".gz") else raw)
    return doc


def test_public_plan_consumer_preserves_three_distinct_numbers_and_original_clocks(tmp_path):
    path = tmp_path / "plan.public.json.gz"; public_plan(path)
    result = plan_forecasts(path)
    assert [r["probability_yes"] for r in result["forecasts"]] == [0.46, 0.48, 0.38]
    assert [r["source_value"] for r in result["forecasts"]] == [46, 48, 38]
    assert all(r["available_at_utc"] == NOW and r["contract"]["resolution_source"] is None for r in result["forecasts"])
    assert result["forecasts"][0]["contract"]["predicate"] == {"operator": ">", "threshold": 73539.18}
    assert "MUST_NOT_LEAK" not in json.dumps(result)


def test_actual_cli_consumes_main_output_and_remains_network_free(tmp_path, monkeypatch, capsys):
    def fail(*args, **kwargs):
        pytest.fail("dry run attempted a network connection")
    monkeypatch.setattr(socket.socket, "connect", fail)
    plan = tmp_path / "plan.public.json"; public_plan(plan)
    questions = tmp_path / "questions.json"; questions.write_text(json.dumps({"round_id": "fixture", "questions": [question()]}))
    output = tmp_path / "result.json"
    assert main(["--questions", str(questions), "--plan-export", str(plan), "--output", str(output)]) == 0
    assert json.loads(capsys.readouterr().out)["network_call_count"] == 0
    result = json.loads(output.read_bytes())
    assert result["inventory"][0]["forecasts"][0]["source_value"] == 46
    assert result["question_count"] == result["abstained_count"] == 1


def test_event_matrix_projection_uses_own_estimates_and_omits_raw_inputs(tmp_path):
    path = tmp_path / "matrix.json"
    path.write_text(json.dumps({"target": {"event_id": "fixture-cpi", "event_type": "US_CPI"}, "matrices": [{
        "target": {"event_type": "US_CPI"}, "bands": {"actual_boundaries": [0.1, 0.2]},
        "branches": [{"branch": "IN_LINE", "probability": 0.7}], "cutoff_utc": "2026-11-10T10:00:00Z",
        "probability_scope": "CONDITIONAL_ON_COVERED_SCALAR_FIRST_PRINT_SURPRISE",
        "public_probabilities_eligible": True, "sources": {"raw_consensus": "NEVER_EXPORT"}}]}))
    result = event_forecasts(path, observed_at_utc=NOW)
    assert result["forecasts"][0]["probabilities"] == {"IN_LINE": 0.7}
    assert result["forecasts"][0]["available_at_utc"] == NOW
    assert result["forecasts"][0]["data_cutoff_utc"] == "2026-11-10T10:00:00Z"
    assert "NEVER_EXPORT" not in json.dumps(result)
