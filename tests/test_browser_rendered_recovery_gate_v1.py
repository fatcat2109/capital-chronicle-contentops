from __future__ import annotations

import urllib.error

from live_contentops.browser_rendered_source_recovery_v1 import (
    BROWSER_UNAVAILABLE,
    BrowserRenderedSourceRecoveryError,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    BROWSER_RENDERED_RECOVERY_DISABLED,
    BrowserRenderedRecoveryConfig,
    dry_run_browser_rendered_recovery,
)


URL = "https://www.bloomberg.com/news/articles/2026-08-18/gate-dry-run"
AS_OF = "2026-08-19T10:23:11Z"


def _response(url: str, *, status: int = 200) -> dict:
    return {
        "status": status,
        "final_url": url,
        "headers": {"content-type": "text/html"},
        "body": b"<html><body>source</body></html>",
    }


def test_disabled_by_default_keeps_browser_callback_unused_after_eligible_http_failure():
    http_calls: list[str] = []
    browser_calls: list[str] = []

    def http_get(url: str, _timeout: float, _maximum: int):
        http_calls.append(url)
        raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)

    def rendered_get(url: str, _timeout: float, _maximum: int):
        browser_calls.append(url)
        return {"status": "PASS"}

    result = dry_run_browser_rendered_recovery(
        url=URL,
        evaluation_as_of_utc=AS_OF,
        http_get=http_get,
        rendered_source_get=rendered_get,
    )

    assert result["status"] == BROWSER_RENDERED_RECOVERY_DISABLED
    assert result["browser_rendered_recovery_enabled"] is False
    assert result["browser_rendered_recovery_attempt_count"] == 0
    assert result["request_count"] == 1
    assert http_calls == [URL]
    assert browser_calls == []
    assert result["public_write_performed"] is False
    assert result["publication_authority"] is False


def test_http_success_short_circuits_without_browser_call():
    http_calls: list[str] = []
    browser_calls: list[str] = []

    def http_get(url: str, _timeout: float, _maximum: int):
        http_calls.append(url)
        return _response(url)

    def rendered_get(url: str, _timeout: float, _maximum: int):
        browser_calls.append(url)
        return {"status": "PASS"}

    result = dry_run_browser_rendered_recovery(
        url=URL,
        evaluation_as_of_utc=AS_OF,
        http_get=http_get,
        rendered_source_get=rendered_get,
        browser_rendered_recovery_config=BrowserRenderedRecoveryConfig(enabled=True),
    )

    assert result["status"] == "HTTP_SUCCESS_NO_BROWSER"
    assert result["browser_rendered_recovery_attempt_count"] == 0
    assert result["request_count"] == 1
    assert http_calls == [URL]
    assert browser_calls == []


def test_named_render_failure_triggers_one_injected_browser_attempt():
    browser_calls: list[str] = []

    def http_get(_url: str, _timeout: float, _maximum: int):
        raise ValueError("public_source_relevant_text_unavailable")

    def rendered_get(url: str, _timeout: float, _maximum: int):
        browser_calls.append(url)
        return {"status": "PASS", "dry_run_marker": True}

    result = dry_run_browser_rendered_recovery(
        url=URL,
        evaluation_as_of_utc=AS_OF,
        http_get=http_get,
        rendered_source_get=rendered_get,
        browser_rendered_recovery_config=BrowserRenderedRecoveryConfig(enabled=True),
    )

    assert result["status"] == "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS"
    assert result["http_failure"] == "public_source_relevant_text_unavailable"
    assert result["browser_rendered_recovery_attempt_count"] == 1
    assert result["request_count"] == 2
    assert browser_calls == [URL]


def test_browser_unavailable_is_fail_closed_after_one_attempt():
    browser_calls: list[str] = []

    def http_get(_url: str, _timeout: float, _maximum: int):
        raise urllib.error.HTTPError(URL, 429, "Too Many Requests", {}, None)

    def rendered_get(url: str, _timeout: float, _maximum: int):
        browser_calls.append(url)
        raise BrowserRenderedSourceRecoveryError("browseros_neo_mcp_unavailable")

    result = dry_run_browser_rendered_recovery(
        url=URL,
        evaluation_as_of_utc=AS_OF,
        http_get=http_get,
        rendered_source_get=rendered_get,
        browser_rendered_recovery_config=BrowserRenderedRecoveryConfig(enabled=True),
    )

    assert result["status"] == BROWSER_UNAVAILABLE
    assert result["failure_detail"] == "browseros_neo_mcp_unavailable"
    assert result["browser_rendered_recovery_attempt_count"] == 1
    assert result["request_count"] == 2
    assert browser_calls == [URL]
    assert result["public_write_performed"] is False
    assert result["publication_authority"] is False
