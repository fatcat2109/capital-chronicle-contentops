"""Main's held event calculations reach the existing editorial writer source pack."""
from copy import deepcopy
from hashlib import sha256
import json

import pytest

from live_contentops import main_report_projection_source_v1 as projection
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from tests.test_capital_chronicle_report_feed_v1 import feed

NOW = "2026-10-18T17:00:00Z"


def retained(tmp_path, monkeypatch, *, score=False):
    root = tmp_path / "event-outputs"
    root.mkdir()
    monkeypatch.setattr(projection, "EVENT_REACTION_ROOT", root)
    monkeypatch.setattr(projection, "EVENT_SCORE_ROOT", root)
    if score:
        path = root / "event-scores-controlled.json"
        value = {"schema": "EventForecastScoreReportV1", "generated_at_utc": NOW,
            "scores": [{"state": "SCORED", "target": {"event_id": "controlled-nfp"},
                "consensus_source": "controlled-source", "happened": "IN_LINE",
                "scores": {"matrix": {"state": "SCORED", "brier": 0.02},
                    "consensus_only": {"state": "SCORED", "brier": 0.0},
                    "prediction_market_only": {"state": "UNAVAILABLE", "brier": None}},
                "score_scope": "CATEGORICAL_AND_POINT_ERROR", "evidence_class": "RESEARCH_PREPARATION",
                "information_tag": "PIT_CLEAN", "matrix_cutoff_utc": "2026-10-18T14:00:00Z",
                "point_forecast_method": "EXTERNAL_MARKET_CONSENSUS",
                "forecast": 7654321, "private_input": "RAW_CONSENSUS_NEVER_PROJECTED"}]}
        pointer = "/scores/0"
    else:
        path = root / "reaction.json"
        value = {"schema": "PrivateEventMarketReactionTableV1", "event_id": "controlled-nfp",
            "built_at_utc": NOW, "event_at_utc": "2026-10-18T14:00:00Z",
            "public_export": False, "intraday_reaction": {"release_utc": "2026-10-18T14:00:00Z",
                "markets": {"XAUUSD": {"returns_pct": {"+5m": -0.23, "+15m": None,
                    "+30m": -0.35, "+60m": -0.67}}}},
            "records": [{"rights_class": "PRIVATE_BROKER_DEMO", "pre_event_level": 9876543,
                "private_input": "RAW_PRICE_NEVER_PROJECTED"}]}
        pointer = "/intraday_reaction/markets/XAUUSD/returns_pct"
    path.write_text(json.dumps(value), encoding="utf-8")
    passage = {"source_path": str(path), "source_sha256": sha256(path.read_bytes()).hexdigest(),
        "source_json_pointer": pointer, "event_id": "controlled-nfp"}
    text = projection._event_output_text(path.resolve(), passage, path.read_bytes())
    passage["fragments"] = [{"start": 0, "end": len(text)}]
    spec = {"authorship_class": projection.AUTHORSHIP, "authority_ref": "JIM_DECISION_89",
        "headline_id": "controlled-review", "headline_text": "Capital Chronicle reviews its event calculations",
        "source_url": "urn:cc-public-report:controlled-review", "known_at_utc": NOW,
        "revision_at_utc": NOW, "candidate_catalyst_tags": ["EVENT_REVIEW"], "passages": [passage]}
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "index.json").write_text(json.dumps({"schema_version": "contentops.retained_source_research.v1",
        "records": [spec]}), encoding="utf-8")
    return sources, path, spec, value


