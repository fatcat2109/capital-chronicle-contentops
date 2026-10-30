import copy
import hashlib
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_desk_record_source_v1 import (
    desk_evidence, display_value, read_export, story_context, validate_article_citations,
)
from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, sha256_of
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

FIXTURE = Path(__file__).parent / "fixtures/desk_record_export_v1/desk_record_export_v1.fixture.json"
NOW = "2026-10-30T16:00:00Z"


def spec(path=FIXTURE):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "allow_fixture_private_preview": True}


def sources():
    return read_export(spec(), cutoff_utc=NOW)


def article():
    record = next(r for r in sources() if r["binding"]["record_id"] == "event:US_ECI_20261030")
    field = next(f for f in record["binding"]["fields"] if f["field_path"] == "/measures/eci_civilian_compensation_12m_nsa/actual")
    citation = {k: field[k] for k in ("citation", "value", "display", "decimals", "unit") if k in field}
    return {"title": "Dated compensation data", "substack_body_markdown":
        "Fixture, not current data. The retained annual rate is 3.4 percent. Analysis, not financial advice. "
        "Derived analysis attributed to the U.S. Bureau of Labor Statistics (BLS). No BLS emblem is used, and BLS does not endorse this publication.",
        "desk_record_citations": [citation]}


def test_exact_fixture_is_public_projected_before_record_candidates():
    records = sources()
    text = json.dumps(records)
    raw = json.loads(FIXTURE.read_bytes())
    assert all(sentinel not in text for sentinel in raw["fixture_sentinels"])
    assert "myfxbook" not in text and "MARKET_CONSENSUS_PRIVATE_ONLY" not in text
    assert "surprise_vs_expectation" not in text and "options_positioning" not in text
    assert all(f["rights_class"] != "OFFICIAL_SOURCE_CONTRACT_PENDING" for r in records for f in r["binding"]["fields"])
    assert any("eci_civilian_compensation_12m_nsa/actual" in f["citation"] for r in records for f in r["binding"]["fields"])


@pytest.mark.parametrize("change,error", [
    ({"sha256": "0" * 64}, "DESK_EXPORT_BYTES_MISMATCH"),
    ({"allow_fixture_private_preview": False}, "DESK_FIXTURE_PRIVATE_PREVIEW_ONLY"),
])
def test_pin_and_fixture_gate_fail_closed(change, error):
    with pytest.raises(ValueError, match=error):
        read_export({**spec(), **change}, cutoff_utc=NOW)


def test_cutoff_does_not_admit_a_later_export():
    with pytest.raises(ValueError, match="DESK_EXPORT_AFTER_CUTOFF"):
        read_export(spec(), cutoff_utc="2026-10-30T12:00:00Z")


@pytest.mark.parametrize("change,error", [("integrity", "INTEGRITY"), ("public_consensus", "SCHEMA"),
    ("text_leak", "REFERENCE_CLOCK_OR_PUBLIC_TEXT"), ("clock", "REFERENCE_CLOCK_OR_PUBLIC_TEXT")])
def test_mutated_producer_input_is_refused(tmp_path, change, error):
    doc = json.loads(FIXTURE.read_bytes())
    if change == "public_consensus":
        card = next(c for c in doc["event_cards"] if c["event_id"] == "US_NFP_20261106")
        card["measures"][0]["expectation"]["visibility"] = "public"
    elif change == "text_leak":
        doc["asset_dossiers"][0]["headline_analysis"].update(value="In line with consensus", missing_cause=None)
        doc["asset_dossiers"][0]["headline_analysis"].pop("missing_cause", None)
    elif change == "clock":
        doc["sources"][0]["known_at_utc"] = "2026-10-31T12:00:00Z"
    doc["integrity"]["content_sha256"] = sha256_of({k:v for k,v in doc.items() if k != "integrity"})
    if change == "integrity":
        doc["integrity"]["content_sha256"] = "a" * 64
    path = tmp_path / "export.json"; path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        read_export(spec(path), cutoff_utc=NOW)


