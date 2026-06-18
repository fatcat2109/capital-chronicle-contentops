import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _result():
    from live_contentops import cockpit_read_model_contract as contract

    return contract.write_artifacts(REPO_ROOT)


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.cockpit_read_model_contract")
    assert module.TASK_LABEL == "TASK_CONTENTOPS_0174YF_YG_YH_COCKPIT_READ_MODEL_CONTRACT_V0"


def test_read_model_statuses_and_platform_statuses():
    read_model = _result()["read_model"]
    assert read_model["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert read_model["local_governance_status"] == "PASS_DRY_RUN_CHAIN"
    assert read_model["live_dispatch_status"] == "BLOCKED"
    assert read_model["manual_export_status"] == "REVIEW_ONLY_READY_FOR_OPERATOR"
    assert read_model["platform_statuses"] == {
        "substack": "MANUAL_EXPORT_ONLY_NO_API",
        "x": "PREVIEW_ONLY_NO_API",
        "telegram": "PREVIEW_ONLY_FROZEN_NO_SEND",
    }


def test_platform_queues_are_separated():
    read_model = _result()["read_model"]
    assert read_model["manual_export_queue"]
    assert all(item["platform"] == "substack" for item in read_model["manual_export_queue"])
    assert read_model["x_preview_queue"]
    assert all(item["platform"] == "x" for item in read_model["x_preview_queue"])
    assert read_model["telegram_preview_queue"]
    assert all(item["platform"] == "telegram" for item in read_model["telegram_preview_queue"])
    telegram_classes = {item["payload_class"] for item in read_model["telegram_preview_queue"]}
    assert "telegram_channel_update" in telegram_classes
    assert "telegram_operator_review_message" in telegram_classes


def test_blocked_live_dispatch_queue_contains_required_future_gates():
    read_model = _result()["read_model"]
    gates = {item["required_future_gate"] for item in read_model["blocked_live_dispatch_queue"]}
    for gate in [
        "kill_switch_activation",
        "redacted_audit_packet",
        "manual_fallback_proof",
        "operator_supervision_window",
        "live_dispatch_separate_approval",
    ]:
        assert gate in gates


def test_allowed_and_forbidden_actions():
    read_model = _result()["read_model"]
    assert "copy_markdown_for_substack" in read_model["allowed_actions"]
    assert "open_static_cockpit_surface_preview" in read_model["allowed_actions"]
    for forbidden in [
        "live_dispatch",
        "credential_hydration",
        "platform_api_call",
        "autonomous_posting",
        "scheduling",
        "reply_or_dm",
        "scraping",
    ]:
        assert forbidden in read_model["forbidden_actions"]
        assert forbidden not in read_model["allowed_actions"]


def test_evidence_index_includes_all_upstream_stage_checksums():
    read_model = _result()["read_model"]
    stages = {entry["stage"] for entry in read_model["evidence_index"]}
    expected = {
        "cockpit_read_model_policy_checksum",
        "manual_export_review_surface_checksum",
        "manual_export_review_policy_checksum",
        "manual_export_review_fixture_outputs_checksum",
        "next_cockpit_read_model_contract_checksum",
        "supervised_dispatch_readiness_summary_checksum",
        "full_dry_run_chain_reconciliation_checksum",
        "dispatch_audit_dry_run_contract_checksum",
        "dispatch_audit_dry_run_fixture_outputs_checksum",
        "platform_universe_registry_checksum",
    }
    assert expected <= stages
    assert all(len(entry["checksum"]) == 64 for entry in read_model["evidence_index"])


def test_payload_hash_index_has_hashes_no_forbidden_material():
    from live_contentops import cockpit_read_model_policy as policy

    read_model = _result()["read_model"]
    assert read_model["payload_hash_index"]
    assert all(len(entry["payload_hash"]) == 64 for entry in read_model["payload_hash_index"])
    assert policy.validate_no_forbidden_material(read_model["payload_hash_index"])
    assert read_model["payload_hash_index_proof"] == "pass_hashes_only_no_raw_credential_token_destination_env_path_live_url_provider_output"


def test_every_queue_item_is_non_dispatchable_and_non_public():
    read_model = _result()["read_model"]
    for item in read_model["current_review_queue"]:
        assert item["public_postable"] is False
        assert item["can_dispatch"] is False
        assert item["human_review_required"] is True
        assert item["no_financial_advice"] is True
        assert item["no_signal_language"] is True


def test_no_forbidden_readiness_claim_and_no_live_behavior():
    from live_contentops import cockpit_read_model_policy as policy

    read_model = _result()["read_model"]
    assert read_model["no_forbidden_readiness_claim_proof"] == "pass_no_forbidden_readiness_claims_in_cockpit_read_model"
    assert policy.validate_no_forbidden_readiness_claims(read_model)
    proof = read_model["no_live_behavior_proof"]
    assert proof["is_local_only"] is True
    for key, value in proof.items():
        if key not in {"is_local_only", "proof"}:
            assert value is False
    assert read_model["public_postable"] is False
    assert read_model["can_dispatch"] is False
    assert read_model["live_ready_state_created"] is False


def test_counts_and_next_task():
    read_model = _result()["read_model"]
    assert read_model["platform_counts"] == {"substack": 6, "x": 6, "telegram": 2}
    assert len(read_model["current_review_queue"]) == 14
    assert len(read_model["manual_export_queue"]) == 6
    assert len(read_model["x_preview_queue"]) == 6
    assert len(read_model["telegram_preview_queue"]) == 2
    assert read_model["next_builder_task"] == "TASK_CONTENTOPS_0174YI_YJ_YK_STATIC_COCKPIT_SURFACE_CONTRACT_V0"
    assert "static cockpit" in read_model["next_operator_action"]


def test_deterministic_generation_and_path_protection():
    from live_contentops import cockpit_read_model_contract as contract

    first = contract.write_artifacts(REPO_ROOT)
    second = contract.write_artifacts(REPO_ROOT)
    assert first == second
    assert first["read_model"]["cockpit_read_model_checksum"] == second["read_model"]["cockpit_read_model_checksum"]
    assert first["next_packet"]["next_static_cockpit_surface_contract_checksum"] == second["next_packet"]["next_static_cockpit_surface_contract_checksum"]
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        contract.write_artifacts(REPO_ROOT, REPO_ROOT)
