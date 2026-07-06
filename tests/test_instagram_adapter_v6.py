"""Unit tests for Instagram Business official API adapter."""
from __future__ import annotations

from unittest.mock import MagicMock
import urllib.error
import urllib.request

from live_contentops import instagram_adapter_v6 as adapter


def test_compile_payload():
    payload = adapter.compile_instagram_media_payload("https://example.com/image.jpg", "Instagram caption")
    assert payload == {"image_url": "https://example.com/image.jpg", "caption": "Instagram caption"}


def test_execute_post_dry_run_env_fallback(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "instagram_123")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "fake_token")
    res = adapter.execute_instagram_post(image_url="https://example.com/image.jpg", caption="Dry run test", dry_run=True)
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "instagram_123_mock_media_12345"


def test_execute_post_validation_failure(monkeypatch):
    monkeypatch.delenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("INSTAGRAM_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    res = adapter.execute_instagram_post(caption="Missing image")
    assert res["status"] == "VALIDATION_FAILED"
    assert {"ig_id", "access_token", "image_url"}.issubset(set(res["missing"]))


def test_execute_post_success(monkeypatch):
    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = b'{"id": "container_id_777"}'
    mock_resp1.__enter__.return_value = mock_resp1
    mock_resp2 = MagicMock()
    mock_resp2.read.return_value = b'{"id": "media_published_id_888"}'
    mock_resp2.__enter__.return_value = mock_resp2
    calls = [mock_resp1, mock_resp2]
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(side_effect=lambda *a, **k: calls.pop(0)))
    monkeypatch.setattr(adapter, "validate_instagram_image_url", lambda image_url: [])

    res = adapter.execute_instagram_post("instagram_123", "fake_token", "https://example.com/image.jpg", "Success flow test")
    assert res["status"] == "SUCCESS"
    assert res["id"] == "media_published_id_888"
    assert res["container_id"] == "container_id_777"


def test_execute_post_step1_failure(monkeypatch):
    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Invalid access token."}}'
    mock_error = urllib.error.HTTPError("https://graph.facebook.com/v21.0/instagram_123/media", 400, "Bad Request", None, mock_fp)
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(side_effect=mock_error))
    monkeypatch.setattr(adapter, "validate_instagram_image_url", lambda image_url: [])

    res = adapter.execute_instagram_post("instagram_123", "fake_token", "https://example.com/image.jpg", "Step 1 failure test")
    assert res["status"] == "FAILED_STEP_1"
    assert res["error_code"] == 400


def test_execute_post_step2_failure(monkeypatch):
    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = b'{"id": "container_id_777"}'
    mock_resp1.__enter__.return_value = mock_resp1
    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Publishing limit reached."}}'
    mock_error = urllib.error.HTTPError("https://graph.facebook.com/v21.0/instagram_123/media_publish", 429, "Too Many Requests", None, mock_fp)
    calls = [mock_resp1, mock_error]
    def side_effect(*args, **kwargs):
        val = calls.pop(0)
        if isinstance(val, Exception):
            raise val
        return val
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(side_effect=side_effect))
    monkeypatch.setattr(adapter, "validate_instagram_image_url", lambda image_url: [])

    res = adapter.execute_instagram_post("instagram_123", "fake_token", "https://example.com/image.jpg", "Step 2 failure test")
    assert res["status"] == "FAILED_STEP_2"
    assert res["error_code"] == 429
    assert res["container_id"] == "container_id_777"


def test_execute_comment_dry_run():
    res = adapter.execute_instagram_comment("media_999", "fake_token", "Dry run comment", dry_run=True)
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "media_999_mock_comment_67890"


def test_execute_edit_unsupported():
    res = adapter.execute_instagram_edit()
    assert res["status"] == "UNSUPPORTED"
    assert res["platform_id"] == "instagram"


def test_validate_instagram_image_url_rejects_non_http():
    assert adapter.validate_instagram_image_url("file:///tmp/image.jpg") == ["image_url_not_http"]


def test_validate_instagram_image_url_rejects_non_image(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.__enter__.return_value = mock_resp
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(return_value=mock_resp))

    assert adapter.validate_instagram_image_url("https://example.com/page") == ["image_url_not_image:text/html"]


def test_validate_instagram_image_url_falls_back_to_get_when_head_is_405(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Type": "image/jpeg"}
    mock_resp.__enter__.return_value = mock_resp
    calls = []

    def fake_urlopen(req, timeout):
        calls.append((req.get_method(), dict(req.headers), timeout))
        if req.get_method() == "HEAD":
            raise urllib.error.HTTPError(req.full_url, 405, "Method Not Allowed", None, None)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(side_effect=fake_urlopen))

    assert adapter.validate_instagram_image_url("https://example.com/image.jpg", timeout_seconds=3) == []
    assert [method for method, _, _ in calls] == ["HEAD", "GET"]
    assert calls[1][1]["Range"] == "bytes=0-0"
    assert calls[1][2] == 3
