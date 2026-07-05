"""Unit tests for Instagram Business official API adapter."""
from __future__ import annotations

import json
from unittest.mock import MagicMock
import urllib.error
import pytest

from live_contentops import instagram_adapter_v6 as adapter


def test_compile_payload():
    payload = adapter.compile_instagram_media_payload("https://example.com/image.jpg", "Instagram caption")
    assert payload["image_url"] == "https://example.com/image.jpg"
    assert payload["caption"] == "Instagram caption"


def test_execute_post_dry_run():
    res = adapter.execute_instagram_post(
        ig_id="instagram_123",
        access_token="fake_token",
        image_url="https://example.com/image.jpg",
        caption="Dry run test",
        dry_run=True,
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "instagram_123_mock_media_12345"


def test_execute_post_success(monkeypatch):
    # Mock Step 1: Create container ID
    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = b'{"id": "container_id_777"}'
    mock_resp1.__enter__.return_value = mock_resp1

    # Mock Step 2: Publish container ID
    mock_resp2 = MagicMock()
    mock_resp2.read.return_value = b'{"id": "media_published_id_888"}'
    mock_resp2.__enter__.return_value = mock_resp2

    # We use a stateful side_effect mock to return different mock responses sequentially
    urlopen_calls = [mock_resp1, mock_resp2]
    def side_effect(*args, **kwargs):
        return urlopen_calls.pop(0)

    mock_urlopen = MagicMock(side_effect=side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res = adapter.execute_instagram_post(
        ig_id="instagram_123",
        access_token="fake_token",
        image_url="https://example.com/image.jpg",
        caption="Success flow test",
    )
    assert res["status"] == "SUCCESS"
    assert res["id"] == "media_published_id_888"
    assert res["container_id"] == "container_id_777"


def test_execute_post_step1_failure(monkeypatch):
    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Invalid access token."}}'
    mock_error = urllib.error.HTTPError(
        url="https://graph.facebook.com/v21.0/instagram_123/media",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=mock_fp,
    )
    mock_urlopen = MagicMock(side_effect=mock_error)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res = adapter.execute_instagram_post(
        ig_id="instagram_123",
        access_token="fake_token",
        image_url="https://example.com/image.jpg",
        caption="Step 1 failure test",
    )
    assert res["status"] == "FAILED_STEP_1"
    assert res["error_code"] == 400


def test_execute_post_step2_failure(monkeypatch):
    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = b'{"id": "container_id_777"}'
    mock_resp1.__enter__.return_value = mock_resp1

    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Publishing limit reached."}}'
    mock_error = urllib.error.HTTPError(
        url="https://graph.facebook.com/v21.0/instagram_123/media_publish",
        code=429,
        msg="Too Many Requests",
        hdrs=None,
        fp=mock_fp,
    )

    urlopen_calls = [mock_resp1, mock_error]
    def side_effect(*args, **kwargs):
        val = urlopen_calls.pop(0)
        if isinstance(val, Exception):
            raise val
        return val

    mock_urlopen = MagicMock(side_effect=side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res = adapter.execute_instagram_post(
        ig_id="instagram_123",
        access_token="fake_token",
        image_url="https://example.com/image.jpg",
        caption="Step 2 failure test",
    )
    assert res["status"] == "FAILED_STEP_2"
    assert res["error_code"] == 429
    assert res["container_id"] == "container_id_777"


def test_execute_comment_dry_run():
    res = adapter.execute_instagram_comment(
        media_id="media_999",
        access_token="fake_token",
        message="Dry run comment",
        dry_run=True,
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "media_999_mock_comment_67890"
