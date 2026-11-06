"""Preview preparation reaches the real retained-source and writer consumer."""
from copy import deepcopy
from hashlib import sha256
import json
import pytest

from live_contentops.contentops_editorial_desk_v1 import (
    preview_preparation_research, record_pre_event_preparation,
)
from tests.test_capital_chronicle_report_feed_v1 import feed
from tests.test_capital_chronicle_report_editorial_workspace_v1 import controlled_writer

NOW = "2026-10-18T17:00:00Z"
EVENT = "bls-emsit-20261106"


def prepare(store, tmp_path, **changes):
    capture = tmp_path / "controlled-prior.txt"
    capture.write_text("CONTROLLED BLS fixture. Employment changed little in the prior month.", encoding="utf-8")
    digest = sha256(capture.read_bytes()).hexdigest()
    packet = {"event_id": EVENT, "title": "Employment report preview",
        "known_at_utc": "2026-10-18T15:00:00Z", "planned_release_utc": "2026-11-06T13:30:00Z",
        "reader_question": "What will the next report tell us about labor demand?",
        "background": "Distinguish the establishment and household surveys.",
        "release_work": "CC-107 adds the frozen dossier scenarios before publication.",
        "missing_inputs": ["Future frozen dossier and future release"],
        "released_facts_admitted": False, "publication_authority": False,
        "official_sources": [{"url": "https://www.bls.gov/news.release/empsit.nr0.htm",
            "capture_path": str(capture), "capture_sha256": digest,
            "observed_at_utc": "2026-10-18T14:00:00Z", "published_at_utc": "2026-10-02T12:30:00Z"}],
        "prior_fact_spans": [{"capture_sha256": digest,
            "exact_source_span": "Employment changed little in the prior month.", "metric": "Fixture text"}]}
    packet.update(changes)
    receipt = record_pre_event_preparation(store, packet)
    return capture, packet, receipt


def consensus_input(tmp_path):
    raw = tmp_path / "controlled-consensus.html"
    raw.write_text("CONTROLLED expectation: 10K", encoding="utf-8")
    projection = {"release_id": "US_NFP_20261106", "records": [{
        "source": "fixture-source", "measure_key": "payrolls", "raw_path": raw.name,
        "raw_sha256": sha256(raw.read_bytes()).hexdigest(), "pre_release_eligible": True,
        "source_value_text": "10K", "known_at_utc": "2026-10-18T14:00:00Z",
        "acquired_at_utc": "2026-10-18T14:00:00Z", "released_at_utc": "2026-11-06T13:30:00Z",
        "source_statistic_label": "Consensus", "reference_period": "2026-10",
        "release_date": "2026-11-06", "unit": "thousands_of_jobs", "rights_class": "MISSING",
        "source_url": "https://fixture.example/expectation", "source_cells": ["RAW_TABLE_NEVER_EXPORTED"]}]}
    path = tmp_path / "controlled-projection.json"
    path.write_text(json.dumps(projection), encoding="utf-8")
    return {"projection_path": str(path), "projection_sha256": sha256(path.read_bytes()).hexdigest(),
        "release_id": projection["release_id"], "source": "fixture-source", "measure_key": "payrolls",
        "capture_root": str(tmp_path)}


def test_preparation_flows_through_feed_to_actual_writer_source_pack(tmp_path, monkeypatch):
    f = feed(tmp_path)
    _, _, receipt = prepare(f.tracker.store, tmp_path, single_consensus_fact=consensus_input(tmp_path))
    f.pointer["preview_event_id"] = EVENT
    monkeypatch.setattr(f, "pending", lambda **_: [])
    donor = controlled_writer([])
    observed = []

    class WriterReached(Exception):
        pass

    def invoke(**kwargs):
        governed = kwargs["governed_input"]
        if "candidates" in governed:
            return donor(**kwargs)
        observed.extend(governed["source_pack"])
        raise WriterReached

    with pytest.raises(WriterReached):
        f.opportunity(output_dir=tmp_path / "out", cutoff_utc=NOW, run_id="preview-source-consumer",
            rolling_input={"headlines": []}, llm_invoke=invoke,
            editorial_request="Write the EVENT_PREVIEW background for the future employment release.")
    assert any(d.get("preview_preparation", {}).get("message_id") == receipt["message_id"] for d in observed)
    doc = next(d for d in observed if "preview_preparation" in d)
    assert "Employment changed little" in doc["canonical_content_text"]
    assert doc["published_at_utc"] == "2026-10-02T12:30:00Z"
    assert doc["preview_preparation"]["future_release_values"] is None
    singles = [d for d in observed if d.get("source_reuse_constraints", {}).get("scope", "").startswith("SINGLE_ATTRIBUTED")]
    assert len(singles) == 1 and "10K" in singles[0]["canonical_content_text"]
    assert "RAW_TABLE_NEVER_EXPORTED" not in json.dumps(observed)
    assert len(f.retained_research.headlines(cutoff_utc=NOW)) == 1
    frozen = f.tracker.store.get_outbox_message(next(r["message_id"] for r in f.tracker.store.list_outbox_messages()
        if r["destination"] == "internal:native-current-input"))
    assert receipt["message_id"] in frozen["payload"]


