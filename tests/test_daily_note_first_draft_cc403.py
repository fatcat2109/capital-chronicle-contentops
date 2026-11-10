"""Controlled text outputs and failures through the native daily-note request owner."""
from copy import deepcopy
import json
import subprocess
from types import SimpleNamespace

import pytest

from live_contentops import daily_note_first_draft_v1 as draft
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.codex_desktop_newsroom_operator_v1 import native_role_call
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
from live_contentops.reader_article_contract_v1 import GUIDANCE, contract_for
from live_contentops.v1_simple_gemini_newsroom_v1 import ARTICLE_SCHEMA_VERSION
from test_reader_article_contract_cc403 import daily


def output():
    article, documents = daily()
    article.pop("reader_article_contract")
    fields = ("title", "dek", "search_title", "meta_description", "social_hook")
    claims = [{"claim_id": field, "claim_text": article[field], "claim_kind": "FACT", "source_id": "SOURCE_1",
               "support_excerpt": article[field], "attribution_required": True} for field in fields]
    for i, paragraph in enumerate(article["substack_body_markdown"].split("\n\n")):
        if paragraph.startswith("#"):
            continue
        claims.append({"claim_id": "p" + str(i), "claim_text": paragraph, "claim_kind": "FACT",
                       "source_id": "SOURCE_1", "support_excerpt": paragraph, "attribution_required": True})
    return {"schema_version": ARTICLE_SCHEMA_VERSION, "article": article,
            "cited_sources": [{k: documents[0][k] for k in ("source_id", "url", "publisher", "published_at_utc")}],
            "material_claim_bindings": claims, "public_write_attempted": False}


def governed():
    _, docs = daily()
    value = {"selected_candidate": {"reader_format": "DAILY_NOTE"}, "source_pack": docs,
             "article_mode": "DATA_OR_DOCUMENT_LENS"}
    value["reader_article_contract"] = contract_for(value)
    return value


@pytest.mark.parametrize("failure", [None, "empty", "timeout", "exit", "bad_number"])
def test_controlled_text_call_is_bounded_and_checks_the_draft_before_editing(tmp_path, failure):
    calls = []
    value = output()
    if failure == "bad_number":
        value["article"]["substack_body_markdown"] += "\n\nThe yield was 99.9%. [[SOURCE:SOURCE_1]]"

    def runner(args, *, cwd, timeout, input=None):
        calls.append(args)
        assert not list(__import__("pathlib").Path(cwd).iterdir())
        if args[-1] == "--version":
            return SimpleNamespace(stdout=b"agy 1.5.3", stderr=b"", returncode=0)
        assert timeout == 120 and "--input-format" in args
        assert args[args.index("--model") + 1] == "gemini-3.8-flash-high"
        assert args[args.index("--effort") + 1] == "high"
        assert json.loads(input)["message"]["content"][0]["text"].startswith("Do not call any tool")
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args, 120)
        raw = b"" if failure == "empty" else json.dumps({"event": "result", "result": {
            "status": "SUCCESS", "response": json.dumps(value)}}).encode()
        return SimpleNamespace(stdout=raw, stderr=b"", returncode=7 if failure == "exit" else 0)

    record = draft.prepare_first_draft(governed(), GUIDANCE, output_dir=tmp_path, runner=runner)
    assert record["configuration_status"] == "CONFIGURED_NOT_OBSERVED"
    assert record["provider_call_attempted"] is True
    assert record["public_write_performed"] is False
    assert record["output_sha256"]
    if failure in {"empty", "timeout", "exit"}:
        assert record["status"] == "AGY_UNAVAILABLE" and record["cause"]
    elif failure == "bad_number":
        assert record["status"] == "NEEDS_EDITOR_FIX"
        assert any("99.9%" in issue for issue in record["checks"])
    else:
        assert record["status"] == "DRAFT_CHECKS_PASS", record["checks"]
    # An interruption resumes the exact saved call, including a real failure.
    assert draft.prepare_first_draft(governed(), GUIDANCE, output_dir=tmp_path,
        runner=lambda *a, **k: pytest.fail("must not repeat the exact AGY call")) == record
    assert len(calls) == 2


