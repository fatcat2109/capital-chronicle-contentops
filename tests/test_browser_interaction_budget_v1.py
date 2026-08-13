from __future__ import annotations

import json
from datetime import datetime, timezone

from live_contentops.browser_interaction_budget_v1 import (
    BROWSER_INTERACTION_BUDGET_V1,
    browser_interaction_summary,
    configure_browser_interaction_telemetry,
    record_browser_interaction_event,
    sanitize_browser_target_metadata,
    sanitize_process_metadata,
)


def test_budget_is_explicit_and_forbids_idle_edge_interaction():
    budget = BROWSER_INTERACTION_BUDGET_V1
    assert budget.edge_idle_readiness_navigation_max == 0
    assert budget.edge_idle_auth_probe_max == 0
    assert budget.edge_global_social_probe_allowed is False
    assert budget.edge_publication_active_probe_per_destination_attempt_max == 1
    assert budget.x_normal_interval_seconds == 1800
    assert budget.x_hot_followup_interval_seconds == 900
    assert budget.x_empty_interval_seconds == 3600
    assert budget.x_parallel_captures_max == 0


def test_target_diagnostics_never_emit_synthetic_oauth_or_token_values():
    fixtures = (
        "http://127.0.0.1:8765/linkedin/oauth/callback?code=SECRET&state=SECRET",
        "https://example.test/callback?access_token=SECRET",
        "https://example.test/callback?client_secret=SECRET#SECRET",
    )
    serialized = json.dumps([
        sanitize_browser_target_metadata({"type": "page", "url": url, "title": url})
        for url in fixtures
    ], sort_keys=True)
    assert "SECRET" not in serialized
    assert "code=" not in serialized
    assert "access_token=" not in serialized
    assert "client_secret=" not in serialized
    callback = sanitize_browser_target_metadata({"type": "page", "url": fixtures[0]})
    assert callback["callback_query_contains_code"] is True
    assert callback["callback_query_contains_state"] is True
    assert callback["contains_access_token_parameter"] is False
    assert callback["contains_client_secret_parameter"] is False
    assert callback["title_classification"] == "TITLE_REDACTED_SENSITIVE"


def test_process_diagnostics_return_classification_only():
    raw = (
        'msedge.exe --remote-debugging-port=9223 '
        '--user-data-dir="A:/Capital Chronicle/operator-browser-profiles/contentops-social-main" '
        'http://127.0.0.1:8765/callback?code=SECRET&state=SECRET'
    )
    result = sanitize_process_metadata({"ProcessId": 41, "Name": "msedge.exe", "CommandLine": raw})
    serialized = json.dumps(result, sort_keys=True)
    assert result == {
        "process_id": 41,
        "executable_class": "EDGE",
        "canonical_profile_match": True,
        "cdp_port": 9223,
        "contentops_ownership": True,
        "sensitive_url_argument_present": True,
    }
    assert "SECRET" not in serialized
    assert "127.0.0.1" not in serialized
    assert "contentops-social-main" not in serialized


def test_local_hourly_counters_are_bounded_and_sanitized(tmp_path):
    root = tmp_path / "telemetry"
    configure_browser_interaction_telemetry(root)
    now = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
    stamp = now.isoformat().replace("+00:00", "Z")
    record_browser_interaction_event(
        "active_probe", reason="PUBLICATION_JIT_READINESS", destination="substack",
        occurred_at_utc=stamp,
    )
    record_browser_interaction_event(
        "navigation", reason="EDGE_DESTINATION_NAVIGATION", destination="substack",
        occurred_at_utc=stamp,
    )
    summary = browser_interaction_summary(root, now=now)
    assert summary["browser_active_probe_count_last_hour"] == 1
    assert summary["browser_navigation_count_last_hour"] == 1
    assert summary["browser_tabs_created_last_hour"] == 0
    assert summary["browser_tabs_closed_last_hour"] == 0
    assert summary["x_capture_count_last_hour"] == 0
    assert summary["global_browser_probe_count_last_hour"] == 0
    assert "SECRET" not in (root / "events.jsonl").read_text(encoding="utf-8")
    configure_browser_interaction_telemetry(None)


def test_edge_page_selection_reuses_existing_canonical_destination_tab():
    from live_contentops.edge_cdp_publishing_adapter_v1 import _reusable_canonical_page

    substack = type("Page", (), {"url": "https://capitalchronicle.substack.com/publish/post"})()
    unrelated = type("Page", (), {"url": "https://example.test/"})()
    context = type("Context", (), {"pages": [unrelated, substack]})()

    assert _reusable_canonical_page(context) is substack