@pytest.mark.parametrize("score", [False, True])
def test_held_computed_outputs_feed_the_real_writer_without_raw_inputs(tmp_path, monkeypatch, score):
    root, path, spec, _ = retained(tmp_path, monkeypatch, score=score)
    research = RetainedSourceResearch(root)
    assert not research.gaps
    f = feed(tmp_path / "feed")
    from tests.test_pre_event_preview_v1 import prepare, EVENT
    prepare(f.tracker.store, tmp_path / "feed", planned_release_utc="2026-10-18T16:00:00Z")
    f.pointer.update(review_event_id=EVENT, research_root=str(root))
    seen = []

    class WriterReached(Exception):
        pass

    def invoke(**kwargs):
        governed = kwargs["governed_input"]
        if "candidates" in governed:
            chosen = next(c for c in governed["candidates"] if c["headline_id"] == spec["headline_id"])
            return {"schema_version": "contentops.v1_simple_gemini_selection.v2", "status": "SELECT_CANDIDATE_PLAN",
                "ordered_candidate_plan": [{"candidate_id": chosen["candidate_id"], "article_mode": "DATA_OR_DOCUMENT_LENS",
                    "selection_rationale": "Review Main's dated calculations.", "research_queries": ["Event review"]}],
                "selection_summary": "Controlled integration test.", "public_write_attempted": False}, {
                    "selected_model": "vx/gemini-3.5-flash(high)", "total_attempts": 0,
                    "replay_only": True, "model_identity_provider_verifiable": False}
        seen.extend(governed["source_pack"])
        raise WriterReached

    with pytest.raises(WriterReached):
        f.opportunity(output_dir=tmp_path / "draft", cutoff_utc=NOW, run_id="event-review-consumer",
            rolling_input={"headlines": []}, llm_invoke=invoke)
    assert len(seen) >= 2
    assert any("Employment changed little" in d["canonical_content_text"] for d in seen)
    doc = next(d for d in seen if d.get("report_lineage", {}).get("report_id") == spec["headline_id"])
    text = doc["canonical_content_text"]
    assert "Capital Chronicle model estimate" in text
    assert doc["data_clock_binding"][0]["sha256"] == sha256(path.read_bytes()).hexdigest()
    if score:
        assert "matrix Brier score 0.02" in text and "consensus only Brier score 0" in text
        assert "prediction market only comparison unavailable" in text
        assert "not a score of the published preview" in text
    else:
        assert "+5m: -0.23%" in text and "+60m: -0.67%" in text
    assert not any(x in json.dumps(doc) for x in ["RAW_PRICE", "RAW_CONSENSUS", "9876543", "7654321"])


@pytest.mark.parametrize("score", [False, True])
@pytest.mark.parametrize("fault,cause", [
    ("hash", "MAIN_REPORT_SOURCE_BYTES_CHANGED"),
    ("event", "MAIN_EVENT_OUTPUT_EVENT_MISMATCH"),
    ("clock", "MAIN_EVENT_OUTPUT_AFTER_SOURCE_CUTOFF"),
    ("pointer", "MAIN_EVENT_COMPUTED_POINTER_REQUIRED"),
])
def test_exact_event_bytes_clocks_and_computed_fields_are_required(tmp_path, monkeypatch, score, fault, cause):
    _, path, spec, _ = retained(tmp_path, monkeypatch, score=score)
    spec = deepcopy(spec)
    if fault == "hash":
        path.write_text("{}", encoding="utf-8")
    elif fault == "event":
        spec["passages"][0]["event_id"] = "different-event"
    elif fault == "clock":
        spec["known_at_utc"] = "2026-10-18T16:00:00Z"
    else:
        spec["passages"][0]["source_json_pointer"] = "/records/0/pre_event_level" if not score else "/scores/0/forecast"
    with pytest.raises(ValueError, match=cause):
        projection.verify_projection(spec)


