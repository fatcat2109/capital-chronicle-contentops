"""Tests for TASK_CONTENTOPS_0171 institutional static polish / UI consistency."""

import copy
import json
from pathlib import Path

from live_contentops import institutional_static_polish_ui_consistency_hardening as m

_SHELL = Path(__file__).resolve().parent.parent / "ui" / "institutional_shell"
_FIXTURE = _SHELL / "fixture_data.js"
_APP = _SHELL / "app.js"


def _p():
    return m.build_packet()


def test_packet_validates():
    assert m.validate_packet(_p())["valid"]


def test_summary_valid():
    assert m.build_summary()["validation_valid"] is True


def test_task_label():
    assert _p()["task_label"] == m.TASK_LABEL


def test_required_starting_baseline():
    assert _p()["required_starting_baseline"] == "063b0bc"


def test_prior_classification_caveat_preserved():
    p = _p()
    assert p["prior_task_classification"] == "PASS_WITH_PROCESS_CAVEAT"
    assert p["process_caveat_preserved"] is True


def test_twelve_screens_present():
    assert _p()["screen_count"] == 12


def test_global_metadata_consistent():
    assert _p()["current_global_metadata_consistent"] is True


def test_no_stale_regression():
    assert _p()["stale_global_header_regression_count"] == 0


def test_historical_policy_present():
    assert _p()["historical_metadata_policy_present"] is True


def test_forbidden_controls_zero():
    assert _p()["forbidden_controls_active_count"] == 0


def test_kill_switch_active():
    assert _p()["kill_switch_status"] == "active"


def test_secret_visible_zero():
    assert _p()["secret_visible_count"] == 0


def test_no_browser_or_antigravity():
    p = _p()
    assert p["browser_opened_now"] is False
    assert p["browser_automation_used_now"] is False
    assert p["antigravity_used_now"] is False


def test_no_export_or_capture():
    p = _p()
    assert p["screenshot_capture_enabled_now"] is False
    assert p["file_export_enabled_now"] is False
    assert p["platform_upload_enabled_now"] is False


def test_no_project_sources_refresh():
    assert _p()["project_sources_refresh_created_now"] is False


def test_no_live_or_scheduler_or_scraping():
    p = _p()
    assert p["live_posting_enabled_now"] is False
    assert p["scheduler_allowed_now"] is False
    assert p["scraping_allowed_now"] is False


def test_no_evidence_mutation():
    assert _p()["evidence_mutation_enabled_now"] is False


# --- negative cases ---

def test_forbidden_flag_true_fails():
    p = copy.deepcopy(_p())
    p["live_posting_enabled_now"] = True
    assert not m.validate_packet(p)["valid"]


def test_stale_regression_fails():
    p = copy.deepcopy(_p())
    p["stale_global_header_regression_count"] = 1
    assert not m.validate_packet(p)["valid"]


def test_historical_policy_missing_fails():
    p = copy.deepcopy(_p())
    p["historical_metadata_policy_present"] = False
    assert not m.validate_packet(p)["valid"]


def test_screen_count_mismatch_fails():
    p = copy.deepcopy(_p())
    p["screen_count"] = 11
    assert not m.validate_packet(p)["valid"]


def test_secret_visible_fails():
    p = copy.deepcopy(_p())
    p["secret_visible_count"] = 1
    assert not m.validate_packet(p)["valid"]


def test_pass_with_errors_fails():
    p = copy.deepcopy(_p())
    p["kill_switch_status"] = "inactive"
    res = m.validate_packet(p)
    assert not res["valid"]


# --- live shell asset checks ---

def test_global_header_not_stale_head():
    fx = _FIXTURE.read_text(encoding="utf-8")
    assert 'accepted_head_short: "15b87ff"' not in fx
    assert 'accepted_head_short: "444ef2c"' in fx


def test_global_header_not_stale_gate():
    fx = _FIXTURE.read_text(encoding="utf-8")
    assert 'current_gate: "telegram_official_docs' not in fx


def test_per_screen_heads_labeled_historical():
    app = _APP.read_text(encoding="utf-8")
    assert "Screen Baseline (historical)" in app
    assert "Screen Gate (historical)" in app


def test_schema_required_fields_match():
    schema = json.loads(
        (Path(__file__).resolve().parent.parent / "schemas"
         / "institutional_static_polish_ui_consistency_hardening_packet.schema.json")
        .read_text(encoding="utf-8")
    )
    p = _p()
    for field in schema["required"]:
        assert field in p
