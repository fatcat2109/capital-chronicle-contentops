"""Isolated context attachment/replay contracts; no native editorial or live proof."""
import json
from copy import deepcopy
from hashlib import sha256

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
from live_contentops.v1_simple_gemini_newsroom_v1 import run_v1_simple_gemini_newsroom, SimpleGeminiNewsroomError
from test_native_newsroom_owner_operation_v1 import entry
from test_reader_first_data_journalism_v1 import decision
from test_native_editorial_media_standard_v1 import controlled_release_packet
from test_v1_simple_gemini_newsroom_v1 import CUTOFF, _headlines, _evidence_result, _selection


def seeded(tmp_path, monkeypatch, change=None):
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "selected-context-test"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    binding = {"schema_version": entry().BINDING_SCHEMA, "run_id": run, "cutoff_utc": CUTOFF,
               "owner_manual_validation": True, "store_path": str(store.db_path),
               "output_dir": str(tmp_path / "output"), "feed_pointer_path": str(tmp_path / "feed.json"),
               "published_memory_store": str(tmp_path / "memory.sqlite3"),
               "published_memory_output_root": str(tmp_path / "memory")}
    turn = NativeDesktopTurn(store, run_id=run, output_dir=binding["output_dir"], owner_manual_validation=True)
    observation = {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol", "reasoning_effort": "low",
                   "invocation_id": "controlled-context", "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}
    evidence = _evidence_result(request_count=0)
    evidence["evidence_documents"][0]["publisher"] = "Reuters — controlled"
    args = dict(output_dir=turn.root, cutoff_utc=CUTOFF, rolling_input=_headlines(1), published_memory=[],
                llm_invoke=turn, evidence_loader=lambda _: deepcopy(evidence), run_id=run)
    with pytest.raises(DesktopInputRequired) as pending:
        run_v1_simple_gemini_newsroom(**args)
    candidate = pending.value.request["governed_input"]["candidates"][0]["candidate_id"]
    selected = _selection(candidate)
    selected["ordered_candidate_plan"][0].update(primary_reader_question="What changed in this financing plan?",
        evidence_plan="Read the exact admitted company financing report and relevant dated context.",
        angle="Financing detail and the earlier dated commitment context.")
    turn.submit("select", {"request_sha256": pending.value.request["request_sha256"],
                           "output": selected, "invocation_observation": observation})
    with pytest.raises(DesktopInputRequired) as media:
        run_v1_simple_gemini_newsroom(**args)
    assert media.value.request["stage"] == "media-plan"
    source_pack = media.value.request["source_pack"]
    visual = {"request_sha256": "controlled-visual", "stage": "visual-edit",
              "governed_input": {"source_packet": {"source_pack": source_pack}}}
    turn._put("visual-edit", "request", visual)
    choice = decision("NEWS", 0)
    choice.update(contextual_photo_ids=["controlled-photo"],
        exception_reason="Controlled narrow news fixture has no quantitative series; no invented chart is useful.")
    choice["channel_media"] = {d: ["controlled-photo"] for d in choice["channel_media"]}
    turn._put("visual-edit", "response", {"request_sha256": visual["request_sha256"], "output": choice,
               "invocation_observation": {**observation, "reasoning_effort": "max"}})
    text = "An earlier dated financing report left individual commitments unresolved."
    record = {"headline_id": "prior-context", "source_identity": "example.org",
        "source_timestamp_utc": "2026-08-20T00:00:00Z", "known_at_utc": "2026-08-20T01:00:00Z",
        "retrieval_time_utc": "2026-08-20T01:00:00Z", "revision_at_utc": "2026-08-20T02:00:00Z",
        "permitted_source_text": text, "source_permissions": {"MODEL_INPUT_ALLOWED": True,
            "scope": "ATTRIBUTED_REPORTED_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE"},
        "document": {"source_url": "https://example.org/dated-financing", "publisher": "Controlled prior report",
            "published_at_utc": "2026-08-20T00:00:00Z", "public_claim_allowed": True, "report_truth_only": True}}
    if change:
        change(record)
    research = {"root": str(tmp_path), "records": {"prior-context": record}, "revision": "controlled", "gaps": []}
    snapshot = {**research, "snapshot_sha256": sha256_of(research)}
    store.register_outbox_message(message_id="native-current-input-" + sha256_of(run), work_item_id=work,
        destination="internal:native-current-input", payload=canonical_bytes({"run_id": run,
            "cutoff_utc": CUTOFF, "research": snapshot}).decode(), status="EDITORIAL_INTERNAL")
    response = {"selected_story_context": True, "expected_request_sha256": visual["request_sha256"],
                "candidate_id": candidate, "supporting_headline_ids": ["prior-context"],
                "match_reason": "Related financing commitment thesis at an earlier dated source, not proof of this current event."}
    return turn, binding, response, args


def test_context_reaches_frozen_writer_without_reselection_or_new_acquisition(tmp_path, monkeypatch):
    turn, binding, response, args = seeded(tmp_path, monkeypatch)
    selection = turn.frozen_request("select"), turn._get("select", "response")
    visual = turn.frozen_request("visual-edit"), turn.visual_response()
    result = entry().operation(binding, command="recover-sources", response=response)
    before = len(turn.store.list_outbox_messages())
    assert entry().operation(binding, command="recover-sources", response=response) == result
    assert len(turn.store.list_outbox_messages()) == before
    assert result["new_source_requests"] == 0 and turn.frozen_request("write") is None
    # Synthetic photo/rights fixture permits writer freeze; no real editorial acceptance is claimed.
    _, photo, _ = controlled_release_packet(tmp_path / "controlled-media")
    turn.store.register_outbox_message(message_id="native-editorial-media-plan-" + sha256_of(turn.run_id),
        work_item_id=turn.work, destination="internal:controlled-media", status="EDITORIAL_INTERNAL",
        payload=canonical_bytes({"source_request_sha256": "controlled", "assets": [photo]}).decode())
    with pytest.raises(DesktopInputRequired) as pending:
        run_v1_simple_gemini_newsroom(**args)
    assert pending.value.request["stage"] == "write"
    governed = pending.value.request["governed_input"]
    current, history = governed["source_pack"]
    assert [current["source_id"], history["source_id"]] == ["SOURCE_1", "SOURCE_2"]
    assert current == visual[0]["governed_input"]["source_packet"]["source_pack"][0]
    assert history["context_only"] and history["report_truth_only"]
    assert history["known_at_utc"] == history["retrieval_time_utc"] == "2026-08-20T01:00:00Z"
    assert history["published_at_utc"] == "2026-08-20T00:00:00Z"
    assert history["canonical_content_sha256"] == sha256(history["canonical_content_text"].encode()).hexdigest()
    assert governed["selected_candidate"]["evolving_story_context"][-1]["relationship"] == "RELATED_DATED_CONTEXT_NOT_EVENT_CORROBORATION"
    walk = json.loads((turn.root / "simple_gemini_evidence_v1.json").read_bytes())
    assert walk["request_count"] == 0 and walk["request_limit"] == 6
    assert selection == (turn.frozen_request("select"), turn._get("select", "response"))
    assert visual == (turn.frozen_request("visual-edit"), turn.visual_response())
    with pytest.raises(DesktopInputRequired) as resumed:
        run_v1_simple_gemini_newsroom(**args)
    assert resumed.value.request == pending.value.request
    history_root = turn.root / "source-recovery-history" / result["request_sha256"]
    original_walk = json.loads((history_root / "simple_gemini_evidence_v1.json").read_bytes())
    assert len(original_walk["selected_source_pack"]) == 1
    assert len(walk["selected_source_pack"]) == 2 and walk["request_count"] == original_walk["request_count"]
    with pytest.raises(ValueError, match="UNWRITTEN"):
        entry().operation(binding, command="recover-sources", response=response)


@pytest.mark.parametrize("clock", ["source_timestamp_utc", "known_at_utc", "revision_at_utc"])
def test_context_rejects_later_information(tmp_path, monkeypatch, clock):
    turn, binding, response, _ = seeded(tmp_path, monkeypatch, lambda r: r.update({clock: "2026-08-27T00:00:00Z"}))
    with pytest.raises(ValueError, match="AFTER_FROZEN_CUTOFF"):
        entry().operation(binding, command="recover-sources", response=response)
    assert turn.source_recovery() is None and turn.frozen_request("write") is None


@pytest.mark.parametrize("change,error", [
    ({"supporting_headline_ids": ["unknown"]}, "NOT_IN_FROZEN"),
    ({"candidate_id": "another-story"}, "QUALIFIED_SELECTED"),
    ({"expected_request_sha256": "changed"}, "UNWRITTEN_SELECTED_VISUAL"),
    ({"match_reason": "same word"}, "MATCH_REASON"),
])
def test_context_rejects_unbound_inputs(tmp_path, monkeypatch, change, error):
    turn, binding, response, _ = seeded(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match=error):
        entry().operation(binding, command="recover-sources", response={**response, **change})
    assert turn.source_recovery() is None


def test_context_cannot_grant_missing_source_permission(tmp_path, monkeypatch):
    turn, binding, response, _ = seeded(tmp_path, monkeypatch,
        lambda r: r["source_permissions"].update(MODEL_INPUT_ALLOWED=False))
    with pytest.raises(ValueError, match="PERMISSION_REQUIRED"):
        entry().operation(binding, command="recover-sources", response=response)
    assert turn.source_recovery() is None


def test_changed_current_event_pack_cannot_reuse_history_attachment(tmp_path, monkeypatch):
    turn, binding, response, args = seeded(tmp_path, monkeypatch)
    entry().operation(binding, command="recover-sources", response=response)
    evidence = _evidence_result(request_count=0)
    evidence["evidence_documents"][0]["canonical_content_text"] += " Changed current event."
    with pytest.raises(SimpleGeminiNewsroomError, match="selected_story_context_source_changed"):
        run_v1_simple_gemini_newsroom(**{**args, "evidence_loader": lambda _: evidence})
    assert turn.frozen_request("write") is None
