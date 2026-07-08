"""Unit tests for Telegram Live Adapter."""
from __future__ import annotations

from live_contentops.telegram_live_adapter_v6 import (
    execute_telegram_comment,
    execute_telegram_edit,
    execute_telegram_photo,
    execute_telegram_post,
)
from live_contentops.public_dispatch_freeze_guard_v6 import (
    build_public_dispatch_payload_hash,
    build_public_dispatch_topic_hash,
    make_public_dispatch_approval_marker,
)


def _telegram_approval_context(*, run_id: str, topic: str, action: str, body_text: str, media_url: str | None = None) -> dict:
    topic_hash = build_public_dispatch_topic_hash(topic, "test angle")
    payload_hash = build_public_dispatch_payload_hash(
        platform="telegram",
        action=action,
        body_text=body_text,
        media_url=media_url,
        topic_hash=topic_hash,
    )
    return {
        "operator_approval_marker": make_public_dispatch_approval_marker(
            run_id=run_id,
            topic_hash=topic_hash,
            payload_hash=payload_hash,
            platform="telegram",
        ),
        "run_id": run_id,
        "topic_hash": topic_hash,
        "payload_hash": payload_hash,
        "media_url": media_url,
        "prior_dispatch_hashes": {},
        "public_dispatch_ledger_path": None,
    }


def test_execute_telegram_post_dry_run():
    res = execute_telegram_post(
        message="Test Telegram message",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "telegram"
    assert res["action"] == "post"
    assert res["payload_redacted"]["message"] == "Test Telegram message"
    assert "telegram_mock_msg_" in res["response"]["id"]


def test_execute_telegram_comment_dry_run():
    res = execute_telegram_comment(
        reply_to_message_id=123,
        message="Test reply text",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "telegram"
    assert res["action"] == "comment"
    assert res["payload_redacted"]["reply_to_message_id"] == 123


def test_execute_telegram_edit_dry_run():
    res = execute_telegram_edit(
        message_id=123,
        new_message="Updated text message",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "telegram"
    assert res["action"] == "edit"
    assert res["payload_redacted"]["new_message"] == "Updated text message"


def test_execute_telegram_photo_dry_run():
    res = execute_telegram_photo(
        photo_url="https://example.com/chart.png",
        caption="Chart caption",
        dry_run=True,
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "telegram"
    assert res["action"] == "photo"
    assert res["payload_redacted"]["photo_url"] == "https://example.com/chart.png"
    assert res["payload_redacted"]["caption"] == "Chart caption"


def test_execute_telegram_post_freezes_without_operator_approval(monkeypatch):
    sent_reqs = []

    def mock_urlopen(req, timeout=None):
        sent_reqs.append(req)
        raise AssertionError("Telegram network call must not be reached")

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res = execute_telegram_post(
        message="A meaningful market note that should still require explicit operator approval.",
        dry_run=False,
    )

    assert res["status"] == "PUBLIC_DISPATCH_FROZEN"
    assert "operator_approval_marker_missing" in res["error"]
    assert sent_reqs == []


def test_execute_telegram_photo_local_file_upload(tmp_path, monkeypatch):
    # Create a temp local file
    img_file = tmp_path / "test_photo.png"
    img_file.write_bytes(b"dummy image bytes")
    
    # Mock credentials in env
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
    monkeypatch.setenv("TELEGRAM_TARGET_CHAT_ID", "mock_chat")
    
    # Mock urllib.request.urlopen
    class MockResponse:
        def read(self):
            return b'{"ok": true, "result": {"message_id": 999}}'
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
            
    sent_reqs = []
    def mock_urlopen(req, timeout=None):
        sent_reqs.append(req)
        return MockResponse()
        
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    import live_contentops.live_telemetry_v6 as telemetry
    recorded_telemetry = []
    monkeypatch.setattr(
        telemetry,
        "classify_and_record_dispatch",
        lambda **kwargs: recorded_telemetry.append(kwargs),
    )
    
    caption = "Local photo caption with enough market context to avoid preview-only Telegram output."
    approval_context = _telegram_approval_context(
        run_id="v6_pipeline_test_adapter",
        topic="Adapter approval test topic",
        action="photo",
        body_text=caption,
        media_url=str(img_file),
    )
    res = execute_telegram_photo(
        photo_url=str(img_file),
        caption=caption,
        dry_run=False,
        approval_context=approval_context,
    )
    
    assert res["status"] == "SUCCESS"
    assert res["id"] == "999"
    assert len(recorded_telemetry) == 1
    assert len(sent_reqs) == 1
    req = sent_reqs[0]
    assert "multipart/form-data" in req.get_header("Content-type")
    assert req.data is not None
    assert b"dummy image bytes" in req.data
