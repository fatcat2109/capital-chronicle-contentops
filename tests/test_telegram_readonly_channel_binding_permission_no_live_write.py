from pathlib import Path

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
    ]
    for needle in forbidden:
        assert needle not in MODULE_TEXT


def test_no_browser_playwright_cdp_or_ui_imports():
    forbidden = [
        "playwright",
        "selenium",
        "browser",
        "cdp",
        "screenshot",
        "localStorage",
        "sessionStorage",
    ]
    lowered = MODULE_TEXT.lower()
    for needle in forbidden:
        assert needle.lower() not in lowered


def test_default_packet_generation_is_redacted(tmp_path):
    output = gate.run_telegram_readonly_channel_binding_permission_proof(write=True, repo_root=tmp_path)
    packet_dir = tmp_path / gate.PACKET_REL_DIR

    assert output["status"] == "blocked"
    assert output["request_count"] == 0
    assert (packet_dir / "evidence_packet.json").exists()
    assert (packet_dir / "audit_packet.json").exists()
    assert (packet_dir / "redacted_candidate_packet.json").exists()
    assert (packet_dir / "validation_packet.json").exists()

    for path in packet_dir.iterdir():
        text = path.read_text(encoding="utf-8")
        assert "api.telegram.org/bot" not in text
        assert "CONTENTOPS_TELEGRAM_BOT_TOKEN=" not in text
        assert "CONTENTOPS_TELEGRAM_CHANNEL_ID_OR_HANDLE=" not in text
        assert "123456:" not in text
        assert "@" not in text
        assert "-1001234567890" not in text


def test_module_keeps_live_write_locked_in_static_contract():
    plan = gate.build_telegram_readonly_probe_plan()
    assert plan.live_write_allowed_now is False
    assert plan.send_permission_unlocked_now is False
    assert plan.request_budget_max == 3
    assert plan.retry_allowed is False
