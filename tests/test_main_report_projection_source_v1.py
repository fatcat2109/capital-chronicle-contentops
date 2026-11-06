import json
from hashlib import sha256

import pytest

from live_contentops import main_report_projection_source_v1 as projection
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from tests.test_capital_chronicle_report_feed_v1 import feed

NOW = "2026-10-18T17:00:00Z"


def retained(tmp_path, monkeypatch, text="The dossier favoured a Democratic sweep. Equities and Bitcoin rose."):
    report = tmp_path / "Main" / "DOSSIER.md"
    report.parent.mkdir()
    report.write_text(text, encoding="utf-8")
    monkeypatch.setattr(projection, "REPORT_ROOTS", (report.parent,))
    root = tmp_path / "sources"
    root.mkdir()
    spec = {"authorship_class": projection.AUTHORSHIP, "authority_ref": "JIM_DECISION_89",
        "headline_id": "midterm-review", "headline_text": "Capital Chronicle reviews its midterm dossier",
        "source_url": "urn:cc-public-report:midterm-review", "known_at_utc": "2026-10-18T15:00:00Z",
        "revision_at_utc": "2026-10-18T16:00:00Z", "passages": [{"source_path": str(report),
            "source_sha256": sha256(report.read_bytes()).hexdigest(), "fragments": [{"start": 0, "end": len(text)}]}]}
    (root / "index.json").write_text(json.dumps({"schema_version": "contentops.retained_source_research.v1",
        "records": [spec]}), encoding="utf-8")
    return root, report, spec


def test_retained_main_report_reaches_existing_newsroom_writer(tmp_path, monkeypatch):
    root, report, spec = retained(tmp_path, monkeypatch)
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
    assert seen[0]["canonical_content_text"] == report.read_text(encoding="utf-8")
    assert seen[0]["source_authority_class"] == "governed_capital_chronicle_report_only"
    assert seen[0]["report_truth_only"] is True


@pytest.mark.parametrize("text,cause", [
    ("Market | price | time", "MAIN_REPORT_RAW_OR_PREDICTION_NUMBERS_FORBIDDEN"),
    ("Kalshi priced the sweep at 74%.", "MAIN_REPORT_RAW_OR_PREDICTION_NUMBERS_FORBIDDEN"),
    ("The DEMO account balance rose.", "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"),
])
def test_private_rows_and_prediction_numbers_stay_out(tmp_path, monkeypatch, text, cause):
    root, _, _ = retained(tmp_path, monkeypatch, text)
    research = RetainedSourceResearch(root)
    assert not research.records
    assert research.gaps[0]["state"] == cause


def test_changed_main_bytes_cannot_replace_frozen_evidence(tmp_path, monkeypatch):
    root, report, _ = retained(tmp_path, monkeypatch)
    report.write_text("Changed report", encoding="utf-8")
    research = RetainedSourceResearch(root)
    assert not research.records
    assert research.gaps[0]["state"] == "MAIN_REPORT_SOURCE_BYTES_CHANGED"


def test_report_path_cannot_escape_configured_main_roots(tmp_path, monkeypatch):
    root, _, spec = retained(tmp_path, monkeypatch)
    spec["passages"][0]["source_path"] = str(tmp_path / "outside.md")
    with pytest.raises(ValueError, match="MAIN_REPORT_SOURCE_PATH_INVALID"):
        projection.verify_projection(spec)
