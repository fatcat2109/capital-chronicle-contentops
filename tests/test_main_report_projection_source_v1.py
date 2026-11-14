import json
from hashlib import sha256

import pytest

from live_contentops import main_report_projection_source_v1 as projection
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from tests.test_capital_chronicle_report_feed_v1 import feed

NOW = "2026-10-18T17:00:00Z"


def retained(tmp_path, monkeypatch, text="The dossier favoured a Democratic sweep. Equities and Bitcoin rose.", *, native=False):
    single_pass = native == "single_pass"
    report = (tmp_path / "Main/shocks/shock-one/analysis-native.json" if single_pass else
              tmp_path / "Main" / ("owner-native.json" if native else "DOSSIER.md"))
    report.parent.mkdir(parents=True)
    synthesis = {"summary": [{"text": text}], "candidates": [{"entry": 123, "rationale": text}]}
    report.write_text(json.dumps({"native_synthesis": synthesis} if single_pass else synthesis)
                      if native else text, encoding="utf-8")
    if single_pass:
        digest = sha256(json.dumps(json.loads(report.read_bytes()), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        (report.parent / "analysis-end.json").write_text(json.dumps({"output_sha256": digest, "schema_errors": []}), encoding="utf-8")
    monkeypatch.setattr(projection, "REPORT_ROOTS", (report.parent,))
    monkeypatch.setattr(projection, "NATIVE_MAIN_REPORT_ROOT", report.parent)
    monkeypatch.setattr(projection, "NATIVE_MAIN_ANALYSIS_ROOT", tmp_path / "Main")
    root = tmp_path / "sources"
    root.mkdir()
    spec = {"authorship_class": projection.AUTHORSHIP, "authority_ref": "JIM_DECISION_89",
        "headline_id": "midterm-review", "headline_text": "Capital Chronicle reviews its midterm dossier",
        "source_url": "urn:cc-public-report:midterm-review", "known_at_utc": "2026-10-18T15:00:00Z",
        "revision_at_utc": "2026-10-18T16:00:00Z", "passages": [{"source_path": str(report),
            "source_sha256": sha256(report.read_bytes()).hexdigest(), "fragments": [{"start": 0, "end": len(text)}]}]}
    if native:
        spec["passages"][0]["source_json_pointer"] = ("/native_synthesis" if single_pass else "") + "/summary/0/text"
    (root / "index.json").write_text(json.dumps({"schema_version": "contentops.retained_source_research.v1",
        "records": [spec]}), encoding="utf-8")
    return root, report, spec


@pytest.mark.parametrize("native", [False, True, "single_pass"])
def test_retained_main_report_reaches_existing_newsroom_writer(tmp_path, monkeypatch, native):
    root, report, spec = retained(tmp_path, monkeypatch, native=native)
    research = RetainedSourceResearch(root)
    assert not research.gaps
    f = feed(tmp_path / "feed")
    f.retained_research = research
    seen = []

    class WriterReached(Exception):
        pass

    def invoke(**kwargs):
        governed = kwargs["governed_input"]
        if "candidates" in governed:
            chosen = next(c for c in governed["candidates"] if c["headline_id"] == spec["headline_id"])
            return {"schema_version": "contentops.v1_simple_gemini_selection.v2", "status": "SELECT_CANDIDATE_PLAN",
                "ordered_candidate_plan": [{"candidate_id": chosen["candidate_id"], "article_mode": "DATA_OR_DOCUMENT_LENS",
                    "selection_rationale": "Review the retained Main report.", "research_queries": ["Review the dossier"]}],
                "selection_summary": "Controlled integration test.", "public_write_attempted": False}, {
                    "selected_model": "vx/gemini-3.5-flash(high)", "total_attempts": 0, "replay_only": True,
                    "model_identity_provider_verifiable": False}
        seen.extend(governed["source_pack"])
        raise WriterReached()

    with pytest.raises(WriterReached):
        result = f.opportunity(output_dir=tmp_path / "draft", cutoff_utc=NOW, run_id="main-review-consumer",
            rolling_input={"headlines": []}, llm_invoke=invoke)
        workspace = result.get("report_workspace_result", {})
        pytest.fail(str({k: workspace.get(k) for k in ("classification", "exact_next_blocker", "simple_result")}))
    assert len(seen) == 1
    document = json.loads(report.read_bytes()) if native else {}
    expected = document.get("native_synthesis", document)["summary"][0]["text"] if native else report.read_text(encoding="utf-8")
    assert seen[0]["canonical_content_text"] == expected
    assert seen[0]["source_authority_class"] == "governed_capital_chronicle_report_only"
    assert seen[0]["report_truth_only"] is True


@pytest.mark.parametrize("text,cause", [
    ("Market | price | time", "MAIN_REPORT_RAW_OR_PREDICTION_NUMBERS_FORBIDDEN"),
    ("Kalshi priced the sweep at 74%.", "MAIN_REPORT_RAW_OR_PREDICTION_NUMBERS_FORBIDDEN"),
    ("The DEMO account balance rose.", "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"),
])
@pytest.mark.parametrize("native", [False, True, "single_pass"])
def test_private_rows_and_prediction_numbers_stay_out(tmp_path, monkeypatch, text, cause, native):
    root, _, _ = retained(tmp_path, monkeypatch, text, native=native)
    research = RetainedSourceResearch(root)
    assert not research.records
    assert research.gaps[0]["state"] == cause


def test_changed_main_bytes_cannot_replace_frozen_evidence(tmp_path, monkeypatch):
    root, report, _ = retained(tmp_path, monkeypatch)
    report.write_text("Changed report", encoding="utf-8")
    research = RetainedSourceResearch(root)
    assert not research.records
    assert research.gaps[0]["state"] == "MAIN_REPORT_SOURCE_BYTES_CHANGED"


@pytest.mark.parametrize("native", [True, "single_pass"])
def test_native_data_capture_clock_reaches_the_actual_writer_source_pack(tmp_path, monkeypatch, native):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack
    from live_contentops.reader_article_contract_v1 import contract_for
    root, report, spec = retained(tmp_path, monkeypatch, native=native)
    capture = report.parent / "capture.json"
    capture.write_text(json.dumps({"known_at_utc": "2026-10-18T14:00:00Z", "private_value": "never projected"}), encoding="utf-8")
    research = RetainedSourceResearch(root)
    docs = _source_pack(research.evidence({"headline_ids": [spec["headline_id"]]}, cutoff_utc=NOW)["evidence_documents"])
    contract = contract_for({"source_pack": docs})
    assert contract["data_cutoff_utc"] == "2026-10-18T14:00:00+00:00"
    assert docs[0]["published_at_utc"] == "2026-10-18T15:00:00Z"
    assert docs[0]["data_clock_binding"][0]["sha256"] == sha256(capture.read_bytes()).hexdigest()
    assert "private_value" not in json.dumps(docs) and "never projected" not in json.dumps(docs)


@pytest.mark.parametrize("failure", ["missing", "changed", "schema_errors"])
def test_single_pass_requires_completed_exact_main_output(tmp_path, monkeypatch, failure):
    _, report, spec = retained(tmp_path, monkeypatch, native="single_pass")
    proof = report.parent / "analysis-end.json"
    if failure == "missing":
        proof.unlink()
    else:
        record = json.loads(proof.read_bytes())
        record["output_sha256" if failure == "changed" else "schema_errors"] = "bad"
        proof.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="MAIN_REPORT_ANALYSIS_COMPLETION_"):
        projection.verify_projection(spec)


@pytest.mark.parametrize("pointer", ["/native_synthesis/candidates/0/entry", "/primary_analysis/summary/0/text", "/summary/0/text"])
def test_single_pass_projects_only_synthesis_prose(tmp_path, monkeypatch, pointer):
    _, _, spec = retained(tmp_path, monkeypatch, native="single_pass")
    spec["passages"][0]["source_json_pointer"] = pointer
    with pytest.raises(ValueError, match="MAIN_REPORT_PUBLIC_TEXT_POINTER_INVALID"):
        projection.verify_projection(spec)


def test_dated_main_context_keeps_its_clock_without_replacing_the_lead_cutoff(tmp_path, monkeypatch):
    from copy import deepcopy
    _, report, spec = retained(tmp_path, monkeypatch, native=True)
    (report.parent / "capture.json").write_text('{"known_at_utc":"2026-10-18T14:00:00Z"}', encoding="utf-8")
    older = report.parent / "older/owner-native.json"
    older.parent.mkdir()
    older.write_bytes(report.read_bytes())
    (older.parent / "capture.json").write_text('{"known_at_utc":"2026-10-18T13:00:00Z"}', encoding="utf-8")
    passage = deepcopy(spec["passages"][0])
    passage.update(source_path=str(older), source_sha256=sha256(older.read_bytes()).hexdigest())
    spec["passages"].append(passage)
    doc = projection.verify_projection(spec)["document"]
    assert doc["data_cutoff_utc"] == "2026-10-18T14:00:00Z"
    assert [v["value"] for v in doc["data_clock_binding"]] == ["2026-10-18T14:00:00Z", "2026-10-18T13:00:00Z"]


@pytest.mark.parametrize("raw", ['{"known_at_utc":"2026-10-18T16:00:00Z"}', 'bad json', '{}'])
def test_a_clock_gap_does_not_wall_off_held_main_analysis(tmp_path, monkeypatch, raw):
    _, report, spec = retained(tmp_path, monkeypatch, native=True)
    (report.parent / "capture.json").write_text(raw, encoding="utf-8")
    doc = projection.verify_projection(spec)["document"]
    assert "Equities and Bitcoin rose." in doc["canonical_content_text"]
    assert doc["data_clock_binding"][0]["cause"]
    assert "data_cutoff_utc" not in doc


def test_own_report_facts_feed_existing_public_card_renderer(tmp_path, monkeypatch):
    from live_contentops.post_visuals_v1 import build_post_data_card, validate_post_data_card
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack
    root, report, spec = retained(tmp_path, monkeypatch)
    research = RetainedSourceResearch(root)
    evidence = research.evidence({"headline_ids": [spec["headline_id"]]}, cutoff_utc=NOW)
    docs = _source_pack(evidence["evidence_documents"])
    fact = "Equities and Bitcoin rose."
    article = {"title": "Main's midterm review", "substack_body_markdown": fact}
    claims = [{"claim_id": "reaction", "claim_text": fact, "support_excerpt": fact, "source_id": "SOURCE_1"}]
    asset = build_post_data_card(article, claims, docs, output_dir=tmp_path / "media")
    assert asset["data_card_packet"]["facts"][0]["text"] == fact
    assert asset["data_card_packet"]["facts"][0]["rights_class"] == "capital_chronicle_own_report"
    validate_post_data_card(asset, article, docs)


def test_exact_main_spans_validate_without_fabricated_typed_claims(tmp_path, monkeypatch):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack, _validate_article_against_source_pack, SimpleGeminiNewsroomError
    root, report, spec = retained(tmp_path, monkeypatch)
    research = RetainedSourceResearch(root)
    docs = _source_pack(research.evidence({"headline_ids": [spec["headline_id"]]}, cutoff_utc=NOW)["evidence_documents"])
    fact = "The dossier favoured a Democratic sweep."
    article = {k: fact for k in ("title", "dek", "search_title", "meta_description", "social_hook")}
    article["substack_body_markdown"] = fact + " [[SOURCE:SOURCE_1]]"
    output = {"article": article, "cited_sources": [{k: docs[0][k] for k in ("source_id", "url", "publisher", "published_at_utc")}],
        "material_claim_bindings": [{"claim_id": "exact-span", "claim_text": fact, "claim_kind": "FACT",
            "support_excerpt": fact, "source_id": "SOURCE_1", "attribution_required": True}]}
    _, validation = _validate_article_against_source_pack(output, docs)
    assert validation["supported_material_claims"][0]["support_status"] == "SUPPORTED_EXACT_RETAINED_MAIN_REPORT_SPANS"
    docs[0]["report_lineage"]["origin"] = "ORIGINAL_TYPED_MAIN_ENVELOPE"
    with pytest.raises(SimpleGeminiNewsroomError, match="report_claim_excerpt_unbound"):
        _validate_article_against_source_pack(output, docs)


def test_report_path_cannot_escape_configured_main_roots(tmp_path, monkeypatch):
    root, _, spec = retained(tmp_path, monkeypatch)
    spec["passages"][0]["source_path"] = str(tmp_path / "outside.md")
    with pytest.raises(ValueError, match="MAIN_REPORT_SOURCE_PATH_INVALID"):
        projection.verify_projection(spec)


def test_unadmitted_file_is_refused_before_reading_bytes(tmp_path, monkeypatch):
    from pathlib import Path
    _, _, spec = retained(tmp_path, monkeypatch, native=True)
    outside = tmp_path / "outside" / "owner-native.json"
    outside.parent.mkdir()
    outside.write_text('{"summary": [{"text": "Not admitted"}]}', encoding="utf-8")
    spec["passages"][0]["source_path"] = str(outside)
    original = Path.read_bytes

    def guarded_read(path):
        assert path != outside, "Unadmitted source bytes must never be read"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read)
    with pytest.raises(ValueError, match="MAIN_REPORT_SOURCE_PATH_INVALID"):
        projection.verify_projection(spec)


