"""Unit tests for Facebook Page official API adapter."""
from __future__ import annotations

import json
from unittest.mock import MagicMock
import urllib.error
import pytest

from live_contentops import facebook_page_adapter_v6 as adapter


def test_compile_payload():
    payload = adapter.compile_facebook_post_payload("Hello world", "https://example.com")
    assert payload["message"] == "Hello world"
    assert payload["link"] == "https://example.com"


def test_execute_post_dry_run():
    res = adapter.execute_facebook_post(
        page_id="12345",
        access_token="fake_token",
        message="Dry run test",
        link="https://example.com",
        dry_run=True,
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "12345_mock_post_12345"


def test_execute_post_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"id": "12345_post_id_999"}'
    mock_response.__enter__.return_value = mock_response
    mock_urlopen = MagicMock(return_value=mock_response)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res = adapter.execute_facebook_post(
        page_id="12345",
        access_token="fake_token",
        message="Real post mock success",
    )
    print("RES IS:", res)
    assert res["status"] == "SUCCESS"
    assert res["id"] == "12345_post_id_999"


def test_execute_post_http_error(monkeypatch):
    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Invalid OAuth access token."}}'
    mock_error = urllib.error.HTTPError(
        url="https://graph.facebook.com/v21.0/12345/feed",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=mock_fp,
    )
    mock_urlopen = MagicMock(side_effect=mock_error)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res = adapter.execute_facebook_post(
        page_id="12345",
        access_token="invalid_token",
        message="Real post mock error",
    )
    assert res["status"] == "FAILED"
    assert res["error_code"] == 400
    assert "Invalid OAuth access token." in res["error_response"]["error"]["message"]


def test_execute_comment_dry_run():
    res = adapter.execute_facebook_comment(
        post_id="12345_67890",
        access_token="fake_token",
        message="Dry run comment",
        dry_run=True,
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "12345_67890_mock_comment_67890"


def test_execute_comment_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"id": "comment_id_abc"}'
    mock_response.__enter__.return_value = mock_response
    mock_urlopen = MagicMock(return_value=mock_response)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res = adapter.execute_facebook_comment(
        post_id="12345_67890",
        access_token="fake_token",
        message="Comment success",
    )
    assert res["status"] == "SUCCESS"
    assert res["id"] == "comment_id_abc"
