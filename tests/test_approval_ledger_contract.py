import copy
import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.approval_ledger_contract")
    assert module.NEXT_BATCH_PROMPT.endswith("DISPATCH_OUTBOX_CANDIDATE_CONTRACT_V0")


def _result():
    from live_contentops import approval_ledger_contract as c

    return c.write_artifacts(REPO_ROOT)


def _by_class(events, event_class):
    return [e for e in events if e["ledger_event_class"] == event_class]


def test_explicit_approve_exact_hash_creates_approval_ledger_candidate_entry():
    events = _result()["events"]
    approved = _by_class(events, "approval_candidate")
    assert len(approved) == 1
    item = approved[0]
    assert item["eligible_for_outbox_candidate"] is True
    assert item["valid_for_dispatch"] is False
    assert item["can_dispatch"] is False
    assert item["can_create_outbox"] is False
    assert item["payload_hash_short"] == item["response_payload_hash_short"]
    assert item["approved_at_order"] == 1


def test_reject_edit_hold_create_non_approval_events():
    events = _result()["events"]
    rejected = _by_class(events, "rejected_event")[0]
    edit = _by_class(events, "edit_request_event")[0]
    hold = _by_class(events, "hold_event")[0]
    assert rejected["eligible_for_outbox_candidate"] is False
    assert "operator_rejected" in rejected["blocked_reasons"]
    assert edit["eligible_for_outbox_candidate"] is False
    assert "operator_requested_revision" in edit["blocked_reasons"]
    assert hold["eligible_for_outbox_candidate"] is False
    assert "operator_hold" in hold["blocked_reasons"]


def test_ambiguous_mismatch_unknown_and_replay_are_blocked():
    events = _result()["events"]
    reasons = [reason for e in _by_class(events, "blocked_event") for reason in e["blocked_reasons"]]
    assert "ambiguous_response_requires_clarification" in reasons
    assert "payload_hash_short_mismatch" in reasons
    assert "unknown_challenge_candidate" in reasons
    assert "replayed_response" in reasons


def test_blocked_proof_sources_cannot_create_approval():
    result = _result()
    events = result["events"]
    blocked_ids = set(result["contract_packet"]["blocked_source_brief_proof"])
    blocked_events = [e for e in events if e["source_brief_id"] in blocked_ids]
    assert blocked_ids == {"brief_intent_msg_003", "brief_intent_msg_011", "brief_intent_msg_012", "brief_intent_future_artifact_demo"}
    assert blocked_events
    for event in blocked_events:
        assert event["ledger_event_class"] == "blocked_event"
        assert event["eligible_for_outbox_candidate"] is False
        assert "blocked_source_brief_proof" in event["blocked_reasons"]


def test_every_entry_has_no_dispatch_no_outbox_no_public_postable():
    events = _result()["events"]
    assert events
    for event in events:
        assert event["can_dispatch"] is False
        assert event["can_create_outbox"] is False
        assert event["valid_for_dispatch"] is False
        assert event["public_postable"] is False
        assert event["platform_api_called"] is False
        assert event["dispatch_outbox_mutated"] is False
        assert event["platform_dispatch_performed"] is False


def test_payload_hash_and_hash_short_preserved_from_candidate_for_known_events():
    from live_contentops import approval_ledger_contract as c

    inputs = c.load_inputs(REPO_ROOT)
    candidates = {item["challenge_candidate_id"]: item for item in inputs["candidates"]}
    events = _result()["events"]
    for event in events:
        candidate = candidates.get(event["source_challenge_candidate_id"])
        if not candidate:
            continue
        assert event["payload_hash"] == candidate["payload_hash"]
        assert event["payload_hash_short"] == candidate["payload_hash_short"]
        assert event["platform"] == candidate["platform"]
        assert event["payload_class"] == candidate["payload_class"]


def test_audit_hash_changes_if_response_text_payload_platform_or_destination_changes():
    from live_contentops import approval_ledger_contract as c
    from live_contentops import approval_ledger_policy as p

    inputs = c.load_inputs(REPO_ROOT)
    candidate = inputs["candidates"][0]
    response = c.build_response_fixtures(inputs["candidates"])[0]
    policy_packet = p.build_policy_packet()
    base = c.compute_audit_hash(response, candidate, "approval_candidate", [], policy_packet)
    changed_response = copy.deepcopy(response)
    changed_response["response_text_redacted"] = "changed approval text"
    assert c.compute_audit_hash(changed_response, candidate, "approval_candidate", [], policy_packet) != base
    changed_candidate = copy.deepcopy(candidate)
    changed_candidate["payload_hash"] = "changed_payload_hash"
    assert c.compute_audit_hash(response, changed_candidate, "approval_candidate", [], policy_packet) != base
    changed_candidate = copy.deepcopy(candidate)
    changed_candidate["platform"] = "changed_platform"
    assert c.compute_audit_hash(response, changed_candidate, "approval_candidate", [], policy_packet) != base
    changed_candidate = copy.deepcopy(candidate)
    changed_candidate["destination_binding_id"] = "changed_symbolic_binding"
    assert c.compute_audit_hash(response, changed_candidate, "approval_candidate", [], policy_packet) != base


def test_no_raw_credential_token_chat_id_env_secret_live_url_material():
    result = _result()
    text = str(result).lower()
    forbidden = ["raw_credential", "raw_token", "raw_chat_id", "raw_destination", "env_var", "secret_path", "live_url", "chat_id", "token", "secret"]
    for item in forbidden:
        assert item not in text


def test_contract_packet_counts_checksums_and_safety():
    result = _result()
    packet = result["contract_packet"]
    assert packet["approved_entry_count"] == 1
    assert packet["rejected_event_count"] == 1
    assert packet["edit_event_count"] == 1
    assert packet["hold_event_count"] == 1
    assert packet["blocked_event_count"] >= 8
    assert packet["hash_mismatch_blocked_proof"] is True
    assert packet["unknown_challenge_blocked_proof"] is True
    assert packet["replay_blocked_proof"] is True
    assert packet["all_can_dispatch_false"] is True
    assert packet["all_can_create_outbox_false"] is True
    assert packet["all_valid_for_dispatch_false"] is True
    assert packet["approval_eligible_entries_bind_exact_hash"] is True
    for key in ["network_performed", "env_read", "dotenv_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "live_post_performed", "dispatch_outbox_mutated", "platform_dispatch_performed"]:
        assert packet[key] is False


def test_next_dispatch_outbox_candidate_contract():
    next_packet = _result()["next_packet"]
    assert next_packet["next_batch_prompt"].endswith("DISPATCH_OUTBOX_CANDIDATE_CONTRACT_V0")
    assert "live_dispatch" in next_packet["forbidden_outputs"]
    assert "platform_api_call" in next_packet["forbidden_outputs"]
    assert next_packet["dispatch_outbox_mutated"] is False
    assert next_packet["platform_dispatch_performed"] is False


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import approval_ledger_contract as c

    first = c.write_artifacts(REPO_ROOT)
    second = c.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        c.write_artifacts(REPO_ROOT, tmp_path)
