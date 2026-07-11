"""Unit tests for Threads official API adapter."""
from __future__ import annotations

from unittest.mock import MagicMock
import urllib.error
import urllib.request

from live_contentops import threads_adapter_v6 as adapter


def test_compile_payload():
    payload = adapter.compile_threads_payload("Threads post text", "TEXT")
    assert payload["media_type"] == "TEXT"
    assert payload["text"] == "Threads post text"
    payload_reply = adapter.compile_threads_payload("Threads reply", "TEXT", reply_to_id="parent_id_123")
    assert payload_reply["reply_to_id"] == "parent_id_123"


def test_execute_post_dry_run_env_fallback(monkeypatch):
    monkeypatch.setenv("THREADS_USER_ID", "threads_user_123")
    monkeypatch.setenv("THREADS_USER_ACCESS_TOKEN", "fake_token")
    res = adapter.execute_threads_post(text="Dry run thread test", dry_run=True)
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "threads_user_123_mock_thread_12345"


def test_execute_post_accepts_media_type():
    res = adapter.execute_threads_post("threads_user_123", "fake_token", "Image post", media_type="IMAGE", image_url="https://example.com/i.jpg", dry_run=True)
    assert res["status"] == "DRY_RUN_PASS"
    assert res["container_payload_redacted"]["media_type"] == "IMAGE"


def test_execute_post_validation_failure(monkeypatch):
    monkeypatch.delenv("THREADS_USER_ID", raising=False)
    monkeypatch.delenv("THREADS_USER_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("THREADS_ACCESS_TOKEN", raising=False)
    res = adapter.execute_threads_post(text="")
    assert res["status"] == "VALIDATION_FAILED"
    assert {"threads_user_id", "access_token", "text"}.issubset(set(res["missing"]))


def test_execute_post_success(monkeypatch):
    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = b'{"id": "threads_container_777"}'
    mock_resp1.__enter__.return_value = mock_resp1
    mock_resp2 = MagicMock()
    mock_resp2.read.return_value = b'{"id": "threads_published_post_888"}'
    mock_resp2.__enter__.return_value = mock_resp2
    calls = [mock_resp1, mock_resp2]
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(side_effect=lambda *a, **k: calls.pop(0)))

    res = adapter.execute_threads_post("threads_user_123", "fake_token", "Success flow test")
    assert res["status"] == "SUCCESS"
    assert res["id"] == "threads_published_post_888"
    assert res["container_id"] == "threads_container_777"


def test_execute_post_step1_failure(monkeypatch):
    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Invalid credentials."}}'
    mock_error = urllib.error.HTTPError("https://graph.threads.net/v1.0/threads_user_123/threads", 401, "Unauthorized", None, mock_fp)
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(side_effect=mock_error))

    res = adapter.execute_threads_post("threads_user_123", "fake_token", "Step 1 failure test")
    assert res["status"] == "FAILED_STEP_1"
    assert res["error_code"] == 401


def test_execute_post_step2_failure(monkeypatch):
    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = b'{"id": "threads_container_777"}'
    mock_resp1.__enter__.return_value = mock_resp1
    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Server error."}}'
    mock_error = urllib.error.HTTPError("https://graph.threads.net/v1.0/threads_user_123/threads_publish", 500, "Internal Server Error", None, mock_fp)
    calls = [mock_resp1, mock_error]
    def side_effect(*args, **kwargs):
        val = calls.pop(0)
        if isinstance(val, Exception):
            raise val
        return val
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(side_effect=side_effect))

    res = adapter.execute_threads_post("threads_user_123", "fake_token", "Step 2 failure test")
    assert res["status"] == "FAILED_STEP_2"
    assert res["error_code"] == 500
    assert res["container_id"] == "threads_container_777"


def test_execute_edit_unsupported():
    res = adapter.execute_threads_edit()
    assert res["status"] == "UNSUPPORTED"
    assert res["platform_id"] == "threads"


def test_delete_exact_rejects_non_allowlisted_target(monkeypatch):
    monkeypatch.setenv("THREADS_USER_ACCESS_TOKEN", "fake_token")
    result = adapter.execute_threads_delete_exact(
        post_id="unrelated",
        expected_permalink="https://www.threads.com/@official.capitalchronicle/post/unrelated",
        expected_text="text",
        allowed_post_ids={"approved"},
        dry_run=True,
    )
    assert result["status"] == "BLOCKED_THREADS_DELETE_TARGET_NOT_ALLOWLISTED"


def test_delete_exact_requires_matching_readback(monkeypatch):
    monkeypatch.setenv("THREADS_USER_ACCESS_TOKEN", "fake_token")
    monkeypatch.setattr(adapter, "readback_threads_post", lambda **_: {"status": "SUCCESS", "account_identity_verified": True, "public_url": "https://wrong.example/post"})
    result = adapter.execute_threads_delete_exact(
        post_id="approved",
        expected_permalink="https://www.threads.com/@official.capitalchronicle/post/approved",
        expected_text="text",
        allowed_post_ids={"approved"},
        dry_run=True,
    )
    assert result["status"] == "BLOCKED_THREADS_DELETE_EXACT_IDENTITY_MISMATCH"


def test_delete_exact_dry_run_preserves_target(monkeypatch):
    monkeypatch.setenv("THREADS_USER_ACCESS_TOKEN", "fake_token")
    permalink = "https://www.threads.com/@official.capitalchronicle/post/approved"
    monkeypatch.setattr(adapter, "readback_threads_post", lambda **_: {"status": "SUCCESS", "account_identity_verified": True, "destination_identity": "official.capitalchronicle", "public_url": permalink})
    result = adapter.execute_threads_delete_exact(
        post_id="approved",
        expected_permalink=permalink,
        expected_text="text",
        allowed_post_ids={"approved"},
        dry_run=True,
    )
    assert result["status"] == "DRY_RUN_PASS"
    assert result["delete_performed"] is False