def test_source_hashes_spans_rights_and_clocks_stay_enforced(tmp_path):
    f = feed(tmp_path)
    capture, _, _ = prepare(f.tracker.store, tmp_path)
    result = preview_preparation_research(f.tracker.store, event_id=EVENT, cutoff_utc=NOW)
    docs = result.evidence({"headline_ids": list(result.records)}, cutoff_utc=NOW)
    assert docs["status"] == "PASS", docs
    assert docs["provenance"]["request_count_for_call"] == 0
    capture.write_text("Changed", encoding="utf-8")
    with pytest.raises(ValueError, match="CAPTURE_BINDING"):
        preview_preparation_research(f.tracker.store, event_id=EVENT, cutoff_utc=NOW)


def test_exact_bls_preview_grant_feeds_the_chart_consumer(tmp_path):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _editorial_data_values
    f = feed(tmp_path)
    capture = tmp_path / "controlled-prior.txt"
    text = "September final demand increased 1.3 percent."
    capture.write_text(text, encoding="utf-8")
    digest = sha256(capture.read_bytes()).hexdigest()
    # Reuse the regular preparation recorder, then bind the numerical span.
    _, packet, _ = prepare(f.tracker.store, tmp_path)
    capture.write_text(text, encoding="utf-8")
    packet["known_at_utc"] = "2026-10-18T16:00:00Z"
    packet["official_sources"][0]["capture_sha256"] = digest
    packet["prior_fact_spans"] = [{"capture_sha256": digest, "exact_source_span": text, "metric": "Final demand"}]
    record_pre_event_preparation(f.tracker.store, packet)
    research = preview_preparation_research(f.tracker.store, event_id=EVENT, cutoff_utc=NOW)
    result = research.evidence({"headline_ids": list(research.records)}, cutoff_utc=NOW)
    doc = result["evidence_documents"][0]
    packet = {"title": "Controlled PPI", "question": "What was the prior monthly rate?", "chart_type": "horizontal_diverging_bar",
        "unit": "percent", "series": [{"name": "Final demand", "points": [{"period": "Final demand", "value": 1.3,
            "observation_kind": "REPORTED_ACTUAL", "inputs": [{"document_id": doc["document_id"],
                "support_excerpt": text, "value_text": "1.3", "source_period_text": "September",
                "source_content_sha256": doc["canonical_content_sha256"], "metric": "Final demand", "unit": "percent",
                "prepared_period": "2026-09", "period_basis": {"basis": "EXACT_REPORTED_PRIOR_PERIOD"}}]}]}]}
    assert _editorial_data_values(packet, [doc]) == [[1.3]]
    doc["source_url"] = "https://third-party.example/report"
    doc["url"] = doc["source_url"]
    with pytest.raises(ValueError, match="FACT_RIGHTS_UNBOUND"):
        _editorial_data_values(packet, [doc])


def test_real_history_source_markers_and_explicit_nonforecast_wording():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _paragraph_marker_blockers, _editorial_growth_edge_blockers
    assert _paragraph_marker_blockers("Prior components. [[SOURCE:SOURCE_6]]", {"SOURCE_6"}) == []
    assert _paragraph_marker_blockers("Unknown. [[SOURCE:SOURCE_6]]", {"SOURCE_1"})
    for text in ["A provider expectation, not a Capital Chronicle forecast.",
                 "Not the release result or a Capital Chronicle forecast."]:
        assert _editorial_growth_edge_blockers({"title": text}, article_mode="WEEK_AHEAD_OR_WATCH") == []
    assert _editorial_growth_edge_blockers({"title": "Capital Chronicle forecasts a 30% probability."}, article_mode="WEEK_AHEAD_OR_WATCH")


