import json
from pathlib import Path

from live_contentops.telegram_live_sendmessage_pilot import run_pilot

TOKEN = "123456:abcdefghijklmnopqrstuvwxyzABCDEF"
CHANNEL = "-1001234567890"


def _env(tmp_path: Path, kill="0"):
    (tmp_path / ".env.local").write_text(f"TELEGRAM_BOT_TOKEN={TOKEN}\nTELEGRAM_CHANNEL_ID={CHANNEL}\nCONTENTOPS_GLOBAL_KILL_SWITCH={kill}\n", encoding="utf-8")


def test_mocked_runner_passes_and_sends_once(tmp_path):
    _env(tmp_path)
    calls = []
    def transport(method_name, http_method, token, params, timeout):
        calls.append((method_name, http_method, dict(params)))
        if method_name == "getMe":
            return "http_2xx_json", {"ok": True, "result": {"id": 1, "is_bot": True}}
        if method_name == "getChat":
            return "http_2xx_json", {"ok": True, "result": {"id": -1, "type": "channel"}}
        if method_name == "sendMessage":
            return "http_2xx_json", {"ok": True, "result": {"message_id": 77}}
        raise AssertionError(method_name)
    audit = run_pilot(tmp_path, "docs/automation/TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY/telegram_live_sendmessage_audit_redacted.json", True, transport)
    assert audit["status"] == "success"
    assert [c[0] for c in calls] == ["getMe", "getChat", "sendMessage"]
    assert audit["request_counts"] == {"getMe": 1, "getChat": 1, "sendMessage": 1}
    assert audit["sendMessage"]["method"] == "POST"
    assert audit["sendMessage"]["sent_message_id_presence_class"] == "present_redacted"


def test_live_send_path_requires_operator_flag(tmp_path):
    _env(tmp_path)
    calls = []
    audit = run_pilot(tmp_path, "docs/automation/TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY/telegram_live_sendmessage_audit_redacted.json", False, lambda *args: calls.append(args) or ("http_2xx_json", {}))
    assert audit["status"] == "blocked_or_not_success"
    assert "operator_approved_live_telegram_flag_missing" in audit["blocked_reasons"]
    assert calls == []


def test_unknown_result_blocks_retry(tmp_path):
    _env(tmp_path)
    calls = []
    def transport(method_name, http_method, token, params, timeout):
        calls.append(method_name)
        if method_name == "getMe":
            return "http_2xx_json", {"ok": True, "result": {"id": 1, "is_bot": True}}
        if method_name == "getChat":
            return "http_2xx_json", {"ok": True, "result": {"id": -1, "type": "channel"}}
        return "transport_or_parse_error_redacted:TimeoutError", None
    audit = run_pilot(tmp_path, "docs/automation/TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY/telegram_live_sendmessage_audit_redacted.json", True, transport)
    assert calls == ["getMe", "getChat", "sendMessage"]
    assert audit["sendMessage"]["result_classification"] == "unknown_requires_manual_reconciliation"
    assert audit["manual_reconciliation_required"] is True
    assert audit["no_retry_performed"] is True


def test_written_audit_excludes_raw_secret_material(tmp_path):
    _env(tmp_path)
    def transport(method_name, http_method, token, params, timeout):
        if method_name == "getMe":
            return "http_2xx_json", {"ok": True, "result": {"id": 1, "is_bot": True}}
        if method_name == "getChat":
            return "http_2xx_json", {"ok": True, "result": {"id": -1, "type": "channel"}}
        return "http_2xx_json", {"ok": True, "result": {"message_id": 77, "chat": {"id": CHANNEL}}}
    rel = "docs/automation/TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY/telegram_live_sendmessage_audit_redacted.json"
    run_pilot(tmp_path, rel, True, transport)
    text = (tmp_path / rel).read_text(encoding="utf-8")
    assert TOKEN not in text
    assert CHANNEL not in text
    assert "message_id\": 77" not in text
    data = json.loads(text)
    assert data["raw_request_persisted"] is False
    assert data["raw_response_persisted"] is False
