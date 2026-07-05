"""Unit tests for Threads official API adapter."""
from __future__ import annotations

import json
from unittest.mock import MagicMock
import urllib.error
import pytest

from live_contentops import threads_adapter_v6 as adapter


def test_compile_payload():
    payload = adapter.compile_threads_payload("Threads post text", "TEXT")
    assert payload["media_type"] == "TEXT"
    assert payload["text"] == "Threads post text"

    payload_reply = adapter.compile_threads_payload("Threads reply", "TEXT", reply_to_id="parent_id_123")
    assert payload_reply["reply_to_id"] == "parent_id_123"


def test_execute_post_dry_run():
    res = adapter.execute_threads_post(
        threads_user_id="threads_user_123",
        access_token="fake_token",
        text="Dry run thread test",
        dry_run=True,
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["response"]["id"] == "threads_user_123_mock_thread_12345"


def test_execute_post_success(monkeypatch):
    # Mock Step 1: Create container ID
    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = b'{"id": "threads_container_777"}'
    mock_resp1.__enter__.return_value = mock_resp1

    # Mock Step 2: Publish container ID
    mock_resp2 = MagicMock()
    mock_resp2.read.return_value = b'{"id": "threads_published_post_888"}'
    mock_resp2.__enter__.return_value = mock_resp2

    urlopen_calls = [mock_resp1, mock_resp2]
    def side_effect(*args, **kwargs):
        return urlopen_calls.pop(0)

    mock_urlopen = MagicMock(side_effect=side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res = adapter.execute_threads_post(
        threads_user_id="threads_user_123",
        access_token="fake_token",
        text="Success flow test",
    )
    assert res["status"] == "SUCCESS"
    assert res["id"] == "threads_published_post_888"
    assert res["container_id"] == "threads_container_777"


def test_execute_post_step1_failure(monkeypatch):
    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Invalid credentials."}}'
    mock_error = urllib.error.HTTPError(
        url="https://graph.threads.net/v1.0/threads_user_123/threads",
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=mock_fp,
    )
    mock_urlopen = MagicMock(side_effect=mock_error)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res = adapter.execute_threads_post(
        threads_user_id="threads_user_123",
        access_token="fake_token",
        text="Step 1 failure test",
    )
    assert res["status"] == "FAILED_STEP_1"
    assert res["error_code"] == 401


def test_execute_post_step2_failure(monkeypatch):
    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = b'{"id": "threads_container_777"}'
    mock_resp1.__enter__.return_value = mock_resp1

    mock_fp = MagicMock()
    mock_fp.read.return_value = b'{"error": {"message": "Server error."}}'
    mock_error = urllib.error.HTTPError(
        url="https://graph.threads.net/v1.0/threads_user_123/threads_publish",
        code=500,
        msg="Internal Server Error",
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

    res = adapter.execute_threads_post(
        threads_user_id="threads_user_123",
        access_token="fake_token",
        text="Step 2 failure test",
    )
    assert res["status"] == "FAILED_STEP_2"
    assert res["error_code"] == 500
    assert res["container_id"] == "threads_container_777"