@pytest.mark.parametrize("pointer", ["/candidates/0/entry", "/summary/8/text", "/account/balance"])
def test_native_projection_refuses_execution_fields_or_absent_prose(tmp_path, monkeypatch, pointer):
    _, _, spec = retained(tmp_path, monkeypatch, native=True)
    spec["passages"][0]["source_json_pointer"] = pointer
    with pytest.raises(ValueError, match="MAIN_REPORT_PUBLIC_TEXT_POINTER_INVALID"):
        projection.verify_projection(spec)


def test_native_synthesis_prose_feeds_existing_public_card(tmp_path, monkeypatch):
    from live_contentops.post_visuals_v1 import build_post_data_card, validate_post_data_card
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack
    text = "Gold faces a dollar risk. A rebound remains possible."
    root, _, spec = retained(tmp_path, monkeypatch, text, native=True)
    research = RetainedSourceResearch(root)
    docs = _source_pack(research.evidence({"headline_ids": [spec["headline_id"]]}, cutoff_utc=NOW)["evidence_documents"])
    article = {"title": "Six markets before payrolls", "substack_body_markdown": text}
    claims = [{"claim_id": "view", "claim_text": text, "support_excerpt": text, "source_id": "SOURCE_1"}]
    asset = build_post_data_card(article, claims, docs, output_dir=tmp_path / "media")
    validate_post_data_card(asset, article, docs)
    assert asset["data_card_packet"]["facts"][0]["text"] in text


