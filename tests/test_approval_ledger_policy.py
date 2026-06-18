import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.approval_ledger_policy")
    assert module.TASK_LABEL.endswith("APPROVAL_LEDGER_CONTRACT_V0")


def _candidate(**overrides):
    candidate = {
        "challenge_candidate_id": "challenge_ok",
        "source_brief_id": "brief_ok",
        "payload_hash_short": "abcdef123456",
        "expires_policy": "future_required_not_active",
    }
    candidate.update(overrides)
    return candidate


def _response(**overrides):
    response = {
        "response_class": "explicit_approve",
        "response_payload_hash_short": "abcdef123456",
        "replay_status": "not_replay",
    }
    response.update(overrides)
    return response


def test_policy_packet_safety_and_rules():
    from live_contentops import approval_ledger_policy as p

    packet = p.build_policy_packet()
    assert packet["only_explicit_approve_exact_hash_can_create_approval"] is True
    assert packet["valid_for_dispatch_always_false"] is True
    assert packet["can_dispatch_always_false"] is True
    assert packet["can_create_outbox_always_false"] is True
    assert packet["public_postable_always_false"] is True
    assert packet["append_only_fixture_output_only"] is True
    for key in ["network_performed", "env_read", "dotenv_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "dispatch_outbox_mutated", "platform_dispatch_performed"]:
        assert packet[key] is False


def test_explicit_approve_exact_hash_can_create_approval_candidate():
    from live_contentops import approval_ledger_policy as p

    event_class, blocked = p.classify_response(_response(), _candidate(), {"blocked_direct_dispatch_proof": [], "blocked_approval_candidate_proof": [], "blocked_signal_advice_proof": [], "blocked_future_artifact_proof": []})
    assert event_class == "approval_candidate"
    assert blocked == []
    assert p.eligible_for_outbox_candidate(event_class, blocked) is True


def test_reject_edit_hold_and_ambiguous_classification():
    from live_contentops import approval_ledger_policy as p

    packet = {"blocked_direct_dispatch_proof": [], "blocked_approval_candidate_proof": [], "blocked_signal_advice_proof": [], "blocked_future_artifact_proof": []}
    assert p.classify_response(_response(response_class="explicit_reject"), _candidate(), packet)[0] == "rejected_event"
    assert p.classify_response(_response(response_class="explicit_edit_request"), _candidate(), packet)[0] == "edit_request_event"
    assert p.classify_response(_response(response_class="explicit_hold"), _candidate(), packet)[0] == "hold_event"
    event_class, reasons = p.classify_response(_response(response_class="ambiguous"), _candidate(), packet)
    assert event_class == "blocked_event"
    assert "ambiguous_response_requires_clarification" in reasons


def test_fail_closed_unknown_mismatch_replay_expired_and_blocked_source():
    from live_contentops import approval_ledger_policy as p

    packet = {"blocked_direct_dispatch_proof": ["brief_blocked"], "blocked_approval_candidate_proof": [], "blocked_signal_advice_proof": [], "blocked_future_artifact_proof": []}
    assert "unknown_challenge_candidate" in p.classify_response(_response(), None, packet)[1]
    assert "payload_hash_short_mismatch" in p.classify_response(_response(response_payload_hash_short="badbadbadbad"), _candidate(), packet)[1]
    assert "replayed_response" in p.classify_response(_response(replay_status="replay"), _candidate(), packet)[1]
    assert "expired_challenge_candidate" in p.classify_response(_response(), _candidate(expires_policy="active_expired"), packet)[1]
    assert "blocked_source_brief_proof" in p.classify_response(_response(), _candidate(source_brief_id="brief_blocked"), packet)[1]


def test_forbidden_material_guard():
    from live_contentops import approval_ledger_policy as p

    with pytest.raises(ValueError, match="forbidden_ledger_material"):
        p.validate_no_forbidden_material({"credential_handle_id": "raw_token"})


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import approval_ledger_policy as p

    first = p.write_artifacts(REPO_ROOT)
    second = p.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        p.write_artifacts(REPO_ROOT, tmp_path)
