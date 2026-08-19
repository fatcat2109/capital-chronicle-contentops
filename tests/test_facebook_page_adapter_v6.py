"""Unit tests for Facebook Page official API adapter."""
from __future__ import annotations

from unittest.mock import MagicMock
import urllib.error
import urllib.parse
import urllib.request

import pytest

from live_contentops import facebook_page_adapter_v6 as adapter
from live_contentops import live_telemetry_v6


@pytest.fixture(autouse=True)
def _disable_persistent_live_telemetry(monkeypatch):
    monkeypatch.setattr(
        live_telemetry_v6, "classify_and_record_dispatch", lambda *_args, **_kwargs: None
    )


def test_compile_payload():
    payload = adapter.compile_facebook_post_payload("Hello world", "https://example.com")
    assert payload == {"message": "Hello world", "link": "https://example.com"}


def test_compile_photo_payload():
    payload = adapter.compile_facebook_photo_payload("Hello world", "https://example.com/img.jpg")
    assert payload == {"caption": "Hello world", "url": "https://example.com/img.jpg"}


def test_execute_post_dry_run_env_fallback(monkeypatch):
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "12345")
    monkeypatch.setenv("FACEBOOK_PAGE_ACCESS_TOKEN", "fake_token")
    res = adapter.execute_facebook_post(message="Dry run test", link="https://example.com", dry_run=True)
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "12345_mock_post_12345"
    assert res["payload_redacted"]["access_token"] == "<redacted>"


def test_execute_photo_dry_run_env_fallback(monkeypatch):
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "12345")
    monkeypatch.setenv("FACEBOOK_PAGE_ACCESS_TOKEN", "fake_token")
    res = adapter.execute_facebook_photo(message="Dry run photo", image_url="https://example.com/img.jpg", dry_run=True)
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["post_id"] == "12345_mock_post_12345"
    assert res["payload_redacted"]["access_token"] == "<redacted>"


def test_execute_post_validation_failure(monkeypatch):
    monkeypatch.delenv("FACEBOOK_PAGE_ID", raising=False)
    monkeypatch.delenv("FACEBOOK_PAGE_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    res = adapter.execute_facebook_post(message="No destination")
    assert res["status"] == "VALIDATION_FAILED"
    assert set(res["missing"]) == {"page_id", "access_token"}


def test_execute_post_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"id": "12345_post_id_999"}'
    mock_response.__enter__.return_value = mock_response
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(return_value=mock_response))

    res = adapter.execute_facebook_post(page_id="12345", access_token="fake_token", message="Real post mock success")
    assert res["status"] == "SUCCESS"
    assert res["id"] == "12345_post_id_999"


def test_execute_photo_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"id": "12345_photo_id_999", "post_id": "12345_post_id_999"}'
    mock_response.__enter__.return_value = mock_response
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(return_value=mock_response))

    res = adapter.execute_facebook_photo(
        page_id="12345",
        access_token="fake_token",
        message="Real photo mock success",
        image_url="https://example.com/img.jpg",
    )
    assert res["status"] == "SUCCESS"
    assert res["id"] == "12345_post_id_999"


def test_execute_post_http_error(monkeypatch):
    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Invalid OAuth access token."}}'
    mock_error = urllib.error.HTTPError("https://graph.facebook.com/v21.0/12345/feed", 400, "Bad Request", None, mock_fp)
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(side_effect=mock_error))

    res = adapter.execute_facebook_post(page_id="12345", access_token="invalid_token", message="Real post mock error")
    assert res["status"] == "FAILED"
    assert res["error_code"] == 400
    assert "Invalid OAuth access token." in res["error_response"]["error"]["message"]


def test_execute_comment_dry_run():
    res = adapter.execute_facebook_comment("12345_67890", "fake_token", "Dry run comment", dry_run=True)
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "12345_67890_mock_comment_67890"


def test_execute_comment_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"id": "comment_id_abc"}'
    mock_response.__enter__.return_value = mock_response
    monkeypatch.setattr(urllib.request, "urlopen", MagicMock(return_value=mock_response))

    res = adapter.execute_facebook_comment("12345_67890", "fake_token", "Comment success")
    assert res["status"] == "SUCCESS"
    assert res["id"] == "comment_id_abc"


def test_execute_edit_dry_run_and_validation():
    res = adapter.execute_facebook_edit("12345_67890", "fake_token", message="Updated", dry_run=True)
    assert res["status"] == "DRY_RUN_PASS"
    assert res["payload_redacted"]["access_token"] == "<redacted>"

    missing = adapter.execute_facebook_edit("12345_67890", "fake_token")
    assert missing["status"] == "VALIDATION_FAILED"
    assert "message_or_link" in missing["missing"]


def test_readback_accepts_canonical_link_from_facebook_attachment_redirect(monkeypatch):
    canonical = "https://capitalchronicle.substack.com/p/exact-story"
    wrapped = (
        "https://l.facebook.com/l.php?u="
        + urllib.parse.quote(canonical + "?utm_source=facebook", safe="")
        + "&h=opaque"
    )
    monkeypatch.setattr(
        adapter,
        "_get_json",
        lambda *_args, **_kwargs: {
            "id": "page_123",
            "message": "Exact story title\nBody without a raw URL",
            "permalink_url": "https://www.facebook.com/page/posts/123",
            "from": {"id": "page", "name": "Capital Chronicle"},
            "attachments": {"data": [{"target": {"url": wrapped}}]},
        },
    )

    result = adapter.readback_facebook_post(
        post_id="page_123",
        expected_text="Exact story title\nBody without a raw URL",
        canonical_url=canonical,
        page_id="page",
        access_token="token",
    )

    assert result["status"] == "SUCCESS"
    assert result["substack_url_visible"] is True


def test_attachment_link_must_match_exact_canonical_host_and_path():
    expected = "https://capitalchronicle.substack.com/p/exact-story"

    assert adapter._canonical_link_matches(
        expected, expected + "?utm_source=facebook"
    )
    assert not adapter._canonical_link_matches(
        expected, "https://capitalchronicle.substack.com.evil.example/p/exact-story"
    )
