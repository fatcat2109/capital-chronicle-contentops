import json
from pathlib import Path

import pytest

from live_contentops import cli
from live_contentops import telegram_readonly_channel_binding_permission_proof as gate


MODULE_PATH = Path(__file__).resolve().parents[1] / "live_contentops" / "telegram_readonly_channel_binding_permission_proof.py"
MODULE_TEXT = MODULE_PATH.read_text(encoding="utf-8")


def test_allowlist_contains_no_write_methods():
    assert gate.ALLOWED_METHODS == ("getMe", "getChat", "getChatMember")
    lower_allowed = " ".join(gate.ALLOWED_METHODS).lower()
    for fragment in gate.FORBIDDEN_TELEGRAM_METHOD_FRAGMENTS:
        assert fragment not in lower_allowed


def test_module_static_text_has_no_telegram_write_api_calls():
    forbidden = [
        "sendMessage(",
        "sendPhoto(",
        "sendVideo(",
        "sendDocument(",
        "editMessageText(",
        "deleteMessage(",
        "pinChatMessage(",
        "unpinChatMessage(",
        "createChatInviteLink(",
        "banChatMember(",
        "promoteChatMember(",
        "setWebhook(",
        "getUpdates(",
    ]
    for needle in forbidden:
        assert needle not in MODULE_TEXT


def test_no_browser_playwright_cdp_or_ui_imports():
    forbidden = [
        "playwright",
        "selenium",
        "chromedevtools",
        "localStorage",
        "sessionStorage",
    ]
    lowered = MODULE_TEXT.lower()
    for needle in forbidden:
        assert needle.lower() not in lowered


def test_default_packet_generation_is_redacted_and_canonical(tmp_path):
    output = gate.run_telegram_readonly_channel_binding_permission_proof(write=True, repo_root=tmp_path)
    packet_dir = tmp_path / gate.PACKET_REL_DIR

    assert output["result_classification"] == gate.BLOCKED_OPERATOR_GO_REQUIRED
    assert output["request_budget_used"] == 0
    for name in gate.canonical_packet_names():
        assert (packet_dir / name).exists(), name
    for name in gate.legacy_packet_names():
        assert (packet_dir / name).exists(), name

    for path in packet_dir.iterdir():
        text = path.read_text(encoding="utf-8")
        assert "api.telegram.org/bot" not in text
        assert "TELEGRAM_BOT_TOKEN=" not in text
        assert "TELEGRAM_CHANNEL_ID=" not in text
        assert "CONTENTOPS_TELEGRAM_BOT_TOKEN=" not in text
        assert "CONTENTOPS_TELEGRAM_CHANNEL_ID_OR_HANDLE=" not in text
        assert "123456:" not in text
        assert "@" not in text
        assert "-1001234567890" not in text


def test_account_binding_candidate_never_enables_live_flags(tmp_path):
    gate.run_telegram_readonly_channel_binding_permission_proof(write=True, repo_root=tmp_path)
    packet = json.loads((tmp_path / gate.PACKET_REL_DIR / "account_binding_update_candidate_packet.json").read_text(encoding="utf-8"))

    assert packet["live_write_allowed_now"] is False
    assert packet["dispatchable_now"] is False
    assert packet["public_postable_now"] is False
    assert packet["valid_for_live_dispatch_now"] is False
    assert packet["no_secret_output"] is True
    assert packet["request_budget_used"] <= 3


def test_live_gate_candidate_never_passes_or_enables_dispatch(tmp_path):
    gate.run_telegram_readonly_channel_binding_permission_proof(write=True, repo_root=tmp_path)
    packet = json.loads((tmp_path / gate.PACKET_REL_DIR / "live_gate_update_candidate_packet.json").read_text(encoding="utf-8"))

    assert packet["valid_for_live_dispatch_now"] is False
    assert packet["gate_passed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["request_budget_max"] == 3
    assert packet["request_budget_used"] <= 3
    assert packet["no_auto_retry"] is True
    assert packet["no_write_endpoint_called"] is True
    assert packet["credential_hydration_performed"] is False
    assert packet["raw_response_persisted"] is False


def test_legacy_packets_marked_as_compat_aliases(tmp_path):
    gate.run_telegram_readonly_channel_binding_permission_proof(write=True, repo_root=tmp_path)
    packet_dir = tmp_path / gate.PACKET_REL_DIR

    for name in gate.legacy_packet_names():
        packet = json.loads((packet_dir / name).read_text(encoding="utf-8"))
        assert packet["legacy_compat_alias"] is True
        assert packet["canonical_packets"] == gate.canonical_packet_names()


def test_module_keeps_live_write_locked_in_static_contract():
    plan = gate.build_telegram_readonly_probe_plan()
    assert plan.live_write_allowed_now is False
    assert plan.send_permission_unlocked_now is False
    assert plan.request_budget_max == 3
    assert plan.retry_allowed is False


def test_cli_default_no_flags_blocks_before_network(monkeypatch, capsys):
    def fail_api(*_args, **_kwargs):
        raise AssertionError("api should not be called")

    monkeypatch.setattr(gate, "_telegram_api_call", fail_api)
    monkeypatch.setattr(cli.sys, "argv", ["cc", "telegram-readonly-channel-binding-permission-proof"])

    cli.telegram_readonly_channel_binding_permission_proof_summary()
    captured = capsys.readouterr().out
    result = json.loads(captured)

    assert result["result_classification"] == gate.BLOCKED_OPERATOR_GO_REQUIRED
    assert result["request_budget_used"] == 0


def test_all_canonical_json_packets_have_no_secret_output(tmp_path):
    gate.run_telegram_readonly_channel_binding_permission_proof(write=True, repo_root=tmp_path)
    packet_dir = tmp_path / gate.PACKET_REL_DIR
    json_names = [name for name in gate.canonical_packet_names() if name.endswith(".json")] + gate.legacy_packet_names()

    for name in json_names:
        packet = json.loads((packet_dir / name).read_text(encoding="utf-8"))
        gate.assert_no_telegram_secret_output(packet)
        assert packet.get("request_budget_used", 0) <= 3


def test_exact_next_task_pointer_created(tmp_path):
    gate.run_telegram_readonly_channel_binding_permission_proof(write=True, repo_root=tmp_path)
    text = (tmp_path / gate.PACKET_REL_DIR / "next_task_pointer.md").read_text(encoding="utf-8")

    assert "TASK_CONTENTOPS_TELEGRAM_SUPERVISED_SENDMESSAGE_PREP_AND_DRY_RUN_GATE_V0" in text