def test_desk_import_is_report_truth_with_no_new_confirmation_or_source_request():
    records = sources()
    result = desk_evidence(records, {"headline_ids": [records[0]["headline_id"]]})
    assert result["epistemic_state"]["event_truth_supported"] is False
    assert result["provenance"]["request_count_for_call"] == 0
    assert result["evidence_documents"][0]["desk_record_binding"] == records[0]["binding"]
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack
    pack = _source_pack(result["evidence_documents"])
    assert pack and pack[0]["desk_record_binding"] == records[0]["binding"]
    bad = copy.deepcopy(result["evidence_documents"])
    bad[0]["desk_record_binding"]["record_id"] = "changed"
    assert _source_pack(bad) == []


def test_exact_citations_retain_value_and_display_decimals():
    result = validate_article_citations(article(), sources())
    assert result["citation_count"] == 1 and result["fixture"]
    assert display_value({"value": 1.0, "decimals": 1}) == "1.0"
    with pytest.raises(ValueError, match="PRECISION"):
        display_value({"value": 1.05, "decimals": 1})


@pytest.mark.parametrize("change,error", [("value", "VALUE_OR_PRECISION"), ("display", "VALUE_OR_PRECISION"),
    ("prose", "UNBOUND_OR_CHANGED_NUMBER"), ("notice", "FIXTURE_NOTICE"), ("private_term", "PRIVATE_DERIVATION")])
def test_article_cannot_change_values_or_hide_fixture_state(change, error):
    value = article()
    if change == "value": value["desk_record_citations"][0]["value"] = 3.5
    elif change == "display": value["desk_record_citations"][0]["display"] = "3.40"
    elif change == "prose": value["substack_body_markdown"] = value["substack_body_markdown"].replace("3.4", "3.5")
    elif change == "notice": value["substack_body_markdown"] = value["substack_body_markdown"].replace("Fixture, not current data.", "")
    else: value["title"] = "Rate beats consensus"
    with pytest.raises(ValueError, match=error): validate_article_citations(value, sources())


def test_feed_freezes_projected_desk_records_in_the_existing_native_request(tmp_path):
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
    store = ContentOpsDurableStore(tmp_path / "copy.sqlite3")
    feed = MainReportFeed(LatestReportDeliveryTracker(store), {"desk_record_exports": [spec()]}, headline_paths=[])
    turn = NativeDesktopTurn(store, run_id="desk-record-fixture", output_dir=tmp_path / "article", owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        feed.opportunity(output_dir=tmp_path / "article", cutoff_utc=NOW, run_id=turn.run_id,
            rolling_input={"headlines": []}, llm_invoke=turn)
    request = json.dumps(pending.value.request)
    assert "event:US_ECI_20261030" in request
    assert "FIXTURE-SENTINEL-PRIVATE-7Q4" not in request
    assert "myfxbook" not in request
    frozen = store.get_outbox_message("native-current-input-" + sha256_of(turn.run_id))
    assert json.loads(frozen["payload"])["feed_scan"]["desk_record_sources"]


def test_story_context_keys_assets_events_and_current_reviewed_articles():
    record = next(r for r in sources() if r["binding"]["record_id"] == "asset:USDJPY")
    final = {"qualified_article_count": 1, "article_identity": "reviewed-id", "article": {"title": "Reviewed dated context"},
        "desk_record_source_bindings": [record["binding"]]}
    rows = [{"destination": "internal:cc-report-feed", "payload": json.dumps({"desk_record_sources": [record]})},
        {"destination": "internal:cc-report-simple-result", "payload": json.dumps(final)}]
    reviews = [{"notes": json.dumps({"article_identity": "reviewed-id"}), "reviewer_ref": "NATIVE_DESKTOP_ARTICLE_REVIEW",
        "decision": "KEEP", "review_id": "exact-review"}]
    story = story_context(rows, reviews)[0]
    assert story["asset_ids"] == ["USDJPY"] and story["event_ids"] == ["US_ECI_20261030"]
    assert story["package_history"][0]["review_id"] == "exact-review"
    assert story["disposition"] == "NO_MATERIAL_CHANGE" and story["publication_state"] == "UNPUBLISHED_RESEARCH"
    assert story_context(rows, [])[0]["package_history"] == []
    # An unrelated export-level change cannot invalidate this exact record.
    newer = copy.deepcopy(record)
    newer["binding"]["projection_sha256"] = "a" * 64
    rows.append({"destination": "internal:cc-report-feed", "payload": json.dumps({"desk_record_sources": [newer]})})
    assert story_context(rows, reviews)[0]["disposition"] == "NO_MATERIAL_CHANGE"
    newer["binding"]["record_content_sha256"] = "b" * 64
    rows[-1]["payload"] = json.dumps({"desk_record_sources": [newer]})
    assert story_context(rows, reviews)[0]["disposition"] == "FOLLOW_UP"


def test_fixture_is_refused_before_publication_preparation(tmp_path, monkeypatch):
    from live_contentops import native_desktop_publication_v1 as publication
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.validated_native_review",
        lambda *a, **kw: ({"desk_record_validation": {"fixture": True}}, {}, {}))
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.validate_release_media",
        lambda *_: pytest.fail("fixture must stop before media or preparation"))
    with pytest.raises(ValueError, match="DESK_FIXTURE_PRIVATE_PREVIEW_ONLY"):
        publication.prepare_native_publication(None, {"run_id": "fixture"})


