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
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _editorial_data_values
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
