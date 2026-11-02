"""CC-117: retained incident replay and disposable source/publication owners only."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_desktop_editorial_v1 import admit_pre_writer_source_recovery
from live_contentops.native_desktop_publication_v1 import prepare_native_publication
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    ARTICLE_SCHEMA_VERSION, _candidate_packet_and_preselection, _validate_article_against_source_pack,
    SimpleGeminiNewsroomError,
)
from tests.test_native_live_source_recovery_v1 import seeded
from tests.test_native_newsroom_owner_operation_v1 import entry
from tests.test_native_text_first_v1 import brief_packet
from tests.test_native_desktop_publication_v1 import composed, finish
from tests.test_v1_simple_gemini_newsroom_v1 import _headlines

INCIDENT = Path(__file__).resolve().parents[1] / "docs/publisher/CC-117/recorded-hold.json"


def fed_copy(snapshot):
    source = snapshot["selected_source_pack"][0]
    text = "The Federal Reserve's October 28 target range was 3.75 percent to 4.0 percent."
    title = "Background: The Fed's October 28 target range"
    article = {"title": title, "dek": text, "search_title": title,
        "meta_description": text, "social_hook": "Background: " + text,
        "substack_body_markdown": "## The dated policy setting\n\n" + text + " [[SOURCE:SOURCE_1]]"}
    return {"schema_version": ARTICLE_SCHEMA_VERSION, "article": article,
        "cited_sources": [{k: source[k] for k in ("source_id", "url", "publisher", "published_at_utc")}],
        "material_claim_bindings": [{"claim_id": "retained-" + field, "claim_text": value,
            "claim_kind": "FACT", "source_id": "SOURCE_1",
            "support_excerpt": source["canonical_content_text"], "attribution_required": True}
            for field, value in article.items() if field != "substack_body_markdown"],
        "public_write_attempted": False}


def test_recorded_2_nov_hold_reaches_text_publication_with_controlled_transports(tmp_path, monkeypatch):
    snapshot = json.loads(INCIDENT.read_bytes())
    assert snapshot["original_source_requests"] == 0
    assert snapshot["original_selection"]["ordered_candidate_plan"][0]["article_mode"] == "DATA_OR_DOCUMENT_LENS"
    assert "2-5" in snapshot["original_media_plan"]["story_plan"]["chart_plan"]["count_decision"]
    assert snapshot["original_outcome"]["outcome"] == "HOLD"
    rolling = _headlines(1)
    rolling["headlines"][0].update(snapshot["original_selected_candidate"])
    sources = [{**s, "source_url": s["url"], "public_claim_allowed": True}
        for s in snapshot["selected_source_pack"]]
    evidence = {"status": "PASS", "evidence_documents": sources,
        "epistemic_state": snapshot["selected_epistemic_state"],
        "provenance": {"request_count_for_call": 0}}
    # A new, controlled short background choice; never amend the saved MAX hold.
    store, binding, rollout, result, stages, calls = brief_packet(tmp_path, monkeypatch,
        rolling_override=rolling, evidence_override=evidence, writer_output=fed_copy(snapshot),
        cutoff=snapshot["cutoff_utc"])
    assert result["qualified_article_count"] == 1 and result["media_assets"] == []
    assert stages == ["select", "write"] and calls == ["source"]
    assert result["article"]["title"].startswith("Background:")
    for preview in result["previews"]:
        if preview["destination"] in {"x", "telegram", "discord", "threads", "linkedin"}:
            assert "Background:" in json.dumps(preview["payload"])
    prepare_native_publication(store, binding)
    operation, executor, transport = composed(store, binding, rollout, monkeypatch)
    value, simulated = finish(operation, executor)
    assert value["publication"]["state"] == "RECONCILED"
    assert "substack" in simulated and set(simulated + transport.calls) == {
        "substack", "x", "telegram", "discord", "threads", "linkedin"}
    assert value["publication"]["destinations"][0]
    report = {"scope": "CONTROLLED_RETROSPECTIVE_TEST_NOT_NATIVE_OR_LIVE_PUBLICATION",
        "original_run_id": snapshot["run_id"], "original_hold_preserved": True,
        "replayed_state": value["publication"]["state"], "native_stages": stages,
        "source_request_count": 0, "external_source_calls": 0, "external_public_writes": 0,
        "simulated_destinations": sorted(simulated + transport.calls),
        "source_pack_sha256": sha256_of(snapshot["selected_source_pack"])}
    (tmp_path / "replay-result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def test_current_news_precedes_old_easy_sources_before_packet_cap():
    rolling = _headlines(40)
    for row in rolling["headlines"]:
        row["source_timestamp_utc"] = "2026-10-28T18:00:00Z"
        row["revision_at_utc"] = "2026-11-02T13:59:00Z"
    rolling["headlines"][-1]["source_timestamp_utc"] = "2026-11-02T13:00:00Z"
    candidates, evidence = _candidate_packet_and_preselection(rolling, [],
        source_resolvability_first=True, freshness_cutoff_utc="2026-11-02T14:00:00Z")
    assert len(candidates) == 32
    assert candidates[0]["headline_id"] == rolling["headlines"][-1]["headline_id"]
    assert candidates[0]["editorial_freshness"]["disposition"] == "CURRENT_WITHIN_24H"
    assert all(c["editorial_freshness"]["disposition"] == "RETAINED_BACKGROUND" for c in candidates[1:])
    assert evidence["freshness_priority_applied_before_packet_cap"]


def test_old_source_requires_background_label():
    snapshot = json.loads(INCIDENT.read_bytes())
    candidate = deepcopy(snapshot["original_selected_candidate"])
    candidate["editorial_freshness"] = {"disposition": "RETAINED_BACKGROUND"}
    output = fed_copy(snapshot)
    output["article"]["title"] = "The Fed's October 28 target range"
    with pytest.raises(SimpleGeminiNewsroomError) as refused:
        _validate_article_against_source_pack(output, snapshot["selected_source_pack"],
            selected_candidate=candidate, article_mode="BREAKING_BRIEF")
    assert "retained_background_label_required:title" in refused.value.details


def test_scheduled_plan_requests_missing_facts_then_uses_existing_admission(tmp_path, monkeypatch):
    turn, binding, response, run, calls = seeded(tmp_path, monkeypatch, used=0, scheduled=True, needs_sources=True)
    pending = entry().operation(binding, command="media-plan")
    assert pending["stage"] == "sources"
    assert pending["coordinator_action"]["action"] == "EXECUTE_BOUNDED_SOURCE_REQUESTS"
    assert not turn.frozen_request("visual-edit")
    path = turn.root / "source_preparation_required.json"
    preserved = path.read_bytes()
    assert entry().operation(binding, command="media-plan")["request_sha256"] == pending["request_sha256"]
    assert path.read_bytes() == preserved
    response["expected_source_request_sha256"] = pending["request_sha256"]
    admitted = entry().operation(binding, command="recover-sources", response=response)
    assert admitted["source_request_count"] == 1 and admitted["source_request_limit"] == 10
    from live_contentops.native_newsroom_volume_v1 import window_progress
    assert window_progress(turn.store, [(binding, None)])["source_request_count"] == 1
    assert entry().operation(binding, command="recover-sources", response=response) == admitted
    from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired
    with pytest.raises(DesktopInputRequired):
        run()
    assert len(calls) == 1  # Only the original zero-request fixture source walk.
    assert entry().operation(binding, command="media-plan")["stage"] == "visual-edit"
    assert path.read_bytes() == preserved and turn.store.list_platform_dispatches() == []


@pytest.mark.parametrize("fault", ["unregistered", "changed_request", "budget", "different_url", "max_frozen"])
def test_scheduled_source_recovery_rejects_wrong_identity_budget_or_freeze(tmp_path, monkeypatch, fault):
    turn, binding, response, _, _ = seeded(tmp_path, monkeypatch, used=0, scheduled=True, needs_sources=True)
    pending = entry().operation(binding, command="media-plan")
    response["expected_source_request_sha256"] = pending["request_sha256"]
    if fault == "unregistered":
        binding["window_id"] = "another-window"
    elif fault == "changed_request":
        response["expected_source_request_sha256"] = "0" * 64
    elif fault == "budget":
        turn.source_request_count_at_start = 10
    elif fault == "different_url":
        response["additional_source_requests"][0]["url"] += "?other"
    elif fault == "max_frozen":
        turn._put("visual-edit", "request", {"request_sha256": "frozen"})
    before = turn.store.list_outbox_messages()
    with pytest.raises(ValueError):
        admit_pre_writer_source_recovery(turn, binding, response)
    assert turn.store.list_outbox_messages() == before


def test_actual_source_access_failure_records_first_cause_and_spending(tmp_path, monkeypatch):
    turn, binding, response, _, _ = seeded(tmp_path, monkeypatch, used=0, scheduled=True, needs_sources=True)
    pending = entry().operation(binding, command="media-plan")
    response.update(expected_source_request_sha256=pending["request_sha256"], source_acquisition_failed=True)
    capture = turn.root / "actual-error.json"
    capture.write_text('{"error":"CONTROLLED publisher access refused"}', encoding="utf-8")
    response["additional_source_requests"][0].update(capture_path=str(capture),
        capture_sha256=sha256(capture.read_bytes()).hexdigest(), status="SOURCE_ACCESS_RESTRICTED",
        error="CONTROLLED publisher access refused")
    result = entry().operation(binding, command="recover-sources", response=response)
    assert result["primary_cause"] == "SOURCE_ACCESS_RESTRICTED" and result["source_request_count"] == 1
    from live_contentops.native_newsroom_volume_v1 import window_progress
    assert window_progress(turn.store, [(binding, None)])["source_request_count"] == 1
    assert turn.current_story_outcomes()[0]["provenance"]["actual_attempts"] == response["additional_source_requests"]
    assert turn.store.list_platform_dispatches() == []
