import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.dispatch_gate_matrix_contract")
    assert module.NEXT_BATCH_PROMPT.endswith("DISPATCH_AUDIT_DRY_RUN_CONTRACT_V0")


def _result():
    from live_contentops import dispatch_gate_matrix_contract as c

    return c.write_artifacts(REPO_ROOT)


def test_active_outbox_candidate_produces_local_dry_run_gate_passed_not_live_ready():
    matrices = _result()["matrices"]
    active = [m for m in matrices if m["overall_gate_status"] == "local_dry_run_gate_passed_not_live_ready"]
    assert len(active) == 1
    item = active[0]
    assert item["source_outbox_candidate_id"] == "outbox_ledger_resp_001_approve_approval_candidate_candidate"
    assert item["eligible_for_dispatch_audit_dry_run"] is True
    assert item["valid_for_live_dispatch"] is False
    assert item["can_dispatch"] is False
    assert item["live_ready_state_created"] is False


def test_blocked_candidates_remain_blocked():
    matrices = _result()["matrices"]
    blocked = [m for m in matrices if m["source_outbox_candidate_id"].endswith("_blocked")]
    assert blocked
    assert all(m["overall_gate_status"] == "blocked" for m in blocked)
    assert all(m["eligible_for_dispatch_audit_dry_run"] is False for m in blocked)


def test_duplicate_suppressed_candidate_remains_duplicate_suppressed():
    matrices = _result()["matrices"]
    duplicates = [m for m in matrices if m["overall_gate_status"] == "duplicate_suppressed"]
    assert len(duplicates) == 1
    assert duplicates[0]["gate_results"]["idempotency_gate"]["status"] == "duplicate_suppressed"
    assert duplicates[0]["eligible_for_dispatch_audit_dry_run"] is False


def test_missing_payload_hash_fails_payload_hash_gate():
    matrices = _result()["matrices"]
    item = next(m for m in matrices if "missing_payload_hash" in m["source_outbox_candidate_id"])
    assert item["gate_results"]["payload_hash_gate"]["status"] == "fail"
    assert "payload_hash_gate_failed" in item["blocked_reasons"]


def test_wrong_request_budget_fails_request_budget_gate():
    matrices = _result()["matrices"]
    item = next(m for m in matrices if m["source_outbox_candidate_id"].endswith("wrong_request_budget"))
    assert item["gate_results"]["request_budget_gate"]["status"] == "fail"
    assert item["overall_gate_status"] == "blocked"


def test_auto_retry_allowed_true_fails_no_auto_retry_gate():
    matrices = _result()["matrices"]
    item = next(m for m in matrices if m["source_outbox_candidate_id"].endswith("auto_retry_true"))
    assert item["gate_results"]["no_auto_retry_gate"]["status"] == "fail"
    assert item["overall_gate_status"] == "blocked"


def test_wrong_destination_and_credential_handle_fail_symbolic_gates():
    matrices = _result()["matrices"]
    wrong_dest = next(m for m in matrices if m["source_outbox_candidate_id"].endswith("wrong_destination"))
    wrong_cred = next(m for m in matrices if m["source_outbox_candidate_id"].endswith("wrong_credential"))
    assert wrong_dest["gate_results"]["destination_binding_gate"]["status"] == "fail"
    assert wrong_cred["gate_results"]["credential_handle_gate"]["status"] == "fail"


def test_platform_capability_gate_statuses():
    matrices = _result()["matrices"]
    statuses = {m["platform"]: m["gate_results"]["platform_capability_gate"]["status"] for m in matrices if m["platform"] in ["telegram", "x", "substack"]}
    assert statuses["telegram"] == "proven_frozen_no_send"
    assert statuses["x"] == "dry_run_no_api"
    assert statuses["substack"] == "manual_export_no_api"
    assert _result()["contract_packet"]["platform_capability_gate_statuses"] == statuses


def test_every_matrix_non_dispatching_and_no_live_ready():
    matrices = _result()["matrices"]
    for matrix in matrices:
        assert matrix["valid_for_live_dispatch"] is False
        assert matrix["can_dispatch"] is False
        assert matrix["live_ready_state_created"] is False
        assert matrix["network_performed"] is False
        assert matrix["telegram_api_called"] is False
        assert matrix["x_api_called"] is False
        assert matrix["substack_api_called"] is False
        assert matrix["platform_api_called"] is False
        assert matrix["provider_api_called"] is False
        assert matrix["llm_provider_api_called"] is False
        assert matrix["credential_hydration_performed"] is False
        assert matrix["platform_dispatch_performed"] is False
        assert matrix["live_post_performed"] is False


def test_every_matrix_has_required_future_gates_for_real_dispatch():
    matrices = _result()["matrices"]
    expected = ["kill_switch_activation", "redacted_audit_packet", "manual_fallback_proof", "operator_supervision_window", "live_dispatch_separate_approval"]
    assert all(m["required_future_gates"] == expected for m in matrices)


def test_no_raw_credential_token_chat_id_env_secret_live_url_material():
    result = _result()
    text = str(result).lower()
    forbidden = ["raw_credential", "raw_token", "raw_chat_id", "raw_destination", "env_var", "secret_path", "live_url", "chat_id", "token", "secret"]
    for item in forbidden:
        assert item not in text


def test_contract_packet_counts_checksums_and_safety():
    packet = _result()["contract_packet"]
    assert packet["matrix_result_count"] == 23
    assert packet["local_dry_run_gate_passed_count"] == 1
    assert packet["blocked_count"] == 21
    assert packet["duplicate_suppressed_count"] == 1
    assert packet["all_valid_for_live_dispatch_false"] is True
    assert packet["all_can_dispatch_false"] is True
    assert packet["all_live_ready_state_false"] is True
    for key in ["network_performed", "env_read", "dotenv_read", "credential_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "credential_hydration_performed", "platform_dispatch_performed", "live_ready_state_created"]:
        assert packet[key] is False


def test_next_dispatch_audit_dry_run_contract():
    next_packet = _result()["next_packet"]
    assert next_packet["next_batch_prompt"].endswith("DISPATCH_AUDIT_DRY_RUN_CONTRACT_V0")
    assert "credential_hydration" in next_packet["forbidden_outputs"]
    assert "platform_api_call" in next_packet["forbidden_outputs"]
    assert "live_ready_state" in next_packet["forbidden_outputs"]
    assert next_packet["platform_dispatch_performed"] is False


def test_audit_hash_changes_if_gate_material_changes():
    from live_contentops import dispatch_gate_matrix_contract as c
    from live_contentops import dispatch_gate_policy as p

    result = _result()
    matrix = next(m for m in result["matrices"] if m["overall_gate_status"] == "local_dry_run_gate_passed_not_live_ready")
    candidate = {
        "outbox_candidate_id": matrix["source_outbox_candidate_id"],
        "source_approval_ledger_entry_id": matrix["source_approval_ledger_entry_id"],
        "platform": matrix["platform"],
        "payload_hash": matrix["payload_hash"],
        "idempotency_key": matrix["idempotency_key"],
    }
    base = c.compute_audit_hash(candidate, matrix["gate_results"], matrix["overall_gate_status"], p.build_policy_packet())
    changed = dict(candidate)
    changed["payload_hash"] = "changed"
    assert c.compute_audit_hash(changed, matrix["gate_results"], matrix["overall_gate_status"], p.build_policy_packet()) != base


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import dispatch_gate_matrix_contract as c

    first = c.write_artifacts(REPO_ROOT)
    second = c.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        c.write_artifacts(REPO_ROOT, tmp_path)
