"""Changed owner entry, exact Main identity and retained evidence permissions."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from live_contentops.v1_simple_gemini_newsroom_v1 import _candidate_universe
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch


def entry():
    path = Path(__file__).resolve().parents[1] / "scripts/run_native_desktop_editorial.py"
    spec = importlib.util.spec_from_file_location("native_owner_entry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_owner_request_resumes_frozen_binding_and_cannot_redirect(tmp_path):
    profile = {"schema_version": "contentops.native_desktop_operator_profile.v1",
        "editorial_output_root": str(tmp_path / "articles"),
        **{k: str(tmp_path / k) for k in ("store_path", "feed_pointer_path", "published_memory_store", "published_memory_output_root")}}
    request = "Explain the admitted evidence and its important limitations."
    module = entry()
    path, first = module.resolve_owner_operation(profile, operation_id="test-edition", request=request,
        now=datetime(2026, 10, 20, tzinfo=timezone.utc))
    assert json.loads(path.read_bytes())["editorial_request"] == request
    assert module.resolve_owner_operation(profile, operation_id="test-edition")[1] == first
    with pytest.raises(ValueError, match="REQUEST_CHANGED"):
        module.resolve_owner_operation(profile, operation_id="test-edition", request=request + " New scope")
    with pytest.raises(ValueError, match="BINDING_CHANGED"):
        module.resolve_owner_operation({**profile, "store_path": str(tmp_path / "other.sqlite3")}, operation_id="test-edition")
    with pytest.raises(ValueError, match="OPERATION_ID"):
        module.resolve_owner_operation(profile, operation_id="../outside", request=request)


def test_identical_first_fact_does_not_collapse_distinct_main_reports():
    text = "Capital Chronicle report update: A dated crude inventory draw is retained."
    rows = [{"headline_id": "cc-report:" + str(i) * 64, "headline_text": text,
        "external_content": {"report_editorial_context": {"report_id": "asset-report:" + asset, "report_version": version}}}
        for i, asset, version in ((1, "USOIL", 4), (2, "UKOIL", 2))]
    result = _candidate_universe({"headlines": rows}, [])
    assert len(result) == 2 and len({r["candidate_id"] for r in result}) == 2
    assert len(_candidate_universe({"headlines": [*rows, rows[0]]}, [])) == 2


def test_verified_retained_agency_spans_reach_epistemic_admission():
    root = Path(__file__).resolve().parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal23/retained_research"
    research = RetainedSourceResearch(root)
    result = research.evidence({"cluster_id": "retained-cftc", "headline_ids": ["goal21-metals-leverage"],
        "story_context": {"report_provenance": {"event_proposition": research.records["goal21-metals-leverage"]["headline_text"]}}},
        cutoff_utc="2026-10-20T15:00:00Z")
    assert result["status"] == "PASS"
    assert result["evidence_documents"][0]["public_claim_allowed"] is True
    assert result["evidence_documents"][0]["published_at_utc"] is None
    assert result["provenance"]["request_count_for_call"] == 0


def test_source_recovery_preserves_pending_request_and_rejects_answered_writer(tmp_path):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
    module = entry()
    research = Path(__file__).resolve().parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal23/retained_research"
    pointer = tmp_path / "feed.json"
    pointer.write_text(json.dumps({"research_root": str(research)}))
    binding = {"schema_version": module.BINDING_SCHEMA, "run_id": "source-recovery-control",
        "owner_manual_validation": True, "store_path": str(tmp_path / "state.sqlite3"),
        "output_dir": str(tmp_path / "out"), "feed_pointer_path": str(pointer),
        "published_memory_store": str(tmp_path / "memory.sqlite3"), "published_memory_output_root": str(tmp_path / "memory")}
    store = ContentOpsDurableStore(Path(binding["store_path"]))
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    store.create_work_item(story_id=work, work_item_id=work, title="Main-enriched newsroom opportunity", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"], owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        turn(logical_invocation_id=binding["run_id"] + ":write", prompt="controlled pending source pack",
            governed_input={"source_pack": []}, validator=lambda raw: (True, None, {}, None))
    expected = pending.value.request["request_sha256"]
    result = module.operation(binding, command="recover-sources", response={"expected_request_sha256": expected, "supporting_headline_ids": ["goal21-gas-storage"]})
    assert result["retained_selection"] is True
    assert turn.frozen_request("write") is None
    assert (Path(binding["output_dir"]) / "source-recovery-history" / expected / "desktop_request_write.json").is_file()
    assert turn.source_recovery()["supporting_headline_ids"] == ["goal21-gas-storage"]
    with pytest.raises(ValueError, match="UNANSWERED_WRITER"):
        module.operation(binding, command="recover-sources", response={"expected_request_sha256": expected, "supporting_headline_ids": ["goal21-gas-storage"]})


def test_utc_spellings_compare_without_changing_sealed_bytes():
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import _time
    assert _time("2026-10-20T15:54:22.185030Z") == _time("2026-10-20T15:54:22.185030+00:00")
    for bad in ("2026-10-20T15:54:22", "2026-10-20T15:54:22+01:00"):
        with pytest.raises(ValueError, match="UTC_TIME_REQUIRED"):
            _time(bad)


def test_new_source_editions_append_and_freeze_exact_records():
    from copy import deepcopy
    base = Path(__file__).resolve().parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018"
    old = RetainedSourceResearch(base / "goal23/retained_research")
    research = RetainedSourceResearch(base / "goal23/retained_research", editions_root=base / "goal27/source_editions")
    assert not research.gaps and len(research.records) == len(old.records) + 2
    assert all(research.records[k] == v for k, v in old.records.items())
    snapshot = research.frozen_snapshot()
    assert RetainedSourceResearch.from_frozen_snapshot(snapshot).records == research.records
    broken = deepcopy(snapshot)
    broken["records"]["goal27-gas-seasonal"]["headline_text"] += " invented"
    with pytest.raises(ValueError, match="SNAPSHOT_CHANGED"):
        RetainedSourceResearch.from_frozen_snapshot(broken)


def test_source_comparison_is_idempotent_and_blocks_old_prepared_handoff(tmp_path):
    from live_contentops.contentops_editorial_desk_v1 import record_story_source_review
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, canonical_bytes
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_editorial_v1 import prepare_reviewed_handoff
    base = Path(__file__).resolve().parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018"
    research = RetainedSourceResearch(base / "goal23/retained_research", editions_root=base / "goal27/source_editions")
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    work = "cc-opportunity-" + sha256_of("existing-story")
    store.create_work_item(story_id=work, work_item_id=work, title="Existing story", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    value = {"article_identity": "a" * 64, "qualified_article_count": 1,
        "model_execution_state": "NATIVE_DESKTOP_REQUEST_RETURN", "article": {"title": "Prior gas", "substack_body_markdown": "Prior dated storage", "story_identity": "gas"},
        "evidence": [{"canonical_content_text": "Stocks were above the seasonal level."}]}
    store.register_outbox_message(message_id="cc-editorial-final-" + sha256_of("existing-story"), work_item_id=work,
        destination="internal:cc-report-simple-result", payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    args = dict(run_id="existing-story", article_identity="a" * 64, review_operation_id="review-1", research=research,
        source_ids=["goal27-gas-seasonal"], attempts=[{"url": "https://www.eia.gov/naturalgas/weekly/supplement/", "status": "PASS"}],
        cutoff_utc="2026-10-21T00:00:00Z", reason="Seasonal injection comparator adds a different question.")
    before = len(store.list_outbox_messages())
    result = record_story_source_review(store, **args)
    assert result["decision"] == "MATERIAL_FOLLOW_UP"
    assert result["source_editions"][0]["period_relation"] == "SAME_PERIOD_ADDITIONAL_SEASONAL_COMPARATOR"
    assert record_story_source_review(store, **args) == result
    assert len(store.list_outbox_messages()) == before + 1
    with pytest.raises(ValueError, match="PREPARED_REVIEW_INVALIDATED"):
        prepare_reviewed_handoff(store, run_id="existing-story", output_dir=tmp_path)
    assert json.loads(store.get_outbox_message("cc-editorial-final-" + sha256_of("existing-story"))["payload"]) == value
    unchanged = {**args, "review_operation_id": "review-2"}
    value["evidence"][0]["canonical_content_text"] = research.records["goal27-gas-seasonal"]["headline_text"]
    store.finalize_outbox_payload_before_dispatch(message_id="cc-editorial-final-" + sha256_of("existing-story"), payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    assert record_story_source_review(store, **unchanged)["decision"] == "USE_UNCHANGED"


def test_oil_date_notice_excludes_unused_gas_context():
    from live_contentops.v1_simple_gemini_newsroom_v1 import native_source_date_notice
    pack = [
        {"source_id": "SOURCE_1", "published_at_utc": "2026-10-19T12:25:00Z",
         "published_at_source": "MAIN_REPORT_CUTOFF_NOT_SOURCE_RELEASE_TIME",
         "report_lineage": {"claims": [{"evidence": [{"observation_time_utc": "2026-10-09T00:00:00Z"}]}]}},
        {"source_id": "SOURCE_2", "published_at_utc": None},
        {"source_id": "SOURCE_3", "published_at_utc": "2026-10-15T00:00:00Z"},
    ]
    notice = native_source_date_notice(pack, {"SOURCE_1", "SOURCE_2"})
    assert "Observation: 2026-10-09" in notice
    assert "Main report cutoff: 2026-10-19" in notice
    assert "Source date: not supplied" in notice
    assert "2026-10-15" not in notice


def test_media_binding_keeps_dates_of_cited_sources_without_main_lineage(tmp_path):
    from hashlib import sha256
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_editorial_v1 import bind_editorial_media
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    work = "cc-opportunity-" + sha256_of("source-dates")
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled dated copy", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    key = "cc-editorial-final-" + sha256_of("source-dates")
    source = "https://www.federalreserve.gov/controlled-source"
    value = {"qualified_article_count": 1, "article_identity": "a" * 64,
        "article": {"substack_body_markdown": "Definition [[SOURCE:SOURCE_1]]. Convention [[SOURCE:SOURCE_4]]."},
        "evidence": [{"source_id": "SOURCE_1", "url": source, "published_at_utc": "2026-10-13T00:00:00Z"},
            {"source_id": "SOURCE_2", "url": "https://www.sec.gov/unused", "published_at_utc": "2026-09-01T00:00:00Z"},
            {"source_id": "SOURCE_4", "url": source, "published_at_utc": "2026-10-13T00:00:00Z"}]}
    store.register_outbox_message(message_id=key, work_item_id=work, destination="internal:cc-report-simple-result", payload=json.dumps(value), status="EDITORIAL_INTERNAL")
    asset = tmp_path / "controlled-asset"
    asset.write_bytes(b"test-only")
    bind_editorial_media(store, run_id="source-dates", article_identity="a" * 64,
        assets=[{"path": str(asset), "sha256": sha256(asset.read_bytes()).hexdigest(), "source_page_url": source,
            "caption": "Controlled source", "alt_text": "Controlled source", "underlying_source_rights_status": "public_domain"}])
    after = json.loads(store.get_outbox_message(key)["payload"])
    assert after["article"]["substack_body_markdown"] == value["article"]["substack_body_markdown"]
    assert "Source date: 2026-10-13" in after["article"]["source_date_notice"]
    assert "2026-09-01" not in after["article"]["source_date_notice"]


def test_prepared_review_rejects_changed_reader_dates(tmp_path):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, canonical_bytes
    from live_contentops.contentops_editorial_desk_v1 import record_native_article_review
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_editorial_v1 import prepare_reviewed_handoff
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    run_id = "dated-reader-package"
    work = "cc-opportunity-" + sha256_of(run_id)
    store.create_work_item(story_id=work, work_item_id=work, title="Dated article", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    key = "cc-editorial-final-" + sha256_of(run_id)
    result = {"model_execution_state": "NATIVE_DESKTOP_REQUEST_RETURN", "qualified_article_count": 1,
              "article_identity": "a" * 64, "article": {"source_date_notice": "Observation: 2026-10-09"},
              "simple_result": {"publication_lifecycle_plan": {"plan_hash": "b" * 64}}}
    store.register_outbox_message(message_id=key, work_item_id=work, destination="internal:cc-report-simple-result",
                                  payload=canonical_bytes(result).decode(), status="EDITORIAL_INTERNAL")
    review = record_native_article_review(store, run_id=run_id, article_identity="a" * 64,
        decision="KEEP", rationale="Reviewed the exact source dates and reader package.")
    assert review["article_metadata_sha256"] == sha256_of(result["article"])
    result["article"]["source_date_notice"] = "Observation: 2026-10-15"
    store.finalize_outbox_payload_before_dispatch(message_id=key, payload=canonical_bytes(result).decode(), status="EDITORIAL_INTERNAL")
    with pytest.raises(ValueError, match="NATIVE_REVIEW_REVISION_CHANGED"):
        prepare_reviewed_handoff(store, run_id=run_id, output_dir=tmp_path / "out")
