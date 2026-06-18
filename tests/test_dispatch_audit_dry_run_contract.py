import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.dispatch_audit_dry_run_contract")
    assert module.NEXT_BATCH_PROMPT.endswith("SUPERVISED_DISPATCH_READINESS_SUMMARY_V0")


def _result():
    from live_contentops import dispatch_audit_dry_run_contract as c

    return c.write_artifacts(REPO_ROOT)


def test_gate_passed_local_dry_run_candidate_produces_local_audit_recorded():
    events = _result()["events"]
    active = [e for e in events if e["audit_status"] == "local_audit_dry_run_recorded"]
    assert len(active) == 1
    event = active[0]
    assert event["gate_matrix_status"] == "local_dry_run_gate_passed_not_live_ready"
    assert event["source_outbox_candidate_id"] == "outbox_ledger_resp_001_approve_approval_candidate_candidate"
    assert event["dispatch_mode"] == "audit_dry_run_only"


def test_blocked_matrix_result_produces_blocked_audit_recorded():
    events = _result()["events"]
    blocked = [e for e in events if e["gate_matrix_status"] == "blocked"]
    assert blocked
    assert all(e["audit_status"] == "blocked_audit_recorded" for e in blocked)


def test_duplicate_suppressed_matrix_result_produces_duplicate_audit_recorded():
    events = _result()["events"]
    duplicates = [e for e in events if e["gate_matrix_status"] == "duplicate_suppressed"]
    assert len(duplicates) == 1
    assert duplicates[0]["audit_status"] == "duplicate_suppressed_audit_recorded"


def test_request_budget_provider_raw_token_retry_final_url_redaction_values():
    events = _result()["events"]
    for event in events:
        assert event["request_budget_used"] == 0
        assert event["request_budget_allowed"] == 1
        assert event["provider_response_class"] == "not_called"
        assert event["provider_response_redacted"] == {}
        assert event["raw_request_persisted"] is False
        assert event["raw_response_persisted"] is False
        assert event["token_logged"] is False
        assert event["retry_count"] == 0
        assert event["final_url_verified"] is None
        assert event["redaction_status"] == "pass"
        assert event["manual_fallback_required"] is True


def test_every_event_is_not_live_or_dispatch_capable():
    events = _result()["events"]
    for event in events:
        assert event["valid_for_live_dispatch"] is False
        assert event["can_dispatch"] is False
        assert event["platform_dispatch_performed"] is False
        assert event["credential_hydration_performed"] is False
        assert event["live_post_performed"] is False
        assert event["live_ready_state_created"] is False


def test_every_event_preserves_required_future_gates():
    events = _result()["events"]
    expected = ["kill_switch_activation", "redacted_audit_packet", "manual_fallback_proof", "operator_supervision_window", "live_dispatch_separate_approval"]
    assert all(e["required_future_gates"] == expected for e in events)


def test_every_event_preserves_payload_hash_platform_ids_and_evidence():
    events = _result()["events"]
    active = next(e for e in events if e["audit_status"] == "local_audit_dry_run_recorded")
    assert active["payload_hash"] == "fd47cf9976d21519d74f60ef47884ec7de603810950ab74007575bf70ce2764a"
    assert active["payload_hash_short"] == "fd47cf9976d2"
    assert active["platform"] == "substack"
    assert active["payload_class"] == "substack_newsletter_issue"
    assert active["destination_binding_id"] == "symbolic_fixture_only"
    assert active["credential_handle_id"] == "symbolic_fixture_only"
    assert active["idempotency_key"]
    assert active["evidence_refs"]


def _scalar_strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _scalar_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _scalar_strings(item)
    elif isinstance(value, str):
        yield value.lower()


def test_no_raw_credential_token_chat_id_env_secret_live_url_material():
    events = _result()["events"]
    text = " ".join(_scalar_strings(events))
    forbidden = ["raw_credential", "raw_token", "raw_chat_id", "raw_destination", "env_var", "secret_path", "live_url", "chat_id", "token", "secret"]
    for item in forbidden:
        assert item not in text


def test_no_live_network_env_provider_platform_behavior():
    events = _result()["events"]
    for event in events:
        assert event["network_performed"] is False
        assert event["env_read"] is False
        assert event["dotenv_read"] is False
        assert event["credential_read"] is False
        assert event["telegram_api_called"] is False
        assert event["x_api_called"] is False
        assert event["substack_api_called"] is False
        assert event["platform_api_called"] is False
        assert event["provider_api_called"] is False
        assert event["llm_provider_api_called"] is False
        assert event["credential_hydration_performed"] is False
        assert event["platform_dispatch_performed"] is False
        assert event["live_ready_state_created"] is False


def test_contract_packet_counts_and_proofs():
    packet = _result()["contract_packet"]
    assert packet["audit_event_count"] == 23
    assert packet["local_audit_dry_run_recorded_count"] == 1
    assert packet["blocked_audit_recorded_count"] == 21
    assert packet["duplicate_suppressed_audit_recorded_count"] == 1
    assert packet["provider_response_class_values"] == ["not_called"]
    assert packet["request_budget_used_values"] == [0]
    assert packet["request_budget_allowed_values"] == [1]
    assert packet["all_provider_response_redacted_empty"] is True
    assert packet["all_raw_request_persisted_false"] is True
    assert packet["all_raw_response_persisted_false"] is True
    assert packet["all_token_logged_false"] is True
    assert packet["all_manual_fallback_required_true"] is True
    assert packet["all_valid_for_live_dispatch_false"] is True
    assert packet["all_can_dispatch_false"] is True
    assert packet["all_platform_dispatch_performed_false"] is True
    assert packet["all_credential_hydration_performed_false"] is True
    assert packet["all_live_ready_state_false"] is True


def test_contract_packet_platform_statuses():
    statuses = _result()["contract_packet"]["platform_statuses"]
    assert statuses["telegram"] == "proven_frozen_no_send"
    assert statuses["x"] == "dry_run_no_api"
    assert statuses["substack"] == "manual_export_no_api"


def test_next_supervised_dispatch_readiness_summary_contract():
    next_packet = _result()["next_packet"]
    assert next_packet["next_batch_prompt"].endswith("SUPERVISED_DISPATCH_READINESS_SUMMARY_V0")
    assert next_packet["readiness_summary_must_remain_blocked_for_live_dispatch"] is True
    assert "platform_api_call" in next_packet["forbidden_outputs"]
    assert "raw_request_response_persistence" in next_packet["forbidden_outputs"]
    assert "token_logging" in next_packet["forbidden_outputs"]


def test_audit_hash_changes_if_material_changes():
    from live_contentops import dispatch_audit_dry_run_contract as c

    result = _result()
    event = result["events"][0]
    matrix = result["inputs"]["gate_outputs"][0] if "inputs" in result else None
    if matrix is None:
        matrix = c.load_inputs(REPO_ROOT)["gate_outputs"][0]
    base = event["audit_hash"]
    changed_event = dict(event)
    changed_event["request_budget_used"] = 1
    assert c.compute_audit_hash(matrix, changed_event, result["policy_packet"]) != base


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import dispatch_audit_dry_run_contract as c

    first = c.write_artifacts(REPO_ROOT)
    second = c.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        c.write_artifacts(REPO_ROOT, tmp_path)
