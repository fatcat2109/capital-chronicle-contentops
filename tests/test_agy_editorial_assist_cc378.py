"""Recorded text-only output through the real compiler; no model/public calls."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from live_contentops import agy_editorial_assist_v1 as agy
from live_contentops.eight_platform_substack_first_pipeline_v1 import build_native_derivative_payloads


def packet():
    return ({"title": "Publisher adapter validation", "subtitle": "Controlled text-only sample",
             "substack_body_markdown": "The source line reports 2 observations. The sample contains no current market claim."},
            [{"publisher": "Controlled fixture", "text": "The source line reports 2 observations."}],
            [{"asset_id": "sample-chart", "modality": "chart", "caption": "Controlled chart of the two observations; no market data.",
              "spec": {"observations": 2}, "alt_text": "Original description."}])


def recorded_output():
    return json.loads((Path(__file__).parent / "fixtures/cc378_agy_recorded_output.json").read_bytes())


def fake_runner(output=None, error=None):
    """A fake `codex exec` (since 24 Nov 2026 the light text runs on Codex, never agy)."""
    def run(args, **kwargs):
        assert list(Path(kwargs["cwd"]).iterdir()) == []
        assert "--version" not in args and args[1] == "exec"
        assert args[args.index("--model") + 1] == agy.ASSIST_MODEL == "gpt-6.2-sol"
        assert 'model_reasoning_effort="' + agy.ASSIST_EFFORT + '"' in args and agy.ASSIST_EFFORT == "medium"
        assert kwargs["input"].decode("utf-8").startswith("Do not call any tool")
        assert kwargs["timeout"] == agy.ASSIST_TIMEOUT_SECONDS
        if error:
            raise error
        out = Path(args[args.index("--output-last-message") + 1])
        out.write_bytes(json.dumps(output).encode())
        return subprocess.CompletedProcess(args, 0, b"", b"")
    return run


def prepare(tmp_path, output=None):
    draft, sources, assets = packet()
    return agy.prepare_assist(draft, sources, assets, output_dir=tmp_path,
                              runner=fake_runner(recorded_output() if output is None else output))


def approve(tmp_path, record):
    return agy.review_assist(tmp_path, {"prompt_sha256": record["prompt_sha256"],
        "decisions": [{"claim_id": f["claim_id"], "action": "KEEP",
                       "reason": "Controlled fixture; the exact source line states the figure."} for f in record["flags"]],
        "use_alt_text": True, "use_variants": True})


def test_recorded_output_is_used_by_live_compiler(tmp_path):
    record = prepare(tmp_path)
    assert record["status"] == "AGY_AVAILABLE"
    assert record["configuration_status"] == "CONFIGURED_NOT_OBSERVED"
    assert (record["caller"], record["model"]) == ("codex", "gpt-6.2-sol")
    assert record["started_utc"] <= record["ended_utc"]
    assert agy.sha256((Path(record["artifact_path"]).parent / "prompt.txt").read_bytes()).hexdigest() == record["prompt_sha256"]
    assert agy.sha256((Path(record["artifact_path"]).parent / "output.txt").read_bytes()).hexdigest() == record["output_sha256"]
    approve(tmp_path, record)
    article, assets = agy.consume_assist(packet()[0], packet()[2], output_dir=tmp_path)
    assert assets[0]["alt_text"] == recorded_output()["alt_text"][0]["text"]
    assert article["agy_light_assist"]["variant_destinations"] == sorted(agy.LIMITS)
    article.update(native_brief_layout=True, social_scenarios={"base_case": "Base case: The sample remains a test.",
                                                            "alternative": "Alternative: A later test changes the sample."})
    canonical = "https://capitalchronicle.substack.com/p/controlled"
    payloads = build_native_derivative_payloads(article=article, selection={}, canonical_url=canonical,
                                               media_asset_ids=["sample-chart"])
    for destination in agy.LIMITS:
        payload = payloads[destination]
        visible = payload.get("full_text") or payload.get("text") or payload["root_text"]
        expected = recorded_output()["variants"][destination]
        assert (expected[0] if isinstance(expected, list) else expected) in visible
        assert canonical in visible
        assert "Capital Chronicle offers analysis only, not financial advice or recommendations." in visible
        assert "Capital Chronicle may hold positions in the markets it covers." in visible
        assert "Base case:" in visible and "Alternative:" in visible
        if destination in {"x", "threads"}:
            assert all(len(post["text"]) <= agy.LIMITS[destination] for post in payload["posts"])
    from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
    assert set(payloads) == set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)


@pytest.mark.parametrize("failure", [FileNotFoundError("controlled missing agy"),
    subprocess.TimeoutExpired("agy", 120, output=b"controlled partial response", stderr=b"controlled timeout")])
def test_failure_never_holds_or_changes_the_original_copy(tmp_path, failure):
    draft, sources, assets = packet()
    record = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=fake_runner(error=failure))
    assert record["status"] == "AGY_UNAVAILABLE"
    article, media = agy.consume_assist(draft, assets, output_dir=tmp_path)
    assert article["substack_body_markdown"] == draft["substack_body_markdown"]
    assert "publisher_light_variants" not in article
    assert media == assets
    assert record["cause"]
    if isinstance(failure, subprocess.TimeoutExpired):
        assert record["output_sha256"] == agy.sha256(failure.output).hexdigest()


def test_failed_or_empty_output_and_resume_do_not_retry(tmp_path):
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, b"", b"")
    draft, sources, assets = packet()
    first = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=run)
    second = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=run)
    assert first == second
    assert first["status"] == "AGY_UNAVAILABLE"
    assert len(calls) == 1  # one Codex call (no agy version probe); resume reuses the result


def test_one_codex_call_feeds_reviewed_copy_and_resume_does_not_repeat_it(tmp_path):
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return fake_runner(recorded_output())(args, **kwargs)
    draft, sources, assets = packet()
    record = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=run)
    assert record["status"] == "AGY_AVAILABLE"
    assert (record["caller"], record["model"], record["effort"]) == ("codex", "gpt-6.2-sol", "medium")
    assert not any(key.startswith(("agy", "version_")) for key in record)
    approve(tmp_path, record)
    article, media = agy.consume_assist(draft, assets, output_dir=tmp_path)
    assert media[0]["alt_text"] == recorded_output()["alt_text"][0]["text"]
    assert article["agy_light_assist"]["variant_destinations"] == sorted(agy.LIMITS)
    agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=run)
    assert len(calls) == 1


def test_codex_timeout_keeps_the_named_cause_and_existing_copy(tmp_path):
    def run(args, **kwargs):
        raise subprocess.TimeoutExpired(args, kwargs["timeout"])
    draft, sources, assets = packet()
    record = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=run)
    assert record["cause"] == "ValueError: CODEX_LIGHT_TIMEOUT_" + str(agy.ASSIST_TIMEOUT_SECONDS) + "S"
    article, media = agy.consume_assist(draft, assets, output_dir=tmp_path)
    assert article["substack_body_markdown"] == draft["substack_body_markdown"]
    assert "publisher_light_variants" not in article
    assert media == assets


def test_flags_are_bound_to_source_lines_and_publisher_decides(tmp_path):
    output = recorded_output()
    output["claims"] = [{"claim_id": "flag-1", "draft_span": "2", "kind": "number",
                         "source_line_ids": ["L999"], "source_quote": "2", "flag": ""}]
    record = prepare(tmp_path, output)
    assert record["flags"][0]["cause"] == "SOURCE_LINE_UNMATCHED"
    # Unreviewed flags do not block the article or silently change its prose.
    article, _ = agy.consume_assist(packet()[0], packet()[2], output_dir=tmp_path)
    assert article["substack_body_markdown"] == packet()[0]["substack_body_markdown"]
    with pytest.raises(ValueError, match="DECISIONS"):
        agy.review_assist(tmp_path, {"prompt_sha256": record["prompt_sha256"], "decisions": []})
    reviewed = approve(tmp_path, record)
    assert reviewed["publisher_decisions"][0]["action"] == "KEEP"


@pytest.mark.parametrize("text", ["See fatcat2109.github.io.", "At 20:00 GMT+7.", "https://unapproved.example/",
                                 "DEMO account login 279805139.", "The sample now reports 999 observations.", "A" * 4097])
def test_bad_suggestion_falls_back_without_holding_the_piece(tmp_path, text):
    output = recorded_output(); output["variants"]["telegram"] = text
    record = prepare(tmp_path, output); approve(tmp_path, record)
    article, _ = agy.consume_assist(packet()[0], packet()[2], output_dir=tmp_path)
    assert "telegram" not in article.get("publisher_light_variants", {})
    assert article["agy_light_assist"]["rejected_suggestions"]


def test_changed_draft_does_not_use_stale_suggestions(tmp_path):
    record = prepare(tmp_path); approve(tmp_path, record)
    draft, _, assets = packet(); draft["substack_body_markdown"] += " A corrected claim."
    article, media = agy.consume_assist(draft, assets, output_dir=tmp_path)
    assert article["agy_light_assist"]["cause"] == "DRAFT_CHANGED"
    assert media == assets


def test_cc755_light_copy_checks_targets_and_preserves_other_variant_work(tmp_path):
    draft, sources, assets = packet()
    prompt, _ = agy.prompt_for(draft, sources, assets)
    assert "Base case and its stated chance" in prompt and "Keep profit targets out" in prompt
    output = recorded_output()
    output["variants"]["telegram"] = "Target level: 2."
    record = prepare(tmp_path, output)
    approve(tmp_path, record)
    article, _ = agy.consume_assist(draft, assets, output_dir=tmp_path)
    assert set(article["publisher_light_variants"]) == {"x", "threads", "discord"}
    assert "SCENARIO_VOICE_TARGET_FORBIDDEN" in article["agy_light_assist"]["rejected_suggestions"]


def test_reader_adapter_preserves_selected_variants():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article
    draft = packet()[0]; draft["publisher_light_variants"] = recorded_output()["variants"]
    assert _reader_safe_native_article(draft, article_mode="BREAKING_BRIEF")["publisher_light_variants"] == draft["publisher_light_variants"]


def test_long_source_pack_stream_and_parser_have_no_command_line_limit(tmp_path):
    draft, sources, assets = packet()
    sources[0]["context"] = "Inert context. " * 5000
    output = recorded_output()
    def run(args, **kwargs):
        # The prompt goes on stdin, never the command line.
        assert len(" ".join(args)) < 1000
        assert len(kwargs["input"]) > 32768
        return fake_runner(output)(args, **kwargs)
    assert agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=run)["status"] == "AGY_AVAILABLE"


def test_native_submit_and_review_route_the_light_step(tmp_path, monkeypatch):
    from scripts import run_native_desktop_editorial as cli
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    store = ContentOpsDurableStore(tmp_path / "isolated.sqlite3")
    draft, sources, assets = packet()
    class Turn:
        def __init__(self, *args, **kwargs):
            self.root = tmp_path
        def submit(self, stage, response):
            return {"stage": stage, "public_write_performed": False}
        def frozen_request(self, stage):
            return {"governed_input": {"source_pack": sources}}
        def admitted_editorial_media(self):
            return assets
    monkeypatch.setattr(cli, "validate_binding", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "_bound_store", lambda *args: store)
    monkeypatch.setattr(cli, "NativeDesktopTurn", Turn)
    from live_contentops import light_model_caller_v1 as light
    monkeypatch.setattr(light, "_run_codex", fake_runner(recorded_output()))
    binding = {"run_id": "controlled-article", "output_dir": str(tmp_path)}
    submitted = cli._operation(binding, command="submit", stage="write", response={"output": {"article": draft}})
    record = json.loads((tmp_path / agy.NAME).read_bytes())
    assert submitted["agy_light_assist"]["status"] == "AGY_AVAILABLE"
    decision = {"prompt_sha256": record["prompt_sha256"], "use_alt_text": True, "use_variants": True,
                "decisions": [{"claim_id": f["claim_id"], "action": "KEEP", "reason": "Controlled exact source."}
                              for f in record["flags"]]}
    reviewed = cli._operation(binding, command="agy-review", response=decision)
    assert reviewed["classification"] == "AGY_PUBLISHER_REVIEW_RECORDED"
    article, media = agy.consume_assist(draft, assets, output_dir=tmp_path)
    assert media[0]["alt_text"] == recorded_output()["alt_text"][0]["text"]
    assert set(article["publisher_light_variants"]) == set(agy.LIMITS)


def test_compiler_rejecting_suggestions_retains_the_original_article(tmp_path, monkeypatch):
    from live_contentops import v1_simple_gemini_newsroom_v1 as newsroom
    record = prepare(tmp_path); approve(tmp_path, record)
    def reject(**kwargs):
        raise newsroom.SimpleGeminiNewsroomError("native_preview_epistemic_certainty_inflation")
    monkeypatch.setattr(newsroom, "_native_preview_bundle", reject)
    article, _ = agy.consume_assist(packet()[0], packet()[2], output_dir=tmp_path,
                                  article_mode="STANDARD_NEWS_ANALYSIS")
    assert "publisher_light_variants" not in article
    assert article["substack_body_markdown"] == packet()[0]["substack_body_markdown"]
    assert article["agy_light_assist"]["rejected_suggestions"]


@pytest.mark.parametrize("span,quote", [("20", "2"), ("-2", "2"), ("2%", "2")])
def test_claim_cannot_launder_a_different_value_sign_or_unit(tmp_path, span, quote):
    draft, sources, assets = packet()
    draft["substack_body_markdown"] = "The source reports " + span + " observations."
    output = recorded_output()
    output["claims"] = [{"claim_id": "wrong-value", "draft_span": span, "kind": "number",
                         "source_line_ids": ["L2"], "source_quote": quote, "flag": ""}]
    record = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=fake_runner(output))
    assert record["status"] == "AGY_AVAILABLE"
    assert any(f["claim_id"] == "wrong-value" and f["cause"] == "CLAIM_NUMBER_NOT_IN_SOURCE_QUOTE"
               for f in record["flags"])
    # A first-pass flag stays a Publisher input, never an article veto.
    approve(tmp_path, record)
    article, _ = agy.consume_assist(draft, assets, output_dir=tmp_path)
    assert article["substack_body_markdown"] == draft["substack_body_markdown"]


def test_number_and_attribution_coverage_is_exact(tmp_path):
    draft, sources, assets = packet()
    draft["substack_body_markdown"] = "Controlled fixture reports 2 observations and 20 checks."
    output = recorded_output()
    output["claims"] = [{"claim_id": "twenty", "draft_span": "20", "kind": "number",
                         "source_line_ids": [], "source_quote": "", "flag": "No source."}]
    record = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=fake_runner(output))
    assert any(f["cause"] == "NUMBER_NOT_LISTED" and f["draft_span"] == "2" for f in record["flags"])
    assert any(f["cause"] == "ATTRIBUTION_NOT_LISTED" for f in record["flags"])


@pytest.mark.parametrize("source_field", ["source_id", "url", "retrieved_at_utc"])
def test_draft_and_source_metadata_cannot_authorize_social_numbers(tmp_path, source_field):
    draft, sources, assets = packet()
    draft["substack_body_markdown"] += " There are 999 checks."
    sources[0][source_field] = "999"
    output = recorded_output()
    output["variants"]["telegram"] = "There are 999 checks."
    record = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=fake_runner(output))
    approve(tmp_path, record)
    article, media = agy.consume_assist(draft, assets, output_dir=tmp_path)
    assert "telegram" not in article["publisher_light_variants"]
    assert set(article["publisher_light_variants"]) == {"x", "threads", "discord"}
    assert article["agy_light_assist"]["rejected_suggestions"] == ["AGY_UNSUPPORTED_NUMBER"]
    assert media[0]["alt_text"] == recorded_output()["alt_text"][0]["text"]
    assert article["substack_body_markdown"] == draft["substack_body_markdown"]


def test_matching_a_metadata_quote_does_not_support_a_claim(tmp_path):
    draft, sources, assets = packet()
    draft["substack_body_markdown"] += " There are 999 checks."
    sources[0]["document_id"] = "999"
    output = recorded_output()
    output["claims"] = [{"claim_id": "metadata", "draft_span": "999", "kind": "number",
                         "source_line_ids": ["L3"], "source_quote": "999", "flag": ""}]
    record = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=fake_runner(output))
    assert record["flags"][0]["cause"] == "SOURCE_LINE_UNMATCHED"


def test_named_dates_and_attributions_are_checked_against_the_quote(tmp_path):
    draft, sources, assets = packet()
    draft["substack_body_markdown"] = "According to Invented Agency, the release is Tuesday in November."
    sources[0]["text"] = "The release is Wednesday in November."
    output = recorded_output()
    output["claims"] = [
        {"claim_id": "wrong-day", "draft_span": "Tuesday", "kind": "date",
         "source_line_ids": ["L2"], "source_quote": "Wednesday", "flag": ""},
        {"claim_id": "wrong-publisher", "draft_span": "According to Invented Agency", "kind": "attribution",
         "source_line_ids": ["L2"], "source_quote": "The release", "flag": ""}]
    record = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=fake_runner(output))
    causes = {f["cause"] for f in record["flags"]}
    assert causes == {"CLAIM_DATE_NOT_IN_SOURCE_QUOTE", "CLAIM_ATTRIBUTION_NOT_IN_SOURCE_LINES", "DATE_NOT_LISTED"}
    assert any(f["cause"] == "DATE_NOT_LISTED" and f["draft_span"] == "November" for f in record["flags"])


@pytest.mark.parametrize("extra,cause", [("The release is Tuesday.", "AGY_UNSUPPORTED_DATE"),
                                        ("According to Invented Agency, there are 2 observations.",
                                         "AGY_UNSUPPORTED_ATTRIBUTION")])
def test_light_copy_checks_dates_and_attributions_without_blocking_other_outputs(tmp_path, extra, cause):
    draft, sources, assets = packet()
    # Even an unsupported attribution/date repeated from the draft must be
    # rejected by the source-record check before the real compiler consumes it.
    draft["substack_body_markdown"] += " " + extra
    output = recorded_output()
    output["variants"]["telegram"] = extra
    output["alt_text"][0]["text"] = "The chart is dated Tuesday."
    record = agy.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=fake_runner(output))
    approve(tmp_path, record)
    article, media = agy.consume_assist(draft, assets, output_dir=tmp_path)
    assert media[0]["alt_text"] == assets[0]["alt_text"]
    assert set(article["publisher_light_variants"]) == {"x", "threads", "discord"}
    assert cause in article["agy_light_assist"]["rejected_suggestions"]