def test_main_computed_reaction_feeds_existing_source_bound_chart(tmp_path, monkeypatch):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _editorial_data_values, editorial_chart_source_links
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack
    root, _, spec, _ = retained(tmp_path, monkeypatch)
    research = RetainedSourceResearch(root)
    docs = _source_pack(research.evidence({"headline_ids": [spec["headline_id"]]}, cutoff_utc=NOW)["evidence_documents"])
    doc = docs[0]
    point = {"period": "+5m", "value": -0.23, "observation_kind": "ESTIMATE", "inputs": [{
        "document_id": doc["document_id"], "support_excerpt": doc["canonical_content_text"],
        "source_content_sha256": doc["canonical_content_sha256"], "value_text": "-0.23",
        "source_period_text": "2026-10-18", "prepared_period": "+5m", "metric": "XAUUSD return",
        "unit": "percent", "period_basis": {"basis": "MAIN_COMPUTED_EVENT_RETURN", "event_id": "controlled-nfp"}}]}
    packet = {"chart_type": "grouped_bar", "title": "Capital Chronicle model estimate",
        "question": "What moved in the first observed window?", "unit": "percent",
        "series": [{"name": "Gold", "points": [point]}]}
    assert _editorial_data_values(packet, docs) == [[-0.23]]
    links = editorial_chart_source_links(packet, docs)
    assert links[0]["label"] == "Capital Chronicle model estimate"
    assert links[0]["provenance_ref"] == doc["url"] and links[0]["url"].startswith("https://")
    docs[0]["source_reuse_constraints"]["public_expression_reuse_allowed"] = False
    with pytest.raises(ValueError, match="FACT_RIGHTS_UNBOUND"):
        _editorial_data_values(packet, docs)


def test_compact_writer_source_hash_covers_delivered_text_and_retains_original_hash():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack, MAX_SOURCE_TEXT_CHARS
    text = "Official October employment background. " * MAX_SOURCE_TEXT_CHARS
    original_hash = sha256(text.encode()).hexdigest()
    doc = {"document_id": "long-official", "source_url": "https://www.bls.gov/news.release/empsit.nr0.htm",
        "publisher": "BLS", "canonical_content_text": text, "canonical_content_sha256": original_hash,
        "source_authority_class": "official_public_primary_source"}
    compact = _source_pack([doc])[0]
    assert compact["canonical_content_sha256"] == sha256(compact["canonical_content_text"].encode()).hexdigest()
    assert compact["source_document_content_sha256"] == original_hash
    assert compact["source_document_text_truncated"] is True
    assert doc["canonical_content_text"] == text


def test_pre_writer_hash_correction_retains_exact_old_artifacts_and_native_request(tmp_path):
    from types import SimpleNamespace
    from live_contentops.v1_simple_gemini_newsroom_v1 import _preserve_compact_source_hash_correction
    text = "Exact held public source excerpt."
    old = {"selected_source_pack": [{"document_id": "official", "canonical_content_text": text,
        "canonical_content_sha256": "a" * 64}]}
    new = deepcopy(old)
    new["selected_source_pack"][0].update(canonical_content_sha256=sha256(text.encode()).hexdigest(),
        source_document_content_sha256="a" * 64, source_document_text_truncated=True)
    raw = json.dumps(old).encode()
    (tmp_path / "simple_gemini_evidence_v1.json").write_bytes(raw)
    (tmp_path / "editorial_media_plan_required.json").write_bytes(b'{"original":"media"}')
    request = tmp_path / "desktop_request_media-plan.json"
    request.write_bytes(b'{"original":"native request"}')
    _preserve_compact_source_hash_correction(tmp_path, new, SimpleNamespace(frozen_request=lambda _: None))
    archived = list((tmp_path / "source-recovery-history").glob('*/simple_gemini_evidence_v1.json'))
    assert len(archived) == 1 and archived[0].read_bytes() == raw
    assert request.read_bytes() == b'{"original":"native request"}'
    (tmp_path / "simple_gemini_evidence_v1.json").write_bytes(raw)
    new["selected_source_pack"][0]["canonical_content_text"] = "Changed fact."
    _preserve_compact_source_hash_correction(tmp_path, new, SimpleNamespace(frozen_request=lambda _: None))
    assert (tmp_path / "simple_gemini_evidence_v1.json").read_bytes() == raw


def test_history_endpoint_keeps_its_actual_unit():
    from live_contentops import rolling_x_grounded_article_media_builder_v1 as media
    from matplotlib import pyplot as plt
    import numpy as np
    packet = {"chart_type": "line", "title": "Payrolls", "question": "What was the first print?",
        "unit": "persons", "source_caption": "BLS", "history_lineage": {"window": ["2026-08", "2026-09"]},
        "series": [{"name": "Payroll change", "points": [{"period": "2026-08"}, {"period": "2026-09"}]}]}
    fig = media._draw_editorial_chart(packet, [[10000, 29000]], plt, np)
    labels = [t.get_text() for ax in fig.axes for t in ax.texts]
    plt.close(fig)
    assert "29000" in labels and "29000%" not in labels


