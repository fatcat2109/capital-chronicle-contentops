import json

import pytest

from live_contentops.native_editorial_continuation_v1 import consume_advance_result, next_editorial_action


def pending():
    return {"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "filter_progress": {"remaining_unprocessed": 131},
            "next_native_calls": [{"tool": "collaboration.spawn_agent", "arguments": {"task_name": "filter-a"}}]}


def test_initial_empty_exec_is_collected_by_its_actual_handle_not_reissued():
    result = consume_advance_result({"session_id": 125, "output": ""})
    assert result == {"action": "COLLECT_EXACT_COMMAND_HANDLE", "session_id": 125, "repeat_advance": False, "terminal": False}
    completed = consume_advance_result({"exit_code": 0, "output": json.dumps(pending())})
    assert completed["action"] == "EXECUTE_AND_COLLECT_NATIVE_ROLES" and not completed["terminal"]


def test_completed_handle_json_is_consumed_even_when_initial_stdout_was_empty():
    result = consume_advance_result({"exit_code": 0, "output": json.dumps({"classification": "PASS_NATIVE_DESKTOP_ZERO_WRITE_ARTICLE", "qualified_article_count": 1, "article_path": "local.md"})})
    assert result["action"] == "REVIEW_EXACT_ARTICLE_AND_RENDERS" and not result["terminal"]


def test_pending_role_without_actual_call_is_a_process_defect():
    result = pending(); result.pop("next_native_calls")
    with pytest.raises(ValueError, match="NO_DISPATCH"):
        next_editorial_action(result)


def test_media_preparation_is_a_local_command_before_a_native_request_exists():
    from scripts.replay_cc041_native_window import pending_result
    result = pending_result([{"stage": "media-plan"}], {"output_dir": "isolated", "run_id": "same"})
    assert result["coordinator_action"]["action"] == "EXECUTE_EDITORIAL_COMMAND"
    assert result["next_command"]["command"] == "media-plan"
    assert "next_native_calls" not in result
    assert not result["coordinator_action"]["terminal"]


def test_fresh_role_dispatch_has_no_retired_callback_authority(tmp_path):
    from live_contentops.codex_desktop_newsroom_operator_v1 import native_role_call
    request = {"stage": "select", "run_id": "run", "requested_model": "gpt-6.1-sol",
        "requested_reasoning_effort": "low", "request_sha256": "a" * 64, "request_path": "frozen.json"}
    call = native_role_call(request, {"run_id": "run", "output_dir": str(tmp_path)}, binding_path="binding.json")
    message = call["arguments"]["message"]
    assert "EXACT NATIVE ASSIGNMENT:" in message
    assert "Do not read or message archived chats" in message
    assert "Only after genuinely completing the WHOLE goal" not in message


def test_replay_missing_source_cannot_fall_through_to_network():
    from types import SimpleNamespace
    from scripts.replay_cc041_native_window import FrozenReplayResearch
    retained = SimpleNamespace(revision="frozen", records={}, evidence=lambda *a, **kw: None)
    result = FrozenReplayResearch(retained).evidence({"headline_ids": ["uncached"]}, cutoff_utc="frozen")
    assert result["status"] == "BLOCKED"
    assert result["provenance"] == {"request_count_for_call": 0, "network_acquisition_on_replay": False}


def test_replay_exact_frozen_relay_reuses_governed_admission_with_zero_gets(monkeypatch):
    from types import SimpleNamespace
    from scripts.replay_cc041_native_window import FrozenReplayResearch
    from live_contentops import v1_simple_evidence_resolver_v1 as resolver
    from live_contentops import v1_simple_epistemic_state_v1 as epistemic
    retained = SimpleNamespace(revision="frozen", records={}, evidence=lambda *a, **kw: None)
    monkeypatch.setattr(epistemic, "canonical_x_report_document", lambda request: ({"document_id": "controlled"}, []))
    monkeypatch.setattr(resolver.SimpleFirstPartyAwareEvidenceResolver, "_accepted_epistemic_route",
        lambda self, request, value, route: (value["evidence_documents"], {"report_truth_supported": True}, []))
    # The adapter invokes only existing deterministic admission helpers, never
    # the resolver __call__ that could initiate a source walk.
    monkeypatch.setattr(resolver.SimpleFirstPartyAwareEvidenceResolver, "__call__",
        lambda *a, **kw: pytest.fail("network-capable resolver entry was invoked"))
    result = FrozenReplayResearch(retained).evidence({"story_context": {"report_provenance": {
        "explicit_reputable_attribution": True}}}, cutoff_utc="2026-10-29T17:58:43Z")
    assert result["status"] == "PASS" and result["provenance"]["request_count_for_call"] == 0


def test_replay_resumes_canonical_final_and_exposes_its_actual_render_targets(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from scripts.replay_cc041_native_window import resume_frozen_window, editorial_command
    from test_native_desktop_publication_v1 import seeded
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    fixture, binding, _, expected, _ = seeded(tmp_path, monkeypatch, manual=True, final_visual=False)
    # The transport fixture intentionally uses target_surface=TEST; mirror an
    # editorial work item in a separate disposable store for this integration.
    store = ContentOpsDurableStore(tmp_path / "canonical-fixture.sqlite3")
    binding = {**binding, "store_path": str(store.db_path)}
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled editorial replay",
        target_surface="CONTENTOPS_EDITORIAL_ONLY")
    row = fixture.get_outbox_message("cc-editorial-final-" + sha256_of(binding["run_id"]))
    store.register_outbox_message(message_id=row["message_id"], work_item_id=work,
        destination=row["destination"], payload=row["payload"], status=row["status"])
    research = SimpleNamespace(revision=None, records={})
    result = resume_frozen_window(store, binding, {}, [], research)
    assert result["article_identity"] == expected["article_identity"]
    assert result["qualified_article_count"] == 1
    targets = editorial_command(store, binding, "final-visual-review")
    assert targets["classification"] == "FINAL_VISUAL_RENDER_TARGETS"
    assert targets["article_identity"] == result["article_identity"]
    assert store.list_platform_dispatches() == []


def test_unassigned_population_never_passes_as_a_complete_window():
    with pytest.raises(ValueError, match="UNASSIGNED_FILTER"):
        next_editorial_action({"classification": "NO_PUBLICATION", "filter_progress": {"remaining_unprocessed": 25}})


def test_typed_hold_is_not_reviewed_article_acceptance():
    result = next_editorial_action({"classification": "NATIVE_PRE_WRITER_EDITION_COMPLETE"})
    assert result["terminal"] and not result["reviewed_article_acceptance"]


def test_native_role_is_collected_in_same_operation_not_ancestor_chat():
    result = next_editorial_action(pending())
    assert result["after_returns"] == "SUBMIT_EACH_THEN_ADVANCE_SAME_BINDING"
    assert result["remaining_unprocessed"] == 131


def test_command_error_preserves_failure_instead_of_editorial_hold():
    assert consume_advance_result({"exit_code": 1, "output": "exception"})["action"] == "REPAIR_COMMAND_ERROR"
    with pytest.raises(ValueError, match="WITHOUT_JSON"):
        consume_advance_result({"exit_code": 0, "output": ""})