def test_derivative_bls_attribution_uses_the_exact_bound_publisher_and_host():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article
    state = {"primary_reporting_publisher": "U.S. Bureau of Labor Statistics"}
    article = {"title": "A release preview", "reader_first_version": "DATA_JOURNALISM_V1",
        "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": state["primary_reporting_publisher"],
            "url": "https://www.bls.gov/news.release/empsit.nr0.htm"}]}
    result = _reader_safe_native_article(article, article_mode="WEEK_AHEAD_OR_WATCH", epistemic_state=state)
    assert result["native_source_attribution"]["display_name"] == "BLS"
    article["public_source_bindings"][0]["url"] = "https://unverified.example/source"
    assert "native_source_attribution" not in _reader_safe_native_article(article, article_mode="WEEK_AHEAD_OR_WATCH", epistemic_state=state)


@pytest.mark.parametrize("fault,expected", [
    ("span", "SPAN_CHANGED"), ("rights", "PUBLIC_BLS_TEXT_RIGHTS"),
    ("clock", "SOURCE_CLOCK"), ("no-facts", "NO_CAPTURED_PRIOR_FACTS"),
])
def test_unverified_preparation_never_establishes_a_fact(tmp_path, fault, expected):
    f = feed(tmp_path)
    _, packet, _ = prepare(f.tracker.store, tmp_path)
    packet = deepcopy(packet)
    packet["known_at_utc"] = "2026-10-18T16:00:00Z"
    if fault == "span":
        packet["prior_fact_spans"][0]["exact_source_span"] = "A made-up release."
    if fault == "rights":
        packet["official_sources"][0]["url"] = "https://third-party.example/news.release/empsit.htm"
    if fault == "clock":
        packet["official_sources"][0]["published_at_utc"] = "2026-10-18T18:00:00Z"
    if fault == "no-facts":
        packet["prior_fact_spans"] = []
    record_pre_event_preparation(f.tracker.store, packet)
    with pytest.raises(ValueError, match=expected):
        preview_preparation_research(f.tracker.store, event_id=EVENT, cutoff_utc=NOW)


def test_preview_scope_event_identity_and_expiry(tmp_path):
    f = feed(tmp_path)
    prepare(f.tracker.store, tmp_path)
    with pytest.raises(ValueError, match="REVIEW_BEFORE_RELEASE"):
        preview_preparation_research(f.tracker.store, event_id=EVENT, cutoff_utc=NOW, article_type="EVENT_REVIEW")
    with pytest.raises(ValueError, match="EVENT_NOT_FOUND"):
        preview_preparation_research(f.tracker.store, event_id="another-event", cutoff_utc=NOW)
    with pytest.raises(ValueError, match="EVENT_HAS_PASSED"):
        preview_preparation_research(f.tracker.store, event_id=EVENT, cutoff_utc="2026-11-06T13:30:00Z")