def test_review_card_renders_prose_without_exposing_markdown_or_certifying_interpretation(tmp_path, monkeypatch):
    from live_contentops import fact_card_design_v1 as design
    from live_contentops.post_visuals_v1 import build_post_data_card
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack
    text = "**Gold.** The review describes competing mechanisms."
    root, _, spec = retained(tmp_path, monkeypatch, text, native=True)
    docs = _source_pack(RetainedSourceResearch(root).evidence({"headline_ids": [spec["headline_id"]]}, cutoff_utc=NOW)["evidence_documents"])
    seen, original = [], design.render_fact_card

    def capture(path, card_spec, **kwargs):
        seen.extend(card_spec.facts)
        return original(path, card_spec, **kwargs)

    monkeypatch.setattr(design, "render_fact_card", capture)
    article = {"title": "Capital Chronicle review", "substack_body_markdown": text}
    asset = build_post_data_card(article, [{"claim_text": text, "support_excerpt": text, "source_id": "SOURCE_1"}], docs,
                                output_dir=tmp_path / "media")
    assert asset["data_card_packet"]["facts"][0]["text"] == text
    assert seen == [("From the dated review", "Gold. The review describes competing mechanisms.")]


def test_all_derivatives_display_public_review_notice_without_changing_frozen_provenance(tmp_path, monkeypatch):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle
    root, _, _ = retained(tmp_path, monkeypatch, native=True)
    state = projection.projection_evidence(list(RetainedSourceResearch(root).records.values()), {})["epistemic_state"]
    old = "Capital Chronicle's dated Main report provides analysis, not independently confirmed event facts or a performance record."
    state["report_scope_notice"] = old
    article = {"title": "Capital Chronicle reviews six markets", "dek": "Capital Chronicle's dated review.",
               "substack_body_markdown": "Capital Chronicle reviews competing mechanisms.\n\n" + old.replace("dated Main report", "dated review")}
    bundle, intents = _native_preview_bundle(article=article, article_mode="DATA_OR_DOCUMENT_LENS",
        article_identity="f" * 64, epistemic_state=state)
    from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
    assert {intent["destination"] for intent in intents} == set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    for package in bundle["packages"].values():
        assert "dated Main report" not in json.dumps(package)
        assert "dated review" in json.dumps(package)
    assert state["report_scope_notice"] == old