def native_turn(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run_id = "cc403-daily-note"
    work = "cc-opportunity-" + sha256_of(run_id)
    store.create_work_item(story_id=work, work_item_id=work, title="Daily note", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run_id, output_dir=tmp_path, owner_manual_validation=True)
    # Preparation is already complete in this fixture; no media/network work.
    media = {"assets": []}
    store.register_outbox_message(message_id="native-editorial-media-plan-" + sha256_of(run_id),
        work_item_id=work, destination="internal:native-editorial-media", payload=json.dumps(media), status="EDITORIAL_INTERNAL")
    return store, turn


def test_daily_request_consumes_agy_once_and_dispatches_one_light_editor(tmp_path, monkeypatch):
    _, turn = native_turn(tmp_path)
    calls = []

    def first(g, prompt, *, output_dir):
        calls.append(deepcopy(g))
        return {"status": "DRAFT_CHECKS_PASS", "output": output(), "checks": [], "artifact_path": "fixture.json",
                "prompt_sha256": "a" * 64, "provider_call_attempted": True}

    monkeypatch.setattr(draft, "prepare_first_draft", first)
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.validate_release_media", lambda *a, **k: None)
    g = governed()
    args = dict(logical_invocation_id=turn.run_id + ":write", governed_input=g,
                prompt="Write the sourced note.", validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as pending:
        turn(**args)
    request = pending.value.request
    assert request["requested_reasoning_effort"] == "low"
    assert request["governed_input"]["daily_note_first_draft"]["output"] == output()
    assert GUIDANCE in request["prompt"]
    call = native_role_call(request, {"run_id": turn.run_id, "output_dir": str(tmp_path)}, binding_path="binding.json")
    assert call["arguments"]["reasoning_effort"] == "low"
    assert call["arguments"]["model"] == "gpt-6.1-sol"
    response = {"request_sha256": request["request_sha256"], "output": output(),
        "invocation_observation": {"model": "gpt-6.1-sol", "reasoning_effort": "low",
            "surface": "CODEX_EXEC", "invocation_id": "fixture-daily-editor", "observation_source": "test fixture"}}
    turn._put("write", "response", response)
    frozen = deepcopy(request)
    args["governed_input"] = request["governed_input"]
    edited, receipt = turn(**args)
    assert edited["article"]["reader_article_contract"] == g["reader_article_contract"]
    assert receipt["reasoning_effort"] == "low"
    assert turn.telemetry()["role_assignments"]["write"]["reasoning_effort"] == "low"
    assert turn.telemetry()["external_provider_attempt_count"] == 1
    assert turn.frozen_request("write")["request_sha256"] == frozen["request_sha256"]
    assert turn._get("write", "response") == response
    assert len(calls) == 1


def test_weekly_role_remains_strong_and_no_agy_daily_call_is_allocated(tmp_path, monkeypatch):
    from test_native_role_configuration_v1 import request, binding
    value = request("write")
    value["governed_input"] = {"reader_article_contract": {"policy": "CC403_READER_ARTICLE_V1", "format": "WEEKLY_REVIEW"}}
    call = native_role_call(value, binding(tmp_path), binding_path="binding.json")
    assert call["arguments"]["reasoning_effort"] == "max"


def test_older_bound_operation_keeps_its_original_editorial_epoch():
    from live_contentops.reader_article_contract_v1 import new_request_contract
    g = governed()
    g.pop("reader_article_contract")
    g["cutoff_utc"] = "2026-10-30T10:00:00Z"
    assert new_request_contract(g) is None
    g["cutoff_utc"] = "2026-11-10T14:00:00Z"
    assert new_request_contract(g)["format"] == "DAILY_NOTE"


@pytest.mark.parametrize("observation", [
    {"model": "gpt-6-astra", "reasoning_effort": "ultra"},
    {"model": None, "reasoning_effort": None},
    {"model": "gpt-6.1-sol", "reasoning_effort": "max", "configuration_status": "CONFIGURED_NOT_OBSERVED"},
])
def test_model_labels_are_recorded_without_a_second_process_veto(tmp_path, observation):
    _, turn = native_turn(tmp_path)
    args = dict(logical_invocation_id=turn.run_id + ":select", prompt="Select the existing report.",
                governed_input={}, validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as pending:
        turn(**args)
    observed = {**observation, "surface": "CODEX_EXEC", "invocation_id": "fixture-selection",
                "observation_source": "test fixture"}
    turn.submit("select", {"request_sha256": pending.value.request["request_sha256"],
        "output": {"selected": "held report"}, "invocation_observation": observed})
    result, receipt = turn(**args)
    assert result["selected"] == "held report"
    assert receipt["selected_model"] == observation["model"]
    assert receipt["reasoning_effort"] == observation["reasoning_effort"]
    assert turn._get("select", "response")["invocation_observation"] == observed


def test_source_validator_accepts_the_edited_note_and_keeps_every_binding():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _validate_article_against_source_pack
    value = output()
    _, docs = daily()
    value["article"]["reader_article_contract"] = governed()["reader_article_contract"]
    article, validation = _validate_article_against_source_pack(value, docs, article_mode="STANDARD_NEWS_ANALYSIS")
    assert article["reader_article_contract"]["format"] == "DAILY_NOTE"
    assert validation["unsupported_material_claim_count"] == 0