def test_retrospective_card_separates_event_date_from_calculation_date(tmp_path, monkeypatch):
    from live_contentops.post_visuals_v1 import build_post_data_card
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack
    root, _, spec, _ = retained(tmp_path, monkeypatch)
    docs = _source_pack(RetainedSourceResearch(root).evidence({"headline_ids": [spec["headline_id"]]}, cutoff_utc=NOW)["evidence_documents"])
    text = "+5m: -0.23%"
    article = {"title": "The dated review", "substack_body_markdown": text, "article_type": "EVENT_REVIEW",
        "event_article_packet": {"event_time_utc": "2026-10-17T13:30:00Z"}, "display_date": "October 19, 2026"}
    card = build_post_data_card(article, [{"claim_id": "reaction", "claim_text": text,
        "source_id": "SOURCE_1", "support_excerpt": text}], docs, output_dir=tmp_path / "media")
    packet = card["data_card_packet"]
    assert packet["source_line"] == "Source: Capital Chronicle; event dated October 17, 2026 (ET)."
    assert packet["dated_line"] == "Capital Chronicle · October 19, 2026"


def test_required_writing_clock_notice_needs_no_fabricated_source_fact_binding():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _paragraph_marker_blockers
    notice = "Retrospective analysis, written on 14 November 2026 (ET)"
    assert _paragraph_marker_blockers(notice + "\n\nWe think the condition held. [[SOURCE:SOURCE_1]]", {"SOURCE_1"}) == []
    assert _paragraph_marker_blockers(notice + ". Gold rose.", {"SOURCE_1"}) == ["unbound_body_paragraph:1"]


def test_own_brand_does_not_turn_nfp_review_into_financing_news():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _selected_news_peg_blockers
    candidate = {"headline_text": "Capital Chronicle NFP review: the Strong branch and measured market response"}
    article = {"title": "October payrolls met our Strong condition", "dek": "Our NFP review separates the market response from the score."}
    assert _selected_news_peg_blockers(article, candidate) == []
    assert _selected_news_peg_blockers({"title": "A financing platform raises money"}, candidate)
    assert _selected_news_peg_blockers(article, {"headline_text": "Capital Chronicle reviews a capital financing platform"})


@pytest.mark.parametrize("voice,accepted", [("We think", True), ("Our interpretation is that", True), ("It is confirmed that", False)])
def test_own_reader_interpretation_keeps_its_epistemic_qualifier(voice, accepted):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _epistemic_copy_blockers
    notice = "Our dated analysis does not independently confirm events or establish a performance record."
    state = {"schema_version": "contentops.v1_simple_epistemic_state.v1",
        "evidence_basis": "GOVERNED_CAPITAL_CHRONICLE_REPORT", "event_confirmation_state": "UNCONFIRMED",
        "origin_character": "ON_RECORD", "source_multiplicity": "SINGLE_SOURCE",
        "report_proposition": "The dated NFP review", "event_proposition": "The report records market observations",
        "primary_reporting_publisher": "Capital Chronicle", "primary_reporting_source_identity": "our-nfp-review",
        "reader_visible_epistemic_label": "DATED REVIEW", "report_truth_supported": True,
        "event_truth_supported": False, "authority_granted_by_adapter": False, "report_scope_notice": notice}
    article = {"reader_article_contract": {"policy": "CC403_READER_ARTICLE_V1"},
        "title": "Our NFP review", "dek": "We think the release met our condition.",
        "substack_body_markdown": voice + " the report and market response answer different questions. [[SOURCE:SOURCE_1]]\n\n" + notice}
    blockers = _epistemic_copy_blockers(article, [{"attribution_required": True}], state)
    assert ("epistemic_event_asserted_as_confirmed:1" not in blockers) == accepted