@pytest.mark.parametrize("key", ["attribution", "disclaimer"])
def test_mandatory_source_credit_is_preserved(key):
    value = article()
    source = next(s for r in sources() for s in r["binding"]["sources"] if s["source_id"] == "src:bls:eci:2026q3")
    if key == "disclaimer":
        value["substack_body_markdown"] += " " + source["attribution"]
    value["substack_body_markdown"] = value["substack_body_markdown"].replace(source[key], "")
    with pytest.raises(ValueError, match="SOURCE_" + key.upper()):
        validate_article_citations(value, sources())


def test_selected_event_joins_only_explicitly_linked_public_context():
    records = sources()
    event = next(r for r in records if r["binding"]["record_id"] == "event:US_ECI_20261030")
    result = desk_evidence(records, {"headline_ids": [event["headline_id"]]})
    docs = result["evidence_documents"]
    assert {d["desk_record_binding"]["record_id"] for d in docs} == {
        "event:US_ECI_20261030", "asset:USDJPY", "asset:XAUUSD", "series:bls:eci:civilian-compensation-3m"}
    series = next(d["desk_record_binding"] for d in docs if d["desk_record_binding"]["record_type"] == "data_series")
    assert series["series"]["series_code"] == "CIS1010000000000Q"
    assert series["series"]["window"] == {"start": "2024-Q1", "end": "2026-Q3"}
    assert "BC_10YEAR" not in json.dumps(docs)



def test_actual_narrow_desk_news_routes_without_relabelling_analysis():
    from live_contentops.native_newsroom_volume_v1 import photo_less_brief, permitted_photo_less_skip, volume_policy
    value = article()
    value.update(resolved_article_mode="DATA_OR_DOCUMENT_LENS", volume_policy=volume_policy(NOW), volume_policy_cutoff_utc=NOW,
        visual_editorial_decision={"story_kind": "NEWS", "accepted_article_mode": "DATA_OR_DOCUMENT_LENS",
            "reader_form": "NARROW_FACTUAL_NEWS_BRIEF", "charts": [],
            "exception_reason": "Only the retained release figures are reported in this compact factual brief. No macro thesis or asset-price inference is made."})
    assert photo_less_brief(value)
    binding = {k:value[k] for k in ("resolved_article_mode", "visual_editorial_decision", "desk_record_citations")}
    plan = {"photo_less_news_policy": True, "volume_policy": volume_policy(NOW), "volume_policy_cutoff_utc": NOW,
        "resolved_article_mode": "DATA_OR_DOCUMENT_LENS", "photo_less_desk_record_binding": binding,
        "skipped_derivative_destinations": [{"destination": "instagram_business", "status": "SKIPPED_PHOTOLESS_NEWS_POLICY"}]}
    assert permitted_photo_less_skip(plan)
    changed = copy.deepcopy(value); changed["visual_editorial_decision"]["story_kind"] = "ANALYSIS"
    assert not photo_less_brief(changed)
    changed = copy.deepcopy(value); changed["visual_editorial_decision"].pop("reader_form")
    assert not photo_less_brief(changed)
    assert not photo_less_brief({**value, "desk_record_citations": []})
    assert not permitted_photo_less_skip({k:v for k,v in plan.items() if k != "photo_less_desk_record_binding"})



