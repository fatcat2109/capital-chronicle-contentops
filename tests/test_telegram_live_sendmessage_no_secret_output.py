from pathlib import Path

from live_contentops.telegram_live_sendmessage_pilot import run_pilot

TOKEN = "123456:abcdefghijklmnopqrstuvwxyzABCDEF"
CHANNEL = "-1001234567890"


def test_no_secret_output_for_mocked_success(tmp_path: Path):
    (tmp_path / ".env.local").write_text(f"TELEGRAM_BOT_TOKEN={TOKEN}\nTELEGRAM_CHANNEL_ID={CHANNEL}\n", encoding="utf-8")
    def transport(method_name, http_method, token, params, timeout):
        if method_name == "getMe":
            return "http_2xx_json", {"ok": True, "result": {"id": 1, "is_bot": True}}
        if method_name == "getChat":
            return "http_2xx_json", {"ok": True, "result": {"id": -1, "type": "channel"}}
        return "http_2xx_json", {"ok": True, "result": {"message_id": 123, "chat": {"id": CHANNEL}}}
    rel = "docs/automation/TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY/telegram_live_sendmessage_audit_redacted.json"
    audit = run_pilot(tmp_path, rel, True, transport)
    text = (tmp_path / rel).read_text(encoding="utf-8")
    assert TOKEN not in text
    assert CHANNEL not in text
    assert "123456:" not in text
    assert audit["raw_secret_persisted"] is False
    assert audit["raw_url_persisted"] is False
