import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.dispatch_audit_policy")
    assert module.TASK_LABEL.endswith("DISPATCH_AUDIT_DRY_RUN_CONTRACT_V0")


def test_policy_packet_fixed_values_and_safety():
    from live_contentops import dispatch_audit_policy as p

    packet = p.build_policy_packet()
    fixed = packet["fixed_event_values"]
    assert fixed["request_budget_used"] == 0
    assert fixed["request_budget_allowed"] == 1
    assert fixed["provider_response_class"] == "not_called"
    assert fixed["provider_response_redacted"] == {}
    assert fixed["raw_request_persisted"] is False
    assert fixed["raw_response_persisted"] is False
    assert fixed["token_logged"] is False
    assert fixed["retry_count"] == 0
    assert fixed["final_url_verified"] is None
    assert fixed["redaction_status"] == "pass"
    assert fixed["manual_fallback_required"] is True
    assert fixed["valid_for_live_dispatch"] is False
    assert fixed["can_dispatch"] is False
    assert fixed["platform_dispatch_performed"] is False
    assert fixed["credential_hydration_performed"] is False
    assert fixed["live_ready_state_created"] is False
    for key in ["network_performed", "env_read", "dotenv_read", "credential_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "credential_hydration_performed", "platform_dispatch_performed", "live_ready_state_created", "raw_request_persisted", "raw_response_persisted", "token_logged"]:
        assert packet[key] is False


def test_audit_status_mapping():
    from live_contentops import dispatch_audit_policy as p

    assert p.audit_status_for("local_dry_run_gate_passed_not_live_ready") == "local_audit_dry_run_recorded"
    assert p.audit_status_for("blocked") == "blocked_audit_recorded"
    assert p.audit_status_for("duplicate_suppressed") == "duplicate_suppressed_audit_recorded"
    assert p.audit_status_for("anything_else") == "blocked_audit_recorded"


def test_required_event_fields_include_contract_fields():
    from live_contentops import dispatch_audit_policy as p

    fields = p.required_audit_event_fields()
    for key in ["audit_event_id", "source_gate_matrix_id", "source_outbox_candidate_id", "payload_hash", "provider_response_class", "provider_response_redacted", "raw_request_persisted", "raw_response_persisted", "token_logged", "manual_fallback_required", "audit_hash", "evidence_refs"]:
        assert key in fields


def test_platform_statuses_preserved():
    from live_contentops import dispatch_audit_policy as p

    packet = p.build_policy_packet()
    assert packet["telegram_dispatch_status"] == "proven_frozen_no_send"
    assert packet["x_dispatch_status"] == "dry_run_no_api"
    assert packet["substack_dispatch_status"] == "manual_export_no_api"


def test_forbidden_material_guard():
    from live_contentops import dispatch_audit_policy as p

    with pytest.raises(ValueError, match="forbidden_audit_material"):
        p.validate_no_forbidden_material({"token_logged_value": "raw_token"})


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import dispatch_audit_policy as p

    first = p.write_artifacts(REPO_ROOT)
    second = p.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        p.write_artifacts(REPO_ROOT, tmp_path)