def chart_packet():
    record = next(r for r in sources() if r["binding"]["record_type"] == "data_series")
    doc = desk_evidence([record], {"headline_ids": [record["headline_id"]]})["evidence_documents"][0]
    binding = doc["desk_record_binding"]
    field = next(f for f in binding["fields"] if f["field_path"] == "/observations")
    point = field["value"][0]
    packet = {"asset_id": "exact-eci-series", "chart_type": "line", "question": "What does the retained quarterly history show?",
        "title": "Retained ECI series", "unit": binding["series"]["unit"],
        "source_caption": "U.S. Bureau of Labor Statistics (BLS), 2024-Q1 to 2026-Q3. Fixture, not current data.",
        "desk_series": [{"document_id": doc["document_id"], "export_id": binding["export_id"], "record_id": binding["record_id"],
            **binding["series"], "captures": [{k:source[k] for k in ("source_id", "raw_sha256", "known_at_utc")} for source in binding["sources"]]}],
        "series": [{"label": "Civilian compensation", "points": [{"period": point["period"], "value": point["value"],
            "transform": "IDENTITY", "observation_kind": "ACTUAL", "inputs": [{"document_id": doc["document_id"],
                "support_excerpt": doc["canonical_content_text"], "source_period_text": point["period"], "prepared_period": point["period"],
                "source_content_sha256": doc["canonical_content_sha256"], "metric": "Civilian compensation",
                "unit": "percent", "period_basis": "Exact producer series observation", "value_text": "1.0"}]}]}]}
    return copy.deepcopy(packet), doc


def test_desk_chart_exact_series_window_capture_and_precision_use_existing_owner():
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _editorial_data_values, editorial_chart_source_links
    packet, doc = chart_packet()
    assert _editorial_data_values(packet, [doc]) == [[1.0]]
    assert all(link["url"].startswith("https://") for link in editorial_chart_source_links(packet, [doc]))
    assert {link["url"] for link in editorial_chart_source_links(packet, [doc])} == {
        "https://www.bls.gov/news.release/eci.nr0.htm", "https://api.bls.gov/publicAPI/v2/timeseries/data/"}


@pytest.mark.parametrize("change,error", [("event", "DATA_SERIES"), ("window", "WINDOW_OR_CAPTURE"),
    ("capture", "WINDOW_OR_CAPTURE"), ("value", "EXACT_OBSERVATION"), ("precision", "EXACT_OBSERVATION"),
    ("period", "EXACT_OBSERVATION"), ("caption", "VISIBLE_WINDOW")])
def test_desk_chart_cannot_use_event_measures_or_change_series_bindings(change, error):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _editorial_data_values
    packet, doc = chart_packet()
    if change == "event": doc["desk_record_binding"]["record_type"] = "event_card"
    elif change == "window": packet["desk_series"][0]["window"]["end"] = "2026-Q4"
    elif change == "capture": packet["desk_series"][0]["captures"][0]["raw_sha256"] = "0" * 64
    elif change == "value": packet["series"][0]["points"][0]["value"] = 1.1
    elif change == "precision": packet["series"][0]["points"][0]["inputs"][0]["value_text"] = "1"
    elif change == "period": packet["series"][0]["points"][0]["period"] = "2026-Q3"
    else: packet["source_caption"] = "U.S. Bureau of Labor Statistics (BLS)"
    with pytest.raises(ValueError, match=error): _editorial_data_values(packet, [doc])



def test_desk_field_contract_does_not_invent_legacy_report_scope_notice():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _epistemic_copy_blockers
    records = sources()
    record = next(r for r in records if r["binding"]["record_id"] == "event:US_ECI_20261030")
    evidence = desk_evidence(records, {"headline_ids": [record["headline_id"]]})
    value = article()
    pack = [{"desk_record_binding": d["desk_record_binding"]} for d in evidence["evidence_documents"]]
    legacy = _epistemic_copy_blockers(value, [], evidence["epistemic_state"])
    current = _epistemic_copy_blockers(value, [], evidence["epistemic_state"], source_pack=pack)
    assert "report_horizon_proxy_cost_limits_missing" in legacy
    assert "report_horizon_proxy_cost_limits_missing" not in current
    value["desk_record_citations"][0]["display"] = "3.40"
    assert "DESK_ARTICLE_VALUE_OR_PRECISION_CHANGED" in _epistemic_copy_blockers(value, [], evidence["epistemic_state"], source_pack=pack)