@pytest.mark.parametrize("paragraph,attributed", [
    ("The review records gold falling even as yields fell.", True),
    ("The review says gold and yields fell together.", True),
    ("Gold and yields fell together.", False),
])
def test_main_review_attribution_survives_natural_document_references(tmp_path, monkeypatch, paragraph, attributed):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _epistemic_copy_blockers
    root, _, spec = retained(tmp_path, monkeypatch, native=True)
    records = list(RetainedSourceResearch(root).records.values())
    state = projection.projection_evidence(records, {})["epistemic_state"]
    state["event_proposition"] = "Gold and yields fell together."
    article = {key: "Capital Chronicle reviews gold and yields" for key in
               ("title", "dek", "search_title", "meta_description", "social_hook")}
    article["substack_body_markdown"] = ("Capital Chronicle reviews gold and yields.\n\n" + paragraph
                                         + "\n\n" + state["report_scope_notice"])
    blockers = _epistemic_copy_blockers(article, [], state)
    assert ("epistemic_event_asserted_as_confirmed:2" not in blockers) is attributed


@pytest.mark.parametrize("keep_limits", [True, False])
def test_public_review_notice_keeps_frozen_packet_limits_without_internal_producer_name(tmp_path, monkeypatch, keep_limits):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _epistemic_copy_blockers
    root, _, _ = retained(tmp_path, monkeypatch, native=True)
    records = list(RetainedSourceResearch(root).records.values())
    state = projection.projection_evidence(records, {})["epistemic_state"]
    state["report_scope_notice"] = ("Capital Chronicle's dated Main report provides analysis, "
                                    "not independently confirmed event facts or a performance record.")
    article = {key: "Capital Chronicle reviews the dated report" for key in
               ("title", "dek", "search_title", "meta_description", "social_hook")}
    notice = state["report_scope_notice"].replace("dated Main report", "dated review")
    article["substack_body_markdown"] = "Capital Chronicle reviews the report.\n\n" + (notice if keep_limits else "")
    blockers = _epistemic_copy_blockers(article, [], state)
    assert ("report_horizon_proxy_cost_limits_missing" not in blockers) is keep_limits


