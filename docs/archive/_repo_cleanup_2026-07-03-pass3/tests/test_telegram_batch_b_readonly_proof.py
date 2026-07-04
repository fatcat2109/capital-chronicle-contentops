from pathlib import Path

from live_contentops.telegram_batch_b_readonly_proof import run_batch_b_telegram_readonly_proof, write_evidence

TOKEN = "123456:ABCdefghijklmnopqrstuvwxyz1234567890"


def _write_env(root, extra=""):
    Path(root, ".env.local").write_text(
        "TELEGRAM_BOT_TOKEN=" + TOKEN + "\nTELEGRAM_CHANNEL_ID=-1001234567890\n" + extra,
        encoding="utf-8",
    )


def test_dry_run_blocks_without_env(tmp_path):
    packet = run_batch_b_telegram_readonly_proof(repo_root=tmp_path)
    assert packet["status"] == "blocked"
    assert "approved_env_source_unavailable" in packet["blocked_reasons"]
    assert packet["raw_response_persisted"] is False


def test_getme_and_getchat_pass_redacted_with_mock_transport(tmp_path):
    _write_env(tmp_path)
    seen = []

    def transport(url, timeout):
        seen.append(url)
        if url.endswith("/getMe"):
            return "http_2xx_json", {"ok": True, "result": {"id": 1, "is_bot": True, "username": "not_returned"}}
        assert "getChat" in url
        return "http_2xx_json", {"ok": True, "result": {"id": -1, "type": "channel", "title": "not_returned"}}

    packet = run_batch_b_telegram_readonly_proof(repo_root=tmp_path, live_readonly_telegram=True, _transport=transport)
    assert packet["status"] == "pass"
    assert packet["probes"]["getMe"]["result_classification"] == "read_only_probe_pass"
    assert packet["probes"]["getChat"]["result_classification"] == "read_only_probe_pass"
    assert packet["probes"]["getMe"]["request_count"] == 1
    assert packet["probes"]["getChat"]["request_count"] == 1
    assert "not_returned" not in str(packet)
    assert len(seen) == 2


def test_getchat_blocks_when_channel_missing(tmp_path):
    Path(tmp_path, ".env.local").write_text("TELEGRAM_BOT_TOKEN=" + TOKEN + "\n", encoding="utf-8")

    def transport(url, timeout):
        return "http_2xx_json", {"ok": True, "result": {"id": 1, "is_bot": True}}

    packet = run_batch_b_telegram_readonly_proof(repo_root=tmp_path, live_readonly_telegram=True, _transport=transport)
    assert packet["status"] == "partial_pass_getchat_blocked_or_unverified"
    assert packet["probes"]["getChat"]["request_count"] == 0


def test_http_error_redacted(tmp_path):
    _write_env(tmp_path)

    def transport(url, timeout):
        return "http_error_redacted_401", None

    packet = run_batch_b_telegram_readonly_proof(repo_root=tmp_path, live_readonly_telegram=True, _transport=transport)
    assert packet["status"] == "blocked"
    assert packet["probes"]["getMe"]["result_classification"] == "http_error_redacted_401"


def test_secret_like_output_guard_blocks(tmp_path):
    _write_env(tmp_path)

    def transport(url, timeout):
        return "http_2xx_json", {"ok": True, "result": {"id": "123456:ABCdefghijklmnopqrstuvwxyz1234567890", "is_bot": True}}

    packet = run_batch_b_telegram_readonly_proof(repo_root=tmp_path, live_readonly_telegram=True, _transport=transport)
    assert packet["probes"]["getMe"]["bot_identity_present_class"] == "present_redacted"


def test_write_evidence_redacted(tmp_path):
    packet = run_batch_b_telegram_readonly_proof(repo_root=tmp_path)
    out = tmp_path / "evidence.json"
    write_evidence(packet, out)
    text = out.read_text(encoding="utf-8")
    assert "raw_response_persisted" in text
    assert TOKEN not in text