def test_new_future_preparation_cannot_replace_frozen_native_input(tmp_path, monkeypatch):
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
    f = feed(tmp_path)
    prepare(f.tracker.store, tmp_path)
    f.pointer["preview_event_id"] = EVENT
    turn = NativeDesktopTurn(f.tracker.store, run_id="frozen-preview", output_dir=tmp_path / "out", owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as before:
        f.opportunity(output_dir=tmp_path / "out", cutoff_utc=NOW, run_id="frozen-preview",
            rolling_input={"headlines": []}, llm_invoke=turn)
    def forbidden(*a, **kw):
        raise AssertionError("Must restore the exact frozen preparation")
    monkeypatch.setattr("live_contentops.contentops_editorial_desk_v1.preview_preparation_research", forbidden)
    with pytest.raises(DesktopInputRequired) as after:
        f.opportunity(output_dir=tmp_path / "out", cutoff_utc=NOW, run_id="frozen-preview", llm_invoke=turn)
    assert before.value.request["request_sha256"] == after.value.request["request_sha256"]


def test_reviewed_background_reaches_next_preview_writer_without_rewriting_prior_preparation(tmp_path, monkeypatch):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.capital_chronicle_report_feed_v1 import _persist
    from live_contentops.contentops_editorial_desk_v1 import retain_reviewed_preview_background
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
    f = feed(tmp_path)
    _, _, original = prepare(f.tracker.store, tmp_path)
    before = f.tracker.store.get_outbox_message(original["message_id"])["payload"]
    run = "controlled-reviewed-background"
    _persist(f.tracker.store, "native-operation-binding-" + sha256_of(run),
        {"preview_event_id": EVENT}, "internal:native-operation-binding")
    result = {"qualified_article_count": 1, "article_identity": "controlled-background-identity",
        "article": {"title": "Controlled reviewed employment preview", "substack_body_markdown":
            "The reviewed background compares the two surveys without a future release value."},
        "simple_result": {"publication_lifecycle_plan": {"plan_hash": "controlled-plan"}},
        "evidence": [{"source_id": "SOURCE_6", "document_id": "controlled-retained-component-source",
            "url": "https://www.bls.gov/news.release/archives/empsit_10022026.htm",
            "publisher": "U.S. Bureau of Labor Statistics", "published_at_utc": "2026-10-02T12:30:00Z",
            "canonical_content_text": "The controlled retained component text remains available to the later preview writer.",
            "canonical_content_sha256": "controlled-component-content-hash"}], "media_assets": []}
    # A dossier is additive. Seven retained source spans must not be silently
    # cut back to the older six-document original-facts allowance.
    component_source = result["evidence"][0]
    result["evidence"] = [{**component_source, "document_id": component_source["document_id"] + str(i),
        "url": component_source["url"] + "?part=" + str(i),
        "source_reuse_constraints": {"scope": "ATTRIBUTED_ORIGINAL_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE"}}
        for i in range(7)]
    key = "cc-editorial-final-" + sha256_of(run)
    _persist(f.tracker.store, key, result, "internal:controlled-native-result")
    row = f.tracker.store.get_outbox_message(key)
    note = {"package_revision": native_review_revision(result),
        "final_visual_review": {"stage": "controlled-final-visual", "request_sha256": "controlled-review"}}
    with f.tracker.store.get_connection() as conn:
        conn.execute("INSERT INTO review_records VALUES (?,?,?,?,?,?)", ("controlled-background-review",
            row["work_item_id"], "NATIVE_DESKTOP_ARTICLE_REVIEW", "KEEP", json.dumps(note), "2026-10-18T16:00:00Z"))
    receipt = retain_reviewed_preview_background(f.tracker.store, event_id=EVENT, run_id=run)
    assert f.tracker.store.get_outbox_message(original["message_id"])["payload"] == before
    assert retain_reviewed_preview_background(f.tracker.store, event_id=EVENT, run_id=run)["message_id"] == receipt["message_id"]
    f.pointer["preview_event_id"] = EVENT
    monkeypatch.setattr(f, "pending", lambda **_: [])
    donor, observed = controlled_writer([]), []

    class WriterReached(Exception):
        pass

    def invoke(**kwargs):
        governed = kwargs["governed_input"]
        if "candidates" in governed:
            return donor(**kwargs)
        observed.extend(governed["source_pack"])
        raise WriterReached

    with pytest.raises(WriterReached):
        f.opportunity(output_dir=tmp_path / "post-freeze-consumer", cutoff_utc=NOW,
            run_id="controlled-next-event-preview", rolling_input={"headlines": []}, llm_invoke=invoke)
    backgrounds = [d["preview_preparation"]["reviewed_background"] for d in observed
        if d.get("preview_preparation", {}).get("reviewed_background")]
    assert len(backgrounds) == 1
    assert backgrounds[0]["article"] == result["article"]
    assert backgrounds[0]["article_revision"] == native_review_revision(result)
    assert backgrounds[0]["review_id"] == "controlled-background-review"
    assert backgrounds[0]["dossier_scenarios_added"] is False
    component = next(d for d in observed if d["document_id"] == "controlled-retained-component-source0")
    assert component["canonical_content_text"] == result["evidence"][0]["canonical_content_text"]
    assert component["url"] == result["evidence"][0]["url"]
    assert component["source_id"].startswith("SOURCE_")
    assert len([d for d in observed if d["document_id"].startswith("controlled-retained-component-source")]) == 7