@pytest.mark.parametrize("change", [None, "title", "opening", "rights", "hash", "lineage", "mixed"])
def test_verified_public_excerpt_reaches_copy_consumer_without_ritual_rewrite(tmp_path, monkeypatch, change):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack, _epistemic_copy_blockers
    text = "Nvidia investigates a suspected intelligence link."
    root, _, spec = retained(tmp_path, monkeypatch, text=text)
    research = RetainedSourceResearch(root)
    evidence = research.evidence({"headline_ids": [spec["headline_id"]]}, cutoff_utc=NOW)
    docs = _source_pack(evidence["evidence_documents"])
    state = evidence["epistemic_state"]
    article = {key: "Capital Chronicle reviews the dated allegations" for key in
               ("dek", "search_title", "meta_description", "social_hook")}
    article.update(title=text, substack_body_markdown=text)
    if change in {"title", "opening"}:
        article["title" if change == "title" else "substack_body_markdown"] = "Nvidia confirms an intelligence link."
    elif change == "rights":
        docs[0]["source_reuse_constraints"]["public_expression_reuse_allowed"] = False
    elif change == "hash":
        docs[0]["canonical_content_text"] += " Changed bytes."
    elif change == "lineage":
        docs[0]["report_lineage"]["report_projection_sha256"] = "0" * 64
    elif change == "mixed":
        docs.append({"canonical_content_text": "External report"})
    blockers = _epistemic_copy_blockers(article, [], state, source_pack=docs)
    if change is None:
        assert blockers == []
        assert state["event_confirmation_state"] == "UNCONFIRMED"
        assert state["underlying_event_may_be_stated_as_confirmed"] is False
    elif change in {"title", "opening"}:
        assert ("epistemic_title_attribution_or_uncertainty_missing" if change == "title"
                else "epistemic_opening_reporting_state_missing") in blockers
    else:
        assert "report_horizon_proxy_cost_limits_missing" in blockers
