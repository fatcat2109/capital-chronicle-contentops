import copy
import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.dispatch_outbox_candidate_contract")
    assert module.NEXT_BATCH_PROMPT.endswith("DISPATCH_GATE_MATRIX_CONTRACT_V0")


def _result():
    from live_contentops import dispatch_outbox_candidate_contract as c

    return c.write_artifacts(REPO_ROOT)


def test_eligible_approved_ledger_entry_creates_one_dry_run_outbox_candidate():
    records = _result()["records"]
    active = [r for r in records if r["status"] == "candidate"]
    assert len(active) == 1
    item = active[0]
    assert item["source_approval_ledger_entry_id"] == "ledger_resp_001_approve_approval_candidate"
    assert item["platform"] == "substack"
    assert item["eligible_for_gate_matrix"] is True
    assert item["dispatch_mode"] == "dry_run_candidate_only"
    assert item["request_budget"] == 1


def test_rejected_edit_hold_and_blocked_events_create_no_active_candidate():
    records = _result()["records"]
    blocked = [r for r in records if r["status"] == "blocked"]
    reasons = [reason for record in blocked for reason in record["blocked_reasons"]]
    assert "ledger_entry_not_eligible_for_outbox_candidate" in reasons
    for record in records:
        if record["source_approval_ledger_entry_id"] and any(tag in record["source_approval_ledger_entry_id"] for tag in ["reject", "edit", "hold", "blocked", "ambiguous", "mismatch", "unknown", "replay"]):
            assert record["status"] != "candidate"
            assert record["eligible_for_gate_matrix"] is False


def test_missing_payload_hash_destination_credential_and_unsupported_platform_are_blocked():
    records = _result()["records"]
    reasons = {r["source_approval_ledger_entry_id"]: r["blocked_reasons"] for r in records}
    assert "missing_payload_hash" in reasons["ledger_resp_001_approve_approval_candidate_missing_payload_hash"]
    assert "destination_binding_not_symbolic_fixture_only" in reasons["ledger_resp_001_approve_approval_candidate_missing_destination"]
    assert "destination_binding_not_symbolic_fixture_only" in reasons["ledger_resp_001_approve_approval_candidate_wrong_destination"]
    assert "credential_handle_not_symbolic_fixture_only" in reasons["ledger_resp_001_approve_approval_candidate_missing_credential"]
    assert "credential_handle_not_symbolic_fixture_only" in reasons["ledger_resp_001_approve_approval_candidate_wrong_credential"]
    assert "unsupported_dispatch_prep_platform" in reasons["ledger_resp_001_approve_approval_candidate_unsupported_platform"]


def test_duplicate_idempotency_key_is_duplicate_suppressed():
    records = _result()["records"]
    duplicates = [r for r in records if r["status"] == "duplicate_suppressed"]
    assert len(duplicates) == 1
    assert duplicates[0]["duplicate_suppression_status"] == "duplicate_suppressed"
    assert "duplicate_idempotency_key" in duplicates[0]["blocked_reasons"]
    assert duplicates[0]["eligible_for_gate_matrix"] is False


def test_idempotency_key_changes_when_bound_fields_change():
    from live_contentops import dispatch_outbox_policy as p

    result = _result()
    active = [r for r in result["records"] if r["status"] == "candidate"][0]
    entry = {
        "platform": active["platform"],
        "payload_hash": active["payload_hash"],
        "destination_binding_id": active["destination_binding_id"],
        "credential_handle_id": active["credential_handle_id"],
        "ledger_entry_id": active["source_approval_ledger_entry_id"],
    }
    proof = p.idempotency_determinism_proof(entry)
    assert all(proof.values())
    assert result["contract_packet"]["idempotency_key_determinism_proof"] == proof


def test_every_record_has_required_safety_gates_disabled():
    records = _result()["records"]
    for record in records:
        assert record["request_budget"] == 1
        assert record["auto_retry_allowed"] is False
        assert record["credential_hydration_allowed"] is False
        assert record["platform_api_call_allowed"] is False
        assert record["live_dispatch_allowed"] is False
        assert record["valid_for_dispatch"] is False
        assert record["can_dispatch"] is False
        assert record["provider_api_called"] is False
        assert record["platform_api_called"] is False
        assert record["live_post_performed"] is False
        assert record["credential_hydration_performed"] is False
        assert record["live_ready_state_created"] is False


def test_platform_statuses_remain_no_api_no_send():
    records = _result()["records"]
    substack = [r for r in records if r["platform"] == "substack"]
    assert substack
    assert all(r["substack_dispatch_status"] == "manual_export_no_api" for r in substack)
    contract = _result()["contract_packet"]
    assert contract["telegram_dispatch_status"] == "proven_frozen_no_send"
    assert contract["substack_dispatch_status"] == "manual_export_no_api"
    assert contract["x_dispatch_status"] == "dry_run_no_api"


def test_audit_hash_changes_if_bound_material_changes():
    from live_contentops import dispatch_outbox_candidate_contract as c
    from live_contentops import dispatch_outbox_policy as p

    inputs = c.load_inputs(REPO_ROOT)
    entry = next(e for e in inputs["ledger_outputs"] if e["eligible_for_outbox_candidate"] is True)
    policy_packet = p.build_policy_packet()
    key = p.compute_idempotency_key(entry)
    base = c.compute_audit_hash(entry, key, "candidate", [], policy_packet)
    for field in ["platform", "payload_hash", "destination_binding_id", "credential_handle_id", "ledger_entry_id"]:
        changed = copy.deepcopy(entry)
        changed[field] = f"changed_{field}"
        changed_key = p.compute_idempotency_key(changed)
        assert c.compute_audit_hash(changed, changed_key, "candidate", [], policy_packet) != base


def test_contract_packet_counts_checksums_and_safety():
    packet = _result()["contract_packet"]
    assert packet["active_candidate_count"] == 1
    assert packet["blocked_candidate_count"] >= 17
    assert packet["duplicate_suppressed_count"] == 1
    assert packet["all_request_budget_one"] is True
    assert packet["all_auto_retry_false"] is True
    assert packet["all_credential_hydration_false"] is True
    assert packet["all_platform_api_call_false"] is True
    assert packet["all_live_dispatch_false"] is True
    assert packet["all_valid_for_dispatch_false"] is True
    assert packet["all_can_dispatch_false"] is True
    assert packet["all_live_ready_state_false"] is True
    for key in ["network_performed", "env_read", "dotenv_read", "credential_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "credential_hydration_performed", "live_ready_state_created", "platform_dispatch_performed"]:
        assert packet[key] is False


def test_no_raw_credential_token_chat_id_env_secret_live_url_material():
    result = _result()
    text = str(result).lower()
    forbidden = ["raw_credential", "raw_token", "raw_chat_id", "raw_destination", "env_var", "secret_path", "live_url", "chat_id", "token", "secret"]
    for item in forbidden:
        assert item not in text


def test_next_dispatch_gate_matrix_contract():
    next_packet = _result()["next_packet"]
    assert next_packet["next_batch_prompt"].endswith("DISPATCH_GATE_MATRIX_CONTRACT_V0")
    assert "credential_hydration" in next_packet["forbidden_outputs"]
    assert "platform_api_call" in next_packet["forbidden_outputs"]
    assert "live_ready_state" in next_packet["forbidden_outputs"]
    assert next_packet["platform_dispatch_performed"] is False


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import dispatch_outbox_candidate_contract as c

    first = c.write_artifacts(REPO_ROOT)
    second = c.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        c.write_artifacts(REPO_ROOT, tmp_path)
