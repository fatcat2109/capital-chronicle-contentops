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