def test_dated_new_desk_writer_resumes_exact_prompt_but_refuses_changed_prompt(tmp_path):
    from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn
    from live_contentops.native_newsroom_volume_v1 import volume_policy
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "controlled-dated-writer"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled prompt", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    turn.volume_policy = volume_policy(NOW)
    args = {"logical_invocation_id": run + ":write", "prompt": "Exact controlled request",
        "governed_input": {"CONTROLLED_TEST_ONLY": True}, "validator": lambda raw: (True, None, json.loads(raw), None)}
    with pytest.raises(DesktopInputRequired) as first: turn(**args)
    with pytest.raises(DesktopInputRequired) as resumed: turn(**args)
    assert first.value.request == resumed.value.request
    assert "DATED J8:" in resumed.value.request["prompt"]
    with pytest.raises(ValueError, match="CONFLICT"): turn(**{**args, "prompt": "Changed controlled request"})


def test_series_observation_display_retains_declared_trailing_zeroes():
    assert display_value({"value": [{"period": "2026-01-01", "value": 4.7}]}, observations_decimals=2) == '[{"period":"2026-01-01","value":4.70}]'



def test_latest_public_snapshot_removes_withdrawn_fields_from_current_story_memory():
    record = sources()[0]
    rows = [{"destination": "internal:cc-report-feed", "payload": json.dumps({"desk_record_sources": [record]})},
        {"destination": "internal:cc-report-feed", "payload": json.dumps({"desk_record_sources": []})}]
    assert story_context(rows) == []
    assert record["binding"]["fields"]  # History input remains intact.


def test_compiler_preserves_fixture_and_required_source_notice_without_exposing_internal_citations():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article
    value = article()
    value.update(fixture=True, reader_first_version="DATA_JOURNALISM_V1", desk_record_source_notices=[
        "Derived analysis attributed to the U.S. Bureau of Labor Statistics (BLS). No BLS emblem is used, and BLS does not endorse this publication."])
    compiled = _reader_safe_native_article(value, article_mode="DATA_OR_DOCUMENT_LENS")
    assert compiled["desk_record_citations"] == value["desk_record_citations"]
    assert "Fixture, not current data" in compiled["editorial_scope_notice"]
    assert value["desk_record_source_notices"][0] in compiled["editorial_scope_notice"]
    assert "fixture-desk-record-export" not in compiled["substack_body_markdown"]



@pytest.mark.parametrize("method", ["register_plan", "_execute_plan"])
def test_sole_coordinator_refuses_fixture_before_recovery_or_transports(method):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    coordinator = object.__new__(DurablePublicationCoordinator)
    # No store, runtime or readiness is installed: fixture check must come first.
    with pytest.raises(ValueError, match="DESK_FIXTURE_PRIVATE_PREVIEW_ONLY"):
        getattr(coordinator, method)("not-a-real-work-item", {"fixture_source_context": True})



def test_series_identity_change_is_a_material_record_revision(tmp_path):
    original = next(r for r in sources() if r["binding"]["record_type"] == "data_series")
    doc = json.loads(FIXTURE.read_bytes())
    doc["data_series"][0]["series_code"] = "CONTROLLED_DIFFERENT_SERIES_NOT_REAL_DATA"
    doc["integrity"]["content_sha256"] = sha256_of({k:v for k,v in doc.items() if k != "integrity"})
    path = tmp_path / "controlled-fixture.json";path.write_text(json.dumps(doc), encoding="utf-8")
    changed = next(r for r in read_export(spec(path), cutoff_utc=NOW) if r["binding"]["record_id"] == original["binding"]["record_id"])
    assert changed["binding"]["record_content_sha256"] != original["binding"]["record_content_sha256"]
