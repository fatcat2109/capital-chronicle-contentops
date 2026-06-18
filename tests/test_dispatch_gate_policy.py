import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.dispatch_gate_policy")
    assert module.TASK_LABEL.endswith("DISPATCH_GATE_MATRIX_CONTRACT_V0")


def _candidate(**overrides):
    candidate = {
        "outbox_candidate_id": "outbox_ok",
        "source_approval_ledger_entry_id": "ledger_ok",
        "status": "candidate",
        "eligible_for_gate_matrix": True,
        "platform": "substack",
        "payload_hash": "abcdef" + "0" * 58,
        "payload_hash_short": "abcdef000000",
        "destination_binding_id": "symbolic_fixture_only",
        "credential_handle_id": "symbolic_fixture_only",
        "idempotency_key": "1" * 64,
        "request_budget": 1,
        "auto_retry_allowed": False,
        "duplicate_suppression_status": "unique",
        "blocked_reasons": [],
    }
    candidate.update(overrides)
    return candidate


def test_policy_packet_safety_and_required_future_gates():
    from live_contentops import dispatch_gate_policy as p

    packet = p.build_policy_packet()
    assert packet["valid_for_live_dispatch_always_false"] is True
    assert packet["can_dispatch_always_false"] is True
    assert packet["live_ready_state_created_always_false"] is True
    assert packet["required_future_gates"] == ["kill_switch_activation", "redacted_audit_packet", "manual_fallback_proof", "operator_supervision_window", "live_dispatch_separate_approval"]
    for key in ["network_performed", "env_read", "dotenv_read", "credential_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "credential_hydration_performed", "platform_dispatch_performed", "live_ready_state_created"]:
        assert packet[key] is False


def test_active_candidate_passes_local_dry_run_not_live_ready():
    from live_contentops import dispatch_gate_policy as p

    candidate = _candidate()
    gates = p.evaluate_gates(candidate)
    assert p.overall_status(candidate, gates) == "local_dry_run_gate_passed_not_live_ready"
    assert gates["payload_hash_gate"]["status"] == "pass"
    assert gates["no_live_ready_gate"]["status"] == "pass"


def test_blocked_and_duplicate_statuses_preserved():
    from live_contentops import dispatch_gate_policy as p

    blocked = _candidate(status="blocked", eligible_for_gate_matrix=False)
    gates = p.evaluate_gates(blocked)
    assert p.overall_status(blocked, gates) == "blocked"
    duplicate = _candidate(status="duplicate_suppressed", eligible_for_gate_matrix=False, duplicate_suppression_status="duplicate_suppressed")
    gates = p.evaluate_gates(duplicate)
    assert gates["idempotency_gate"]["status"] == "duplicate_suppressed"
    assert p.overall_status(duplicate, gates) == "duplicate_suppressed"


def test_payload_hash_gate_fails_missing_or_mismatch():
    from live_contentops import dispatch_gate_policy as p

    assert p.evaluate_gates(_candidate(payload_hash=None))["payload_hash_gate"]["status"] == "fail"
    assert p.evaluate_gates(_candidate(payload_hash_short="wrong"))["payload_hash_gate"]["status"] == "fail"


def test_request_budget_and_auto_retry_gates_fail_closed():
    from live_contentops import dispatch_gate_policy as p

    assert p.evaluate_gates(_candidate(request_budget=2))["request_budget_gate"]["status"] == "fail"
    assert p.evaluate_gates(_candidate(auto_retry_allowed=True))["no_auto_retry_gate"]["status"] == "fail"


def test_destination_and_credential_symbolic_gates_fail_closed():
    from live_contentops import dispatch_gate_policy as p

    assert p.evaluate_gates(_candidate(destination_binding_id="wrong"))["destination_binding_gate"]["status"] == "fail"
    assert p.evaluate_gates(_candidate(credential_handle_id="wrong"))["credential_handle_gate"]["status"] == "fail"


def test_platform_capability_statuses():
    from live_contentops import dispatch_gate_policy as p

    assert p.platform_capability_status("telegram") == "proven_frozen_no_send"
    assert p.platform_capability_status("x") == "dry_run_no_api"
    assert p.platform_capability_status("substack") == "manual_export_no_api"
    assert p.platform_capability_status("linkedin") == "unsupported_platform"


def test_future_gates_are_future_required_not_active():
    from live_contentops import dispatch_gate_policy as p

    gates = p.evaluate_gates(_candidate())
    assert gates["kill_switch_gate"]["status"] == "future_required_not_active"
    assert gates["redacted_audit_gate_future"]["status"] == "future_required_not_active"
    assert gates["manual_fallback_gate_future"]["status"] == "future_required_not_active"


def test_forbidden_material_guard():
    from live_contentops import dispatch_gate_policy as p

    with pytest.raises(ValueError, match="forbidden_gate_material"):
        p.validate_no_forbidden_material({"credential_handle_id": "raw_token"})


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import dispatch_gate_policy as p

    first = p.write_artifacts(REPO_ROOT)
    second = p.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        p.write_artifacts(REPO_ROOT, tmp_path)
