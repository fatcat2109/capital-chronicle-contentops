import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    assert callable(module.write_artifacts)
    assert module.TASK_LABEL.startswith("TASK_CONTENTOPS_0174WY_WZ_XA")


def test_registry_accepts_latest_committed_ledger12_chain():
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    registry = module.build_registry(REPO_ROOT)
    assert registry["status"] == "pass"
    assert registry["telegram_channel_dispatch_status"] == "proven_frozen"
    assert registry["latest_accepted_ledger_count"] == 12
    assert registry["latest_successful_sequence"] == 13
    assert registry["latest_remote_loop_state_checksum"] == "56fd3ac4b4aabf30e679fd2aff4ce9a62e03e86c20a70557febe85741e28a9cc"
    assert registry["latest_chain_hardening_audit_checksum"] == "d32844aa049072fc3712e4fcd06cd660d911f440d250078cc245c67838ca52bf"
    assert registry["latest_dispatch_proof_checksum"] == "93c8bc238f6a0f823ed8ee6c85c621f1908e7d9ed6c4ea991275175b80005865"


def test_registry_blocks_stale_ledger_count(monkeypatch):
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    original = module._load_json

    def fake(repo_root, rel_path):
        data = original(repo_root, rel_path)
        if rel_path == module.LEDGER12_PACKET_REL:
            data["current_ledger_count"] = 11
        return data

    monkeypatch.setattr(module, "_load_json", fake)
    registry = module.build_registry(REPO_ROOT)
    assert "latest_ledger_count_below_12" in registry["blockers"]
    assert registry["status"] == "blocked"


def test_registry_blocks_stale_sequence(monkeypatch):
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    original = module._load_json

    def fake(repo_root, rel_path):
        data = original(repo_root, rel_path)
        if rel_path == module.LEDGER12_PACKET_REL:
            data["last_successful_send_sequence"] = 12
        return data

    monkeypatch.setattr(module, "_load_json", fake)
    registry = module.build_registry(REPO_ROOT)
    assert "latest_successful_sequence_below_13" in registry["blockers"]
    assert registry["status"] == "blocked"


def test_registry_blocks_missing_or_failed_chain_hardening_audit(monkeypatch):
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    original = module._load_json

    def fake(repo_root, rel_path):
        data = original(repo_root, rel_path)
        if rel_path == module.HARDENING_AUDIT_REL:
            data["audit_passed"] = False
        return data

    monkeypatch.setattr(module, "_load_json", fake)
    registry = module.build_registry(REPO_ROOT)
    assert "missing_or_failed_chain_hardening_audit" in registry["blockers"]
    assert registry["status"] == "blocked"


def test_freeze_flags_and_no_treadmill_policy():
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    registry = module.build_registry(REPO_ROOT)
    assert registry["next_live_send_allowed"] == "false_by_default"
    assert registry["requires_new_operator_task"] is True
    assert registry["requires_new_exact_payload_hash"] is True
    assert registry["requires_new_manual_gate_packet"] is True
    assert registry["requires_new_outbox_entry"] is True
    assert registry["requires_regression_reason"] is True
    assert registry["no_more_ledger_treadmill"] is True
    assert registry["default_next_task_class"] == "platform_registry_and_remote_inbox_pipeline"


def test_refuses_new_ledger_live_send_next_task():
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    registry = module.build_registry(REPO_ROOT)
    assert registry["refuses_new_ledger_to_ledger_live_send_next_task"] is True
    assert "arbitrary_ledgerN_increment" in registry["future_live_send_not_allowed_for"]
    assert "proof_of_life_ping" in registry["future_live_send_not_allowed_for"]


def test_freeze_certificate_proves_required_capability():
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    cert = module.build_freeze_certificate(module.build_registry(REPO_ROOT))
    demonstrated = cert["capability_demonstrated"]
    assert demonstrated["bot_channel_destination_binding"] is True
    assert demonstrated["exact_payload_hash_approval"] is True
    assert demonstrated["manual_gate_capture"] is True
    assert demonstrated["exactly_one_sendMessage"] is True
    assert demonstrated["request_budget_used"] == 1
    assert demonstrated["no_retry"] is True
    assert demonstrated["ledger_append"] is True
    assert demonstrated["replay_guard"] is True
    assert demonstrated["redacted_audit"] is True
    assert demonstrated["multi_send_chain_reconciliation_through_ledger12"] is True


def test_no_live_env_network_provider_behavior():
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    registry = module.build_registry(REPO_ROOT)
    for key in [
        "network_performed", "env_read", "dotenv_read", "credential_read",
        "telegram_api_called", "platform_api_called", "provider_api_called",
        "scheduler_enabled", "live_post_performed",
        "autonomous_reply_or_dm_performed", "scraping_performed",
        "new_live_send_runner_created",
    ]:
        assert registry[key] is False


def test_deterministic_packet_generation_and_unsafe_path_refusal(tmp_path):
    module = importlib.import_module("live_contentops.telegram_supervised_dispatch_capability_registry")
    first = module.write_artifacts(REPO_ROOT)
    second = module.write_artifacts(REPO_ROOT)
    assert first == second
    assert (REPO_ROOT / module.DOC_REL_DIR / module.REGISTRY_PACKET).exists()
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        module.write_artifacts(REPO_ROOT, tmp_path)
