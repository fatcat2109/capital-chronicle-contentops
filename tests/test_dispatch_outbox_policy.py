import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.dispatch_outbox_policy")
    assert module.TASK_LABEL.endswith("DISPATCH_OUTBOX_CANDIDATE_CONTRACT_V0")


def _entry(**overrides):
    entry = {
        "ledger_entry_id": "ledger_ok",
        "eligible_for_outbox_candidate": True,
        "platform": "substack",
        "payload_hash": "a" * 64,
        "destination_binding_id": "symbolic_fixture_only",
        "credential_handle_id": "symbolic_fixture_only",
    }
    entry.update(overrides)
    return entry


def test_policy_packet_safety_and_platform_rules():
    from live_contentops import dispatch_outbox_policy as p

    packet = p.build_policy_packet()
    assert packet["supported_dispatch_prep_platforms"] == ["substack", "telegram", "x"]
    assert packet["request_budget_required"] == 1
    assert packet["auto_retry_allowed"] is False
    assert packet["credential_hydration_allowed"] is False
    assert packet["platform_api_call_allowed"] is False
    assert packet["live_dispatch_allowed"] is False
    assert packet["valid_for_dispatch_always_false"] is True
    assert packet["can_dispatch_always_false"] is True
    assert packet["telegram_dispatch_status"] == "proven_frozen_no_send"
    for key in ["network_performed", "env_read", "dotenv_read", "credential_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "credential_hydration_performed", "live_ready_state_created"]:
        assert packet[key] is False


def test_candidate_classification_allows_only_eligible_valid_supported_entry():
    from live_contentops import dispatch_outbox_policy as p

    status, reasons, duplicate = p.classify_entry(_entry(), set())
    assert status == "candidate"
    assert reasons == []
    assert duplicate == "unique"


def test_rejected_edit_hold_blocked_entries_are_blocked():
    from live_contentops import dispatch_outbox_policy as p

    for event_class in ["rejected_event", "edit_request_event", "hold_event", "blocked_event"]:
        status, reasons, _ = p.classify_entry(_entry(eligible_for_outbox_candidate=False, ledger_event_class=event_class), set())
        assert status == "blocked"
        assert "ledger_entry_not_eligible_for_outbox_candidate" in reasons


def test_missing_payload_destination_credential_and_unsupported_platform_block():
    from live_contentops import dispatch_outbox_policy as p

    assert "missing_payload_hash" in p.classify_entry(_entry(payload_hash=None), set())[1]
    assert "destination_binding_not_symbolic_fixture_only" in p.classify_entry(_entry(destination_binding_id=None), set())[1]
    assert "destination_binding_not_symbolic_fixture_only" in p.classify_entry(_entry(destination_binding_id="wrong"), set())[1]
    assert "credential_handle_not_symbolic_fixture_only" in p.classify_entry(_entry(credential_handle_id=None), set())[1]
    assert "credential_handle_not_symbolic_fixture_only" in p.classify_entry(_entry(credential_handle_id="wrong"), set())[1]
    assert "unsupported_dispatch_prep_platform" in p.classify_entry(_entry(platform="linkedin"), set())[1]


def test_duplicate_idempotency_key_is_duplicate_suppressed():
    from live_contentops import dispatch_outbox_policy as p

    entry = _entry()
    seen = {p.compute_idempotency_key(entry)}
    status, reasons, duplicate = p.classify_entry(entry, seen)
    assert status == "duplicate_suppressed"
    assert "duplicate_idempotency_key" in reasons
    assert duplicate == "duplicate_suppressed"


def test_idempotency_key_changes_when_bound_fields_change():
    from live_contentops import dispatch_outbox_policy as p

    entry = _entry()
    proof = p.idempotency_determinism_proof(entry)
    assert proof["same_input_same_key"] is True
    assert proof["platform_change_changes_key"] is True
    assert proof["payload_hash_change_changes_key"] is True
    assert proof["destination_binding_id_change_changes_key"] is True
    assert proof["credential_handle_id_change_changes_key"] is True
    assert proof["ledger_entry_id_change_changes_key"] is True


def test_forbidden_material_guard():
    from live_contentops import dispatch_outbox_policy as p

    with pytest.raises(ValueError, match="forbidden_outbox_material"):
        p.validate_no_forbidden_material({"credential_handle_id": "raw_token"})


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import dispatch_outbox_policy as p

    first = p.write_artifacts(REPO_ROOT)
    second = p.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        p.write_artifacts(REPO_ROOT, tmp_path)
